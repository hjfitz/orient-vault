---
title: "Shopify Dev Proxy — Overview"
status: planning
verdict: go
owner: "hjf"
services: ["fuse-mocker", "shopify-connector"]
created: "2026-10-09"
updated: "2026-10-09"
tags: [bifrost]
---
# Shopify Dev Proxy — Overview

## Deliverables
- [[Shopify Dev Proxy/Migration State|Migration State]] — the live source of truth for progress
- `fuse-mocker/apps/shopify-api` — a standalone Go service alongside `apps/snap-api`: a dev-store **driver** plus a **pass-through proxy with fault injection**
- A second, dev-only Shopify app ("Fuse Mocker"), separate from the main Fuse app, installed on the dev stores
- `shopify-*` tools on the fuse MCP, calling shopify-api's `/api/v1` control plane directly (same pattern as the snap-api simulator)
- One small shopify-connector change: `customShopDomains` read from an optional env var, set only in dev

## Verdict
**Go.** Every part of the Fuse pipeline except Shopify can already be mocked. Every dev business connector already points at a real Shopify dev store. What's missing is a way to (a) drive activity on those stores, and (b) simulate Shopify failures. Both are built **outside** the connector, as a fuse-mocker devtool. The only connector change is enabling a library option the Shopify app already uses.

## Why this needs a programme
It spans three repos (fuse-mocker, shopify-connector, fuse-mcp-server), a manual setup step (creating the separate Shopify app), and a credentials design that is easy to get wrong: Shopify refresh tokens rotate, and the connector must never be able to send real tokens to a non-Shopify host in prod.

## Strategy
- **Real dev stores, not a Shopify mock.** A hand-built mock would test against our own assumptions about Shopify; the past bugs (kit components, fulfilment line IDs, `retrievalConditions`) were exactly Shopify behaving differently from what we expected. The proxy fakes only failures.
- **Option A routing:** a dedicated mock business/connector has `shopifyUri = <store>.<proxy-domain>`. All of that connector's Shopify traffic, OAuth included, goes to the proxy. Other dev businesses are untouched, so it's opt-in per connector.
  - Rejected — fetch hook in the connector (option C): it changes code in every environment and switches on globally per deploy rather than per connector.
  - Rejected — `HTTPS_PROXY` plus decrypting the traffic with our own CA (option B): it means a decryption key to manage, all egress depends on the proxy, and nothing in the code shows the traffic is diverted.
- **The proxy terminates auth.** The separate app's real offline token lives only in shopify-api. The connector's `tokens` record for the proxy hostname holds a **placeholder**, and the proxy swaps it for the real token on the way out. This is forced, not a choice: the connector refreshes with the main Fuse app's client secret (`store.api.ts` `getShopifyApi`), which can't refresh a token issued to a different app.
- **The connector change is the minimum the library requires.** `customAppSession` calls `sanitizeShop(...)(shop, true)` and throws `InvalidShopError` unless the shop domain matches `^<label>\.(myshopify\.com|shopify\.com|myshopify\.io|shop\.dev)/*$` (`@shopify/shopify-api` 12.2.0, `lib/utils/shop-validator.js`; called from `store.api.ts:465`). The escape hatch is `customShopDomains`, which `apps/shopify-app/app/shopify.server.ts:18` already sets from `SHOP_CUSTOM_DOMAIN`.
- No cutover: this is a dev-only tool, and nothing in prod changes behaviour.

## Scar tissue
See [[Shopify Dev Proxy/Migration State#Scar tissue|Migration State → Scar tissue]].

## Next
**S0**, the assumptions spike, is the first unit with no dependencies. **C1** (connector `customShopDomains`) can go in parallel. A gate holds **A1**: someone with Shopify Partner / Dev Dashboard access has to create the separate app. Drive it with `waypoint-programme`.
