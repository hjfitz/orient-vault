---
tags:
- waypoint
- replay-service
verified: '2026-10-13'
verified_sha: 43380eb
verified_paths:
- code/src
- iac/projects/replay
- .github/workflows
- code/package.json
- code/dockerfile
- code/mise.toml
- mise.toml
- iac/env
- CLAUDE.md
title: replay-service — architecture
thesis: A public Nest app on Cloud Run stores each pushed failure as received in one
  Mongo collection, replays it only after a strict canonical gate, and clears it when
  a later delivery succeeds.
confidence: high
---
# replay-service — architecture

```orient-bluf
{ "v": 1, "bluf": "A public Nest app on Cloud Run stores each pushed failure as received in one Mongo collection, replays it only after a strict canonical gate, and clears it when a later delivery succeeds.", "confidence": "high", "action": "Do not treat the /event routes as authenticated: Cloud Run admits allUsers and the app never verifies the Pub/Sub token. Keep the strict replay gate and the ack-and-drop guard intact." }
```

## Guardrails

- [technical:G1] The poison-message guard has three parts that stay together: the handler acks and drops `ValidationError`/`DecodeError`, the subscription `filter` excludes non-matching messages, and the dead-letter topic catches transient failures after 5 attempts. Touching one without the others reopens the dev redelivery loop.
  — paths: code/src/http/controllers/event.controller.ts, iac/projects/replay/pubsub.tf
- [technical:G2] Store `failure.record` as received and validate only at replay, against the target's strict canonical schema. Re-checking on store (even leniently) drops records whose failure was a wrong-typed value, so they never reach the Retry Queue.
  — paths: code/src/http/controllers/failures.controller.ts, code/src/core/failure/failure.service.ts, code/src/core/failure/derive-replayability.ts
- [contract:G3] A confirmation redrive goes back to the channel that failed, never as a broadcast. A failure whose `source` is not a delivery channel answers 400 until an operator sets `routing`. Other connectors may already have delivered it.
  — paths: code/src/core/failure/confirmation-redrive-routing.ts, code/src/http/controllers/failures.controller.ts
- [technical:G4] Clear-down is soft and connector-aware. It matches `useCase` + `businessId` + the record's own identifier. A failure pinned to a connector clears only on a delivery naming that connector. A hard delete would erase the history of a failure that succeeded on replay.
  — paths: code/src/core/failure/failure.service.ts, code/src/core/failure/derive-record-id.ts, code/src/http/controllers/event.controller.ts
- [technical:G5] A new capturable record type needs four touchpoints: a subscription `filter` entry, a schema-map entry, an `extractBusinessId` case and a `deriveRecordId` case. Miss the business-id case and the row stores with `businessId: ""`, so no queue ever shows it. Each filter stays under 256 characters.
  — paths: code/src/core/failure/failure.service.ts, code/src/core/failure/derive-record-id.ts, code/src/models/constants.ts, iac/projects/replay/pubsub.tf
- [contract:G6] Stock sync redrive has two shapes. A whole run keeps its stored timestamp and publishes under `stock_sync`. A single SKU publishes under `stock_sync_sku`, so a consumer filtering on `stock_sync` never reads it as a new run.
  — paths: code/src/core/failure/failure.service.ts, code/src/adapters/pubsub/pubsub.service.ts, code/src/models/constants.ts

## Runtime shape

NestJS 11 on `platform-express`, MongoDB, `@google-cloud/pubsub` and Zod v4 [20]. The layers are `http/controllers` → `core/failure` → `adapters/{pubsub,mongo}` and `repositories`. `event.controller.ts` takes the Pub/Sub pushes and `failures.controller.ts` takes the admin API. Swagger UI is at `/api`. There is no global prefix: the push routes are `/event/*`, singular, and predate the org's `/events/v1` convention. The JSON body limit is 100 MB [15].

Inbound, three topics feed the service and the operator console drives the admin API.

