---
tags: [datadog-triage]
date: 2026-09-22
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: shopify-connector
business_id: SAIRA
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790060379653289"
opened_at: "2026-09-22T06:59:39Z"
resolved_at: "2026-09-22T07:19:30Z"
minutes_spent: 20
severity_assessed: P4
flapping: true
outcome: real_minor
escalated_to:
ticket:
session_id: 1407be41-68ab-4a82-a024-bec2c34722c3
status: resolved
---
# SAIRA Shopify order-tag-update failures chronically tripped the platform error-rate monitor

## Fired
"[FUSE][Platform] Elevated production error rate (2m window)" (monitor `180072217`) fired again at 2026-09-22 07:59:39 BST. It had also fired repeatedly over the prior ~17 hours: 2026-09-21 15:10, 15:16, 15:18, 15:20, 16:11, 16:17, 16:21, 21:20, 21:25 BST, plus this morning's 07:58/08:00. Harry had already flagged (16:20 BST the day before, same channel) that the errors traced to business SAIRA (Saira Skin), possibly reinstalling their Shopify app, and asked Thomas Dunn/James Godsell to check — James replied he'd messaged the customer the prior week with no response yet.

## Investigation
Pulled the raw log lines behind the monitor's own query for the 07:59 firing window: all 6 errors were `shopify-connector` "Order tag update failed on store" / "Shopify GraphQL mutation failed" pairs, `businessId: SAIRA`. Pulled the full error body for one: `GraphqlQueryError` — "Access denied for orderUpdate field. Required access: write_orders access scope, write_marketplace_orders access scope or write_quick_sale access scope...". Confirmed the record's own confirmation flow (`goods_out_confirmation`) still completed and published successfully — only the outbound order-tagging side-effect (`outboundTagsEnabled`) failed. Re-ran the same query across every earlier firing in the last day+ — every single "Order tag update failed" log line in that window was also `businessId:SAIRA`, confirming one recurring cause, not new/different noise each time.

## Root cause
SAIRA's Shopify app is missing the `write_orders` (or equivalent) OAuth scope needed for the `orderUpdate` mutation Fuse uses to tag orders post-confirmation. Not a Fuse defect — customer/app-installation-side. Each failed tag-update emits 2 error log lines, which alone sits right at this monitor's `>2 in 2m` threshold, so a single SAIRA blip is enough to trip it — a mistuning contributing factor on top of the real underlying customer issue.

## Fix / Resolution
Disabled `outboundTagsEnabled` on SAIRA's Shopify connector (`conn_ff3c0a00a5504842b205a3f4cd2dd27a`, storefront `sf_14f3fe4ff2d74999bb2b2f3b48113a69`) in prod config via config-service, verified with a fresh GET. This stops both the customer-facing tag-update failures and the monitor noise. Posted an update in the existing SAIRA thread asking James to flag when the customer reinstalls/reauthorizes, so tagging can be re-enabled then. Monitor itself (`180072217`) not retuned as part of this triage — flagged in-thread as worth a retune (mirroring its existing `snap-polling-service` 401 exclusion) if it fires on something similar again.

## Links
- Slack thread (monitor): https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790060379653289
- Slack thread (SAIRA/James update): https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790004046666499
