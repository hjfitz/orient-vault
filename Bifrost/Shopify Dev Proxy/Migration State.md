---
title: "Shopify Dev Proxy — Migration State"
programme: "shopify-dev-proxy"
status: planning
owner: "hjf"
services: ["fuse-mocker", "shopify-connector"]
created: "2026-10-09"
updated: "2026-10-09"
tags: [bifrost, migration-state]
---
# Shopify Dev Proxy — Migration State

## Unit status
Legend: ⬜ not started · 🟨 in progress · ✅ merged · ⛔ blocked · ⏸ deferred · ❌ dropped · 🔄 rescoped

### Foundations
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **S0** | ⬜ | Assumptions spike | | low | sonnet/medium | | No PR, findings go in the Decision log. Confirm: (1) what `TokenUtils.isExpired` (`packages/shopify-token-management/src/token.utils.ts:9`) does with an empty or far-future `expires`, i.e. can a placeholder token never trigger a refresh; (2) every other place `shopifyUri` acts as an identity (Firestore routing-metadata keys, storefront/connector resolution, Shopify App install flow); (3) whether the connector receives any Shopify webhooks the proxy can't see; (4) DNS: explicit per-store records vs a wildcard via a load balancer (Cloud Run domain mappings have no wildcard). |
| **C1** | ⬜ | Connector `customShopDomains` from env | | med | sonnet/low | | shopify-connector: pass `customShopDomains` from an optional env var (e.g. `SHOP_CUSTOM_DOMAIN`, mirroring `apps/shopify-app/app/shopify.server.ts:18`) into both `shopifyApi({...})` calls in `store.api.ts` (`validateToken`, `getShopifyApi`). Set it only in dev Terraform, pinned to the proxy domain. Unset means the current behaviour. Verify: the dev connector accepts a `<store>.<proxy-domain>` shop, and prod config is unchanged. |
| **A1** | ⬜ | Separate dev Shopify app | | low | — | | Manual. Create a "Fuse Mocker" app outside the main Fuse app. Scopes: orders, draft orders, fulfillments, inventory, products, metafields, plus whatever the connector's queries need (match the Fuse app). Install it on the dev stores, OAuth redirect to shopify-api. Client ID and secret go in Secret Manager. Gated by G1. |

### fuse-mocker shopify-api
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **M1** | ⬜ | Scaffold `apps/shopify-api` + infra | S0 | low | sonnet/medium | | A Go service shaped like `apps/snap-api` (bootstrap/config/core/http/repositories). Cloud Run TF alongside `iac/projects/fuse-mocker/cloud-run-snap-api.tf`. Host-based routing: `<store>.<proxy-domain>` maps to `<store>.myshopify.com`. DNS per S0's finding. |
| **M2** | ⬜ | OAuth install + auth termination | M1, A1 | high | opus/high | | The separate app's OAuth install flow. Store the real offline/refresh tokens in shopify-api's own store and refresh them itself. Serve `/admin/oauth/access_token` for proxy shops by issuing placeholder tokens, so the connector's refresh never reaches Shopify. See Scar tissue on refresh faults. |
| **M3** | ⬜ | Pass-through | M2 | med | sonnet/medium | | Forward `/admin/api/{version}/graphql.json` to the mapped real store, swapping the placeholder `X-Shopify-Access-Token` for the real one. Version-agnostic, no awareness of the schema. Log operation name and root field per call. |
| **M4** | ⬜ | Fault rules | M3 | med | sonnet/high | | `/api/v1/faults`: match on shop + operationName/rootField. Kinds: 429, GraphQL `THROTTLED`, 5xx, latency, canned response, bulk op stuck `RUNNING`/`FAILED`. With no rules active it is pure pass-through. OAuth faults only apply before forwarding. |
| **M5** | ⬜ | Dev-store driver | M2 | low | sonnet/medium | | `/api/v1` commands using the separate app's token: create an order (`orderCreate`, or a draft then complete, Bogus Gateway), cancel, adjust/set inventory, tags, metafields. Scenario presets: kit lines, multiple locations, partial fulfilment, orders `retrievalConditions` should skip. |
| **M6** | ⬜ | Mock connector + placeholder seeding | C1, M3 | med | sonnet/medium | | A command that sets up a mock business/connector with `shopifyUri = <store>.<proxy-domain>` (fuse MCP `config-write`) and seeds the placeholder token into the connector's dev Mongo `tokens` collection (keyed by `shop`). This is a cross-service write of dev-only data; see R3. |
| **M7** | ⬜ | fuse MCP `shopify-*` tools | M4, M5 | low | sonnet/low | | fuse-mcp-server: tools for the driver and fault rules, calling shopify-api `/api/v1` directly (same pattern as the snap-api simulator). Update the data files and run the parity check before committing. |
| **M8** | ⏸ | Bulk download faults | M4 | low | sonnet/medium | | Deferred. Rewrite the `url` in bulk-operation responses so the JSONL download from Google Cloud Storage also goes through the proxy and can be faulted. |
| **M9** | ⬜ | End-to-end verification | M6, M7 | low | sonnet/medium | | Driver creates an order → connector polls through the proxy → canonical `sales_order` → Snap simulator → confirmation → `fulfillmentCreate` through the proxy. Then repeat with a 429/THROTTLED rule and a stuck bulk op, and confirm the connector behaves as expected. |

