---
tags:
- waypoint
- fapi
verified: '2026-10-13'
verified_sha: ced057d
verified_paths:
- code/src
- iac
- portal
- code/package.json
- code/dockerfile
- mise.toml
- CLAUDE.md
- .github/workflows
- api-gateway-sandbox/dockerfile
title: fapi — architecture
thesis: 'One NestJS app on Cloud Run runs three flows: Basic-authenticated REST ingest
  to create_record_request, Pub/Sub-pushed confirmations forwarded to customer webhooks,
  and a RemoteConfig cache consumer.'
confidence: high
---
# fapi — architecture

```orient-bluf
{ "v": 1, "bluf": "One NestJS app on Cloud Run runs three flows: Basic-authenticated REST ingest to create_record_request, Pub/Sub-pushed confirmations forwarded to customer webhooks, and a RemoteConfig cache consumer.", "confidence": "high", "action": "Keep tenancy on every customer route, and route a confirmation only through the business's own REST connectors." }
```

## Guardrails

- [technical:G1] Every customer route carries tenancy. v2 uses `@Authenticated({ useCase })`, which bundles auth, `TenancyGuard` and `@EnforceTenancy`. v1 uses `@LegacyAuthenticated()` and calls `assertRecordsMatchBusiness` after the legacy-to-canonical mapping. Never wire a bare `RemoteConfigApiKeyGuard` onto a route that takes records.
  — paths: code/src/http/decorators, code/src/http/guards, code/src/utils/assert-records-match-business.ts, code/src/http/controllers/legacy.controller.ts
- [contract:G2] `confirmation_made` is one single-record `BifrostMessage` per record, never a bulk envelope. Consumers decode it with `ingestEvent`, and a bulk publish fails their Zod boundary and is acked away.
  — paths: code/src/services/pubsub-emitter.ts
- [technical:G3] Route a confirmation only through the business's own REST connectors, and validate connector webhook config at candidate selection. Never resolve a `connectorId` across businesses. Never reintroduce `confirmationsEnabled` as a gate.
  — paths: code/src/services/confirmation.service.ts, code/src/adapters/config/config-api.adapter.ts, code/src/services/connector-registry.service.ts
- [technical:G4] A `confirmation_made` or recorded failure that cannot be published rejects the push (500) so Pub/Sub redelivers it. Acking would lose the confirmation. `stock_adjustment` is the one best-effort exception.
  — paths: code/src/services/confirmation.service.ts, code/src/http/controllers/confirmation.controller.ts
- [technical:G5] Which exceptions get acked lives in two lists: `AllExceptionsFilter.catch()` and `isAckedException()`. A new "ack, do not retry" exception goes in both. Miss the filter and a poison message redelivers forever. Miss the predicate and the metric counts an acked call as a failure.
  — paths: code/src/http/filters/all-exceptions
- [contract:G6] A new record type needs both maps in `PubsubEmitter` (`topicMap` and `attributesMap` for create, `confirmationTopicMap` and `confirmationAttributesMap` for egress) and a `recordType`-filtered subscription in `pubsub.tf`. Cross-entity subscriptions never go unfiltered.
  — paths: code/src/services/pubsub-emitter.ts, iac/projects/api-gateway/pubsub.tf

## Where fapi sits

Three kinds of traffic reach the app. Customers POST records. Pub/Sub pushes confirmations and config revisions. [1][8][9]

