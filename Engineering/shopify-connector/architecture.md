---
tags:
- waypoint
- shopify-connector
verified: '2026-10-14'
verified_sha: 59f919ba
verified_paths:
- iac/shopify-connector
title: shopify-connector — architecture
thesis: 'A pnpm monorepo of three Cloud Run apps and one token package: a polling
  NestJS connector, a stock-sync egress service and an OAuth-only React Router app,
  coupled through one ShopToken collection.'
confidence: high
---
# shopify-connector — architecture

```orient-bluf
{ "v": 1, "bluf": "A pnpm monorepo of three Cloud Run apps and one token package: a polling NestJS connector, a stock-sync egress service and an OAuth-only React Router app, coupled through one ShopToken collection.", "confidence": "high", "action": "Take the ShopToken lock only through ShopTokenLock on the native mongodb driver, never through Prisma." }
```

## Guardrails
<!-- Max ~6, promoted out of known-context.md prose so a tool can push them at you BEFORE the
     mistake rather than leaving them at line 92 of a doc nobody opens mid-task. Push, not pull:
     `wp context --paths <what you are touching>` prints only the ones on those paths, and
     `wp signoff` names any the diff actually touches. Nobody deletes a guardrail, so a long list
     becomes a wall that gets skipped — prune before adding.
     kind: contract | policy | operational | technical -->

- [policy:G1] The `ShopToken` lock lives on the **native `mongodb` driver** and must never move
  onto Prisma: Prisma's Mongo connector can't match a missing field, so legacy documents would
  become permanently unlockable. — paths: packages/shopify-token-management/src, apps/shopify-app/app/utils
- [policy:G2] `GRAPHQL_REQUEST_RETRIES = 0` and the 30s TTL of the per-shop `ShopifyStoreApi` LRU
  are deliberate; a plan to "fix" that TTL was explicitly rejected. — paths: apps/shopify-connector/src
- [policy:G3] Failure-publish-don't-throw on ingest, the pagination bounds and the batched detail
  fan-out are deliberate, not incomplete. — paths: apps/shopify-connector/src/core
- [operational:G4] The local checkout is a standing hazard — read `origin/main` via `git show`,
  never the working tree.
- [operational:G5] The secops nightly is chronically red and clearing it is the PR author's job,
  in its own PR off the default branch. — paths: .github/workflows
- [contract:G6] `STOCK_SYNC_MAX_DELIVERY_ATTEMPTS` must equal the `max_delivery_attempts` in the egress `pubsub.tf`, and a stale stock export is never replayed: nothing subscribes to the dead-letter topic. — paths: apps/shopify-egress-service/src/core/stock-sync, iac/shopify-egress-service/projects/shopify-egress-service/pubsub.tf

## Three apps and one package

**CONFIRMED** The repo-root pnpm workspace holds three apps and one local package, never published. They share one lockfile. The connector and egress service take framework versions from `catalog:`; `shopify-app` keeps its own [41].

```orient-flow
{ "v": 1, "title": "Repository units and shared state",
  "nodes": [
    { "id": "app", "label": "apps/shopify-app", "sub": "React Router 7, node 22", "kind": "service", "ev": [22] },
    { "id": "conn", "label": "apps/shopify-connector", "sub": "NestJS, node 24, Jest", "kind": "service", "service": "shopify-connector", "tone": "accent", "ev": [1] },
    { "id": "egress", "label": "apps/shopify-egress-service", "sub": "NestJS, node 24, Vitest", "kind": "service", "ev": [26] },
    { "id": "pkg", "label": "shopify-token-management", "sub": "lock, read, refresh", "kind": "step", "ev": [21] },
    { "id": "tok", "label": "ShopToken", "sub": "Mongo shopify-{env}", "kind": "store", "ev": [21] }
  ],
  "edges": [
    { "from": "app", "to": "pkg", "label": "/lock entry only" },
    { "from": "conn", "to": "pkg", "label": "full provider" },
    { "from": "egress", "to": "pkg", "label": "full provider" },
    { "from": "pkg", "to": "tok", "label": "native driver" }
  ] }
```

| App | Runtime and tests | Cloud Run service | Ingress and scale |
| --- | --- | --- | --- |
| `apps/shopify-connector` | node 24, Jest, Biome, no `build:check:tests` | `shopify-connector-{env}-cr` | `allUsers` invoker; max 10 instances at concurrency 3; 1 GiB; no minimum [17][19][44] |
| `apps/shopify-app` | node 22, Vitest, Biome v1, `prisma db push --accept-data-loss` on boot | `shopify-app-{env}` | public through a global load balancer; minimum 1 instance [43] |
| `apps/shopify-egress-service` | node 24, Vitest, has `build:check:tests` | `shopify-egress-service-{env}-cr` | no `allUsers`; invoker is its own service account; 0 to 5 instances; 512 MiB; 600 s timeout [32][33] |

**CONFIRMED** All dockerfiles build from the repo root. The three apps deploy on separate path-filtered workflows. A change to `packages/shopify-token-management` or to the root `pnpm-workspace.yaml`, `pnpm-lock.yaml` or `.npmrc` redeploys all three [39][41]. Each push to `main` runs a dev build and apply, then a `terraform-prod`-gated prod leg [39].

## Runtime shape (connector)

NestJS app wired by `app.module.ts`. The layers are `http/controllers` (thin), then `core/{collections,bulk,confirmations,shopify}` (business logic), then `adapters/{shopify,pubsub,config,db,http}` (SDK wrappers), then `providers/` (config, observability, connector and mapping remote-config) [1].

**CONFIRMED** The layering contract is not met. 32 non-test files under `core/` import adapters and 13 import `@nestjs`. The depcruise rules `no-core-to-adapters` and `no-core-to-nestjs` are set to `warn`, and no workflow runs depcruise [37][38].

**CONFIRMED** Two ingest paths feed one canonicaliser. The metered collector and the bulk reaper both call `SalesOrderCanonicaliser`. Mapping rules come from config-service per connector and use case (`ConnectorMappingsProvider`), passed to `@gfs-bifrost/rules-engine` with any mapping dictionaries [15].

## Two ingest paths, one shared canonicaliser

