---
tags: [datadog-triage]
date: 2026-10-14
monitor: "[FUSE][SFTP Connector] Canonical validation failures"
service: sftp-connector
business_id: DISCOVERED
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791966250290459"
opened_at: "2026-10-14T08:23:08Z"
resolved_at: "2026-10-14T08:30:00Z"
minutes_spent: 7
severity_assessed: P3
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: 4fc06c6b-d424-4da8-b551-fb874e9c6e96
status: resolved
---
# DISCOVERED PO file 142909-2.csv: 1 order fails on lines.*.quantities (not LISAUK)

## Fired
Monitor 324087068 (any `Records failed CSV validation` line in 15m) fired at 08:23:08Z. Trigger log: DISCOVERED, create_purchase_order, CanonicalPurchaseOrderSchema, 1 failed row, `lines.0-4.quantities: expected object, received undefined`. Not the LISAUK business from yesterday.

## Investigation
- Trigger log, correlationId `47102394-c167-42e2-9910-b779022edb83`: file `FUSE_1A6CEE3E09/to_ilg/create_purchase_order/142909-2.csv` at 08:22:44Z, `Records validated` valid 0 / invalid 1, `create_data_failure` 204. Same build `28c514e` as yesterday.
- Held record (replay-get-failure `d680cf5b-37ab-4788-9678-0f399a01a269`, production): PO `EU0000836404`, 5 lines, attempts 0, `replayable: false`. Lines have `skuId` `DBR-`, no line number and no quantities, and `dates.dueIn` is the 1970 epoch.
- Mapping (config-read `/api/v1/connectors/conn_2a904fd2413d4f61aa733fe5d341050c`, production): `purchase_order` reads `iOrderLines_Qty` into `quantities.ordered/advised`, `concat('DBR-', iOrderLines_ProductID)` into `skuId` and `iOrderLines_LineDelDate` into `dates.dueIn`. The held record is therefore consistent with every `iOrderLines_*` value arriving empty.
- Same filename `142909-2.csv` was ingested via `create_sales_order` as valid 1/0 at 2026-10-13 13:50Z, 14:05Z and 2026-10-14 08:24:11Z (DDSQL on `Records validated`, fileName filter, 3d). The only other DISCOVERED PO file in 30d, `DB PO MG019.csv` (2 Oct), validated 1/0.
- Monitor history: events show a trigger 13 Oct 09:30Z (LISAUK), recovery 13 Oct 09:45Z, trigger 14 Oct 08:23Z (3d window). Not flapping. The monitor message's "only occurrence in 7 days" text is stale. 30d failure log lines by business/type: WILDSMITH master_data 3, MANUCURIST sales_order 3, SHACKLETON PO 1, LISAUK sales_order 1, DISCOVERED PO 1.
- Is it us: no. Failure is at our canonical boundary on the customer's file. Vendor: no (never reached Snap).

### LISAUK follow-up from 2026-10-13
- Still held: replay-list-failures LISAUK production, createdAt 2026-10-13 with search "expected date": total 51, attempts 0, all `UK Concealer  WAVE 2.csv`. Nothing changed. No LISAUK failures created today (createdAt 2026-10-14: total 0), and no LISAUK ingests today in the DDSQL listing.
- Probably superseded: `UK Concealer  WAVE 2 NEW.csv` arrived 2026-10-13 10:12:49Z, valid 51 / invalid 0, and its correlationId `8115fcc0-2b26-4682-b487-5e277d4e71d0` logged 51 `Entity created in SNAP`. Matched on count only, order refs not compared.
- Repeat pattern: replay createdAt 2026-09-22 with the same `dates.dueOut` error: total 156, all `UK Concealer seeding CSV.csv`, attempts 0. So LISAUK has 207 held rows (51 + 156), same cause, from "UK Concealer" files lacking `DueOutDate`; both times held and never replayed. Total of LISAUK search "expected date" is 207 (replay-list-failures). Other older LISAUK holds (Snap City MANDATORY, 401 auth, confirmations) are unrelated.

Not established: CSV content (columns missing vs blank, or a sales-order file dropped in the PO folder; matching filename is consistent but not proof). Whether DISCOVERED has since resent a corrected PO. Whether the 51 resent LISAUK orders equal the 51 held. 22 Sep LISAUK ingest logs (not retrievable in Datadog, only replay records). Customers/DISCOVERED and Customers/LISAUK exist but are config snapshots with no known-context.md, so no customer-specific history to check.

## Outcome
P3, real_minor. One DISCOVERED purchase order held in replay, none reached Snap; recovery is a corrected resend by the customer. LISAUK's 51 rows from yesterday are still held but look superseded by the resend; 156 older rows with the same cause are also held. Nothing changed (read-only). Verdict posted with broadcast. No ticket filed. Suggested for the team: confirm and clear the LISAUK holds, and consider whether LISAUK's mapping should default `dates.dueOut`.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791966250290459
- Verdict reply: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791966385158399
- Monitor: https://app.datadoghq.com/monitors/324087068
- Prior record: Monitors/2026-10-13-sftp-connector-canonical-validation-failures-lisauk.md
