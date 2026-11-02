---
tags:
- waypoint
- config-service
verified: '2026-10-14'
verified_sha: de3e3c0
verified_paths:
- code/package.json
title: config-service — architecture
thesis: A NestJS REST API over MongoDB behind a hand-rolled Express API-key layer;
  every write publishes a best-effort config_revision event, and the one push route
  it exposes is never authenticated by the app.
confidence: high
---
# config-service — architecture

```orient-bluf
{ "v": 1, "bluf": "A NestJS REST API over MongoDB behind a hand-rolled Express API-key layer; every write publishes a best-effort config_revision event, and the one push route it exposes is never authenticated by the app.", "confidence": "high", "action": "Treat POST /events/customer-creation as open to the internet: Cloud Run grants allUsers invoker and the app ignores the Pub/Sub token, so any caller can rewrite an SFTP connector's auth." }
```

## Guardrails

- [contract:G1] The `config_revision` publish is best-effort and never fails the HTTP write; Mongo is the source of truth. A delete publishes `version: -1` as the removal sentinel, and no other path may reuse `-1`.
  — paths: code/src/core/pubsub/config.dispatcher.ts, code/src/http/api/v1
- [technical:G2] A new field on a connector `config` goes in both the `@gfs-bifrost/types` stored type and this service's ingress and response Zod schemas. Zod strips unknown keys, so a one-sided field never reaches `remote-config`.
  — paths: code/src/http/api/v1/storefronts/schemas, code/src/core/schemas.ts
- [technical:G3] A new thrown exception type needs an arm in `DomainExceptionFilter`, which every `v1` controller attaches with `@UseFilters`, and in `errorMiddleware`. Otherwise it answers a generic 500.
  — paths: code/src/exceptions/http, code/src/http/api/v1
- [technical:G4] Rules that depend on stored state run in `StorefrontService` after the PATCH merges into the stored connector. The OpenAPI DTOs drop container-level Zod refinements, so those never run in the request pipe. `toOpenApiSchema` also rebuilds every object as `.passthrough()`, so a `z.strictObject` from types neither rejects nor strips unknown keys at the API. A route that must refuse unknown keys re-parses the body in its service, as `FeatureFlagsService` does.
  — paths: code/src/core/storefront/storefront.service.ts, code/src/shared/openapi-schema.utilities.ts
- [contract:G5] Any route outside `/api/v1`, and any entry in the auth `ignoredRoutes`, needs its own authentication. The Cloud Run service is public, so the API-key middleware is the only gate.
  — paths: code/src/bootstrap/factory.ts, iac/projects/config-service/iam.tf
- [technical:G7] A repository method's name or comment states which rows it sees (live, or live and soft-deleted) and how it writes (insert, non-upserting update, upsert, soft or hard delete). Keep it true when changing the Mongo implementation; the Cloud SQL implementation copies it, and a contract parity test will run both.
  — paths: code/src/repositories
- [contract:G6] Connector mappings stay keyed by `:useCase` and the legacy `UseCase` type. This service is the known holdout from the `recordType` rename; do not rename it outside a PR scoped to that cutover.
  — paths: code/src/http/api/v1/storefronts/connector-mappings.controller.ts

## Runtime shape: NestJS with a bolted-on Express instance

```orient-flow
{ "v": 1, "title": "Request path and the push route",
  "nodes": [
    { "id": "cl", "label": "Callers", "sub": "fuse-ui, MCP, services", "kind": "external" },
    { "id": "auth", "label": "API-key middleware", "sub": "x-api-key, Express", "kind": "step", "ev": [3, 4] },
    { "id": "ctl", "label": "Nest controllers", "sub": "12 under /api/v1", "kind": "step", "ev": [1, 12] },
    { "id": "svc", "label": "Core services", "sub": "code/src/core", "kind": "step", "ev": [5] },
    { "id": "mongo", "label": "MongoDB", "kind": "store", "ev": [6] },
    { "id": "rev", "label": "config_revision", "kind": "topic", "ev": [7] },
    { "id": "cc", "label": "customer_creation", "sub": "OIDC push", "kind": "topic", "ev": [8] },
    { "id": "ev", "label": "/events/customer-creation", "sub": "no app auth", "kind": "step", "service": "config-service", "tone": "alert", "ev": [4, 9] }
  ],
  "edges": [
    { "from": "cl", "to": "auth" },
    { "from": "auth", "to": "ctl", "label": "key matches" },
    { "from": "ctl", "to": "svc" },
    { "from": "svc", "to": "mongo" },
    { "from": "ctl", "to": "rev", "label": "after write" },
    { "from": "cc", "to": "ev", "label": "push" },
    { "from": "ev", "to": "mongo", "label": "connector auth, user" }
  ] }
```

