---
tags: [datadog-triage]
date: 2026-11-02
monitor: "[FUSE][SFTP Connector] Canonical validation failures"
service: sftp-connector
business_id: LISAUK
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793634807363069"
opened_at: "2026-11-02T15:52:08Z"
severity_assessed: P4
flapping: false
outcome: real_minor
ticket:
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: open
---
# LISAUK `TEST for RE.csv`: 1 sales order failed canonical validation (missing quantities)

## Fired
Log monitor 324087068 (`service:sftp_connector @environment:prod "Records failed CSV validation"`, last 15m, count > 0). Tripped on a single log at 15:52:01Z: business LISAUK, recordType create_sales_order, schema CanonicalSalesOrderSchema, failedCount 1, `shipmentLines.0.quantities: Invalid input: expected object, received undefined`.

## Investigation
- Correlation 6d7f5c13-5c8b-4b2f-8265-bb1fdf28b698, file `FUSE_84B6F5A152/to_ilg/create_sales_order/TEST for RE.csv`, connector conn_01af9d943bc848bcaf5674c30df5cb07. Sequence: Records failed CSV validation, Record dropped, Validation failures published (failedCount 1), Records to send resolved recordCount 0, Emitting records recordCount 0, File routed destination `error`, POST create_data_failure 204. The only row failed, so the whole file went to `error/` and nothing was published to the bus.
- Only LISAUK in the last 60 min (that monitor query over 14d returns 6 logs, the other 5 are 10-23 to 10-30). ESCENTRIC does not appear in it, so this is unrelated to the ESCENTRIC upload failure.
- LISAUK's 14 other files since 10-20 (incl. 5 earlier today, last 14:06Z, version 707ee92, same build as the failure) each emitted 1 record (one file 140) and were archived. Same mapping works for them.
- No further LISAUK sftp-connector logs after 15:52:02Z at query time (about 15:54Z): no re-upload yet.
- Monitor event history (14d): 5 distinct triggers, each recovering ~15 min later: 10-23 (WILDSMITH master_data), 10-27 (ACADEMIC purchase_order), 10-28 (WILDSMITH), 10-30 (WILDSMITH), 11-02 (LISAUK). Different businesses, repeated WILDSMITH pattern (`product.lifecycle.life` expected int, `dimensions.box.height` NaN). Not a flapper. The monitor message's "only occurrence in the past 7 days ... 8/242 rows" text is stale.
- Fuse-side regression: sftp-connector master commits since 10-26 are infra, Renovate and audit fixes (e.g. 8473e5f, 707ee92 SFTP VM backend, c26e0e3 LB), none touch mapping or validation; and LISAUK's other files validate on the same revision. Failing field set is a single order line with no quantities.

## Second firing 16:25Z (thread https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793636783919299)
- Log at 16:24:15Z, correlation 0e7a6d94-eef4-49f5-84f2-15b014f06f55: LISAUK, conn_01af9d943bc848bcaf5674c30df5cb07, file `FUSE_84B6F5A152/to_ilg/create_sales_order/TEST for RE 2.csv`, create_sales_order, CanonicalSalesOrderSchema, failedCount 1, identical error `shipmentLines.0.quantities: expected object, received undefined`. Same sequence as the first: Record dropped, Validation failures published, recordCount 0, File routed `error`, create_data_failure 204. Only row failed, so whole file to `error/`, nothing published.
- Same customer, same connector, new filename (`TEST for RE 2.csv`), 32 min after `TEST for RE.csv`: a retry with the same defect, not a different customer. Only these 2 "Records failed CSV validation" logs exist in the 45 min to 16:27Z, both LISAUK.
- Nothing successful since: LISAUK's last good file was 14:06Z (SPACE NK, archived, recordCount 1). Real LISAUK_SO files at 10:54, 12:24, 13:46, 14:06Z all emitted 1 record and archived; only the two TEST files failed.
- Deploy: failure 1 ran on 707ee92 (rev 00116), failure 2 on c26e0e3 (rev 00117, "Serve prod SFTP's static IP through the load balancer", merged 15:52:09Z). Infra only, and failure 1 predates it with the same error, so the deploy does not explain the pair.
- Not established: the real feed on the new revision (no real LISAUK file since 14:06Z), which source column is empty, replay-service holding (Fuse MCP 401).

## Outcome
Customer data problem on one file: the order's first line had no quantities after mapping. Rest of file: there was none (1 row). The customer must fix and resend the order if it is real; the filename suggests a test but that is not established. P4, no ticket.

## Not established
- Whether the `create_data_failure` record is held in replay-service (Fuse MCP unavailable, 401).
- Whether the file is a genuine order or a test, and which source column was empty/renamed (file content not inspected).
- Whether LISAUK resends later.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793634807363069
- Monitor: https://app.datadoghq.com/monitors/324087068
