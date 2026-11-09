---
tags: [datadog-triage]
date: 2026-11-06
monitor: "[FUSE][Platform] Pub/Sub backlog not draining (any subscription)"
service: collector
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793961105888229"
opened_at: "2026-11-06T10:30:38Z"
severity_assessed: P4
flapping: true
outcome: self_resolved
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Backlog not draining (Warn, then Alert at 10:36Z): collector, tracking-service and dedupe sales_order subs Warn at 10:30Z (and dedupe earlier at 10:03Z and 10:14Z): 5-minute duplicate batches, all acked

## Fired
Monitor 323648858 (`change(avg(last_15m),last_1h):avg:gcp.pubsub.subscription.num_undelivered_messages{project_id:bifrost-prod-global1} by {subscription_id} > 200`, warning 75 / critical 200, `requireFullWindow` true, P3, Terraform-managed; `getMonitor`). The "grown by more than 200" text prints the critical threshold; Warn is 75. Events (`search_datadog_events`, 24h): dedupe sub Warn 09:47:38Z (Recovered 09:48:38Z, earlier thread), Warn 10:03:38Z (Recovered 10:07:38Z), Warn 10:14:38Z (Recovered 10:16:38Z), Warn 10:30:38Z; collector and tracking-service subs Warn 10:30:38Z; collector Recovered 10:32:38Z and Warn again 10:34:38Z. Slack parents with no reply at 10:36Z: dedupe 10:04:46Z `1793959486.639409`, dedupe 10:15:47Z `1793960147.951869`, collector 10:31:45Z `1793961105.888229`, dedupe 10:31:47Z `1793961107.828869`, tracking-service 10:31:49Z `1793961109.954809`, collector 10:35:43Z `1793961343.551919`.

## Investigation
Pub/Sub metrics lag about 4 minutes (newest undelivered sample 10:32Z, newest oldest-unacked 10:33Z at 10:36Z).
- Peaks (max undelivered per minute): dedupe 385 at 10:01-10:02, 100 at 10:11-10:12, 77 at 10:17, 329 at 10:27, 581 at 10:32; tracking-service 214 at 10:01, 180 at 09:56, 100 at 10:11, 81 at 10:16, 301 at 10:27, 573 at 10:32; collector 190 at 10:02, 100 at 10:12, 79 at 10:17, 301 at 10:27, 320 at 10:32. Zero in the minutes between batches.
- Drain: max oldest-unacked 10:00-10:33Z: dedupe 6s, tracking-service 5s, collector 3s; all three read 0 at 10:33. Undelivered for 10:33 and later not yet published, so the 10:32 batch drain rests on oldest-unacked 0 at 10:33.
- Errors: push responses 10:00-10:35Z, 16,738 each, all `ack_204` (tracking-service, dedupe) and `ack_201` (collector), no other response code returned. Cloud Run 10:00-10:35Z: collector-prod 2xx 17,263 and 6 4xx (source not found), dedupe-service-prod 2xx 16,756, tracking-service-api-prod 2xx 17,520 and a 5xx series that is 0. Instances flat (8, 5, 2-3), pending queue 0 on all three 10:28-10:32Z. No `dead_letter_message_count` series for the three subs. Logs 10:28-10:36Z: collector_service info only; dedupe_service warn only (all "Record dropped", `reason:duplicate`); tracking-service has 1 info line, no warn or error.
- Cause shared by all three: shopify-connector published 11,274 PURDYFIGG records 10:15-10:36Z, 2,310-2,431 per poll over six polls since 10:10Z; `sent_message_count` batch minutes 10:26: collector 2,284, tracking-service 2,325, dedupe 2,361; 10:31: 2,192, 2,274, 2,365. In dedupe 7,045 records since 10:25Z were dropped as duplicate; the same PURDYFIGG recordIds arrived 13 times in an hour; 110 PURDYFIGG records were published onward.
- Monitor evaluation: not reproduced. A 1-minute reconstruction of change(avg15, 1h) (and a `moving_rollup` formula) gives 25-27 at 10:30Z for all three groups and 41-62 at 10:32Z (dedupe 60.7), against Warn 75, yet the monitor posted Warn at 10:30:38Z and 10:34:38Z. At 10:11-10:12Z the formula peaked at 74.6 for dedupe, just under 75.
- Held: `replay-list-failures` (production): newest overall 09:30:42Z PURDYFIGG goods_out_confirmation (Shopify fulfilment order CLOSED), newest sales_order 2026-11-05T17:20:05Z (WILDSMITH). Nothing held from 10:00Z onwards, nothing is a Snap submission failure.
- Flapping: dedupe group 4 Warn and 3 Recovered in 47 minutes, collector Warn, Recovered, Warn between 10:30 and 10:34Z.

