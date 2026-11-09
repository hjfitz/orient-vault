---
tags: [datadog-triage]
date: 2026-11-06
monitor: "[FUSE][Egress] Shopify confirmation delivery failing (fulfilment / order-tag)"
service: shopify-connector
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793996283726359"
opened_at: "2026-11-06T20:16:49Z"
severity_assessed: P3
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Shopify fulfilment rejected for one PURDYFIGG order (invalid line quantity); not the CLOSED class

## Fired
Monitor 303425509 (warn >1, critical >5 over 15m of fuse.confirmation.forward.failure + fuse.order.tags.update.failure) went Warn at metric value 2.

## Investigation
- Metric: forward.failure = 2 in the whole last 24h (one 15m bucket, 20:10-20:25Z); tags.update.failure = 0 (execute_code queryTimeseriesData).
- Logs (service:shopify-connector @environment:prod status:error, 24h): 4 lines, all PURDYFIGG recordId 14648314036604 (Shopify FulfillmentOrder), correlation 9b8c3a01-bcba-407f-8f91-412be6a4c52b, at 20:16:26 and 20:16:43Z. Shopify userError: "Invalid fulfillment order line item quantity requested." for lineItems FulfillmentOrderLineItem/39058374459772 qty 1 and /39058374492540 qty 2. The same "Invalid fulfillment order line item quantity requested" error occurred 2 Nov 07:48Z for two other orders (14627077292412, 14626586329468; both still held in replay), and nowhere else in 7 days. No error or warn lines after 20:17Z at 20:20Z.
- Order: PURDYFIGG #6664368, SNAP shipment PURDBE21DB8396A on ilg005. SNAP Stage 90, despatched 20:15:14, EVRI T08HLA0000983134. Level 00 line FG1569X_V1: QtyOrdered 1, QtyShipped 2 (one box, productQuantity 2); line FG1209D_V2 ordered 1 shipped 1. Fuse tracking: despatchState confirmation_failed, goods_out not delivered, 2 attempts.
- Replay holds the record twice (ids 6febf31b-..., df08d233-..., attempts 0, replayable true, extensions.shopify.fulfillmentId present on both Level 00 lines). SNAP DESPATCH unprocessed queue at 20:20Z does not hold SPLU117050, so it is not looping.
- Different from the CLOSED class: replay holds 998 PURDYFIGG failures created 6 Nov UTC, 995 are "FulfillmentOrder ... CLOSED in Shopify", 995 distinct recordIds each held once, bursts every ~10m (23 in the 20:16 minute at snapshot). Neither feeds this monitor (forward.failure 2 in 24h). Sample of 2 CLOSED orders (#6663155, #6672590): both have a delivered goods_out event (20:16:30-31Z) before the CLOSED delivery_failed at 20:16:44Z, and SNAP shows despatched 20:15.
- repair-shopify-confirmation does not apply: fulfilment ids are present, no loop, and the failure is a quantity rejection (not "no fulfillment ID").

## Not established
- Shopify-side state of #6664368 (no Shopify read tool): whether the order is still unfulfilled and what quantity its fulfilment order line holds.
- Why SNAP shipped 2 of a line ordered 1 (warehouse action or kit pack) and that this is why Shopify rejected it.
- Why CLOSED confirmations are delivered twice, and whether all 995 had a prior delivery (2 of 995 checked).
- Why the monitor does not count the CLOSED holds.

## Outcome
Real, minor: one order despatched in SNAP but not marked fulfilled in Fuse tracking, held in replay. Support to confirm the over-ship with the warehouse and fulfil or correct #6664368. No retry/replay done.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793996283726359
- Monitor: https://app.datadoghq.com/monitors/303425509

## Re-check 20:51Z (second firing, thread https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793998205257039)
Monitor went Warn again at 20:48:49Z, value 3.
- Metric since 20:30Z: fuse.confirmation.forward.failure = 3, all businessid purdyfigg; fuse.order.tags.update.failure = none (get_datadog_metric scalar).
- Error logs since 20:17Z: 6 lines, all 20:48:45-47Z, correlation 73dd2884-9243-46ae-aaf0-5e1365308281: "Shopify fulfillment creation returned errors" userError "Invalid fulfillment order line item quantity requested." plus "Confirmation dispatch failed", for 3 Shopify records 14650167722364 (#6672868, SNAP PURD04AEF6FAF2B), 14650419806588 (#6675091, PURDA4F2F767CE2), 14650485375356 (#6675725, PURD65BC2640924). One attempt each; no errors after 20:48:47Z through ~20:51Z. Same userError text as the 20:16Z order, not auth, rate limit, 5xx or order-tag.
- Dispatch outcomes since 20:30Z: 245 "Confirmation dispatched successfully", 3 "Confirmation dispatch failed".
- SNAP (ilg005, read-only): PURDA4F2F767CE2 and PURD04AEF6FAF2B Stage 90, despatched 20:47:53-56Z; Level 00 line ordered 1 shipped 1 on both (FG1209D_V2, FG1527D_V1), plus Level 20 kit components. Replay record of PURD65BC2640924 shows the same shape (Level 00 ordered 1 shipped 1). So NOT the 20:16Z over-ship (ordered 1 shipped 2). Only common point: each has one Level 00 line carrying extensions.shopify.fulfillmentId plus kit_component lines (and the 20:16Z order had a line FG1569X_V1; #6672868 carries FG1569X_V1 as a component qty 3, the other two do not).
- Replay (production): 3 new holds goods_out_confirmation, failurePoint confirmation.delivery_shopify, attempts 0, replayable true (ids fea8467b-f11c-4c19-854f-052ea138c231, 3561f93c-0f14-4a83-9579-8a19a4c05006, 63901b23-f80e-437f-941f-6ecd3041cba6). Replay now holds 5 such records for 2026-11-06 (4 orders), 2 for 2 Nov, plus older ones from 20 Oct (66 matching in total).
- Platform monitor 180072217 (thread p1793998243770429) fired 20:49:37Z on these same 6 lines (its query for 20:45-20:52Z returns exactly them, 20:48Z bucket only).
- Not retried, released or replayed.

### Not established (re-check)
- Shopify-side fulfilment order line quantities for the 3 new orders (no Shopify read tool), so why Shopify rejected them is unknown; the SNAP over-ship explanation does not fit these.
- Why 245 other confirmations in the same window succeeded.
- Whether more orders will fail in later batches.