```orient-flow
{ "v": 1, "title": "Inbound: what reaches fapi",
  "nodes": [
    { "id": "cust", "label": "Customer systems", "sub": "HTTP Basic", "kind": "external", "ev": [6, 11] },
    { "id": "p", "label": "snap-queue-polling-service", "kind": "service", "service": "snap-queue-polling-service", "ev": [45] },
    { "id": "cr", "label": "confirmation_ready", "sub": "7 subs, recordType + source/broadcast", "kind": "topic", "ev": [26] },
    { "id": "sar", "label": "stock_adjustment_ready", "sub": "unfiltered", "kind": "topic", "ev": [26] },
    { "id": "cs", "label": "config-service", "kind": "service", "service": "config-service", "ev": [9] },
    { "id": "cfg", "label": "config_revision", "kind": "topic", "ev": [26] },
    { "id": "f", "label": "fapi", "sub": "api-gateway", "kind": "service", "service": "fapi", "tone": "accent", "ev": [1] }
  ],
  "edges": [
    { "from": "cust", "to": "f", "label": "POST /api/v1, /api/v2" },
    { "from": "p", "to": "cr" },
    { "from": "p", "to": "sar" },
    { "from": "cr", "to": "f", "label": "push" },
    { "from": "sar", "to": "f", "label": "push" },
    { "from": "cs", "to": "cfg" },
    { "from": "cfg", "to": "f", "label": "push" }
  ] }
```

Outbound, fapi publishes to four topics, POSTs to customer webhooks and reads config. [18][19]

```orient-flow
{ "v": 1, "title": "Outbound: what fapi publishes and calls",
  "nodes": [
    { "id": "f", "label": "fapi", "kind": "service", "service": "fapi", "tone": "accent", "ev": [18] },
    { "id": "crr", "label": "create_record_request", "sub": "attributes.recordType", "kind": "topic", "ev": [18] },
    { "id": "d", "label": "dedupe-service", "kind": "service", "service": "dedupe-service", "ev": [45] },
    { "id": "h", "label": "Customer webhook", "sub": "POST, 30 s timeout", "kind": "external", "ev": [19, 37] },
    { "id": "m", "label": "confirmation_made", "sub": "attributes.recordType", "kind": "topic", "ev": [18] },
    { "id": "sam", "label": "stock_adjustment_made", "kind": "topic", "ev": [18] },
    { "id": "fl", "label": "confirmation_data_failure", "kind": "topic", "ev": [18] },
    { "id": "r", "label": "Redis", "sub": "config cache, rate limit", "kind": "store", "ev": [44] },
    { "id": "cs", "label": "config-service", "kind": "service", "service": "config-service", "ev": [24] }
  ],
  "edges": [
    { "from": "f", "to": "crr", "label": "ingest" },
    { "from": "crr", "to": "d" },
    { "from": "f", "to": "h", "label": "forward" },
    { "from": "f", "to": "m" },
    { "from": "f", "to": "sam" },
    { "from": "f", "to": "fl" },
    { "from": "f", "to": "r" },
    { "from": "f", "to": "cs", "label": "GET on cache miss", "style": "dashed" }
  ] }
```

Topics belong to bifrost-pubsub. This stack reads their ids from remote state and owns the subscriptions and publisher grants [26][28].

## Stack

NestJS 11 on Express 5, Zod 4 through `nestjs-zod`, Biome for lint (not ESLint or Prettier), Vitest for tests, Node 24 [3][5]. `code/` is the service root.
`pnpm run build:check`, `pnpm test` and `pnpm run lint:fix` all run from there. The layout is `http/`, `services/`, `adapters/config`, `config/`, `cache/`, `models/`, `observability/events/`, `bootstrap/` (OpenAPI enrichment) and `utils/`.

`tsconfig.json` type-checks everything including specs, and `build:check` runs it. `tsconfig.build.json` also excludes `*.integration.ts`, and the Docker image uses it [4].
There is no `build:check:tests` script, because `build:check` already covers spec and fixture files.

**ASSESSED** `mise.toml` pins `pnpm = latest` (10.x), while `package.json` and both Dockerfiles pin `pnpm@9.0.0`. No incident, inferred from reading the pins only [3][5][36].
`code/dockerfile` runs plain `pnpm install` with a TODO to restore `--frozen-lockfile`, so the image build does not use the lockfile as locked. CI uses `--frozen-lockfile` [5][40].

`main.ts` raises the body limit to 50 MB for JSON, urlencoded and `text/csv`, and applies `ZodValidationPipe` globally. `uncaughtException` and `unhandledRejection` log and exit 1, so Cloud Run recycles the instance [2].
The Redoc page at `/api` and `/api-json` serve the enriched OpenAPI document without auth [2][43].

## Endpoint map

