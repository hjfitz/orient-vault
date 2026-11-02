---
tags:
- waypoint
- dedupe-service
verified: '2026-10-13'
verified_sha: c8aa319
verified_paths:
- code/src
- iac/projects/dedupe-service
- iac/env/global.tfvars
- code/package.json
- code/pnpm-lock.yaml
- CLAUDE.md
- code/dockerfile
title: dedupe-service — architecture
thesis: A Nest app on bounded Cloud Run gates every create_record_request push through
  one IDeduper per record type backed by MongoDB, forwards survivors to create_record,
  and acks only after the work finishes.
confidence: high
---
# dedupe-service — architecture

```orient-bluf
{ "v": 1, "bluf": "A Nest app on bounded Cloud Run gates every create_record_request push through one IDeduper per record type backed by MongoDB, forwards survivors to create_record, and acks only after the work finishes.", "confidence": "high", "action": "Keep ack-versus-nack classification in CreateRequestController; never add a global guard, pipe or interceptor." }
```

## Guardrails

- [contract:G1] dedupe-service is the only production publisher of `create_record`; connectors never publish it and never dedupe.
  — paths: code/src/factory.ts, iac/projects/dedupe-service/iam.tf
- [technical:G2] The create route acks last. Transient failures nack (503), permanent ones ack and drop, and an unknown error counts as transient. That classification stays in `CreateRequestController`; no global guard, pipe or interceptor.
  — paths: code/src/http/controllers/create-request.controller.ts, code/src/exceptions/type-guards.ts, code/src/bootstrap
- [technical:G3] Every gate keys on `identifiers.businessId` plus the customer's own reference, never `identifiers.id`. A key change needs existing data to fit first, or the unique index build fails at boot.
  — paths: code/src/core, code/src/scripts
- [technical:G4] Store the original record and forward the blacklist-filtered one. Storing the filtered record makes every identical replay read as changed and re-forward.
  — paths: code/src/core/create-request.service.ts
- [technical:G5] Build each collaborator once in `buildRuntimeSingletons` and hand it to Nest with `useValue`, never `useFactory`. A factory builds a second router, Redis client and Pub/Sub client.
  — paths: code/src/factory.ts, code/src/bootstrap/containers
- [contract:G6] The `/api/v1/record` response shapes are effectively frozen. fuse-ui's Dedupe Summary and the Fuse MCP dedupe tools both consume them, and the API has no versioning.
  — paths: code/src/http/controllers/record.controller.ts, code/src/models/types.ts

## Where the gate sits

Inbound, four kinds of Pub/Sub push reach the service. Each lands on one controller. [21]

```orient-flow
{ "v": 1, "title": "Inbound: what reaches the gate",
  "nodes": [
    { "id": "ing", "label": "Ingress paths", "sub": "sftp-connector, fapi, shopify-connector, replay, fuse-mocker", "kind": "external", "ev": [26] },
    { "id": "req", "label": "create_record_request", "sub": "5 filtered subscriptions", "kind": "topic", "ev": [21] },
    { "id": "sa", "label": "snap-adapter", "kind": "service", "service": "snap-adapter", "ev": [26] },
    { "id": "rel", "label": "release_*", "sub": "sales_order, purchase_order, master_data", "kind": "topic", "ev": [21] },
    { "id": "fail", "label": "create_data_failure", "sub": "5 filtered subscriptions", "kind": "topic", "ev": [21] },
    { "id": "cs", "label": "config-service", "kind": "service", "service": "config-service", "ev": [26] },
    { "id": "cfg", "label": "config_revision", "sub": "refreshes the blacklist", "kind": "topic", "ev": [21] },
    { "id": "d", "label": "dedupe-service", "sub": "gate + blacklist", "kind": "service", "service": "dedupe-service", "tone": "accent", "ev": [5] }
  ],
  "edges": [
    { "from": "ing", "to": "req" },
    { "from": "req", "to": "d", "label": "gate" },
    { "from": "sa", "to": "rel", "label": "WMS release" },
    { "from": "rel", "to": "d", "label": "clear gate" },
    { "from": "sa", "to": "fail", "label": "rejection" },
    { "from": "fail", "to": "d", "label": "clear gate" },
    { "from": "cs", "to": "cfg" },
    { "from": "cfg", "to": "d", "label": "refresh" }
  ] }
```