```orient-flow
{ "v": 1, "title": "Metered poll",
  "nodes": [
    { "id": "sch", "label": "Cloud Scheduler", "sub": "*/5 * * * *", "kind": "external", "ev": [18] },
    { "id": "t", "label": "poll_trigger", "sub": "internal topic", "kind": "topic", "ev": [16] },
    { "id": "poll", "label": "/events/poll", "sub": "single-flight pollMutex", "kind": "step", "service": "shopify-connector", "tone": "accent", "ev": [2] },
    { "id": "svc", "label": "ShopifySalesOrderService", "sub": "active, non-bulk connectors", "kind": "step", "ev": [7] },
    { "id": "col", "label": "SalesOrderCollector", "sub": "headers, then detail", "kind": "step" },
    { "id": "can", "label": "SalesOrderCanonicaliser", "sub": "shared with bulk", "kind": "step", "ev": [15] },
    { "id": "out", "label": "create_record_request", "sub": "recordType sales_order", "kind": "topic", "ev": [1] },
    { "id": "fail", "label": "create_data_failure", "sub": "per store or order", "kind": "topic", "tone": "alert", "ev": [1] }
  ],
  "edges": [
    { "from": "sch", "to": "t" },
    { "from": "t", "to": "poll", "label": "push" },
    { "from": "poll", "to": "svc" },
    { "from": "svc", "to": "col" },
    { "from": "col", "to": "can" },
    { "from": "can", "to": "out", "label": "publish" },
    { "from": "can", "to": "fail", "label": "drop one item", "style": "dashed" }
  ] }
```

- **CONFIRMED** The **metered poll** runs `ShopifySalesOrderService.collect()`, then `SalesOrderCollector.collectFor()` per active connector, then `SalesOrderCanonicaliser`. The service drops every business in the bulk allowlist first, so a customer ingests one way, never both [7].
- **CONFIRMED** The **bulk ingest** (`core/bulk/{tick,reap,reassemble}`) is a per-business opt-in. The tick advances each bulk-enabled connector: it reaps a COMPLETED bulk operation, then starts the next bulk query. It publishes a reap message onto a dedicated internal topic [14][4].

```orient-flow
{ "v": 1, "title": "Bulk ingest",
  "nodes": [
    { "id": "sch", "label": "Cloud Scheduler", "sub": "*/5 * * * *", "kind": "external", "ev": [18] },
    { "id": "bp", "label": "bulk_poll_trigger", "sub": "internal topic", "kind": "topic", "ev": [16] },
    { "id": "tick", "label": "/events/bulk-poll", "sub": "BulkIngestTick", "kind": "step", "service": "shopify-connector", "tone": "accent", "ev": [4, 14] },
    { "id": "shop", "label": "Shopify bulk operation", "sub": "orders, groupObjects true", "kind": "external", "ev": [11] },
    { "id": "reap", "label": "reap topic", "sub": "DLT after 10", "kind": "topic", "ev": [16] },
    { "id": "rp", "label": "/events/reap", "sub": "BulkOrderReaper", "kind": "step", "ev": [3] },
    { "id": "out", "label": "create_record_request", "kind": "topic", "ev": [1] }
  ],
  "edges": [
    { "from": "sch", "to": "bp" },
    { "from": "bp", "to": "tick", "label": "push" },
    { "from": "tick", "to": "shop", "label": "poll, start next" },
    { "from": "tick", "to": "reap", "label": "COMPLETED op" },
    { "from": "reap", "to": "rp", "label": "push" },
    { "from": "rp", "to": "out", "label": "reassemble, canonicalise" }
  ] }
```

- **CONFIRMED** The tick picks its own run as the newest of the shop's recent `bulkOperations` whose query is rooted at `orders` (`operation_type:query`). It assumes one bulk-ingest connector per shop. Runs the app starts for other reasons are never reaped. The order query sends `groupObjects: true` explicitly, because the reassembler needs each child line after its parent [11][14].
- **CONFIRMED** The reap resolves mappings, routing and DDP once per window. A config outage aborts the window and Pub/Sub redelivers. A window with no mapping rules skips every order. An order that fails canonicalisation goes to `create_data_failure`. The reap path warns when an order has more than one fulfillment order, as the metered poll does: both map only the first fulfillment order [3].
- **CONFIRMED** Reap load is bounded by Cloud Run, not the app: `max_instance_request_concurrency` is 3 and the ceiling is 10 instances, so 30 concurrent reaps fleet-wide. The tick's single-flight mutex is per instance and best-effort; Shopify's one-operation-per-shop rule and dedupe-service absorb the rest [4][19].
- **CONFIRMED** Bulk is enabled in prod for `PURDYFIGG` only (`bulk_ingest_tick_enabled = true`). Dev carries the same pair. `global.tfvars` leaves the tick off, and preview envs close both gates. Retiring the metered poll is a Won't-do, so bulk stays a per-customer opt-in [19][20].
- **UNKNOWN** Whether PURDYFIGG's prod bulk enablement is permanent or was set for a smoke test. Nothing in the repo says.

## HTTP surface (connector)

All routes are `POST` unless noted. The `/events/*` routes return `202 Accepted`.

