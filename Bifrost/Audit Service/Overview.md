---
title: "Audit Service — Overview"
status: active
verdict: go
owner: "hjf"
services: ["fuse-ui", "pkg-node", "bifrost-pubsub", "sftp-connector", "audit-service"]
created: "2026-10-09"
updated: "2026-10-12"
tags: [bifrost]
---
# Audit Service — Overview

<!-- The narrative and the verdict. PROGRESS lives in the Migration State doc, not here — link it,
     never duplicate its ledger. This doc changes rarely; the state doc changes every session. -->

## Deliverables
- [[Audit Service/Migration State|Migration State]]: the live source of truth for progress.
- New repo `gfs-bifrost/audit-service`: a Go service that owns the audit store, ingest and read API.
- New package `@gfs-bifrost/audit` in pkg-node: the audit event contract and a producer publisher.
- fuse-ui: writes and reads audit through the service, and the `audit_log` collection is retired.
- sftp-connector: the first producer that isn't the UI.
- Out-of-ticket work. No Jira ticket; nearest epic is FUSE-980 (audit log, platform-wide).

## Verdict
**Go** (Harry, 2026-10-12). Gates G1–G5 are cleared; see the State doc's decision log. The intent is
fixed (Harry, 2026-10-09):
- Other services report audit events into one standalone Go service.
- The service owns its own datastore, and fuse-ui's `audit_log` history is migrated into it.
- fuse-ui keeps writing and keeps the browse UI, but through the service.

## Why this needs a programme
It spans five repos plus a new one. Every merge in those repos applies to prod; there is no dev-only
merge. Several pieces of shared state git doesn't own are involved: a Pub/Sub topic, an Atlas
cluster, IAM grants, package access grants and Datadog monitors. The fuse-ui cutover has a one-way
door. The migrated data includes full config snapshots carrying connector credentials.

## Strategy

### 1. Fix fuse-ui first (UA)
The reviews found existing prod bugs that don't depend on the split, so they ship first:
- Audit failures block or corrupt user-management actions.
- `templates.action.ts` fires its audit calls without awaiting them.
- `logAuditEvent` can be called from the client, so any session can forge rows.
- The read server functions have no admin guard.
- Snapshots reach the browser unmasked inside the RSC payload.

### 2. Contract (UC, UD)
- **Event contract.** `@gfs-bifrost/audit` holds the `AuditMessage` envelope in Zod, plus the per-kind
  `details` schemas and a publisher that never throws.
- **`AuditMessage` is a standard envelope of its own, deliberately not `BifrostMessage`** (G1). It
  may be used outside the Bifrost suite, so the envelope carries no Bifrost-specific field or
  vocabulary:
  - Fuse's `businessId` maps onto a generic tenant/scope field.
  - Fuse-specific kinds sit in the per-kind registry, apart from the envelope.
  - **Events are stored by system** (Harry, 2026-10-12), for extensibility; `fuse` is the first.
    Everything is scoped by system: `system` is required on every message, every index leads with
    it, and the read API is always system-scoped. Kind registries are per system.
  - The exact field names are settled when UC is planned.
- **Envelope fields:**
  - `schemaVersion`, `eventId`, `occurredAt`
  - `producer`: deliberately not `source`, which already means the ingress connector
  - `kind`, `action`, `target{entity,id}`
  - `actor{type,id,ip?}`
  - a required `system` (the reporting system; `fuse` today), then a generic tenant/scope field within
    that system (Fuse: `businessId`), and a required `correlationId`
  - `details`
- **Publisher:**
  - Bounded timeout.
  - Returns a result instead of throwing.
  - Emits no telemetry; the calling service emits `fuse.audit.publish_failed`.
- **Go side.** The service's `tools/auditschema` imports the package's Zod and runs `z.toJSONSchema`,
  then `go-jsonschema`. This is the same pattern as wms-gateway `canonschema`, and it is gated by
  `make gen-check`.
  - The package itself ships no JSON Schema artefacts.
  - Only the envelope is generated, and it must not be a root union, because canonschema emits an
    empty file for one.
- **Transport: one topic per system** (scaling review, 2026-10-12): `audit.<env>.<system>.v1`, so
  Fuse's is `audit.<env>.fuse.v1`. It's built with bifrost-pubsub's topic module (`domain = "audit"`),
  and the module's `.dlt` is the subscription's dead-letter topic.
  - Publisher IAM on each topic decides who may write as that system, so `system` is enforced rather
    than self-declared. audit-service rejects a message whose `system` attribute or body doesn't
    match its topic.
  - Each system gets its own quota, dead-letter topic and blast radius. Adding a system means one
    more topic, plus an entry in audit-service's subscription list.
  - Pub/Sub attributes are `auditKind`, `producer`, `system` and `schemaVersion`, never `recordType`.
