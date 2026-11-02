---
tags: [datadog-triage]
date: 2026-10-28
monitor: "Pub/Sub ack-deadline headroom eroding (standard subscriptions)"
service: snap-adapter
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793204781089539"
opened_at: "2026-10-28T16:26:21Z"
severity_assessed: P3
flapping: false
outcome: real_minor
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: resolved
---
# Ack-deadline monitor Warn on snap_adapter create_record_sales_order sub (118s)

## Fired
Monitor 323648859 (max oldest_unacked_message_age over 10m > 180s) warned on snap_adapter.prod.create_record_sales_order.v1.sub, value 118.0s at 16:26Z.

## Investigation
- snap_adapter prod logs 6h: 1 slot_timeout (PURDYFIGG #6611181, 16:15Z), DOCKBAY slot_timeouts only at 12:05Z. No slot-wait wave visible.
- snap_adapter errors 6h are mostly schema_validation retries: ESCENTRIC #138864 (28, every 5 min since 14:15Z, deliveryAttempt 1, fieldError ShipAddress.0.Line1 empty value fails max 50 chars), PURDYFIGG #6521935 (35, 12:50-15:45Z).
- search_datadog_events for monitor 323648859 over 1d returned 0 (not conclusive for flapping).

## Not established
Ack latency, undelivered backlog, redelivery counts, the subscription's ack deadline, flapping history, Snap latency link: every Datadog metrics query timed out, 500ed or was rate limited (429).

## Update (17:30Z, later firing)
Metrics recovered. In 16:05-16:35Z the only error was one slot_timeout (#6611181: 503 at 16:15:53, created 16:17:15). The 118s is consistent with that retry, not message-level confirmed. Ack deadline 300s per snap-adapter iac. See Monitors/2026-10-28-pubsub-ack-deadline-snap-adapter-sales-order-1726.md. Verdict now real_minor, P3.

## Update (2026-11-02 16:46Z, Alert at 16:42:39Z, 248s)
Monitor 323648859 (query max(last_10m) oldest_unacked_message_age by subscription_id > 180, excludes the 600s-deadline subs) went Alert on snap_adapter.prod.create_record_sales_order.v1.sub at 248s. Thread C099WKQTE8G / 1793637845.734799. Warn/Alert levels not read back (the monitor search returned the query only).
- Sub 1-min, 16:37-16:43Z: oldest_unacked 23, 87, 136, 248, 248, 25, 0; num_undelivered 60, 60, 52, 36, 3, 13. Drained by 16:43Z. Other snap_adapter create_record subs (work_order, master_data, purchase_order, rga) and dedupe create_record_request_sales_order: 0 throughout 16:30-16:43Z.
- 24h max in 10-min buckets: 248 is today's highest; the last four buckets rose 72, 44, 136, 248. 300s deadline is the Terraform default, not read back live.
- Cause of this wave: second PURDYFIGG slot_timeout wave, 101 errors 16:35-16:38Z (all transient, failureMode slot_timeout, deliveryAttempt up to 5 on the received log). 49 recordIds errored; all 49 have an "Entity created" (35) or "already exists" (14) log by 16:39:33Z. None pending. Longest first error to created 3m49s (16:35:44 to 16:39:33).
- Waves are the 5-min shopify reap: PURDYFIGG "Bulk reap completed" total (= published) 548, 631, 705, 777, 836, 893, 968, 1042 at 16:10-16:45Z, only PURDYFIGG logs it. snap_adapter receives about 65-86 new sales_orders per 5 min (86, 78, 76, 65, 68, 81, 77). 16:40 batch (81) and 16:45 batch (77) were created in-minute, no errors after 16:38Z.
- Snap: ilg005 snap.slot_queue_depth 24 at nearly every 2-min point 16:16-16:46Z (ilg003/004 0). 5-min avg latency 16:15-16:46Z: ilg005 1.3-17.0s, ilg003 1.9-11.1s, ilg004 4.6-25.8s. ilg005 latency Warn at 16:38Z. No maintenance window covers today (Maintenance/ records end 31 Oct).
- Verdict: real_minor, P3. Backlog drained, nothing held, no order lost, oldest wait 248s (52s inside the 300s deadline). Headroom is thin and rising across waves.
Not established: which Snap host PURDYFIGG uses (Fuse MCP 401), whether the ilg005 queue is PURDYFIGG's, whether Snap latency or the 30s slot cap drives the timeouts, why reap total keeps rising, expired_ack_deadlines_count and ack_latencies (no series), monitor Warn threshold, whether any "already exists" came from a deadline redelivery.

## Outcome (original)
No verdict. Ack posted in thread. Re-check oldest_unacked_message_age / ack_latencies for the sub when the metrics API recovers.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793204781089539