Outbound, the gate publishes survivors and talks to three stores and peers. [3]

```orient-flow
{ "v": 1, "title": "Outbound: what the gate publishes and reads",
  "nodes": [
    { "id": "d", "label": "dedupe-service", "kind": "service", "service": "dedupe-service", "tone": "accent", "ev": [7] },
    { "id": "out", "label": "create_record", "sub": "attributes.recordType", "kind": "topic", "ev": [3] },
    { "id": "sa", "label": "snap-adapter", "sub": "all 5 record types", "kind": "service", "service": "snap-adapter", "ev": [26] },
    { "id": "col", "label": "collector", "sub": "RGA only", "kind": "service", "service": "collector", "ev": [26] },
    { "id": "mongo", "label": "MongoDB", "sub": "dedupe-<env>, 5 collections", "kind": "store", "ev": [3, 16] },
    { "id": "redis", "label": "Redis", "sub": "SKU blacklist", "kind": "store", "ev": [19, 23] },
    { "id": "cs", "label": "config-service", "kind": "service", "service": "config-service", "ev": [20] }
  ],
  "edges": [
    { "from": "d", "to": "out", "label": "forward" },
    { "from": "out", "to": "sa" },
    { "from": "out", "to": "col" },
    { "from": "d", "to": "mongo", "label": "held records" },
    { "from": "d", "to": "redis" },
    { "from": "d", "to": "cs", "label": "GET blacklist on miss", "style": "dashed" }
  ] }
```

Topics belong to bifrost-pubsub; this stack reads them from remote state and owns the subscriptions [36]. Source layout:

```
code/src/
  index.ts, config.ts, factory.ts   entrypoint, env config, singleton wiring
  bootstrap/                        main.ts (createApp), containers/ (AppModule, RuntimeModule)
  app.ts                            request-id/logger middleware and body parsing
  http/                             controllers/, middleware/ (guard, interceptors, filter), validators/
  core/                             create-request, release, config-revision services;
                                    one <type>/ deduper per record type; dedupe.router/; cache/
  repositories/                     Collection<T> over Mongo
  adapters/                         db/ (connection, retry policy), http/ (axios builder)
  config/                           config.api.ts (config-service client)
  models/, exceptions/, observability/, shared/, scripts/
```

## Record types

Five, each an `IDeduper` registered on `DedupeRouter` in `code/src/factory.ts` [3][32]:
`purchase_order`, `sales_order`, `master_data`, `return_goods_authorization`, `work_order`.
All five forward to the single `create_record` topic, discriminated by `attributes.recordType`.
Adding a type means an `IDeduper` in `code/src/core/<type>/`, a `register` call on both routers, a
`recordTypes` entry, and filtered subscriptions in `iac/projects/dedupe-service/pubsub.tf`.

## HTTP stack: Nest on Nest's own Express 5 instance

`code/src/index.ts` calls `createApp()` (`code/src/bootstrap/main.ts`). It builds every collaborator once via
`buildRuntimeSingletons()` (`code/src/factory.ts`), then calls
`NestFactory.create<NestExpressApplication>(AppModule.forRoot(singletons), { bodyParser: false })`.
It then hands Nest's underlying Express instance to `buildApp()` (`code/src/app.ts`) for the little that is
not a Nest route [1][2][3].

- **On Nest**: every HTTP surface. That is `HealthController`, `RecordController`, `CreateRequestController`,
  `ReleaseV1Controller`, `ReleaseV2Controller` and `ConfigRevisionController`, plus `ApiKeyGuard`, three
  status interceptors and `AllExceptionsFilter` as the only `APP_FILTER` [5]. The status interceptors set
  204/503 on the create route, 202/200 on config revision and 200/503 on readiness off the handler outcome.
  All of it lives under `code/src/http/`: `controllers/`, `middleware/` and `validators/`.
- **On the Express instance**: the observability middleware (`requestIdMiddleware`, `loggerMiddleware`, in
  `code/src/observability/middleware.ts`) and `bodyParser.json({ limit: "100mb" })` plus `urlencoded`.
  `buildApp()` mounts them as raw `app.use()` calls, not Nest middleware [2].

