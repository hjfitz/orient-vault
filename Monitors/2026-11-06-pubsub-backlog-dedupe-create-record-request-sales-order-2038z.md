---
tags: [datadog-triage]
date: 2026-11-06
monitor: "[FUSE][Dedupe Service] Pub/Sub backlog (undelivered messages) + [FUSE][Platform] Pub/Sub backlog building (any subscription), dedupe group"
service: dedupe-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793997585089329"
opened_at: "2026-11-06T20:38:38Z"
severity_assessed: P3
flapping: true
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Dedupe sales_order sub Warn again at 20:38Z (peak 209, oldest unacked 20s, drained within 2 minutes), with 34 rejected pushes since 20:00Z and Mongo heartbeat failures that ran on until 20:00Z

## Fired
Two new alert posts in #bifrost-notifications, neither with a reply at about 20:44Z:
- 302511458 Dedupe Service backlog (warn 200 / crit 1000, `max(last_15m)`), group `dedupe_service.prod.create_record_request_sales_order.v1.sub`, Warn P3, value 209, ts 1793997585.089329 (post 20:39:45Z).
- 302536090 Platform backlog building, same group, value 209, ts 1793997568.432559 (post 20:39:28Z).
Channel read 20:18Z to 20:44Z (all Datadog alert posts): 303425509 Shopify confirmation delivery failing, Warn, 1793996283.726359, Bot reply 20:22:38Z; 180072217 Elevated production error rate, Triggered, 1793996329.016919, Bot reply 20:22:41Z; the two above (no reply); 303425509 Recovered 20:33:03Z (ignored). The 19:40Z tracking not-draining thread (1793994044.217229) also carries a reply at 20:22:57Z.

