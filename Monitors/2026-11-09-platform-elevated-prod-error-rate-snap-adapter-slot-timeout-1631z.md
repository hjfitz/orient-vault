---
tags: [datadog-triage]
date: 2026-11-09
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: snap-adapter
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794241962936309"
opened_at: "2026-11-09T16:31:37Z"
resolved_at: "2026-11-09T16:33:37Z"
minutes_spent: 2
severity_assessed: P3
flapping: true
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# Error-rate monitor fired on 18 PURDYFIGG snap_adapter slot_timeout 503s (17 orders), all now in Snap

## Fired
Log alert 180072217 (more than 2 matching error lines in 2m) went Alert at 16:31:37Z. The third trigger today, after 15:21:37Z and 16:06:37Z. Datadog's own event stream shows it Recovered at 16:33:37Z.

## Investigation
- The monitor's own query for 16:29:37Z-16:31:37Z matched 18 logs (aggregateLogs): all service snap_adapter, all businessId PURDYFIGG, all transient:true, failureMode slot_timeout, "Timed out after 30000ms waiting for a concurrency slot", exhausted:false. 15 in the 16:30Z minute, 3 in 16:31Z. No other service matched the query from 16:29:37Z to 16:35Z.
- 17 distinct orders (#6703471 to #6703566, plus #6701849). Sixteen were deliveryAttempt 1. #6703504 failed at attempt 1 (16:30:43Z) and attempt 2 (16:31:27Z).
- Read-only snap-search of ilg005 by CustomerRef returned 17 shipments for the 17 refs, one each, Status 00, DateCreated 16:30:53 to 16:31:54. None is held.
- Earlier waves today were 3 (15:20Z bucket) and 4 (16:05Z bucket) slot_timeout logs. This one is 18.
- snap.request.latency.avg for ilg005, 5-minute buckets: 3258 ms (16:20Z), 3054 ms (16:25Z), 7789 ms (16:30Z); max 8824 ms in the last. snap.slot_queue_depth reached about 16 at 16:30Z. snap.request count was 0 for 16:26-16:29Z, then 28 at 16:30Z. snap.breaker.state stayed 0 throughout.
- snap.messages.received arrives in bursts about every 5 minutes (16:00: 37, 16:05: 30, 16:10: 33, 16:15: 39, 16:20: 20, 16:25: 23, 16:30: 37). Cloud Run 429s on snap-adapter-prod: 23 at 16:07Z only, none after. Pub/Sub oldest unacked age on snap subscriptions peaked at 157 s (16:10Z), 95 s at 16:33Z.
- Seven-day slot_timeout count (snap_adapter, logs): PURDYFIGG 199, DOCKBAY 6, ESCENTRIC 2.
- No Maintenance/ record covers 2026-11-09 (latest are 2026-11-04 and earlier).

## Not established
- Whether our concurrency cap or slow Snap creates held the slots (no per-call create duration or in-flight telemetry; the cap value was not read).
- Why #6703566 and #6701849 already existed in Snap (16:30:56 and 16:30:53) before their slot_timeout logs (16:31:31 and 16:31:28).
- Why orders created in Shopify at 15:19Z-16:12Z (canonicalRecord dates.created) first reached the adapter at about 16:30Z.
- Which other businesses share ilg005 (lookup-snap-instance returned businessCount 0); direct probe response time (snap-lookup RECSTATUS returned data at about 16:34Z, duration not measured); Snap vendor mail and the #bifrost-general pin were not checked.

## Outcome
real_minor, P3. Transient, all 17 orders in Snap, nothing held. Recurring on the same cause with a larger wave and doubled ilg005 latency, so worth a ticket on the slot cap and burst intake if it repeats. No escalation.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794241962936309
- Earlier: 2026-11-09-platform-elevated-prod-error-rate-snap-adapter-slot-timeout-1606z.md, 2026-11-09-platform-elevated-prod-error-rate-snap-adapter-slot-timeout-1521z.md
