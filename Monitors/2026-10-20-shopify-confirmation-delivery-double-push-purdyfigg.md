---
tags: [datadog-triage]
date: 2026-10-20
monitor: "[FUSE][Egress] Shopify confirmation delivery failing (fulfilment / order-tag) + [FUSE][Platform] Elevated production error rate (2m window)"
service: shopify-connector
business_id: PURDYFIGG
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792507804126269"
opened_at: "2026-10-20T14:48:49Z"
resolved_at: "2026-10-20T14:54:12Z"
minutes_spent: 5
severity_assessed: P4
flapping: false
outcome: real_minor
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# PURDYFIGG goods-out batch pushed twice to shopify-connector; second push failed on already-fulfilled orders

## Fired
303425509 (Shopify delivery failing, metric 6 > 5 in 15m) at 14:48:49Z and 180072217 (prod error rate >2 in 2m) at 14:49:37Z; 180072217 recovered 14:51:37Z. One cause.

## Investigation
- Poller confirmation poll 14:48:03Z, correlationId `1d3386ba-ac99-4521-b0e4-7c8a327148e3`, announced 14 PURDYFIGG goods_out confirmations.
- shopify-connector got two `POST /events/confirmations/sales-order` pushes (Google IPs 35.187.141.161 and 34.98.142.33), both 202 at 14:48:46Z.
- First push: 14x "Confirmation dispatched successfully" + 14x published to `confirmation_made` — all orders fulfilled.
- Second push: 14 failures 14:48:38–46Z — 8 "fulfillment order CLOSED" (warn-level), 6 "Invalid fulfillment order line item quantity requested." (error; = monitor value 6). Replay-service stored all 14 (e.g. `f607bd20-7754-4f28-8981-af939f26ad80`, shipment PURDA14369C36CB despatched 14:46Z, attempts 0, empty replayHistory).
- Not a replay: replay_service today shows only `GET /api/v1/failures/*` outside ingest; no redrive.
- Not Redis / Shopify: no Redis errors since 13:30Z; no Shopify auth/429/5xx.
- Error-rate monitor window also held 1 snap_adapter PURDYFIGG #6531052 `cancelled_in_wms` (known).
- Not established: why it was pushed twice. Lead: Pub/Sub redelivery — first push ran ~40s vs Terraform `ack_deadline_seconds = 20` on the goods_out_confirmation subscription (shopify-connector `pubsub.tf`), second push began ~31s in. Deployed ack deadline and delivery-attempt count not checked.

## Outcome
No customer impact. 14 new PURDYFIGG goods_out_confirmation failures in replay-service (14:48:38–46Z) are junk duplicates — do not replay. Possible follow-up: shopify-connector processing a 14-record batch exceeds the 20s ack deadline, causing redelivery and double fulfilment attempts (not filed; needs confirmation first).

## Links
- Slack thread (Shopify): https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792507804126269
- Slack thread (error rate): https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792507846888979
