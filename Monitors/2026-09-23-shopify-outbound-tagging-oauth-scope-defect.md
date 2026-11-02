---
tags: [datadog-triage]
date: 2026-09-23
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: shopify-connector
business_id: SAIRA
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790174979785299"
opened_at: "2026-09-23T14:32:37Z"
resolved_at: "2026-09-23T15:39:46Z"
minutes_spent: 67
severity_assessed: P4
flapping: true
outcome: real_minor
escalated_to:
ticket: FUSE-1252
session_id: 335db79e-9fb1-423f-b0ea-f1e58dfe56ca
status: resolved
---
# SAIRA Shopify order-tag failures: yesterday's root cause was wrong — it's a Fuse OAuth scope gap, not a customer install issue

## Fired
`[FUSE][Platform] Elevated production error rate (2m window)` (monitor `180072217`) fired three times back-to-back today (14:32, 14:44, 14:48 UTC), each self-resolving within ~2 minutes. Same symptom as a 2026-09-22 triage: `shopify-connector` "Order tag update failed on store" / "Shopify GraphQL mutation failed" pairs, all `businessId:SAIRA`.

## Investigation
- Confirmed today's error is byte-for-byte identical to yesterday's: `GraphqlQueryError` — "Access denied for orderUpdate field. Required access: `write_orders` access scope, `write_marketplace_orders` access scope or `write_quick_sale` access scope."
- Yesterday's triage concluded this was customer-side (SAIRA's app installation missing the scope) and had SAIRA asked to reinstall; `outboundTagsEnabled` was disabled on their connector as a stopgap.
- Checked live config via Fuse MCP: `outboundTagsEnabled` was back to `true` on SAIRA's connector today — the stopgap had been reverted, presumably expecting the reinstall to have fixed things.
- Queried the prod `shopify-prod` Mongo `ShopToken` collection directly for `fb1ba1.myshopify.com` (with the user's explicit go-ahead, after the harness's auto-mode classifier initially blocked touching Cloud Run env/secrets — resolved via `/permissions`): `installedAt` had reset to `2026-09-23T08:28:18Z`, a fresh document (Prisma `@default(now())` only fires on document creation, keyed on `shop`) — confirming SAIRA genuinely did reinstall this morning.
- The granted `scope` after that reinstall (`write_assigned_fulfillment_orders,read_customers,write_inventory,read_locations,read_markets_home,write_merchant_managed_fulfillment_orders,read_orders,write_products`) still lacks `write_orders`.
- Root cause: `apps/shopify-app/shopify.app.fuse.toml`'s `[access_scopes]` block never requests `write_orders`/`write_marketplace_orders`/`write_quick_sale` (`optional_scopes = []`). The app cannot be consented into having a scope it never asks for — no reinstall, by SAIRA or anyone, could ever have worked. Yesterday's "customer-side, ask them to reinstall" conclusion was wrong.
- Re-verified independently against the **live deployed** config (not just source) at the user's request: `shopify-app-prod`'s Cloud Run `SCOPES` env var matches the TOML exactly and also lacks the three scopes — two independent sources agree, so this isn't a stale-source-vs-live-drift case.
- Per the 2026-09-18 #bifrost-notifications thread, outbound tagging was agreed to become standard for every Shopify customer, with Purdy & Figg next after SAIRA — that rollout is blocked by the same defect.

## Outcome
Real, minor, now correctly diagnosed and tracked. The confirmation flow itself is unaffected — only the Shopify order-tagging side-effect fails, permanently, for any business with `outboundTagsEnabled` on.

- Filed **FUSE-1252** for the real fix.
- **Framing correction:** prod lacking `write_orders` wasn't an oversight — PR #226 (2026-08-18) deliberately withheld it, relying on `outboundTagsEnabled` staying off per connector. SAIRA's rollout went ahead without that decision being re-checked. Harry chose to supersede it.
- **Fixed, same day.** `shopify-connector` PR #278 added `write_orders` to the prod TOML and the Cloud Run `SCOPES` env (`global.tfvars`). The Partner-dashboard side was pushed with the Shopify CLI as an unreleased version `fuse-1252-write-orders`, diffed against the active `fuse-8` (the only functional change was `write_orders`; webhooks only reordered), then released by Harry in the UI. After that, the held `terraform-prod` gate was approved: revision `shopify-app-prod-00036-rkb` serves `SCOPES` with `write_orders`, and no `shopify-app` errors followed.
- Retuned monitor `180072217`: added `AND NOT(service:shopify-connector AND @businessId:SAIRA)` to its query, mirroring the monitor's existing `snap-polling-service` exclusion — temporary until tagging is confirmed working (`observability` PR #48, plan reviewed, merged, applied, verified live `OK`). The more targeted `shopify_confirmation_delivery_failing_fulfilment_order_tag` monitor remains in place.
- **Slack:** the bot's verdict and James-thread correction were posted, then deleted at Harry's request. James has not been told yet.
- **Still open:** SAIRA must re-open the app to re-consent before tag writes succeed (`outboundTagsEnabled` is still `true`, so errors continue until then, just not paging). Then revert observability#48. Tracked in the 2026-09-23 digest Todo.

## Links
- Slack thread (today's alert): https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790174979785299
- Slack thread (2026-09-18 SAIRA/James): https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790004046666499
- Ticket: https://globalfreight.atlassian.net/browse/FUSE-1252
- PR: https://github.com/gfs-bifrost/observability/pull/48
- PR: https://github.com/gfs-bifrost/shopify-connector/pull/278
