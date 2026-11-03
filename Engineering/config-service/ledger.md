---
tags: [waypoint, ledger]
title: config-service — work ledger
---
# config-service — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-03 — Freeze dev config writes for the Cloud SQL cutover

Freeze dev config writes for the Cloud SQL cutover

D3 runbook step 6: persistence_read_only = true in dev.tfvars. Held as a draft until the window is agreed with integrations; merging starts the window.

Ship: SHIP-1028-cloudsql-repo-seam
PR: gfs-bifrost/config-service#306

## 2026-11-03 — Number parity placeholders in sorted key order

Number parity placeholders in sorted key order

parity:write numbered generated values by first appearance, so a key-order difference (Mongo updatedAt before createdAt) read as a value difference. Now numbered in sorted key order; output key order kept. First live dev write check: 83/83 steps and 62 events identical with the fix.

Ship: SHIP-1028-cloudsql-repo-seam
PR: gfs-bifrost/config-service#305

## 2026-11-03 — Add the write half of the Cloud SQL parity check

Add the write half of the Cloud SQL parity check

Ship: SHIP-1028-cloudsql-repo-seam. D2 parity oracle (83-step write sequence plus the events each step publishes). Script only.

PR: gfs-bifrost/config-service#303

## 2026-11-03 — Add the read half of the Cloud SQL parity check

Add the read half of the Cloud SQL parity check

Ship: SHIP-1028-cloudsql-repo-seam. D2 parity oracle (every GET route, values compared, Mongo as the expected side). Script only.

PR: gfs-bifrost/config-service#302

## 2026-11-03 — Set PERSISTENCE_READ_ONLY from a persistence_read_only tfvar

Set PERSISTENCE_READ_ONLY from a persistence_read_only tfvar

Ship: SHIP-1028-cloudsql-repo-seam. The cutover write freeze becomes a tfvars change (default false, no behaviour change), needed for the D3 dev rehearsal and E2. E1/E2 owe (1).

PR: gfs-bifrost/config-service#301

## 2026-11-03 — Take zod 4.6.7 so the zod advisory is fixed, not allowlisted

Take zod 4.6.7 so the zod advisory is fixed, not allowlisted

Dependency Audit went red on main and on every open PR when the GHSA-mrhx-c7xc-m3w5 allowlist entry expired. types 11.4.1 and observability 2.5.0 now accept zod ^4.4.3, so zod moved to 4.6.7 and the entry was removed.

PR: gfs-bifrost/config-service#300

## 2026-11-02 — Add the Mongo to Cloud SQL backfill job

Add the Mongo to Cloud SQL backfill job

Unit D1. A hand-run Cloud Run Job (config-service-<env>-backfill) makes Cloud SQL mirror Mongo in one transaction: upsert on natural ids, delete what Mongo lacks, carry version and timestamps, skip and report what the schema would refuse. Dry run by default; refuses when Postgres holds writes Mongo doesn't, when every collection reads empty, or during a migration. A new persistence_backend tfvar sets PERSISTENCE_BACKEND, and the job exists only while it is mongo. Dev dry run: whole dataset in 1.5s. Prod pre-check: no duplicates or orphans.

Ship: SHIP-1028-cloudsql-repo-seam
PR: gfs-bifrost/config-service#296
PR: gfs-bifrost/config-service#297
PR: gfs-bifrost/config-service#298

## 2026-11-02 — Switch config-service's persistence backend by env and add a read-only write freeze

Switch config-service's persistence backend by env and add a read-only write freeze

Unit C5. PERSISTENCE_BACKEND=mongo|postgres (default mongo) chooses the repositories inside RepositoriesModule; in postgres mode Mongo is never connected, boot waits for Cloud SQL's first ping and /health gates on Postgres. PERSISTENCE_READ_ONLY=true answers every write with 503 + Retry-After (the E2 write freeze), the SFTP callback push included. /health reports persistence { backend, readOnly }. Defaults leave prod unchanged; no Terraform.

Ship: SHIP-1028-cloudsql-repo-seam
PR: gfs-bifrost/config-service#295

## 2026-11-02 — Hold a Cloud SQL pool in config-service and report it on /health

Hold a Cloud SQL pool in config-service and report it on /health

Unit C4. config-service opens a Cloud SQL pool (IAM user via the connector, no password) in the background, pings it once a minute and reports checks.postgres on /health without gating the 200. Emits fuse.postgres.up/latency. New env INSTANCE_CONNECTION_NAME/PGDATABASE/PGUSER (all or none) and PG_POOL_MAX; Cloud Run max_instance_count is now 20 in prod and 3 in dev. Nothing reads from Postgres yet; C5 gates health on it when it becomes the backend. R10 still open: a 77-minute session on dev stayed UP, but a long idle is untested.

Ship: SHIP-1028-cloudsql-repo-seam
PR: gfs-bifrost/config-service#294

## 2026-11-02 — Add the Postgres repositories for all seven aggregates (C2 + C3)

Add the Postgres repositories for all seven aggregates (C2 + C3)

Stack #286-#290: per-backend integration wiring, Postgres TestStore + row mapping + unit of work, then connectors, storefronts + businesses, and backends/shipment methods/DDP/flags. The Mongo write semantics are copied (mongoSet merge, keep-version-when-unchanged), except two recorded differences. The integration suite runs on both backends in CI: Mongo 577, Postgres 568 passed. Nothing in the running service uses the Postgres code until C5. Prod 00055-cpk on 057c8f8.

Ship: SHIP-1028-cloudsql-repo-seam
PR: gfs-bifrost/config-service#286
PR: gfs-bifrost/config-service#287
PR: gfs-bifrost/config-service#288
PR: gfs-bifrost/config-service#289
PR: gfs-bifrost/config-service#290

## 2026-11-02 — Stop a terminated idle Postgres test connection failing the integration run

Stop a terminated idle Postgres test connection failing the integration run

Existing CI flake (3 runs): a forced Postgres database drop terminated an idle test connection, and with no error listener the run failed after every test passed (57P01). tolerateTermination() on every Postgres test connection; green 4/4 on re-runs.

Ship: SHIP-1028-cloudsql-repo-seam
PR: gfs-bifrost/config-service#292

## 2026-11-02 — Keep a patched flag's description absent instead of null

Keep a patched flag's description absent instead of null

PATCH of a feature flag with no description stored description: null (Mongo writes undefined as null), which remote-config's FeatureFlagSchema rejects, so the flag would read false in every backend reader. Found by the C3 parity review. Latent in prod: the only prod flag has never been patched.

Ship: SHIP-1028-cloudsql-repo-seam
PR: gfs-bifrost/config-service#285

