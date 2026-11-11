---
tags: [datadog-triage]
date: 2026-11-11
monitor: "[FUSE][SFTP Connector] Canonical validation failures"
service: sftp-connector
business_id: WILDSMITH
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794393630093619"
opened_at: "2026-11-11T10:39:08Z"
severity_assessed: P4
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# One WILDSMITH sales order row (SO-29733) failed canonical validation; the other 3 orders in the file reached SNAP; support owes a corrected resend of SO-29733

## Fired
Monitor 324087068 (Terraform-managed, `managed-by:terraform`, priority null): `logs("service:sftp_connector @environment:prod \"Records failed CSV validation\"").index("*").rollup("count").last("15m") > 0`. Tripped at 10:39:08Z with 1 matching log (the 15-minute bucket starting 10:30Z holds 1). Slack post 10:40:30Z, parent ts 1794393630.093619, no replies. The log is the sftp_connector line at 10:38:42Z for `wildsmith-20261111-103842.csv` (`FUSE_C232BE3BCC/to_ilg/create_sales_order/`), connector `conn_69ff5796c5e043d1986e4ec3bca040ed`, correlationId `22f5f434-c441-41d0-85ad-722c8c07b815`, `failedCount: 1`, schema `CanonicalSalesOrderSchema`.

## Investigation
- Failing fields (log `validationErrors`, replay-service `errors`): `financial.lineValue` (expected number, received NaN), `dates.dueOut` and `dates.shipment` (expected date, received string), `shipmentLines.0.soLineId` and `shipmentLines.1.soLineId` (expected number, received NaN). One order dropped: `SO-29733` ("Record dropped", reason `canonical_validation`). In the held record (replay-service `a770384f-1ed7-4ac5-90c7-2e327d602cda`) the values sit in the wrong fields: a delivery-service string in `financial.lineValue`, a currency code in `identifiers.customerId`, text where the dates belong, a SKU string in `soLineId`, and the address and contact fields each hold a neighbouring field's kind of value. That reads as the row's columns being shifted. No personal data is quoted here.
- What happened to the file and the other rows (all under correlationId `22f5f434-...`, 61 log lines across sftp_connector, collector, dedupe, snap_adapter, config-service, replay, shopify-connector): three orders (`SO-29684`, `SO-29698`, `SO-29705`) passed validation, went through dedupe and collector, and snap_adapter logged "Entity created in SNAP" for each at 10:38:44Z. They are held in dedupe (`dedupe-list`, storedAt 10:38:43Z, dedupeCount 0). `SO-29733` is not in dedupe's held list. The failure was published to `create_data_failure` ("Validation failures published", `POST /events/v1/create_data_failure` 204), collector logged "Failure for a record not held", dedupe logged "Record failed validation" on the release path, replay-service logged "Failure stored". sftp_connector then logged "File routed" with `destination: error`, `trigger: failure` at 10:38:43Z; a second "Incoming file event" (correlationId `2371593e-...`, path `.../create_sales_order/error/wildsmith-20261111-103842.csv`) is the move into error/, answered 200, with no ingest logs after it. No further `File routed` for WILDSMITH after 10:00Z.
- Held, not lost: `replay-list-failures` (production, WILDSMITH) shows `a770384f-1ed7-4ac5-90c7-2e327d602cda`, useCase sales_order, stage `ingest`, failurePoint `create.sftp_row`, attempts 0; `replay-get-failure` shows empty `replayHistory` and `replayable: false` with the same 5 `blockingIssues`, so a retry of the held record as stored would be rejected. Nothing was retried or released by me.
- Counts: monitor query in 15-minute buckets, last 24 h: 1 (10:30Z bucket). the 7 days before that (now-8d to now-24h, 15-minute buckets): 3, all on 3 Nov in the 14:15 and 14:30Z buckets. Daily buckets over 30 days: 28 Oct 1, 30 Oct 1, 2 Nov 2, 3 Nov 3, 11 Nov 1 (8 logs in total). By business and file: ESCENTRIC `create_sales_order` 3 (one file, 3 Nov, `order.customerRef` undefined), LISAUK `create_sales_order` 2 (2 Nov, `shipmentLines.0.quantities` undefined), WILDSMITH `create_master_data` 2 (28 and 30 Oct, `product.lifecycle.life` and `product.dimensions.box.height`), WILDSMITH `create_sales_order` 1 (today). None from 4 Nov to 11 Nov 10:30Z. Different customers and different fields each time.
- Data problem, not a regression: (1) `sftp_connector` prod logs for the last 24 h are all on revision `sftp-connector-prod-cr-00129-4gd` (26,859 logs) and version `e17c9ca6` (27,074 logs by `version`), deployed 2026-11-09 09:42:37Z (`Deploy sftp-connector` run 42594936500). (2) Yesterday's `91d70dea` (FUSE-1351, #408) changed only `apps/host/internal/directories/directories.json` and its test, and the only workflow that ran for it is `Deploy sftp-host` (run 42829034298, success 14:01:38Z); no `Deploy sftp-connector` run exists for it and no connector log carries that version. (3) `e17c9ca6` (#404, mapping rules read through remote-config) changed config, confirmation egress, debug controller and factory files, none of them CSV parsing or validation. (4) Since 2026-11-09T09:42:37Z there are 1308 `Records validated` logs for create_sales_order (592 master_data, 21 purchase_order) and the only `Records failed CSV validation` log is this one. (5) Three of the four orders in this same file passed the same mapping on the same version. (6) Fuse `audit-search` for tenant WILDSMITH (kinds other than sftp_login, no date bound) returns two events, 2026-09-04 (connector mapping `mapping.config.rules.lines`) and 2026-09-11 (connector `config.finishedGoodReceiptEgressDirectory`, `confirmationsEnabled`), nothing in the last 24 h or since 4 Nov. (7) Datadog `get_change_stories` for sftp-connector (10 Nov 10:00Z to 11 Nov 10:45Z) and `source:change_tracking` events for the sftp and config services returned nothing. (8) Last prod deployments on the failing path: config-service 5 Nov, dedupe-service 5 Nov, replay-service 5 Nov, collector 9 Nov 09:59Z, snap-adapter 10 Nov 13:14Z (GitHub deployments, `terraform-prod`). The failure is raised inside sftp_connector before any of those.
- Customer notification: the only customer-facing effect found is the file landing in `error/`. The "Record dropped" and "File routed" lines carry `audience: support`. A query for notification or email services and messages for WILDSMITH over 24 h returned nothing. Slack search for "WILDSMITH after:2026-11-10" returns only this alert. shopify-connector logged receipt of the failure event and answered `POST /events/failures/sales-order` 202; I did not establish what it does with it.
- Still firing: monitor status Alert at 10:44Z (`search_datadog_monitors`). No `Records failed CSV validation` log after 10:38:42Z and no warn/error sftp_connector log for WILDSMITH after 10:39Z. The monitor's 15-minute window clears at about 10:53:42Z.
- Flapping: Datadog `source:alert` events for this monitor over 7 days hold only this trigger.
- Maintenance/: latest records are 2026-11-04 (test DBs, window 4 Nov 09:00Z) and 2026-11-04 emergency patch (window 5 Nov 10:00Z); none covers 11 Nov 10:38Z, and the failure is not a Snap failure.
- Waypoint `Engineering/sftp-connector/known-context.md`: nothing on this failure mode; notes that references only come from mapping and that an unmapped or blank column fails ingest validation. `wp stale` flags architecture, interfaces, operations and overview as behind source; not relied on. Customers vault `Customers/WILDSMITH/`: no `known-context.md`; `overview.md` is generated from config (1 sftp connector, SNAP backend, last verified 2026-10-22) and `ledger.md` is empty.
- Other WILDSMITH failures in replay-service (SO-29625, SO-29606: `ShipContacts.Phone` too long; SO-29578 and earlier: SNAP mandatory fields) are separate snap-adapter rejections from earlier days, not part of this alert.

## Not established
- Why the row's columns are shifted. The raw CSV was not read (no access, and it holds customer data). A delimiter inside an earlier field of that row is a lead, not a finding. A customer export fault versus a parse edge case in the connector is not settled; the evidence above (same file, same version, 1 failing file in 1308) points at the row, not at a release.
- Whether anyone has told WILDSMITH. No log or Slack evidence either way; email and support tickets were not checked.
- What shopify-connector does with the failure event it received.
- The version `sftp_host` serves in prod (not queried; the failure is in the connector).

## Outcome
Real but minor, P4. One customer row is malformed and rejected; 3 of the 4 orders in the file are in SNAP; `SO-29733` is not, and its failure is held in replay-service as not replayable until the data is fixed. Support needs to get WILDSMITH to correct and resend `SO-29733` only. No regression indicated, no escalation.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794393630093619
- Monitor: https://app.datadoghq.com/monitors/324087068
- Replay failure: a770384f-1ed7-4ac5-90c7-2e327d602cda