| Route | Controller | Notes |
| --- | --- | --- |
| `POST /api/v2/{master-data,sales-orders,purchase-orders,return-goods,work-orders}` | `api.controller` | canonical in, validate, emit; 202 |
| `POST /api/v1/{sales-orders,purchase-orders,master-data}` | `legacy.controller` | ILG goodsOut/goodsIn/masterData JSON **or** `text/csv`, mapped to canonical; 202 |
| `POST /api/v1/{return-goods,work-orders}` | `legacy.controller` | **501**, sandbox and docs parity only |
| `GET /api/v1/customer/:accountId/stock` | `legacy.controller` | **501** |
| `GET /api/v1/stock`, `GET /api/v2/stock` | `legacy.controller`, `api.controller` | **501**, contract documented, awaiting the wms-gateway proxy; `@RateLimited()` |
| `POST /events/v1/confirmation/ready/:recordType` | `confirmation.controller` | egress, Pub/Sub push |
| `POST /events/v1/config/revision` | `config-event.controller` | RemoteConfig refresh, Pub/Sub push; 202 |
| `GET /health/liveness` | `health.controller` | no auth; reports uptime and Redis status |

There is no `/health/readiness` route, although `README.md` and `CLAUDE.md` list one. The Cloud Run startup probe uses `/health/liveness` [6][7][8][9][10][27].
The wms-gateway docs name fapi as the intended caller of its stock read. No fapi code calls wms-gateway at this commit [6][7].

## Auth: two separate schemes

**Customer routes (v1 and v2): HTTP Basic against RemoteConfig.** `RemoteConfigApiKeyGuard` decodes `Authorization: Basic`.
Username is the businessId. Password is the `apiKey` of one of that business's REST connectors, resolved through the `CONNECTOR` fragment.
On a match it stores `authenticatedBusinessId` and `authenticatedConnectorId` for handlers. Every failure is a bare 401 with a logged reason [11].
The `API_KEY` env var is required by the env schema and read by no guard. Terraform generates it with `random_password` [25][27].

**Push routes (`/events/*`): `PubSubAuthGuard`** checks only that an `Authorization: Bearer` header is present. It bypasses even that under `USE_SERVICE_MOCKS=true` [12].
Its comment says Cloud Run verifies the OIDC token first. In this stack Cloud Run does not:
`cloud-run.tf` grants `roles/run.invoker` to `allUsers`, sets no ingress restriction, and the push endpoints use the public service URL [26][27][28].
**ASSESSED** Any caller who can reach the service and sends `Authorization: Bearer x` can post a forged confirmation or config revision. A forged confirmation would make fapi POST attacker-chosen records to a customer webhook and publish `confirmation_made`.
That inference rests on the repo's IaC alone. An org policy or network control outside this repo could narrow it.

## Tenancy

v2 uses `@Authenticated({ useCase })`. `TenancyGuard` reads the body array and calls `assertRecordsMatchBusiness` against the authenticated business before the handler runs [13][14].
v1 bodies are legacy or CSV shaped, so the handler calls `assertRecordsMatchBusiness` after the mapping [7][15].
The check skips a record with no `businessId` and leaves it to the canonical schema, which requires the field. **ASSESSED** from the schemas in `@gfs-bifrost/types`, not re-read at the pinned version.

## Per-customer rate limit

`@RateLimited()` applies `RateLimitInterceptor`. It is an interceptor, not a guard, so it runs after auth has set the businessId. It sits on the two `GET` stock routes only, and one bucket per business serves both [16].
Over the limit is 429 (`RATE_LIMIT_MAX_REQUESTS` and `RATE_LIMIT_WINDOW_MS`, default 30 per 60 s). A cache failure lets the request through [25].
The window is the time-bucketed key name `rate-limit:{businessId}:{windowIndex}`, not the TTL, because `@gfs-bifrost/cache` has no atomic increment.
The interceptor evicts the per-instance LRU entry after each read, or the count goes stale. The limit is best effort across instances.

## Ingress pipeline

