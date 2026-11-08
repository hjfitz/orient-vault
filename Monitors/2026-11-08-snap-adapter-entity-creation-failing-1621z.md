---
tags: [datadog-triage]
date: 2026-11-08
monitor: "[FUSE][Snap Adapter] Entity creation failing for many records"
service: snap-adapter
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794154967934129"
opened_at: "2026-11-08T16:21:36Z"
severity_assessed: P3
flapping: true
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# Second firing today: 15 PURDYFIGG sales orders hit snap-adapter's 30s slot timeout in the 16:20 burst on slow Snap ilg005; all created on redelivery

## Fired
Monitor 334832256 (P2, group total) went Alert at 16:21:36Z (more than 10 distinct `@recordId` with "Entity creation in SNAP failed" in 15m). It recovered 16:01:36Z after the 15:46:36Z firing (monitor events, source:alert, 24h: Triggered 15:46:36, Recovered 16:01:36, Triggered 16:21:36). No Slack post of its own; nearest thread is the same-minute Platform error-rate alert 180072217 (C099WKQTE8G 1794154967.934129, no replies when read). The monitor stays Alert until the 15m window empties (about 16:36Z); still Alert at 16:32Z.

## Investigation
- Failures (snap_adapter prod logs, 16:00Z to 16:32Z): 15 "Entity creation in SNAP failed", 15 distinct recordIds, all PURDYFIGG, all `sales_order`, all `failureMode:slot_timeout`, `errorMessage` "Timed out after 30000ms waiting for a concurrency slot", `transient:true`, `deliveryAttempt:1`, `exhausted:false`. First 16:20:42.521Z, last 16:21:12.506Z. No other failure mode and no other status:error log from 16:20Z on.
- Same mechanism as the 15:45Z firing (same failureMode, error text, business, record type, attempt 1/transient, revision snap-adapter-prod-00099-b4z). Not worse: 15 failures against 33 at 15:45Z.
- Burst: 97 "Incoming record received" 16:20:04Z-16:21:26Z = 82 `deliveryAttempt:1` + 15 `deliveryAttempt:2` (the redeliveries of the 15 failures). 82 "Entity created in SNAP", 82 distinct recordIds, first 16:20:23Z, last 16:22:30Z: PURDYFIGG 76, STUBBLE 4, EPARFUM 1, ESCENTRICPL 1. gcp.pubsub.topic.send_message_operation_count on bifrost.prod.create_record.v1: 76 at 16:21 + 6 at 16:22 = 82. Earlier bursts that created without failure were larger (send counts 128 at 15:51, 111 at 16:01, 110 at 16:06; logs 112 at 16:00 and 115 at 16:05 incoming = created). So burst size alone does not separate the failing bursts.
- Recovery: all 15 failed recordIds have a later "Entity created in SNAP" (checked by recordId, 0 missing): 16:21:54Z to 16:22:28Z, 47.6 s to 100.9 s after each record's last failure. 15 x "POST /events/v1/record/create/sales_order - 503" and 82 x 204.
- Held: replay-list-failures (production, sales_order, 2026-11-08) total 1, DOCKBAY UK-913950 (ShipAddress.City over 30 chars, 15:02:45Z, unrelated). PURDYFIGG sales_order held list newest entry is 2026-11-06 (#6679913), nothing from today.
- Ongoing? No. Next bursts: 16:25 = 69 incoming / 69 created / 0 failed; 16:30 = 74 incoming / 74 created / 0 failed; zero status:error logs in 16:23-16:32Z.
- Cloud Run snap-adapter-prod (gcp.run.*): instance_count 1 until 15:35Z, 3 from 15:36Z to at least 16:24Z (no change at 16:20). 429: 0 every minute 15:37-16:29Z. 503: 11 at 16:21 + 4 at 16:22 = 15, matching the 15 log lines; 0 at all other minutes 16:15-16:29Z.
- Snap ilg005 (host of PURDYFIGG, STUBBLE, EPARFUM per get-snap-connection; ESCENTRICPL is on ilg003): snap.request.latency.avg 568 ms at 16:15, 6586 ms 16:20, 5126 16:21, 4661 16:22, 3387 16:25, 624 16:30. For comparison the clean bursts at 16:00 / 16:02 / 16:05 / 16:06 read 989 / 1487 / 1961 / 2422 ms. At 15:45 it was 7824 ms. snap.slot_queue_depth (max, rollup 60) on ilg005: 24 at 16:15, 16:20, 16:21, 16:30; 14 at 16:22; 15 at 16:25. It also reads 24 at clean bursts, so it does not separate failing from clean bursts. ilg004: 506-808 ms, depth 0. ilg003: depth 0. snap.request.failure returned no data points.
- Direct read-only probe of ilg005 (GET /v2/snaplookups/RECSTATUS at 16:25:35Z, 5 calls 2 s apart): HTTP 200 x5, 0.06-0.08 s on 4 and 4.13 s on 1 (the same roughly 4.1 s outlier seen in the 15:50Z probe).
- Changes: all snap_adapter logs in the last 6h carry revision snap-adapter-prod-00099-b4z (5666 logs); no change_tracking events and no change stories for snap_adapter 10:25-16:26Z. No Maintenance/ record covers 2026-11-08 (grep of 2026-11-0[78] across the folder returned none).
- Failure history (snap_adapter logs, @failureMode:slot_timeout by day, 2-8 Nov): 2 Nov 267, 3 Nov 4, 4 Nov 0, 5 Nov 0, 6 Nov 6, 7 Nov 0, 8 Nov 48 (33 + 15). Today's other failure logs are unrelated (schema_validation DOCKBAY 1).
- Monitor 334832256 fired twice today (15:46:36Z, 16:21:36Z).

## Outcome
real_minor, P3, repeat of the 15:45Z mechanism: a PURDYFIGG order burst met slow ilg005 and snap-adapter's own 30 s slot timeout. 15 orders were delayed 48-101 s and are all in Snap; nothing held; the following 16:25 and 16:30 bursts (69 and 74 orders) created cleanly. Not getting worse (33 then 15 failures). Recurrence is the signal: two slot-timeout bursts in 36 minutes, both coinciding with ilg005 request latency above 6 s, so a ticket for the monitor and slot-cap tuning is the open follow-up (not filed).

Not established: adapter slot cap and ack deadline settings (not read); split of cause between burst size, ilg005 latency and slot cap; why ilg005 averages 4.6-7.8 s in these bursts while 4 of 5 idle probes take 0.06-0.08 s; what the constant slot_queue_depth of 24 means; whether the ilg005 latency is caused by our own load or by Snap (not tested); mapping of "Incoming record received" lines to recordIds (those logs carry messageId, not recordId, so the 82 attempt-1 = 82 created match is by count plus the per-recordId check of the 15 failures).

## Links
- Slack thread (Platform error-rate 180072217, the nearest thread): https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794154967934129
- Monitor: https://app.datadoghq.com/monitors/334832256
- Earlier record, first firing: [[2026-11-08-snap-adapter-entity-creation-failing]]
