---
tags:
- waypoint
- shopify-connector
verified: '2026-10-13'
verified_sha: e9aef9e0
verified_paths:
- README.md
- CLAUDE.md
- apps/shopify-egress-service
- packages/shopify-token-management
- pnpm-workspace.yaml
- .github/workflows
- apps/shopify-connector/src
- apps/shopify-app
- iac/shopify-connector
- iac/shopify-egress-service
title: shopify-connector — overview
thesis: 'shopify-connector is the Fuse-to-Shopify integration monorepo: it owns every
  call to a merchant''s Shopify shop, and the offline tokens those calls use.'
confidence: high
---
# shopify-connector — overview

```orient-bluf
{ "v": 1, "bluf": "shopify-connector is the Fuse-to-Shopify integration monorepo: it owns every call to a merchant's Shopify shop, and the offline tokens those calls use.", "confidence": "high", "action": "Never take the ShopToken lock through Prisma, and read origin/main, never the local checkout, before you trust this repo." }
```

## Responsibility

- **`apps/shopify-connector`** polls shops for orders and publishes canonical `sales_order` records to `create_record_request`. It also delivers goods-out confirmations as Shopify fulfilments, applies stock adjustments and tags orders [1][2].
- **`apps/shopify-egress-service`** runs stock sync. It reads a GCS export, sets Shopify inventory in one bulk mutation, verifies every row and publishes `confirmation_made` or `confirmation_data_failure`. It also redrives one SKU [3][4].
- **`apps/shopify-app`** is an embedded React Router app. Its only job is to acquire the offline OAuth tokens the other two apps use.
- **`packages/shopify-token-management`** is the single implementation of the token read, lock and refresh protocol [5].

Orders reach Fuse by two paths. The metered poll runs every 5 minutes. Bulk ingest is a per-business opt-in, and the metered poll skips those businesses. Prod enables bulk for `PURDYFIGG` only [2][6].

## Why it exists separately

Shopify's app model forces a distinct embedded app. The connector polls, the egress service runs long bounded pushes, and the app serves OAuth. Each has its own runtime and its own deploy path.

Egress is split out of the connector's confirmation handlers. A stock sync run lasts up to 570 s inside one push. It needs its own timeout, scale-to-zero and a private ingress [3][4].

The apps share a repo because they merged from separate repos. They also share one MongoDB `ShopToken` collection and the lock code in the package. A change to the package or to the root workspace files redeploys all three apps [7].

## Neighbours

```orient-flow
{ "v": 1, "title": "shopify-connector in context",
  "nodes": [
    { "id": "shop", "label": "Shopify shops", "sub": "Admin GraphQL 2026-04", "kind": "external" },
    { "id": "app", "label": "shopify-app", "sub": "OAuth, offline tokens", "kind": "service", "ev": [7] },
    { "id": "tok", "label": "ShopToken", "sub": "Mongo, advisory lock", "kind": "store", "ev": [5] },
    { "id": "conn", "label": "shopify-connector", "sub": "poll, confirm, tag", "kind": "service", "service": "shopify-connector", "tone": "accent", "ev": [1] },
    { "id": "egress", "label": "shopify-egress-service", "sub": "stock sync", "kind": "service", "ev": [3] },
    { "id": "dd", "label": "dedupe-service", "kind": "service", "service": "dedupe-service" },
    { "id": "poll", "label": "snap-queue-polling-service", "sub": "confirmations, stock export", "kind": "service", "service": "snap-queue-polling-service" },
    { "id": "cfg", "label": "config-service", "sub": "connectors, mappings", "kind": "service", "service": "config-service" }
  ],
  "edges": [
    { "from": "shop", "to": "conn", "label": "orders" },
    { "from": "conn", "to": "dd", "label": "create_record_request" },
    { "from": "poll", "to": "conn", "label": "confirmation_ready, stock_adjustment_ready" },
    { "from": "conn", "to": "shop", "label": "fulfil, adjust, tag" },
    { "from": "poll", "to": "egress", "label": "stock_sync" },
    { "from": "egress", "to": "shop", "label": "bulk inventory set" },
    { "from": "app", "to": "tok", "label": "writes" },
    { "from": "conn", "to": "tok", "label": "refreshes" },
    { "from": "egress", "to": "tok", "label": "refreshes" },
    { "from": "cfg", "to": "conn", "label": "connectors, mappings", "style": "dashed" }
  ] }
```

