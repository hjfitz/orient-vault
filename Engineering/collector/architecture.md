---
tags:
- waypoint
- collector
verified: '2026-10-13'
verified_sha: 9c4d56d
verified_paths:
- code/src
- iac/projects/collector
- iac/env
- code/package.json
- code/dockerfile
- code/tsconfig.json
- code/.env
- .github/workflows/code-quality.yaml
- .github/workflows/on-push.yaml
- CLAUDE.md
title: collector — architecture
thesis: 'A NestJS observer on Cloud Run: 35 Pub/Sub push subscriptions feed 13 MongoDB
  collections through per-type upsert keys and a monotonic lifecycle status, and an
  API-key-guarded read API serves them back. It never publishes.'
confidence: high
---
# collector — architecture

```orient-bluf
{ "v": 1, "bluf": "A NestJS observer on Cloud Run: 35 Pub/Sub push subscriptions feed 13 MongoDB collections through per-type upsert keys and a monotonic lifecycle status, and an API-key-guarded read API serves them back. It never publishes.", "confidence": "high", "action": "Declare a new specific ingest route before its generic `:recordType` sibling, and keep reference search's `$or` top-level (G1)." }
```

## Guardrails
<!-- Max ~6, pushed by `wp context --paths` / named by `wp signoff` when a diff touches them.
     kind: contract | policy | operational | technical -->

- [technical:G1] Reference search's `$or` stays **top-level**, with `bizKey` + `deletedAt: null`
  repeated inside every branch and one branch per `#` variant, and never goes through
  `withNotDeleted`. An enclosing `$and` or a two-value `$in` twin loses the sorted merge, or makes a
  high-fanout count fetch the whole business. `reference-search-index-coverage.spec.ts` catches a
  regression. — paths: code/src/core/reference-search.ts, code/src/repositories/collection.ts
- [technical:G2] Never put a query param into a Mongo filter unless it's validated as a plain string.
  Express 4's extended parser turns `?x[$ne]=y` into an object, which Mongo reads as an operator.
  `ReferenceSearchPipe` is the pattern. — paths: code/src/http
- [contract:G3] The Record ID search fields in each type's `referenceSearchFields` mirror fuse-ui's
  Transaction History `refPaths` chains (the displayed Record ID), so change both together or
  search stops finding what the UI shows. — paths: code/src/core/use-case-registry.service.ts, code/src/core/confirmation-registry.service.ts

## Where collector sits

Collector holds 35 push subscriptions [2]. Each posts to one route on `EventController` [1]. bifrost-pubsub owns the topics. This stack reads their names from remote state and owns the subscriptions [34].

```orient-flow
{ "v": 1, "title": "Create side: pipeline events to record collections",
  "nodes": [
    { "id": "req", "label": "create_record_request", "sub": "4 filtered subs: PO, SO, MD, WO", "kind": "topic", "ev": [2] },
    { "id": "cr", "label": "create_record", "sub": "1 filtered sub: RGA", "kind": "topic", "ev": [2] },
    { "id": "ack", "label": "create_acknowledge", "sub": "4 filtered subs: PO, SO, MD, RGA", "kind": "topic", "ev": [2] },
    { "id": "fail", "label": "create_data_failure", "sub": "4 filtered subs: PO, SO, MD, RGA", "kind": "topic", "ev": [2] },
    { "id": "rel", "label": "release_*", "sub": "3 subs: PO, SO, MD", "kind": "topic", "ev": [2] },
    { "id": "c", "label": "collector", "kind": "service", "service": "collector", "tone": "accent", "ev": [1] },
    { "id": "m", "label": "MongoDB", "sub": "7 record collections", "kind": "store", "ev": [7] }
  ],
  "edges": [
    { "from": "req", "to": "c", "label": "upsert, pending" },
    { "from": "cr", "to": "c", "label": "upsert, processing" },
    { "from": "ack", "to": "c", "label": "upsert, processed" },
    { "from": "fail", "to": "c", "label": "mark failed, no upsert" },
    { "from": "rel", "to": "c", "label": "soft-delete" },
    { "from": "c", "to": "m" }
  ] }
```

```orient-flow
{ "v": 1, "title": "Confirmation side: egress events to confirmation collections",
  "nodes": [
    { "id": "ready", "label": "confirmation_ready", "sub": "7 filtered subs: PO, SO, pick, pack, WOC, FGR, stock_sync", "kind": "topic", "ev": [2] },
    { "id": "sar", "label": "stock_adjustment_ready", "kind": "topic", "ev": [2] },
    { "id": "sam", "label": "stock_adjustment_made", "kind": "topic", "ev": [2] },
    { "id": "made", "label": "confirmation_made", "sub": "5 filtered subs: PO, SO, WOC, FGR, stock_sync", "kind": "topic", "ev": [2] },
    { "id": "cf", "label": "confirmation_data_failure", "sub": "5 filtered subs, snap-adapter excluded", "kind": "topic", "ev": [2] },
    { "id": "c", "label": "collector", "kind": "service", "service": "collector", "tone": "accent", "ev": [1] },
    { "id": "m", "label": "MongoDB", "sub": "6 confirmation collections, stock_adjustments, stock_sync_runs", "kind": "store", "ev": [8] }
  ],
  "edges": [
    { "from": "ready", "to": "c", "label": "store" },
    { "from": "sar", "to": "c", "label": "store, no status" },
    { "from": "sam", "to": "c", "label": "confirm, processed" },
    { "from": "made", "to": "c", "label": "record delivery" },
    { "from": "cf", "to": "c", "label": "mark failed, no upsert" },
    { "from": "c", "to": "m" }
  ] }
```