| Route | Trigger | Does |
| ----- | ------- | ---- |
| `/events/poll` | Cloud Scheduler, 5 min | Poll all active non-bulk connectors, canonicalise, publish `sales_order`. Single-flight. |
| `/events/revalidate-tokens` | Cloud Scheduler, daily 03:00 | Revalidate every active connector's offline token. |
| `/events/bulk-poll` | Cloud Scheduler, 5 min, via `bulk_poll_trigger` | Advance the bulk-ingest tick. Single-flight per instance. |
| `/events/reap` | `reap` topic, published by the bulk tick | Drain one COMPLETED bulk op's JSONL, canonicalise and publish. |
| `/events/manual/poll?businessId=` | manual | Poll one business, return a per-order summary. |
| `/events/config/revision` | `config_revision` topic | Refresh cached connector, mapping, DDP, routing and blacklist config. |
| `/events/confirmations/sales-order` | `confirmation_ready` (filtered `goods_out_confirmation`) | Route to the originating connector (`metadata.connectorId` and `broadcast`, else fan out), create Shopify fulfillments, publish the made confirmation, tag `ILG_FULFILLED`. Drops `role: kit_component` lines and lines with no Shopify reference. |
| `/events/confirmations/stock-adjustment` | `stock_adjustment_ready` | Adjust inventory on every active connector with `stockAdjustmentsEnabled`, publish `STOCK_ADJUSTMENT_MADE` only if one succeeded. No enabled connector: skipped, nothing published. Each Shopify mutation carries an `@idempotent` key (see Shopify API resilience). |
| `/events/acknowledgements/sales-order` | `create_acknowledge` (filtered `sales_order`) | Tag order `ILG_RECEIVED`. |
| `/events/failures/sales-order` | `create_data_failure` (filtered `sales_order`) | Tag order `ILG_ERRORED`. |
| `POST /api/v1/preview` | manual (fuse-ui "Test conditions") | Body `{ connectorId }`. Runs that connector's retrieval conditions against Shopify and reports count, earliest and latest `createdAt` and matched order headers, capped at `MAX_PREVIEW_ORDERS` (500) with a `truncated` flag. Read-only. Returns 200. |
| `GET /health/liveness` | Cloud Run probe | Health check. |

**CONFIRMED** `EventsController`, `BulkController`, `BulkPollController` and `PreviewController` sit behind `ApiKeyGuard`. It accepts a matching `x-api-key` header, or a Google-signed bearer token whose issuer is `accounts.google.com` and whose audience is the request URL. The confirmation, acknowledgement and failure controllers have no app-level guard. No global guard exists. `API_BYPASS_GUARD=true` disables the guard and logs `[HIGH SEVERITY]`; it is for dev only [5][6].

**ASSESSED** The guard checks issuer and audience, not the caller's identity, and the connector's Cloud Run service grants `run.invoker` to `allUsers`. Any Google service account can therefore mint a token that passes `ApiKeyGuard`. Anyone can post to the three unguarded event routes, including a crafted goods-out confirmation that creates fulfillments. This rests on the IaC grant at `iam.tf` and the guard code. An org-level policy outside the repo could narrow it, and nothing was exercised live [6][17].

## Pub/Sub topology

| Subscription | Ack | Notes |
| ------------- | --- | ----- |
| `poll_trigger` (internal) | 20s | |
| `bulk_poll_trigger` (internal) | 20s | Scheduler-driven, like `poll_trigger`. |
| `token_revalidation_trigger` (internal) | 600s | |
| `reap` (internal) | 600s | 30s retry backoff; DLT after 10 attempts. Published by the bulk tick. |
| `confirmation_ready` | 20s | `filter = attributes.recordType = "goods_out_confirmation" AND (attributes.source = "shopify" OR attributes.broadcast = "true")`. The `source` and `broadcast` half relies on the poller stamping both attributes; if that regresses, the subscription receives nothing. Retry backoff 10s–600s; dead-letter policy at 10 attempts, mirroring the controller's own redelivery budget. |
| `stock_adjustment_ready` | 600s | |
| `create_acknowledge` | 20s | filtered `sales_order`; 30s retry backoff; DLT after 5 attempts |
| `create_data_failure` | 20s | filtered `sales_order`; no DLT |
| `config_revision` | 20s | |

**CONFIRMED** The subscription was renamed, re-topiced and re-filtered from the original `sales_order_confirmation_ready`. The route looks unchanged but its message source changed entirely [16].

**CONFIRMED** `sales_order` publishes **only** to the cross-entity `create_record_request` topic, tagged `attributes.recordType = "sales_order"`. The legacy dual-publish leg is gone. No ingest `capture` is attached [1].

**CONFIRMED** A made confirmation publishes once, to `confirmation_made`, tagged `attributes.recordType = "goods_out_confirmation"`. The legacy `sales_order_confirmation_made` leg is gone. Stock-adjustment confirmations publish only to `stock_adjustment_made` [1].

## Confirmation routing (per-connector, not per-business)

```orient-flow
{ "v": 1, "title": "Goods-out confirmation routing",
  "nodes": [
    { "id": "in", "label": "confirmation_ready", "sub": "goods_out_confirmation", "kind": "topic", "ev": [16] },
    { "id": "c", "label": "/events/confirmations/sales-order", "kind": "step", "service": "shopify-connector", "tone": "accent", "ev": [5] },
    { "id": "r", "label": "Routed", "sub": "connectorId, not broadcast", "kind": "step", "ev": [7] },
    { "id": "f", "label": "Fan-out", "sub": "every Shopify connector", "kind": "step", "ev": [7] },
    { "id": "s", "label": "Shopify fulfil", "sub": "per fulfillment order", "kind": "external", "ev": [8] },
    { "id": "m", "label": "confirmation_made", "kind": "topic", "ev": [5] },
    { "id": "x", "label": "confirmation_data_failure", "sub": "goods_out_confirmation", "kind": "topic", "tone": "alert", "ev": [7] }
  ],
  "edges": [
    { "from": "in", "to": "c", "label": "push" },
    { "from": "c", "to": "r" },
    { "from": "c", "to": "f" },
    { "from": "r", "to": "s" },
    { "from": "f", "to": "s" },
    { "from": "s", "to": "m", "label": "delivered or already fulfilled" },
    { "from": "r", "to": "x", "label": "not deliverable", "style": "dashed" },
    { "from": "f", "to": "x", "label": "per failed leg", "style": "dashed" }
  ] }
```

A `goods_out_confirmation` carries its routing signals on the envelope: `metadata.connectorId` (stamped by the poller from the SNAP attachment), the `broadcast` Pub/Sub attribute and the `source` attribute, read via `PubsubService.parseEnvelope`. A confirmation is **routed** when it names a `connectorId` and is not a broadcast (`isRoutedConfirmation`); everything else is **fan-out** [5][7].

