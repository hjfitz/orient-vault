---
tags: [datadog-triage]
date: 2026-11-07
monitor: "[FUSE][Dedupe Service] Pub/Sub backlog (undelivered messages) + [FUSE][Platform] Pub/Sub backlog building (any subscription) x3 + [FUSE][Platform] Pub/Sub backlog not draining (any subscription) x2"
service: dedupe-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794069226183229"
opened_at: "2026-11-07T16:32:38Z"
resolved_at: "2026-11-07T16:33:00Z"
severity_assessed: P4
flapping: true
outcome: self_resolved
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# Backlog alerts at 16:32Z on dedupe, tracking and collector create_record_request sales_order subs: the day's highest peak (723) but drained within seconds, no rejected pushes, no holds

## Fired
Six alert posts in #bifrost-notifications between 16:33:46Z and 16:35:49Z, none replied to when read at about 16:38Z (the Snap poller latency post for ilg001, ts 1794068902.602479, already has a Bifrost Support Bot reply and is excluded):
- 302511458 Dedupe Service backlog (warning 200 / critical 1000, `max(last_15m)`), dedupe group, Warn, value 723, ts 1794069226.183229 (monitor group triggered 16:32:38Z).
- 302536090 Platform backlog building (warning 200 / critical 1000), Warn: dedupe 723 ts 1794069270.400219; collector 643 ts 1794069268.272389; tracking 737 ts 1794069265.685939 (group triggered 16:33:10Z).
- 323648858 Platform backlog not draining (trend, `change(avg(last_15m),last_1h)`, warning 75 / critical 200), tracking group only: Warn ts 1794069288.750359 (16:34:38Z) then Triggered ts 1794069349.149689 (16:35:49Z). Monitor state read via API at about 16:38Z: Alert for the tracking group.

## Investigation
- **Backlog and drain (Pub/Sub, per-minute max, metric stamped about 1 min after the burst and lagging about 4-5 min):** dedupe undelivered 135 (16:16), 107 (16:21), 106 (16:26), 723 (16:31), then 0 at 16:32-16:35, 9 at 16:36 (next batch), 0 at 16:37. Tracking 131, 107, 106, 737 (16:31 and 16:32), 0 from 16:33, then 42 at 16:36-16:37 (last point available). Collector 106, 107, 106, 643 (16:31), 0 at 16:32 (last point). Oldest unacked: dedupe max 1 s, tracking max 1 s, collector 0, 16:15-16:33. Over the 24h from 16:00Z on 6 Nov: dedupe max 723, tracking max 737, collector max 643, all at 16:31 today (previous high 623 at 19:17Z on 6 Nov); oldest unacked over that 24h max 27 s dedupe, 5 s tracking, 11 s collector.
- **Burst shape (dedupe_service logs, "Incoming record received" min/max timestamp):** 16:15:02-16:15:15, 16:20:03-16:20:36, 16:25:03-16:25:14, 16:30:03-16:30:16, 16:35:02 onwards. The 16:30 batch: 1282 received in 13 s, 1202 "Record dropped" + 80 "Record published to topic" = 1282.
- **Batch size and duplicate rate, dedupe:** acks 1035 / 1138 / 1217 / 1282 for the four batches, about 1377 received for the 16:35 batch (1263 dropped + 114 published). Dropped / published: 965/70, 1023/115, 1124/93, 1202/80, 1263/114; duplicates 93.2%, 89.9%, 92.4%, 93.8%, 91.7%. Each reconciles with acks. Batch size is rising about 5-8% per batch; the 723 peak is not explained by size (the 16:35 batch is larger and peaked 9 / 42).
- **Push responses:** `push_request_count` for the three subs shows only ack classes (dedupe ack_204 1035/1137+1/1217/1282, tracking ack_204 1022+13/1132+6/1207+10/1256+26, collector ack_201 1035/1135+3/1217/1282); no 429, 4xx, 5xx or nack series. `nack_requests` for dedupe: no series. Cloud Run `request_count` 16:10-16:34: dedupe-service 2xx only (978, 1031, 1133, 1212, 1278 per batch); tracking-service 2xx only, zero 4xx/5xx; collector 2xx only plus one 4xx at 16:10 and one at 16:24 (outside the batch minutes).
- **Errors and Mongo (dedupe):** `fuse.dedupe.mongo.heartbeat_failed` returned no series 16:15-16:37 (none emitted); `fuse.mongo.up` min 1 every minute 16:15-16:37; `fuse.mongo.latency.max` dedupe 167-299 ms in 16:15-16:35 buckets (473.5 at 16:10). Error/critical/alert/emergency logs for dedupe_service, tracking, collector, snap_adapter: 0 from 16:15; the only warns are dedupe "Record dropped" (about 5,580) and 1 replay_service warn. Pattern search for status error, 4xx/5xx, heartbeat, timeout, ECONN across dedupe, tracking, collector: 0 logs.
- **Cloud Run saturation:** dedupe-service 5 active instances constant, CPU p95 0.15-0.24, memory p95 0.35-0.36, max concurrency avg up to 34, request latency p95 545 ms at 16:31 (96-833 ms across the window), no container-start samples. Collector 6 instances, 7-8 in batch minutes, with 1-2 container starts per batch; CPU p95 0.12-0.22. Tracking-service 1 instance, 3 in batch minutes; no start samples.
- **Tracking and collector throughput (5-min buckets, not reconciled to acks):** tracking events ingested 531/666/619/615/675, duplicate_folded 339/377/403/396/415; collector `fuse.records.collected` 1025/1123/1206/1270/1361 (matches batch growth), `records_persisted` 575/664/663/535/744.
- **Dead letters:** all 24 prod `*dlt*` subscriptions (tracking-service, audit-service, create_sftp_user) 0 undelivered and 0 oldest unacked at every point 16:15-16:32. Dedupe and collector have no `*dlt*` subscription in that list.
- **Held records:** `replay-list-failures` production. Newest across sales_order / purchase_order / master_data / pick / pack is sales_order DOCKBAY 13:03:14Z (create.wms_precheck, City over 30 characters), 0 since 16:00Z; `createdAt` 2026-11-07 for sales_order returns only that one. Since 16:00Z the only new holds are goods_out_confirmation: `fuse.replay.record_persisted` 38, 18, 19, 19, 22 in the 16:10-16:35 5-min buckets (116 total, 16:35 bucket partial); the newest 20 (16:34:38-16:36:22Z) are all PURDYFIGG "Fulfillment order ... is CLOSED in Shopify", confirmation.delivery_shopify, attempts 0. That is the already-recorded Shopify CLOSED class on the confirmation side.
- **Snap side (5-min buckets, 16:00-16:35):** `snap.poll.request.latency.avg` 2.1-3.3 s at 16:00 on all five hosts, 1.0-2.1 s at 16:20 and 2.8-3.0 s at 16:25, otherwise 64-155 ms (16:30 bucket 64-155 ms). ilg005 create path: `snap.request.success` 137-245 per bucket, `snap.request.latency.avg` 676-3001 ms, max 5.9 s (16:00 and 16:20), `snap.slot_queue_depth` 8.2-19.0, rate queue 0; `snap.request.failure` returned no series; `snap.breaker.state` 0 for ilg001-005. The 71 s create seen at 14:50Z does not recur in this window (max 5.9 s). dedupe-service's listed responsibilities contain no Snap call (lookup-service).
- **Monitors:** all three managed-by:terraform. The 5-min burst puts the per-minute gauge over 200 only when a sample lands inside the 13 s burst: dedupe over 200 at 12:17 (370), 12:27 (217), 15:36 (204), 16:31 (723) today; tracking at 12:16 (429), 12:26, 12:31, 12:36, 15:36, 15:37, 16:31/16:32. The vault holds many Monitors/ records on the same monitors on 6 Nov. `search_datadog_events` over 24h for the three ids returned 0 events.