Source layout:

```
code/src/
  main.ts                 bootstrap, body parsers, Swagger
  bootstrap/modules/      app, business, database, event, health, observability modules
  http/                   controllers, guards, interceptors, middlewares, pipes, dto
  core/                   per-type services, the two registries, use-cases.service, reference-search
  repositories/           collection.ts (Collection<T>), mongo.connection.ts
  adapters/storage/       object-store.ts (GCS copy)
  models/                 constants, lifecycle, use-case registry types
  exceptions/, observability/, config/, shared/, scripts/
```

## Stack

NestJS 10 on Express 4. MongoDB through the native `mongodb` driver, with no ODM. `@gfs-bifrost/pubsub`'s `PubSubIngestor` decodes and validates envelopes. `@gfs-bifrost/observability` and `@ilg-platform/observability` ship logs and `fuse.*` metrics. `hot-shots` is the DogStatsD peer, and `dd-trace` is not a dependency. Zod 4, Swagger at `/api`. Everything runs from `code/` [25][29].

Toolchain pins disagree, so CI is the source of truth for what must pass [24][25][26]:

| Source | Pin |
| --- | --- |
| `package.json` `packageManager` | `pnpm@9.15.0` |
| `dockerfile` | `pnpm@11.11.0`, `node:24` build and `node:24-alpine` runner |
| `code-quality.yaml` | `pnpm@11.0.8`, Node `22` |
| root `mise.toml` / `code/mise.toml` | Node `24` / Node `latest` |

`pnpm.overrides` live in `package.json`, not `pnpm-workspace.yaml`.

## HTTP surfaces and auth

| Surface | Controller | Mount | Auth |
| --- | --- | --- | --- |
| Pub/Sub push ingest | `EventController` | `events/v1/*` | none in the app |
| Business query API | `BusinessController` | `/:businessId/*`, `POST` and `PUT /:businessId/:useCaseName` | `x-api-key`, with a path skip (below) |
| Records v1 | `RecordsController` | `api/v1/records/*` | `x-api-key` |
| Health | `HealthController` | `GET /health/liveness` only | none |
| Swagger UI | `SwaggerModule` | `/api` | none |

`ApiKeyGuard` is per-controller, on `BusinessController` and `RecordsController` only. It compares `x-api-key` to `API_KEY`. It returns early for any path starting `/health` or `/event` [5][10][11][29].

```orient-flow
{ "v": 1, "title": "Read path",
  "nodes": [
    { "id": "ui", "label": "fuse-ui", "kind": "service", "service": "fuse-ui", "ev": [33] },
    { "id": "g", "label": "ApiKeyGuard", "sub": "x-api-key", "kind": "step", "ev": [5] },
    { "id": "v1", "label": "api/v1/records", "sub": "13 types, ?reference=", "kind": "step", "ev": [11] },
    { "id": "leg", "label": "/:businessId/* lists", "sub": "4 record types, PO and SO confirmations", "kind": "step", "ev": [10] },
    { "id": "man", "label": "POST/PUT /:businessId/:useCaseName", "sub": "manual create and update", "kind": "step", "ev": [10] },
    { "id": "m", "label": "MongoDB", "kind": "store", "ev": [9] }
  ],
  "edges": [
    { "from": "ui", "to": "g" },
    { "from": "g", "to": "v1" },
    { "from": "g", "to": "leg" },
    { "from": "g", "to": "man" },
    { "from": "v1", "to": "m", "label": "read" },
    { "from": "leg", "to": "m", "label": "read" },
    { "from": "man", "to": "m", "label": "upsert" }
  ] }
```

**ASSESSED** The ingest routes accept any caller that can reach the URL. `cloud-run.tf` sets `ingress = "INGRESS_TRAFFIC_ALL"` and grants `roles/run.invoker` to `allUsers` [6]. `pubsub.tf` adds the push service account as a second invoker member [2]. The app never verifies the OIDC token. An org policy outside this repo could still narrow the grant. A forged push body can store a record, mark one failed or soft-delete one.

**ASSESSED** The guard's path skip reaches the manual routes. `:businessId` is the first path segment, so `POST` or `PUT /events/<useCase>` and `/health/<useCase>` skip the guard and run create or update. `createRecord` ignores the path business id and keys on the body [5][10]. Nothing in the repo exercises this, so a live probe has not confirmed it.

```orient-flow
{ "v": 1, "title": "Where the API key is checked",
  "nodes": [
    { "id": "any", "label": "Any caller", "sub": "allUsers can invoke", "kind": "external", "ev": [6] },
    { "id": "ing", "label": "events/v1/* ingest", "sub": "no guard", "kind": "step", "tone": "alert", "ev": [1] },
    { "id": "rd", "label": "api/v1 and list routes", "sub": "ApiKeyGuard", "kind": "step", "ev": [5] },
    { "id": "man", "label": "PUT /events/<useCase>", "sub": "guard skips /event and /health", "kind": "step", "tone": "alert", "ev": [5, 10] },
    { "id": "m", "label": "MongoDB", "kind": "store", "ev": [3] }
  ],
  "edges": [
    { "from": "any", "to": "ing", "label": "forged push body" },
    { "from": "any", "to": "rd", "label": "needs x-api-key", "style": "dashed" },
    { "from": "any", "to": "man" },
    { "from": "ing", "to": "m", "label": "upsert, mark, delete" },
    { "from": "man", "to": "m", "label": "upsert" },
    { "from": "rd", "to": "m", "label": "read" }
  ] }
```