Every Nest provider shares the singletons built once in `factory.ts`. `RuntimeModule.forRoot` provides them `useValue`
against the symbol tokens in `code/src/models/tokens.ts`, never `useFactory` [4]. `AllExceptionsFilter`
flattens `HttpException` bodies to a bare `{ message }`, passes an object body through minus Nest's
`statusCode`/`error` keys, and answers any other error with an empty 500, which makes Pub/Sub redeliver [13].

The service pins `express` 4 and `body-parser` 1, but `@nestjs/platform-express` brings Express 5, and Nest's
instance is the Express 5 one [24][25]. `createApp` always passes that instance, so the service's own
`express()` fallback in `buildApp` never runs there. `bodyParser: false` stops Nest installing its default
100kb parser, and `main.ts` resets `query parser` to `extended` because Express 5 defaults to `simple` [1].

## Inbound HTTP

All routes are Nest controllers.

| Route | Controller | Behaviour |
| --- | --- | --- |
| `GET /health/liveness` | `HealthController` | 200 once serving, even mid-outage; the body still reports db and redis state. The Cloud Run startup probe uses it [22][27] |
| `GET /health/readiness` | `HealthController` | 503 when Mongo is not `UP` (`HealthStatusInterceptor`) [27] |
| `POST /events/v1/record/request/:recordType` | `CreateRequestController` | the gate: decode, blacklist, dedupe, forward. 204 ack, 503 nack [6] |
| `POST /events/v1/record/release/:recordType` | `ReleaseV1Controller` | `release_*` push; deletes the stored record. 204 after the work [8] |
| `POST /events/v2/record/release/:recordType` | `ReleaseV2Controller` | `create_data_failure` push; the canonical sits at `record.record` [8][9] |
| `POST /events/v1/config/revision` | `ConfigRevisionController` | refreshes the cached SKU blacklist. 202 applied, 200 acked and dropped [10] |
| `GET /api/v1/record/:recordType`, `/stats`, `/:id`; `DELETE /:id` | `RecordController` | record admin API behind `ApiKeyGuard` [11][12] |

There is no bare `GET /health`. An unknown `:recordType` on an event route is warned and acked. On the admin
API it is a 404.

`ApiKeyGuard` validates the shared `x-api-key` header and fails closed: with no `API_KEY` configured it
answers 503. It is route-scoped on `RecordController` [12]. The admin API:

- **List** pages newest first by `createdAt`. `pageSize` defaults to 25 with a maximum of 100. Filters are
  `businessId` (exact), `reference` (case-insensitive contains), `from`/`to`, and
  `minDedupeCount`/`maxDedupeCount` [11].
- **Stats** returns `{ recordType, total, duplicatesBlocked }` over the same filters.
- **Detail** and **release** key on the Mongo `_id`, the only handle common to all five types. A malformed id is
  a 400, an unknown id a 404, and a release answers 200 with `{ released: true }`.

The admin `reference` filter matches `identifiers.id` (the SKU for master data), which is not the gate key.

**Authentication of the event routes.** Pub/Sub pushes with an OIDC token for the
`pubsub_handler_invoker` service account, and `pubsub.tf` grants it `run.invoker` [21]. Its service account is declared in `iam.tf` [35]. The app never verifies
the token, and `cloud-run.tf` also grants `run.invoker` to `allUsers` [22].
**ASSESSED** The event routes therefore accept any caller that can reach the URL. Nothing in `cloud-run.tf`
restricts ingress; an org-level policy outside this repo could still narrow it.

## Subscriptions (14)

| Topic | Count | Filter | Push target |
| --- | --- | --- | --- |
| `create_record_request` | 5 | `attributes.recordType`, one per type | `/events/v1/record/request/<type>` |
| `create_data_failure` | 5 | `attributes.recordType`, one per type | `/events/v2/record/release/<type>` |
| `release_{sales_order,purchase_order,master_data}` | 3 | none | `/events/v1/record/release/<type>` |
| `config_revision` | 1 | none | `/events/v1/config/revision` |