## 2026-11-02 — Run the integration suite through a backend-neutral TestStore

Run the integration suite through a backend-neutral TestStore

Programme unit A4. 19 integration specs moved off direct Mongo access onto repositories/__fixtures__/test-store (seed/inspect/remove/clear), backend chosen by INTEGRATION_BACKEND (mongo only until C2), CI matrix axis added, Mongo-implementation suites gated to the mongo leg. Converted by four parallel agents from a reference conversion; identical pass counts per file (suite 574 passed / 15 skipped). Review: no weakened assertion; lookups now type-checked; the SNAP-delete test now counts only live SELECTOR backends. Prod on 5539cbb (test-only).

Ship: SHIP-1028-cloudsql-repo-seam
PR: gfs-bifrost/config-service#284

## 2026-11-02 — Add the Postgres schema for config-service's seven aggregates

Add the Postgres schema for config-service's seven aggregates

Programme unit C1. Drizzle schema (businesses, storefronts, connectors, backends, shipment_methods, ddp_rules, feature_flags) as migration 0001_schema: metadata envelope as columns behind a bigint identity, jsonb typed to @gfs-bifrost/types (Jsonified dates), natural ids unique over all rows, FKs business→storefront→connector, partial unique one-live-backend-per-type and flag key, generated connector type/status/sftp username. 16 real-Postgres tests as the app user. Applied in dev and prod by the migration job; nothing reads it yet. Prod on 88d506d.

Ship: SHIP-1028-cloudsql-repo-seam
PR: gfs-bifrost/config-service#283

## 2026-10-29 — Fail a PR whose schema has no migration, or whose migrations Drizzle would skip

Fail a PR whose schema has no migration, or whose migrations Drizzle would skip

Programme unit B4. Migrations job in code-quality.yaml runs scripts/check-migrations.ts: drizzle-kit generate into a scratch copy must write nothing; journal, SQL and snapshots must agree with strictly increasing timestamps; merged migrations/snapshots unchanged vs base; new migrations timestamped after main's newest; PR SQL written to the job summary. Proven red in CI on a throwaway branch (run 40948742886). drizzle-kit exits 0 on failure, so the check reads its output. Review caught unchecked snapshots; fixed and re-proven. Prod on 8ec3e6d (CI-only change).

Ship: SHIP-1028-cloudsql-repo-seam
PR: gfs-bifrost/config-service#281

## 2026-10-29 — Run Cloud SQL migrations in a Cloud Run Job the deploy waits on

Run Cloud SQL migrations in a Cloud Run Job the deploy waits on

Programme unit B3. google_cloud_run_v2_job migrate (same image, node dist/migrate.js, migrator SA, Drizzle migrator under an advisory lock, grants config_service_app to PG_APP_USERS); run_execution_token from image + run id/attempt so every apply executes and the provider waits; service depends_on it. G5 resolved without gcloud (terragrunt-action container has none). Proven on dev with a throwaway failing migration: first create, update and re-runs all fail the apply with the service unchanged. First migration (app role) applied in dev and prod. docs/migrations.md added. Prod on 620ed7b.

Ship: SHIP-1028-cloudsql-repo-seam
PR: gfs-bifrost/config-service#280

## 2026-10-29 — Make the business delete atomic through a backend-neutral unit of work

Make the business delete atomic through a backend-neutral unit of work

Programme unit A3. UnitOfWork (repositories/unit-of-work.ts) with a Mongo implementation on withTransaction replaces MongoUtilities.transaction; the seven cascade repository methods take an optional tx; deleteBusinessInformation runs its cascade in one transaction, one write at a time (Harry chose atomic). Core imports no mongodb types. Parity with main: 52 steps / 17 events / 12 rows identical locally; 54-step dev round trip identical. Prod on 83f2292, read-only checks clean.

Ship: SHIP-1028-cloudsql-repo-seam
PR: gfs-bifrost/config-service#279

## 2026-10-29 — Create config-service's Cloud SQL instance in prod

Create config-service's Cloud SQL instance in prod

Programme unit B2 (prod half). cloudsql_enabled in prod.tfvars: config-service-prod, PostgreSQL 17, db-custom-1-3840, REGIONAL, no impersonators. Prod plan (10 to add) agreed with Harry before merge via a local read-only targeted plan; the gate plan matched (plus image + standing drift). Verified read-only: RUNNABLE, REQUIRED/ENCRYPTED_ONLY/no authorised networks, PITR and deletion protection on, both IAM users, direct connection times out; service healthy on 41e843f. Shared in #bifrost-forge per the no-review-window rule.

Ship: SHIP-1028-cloudsql-repo-seam
PR: gfs-bifrost/config-service#278

## 2026-10-29 — Order the Cloud SQL module's users after their grants

Order the Cloud SQL module's users after their grants

From the parcel-portal sql.tf comparison: google_sql_user now depends on its connector grants, so a workload rolling on PGUSER can't start before them. README: retry the first connection, local plain Postgres, CREATE ROLE works directly, the built-in postgres user. No resource changes.

Ship: SHIP-1028-cloudsql-repo-seam
PR: gfs-bifrost/config-service#277

## 2026-10-29 — Have the Cloud SQL module create the migrator and declare its impersonators

Have the Cloud SQL module create the migrator and declare its impersonators