Orders flow out to dedupe-service. Confirmations and stock adjustments flow in from the SNAP poller. The poller also publishes the stock export that egress consumes. All three Shopify-calling paths read the same token document.

## Where the reference lives

[[architecture]] carries the routes, subscriptions, stock sync rules and the token lock. [[known-context]] carries the risk register. Read `apps/shopify-egress-service/CLAUDE.md` before you touch egress.

Do not trust three sources:

- The root `README.md` lists two apps and omits egress.
- The root `CLAUDE.md` still describes a `ReapConcurrencyGate`, a dual-published `confirmation_made` and a failure for lines with no Shopify reference. The code has none of these.
- The local checkout. It is routinely well behind `origin/main` [[known-context#stale-checkout]].

**The refactor programme** lives in the vault at `Bifrost/Shopify Connector Untangle/`, not in this folder (created 2026-11-13). Its north star is 3am debuggability: each flow made visible, monitored, pinned by wire-level tests and switchable by runtime flag before it moves into its own slice. It replaced the retired `Bifrost/Shopify Connector Rearchitecture/`.

- **Finished, verified in code.** `S0` (tsconfig and depcruise baseline) and `S1` (the characterization harness plus a boot smoke test) [8][9].
- **Finished by ordinary feature work.** `D`, `F2`, `BUGFIX(a)` and `PREVIEW-ISO(a)`, per Migration State. Not re-verified here.
- **Not finished.** Non-test `core/` files still import adapters in 32 files and `@nestjs` in 13. Depcruise rules sit at `warn` and run in no workflow. No characterization scenarios exist beyond the smoke test. No subscription or scaling golden exists [8][10].
- **Out of date in Migration State.** It still records the ingest monitors as not started. Monitors for the bulk lane, token refresh and confirmations now exist in `gfs-bifrost/observability` [11]. It also assumes a zero-tenant prod [[known-context]].
- **UNKNOWN.** Whether a rehearsed pause-and-rollback runbook exists. Nothing in the repo holds one.

## What deliberately isn't here

- **Idempotency.** dedupe-service gates repeats. The connector may republish an order across polls until Shopify marks it fulfilled.
- **A poll watermark.** The retrieval window slides on every poll. A regression that outlives a connector's window loses orders for good [[known-context#r1-permanent-order-loss]].
- **Raw payload capture.** Shopify has no raw webhook payload to capture, so the connector attaches no ingest `capture`.
- **Stock sync production.** snap-queue-polling-service builds the export. collector tracks the run and replay-service redrives it.
- **Connector setup and mapping rules.** config-service owns both. This repo reads them.
- **Purchase orders.** No `purchase_order` path exists here.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "apps/shopify-connector/src/http/controllers/events.controller.ts@e9aef9e0" },
  { "id": 2, "kind": "code", "ref": "apps/shopify-connector/src/core/shopify/use-cases/shopify-sales-order.service.ts@e9aef9e0" },
  { "id": 3, "kind": "code", "ref": "apps/shopify-egress-service/src/core/stock-sync/stock-sync.service.ts@e9aef9e0" },
  { "id": 4, "kind": "code", "ref": "iac/shopify-egress-service/projects/shopify-egress-service/pubsub.tf@e9aef9e0" },
  { "id": 5, "kind": "code", "ref": "packages/shopify-token-management/src/shop-token-lock.ts@e9aef9e0" },
  { "id": 6, "kind": "code", "ref": "iac/shopify-connector/env/prod.tfvars@e9aef9e0" },
  { "id": 7, "kind": "code", "ref": "CLAUDE.md@e9aef9e0" },
  { "id": 8, "kind": "code", "ref": "apps/shopify-connector/.dependency-cruiser.cjs@e9aef9e0" },
  { "id": 9, "kind": "code", "ref": "apps/shopify-connector/src/__characterization__/support/harness.ts@e9aef9e0" },
  { "id": 10, "kind": "code", "ref": ".github/workflows/shopify-connector-code-quality.yaml@e9aef9e0" },
  { "id": 11, "kind": "url", "ref": "https://github.com/gfs-bifrost/observability/blob/77629f6/iac/projects/bifrost-observability/monitors.shopify-connector.tf", "note": "monitors for the bulk lane, token refresh and confirmations" }
] }
```