## Outcome
Self-resolved P4. The 5-minute shopify-connector burst reached its highest per-minute undelivered value in 24h (723 dedupe, 737 tracking, 643 collector) but dedupe finished all 1282 messages in 13 s, tracking was at 0 by 16:33, oldest unacked stayed at or below 1 s, every push was acked, no dead letters, no new sales_order hold. None of the P1/P2 triggers (oldest unacked in minutes, rejected pushes, held sales_order, dead-lettering) is met or approaching. The trend monitor 323648858 is the only one still in Alert at about 16:38Z and should clear as its 15-minute window slides.

## Not established
- Why the 16:31 sample was 723 when the previous four batches sampled 106-135 and the 16:35 batch sampled 9/42: batch size changed only 5-8%. Sampling phase against a 13 s burst is a lead, not tested.
- Whether tracking and collector drained as fast as dedupe: tracking drain is seen (0 at 16:33), collector only to 0 at 16:32; per-batch duplicate rate for tracking and collector is not reconciled to the acks.
- Whether the 16:35-16:36 batch drained: the metric lags about 4-5 min (tracking 42 at 16:37 was the last point).
- Why 323648858 evaluated above 200 for tracking: my scalar average of 16:19-16:34 is 126.7 against 0.9 an hour earlier, below 200, so the evaluated value was not reproduced.
- Why `fuse.dedupe.event.handled` (327 in the 16:15 bucket) is lower than the acks (1035): the metric appears not to count every push.
- Cause of the PURDYFIGG goods_out_confirmation holds (not investigated; separate class).
- Whether dedupe or collector have dead-letter subscriptions outside the `*dlt*` naming.

## Links
- Slack threads: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794069226183229 (302511458 primary), p1794069270400219 (302536090 dedupe), p1794069268272389 (302536090 collector), p1794069265685939 (302536090 tracking), p1794069288750359 and p1794069349149689 (323648858 tracking)
- Monitors: https://app.datadoghq.com/monitors/302511458, /302536090, /323648858
- Earlier: Monitors/2026-11-06-pubsub-backlog-dedupe-tracking-create-record-request-sales-order-1919z.md, Monitors/2026-11-07-snap-poller-api-latency-all-hosts-0429z.md
