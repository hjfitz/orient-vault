---
tags: [datadog-triage]
date: 2026-11-09
monitor: "[FUSE][Platform] Pub/Sub ack-deadline headroom eroding (standard subscriptions)"
service: snap-adapter
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794237907288869"
opened_at: "2026-11-09T15:23:39Z"
severity_assessed: P4
flapping: true
outcome: self_resolved
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# Ack-deadline Warn (99 s) on snap_adapter sales-order subscription: 3 slot_timeout 503s during an ilg005 slow spell, all redelivered, nothing held

## Fired
Monitor 323648859 (`max(last_10m)` of oldest_unacked_message_age by subscription, Warn 90 s, Critical 180 s, managed-by:terraform, P3) went Warn on `snap_adapter.prod.create_record_sales_order.v1.sub` at 15:23:39Z with 99.0 s (Slack post 15:25:07Z, C099WKQTE8G 1794237907.288869, no replies when read). Datadog event Recovered 15:33:39Z at 13.0 s. Related: error-rate monitor 180072217 Triggered 15:22:46Z (another agent triages it).

## Investigation
- Metric (gcp.pubsub oldest_unacked_message_age, max per minute, 14:00-16:10Z): 99 s at 15:23 only; other minutes at or above 20 s: 22 (14:02), 25 (14:47), 41 (15:04, 15:05), 34 (15:17), 27 (15:21), 39 (15:22). num_undelivered_messages 0-6 at the 5-minute samples, 16 at 15:31, 0 at 15:36.
- snap_adapter prod error logs 15:00-16:10Z: 4 total. One ESCENTRIC schema_validation at 15:03:00Z (transient:false, "Unable to parse data"; held in replay-service as 74fa40a1..., recordId 15337, "ShipContacts.Phone - Too big: expected string to have <=20 characters", failurePoint create.wms_precheck, attempts 0). Three slot_timeout at 15:20:41Z (ESCENTRIC), 15:20:58Z and 15:21:06Z (PURDYFIGG), all sales_order, transient:true, deliveryAttempt 1, "Timed out after 30000ms waiting for a concurrency slot". Each of the three messageIds logged "Incoming record received" with deliveryAttempt 2 at 15:20:53, 15:21:12 and 15:21:20Z and no later error.
- snap_adapter 15:18-15:50Z: 297 "Incoming record received", 294 "Entity created in SNAP", 3 "Entity creation in SNAP failed", 3 x 503 on POST create/sales_order. No explicit per-messageId success log was found for the three redeliveries, so completion is inferred from 297 = 294 + 3.
- Replay-service (production): newest PURDYFIGG held failures are goods_out_confirmation delivery_shopify entries from 13:25Z; none are sales_order create failures from 15:20Z. ESCENTRIC's newest is the 15:03Z record above.
- Snap ilg005 (snap.request.latency.avg, environment:prod, by snap_host, ms): 3,891 (15:10), 7,266 (15:15), 7,423 (15:19), 8,541 (15:20), 7,015 (15:21), 4,686 (15:22), 4,129 (15:23), 4,212 (15:25), 2,202 (15:27), 875 (15:30), 1,025 (15:35), 3,300 (15:36), 2,131 (15:40). Max 9,693 ms at 15:20. slot_queue_depth (max) 10.9 at 15:19, 16 at 15:20-15:21, 15.1-15.5 at 15:22-15:25, 7.1 at 15:27, 17.3 at 15:30, 19.2 at 15:35, 1 at 15:36, 18 at 15:40. Other hosts: ilg001 no points 15:10-15:40, ilg003 one point (541 ms avg, 1,235 ms max at 15:40).
- Arrivals (snap.messages.received, sales_order, per minute): 9 (15:10), 6 (15:15), 1 (15:19), 23 (15:20), 3 (15:21), 2 (15:22), 1 (15:23), 7 (15:25), 30 (15:30), 103 (15:35), 36 (15:40).
- ilg005 hourly adapter-side latency avg: 1,261-4,206 ms for every hour from 8 Nov 15Z to 9 Nov 14Z, 4,614 ms in the 15Z hour (max 8,193). Daily avg: 2 Nov 2,689; 3-6 Nov 726-990; 7 Nov 2,436; 8 Nov 2,324; 9 Nov 3,025 (max 9,027). The Fuse MCP lookup-service note for snap-adapter gives healthy latency as about 0.5-1 s.
- slot_timeout logs since 2 Nov: PURDYFIGG 310, DOCKBAY 21, SPORTLUX 21, ESCENTRIC 2.
- Monitor 323648859 events (13 of 20 in 7 days read, all this subscription): Warn 8 Nov 15:43Z, 15:52Z, 16:27Z, 16:48Z; 9 Nov 08:23Z and 15:23Z; each Recovered within 6-11 min. Earlier today the Recovered post at 08:34:02Z and Warn post 08:24:45Z were read in the channel.
- Related monitor 180072217: query is `@domain:fuse status:error @environment:prod` excluding snap_adapter `@transient:false` and three other filters, `last(2m) > 2`. Matching lines 15:15-15:40Z: the three snap_adapter slot_timeout lines (15:20:41, 15:20:58, 15:21:06Z) and three config-service lines at 15:37-15:39Z (after the trigger, not examined).
- Snap probe: one read-only snap-lookup RECSTATUS against ilg005 with PURDYFIGG's connection returned 6 rows. The tool reports no timing.
- Maintenance: no Maintenance/ record covers 9 Nov (latest windows 3 Nov 10:00-10:30Z and the 4 Nov files). Snap latency monitor 179927768 is silenced per snap_host group until 1794306159 (about 10 Nov 10:22Z), so it does not show this.
- Prod snap-adapter deploys in channel today: 10:52Z (snap-queue-polling-service) and 11:14Z (snap-adapter, commit 8b2e5af); nothing between 11:14Z and 15:25Z.

## Outcome
self_resolved, P4. A burst on ilg005 at 15:20Z (23 sales_order messages in the minute, adapter-side latency avg 7-8.5 s, queue depth 16) made three requests wait out the adapter's 30 s slot limit; they returned 503, were redelivered 12-14 s later, and nothing is held from them. Age recovered by 15:33Z. Flapping: 6 Warns on this subscription in about 24 h. ilg005 latency has been 2.3-3.0 s on average since 7 Nov against 0.7-1.0 s on 3-6 Nov.

Not established: which message was the 99 s oldest; whether ilg005 slowness or the adapter's own concurrency cap was the bottleneck (the latency metric may or may not include slot wait); the probe's response time; the three redeliveries' individual success logs; whether the 15:35 burst (103 messages) had any delay (no errors logged); ILG mail and the #bifrost-general maintenance pin; the 15:37-15:39Z config-service errors; the 7 events of the 20 not read.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794237907288869
- Monitor: https://app.datadoghq.com/monitors/323648859
- Related: 180072217 (error rate, 15:22:46Z), [[2026-11-09-pubsub-backlog-snap-adapter-sales-order-0823z]]