All 14 carry `ack_deadline_seconds = var.event_ack_deadline_seconds` (60), a `retry_policy` of 10s to 600s
exponential backoff, and a never-expire `expiration_policy` [21]. Every type clears its gate off
`create_data_failure`. Only RGA and `work_order` have no `release_*` topic, so that is their only release path.
`snap-adapter` publishes the three `release_*` topics, so `/events/v1/record/release` is live [26].
No subscription has a dead-letter topic, so a nacked message loops until the 7-day retention expires.
`pubsub.tf` still declares three unreferenced `*_request_subscription_name` locals for the superseded
per-entity topics.

## Delivery contract on the create route

`postRequest` acks last: the 204 is the outcome of the work. A transient failure answers 503 and Pub/Sub
redelivers under the subscription backoff. A permanent one still acks 204 and drops [6]. `isTransientFailure`
treats Zod, decode and validation errors as permanent and defaults every other error to transient: a visible
nack storm beats silent loss [14].

```orient-flow
{ "v": 1, "title": "Create route outcomes",
  "nodes": [
    { "id": "in", "label": "Push arrives", "sub": "request/:recordType", "kind": "step", "ev": [6] },
    { "id": "v", "label": "Decode and validate", "kind": "step", "ev": [7] },
    { "id": "b", "label": "SKU blacklist", "sub": "cache, then config-service", "kind": "step", "ev": [7, 19] },
    { "id": "g", "label": "Gate write", "sub": "findOneAndUpdate, before", "kind": "step", "ev": [7, 15] },
    { "id": "f", "label": "Publish create_record", "kind": "topic", "ev": [7] },
    { "id": "ok", "label": "204 ack", "kind": "step", "tone": "accent", "ev": [6] },
    { "id": "nack", "label": "503 nack", "sub": "Pub/Sub redelivers", "kind": "step", "tone": "alert", "ev": [6, 14] }
  ],
  "edges": [
    { "from": "in", "to": "v" },
    { "from": "v", "to": "b", "label": "valid" },
    { "from": "b", "to": "g" },
    { "from": "g", "to": "f", "label": "new or changed" },
    { "from": "f", "to": "ok", "label": "forwarded" },
    { "from": "v", "to": "ok", "label": "invalid: dropped", "style": "dashed" },
    { "from": "b", "to": "ok", "label": "config unavailable: dropped", "style": "dashed" },
    { "from": "g", "to": "ok", "label": "held or fully blacklisted", "style": "dashed" },
    { "from": "g", "to": "nack", "label": "Mongo error" },
    { "from": "f", "to": "nack", "label": "publish error" }
  ] }
```

Four paths drop the record behind a 204. Each has its own metric and log, and recovery is a re-send, not a
redelivery [7]:

- **Undecodable envelope** counts `dedupe.event.invalid`.
- **Missing `metadata.customer`** logs `missing_business_id`.
- **Failed canonical validation** counts `dedupe.record.invalid`.
- **Blacklist unavailable** counts `dedupe.event.dropped_config_unavailable`. The record is neither stored nor
  forwarded, so a later sighting reads as new.

The forward publishes the blacklist-filtered record with the inbound metadata, including `metadata.capture`,
`recordId` filled in, and `attributes.recordType` [7].

The redelivery carve-out follows from acking last. The gate write stamps envelope metadata on every sighting,
acked or not, so an unchanged record under the **same** `correlationId` is a redelivery and forwards. Only a
**new** `correlationId` holds it as a customer duplicate. Hold bookkeeping (`recordDuplicateHold`) is non-fatal
for the same reason: failing it would turn the redelivery into a forward of a genuine duplicate [15].

The release routes ack 204 after the work. Invalid or unroutable messages return normally and ack. A real
failure throws, `AllExceptionsFilter` answers 500, and Pub/Sub redelivers [8][13]. The config-revision route
always acks, because every failure there is deterministic on the payload; `dedupe.config_revision.exception` is
its only signal [10].

## Persistence

MongoDB database `dedupe-<env>`, one collection per record type. Each gate keys on the business plus the
customer's own reference, never the Fuse-generated `identifiers.id`, which a customer would not resend [15][28][29][30][31]:

