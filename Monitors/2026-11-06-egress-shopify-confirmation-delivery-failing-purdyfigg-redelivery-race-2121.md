---
tags: [datadog-triage]
date: 2026-11-06
monitor: "[FUSE][Egress] Shopify confirmation delivery failing (fulfilment / order-tag)"
service: shopify-connector
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794000182752329"
opened_at: "2026-11-06T21:21:49Z"
severity_assessed: P3
flapping: true
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# PURDYFIGG quantity rejections are mostly a redelivery race; 2 over-shipped orders are really unfulfilled

## Fired
Monitor 303425509 Warn at 21:21:49Z (post 21:23:02Z, value 2.0), Recovered 21:22:49Z (post 21:24:06Z). Earlier today: Warn 20:16, Recovered 20:31, Warn 20:48, Triggered 21:06 (value 6). Same monitor, same cause, 7th pattern occurrence since 23 Sep (see Links). The 21:23 post is the tail of the 21:06 burst.

## Investigation
- 1 Matching errors since 21:00Z (shopify-connector prod error logs): 12 lines = 6 orders, all PURDYFIGG, all 21:06:45-51Z, one correlationId b0fdb149-7ac4-4026-8194-181cdbf7446d. Every one is "Shopify fulfillment creation returned errors" + "Confirmation dispatch failed", Shopify userError "Invalid fulfillment order line item quantity requested." Each sent one FulfillmentOrderLineItem qty 1. This is the quantity family. No CLOSED text, auth, rate-limit or 5xx. No error log 21:07-21:30Z. fuse.confirmation.forward.failure = 6 in the 21:06 minute only (queryTimeseriesData, 1 min); fuse.order.tags.update.failure no points. 309 PURDYFIGG "Confirmation dispatched successfully" since 21:00Z.
- 2 The 6 orders (FulfillmentOrder ids 14648380195196 #6665115, 14650986529148, 14650606813564, 14648339464572, 14650178568572, 14648252170620) each ALSO have a "Confirmation dispatched successfully" with a Shopify Fulfillment id (e.g. gid .../Fulfillment/8730179764604 for the first) and "Record published to topic" in the same correlation, 12-300 ms before the rejection. Tracking timeline of #6665115 has delivered:goods_out (21:06:45.243Z) and delivery_failed (21:06:45.314Z). So these orders are fulfilled; the rejection is a second, concurrent attempt at the same confirmation.
- 3 Position in batch: the poll announced 40 confirmations (21:06:03Z, snap-polling-service); shopify-connector processed them one after another from 21:06:08.6 to 21:06:52.5 (43.9 s). The 6 rejections are positions 34-39 of 40 (+36.7 s to +43.3 s). The 20:48 batch (39 orders, 38.8 s): the 3 rejections are positions 37-39. Subscription ack_deadline_seconds = 20 for goods_out_confirmation (iac/shopify-connector pubsub.tf on origin/main; deployed value not checked). Two POST /events/confirmations/sales-order 202s per batch (e.g. 21:06:52.532 and .706).
- 4 Whole day, PURDYFIGG: 4,494 confirmations announced, 4,255 success logs, 13 reject log pairs. 13 = 11 distinct orders (two orders attempted twice, 17-23 s apart). 9 of 11 have a success log for the same fulfilment order (3 at 20:48, 6 at 21:06). The 2 Nov pair (14626586329468, 14627077292412) also had success then rejection within 30 ms.
- 5 The 2 without a success log: #6664368 (FO 14648314036604, 20:16Z, SNAP PURDBE21DB8396A) and #6665513 (FO 14648428462460, 20:52Z, SNAP PURDB6742924289). Both attempts failed on both orders, no success log all day. Tracking get-shipment: goods_out deliveredAt null, despatchState confirmation_failed, attempts 2, deadlineAt 22:16:06Z and 22:52:06Z. Both are over-shipped: tracking lines show ordered 1 shipped 2 on FG1569x_V1 (#6664368, units ordered 2 shipped 3) and on FG1302x_V1 (#6665513, units ordered 5 shipped 6). The logged request carried qty 2 for one line item in each (39058374492540 x2; 39058595774844 x2).
- 6 Common factors: nothing about the order separates the racing orders from the ~4,250 successes, because those orders succeeded (same connector, one Shopify connector for the business per get-business-config, same store, kit_component lines present on #6665115). What separates them is position at the tail of a long batch. The two truly unfulfilled orders share an over-ship (shipped > ordered on one line).
- 7 CLOSED family (replay-service, production, search "CLOSED in Shopify"): 1,557 holds created 6 Nov (first 07:06:38Z), 644 on 5 Nov, 1,065 on 2 Nov (first 07:26:40Z), 0 on 1 Nov. 5 CLOSED holds created 21:20:42-43Z (FO 14649034146172, 14650218119548, 14651340456316, 14648851464572, 14650609631612) each have a success log at 21:20:24-28Z, 15-18 s earlier. Plus 2 sampled by the earlier triage. So CLOSED holds for these are the later, redelivered copy hitting an already-fulfilled order. Tracking-stats delivery_failed events per day: 2 Nov 1,068; 3 Nov 666; 4 Nov 205; 5 Nov 644; 6 Nov 1,570; attention 8,090.
- 8 Code (shopify-connector origin/main 84714fc): handler sums `shipped` of non-kit_component lines per Shopify FulfillmentOrderLineItem id, drops zero quantities, one fulfillmentCreate per fulfilment order. State check: status FULFILLED returns alreadyFulfilled (success, made re-published); ON_HOLD/CLOSED/CANCELLED throws ConfirmationNotDeliverableException "is CLOSED in Shopify", recorded as a business_rule failure, not counted in forward.failure (counted only for other exceptions). So a re-sent confirmation for an order Shopify reports as CLOSED is recorded as a failure, not as already fulfilled. The monitor only sees the quantity-rejection race, not the CLOSED duplicates.
- 9 Deploys/changes: no config_change audit events 1 Nov 12:00Z - 2 Nov 08:00Z; get_change_stories empty; GitHub deployment records show no shopify-connector prod deploy between 30 Oct 15:53Z and 2 Nov 09:37Z and no snap-adapter prod deploy before 2 Nov 11:16Z, so none precedes the first CLOSED hold (2 Nov 07:26Z). Deployment records show creation, not outcome. Despatch volume (tracking-stats despatched): 31 Oct 1,020; 1 Nov 1,085; 2 Nov 3,491; 3 Nov 3,578; 4 Nov 1,915; 5 Nov 2,980; 6 Nov 4,210.
- 10 Prior occurrences of this pattern: 2026-10-20 double push (14 orders, 8 CLOSED + 6 quantity; same lead), 2026-10-14, 2026-10-02, 2026-09-29, 2026-09-23.
- 11 Alert threads with no reply since 21:00Z (Recovered posts ignored): 1793999284.700559 (this monitor, Triggered 21:08:04), 1793999324.483979 (Platform error rate 180072217, 21:08:44), 1794000182.752329 (this alert).

## Not established
- Shopify-side state of any order (no Shopify read tool): whether #6664368 and #6665513 are still unfulfilled, and the fulfilment-order line quantities.
- That Pub/Sub redelivery causes the duplicate attempt: delivery attempt count and the deployed ack deadline were not observed. The timing fits (batch 39-44 s vs a 20 s deadline; rejections at the batch tail) but the redelivery itself is not seen.
- Whether all 1,557 CLOSED holds are fulfilled orders: 7 sampled (5 here, 2 earlier), all had an earlier success. Distinct count of CLOSED orders not computed.
- Why 239 announced confirmations today have no success log (4,494 announced vs 4,255 successes).
- Why the monitor read 2.0 at 21:23 when the metric has no points after 21:06.
- Whether over-ship is rare among the successes.
- Why onset was 2 Nov 07:26Z and not 1 Nov (volume rose 1,085 to 3,491; not shown to be the cause).

## Outcome
P3 real_minor. 2 PURDYFIGG orders (#6664368, #6665513) appear unfulfilled in Shopify (over-shipped), confirmation deadline 22:16Z and 22:52Z. 9 of 11 rejected orders today were fulfilled by the first attempt. Support: check the 2 orders in Shopify and fulfil or correct, do not replay/retry/release. Engineering: hypothesis only, see HYPOTHESIS in the reply. Nothing retried, released or replayed.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794000182752329
- Earlier threads today: p1793996283726359 (20:16Z), p1793998205257039 (20:48Z), p1793999284700559 (21:08Z)
- Monitor: https://app.datadoghq.com/monitors/303425509
- Prior: [[2026-11-06-egress-shopify-confirmation-delivery-failing-purdyfigg-invalid-quantity-2016]], [[2026-10-20-shopify-confirmation-delivery-double-push-purdyfigg]], [[2026-10-14-shopify-confirmation-delivery-failing-purdyfigg]]
