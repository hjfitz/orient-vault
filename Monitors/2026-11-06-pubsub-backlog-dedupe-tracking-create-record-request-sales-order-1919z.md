---
tags: [datadog-triage]
date: 2026-11-06
monitor: "[FUSE][Dedupe Service] Pub/Sub backlog (undelivered messages) + [FUSE][Platform] Pub/Sub backlog building (any subscription) x2 + [FUSE][Platform] Pub/Sub backlog not draining (any subscription)"
service: dedupe-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793992784332109"
opened_at: "2026-11-06T19:18:38Z"
severity_assessed: P3
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Backlog alerts at 19:18Z on dedupe and tracking create_record_request sales_order subs: drained in about a minute, but the batch also brought 126 rejected pushes and about 6 min of dedupe Mongo heartbeat failures

## Fired
Four alert posts in #bifrost-notifications, none replied to when read at about 19:21Z:
- 302511458 Dedupe Service backlog (warn 200 / crit 1000, max(last_15m)), group `dedupe_service.prod.create_record_request_sales_order.v1.sub`, Warn P3, value 623, ts 1793992784.332109 (post 19:19:44Z).
- 302536090 Platform backlog building, same dedupe group, value 623, ts 1793992767.311169 (19:19:27Z).
- 302536090 Platform backlog building, group `tracking-service.prod.create_record_request.sales_order.v1.sub`, value 446, ts 1793992765.413329 (19:19:25Z).
- 323648858 Platform backlog not draining (trend, `change(avg(last_15m),last_1h) > 200`), P3, status Alert, dedupe group, ts 1793992788.399719 (19:19:48Z). Not in the truncated notification; found in the channel read.

## Investigation
- **Backlog and drain (Pub/Sub metrics, per-minute max):** dedupe undelivered 623 at 19:17, then 0 at 19:18, 19:19, 19:20, 19:21; oldest unacked 4s at 19:17, 0 at every other minute 19:08-19:23. Tracking undelivered 446 at 19:17, then 0 for 19:18-19:21; oldest unacked 0 throughout. A smaller rise followed: dedupe 122 and tracking 104 at 19:22 (last point available; the 19:23 point was not yet published, so whether those drained is not seen). Collector sub max 2, oldest unacked 0. Since 19:10 across all prod subscriptions the only others non-zero were snap_adapter create_record sales_order (2 / 1s) and shopify goods_out_confirmation (1 / 12s). Every `*.dlt.sub` in prod: 0 undelivered.
- **Push responses, dedupe sub (Pub/Sub `push_request_count`):** acked 204 on the bulk of each batch, but 429 (`unreachable_5xx_error_429`) 68 at 19:11 and 51 at 19:12 and 1 at 19:16, and 500 (`remote_server_5xx`) x6 at 19:16. Cloud Run `gcp.run.request_count` agrees: 4xx 79 + 40 at 19:11-19:12, 5xx 6 at 19:15:40. Hourly since 00:00Z the 19:00 hour holds the day's only dedupe-service-prod 4xx (120) and 5xx (6); every earlier hour has none (one non-ack push at 09:00).
- **Push responses, other subs:** tracking sub acked 204 only (2029+57 at 19:11-12, 1968+40 at 19:16-17, 1872+38 at 19:21-22), no 5xx or 429. Collector sub: `webhook_timeout` 427 at 19:11 and 19:19... (427 + 19 over 19:11-19:12), with ack_201 175 and 58 in the following minutes; no timeouts in the 19:16 or 19:21 batches. Collector logs: info only, no error status 19:05-19:22.
- **Errors in consuming services:** error/critical/alert/emergency logs for dedupe_service, tracking_service, collector, snap_adapter, replay_service 19:00-19:23Z: 0. The 6 x 500 and 120 x 4xx have no matching error log in dedupe_service and no Cloud Run request log was indexed for dedupe-service-prod (only Nest start-up lines), so their cause was not found.
- **Batch size and duplicate rate (dedupe_service logs):** incoming / dropped / published per batch: 19:00 2145/2106/39; 19:05 2136/2101/35; 19:10 1967/1946/21 (+119 redelivered at 19:11: 119/111/8); 19:15 2008/1980/28; 19:20 1910/1880/30. Each reconciles exactly (incoming = dropped + published); duplicate rate 97.9-98.5%, no change in batch size or rate.
- **Cloud Run saturation, dedupe-service-prod:** instance_count 4-5 throughout 19:05-19:20, idle 0; CPU p99 peaks 0.69 (19:11) and 0.59 (19:16); memory p99 0.36-0.40; max_request_concurrencies p99 about 42 in the batch minutes. New containers started at 19:10:20Z and 19:15:29Z (startup latency avg about 20s each); the same revision (00053-m72, version 1eeac6f) has been serving since before 18:05Z, no deploy seen in logs.
- **New: dedupe Mongo heartbeat failures.** `fuse.dedupe.mongo.heartbeat_failed` per minute 5, 6, 6, 6, 1, 0, 0 for 19:18-19:24 (first failures at about 19:16:50); `fuse.mongo.up` (min across instances, revision 00053-m72 only) alternating 0/1 from 19:16:50, 0 from about 19:20 to 19:22, back to 1 at 19:23 and 19:24. dedupe_service logged "Dependency degraded, continuing in reduced capacity" (`dependency: mongo`) 116 times 19:16-19:21, alternating with "Dependency connected". Earlier today only 2 single warnings (10:48 and 10:53) and 1 heartbeat failure each at 10:48 and 10:53. Other Mongo users (collector, shopify-connector, replay) reported mongo.up 1 or no data since 18:00 and no degradation. Mongo latency (dedupe) max 295ms avg 15ms over 19:14-19:23. The 19:20 batch ran during the degradation and fully reconciled (1910 = 1880 + 30). Same warning appeared on 2 Nov (37 lines at 19:01-19:03), 3 Nov (40, 19:03-23:14) and 5 Nov (1).
- **tracking-service `store failed`:** none since the 7-line burst at 16:01Z (properly scoped query 11:00-19:24Z: 485 at 11:20, 1 at 11:21, 7 at 16:01). No new burst, no Firestore error check made this run (see Not established).
- **Held records (`replay-list-failures`, production, createdAt 2026-11-06):** total 547 = 542 goods_out_confirmation "Fulfillment order ... is CLOSED in Shopify" (PURDYFIGG, confirmation.delivery_shopify, newest 19:20:44Z; 485 at 18:49Z per the 18:46Z record, so +62) + 5 create-side (sales_order, create.wms_precheck: DOCKBAY, WILDSMITH; newest DOCKBAY UK-913330 18:03:53Z, still attempts 0). pick_confirmation/pack_confirmation: 0. No new create-side hold since 18:03:53Z.
- **Monitor state:** all three monitors managed-by:terraform. `search_datadog_events` for the three monitor ids over 24h returned 0 events (so no flapping history visible by that query).

