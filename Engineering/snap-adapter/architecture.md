---
tags:
- waypoint
- snap-adapter
verified: '2026-10-13'
verified_sha: b16942a
verified_paths:
- apps/snap-adapter/src
- apps/snap-adapter/CLAUDE.md
- iac/projects/snap-adapter
- .github/workflows
- iac/env
title: snap-adapter — architecture
thesis: An Express app on Cloud Run takes create_record pushes, writes routing data
  to Firestore, then upserts the record into SnapFulfil under per-host concurrency,
  rate and circuit limits. It acks, fails or releases through Pub/Sub, and no longer
  clears SNAP's queue.
confidence: high
---
# snap-adapter — architecture

```orient-bluf
{ "v": 1, "bluf": "An Express app on Cloud Run takes create_record pushes, writes routing data to Firestore, then upserts the record into SnapFulfil under per-host concurrency, rate and circuit limits. It acks, fails or releases through Pub/Sub, and no longer clears SNAP's queue.", "confidence": "high", "action": "Write routing data before the SNAP create, and create with a keyed PUT, never a POST." }
```

## Guardrails

- [contract:G1] The adapter never clears SNAP's outbound queue. The poller clears every published confirmation, and this app has no `confirmation_made` route or subscription. Re-adding one double-clears a row [1][4][27].
  — paths: apps/snap-adapter/src/http/controllers/event.controller.ts, iac/projects/snap-adapter/pubsub.tf
- [technical:G2] Write routing provenance, and sales-order line data, to Firestore before the SNAP create, and fail the delivery transiently when the write fails. The poller reads that doc, and a create that fails or is acked as `already_in_wms` must still leave it [1][10].
  — paths: apps/snap-adapter/src/http/controllers/event.controller.ts, apps/snap-adapter/src/adapters/firestore
- [technical:G3] Create with a keyed `PUT` carrying a client-supplied id, and an array body on the shipment and receipt collection routes. Never `POST`, which mints a fresh id on a colliding client id. Never compensate with a delete, which would remove a live record [14][28].
  — paths: apps/snap-adapter/src/shared/identity-helper, apps/snap-adapter/src/core
- [contract:G4] `metadata.source` stays the originating connector. Acknowledge, release and failure publishers copy the metadata and never overwrite it, because a redrive re-sends it and routing reads it [19][26].
  — paths: apps/snap-adapter/src/adapters/pubsub
- [technical:G5] Never match a SNAP error body by fixed shape. `collectSnapFieldErrors` walks the response, because a schema-matched parser has discarded the real error twice [15][28].
  — paths: apps/snap-adapter/src/observability/classify-snap-failure.ts
- [technical:G6] Every SNAP request passes the circuit breaker, then the rate limit, then a concurrency slot. Keep the Cloud Run caps (3 instances, 5 slots each, 15 per host) far below the roughly 50 concurrent requests at which SNAP has melted down [7][16].
  — paths: apps/snap-adapter/src/adapters/customer-router, iac/projects/snap-adapter/cloud-run.tf

## Runtime shape

An Express 4 app (`bootstrap/app.ts`) mounts `/health` and `/events/v1`, with a 100 MB JSON body limit [2]. Layers follow the org convention: `http/controllers` (thin) → `core/{sales-order,puchase-order,master-data,return-goods-authorization,work-order}` → `adapters/{snap,pubsub,config,cache,http,firestore,customer-router}`. The `core/puchase-order` directory name is misspelled in source. `core/country` holds a shared helper [3].

Each entity service implements `ISnapService`: validate canonical → map to SNAP → validate the SNAP shape → create → write the SNAP-visible attachments. Attachments are duty, notes, delivery instructions and customisations. `bootstrap/factory/controller.factory.ts` builds everything once and registers the five services on a `SnapRouter` [3][11].

All five services are real implementations [3]. [[known-context]] records RGA and work order as newer and less trusted than the other three.

`config/env/config.ts` validates env with Zod. `process.env` is read nowhere else [18]. Fuse has no APM here. The service emits logs and `hot-shots` metrics only [25].

### Inbound

