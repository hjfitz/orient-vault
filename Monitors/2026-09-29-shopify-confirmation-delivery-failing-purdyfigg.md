---
tags: [datadog-triage]
date: 2026-09-29
monitor: "[FUSE][Egress] Shopify confirmation delivery failing (fulfilment / order-tag)"
service: shopify-connector
business_id: PURDYFIGG
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790670292165699"
opened_at: "2026-09-29T05:08:00Z"
resolved_at: "2026-09-29T09:32:00Z"
minutes_spent: 24
severity_assessed: P3
flapping: true
outcome: real_minor
ticket: "https://globalfreight.atlassian.net/browse/FUSE-1118"
session_id: 269a178b-2b8f-4765-892c-66ce15aec7f4
status: resolved
---
# Shopify confirmation delivery failing (fulfilment / order-tag) — monitor 303425509

## Fired

Monitor 303425509 alternated Warn/Recovered every ~3 minutes in #bifrost-notifications from at least 05:08 through 09:24 UTC (visible history checked back further via the underlying metric, which held a steady ~1/interval baseline for 2+ days). Query: `sum(last_15m):default_zero(sum:fuse.confirmation.forward.failure{environment:prod}.as_count()) + default_zero(sum:fuse.order.tags.update.failure{environment:prod}.as_count()) > 5`, metric value oscillating 1.0–2.0 (well under the critical threshold of 5) — the warning threshold is evidently much lower.

## Investigation

Confirmed real, not noise: `service:shopify-connector status:error @businessId:PURDYFIGG "Confirmation dispatch failed"` recurs on almost every SNAP poll cycle (~12 min), all with the same shipment/order. Pulled the full error + stack trace for one instance (correlationId `dbf656c5-1281-44cd-93da-b4bd42759d7c`, 08:20:07Z):

`ConfirmationException: Unable to confirm order: Line item has no fulfillment ID`, thrown from `SalesOrderConfirmationHandler.getLineItemsFromMappings` (`apps/shopify-connector/src/core/confirmations/sales-order-confirmation.handler.ts:342`) for PURDYFIGG shipment `PURD133D2FB4FD8` / customer order `14425863324028` / SKU `FG1151` (line role `standard`, not a kit component).

Confirmed isolated to this one order — other PURDYFIGG confirmations in the same poll batches (e.g. order `14484447756668`) dispatched to Shopify successfully in the same run, and Shopify's own GraphQL API responded healthily throughout. Confirmed there's no held failure record: `replay-list-failures` (prod, PURDYFIGG, searched the order id) returned 0 results — the per-record throw is swallowed by `Promise.allSettled` and never reaches `confirmation_data_failure`, so nothing clears the SNAP-side outbound queue entry and it just re-announces forever.

Duplicate check surfaced **FUSE-1118** ("shopify-connector: unmappable line item aborts entire confirmation instead of being skipped") — an exact match: same file, same line, same exception message, same root-cause analysis, filed 2026-08-19 after an identical SAIRA occurrence (INC-33), still sitting unresolved in Backlog.

## Outcome

Real but contained — single order, single business, no vendor involvement, no growth, not escalated to incident-response (P3: below P1/P2 bar). Posted the verdict + root cause to the monitor thread in #bifrost-notifications (broadcast). No new defect filed — added this occurrence as a comment on the existing FUSE-1118 instead, since it already covers the exact bug and this is a live second recurrence worth reprioritizing on. Flagging separately: the monitor's warning threshold is sensitive enough to flap continuously on a single contained record-level failure — worth a retune conversation, not actioned here (would need explicit go-ahead per the plan-then-proceed rule for monitor changes).

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790670292165699
- Ticket: https://globalfreight.atlassian.net/browse/FUSE-1118 (comment added, not newly filed)