- **Routed** targets the single originating connector. The connector is looked up **inside the business's own Shopify connector list** (`getByBusinessIdWithUnresolved`), never through `ConnectorConfigProvider.getByConnectorId`. That resolver finds any connector by id across the whole fleet and hydrates it with `ShopifyIngressSchema`, which throws for a non-Shopify connector. A wrong id could therefore reach another customer's connector [7][10].
- **Fan-out** (`processFanOut`) reads every Shopify connector of the business one by one (`getGoodsOutConfirmationStates`: connector config plus its goods-out mapping, so one unreadable connector doesn't hide the others) and delivers to each that takes goods-out. A connector takes it by having the goods-out mapping, whatever its ingress status [7][10].

**CONFIRMED** There is no `purchase_order` path in this service (no `EntityType`, route or use case). Fleet tickets written as "PO/SO" mean sales orders only here [1].

**Failures are recorded, not dropped.** The poller clears its SNAP row once it publishes, so a silent drop would be permanent loss. `ConfirmationFailurePublisher` publishes every way a confirmation fails to reach Shopify to the egress `confirmation_data_failure` topic. The `recordType` and `useCase` are `goods_out_confirmation`, never `sales_order`, which replay dispatches as a create-side use case. Stage is `confirmation_ready`, source `shopify`. The envelope's `connectorId` is the connector that failed, never the origin's, because replay redrives to it [7].

Routed failures:

- **`source_mismatch`** — the `connectorId` names no Shopify connector for the business (another channel's confirmation that got past the subscription filter).
- **`connector_unresolvable`** — a Shopify connector for the business, but inactive or with no confirmation mapping.
- **`connector_unresolved`** — config-service couldn't return the named connector as a valid one (remote-config's `unresolved` list); retryable. **`connector_lookup_failed`** — the business's connectors couldn't be read at all; retryable.
- **No routable connector** at all for the business.
- **`ConfirmationNotDeliverableException`** from the handler: `invalid_fulfillment_order_id`, `fulfillment_order_not_found`, `fulfillment_order_not_open` (on hold, closed, cancelled) or `nothing_to_fulfil`.
- Any other handler failure (`toFailureError`: `confirmation_failed` business rule, else a retryable Shopify `dependency` error).

Fan-out records **one failure per leg that takes goods-out but wasn't delivered**, each against its own `connectorId`, beside delivery to the rest. A connector with no goods-out mapping, or a business with none, records nothing (logged and metered only). Legs fail as `use_case_inactive`, `connector_inactive`, `misconfigured` (config unreadable), `mapping_lookup_failed`, `connector_unresolved`, or on delivery with the same handler failures as above. An order **not in a shop** (`fulfillment_order_not_found`, or `invalid_fulfillment_order_id`, which fan-out checks before calling Shopify because Shopify answers a non-numeric id with a GraphQL error) is the one leg that is *not* automatically a failure: it fails only the connector the confirmation came in through (`metadata.connectorId`, or every shop when `attributes.source` is `shopify` with no connectorId), and only when no other shop delivered. Another channel's order, or one created in the WMS, records nothing [7].

**Lines.** The handler drops `role: kit_component` lines. It also drops a line with no Shopify fulfillment-order line id, so a warehouse-added free item no longer fails the whole confirmation. It logs the skipped SKUs for support and counts `confirmations.lines_skipped`. If every line is dropped, the confirmation fails as `nothing_to_fulfil` and the order is tagged `ILG_SUBSTITUTED`. A short-ship is recorded as a failure, not a made [8].

**Tracking.** Every distinct `despatches[].carrier.track` goes to Shopify as a tracking number. The company is the header rule mapped to `shipping.carrierId`, else the `carrier.id` of the first tracked despatch that has one. That rule runs through the DSL with the mapping's dictionaries, so `lookup()` resolves; an unknown dictionary fails the confirmation. An optional header rule mapped to `shipping.carrierTrackingNumberUrl` adds one URL per number. It is evaluated per number, with that number's despatch as the only entry in `despatches`. Shopify pairs URLs with numbers by position, so they go all or none. Any gap leaves them off and logs `Tracking URLs omitted…` for support, and the fulfillment still goes. The success log carries the `trackingInfo` Shopify stored [45][46].

**Already fulfilled is success.** An already-**fulfilled** fulfillment order creates no new fulfillment, but `confirmation_made` is still published and the order tagged, so a redelivery after a lost made repairs the loss. If a failure record or the `confirmation_made` publish cannot be published, the publisher or controller throws `ConfirmationRedeliveryRequiredException` and the filter replies **500** so Pub/Sub redelivers. That retry is **bounded**: from `deliveryAttempt` 10 (`MAX_TRANSIENT_DELIVERY_ATTEMPTS`, mirroring the subscription's `max_delivery_attempts`) the controller records the confirmation itself as a retryable `shopify-connector.redelivery_exhausted` failure (against the routed connector, none on fan-out) and carries on with the batch. If even that can't be published, the push is still nacked. Every other confirmation exception is acked with 202 [5][16].

## Retrieval conditions — full-replace, not AND-merge

`ConnectorConfigProvider`'s hardcoded `defaultRuleset` (`created_at` within the last 10 minutes, `fulfillment_status != FULFILLED`) applies **only** when a connector has no configured `retrievalConditions.salesOrder`. A non-empty remote condition list **fully replaces** the defaults, including any time bound. There is no implicit floor once remote conditions are present. An empty array is treated as absent. **Per connector, read that connector's own conditions to know its actual retrieval window; never assume the 10-minute default** [10].

## Per-business mapping

**CONFIRMED** Business-specific mapping comes from config-service, per connector and use case, through `ConnectorMappingsProvider`. A mapping that fails `LinedMappingConfigSchema` is logged and treated as absent [15].

**ASSESSED** The in-repo `src/core/shopify/rules/GADG` rules (`shopifyRules`) have no consumer in `src`: nothing imports the export outside its barrel. `BYOMA` is an empty placeholder. Treat the rules directory as dead code, pending a check outside the repo [40].

## Shared token store (`ShopToken`)

One Mongo collection, written by shopify-app (OAuth exchange) and refreshed on read by the connector and the egress service. A Mongo-level advisory lock guards it (`isRefreshing` and `lockTimeout`). **Every writer takes the lock through one implementation**: `ShopTokenLock` in `packages/shopify-token-management` (`tryLock` / `release` / `reclaimStale`), on the native `mongodb` driver [21].

- The connector and egress service use the full provider (`TokenProviderBase` / `ShopTokenProvider`, which delegate to the lock).
- shopify-app imports only the dependency-free `shopify-token-management/lock` entry over a native collection (`app/mongo.server.ts`, same `DATABASE_URL` Prisma uses). It keeps its own retry loop and `no_row` first-install outcome around it [23].
- The 30s lock timeout (`MONGO_LOCK_TIMEOUT`) is the package's constant, with no second copy [21].

**Never take the lock through Prisma.** Its Mongo connector can't match a missing field with equality or `NOT` filters (only `isSet`), and legacy documents predate `isRefreshing`, so a Prisma lock left those shops permanently unlockable (prod incident 2026-07-02). The native filters (`isRefreshing: { $ne: true }`, `lockTimeout: null`) do match a missing field; the package's tests pin this against a real mongod. Prisma is fine for the app's plain reads and the session `upsert`. See [[known-context#do-not-change]] [21].

The package is framework-free (the consumer supplies the collection, logger and metrics sink) and owns the token metric and event catalogue (`TOKEN_METRIC`, `TokenEvent`). Its built output must `require` real dependencies, not peers (`autoInstallPeers: false`). A consumer's dockerfile must copy the package's `node_modules` as well as its `dist`. The database is `shopify-<env>` on a MongoDB Atlas cluster owned by the `shopify-app` stack [42].

## shopify-app

```orient-flow
{ "v": 1, "title": "shopify-app token path",
  "nodes": [
    { "id": "m", "label": "Merchant", "sub": "installs, opens the app", "kind": "external" },
    { "id": "a", "label": "authenticate.admin", "sub": "token exchange, offline only", "kind": "step", "ev": [22] },
    { "id": "s", "label": "MongoSessionStorage", "sub": "rejects online sessions", "kind": "step", "ev": [23] },
    { "id": "l", "label": "ShopTokenLock", "sub": "/lock entry, native driver", "kind": "step", "ev": [21] },
    { "id": "t", "label": "ShopToken", "sub": "Prisma upsert", "kind": "store", "ev": [23] },
    { "id": "w", "label": "app/uninstalled webhook", "sub": "deletes the row", "kind": "step", "ev": [24] }
  ],
  "edges": [
    { "from": "m", "to": "a" },
    { "from": "a", "to": "s", "label": "storeSession" },
    { "from": "s", "to": "l", "label": "acquire" },
    { "from": "l", "to": "t", "label": "upsert, release" },
    { "from": "m", "to": "w", "style": "dashed" },
    { "from": "w", "to": "t", "label": "deleteMany", "style": "dashed" }
  ] }
```

- **CONFIRMED** React Router 7 embedded app (`@shopify/shopify-app-react-router`). `shopify.server.ts` sets `apiVersion` October25, `distribution: AppStore` and `future.expiringOfflineAccessTokens: true`. `MongoSessionStorage` **throws** if an online session ever reaches it [22][23].
- **CONFIRMED** Public admin URLs: prod `https://sync.integrations.fuse.ilg.software`, dev `https://sync.integrations.fuse.freightops.dev`, served through a global HTTPS load balancer and managed cert. The connector's own domain is `shopify.integrations.fuse.*`.
- **CONFIRMED** Two config TOMLs, one per env (`shopify.app.fuse.toml` prod, `shopify.app.fuse-dev.toml` dev). `client_id` is the public API key, allowlisted in `.gitleaks.toml`; the secret is `SHOPIFY_API_SECRET` in Cloud Run env. They define the scopes, redirect URLs and webhooks, including the three GDPR compliance topics plus `app/uninstalled` and `app/scopes_update` [24].
- **CONFIRMED** Scopes live in three places that must agree: the Partner-dashboard app config (the source of truth, since no CI step runs `shopify app deploy`), the TOML's `access_scopes`, and the Cloud Run `SCOPES` env. Change the dashboard first. A widened scope prompts every shop to re-consent on next app open. Both envs carry `write_orders`, `write_inventory` and `read_locations` [24].
- **ASSESSED** The `app._index` loader reads `shop` from the query string and returns the whole `ShopToken` row, access and refresh tokens included, to the client. Only the parent `app.tsx` loader calls `authenticate.admin`. React Router runs child loaders in parallel, and a data request can target one route alone. A caller may therefore read any shop's tokens without a session. The code is certain; nothing was exercised live. The fix is to authenticate in the child loader and select only `installedAt` [22].

## Egress service (`apps/shopify-egress-service`)

**CONFIRMED** The service writes stock sync exports to Shopify and confirms them. The snap-queue-polling-service producer writes a JSONL export to GCS and publishes a pointer on `confirmation_ready`. The egress service resolves the export's connector, reads the file, plans quantities, writes them with one bulk mutation, verifies every result row and publishes the outcome [25][26].

```orient-flow
{ "v": 1, "title": "Stock sync run",
  "nodes": [
    { "id": "in", "label": "confirmation_ready", "sub": "recordType stock_sync", "kind": "topic", "ev": [31] },
    { "id": "route", "label": "/events/confirmations/stock-sync", "sub": "ack 600s, 202", "kind": "step", "ev": [30] },
    { "id": "gcs", "label": "Export bucket", "sub": "JSONL, pinned bucket", "kind": "store", "ev": [34] },
    { "id": "svc", "label": "StockSyncService", "sub": "skip rules, plan, decide run", "kind": "step", "service": "shopify-connector", "tone": "accent", "ev": [26] },
    { "id": "shop", "label": "Shopify bulk mutation", "sub": "one row per SKU", "kind": "external", "ev": [26] },
    { "id": "res", "label": "result.jsonl copy", "sub": "create-only", "kind": "store", "ev": [26] },
    { "id": "made", "label": "confirmation_made", "sub": "all rows applied", "kind": "topic", "ev": [26] },
    { "id": "fail", "label": "confirmation_data_failure", "sub": "not a complete success", "kind": "topic", "tone": "alert", "ev": [26] }
  ],
  "edges": [
    { "from": "in", "to": "route", "label": "push" },
    { "from": "route", "to": "svc" },
    { "from": "svc", "to": "gcs", "label": "read export" },
    { "from": "svc", "to": "shop", "label": "catalogue, set" },
    { "from": "shop", "to": "res", "label": "verify, copy" },
    { "from": "res", "to": "made", "label": "every row applied" },
    { "from": "res", "to": "fail", "label": "rejected, mismatch", "style": "dashed" },
    { "from": "svc", "to": "fail", "label": "systemic Shopify failure", "style": "dashed" }
  ] }
```

**Routes and subscriptions.** Two filtered subscriptions on `confirmation_ready` push to Cloud Run with an OIDC token for the service's own account. Both retry at 10s–600s and dead-letter after 10 attempts to the shared `confirmation_ready` DLT [31].

| Route | Filter | Ack | Purpose |
| --- | --- | --- | --- |
| `POST /events/confirmations/stock-sync` | `recordType = "stock_sync"` | 600s | One export run. A singular `BifrostMessage<StockSyncExport>`; every other `confirmation_ready` type is a bulk message. |
| `POST /events/confirmations/stock-sync-sku` | `recordType = "stock_sync_sku"` | 60s | Redrive one SKU of a held failure. |

The filter is `recordType` alone, because the poller stamps no `source` or `broadcast` on stock sync. Both routes return 202. The DLT is a **loop-breaker, not a recovery path**: nothing subscribes to it, and a stale snapshot must never be replayed over newer levels [30][31].

**Skip rules (acknowledged).** A run is skipped, and acknowledged, when the connector cannot be resolved, is inactive, belongs to a different business from the export, or has `stockSync.enabled` off. The business check stops one customer's stock reaching another's shop. "Cannot be resolved" means config-service answered 404, returned a non-Shopify connector, or the shop has no usable token. A timeout, 5xx or held token lock is rethrown and redelivered. The token is fetched only after the settings checks pass, so a skipped connector never spends a refresh token. remote-config runs **uncached** here, because there is no `config_revision` subscription to invalidate a deactivated connector [26][35][36].

**Export read rules.** The export is read whole, buffered, with the producer capping a run at 100,000 lines. Four rules each fail the same way on every delivery, so they are acknowledged, logged as `Stock sync export rejected` and counted as `errors.generic` [26][27][34]:

- The bucket is pinned to `STOCK_SYNC_EXPORT_BUCKET`. Any `run.invoker` principal can call the route, so the pointer is untrusted.
- The object must sit under `{businessId}/{connectorId}/`, the producer's naming convention. If the producer renames, every run fails here.
- One malformed line fails the run. The message names the line number, never the line.
- The line count must equal the event's `recordCount`.

A missing or unreadable object is thrown and redelivered, since it can clear. An envelope timestamp that is not whole seconds, predates 2020 or is over five minutes ahead is rejected the same way (`invalid_timestamp`).

**Target and plan.** Stock goes to the shop's **primary Shopify location** and no other. A shop with no primary location, or an inactive one, counts `misconfigured` and is acknowledged. The plan matches each export line to a variant by SKU, verbatim. It excludes and counts a SKU the shop lacks, a SKU on several variants, an untracked item and a SKU repeated in the export. One exception: when exactly one of a SKU's variants belongs to an ACTIVE product, the plan uses it. Quantity is `max(0, quantity − allocated)`, or `max(0, quantity)` for a kit, rounded down to whole units. A variant with no active level at the location is kept, and Shopify records the quantity at an inactive level. The catalogue is one bulk query that a redelivery reuses for 15 minutes [26][28].

**Inventory run.** The plan becomes one bulk mutation, **one row per SKU**, so a rejected SKU fails only its own row. Each row sets `available` with `changeFromQuantity: null`, reason `correction`, and its own `@idempotent` key (a UUID v5 of export, location and item). The operation is named `StockSyncSet_<UTC timestamp>_<digest>`, from the envelope's `metadata.timestamp` and the export object. Before the export is read, and again before staging, the app's 25 most recent mutation runs decide what happens [26][27][29]:

- **Its own run**, in flight or completed within 24 hours, is resumed. Nothing is read or submitted again. **ASSESSED** The 24 hours is the connector's figure for how long Shopify keeps idempotency keys, not a measured limit.
- **A newer export's run** supersedes it. The push acks and never writes, so older figures cannot overwrite newer ones.
- **Another run in flight** makes it wait. `BulkOperationPendingException` redelivers the push.
- Otherwise the run starts.

**Known limit.** Reading the runs and starting one are not atomic. Two exports for one shop that arrive within seconds can both start, and the older figures can land last. The next export corrects the shop [25].

**Verification and outcome.** One download both verifies the result and copies it, create-only, to `<export object>.result.jsonl` in the export bucket. A row counts as applied only with empty `userErrors` and no top-level `errors`, and the tallied rows must equal the run's `objectCount`. Per-run SKU lines are recorded beside the export so a failure can name them [26]:

- **Every row applied:** publish `confirmation_made` (`recordType: stock_sync`) carrying the export plus the result pointer.
- **A row rejected, a count mismatch or no result:** ack, and publish `confirmation_data_failure` in the `StockSyncFailure` shape (source `shopify-egress-service`, stage `confirmation_made`, `retryable: false`). Rejected rows list `failedRecords` by SKU.
- **A systemic Shopify failure** (location lookup, catalogue query, run start or wait) publishes at once when not retryable. A retryable one is redelivered and published on the last delivery attempt instead of dead-lettering. A pending run and any fault outside Shopify (config-service, GCS) are redelivered and dead-lettered without a failure.

**One-SKU redrive.** `redriveSku` applies the same connector checks, finds the SKU's line, looks it up with one synchronous `productVariants` query and sets it with one `inventorySetQuantities`. The idempotency key includes the push's `messageId`, so a redelivery replays and a new redrive is fresh. Success publishes `confirmation_made` under `stock_sync_sku`; any failure publishes a `stock_sync` failure naming the one SKU [26].

**Deadline.** One 570 s budget runs from receipt. Every bulk wait, upload and download gets what is left. With under 60 s left before staging, or 30 s before the result read, the push is redelivered as pending and continues then. Signed urls are credentials and are never logged [27].

**Runtime.** Cloud Run, scale-to-zero in both environments, `INGRESS_TRAFFIC_ALL` with `run.invoker` granted only to its own service account. `GET /health/liveness` is the only probe. Any uncaught error replies non-2xx, so Pub/Sub redelivers; the routes acknowledge incurable faults themselves. The Pub/Sub service agent holds publisher on the DLT and subscriber on both subscriptions; without both, redelivery is not bounded [31][32][33].

## Shopify API resilience

- **GraphQL cost-based rate limiting**: order-detail fetches are batched at `MAX_CONCURRENT_ORDER_DETAIL_FETCHES = 10`. Pagination loops (six of them, across the collector and confirmation handler) cap at `MAX_*_PAGES = 100`, logging a support warning rather than looping forever. `GRAPHQL_REQUEST_RETRIES = 0` leaves the Shopify SDK's own retry doing nothing on purpose, because it only sees 429/503 and sleeps `Retry-After` seconds as milliseconds [12].
- **Throttle detection is HTTP-200-shaped, not just 429**: Shopify signals a GraphQL throttle as HTTP 200 with a `THROTTLED` error in the body. `isThrottleError` checks both that and a literal 429 [11][12].
- **Retry is owned at one chokepoint**: `executeGraphqlRequest` in `adapters/shopify/api/store.api.ts`, which every query *and* mutation passes through. Retryable means throttle, 5xx or transient network failure. `GRAPHQL_THROTTLE_MAX_RETRIES = 2` on top of the first attempt, each wait capped at `THROTTLE_MAX_WAIT_MS = 5_000`. The wait prefers Shopify's own arithmetic (points deficit ÷ restore rate), then `Retry-After`, then equal-jitter backoff, all in `adapters/shopify/api/throttle.ts`. Once retries are exhausted it throws and the poll re-runs under Pub/Sub redelivery. `ShopifyGraphQLException` carries `throttled`, `statusCode` and `retryAfterMs` so callers branch on the failure kind [11][12].
- **Per-shop API instances** are cached in an LRU of 100 entries with a 30s TTL (`ShopifyApiFactory`) [13]. The key is the shop, or shop plus connector when the runtime flag `shopify-connector.api-cache-per-connector` is on. It's read per call through remote-config 2.4.0's `provider.featureFlags`; an unresolvable flag is false, and prod has no flag. Cache metrics carry `key_mode`.
- **Runtime feature flags** come from `RemoteConfigModule`'s `.withFeatureFlags()`: a 30 s in-process snapshot, `ready()` awaited at boot for at most 1 s, and `POST /events/feature-flags/revision` fed by a push subscription on `bifrost.{env}.feature_flag_revision.v1`. Refreshes emit `fuse.feature_flag.refresh{trigger,outcome}`. The characterization harness's config fake stubs `featureFlags` (false), so a new flag consumer needs nothing there.
- **The characterization harness only intercepts `fetch`** (undici `MockAgent`, `disableNetConnect`). An axios client bypasses it and makes real requests from tests, and on Node axios `timeout` doesn't bound the whole request: its timer clears when headers arrive. Prefer `fetch` with `AbortSignal.timeout` for new outbound clients.
- **Admin API version is `2026-04`** (`API_VERSION` in `store.api.ts`, and the egress service's own constant); shopify-app still pins `October25`. `bulkOperations` and `@idempotent` don't exist before 2026-01, so never pin the connector back below it. The inventory mutations require an `@idempotent` key, derived in `StockAdjustmentHandler` as `uuidv5(messageId | recordIndex | connectorId)`. A redelivered push replays Shopify's cached result (kept 24h) instead of applying a delta twice; a deliberate republish gets a new key. The key is transport-level on purpose, never derived from WMS fields. `IDEMPOTENCY_CONCURRENT_REQUEST` retries with the same key [9][11][12].
- Failures during ingest are **published, not thrown**: a per-store or per-order canonicalisation failure publishes to `create_data_failure` and drops just that item (`Promise.allSettled` and null-drop). The rest of the poll continues [7].

## Build / test / deploy

- All three apps pin pnpm 10.24 and install from the **repo root** (one `pnpm-lock.yaml`); every dockerfile builds from the root context.
- Connector: node 24, Jest (`jest --forceExit`), Biome lint, `nest build`. No `build:check:tests` script; CI runs `test`, `lint` and `build:check` only. The Jest run includes the characterization boot smoke test and a real `mongod` from `mongodb-memory-server` [38].
- Egress service: node 24, Vitest, has `build:check:tests`.
- App: node 22, Vitest, Biome v1, `react-router build`, Prisma `db push --accept-data-loss` on container boot.
- Each app deploys independently on its own path-filtered CI. `secops.yaml` (gitleaks, per-app terraform, semgrep and image scans, and one dependency audit against the root lockfile with one root `audit-ci.jsonc`) is the only shared workflow [41].
- The connector has a preview-env system (`shopify-connector-preview-env-*`). Dispatching it on an app-only branch still builds a *connector* preview, since there is no branch input by design.
- This service's Datadog monitors and dashboards live in `gfs-bifrost/observability`, not in this repo's IaC. Scope every monitor query on `environment`, never `env`.
- **App metrics emit as `fuse.<name>`** (e.g. `fuse.api.factory.cache.miss`), defined in per-domain `providers/observability/catalog/*-metric.type.ts` constants. Datadog lowercases tag keys, so query `shopname` and `keymode`/`key_mode` as emitted. `src/exceptions/config-api.exception.ts`'s `RequestFailed`/`ValidationFailed` statics pass `endpoint` as the `cause` and drop the real error.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "apps/shopify-connector/src/app.module.ts@e9aef9e0" },
  { "id": 2, "kind": "code", "ref": "apps/shopify-connector/src/http/controllers/events.controller.ts@e9aef9e0" },
  { "id": 3, "kind": "code", "ref": "apps/shopify-connector/src/http/controllers/bulk.controller.ts@e9aef9e0" },
  { "id": 4, "kind": "code", "ref": "apps/shopify-connector/src/http/controllers/bulk-poll.controller.ts@e9aef9e0" },
  { "id": 5, "kind": "code", "ref": "apps/shopify-connector/src/http/controllers/confirmation-events.controller.ts@e9aef9e0" },
  { "id": 6, "kind": "code", "ref": "apps/shopify-connector/src/http/middleware/apiKey.guard.ts@e9aef9e0" },
  { "id": 7, "kind": "code", "ref": "apps/shopify-connector/src/core/shopify/use-cases/shopify-sales-order.service.ts@e9aef9e0" },
  { "id": 8, "kind": "code", "ref": "apps/shopify-connector/src/core/confirmations/sales-order-confirmation.handler.ts@e9aef9e0" },
  { "id": 9, "kind": "code", "ref": "apps/shopify-connector/src/core/confirmations/stock-adjustment.handler.ts@e9aef9e0" },
  { "id": 10, "kind": "code", "ref": "apps/shopify-connector/src/providers/connector/connector-config.provider.ts@e9aef9e0" },
  { "id": 11, "kind": "code", "ref": "apps/shopify-connector/src/adapters/shopify/api/store.api.ts@e9aef9e0" },
  { "id": 12, "kind": "code", "ref": "apps/shopify-connector/src/adapters/shopify/api/constants.ts@e9aef9e0" },
  { "id": 13, "kind": "code", "ref": "apps/shopify-connector/src/adapters/shopify/api/api.factory.ts@e9aef9e0" },
  { "id": 14, "kind": "code", "ref": "apps/shopify-connector/src/core/bulk/tick/bulk-ingest-tick.ts@e9aef9e0" },
  { "id": 15, "kind": "code", "ref": "apps/shopify-connector/src/core/collections/sales-order.transformer.ts@e9aef9e0" },
  { "id": 16, "kind": "code", "ref": "iac/shopify-connector/projects/bifrost-shopify-connector/pubsub.tf@e9aef9e0" },
  { "id": 17, "kind": "code", "ref": "iac/shopify-connector/projects/bifrost-shopify-connector/iam.tf@e9aef9e0" },
  { "id": 18, "kind": "code", "ref": "iac/shopify-connector/projects/bifrost-shopify-connector/schedule.tf@e9aef9e0" },
  { "id": 19, "kind": "code", "ref": "iac/shopify-connector/env/global.tfvars@e9aef9e0" },
  { "id": 20, "kind": "code", "ref": "iac/shopify-connector/env/prod.tfvars@e9aef9e0" },
  { "id": 21, "kind": "code", "ref": "packages/shopify-token-management/src/shop-token-lock.ts@e9aef9e0" },
  { "id": 22, "kind": "code", "ref": "apps/shopify-app/app/routes/app._index.tsx@e9aef9e0" },
  { "id": 23, "kind": "code", "ref": "apps/shopify-app/app/session-storage.server.ts@e9aef9e0" },
  { "id": 24, "kind": "code", "ref": "apps/shopify-app/shopify.app.fuse.toml@e9aef9e0" },
  { "id": 25, "kind": "code", "ref": "apps/shopify-egress-service/CLAUDE.md@e9aef9e0" },
  { "id": 26, "kind": "code", "ref": "apps/shopify-egress-service/src/core/stock-sync/stock-sync.service.ts@e9aef9e0" },
  { "id": 27, "kind": "code", "ref": "apps/shopify-egress-service/src/core/stock-sync/constants.ts@e9aef9e0" },
  { "id": 28, "kind": "code", "ref": "apps/shopify-egress-service/src/core/stock-sync/stock-sync-plan.ts@e9aef9e0" },
  { "id": 29, "kind": "code", "ref": "apps/shopify-egress-service/src/core/stock-sync/stock-sync-runs.ts@e9aef9e0" },
  { "id": 30, "kind": "code", "ref": "apps/shopify-egress-service/src/http/controllers/stock-sync.controller.ts@e9aef9e0" },
  { "id": 31, "kind": "code", "ref": "iac/shopify-egress-service/projects/shopify-egress-service/pubsub.tf@e9aef9e0" },
  { "id": 32, "kind": "code", "ref": "iac/shopify-egress-service/projects/shopify-egress-service/cloud-run.tf@e9aef9e0" },
  { "id": 33, "kind": "code", "ref": "iac/shopify-egress-service/projects/shopify-egress-service/iam.tf@e9aef9e0" },
  { "id": 34, "kind": "code", "ref": "apps/shopify-egress-service/src/adapters/gcs/gcs-object.store.ts@e9aef9e0" },
  { "id": 35, "kind": "code", "ref": "apps/shopify-egress-service/src/bootstrap/containers/remote-config.module.ts@e9aef9e0" },
  { "id": 36, "kind": "code", "ref": "apps/shopify-egress-service/src/core/connector/connector-resolution.service.ts@e9aef9e0" },
  { "id": 37, "kind": "code", "ref": "apps/shopify-connector/.dependency-cruiser.cjs@e9aef9e0" },
  { "id": 38, "kind": "code", "ref": ".github/workflows/shopify-connector-code-quality.yaml@e9aef9e0" },
  { "id": 39, "kind": "code", "ref": ".github/workflows/shopify-egress-service-on-push.yaml@e9aef9e0" },
  { "id": 40, "kind": "code", "ref": "apps/shopify-connector/src/core/shopify/rules/index.ts@e9aef9e0" },
  { "id": 41, "kind": "code", "ref": "CLAUDE.md@e9aef9e0", "note": "workspace, deploy and secops facts" },
  { "id": 42, "kind": "code", "ref": "iac/shopify-app/projects/shopify-app/mongo.tf@e9aef9e0" },
  { "id": 43, "kind": "code", "ref": "iac/shopify-app/projects/shopify-app/cloud-run.tf@e9aef9e0" },
  { "id": 44, "kind": "code", "ref": "iac/shopify-connector/projects/bifrost-shopify-connector/cloud-run.tf@e9aef9e0" },
  { "id": 45, "kind": "code", "ref": "apps/shopify-connector/src/core/confirmations/tracking-urls.ts@0fefcb40" },
  { "id": 46, "kind": "code", "ref": "apps/shopify-connector/src/core/confirmations/sales-order-confirmation.handler.ts@0fefcb40", "note": "buildTrackingInfo, evaluateHeaderRule, resolveTrackingUrls" }
] }
```
