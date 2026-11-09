---
tags: [datadog-triage]
date: 2026-11-08
monitor: "[FUSE][Platform] Pub/Sub ack-deadline headroom eroding (standard subscriptions)"
service: snap-adapter
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794152689491929"
opened_at: "2026-11-08T15:43:39Z"
resolved_at: "2026-11-08T15:52:00Z"
minutes_spent: 8
severity_assessed: P3
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# snap_adapter sales_order sub unacked 110s: burst of ~94 orders, 429s then slot timeouts, all redelivered and created

## Fired
Monitor 323648859 (thresholds warning 90, critical 180), group snap_adapter.prod.create_record_sales_order.v1.sub, Warn at 15:43:39Z with 110s. Prior firings: 2026-11-07 17:03Z (137s, same sub) and 2026-10-21 (outage).

## Investigation
- oldest_unacked_message_age on the sub (60s samples): 38s at 15:37 and 15:38, 110s at 15:39, 0 by 15:40. num_undelivered 57, 57, 19 over 15:37-15:39. 110s is the highest value in the last 2h (next highest 38s); critical 180 was never reached.
- bifrost.prod.create_record.v1 publishes (dedupe-service output, all record types): 94 in the 15:36 minute, against 5-minute buckets of 6-34 over the previous 100 minutes (97 in the 15:35 bucket). create_record_request in: 433 at 15:36.
- snap-adapter-prod Cloud Run: instance_count 1 until 15:35, 3 from 15:36; pending_queue max 33 at 15:36; 10 responses with code 429 at 15:37; Pub/Sub push responses of class unreachable 9 (15:35) and 1 (15:36); nack_requests 9 and 10. "Server listening" x2 at 15:35:16Z. Same mechanism as the 07 Nov 17:03 firing (26 x 429).
- snap_adapter logs 15:35:03-15:40:41: 182 "Incoming record received", 182 "Entity created in SNAP", 182 x 204; no warn or error logs between 13:45Z and 15:45Z other than DOCKBAY UK-913950 at 15:02:44Z. 260 "Entity created in SNAP" logs from 15:30Z, 260 distinct recordIds, so no order created twice.
- Second burst after the alert: 94 "Incoming record received" in the 15:45 minute, 33 "Entity creation in SNAP failed" (PURDYFIGG, failureMode slot_timeout, "Timed out after 30000ms waiting for a concurrency slot") with 33 x 503 on POST /events/v1/record/create/sales_order, 15:45:40-15:46:13Z. By 15:48Z all 33 recordIds (#6694384 ... #6694570) have an "Entity created in SNAP" log. Subscription at last read: undelivered 15, oldest 17s (15:42-15:43 samples).
- snap_adapter snap.request.latency.avg to ilg005 (only host): 4349ms at 15:33, 3390 at 15:34, 3287 at 15:35, 2161 at 15:38, 7824 at 15:45, 6330 at 15:46, 4769 at 15:47; max 8680ms. service note healthy figure 0.5-1s. snap.slot_queue_depth max 10-19 in those minutes. snap.breaker.state 0 throughout.
- Direct read-only probe of ilg005 (GET snaplookups/RECSTATUS, 15:48Z, from the workstation): 200 in 88, 53, 56 ms, then 200 in 4118 and 4148 ms (connect fast, ttfb 4.1s).
- Held failures: replay-service prod sales_order newest entry is DOCKBAY UK-913950 (15:02:45Z, ShipAddress.City > 30 characters, wms_precheck), unrelated to this firing. Nothing from the burst is held.
- Monitor query uses max(last_10m) so one burst keeps it in Warn for 10 minutes; events show the same group warned 07 Nov 17:03Z and again today.

## Outcome
Real but minor, self-recovering: bursts of ~90 sales orders arrive every ~5 minutes, Cloud Run scale-out lags (429 then unreachable, 19 nacks), and in the second burst snap-adapter's own 30s slot wait expired for 33 orders while Snap ilg005 was answering in 4-8s. Every affected order was redelivered and created; nothing stuck or held. Contribution of burst size vs Snap latency vs the slot cap is not separable from the data.

Not established: the subscription's ack deadline and the live snap-adapter concurrency settings (SNAP_MAX_CONCURRENT_REQUESTS, max instances) were not read; why the 4.1s delays occur on ilg005; whether the 15:45 burst was also a dedupe-service publish burst (create_record publish metric for 15:41-15:47 not yet reported); the 94-record 15:45 minute counts from logs only.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794152689491929
- Earlier firing: [[2026-11-07-pubsub-ack-deadline-headroom-snap-adapter-sales-order-1705]]
