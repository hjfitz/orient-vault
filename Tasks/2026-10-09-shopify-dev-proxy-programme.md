---
tags: [adhoc-task]
date: 2026-10-09
tldr: "Designed Shopify dev-store driver + fault-injecting proxy for fuse-mocker; recorded as Waypoint programme 'Shopify Dev Proxy'"
session_id: cb7142c0-e039-473e-872f-4e2e8a57aef3
status: open
---
# Design Shopify dev-store mocking for the Fuse pipeline

## Outcome
Chose real dev stores + a fuse-mocker `apps/shopify-api` (driver + pass-through with fault rules) over a Shopify mock. Routing is option A: separate dev Shopify app, `shopifyUri` = proxy host, proxy terminates auth. Only connector change: `customShopDomains` from an env var (`sanitizeShop` otherwise rejects the host). Programme scaffolded at `Bifrost/Shopify Dev Proxy/`, 12 units. Next: S0, C1; A1 gated on Shopify Partner access.
