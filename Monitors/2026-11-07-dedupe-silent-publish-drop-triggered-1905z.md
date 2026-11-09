---
tags: [datadog-triage]
date: 2026-11-07
monitor: "[FUSE][Dedupe Service] Silent publish drop (handled minus outcomes)"
service: dedupe-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794078409026959"
opened_at: "2026-11-07T19:05:36Z"
resolved_at: "2026-11-07T19:15:00Z"
minutes_spent: 10
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Dedupe "silent publish drop" went Triggered (critical) at 19:05Z: nothing unaccounted for, 0 held

## Fired
Monitor 302511456 (P2, managed-by:terraform, `sum(last_1h)` handled minus outcomes) went Warn 18:55:36Z, Triggered 19:05:36Z (first time it has been critical), back to Warn 19:10:36Z (still Warn at 19:13:30Z). Thresholds from the monitor API: critical 50, warning 20, evaluation_delay 300 s, require_full_window false, notify_no_data false, renotify 60 min. Alert post ts 1794078409.026959, no replies when read (19:13Z).

## Investigation
- Monitor events (search_datadog_events, last 24h): Warn 18:00:36, Recovered 18:20:36, Warn 18:26:36, Recovered 18:30:36, Warn 18:55:36, Triggered 19:05:36, Warn 19:10:36. Flapping.
- Monitor net by 5-minute bucket (metrics handled minus fresh minus duplicate; blacklisted, invalid, record.invalid, dropped_config_unavailable returned no series): 18:00 -10, 18:05 +20, 18:10 -2, 18:15 -9, 18:20 +9, 18:25 0, 18:30 -5, 18:35 +16, 18:40 0, 18:45 0, 18:50 +14, 18:55 +3, 19:00 +20, 19:05 -2 (partial). My arithmetic, not the monitor's evaluated value (not retrieved): buckets 18:00-18:55 sum 36 (Warn band, matches Warn at 18:55:36), 18:05-19:00 sum 66 (above 50, matches Triggered at 19:05:36), 18:10-19:05 sum 44 (below 50, matches Warn at 19:10:36).
- Counters undercount logs: handled metric 18:30-19:00 buckets sum 2,970 against 10,193 incoming logs (29%); fresh metric sum 35 against 79 published logs.
- dedupe_service logs (@environment:prod), per 5-minute bucket, counts: 18:30 inc 1532 = drop 1529 + pub 3; 18:35 1520 = 1507 + 13; 18:40 1498 = 1488 + 10; 18:45 1489 = 1480 + 9; 18:50 1443 = 1431 + 12; 18:55 1398 = 1384 + 14; 19:00 1313 = 1295 + 18; held 0 in every bucket. 19:05:00Z to 19:12:47Z by counts only: incoming 2,315 = dropped 2,288 + published 27, held 0. Whole window 18:30:00Z to 19:09:42Z by counts: incoming 11,397 = dropped 11,303 (all @reason duplicate) + published 94 + held 0.
- Per record, incoming 18:30:00Z to 19:05:00Z (listLogs, key businessId|recordId|correlationId; last incoming log 19:02:51Z): 10,193 incoming, 10,193 distinct keys, 0 keys where incoming differs from drops+published+held, 0 outcome keys (to 19:05:00Z) without an incoming log, 0 non-duplicate drops.
- Cloud Run dedupe-service-prod: 2xx request count per bucket equals incoming logs exactly (1532, 1520, 1498, 1489, 1443, 1398, 1313); push_request_count response_class returned only `ack` for both the dedupe and snap_adapter subscriptions (no 4xx/5xx/429 series); active instances 5 in every bucket, idle 0; one revision in the window (dedupe-service-prod-00053-m72 on 37,530 logs; snap-adapter-prod-00099-b4z on 318); change_tracking events for dedupe/snap_adapter in 3h: 0.
- Published vs snap_adapter outcome, per record (listLogs 18:30:00Z to 19:12:19Z): dedupe published 106 (106 distinct keys), snap_adapter 102 "Entity created in SNAP" + 4 "Entity already exists in SNAP" = 106 outcomes; published without outcome 0; outcome without publish 0; 11 published at 19:10:12-19:10:17Z had no outcome at 19:11:23Z and all had one at 19:12:19Z. Lag publish to first create log (95 matched at 19:11Z): p50 3 s, p95 37 s, max 42 s. No snap_adapter failure messages; snap_adapter had no warn/error logs in the window.
- The 4 "already exists" are PURDYFIGG #6688997 (published 18:55:11Z), #6688876, #6688589 and #6688726 (19:05:11Z); each had an earlier "Entity created in SNAP" the same day (16:50-17:00Z) and was then dropped as a duplicate every 5 minutes until dedupe logged "Mismatch at shipping.trackingNumber ... !== undefined" (3) or "Mismatch at shipmentLines[0].quantities.required: 0 !== 1" (1) and published again. 4 "Mismatch at" logs in the window, all PURDYFIGG.
- Ledger (`dedupe-list` production, sales_order, storedAt from 18:30:00Z, read at about 19:11Z): total 102 (page 1 of 2 read, 100 rows; newest storedAt 19:10:17Z) = 102 snap_adapter created. Rows with dedupeCount 1 to 8 are records re-received and held as duplicates of an already published record.
- Error-level logs (@domain:fuse @environment:prod status error/critical/alert/emergency) 18:30:00Z to 19:09:42Z: 0 in every service. Warn: dedupe_service 12,402 (includes the duplicate drops), replay_service 4.
- Mongo: fuse.mongo.up min 1 in all 15 buckets 18:00Z-19:13Z; fuse.dedupe.mongo.heartbeat_failed returned no series.
- Pub/Sub 5-minute max: dedupe sales_order sub undelivered 0 to 81.4, oldest unacked max 0.2 s; snap_adapter create sub undelivered max 1, oldest unacked 0 s.
- replay-service (`replay-list-failures` production, createdAt 2026-11-07, total 2,409, newest 400 read, oldest read 17:42:42Z): 290 distinct failures since 18:30Z, all PURDYFIGG goods_out_confirmation, failurePoint confirmation.delivery_shopify, reason "Fulfillment order ... is CLOSED in Shopify". No create-side type (sales_order, purchase_order, master_data, pick/pack) among them.
- Slack: #bifrost-notifications from 19:00Z. Every other non-Recovered alert post had a Bifrost Support Bot reply when read (19:13-19:14Z). No unreplied others.

