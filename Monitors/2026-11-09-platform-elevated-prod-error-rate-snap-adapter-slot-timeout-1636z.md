---
tags: [datadog-triage]
date: 2026-11-09
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: snap-adapter
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794242270963239"
opened_at: "2026-11-09T16:36:37Z"
severity_assessed: P3
flapping: true
outcome: real_minor
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Elevated production error rate: 94 slot_timeout 503s (86 orders) on Snap ilg005

## Fired
Monitor 180072217 matched 94 logs in 16:34:37Z-16:36:37Z. All were snap_adapter "Entity creation in SNAP failed", failureMode `slot_timeout`, `transient:true`, `exhausted:false`. 92 were PURDYFIGG and 2 STUBBLE. deliveryAttempt was 1 for 86 and 2 for 8.

## Investigation
- Monitor query, faceted with aggregateLogs over the window: 94 total, service snap_adapter only, businessId PURDYFIGG 92 and STUBBLE 2. They were 86 distinct records (84 PURDYFIGG, 2 STUBBLE). Eight PURDYFIGG orders failed twice.
- Read-only Snap check on ilg005, shipments by CustomerRef, run for all 86 refs: 86 found, none missing, no duplicates, all Status 00. PURDYFIGG created 16:35:13-16:38:35Z, STUBBLE 16:38:11-16:38:13Z.
- Trend: slot_timeout per 5 min since 15:00Z is 3 (15:20), 4 (16:05), 18 (16:30), 100 (16:35, incl. 2 STUBBLE). Cloud Run snap-adapter-prod 5xx per 5 min matches (3, 4, 18, 100). By the minute: 16:35=30, 16:36=70, then none. Entity created logs resumed at 16:37 (47) and 16:38 (52) after 1-3 per minute at 16:33-16:35.
- ilg005 request latency (snap.request.latency.avg, ms) per minute: 10395 at 16:30, 7414, 5656, 6894, 7933, 8366, 10972 at 16:36, then 5422, 5110, 4939, 4362 at 16:40. Max 14.6 s at 16:36. Slot queue depth peaked at 24 at 16:36 (16 in the previous wave). Breaker state 0 on every host.
- Read-only probes of ilg005 (GET shipments top 1) at 16:41Z and 16:43Z: 12 requests, all 200, 2.8-7.6 s each (3.05, 3.33, 3.73, 4.15, 5.5, 7.6 and 2.8, 2.91, 2.91, 5.45, 7.02, 7.62). Earlier thread read 0.06-0.12 s at 16:08Z.
- 429s: 23 on snap-adapter-prod in the 16:05 bucket only, none since. Oldest unacked on snap_adapter prod create_record_sales_order sub peaked at 60.75 s in the 16:35 bucket.
- deliveryAttempt 3 appears on 14 info-level logs 16:36:52-16:37:49Z (one identified: PURDYFIGG #6700369). No error log at attempt >2 and no `exhausted:true` log today.
- Replay-service held failures today (newest 100 of 130): no create-side failure for PURDYFIGG or STUBBLE. Separate held Snap submission failures exist for other causes: DOCKBAY PO (16:38:45Z, snap_api_error, held), AYMSTUDIO PO, SAIRA SO, ESCENTRIC x2, DOCKBAY SO.
- Monitor flapping: 5 triggers before this one since 8 Nov 15:46Z. No Maintenance record covers 9 Nov; #bifrost-general had no maintenance notice since 8 Nov ~15:00Z.

## Outcome
real_minor, P3. All 86 orders are in Snap. The pattern is getting worse (3, 4, 18, 100 per 5 min) and ilg005 is still slow. Nothing stuck. A ticket on the adapter slot cap and burst intake is warranted.

Not established: retry limit before an order exhausts; whether our concurrency cap or Snap held the slots; why ilg005 is slow; which orders were the 14 attempt-3 deliveries; whether 30 older held failures (beyond the 100 read) matter; whether STUBBLE was sharing the burst or just arrived in it; the maintenance mail and #bifrost-general pin were not read.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794242270963239
