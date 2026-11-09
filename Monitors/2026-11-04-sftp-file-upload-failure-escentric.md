---
tags: [datadog-triage]
date: 2026-11-04
monitor: "[FUSE][SFTP Connector] File Upload Failure"
service: sftp-connector
business_id: ESCENTRIC
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793807824725799"
opened_at: "2026-11-04T15:55:49Z"
severity_assessed: P4
flapping: false
outcome: real_minor
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# SFTP File Upload Failure: ESCENTRIC uploaded POLAND TRANSFER exce.xlsx; order 41126 from their CSV is held after a Snap rejection

## Fired
`fuse.file.invalid_type` (monitor 179967409, `sum(last_5m) >= 1`, sftp_connector, prod) hit 1.0 at 15:55:49Z.

## Investigation
- sftp-connector warn `File is not a valid type` at 15:55:10Z, path `FUSE_ABDAD7F392/to_ilg/create_sales_order/POLAND TRANSFER exce.xlsx`, correlationId a2aead82-ea30-4645-b28d-526eee8a9314. Only invalid_type log in the last 2h. Same path's logs show businessId ESCENTRIC, connector conn_1586e51cc79e4d4eb0a14e53ebab78d4.
- Same user, same morning, three files named POLAND TRANSFER:
  - 15:31:59Z `POLAND TRANSFER 231026.csv` (correlationId a602bcfe-c1f8-46af-bcb3-34814736b5a5): validated, emitted, order recordId 41126 stored. snap-adapter "Entity creation in SNAP failed" 15:32:01Z (status 400, `/v2/shipments`, transient false). replay-service holds failure id beffbbf0-d8db-427a-98a5-0458131ee95d, reason "OrderClass - No Check Code Found on line SH70RCX48H; OrderType - No Check Code Found on line SH70RCX48H; ShipmentId - Invalid Shipment on 21 lines (SH70RCXBK9, SH70RCXDCB, SH70RCXEL7 and 18 more)", attempts 0. dedupe "Dedupe gate held on permanent failure". File routed to `error/`.
  - 15:52:29Z `POLAND TRANSFER CSV.csv` (9e3f132d-e086-421a-9b7c-bd803e0d8777): validated, emitted, record 41126 again. dedupe_service warn "Record dropped", reason `duplicate`. dedupe-list (prod): held record 41126, dedupeCount 1, lastDedupedAt 15:52:29Z. So the resend did not reach Snap.
  - 15:55:10Z the .xlsx, rejected by the filetype rule.
- Not flapping: 5 invalid_type logs in 14d (10-30 .csv.filepart FUSE_DD2AF79592; 11-02 x2 and 11-04 xlsx, 11-03 pdf, all FUSE_ABDAD7F392). Monitor alert events in 14d: triggers 10-30 11:41Z, 11-02 10:58Z and 11:10Z, 11-03 14:32Z, 11-04 15:55Z, each recovered ~5 min later. Today: only one trigger.
- Prior record 2026-11-02 (same user, xlsx) reached the same verdict. Monitor behaved correctly.
- Other ESCENTRIC activity today is healthy: CSVs 15322, 15323, 15324, 15325 validated, emitted and routed.

## Not established
- Why the customer sent an xlsx after the dropped resend (timing only, not checked with the customer).
- Whether the xlsx is still in the SFTP folder.
- Which check codes the OrderClass/OrderType rejection refers to (snapResponseBody empty in the log; only the replay-service reason read).
- No "File routed" log found for the 15:52 CSV.
- Whether the 1 further folded firing is a separate log: only one invalid_type log and one trigger event found today.

## Outcome
Real, minor, P4. Monitor correct (reject is expected, customer to be told only CSV is accepted). Separately, order 41126 is held (Snap rejection, replay failure beffbbf0, dedupe gate held). Support to fix the data in Snap or with the customer, release the dedupe record and replay. No ticket filed.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793807824725799