```orient-flow
{ "v": 1, "title": "Create path: push to outcome",
  "nodes": [
    { "id": "cr", "label": "create_record", "sub": "5 subs, one per recordType", "kind": "topic", "ev": [4] },
    { "id": "sa", "label": "snap-adapter", "sub": "POST /events/v1/record/create/:recordType", "kind": "service", "service": "snap-adapter", "tone": "accent", "ev": [1] },
    { "id": "fs", "label": "fuse-wms-routing", "sub": "write before create", "kind": "store", "ev": [10] },
    { "id": "snap", "label": "SnapFulfil", "sub": "keyed PUT", "kind": "external", "ev": [12] },
    { "id": "ack", "label": "create_acknowledge", "sub": "created, or already in WMS", "kind": "topic", "ev": [26] },
    { "id": "fail", "label": "create_data_failure", "sub": "terminal failure", "kind": "topic", "tone": "alert", "ev": [19] },
    { "id": "rel", "label": "release_*", "sub": "SO, PO, MD only", "kind": "topic", "ev": [20] }
  ],
  "edges": [
    { "from": "cr", "to": "sa", "label": "OIDC push" },
    { "from": "sa", "to": "fs", "label": "1 routing + lines" },
    { "from": "sa", "to": "snap", "label": "2 create, attachments" },
    { "from": "sa", "to": "ack", "label": "success" },
    { "from": "sa", "to": "fail", "label": "terminal", "style": "dashed" },
    { "from": "sa", "to": "rel", "label": "terminal", "style": "dashed" }
  ] }
```

`event.controller.ts` mounts two routes under `/events/v1` [1]:

| Method + path | Trigger | What happens |
| ------------- | ------- | ------------ |
| `POST /record/create/:recordType` | `create_record`, filtered per recordType | validate → map → Firestore write → create in SNAP → attachments → publish `create_acknowledge` |
| `POST /config/revision` | `config_revision` | refresh cached backends and shipment methods in Redis |

An unknown `recordType` answers 404. `/health/liveness` answers 200 with a Redis status even when Redis is down [30]. **ASSESSED** The two event routes have no app-level auth. Cloud Run grants `roles/run.invoker` only to the Pub/Sub invoker service account, with no `allUsers` binding, so the OIDC token is the gate [6]. An org policy outside this repo could change that.

### Config refresh

```orient-flow
{ "v": 1, "title": "Config path",
  "nodes": [
    { "id": "rev", "label": "config_revision", "kind": "topic", "ev": [4] },
    { "id": "sa", "label": "snap-adapter", "sub": "POST /events/v1/config/revision", "kind": "service", "service": "snap-adapter", "tone": "accent", "ev": [1] },
    { "id": "redis", "label": "Redis + memory", "sub": "backends, shipment methods", "kind": "store", "ev": [22] },
    { "id": "cs", "label": "config-service", "sub": "API fallback on miss", "kind": "service", "service": "config-service", "ev": [23] }
  ],
  "edges": [
    { "from": "rev", "to": "sa", "label": "OIDC push" },
    { "from": "sa", "to": "redis", "label": "save" },
    { "from": "sa", "to": "cs", "label": "all backends", "style": "dashed" }
  ] }
```

A `BACKEND_CONFIG` backlink refetches every backend. A `SHIPMENT_METHOD` fragment is saved directly [22]. A shipment-method miss falls back to the config API, then to the default `TBC` [23]. Both caches default to a one-week TTL [8].

The config handler returns 204 on every error [1]. **ASSESSED** A failed refresh is therefore never redelivered, and a stale entry lives until its TTL. Inferred from the status code and the cache-first read in `getSnapHostDetails`.

## Pub/Sub topology (`iac/projects/snap-adapter/pubsub.tf`)

**Inbound.** Five filtered subscriptions on the cross-entity `create_record` topic, one per recordType: `return_goods_authorization`, `purchase_order`, `sales_order`, `master_data` and `work_order`. Each has a 300 s ack deadline by default, a retry policy of 10 s to 600 s exponential backoff and a dead-letter policy of 10 attempts [4][8]. The dead-letter topic belongs to the `bifrost-pubsub` remote state, not this stack [5]. A sixth subscription takes `config_revision` with a 20 s deadline and no dead-letter policy [4].

**Outbound.** `create_acknowledge`, `create_data_failure` and the three `release_*` topics. The Cloud Run service account holds publisher rights on exactly those five topics [6].

## Create flow: retry, exhaustion, release

`handleIncomingCreateInSnapRequest` → `createSnapData` → `handleSnapFailure`, which classifies through `classifySnapFailure` [1][15].

- **Transient and within budget** (5xx, 429, timeout, circuit open, slot timeout, routing write failure): answer `503` and publish nothing. Pub/Sub redelivers with backoff.
- **Transient and exhausted, or permanent** (4xx, schema validation, structural SNAP error, missing credentials, missing reference):
  - Publish a `release_*` message when the type has one: sales order, purchase order, master data.
  - Publish `create_data_failure` in every case. RGA and work order clear the deduper only through it.
  - Answer `204`.
- **`already_in_wms`**: SNAP holds a later-stage shipment, or rejected a keyed re-PUT with only an `XDoc` / "Invalid Order Stage" error. The app publishes `create_acknowledge`, keeps the deduper hold and skips the attachments. It is metered apart from a real failure [1][15].
- **`cancelled_in_wms`** (stage 91 or 99, or header status 01): terminal. The app keeps the deduper hold and publishes nothing, because a release would send the order back onto the cancelled shipment [1].

