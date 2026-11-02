---
tags: [datadog-triage]
date: 2026-09-29
monitor: "[FUSE][Fuse API] Availability below target (request failure rate)"
service: api-gateway
business_id: DOCKBAY
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790678688796459"
opened_at: "2026-09-29T10:44:48Z"
resolved_at: "2026-09-29T10:46:17Z"
minutes_spent: 2
severity_assessed: P3
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 7cd29267-d3cb-4955-9e87-62ec7d46fb57
status: resolved
---
# Fuse API availability 33% — 1 failed request of ~3 in the window

## Fired
Monitor 302685705 tripped at 33.3% (threshold >5%) at 11:44 BST, having warned at 10:56 and recovered at 11:01. Same window also saw [FUSE][Platform] error rate and the Shopify egress monitor flapping.

## Investigation
- Confirmed: api-gateway carried ~326 requests in 3h (~0.2/min); only 3 `fuse.request.failure`, all `recordType:sales_order`. One failure flips the ratio.
- Confirmed: snap_adapter logged 3 DOCKBAY `Entity creation in SNAP failed` at 09:53-09:55Z, `schema_validation`, `ShipAddress.0.Line1` too big (>50 chars). D9 go-live monitor already RED.
- Confirmed: PURDYFIGG shopify-connector `Confirmation dispatch failed` ~every 12 min since 09:56Z; a logged cause is Shopify userError "Invalid fulfillment order line item quantity requested".
- Confirmed: `Confirmation could not be routed` warns are `reason: use_case_inactive` (stock_adjustment), config working as designed.
- Hypothesis (unverified): PURDYFIGG fulfilment quantity mismatch being retried; DOCKBAY address is customer data vs mapping. Not checked against Shopify / raw payload.
- Not established which of the 3 gateway failures maps to which DOCKBAY order (metric lacked businessid tag).

## Outcome
P3, ours not vendor. No fix applied (read-only). Verdict posted in thread: monitor needs a minimum-volume guard; DOCKBAY and PURDYFIGG follow-ups suggested. Ticket for monitor retune offered, not filed.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790678688796459
