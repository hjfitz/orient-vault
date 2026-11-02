---
tags: [datadog-triage]
date: 2026-10-09
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: snap-adapter
business_id: SAIRA
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791558099758619"
opened_at: "2026-10-09T15:00:37Z"
resolved_at: "2026-10-09T15:03:00Z"
minutes_spent: 3
severity_assessed: P3
flapping: true
outcome: real_minor
escalated_to:
ticket:
session_id: 0a6fab47-9201-4b91-aea7-e306bf321ad2
status: open
---
# Elevated prod error rate: three SAIRA orders rejected by Snap for an empty SKU line, resubmitted every 5 min

## Fired
Monitor 180072217 (>2 error logs tagged domain:fuse in 2m, Terraform-managed) tripped at 15:00:37Z on 3 `snap_adapter` "Entity creation in SNAP failed" logs, all SAIRA sales_order.

## Investigation
- Confirmed: Snap 400 on `LINE_UPDATE`, `SKUId MANDATORY` + `UnitOfMeasure Invalid Unit`, on one price-0 line with `skuId: ""` (unit EA). Orders #37125, #37126, #37127 (created from 14:38Z), each resubmitted every ~5 min under a new correlationId. snap_adapter prod `9e09021`.
- Confirmed: not vendor (Snap answers with a validation error on our payload); no other business or service in this firing.
- Hypothesis, not verified: the Shopify order has a SKU-less line item (zero-price add-on), so the mapped line has no `skuId`; customer data, loops until fixed.
- Flapping: fired 10-08 13:06Z on SAIRA #37079 (`schema_validation`, 57 errors over ~5h). Over 2 days of the monitored query SAIRA = 64 and PURDYFIGG = 37 of the snap_adapter errors. The monitor excludes SAIRA for shopify-connector but not snap_adapter.

## Outcome
P3, real-but-minor, one customer, three orders. Verdict posted in-thread with broadcast. No ticket filed. Owed: ask SAIRA about the SKU-less line on the three orders; retune the monitor in `observability` (plan-then-proceed).

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791558099758619
- Monitor: https://app.datadoghq.com/monitors/180072217

## Update 2026-10-09T15:32Z
Re-verified after 6 further firings: still only `snap_adapter` / SAIRA "Entity creation in SNAP failed", a steady 3 per 5 min since 14:45Z (25 in 90 min), no other business, service or message in the monitored query. Unchanged, no widening, no duplicate verdict posted. Still owed: SAIRA SKU-less line follow-up and the `observability` monitor retune.