| Record type | Collection | Gate key (with the business id) | Admin `reference` matches |
| --- | --- | --- | --- |
| `sales_order` | `create_sales_order` | `order.customerRef` | `identifiers.id` |
| `purchase_order` | `create_purchase_order` | `supplier.reference` | `identifiers.id` |
| `return_goods_authorization` | `create_return_goods_authorization` | `identifiers.businessRgaNumber` | `identifiers.id` |
| `work_order` | `create_work_order` | `workOrder.customerRef` | `identifiers.id` |
| `master_data` | `create_master_data` | `product.identifiers.skuId` (business id at `product.identifiers.businessId`) | `product.identifiers.skuId` |

Boot builds two indexes per collection: a non-unique `{ createdAt: -1 }` backing the admin default sort and
date filters, and a unique compound index on the gate key. Sales order, purchase order, RGA and work order first
drop the superseded unique index (`Collection.dropIndexIfExists`), because a stale unique index on fields the
gate no longer reads rejects writes the current key allows [16].

`StoredRecord<T>` is `BifrostMessage<T>` plus `createdAt`, `updatedAt` and the dedupe observability fields
(`dedupeCount`, `dedupeReason`, `originalCorrelationId`, `duplicateCorrelationIds`, `lastDedupedAt`). The admin
API filters `businessId` on `metadata.customer`, the envelope value it reports back. That predicate and the
`reference` contains-match are collection scans [11][15].

Every runtime collection call runs through a shared cockatiel retry policy
(`code/src/adapters/db/mongo.resilience.ts`). It covers transient driver failures only: network, pool-cleared,
server-selection, retryable-write and the E11000 concurrent-upsert race. Permanent errors pass straight through [18].
`MongoConnection` sets explicit pool and timeout options and un-latches its status off server heartbeat events,
so health reflects a live outage instead of holding `UP` from boot [17]. Boot fails fast when Mongo is not `UP`:
there is no degraded mode for it [3].

The gate's decision mechanics are in the repo's `CLAUDE.md`: `findOneAndUpdate` with `returnDocument: "before"`,
the deep compare, and why the blacklist persists the unfiltered original [33]. Two scripts in `code/src/scripts`
support key changes: `fix:dedupe-collisions` reports (and with `--apply` repairs) data that would violate a new
unique key, and `backfill:timestamps` seeds `createdAt` on old rows.

## Cache and config

Redis (Memorystore, `BASIC` tier) holds the per-business SKU blacklist under the key
`config:sku-blacklist:<businessId>`, behind the cache's `snap-polling:` key prefix. An in-process LRU of 1,000 entries fronts it [19][23]. A
`config_revision` event with an `SKU_BLACKLIST` fragment rewrites the entry. On a miss the service fetches
`/business/<businessId>/skus/blacklist` from config-service with API-key auth [10][20].

Breaker thresholds, retry counts and the TTL (604800000 ms, one week) are Cloud Run env vars [22][34]. Redis
connect, read and write are each bounded at 5 seconds, so an outage cannot wedge boot or the write path. A
read that times out counts as a cache miss and falls through to config-service [19].

The lookup **fails closed**. An array (empty included) or a 404 is an authoritative answer and is cached.
Anything else raises `RequiredConfigMissingException` and the create route drops the record, as above [19][20].
`master_data` is all-or-nothing: with no lines to strip, a blacklisted SKU drops the record, while every other
type has its lines filtered and drops only when all lines go [28].

## Runtime

