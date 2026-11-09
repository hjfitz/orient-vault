---
tags: [datadog-triage]
date: 2026-11-06
monitor: "[FUSE][SFTP Connector] File Upload Failure"
service: sftp-connector
business_id: LISAUK
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793965266063869"
opened_at: "2026-11-06T11:39:49Z"
severity_assessed: P4
flapping: false
outcome: false_positive
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# SFTP File Upload Failure: LISAUK `.csv.filepart` temp file rejected; the real CSV in the same second was processed and created in Snap

## Fired
`fuse.file.invalid_type` (monitor 179967409, `sum(last_5m) >= 1`, sftp_connector, prod) tripped at 11:39:49Z, value 1.0. Monitor still Alert at ~11:42Z (inside its 5m window).

## Investigation
- sftp-connector warn `File is not a valid type` at 11:39:42Z, path `FUSE_84B6F5A152/to_ilg/create_sales_order/RE 26 seeding UK.csv.filepart`, correlationId 9725381e-1dac-4f53-848a-8013d87f9706. Only invalid_type log in 24h (aggregate by @filePath: 1). Business LISAUK (from the same user's other logs, connector conn_01af9d943bc848bcaf5674c30df5cb07).
- Same second, same user: `RE 26 seeding UK.csv` (correlationId a2f7f069-b03a-48f5-87db-06b4653b0f0e) validated, emitted, 200 OK, routed to archive. Downstream for that correlationId: 182 records published, 182 "Entity created in SNAP" (snap_adapter), 0 error-status logs; 4 warns, all "File routing deferred to an in-flight claim; redelivering" (retryable).
- Not the 11-04 pattern. 11-04 was ESCENTRIC FUSE_ABDAD7F392 sending real .xlsx/.pdf files. This is a transient `.filepart` upload artefact (SFTP client temp name) rejected while the upload finished and the CSV landed. Same shape on 10-30 (FUSE_DD2AF79592 `Stock Release Batch-6.csv.filepart`; the real CSV in that path then logged "File routed").
- invalid_type history 14d: 7 logs, 10-30 (1, .filepart DD2AF79592), 11-02 (2 xlsx), 11-03 (1 pdf), 11-04 (2 xlsx), 11-06 (1 .filepart). No other business affected today.
- replay-list-failures (prod, LISAUK): newest 2026-11-02 16:24Z ("TEST for RE 2.csv"), nothing today. All 43 failures created today are PURDYFIGG goods_out_confirmation (10:50Z, unrelated). dedupe-list (prod) LISAUK sales_order today: stored records for correlationId a2f7f069 with dedupeCount 0, so nothing blocked. No repeat upload of the same file.
- Unreplied alert threads since 10:52Z in #bifrost-notifications: 1793964403.685289 (Warn, backlog not draining, 11:26:43Z) and this alert 1793965266.063869.

## Not established
- Whether the 1 further folded firing is a separate event: one invalid_type log and one trigger event (11:39:49Z) found today.
- Why the connector sees the `.filepart` file (client or SFTP-server rename behaviour): not checked.
- Whether all 182 Snap-created orders are complete: Snap not queried, only "Entity created in SNAP" counts.
- Whether the 8 in-flight-claim warns in 3h (4 on this correlationId) carry any impact.

## Outcome
Monitor tripped on a `.filepart` temp file, not a customer sending the wrong filetype. Nothing held, customer's CSV processed. P4, false positive (monitor counts partial-upload temp files as invalid type; recurrence 10-30 and 11-06). Noted for monitor owners; no ticket filed.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793965266063869