> SUPERSEDED 2026-10-12: one topic per system replaces the single shared topic below.
- **Transport.** A single topic, `bifrost.<env>.audit_event.v1`, owned by bifrost-pubsub, is the only
  write path. Pub/Sub attributes are `auditKind`, `producer` and `schemaVersion`, never `recordType`.

### 3. The service (UE)
- **Runtime.** A private Cloud Run service running Go 1.26.9 or later. The same version is pinned in
  `mise.toml`, `go.mod`, CI and the Dockerfile.
- **Ingest.** A push subscription delivers to a route named under the `/events/v1/<domain>/<stage>`
  grammar. Events are idempotent on `_id = eventId`:
  - a duplicate returns 204;
  - a poison message returns 204 and emits a metric;
  - a store error returns 500, so Pub/Sub redelivers.
> SUPERSEDED 2026-10-12 — the subscription dead-letters to bifrost-pubsub's module `.dlt` (`audit.<env>.<system>.v1.dlt`); see audit-service `architecture.md`.
- **Dead-letter topic.** The subscriber owns it, following tracking-service, with explicit
  Pub/Sub service-agent grants. bifrost-pubsub's module `.dlt` is left unused.
  - This overrides the recorded preference for a manual retry budget
    ([[feedback_manual_retry_budget_over_pubsub_dlq]]). Audit has no failure topic to route to, and
    the dead-letter topic here only ever holds store outages, because poison messages are acked.
- **Store.** MongoDB Atlas. The query shape suits it: optional five-field filters, totals, `distinct`
  for the filter options, and large opaque before/after documents. Firestore has no `distinct` and a
  1 MiB document limit. fuse-mocker is the existing Go + Atlas precedent.
- **Store layout, scaled across systems** (scaling review, 2026-10-12):
  - **One `events` collection, with every index leading on `system`:**
    - `{system, occurredAt, _id}`
    - `{system, tenantId, occurredAt}`
    - `{system, target.type, target.id, occurredAt}`
    - `{system, actor.id, occurredAt}`
    - `{system, kind, occurredAt}`
    - `{system, action, occurredAt}`
  - **Sharding-ready:** `{system, …}` is shard-key-ready if one cluster ever isn't enough.
  - **`receivedAt` stamped at ingest,** next to the producer's `occurredAt`.
- **Read API v1, always system-scoped** (`/api/v1/systems/{system}/…`):
  - `GET /events` takes the filters plus `limit` and a **cursor** on `(occurredAt, _id)`, sorted
    newest first. It returns `{events, nextCursor, total}`, where `total` is capped (`totalCapped:
    true` past 1,000) so a count never scans forever-retained history.
  - `GET /events/{id}` returns a single event.
  - `GET /filter-options?tenantId=` returns the distinct actors and tenants.
  - fuse-ui moves from page numbers to next/previous over the cursor in UF.2.
> SUPERSEDED 2026-10-12: store layout and cursor paging replace the offset-paged read API below.
- **Read API.** Always scoped to one system, e.g. `GET /api/v1/systems/{system}/events`; the exact
  shape is settled in UE.
  - `GET /api/v1/events` (offset paging plus `total`), `/events/{id}`, `/filter-options`.
  - Slices always encode as `[]`, never `null`.
  - `details` is normalised out of `bson.D`/`bson.A` in the store layer.
- **Auth.** Cloud Run IAM, plus in-app ID-token checks per route: ingest accepts only the push SA,
  reads only an allow-list.
  - The in-app check has no precedent; tracking relies on IAM alone.
  - fuse-ui reaches the service through a tfvars URL and a static invoker list, the tracker pattern,
    rather than remote state, which is the dedupe trap.
  - Preview envs get no audit, as with the tracker. `extractClientIp` can also be spoofed there,
    because previews have no load balancer.

### 4. Rollout order (agreed 2026-10-12)
1. **Build the service first, in its own repo:** UB, then UC, UD and UE, all in prod before fuse-ui
   changes anything. UA (hardening) runs alongside it, because UA's server-only writer is the seam
   dual-publish plugs into, so it must land before UF.1.
