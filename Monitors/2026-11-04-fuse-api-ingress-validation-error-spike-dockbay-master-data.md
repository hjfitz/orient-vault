---
tags: [datadog-triage]
date: 2026-11-04
monitor: "[FUSE][Fuse API] Ingress validation-error spike"
service: fapi
business_id: DOCKBAY
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793794465192679"
opened_at: "2026-11-04T12:12:59Z"
severity_assessed: P3
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Ingress validation-error spike: one 50-product DOCKBAY master-data push rejected (nmfcCode null) at 12:12Z

## Fired
Monitor 302685719 (priority 3, Terraform-managed): `sum(last_15m):default_zero(sum:fuse.ingest.validation_errors{service:rest_connector,environment:prod}.as_count()) > 50`. Warn at metric value 50.0 (event 12:12:59Z, thread post 12:14:25Z). Third firing in three days (2 Nov 15:01Z, 3 Nov 13:03Z, now); each earlier one recovered ~15 min later.

## Investigation
- **Tripping value reproduced:** metric `fuse.ingest.validation_errors` 5-min buckets 09:50Z=1, 10:xx=0, 12:10Z=50. The 50 is one log: `Record batch rejected` at 12:12:53Z, count 50, failedCount 50, recordType master_data, correlationId fulfil, connectorId conn_068adb81... (Fuse MCP list-customers: DOCKBAY, "Fulfil.io API Live"). Per-minute rejected-log counts over 3h: 09:54Z 1 (a purchase_order), 12:12Z 1 (the 50-record one); nothing else.
- **Reason:** all 50 records carry `product.identifiers.nmfcCode: expected string, received null` (indices 0-49). Same rest_connector instance accepted the preceding request ("Auth accepted", "Received 50 master-data records" 12:12:53.973Z).
- **Not a routine push:** the connector's hourly master-data polls return `Received 0 master-data records` (e.g. 12:01:54-55Z). Non-empty master-data pushes in 7 days: 25 logs, last before today 3 Nov 15:11Z (1 record); they total 465 records, almost all on 28 Oct (13:00-13:11Z batches plus 127 at 16:50Z).
- **Same customer and field before:** master_data rejections for nmfcCode null on 30 Oct (1), 3 Nov 14:49Z (2 x 1 record); countryOfOrigin null on 28 Oct (75 records). All the same connector; no other connector rejected anything in 14 days (125 rejection logs, one connector).
- **No Fuse change:** a single fapi version 1d72173 across 11,447 rest_connector logs in 48h.
- **Loss / resend:** replay-service list for DOCKBAY has no failure for this batch (newest held failure 11:41Z, a different sales_order cause at snap-adapter). No master-data request from the connector after 12:12:53Z up to 12:15:42Z. No 4xx http status log was found for the rejected POST, so the status returned is not confirmed.
- **Flapping:** not flapping within a day (one firing per day), but recurring daily for this connector since 2 Nov.

## Not established
- Whether DOCKBAY/Fulfil.io resent the 50 products (no request seen up to 12:15:42Z; products not identified in the log, only indices).
- Why nmfcCode is null (what Fulfil.io sends), and which 50 SKUs.
- HTTP status returned for the rejected POST.
- The monitor's Warn threshold (only the >50 critical is in the query).
- Separate DOCKBAY snap-adapter held failures (sales_order ShipAddress.City >30 chars; purchase_order unit/SKU) exist in replay-service; not the cause of this alert and not triaged here.

## Outcome
Real_minor, P3. Customer-side data: DOCKBAY's Fulfil.io pushed 50 products with null nmfcCode and fapi's canonical schema rejected the whole batch at the edge. Not held anywhere in Fuse, so the products only arrive if DOCKBAY resends with nmfcCode populated (or the schema accepts null). No Fuse change, one customer, no flow shown stopped (rest_connector accepted a sales_order confirmation push at 12:14:05Z). Re-check if DOCKBAY keeps pushing nulls or the master-data is needed for upcoming orders.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793794465192679
- Monitor: https://app.datadoghq.com/monitors/302685719
- Related: [[2026-11-02-fuse-api-ingress-validation-error-spike-dockbay]]
