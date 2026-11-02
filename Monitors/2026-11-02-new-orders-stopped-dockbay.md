---
tags: [datadog-triage]
date: 2026-11-02
monitor: "[FUSE][Platform] New orders stopped for {{businessid.name}} (businessid:dockbay)"
service: fapi
business_id: DOCKBAY
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793624585917139"
opened_at: "2026-11-02T13:01:58Z"
severity_assessed: P3
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: open
---
# New orders stopped for DOCKBAY: no sales-order POSTs reached fapi after 10:43Z

## Fired
Monitor 334504858 (priority 3, Terraform-managed). Query: min over 3h of (10 x same hour last week's fresh sales_order count, minus a huge multiple of this hour's count) >= 5, per businessid. It fires when every hourly bucket in the last 3h has zero fresh sales orders while the same hours last week each had at least one; the message's "quietest had 10" is last week's minimum. No weekend or time-of-day logic beyond week-over-week comparison. Alerted 13:01:58Z.

## Investigation
- fuse.dedupe.event.fresh (sales_order, dockbay, hourly, 8 days): last fresh orders 10:00Z hour (3); nothing in 11:00 or 12:00Z. Previous 8 days had no zero hour between 09:00 and 22:00Z. Today 08:00/09:00Z had 1/1 against 5-13 on recent weekdays; Mon 26 Oct 08-12Z was 2/7/12/21/36. fuse.dedupe.event.duplicate for dockbay: no data (not records arriving as duplicates).
- Ingress: last inbound POST /api/v2/sales-orders for DOCKBAY (rest_connector/fapi, 202, correlationId fulfil) at 10:43:48Z. None since. fuse.ingest.records_emitted (api-gateway, dockbay, sales_order): 1 / 1 / 3 in 08:30-10:30Z buckets, then zero. Last create_acknowledge routing log (sftp_connector service) 10:43:53Z; no later ingest of any kind from DOCKBAY. Which channel carried that order is not established beyond the fapi POST.
- Inside Fuse: 0 fapi 4xx/5xx request log lines, 0 status:error/warn rest_connector logs in 3h; fuse.ingest.validation_errors (api-gateway) no data in 8h; 0 auth-failure lines. The only DOCKBAY error in 26h is snap_adapter "Entity creation in SNAP failed" sales_order at 09:21:21Z. DOCKBAY traffic that is flowing now is confirmation egress (confirmation/ready, clear-down, ~222 rest_connector lines in the last hour).
- Wider: other businesses' fresh sales orders normal 08-12Z (purdyfigg 12-45/h, stubble 8-22/h, eparfum, saira, escentric, wildsmith). DOCKBAY is the only business whose REST sales-order stream stopped.
- Config and deploys: no non-GET config-service log lines mentioning DOCKBAY in 72h; GETs only (business, shipment_methods at 10:43:48Z, storefront at 11:23Z). fapi last prod deploy 2026-10-20 (GitHub deployments). Deploys today to dedupe-service (09:37, 09:57Z), collector (09:16, 09:44Z), config-service (10:13, 11:27Z); the order stream was still flowing after the earlier ones, so none line up with a stop at the REST edge.
- D monitors (monitor search): D1, D4, D5, D6, D9, D10, D11, L2 OK; D2, D3, D7, D8 Alert (master data and purchase orders, not sales orders).

## Not established
- Whether any DOCKBAY calls reached the api-gateway and were rejected before app logging: Cloud Run api-gateway-prod shows 4xx bursts (33 in the 11:00Z half hour, 8 at 12:30Z, 10 at 13:00Z) that I could not attribute to a business or path, and no log lines carry them.
- Why the customer stopped (Fulfil.io side, their own order volume, credentials) and whether Dock and Bay know.
- Whether the 09:21Z failed order is still held (replay-service not queried); the CustomerRef-over-20 cause and the 30 Oct City failure come from the request context, not from a query I ran.
- Fuse MCP was down (401): no lookup-service, get-business-config or audit-search; the DOCKBAY Customers folder has no known-context.md (config snapshot only).

## Outcome
P3 real_minor, Fuse-side stop not found: fapi received no sales-order requests from DOCKBAY after 10:43Z and logged no rejections; the pipeline downstream is healthy for other customers. For a live customer a 2.3h daytime gap is out of pattern for the last 8 days, so DOCKBAY should be asked whether Fulfil.io is still sending. Re-check if the edge 4xx turn out to be DOCKBAY; that would turn this into rejected orders and a P2 call.

## Follow-up: are the api-gateway 4xx DOCKBAY orders rejected at the edge?
- gcp.run.request_count for api-gateway-prod from 10:40Z: every 4xx is HTTP 404 (revision 00042-zdf), 1-3 per 10 min with 28 in 11:20Z and 10 in 13:00Z. No 401, 403, 413 or 429. 202s continue (3 in each of 11:00, 12:00 and 13:00Z buckets).
- The 4xx pre-date the stop: the earlier 30-min series had 21 (06:30Z), 91 (07:30Z), 59 (09:30Z) when DOCKBAY orders were still being accepted (fresh sales_order 1/1/3 in 08-10Z). A 404 burst is therefore not specific to 10:43Z.
- fapi/rest_connector logs carry no 4xx lines, and Cloud Run request logs are not in Datadog, so no 404 could be attributed to a path, client or API key. A POST to /api/v2/sales-orders with a valid route returned 202 earlier, but that does not show what the 404s were.
- Since 10:43Z, rest_connector logged 9 POST /api/v2/master-data, 202, python-httpx/0.28.1, correlationId fulfil, at about :01 each hour (11:01 x3, 12:01 x3, 13:01 x3). Those lines carry no businessId and fuse.ingest.records_emitted shows no master_data records for any business, so they are not attributed to DOCKBAY. DOCKBAY's own requests since 30 Oct were all python-httpx (878 lines). Same client signature, authenticated and accepted.
- No fapi commits since 31 Oct and no core-infra commits (gh). The api-gateway repo name was not found, ilg-platform and gateway Terraform/WAF/API-key rotation not checked.
- Not established: what the 404s are; whether DOCKBAY's hourly master-data posts carry records.
- Result: no evidence the 4xx are DOCKBAY rejections; severity stays P3.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793624585917139
- Monitor: https://app.datadoghq.com/monitors/334504858
