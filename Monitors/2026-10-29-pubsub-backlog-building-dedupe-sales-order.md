---
tags: [datadog-triage]
date: 2026-10-29
monitor: "[FUSE][Platform] Pub/Sub backlog building (any subscription)"
service: dedupe-service
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793291848570189"
opened_at: "2026-10-29T16:36:10Z"
resolved_at: "2026-10-29T16:40:00Z"
minutes_spent: 4
severity_assessed: P3
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: resolved
---
# Pub/Sub backlog Warn on dedupe create_record_request_sales_order sub: 5-minute PURDYFIGG reap burst, not a stall

## Fired
Warn on `dedupe_service.prod.create_record_request_sales_order.v1.sub`, value 252 (warn > 200, crit > 1000, `max(last_15m)` of `num_undelivered_messages`, so any single 1-min sample above 200 in 15m trips it). The monitor API shows `created` 2026-07-04, not today.

## Investigation
- Dedupe sub (1-min max): 0 from 15:55 to 16:20, 200 at 16:21-16:22, 0 at 16:23, 2 at 16:26, 0 16:27-16:35, 252 at 16:36. `oldest_unacked_message_age` was 0-1s throughout. Backlog is a one-minute spike each time, not growing.
- Feed: shopify-connector "Bulk reap completed" for PURDYFIGG every 5 min (16:00 to 16:35). `published` per reap: 488, 583, 674, 770, 871, 932, 1013, 1097, with `skipped` 0, `errored` 0. Dedupe "Incoming record received" for PURDYFIGG per 5 min: 490, 1170, 676, 772, 873, 934, 1015, 1099, matching the reap counts. No other business is bulk-sending (all others under 15 per 5 min).
- Dedupe health: 0 error-level logs 16:00-16:38; every reap POST returned 204; 5 Cloud Run instances steady 16:20-16:34. Forwarded vs dropped (PURDYFIGG, per 5 min): published 89, 682, 107, 110, 120, 76, 105, 92; dropped (`reason: duplicate`) 400, 486, 568, 661, 752, 857, 909, 1006. About 90% of each reap is dropped as duplicate, and the dropped count grows each cycle.
- Downstream snap_adapter `create_record_sales_order.v1.sub` backlog (1-min max): spikes 16:12-16:15 (106, oldest 44-164s), 16:17 (57), 16:22 (35), 16:33 (104, oldest 78s), 0 at 16:35-16:36. Not building at 16:38.
- snap_adapter errors, PURDYFIGG: 33 at 16:12 (earlier burst), then 18 / 36 / 18 at 16:35 / 16:36 / 16:37 (72 total, 61 distinct recordIds). Sampled error: `failureMode: slot_timeout`, "Timed out after 30000ms waiting for a concurrency slot", `deliveryAttempt: 2`, `exhausted: false`. No snap_adapter error logs 16:38:00-16:38:36.
- Snap latency (`snap.poll.request.latency.avg`, 1-min avg): all five hosts spiked 16:36-16:38 (ilg001 17.6s, ilg002 6.6s, ilg003 23.6s, ilg004 21.0s, ilg005 5.8s at 16:36), ilg002/005 down to 1.6s/2.0s by 16:38; ilg001/003/004 baseline 3-8s before the spike and still 10-11s at 16:38.

## Outcome
Not a dedupe stall. Dedupe is draining each burst within the minute. The Warn is the instantaneous queue depth when the 5-minute PURDYFIGG reap pushes about 1100 messages at once. The real, minor impact is the snap_adapter slot_timeout bursts on the same cadence, redelivered rather than lost. Whether the 16:35 burst's orders have been created in Snap is not yet checked.

Not established:
- Why the PURDYFIGG reap republishes its whole, growing set every 5 min (488 to 1097, about 90% duplicates) instead of only new orders.
- Whether Snap slowness or our own 30s slot cap causes the slot timeouts (Fuse MCP 401, no host probe).
- Whether the 61 distinct orders from the 16:35-16:37 burst have been created in Snap.
- Why the monitor API shows `created` 2026-07-04.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793291848570189
- Related: [[2026-10-29-snap-adapter-api-latency-ilg005-ilg002]]
