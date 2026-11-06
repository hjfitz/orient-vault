---
tags: [datadog-triage]
date: 2026-11-06
monitor: "[FUSE][Platform] Pub/Sub backlog building (any subscription), collector group"
service: collector
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793998465762949"
opened_at: "2026-11-06T20:53:10Z"
severity_assessed: P4
flapping: true
outcome: self_resolved
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Collector sales_order sub Warn at 20:53Z (peak 502, oldest unacked 1s, 103 a minute later, every push acked)

## Fired
302536090 (warn 200 / crit 1000, `max(last_15m)`), group `subscription_id:collector.prod.create_record_request_sales_order.v1.sub`, Warn P2-priority monitor, value 502, post 20:54:25Z (ts 1793998465.762949), no reply at 20:55Z. Shortened re-check, run at 20:57Z, so Pub/Sub points stop at 20:52Z (undelivered) / 20:53Z (oldest unacked).

Channel read 20:40Z to 20:55Z, all Datadog alert posts:
- 303425509 Shopify confirmation delivery failing, Warn, 1793998205.257039 (20:50:05Z), Bot reply 20:52:38Z.
- 180072217 Elevated production error rate, Triggered, 1793998243.770429 (20:50:43Z), Bot reply 20:52:40Z.
- 302536090 collector group, Warn, 1793998465.762949 (20:54:25Z), no reply (this record).
- 302536090 dedupe group, Recovered, 1793998467.658739 (20:54:27Z), ignored.
The 20:38Z dedupe backlog thread (1793997585.089329) has its reply at 20:47:07Z (record `2026-11-06-pubsub-backlog-dedupe-create-record-request-sales-order-2038z.md`).

