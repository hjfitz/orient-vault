---
tags: [datadog-triage]
date: 2026-10-22
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: tracking-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792685210233929"
opened_at: "2026-10-22T16:05:37Z"
resolved_at: "2026-10-22T16:09:54Z"
minutes_spent: 4
severity_assessed: P4
flapping: false
outcome: self_resolved
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# 16:05Z prod error-rate spike: a 0.3s Firestore Unavailable blip in tracking-service

## Fired
Monitor 180072217 (more than 2 `domain:fuse` prod error logs in 2m) triggered at 16:05:37Z. One further firing of the same cause was folded into this triage.

## Investigation
- Breakdown of the monitor's query from 15:55Z to now:
  - tracking-service, 18 × `store failed; nacking for redelivery`, 16:05:08.806–16:05:09.047Z. All were `create_record_request` sales_order messages, and each carried a Firestore `rpc error: code = Unavailable` (read event / read shipment).
  - snap_adapter PURDYFIGG, 2 × `slot_timeout` at 15:55:50Z (transient).
- Errors since 16:05:10Z: 0.
- Every `tracking-service.prod.*` subscription and its DLT had max num_undelivered of 0 from 15:50Z, apart from a transient 2 on `create_acknowledge.sales_order.v1.sub`. Redelivery succeeded and nothing was dead-lettered.
- Non-transient snap_adapter errors since 15:55Z: 6, all PURDYFIGG #6506667 and #6575295 with `ShipContacts.0.LastName` over 30 characters. These are known holds already with @fuse-support.
- replay_service `Failure stored` since 16:00Z: 4, the same two records (correlations 2270fa82…, d5a868d5…). No new holds.
- Prod replay-service failure listing through the Fuse MCP was unavailable (MCP auth rejected), so the replay_service logs in Datadog were used instead.
- tracking-service error history over 7 days: 2 in the 08:00Z hour today, about 2.5k on 20 Oct (09:00–17:00Z).
- Monitor events over 24h: triggered at 15:11Z, 15:21Z and 16:05Z (different causes). The 15:11Z and 15:21Z firings recovered at 15:13Z and 15:23Z.
- Snap and maintenance: N/A. No Snap host errors are in this spike.
- Not established:
  - The root cause of the Firestore Unavailable.
  - The 16:05Z monitor recovery event, which had not been seen at the time of posting. Query errors had already gone to 0.

## Outcome
Self-resolved, P4. No customer data failed to reach Snap. No ticket was filed and no @fuse-support ping was sent.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792685210233929
- Reply: ts 1792685394.050959
