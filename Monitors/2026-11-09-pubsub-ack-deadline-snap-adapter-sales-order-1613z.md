---
tags: [datadog-triage]
date: 2026-11-09
monitor: "[FUSE][Platform] Pub/Sub ack-deadline headroom eroding (standard subscriptions)"
service: snap-adapter
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794240885529899"
opened_at: "2026-11-09T16:13:39Z"
severity_assessed: P4
flapping: true
outcome: real_minor
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# snap_adapter create_record_sales_order sub: oldest unacked 157 s after the 16:05Z PURDYFIGG burst

## Fired
Warn (90 s) on `max(last_10m)` of oldest_unacked_message_age for `snap_adapter.prod.create_record_sales_order.v1.sub`, group first triggered 16:13:39Z (value 157 s, critical line 180 s). The previous Recovered for this group was 15:33:39Z (monitor group `lastResolvedTs`).

## Investigation
- Per-minute metric (oldest_unacked / undelivered, minute stamps 16:08-16:13): 61/119, 92/81, 157/4, 0/0, 13/9, 0/-. The 157 s is a single minute; the next stamps are 0 and 13 s. Datadog's GCP metric stamps run about 2-3 min behind the snap_adapter logs, so the 157 s corresponds to the 16:05-16:08Z log burst, not a newer one.
- snap_adapter, 16:05:00-16:18:16Z: 326 "Incoming record received" (299 deliveryAttempt 1, 27 deliveryAttempt 2, none above 2); 321 "Entity created in SNAP" + 1 "Entity already exists" = 322 records, and 299 + 23 = 322 unique first deliveries. Error/warn logs in that window: exactly 4 (the PURDYFIGG `slot_timeout` 503s at 16:06:11-16:06:20Z already traced in the 16:07Z error-rate thread, `transient:true`, `exhausted:false`, attempt 1). No error or warn after 16:06:20Z. Waves at 16:10 (94 received, 94 created) and 16:15 (107 received, 107 created) were clean and fast.
- 16:05 wave: 90 records received at 16:05:10Z, first "Entity created" at 16:06:40Z, then 10-31 per 10 s until about 16:07:55Z. So roughly 90 s of queueing before the first create.
- Cloud Run snap-adapter-prod `gcp.run.request_count`: 23 responses with code 429 and 4 with 5xx in the minute stamped 16:07 (the 5xx are the 4 slot_timeout 503s). 429s never reached the app, so they are not in its logs. 27 attempt-2 deliveries = 4 (503) + 23 (429), consistent with each failed first delivery being redelivered once. instance_count was already 3 from about 15:20 and stayed 3 through 16:14. `gcp.run.request_latency.pending.p99` read 69,131 (ms assumed) in the 2-minute bucket starting 16:07Z against about 9.9 at 16:03-16:06 buckets.
- The same 429 signature appeared at 08:xx today (35 responses in the 08:00 hour, matching the 08:23Z Warn on this subscription) and again 23 in the 16:00 hour; none in the 15:00 hour.
- Fuse MCP lookup-service notes for snap-adapter: Cloud Run max 3 instances x concurrency 30, per-instance Snap semaphore 5, 503-nack on transient failure with 10-600 s Pub/Sub backoff. A 90-message burst against 3 x 30 matches those numbers, but the live Terraform values were not checked.
- replay-service production list for 2026-11-09 (20 newest of 129): no sales_order create failure after 15:03:01Z (ESCENTRIC 15337, unrelated, ShipContacts.Phone over 20 chars). None for PURDYFIGG sales_order create.
- Snap ilg005 (live host from get-snap-connection, production): snap-lookup RECSTATUS returned 6 rows at about 16:17Z. The tool reports no timing.
- Maintenance/: no record covers 2026-11-09 (latest are 2026-11-02 API update and 2026-11-04 emergency patch / test-DB patch). ILG mail and the #bifrost-general pin not checked.

## Outcome
Real but minor, self-limiting. A 90-message PURDYFIGG burst at 16:05:10Z queued about 90 s behind a Cloud Run request cap (23 x 429, 4 x slot_timeout 503); every message was redelivered once and created. Nothing held, no deliveryAttempt above 2, no exhausted retries. Monitor group still read Warn at about 16:18Z because the 157 s point stays inside its 10 min window until about 16:23Z; the underlying age is back to 0-13 s.

Recurring: second Warn today after 15:25Z, and the 429 signature has now matched two Warns today. The capacity ceiling (3 instances x 30, semaphore 5) vs 5-minute bursts of 90-120 orders is worth a look, and a ticket if it repeats.

Not established: whether Snap create latency or the per-instance semaphore (5) held the slots (no per-call create duration); why 90 s passed before the first create at 16:05:10Z beyond the pending latency above; live Cloud Run max-instances / concurrency; which Warns on 8 Nov belonged to this cause; ILG mail and the #bifrost-general pin; Snap response timing (probe returned status and rows only).

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794240885529899
- Earlier thread (15:25Z, Recovered 15:33:39Z): https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794237907288869
- Monitor: https://app.datadoghq.com/monitors/323648859