The app counts its own retry budget. `MAX_TRANSIENT_DELIVERY_ATTEMPTS = 10` mirrors, and does not read, the Terraform `ack_event_delivery_attempts` default. It keys off the envelope's `deliveryAttempt` [1][8]. A failure before `createSnapData` runs (an undecodable envelope) logs and answers `204`, so Pub/Sub drops it.

**ASSESSED** The release, acknowledge and failure publishers log a publish error and return `false`. The controller ignores that value [19][20][26]. A failed `create_data_failure` publish therefore still answers `204`, and no failure record exists. Inferred from the call sites, not from an observed incident.

## Routing store (Firestore) {#routing-store}

Before each routed create, the adapter upserts `{connectorId, source}` from the envelope metadata into the `fuse-wms-routing` database, collection `routing-metadata`, doc `{businessId}__{entityId}` [1][10]. Firestore is the only copy for new orders. The poller reads the doc back, and reads a SNAP routing attachment only for older orders.

- The write is a field-masked merge. A redelivery replaces routing fields and never wipes line data. The mask is built from the fields present, because `mergeFields` throws on an absent one [10].
- Master data has no routing key and is skipped, as is any create with no `connectorId`, `source` or lines [1][11].
- Sales orders add `lines`, keyed by `SOLineId` with each line's extensions. Lines that share an id with differing extensions are dropped and metered as `soline_collision`. An id of 0 or less is skipped [12].
- The write is required, with no flag. It has a 20 s timeout inside the 300 s ack deadline. A failure throws `RoutingPersistenceException`, which classifies as transient [10][15].
- This stack owns the database (`firestore.tf`, delete protection on). The runtime service account holds `roles/datastore.user` [6][9].

## Read-before-write: sales-order shipments {#read-before-write}

A keyed `PUT` replaces a shipment's child lines, so a blind rewrite of a live shipment wipes its attachments. `SalesOrderService.createInSnap` therefore `GET`s `/v2/shipments/{id}` first and runs `classifyShipmentForWrite` [12][13].

- Absent (404, a "No matching entity" envelope or an empty `Results`) or stage `00` (Due Out): write.
- Any later stage: throw `already_in_wms`. Stage 91 or 99, or header status 01: throw `cancelled_in_wms`.

Only sales orders pre-check. The other four entity services `PUT` directly. See [[read-before-write-create-path]].

## Deterministic ids

Sales-order shipments, purchase-order and RGA receipts, and work-order shipments take a client-supplied id: `{≤4-char business prefix}{14-hex sha256(businessId:connectorId:ref1:ref2)}`, capped at 15 characters [14]. The ids ride in the array body of `PUT /v2/shipments` or `PUT /v2/receipts/`, so a redelivery upserts [12][21]. A record with no business or reference throws `DeterministicIdException`, a permanent failure.

A work order lands as an `S10` shipment. Its `CarrierId` comes straight from `identifiers.carrierId`, with no default [21].

## SNAP write-response handling

SNAP answers a write per segment (`HEADER_POST`, `LINE_UPDATE`, and so on). Partial success is the normal shape, and the top-level `Successes: 0/1` tally never names the failing field. `collectSnapFieldErrors` walks the response for any node carrying `ColumnId` and `Error` [15]. A structural 5xx ("Object reference not set…", "API Error - Please contact support") is permanent, because redelivery cannot fix it [15][28].

## Concurrency protection against SNAP

SNAP degrades hard under load. [[known-context]] records the May 2026 incidents: about 10-20 concurrent requests is comfortable, and 50-60 produced 12-18 s average latency and roughly 70% hourly failures. Every request through `CustomerHttpRouter` passes three gates in this order [16]:

1. **`SnapCircuitBreaker`**, per host. Five consecutive 5xx or network failures open it. A 4xx counts as success. It half-opens after 30 s. It is hand-rolled, because the gate runs in an axios interceptor [17].
2. **`TokenBucket`**, per host: 10 requests per second, burst 20.
3. **`Semaphore`**, per host: 5 slots per instance, with a 30 s acquire timeout that nacks the delivery.

Cloud Run adds a cap of 3 instances and 30 concurrent requests per instance, so 15 SNAP slots per host at most [7]. The per-request timeout is 120 s with one retry. The retry replays only idempotent methods, honours `Retry-After` up to 60 s and releases its slot before it sleeps [18][29].

## Build, test, deploy