## Outcome
The backlog itself is the known 5-minute shopify-connector burst (about 2,000 pushes, about 98% duplicates): peak 623/446 at 19:17, drained to 0 by 19:18 with oldest unacked at most 4s, no dead letters, nothing lost (every incoming record accounted for). Not the benign pattern in two respects: dedupe returned 429/500 on 126 pushes at 19:11-19:16 (all later processed; first of the day) and dedupe's Mongo heartbeat failed on at least one instance for about 6 minutes (19:16:50-19:22), cleared by 19:23 with no verified customer impact. P3 real_minor for the dedupe threads; tracking thread self_resolved P4.

## Not established
- Cause of the 429s and 500s (no error log, no Cloud Run request log found). The 429s fall in the minutes a batch arrives with new containers starting, but that was not tested.
- Cause of the dedupe Mongo heartbeat failures, whether one instance or several, and whether it will recur: the metric carries no per-instance tag that I could group on.
- Whether the 19:22 rise (dedupe 122, tracking 104) drained: Pub/Sub undelivered lags and the 19:23 point was not yet in.
- Whether the collector `webhook_timeout` (446 at 19:11-19:12) is new: the history query failed on syntax and was not rerun; no collector-side error found.
- Why monitor 323648858 (trend) fired when the backlog was 0 from 19:18; its evaluated avg values were not pulled.
- Firestore RESOURCE_EXHAUSTED on `tracking-service` this window (not queried; no `store failed` lines seen).
- The 62 new Shopify CLOSED holds were not investigated (separate, already recorded class).

## Links
- Slack threads: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793992784332109 (302511458, primary), p1793992767311169 (302536090 dedupe), p1793992765413329 (302536090 tracking), p1793992788399719 (323648858)
- Monitors: https://app.datadoghq.com/monitors/302511458, /302536090, /323648858
- Earlier backlog records: Monitors/2026-11-06-pubsub-backlog-building-tracking-service-store-failed-1123.md, Monitors/2026-11-06-pubsub-backlog-not-draining-dedupe-create-record-request-sales-order.md