## Gates
- [ ] **G1 — Shopify Partner / Dev Dashboard access to create the separate app** — blocks A1. Clears when someone with Partner org access creates the "Fuse Mocker" app (or grants access to whoever will).

## Risks
- **R1 ★ Connector sends tokens to a non-Shopify host** — `customShopDomains` widens which hosts the connector will talk to. Mitigation: the env var is unset in prod, the dev value is pinned to the exact proxy domain, and proxy shops only ever hold placeholder tokens — open.
- **R2 ★ `shopifyUri` is an identity, not just a host** — it keys `tokens` and appears in logs, routing metadata and possibly resolution. Mitigation: a dedicated mock business/connector isolates it, and S0 audits every use — open.
- **R3 Cross-service write for placeholder seeding** — the mocker writes into the connector's dev `tokens` collection. Dev-only data. The fallback is seeding by hand once per mock connector — open.
- **R4 Refresh with the wrong app secret** — if a placeholder ever expires, the connector refreshes with the main Fuse app's client secret. Mitigation: the proxy terminates OAuth for proxy shops (M2), and S0 checks whether a non-expiring placeholder avoids refreshes entirely — open.
- **R5 Dev-store limits and shared state** — real rate limits apply, and stores are shared across developers. Mitigation: one store per environment or developer where it matters, and driver orders are tagged so they can be recognised — standing.

## Decision log
- **2026-10-09** — **Option A routing with a separate dev app** over a fetch hook in the connector (C) and `HTTPS_PROXY` plus decrypting with our own CA (B). Why: it's opt-in per connector through config, the only Fuse change is one env var plus a library option the Shopify app already uses, and the proxy terminating auth removes the rotating refresh-token risk.
- **2026-10-09** — Built as a **distinct service in fuse-mocker** (`apps/shopify-api`), not in connector code. Its control plane is its own `/api/v1`, used by fuse MCP `shopify-*` tools. The mocker API (canonical envelope publishing) is not extended for now.
- **2026-10-09** — **Real dev stores plus a pass-through**, not a full Shopify mock. A mock would encode our assumptions about Shopify's behaviour and need maintaining across Shopify's quarterly API versions. The pass-through adds only failure simulation.

## Scar tissue
- **Never fault a forwarded response from Shopify's `/admin/oauth/access_token`.** Refresh tokens rotate: once Shopify has exchanged one, a faulted response loses the credentials and the dev store has to re-authorise the app. Faults on OAuth only ever apply **before** forwarding.
- **`customShopDomains` stays unset in prod.** It is the only thing stopping the connector sending a token to a host that isn't Shopify.
- **Proxy shop hostnames must be `<single-label>.<proxy-domain>`.** `sanitizeShop` allows exactly one label in front of an allowed domain (`^[a-zA-Z0-9][a-zA-Z0-9-_]*\.(<domains>)/*$`), so `a.b.<proxy-domain>` is rejected.
