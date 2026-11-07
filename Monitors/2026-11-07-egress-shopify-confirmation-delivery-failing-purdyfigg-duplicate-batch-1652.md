---
tags: [datadog-triage]
date: 2026-11-07
monitor: "[FUSE][Egress] Shopify confirmation delivery failing (fulfilment / order-tag)"
service: shopify-connector
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794070446444079"
opened_at: "2026-11-07T16:52:49Z"
severity_assessed: P3
flapping: true
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Egress monitor: duplicate batch delivery makes the second attempt fail on already-fulfilled PURDYFIGG orders

## Fired
Monitor 303425509 warn (value 2 over 15m, warn above 1, critical above 5).

## Investigation
- fuse.confirmation.forward.failure since 16:40Z: 2, businessid purdyfigg. shopify-connector warn/error logs since 16:40Z: 2 "Shopify fulfillment creation returned errors" and 2 "Confirmation dispatch failed", both orders in correlation f4f1925b, userError "Invalid fulfillment order line item quantity requested." (quantity family). No order-tag failure metric data seen.
- Both orders had a success log first (14649383518588 at 16:52:45.727Z, error 45.964Z; 14650851459452 at 46.875Z, error 46.934Z): a duplicate attempt racing the first.
- The CLOSED family is the bulk: replay failures "Fulfillment order ... is CLOSED in Shopify, so it cannot be fulfilled", 33 in batch f4f1925b alone, 223 since 16:30Z, logged at info so they never reach the error monitors. Every failed order in 16:30-16:55Z has a success log except FO 14650615169404.
- Each goods-out batch is accepted twice (same correlationId) in 10 of 13 batches; batches accepted once have no failures. Replay hourly failure-stored vs success today: e.g. 15:00h 244 vs 498, 16:00h 298 vs 478.
- FO 14650615169404 (shipment PURDB01A67FDB2F, shipped 16:35:09Z, canonical ordered 10, shipped 10, so not over-shipped): CLOSED at first sight 16:36:21Z, no success log in 7 days, two held failures (16:36:22, 16:36:42Z). Tracking deadlineAt not retrieved.

## Not established
- Why batches are delivered twice. Whether FO 14650615169404 was fulfilled earlier or closed another way. Its deadlineAt. SNAP shipped greater than ordered was not checked in SNAP itself (canonical only).

## Outcome
Real minor P3: no genuine failure verified except one order needing a Shopify check; held replay failures are false and must not be replayed.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794070446444079
- Monitor: https://app.datadoghq.com/monitors/303425509
- Related: 2026-11-07-platform-elevated-prod-error-rate-shopify-duplicate-attempt-tracking-contention-1651.md
