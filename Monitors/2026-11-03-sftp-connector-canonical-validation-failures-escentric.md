---
tags: [datadog-triage]
date: 2026-11-03
monitor: "[FUSE][SFTP Connector] Canonical validation failures"
service: sftp-connector
business_id: ESCENTRIC
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793715989379819"
opened_at: "2026-11-03T14:25:08Z"
severity_assessed: P4
flapping: false
outcome: real_minor
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# SFTP canonical validation failures: ESCENTRIC re-uploads a sales order file missing customerRef

## Fired
Monitor 324087068 (log alert, `service:sftp_connector @environment:prod "Records failed CSV validation"` count over 15m > 0, Terraform-managed) triggered 14:25:08Z for ESCENTRIC, create_sales_order, CanonicalSalesOrderSchema, 1 failed row, `order.customerRef: Invalid input: expected string, received undefined`.

## Investigation
- Matching logs (sftp_connector, prod): 14:24:48Z, 14:32:07Z, 14:38:31Z, all ESCENTRIC, file `FUSE_ABDAD7F392/to_ilg/create_sales_order/15320 15321 ABU DHABI CSV.csv`, connector conn_1586e51cc79e4d4eb0a14e53ebab78d4, failedCount 1, same sampleError. correlationIds 4b78437b-a665-444b-8a94-ae55735449cb, d7cff383-d82c-4a0c-b1a6-ecf71c65872b, 6a9774db-1a2a-4d75-a851-e81883c032ae.
- Per attempt: "Records to send resolved" recordCount 0, "Validation failures published" to bifrost.prod.create_data_failure.v1, "File routed" destination `error` trigger `failure`. Each attempt is followed by an "Incoming file event" under `.../create_sales_order/error/`, and the next attempt is a new file event in the source folder with a fresh `created` time (14:24:48.067, 14:32:06.671, 14:38:30.713). No log after 14:38:32Z for the file as of ~14:47Z.
- Downstream per correlationId (services seen: sftp_connector, replay_service, dedupe_service, shopify-connector, collector_service; no snap_adapter): replay_service "Failure stored" failureIds ba985b79-4e21-491d-b92e-579d9c6ab529, 77d104f6-7fa0-4dc1-a8e2-f9c703d6967c, 6b791fa9-80e5-4541-af1c-8bbdca6cb967; dedupe "Record failed validation" recordId unknown; collector "Failure for a record not held"; shopify-connector "No shopifyOrderId found in failure record; skipping tag update".
- Same SFTP user also had a file event for `15303 15304 ABU DHABI.pdf` at 14:31:53Z; earlier today `03 11 CSV IMPORT.csv` at 11:53Z moved to archive/ (no validation failure for it in the monitor query).
- Monitor history (14d logs): 10 matching logs: WILDSMITH x4 (23, 28, 30 Oct), ACADEMIC x1 (27 Oct), LISAUK x2 (2 Nov, test files, replied in earlier threads), ESCENTRIC x3 (today). Alert events last 3d: triggered 2 Nov 15:52Z, recovered 16:07Z, triggered 16:25Z, recovered 16:40Z, triggered 3 Nov 14:25Z. Different businesses and causes, not a flapper. The monitor message's "only occurrence in the past 7 days was one file redelivered 4 times" is out of date against these counts.
- Not a Fuse change: sftp-connector revision 72984d4 serving all three, validation rejects a missing required field.

## Not established
- Which CSV column maps to customerRef, and whether the file holds one or two orders (name suggests 15320 and 15321; failedCount 1, recordCount 0).
- What re-places the file in the source folder after each move to error/ (customer client or person); whether more attempts follow.
- Whether the three replay-service failures hold the order and are replayable (Fuse MCP in this session resolved ESCENTRIC to a staging config, so prod replay-service was not read).
- Whether orders 15320/15321 exist in Snap (no snap_adapter log for these correlationIds, no direct Snap read).
- Whether the 14:31:53Z PDF upload is related to the 14:34Z File Upload Failure alert.

## Outcome
Real, minor (P4), customer data defect, monitor behaved correctly. Support to ask ESCENTRIC to supply the missing customerRef and re-upload. Not filed as a ticket.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793715989379819
- Monitor: https://app.datadoghq.com/monitors/324087068