`main.ts` boots a Nest app on `RootModule`, then reaches into the underlying Express instance and runs `buildApp` on it [1][2].

- **Nest** owns controllers, DI (`bootstrap/containers/*.module.ts`) and Swagger. `main.ts` builds the OpenAPI document with `SwaggerModule`, runs `attachErrorResponses` over it so every 4xx and 5xx carries the problem+json envelope, and serves it at `/api/v1/docs` with JSON at `/api/v1/docs-json` [1].
- **The Express layer** (`bootstrap/app.ts`) adds `requestId` and logger middleware, `body-parser` with a 10 MB JSON limit, the API-key middleware and `errorMiddleware` [2].
- `setGlobalPrefix("api", { exclude: ["health", "events/(.*)"] })` makes every `v1/...` controller path `/api/v1/...`. `/health` and `/events/*` stay unprefixed [1].
- **ASSESSED** `buildApp` runs before `listen()`, and Nest registers its routes during `listen()`. So the Express middleware sits ahead of every Nest route, and `errorMiddleware` only sees errors raised by earlier middleware such as body parsing. Nothing in the repo tests that order.

## Authentication

**CONFIRMED** The API key is the only gate. When `AUTH_ENABLED` and `AUTH_API_KEY` are both set, a request needs a matching `x-api-key` header. Otherwise the middleware is a no-op [3][4]. `global.tfvars` sets `api_auth_enabled = true` and the key comes from Secret Manager, so the key is enforced in dev and prod [10][11]. The comparison is a plain string equality.

Four routes are open regardless, matched by exact path and method (`auth.middleware.ts` compares `r.path === req.path`) [3][4]:

- `GET /health`
- `GET /api/v1/docs`
- `GET /api/v1/docs-json`
- `POST /events/customer-creation`

Swagger UI's asset files under `/api/v1/docs/` are open for a different reason. `SwaggerModule.setup` registers them in `main.ts` before `buildApp` adds the auth middleware [1][2]. Any other path under `/api/v1/docs/` returns 401.

**Cloud Run is public.** `cloud-run.tf` sets `ingress = "INGRESS_TRAFFIC_ALL"`, and `iam.tf` binds `roles/run.invoker` to `allUsers` [9][13]. A global HTTPS load balancer with a managed certificate fronts the same service [14]. **ASSESSED** An org-level policy outside this repo could still narrow ingress or the binding; nothing in the repo shows one.

**The event route is unauthenticated.** `pubsub.tf` configures the push subscription with an OIDC token for the `pubsub_handler_invoker` service account, and `iam.tf` grants that account `run.invoker` [8][13]. The app never verifies the token, and `allUsers` already holds the role, so Cloud Run admits any caller too [4][9]. **ASSESSED** Any caller holding a valid `storefrontId` and `connectorId` pair can POST a well-formed envelope and set that SFTP connector's `config.auth` (including `publicKey`), `config.user` and `config.isActive`. The ids are identifiers, not secrets, but whether an outsider can learn a pair is not established here. Whether sftp-connector then honours a swapped key is also not established.

**ASSESSED** `iam.tf` also declares the invoker role twice: an authoritative `iam_binding` for `allUsers` and an `iam_member` for the push service account. Terraform treats the binding as the full member list for that role, so the two likely fight on each apply. The push still succeeds because `allUsers` holds the role.

## Error mapping

Two emitters exist and a new exception type needs an arm in both [12][15][16]:

- **`DomainExceptionFilter`** (`exceptions/http/domain-exception.filter.ts`) is a `@Catch()` filter that emits RFC-7807 `application/problem+json`. It is not global: each of the 12 `v1` controllers attaches it with `@UseFilters` [12]. Arms: `ValidationException`→400, `InvalidMappingConfigException`→400 (per-field `issues`), `ConflictException`→409, `EntityNotFoundException`→404, `TooManyRequestsException`→429 (+`Retry-After`), `RepositoryException`→500, `NotImplementedException`→501. Anything else is a generic 500.
- **`errorMiddleware`** (`exceptions/http/middleware.ts`) is mounted by `buildApp` and mirrors those arms. It also maps `PubsubEventDecodeException` to a 204 [15].

The only global Nest filter is `PubsubEventDecodeExceptionFilter`, registered as `APP_FILTER` in `AppModule`. It turns a bad envelope or payload shape into a 204 ack, a deliberate poison-message drop with no retry and no dead-letter topic [16][9]. The generated OpenAPI document declares `ProblemDetailsDto` on every 4xx and 5xx, and `ValidationProblemDetailsDto` with optional `issues` on 400.

**ASSESSED** `EventsController` carries no `DomainExceptionFilter`, so `SftpAuthStatusException.ConnectorNotFound` is not a decode error. It likely answers 500, and Pub/Sub redelivers. The subscription sets no `retry_policy` and no dead-letter topic, so Pub/Sub defaults apply and an event for an unknown connector would redeliver until retention expires [8][17].

## HTTP surface

**CONFIRMED** 52 routes under `/api/v1` across 12 controllers, plus `GET /health` and one push route [18]. The resources are business, storefront, connector, backend, DDP rules, warehouse routing, SKU blacklist, shipment methods and feature flags. [[interfaces]] holds the full table.

`/health` returns 200 with the Mongo status and throws a 502 when Mongo is in `ERROR`. The Cloud Run startup probe hits it [19][20].

## Connector validation runs on the merged document

Connector-level rules that depend on stored state are enforced in `StorefrontService` after the PATCH body is merged into the stored connector, not in the Zod request schema [5]:

- an `edi` SFTP connector must end up with a complete `ediEnvelope`
- Shopify `stockSync.enabled` needs a schedule
- an SFTP connector cannot be set `active` before its SFTP user is provisioned
- mapping dictionary name and key uniqueness, checked in `validateMappingConfig`

A partial update that flips only `enabled`, or sends half an envelope, is judged against what is stored. The OpenAPI DTO conversion drops container-level Zod refinements, which is why dictionary uniqueness is checked in `validateMappingConfig`. It does carry `.meta()` across: `toOpenApiSchema` rebuilds containers, and Zod keys metadata by schema instance, so `carryMetadata` copies it onto each rebuilt node, with the outer node winning per key [21]. A `.meta()` on a call site of `requiredString()` or `trimString()` lands on the unwrapped string.

## Config revision events {#publish-is-best-effort}

```orient-flow
{ "v": 1, "title": "Config revision publish",
  "nodes": [
    { "id": "ctl", "label": "Mutating controller", "sub": "after the Mongo write", "kind": "step", "ev": [22] },
    { "id": "disp", "label": "ConfigEventDispatcher", "sub": "catch and log", "kind": "step", "service": "config-service", "tone": "accent", "ev": [7] },
    { "id": "rev", "label": "config_revision", "sub": "no attributes", "kind": "topic", "ev": [7, 23] },
    { "id": "cons", "label": "Fuse services", "sub": "remote-config", "kind": "external" }
  ],
  "edges": [
    { "from": "ctl", "to": "disp" },
    { "from": "disp", "to": "rev", "label": "best-effort" },
    { "from": "rev", "to": "cons", "label": "refresh or refetch" }
  ] }
```

Mutating controllers call `ConfigEventDispatcher` (`core/pubsub/config.dispatcher.ts`) after writing Mongo [22]. It publishes to one topic, named by `CONFIG_REVISION_TOPIC_NAME`. Two envelope shapes ride it, both wrapped as `{ record, metadata }` with `metadata.customer = "system"` and `metadata.source = "config-service"` [7][23]:

- **Data fragment** (`ConfigRevision = { updatedBy, fragments }`) inlines the changed config. It carries shipment-method, connector-mapping, backend-config, warehouse-routing, sku-blacklist and DDP-rules changes.
- **Resource link** (`ConfigResourceRevision = { updatedBy, resources }`) carries HATEOAS `{ self, connectors }` links only, not the data. The consumer (`@gfs-bifrost/remote-config`) fetches the resource back from this API. It carries `BACKEND_CONFIG` and `CONNECTOR` updates.

`FragmentType` is `DEFAULT_MAPPING`, `SNAP_ROUTING`, `SHIPMENT_METHOD`, `CONNECTOR_MAPPING`, `BACKEND_CONFIG`, `CONNECTOR`, `WAREHOUSE_ROUTING`, `SKU_BLACKLIST` and `DDP_RULES`. **CONFIRMED** Nothing calls `dispatchSnapRoutes`, and no dispatcher method exists for `DEFAULT_MAPPING`, so those two types are declared but never published [7][22].

**The publish is deliberately best-effort.** A Pub/Sub outage does not fail the HTTP write. `publish()` and `publishResourceLink()` catch, count `REVISION_PUBLISH_FAILED` and log; they never rethrow [7]. `PubsubHandler` sends `data` only, with no Pub/Sub attributes [23]. `updatedBy` is the constant `"admin"` [24].

The SFTP callback writes to Mongo through `updatePartial` and publishes no revision [9][25]. **ASSESSED** Cached readers of that connector therefore learn of the provisioned user only on cache expiry or the next unrelated connector event.

The topics `config_revision` and `customer_creation` belong to `bifrost-pubsub`, resolved through `terraform_remote_state` (`core_pubsub`) [17]. This repo creates only its own push subscription.

## The `/events/customer-creation` route is misnamed

It is the async callback from SFTP connector provisioning (`SftpAuthStatusHandler`), not customer creation. sftp-connector publishes and this service subscribes [9][25]. The handler finds the connector by `storefrontId`, `connectorId` and `config.type = SFTP`, then writes `config.isActive`, `config.auth` (public and private key) and `config.user` back [25]. A `failed` status blanks `auth` and `user`. A decode failure is logged at `warn` and dropped with a 204.

## Persistence (`repositories/`)

**Core reaches storage only through repositories.** Each aggregate has a driver-free interface in `repositories/<aggregate>.repository.ts` (businesses, storefronts, connectors, backends, shipment methods, DDP rules, feature flags), injected by `RepositoryTokens` from `RepositoriesModule`. The Mongo implementations in `repositories/mongo/` hold every filter, pipeline (`repositories/mongo/pipelines/`) and update, and return records without `_id`. Each method's name or comment states which rows it sees, live or live and soft-deleted, and that is the contract the Cloud SQL implementation is written against. The only Mongo types left in `core/` are the business delete's `MongoClient` and `ClientSession`. Underneath, `Collection<T>` is a thin generic Mongo wrapper, DI-injected per collection [6][26].

| Collection | Type | Indexes |
| ---------- | ---- | ------- |
| `business_information` | `BusinessInformation` | `businessId` |
| `storefronts` | `Storefront` | `storefrontId`, `businessId`, `businessId+storefrontId` |
| `connectors` | `ConnectorConfigService` | `connectorId`, `storefrontId`, `storefrontId+connectorId` |
| `backend_config` | `SnapBackendConfig` | `businessId` |
| `shipment_methods` | `ShipmentMethodConfig` | `businessId` |
| `ddp_config` | `DDPRuleConfig` | `businessId` |
| `feature_flags` | `FeatureFlag` | `key` (unique) |

**Runtime feature flags are not customer config.** `feature_flags` sits behind `/api/v1/feature-flags` in `core/feature-flags/` and publishes no `config_revision`. Instead, each successful write publishes a `FeatureFlagRevision` refetch signal (`{key, change, version?}`, no version on delete) to `bifrost.{env}.feature_flag_revision.v1` through `FeatureFlagEventDispatcher`. That publish is best-effort, bounded at 3 s, and counted on `fuse.feature_flag.published` / `.publish_failed`. Reads go through types' `resolveFeatureFlag`, so a due `scheduledChange` is served as applied without being written, and the next write folds it in. Writes re-parse strictly against `FeatureFlagSchema` and use `Collection.insert` / `setFields` (plain `$set` / `$inc`) rather than `save` / `updatePartial`.

