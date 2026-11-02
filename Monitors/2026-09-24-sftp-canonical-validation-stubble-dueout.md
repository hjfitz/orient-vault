---
tags: [datadog-triage]
date: 2026-09-24
monitor: "[FUSE][SFTP Connector] Canonical validation failures"
service: sftp-connector
business_id: STUBBLE
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790244370924869"
opened_at: "2026-09-24T10:05:08Z"
resolved_at: "2026-09-24T10:15:00Z"
minutes_spent: 10
severity_assessed: P4
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: a5533af9-6c8f-4c08-aab9-53c76f9fbfce
status: resolved
---
# STUBBLE sales-order files arriving as order lines with no order header (surfaced as missing dates.dueOut)

## Fired
Monitor id `324087068` triggered at 10:05:08 UTC on `service:sftp_connector "Records failed CSV validation"` — a genuinely rare monitor per its own message (only one prior occurrence in 7 days).

## Investigation
- Pulled the 5 triggering log lines directly: all `businessId:STUBBLE`, `recordType:create_sales_order`, files `260924110442876SO.csv`–`260924110442880SO.csv` delivered together at 10:04:41-42 UTC, each with exactly 1 row failing `CanonicalSalesOrderSchema` on `dates.dueOut: Invalid input: expected date, received undefined`.
- Checked 30 days of STUBBLE history for this same error — this is the first occurrence; not a chronic/recurring gap for this business.
- Checked memory ([[feedback_dueout_required_by_design]]): `dates.dueOut` is required by design on sales orders (2026-07-30, Harry's call) — the connector correctly rejects rows missing it. Same failure class previously hit LISAUK and DISCOVERED in 2026-07, both resolved via a CONNECTOR_MAPPING rule/default for that business, not a platform change.
- Confirmed via Fuse MCP `get-business-config` that STUBBLE (Stubble & Co) has one active SFTP connector (`conn_9758e49936e64060b314b4cebc82c0ff`) with `sales_order` among its use cases — did not pull the mapping rules themselves (out of scope for read-only triage).
- Checked for a Customers vault folder for STUBBLE — none exists yet.

## Outcome
Real but minor and correctly-handled: 5 sales-order rows dropped at the connector boundary and published to `create_data_failure` (held for replay, not lost), isolated to one business, first occurrence. Not a platform defect — the schema is working as designed. Posted the verdict to the thread with the LISAUK/DISCOVERED precedent and recommended a support/config follow-up (map or default `dueOut` in STUBBLE's mapping, or have STUBBLE's export start sending it), offering to make the config change but holding off pending Harry's confirmation. No ticket filed (not a platform bug).

Follow-up (13:48 BST): per Harry, DMed [[Tom Dunn]] (as Harry) the 5 failing filenames + SFTP error-folder location + the dueOut explanation, asking him to confirm with STUBBLE whether their export should send a due-out date or whether we default it in the connector mapping. Files not attached (no Slack file-upload path available from the agent). Thread updated (broadcast) noting the handoff.

## Correction (13:55 BST)
Pulled the 5 files from `gs://sftp-connector-prod-storage/FUSE_E5A356978A/to_ilg/create_sales_order/error/`. The earlier "missing dueOut" diagnosis was incomplete: every data row is an order **line only** (`oOrderLines_*` columns: line number, product, qty, price), with **every order-level column blank** (OrdRef1, addresses, contact, Service, DueOutDate). `dueOut` was just the first validation to fail. A CONNECTOR_MAPPING default would NOT fix it, so the LISAUK/DISCOVERED precedent doesn't apply. It's a STUBBLE export problem (order header dropped, lines sent alone). SKUs mostly `SC.EB20.BLACK`. Correction sent to Tom (DM) and broadcast in the thread; Harry attached the zip of the files to the DM himself.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790244370924869
- Monitor: id 324087068
- DM to Tom: https://gfsdeliver-eng.slack.com/archives/D0AM9957WTS/p1790253286380299
- Thread update: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790253291548559
- DM correction: https://gfsdeliver-eng.slack.com/archives/D0AM9957WTS/p1790255345474329
- Thread correction: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790255345716869