- pnpm `10.30.3` and node 24 (`mise.toml`, `packageManager`, Dockerfile). Tests run on Vitest; lint runs on Biome [25].
- **ASSESSED** `snap-adapter-code-quality.yaml` pins pnpm `11.0.8`, which disagrees with the app's pin. A CI lockfile install may therefore use a different pnpm major than the image build.
- CI is `.github/workflows/snap-adapter-*.yaml`: `code-quality`, `on-push`, `manual-deploy` (dev only), `blackbox-testing` and `tf-output` [24].
- `on-push` deploys dev, then a prod leg behind the `terraform-prod` environment. It path-filters on `apps/snap-adapter/**`, `iac/projects/snap-adapter/**` and `iac/env/**`. The poller's workflow filters on `iac/env/**` too, so an `iac/env` edit deploys both apps [24].
- Cloud Run service `snap-adapter-{env}` in `europe-west2`, projects `bifrost-dev-global1` and `bifrost-prod-global1`. A Datadog sidecar ships logs and metrics to two orgs [7][24].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "apps/snap-adapter/src/http/controllers/event.controller.ts@b16942a" },
  { "id": 2, "kind": "code", "ref": "apps/snap-adapter/src/bootstrap/app.ts@b16942a" },
  { "id": 3, "kind": "code", "ref": "apps/snap-adapter/src/bootstrap/factory/controller.factory.ts@b16942a" },
  { "id": 4, "kind": "code", "ref": "iac/projects/snap-adapter/pubsub.tf@b16942a" },
  { "id": 5, "kind": "code", "ref": "iac/projects/snap-adapter/remote.tf@b16942a" },
  { "id": 6, "kind": "code", "ref": "iac/projects/snap-adapter/iam.tf@b16942a" },
  { "id": 7, "kind": "code", "ref": "iac/projects/snap-adapter/cloud-run.tf@b16942a" },
  { "id": 8, "kind": "code", "ref": "iac/projects/snap-adapter/variables.tf@b16942a" },
  { "id": 9, "kind": "code", "ref": "iac/projects/snap-adapter/firestore.tf@b16942a" },
  { "id": 10, "kind": "code", "ref": "apps/snap-adapter/src/adapters/firestore/routing-metadata.store.ts@b16942a" },
  { "id": 11, "kind": "code", "ref": "apps/snap-adapter/src/adapters/snap/snap-service.type.ts@b16942a" },
  { "id": 12, "kind": "code", "ref": "apps/snap-adapter/src/core/sales-order/sales-order.service.ts@b16942a" },
  { "id": 13, "kind": "code", "ref": "apps/snap-adapter/src/adapters/snap/shipment-stage.ts@b16942a" },
  { "id": 14, "kind": "code", "ref": "apps/snap-adapter/src/shared/identity-helper/create-deterministic-id.ts@b16942a" },
  { "id": 15, "kind": "code", "ref": "apps/snap-adapter/src/observability/classify-snap-failure.ts@b16942a" },
  { "id": 16, "kind": "code", "ref": "apps/snap-adapter/src/adapters/customer-router/customer.http-router.ts@b16942a" },
  { "id": 17, "kind": "code", "ref": "apps/snap-adapter/src/adapters/snap/snap-circuit-breaker.ts@b16942a" },
  { "id": 18, "kind": "code", "ref": "apps/snap-adapter/src/config/env/config.ts@b16942a" },
  { "id": 19, "kind": "code", "ref": "apps/snap-adapter/src/adapters/pubsub/entity-error.service.ts@b16942a" },
  { "id": 20, "kind": "code", "ref": "apps/snap-adapter/src/adapters/pubsub/release.service.ts@b16942a" },
  { "id": 21, "kind": "code", "ref": "apps/snap-adapter/src/core/work-order/work-order.service.ts@b16942a" },
  { "id": 22, "kind": "code", "ref": "apps/snap-adapter/src/adapters/cache/cache.service.ts@b16942a" },
  { "id": 23, "kind": "code", "ref": "apps/snap-adapter/src/config/user/user-config.service.ts@b16942a" },
  { "id": 24, "kind": "code", "ref": ".github/workflows/snap-adapter-on-push.yaml@b16942a" },
  { "id": 25, "kind": "code", "ref": "apps/snap-adapter/package.json@b16942a" },
  { "id": 26, "kind": "code", "ref": "apps/snap-adapter/src/adapters/pubsub/entity-acknowledge.service.ts@b16942a" },
  { "id": 27, "kind": "pr", "ref": "gfs-bifrost/snap-adapter#294" },
  { "id": 28, "kind": "code", "ref": "apps/snap-adapter/CLAUDE.md@b16942a" },
  { "id": 29, "kind": "code", "ref": "apps/snap-adapter/src/adapters/http/interceptors/retry.interceptor.ts@b16942a" },
  { "id": 30, "kind": "code", "ref": "apps/snap-adapter/src/http/controllers/health.controller.ts@b16942a" }
] }
```