`BulkIngestService.handleBulkRequest(entityType, records, connectorId)` runs `validateRecords` and then `processRecords` [17].
`validateRecords` safe-parses each record against its canonical schema and collects every failure into one 400. `processRecords` emits each record through `PubsubEmitter`.

Metadata is built per record [17]:

- `customer` comes from `extractBusinessId`, whose path differs per type.
- `correlationId` comes from the `Correlation` scope. `timestamp` is unix seconds.
- `source` is `"rest"`, the origin channel and not the emitting service.
- `connectorId` is the authenticated REST connector.
- `recordType` and `recordId` come from the type and `extractRecordReference`. `recordId` is the customer's own reference.
- `capture` is `{ type: "api" }`, the fieldless `ApiCapture` marker.

All five types publish only to `create_record_request`, with `attributes.recordType` set to `master_data`, `sales_order`, `purchase_order`, `return_goods_authorization` or `work_order` [18].
`PubsubEmitter`'s two maps are where a new type is wired in.
`EntityType` and its alias `UseCase` keep the pre-cutover names inside the service. The wire uses `recordType`. Do not add new `useCase` identifiers or mass-rename the old ones.

## Egress and confirmation pipeline

`:recordType` is one of eight: `purchase_order`, `sales_order`, `stock_adjustment`, `return_goods_authorization`, `pick_confirmation`, `pack_confirmation`, `work_order_confirmation`, `finished_good_receipt`.
They live in one place, `CONFIRMATION_RECORD_REGISTRY` in `@gfs-bifrost/types`. fapi's `ConfirmationType` is an alias onto it [8].

```orient-flow
{ "v": 1, "title": "Confirmation push outcomes",
  "nodes": [
    { "id": "in", "label": "Push arrives", "sub": "ready/:recordType", "kind": "step", "ev": [8] },
    { "id": "dec", "label": "Decode and validate", "sub": "ingestBulkEvent", "kind": "step", "ev": [8] },
    { "id": "res", "label": "Resolve REST connectors", "sub": "business only", "kind": "step", "ev": [19, 23] },
    { "id": "cand", "label": "Select candidates", "sub": "active, webhook, valid config", "kind": "step", "ev": [19] },
    { "id": "post", "label": "POST each target", "sub": "3 tries, 1 s then 2 s", "kind": "step", "ev": [19] },
    { "id": "made", "label": "Publish confirmation_made", "sub": "once, if any delivered", "kind": "topic", "ev": [19] },
    { "id": "ack", "label": "204 ack", "kind": "step", "tone": "accent", "ev": [8] },
    { "id": "rec", "label": "Record failure", "sub": "confirmation_data_failure", "kind": "topic", "ev": [19] },
    { "id": "rej", "label": "500 reject", "sub": "Pub/Sub redelivers", "kind": "step", "tone": "alert", "ev": [8, 19] }
  ],
  "edges": [
    { "from": "in", "to": "dec" },
    { "from": "dec", "to": "ack", "label": "invalid: dropped", "style": "dashed" },
    { "from": "dec", "to": "res" },
    { "from": "res", "to": "cand" },
    { "from": "cand", "to": "post" },
    { "from": "cand", "to": "rec", "label": "no target, bad leg" },
    { "from": "post", "to": "made" },
    { "from": "post", "to": "rec", "label": "retries exhausted" },
    { "from": "made", "to": "ack" },
    { "from": "made", "to": "rej", "label": "publish fails" },
    { "from": "rec", "to": "rej", "label": "publish fails" }
  ] }
```

1. **Decode.** `PubSubIngestor.ingestBulkEvent` validates the envelope against `getConfirmationSchema(type)`. `parseEnvelope` reads `attributes.broadcast`. The config consumer uses the same ingestor's `ingestEvent` [8][9].
   A `PubSubValidationError` or `PubSubDecodeError` is acked with 204: the message can never become valid, so a 204 is not proof of delivery. Only the `Received ... confirmation payload` log line is.
2. **Resolve.** The businessId comes from the first record via `getConfirmationBusinessId`. RGA adds a presence check, because its line-level businessId is optional.
   `ConnectorRegistryService` loads only that business's REST connectors through `resolveWithUnresolved(businessId, REST)`, and sets `maxRetries` to the constant 3 [19][20][23].