## Alert (critical 200) at 10:36:38Z: tracking-service and dedupe groups
Monitor 323648858 went Alert (not just Warn) for the tracking-service sub (Slack parent `1793961463.575949`, Triggered post 10:37:43Z, Recovered post `1793961522.299509`) and the dedupe sub (`1793961462.007539`, 10:37:42Z) at 10:36:38Z. Events (`search_datadog_events`): tracking Alert 10:36:38Z, Recovered 10:37:38Z (change at most 200); dedupe Alert 10:36:38Z, Recovered 10:38:38Z; collector Warn 10:34:38Z, Recovered 10:38:38Z. `getMonitor` at 10:39Z: thresholds critical 200 / warning 75, `requireFullWindow` true, overall Alert.
- Tracking-service series (per minute max undelivered, 09:00-10:38Z): peaks 25, 41, 171, 32, 180, 214, 100, 81, 301 (10:27), 573 (10:32); 0 at 10:33 to 10:38 and at 10:35-10:36, the minutes of the newest batch. Oldest-unacked 5s at 10:32 (24s at 09:12-09:13 and 09:17-09:18), 0 at 10:33-10:38. Draining: yes, undelivered and oldest-unacked read 0 after each batch.
- Batch sizes (`sent_message_count`, batch minute plus tail minute): 2,297 (10:11-10:12), 2,400 (10:16-10:17), 2,451 (10:21-10:22), 2,433 (10:26-10:27), 2,398 (10:31-10:32), 2,259 (10:35 268 + 10:36 1,991). Acks equal sent in each of those minutes (2,274 / 2,274 at 10:31; 268 and 1,991 at 10:35 and 10:36, plus 78 acks at 10:37); sum 10:00-10:38Z sent 18,997, acked 19,077. Batch size is flat to slightly falling, not growing.
- Push responses 10:30-10:35Z: 4,735 `ack_204` and nothing else for tracking-service (and dedupe, 4,735 `ack_204`; collector `ack_201`); tracking-service-api-prod Cloud Run 2xx 2,496, 5xx series 0.
- Why it evaluated above 200: not reproduced and not explained. A reconstruction of change(avg(last_15m), last_1h) from the stored 1-minute series (no finer points exist: a 10-second request returned 60-second points) gives 58.3 at 10:36Z. That is also the largest value it can take: the 15-minute window 10:22-10:36Z holds only the 301 and 573 samples (sum 874, average 58.3) and the comparison hour 09:22-09:36Z holds 0, so Alert needs the window to sum above 3,000. Sub-lead, untested: a transient sample of about the whole 10:35-10:36 batch (2,259) would give 208.9, but the series shows 0 at 10:35-10:37 and nothing here shows such a sample existed.
- Not the same as 09:47Z: that was Warn (75) on the dedupe group after a 174 peak; this is the 200 critical on a different group, and the stored series cannot reproduce it either.
- Held: `replay-list-failures` production, 32 entries created on 2026-11-06, newest 09:30:42Z PURDYFIGG goods_out_confirmation; nothing from the 10:36Z window.

## Not established
- Why the monitor evaluated above 75 at 10:30:38Z and 10:34:38Z, and above its 200 critical at 10:36:38Z (tracking-service, dedupe), when the stored series gives about 25-62 and at most 58.3; so mistuning is not claimed.
- Why shopify-connector republishes the same PURDYFIGG orders every 5 minutes (publisher logic not read).
- Drain of the 10:32 batch on the undelivered series; state of collector after 10:33Z (lag).
- Source of the 6 collector 4xx responses; Cloud Run concurrency caps.

## Outcome
Self-resolved, P4. Consumers ack every push within seconds (oldest-unacked at most 6s), nothing errors, dead-letters or is held; the Warns follow the 5-minute duplicate batch. The monitor flaps on every batch and, because it latches for an average over 15 minutes, keeps re-posting; why it trips is not established. Pass the PURDYFIGG republish to the shopify-connector owner. Peaks are rising (581 vs 385).

## Links
- Slack threads: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793961105888229, p1793961107828869, p1793961109954809, p1793961343551919, p1793959486639409, p1793960147951869
- Monitor: https://app.datadoghq.com/monitors/323648858
- Related: Monitors/2026-11-06-pubsub-backlog-not-draining-dedupe-create-record-request-sales-order.md, Monitors/2026-11-06-dedupe-backlog-undelivered-warn-create-record-request-sales-order-1028.md