## Investigation
- **Backlog and drain (`gcp.pubsub.subscription.num_undelivered_messages` / `oldest_unacked_message_age`, max per minute, collector sub):** undelivered 0 for 20:30-20:50, 502 at 20:51, 103 at 20:52; oldest unacked 0 until 1s at 20:51 and 1s at 20:52, 0 at 20:53. The 20:53+ undelivered points were not yet published (metric lag), so the drain to 0 rests on oldest unacked = 0 at 20:53 and the fall 502 to 103. The peak is 302 over the warn line and about half the 1000 critical. The collector peak was 23 at its highest in the 20:00-20:42 window (earlier record), so this is a larger collector spike than any earlier one today, and still short.
- **Push responses (`push_request_count`, collector sub):** only `ack_201` series exists, per-minute 1374/48 (20:31-32), 1121/60 (20:36-37), 1068/55 (20:41-42), 1051/46 (20:46-47), 1003/24 (20:51-52) plus 48 at 20:50; a query for non-ack classes returns no series. So every push was acked 201 and the pushes arrive in the same 5-minute batches (20:31, 20:36, 20:41, 20:46, 20:51). Earlier batches (20:31 to 20:46) did not back up the collector (undelivered 0).
- **Collector Cloud Run (`collector-prod`):** instances 7 at 20:46, 5 at 20:47-20:54; CPU p99 0.23 / 0.14 / 0.13 / 0.12 / 0.13 (20:46-20:50), memory p99 0.29-0.31; max request concurrency p99 84.75 at 20:46-47 and 84.875 at 20:51 (the same value in the batch that did not back up); request latency p99 790ms (20:46), 868ms (20:51). Non-2xx: one 404 at 20:31 and none since (`gcp.run.request_count`, 20:30 to now). CPU/memory/concurrency points after 20:50 not yet published.
- **Collector logs:** no warn or error level patterns for `service:collector*` in prod 20:30 to 20:56Z (search_datadog_logs, log patterns: 0).
- **Dedupe (same topic):** every push acked 204 for 20:30-20:52 except 503 x1 at 20:36 (the one in the 20:38Z record); no 429 since 20:02; undelivered 0 at every point from 20:39 to 20:52; oldest unacked 0 since 20:39. `fuse.dedupe.mongo.heartbeat_failed` has no data points 20:30 to now; `fuse.mongo.up` for dedupe-service 1 at every 10s point (collector and replay also 1 where reported).
- **Other subs:** peak and oldest unacked over 20:44-now for every prod non-dlt subscription: only collector sales_order sub is elevated (avg of the per-minute max 67); tracking `create_record_request.sales_order` 0/0, dedupe 0/0, snap_adapter sales_order 0/0. Dead-letter: all 22 `*.dlt.sub` average undelivered 0 over 20:30-now and `dead_letter_message_count` has no points.
- **Held records (`replay-list-failures`, production):** sales_order created 6 Nov, replayed:false: 6 total, newest still PURDYFIGG #6679913 (19:55:23Z, Snap "Line1 - Invalid Text", the one in the earlier record), so no new sales_order hold and none lost on this path.
- **New hold, separate pipeline (Shopify egress, not the collector):** PURDYFIGG goods_out_confirmation, Shopify FulfillmentOrder 14648428462460 (#6665513, shipment PURDB6742924289), held twice at 20:52:19.911Z and 20:52:42.071Z, reason "Unable to confirm order: One or more fulfillment orders could not be fulfilled in Shopify." (ids 4e181ad1-f6b5-46f2-92b1-8f17d6c59a6e, f287c450-43d1-4899-9a19-89011cc43325, attempts 0). Matching error logs are the only error-level lines in prod since 20:49Z (shopify-connector, 2 x "Shopify fulfillment creation returned errors" + 2 x "Confirmation dispatch failed" at 20:52:19 and 20:52:42Z, correlation 6b265ff5-0c5d-47fa-bbd9-7bfa2386f0f8). `fuse.confirmation.forward.failure` since 20:49Z = 2. The replay record shows quantities ordered 54, shipped 54. This is after both Shopify thread replies (20:52:38-40Z), which counted 3 holds; replay now holds 5 distinct orders with this reason for 6 Nov (14648314036604, 14650167722364, 14650419806588, 14650485375356, 14648428462460). Not retried, released or replayed.
- **CLOSED class, continuing:** PURDYFIGG goods_out_confirmation holds "FulfillmentOrder ... is CLOSED in Shopify": 1,304 created 6 Nov (replay `search`, createdAt 2026-11-06), against 995 recorded at 20:16Z, a burst of at least 15 at 20:54:40-42Z. Not counted by `fuse.confirmation.forward.failure` (2 since 20:49Z) and not an error-level log (0 logs match "CLOSED" at warn/error since 20:30Z). Already in `2026-11-06-egress-shopify-confirmation-delivery-failing-purdyfigg-invalid-quantity-2016.md`.
- **Monitor:** 302536090 is Terraform-managed (`managed-by:terraform`), `max(last_15m) > 1000` critical with a warn of 200 per the alert text; status Warn at 20:56Z.

## Outcome
Real signal, minor (P4): a 5-minute batch (1,003 messages in the 20:51 minute) pushed the collector sub to 502 undelivered with oldest unacked 1s; every push acked, no collector errors, no dead letters, no dedupe rejections or Mongo heartbeat failures since 20:36Z / 20:00Z, no new sales_order hold. Self-resolved on the evidence available (oldest unacked 0 at 20:53; undelivered 20:53+ unpublished). Not escalated.
Separate, for the Shopify threads: one more PURDYFIGG order (#6665513) held at 20:52Z with the Shopify fulfilment-order rejection, after those threads' replies.

## Not established
- Why this batch peaked at 502 on the collector when the four earlier batches today did not (collector concurrency p99 was the same 85 in the 20:46 batch; saturation points after 20:50 not published yet).
- The undelivered value for 20:53 onward (metric lag), so a full drain to 0 is inferred from oldest unacked 0 at 20:53.
- Cause of the dedupe 429s (20:02) and 503 (20:36), and of the dedupe Mongo heartbeat failures (19:16-20:00), carried from the 20:38Z record.
- Why Shopify rejected #6665513 (no Shopify read tool; SNAP not checked for this order); whether the 5 distinct "could not be fulfilled" holds share a cause.
- Why the CLOSED-class confirmations are held and why the monitor does not count them.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793998465762949
- Monitor: https://app.datadoghq.com/monitors/302536090
- Earlier records: Monitors/2026-11-06-pubsub-backlog-dedupe-create-record-request-sales-order-2038z.md, Monitors/2026-11-06-egress-shopify-confirmation-delivery-failing-purdyfigg-invalid-quantity-2016.md