2. **UI dual-publishes** (UF.1, `AUDIT_SINK=both`). fuse-ui mints `eventId` and stores it on the Mongo
   row, then publishes the same id. Reads stay on Mongo. The read client (UF.2) is built behind
   `AUDIT_READ_SOURCE` during the soak, but stays off.
3. **Cutover, then migrate.**
   - **One deploy flips both flags:** `AUDIT_SINK=service` and `AUDIT_READ_SOURCE=service`. Mongo is
     frozen from that moment.
   - **One migration run follows immediately.** Converting legacy rows to the `AuditMessage` format
     involves:
     - mapping eras E1–E5;
     - mapping `businessId` to the tenant field;
     - mapping `sourceIp` to `actor.ip`;
     - setting `_id = row.eventId ?? row._id.toHexString()`, so old `?change=<ObjectId>` links still
       resolve.
   - **One run is enough because Mongo is frozen.** It copies every Mongo-only row, including any
     publish that failed during dual-publish. It skips rows that already exist, which makes it
     idempotent. There is no catch-up import.
   - **Human-run.** A dry run before cutover and the real run straight after, both run by a person.
   - **Accepted costs:**
     - Old history is missing from the UI for the few minutes the migration takes; announce it.
     - Once cut over, rolling back to Mongo reads hides post-cutover events, so it is fix-forward
       only. The cutover deploy is **the one-way door**.
4. **Remove the Mongo path** (UF.3). **Drop the collection** after the G6 hold (UH).
- The whole sequence is rehearsed end to end in dev first (dual-publish → cutover → migrate → verify).

> SUPERSEDED 2026-10-12: replaced by the rollout order above (service first; cutover then a single
> migration; no import during dual-write and no catch-up import). Kept as the original draft.
### 4. Cutover (UF)
1. **Dual-write** behind `AUDIT_SINK=mongo|both|service`. fuse-ui mints `eventId` and stores it on the
   Mongo row, then publishes the same id.
2. **Idempotent legacy import.** `_id = row.eventId ?? row._id.toHexString()`, so old
   `?change=<ObjectId>` links still resolve.
   - It handles row eras E1–E5 (see Scar tissue) and maps `sourceIp` → `actor.ip`.
   - It is human-run, dry-run first.
3. **Flip reads** behind `AUDIT_READ_SOURCE`.
4. **Soak.**
5. **Catch-up import**, to recover any publishes that failed during dual-write.
6. **`AUDIT_SINK=service`.** This is **the one-way door**: from here a failed publish is a lost event.
7. **Delete the Mongo path.**
8. **Drop the collection** after the G6 hold.

### 5. More producers (UG and follow-ups)
- sftp-connector emits user-lifecycle events from Cloud Run (UG). This needs no VM change.
- SFTP logins come first from a log sink on the systemd-logind session lines, which **already reach
  Cloud Logging**. This needs no VM change either.
- Source IP and failed attempts need Ops Agent on the fragile VM, so that waits for a runbook and an
  owner (G7).
- Other producers, such as fuse-mcp mutations, need a real user identity first. dedupe-service and
  config-service only see a shared key or `"admin"`. Mutations made through fuse-ui are already
  audited with the session.

## Unit outlines (material for promotion; the ledger holds progress)

**UA fuse-ui audit hardening**: promoted 2026-10-09 to
[[Engineering/fuse-ui/plans/harden-the-audit-log-non-blocking-writes-closed-|the fuse-ui plan]].

**UB repo bootstrap** (github-config, plan-less)
- `modules/repository` creates `gfs-bifrost/audit-service` along with its `terraform-dev` and
  `terraform-prod` envs. wms-gateway is the precedent; tracking-service is not managed by
  github-config.
- WIF is org-wide.
- Package access goes through per-package *Manage Actions access* grants plus `github.token`, never
  a PAT ([[project_pat_retirement]]). The grants cover audit-service, fuse-ui and sftp-connector on
  `@gfs-bifrost/audit`.
- Atlas API keys are added as repo secrets.

**UC pkg-node `@gfs-bifrost/audit` 0.1.0**
1. Scaffold, envelope and `code-quality-audit.yaml`, which calls
   `node-run.yaml@hjf/node-run-pnpm-filter`. No publish job yet.
   - Verify: `tsc` passes, and a `z.toJSONSchema` emit of the envelope succeeds. No Zod schema
     tests ([[feedback_no_zod_schema_tests]]).