## Investigation
Pub/Sub metrics lag about 4-5 minutes; points below are the newest real ones (queried with fill(null) at 20:45Z).
- **Backlog and drain (per-minute max, dedupe sub):** undelivered 0 for 20:00-20:42 except 51 at 20:12 and 209 at 20:37 and 20:38; oldest unacked 0 except 2s at 20:12 and 20s at 20:37 and 20:38. 0 and 0 at every point 20:39-20:42/43, so it drained. The 209 peak is 9 above the warn line and a fifth of the 1000 critical. Tracking sub undelivered 0 at every point 20:00-20:42, oldest unacked 0.
- **Rest of prod subscriptions 20:00-20:42:** the only other non-zero undelivered were small (snap_adapter create_record sales_order up to 16 with oldest 12s; collector create_record_request sales_order 23 with oldest 1s; a few of 1-5 elsewhere). Every prod `*.dlt.sub` (22 listed): 0 throughout.
- **Push responses, dedupe sub (`push_request_count`):** every push acked 204 except 429 (`unreachable_5xx_error_429`) x33 at 20:02 and 503 (`unreachable_5xx_error_503`) x1 at 20:36. Cloud Run `gcp.run.request_count` agrees (4xx 33 at 20:02, 5xx 1 at 20:36; no other 4xx/5xx 20:00-20:40). The 20:40 batch acked 1077 + 46 with no non-ack. The 20:36 minute also saw the oldest-unacked rise to 20s at 20:37-20:38; the link between the 503 and the 20s age was not tested.
- **Other subs' non-acks:** none on tracking or collector since 20:00 (collector `webhook_timeout` has not recurred). shopify-connector goods_out_confirmation sub has 1 `webhook_timeout` about every 2-6 minutes (20:05-20:37), a different subscription.
- **Errors:** error/critical/alert/emergency logs for dedupe_service, tracking_service, collector, snap_adapter, replay_service, shopify-connector 20:00-20:44Z: 4, all shopify-connector at 20:16 (the PURDYFIGG Shopify line-item error already answered in thread 1793996329.016919). dedupe_service logs only two warn patterns 19:24-20:40: "Record dropped" and "Dependency degraded, continuing in reduced capacity"; no error level. No Cloud Run request log for the 429s/503 is indexed (search for 429/503/"no available instance" returned 0), so their cause was not found.
- **Batch size and duplicate rate (dedupe_service logs, per 5-minute batch, incoming = dropped + published):** 20:00 1558=1533+25; 20:05 1594=1567+27; 20:10 1592=1568+24; 20:15 1593=1564+29; 20:20 1575=1549+26; 20:25 1512=1492+20; 20:30 1422=1404+18; 20:35 1180=1159+21; 20:40 (partial, to 20:40:20Z) 1123=1104+19. All reconcile exactly. Duplicate rate 98.0-98.7%. Batches shrank from about 1,590 (20:05-20:20) to 1,180 (20:35).
- **Cloud Run saturation, dedupe-service-prod:** active instances 3-7 (3 at 20:24-25 and 20:36, 7 at 20:16), idle 0; request concurrency p99 about 42 in every batch minute (20:01-20:02, 20:16-20:22, 20:26-20:37) incl. batches with no rejects; memory p99 0.35-0.39; CPU p99 max 0.45 (20:16, 20:26); request latency p99 up to 1985ms at 20:01. New containers started at 20:01, 20:02, 20:11, 20:16, 20:26, 20:36 (startup latency 10-21s). The 429s (20:02) and 503 (20:36) fall in minutes with a new container starting, but 20:11, 20:16 and 20:26 started containers with no rejects. Same revision version 1eeac6f throughout; no deploy.
- **Dedupe Mongo heartbeat, recurrence:** the 19:16-19:22 failures recurred. `fuse.dedupe.mongo.heartbeat_failed` per minute: 19:22 1, then 0; 19:31-19:36 3,5,6,6,6,5; 19:46-20:00 4, 6 (x9), 5, 6,6,6, 2; 0 from 20:01 to 20:44 (no failure points). `fuse.mongo.up` (min over dedupe) 0.67-0.83 during those windows, 1 at every minute 20:00-20:40. "Dependency degraded" log lines: 674 from 19:16:44Z to 20:00:19Z (minutes 19:31-19:36, 19:46-20:00 after the first window), none since. During 19:10-20:45 collector, replay and shopify-connector `fuse.mongo.up` read 1 wherever they reported (dedupe was the only service below 1). No Mongo error text found in dedupe logs (search for heartbeat/MongoServerSelectionError/ECONNRESET/timed out: 0). Degradation windows carried batches (19:35, 19:50, 19:55, 20:00) that all reconciled.
- **Held records (`replay-list-failures`, production, createdAt 2026-11-06):** filtered to sales_order, purchase_order and master_data (pick/pack and confirmation types not re-listed this run), 6 total: DOCKBAY x3 and WILDSMITH x1 and SAIRA x1 (all before 19:00Z, already known) and one new, PURDYFIGG `#6679913` (id aeade1c6-9672-43a2-a861-de63b8614763), created 19:55:23Z, `create.snap_api` from snap-adapter, "Line1 - Invalid Text on line SHB5VWSRFS", error code `snap-adapter.sales_order.snap_api_error.Line1`, retryable false, attempts 0, replayable true. The record's address line1 is "247 |Beckfield Lane" (contains a pipe). That is a Snap validation rejection returned to snap-adapter; no link to the dedupe events was found. Not in any earlier Monitors/ or Support/ record (grep). No new hold from the dedupe path (the record passed dedupe: batch counts reconcile).
- **Monitor state:** 302511458 posts today: Warn 10:04, 10:29, 19:19, Recovered 19:58, Warn 20:39 (channel); `search_datadog_events` for the monitor over 24h returns 0 events, so flapping is from Slack posts only. All monitors Terraform-managed (noted in the 19:19Z record).

## Outcome
Real but minor, P3. Same 5-minute shopify-connector duplicate batch (about 98% duplicates), peak 209, drained by 20:39 with every record accounted for and no dead letters, no error-level logs. Not the clean pattern in three respects: 34 pushes rejected (33 x 429 at 20:02, 1 x 503 at 20:36), oldest unacked reached 20s (vs 4s at 19:17), and dedupe's Mongo heartbeat failures did recur (19:31-19:36, 19:46-20:00, about 44 minutes in all since 19:16:44Z) before stopping at 20:00Z with no failures in 40 minutes since. The one new held record (PURDYFIGG #6679913) is a Snap validation rejection, not caused by this.

## Not established
- Cause of the 429s and 503 (no request log indexed; correlation with new containers is partial).
- Cause of the dedupe Mongo heartbeat failures, why they stopped at 20:00Z, and whether they will recur (no Mongo error text, no per-instance tag on the metric).
- Whether the 503 at 20:36 explains the 20s oldest-unacked (not tested).
- Whether the pipe in PURDYFIGG #6679913's address line1 is what Snap rejected; Snap's own validation rule not checked.
- Why batches shrank from about 1,590 to 1,180 messages (publisher not examined).

## Links
- Slack threads: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793997585089329 (302511458, primary), p1793997568432559 (302536090 dedupe)
- Monitors: https://app.datadoghq.com/monitors/302511458, /302536090
- Earlier records: Monitors/2026-11-06-pubsub-backlog-dedupe-tracking-create-record-request-sales-order-1919z.md, Monitors/2026-11-06-pubsub-backlog-building-collector-tracking-dedupe-create-record-request-sales-order-1028.md