**Pipeline updates drop `$`-prefixed strings.** `save` and `updatePartial` are aggregation-pipeline updates, and a pipeline `$set` reads a string starting with `$` as a field path. A free-text value like `"$5 off"` is therefore silently replaced, confirmed live on 2026-10-14. This applies to every config-service write that goes through those two methods. Use `insert` / `setFields` for free text.

**Warehouse routing and SKU blacklist have no collection of their own.** They live as fields on `business_information`, written through `BusinessesRepository.update` / `unset`, despite having their own HTTP resources [27]. The `Collections` enum also names `default_mappings` and `warehouse_routing`, but no provider uses them.

Every write carries a `metadata` sub-document: `createdAt` (once), `updatedAt`, and a `version`. **`version` increments on every write except an unchanged connector save.** `save` guards it with `$eq: ["$$ROOT", record]`. A fresh DTO never equals the stored document, which carries `_id` and `metadata`, so storefront, business, backend, shipment-method and DDP writes always bump. Connector saves pass the document just read, with its `_id` first (the connectors repository restores it), so an identical connector PATCH or mapping replace keeps its version. `updatePartial` and `setFields` increment unconditionally. The `X-Resource-Version` response header mirrors that version [26]. Deletes are hard (`deleteRecord`) or soft (`softDelete`, which sets `metadata.deletedAt`). Most reads filter out soft-deleted documents, so match that in any new query. Deleting a business soft-deletes its live backends, shipment methods, DDP configs and storefronts, and the live connectors in those storefronts, through each child's repository [26][27]. **The cascade is atomic.** It runs in one `UnitOfWork` (`repositories/unit-of-work.ts`). The Mongo implementation uses the driver's `withTransaction`, which is why MongoDB must run as a replica set, and it retries a write conflict, so concurrent deletes both succeed. The writes run one at a time. If any fails, or the business soft-deletes nothing, all of them roll back and the route answers 500. Integration tests pin this [28].

**Known gaps, carried as-is:**
- A live connector under an already soft-deleted storefront survives a business delete: the cascade reaches connectors through live storefront ids only.
- Business refs join connectors on the connector's own `businessId`, while the cascade goes through storefronts, so the two can disagree for a connector without one.
- The storefront connector list reads `connectorMappings`, which nothing writes, so `useCases` is always `[]`. Its filters return wrong pages too: on a seed of 3 connectors, the unfiltered list returned 1 and `type=sftp` returned 0. `userName` is ignored there.
- The business storefront list applies `status` to the total but not the page.
- Shipment-method and DDP upserts and hard deletes match tombstones too: they filter on `businessId` alone, so a write over a soft-deleted config rewrites it but keeps it deleted.
- `PUT /business/:id/ddp/rules` accepts a non-numeric `minValue`, so request validation is bypassed there (see [technical:G4]).
- An SFTP callback for an unknown or non-SFTP connector answers 500, which Pub/Sub redelivers until retention runs out.
- A `config_revision` publish has no timeout. An unreachable Pub/Sub holds every config write's response until the client gives up, unlike the feature-flag publish (3 s).
- `tsconfig.test.json` excludes integration specs from `build:check:tests`, and 14 type errors sit in them.

### Persistence surface {#persistence-surface}

**CONFIRMED** Inventory taken on 2026-10-28 at `dee24d0`, for [[Config Service Cloud SQL/Overview|Config Service Cloud SQL]] A0.