3. **Candidates.** A candidate is `isActive === ACTIVE`, has a `webhookUrl`, and has a deliverable config: a valid URI and a `webhookSecretKey`. `stock_adjustment` also needs `stockAdjustmentsEnabled === true`.
   A bad config is logged as `errors.connector_configuration` and dropped here, before any POST [19].
4. **Targets.** A `metadata.connectorId` targets that one candidate. Broadcast (`attributes.broadcast === "true"`) or no `connectorId` targets every candidate [19].
5. **Deliver.** POST the confirmation array with `x-webhook-secret-key` and `x-correlation-id`. The shared axios instance adds `User-Agent: Bifrost-API-Gateway/1.0` and a 30 s timeout [37].
   Retry up to 3 times with `2^(n-1) * 1000` ms backoff. One dead webhook takes about 93 s. Targets are isolated: a failing one does not stop the others.
6. **Made.** Publish `confirmation_made` once per push, after every target has been tried, and only if one delivered. It is one message per record [18][19].
   `stock_adjustment` is the exception: one best-effort made per delivering connector on `stock_adjustment_made`, with no attribute.
7. **Ack or reject.** A failed delivery is recorded and the push is acked. A made or a recorded failure that cannot be published rejects the push, and the redelivery re-POSTs every webhook. Duplicates beat loss [19].

PO and SO stamp the confirmation names `goods_in_confirmation` and `goods_out_confirmation` on `attributes.recordType` and `metadata.recordType`. The other types use their own names. `stock_adjustment` publishes with no attribute [18].
There are no per-entity PO or SO `*_made` topics. Every confirmation type publishes terminal failures to `confirmation_data_failure`, distinct from the ingress-side `create_data_failure` [18][19].

A **routed** message names a `connectorId` and is not a broadcast. Every non-stock routed message is recorded when it cannot be delivered. A **fan-out** is anything else. A fan-out records every REST connector with a webhook that should have taken it and did not.
A REST connector carries no use-case keys, so having a `webhookUrl` is what "takes the type" means. One without a webhook records nothing. Each leg names its connector on the failure body and on `metadata.connectorId`, so a replay redrive reaches that connector alone [19].

| Situation | Failure recorded | Retryable |
| --- | --- | --- |
| Routed, named connector is not a candidate | `business_rule` / `connector_unresolvable` | no |
| Routed, no candidate at all | `business_rule` / the unroutable reason | no |
| Connector list unreadable (`ConfigApiException`) | `dependency` / `fapi.connector_lookup_failed`, no `connectorId` on a fan-out | yes |
| Connector remote-config could not fetch or validate | `dependency` / `fapi.connector_unresolved` | yes |
| Fan-out, connector inactive | `business_rule` / `connector_inactive` | no |
| Fan-out, webhook config invalid | `business_rule` / `misconfigured` | no |
| Webhook retries exhausted | `dependency` / `fapi.confirmation_webhook_delivery_failed` | no |
| Delivery attempt 10 and a server fault | `infrastructure` / `fapi.redelivery_exhausted`; names a connector only when routed | yes |

Fan-out tries every connector and publishes `confirmation_made` before it records leg failures. It rejects the push on the first leg failure it cannot publish. `stock_adjustment` never rejects: it records nothing for a missing candidate, and its made and failures are best effort [19].
When no candidate exists, the event is metered `unroutable` with a tier: `no_connectors`, `no_active_connectors`, `use_case_inactive` (stock adjustments disabled), `no_confirmation_mappings` (no webhook) or `misconfigured` (every webhook config failed validation) [19].

**Retry budget.** The seven `confirmation_ready` subscriptions back off 10 s to 600 s. They carry a `dead_letter_policy` (max 10 attempts) only so Pub/Sub stamps `deliveryAttempt` on the push body [26].
At attempt 10 the controller turns any server fault into a retryable `fapi.redelivery_exhausted` failure and acks. If that failure cannot be published, the push keeps rejecting [8].
`ack_deadline_seconds` is 300, Cloud Run's request timeout. **ASSESSED** The DLT receives nothing because it has no publisher grant. The grant would live in bifrost-pubsub, outside this repo, and a comment in `pubsub.tf` states the intent [26].