Health: `GET /health/liveness` always answers 200. Its body reports `UP` or `PENDING` from `MongoConnection.getStatus()`. The status latches `UP` after the first connect and never recomputes, so it is not a live health signal [30][32]. There is no readiness route. Boot fails fast when Mongo does not connect within 5 seconds, so there is no degraded mode.

## Event ingest routes — order-sensitive

`EventController` matches routes in **declaration order**. Specific routes sit before their generic `:recordType` siblings:

- `confirmation/ready/stock_adjustment` and `confirmation/failure/stock_adjustment`, because stock adjustments live in the use-case registry and the generic routes resolve against the confirmation registry.
- `confirmation/ready/stock_sync` and `confirmation/made/stock_sync`, for the same reason.

`confirmation/made/stock_adjustment` and `record/create/return_goods_authorization` have no generic sibling to shadow them [1]. Each route has one or more Terraform push subscriptions in `pubsub.tf`, and the two must agree on the push path [2].

| Route (`events/v1/…`) | Fed by | Registry and effect |
| --- | --- | --- |
| `record/request/:recordType` (PO, SO, MD, WO) | `create_record_request`, one sub per type, filtered on `attributes.recordType` | use-case upsert, `pending` |
| `record/create/return_goods_authorization` | `create_record`, filtered `return_goods_authorization` | use-case upsert, `processing` |
| `record/ack/:recordType` (PO, SO, MD, RGA, not WO) | `create_acknowledge`, `for_each` over `local.create_lifecycle_record_types` | upsert, `processed` |
| `record/failure/:recordType` (PO, SO, MD, RGA, not WO) | `create_data_failure`, same `for_each` | `failed` on the stored doc, no upsert (`BifrostFailure`) |
| `record/release/:recordType` (PO, SO, MD) | `release_<type>`, unfiltered | soft-delete |
| `confirmation/ready/:recordType` (PO, SO, pick, pack, WOC, FGR) | `confirmation_ready`, one filtered sub each (bulk). PO matches `purchase_order` or `goods_in_confirmation`. SO matches `goods_out_confirmation` | confirmation registry upsert, no status |
| `confirmation/made/:recordType` (PO, SO, WOC, FGR) | `confirmation_made`, `for_each` over `local.confirmation_made_filters`, single or bulk | upsert, then `markDelivered` |
| `confirmation/failure/:recordType` (PO, SO, WOC, FGR) | `confirmation_data_failure`, `for_each` over `local.confirmation_failure_filters`. PO and SO match `goods_in_confirmation` and `goods_out_confirmation`. `source = snap-adapter` is excluded | `markFailed` on the stored doc, no upsert |
| `confirmation/failure/stock_adjustment` | `confirmation_data_failure`, filtered `stock_adjustment`, same exclusion | use-case `failed` |
| `confirmation/ready/stock_adjustment` | `stock_adjustment_ready`, unfiltered (bulk) | use-case upsert, status stays null |
| `confirmation/made/stock_adjustment` | `stock_adjustment_made`, unfiltered (single) | use-case upsert plus `confirmedAt`, `processed` |
| `confirmation/ready/stock_sync` | `confirmation_ready`, filtered `stock_sync` (single `StockSyncExport`) | use-case run, `pending` |
| `confirmation/made/stock_sync` | `confirmation_made`, filtered `stock_sync` (single `StockSyncResult`) | use-case run, `processed` |

The 35 subscriptions split as 4 request, 1 create, 4 acknowledge, 4 failure, 3 release, 7 ready, 5 made, 5 confirmation failure and 2 stock adjustment [2].

**Not tapped:**

- `work_order` acknowledge, failure and release: it is absent from `local.create_lifecycle_record_types`, and no `release_work_order` subscription exists.
- Pick and pack `confirmation_made` (extend `local.confirmation_made_filters`) and `confirmation_data_failure` (extend `local.confirmation_failure_filters`).
- `stock_sync` failure.
- RGA release, which the platform deprecated.

Key mechanics:

- **Sources differ by type.** PO, SO, MD and WO come off the pre-dedupe `create_record_request`. RGA comes off the post-dedupe `create_record`. Collector's per-key upsert collapses repeats onto one document, and it does not dedupe on the bus [2][33].
- **Work orders arrive untouched from fapi.** `identifiers.id` is whatever the caller sent. snap-adapter derives its own Snap shipment id and never republishes onto `create_record_request` [33].
- **Failures never upsert.** The failure envelope can carry a partial record, so collector marks the stored doc. A failure for a record it never held, or one missing its business key, is a logged no-op: `markFailed` returns 0 [1][16].
- **Failure envelopes vary by producer.** sftp-connector sends a bulk envelope of one `BifrostFailure` per confirmation. fapi sends one `BifrostFailure` whose `record` is `{ confirmations: [...] }`. The handler accepts both and a bare confirmation. A failure carrying rule `no_originating_connector` is a notice of a broadcast already sent, so the handler skips it [1].
- **Made envelopes are single or bulk.** fapi publishes PO and SO acknowledgements as bulk, so `envelopeRecordIsBulk` picks the parser [1].
- **RGA acknowledgements.** The subscription exists. `pubsub.tf` still calls it inert, and **ASSESSED** the topology lists snap-adapter as the RGA ack publisher, so it is live [2][33].
- **An unknown `:recordType` returns 404.** The 404 is non-2xx, so Pub/Sub nacks and redelivers [14].

