---
tags: [datadog-triage]
date: 2026-11-06
monitor: "[FUSE][Dedupe Service] Silent publish drop (handled minus outcomes)"
service: dedupe-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793990869177349"
opened_at: "2026-11-06T18:46:36Z"
severity_assessed: P4
flapping: false
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Dedupe "silent publish drop" Warn at 18:46Z: shortened re-check, every incoming record accounted for

## Fired
Monitor 302511456 (P2, managed-by:terraform, `sum(last_1h)` handled minus outcomes) went Warn at 18:46:36Z. Alert post in #bifrost-notifications at 18:47:49Z (ts 1793990869.177349), no replies when read. Shortened re-check of a cause triaged three times on 4 Nov; window 18:15Z to about 18:49Z.

## Investigation
- dedupe_service logs (@environment:prod), 18:15:00Z to 18:48:28Z: "Incoming record received" 17,672 = "Record dropped" 17,399 (all `@reason:duplicate`) + "Record published to topic" 273 + "Dedupe gate held" 0. Unaccounted 0. Each of the 7 five-minute buckets reconciles (e.g. 18:30Z 2,527 = 2,501 + 26; 18:45Z 2,406 = 2,348 + 58).
- By business, incoming 17,672: PURDYFIGG 17,518, ESCENTRIC 76, SAIRA 41, ESCENTRICPL 35, STUBBLE 2. Published 273: PURDYFIGG 267, ESCENTRIC 3, STUBBLE 2, SAIRA 1. All sales_order.
- snap_adapter, same window: "Incoming record received" 273 = "Entity created in SNAP" 253 + "Entity already exists" 20 + "Entity creation in SNAP failed" 0. Matches the 273 dedupe published. PURDYFIGG: 267 published = 247 created + 20 already exists (all 20 already-exists logs are PURDYFIGG, `detectedBy: precheck`); ESCENTRIC 3, STUBBLE 2, SAIRA 1 created = published.
- dedupe ledger (`dedupe-list`, production, sales_order, storedAt 18:15:00Z to 18:48:28Z): 253 stored (PURDYFIGG 247), every one dedupeCount 0. Equals the snap_adapter created count (253), and published minus ledger = 20 = already-exists count.
- Error-level logs (`@domain:fuse @environment:prod status:error/critical/alert/emergency`), 18:15Z to 18:48:28Z: 0. Also 0 in dedupe_service, snap_adapter, replay_service.
- Metric view (`fuse.dedupe.event.*`, environment:prod, 5-minute buckets 18:15Z to 18:45Z): handled 4,895, fresh 71, duplicate 4,799, net +25. Per bucket net: -1, -8, 0, -7, +27, 0, +14. blacklisted, invalid, record.invalid and dropped_config_unavailable returned no series. For 17:50Z to 18:45Z the same arithmetic gives +21 (my own sum, not the monitor's evaluation).
- Metrics vs logs, same window: handled 4,895 vs 17,672 incoming logs (28%); fresh 71 vs 273 published; duplicate 4,799 vs 17,399 dropped. The counters run below log volume, as on 4 Nov, and the net is positive in the 18:35Z (+27) and 18:45Z (+14) buckets while logs reconcile exactly in both.
- Pub/Sub, max since 18:15Z: dedupe_service.prod.create_record_request_sales_order sub 23 undelivered, oldest unacked 1s; highest undelivered on any prod subscription 106 (tracking-service.prod.create_record_request.sales_order); highest oldest-unacked age on any prod subscription 7s (shopify-connector_prod_bulk_ingest_order_reap_v1_internal_sub).
- Held in replay-service (`replay-list-failures`, production, createdAt 2026-11-06, total 485): 32 new since 18:15Z, all PURDYFIGG goods_out_confirmation, reason "Fulfillment order ... is CLOSED in Shopify, so it cannot be fulfilled", failurePoint confirmation.delivery_shopify, created 18:20:38-18:20:40Z (9), 18:30:40-18:30:42Z (13), 18:40:40-18:40:41Z (10). Confirmation delivery to Shopify, not dedupe or Snap submission. Same class and reason already recorded earlier today (e.g. Monitors/2026-11-06-platform-elevated-prod-error-rate-tracking-service-store-0910 and others). No new create-side (sales_order) failure since 18:15Z: the newest is DOCKBAY UK-913330 (create.wms_precheck, ShipAddress.City over 30 characters) at 18:03:53Z, attempts 0 and still listed at about 18:49Z; it was flagged to support in the 18:11Z reply on the platform error-rate thread.
- Monitor state (`search_datadog_monitors` id:302511456): Warn. `search_datadog_events` source:alert for this monitor, last 12h: one event (18:46:36Z), so no earlier firing or recovery today.
- Channel read since 18:06Z: only two alert posts. The 18:06:49Z platform error-rate post has a reply (18:11:25Z). The 18:47:49Z post for this monitor has none, so this thread is the only unreplied alert thread; no Recovered posts.

## Outcome
Nothing unaccounted for: every incoming record is a duplicate drop or a publish, every publish reached snap_adapter (253 created, 20 already in Snap, 0 failed), nothing held by dedupe, no errors, no backlog. The monitor's net (+25 over the window) comes from counters that undercount log volume, so it cannot tell this from a real drop. Same conclusion as the three 4 Nov records: monitor_mistuned, P4. The 32 new PURDYFIGG held confirmations are a separate, already-recorded class (Shopify FO CLOSED) and were not investigated further.

## Not established
Why the metric counters run below log volume and why some buckets net positive (no code or instrumentation check). Why the 20 "Entity already exists" PURDYFIGG records have no ledger entry (counts match, mechanism not checked). The cause of the 32 Shopify CLOSED confirmation failures (reason read from replay-service only; Shopify fulfillment-order state not checked). The monitor's exact evaluated value at 18:46:36Z and when it recovers. Per-record rather than per-batch matching of incoming to outcome (counts only). Whether DOCKBAY UK-913330 has been fixed or replayed (still listed, attempts 0, at about 18:49Z). Logs for the 18:10Z bucket (+28 in metrics) were outside the queried window.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793990869177349
- Monitor: https://app.datadoghq.com/monitors/302511456
- Earlier records: Monitors/2026-11-04-dedupe-silent-publish-drop.md, Monitors/2026-11-04-dedupe-silent-publish-drop-alert-1925z.md, Monitors/2026-11-04-dedupe-silent-publish-drop-warn-2000z.md
