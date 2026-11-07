---
tags: [datadog-triage]
date: 2026-11-07
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: shopify-connector
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794070363887309"
opened_at: "2026-11-07T16:51:37Z"
severity_assessed: P3
flapping: true
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Error-rate monitor tripped by a duplicate-attempt Shopify rejection (PURDYFIGG) and 3 tracking-service Firestore contention nacks

## Fired
Monitor 180072217 (more than 2 error lines in 2 minutes). Shortened re-check; the Snap-delay lead was tested and not confirmed as a cause.

## Investigation
- Monitor query run via aggregateLogs 16:45-16:58Z: 7 matches. tracking-service "store failed; nacking for redelivery" x3 (16:51:16, 16:51:25, 16:51:26Z; Firestore "Aborted due to cross-transaction contention", record types goods_out_confirmation x2 and sales_order x1). shopify-connector PURDYFIGG "Shopify fulfillment creation returned errors" x2 and "Confirmation dispatch failed" x2 (16:52:45-46Z, userError "Invalid fulfillment order line item quantity requested.").
- All domain:fuse prod error logs 16:30Z to 16:57Z (no monitor exclusions): the same 7 plus one config-service "Dependency connection failed" at 16:42:31Z. Nothing after 16:52:47Z.
- The two Shopify errors are racing duplicates: each order has one "Confirmation dispatched successfully" log 0.06-0.24 s before the error (orders 14649383518588 and 14650851459452).
- Wider PURDYFIGG pattern: shopify-connector accepts each goods-out batch twice (same correlationId, two "202 Accepted") in 10 of 13 batches 16:30-16:55Z; the second pass finds the fulfilment order CLOSED and replay-service stores a failure (223 "Failure stored" 16:30-16:57Z, 1774 production failures created today per replay-list-failures). The 3 batches accepted once stored no failures.
- Only one failed order has no success log in 7 days: fulfilment order 14650615169404 (batch 16:36Z, CLOSED at first sight, shipment shows shipped equal to ordered).
- Pub/Sub: oldest-unacked max since 16:30Z is 33 s (shopify goods_out sub), 20 s snap_adapter sales_order sub, 14 s fourth; tracking create_record_request sales_order undelivered 242 (16:46-47Z) and 405-409 (16:51-52Z), recovered by 16:53:48Z (monitor 323648858).
- No snap_adapter / snap-polling error logs 16:30-16:57Z other than two known polling warns (stock movement dropped x84, withholding confirmation x14). No held sales_order, purchase_order, master_data, pick or pack since 16:30Z (newest sales_order failure 13:03Z, DOCKBAY).

## Not established
- Whether the 3 nacked tracking events were later stored (event-id search returned no logs).
- Why shopify-connector processes each batch twice.
- Whether FO 14650615169404 is fulfilled in Shopify (no read tool); its tracking deadlineAt (tracking search did not match).
- 5xx count (http.status_code query returned none; attribute naming not confirmed). Config-service 16:42:31Z cause.

## Outcome
Real but minor, P3. No customer impact verified; replay inbox polluted by false held failures. See the egress record for the same cause.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794070363887309
- Monitor: https://app.datadoghq.com/monitors/180072217
