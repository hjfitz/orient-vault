---
tags: [datadog-triage]
date: 2026-11-02
monitor: "[FUSE][SFTP Connector] File Upload Failure"
service: sftp-connector
business_id: ESCENTRIC
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793617205387249"
opened_at: "2026-11-02T10:58:49Z"
severity_assessed: P4
flapping: false
outcome: real_minor
ticket:
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: open
---
# SFTP File Upload Failure: ESCENTRIC uploaded an .xlsx; one order from their earlier CSV is held

## Fired
`fuse.file.invalid_type` (monitor 179967409, `sum(last_5m) >= 1`, service sftp_connector, prod) hit 1.0 at 10:58:49Z.

## Investigation
- sftp-connector log 10:58:19Z, warn `File is not a valid type`: `FUSE_ABDAD7F392/to_ilg/create_sales_order/02 11 csv.xlsx` (create_sales_order). Nothing else logged for that file, and no later log for that path through the end of my window. This is the only invalid_type warn in the 10:50 to 11:10 window.
- Same user path, 10:57:20Z: `02 11 csv.csv` (businessId ESCENTRIC, connector conn_1586e51cc79e4d4eb0a14e53ebab78d4, correlationId 6ccaf816-b809-478d-8423-9f1420d6e5af) was validated and emitted. Pipeline summary for that correlationId: 10 sales orders published, 9 "Entity created in SNAP", 1 "Entity creation in SNAP failed" (snap-adapter, order/recordId 15309, HTTP 400, `City` MANDATORY on ADDRESS_UPDATE, ShipAddress Line1 "ID Logistics Germany GmbH"). replay-service "Failure stored" failureId 521c3b1a-3fd3-40c9-b5f8-f1388abed282; dedupe "Dedupe gate held on permanent failure"; sftp-connector "File routed" destination `error`, trigger `failure` at 10:57:26Z.
- So the CSV went to `error/` because of that one order, and about a minute later the customer uploaded an xlsx named like it. Whether the xlsx is a re-send of the same orders is an inference, not checked.
- Ingress, one file. Ran the same `File is not a valid type` count for 14d: 2 occurrences (2026-10-30, a `.csv.filepart` for FUSE_DD2AF79592, and today). Monitor alert events in 14d: 2 triggers (10-30 11:41Z, recovered 11:46Z; today). Not flapping.
- Prior record 2026-09-22 (LISAUK `.filepart`) was the same monitor and same behaviour: reject is correct, upload client's problem.
- No customer known-context.md for ESCENTRIC (folder has overview/ledger only; nothing relevant).

## Not established
- Whether the xlsx is still in the SFTP folder or was archived.
- Whether any corrected CSV for order 15309 arrives later.
- Which SFTP user (businessId) the 10-30 `.filepart` belonged to.
- Deploy correlation not checked in detail: #bifrost-notifications shows sftp-connector prod deploys earlier today, but the reject is the expected filetype rule.

## Outcome
Real, minor. Monitor behaved correctly. Customer to be told only CSV is accepted. Support to fix the missing City on the ADDRESS_UPDATE for order 15309 and replay. Not filed as a ticket.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793617205387249
