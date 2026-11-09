---
tags: [datadog-triage]
date: 2026-11-07
monitor: "[FUSE][Egress] Shopify confirmation delivery failing (fulfilment / order-tag)"
service: shopify-connector
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794081189054459"
opened_at: "2026-11-07T19:51:49Z"
severity_assessed: P3
flapping: true
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# PURDYFIGG duplicate-attempt rejections again (6 orders, all already fulfilled); CLOSED holds keep growing

## Fired
Monitor 303425509 Triggered 19:51:49Z (post 19:53:09Z, value 6.0, threshold > 5). Same monitor fired earlier today (Warn 16:52:49Z, Recovered 17:07:49Z) and four times on 6 Nov (20:16, 20:48, 21:06, 21:21Z), so it is a chronic flapper.

## Investigation
- 1 shopify-connector prod error logs 19:00Z-now: 12 lines, all in the 19:51:37-42Z second window, all PURDYFIGG, one correlationId cd93357d-4e4f-4a18-9f0a-ae8cbea0600f. Six "Shopify fulfillment creation returned errors" ("Invalid fulfillment order line item quantity requested.", one FulfillmentOrderLineItem qty 1 each) plus six "Confirmation dispatch failed". No other message, business or error text in the 12.
- 2 All logs for that correlationId (257): 33 "Confirmation dispatched successfully", 6 "Confirmation dispatch failed", 2 "POST /events/confirmations/sales-order 202" (19:51:42.874 and .921). Span 19:51:00.98-19:51:42.92 = 42 s. Each of the 6 rejected fulfilment orders (14654536712572, 14654442504572, 14654305206652, 14654453743996, 14654266835324, 14654543266172) has its own "Confirmation dispatched successfully" in the same correlation, 0.04-0.54 s before the rejection, each with a Shopify Fulfillment id (e.g. gid .../Fulfillment/8732513993084). The 6 rejections are the last 6 of the 39 orders, at +37 s to +42 s.
- 3 Whole day, shopify-connector prod errors: 16 lines = 8 distinct orders (2 at 16:xx, 6 at 19:51), all PURDYFIGG. Every one of the 8 has a success log today. Zero failed orders without a success log. 5,531 PURDYFIGG success logs today.
- 4 Version: the only shopify-connector version logged since 6 Nov 00:00Z is 474d5d55; no deploy since the 6 Nov analysis.
- 5 CLOSED family (replay-service production, search "CLOSED in Shopify", PURDYFIGG, created 7 Nov): 2,744 held failures by 19:54Z (1,774 at the 16:58Z reply), attempts 0. 35 sampled (15 newest, created 19:54:44-46Z, and 20 from offset 1500, 14:41-14:44Z): all 35 have a "Confirmation dispatched successfully" log since 6 Nov. Ordering against the hold time was not checked.
- 6 Carried over from the 16:58Z reply, re-queried: fulfilment order 14650615169404 still has no success log since 1 Nov (only two "Shopify GraphQL response received" at 16:36:21 and 16:36:42Z). Not re-verified in Shopify.
- 7 Slack: no replies in the alert thread 1794081189.054459. The 16:54 thread 1794070446.444079 already carries a reply (16:58:09Z) for this same cause.

## Not established
- Why batches are handled twice. The 20 s ack deadline lead from the 6 Nov record was tested with gcp.pubsub.subscription.expired_ack_deadlines_count: no data returned for 19:30-20:05Z, so it neither confirms nor refutes. Delivery attempts were not observed.
- Shopify-side state of any order (no Shopify read tool), including 14650615169404.
- Whether all 2,744 CLOSED holds are fulfilled orders (35 sampled).
- Whether the 2 POST 202s are two deliveries of the same batch (two 202 lines logged 47 ms apart).

## Outcome
P3 real_minor, repeat of the duplicate-attempt pattern. All 6 rejected orders in this firing, and all 8 today, were fulfilled by their first attempt. No unfulfilled order found from this firing. Nothing replayed, retried or released. Broadcast skipped: same cause already replied to at 16:58Z.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794081189054459
- Earlier thread today: p1794070446444079
- Monitor: https://app.datadoghq.com/monitors/303425509
- Prior: [[2026-11-06-egress-shopify-confirmation-delivery-failing-purdyfigg-redelivery-race-2121]], [[2026-11-07-egress-shopify-confirmation-delivery-failing-purdyfigg-duplicate-batch-1652]]