**Intake.** Each of the seven delivery subscriptions filters on `recordType` and `(attributes.source = "rest" OR attributes.broadcast = "true")`, so fapi sees only confirmations the poller routed to a REST connector, plus broadcasts [26].
PO accepts both `purchase_order` and `goods_in_confirmation`. `stock_adjustment_ready` is unfiltered, with a 60 s ack deadline, no retry policy and no DLT [26].

Two exception paths ack as well. `ConfigApiException` and `BusinessIdExtractionException` return 204, and `ConnectorConfigurationException` is a safety net that nothing throws [21][22].
The exception filter writes RFC 9457 `application/problem+json` for HTTP errors. An unknown error on a push route is a 500 and redelivers [21].

## Config consumer

`/events/v1/config/revision` is a push route behind `PubSubAuthGuard`, with a 20 s ack deadline and no filter. It validates the envelope with `ConfigPayloadSchema` and branches on shape [9][26].

- **`resources`** (backlinks): only `CONNECTOR` backlinks are passed to the connector handler.
- **`fragments`** (revisions): the whole payload goes to the remote-config dispatcher.
  `ConfigApiAdapter` defines a `SAVABLE_FRAGMENTS` set of `CONNECTOR_MAPPING`, `WAREHOUSE_ROUTING`, `DDP_RULES` and `SKU_BLACKLIST`, but no production code applies it on this path [23].
  **ASSESSED** The dispatcher caches every fragment type it has a handler for. The claim rests on a local pkg-node checkout, not the pinned `remote-config` 2.3.0 [46].

`RemoteConfigProviderService` builds the standard Fuse RemoteConfig consumer in full cache mode (Redis plus in-memory LRU). Init has a 10 s timeout, and on failure the handlers fall back to the config-service API per request [24].
Redis and the cache init are bounded the same way, degrading to LRU only. Read `fuse://config-domain` before changing this wiring [44].

## Observability

Logs and metrics only, through `@gfs-bifrost/observability` (the `fuse.*` catalogue and the `Correlation` facade) over `@ilg-platform/observability` and `observability-nest`. There is no tracing [1][35].
`app.module.ts` bootstraps it once with `FuseObservabilityModuleBuilder`. It is env-driven with no options bag. The `service` tag is `rest_connector` and the `channel` tag is `rest` [1][25].
Call sites inject `FuseEventLogger` and emit catalogued events. Shared ones come from `@gfs-bifrost/observability`. fapi's own are in `src/observability/events/`: auth, confirmation dispatch and audit, ingest batch.
`cache/cache.service.ts` is the one holdout that injects the raw SDK logger [44].

`errors.http` and `request.failure` count 5xx only. A 4xx, mostly scanner noise in prod, goes to `REQUEST_METRIC.REJECTED` at debug and counts as `request.success`. A rejected ingest batch shows as the `Record batch rejected` warn [21][47].

`@ilg-platform/*` packages come from GitHub Packages in another org, so the built-in `GITHUB_TOKEN` cannot read them. CI and deploy authenticate with the `GH_TOKEN` PAT secret through `.npmrc` and a Dockerfile build arg [5][31].
**ASSESSED** From `CLAUDE.md`: a 403 on install means one `@ilg-platform/*` package has not granted read to the PAT's identity. This is not checkable in the repo.

## Deployment

Three independently deployed Cloud Run services come from this repo.

- **`api-gateway`**, the real service. `deploy.yml` runs on push to main or master: dev applies automatically, and prod plans then applies behind the `terraform-prod` approval. `manual-deploy.yaml` is the dev-only on-demand path. Terraform lives in `iac/projects/api-gateway` with tfvars in `iac/env/`.
  Reusable workflows come from `ilg-platform/github-actions@0.1-affogato` [31].
  The app container sets no scaling or resource limits, so Cloud Run defaults apply. A Datadog serverless-init sidecar dual-ships logs and metrics to both accounts. Redis is a `BASIC` Memorystore instance, reached over Direct VPC egress [27][48].
