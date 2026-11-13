---
tags: [datadog-triage]
date: 2026-11-13
monitor: "[FUSE][SFTP Connector] Canonical validation failures"
service: sftp-connector
business_id: ESCENTRIC
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794557728065199"
opened_at: "2026-11-13T08:14:08Z"
severity_assessed: P4
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# ESCENTRIC file `15316 JARROLDS CSV.csv` rejected at ingest: no order.customerRef again; file in error/, support owes a corrected resend

## Fired
Monitor 324087068 (Terraform-managed, `managed-by:terraform`): `logs("service:sftp_connector @environment:prod \"Records failed CSV validation\"").index("*").rollup("count").last("15m") > 0`. Triggered 08:14:08Z (Datadog `source:alert` event), Slack post 08:15:28Z, parent ts 1794557728.065199, no replies when read. The post names ESCENTRIC, `create_sales_order`, `CanonicalSalesOrderSchema`, 1 failed row, sample error `order.customerRef: Invalid input: expected string, received undefined`. The matching log is the sftp_connector line at 08:13:51.826Z, file `15316 JARROLDS CSV.csv`, correlationId `3991d779-6708-4012-80be-fde59e4606e1`, version `6272f527aa532e47fa098adadfc8dfa2dd97aae3` (revision `sftp-connector-prod-cr-00130-db6`), `validationErrors` holding one entry: field `order.customerRef`.