## Subscription delivery settings

| Setting | Value |
| --- | --- |
| Expiry | All 35 set `expiration_policy { ttl = "" }`: they never expire |
| Dead-letter | None. A nacked message redelivers until the default message retention ends |
| Ack deadline | 600 s for the master-data request sub, 20 s for the rest |
| Retry policy | 23 carry 10 to 600 s exponential backoff |
| No retry policy | **Twelve**: the WOC and FGR `confirmation_ready` subs, the five `confirmation_made` subs and the five `confirmation_data_failure` subs. They redeliver immediately on a nack |

The `pubsub.tf` header claims every subscription has a retry policy. It is wrong for those twelve [2].

## Persistence and upsert semantics

`Collection.save(record, filter, metadata, status?)` runs one `updateOne(filter, …, { upsert: true })`, then an optional `advanceStatus` [3]:

- `$set: { ...record, metadata }` replaces each **top-level** key on every sighting (last writer wins). It is not a whole-document replace: a resubmission that omits a top-level block keeps the old one. `metadata` is rewritten each time, so `metadata.correlationId` is always the latest ingest's.
- `$unset: { deletedAt: "" }` un-deletes a previously soft-deleted record.
- `$setOnInsert: { lifecycle: { createdAt, status: null } }`.
- Per save it emits `fuse.collector.records_persisted` (tag `customer`) and `fuse.collector.persist_lag_ms` (now minus envelope timestamp).

Every key is the business id plus the type's customer reference, with the exceptions below. Each service's `softDelete` uses the same key plus `metadata.customer` [16][17][18][19]:

