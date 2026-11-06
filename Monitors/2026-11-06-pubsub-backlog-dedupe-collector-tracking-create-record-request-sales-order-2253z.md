---
tags: [datadog-triage]
date: 2026-11-06
monitor: "[FUSE][Dedupe Service] Pub/Sub backlog (302511458) + [FUSE][Platform] Pub/Sub backlog building (302536090, dedupe/tracking/collector groups) + [FUSE][Platform] Pub/Sub backlog not draining (323648858, dedupe/tracking groups)"
service: dedupe-service
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794005684462839"
opened_at: "2026-11-06T22:53:38Z"
severity_assessed: P4
flapping: true
outcome: self_resolved
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Six Pub/Sub backlog posts at 22:54-22:56Z: the usual 5-minute PURDYFIGG batch peaked at 328 (dedupe), 338 (tracking), 298 (collector), every push acked, oldest-unacked at most 6s, no rejections, no Mongo failures, no errors

## Fired
Shortened re-check. Channel read 22:40Z to 22:58Z, every Datadog alert post, none with a Bifrost Support Bot reply:
- 302536090 Platform backlog building, group collector `create_record_request_sales_order`, Warn, 298, ts 1794005663.462829 (22:54:23Z).
- 302536090 group tracking `create_record_request.sales_order`, Warn, 338, ts 1794005665.152119 (22:54:25Z).
- 302536090 group dedupe `create_record_request_sales_order`, Warn, 328, ts 1794005666.902329 (22:54:26Z).
- 302511458 Dedupe Service backlog (warn 200 / crit 1000, `max(last_15m)`, priority 3), group dedupe sales_order, Warn, 328, ts 1794005684.462839 (22:54:44Z; trigger 22:53:38Z from the alert link event ts 1794005618).
- 323648858 Platform backlog not draining, group dedupe, Warn, ts 1794005802.628169 (22:56:42Z; event ts 1794005738 = 22:55:38Z).
- 323648858 group tracking, Warn, ts 1794005804.782659 (22:56:44Z).
No Recovered posts in the window. Monitor state at 22:57Z (`search_datadog_monitors`): 302511458 Warn, 302536090 Warn (group-level), 323648858 Warn; all `managed-by:terraform`. 323648858 is `change(avg(last_15m),last_1h) > 200` per its definition; its alert text for today's earlier posts shows a 75 Warn line ("was > 75.0 compared to 1h ago").

## Investigation
Pub/Sub points checked at 22:59Z; metrics lag was 1 to 6 minutes during this run.
- **Peaks and drain (per-minute max, `num_undelivered_messages` / `oldest_unacked_message_age`, one query per subscription):**
  - 22:36-22:37: all three at 101, oldest-unacked 0.
  - 22:51: collector 298 (oldest 0). 22:52: dedupe 328, tracking 338 (oldest-unacked 1s on both), collector 0. All 0 from 22:53 to 22:56.
  - 22:56: collector 273. 22:57: dedupe 257, tracking 314 (oldest-unacked 6s on dedupe, 1s on tracking, 0 on collector). Oldest-unacked 0 on all three at 22:58, so each spike drained within about a minute. The undelivered value for 22:58 was not yet published.
  - So the three peaks that fired the alerts (298/328/338) are at 22:51-22:52, and a second similar spike (273/257/314) followed at 22:56-22:57. The 22:41 and 22:46 batches left all three at 0.
