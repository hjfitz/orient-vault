---
tags: [datadog-triage]
date: 2026-11-05
monitor: "[FUSE][Fuse API] Ingress validation-error spike"
service: rest_connector
business_id: DOCKBAY
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793874203306189"
opened_at: "2026-11-05T10:21:59Z"
severity_assessed: P3
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Ingress validation-error spike: one 136-product DOCKBAY master-data push rejected (nmfcCode null) at 10:21Z

## Fired
Monitor 302685719 (priority 3, Terraform-managed, tags service:rest_connector): `sum(last_15m):default_zero(sum:fuse.ingest.validation_errors{service:rest_connector,environment:prod}.as_count()) > 50`. Metric value 136.0, triggered 10:21:59Z, Slack post 10:23:23Z (ts 1793874203.306189, no thread replies when read). Fourth firing in four days (2 Nov 15:01Z, 3 Nov 13:03Z, 4 Nov 12:12Z, now); the first three each recovered about 15 min later (Datadog alert events).

## Investigation
- **Tripping value reproduced:** metric `fuse.ingest.validation_errors` (service:rest_connector, environment:prod) 5-min bucket 10:20Z = 136, the only point returned for 06:00Z to 10:23Z. It is one log: `Record batch rejected` at 10:21:08.134Z, count 136, failedCount 136, recordType master_data, correlationId `fulfil`, connectorId conn_068adb81... ("Fulfil.io API Live" on DOCKBAY, Fuse MCP list-customers production). Preceding logs in the same request: "Auth accepted" 10:21:08.111Z, "Received 136 master-data records" 10:21:08.112Z.
- **Same business, record type and field as 4 Nov, different batch:** all 136 records (indices 0-135) carry `product.identifiers.nmfcCode: expected string, received null`. 4 Nov's batch was 50 records at 12:12:53Z with the same error. Master-data rejection history for this connector (14d): 28 Oct countryOfOrigin null (12+48+15 records), 30 Oct nmfcCode null (1), 3 Nov nmfcCode null (1+1), 4 Nov nmfcCode null (50), 5 Nov nmfcCode null (136). No other connector has a master_data rejection in 14d.
- **Not the hourly poll:** the connector's hourly POSTs to /api/v2/master-data returned 202 (e.g. 10:01:30-31Z, 09:00:15Z). The rejected push arrived at 10:21:08Z, off the hour.
- **fapi version differs from 4 Nov, but the same rejection occurs on both:** api-gateway-prod version 09ac2c3c (first log 4 Nov 17:19:46Z; last log of the previous 1d72173 at 17:18:05Z). The 4 Nov 12:12Z rejection and today's both reject on nmfcCode null, so the version change does not explain it.
- **Loss / resend:** replay-service (production) lists no DOCKBAY failure after 4 Nov 22:02:27Z (a sales_order ShipAddress.City cause), and the only DOCKBAY master_data failures held are 4 from 28-29 Sep (SKUId too long, unrelated). Across all businesses, replay-service holds nothing created on 5 Nov except PURDYFIGG goods_out_confirmation failures (07:24Z/07:00Z). rest_connector logged nothing for the connector after 10:21:08.134Z up to the 10:24Z check. No HTTP status log exists for the rejected POST, so the status returned is not confirmed.
- **Flapping:** monitor events show Warn/Alert then Recovered for 2 Nov, 3 Nov, 4 Nov, each one firing per day; this is the fourth consecutive day. The causes of the 2 Nov and 3 Nov firings were not checked in this triage.

## Not established
- Whether DOCKBAY/Fulfil.io resends the 136 products (only 3 min of logs after the rejection when checked); which SKUs they are (the log carries indices only).
- Why nmfcCode is null (what Fulfil.io sends).
- HTTP status returned for the rejected POST.
- Whether the 50 products from 4 Nov were ever resent successfully (not checked).
- The monitor's Warn threshold; when this firing recovers.

## Outcome
Real_minor, P3. Same customer-side data problem as 4 Nov, on a larger batch: DOCKBAY's Fulfil.io pushed 136 products with null nmfcCode and fapi's canonical schema rejected the whole batch at the edge. Nothing is held in replay-service, so the products reach Fuse only if DOCKBAY resends with nmfcCode populated (or the schema is changed to accept null). One customer, no Fuse-side fault found, and rest_connector served other traffic (202s from the same connector earlier that hour). Re-check if DOCKBAY keeps pushing nulls; the pattern of daily rejections on this connector may warrant raising with the customer.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793874203306189
- Monitor: https://app.datadoghq.com/monitors/302685719
- Related: [[2026-11-04-fuse-api-ingress-validation-error-spike-dockbay-master-data]], [[2026-11-02-fuse-api-ingress-validation-error-spike-dockbay]]