## Investigation
- The file held one order: `Records validated` validCount 0, invalidCount 1. `Record dropped` reason `canonical_validation`. Failing field (log `validationErrors` and replay-service `errors`): `order.customerRef` only. In the held record `customer.order` is present (15316) and the `order` block has no `customerRef` key; every other field was accepted. The held record's `dates.dueOut` is 07/11/2026, already past. No personal data quoted here.
- Routing: `Records to send resolved` recordCount 0; `Validation failures published` (`POST /events/v1/create_data_failure` 204); `File routed` destination `error`, trigger `failure` at 08:13:52Z; an `Incoming file event` for `.../create_sales_order/error/15316 JARROLDS CSV.csv` at 08:13:52Z (correlationId `a386c596-16c7-441f-a1a8-2cfa633c0bd6`). The 28 logs under correlationId `3991d779-...` come from sftp_connector, config-service, collector_service, dedupe_service, replay_service and shopify-connector. There are no snap_adapter logs, so nothing from this file reached Snap, and there were no other rows. collector: "Failure for a record not held"; dedupe: "Record failed validation"; shopify-connector: `POST /events/failures/sales-order` 202 and "No shopifyOrderId found in failure record; skipping tag update".
- Held, not lost: `replay-list-failures` (production, ESCENTRIC) shows `2b3ba11a-1975-4e1c-85fd-aba094c83c4e`, sales_order, stage `ingest`, failurePoint `create.sftp_row`, attempts 0, createdAt 08:13:52Z. `replay-get-failure`: empty `replayHistory`, `replayable: false`, one blocking issue, `order.customerRef`. Nothing retried or released by me.
- Same customer and field as 12 Nov and 3 Nov: the monitor-query logs over the retained window (earliest returned 30 Oct, 9 logs) are WILDSMITH master_data 30 Oct, LISAUK 2 Nov x2, ESCENTRIC 3 Nov x3 (one file, three attempts, `order.customerRef`), WILDSMITH sales_order 11 Nov, ESCENTRIC 12 Nov (`15348 CSV.csv`, `order.customerRef`), and this one. ESCENTRIC corrected and resent twice before: 3 Nov in about 28 minutes (first failure 14:24:48Z, `15320 15321 ABU DHABI CSV.csv` validated 2 rows at 14:52:38Z), and 12 Nov order 15348 in about 2 h 15 min: `Records validated` for `12 11 csv.csv` (3 valid, 0 invalid) at 14:01:02Z, and a search by `@recordId:15348` shows collector, dedupe and snap_adapter "Entity created in SNAP" at 14:01:06Z under correlationId `433c8979-26f2-4c11-8938-25a159f6c116`. The 15348 held failure `59580430-f7d7-4d7d-849a-b4c069fafe71` is still listed with attempts 0 although the order was recreated.
- Order 15316 itself: `@recordId:15316` returns no prod log in the 14-day query, so it was not created through the pipeline in that window. Snap not queried.
- WILDSMITH SO-29733 (11 Nov): not resent as far as logs show. `@recordId:SO-29733` over prod from 11 Nov 10:00Z to now returns only the 10:00Z hour (collector 2, dedupe 3, sftp_connector 1); every WILDSMITH sales-order file since has validCount>0, invalidCount 0 (55 files after the failing one, 11 Nov 10:53Z to 13 Nov 07:09Z). `replay-list-failures` (production, WILDSMITH) still lists `a770384f-1ed7-4ac5-90c7-2e327d602cda`, attempts 0.
- One bad file, not broad: monitor-query logs in the last 24 h: 2 (12 Nov 11:45Z and 13 Nov 08:13Z, two separate 15-minute buckets). Last 7 days (from 6 Nov): 3 (WILDSMITH 11 Nov 10:38Z, ESCENTRIC 12 Nov, ESCENTRIC 13 Nov). Fleet `Records validated` logs, last 24 h: 709 clean, 2 with invalid rows. ESCENTRIC over 14 days: 46 `Records validated` logs, 5 with an invalid row (all `order.customerRef`: 3 on 3 Nov, 12 Nov, 13 Nov); the file names do not separate good from bad (clean ESCENTRIC files carry the same `NNNNN NAME CSV.csv` pattern).
- Not our change: (1) version split by `Records validated` logs from 12 Nov 00:00Z. `e17c9ca6` (to 13:36:24Z): 348 files (324 sales_order clean, 20 purchase_order, 3 master_data) and 1 with an invalid row (15348). `6272f527` (from 13:31:12Z): 443 files (424 sales_order clean, 16 purchase_order, 2 master_data) and 1 with an invalid row (this one). 506 rows validated clean after the deploy. (2) The same field failed on `e17c9ca6` (12 Nov 11:45Z) and on `72984d47` (3 Nov), before the deploy. (3) The deploy: GitHub deployment `7738583964` (`terraform-prod`, 13:29:04Z), run 43189229255 `terraform-apply-prod` success 13:31:32Z, first log on the new version 13:31:12Z. Compared with `e17c9ca6` it carries 3 commits: `91d70dea` (FUSE-1351, sftp-host `directories.json` and its test), `895f59c5` (FUSE-1156, one line in `pubsub.controller.ts` plus a test; its own deploy run 43049944939 still reads `waiting`, but it is an ancestor of `6272f527`, `compare` ahead_by 1 behind_by 0, so its code is live) and `6272f527` (Renovate #410: `@gfs-bifrost/observability` ^2.5.0 to ^2.6.0, `@gfs-bifrost/remote-config` ^2.6.0 to ^2.8.0). (4) `audit-search` for tenant ESCENTRIC, kinds other than `sftp_login`, from 1 Nov: 0 events. (5) Datadog `get_change_stories` for sftp-connector, env prod, 11 Nov 08:00Z to 13 Nov 08:20Z: none. (6) The other services in the trace log their own versions (collector `c7e28e9f`, dedupe `1eeac6f2`, replay `6ee4022d`, shopify-connector `ed380385`, config-service `6b736842`); the failure is raised inside sftp_connector before any of them.
- Still firing: monitor status Alert at about 08:17Z (`search_datadog_monitors`). No `Records failed CSV validation` log after 08:13:51.8Z and no ESCENTRIC sftp_connector or snap_adapter log after 08:13:53Z (queried to about 08:17Z). The 15-minute window clears about 08:29Z if nothing new arrives.
- Flapping: `source:alert` events for this monitor over 7 days: Triggered 11 Nov 10:39:08Z, Recovered 10:54:08Z, Triggered 12 Nov 11:46:08Z, Recovered 12:01:08Z, Triggered 13 Nov 08:14:08Z. Three firings in 46 h on two customers, each a different file; ESCENTRIC twice in about 20.5 h. Not a flapper.
- Monitor text is stale: it says "the only occurrence in the past 7 days was one file redelivered 4 times in a 10-minute window (8/242 rows failing each time)"; the queries above no longer match that. Cosmetic; not ticketed.
- Maintenance/: latest records are 2026-11-04; none covers 13 Nov, and this is not a Snap failure. Customers vault `Customers/ESCENTRIC/` has `overview.md` and `ledger.md` but no `known-context.md`.

## Not established
- Why `order.customerRef` is empty for order 15316: the CSV was not read (customer data) and ESCENTRIC's live mapping was not read, so a blank source column versus a mapping gap is open.
- Whether ESCENTRIC or support already know, or whether a corrected file is on its way (no ESCENTRIC log after 08:13:53Z as of about 08:17Z; email and tickets not checked).
- Whether order 15316 exists in Snap by another route (no pipeline log for it in 14 days; Snap not queried).
- Whether WILDSMITH SO-29733 was corrected under a different order reference; only a search by that reference was run.
- What shopify-connector does with the failure event beyond the two log lines.
- The version sftp-host serves in prod (its logs carry no `version` tag).

## Outcome
Real but minor, P4. One ESCENTRIC file with one order was rejected for a missing `order.customerRef`; the file is in `error/`, the failure is held in replay-service as not replayable, and nothing reached Snap. One bad file, not at scale, no Fuse change implicated (same field failed before the 12 Nov 13:31Z deploy). Support needs ESCENTRIC to correct and resend order 15316 (its held due-out date, 07/11/2026, has passed). WILDSMITH SO-29733 is still outstanding. No escalation, no ticket.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794557728065199
- Monitor: https://app.datadoghq.com/monitors/324087068
- Replay failure: 2b3ba11a-1975-4e1c-85fd-aba094c83c4e
- Earlier triages: 2026-11-12-sftp-connector-canonical-validation-failures-escentric.md, 2026-11-11-sftp-connector-canonical-validation-failures-wildsmith.md, 2026-11-03-sftp-connector-canonical-validation-failures-escentric.md
