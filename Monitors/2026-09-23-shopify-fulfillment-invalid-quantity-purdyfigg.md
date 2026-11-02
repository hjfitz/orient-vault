---
tags: [datadog-triage]
date: 2026-09-23
monitor: "[FUSE][Egress] Shopify confirmation delivery failing (fulfilment / order-tag)"
service: shopify-connector
business_id: PURDYFIGG
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790187654181979"
opened_at: "2026-09-23T16:22:49Z"
resolved_at: "2026-09-23T18:19:49Z"
minutes_spent: 15
severity_assessed: P3
flapping: true
outcome: real_minor
escalated_to:
ticket:
session_id: a5533af9-6c8f-4c08-aab9-53c76f9fbfce
status: resolved
---
# PURDYFIGG intermittent "invalid fulfillment order line item quantity" recurring over weeks

## Fired
Monitor id `303425509` (`sum:fuse.confirmation.forward.failure + sum:fuse.order.tags.update.failure > 5` over 15m) fired twice on 2026-09-23: 16:22-16:32 UTC and 18:00-18:08 UTC, both self-recovering. Triaged after the fact (found while looking for "another flappy flapper" alongside the STUBBLE/snap_adapter triages the same day) — by the time of triage the monitor had been quiet for ~16h and was `OK`.

## Investigation
- The metric itself carries no `businessId` tag (`fuse.confirmation.forward.failure{environment:prod}` groups to `businessId:N/A`), so pulled the underlying `shopify-connector` logs directly instead (note: shopify-connector logs use the hyphenated `service:shopify-connector` tag, opposite of the metric-name convention — per observability repo's own Datadog gotchas).
- All 10 error lines behind both firing windows are `businessId:PURDYFIGG`, `recordType:goods_out_confirmation`, message "Shopify fulfillment creation returned errors" — Shopify's GraphQL API rejecting with `userErrors: [{field: [fulfillment], message: "Invalid fulfillment order line item quantity requested."}]`, each against a distinct `fulfillmentOrderId`.
- Checked 30-day history for this exact error + business: 17 occurrences total, on three separate days — 2026-09-17 (6), 2026-09-18 (1), 2026-09-23 (10) — always PURDYFIGG, always clustered in the 16:00-18:00 UTC window. Not a chronic every-day flapper, but a recurring, business-specific pattern.
- No existing Monitors or ticket record for this specific error/business found.

## Outcome
Real and recurring, not currently active, not escalated (contained to one business, self-recovers within ~10 minutes each burst, no growth trend across the three occurrences). Each affected order fails to reflect as fulfilled on PURDYFIGG's Shopify store — a genuine customer-facing gap, distinct from the STUBBLE dueOut case (that was correct-by-design rejection; this is Shopify rejecting a quantity our side computed, which shouldn't happen). Flagged a plausible link to the 2026-08 kit-component exploded-line class of bug (types 9.0.0) without having traced the actual code path — that's real investigation, not something a log read alone confirms. Posted the verdict to the thread and offered to file a create-defect ticket for engineering to trace the root cause; held off pending Harry's go-ahead.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790187654181979
- Monitor: id 303425509
