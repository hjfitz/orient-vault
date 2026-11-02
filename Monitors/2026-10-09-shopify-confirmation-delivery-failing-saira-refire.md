---
tags: [datadog-triage]
date: 2026-10-09
monitor: "[FUSE][Egress] Shopify confirmation delivery failing (fulfilment / order-tag)"
service: shopify-connector
business_id: SAIRA
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791560393747039"
opened_at: "2026-10-09T15:38:49Z"
resolved_at: "2026-10-09T15:42:00Z"
minutes_spent: 4
severity_assessed: P3
flapping: true
outcome: real_minor
escalated_to:
ticket:
session_id: 0a6fab47-9201-4b91-aea7-e306bf321ad2
status: open
---
# Shopify confirmation delivery warn re-fire: two NEW SAIRA orders, same missing-fulfillment-ID error

## Fired
Monitor 303425509 re-warned at 15:38:49Z (value 2.0, warn 1, crit 5), about three hours after the three looping SAIRA orders were cleared from the SNAP queue.

## Investigation
- Confirmed: the morning loop is dead. Prod `Confirmation dispatch failed` was 15/hr to 11:00Z, 7 in the 12:00Z hour, then zero from 13:00Z to 15:00Z.
- Confirmed: this firing is 2 failures at 15:38:08-09Z on two orders that had never failed before, `14510735327607` and `14507353145719`. Same error `Unable to confirm order: Line item has no fulfillment ID`, same connector (`conn_ff3c...`), prod `1d71e08`. Other SAIRA confirmations in the same poll dispatched fine. `fuse.order.tags.update.failure` empty; no other prod business failing (the GADG series seen in an unfiltered metric query is non-prod).
- Confirmed: SAIRA's SNAP outbound queue holds two unprocessed DESPATCH rows (SIOB001035 / SIOB001036, created 16:40 BST), so a ~12 min retry loop is likely.
- Hypothesis, not verified: same SNAP-only price-0 line gap as the morning (FUSE-1118), possibly tied to the SKU-less price-0 lines on SAIRA #37125-37127 seen on the create path. The two orders were not matched to shipments or lines.

## Outcome
P3, real-but-minor, new instance of the known cause class. Verdict posted in-thread with broadcast. Nothing changed. Owed: `repair-shopify-confirmation` classification of the two new orders before any queue clear, the SNAP-only-line mechanism on FUSE-1118, and the warn-threshold retune in `observability`.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791560393747039
- Earlier record this morning: [[2026-10-09-shopify-confirmation-delivery-failing-saira]]
- Ticket: FUSE-1118 (existing, not commented)