2. `details` registry for `config_change`, `user_change`, `credential_access`, `sftp_user` and
   `legacy`.
   - Verify: every kind emits JSON Schema; `npm pack --dry-run` shows the right contents.
3. Publisher subpath, plus the `publish-audit` job that publishes 0.1.0. Add the Package Changelog
   entry, and add `minimumReleaseAgeExclude` in the consumers.
   - Verify: mocked-topic tests for success, timeout, rejection and an invalid event (returns
     `{ok:false}` and nothing is published); `npm view @gfs-bifrost/audit@0.1.0`.

**UD bifrost-pubsub topic** (single PR)
- Add `audit.pubsub.tf` with `module "audit_fuse"` (`domain = "audit"`, `topic_name = "fuse"`), giving
  `audit.<env>.fuse.v1` and its `.dlt`, plus outputs in `audit.outputs.tf`.
- Verify: `gcloud pubsub topics describe audit.<env>.fuse.v1` and `….dlt` succeed in dev and prod.
  Both envs have an approval gate ([[project_bifrost_pubsub_deploy_gates]]).
- At sign-off, record the `AuditMessage` contract and the topic in fuse-mcp (`pubsub-topology.json`,
  `event-contracts.json`).

> SUPERSEDED 2026-10-12: per-system topic replaces the shared `audit_event` topic below.
**UD bifrost-pubsub topic** (plan-less, single PR, can run alongside UC)
- Add `audit.pubsub.tf` and outputs.
- Verify: `gcloud pubsub topics describe` succeeds in dev and prod. Both envs have an approval gate
  ([[project_bifrost_pubsub_deploy_gates]]).

**UE audit-service** (Go, `code/` layout, not `apps/`)
1. Skeleton, CI and private Cloud Run with IAM.
   - Verify: an ID-token curl to `/health` returns 200 for an allowed caller and 403 for anyone else,
     in dev and prod.
2. Contract codegen.
   - Verify: `gen-check` passes in CI; a Go test runs a fixture per kind and confirms an unknown kind
     is accepted and stored as-is.
3. Atlas cluster (dedicated; prod M10, dev Flex), ingest, the system-led indexes, and one push
   subscription per system, dead-lettering to the module's `.dlt`, with service-agent grants.
   Ingest rejects a `system` that doesn't match the subscription's topic. **No TTL index: data is kept forever** (G5).
   - gate: UD applied in dev **and** prod (the prod apply reads its outputs).
   - Verify:
     - Publishing the same event twice in dev leaves 1 document.
     - With the store forced down, the message lands on the dead-letter topic.
     - A real-Mongo round trip with nested arrays comes back as JSON, not `[{Key,Value}]`.
4. Read API and caller auth.
   - Verify: an impersonated fuse-ui-dev SA gets rows; your own token gets 403; filter and cursor
     paging tests pass; a capped total is returned past the cap; empty results are `[]`.
5. Legacy import tool with `--dry-run` / `--verify`.
   - Verify: against docker-compose Mongo seeded with E1–E5 fixtures, counts match, a rerun inserts 0
     and ids are preserved. The real runs are UF rollout steps.
6. Metrics plus monitors in `gfs-bifrost/observability`: dead-letter backlog, push 5xx,
   `unknown_kind`, `publish_failed`.
   - Verify: each series exists in dev; a forced dead-letter fires the backlog monitor.
> SUPERSEDED 2026-10-12 — retention is forever (G5), so there is no TTL increment.
7. TTL retention.
   - gate: G5
   - Verify: the `expireAt` index exists, and a backdated dev document expires.

**UF fuse-ui cutover**
1. Dual-write behind `AUDIT_SINK`.
   - Mint `eventId`, add `@google-cloud/pubsub` (plus `serverExternalPackages`), and wire the
     publisher.
   - Add the topic name and the publisher grant for `cloudrun_sa`, built by name, with no remote
     state.
   - Add a read-only Atlas user with `count = is_preview_env ? 0 : 1`.
   - dev is `both`; prod and previews stay on `mongo`. Ship as stacked PRs.
   - Verify: a dev edit gives a Mongo row with `eventId=E`, and `GET /events/E` returns it; with a bad
     topic the save still succeeds and the failure is logged.
2. Read client behind `AUDIT_READ_SOURCE`.
   - Generalise `id-token.ts`, add the `gen-audit-service-client` script, and map responses to
     `AuditLogView`.
   - gate: UE.4 is in prod and the fuse-ui prod SA is in its invokers.
   - Verify (in dev, after the rehearsal migration):
     - Page totals match Mongo for every filter.
     - `/changes` and connector history work, and an old ObjectId link resolves.
     - Take screenshots.