- **`api-gateway-sandbox`**, a Stoplight Prism mock of fapi's own OpenAPI export. Its Dockerfile runs `pnpm run export:openapi` with dummy env vars, then serves `openapi.yaml`. No fapi code runs in the image.
  It deploys to **dev only** on push to main or master. `prod.tfvars` has no sandbox domain [29][30][32][38][39].
- **`developer-portal`** (`portal/`), a public Next.js app that renders the same OpenAPI export as customer documentation. It deploys to **prod** from `deploy-developer-portal.yaml` on pushes touching `portal/**` or `code/src/**`, behind `terraform-prod`.
  It runs 1 to 4 instances and never scales to zero. `manual-deploy.yaml` previews a branch on dev with `-f deploy_portal=true` [33][34].
  Its try-it console targets the sandbox URL listed in the OpenAPI servers, which is the dev-hosted sandbox [43].

**UNKNOWN** Whether the prod portal is serving customers. Only the prod Terraform and workflow are confirmed.
Its Cloud Run service grants `allUsers` the invoker role and carries no auth in the IaC [34].

DNS records live in the ilg-platform zone (`ilg_core_infra` remote state), not the Bifrost one [26].

Required env, from the schema, with no default: `SERVICE_NAME`, `CREATE_RECORD_REQUEST_TOPIC`, `STOCK_ADJUSTMENT_MADE_TOPIC`, `CONFIRMATION_MADE_TOPIC`, `CONFIRMATION_DATA_FAILURE_TOPIC`, `API_KEY` (unused), `CONFIG_SERVICE_URL`, `CONFIG_SERVICE_API_KEY` and `REDIS_HOST`.
`MEM_CACHE_CAPACITY` defaults to 500, and the rate-limit variables default as above [25].

## Testing