| What | Where | Count |
| --- | --- | --- |
| Core services holding an `ICollection<T>` | `backend-config`, `business-information` (six collections), `connectors`, `ddp-configs`, `feature-flags`, `sftp-auth-status`, `shipment-methods`, `storefront` (two) | 8 services, 14 injections |
| Hand-written aggregation pipelines | `backend-config/mongo-queries/list-all-configs.ts`, `business-information/constants.ts`, `connectors/connectors.service.ts`, `connectors/mongo-queries/list-all-connectors.ts`, `storefront/constants.ts`, `storefront/mongo-queries/storefront-update-retrieval-query.ts` | 6 files, all in `core/` |
| Transactions | `business-information.service.ts:160`, the cascading business delete. `ClientSession` appears in no other core file. | 1 caller |
| `Collection` methods called from core | `findOne` 24, `save` 15, `updatePartial` 4, `softDeleteMany` 4, `deleteRecord` 4, `find` 3, `deleteRecordMany` 3, `unsetFields` 2, `softDelete` 2, `countDocuments` 2, `setFields` 1, `insert` 1 | |
| Unique indexes | `feature_flags.key` and `backend_config`'s `businessId+type+metadata.deletedAt`. `businessId`, `storefrontId` and `connectorId` are indexed but **not unique**; creates check for conflicts in code. Business create refuses a soft-deleted id too (409 "previously deleted"). | 1 |

**CONFIRMED** Since A1 (`5bb05ac`) none of the injections, pipelines or `Collection` calls above sit in `core/`: they live behind the repositories. The transaction is the one exception.

**The response contract is recorded as shapes** in `code/src/__contract__/` by `pnpm run contract:snapshot` (shapes, status, content type, `X-Resource-Version`, list order; never values). Taken against dev on 2026-10-28, it pins:

- `GET /storefronts/:id/connectors` returns `metadata` (`createdAt`, `updatedAt`, `version`) on each row. That is part of the shared contract: `@gfs-bifrost/types` `ConnectorSummaryDTOSSchema` declares it optional. No GET route returns Mongo's `_id`; the storefront connector rows did until A5 (#254), and the PATCH storefront response did until A1 (#269).
- The list routes page with `count` (1–100, default 20) and `offset`. There is no `limit` parameter: it is ignored, so a caller using it silently gets the default 20. Only the business list sorts explicitly (`_id`, oldest first); the connector, backend and storefront-connector lists come back in Mongo's natural order.
- `X-Resource-Version` is sent on single-resource GETs (business, backend, connector, storefront, mapping, feature flag) and absent on lists and on the DDP, SKU-blacklist, warehouse-routing and shipment-method routes.
- An unknown business id answers 404; a malformed one (anything but uppercase letters and digits) answers 400 with `issues`.

**CONFIRMED** No code or IaC in this repo encrypts credential fields. The SFTP private key from the callback, the REST connector's generated API key and the Snap backend credentials are stored as supplied [25][29]. **UNKNOWN** Whether Atlas encrypts at rest beyond its default, and what the `config_service_aes_key` secret in `core-infra` is used for: no consumer of it appears here.

## Build, test and deploy

- pnpm 10 (`node = 24`), run from `code/`. `pnpm run check-code` is `build:check` plus `build:check:tests`, two separate tsconfigs: the test one catches spec and fixture errors the main one misses [30][31]. `pnpm test` is Vitest. Integration tests need a real Mongo replica set (`docker-compose.integration.yaml` in CI).
- Lint is Biome, not ESLint. pnpm overrides live in `pnpm-workspace.yaml`, because pnpm 10 ignores `package.json`'s `pnpm.overrides`.
- **CI drift.** `code-quality.yaml` and `integration-tests.yaml` still `setup-node` 22 and pin pnpm `11.0.8` or `latest`, against the real node-24 and pnpm-10 runtime [32]. `latest` risks `ERR_PNPM_TARBALL_URL_MISMATCH` against `@gfs-bifrost` GitHub Packages.
- **Deploy.** `on-push.yaml` triggers on any push to `main` or `master` with no path filter, so a docs-only commit redeploys. The prod leg is gated by the `terraform-prod` environment approval [33].
- **Hosts.** Dev `config.fuse.freightops.dev`, prod `config.api.fuse.ilg.software` [34].

## Runtime

