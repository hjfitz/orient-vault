---
tags: [datadog-triage]
date: 2026-10-14
monitor: "[FUSE][Egress] Shopify confirmation delivery failing (fulfilment / order-tag)"
service: shopify-connector
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791977152607419"
opened_at: "2026-10-14T11:24:49Z"
resolved_at: "2026-10-14T11:40:16Z"
minutes_spent: 15
severity_assessed: P3
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: 4fc06c6b-d424-4da8-b551-fb874e9c6e96
status: open
---
# Three PURDYFIGG goods-out confirmations rejected by Shopify, one attempt each

## Fired
Monitor 303425509 went Warn at 11:24:49Z (metric value 2.0 at notification). `fuse.confirmation.forward.failure` was 3 in the 11:24Z bucket.

## Investigation
- Confirmed: 6 error logs 11:24:45-51Z, all shopify-connector prod (`e9aef9e`), all PURDYFIGG, one correlationId `94244d57-e32e-4cbe-afb0-8e873a9d113e`. Three goods_out_confirmations, each "Shopify fulfillment creation returned errors" + "Confirmation dispatch failed".
- Confirmed: Shopify userError is `Invalid fulfillment order line item quantity requested.` on FulfillmentOrders 14556083093884, 14556092367228, 14556141420924. A line item id was sent (14556141420924: `FulfillmentOrderLineItem/38874172817788`, qty 1), so not the missing-fulfilment-id case. The same run dispatched 15 other confirmations successfully.
- Confirmed: one failure each in replay-service (`2662350c-cc8c-4a32-bdae-2c56fd1f3d96`, `875bc245-5998-4c20-b753-cd3cbf83b977`, `4a5a2477-da77-46f3-9cfe-ff859e71e267`), attempts 0, replayable true, stage `confirmation_ready`. The record for `14556141420924` is shipment `PURDFC0CA6ED557`, queueId `SPLU065066`.
- Confirmed: no shopify-connector error logs after 11:24:51Z, checked to 11:40Z. That is longer than the ~12 min retry cycle seen in the 10-02 PURDYFIGG loop, so not looping so far. `SPLU065066` is not among the 7 unprocessed SNAP outbound rows read at ~11:40Z.
- Confirmed: SNAP shipment `PURDFC0CA6ED557` is a normal full despatch (kit FG1209D_V2 ordered 1, shipped 1, stage 90, closed 11:24:01Z).
- Confirmed: no `Confirmation dispatch failed` logs between 2026-10-09 16:00Z and 2026-10-14 11:24Z. The 7-9 Oct firings were the SAIRA loop (1,098 failures, last 10-09 15:38Z). Not flapping now.
- Customer context: vault `Customers/PURDYFIGG/known-context.md` has no entry for this error. Its `confirmationsEnabled: false` row (verified 09-02) is stale, since confirmations are flowing.

## Not established
- Why Shopify rejects qty 1 on these line items. Lead only: already fulfilled/closed in Shopify. No Shopify access, FO states unchecked.
- Whether the other two shipments (`PURDF1F43BD4CBD`, `PURDF1C56F8FE32`) are normal despatches; only `PURDFC0CA6ED557` was read in SNAP.
- The monitor's configured warn threshold (value 2.0 fired Warn; `>5` is the critical query).

## Outcome
P3, real-but-minor, PURDYFIGG only, 3 orders, not escalated, verdict posted with broadcast. Nothing retried, repaired or cleared. Owed: check the three FO states in Shopify, then either `replay-retry` (if still unfulfilled) or dismiss the replay failures (if already fulfilled). No ticket filed.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791977152607419
- Prior PURDYFIGG triage of this monitor: [[2026-10-02-shopify-confirmation-delivery-failing-purdyfigg]]
