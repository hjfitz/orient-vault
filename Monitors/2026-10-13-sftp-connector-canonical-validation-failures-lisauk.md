---
tags: [datadog-triage]
date: 2026-10-13
monitor: "[FUSE][SFTP Connector] Canonical validation failures"
service: sftp-connector
business_id: LISAUK
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791883870440439"
opened_at: "2026-10-13T09:30:08Z"
resolved_at: "2026-10-13T09:36:00Z"
minutes_spent: 6
severity_assessed: P3
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: 4fc06c6b-d424-4da8-b551-fb874e9c6e96
status: resolved
---
# LISAUK file "UK Concealer  WAVE 2.csv": 51/51 sales-order rows fail on dates.dueOut

## Fired
Monitor 324087068 (log alert, any `Records failed CSV validation` line in 15m) fired at 09:30:08Z. The trigger log is LISAUK, create_sales_order, CanonicalSalesOrderSchema, 51 failed rows, sample error `dates.dueOut: Invalid input: expected date, received undefined`.

## Investigation
- Trigger log, correlationId `8890c6b4-e6c4-4aa6-a9d5-cfd5b5d70c9e`: file `UK Concealer  WAVE 2.csv` arrived 09:29:33Z, `Records validated` validCount 0 / invalidCount 51. All 51 `validationErrors` entries are `dates.dueOut`. Message counts for that correlationId: 51 `Record dropped`, 51 `POST /events/v1/create_data_failure - 204`, 12 `...create_data_failure - 500` (each followed by `File routing deferred to an in-flight claim; redelivering`, then retried).
- Mapping (config-read `/api/v1/connectors/conn_01af9d943bc848bcaf5674c30df5cb07`, production): LISAUK `sales_order` maps `DueOutDate` to `dates.dueOut` (and `dates.shipment`), `ExpDelDate` to `dates.delivery`, with no default for any of them.
- Held record (replay-get-failure `be1e9488-4f36-48cf-867d-0b88bc793869`): address, contact, SKUs and shipping method are all mapped, but `dates: {}`, `replayable: false`, `blockingIssues` = dates.dueOut. So `DueOutDate` was absent or empty in the row.
- Held in replay-service: replay-list-failures (LISAUK) offsets 0-50 are all this transaction; offset 51 is an older, unrelated record, so exactly 51 held, `attempts: 0`. LISAUK also carries older unrelated Snap "City - MANDATORY" failures (7-8 Oct), not part of this alert.
- Regression check: DDSQL on `Records validated` for create_sales_order over 5d. On the same build `28c514e`, STUBBLE 223 valid / 0 invalid, EPARFUM 33/0, SPORTLUX 45/0, WILDSMITH 11/0. LISAUK's earlier files (30 Sep to 9 Oct, 76 log groups) were all valid. LISAUK's earlier files used the name pattern `LISAUK_SO - ...`; this one does not.
- Newer LISAUK files since 09:31Z: none (DDSQL, empty).
- Flapping/history: monitor events over 30d show triggers on 28 Sep, 29 Sep, 1 Oct, 6 Oct, 8 Oct, 9 Oct and 13 Oct (first 18 of 33 events read), almost all single-row failures for other businesses. Each trigger recovered by itself about 15 minutes later, so it is a per-event monitor, not a flapper. The monitor message's "only occurrence in 7 days" text is stale.
- Is it us: no. Vendor: no (the failure is at our canonical boundary, before Snap).

## Outcome
P3, real_minor. One customer's file lacks `DueOutDate` values, so 51 orders (`W2LCPRUK1` onwards) are held in replay and none reached Snap. Recovery is a corrected resend from the customer, or support adding `dates.dueOut` to the held records via replay. Nothing was changed. Verdict posted to the thread with broadcast.

Not established: whether the `DueOutDate` column is missing or just blank (the CSV was not read). Customers/LISAUK is not onboarded (`cust locate`: onboarded false), so no known-context to say whether the wave-file format is a known pattern. Why 12 `create_data_failure` POSTs returned 500 before succeeding was not examined.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791883870440439
- Monitor: https://app.datadoghq.com/monitors/324087068
