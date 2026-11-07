---
tags: [datadog-triage]
date: 2026-11-07
monitor: "[FUSE][Dedupe Service] Silent publish drop (handled minus outcomes)"
service: dedupe-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794074513024329"
opened_at: "2026-11-07T18:00:36Z"
severity_assessed: P4
flapping: false
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Dedupe "silent publish drop" Warn at 18:00Z (7 Nov): shortened re-check, every incoming record accounted for

## Fired
Monitor 302511456 (P2, managed-by:terraform, `sum(last_1h)` handled minus outcomes, threshold above 50) went Warn at 18:00:36Z. Alert post in #bifrost-notifications at 18:01:53Z (ts 1794074513.024329), no replies when read (slack_read_thread, about 18:04Z). Shortened re-check of a cause already triaged on 4 and 6 Nov.

## Investigation
- dedupe_service logs (@environment:prod), 17:30:00Z to 18:03:00Z (aggregate re-run after ingestion settled): "Incoming record received" 11,677 = "Record dropped" 11,585 (all `@reason:duplicate`) + "Record published to topic" 92 + "Dedupe gate held" 0. Unaccounted 0. Each 5-minute bucket reconciles (17:30 1,732 = 1,725 + 7; 17:35 1,727 = 1,711 + 16; 17:40 1,697 = 1,689 + 8; 17:45 1,670 = 1,662 + 8; 17:50 1,635 = 1,621 + 14; 17:55 1,616 = 1,602 + 14; 18:00 to 18:03 1,600 = 1,575 + 25).
- Per record, 17:30:00Z to 18:00:00Z (key businessId|recordId|correlationId, listLogs): incoming 10,077 = drops 10,010 + published 67 + held 0; 10,077 distinct keys, 0 keys where incoming differs from outcomes, 0 outcome keys without an incoming log.
- By business, incoming 11,544+: PURDYFIGG 11,544, ESCENTRIC 63, ESCENTRICPL 34, DOCKBAY 16, SAIRA 14, STUBBLE 3, EPARFUM 1, PHLUR 1 (from the 17:30Z to 18:03Z count by @businessId, taken at about 18:03Z). Published (at the same time, 91 of the later 92): PURDYFIGG 67, DOCKBAY 16, STUBBLE 3, ESCENTRICPL 2, EPARFUM 1, ESCENTRIC 1, PHLUR 1.
- Published versus snap_adapter, per record (listLogs to 18:03:41Z, key businessId|recordId|correlationId): dedupe published 92 (92 distinct keys, 0 repeated); snap_adapter "Entity created in SNAP" 92 (92 distinct keys, 0 repeated); published without a snap_adapter outcome 0; created without a dedupe publish 0. snap_adapter "Entity already exists" or failure messages: 0 (message list for the window is only "Incoming record received", "Entity created in SNAP" and the 204 POST log). Creates lag publishes: at 18:03:00Z the aggregate showed 81 created against 92 incoming, and all 92 were present by 18:03:31Z.
- Dedupe ledger (`dedupe-list`, production, sales_order, storedAt 17:30:00Z to 18:03:00Z): 92 stored, equal to published and created. With minDedupeCount 1 and the window to 18:04Z: 62 records have dedupeCount of 1 or more (a stored record re-received later; example reference 13806507524476, stored 17:55:14Z, dedupeCount 1). `dedupe-summary` production: sales_order total 199,388, duplicatesBlocked 4,158,218 (cumulative, not a window figure).
- Error-level logs (@environment:prod status error/critical/alert/emergency), 17:30Z to 18:03Z: 0 in dedupe_service, snap_adapter and replay_service. One across @domain:fuse: tracking-service "store failed; nacking for redelivery" at 17:34:56Z (not investigated further).
- Metrics (`fuse.dedupe.event.*`, environment:prod, 5-minute buckets): handled / fresh / duplicate / net (handled minus fresh plus duplicate): 17:30 513 / 2 / 515 / -4; 17:35 417 / 5 / 399 / +13; 17:40 479 / 5 / 474 / 0; 17:45 311 / 5 / 307 / -1; 17:50 465 / 8 / 459 / -2; 17:55 499 / 9 / 490 / 0; 18:00 (partial, to 18:05) 299 / 12 / 297 / -10. Handled per bucket is about 30% of the incoming log count (e.g. 17:30: 513 against 1,732), fresh is below published (2 against 7, 5 against 16). blacklisted, invalid, record.invalid and dropped_config_unavailable returned no series (the net with and without them is identical).
- Rolling 12-bucket net (my own arithmetic, not the monitor's evaluation): -137 to -50 across 15:55 to 17:05, then -23 to +15 through 17:50, +27 at the window ending 18:00 and +47 at 18:05. The rise comes from the -41 (16:55) and -30 (17:00) buckets leaving the window while +28 (17:05), +14 (17:10) and +13 (17:35) stay. Logs reconcile exactly in every bucket in the same period.
- Pub/Sub (5-minute rollups, 17:30Z to 18:05Z, prod project): highest undelivered on any subscription 42.7 (tracking-service.prod.create_record_request.sales_order), then collector create_record_request_sales_order 13.3; dedupe_service.prod.create_record_request_sales_order max 1.2 undelivered, oldest unacked max 1.2s; snap_adapter.prod.create_record_sales_order max 0.6 undelivered, oldest unacked max 3.6s; highest oldest-unacked age on any subscription 16.8s (bifrost.prod.snap_poll_customer.v1.sub), then 10.8s (shopify-connector_prod_goods_out_confirmation_v1_sub).
- Held in replay-service (`replay-list-failures`, production, createdAt 2026-11-07, total 2,119; newest 17:57:32Z): since 17:30Z 177, all PURDYFIGG goods_out_confirmation, reason "Fulfillment order ... is CLOSED in Shopify, so it cannot be fulfilled", failurePoint confirmation.delivery_shopify, attempts 0, 177 distinct recordIds, in bursts at about 17:34, 17:36, 17:39, 17:42, 17:47, 17:48, 17:54 and 17:57Z. Per record, all 177 have an earlier "Confirmation dispatched successfully" shopify-connector log for the same recordId today (shopify-connector logs from 00:00Z). No create-side held record since 17:30Z: `replay-list-failures` for sales_order, purchase_order, master_data, pick_confirmation and pack_confirmation today returns 1 total, DOCKBAY UK-913529 (create.wms_precheck, ShipAddress.City over 30 characters) created 13:03:14Z, attempts 0.
- Monitor state: Warn (`search_datadog_monitors` id:302511456). `search_datadog_events` source:alert for this monitor, last 12h: one event (18:00:36Z).
- Slack: #bifrost-notifications read from 17:50Z: one message, the monitor's alert post (18:01:53Z); no other alert posts, no Recovered posts.

## Outcome
Nothing unaccounted for: every incoming record is a duplicate drop or a publish, every publish reached snap_adapter as a create (92 per record), nothing held by the dedupe gate, no errors in dedupe, snap_adapter or replay, no dedupe or snap backlog. The monitor's net crosses the threshold because the metric counters undercount log volume and some buckets net positive while logs reconcile exactly. Same conclusion as 4 and 6 Nov: monitor_mistuned, P4. The 177 new held PURDYFIGG confirmations are the already-recorded Shopify CLOSED class and each has an earlier successful dispatch, so none is a lost confirmation. Not replayed, not changed.

## Not established
Why the counters run below log volume and why some buckets net positive (no code or instrumentation check). The monitor's own evaluated value at 18:00:36Z (only my rolling sum was computed). The user-reported "1 further firing folded in": the events search showed one event in 12h, so I could not see a second. Why the PURDYFIGG goods-out confirmations are attempted again after a success (only the earlier success was checked, not the cause; the earlier 7 Nov record points at duplicate batch delivery). Whether Shopify fulfillment-order state matches (Shopify not queried). The tracking-service 17:34:56Z nack. Pub/Sub peaks inside a 5-minute bucket (rollups, not raw). Reconciliation of the 18:00:00Z to 18:03:00Z minutes is by counts only; per-record reconciliation covers 17:30:00Z to 18:00:00Z for dedupe and 17:30:00Z to 18:03:00Z for published to snap_adapter created.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794074513024329
- Monitor: https://app.datadoghq.com/monitors/302511456
- Earlier records: Monitors/2026-11-04-dedupe-silent-publish-drop.md, Monitors/2026-11-06-dedupe-silent-publish-drop-warn-1846z.md, Monitors/2026-11-07-egress-shopify-confirmation-delivery-failing-purdyfigg-duplicate-batch-1652.md
