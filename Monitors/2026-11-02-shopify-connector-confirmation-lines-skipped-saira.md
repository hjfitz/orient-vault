---
tags: [datadog-triage]
date: 2026-11-02
monitor: "[FUSE][Shopify Connector] Confirmation lines skipped — prod"
service: shopify-connector
business_id: SAIRA
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793629803436269"
opened_at: "2026-11-02T14:28:56Z"
severity_assessed: P4
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: resolved
---
# SAIRA: despatched HFO line with no Shopify reference skipped twice (14:28Z, 16:46Z)

## Fired
Warn on `fuse.confirmations.lines_skipped` (sum last 1h, businessid:saira) = 1. The monitor warns at >= 1; the critical threshold in the query is 1,000,000. The message defines "skipped" as a despatched line carrying no Shopify reference.

## Investigation
- Log search `service:shopify-connector @environment:prod "Lines with no Shopify reference skipped"` over 7d: exactly 1 log, 14:28:37Z, SAIRA, shipment SAIR6C40040ECD4, order/fulfillmentOrder 14664046379383, `goods_out_confirmation`, skippedSkus [HFO], skippedCount 1 of totalLines 7, shop fb1ba1.myshopify.com. Not a kit-component skip (that reason is not what this log says).
- Same shipment/correlation (607885f1-...): `Confirmation dispatched successfully`, `Confirmation processed`, `Record published to topic` and `POST /events/confirmations/sales-order 202` at 14:28:38-39Z. No error logs. The rest of the order was dispatched.
- Metric `fuse.confirmations.lines_skipped` over 14d, all businesses: one point (15:00 bucket 14:00Z, 1, saira). No repeat, no other business.
- SAIRA shopify-connector warn/error patterns 24h: 88 `Confirmation dispatched successfully` vs 1 skip; other warns are `DDP rules unavailable for business` (3007) and `Shopify GraphQL retried after transient failure` (132), unrelated to this monitor.
- Monitor created 2026-10-12; prior firing the same day (12 lines, 9 orders, see 2026-10-12 record). Metric history shows no other firings in 14d, so not flapping. `search_datadog_events` for the monitor returned nothing.
- shopify-connector merged PRs this week: #355 Renovate (merged 09:49Z), #357 follow-redirects. Running revision shopify-connector-prod-cr-00061-rct, version 8266733. Nothing tied to this skip established.

Not established: whether HFO is on Shopify order 14664046379383 (Shopify not readable); whether the Snap line is a warehouse-added zero-price item as on 12 Oct (fuse MCP unavailable, 401, so no Snap connection to read); whether #355 changed behaviour.

## Second firing, 16:46Z
- Warn again at 16:46:56Z (group businessid:saira). Logs `Lines with no Shopify reference skipped` since 14:00Z: exactly 2. (1) 14:28:37Z shipment SAIR6C40040ECD4, order/fulfillmentOrder 14664046379383, skippedSkus [HFO], 1 of 7 lines. (2) 16:46:16Z shipment SAIRC6182311894, order/fulfillmentOrder 14675642024311, skippedSkus [HFO], 1 of 4 lines. Both goods_out_confirmation, shop fb1ba1.myshopify.com, connector conn_ff3c0a00..., revision shopify-connector-prod-cr-00061-rct, version 8266733 (commit of 27 Oct, #354).
- Same SKU, different shipments and orders. Not growing: 2 lines in total, metric 14d by businessid = saira only, 1 + 1 (14:00 and 16:00 buckets).
- Both confirmations dispatched: for 14675642024311 `Confirmation dispatched successfully`, `Record published to topic`, POST /events/confirmations/sales-order 202 at 16:46:16-18Z. Each order id has one dispatched and one skip log today, so no re-announce loop. SAIRA error logs since 14:00Z: 0. SAIRA dispatches per hour 28, 28 (14Z), 23, 18 (partial).
- Fuse change: the running version (8266733, 27 Oct) was the same at both firings, and #355 and #357 (merged 2 Nov 09:37-09:49Z) are not in it (main head 5af8a198 is later). No deploy between the two firings. No change in the running code since the 12 Oct burst established.
- Log search over 30d returns only today's 2; the 12 Oct burst is not in the indexed window, so the history comes from the 12 Oct record.

Not established (second firing): whether HFO is on either Shopify order; whether HFO is a warehouse-added item (Fuse MCP 401, no Snap read); why HFO now twice today after no skips between 12 Oct and today (the log window cannot show it).

## Outcome
Real but minor: two HFO lines skipped on two orders, both confirmations still delivered, no loop, no errors. Monitor working as designed. Ops to check HFO against orders 14664046379383 and 14675642024311 in Shopify. No ticket.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793629803436269
- Monitor: https://app.datadoghq.com/monitors/331502396