Cloud Run on Node 24 (`node:24-alpine` image) [22]. Two containers: the app, and a Datadog `serverless-init` sidecar that
dual-ships logs and metrics to both the GFS and ILG accounts. The app container is bounded: at most 5 instances
at 40 concurrent requests each, 1Gi memory and 1 CPU, and a request timeout equal to the push ack deadline. Bursts
queue in the Pub/Sub backlog instead of scaling out into Mongo. `min_instance_count` is a per-environment
variable: prod sets 1 so the UI's synchronous calls (dashboard, dedupe summary) skip a cold start, and dev
defaults to 0. Egress to Redis goes over Direct VPC; Pub/Sub, Datadog and config-service use the managed public path.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "code/src/bootstrap/main.ts@c8aa319" },
  { "id": 2, "kind": "code", "ref": "code/src/app.ts@c8aa319" },
  { "id": 3, "kind": "code", "ref": "code/src/factory.ts@c8aa319" },
  { "id": 4, "kind": "code", "ref": "code/src/bootstrap/containers/runtime.module.ts@c8aa319" },
  { "id": 5, "kind": "code", "ref": "code/src/bootstrap/containers/app.module.ts@c8aa319" },
  { "id": 6, "kind": "code", "ref": "code/src/http/controllers/create-request.controller.ts@c8aa319" },
  { "id": 7, "kind": "code", "ref": "code/src/core/create-request.service.ts@c8aa319" },
  { "id": 8, "kind": "code", "ref": "code/src/core/release.service.ts@c8aa319" },
  { "id": 9, "kind": "code", "ref": "code/src/http/controllers/release-v2.controller.ts@c8aa319" },
  { "id": 10, "kind": "code", "ref": "code/src/core/config-revision.service.ts@c8aa319" },
  { "id": 11, "kind": "code", "ref": "code/src/http/controllers/record.controller.ts@c8aa319" },
  { "id": 12, "kind": "code", "ref": "code/src/http/middleware/api-key.guard.ts@c8aa319" },
  { "id": 13, "kind": "code", "ref": "code/src/http/middleware/all-exceptions.filter.ts@c8aa319" },
  { "id": 14, "kind": "code", "ref": "code/src/exceptions/type-guards.ts@c8aa319" },
  { "id": 15, "kind": "code", "ref": "code/src/core/sales-order/sales-order.service.ts@c8aa319" },
  { "id": 16, "kind": "code", "ref": "code/src/repositories/collection.ts@c8aa319" },
  { "id": 17, "kind": "code", "ref": "code/src/adapters/db/mongo.connection.ts@c8aa319" },
  { "id": 18, "kind": "code", "ref": "code/src/adapters/db/mongo.resilience.ts@c8aa319" },
  { "id": 19, "kind": "code", "ref": "code/src/core/cache/cache.service.ts@c8aa319" },
  { "id": 20, "kind": "code", "ref": "code/src/config/config.api.ts@c8aa319" },
  { "id": 21, "kind": "code", "ref": "iac/projects/dedupe-service/pubsub.tf@c8aa319" },
  { "id": 22, "kind": "code", "ref": "iac/projects/dedupe-service/cloud-run.tf@c8aa319" },
  { "id": 23, "kind": "code", "ref": "iac/projects/dedupe-service/redis.tf@c8aa319" },
  { "id": 24, "kind": "code", "ref": "code/package.json@c8aa319" },
  { "id": 25, "kind": "code", "ref": "code/pnpm-lock.yaml@c8aa319", "note": "platform-express 11.1.29 resolves express 5.2.1" },
  { "id": 26, "kind": "doc", "ref": "fuse://pubsub-topology", "note": "publishers and subscribers of create_record_request, create_record, release_*, create_data_failure, config_revision" },
  { "id": 27, "kind": "code", "ref": "code/src/http/controllers/health.controller.ts@c8aa319" },
  { "id": 28, "kind": "code", "ref": "code/src/core/master-data/master-data.service.ts@c8aa319" },
  { "id": 29, "kind": "code", "ref": "code/src/core/purchase-order/purchase-order.service.ts@c8aa319" },
  { "id": 30, "kind": "code", "ref": "code/src/core/return-goods-authorization/return-goods-authorization.service.ts@c8aa319" },
  { "id": 31, "kind": "code", "ref": "code/src/core/work-order/work-order.service.ts@c8aa319" },
  { "id": 32, "kind": "code", "ref": "code/src/core/dedupe.router/constants.ts@c8aa319" },
  { "id": 33, "kind": "code", "ref": "CLAUDE.md@c8aa319" },
  { "id": 34, "kind": "code", "ref": "iac/env/global.tfvars@c8aa319" },
  { "id": 35, "kind": "code", "ref": "iac/projects/dedupe-service/iam.tf@c8aa319" },
  { "id": 36, "kind": "code", "ref": "iac/projects/dedupe-service/remotes.tf@c8aa319" }
] }
```