- `code-quality.yaml` runs a `test` (vitest), `lint` (biome) and `build` (`build:check`) matrix, plus portal `typecheck` and `lint`. It runs on PR, on a nightly cron and on manual dispatch [40].
- `blackbox-testing.yaml` brings up `docker-compose-4pipeline.yaml` with a Pub/Sub emulator, waits on `/health/liveness`, then runs the `blackbox` profile. It runs nightly, on PRs to master and on manual dispatch [41].
- `secops.yaml` runs a secret scan, a dependency audit and a container scan (audit-ci and Trivy) for both images [42].
- Vitest also picks up `*.integration.ts`, which holds the OpenAPI example checks. The build excludes them [4].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "code/src/app.module.ts@ced057d" },
  { "id": 2, "kind": "code", "ref": "code/src/main.ts@ced057d" },
  { "id": 3, "kind": "code", "ref": "code/package.json@ced057d" },
  { "id": 4, "kind": "code", "ref": "code/tsconfig.build.json@ced057d" },
  { "id": 5, "kind": "code", "ref": "code/dockerfile@ced057d" },
  { "id": 6, "kind": "code", "ref": "code/src/http/controllers/api.controller.ts@ced057d" },
  { "id": 7, "kind": "code", "ref": "code/src/http/controllers/legacy.controller.ts@ced057d" },
  { "id": 8, "kind": "code", "ref": "code/src/http/controllers/confirmation.controller.ts@ced057d" },
  { "id": 9, "kind": "code", "ref": "code/src/http/controllers/config-event.controller.ts@ced057d" },
  { "id": 10, "kind": "code", "ref": "code/src/http/controllers/health.controller.ts@ced057d" },
  { "id": 11, "kind": "code", "ref": "code/src/http/guards/remote-config-guard.ts@ced057d" },
  { "id": 12, "kind": "code", "ref": "code/src/http/guards/pubsub-auth.guard.ts@ced057d" },
  { "id": 13, "kind": "code", "ref": "code/src/http/decorators/authenticated.decorator.ts@ced057d" },
  { "id": 14, "kind": "code", "ref": "code/src/http/guards/tenancy.guard.ts@ced057d" },
  { "id": 15, "kind": "code", "ref": "code/src/utils/assert-records-match-business.ts@ced057d" },
  { "id": 16, "kind": "code", "ref": "code/src/http/interceptors/rate-limit.interceptor.ts@ced057d" },
  { "id": 17, "kind": "code", "ref": "code/src/services/bulk-ingest.service.ts@ced057d" },
  { "id": 18, "kind": "code", "ref": "code/src/services/pubsub-emitter.ts@ced057d" },
  { "id": 19, "kind": "code", "ref": "code/src/services/confirmation.service.ts@ced057d" },
  { "id": 20, "kind": "code", "ref": "code/src/services/connector-registry.service.ts@ced057d" },
  { "id": 21, "kind": "code", "ref": "code/src/http/filters/all-exceptions/all-exceptions.filter.ts@ced057d" },
  { "id": 22, "kind": "code", "ref": "code/src/http/filters/all-exceptions/is-acked-exception.ts@ced057d" },
  { "id": 23, "kind": "code", "ref": "code/src/adapters/config/config-api.adapter.ts@ced057d" },
  { "id": 24, "kind": "code", "ref": "code/src/config/remote-config-provider.service.ts@ced057d" },
  { "id": 25, "kind": "code", "ref": "code/src/config/config.service.ts@ced057d" },
  { "id": 26, "kind": "code", "ref": "iac/projects/api-gateway/pubsub.tf@ced057d" },
  { "id": 27, "kind": "code", "ref": "iac/projects/api-gateway/cloud-run.tf@ced057d" },
  { "id": 28, "kind": "code", "ref": "iac/projects/api-gateway/iam.tf@ced057d" },
  { "id": 29, "kind": "code", "ref": "iac/projects/api-gateway-sandbox/cloud-run.tf@ced057d" },
  { "id": 30, "kind": "code", "ref": "api-gateway-sandbox/dockerfile@ced057d" },
  { "id": 31, "kind": "code", "ref": ".github/workflows/deploy.yml@ced057d" },
  { "id": 32, "kind": "code", "ref": ".github/workflows/deploy-api-gateway-sandbox.yaml@ced057d" },
  { "id": 33, "kind": "code", "ref": ".github/workflows/deploy-developer-portal.yaml@ced057d" },
  { "id": 34, "kind": "code", "ref": "iac/projects/developer-portal/cloud-run.tf@ced057d" },
  { "id": 35, "kind": "code", "ref": "CLAUDE.md@ced057d" },
  { "id": 36, "kind": "code", "ref": "mise.toml@ced057d" },
  { "id": 37, "kind": "code", "ref": "code/src/services/axios-instance.factory.ts@ced057d" },
  { "id": 38, "kind": "code", "ref": "iac/env/dev.tfvars@ced057d" },
  { "id": 39, "kind": "code", "ref": "iac/env/prod.tfvars@ced057d" },
  { "id": 40, "kind": "code", "ref": ".github/workflows/code-quality.yaml@ced057d" },
  { "id": 41, "kind": "code", "ref": ".github/workflows/blackbox-testing.yaml@ced057d" },
  { "id": 42, "kind": "code", "ref": ".github/workflows/secops.yaml@ced057d" },
  { "id": 43, "kind": "code", "ref": "code/src/bootstrap/openapi.ts@ced057d" },
  { "id": 44, "kind": "code", "ref": "code/src/cache/cache.service.ts@ced057d" },
  { "id": 45, "kind": "doc", "ref": "fuse://pubsub-topology", "note": "publishers and subscribers of confirmation_ready and create_record_request" },
  { "id": 46, "kind": "doc", "ref": "pkg-node pkg/remote-config/src/dispatcher/config-event.dispatcher.ts", "note": "read from a local checkout, not a pinned ref" },
  { "id": 47, "kind": "code", "ref": "code/src/http/interceptors/logging.interceptor.ts@ced057d" },
  { "id": 48, "kind": "code", "ref": "iac/projects/api-gateway/redis.tf@ced057d" }
] }
```
