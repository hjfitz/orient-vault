---
tags: [datadog-triage]
date: 2026-11-07
monitor: "[FUSE][Dedupe Service] Silent publish drop (handled minus outcomes)"
service: dedupe-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794082909820079"
opened_at: "2026-11-07T20:20:36Z"
minutes_spent: 6
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Dedupe "silent publish drop" Warn at 20:20Z (tail of a critical spell since 19:15Z): nothing unaccounted for, 0 held

## Fired
Monitor 302511456 (P2, managed-by:terraform, `sum(last_1h)` handled minus outcomes, warn >20, critical >50). Events (search_datadog_events, 24h, 10 events): Triggered 19:15:36Z, Re-Triggered 20:15:36Z (60 min renotify), Warn 20:20:36Z, with no Recovered event between 19:15:36Z and 20:20:36Z. So the 20:20:36Z "first triggered" is the downgrade from critical to Warn at the end of a critical spell of about 65 minutes, not a new onset. Earlier today: Warn 18:00:36, Recovered 18:20:36, Warn 18:26:36, Recovered 18:30:36, Warn 18:55:36, Triggered 19:05:36, Warn 19:10:36. Alert post ts 1794082909.820079 (20:21:49Z), no replies; the Re-Triggered post 1794082604.553329 (20:16:44Z) also had no replies.

## Investigation
- Aggregate, 5-minute buckets 19:10Z to 20:20Z (analyze via aggregateLogs, dedupe_service @environment:prod): "Incoming record received" 1111, 1056, 998, 945, 861, 775, 701, 632, 548, 483, 412, 331, 294, 278 = 9,425. "Record dropped" (all @reason duplicate) 9,236 + "Record published to topic" 189 = 9,425. Every bucket reconciles exactly (e.g. 20:00 412 = 376 + 36; 20:15 278 = 271 + 7). No "held" or failure message in dedupe_service in the window.
- Per record (listLogs, key businessId|recordId|correlationId): 19:10:00Z to 20:15:00Z 9,147 incoming, 9,147 distinct keys, 0 keys where incoming differs from drops + published; 20:15:00Z to 20:20:00Z 278 incoming = 271 dropped + 7 published, 0 incoming without an outcome and 0 outcome without an incoming. Covers the monitor's 1h window (19:15:36Z to 20:15:36Z, evaluation delay 300 s).
- Published to snap_adapter, per record (listLogs, 19:05:00Z to 20:23:36Z): 215 published (215 distinct keys), 208 "Entity created in SNAP" + 7 "Entity already exists in SNAP" = 215 outcomes. Published without an outcome 0; outcome without a publish 0. Publish to first outcome lag p50 6 s, p95 74 s, max 83 s. snap_adapter warn/error/critical logs in that span: 0. Re-counted at about 20:26Z (19:10Z onward): 212 published = 206 created + 6 exists.
- Dedupe ledger (dedupe-list production, sales_order, storedAt 19:10:00Z to 20:20:10Z): total 196 = snap_adapter "Entity created" 196 for 19:10:00Z to 20:20:25Z. Published 200 in 19:10:00Z to 20:20:10Z = 196 created + 4 already exists.
- Cloud Run dedupe-service-prod 2xx request_count per bucket 1112, 1056, 998, 945, 861, 775, 701, 629, 551, 483, 410, 333, 294, 277 = 9,425, equal to incoming logs in total (per-bucket differences of 1 to 3 are bucket alignment). Only one version in the window (1eeac6f25d59e781fd75661c504410d3d5611170, 29,142 logs). change_tracking events for dedupe/snap_adapter in 6h: 0.
- Pub/Sub push_request_count (project-wide, by response_class, 19:10Z to 20:20Z): ack on every bucket; 22 deadline_exceeded, all on shopify-connector_prod_goods_out_confirmation_v1_sub (none on the dedupe or snap_adapter subscriptions). Window averages: dedupe create_record_request_sales_order sub undelivered 3.6, snap_adapter create_record_sales_order sub undelivered 1.05 and oldest unacked 3.9 s (averages, not peaks).
- Error-level logs (@domain:fuse @environment:prod, 19:10Z to about 20:26Z): config-service 1, shopify-connector 12, none in dedupe_service or snap_adapter.
- Why it fired (counters vs logs): handled counter 19:10Z to 20:15Z = 2,697 against 9,425 incoming logs (29%); fresh 60 against 189 published (32%); duplicate 2,552 against 9,236 dropped (28%). Net per 5-minute bucket (monitor expression, 19:10 to 20:20): +21, +26, +12, +13, +15, -1, +3, -2, -1, 0, -1, 0, 0, 0, 0. My arithmetic, not the monitor's evaluated value: 19:10 to 20:05 buckets sum 85 (above 50, matches Re-Triggered at 20:15:36Z); 19:20 to 20:10 sum 38 (warn band, matches Warn at 20:20:36Z as the 26 and 21 from the early buckets age out). The net is positive only in early buckets, then about 0, while log volume decays from 1,111 to 278 per bucket.
- The 4 already-exists records in 19:10Z to 20:20Z (#6689276, #6689354 at 19:25:11Z; #6688254, #6689500 at 19:35:08-11Z, all PURDYFIGG) each match a dedupe "Mismatch at shipping.trackingNumber" (3) or "Mismatch at shipmentLines[0].quantities.required: 0 !== 1" (1) log at the same second, then publish. Snap (snap-get-shipment, host ilg005, read only): #6689276 = PURD3B46B7CBF71, created 17:05:24Z, Stage 90, CarrierTrackingNumber T08HLA0001044539, which is the value dedupe's mismatch log names. #6688254 = PURD01CE46775B0, created 16:40:29Z, Stage 90.
- Slack: #bifrost-notifications 19:00Z onward; the earlier 19:05Z Triggered alert already has the Bifrost Support Bot reply (monitor_mistuned P4, posted 19:14:51Z); the 19:15Z Triggered, 20:16Z Re-Triggered and 20:21Z Warn threads had no reply when read.

## Outcome
No record unaccounted for: 9,425 incoming = 9,236 duplicate drops + 189 published, nothing held, every publish has a snap_adapter outcome (created, or already exists), ledger equals created, no deploy, no errors in dedupe or snap_adapter. The monitor's net crosses 50 because the counters undercount logs by about 70% and some early buckets net positive. Same conclusion as the 19:05Z record: monitor_mistuned, P4, flapping. Nothing replayed, released or changed.

## Not established
Why the counters undercount the logs and why early buckets net positive (no code or instrumentation check). The monitor's own evaluated value at 20:15:36Z and 20:20:36Z. Why PURDYFIGG orders are re-received every 5 minutes. Whether the changed quantity on the quantity-mismatch republish (#6688254) is reflected in Snap (the order exists and is despatched; its line quantities were not compared); #6689354 and #6689500 were not read in Snap. The 22 deadline_exceeded pushes on the shopify-connector goods_out_confirmation subscription. The 12 shopify-connector and 1 config-service error logs. Peaks inside a 5-minute Pub/Sub bucket (window averages only). snap-polling-service "Consignment StU not found" warns (8,342 in the window) were seen in a warn sweep but not examined.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794082909820079
- Monitor: https://app.datadoghq.com/monitors/302511456
- Earlier records: Monitors/2026-11-07-dedupe-silent-publish-drop-triggered-1905z.md, Monitors/2026-11-07-dedupe-silent-publish-drop-warn-1800z.md, Monitors/2026-11-06-dedupe-silent-publish-drop-warn-1846z.md, Monitors/2026-11-04-dedupe-silent-publish-drop.md