- **Push responses (`push_request_count` by `response_class`, three subs):** only the `ack` class exists for 22:30-22:58 on every sub; no non-ack series. Per-minute acks for the three subs combined: 1,730 at 22:56 and 13 at 22:57.
- **Cloud Run non-2xx:** dedupe-service-prod 0 non-2xx in 22:30-22:58 (the 503 series averages 0). collector-prod: 4 x 404 in 22:30-22:55 (`gcp.run.request_count`, avg 0.16 a minute); tracking-service-api-prod none. The collector 404s are not push responses (no non-ack push class), and no collector or tracking warn/error/404 log line exists (`search_datadog_logs` patterns: 0).
- **Cloud Run saturation:** dedupe-service-prod 5 active, 0 idle instances at every minute 22:30-22:55 (no new containers); CPU p99 at most 0.19, memory p99 0.41, concurrency p99 about 42 in 22:47-22:51 and 1.99 afterwards, request latency p99 at most 796ms (22:45-22:55). collector-prod 6-8 active, CPU p99 0.53 at 22:46 then at most 0.25, concurrency p99 84.9 at 22:47 and 22:51 (the 22:47 batch did not back up). tracking-service-api-prod CPU p99 at most 0.09, concurrency p99 at most 10, active instances 0-3 (3 at 22:51).
- **Dedupe errors and Mongo:** no error-level logs for dedupe_service 22:30-22:58 (0 rows). Warn/error logs for dedupe, tracking, collector, snap_adapter, replay and shopify-connector 22:30-22:58: only warn, dedupe_service "Record dropped" 3,659 and shopify-connector 208; no error, critical, alert or emergency. No "Dependency degraded" line. `fuse.dedupe.mongo.heartbeat_failed` has data points at 19:15-20:00 (5-minute sums 18, 13, 0, 20, 11, 0, 22, 30, 29, 2) and none after; `fuse.mongo.up` for dedupe is 1 at every minute 22:30-22:55. So the 19:16-20:00 Mongo failures and the 429/503 rejections (20:02, 20:36) have not recurred.
- **Dead letters:** all 22 prod `*.dlt.sub` subscriptions average 0 undelivered over 22:30-22:56.
- **Every other prod subscription 22:30-22:56:** only the three sales_order subs are above 0 (the others are 0 on both undelivered and oldest-unacked).
- **Batch size and duplicate rate (dedupe_service logs, PURDYFIGG, incoming = "Incoming record received", dropped = "Record dropped", per 5-minute bucket):** 22:30 648/642 (99.1% dropped); 22:35 625/610 (97.6%); 22:40 604/596 (98.7%); 22:45 589/577 (98.0%); 22:50 573/559 (97.6%); 22:55 559/552 (98.7%, partial). Whole window by business: PURDYFIGG 3,598 incoming / 3,536 dropped; ESCENTRICPL 60/60; SAIRA 38/37; ESCENTRIC 27/26; STUBBLE 4, EPARFUM 2, PHLUR 1 (incoming only). Batches are smaller than the 1,180-1,590 of 20:00-20:40 and the spikes are not smaller (328 now vs 209 at 20:38).
- **Held records (`replay-list-failures`, production, createdAt 2026-11-06):** all types, newest first: newest is a PURDYFIGG goods_out_confirmation at 21:48:45Z (Shopify fulfilment order CLOSED), so nothing new since 22:30Z; total 1,766 for the day. sales_order/purchase_order/master_data: 6 total, newest still PURDYFIGG #6679913 (19:55:23Z, already known). No new hold, none lost on this path.
- **Why 323648858 fired:** a reconstruction from the 1-minute average series gives change(avg15, 1h) of about 22 at 22:52-22:55 (328/15 with 0 an hour earlier), under its 75 Warn line, the same non-reproduction noted in earlier records today. Mechanism not established.
- **Flapping:** the first Slack search page for "Pub/Sub backlog" in #bifrost-notifications on 6 Nov returned 20 earlier posts (09:48-20:54Z) from the same monitor family on these subscriptions, so this is a chronic flapper.

## Outcome
Self-resolved, P4. The same 5-minute PURDYFIGG duplicate batch backed three subscriptions up to about 300 undelivered for about a minute, twice (22:51-22:52 and 22:56-22:57). Every push acked, oldest-unacked at most 6s and 0 afterwards, dead letters 0, no error logs, no rejected pushes or Mongo heartbeat failures since 20:36Z / 20:00Z, no new held record. Not the 20:38Z pattern (no 429/503, no Mongo failures). The monitors keep re-firing on these drained spikes, so the Warn lines (200 and a 15-minute-average change) are tuned below normal batch spikes.

## Not established
- Why the 22:51 and 22:56 batches spiked to about 300 while the 22:41 and 22:46 batches left the subscriptions at 0, with batch size shrinking (no saturation, new container or error found on dedupe; tracking scaled 0 to 3 instances at 22:51 but not tested as a cause).
- The undelivered value for 22:58 onward (drain rests on oldest-unacked 0 at 22:58; Cloud Run saturation for the 22:56 batch not pulled).
- Why 323648858 evaluated above 75 (reconstruction about 22).
- Cause of the 4 collector 404s (no log line indexed).
- Cause of the earlier dedupe 429/503 and Mongo heartbeat failures (none recurred, none explained).
- Why shopify-connector republishes the same PURDYFIGG orders, and the shopify confirmation-delivery duplicate hypothesis (not examined here).

## Links
- Slack threads: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794005684462839 (302511458, primary), p1794005666902329, p1794005665152119, p1794005663462829 (302536090), p1794005802628169, p1794005804782659 (323648858)
- Monitors: https://app.datadoghq.com/monitors/302511458, /302536090, /323648858
- Earlier records: Monitors/2026-11-06-pubsub-backlog-dedupe-create-record-request-sales-order-2038z.md, Monitors/2026-11-06-pubsub-backlog-collector-create-record-request-sales-order-2053z.md