Agreed with Harry: the module creates <name>-migrator by default (overridable; app accounts stay caller-owned), and migrator_impersonators declares break-glass access in code. config-service moved its migrator into the module with a moved block (dev plan: display_name in place + Harry's tokenCreator on the migrator). Dev verified: both IAM users log in under the conditioned instanceUser; the migrator has CREATEROLE/CREATEDB; the app is refused DDL/CREATE ROLE/SET ROLE.

Ship: SHIP-1028-cloudsql-repo-seam
PR: gfs-bifrost/config-service#276

## 2026-10-29 — Create config-service's Cloud SQL instance in dev

Create config-service's Cloud SQL instance in dev

Programme unit B2 (dev half). config-service-dev Cloud SQL (PostgreSQL 17, db-f1-micro, ZONAL) through iac/modules/cloud-sql-iam, behind cloudsql_enabled (dev only); app user = the service's existing SA, new config-service-dev-migrator SA holds cloudsqlsuperuser. Dev plan agreed with Harry (11 add). Verified live: RUNNABLE, REQUIRED/ENCRYPTED_ONLY/no authorised networks, both IAM users, direct connection to the public IP times out, a non-user identity is refused at login. Prod plan image + standing drift only; prod on ad51d6a. Owed: login as each SA (needs temporary tokenCreator), the default postgres BUILT_IN user, prod enablement.

Ship: SHIP-1028-cloudsql-repo-seam
PR: gfs-bifrost/config-service#275

## 2026-10-29 — Add a local IAM-only Cloud SQL module

Add a local IAM-only Cloud SQL module

Programme unit M1. iac/modules/cloud-sql-iam: Cloud SQL for PostgreSQL where every login is an IAM service account through a connector (no passwords, no authorised networks, connector_enforcement REQUIRED). Inputs are identities (app accounts, one migrator with cloudsqlsuperuser); connector_env output per account. 27 terraform tests on 1.9.0 against google 7.46.2 and 8.9.0. No caller yet, so no infra change; B2 instantiates it on dev.

Ship: SHIP-1028-cloudsql-repo-seam
PR: gfs-bifrost/config-service#274

## 2026-10-28 — Read businesses through repositories and cascade the delete through each child's

Read businesses through repositories and cascade the delete through each child's

Config Service Cloud SQL programme, unit A1, increment 4 (business, the last); A1 done. BusinessesRepository plus a live soft-delete on each child repository, and BusinessInformationService moved onto them. No behaviour change. Found that the business-delete cascade was never atomic; kept and pinned for A3. Prod 5bb05ac.

Ship: SHIP-1028-cloudsql-repo-seam
PR: gfs-bifrost/config-service#271
PR: gfs-bifrost/config-service#272

## 2026-10-28 — Read storefronts and storefront connectors through repositories

Read storefronts and storefront connectors through repositories

Config Service Cloud SQL programme, unit A1, increment 3 (storefront). StorefrontsRepository plus storefront-scoped ConnectorsRepository operations, and StorefrontService moved onto them. No behaviour change except PATCH storefront dropping Mongo's _id (approved). Prod abbca36.

Ship: SHIP-1028-cloudsql-repo-seam
PR: gfs-bifrost/config-service#268
PR: gfs-bifrost/config-service#269

## 2026-10-28 — Put connectors behind a repository

Put connectors behind a repository

Config Service Cloud SQL programme, plan increment 2 (A1). ConnectorsService and the SFTP provisioning callback onto a ConnectorsRepository; list pipeline and shared helpers moved to repositories/mongo/pipelines. Corrected the A0 count-vs-limit claim. Local parity with main exact (19 GET routes, 17-step connector + callback sequence).

Ship: SHIP-1028-cloudsql-repo-seam
PR: gfs-bifrost/config-service#267

## 2026-10-28 — Put backends behind a repository

Put backends behind a repository

Config Service Cloud SQL programme, A2 / plan increment 1, fourth slice (completes increment 1), stacked on #265. Keeps the Delivery Backends invariants (plain-insert create, live-row _id write-back, type-scoped delete, { configs: 0 }), each pinned by a test and mutation-checked. Local parity with main at 2465c74 exact for SNAP and SELECTOR.

Ship: SHIP-1028-cloudsql-repo-seam
PR: gfs-bifrost/config-service#266

## 2026-10-28 — Put feature flags behind a repository

Put feature flags behind a repository

Config Service Cloud SQL programme, A2 / plan increment 1, third slice, stacked on #263. Duplicate-key MongoServerError now translated in the repository. Local parity with main exact. Review found _id strip tested on one of four paths (fixed, mutation-checked).

Ship: SHIP-1028-cloudsql-repo-seam
PR: gfs-bifrost/config-service#265

## 2026-10-28 — Put DDP rules behind a repository

Put DDP rules behind a repository

Config Service Cloud SQL programme, A2 / plan increment 1, second slice, stacked on #262. Same pattern; local parity with main exact. Review added upsert-argument assertions. Found a pre-existing validation bypass: PUT ddp/rules accepts a non-numeric minValue (recorded as follow-up).

Ship: SHIP-1028-cloudsql-repo-seam
PR: gfs-bifrost/config-service#263

## 2026-10-28 — Put shipment methods behind a repository

Put shipment methods behind a repository

Config Service Cloud SQL programme, A2 / plan increment 1, first slice; sets the repository pattern (driver-free interface, Mongo implementation, RepositoriesModule). Local parity with main exact on 19 GET routes and a 12-step write sequence. Self-review fixed a lost soft-delete test, a mongodb type leak and a wrong comment (upsert over a soft-deleted config keeps deletedAt, checked on Mongo 7).

Ship: SHIP-1028-cloudsql-repo-seam
PR: gfs-bifrost/config-service#262

## 2026-10-28 — Move the google providers from 6.41.0 to 7.46.2

Move the google providers from 6.41.0 to 7.46.2

Config Service Cloud SQL programme, unit M0. google_sql_user.database_roles (7.18.0+) lets the IAM-centric Cloud SQL module grant Postgres roles with no password. No project resource is in the 7.0 upgrade guide. Merge waits on dev's B1 network cleanup; prod plan shared with Harry if it shows more than image + drift.

Ship: SHIP-1028-cloudsql-repo-seam
PR: gfs-bifrost/config-service#261

## 2026-10-28 — Give config-service a VPC and send private-range egress through it

Give config-service a VPC and send private-range egress through it

Config Service Cloud SQL programme, unit B1. Own VPC + subnet, PSA range + connection for Cloud SQL, Cloud Run direct VPC egress (PRIVATE_RANGES_ONLY). Verified on dev: revision serving with the VPC, PSA ACTIVE, Atlas, Pub/Sub publish and Datadog unchanged. Gotcha: merging #257 while this branch was on dev let main's dev apply destroy the PSA resources and fail on the subnet; restored by re-running the branch deploy. Must merge before anything else in config-service.

PR: gfs-bifrost/config-service#260

## 2026-10-28 — Format the contract snapshot after writing it

Format the contract snapshot after writing it

Config Service Cloud SQL programme, A0 follow-up. contract:snapshot runs biome format on its output so a re-run only diffs on a real shape change. Re-run against dev after #254 matched the committed contract exactly, confirming #254 live on dev.

PR: gfs-bifrost/config-service#257

## 2026-10-28 — List a business's backends and tag backend change events with their type

List a business's backends and tag backend change events with their type

Delivery Backends A3, slice 3/3. GET /business and /business/{id} carry backends refs ({backendId, type}, tombstones excluded); BACKEND_CONFIG backlink carries backendType; self href left as /backends/{id} because wms-gateway parses it. Business GET contracts re-recorded. Verified on dev via a temporary pull subscription.

PR: gfs-bifrost/config-service#258

## 2026-10-28 — Accept SELECTOR on the backend routes

Accept SELECTOR on the backend routes

Delivery Backends A3, slice 2/3. ?type=SELECTOR on every backend route; POST takes either shape; update bodies parsed by type; per-type response mapping; Selector changes publish no revision events. Verified on dev on A3VERIFY.

PR: gfs-bifrost/config-service#256

## 2026-10-28 — Stop returning Mongo's _id on the storefront connector list

Stop returning Mongo's _id on the storefront connector list

Config Service Cloud SQL programme, unit A5 (out-of-ticket, approved by Harry). GET /storefronts/:id/connectors projects _id: 0 like the global /connectors list; metadata stays (declared by ConnectorSummaryDTOSSchema). No consumer reads _id. Proven by a red/green integration test and a local before/after contract snapshot that differs only by that property. Not yet on dev: dev was serving another in-flight branch deploy.

PR: gfs-bifrost/config-service#254

## 2026-10-28 — Record the GET contract as shapes so a persistence swap can be diffed

Record the GET contract as shapes so a persistence swap can be diffed

Config Service Cloud SQL programme, unit A0 (out-of-ticket, prep for Merak). Adds pnpm run contract:snapshot, which records every GET route's shape, status, content type, X-Resource-Version and list order into code/src/__contract__/ (shapes only, never values), and commits the first dev snapshot. Found: _id leaking on GET /storefronts/:id/connectors (fixed in A5), limit clamped to 20 on list routes, only the business list sorted, and no unique index except feature_flags.key.

PR: gfs-bifrost/config-service#253

## 2026-10-28 — Allow one backend per type per business, with a 409 on a second create

Allow one backend per type per business, with a 409 on a second create

Delivery Backends A3, slice 1/3. Create is a plain insert behind a unique index on businessId+type+metadata.deletedAt; a second POST is a 409 (documented but never real: the upsert overwrote and re-minted backendId). Updates write back by _id. Verified on dev on throwaway business A3VERIFY.

PR: gfs-bifrost/config-service#252

## 2026-10-28 — Ignore two new undici advisories in the base image's bundled npm

Ignore two new undici advisories in the base image's bundled npm

CVE-2026-87018 and CVE-2026-109383 (undici 6.28.0, HIGH) appeared overnight in the npm CLI bundled in node:24-alpine and turned the container scan red on main and on #248. The runner never invokes npm and no npm release bundles undici >=6.29.1 yet, so they're ignored with expiry 2026-11-04. Follow-up named on the PR: move the runner to the node24-runtime golden image or strip npm from it, retiring this whole class of ignores.

PR: gfs-bifrost/config-service#251

## 2026-10-27 — Take the backend type as a query param on the backend routes

Take the backend type as a query param on the backend routes

Reworked A2 after Harry's review. The legacy backend routes take ?type=, defaulting to SNAP (only SNAP accepted until types adds SELECTOR; others 400), instead of a hidden SNAP filter. PATCH keeps the stored type. No plural /backends route: A3 widens the param instead. Programme docs and decision record updated.

PR: gfs-bifrost/config-service#248

## 2026-10-27 — Clear the container scan's new HIGH findings

Clear the container scan's new HIGH findings

DevSecOps Scans (Trivy container scan) red nightly on main since 10-24. body-parser 1.20.9/2.4.0 (reachable one-request crash, fixed via direct bump + overrides), multer override floor to 2.5.0, npm-bundled undici and http-cache-semantics ignored. zod CVE-2023-54404 is reachable but ignored with exp:2026-11-03, because @gfs-bifrost/types and observability pin their zod peer to 4.4.3. Follow-up: raise that peer in pkg-node. Rescan of the branch image: 0 unignored HIGH/CRITICAL.

PR: gfs-bifrost/config-service#249

## 2026-10-27 — Scope the legacy backend routes to SNAP backends

Scope the legacy backend routes to SNAP backends

Delivery Backends A2. /api/v1/backend and /api/v1/business/:id/backend now find, upsert and delete only type SNAP rows (SNAP_BACKENDS_ONLY), so a SELECTOR row is invisible to them and can't be overwritten (save upserts on its filter; the old filter was businessId alone). No behaviour change today: dev 40 / prod 33 backends are all SNAP. Verified on dev with a hand-inserted SELECTOR row and a throwaway business; the poller, snap-adapter and wms-gateway re-read the list cleanly. Must reach prod before A3 (G1).

PR: gfs-bifrost/config-service#248

## 2026-10-14 — Publish feature flag revisions

Publish feature flag revisions

FeatureFlagsService now publishes BifrostMessage<FeatureFlagRevision> {key, change, version?} to bifrost.{env}.feature_flag_revision.v1 after each successful create/update/delete, via a new FeatureFlagEventDispatcher. It's best-effort, awaited behind a 3 s timeout, and counted on fuse.feature_flag.published / .publish_failed (not the config_revision metrics). IaC adds the remote-state local, the publisher IAM member and the Cloud Run env var. Dev-verified with a throwaway pull subscription: exactly 3 messages, none for a 409. The flag write-route specs run through an always-rejecting publisher.

PR: gfs-bifrost/config-service#243

## 2026-10-14 — Runtime feature flags live in prod

Runtime feature flags live in prod

config-service-prod on 815b0e5 (Deploy 38565511306, approved 2026-10-14 per Harry), carrying #239-#242 plus Renovate #236/#237. Prod GET /api/v1/feature-flags returns 200 {flags:[]}. 25 older parked Deploy runs cancelled; 35326288564 (11d4771) is stuck in GitHub (cancel/force-cancel/gate review all 409/422), so it cannot be approved and is not a rollback hazard. Plan signed off; learnings in architecture.md (G4 passthrough DTOs, version always increments, $-string pipeline drop). Backend delivery and caching: FUSE-1313.

PR: gfs-bifrost/config-service#242

## 2026-10-14 — Add feature-flag write routes and docs

Add feature-flag write routes and docs

Runtime feature flags, part 3 of 3 in this repo; workshop action L3, with no ticket.

- POST, PATCH and DELETE on /api/v1/feature-flags. PATCH takes expectedVersion, and a conflict gives 409. DELETE is a hard delete (204). x-user becomes updatedBy, falling back to admin.
- Writes emit an operational 'Feature flag changed' log. It is not an audit trail: fuse-ui owns audit.
- Gotcha, fixed in #242: a log attribute named version lands on Datadog's reserved service-version tag, so it is now flagVersion.
- CLAUDE.md corrects the claim that metadata.version only increments on a real change, and documents the $-string pipeline footgun. fuse-mcp data is updated at a686a6e.
- Verified live on dev: a full round trip, including a scheduled flip with no write.
- The prod deploy is still waiting on the terraform-prod approval and the freeze question.

Plan: [[runtime-feature-flags-feature-flags-store-and-ap]].

PR: gfs-bifrost/config-service#241 (and the follow-up gfs-bifrost/config-service#242)

## 2026-10-14 — Serve feature flags on GET /api/v1/feature-flags

Serve feature flags on GET /api/v1/feature-flags

Runtime feature flags, part 2 of 3 in this repo; workshop action L3, with no ticket.

- Read routes: the list returns { flags: [...] }, wrapped because the generated doc mangles array DTOs; GET by key sends X-Resource-Version.
- Both serve resolved state.
- openapi.yaml schemas are named after the Nest DTO classes (FeatureFlagResponseDto, FeatureFlagListResponseDto), so fuse-ui's alias survives the generated-spec move.
- Verified live on dev: 200 {flags:[]} with the key, 401 without it, 404 for an unknown key, and both operations in docs-json.

Plan: [[runtime-feature-flags-feature-flags-store-and-ap]].

PR: gfs-bifrost/config-service#240

## 2026-10-14 — Add the feature_flags store and FeatureFlagsService

Add the feature_flags store and FeatureFlagsService

Runtime feature flags, part 1 of 3 in this repo. This is workshop action L3, with no ticket; backend delivery is FUSE-1313.

- A feature_flags collection with a unique key index. Collection takes a uniqueIndexes param.
- FeatureFlagsService re-parses writes against the types 10.14.0 strict schema, because the DTOs are passthrough.
- Reads resolve a due scheduledChange without writing. Updates fold that change in and are conditional on the version they read.
- Gotcha: Collection.save and updatePartial are pipeline updates, so a free-text value starting with $ is evaluated as a field path and dropped. Flags use the new plain-operator insert and setFields instead. Existing paths are unchanged, and that needs its own look.
- No route yet: read routes come next, then the write routes, openapi.yaml and the docs.

Plan: [[runtime-feature-flags-feature-flags-store-and-ap]].

PR: gfs-bifrost/config-service#239

## 2026-10-01 — Derive connector useCases in the business index

Derive connector useCases in the business index

GET /api/v1/business and /:businessId projected the unstored `$$connector.useCases`, so every connector ref lacked `useCases` (required in openapi.yaml and ConnectorRefDTOSchema). Now uses `useCasesProjection("$$connector.")` like the storefront routes; integration fixtures seed per-use-case keys instead of the stored array that hid the bug. Poller Clear-Down E1 prerequisite for C1's "does any connector take this type" check — note REST connectors carry no use-case keys, so C1 must treat REST separately. Plan: [[config-service/plans/business-index-returns-connector-usecases]].

PR: gfs-bifrost/config-service#235

## 2026-09-24 — FUSE-1253

Accept egressFiletype edi and ediEnvelope on SFTP connectors

SFTP connectors accept egressFiletype edi plus an optional ediEnvelope. Validation runs on the merged document after mergePartialUpdate: edi requires an envelope, ids are 1-35 characters, qualifiers are 14/91/ZZ. There are no defaults, and a PATCH that omits the fields preserves them. The rules live in core/schemas.ts. Must not merge until fapi#147 and shopify-connector#282 are on types 10.4.0 in prod, because remote-config's backlink refresh isn't type-filtered.

PR: gfs-bifrost/config-service#226

## 2026-09-23 — FUSE-809

Remove the business-level backend confirmations flag

Re-lands the FUSE-809 removal that was reverted as a HOTFIX until the per-connector confirmations toggle existed (FUSE-1063, now gating polling in snap-adapter). Backend confirmations is no longer accepted on create/update or returned by the backend/business-backend routes; every HOTFIX(FUSE-809 revert) site removed. broadcastConfirmations is untouched (the poller still reads it). Stored data left alone: 27 of 30 prod backend docs still carry the field, but nothing reads or returns it.

PR: gfs-bifrost/config-service#222

## 2026-09-23 — FUSE-1217

Accept and validate dictionaries on connector mappings

Connector mappings now accept dictionaries on create/replace; they persist, return on the mapping GET and ride the CONNECTOR_MAPPING revision event (verified on dev by pulling the real message). Validated against types 10.3.0 MappingDictionariesSchema; uniqueness re-checked in validateMappingConfig because createOpenApiZodDto drops container refinements. openapi.yaml declares the field for fuse-ui. Found a pre-existing Collection.save() merge: a PUT omitting an optional nested field (dictionaries, columnOrder) keeps the old value; send [] to clear. Documented in CLAUDE.md, not fixed here.

PR: gfs-bifrost/config-service#224

## 2026-09-22 — FUSE-1190

Persist and validate Shopify stockSync on connectors

config-service was silently stripping the stockSync field @gfs-bifrost/types 10.2.0 already
added to ShopifyIngress/ShopifyIngressConfigService, since the create/update/response ingress
Zod schemas here didn't carry it — no connector could ever be made due for stock sync in any
environment, blocking end-to-end proof of the poller side (FUSE-1192/1193). Added stockSync to
the create/update paths (response covered for free via the shared base schema) with the
quarter-hour time-format check this repo is the only layer that enforces; the
enabled-requires-schedule cross-field rule validates post-merge, mirroring the existing
SFTP-activation check, so a partial update relying on an already-stored schedule isn't
incorrectly rejected. Verified live on dev end-to-end: the ticket's own named acceptance check
(dueConnectors flipping 0 -> 1 on the poller's next tick) confirmed.

PR: gfs-bifrost/config-service#221

## 2026-09-17 — FUSE-1167

confirmationsEnabled on business index

Surfaced confirmationsEnabled per-connector on GET /v1/business (+ /v1/business/:businessId) -- one line in businessInformationProjection's connector $map (mirrors the FUSE-1122 storeFrontsWithConnectorsProjection precedent). Closed a pre-existing openapi.yaml gap: CustomerInformationResponseDTO declared only businessId/friendlyName despite the API returning storefronts/connectors since FUSE-1064, which never touched the spec -- now both arrays are inlined (no reusable ConnectorRef component to $ref). Started as Structure B (no types-pin bump, relying on the projection's raw-aggregation/no-response-serializer decoupling -- see known-context.md#two-openapi-consumers) but ended as Structure A: bumped @gfs-bifrost/types ^9.2.2 -> ^10.1.0 once published, because /api/v1/docs/generated (the NestJS-generated Swagger, a SEPARATE consumer from openapi.yaml -- see known-context.md) needed the typed field via CustomerInformationResponseDTOSchema, not just the raw runtime response. Verified clean against the real published 10.1.0 (build:check, build:check:tests, 619/619 unit, 334/334 integration) -- the 10.0.0 major (FUSE-1164) is confirmed inert for this service. AC2 (storefronts/{id}/connectors unaffected) verified passive -- separate projection, findConnectorsWithStorefrontsPipeline, genuinely untouched. Sibling PR (types half): gfs-bifrost/pkg-node#225. Also found + fixed en route: 4 new HIGH dependency-audit/image-scan CVEs (js-yaml, multer) unrelated to this ticket, in gfs-bifrost/config-service#212. PR: gfs-bifrost/config-service#211.

## 2026-08-12 — FUSE-855

work_order ingress-mapping use case

Added work_order as its own dedicated lined ingress mapping (not piggybacked on the sales_order mapping) -- the DefaultMapping union, the lined-vs-simple validation allowlist, the connector-init skeleton, and openapi.yaml (WorkOrderDTO, the DefaultMappingDTO oneOf, the UseCase enum). POST/GET/PUT/DELETE /api/v1/storefronts/{storefrontId}/connectors/{connectorId}/mappings/work_order now accepts a lined config and rejects a simple one with InvalidMappingConfigException; GET /api/v1/connectors reports work_order in a connector's useCases when mapped, via the existing generic projection. Bumped @gfs-bifrost/types ^8.3.0 -> ^9.1.0.

PR: gfs-bifrost/config-service#197

## 2026-08-03 — FUSE-1025

Thread FGR + WOC egress mapping use cases through config-service

finished_good_receipt and work_order_confirmation joined the connector-mapping use cases (CRUD via POST/GET/PUT/DELETE .../mappings/{useCase}), lined-only like every other confirmation egress mapping, documented in openapi.yaml (new DTOs, DefaultMappingDTO oneOf, UseCase enum). Fixed a pre-existing bug affecting every lined use case (RGA, pick/pack, goods-in/out, not just the two new ones): InvalidMappingConfigException had no arm in the exception filter, so posting a simple config to a lined-only use case returned a generic 500 instead of the established 400 problem type -- an explicit acceptance criterion on both this ticket and FUSE-856. Retired the null-coalesce crutch in getConnectorWithBusinessId now that types 8.3.0 makes ConnectorDTOSchema's use-case keys optional rather than present-but-nullable -- GET /connectors/{id} now omits absent use-case keys rather than returning explicit null, a wire-visible but backward-compatible change (both were already falsy to every consumer). Derived UseCaseSchema, the mapping-response useCase enum, the four @ApiParam enums, stripUseCaseMappings() and both Mongo useCases projections from ALL_USE_CASES so adding a future use case is no longer a ten-file edit. Also delivers the config half of FUSE-856. Requires @gfs-bifrost/types ^8.3.0.

PR: gfs-bifrost/config-service#193

## 2026-07-06 — FUSE-954

columnOrder on connector mappings

Connector mappings can now accept, persist and serve an optional columnOrder: string[] on the Lined/Simple mapping schemas, riding the existing mapping POST/PUT routes and returned un-stripped on GET /connectors/{id} (#179). Shipped with an idempotent backfill script (migrate:column-ordering) deriving today's column order for existing confirmation-egress mappings so egress output stayed byte-for-byte unchanged on rollout; a follow-up (#180) scoped that backfill to the actual UI-configured confirmation keys (goods_in_confirmation, goods_out_confirmation, return_goods_confirmation -- not the RGA ingress key it had originally targeted) and excluded default-value keys from the derived order so the connector's own default-column append stays correct. A third PR (#182) then added columnOrder to the hand-maintained openapi.yaml (GroupedTranslatorConfig, SimpleMappingConfig, LinedMappingConfig) -- the earlier PRs had only reached the Zod-schema-generated spec, so fuse-ui's client codegen against openapi.yaml still couldn't see the field. Stayed on @gfs-bifrost/types ^6.3.0 throughout, threading columnOrder via local schemas rather than pulling in the unrelated 7.0.0 businessId-required major.

PR: gfs-bifrost/config-service#179
PR: gfs-bifrost/config-service#180
PR: gfs-bifrost/config-service#182

## 2026-06-23 — FUSE-794

Bifrost metadata + logger traceability

Config-service's slice of the FUSE-794 traceability rollout. PubsubHandler.publish now stamps source="config-service" on the config-revision BifrostMessageMetadata (connectorId/recordId/recordType deferred on this envelope -- config-revision fragments carry no single customer-facing record reference, and most FragmentTypes have no connectorId in scope). The winston requestMetadataFormat now spreads the full getCorrelationDetails() object under requestor on every log line instead of cherry-picking correlationId/user. CorrelationDetails gained optional businessId/source/flow/connectorId/recordType/recordId, and setCorrelationDetails became a no-op outside a cls-hooked context. The events controller now lifts the decoded SftpAuthStatusEvent context (source, flow="config", businessId, connectorId, correlationId) onto the namespace before delegating to the handler. Bumped @gfs-bifrost/types ^6.1.0 -> ^6.3.0.

PR: gfs-bifrost/config-service#172

## 2026-06-17 — FUSE-953

Dual-ship telemetry to ILG + right-size Datadog sidecar

Dual-ships config-service logs and metrics to the ILG Datadog org (alongside GFS) via the agent's DD_LOGS_CONFIG_ADDITIONAL_ENDPOINTS / DD_ADDITIONAL_ENDPOINTS, matching the rest of the fleet, and right-sizes the Datadog sidecar from 1 vCPU/512Mi to 0.5 vCPU/256Mi. Forward-ported Terraform that had merged to a stale master branch but never reached main; main's deploy workflow already passed datadog_api_key_ilg but config-service's Terraform never declared/used it. IaC-only, no app code. Salvage PR under FUSE-952 (main/master reconciliation); originally tracked as FUSE-953.

PR: gfs-bifrost/config-service#170

## 2026-06-12 — FUSE-811

Null-coalesce RGA use-case keys on GET /connectors/{id}

GET /connectors/{id} now always returns return_goods_authorization / return_goods_confirmation, with an explicit null when a connector document predates FUSE-811 adding those keys to createStorefront -- needed because ConnectorDTOSchema (types >=5.1) requires them as present-but-nullable, so remote-config consumers were rejecting every pre-existing connector once they picked up the new types. Follows the same in-code normalization pattern as the existing outboundTagsEnabled ??= false coalesce rather than a backfill migration, so it covers restores/imports too. Bumped @gfs-bifrost/types ^5.1.0 -> ^5.2.0 (ConnectorConfigService's use-case record now admits null, matching what Mongo actually stores).

PR: gfs-bifrost/config-service#166

## 2026-06-12 — FUSE-775

Stop connectors endpoints leaking _id and metadata

GET /api/v1/connectors and GET /api/v1/connectors/:connectorId were serialising raw Mongo documents, leaking the internal _id and audit metadata fields (the controller's DTO casts didn't strip anything at runtime). Fixed the $project stages in list-all-connectors and getConnectorWithBusinessId to drop metadata and _id, and inverted the old "version in metadata" integration test into a leak-regression assertion on both the list and single-GET endpoints.

PR: gfs-bifrost/config-service#164

## 2026-06-02 — FUSE-671

Require egressFiletype on SFTP connector config

Added a required egressFiletype field ("csv" | "jsonl") to SFTP connector config -- required on create, optional on PATCH (kept on omission via mergePartialUpdate), documented in openapi.yaml, and bumped @gfs-bifrost/types to ^4.2.0 for the canonical EgressFiletype type. Shipped with a one-off idempotent backfill script (migrate:egress-filetype) defaulting existing SFTP connectors missing the field to "csv", and a new 400 regression test for SFTP creation without egressFiletype. Part of the FUSE-725 cross-repo stack (pkg-node types -> config-service -> sftp-connector .jsonl writer -> fuse-ui toggle); deploy/migration had to land before sftp-connector's validation went live, and fuse-ui's SFTP creation would 400 until its own FUSE-672 follow-up shipped a UI default.

PR: gfs-bifrost/config-service#157

## 2026-03-03 — FUSE-624

Enable RESTful connectors

Added support for RESTful connectors -- a crypto library, types for REST connectors, and creation/fetch/update logic for them, verified via manual requests (create, fetch existing, update, updated connector reflected).

PR: gfs-bifrost/config-service#107

## 2026-02-11 — FUSE-703

Update SFTP connector data on user-creation message

Added an events controller and handling for user-creation events, updating SFTP connector data on receipt, with Terraform for the Pub/Sub subscription and the corresponding Nest wiring. Verified locally against a Pub/Sub push emulator for both the happy and error paths.

PR: gfs-bifrost/config-service#98

## 2026-01-28 — FUSE-102

Remove uniqueness requirement for snap shipment methods

Updated the PUT and DELETE shipment-method endpoints to accept arrays of shipment methods rather than a single method, changing the shipment-method structure accordingly, with tests updated to match.

PR: gfs-bifrost/config-service#88

## 2026-01-27 — FUSE-702

Emit backlink events on snap backends

Switched snap backend backlinks to read from @gfs-bifrost/types, and wired emission of backlink events on backend creation, deletion and update.

PR: gfs-bifrost/config-service#85

## 2026-01-27 — FUSE-701

Emit events on DDP rule config changes

Added event emission on DDP rule create/update/delete. Also migrated the repo's linting to biome and fixed type issues in the storefront controller as part of the same change.

PR: gfs-bifrost/config-service#84

## 2025-12-15 — FUSE-536

Warehouse routing logic (full CRUD)

Implemented full CRUD for warehouse routing rules (GET/POST/PUT/DELETE /api/v1/business/:businessId/warehouses/routing), denormalised onto the BusinessInformation document as a warehouseRouting field rather than a dedicated collection. Added a WarehouseRoutingService for the domain logic (business existence, conflict detection on create) plus updateWarehouseRoutingField/deleteWarehouseRoutingField on BusinessInformationService (the latter using Mongo $unset via a new unsetFields Collection method), and excluded warehouseRouting/ddpRules from the general business endpoints so they're only reachable via the dedicated routes. Also covers FUSE-535/537/538. Documented all four endpoints in the OpenAPI spec (200/201/400/404/409/500 + X-Resource-Version) with full service/controller test coverage (69 tests).

PR: gfs-bifrost/config-service#68

## 2025-12-15 — FUSE-496

Base DDP controller

Added a dedicated controller for DDP routes with an updatePartial method for denormalised types, centralised country-code logic, and new central types for DDP rules with DTOs based on them. Updated the OpenAPI schema and added an exception + handling path for consistent 501 responses.

PR: gfs-bifrost/config-service#67

## 2025-12-11 — FUSE-359

Base controller for warehouse routing

Added the base controller skeleton for warehouse routing.

PR: gfs-bifrost/config-service#63

## 2025-11-25 — FUSE-476

Retrieve connector by ID

Implemented GET /storefronts/:storefrontId/connectors/:connectorId to retrieve a single connector, covering existing connectors, public-key-authenticated connectors, and missing storefront/connector cases. Added ConnectorSummaryDTO and GetConnectorResponseDTO types and documented the endpoint in the OpenAPI spec.

PR: gfs-bifrost/config-service#45

## 2025-11-25 — FUSE-473

Delete storefront endpoint (cascading)

Implemented DELETE /api/v1/storefronts/{storefrontId}, cascading the delete to associated connectors and mappings and making the operation idempotent (repeat deletes don't error). Updated the OpenAPI spec and added unit tests covering cascading deletes and idempotence.

PR: gfs-bifrost/config-service#43

## 2025-11-24 — FUSE-408

Update mappings

Update mappings.

PR: gfs-bifrost/config-service#41

## 2025-11-24 — FUSE-406

Get connector mapping by storefront, connector and entity type

Added GET /api/v1/storefronts/{storefrontId}/connectors/{connectorId}/mappings/{entityType} to retrieve a single mapping configuration, documented in openapi.yaml. Changed getVersion() to return a string rather than a number.

PR: gfs-bifrost/config-service#40

## 2025-11-24 — FUSE-407

Add mappings to connector + DTO reorganisation

Restored POST /api/v1/storefronts/{storefrontId}/connectors/{connectorId}/mappings/{entityType} for creating custom connector mappings, with validation for simple and lined mapping configs and event dispatching via ConfigEventDispatcher on mapping changes. Removed useCases from the connector-create request DTO (defaults to an empty array in responses), and split the previously monolithic dto.types.ts/dto.schema.ts into per-domain storefront/connector/mapping files, moving request/response DTOs from the service layer to the controller layer to match the rest of the codebase.

PR: gfs-bifrost/config-service#38

## 2025-11-21 — FUSE-526

Connector controller skeleton

Added the connectors API skeleton -- GET /api/v1/connectors (query all connectors with optional type filter + pagination) and GET /api/v1/connectors/{connectorId}/mappings (fetch all mappings under a connector) -- both returning 501 pending real implementation. Introduced ConnectorsController/ConnectorsService, schemas/types for the query params and responses, unit tests, and documented the new endpoints in the OpenAPI spec.

PR: gfs-bifrost/config-service#39

## 2025-11-10 — FUSE-42

Business information GET and DELETE endpoints

Implemented GET and DELETE for business information (FUSE-423, FUSE-425), with unit tests for both. Added a getVersion utility to read the metadata version off a record and refactored controllers to use it instead of ad hoc version-header logic.

PR: gfs-bifrost/config-service#31

## 2025-11-10 — FUSE-344

Delete shipment method endpoint

Added the shipment-method deletion endpoint. Also fixed the docker-compose setup for local testing (no topics configured locally means a roughly one-second delay between request and response).

PR: gfs-bifrost/config-service#30

## 2025-11-05 — FUSE-470

Create storefront endpoint

Implemented the create-storefront API endpoint via a new StorefrontService, with business-ID and request-body validation, a storefronts database collection, error handling for non-existent businesses, and a 201 response carrying the created storefront plus an X-Resource-Version header. Documented the endpoint in the OpenAPI spec with fixtures/tests.

PR: gfs-bifrost/config-service#26

## 2025-11-04 — FUSE-375

Storefront and connector API endpoints and schemas

Added the storefront/connector management surface under /api/v1/storefronts/{storefrontId} and /api/v1/business/{businessId}/storefront -- a StorefrontsController (GET/PATCH/DELETE storefronts, POST/GET/PATCH/DELETE connectors) backed by a new StorefrontService, with Zod DTO schemas for storefront/connector requests and responses. Added CreateStorefrontRequest/UpdateStorefrontRequest/CreateConnectorRequest/SFTPIngress/ShopifyIngress models with their auth methods, basic businessId/body validation on the business controller (returning 501 for unimplemented routes), and updated openapi.yaml.

PR: gfs-bifrost/config-service#23

## 2025-11-03 — FUSE-341

Get shipment methods endpoint

Implemented GET /api/v1/snap/shipment_methods/:businessId, fetching ShipmentMethod records from the configuration store and returning 404 when none exist for the business. Added a ShipmentMethodsService for the fetch/parse logic and a buildDbResponse fixture (refactoring existing business-information/custom-mapping/default-mapping/shipment-method fixtures onto it), plus unit and controller tests.

PR: gfs-bifrost/config-service#22

## 2025-11-03 — FUSE-426

Update business information endpoint

Implemented PUT /:businessId to update business information -- 200 with the updated record and X-Resource-Version header on success, 404 if the business doesn't exist, 400 for invalid bodies/IDs. Added request-body and businessId validation, unit tests, and a beforeEach mock-clear to the business controller spec.

PR: gfs-bifrost/config-service#21

## 2025-11-03 — FUSE-424

Create business information endpoint

Implemented POST business-information creation: 201 on success, 400 on validation errors, 409 when the business already exists.

PR: gfs-bifrost/config-service#20

## 2025-11-03 — FUSE-422

Fetch-all business information endpoint

Implemented the GET / endpoint returning a paginated list of businesses (offset/count query params) via a new BusinessInformationService. Added DTO types for business information and paged API responses, fixtures/tests covering pagination, and removed the X-Resource-Version header from the OpenAPI spec for this endpoint.

PR: gfs-bifrost/config-service#19

## 2025-10-30 — FUSE-239

Custom user mappings API + connector type support

Implemented the custom user mappings endpoints (GET /api/v1/mappings/:businessId, GET/POST/PUT .../:entityType) with a new UserMappingsService/controller, schemas and types, moving shared mapping-related files into src/core/mappings; the backend config schema was updated to require at least one storage backend configuration (PR#13). Follow-up PR#17 then added connectorType to the endpoint path (/api/v1/mappings/{businessId}/{connectorType}/{entityType}) with a new ConnectorType enum (shopify, sftp), updated request/response schemas, and 501 responses documented in the OpenAPI spec.

PR: gfs-bifrost/config-service#13
PR: gfs-bifrost/config-service#17

## 2025-10-30 — FUSE-414

Business Information API endpoints

Added the /api/v1/business endpoints (GET list, GET by ID, POST, PUT, DELETE) with a BusinessController, BusinessInformationService, and DTO schemas (CreateCustomerInformationDTO, CustomerInformationResponseDTO, PagedBusinessInformationResponse). Introduced BusinessIdSchema restricting business IDs to uppercase alphabetic characters, added initial validation/"Not Implemented" tests, and documented the new endpoints in openapi.yaml.

PR: gfs-bifrost/config-service#18

## 2025-10-23 — FUSE-340

Snap shipment method route stubs + schema

Added base routes under /api/v1/snap/shipment_methods (GET/POST/PUT/DELETE) via a new ShipmentMethodsController, returning 501 until real logic lands. Defined the ShipmentMethod Zod schema/validation type and added the X-Resource-Version header to API responses for translator config, user mappings, shipment methods, user backends and business ingresses.

PR: gfs-bifrost/config-service#16

## 2025-10-22 — FUSE-233

Make config service publicly available with API key auth

Added API key authentication middleware (AUTH_ENABLED / AUTH_API_KEY env vars) gating all routes except the public GET /health check, plus rate-limiting on authenticated routes and RFC 9457 problem responses for 401/429. Terraform sets up a load balancer, static IP and DNS to expose the service over the internet, with the API key generated via a CSPRNG and stored in Secret Manager for Cloud Run to read.

PR: gfs-bifrost/config-service#15

## 2025-10-21 — FUSE-236

Emit backlink events on snap binding create/replace

Wired snap-instance-binding creation/replacement to emit a dispatchSnapBinding event on success, with tests verifying the event fires correctly from the controller. Fixed the controller to return correct HTTP status codes for success/conflict/not-found, and switched mockResponse.send to mockResponse.json in tests to better reflect the real response type.

PR: gfs-bifrost/config-service#14

## 2025-10-20 — FUSE-237

Emit config events on default mapping changes

Wired default-mapping create/update logic to the config event dispatcher so subscribers see mapping changes. The collection save method was changed to return the entire persisted object (needed to get hold of metadata/version for the event) rather than just to/from, and the event dispatcher now emits the whole mapping rather than just the to/from pair so subscribers know which mapping changed. Registered the dispatcher in the dependency registry.

PR: gfs-bifrost/config-service#11

## 2025-10-16 — FUSE-355

Backend configuration API route stubs

Added base routes under /api/v1/backend (POST/PUT/GET/DELETE /api/v1/backend/:businessId) returning 501 Not Implemented, with a BackendConfigController, BackendConfigService and Zod backendConfig schema (including a SNAP config sub-schema). Updated the OpenAPI spec to reflect storage as an array.

PR: gfs-bifrost/config-service#10

## 2025-10-15 — FUSE-396

Document skeleton config-service API surface

Updated the OpenAPI spec to document the config-service skeleton routes (mappings, default mappings, snap shipment methods, backends, business ingresses) so consumers could start building against them ahead of real implementations. Modified Snap Instance API endpoints to use schema objects.

PR: gfs-bifrost/config-service#9