```orient-flow
{ "v": 1, "title": "Inbound: what reaches the failure inbox",
  "nodes": [
    { "id": "prod", "label": "Pipeline producers", "sub": "snap-adapter, sftp-connector, shopify-connector, fapi, egress", "kind": "external", "ev": [27] },
    { "id": "cdf", "label": "create_data_failure", "sub": "1 subscription, 4 record types", "kind": "topic", "ev": [11] },
    { "id": "ccf", "label": "confirmation_data_failure", "sub": "2 subscriptions, 8 record types", "kind": "topic", "ev": [11] },
    { "id": "made", "label": "confirmation_made", "sub": "2 subscriptions", "kind": "topic", "ev": [11] },
    { "id": "r", "label": "replay-service", "sub": "/event/*", "kind": "service", "service": "replay-service", "tone": "accent", "ev": [1] },
    { "id": "m", "label": "failures", "sub": "MongoDB, soft delete", "kind": "store", "ev": [3, 9] },
    { "id": "dlt", "label": "Dead-letter topics", "sub": "3, unconsumed", "kind": "topic", "tone": "alert", "ev": [11] }
  ],
  "edges": [
    { "from": "prod", "to": "cdf" },
    { "from": "prod", "to": "ccf" },
    { "from": "prod", "to": "made", "label": "success acks" },
    { "from": "cdf", "to": "r", "label": "push" },
    { "from": "ccf", "to": "r", "label": "push" },
    { "from": "made", "to": "r", "label": "push" },
    { "from": "r", "to": "m", "label": "store / clear down" },
    { "from": "r", "to": "dlt", "label": "5 failed attempts", "style": "dashed" }
  ] }
```

Outbound, a replay publishes the stored canonical to one of two cross-entity topics. The service publishes nowhere else.

```orient-flow
{ "v": 1, "title": "Outbound: where a replay goes",
  "nodes": [
    { "id": "ui", "label": "fuse-ui", "sub": "Retry Queue, x-api-key", "kind": "service", "service": "fuse-ui", "ev": [10] },
    { "id": "r", "label": "replay-service", "sub": "/api/v1/failures", "kind": "service", "service": "replay-service", "tone": "accent", "ev": [2] },
    { "id": "gate", "label": "Strict canonical gate", "sub": "400 when invalid", "kind": "step", "tone": "alert", "ev": [2, 6] },
    { "id": "req", "label": "create_record_request", "sub": "inbound types", "kind": "topic", "ev": [3] },
    { "id": "rdy", "label": "confirmation_ready", "sub": "confirmations + stock sync", "kind": "topic", "ev": [3] },
    { "id": "dd", "label": "dedupe-service", "kind": "service", "service": "dedupe-service", "ev": [27] },
    { "id": "conn", "label": "Connectors and egress", "sub": "fapi, sftp-connector, shopify-connector, collector, egress", "kind": "external", "ev": [27] }
  ],
  "edges": [
    { "from": "ui", "to": "r", "label": "replay" },
    { "from": "r", "to": "gate" },
    { "from": "gate", "to": "req", "label": "inbound" },
    { "from": "gate", "to": "rdy", "label": "confirmation, stock sync" },
    { "from": "req", "to": "dd" },
    { "from": "rdy", "to": "conn", "label": "by recordType and source" }
  ] }
```

## Ingestion: three failure subscriptions, one storage path