3. Remove the Mongo path, the flags and `AUDIT_LOG_RETENTION_DAYS`. Forever is now the intended
   retention, not a placeholder.
   - gate: prod cutover done and the migration verified with 0 missing.
   - Verify: after a dev edit, the `audit_log` count is unchanged and the row appears in the service.
- Rollout section (one tfvars PR or operator step per line, with a confirm box each):
  1. dev: `sink=both`, then soak. Every new row appears in the service under the same `eventId`.
  2. dev rehearsal of the cutover: one deploy with `sink=service` + `read=service`, then the migration,
     then `--verify` (0 missing, rerun inserts 0), and UI parity spot checks.
  3. prod: `sink=both`, then soak. Exit criteria: `publish_failed` = 0 and dead-letter = 0.
  4. prod: migration `--dry-run` against the live collection (human-run).
  5. prod cutover deploy: `sink=service` + `read=service` (**one-way door**; announce the short
     history gap).
  6. prod: run the migration (human-run), then `--verify` shows 0 missing.

> SUPERSEDED 2026-10-12: rollout re-ordered (cutover then a single migration). Kept as the original draft.
- Rollout section (one tfvars PR or operator step per line):
  1. dev import + verify
  2. dev read=service
  3. prod sink=both
  4. prod import (human-run) + verify
  5. prod read=service, then soak
  6. catch-up import
  7. prod sink=service (**one-way**). Exit criteria: `publish_failed` = 0, dead-letter = 0, verify
     shows 0 missing.

**UG sftp-connector user-lifecycle events**
- Emit from the `createCustomer` handler (`/events/v1/create_sftp_user`, after `provisionUser`). The
  `eventId` is deterministic, derived from the Pub/Sub message id. Add the publisher grant.
- Verify:
  - The event never contains `privateKey`.
  - A redelivered message still gives 1 row.
  - If the publish fails, the message is still acked and the user is provisioned once.
  - The row appears through the API.
- Caveat: manual `users.json` edits and the `sftp-partner-key` skill bypass this path. A "key set"
  event records what the app provisioned, not the VM's effective key set.

## Scar tissue
- **Every merge to main applies to prod** in fuse-ui, bifrost-pubsub, pkg-node (publish) and the new
  service. A gate that says "in dev" means nothing; gate on the prod apply.
- **Approving fuse-ui's prod gate ships everything on `main` since the live sha.** Check `git log`
  first, and cancel older parked runs afterwards.
- **Prod imports and backfills are run by a human, never an agent**, dry-run first (from Tracking
  Service).
- **Dead-letter IAM fails silently.** Grant the Pub/Sub service agent publisher on the dead-letter
  topic and subscriber on the subscription explicitly.
- **Audit row eras the import must handle:**
  - E1 (#111): `user` target, created/updated/deleted, no `businessId`.
  - E2 (#189): credential access; `businessId` is only in `details`.
  - E3 (#216): before/after snapshots. dev may hold phantom-diff branch rows from before `943ab9b`.
  - E4: template targets.
  - E5 (#298): `sourceIp`.
- **The masking boundary is load-bearing.** Snapshots carry credentials. Never log an event payload.
  Never return a snapshot to the client unmasked.
- **The `details` diff is recomputed from before/after in the drawer** (`diffConfig`), not from
  `changedPaths`. Any change to snapshots must keep "this secret changed" detectable.

## Candidate learnings (for other services' docs; not yet written anywhere)
- **Package Changelog gap.** The org changelog for `@gfs-bifrost/observability` stops at 1.2.0. 1.3.0 (`57dd442`) deprecated the fuse-ui metric catalogue, and 2.x is also missing.
- **`gfs-bifrost/pkg-go`** ("Core Bifrost packages for Golang") exists only as a README (github-config `ff99383`). It's a possible future home for a Go audit client.
- **github-config coverage.** tracking-service is not managed by github-config; wms-gateway and observability are.
- **wms-gateway gen-check** still wires the `GH_TOKEN` PAT, contrary to [[project_pat_retirement]].
- **config-service `known-context.md`** still says FUSE-980 has "no PR opened yet". It merged as FUSE-1138 (#216).

## Next
The service comes first. UB (repo bootstrap) and UC (package) start now, and UD (topic) can run
alongside them. UA runs in parallel and must land before UF.1. Drive this with `waypoint-programme`.
