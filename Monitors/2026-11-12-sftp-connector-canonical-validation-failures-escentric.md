---
tags: [datadog-triage]
date: 2026-11-12
monitor: "[FUSE][SFTP Connector] Canonical validation failures"
service: sftp-connector
business_id: ESCENTRIC
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794484045400419"
opened_at: "2026-11-12T11:46:08Z"
severity_assessed: P4
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# ESCENTRIC order 15348 rejected at ingest: the mapping produced no order.customerRef; file in error/, support owes a corrected resend

## Fired
Monitor 324087068 (Terraform-managed, `managed-by:terraform`): `logs("service:sftp_connector @environment:prod \"Records failed CSV validation\"").index("*").rollup("count").last("15m") > 0`. Triggered 11:46:08Z, Slack post 11:47:25Z, parent ts 1794484045.400419, no replies when read. The matching log is the sftp_connector line at 11:45:27Z: ESCENTRIC, `create_sales_order`, `CanonicalSalesOrderSchema`, `failedCount` 1, sample error `order.customerRef: Invalid input: expected string, received undefined`.

## Investigation
- The file: `15348 CSV.csv`, path `FUSE_ABDAD7F392/to_ilg/create_sales_order/`, connector `conn_1586e51cc79e4d4eb0a14e53ebab78d4` ("Primary SFTP"), correlationId `fd7d0db2-0793-413b-bfad-bf9cabd9c0ea`. The `Records validated` log says validCount 0, invalidCount 1, so the file held one order and it failed. `Record dropped` reason `canonical_validation`. Failing field (log `validationErrors` and replay-service `errors`): `order.customerRef` only. In the held canonical record the `order` block has no `customerRef` key; `customer.order` (15348) and the other header fields are present. No personal data is quoted here.
- Routing: `File routed` destination `error`, trigger `failure` at 11:45:28.622Z; an `Incoming file event` for `.../create_sales_order/error/15348 CSV.csv` at 11:45:28.414Z (correlationId `4eea7cff-5a65-4582-a062-f7f30b4dff98`). `Records to send resolved` recordCount 0, `Validation failures published` (`POST /events/v1/create_data_failure` 204). All logs for this correlationId (28 lines) come from sftp_connector, config-service, collector_service, dedupe_service, replay_service and shopify-connector. There are no snap_adapter logs, so nothing from this file reached Snap, and there were no other rows. shopify-connector answered `POST /events/failures/sales-order` 202 and logged "No shopifyOrderId found in failure record; skipping tag update". collector: "Failure for a record not held". dedupe: "Record failed validation".
- Held, not lost: `replay-list-failures` (production, ESCENTRIC) shows `59580430-f7d7-4d7d-849a-b4c069fafe71`, sales_order, stage `ingest`, failurePoint `create.sftp_row`, attempts 0, createdAt 11:45:28Z. `replay-get-failure` shows empty `replayHistory` and `replayable: false` with one blocking issue, `order.customerRef`. Held record `dates.dueOut` is 16/11/2026. Nothing retried or released by me.
- Same customer and field as 3 Nov, not the same as 11 Nov: the 3 Nov alert (record `2026-11-03-...-escentric.md`) was ESCENTRIC, same connector, same field. That time the file `15320 15321 ABU DHABI CSV.csv` failed three times (14:24:48, 14:32:07, 14:38:31Z, validCount 0 / invalidCount 1) and validated 2 orders at 14:52:38Z and again 14:59:43Z, so ESCENTRIC corrected and resent within about 28 minutes. The 11 Nov alert was WILDSMITH, different file naming (`wildsmith-YYYYMMDD-HHMMSS.csv`), different fields (shifted columns).
- One bad file, not broad: monitor query in 15-minute buckets, last 24 h (11 Nov 11:50Z to now): 1 (the 11:45Z bucket). The 7 days from 5 Nov 11:50Z: 2 logs (WILDSMITH 11 Nov 10:30Z bucket, ESCENTRIC 12 Nov 11:45Z bucket). 30-day daily query (earliest day returned 30 Oct): 8 logs: 30 Oct WILDSMITH master_data 1, 2 Nov LISAUK 2, 3 Nov ESCENTRIC 3, 11 Nov WILDSMITH 1, 12 Nov ESCENTRIC 1. Fleet-wide `Records validated` logs for sftp_connector, last 24 h: 746 clean (719 sales_order, 20 purchase_order, 7 master_data) and 1 with invalid rows. ESCENTRIC since 2 Nov: 38 clean files, 4 with invalid rows (3 on 3 Nov, 1 today).
- WILDSMITH SO-29733 (11 Nov): not corrected and resent as far as logs show. A search by `@recordId:SO-29733` across all prod services from 11 Nov 10:00Z to 11:50Z returns only the six original 10:38Z logs (sftp_connector "Record dropped", collector, dedupe), none after 10:38:43Z, and nothing from snap_adapter. A 14-day snap_adapter query for that recordId returns nothing. `replay-list-failures` (production, WILDSMITH) still lists `a770384f-1ed7-4ac5-90c7-2e327d602cda` with attempts 0. No further `Records failed CSV validation` log for WILDSMITH after 10:38:42Z on 11 Nov. WILDSMITH's newest replay failure is SO-29746 (13:38Z 11 Nov, snap-adapter precheck, phone length), a different record.
- Not our change: (1) all 64,100 sftp_connector prod logs from 10 Nov 12:00:06Z to 12 Nov 11:48:31Z carry `version` `e17c9ca6c7752ad23797155277bbd4359b20e316` (revision `sftp-connector-prod-cr-00129-4gd` on the failing log); no other version appears in any hourly bucket. GitHub deployment `7651460487`/`7651412912` for `e17c9ca6`: success 9 Nov 09:42:37Z (run 42594936500). (2) The 10 Nov deployments `7684004327` and `7684098546` (sha `91d70dea`, 13:55:50Z and 14:00:01Z) belong to run 42829034298, `Deploy sftp-host`, with `terraform-apply-prod` success at 14:01:37Z; no connector log carries `91d70dea`. sftp_host logs (18,877 since 10 Nov 12:00Z) carry no `version` tag, so the version sftp-host serves is not readable from Datadog. (3) Two newer `Deploy sftp-connector` runs are `waiting` on the prod gate: 43049944939 (`895f59c5`, FUSE-1156, 11 Nov 15:35Z) and 43189229255 (`6272f527`, Renovate #410, 12 Nov 09:11Z); `docker-push-prod` has not run, so neither is serving. A `Manual Deploy sftp-connector` run on 11 Nov 11:22Z (`556043a8`) ran `docker-push-dev` and `terraform-apply-dev` only. (4) `audit-search` for tenant ESCENTRIC (kinds other than sftp_login, no date bound, newest first, 27 events): newest is 28 Oct 11:07Z (shipment_methods update); last mapping change on `conn_1586e51c...` is 23 Oct 13:35Z (`mapping.config.rules.header`); nothing in the last 48 h or since 28 Oct (the 20 newest events are all `config_change` or `credential_access`; the 7 older ones were not read). (5) Datadog `get_change_stories` for sftp-connector (10 Nov 11:00Z to 12 Nov 11:55Z, env prod) returned none; `source:change_tracking` events for sftp and config services over 48 h returned none.
- Context, not relied on for the verdict: the Waypoint ledger for sftp-connector (FUSE-1254, Sep) says the connector's factories emit no `order.customerRef`, only the mapping can supply it, and a blank or unmapped reference fails ingest validation into error/; and that all 26 prod SFTP sales-order connectors then mapped `OrdRef1` to it. I did not read ESCENTRIC's live mapping or the CSV.
- Still firing: monitor status Alert at about 11:51Z (`search_datadog_monitors`). No `Records failed CSV validation` log and no ESCENTRIC sftp_connector log after 11:45:28.6Z (queried to 11:51Z). The 15-minute window clears about 12:00:27Z if nothing new arrives.
- Flapping: `source:alert` events for this monitor over 7 days: Triggered 11 Nov 10:39:08Z, Recovered 11 Nov 10:54:08Z, Triggered 12 Nov 11:46:08Z. Two firings in 7 days on different customers; not a flapper.
- Monitor text is stale: it says "the only occurrence in the past 7 days was one file redelivered 4 times in a 10-minute window (8/242 rows failing each time)". Against the queries above that no longer matches (2 logs in 7 days, different customers). Cosmetic; not ticketed.
- Maintenance/: latest records are 2026-11-04 Snap patch windows and 2026-11-02; none covers 12 Nov, and this is not a Snap failure. Customers vault `Customers/ESCENTRIC/`: no `known-context.md`; overview generated from config (verified 2026-11-11), ledger empty.

## Not established
- Which CSV column is blank or missing for order 15348 (file not read, it holds customer data), and whether it is the mapped `OrdRef1`-style column. ESCENTRIC's live mapping was not read.
- Whether ESCENTRIC or support already know, or whether a corrected file is on its way (no log after 11:45:28Z as of 11:51Z; email and tickets not checked).
- Whether SO-29733 has been corrected under a different order reference; only a search by that reference was run.
- The version sftp-host serves in prod (sftp_host logs carry no version tag); only the 10 Nov 14:01:37Z deploy record is known.
- What shopify-connector does with the failure event beyond the two log lines above.

## Outcome
Real but minor, P4. One ESCENTRIC file with one order was rejected for a missing `order.customerRef`; the file is in `error/`, the failure is held in replay-service as not replayable, and nothing reached Snap. One bad file, not at scale, no Fuse change implicated. Support needs ESCENTRIC to correct and resend order 15348 (due out 16 Nov per the held record). The earlier WILDSMITH SO-29733 resend is still outstanding. No escalation, no ticket.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794484045400419
- Monitor: https://app.datadoghq.com/monitors/324087068
- Replay failure: 59580430-f7d7-4d7d-849a-b4c069fafe71
- Earlier triages: 2026-11-03-sftp-connector-canonical-validation-failures-escentric.md, 2026-11-11-sftp-connector-canonical-validation-failures-wildsmith.md
