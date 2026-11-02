---
tags: [datadog-triage]
date: 2026-09-22
monitor: "[FUSE][SFTP Connector] File Upload Failure"
service: sftp-connector
business_id: LISAUK
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790087451928359"
opened_at: "2026-09-22T14:17:35Z"
resolved_at: "2026-09-22T14:52:19Z"
minutes_spent: 35
severity_assessed: P4
flapping: false
outcome: real_minor
ticket:
session_id: a52d6f5c-f563-4fcb-9e52-064d9270f089
status: resolved
---
# SFTP Connector File Upload Failure — LISAUK `.filepart` uploads

## Fired
`fuse.file.invalid_type` tripped twice (15:18 & 15:30 BST) for `service:sftp_connector, environment:prod` — an incorrect filetype uploaded to the SFTP connector, only CSV expected.

## Investigation
Resolved the connector logs for both correlationIds: both are business **LISAUK** (SFTP user `FUSE_84B6F5A152`, resolved via `config-read` on its Primary SFTP connector), use case `create_sales_order`. Both uploaded filenames genuinely end in `.filepart` (`UK Concealer seeding CSV.csv.filepart`, `...V2.csv.filepart`), not `.csv`. Confirmed in `sftp-connector` source (`code/src/gcs/storage.service.ts:328-337`) that `deriveFiletype()` takes the last dot-segment of the filename as the type — `filepart` isn't in the accepted `csv/json/jsonl` set, so the reject is correct behaviour, not a connector bug. Neither correlationId shows a later successful receipt of the same file under its real `.csv` name. Checked monitor history: this monitor has fired exactly twice in the last 7 days — both are these two events, so not a flapper.

## Outcome
No platform fix needed — this is LISAUK's own upload client/process leaving files in a partial-upload (`.filepart`) state, never completing the rename to `.csv`. Posted a summary reply in the alert thread; no ticket filed (monitor behaved correctly, no defect found). Worth a support nudge to LISAUK to check their upload tooling completes the rename step after transfer.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790087451928359