- **`POST /event/create-failure`** is a push subscription on `create_data_failure`, filtered to `sales_order`, `purchase_order`, `master_data` and `work_order`. It decodes the envelope and validates only the inner `BifrostFailure`. The embedded `failure.record` is stored as received [1][3]. An unknown `useCase` is acked and skipped.
- **`POST /event/confirmation-failure`** is two push subscriptions on `confirmation_data_failure`. One carries `pick_confirmation`, `pack_confirmation`, `work_order_confirmation` and `finished_good_receipt`. The other carries `goods_in_confirmation`, `goods_out_confirmation`, `return_goods_confirmation` and `stock_sync`. They split because a Pub/Sub `filter` caps at 256 characters [11].
> SUPERSEDED 2026-10-19: sftp-connector sends one single-record message per failure; no producer sends the bulk envelope. See [[known-context#where-it-failed]].
- The confirmation handler takes a single `BifrostMessage` (fapi) or a `BifrostBulkMessage` (sftp-connector). It unwraps fapi's `{ confirmations: [...] }` record so each confirmation is its own failure. An invalid envelope drops the whole delivery and stores nothing [1].
- A failure whose error `rule` is `no_originating_connector` is acked and not stored. The poller already broadcast that confirmation, so a replay would duplicate it [1].
- Both routes persist through `saveCreateFailure` into the `failures` collection under a fresh `randomUUID()`. A redelivery therefore creates a second row [3].
- `businessId` comes from `record.identifiers.businessId`. `master_data` reads `record.product.identifiers.businessId`. `stock_sync` reads `record.businessId`. A missing or non-string value gives `""` [3].
- All five subscriptions use a 20 s ack deadline, a 30 s minimum backoff and a dead-letter policy of 5 delivery attempts. The three dead-letter topics have no consumer [11].

## Clear-down: `POST /event/confirmation-made`

Two push subscriptions on `confirmation_made` share one dead-letter topic. The first carries pick, pack, work-order confirmation, `stock_sync` and `stock_sync_sku`. The second carries finished-good receipt, goods-in, goods-out and `return_goods_authorization` [11]. The handler maps RGA's made-side name to the stored `return_goods_confirmation` [7].

Connectors publish one single-record `BifrostMessage` per delivered record. The handler also accepts a bulk envelope [1].

For each confirmation the handler soft-deletes matching failure rows. The match is `useCase` + `identifiers.businessId` + the record's own identifier from `confirmationRecordKey`. That is the field the Retry Queue shows as Record ID:

- `shipmentId` for pick, pack and goods-out.
- `receiptId` for goods-in.
- `businessRgaNumber`, then `id`, for RGA.
- `workOrderId`, `businessWorkOrderId`, then `id`, for work-order confirmation and finished-good receipt.

The key is not the SNAP `queueId`, because a later poll re-delivers a confirmation under a new one [5].

**Connector-aware.** A failure with no `connectorId` clears on any delivery. A failure pinned to a connector clears only when the ack's `metadata.connectorId` names it. Broadcast acks do not name the connector that took the record [3].

**Soft, not hard.** The row gains `deletedAt`, `clearedAt` and `clearedBy` (`{ source, connectorId? }`). A cleared row leaves every queue read and cannot be replayed. `GET /failures?resolved=true` still lists it, and `/failures/replays` keeps its attempts. `clearedAt` is distinct from a person's `dismissedAt` [3][9].

**Stock sync.** A `stock_sync` ack soft-deletes the held run, matched on `businessId` + `record.export.object` and the same connector scope. A `stock_sync_sku` ack records the SKU in `resolvedSkus`. When every SKU in `failedRecords` is resolved, the run clears. A SKU outside `failedRecords`, or already resolved, changes nothing. An ack that fails its schema is acked and dropped [1][3].

## Admin API: `/api/v1/failures`

`ApiKeyGuard` guards the controller with `x-api-key` [10].

| Route | Notes |
| ----- | ----- |
| `GET /failures` | Paginated list, `count` at most 100. Filters: `useCase`, `businessId`, `createdAt` (whole day), `replayed`, `search`, `sort`, `reason`, `connectorId`, `transaction`, `assigned`, `resolved`. `resolved=true` lists cleared failures instead of the live queue. |
| `GET /failures/stats` | Whole-queue aggregate cards. List filters never narrow it. |
| `GET /failures/replays` | Every replay attempt, flattened, including soft-deleted rows. This is the resolved-cases view. |
| `GET /failures/groups` | Group headers by `reason`, `connector` or `transaction`, largest first, capped at 100 groups. |
| `GET /failures/:id` | Full detail with `replayable` and `blockingIssues`. It runs the same strict schema the replay gate runs. A confirmation also returns `redriveRouting`. A stock sync run also returns `skuRedrives` and `resolvedSkus`. |
| `PATCH /failures/:id` | Repairs the record before replay and diffs it into `editHistory`. It also takes `routing` (`{ source, connectorId? }` or `null`) on confirmation failures only. |
| `POST /failures/:id/replay` | Replays one failure. |
| `POST /failures/replay` | Bulk replay. Body `{ ids }`, deduplicated, at most 100, run 5 at a time. One bad id never fails the batch. |
| `POST /failures/:id/skus/:sku/replay` | Redrives one SKU of a held stock sync run. |
| `POST /failures/:id/assign` | Soft claim from `x-user`. It is not a lock, and a new claim always replaces the old one. |
| `POST /failures/:id/dismiss` | Soft delete with a required reason. |
| `DELETE /failures/:id` | Hard delete with no audit trail. Prefer `dismiss`. |

`reason` and `recordId` are derived at read time. A stored `reason` wins. `search` matches the fields backing them, plus `record.export.object` and `record.failedRecords.sku`. The `reason=` filter and the `reason` grouping share one `REASON_EXPRESSION` and cost a collection scan [3].

## Replay semantics

`getReplayTarget(useCase)` resolves one of three destinations. Each stamps `attributes.recordType`. A `null` target (unknown use case, or an unset topic env var) answers 400 [3].

| Kind | Types | Topic | Envelope |
| ---- | ----- | ----- | -------- |
| inbound | `sales_order`, `purchase_order`, `master_data`, `work_order` | `CREATE_RECORD_REQUEST_TOPIC` | single `BifrostMessage` |
| confirmation | pick, pack, work-order confirmation, finished-good receipt, goods-in, goods-out, RGA | `CONFIRMATION_READY_TOPIC` | single-element `BifrostBulkMessage` |
| stock sync | `stock_sync` | `CONFIRMATION_READY_TOPIC` | single `BifrostMessage` of the run's export pointer |

RGA is the one type where the tag differs from the stored `useCase`. It publishes `recordType = "return_goods_authorization"`, the value fapi and sftp-connector filter on [3].

1. **Route the confirmation.** `resolveConfirmationRedriveRouting` takes an operator-set `routing`, else the failure's own `source` when it is `rest`, `sftp` or `shopify`. The redrive stamps `attributes.source` with it and sets `metadata.connectorId` to the routed connector, or drops it on a channel-only override. Connectors subscribe on `source` or `broadcast`, so a redrive without `source` reached only the collector [4][2].
2. **Revalidate.** The service runs the target's strict canonical schema before publishing. A fresh failure usually fails here until a `PATCH` repairs it. A 400 means "fix the record", not a bug [2][6].
3. **Publish.** Metadata is preserved except a fresh `timestamp`. `source` is never invented, because routing reads it downstream [8].
4. **Record.** The service appends a `replayHistory` entry on success and on failure. `by` is the caller's `x-user` header. That is attribution, not authentication [2][3].

### Stock sync redrive

A held `stock_sync` run stores the egress service's failure with its full `failedRecords` list. The run's `recordId` is its `export.object`. The tests use `source: "shopify-egress-service"` [3][31].

- **Whole run.** The generic replay republishes the run's export pointer to `confirmation_ready` as `stock_sync`. It keeps the stored `metadata.timestamp` and skips channel routing. **ASSESSED** from the commit message: egress derives a run key from that timestamp, rejects a millisecond or future value, and marks a redrive superseded if a newer export ran since [29][3].
- **One SKU.** The route 400s unless the failure is `stock_sync`, the SKU is in `failedRecords`, and it is unresolved. It publishes the export pointer plus the SKU as `stock_sync_sku`. Each attempt lands in `skuRedrives`, not `replayHistory` [2][3][30].
- **Consumers.** The Fuse MCP lists shopify-egress-service as the `stock_sync` subscriber on `confirmation_ready` [27]. **UNKNOWN**: which service consumes `stock_sync_sku`, because the catalog does not list it.

### Diff on write, never snapshots {#diff-not-snapshot}

`PATCH` diffs old against new (`diffRecords`, capped at 50 changes) and appends the result to the append-only `editHistory` (`{ timestamp, by, changes[] }`). A routing change is diffed the same way. An edit that changed nothing is not recorded. `editHistory` and `replayHistory` are separate lists. The service never keeps a full copy of the record. History costs nothing for the majority of failures nobody edits. The price is that an intermediate record state cannot be rebuilt [3][26].

## Record-type coverage is two independent halves

Replaying a type needs an enum entry and a `getReplayTarget` case. Both destination topics are cross-entity, so it needs no new env var or publisher grant. Capturing a type needs the four touchpoints in G5. A confirmation type also needs a `CONFIRMATION_KEY_FIELDS` entry and its `recordType` on a `confirmation_made` subscription filter. Without them its failures never clear [5][7].

RGA's create side is deliberately not captured. Its confirmation side is, stored as `return_goods_confirmation` over the same canonical schema. That string is a storage and dispatch name only. On publish it becomes `return_goods_authorization` [3][17].

## Authentication and exposure

- **Admin API.** `ApiKeyGuard` is class-level on `FailuresController` and answers 401 on a missing or wrong key. The key is a Terraform `random_password` set as a plain Cloud Run env var [10][12].
- **Event routes have no authentication in the app.** No guard covers `/event/*`, and nothing verifies the Pub/Sub OIDC token. The guard's `/event` skip is dead code, since the guard sits only on the admin controller [10][16].
- **Cloud Run is public.** `ingress = INGRESS_TRAFFIC_ALL`, and `allUsers` holds `run.invoker` beside the push service account. A live read on 2026-10-13 showed `allUsers` on both `replay-dev` and `replay-prod`. An external load balancer with a managed certificate also fronts it [12][13][14][28].
- **Effect.** Anyone who reaches the URL can post to `/event/*`. A forged `confirmation-made` clears held failures given a `businessId` and record key. A forged failure adds a queue row. An operator's replay still passes the strict gate [1].
- **Swagger UI** at `/api` has no guard [15].

## Persistence

MongoDB database `replay-{env}`, one `failures` collection. Atlas runs a three-node replica set, M10 autoscaling to M20, with backups and point-in-time recovery [24].

`FailureRecord` holds `id` (UUID), `useCase`, `businessId`, `record`, `metadata`, `createdAt`, `replayHistory[]`, optional `editHistory`, `skuRedrives`, `resolvedSkus`, `routing`, `reason`, `stage`, `source`, `errors`, `upstream`, `connectorId`, `transaction`, and the dismissal, clear and assignment fields [3].

Boot creates these indexes. The `id` index is not unique [3]:

- `id`, `{ useCase, createdAt }`, `{ businessId, createdAt }` and `{ createdAt }`.
- `{ businessId, useCase, record.identifiers.<field> }` for `shipmentId`, `receiptId`, `businessRgaNumber`, `workOrderId`, `businessWorkOrderId` and `id`. These back the clear-down lookups.
- `{ businessId, useCase, record.export.object }` for the stock sync lookups.

Every read filters on `deletedAt`, except `resolved=true` and `/replays`. The `reason`, `search` and `resolved` filters scan the collection, which is acceptable at per-customer scale [9][3].

Boot fails when Mongo does not connect within 5 s [32].

`core/use-case/*` is dead inherited scaffolding from the collector and dedupe fork: a registry, three services and the `purchase_orders`, `sales_orders` and `master_data` collections. `EventModule` still provides it and it still ensures indexes at init. Replay writes only `failures` [19].

## Build, test and deploy

- pnpm 10.24.0, Vitest (`test:unit`, `test:integration`, `test:e2e`) and Biome lint. There is no `build:check:tests` script. `pnpm test` covers spec and fixture typing [20].
- The Dockerfile uses `node:24` and activates pnpm 11.11.0. CI (`code-quality.yaml`) runs on node 22. The root `mise.toml` pins node 24 and `code/mise.toml` says `latest` [21][22].
- `on-push.yaml` deploys on push to `main` or `master` with no path filter, so a docs-only push redeploys. Dev auto-applies. Prod applies behind the `terraform-prod` environment [23].
- `manual-deploy.yaml` deploys a branch to dev only.

## Runtime

Cloud Run service `replay-{env}` in `europe-west2`, with a Datadog `serverless-init` sidecar that dual-ships logs and metrics to the GFS and ILG accounts. Egress is Direct VPC with `PRIVATE_RANGES_ONLY`. `min_instance_count` is per environment: prod keeps one instance warm for the Retry Queue's synchronous calls, and dev scales to zero [12][25].

The startup probe polls `GET /health/liveness` every 10 s with a 1 s timeout and allows 6 failures, a 60 s window. Liveness returns 200 even when Mongo is down, with `PENDING` in the body. There is no readiness route [12][18].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "code/src/http/controllers/event.controller.ts@43380eb" },
  { "id": 2, "kind": "code", "ref": "code/src/http/controllers/failures.controller.ts@43380eb" },
  { "id": 3, "kind": "code", "ref": "code/src/core/failure/failure.service.ts@43380eb" },
  { "id": 4, "kind": "code", "ref": "code/src/core/failure/confirmation-redrive-routing.ts@43380eb" },
  { "id": 5, "kind": "code", "ref": "code/src/core/failure/derive-record-id.ts@43380eb" },
  { "id": 6, "kind": "code", "ref": "code/src/core/failure/derive-replayability.ts@43380eb" },
  { "id": 7, "kind": "code", "ref": "code/src/models/constants.ts@43380eb" },
  { "id": 8, "kind": "code", "ref": "code/src/adapters/pubsub/pubsub.service.ts@43380eb" },
  { "id": 9, "kind": "code", "ref": "code/src/repositories/collection.ts@43380eb" },
  { "id": 10, "kind": "code", "ref": "code/src/http/middleware/api-key.guard.ts@43380eb" },
  { "id": 11, "kind": "code", "ref": "iac/projects/replay/pubsub.tf@43380eb" },
  { "id": 12, "kind": "code", "ref": "iac/projects/replay/cloud-run.tf@43380eb" },
  { "id": 13, "kind": "code", "ref": "iac/projects/replay/iam.tf@43380eb" },
  { "id": 14, "kind": "code", "ref": "iac/projects/replay/load-balancer.tf@43380eb" },
  { "id": 15, "kind": "code", "ref": "code/src/bootstrap/main.ts@43380eb" },
  { "id": 16, "kind": "code", "ref": "code/src/bootstrap/containers/app.module.ts@43380eb" },
  { "id": 17, "kind": "code", "ref": "code/src/core/failure/confirmation-schema.ts@43380eb" },
  { "id": 18, "kind": "code", "ref": "code/src/http/controllers/health.controller.ts@43380eb" },
  { "id": 19, "kind": "code", "ref": "code/src/core/use-case/use-case-registry.service.ts@43380eb" },
  { "id": 20, "kind": "code", "ref": "code/package.json@43380eb" },
  { "id": 21, "kind": "code", "ref": "code/dockerfile@43380eb" },
  { "id": 22, "kind": "code", "ref": ".github/workflows/code-quality.yaml@43380eb" },
  { "id": 23, "kind": "code", "ref": ".github/workflows/on-push.yaml@43380eb" },
  { "id": 24, "kind": "code", "ref": "iac/projects/replay/mongo.tf@43380eb" },
  { "id": 25, "kind": "code", "ref": "iac/env/prod.tfvars@43380eb" },
  { "id": 26, "kind": "code", "ref": "code/src/core/failure/diff-record.ts@43380eb" },
  { "id": 27, "kind": "doc", "ref": "fuse://pubsub-topology", "note": "publishers and subscribers of the five topics; lists shopify-egress-service on stock_sync" },
  { "id": 28, "kind": "log", "ref": "gcloud run services get-iam-policy replay-{dev,prod}: roles/run.invoker members include allUsers (2026-10-13)" },
  { "id": 29, "kind": "pr", "ref": "gfs-bifrost/replay-service#109", "note": "hold and whole-run redrive of stock sync failures" },
  { "id": 30, "kind": "pr", "ref": "gfs-bifrost/replay-service#110", "note": "redrive one SKU of a held run" },
  { "id": 31, "kind": "code", "ref": "code/src/__test__/e2e/confirmation-failure.e2e-spec.ts@43380eb" },
  { "id": 32, "kind": "code", "ref": "code/src/adapters/mongo/mongo.connection.ts@43380eb" }
] }
```
