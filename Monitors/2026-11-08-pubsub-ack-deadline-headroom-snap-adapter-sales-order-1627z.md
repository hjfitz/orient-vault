---
tags: [datadog-triage]
date: 2026-11-08
monitor: "[FUSE][Platform] Pub/Sub ack-deadline headroom eroding (standard subscriptions)"
service: snap-adapter
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794155330085899"
opened_at: "2026-11-08T16:27:39Z"
severity_assessed: P3
flapping: true
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# Ack-deadline Warn on snap_adapter.prod.create_record_sales_order.v1.sub is the knock-on of the 16:20 slot-timeout burst, not a new fault

## Fired
Monitor 323648859 (P3, query alert `max(last_10m)` of gcp.pubsub.subscription.oldest_unacked_message_age, per subscription) went Warn on `snap_adapter.prod.create_record_sales_order.v1.sub` at 16:27:39Z with "unacked message for 130.0s". Datadog's post: C099WKQTE8G 1794155330.085899 (16:28:50Z, no replies when read). Events for this monitor and subscription: Warn 15:52:39Z, Recovered 16:00:39Z, Warn 16:27:39Z. An earlier Warn at 15:43Z is recorded in its own Monitors/ file. Still Warn at 16:32Z; it recovers once the 130 s sample leaves the 10 minute window.

## Investigation
- Subscription metrics (max per minute, 16:15-16:28Z, the latest samples returned at 16:32Z): oldest_unacked_message_age 9 s at 16:17, 40 s at 16:22 and 16:23, 130 s at 16:24, 0 at 16:25 and 16:26, 12 s at 16:27, 0 at 16:28. num_undelivered_messages 3 at 16:17, 76 at 16:22, 77 at 16:23, 5 at 16:24, 0 at 16:25 and 16:26, 29 at 16:27. The 130 s sample at 16:24 equals the 130.0 s the monitor reported. No samples were returned for 16:29-16:35Z yet (metric lag).
- The 16:20 burst is the mechanism: snap_adapter logged 15 slot_timeout failures (PURDYFIGG sales_order, 30000 ms concurrency-slot timeout, 503, 16:20:42Z-16:21:12Z); all 15 were redelivered and created 16:21:54Z-16:22:28Z. See the 16:21 entity-creation record for the full detail. Cloud Run snap-adapter-prod 503 count: 11 at 16:21 + 4 at 16:22.
- Did it recur around 16:25? No slot_timeout and no 429/503: the 16:25 burst logged 69 incoming / 69 created / 0 failed, and the 16:30 burst 74 / 74 / 0. 429: 0 every minute 16:15-16:29Z; 503: 0 at every minute 16:23-16:29Z. The 12 s age and 29 undelivered samples at 16:27 are a short drain of a burst, not a stuck message.
- Every record created: all 15 failed recordIds have a later "Entity created in SNAP" (0 missing); 82 distinct recordIds created in the 16:20 burst. Held: replay-list-failures (production, sales_order, 2026-11-08) total 1, DOCKBAY UK-913950 (ShipAddress.City over 30 chars, 15:02:45Z, unrelated); no PURDYFIGG sales_order held today.
- Snap per host (snap.request.latency.avg / snap.slot_queue_depth max): ilg005 6586 ms / 24 at 16:20, 5126 / 24 at 16:21, 4661 / 14 at 16:22, 3387 / 15 at 16:25, 624 / 24 at 16:30; ilg004 506 ms / 0 at 16:25 and 16:30; ilg003 a flat 4599 ms reading with depth 0; ilg001 no points after 16:06. Depth 24 also appears on clean bursts, so it does not discriminate. Cloud Run snap-adapter-prod instance_count 3 from 15:36Z, unchanged at 16:20.
- Changes: all snap_adapter logs in the last 6h are revision snap-adapter-prod-00099-b4z; no change_tracking events or change stories for snap_adapter in 6h. No Maintenance/ record covers today.
- Flapping: this monitor and subscription went Warn at 15:52:39Z and 16:27:39Z today, each about 6-7 minutes after a slot-timeout burst (15:45Z and 16:20Z).

## Outcome
real_minor, P3: ack-deadline Warn caused by the 16:20Z slot-timeout redeliveries; the oldest unacked message reached 130 s and was acked. Nothing held, nothing left uncreated, no recurrence at 16:25 or 16:30. Same mechanism and same follow-up as the 16:21 entity-creation firing.

Not established: which exact message was the 130 s one; the subscription's ack-deadline and retry-backoff settings (not read); age and undelivered values for 16:29-16:35Z; whether the slot cap or Snap latency is the primary limit.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794155330085899
- Monitor: https://app.datadoghq.com/monitors/323648859
- Related: [[2026-11-08-snap-adapter-entity-creation-failing-1621z]]