## Outcome
No record unaccounted for: every incoming record is a duplicate drop or a publish, every publish has a snap_adapter outcome (102 created, 4 already exists), nothing held, no errors, no backlog, no 4xx/5xx/429, no deploy. The monitor's counter-based net crosses 50 because the counters undercount logs and some buckets net positive. Same conclusion as 4, 6 and 7 Nov: monitor_mistuned, P4, flapping. Not replayed, nothing changed.

## Not established
Why the counters undercount logs and why some buckets net positive (no code or instrumentation check). The monitor's own evaluated value at 19:05:36Z. Whether the 4 re-published PURDYFIGG orders' changed fields (tracking number, line quantity) reached Snap: snap_adapter answered "already exists" and only the log was checked, Snap was not queried. Why PURDYFIGG orders are re-received every 5 minutes. Page 2 (2 rows) of the ledger. Per-record reconciliation covers incoming 18:30:00Z-19:05:00Z; 19:05:00Z-19:12:47Z is counts only. Whether each of the 290 held Shopify confirmations has an earlier successful dispatch (checked on the 18:03Z record, not re-checked here). The 4 replay_service warns. Pub/Sub peaks inside a 5-minute bucket (rollups).

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794078409026959
- Monitor: https://app.datadoghq.com/monitors/302511456
- Earlier records: Monitors/2026-11-07-dedupe-silent-publish-drop-warn-1800z.md, Monitors/2026-11-06-dedupe-silent-publish-drop-warn-1846z.md, Monitors/2026-11-04-dedupe-silent-publish-drop.md