| Record | Upsert key |
| --- | --- |
| `purchase_order` | `identifiers.businessId` + `supplier.reference` (not `dates.dueIn`: it is mutable, so an amendment would fork the PO) |
| `sales_order` | `identifiers.businessId` + `order.customerRef` |
| `master_data` | `product.identifiers.businessId` + `product.identifiers.skuId` |
| `stock_adjustment` | `identifiers.businessId` + `identifiers.id` + `identifiers.lineId` |
| `return_goods_authorization` | `identifiers.businessId` + `identifiers.businessRgaNumber` |
| `work_order` | `identifiers.id` + `identifiers.businessId` + `workOrder.customerRef` (an absent ref stores as explicit `null`, so the filter cannot widen) |
| `stock_sync` run | `identifiers.businessId` + `identifiers.connectorId` + `identifiers.runId` (the export's GCS object path) |
| PO confirmation | `identifiers.receiptId` + `identifiers.bizId` |
| SO confirmation | `identifiers.shipmentId` + `identifiers.bizId` |
| pick, pack | `identifiers.shipmentId` + `identifiers.businessId` |
| WOC, FGR | `identifiers.id` + `identifiers.businessId` |

**ASSESSED** The work-order key keeps `identifiers.id`, while dedupe-service keys work orders on business plus customer ref alone [43]. A resend with a new caller-sent id forks the work order here, and dedupe holds it. The compared sources are this table and the dedupe architecture doc.

**ASSESSED** Every upsert key is backed by a non-unique compound index [7][8], so two concurrent first sightings of one key can each insert a document.

WOC and FGR have their own collections, not `purchase_order_confirmations`. Snap books a finished good off a PO it auto-generates from the work order. Folding FGRs in would blur "a supplier delivered this" with "we built this ourselves" [8].

`release_*` calls the type's `softDelete`, which sets `deletedAt` scoped by `metadata.customer`. **All reads filter out soft-deleted docs**, including `/api/v1` [3].

**Indexes are create-only and unnamed.** Each registry entry declares bare key specs, and the driver names them from the keys. `Collection.ensureIndexes()` runs at boot and only calls `createIndex`, so nothing drops [3][7][8]:

- A changed key spec makes a new index and leaves the old one in Atlas until someone drops it by hand. Copy the exact key spec from a live `getIndexes()`, never a remembered name.
- **ASSESSED** The superseded 2-field `{<business key>, lifecycle.createdAt}` list indexes are still in Atlas. The registries no longer declare them.
- The standalone `{deletedAt:1}` is still declared and **ASSESSED** redundant beside the compound. Dropping both waits on `$indexStats` showing no traffic, and no plan tracks it.
- Boot awaits index creation before `listen`, so a slow build eats the startup-probe budget. `pnpm run ensure:indexes` pre-builds them before a deploy and logs what it created [31].

The business-id query key differs by type (`buildBusinessIdQuery` and `buildConfirmationBusinessIdQuery`) [9]:

| Types | Business key |
| --- | --- |
| `master_data` | `product.identifiers.businessId` |
| PO, SO, stock adjustment, work order, RGA, stock sync | `identifiers.businessId` |
| goods-in and goods-out confirmations | `identifiers.bizId` |
| pick, pack, WOC, FGR | `identifiers.businessId` |

An unmapped type falls back to `metadata.customer`. A wrong key returns an empty list, not an error.

`api/v1/records` resolves a type against the use-case registry first, then `CONFIRMATION_RECORD_TYPES`. `goods_in_confirmation` and `goods_out_confirmation` map to the PO and SO confirmation entries. Pick, pack, WOC and FGR go under their own names. All 7 record types and 6 confirmation types list and fetch by `_id`, and anything else is a 404. The legacy `GET /:businessId/<type>/confirmations` pair serves PO and SO only [9][11].

## Lifecycle metadata

Every document carries a collector-owned `lifecycle: { createdAt, status, failedConnectorIds? }`, a sibling of the canonical body and the envelope `metadata`. `createdAt` is set once on insert from `metadata.timestamp`, in seconds or milliseconds, and never moves. `status` ranks `pending`, `processing`, `processed`, `failed` and only ever moves up, so out-of-order delivery cannot demote a record [3][4].

```orient-flow
{ "v": 1, "title": "Lifecycle status",
  "nodes": [
    { "id": "n", "label": "null", "sub": "no stage seen", "kind": "step", "ev": [4] },
    { "id": "p", "label": "pending", "sub": "create request", "kind": "step", "ev": [1] },
    { "id": "pr", "label": "processing", "sub": "RGA create_record", "kind": "step", "ev": [1] },
    { "id": "ok", "label": "processed", "sub": "acknowledge, made, stock made", "kind": "step", "tone": "accent", "ev": [1] },
    { "id": "f", "label": "failed", "sub": "failure events", "kind": "step", "tone": "alert", "ev": [4] }
  ],
  "edges": [
    { "from": "n", "to": "p" },
    { "from": "p", "to": "pr" },
    { "from": "pr", "to": "ok" },
    { "from": "ok", "to": "f", "label": "failure wins by rank" },
    { "from": "f", "to": "ok", "label": "delivery, once no connector still fails", "style": "dashed" }
  ] }
```

`failed` is terminal for the create lifecycle and for stock adjustments. A PO, SO, WOC or FGR confirmation delivery can clear it. A stage collector never taps leaves `status` alone: PO, SO and MD never reach `processing`, `work_order` never leaves `pending`, RGA never has `pending`, and pick and pack keep `status: null` [1][4].

**Confirmation failures are connector-aware.** A failure adds its `failure.connectorId` (`""` when none is named) to `lifecycle.failedConnectorIds` (`markConfirmationFailed`). A made event removes the delivering connector and `""` (`recordDelivery`, via `markDelivered`). It flips `failed` to `processed` only once the list is empty, so one connector's delivery cannot hide another's failure. A record failed before the list existed has none, so any delivery clears it. A failure arriving after the delivery still wins by rank. `/api/v1/records` serves the list [3][19].

Backfills, both idempotent: `pnpm run backfill:lifecycle` stamps `lifecycle` on pre-lifecycle documents, and `pnpm run backfill:stock-adjustment-status` marks confirmed stock adjustments `processed`.

## Stock adjustment: the one stateful record type

Two shapes land in one `stock_adjustments` collection [18]:

- `ready` (bulk) stores the adjustment with no `confirmedAt` and leaves `lifecycle.status` null.
- `made` (single) upserts the adjustment, stamps top-level `confirmedAt` from `metadata.timestamp`, and advances `status` to `processed`.

`saveRecord` never writes `confirmedAt`, so a late `ready` cannot demote a confirmed adjustment. A delivery failure marks `failed` through `advanceStatus`, which is terminal. `GET /:businessId/stock_adjustment/summary` computes per-SKU stock from confirmed adjustments only. It replays them by `dates.created`, then `identifiers.sequence`: `set` overwrites, `increase` and `decrease` are relative.

## Stock sync runs: files, not records

A stock sync announces files, not a canonical record. `stock_sync_runs` holds one document per **run**, keyed on business, connector and `runId`. Business plus connector alone would collapse every run for a connector into one document [12].

```orient-flow
{ "v": 1, "title": "Stock sync file copy",
  "nodes": [
    { "id": "ev", "label": "ready, made", "sub": "confirmation_ready and confirmation_made, recordType stock_sync", "kind": "topic", "ev": [2] },
    { "id": "c", "label": "collector", "kind": "service", "service": "collector", "tone": "accent", "ev": [12] },
    { "id": "src", "label": "Owner bucket", "sub": "sftp-connector or core-infra export bucket", "kind": "store", "ev": [22] },
    { "id": "own", "label": "collector-<env>-storage", "sub": "stock_sync/<source object>", "kind": "store", "ev": [22] },
    { "id": "m", "label": "stock_sync_runs", "sub": "pointers and status", "kind": "store", "ev": [12] }
  ],
  "edges": [
    { "from": "ev", "to": "c" },
    { "from": "src", "to": "own", "label": "server-side copy" },
    { "from": "c", "to": "own", "label": "ifGenerationMatch 0" },
    { "from": "c", "to": "m", "label": "pointer, status" }
  ] }
```

`ready` (`StockSyncExport`) stores the run `pending` with `exportPointer`. `made` (`StockSyncResult`) sets `resultPointer` and `processed`. Each event writes only its own pointer, and the status guard keeps a late `ready` from demoting a processed run. Reference search covers `identifiers.connectorId` and `identifiers.runId` [12].

Each event first copies its JSONL from the owner's bucket into `STORAGE_BUCKET` under `stock_sync/<source object>`, through the `ObjectStore` adapter [13]:

- The copy is server-side and pinned to `ifGenerationMatch: 0`. A redelivery's 412 counts as already copied, so `objectCreator` alone suffices.
- A missing source object (404) stores the run without that pointer, logs `StockSyncFileMissing` at error and counts `fuse.stock_sync.file_missing`. A wrong `STORAGE_BUCKET` shows as the same 404 on every run.
- Any other storage error is a retryable `ServiceError` (500). Nothing stores and Pub/Sub redelivers.
- The copy never touches the source objects.

**ASSESSED** The source bucket and object come straight from the message, with no allow-list [12][13]. Combined with the open ingest routes, a caller can make collector copy any object its service account can read into its own bucket. That reaches sftp-connector's bucket and the export bucket [22].

## Query API gotchas

Every list route pushes `skip`, `limit` and `sort` to Mongo through `findPaginated` or `findPaginatedWithLifecycle`. `count` defaults to 10 with a maximum of 100. The one in-memory page is `GET /:businessId/stock_adjustment/summary`, which replays confirmed adjustments per SKU and then slices [9][10].

- **Unfiltered lists sort on `lifecycle.createdAt` alone.** It is stored to the second, so ties are routine and a page can skip or repeat a record at a boundary. Reference search sorts `{lifecycle.createdAt:-1, _id:-1}` (`REFERENCE_SEARCH_SORT`) and pages deterministically [37].
- **The count is half the cost of a page.** `findPaginated` runs the page `find()` and a `countDocuments()` in parallel and returns `{data, total}`. An uncovered count can trip Atlas's Query Targeting alert even when the page is cheap [3].
- **`withNotDeleted` is the equality `{deletedAt: null}`, not `$exists: false`.** It matches absent and null alike and gets clean index bounds. That holds only because nothing writes a literal `deletedAt: null`: `save()` unsets it and `softDelete()` sets a `Date`.
- **Each list index is `{<business key>:1, deletedAt:1, lifecycle.createdAt:-1}`**, so the count answers from the index. `collection-index-coverage.spec.ts` pins this with an `explain()` test (no `FETCH` stage) [42].
- **Reference search** (`GET /api/v1/records/:recordType/:businessId?reference=`) is documented in [[reference-search]]. It matches one value exactly against the type's `referenceSearchFields`, `metadata.correlationId`, and `_id` for 24 hex characters, plus the `#`-toggled twin of each. `ReferenceSearchPipe` answers 400 to anything but a plain 1 to 256 character string. The query is the guardrailed top-level `$or` (G1). v1 responses lift `metadata.correlationId` to a top-level `correlationId`, and legacy routes do not [35][37].
- **A correlation id finds only a record's latest ingest**, because each save overwrites `metadata`.
- `POST` and `PUT /:businessId/:useCaseName` are manual operator tools: 409 on an existing match, 404 on a missing one. `buildExistenceFilter` knows only PO, SO, MD and stock adjustment, so a manual create or update of an RGA, work order or confirmation throws [9][10].
- **ASSESSED** Two legacy query params skip the plain-string rule in G2. `master_data/summary?query=` builds an unescaped case-insensitive `$regex` from the raw value. `stock_adjustment/summary?sku=` puts the raw value into the filter. The `string` typing is not enforced at runtime, and both routes sit behind the API key [10][18].

## The 204-ACK-drop footgun

`all-exceptions.filter.ts` maps `ValidationError`, `PubSubValidationError`, `DecodeError` and `PubSubDecodeError` to **HTTP 204** with a problem body. Any 2xx acks a Pub/Sub push, so a malformed or undecodable event is dropped: acknowledged, never retried, never dead-lettered. Both arms leave a trail. Each bumps `fuse.collector.record_dropped` (tags `reason` = `zod` or `decode`, and `customer`) and logs a `RecordDropped` event. The validation arm also bumps `fuse.errors.zod_validation`. `UseCaseNotFoundError` maps to 404, `ConflictError` to its own status, and `DatabaseError` and `ServiceError` to 500. Non-2xx responses nack, and Pub/Sub redelivers with backoff where the subscription has a retry policy [14].

## Config and env

`config/index.ts` is the only place that reads `process.env`, validated by Zod. Required: `ENVIRONMENT`, `API_KEY`, `MONGODB_CONNECTION_STRING`, `MONGODB_DB`, `STORAGE_BUCKET`. Optional: `PORT` (3000), `LOG_LEVEL` (`info`), `LOGGING_DISABLED`, `DATADOG_ENABLED`, `USE_SERVICE_MOCKS` [15].

`cloud-run.tf` sets `RELEASE_*_TOPIC`, and `.env.development` and `.env.test` set `CREATE_*_TOPIC` and `RELEASE_*_TOPIC`. The schema never reads them. They are template and fork leftovers, and collector needs no topic names. `cloud-run.tf` also sets `LOG_LEVEL=debug` in every environment [6].

**ASSESSED** `code/.env` is committed and carries an Atlas SRV connection string with a password for user `collector-dev` [41]. Its host names a cluster that does not match Terraform's `collector-<env>`, so the credential looks stale [23].

## Testing

- `code-quality.yaml` runs test (vitest), lint (biome) and typecheck (`build:check`), then build. It runs on PR, push to `main`, `master` and `develop`, and nightly [26].
- Nothing type-checks tests. `tsconfig.json` excludes `__test__` from `build:check`, and vitest runs specs through SWC, which only transpiles. A type error in a spec or fixture escapes both. No `build:check:tests` script exists [25][36].
- Integration and e2e tests use `mongodb-memory-server`, so no external Mongo is needed. Work orders and WOC/FGR each have an e2e spec under `code/src/__test__/e2e/`.
- A separate black-box harness lives in `/tests` and runs through `docker-compose-4pipeline.yaml` (`blackbox-testing.yaml`). That workflow's `push:` line is malformed (`branches: moisis/adding-tests]`), so it effectively runs only on PR and nightly [38].
- `docker-compose.yml` brings up Mongo 8, the service and a Pub/Sub emulator for local end-to-end runs.

## Deploy and infrastructure

A push to `master` runs `on-push.yaml`: build and push the dev image, apply dev Terraform, plan prod, then push the prod image and apply prod Terraform behind the `terraform-prod` environment approval. There is **no path filter**, so a docs-only push redeploys. `gh workflow run manual-deploy.yaml --ref <branch>` deploys a branch to dev only [27].

| Area | Fact |
| --- | --- |
| Projects | `bifrost-dev-global1` and `bifrost-prod-global1`, region `europe-west2`. Terragrunt via `ilg-platform/github-actions` workflows at `@0.1-affogato` [27] |
| Edge | Global external HTTPS load balancer on `collector.api.fuse.ilg.software` (prod) and `collector.api.fuse.freightops.dev` (dev). Managed certificate, HTTP-to-HTTPS redirect, 30 s backend timeout, A record in the ilg-platform DNS zone. Pub/Sub pushes to the Cloud Run `uri`, not the domain [2][20][40] |
| Cloud Run | Service `collector-<env>`, `INGRESS_TRAFFIC_ALL`, `allUsers` invoker. Direct VPC egress with `PRIVATE_RANGES_ONLY`, so Atlas, Pub/Sub and Datadog use the public path. No resource limits and no max instance count on the app container. `min_instance_count` defaults to 0 and prod sets 1 [6][40] |
| Sidecar | Datadog `serverless-init`, 256Mi and 500m, dual-ships logs and metrics to the GFS and ILG accounts [6] |
| Image | `node:24` build stage, `node:24-alpine` runner as user `node`, with `libcrypto3` and `libssl3` upgraded in place [24] |
| Mongo | Atlas cluster `collector-<env>`, MongoDB 8.0 LTS, three-node replica set on `EUROPE_WEST_2`, M10 autoscaling to M20, 10 GB disk. Backups and point-in-time recovery on, termination protection off. DB user `collector-user-<env>` has `readWrite` on `collector-<env>`. Atlas keys come from GitHub secrets as Terraform variables [23] |
| Storage | Private bucket `collector-<env>-storage`: the Cloud Run account has `objectCreator` and `objectViewer`. It also has `objectViewer` on sftp-connector's bucket and core-infra's stock sync export bucket (both named from remote state), and `serviceAccountTokenCreator` on itself for signed URLs [22][34] |
| IAM | The Cloud Run account holds project-level `compute.instanceAdmin`, `compute.networkUser` and `vpcaccess.user` [21] |

**ASSESSED** Terraform ignores `instance_size` and `disk_size_gb` on the cluster, so the live size can differ from M10 and 10 GB. **ASSESSED** `compute.instanceAdmin` is unused: its comment cites VPC connector management, and the service uses Direct VPC egress.

## Observability

There is no APM or tracing. Build from logs, custom metrics and `gcp.run.*` and `gcp.pubsub.*`. `observability/observability.ts` bootstraps the process-wide `{logger, metrics}` through `FuseObservabilityBuilder`. It sets no `.withChannel()`, because collector is an observer and not an origin channel. Call sites emit metrics directly, with no recorder classes.

| Name | Detail |
| --- | --- |
| Cloud Run service | `collector-<env>` |
| Sidecar `DD_SERVICE` / `DD_ENV` | `collector` / hardcoded `serverless`, so filter by `@environment`, not `env` |
| App tags | `service:collector_service`, `@domain:fuse`, `@environment` |
| Namespace | `fuse.*`, fleet-wide, discriminated by the `service:collector_service` tag |
| Shared catalogue | `fuse.collector.records_persisted`, `fuse.collector.persist_lag_ms`, `fuse.collector.record_dropped` (`reason`, `customer`), `fuse.collector.http.request` (`route`, `method`, `statusClass`, `customer`), `fuse.collector.http.latency_ms`, `fuse.mongo.latency`, `fuse.coldstart.count`, `fuse.errors.zod_validation`, `fuse.errors.generic`, `fuse.errors.unknown` |
| `fuse.mongo.up` | A gauge set on connect: a boot marker, not health |
| Service-local [28] | `fuse.event.handled` (tag `type`, such as `create_work_order` or `finished_good_receipt_made`), `fuse.event.handled_release`, `fuse.lifecycle.transition` (`to`, `type` = collection), `fuse.stock_sync.file_missing` (`customer`) |

Correlation uses the `Correlation` facade from `@gfs-bifrost/observability/correlation`. `RequestIdMiddleware` opens the root scope per request. `/event*` seeds an empty `correlationId` that the ingestor's `onCorrelationId` hook overwrites from the envelope. Other routes take `x-request-id` or mint a uuid. Each handler sets `flow`, `recordType`, `recordId` and `businessId`, which ride onto every log line. Trace a record with `service:collector_service`, `@environment` and a `correlationId` or `recordId` from the log body. Then chain to the SNAP MCP by a reference found in the log [39].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "code/src/http/controllers/event.controller.ts@9c4d56d" },
  { "id": 2, "kind": "code", "ref": "iac/projects/collector/pubsub.tf@9c4d56d" },
  { "id": 3, "kind": "code", "ref": "code/src/repositories/collection.ts@9c4d56d" },
  { "id": 4, "kind": "code", "ref": "code/src/models/lifecycle.ts@9c4d56d" },
  { "id": 5, "kind": "code", "ref": "code/src/http/guards/api-key.guard.ts@9c4d56d" },
  { "id": 6, "kind": "code", "ref": "iac/projects/collector/cloud-run.tf@9c4d56d" },
  { "id": 7, "kind": "code", "ref": "code/src/core/use-case-registry.service.ts@9c4d56d" },
  { "id": 8, "kind": "code", "ref": "code/src/core/confirmation-registry.service.ts@9c4d56d" },
  { "id": 9, "kind": "code", "ref": "code/src/core/use-cases.service.ts@9c4d56d" },
  { "id": 10, "kind": "code", "ref": "code/src/http/controllers/business.controller.ts@9c4d56d" },
  { "id": 11, "kind": "code", "ref": "code/src/http/controllers/records.controller.ts@9c4d56d" },
  { "id": 12, "kind": "code", "ref": "code/src/core/stock-sync/stock-sync.service.ts@9c4d56d" },
  { "id": 13, "kind": "code", "ref": "code/src/adapters/storage/object-store.ts@9c4d56d" },
  { "id": 14, "kind": "code", "ref": "code/src/exceptions/all-exceptions.filter.ts@9c4d56d" },
  { "id": 15, "kind": "code", "ref": "code/src/config/index.ts@9c4d56d" },
  { "id": 16, "kind": "code", "ref": "code/src/core/purchase-order/purchase-order.service.ts@9c4d56d", "note": "representative record-type service: key, softDelete, markFailed" },
  { "id": 17, "kind": "code", "ref": "code/src/core/work-order/work-order.service.ts@9c4d56d" },
  { "id": 18, "kind": "code", "ref": "code/src/core/stock-adjustment/stock-adjustment.service.ts@9c4d56d" },
  { "id": 19, "kind": "code", "ref": "code/src/core/sales-order-confirmation/sales-order-confirmation.service.ts@9c4d56d", "note": "markFailed and markDelivered" },
  { "id": 20, "kind": "code", "ref": "iac/projects/collector/load-balancer.tf@9c4d56d" },
  { "id": 21, "kind": "code", "ref": "iac/projects/collector/iam.tf@9c4d56d" },
  { "id": 22, "kind": "code", "ref": "iac/projects/collector/storage.tf@9c4d56d" },
  { "id": 23, "kind": "code", "ref": "iac/projects/collector/mongo.tf@9c4d56d" },
  { "id": 24, "kind": "code", "ref": "code/dockerfile@9c4d56d" },
  { "id": 25, "kind": "code", "ref": "code/package.json@9c4d56d" },
  { "id": 26, "kind": "code", "ref": ".github/workflows/code-quality.yaml@9c4d56d" },
  { "id": 27, "kind": "code", "ref": ".github/workflows/on-push.yaml@9c4d56d" },
  { "id": 28, "kind": "code", "ref": "code/src/observability/collector-metric.type.ts@9c4d56d" },
  { "id": 29, "kind": "code", "ref": "code/src/main.ts@9c4d56d" },
  { "id": 30, "kind": "code", "ref": "code/src/repositories/mongo.connection.ts@9c4d56d" },
  { "id": 31, "kind": "code", "ref": "code/src/scripts/ensure-indexes.ts@9c4d56d" },
  { "id": 32, "kind": "code", "ref": "code/src/http/controllers/health.controller.ts@9c4d56d" },
  { "id": 33, "kind": "doc", "ref": "fuse://pubsub-topology", "note": "publishers and subscribers; fuse-ui calls collector" },
  { "id": 34, "kind": "code", "ref": "iac/projects/collector/remotes.tf@9c4d56d" },
  { "id": 35, "kind": "doc", "ref": "Engineering/collector/explainers/reference-search.md" },
  { "id": 36, "kind": "code", "ref": "code/tsconfig.json@9c4d56d" },
  { "id": 37, "kind": "code", "ref": "code/src/core/reference-search.ts@9c4d56d" },
  { "id": 38, "kind": "code", "ref": ".github/workflows/blackbox-testing.yaml@9c4d56d" },
  { "id": 39, "kind": "code", "ref": "code/src/http/middlewares/request-id.middleware.ts@9c4d56d" },
  { "id": 40, "kind": "code", "ref": "iac/env/prod.tfvars@9c4d56d" },
  { "id": 41, "kind": "code", "ref": "code/.env@9c4d56d" },
  { "id": 42, "kind": "code", "ref": "code/src/__test__/integration/collection-index-coverage.spec.ts@9c4d56d" },
  { "id": 43, "kind": "doc", "ref": "Engineering/dedupe-service/architecture.md", "note": "work order gate key: business id plus customer ref" }
] }
```