Cloud Run in `europe-west2` with `min_instance_count = 1`. Two containers: the app on port 3000 (`node:24-alpine` image), and a Datadog `serverless-init` sidecar at 256Mi and 500m that ships logs and metrics to both the GFS and ILG accounts [9][35]. MongoDB is an Atlas `REPLICASET` cluster on GCP `EUROPE_WEST_2`: three M10 nodes autoscaling to M20, with backup and point-in-time recovery on. The database name equals the project name [36].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "code/src/main.ts@63babd7" },
  { "id": 2, "kind": "code", "ref": "code/src/bootstrap/app.ts@63babd7" },
  { "id": 3, "kind": "code", "ref": "code/src/http/middleware/auth/auth.middleware.ts@63babd7" },
  { "id": 4, "kind": "code", "ref": "code/src/bootstrap/factory.ts@63babd7" },
  { "id": 5, "kind": "code", "ref": "code/src/core/storefront/storefront.service.ts@63babd7" },
  { "id": 6, "kind": "code", "ref": "code/src/repositories/collections.module.ts@63babd7" },
  { "id": 7, "kind": "code", "ref": "code/src/core/pubsub/config.dispatcher.ts@63babd7" },
  { "id": 8, "kind": "code", "ref": "iac/projects/config-service/pubsub.tf@63babd7" },
  { "id": 9, "kind": "code", "ref": "code/src/http/events/events.controller.ts@63babd7" },
  { "id": 10, "kind": "code", "ref": "iac/env/global.tfvars@63babd7" },
  { "id": 11, "kind": "code", "ref": "code/src/config/env.ts@63babd7" },
  { "id": 12, "kind": "code", "ref": "code/src/exceptions/http/domain-exception.filter.ts@63babd7" },
  { "id": 13, "kind": "code", "ref": "iac/projects/config-service/iam.tf@63babd7" },
  { "id": 14, "kind": "code", "ref": "iac/projects/config-service/load-balancer.tf@63babd7" },
  { "id": 15, "kind": "code", "ref": "code/src/exceptions/http/middleware.ts@63babd7" },
  { "id": 16, "kind": "code", "ref": "code/src/bootstrap/app.module.ts@63babd7" },
  { "id": 17, "kind": "code", "ref": "iac/projects/config-service/remote.tf@63babd7" },
  { "id": 18, "kind": "code", "ref": "code/src/http/api/v1/business/business.controller.ts@63babd7", "note": "one of 11 controllers; routes counted by grepping @Get/@Post/@Put/@Patch/@Delete under code/src/http" },
  { "id": 19, "kind": "code", "ref": "code/src/http/health/health.controller.ts@63babd7" },
  { "id": 20, "kind": "code", "ref": "iac/projects/config-service/cloud-run.tf@63babd7" },
  { "id": 21, "kind": "code", "ref": "code/src/shared/openapi-schema.utilities.ts@63babd7" },
  { "id": 22, "kind": "code", "ref": "code/src/http/api/v1/storefronts/storefront-connectors.controller.ts@63babd7" },
  { "id": 23, "kind": "code", "ref": "code/src/core/pubsub/pubsub.handler.ts@63babd7" },
  { "id": 24, "kind": "code", "ref": "code/src/core/pubsub/constants.ts@63babd7" },
  { "id": 25, "kind": "code", "ref": "code/src/core/sftp-auth-status/sftp-auth-status.handler.ts@63babd7" },
  { "id": 26, "kind": "code", "ref": "code/src/repositories/collection.ts@63babd7" },
  { "id": 27, "kind": "code", "ref": "code/src/core/business-information/business-information.service.ts@63babd7" },
  { "id": 28, "kind": "code", "ref": "code/src/shared/mongo.utilities.ts@63babd7" },
  { "id": 29, "kind": "code", "ref": "code/src/shared/crypto/secure-key.ts@63babd7" },
  { "id": 30, "kind": "code", "ref": "code/package.json@63babd7" },
  { "id": 31, "kind": "code", "ref": "mise.toml@63babd7" },
  { "id": 32, "kind": "code", "ref": ".github/workflows/code-quality.yaml@63babd7" },
  { "id": 33, "kind": "code", "ref": ".github/workflows/on-push.yaml@63babd7" },
  { "id": 34, "kind": "code", "ref": "iac/env/prod.tfvars@63babd7" },
  { "id": 35, "kind": "code", "ref": "code/dockerfile@63babd7" },
  { "id": 36, "kind": "code", "ref": "iac/projects/config-service/mongo.tf@63babd7" }
] }
```
