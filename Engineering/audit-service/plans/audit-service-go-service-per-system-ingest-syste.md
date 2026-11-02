---
ticket: none
title: 'audit-service: Go service, per-system ingest, system-scoped read API, legacy
  import'
service: audit-service
status: complete
created: '2026-10-12'
updated: '2026-10-12'
repo: /home/hjf/code/fuse/audit-service
worktree: /home/hjf/code/fuse/audit-service/.claude/worktrees/service-skeleton
branch: hjf/service-skeleton
base: origin/main
base_sha: b0f547105
pr: '9'
tags:
- waypoint
- plan
programme: Audit Service
unit: UE
impl_model: opus
impl_effort: high
---
# none — audit-service: Go service, per-system ingest, system-scoped read API, legacy import

<!-- Guidance in this file is written as HTML comments: Obsidian hides them, agents read them,
     and `wp signoff` ignores them. Only <angle spans> are treated as unfilled placeholders, so
     they mark the places a human or agent must actually type something. Leave the comments in
     place — deleting them costs the next reader the guidance and gains nothing at the gate.

     SUPERSEDING A STATEMENT. This file is edited by several sessions over days. When something
     here stops being true, do NOT strike it through, delete it, or bury a correction inside it.
     Put one blockquote immediately ABOVE the stale text and leave the text alone:

         > SUPERSEDED 2026-09-04 — the monitor now lives in `gfs-bifrost/observability`.
         > Everything below is kept as the record of how it was first built here.

     One marker, always above, never inside. `wp decide` writes the dated entry in
     `## Decisions & deviations` that explains why. -->

## Intent
<!-- What we are changing and why. Link the ticket. -->
This is unit UE of the [[Audit Service/Migration State|Audit Service]] programme. It is out-of-ticket work; the nearest epic is FUSE-980.

The change builds `gfs-bifrost/audit-service`, a private Go Cloud Run service that owns the audit store. It ingests `AuditMessage`s (`@gfs-bifrost/audit` 0.1.0) from one push subscription per system topic (`audit.<env>.fuse.v1` today), writes them idempotently into its own Atlas cluster, and serves a system-scoped, cursor-paged read API to allow-listed callers. It also ships the legacy import tool that the fuse-ui cutover runs.

Proof that it worked: in dev and prod, a published Fuse message lands exactly once and reads back through the API with the fuse-ui SA's token, and an unauthorised token gets 403.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. The service is private in both envs: an ID token for an allowed caller gets 200 on `/api/v1/health`, and an unauthenticated call gets 403 from Cloud Run.
- [x] 2. The Go envelope is generated from `@gfs-bifrost/audit` with `make gen`, and `gen-check` fails CI when the generated code is stale.
- [x] 3. An `AuditMessage` published to `audit.<env>.fuse.v1` is stored exactly once under `_id = eventId`, with `receivedAt` stamped. A redelivery creates no second row. A message whose `system` doesn't match its topic, or that fails the envelope, is acked and counted, not stored. A store failure is redelivered, and dead-letters after 5 attempts.
- [x] 4. `GET /api/v1/systems/{system}/events` filters by tenant, target, actor, kind, action and time, pages by cursor, newest first, caps `total`, and never returns `null` for an empty list. `/events/{id}` and `/filter-options` work. Only allow-listed callers reach `/api/v1`, and only the push SA reaches `/events/v1`.
- [x] 5. `cmd/import-legacy` copies fuse-ui `audit_log` rows into `AuditMessage` form, keeping the ObjectId hex as the id. It is idempotent (a rerun inserts 0) and `--verify` reports missing ids.
- [x] 6. Metrics exist for ingest outcomes, and monitors in `gfs-bifrost/observability` alert on dead-letter backlog and push 5xx.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- **New repo `gfs-bifrost/audit-service`.** It is a Go module at `code/` (the org layout, not tracking's `apps/`), with these packages: `cmd/api`, `cmd/import-legacy`, `internal/{config,bootstrap,http/{controllers,middleware,respond},core,repositories,models,observability}`.
- **IaC `iac/projects/audit-service`:**
  - private Cloud Run with the Datadog sidecar;
  - SAs for the API and the push invoker;
  - an Atlas cluster (prod M10, dev Flex);
  - one push subscription per system, dead-lettering to bifrost-pubsub's module `.dlt`, with a hold subscription and service-agent grants;
  - an `api_extra_invokers` list.
- **Contracts:**
  - `@gfs-bifrost/audit` `AuditMessage` (codegen source);
  - bifrost-pubsub outputs `audit_fuse_topic_{id,dlt_id}`, read from the env-matched state bucket;
  - the read API `openapi.yaml`, which fuse-ui copies in UF.2.
- **Shared org secrets:** `MONGO_ATLAS_{PUBLIC,PRIVATE}_KEY`, `DATADOG_API_KEY(_ILG)` and `GH_TOKEN`, all visible to the repo already.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **Precedents:**
  - fuse-mocker `apps/api` for the Go layout, Mongo repositories, observability and canonschema codegen.
  - tracking-service for private Cloud Run, OIDC push, the dead-letter hold and the dev→prod deploy workflow. Its own stack is not yet applied, so the prod path is proven here for the first time.
  - Source: reads of both repos' `origin/main` on 2026-10-12.
- **Bootstrap needs:** the Artifact Registry repos `gfs-bifrost-{dev,prod}` and the WIF providers are shared, and the org secrets above are visible to `audit-service` (`gh api …/organization-secrets`), so no manual GCP or GitHub bootstrap is needed. Source: checked.
- **Codegen auth:** codegen installs `@gfs-bifrost/audit` from GitHub Packages with `GH_TOKEN`, as wms-gateway does. This contradicts the PAT-retirement direction (per-package grants plus `github.token`), but those grants are UI-only and I can't set them. Recorded as debt.
- **Retention:** forever (G5), so there is no TTL index.
- **Authorisation:** Cloud Run IAM does the coarse gate. The app re-verifies the Google ID token's `email` claim per route group, against the push SA for `/events/v1` and against `READ_CALLERS` for `/api/v1`.

## Increments
<!-- Each independently implementable AND verifiable. Cite the criteria it discharges as
     (AC n,n). Tick with `wp tick`, which stamps `— done: <sha>` from HEAD; never hand-write it.
     Prefer 3-7 — more usually means the ticket is too big, so say that rather than splitting
     hairs.

     A PRECONDITION THAT IS NOT CODE goes on its own indented `gate:` line, with a confirmation
     box under it. Sign-off blocks on a ticked increment sitting above an unconfirmed gate, and
     `wp brief` shows unmet gates in its NEXT block — so "do not action this yet" stops being
     bold prose a fresh session can miss:

         - [ ] 6. Widen the subscription filter (AC 6) — verify: filter matches in dev
               gate: FUSE-1052 AND FUSE-1053 confirmed in prod
                     [ ] confirmed
-->

- [x] 1. **Skeleton and private Cloud Run.** (AC 1) — audit-service#1 merged; dev+prod: health 403 without token, 200 with ID token — done: 6505c4e
      - App: config, observability (slog JSON to the Datadog sidecar), recover/correlation/logger middleware, `GET /api/v1/health`.
      - Build and CI: Dockerfile, Makefile gates, code-quality, secops, tf-plan, and a deploy workflow (dev apply, then prod plan and prod apply behind `terraform-prod`).
      - IaC: Cloud Run with the API SA and no public invoker. (AC 1)
      - verify: `make fmt-check vet test-race lint` pass; after deploy, in dev and prod, an ID-token curl to `/api/v1/health` returns 200 for an allowed principal and 403 without a token.
- [x] 2. **Contract codegen.** `tools/auditschema` imports `@gfs-bifrost/audit`, runs `z.toJSONSchema` and then go-jsonschema into `internal/models/audit`. Adds `make gen` / `gen-check` and a CI job. (AC 2) — verify: gen-check is green in CI, and a Go test decodes a Fuse `config_change` message into the generated type. — audit-service#2: gen-check green in CI; decode tests (fuse config_change, missing system rejected, unregistered kind accepted) — done: 09aa0df
- [x] 3. **Atlas, ingest and subscriptions.** (AC 3) — audit-service#3 (infra) + #4 (ingest); dev: stored, duplicate, system_mismatch; prod: system_mismatch acked, DLT empty — done: b51b2b1
      - Atlas cluster, user and connection string.
      - Ingest at `POST /events/v1/audit/{system}`. Outcomes: decode + validate → system-match check → insert with `_id = eventId` + `receivedAt`. A duplicate returns 204; a poison message returns 204 plus a metric; a store error returns 500.
      - Indexes leading on `system`.
      - One push subscription per system with OIDC, a dead-letter policy to the module `.dlt`, a hold subscription and grants.
      - (AC 3)
      - gate: bifrost-pubsub#15 applied in dev and prod
            [x] confirmed
      - verify: unit tests for each ingest outcome; a real-Mongo round trip with nested `details` arrays; in dev, publishing the same message twice gives `countDocuments({_id})` = 1, and a mismatched `system` isn't stored.
- [x] 4. **Read API and caller auth.** `/api/v1/systems/{system}/events` (filters, cursor, capped total), `/events/{id}` and `/filter-options`; `openapi.yaml`; `READ_CALLERS` and `api_extra_invokers` set to the fuse-ui-dev and fuse-ui-prod SAs. (AC 1,4) — verify: handler and store tests for each filter, cursor continuation, the cap and an empty `[]`; in dev, an impersonated `fuse-ui-dev` SA reads the UE.3 row and the push SA gets 403 on `/api/v1`. — audit-service#6; dev: allow-listed SA token reads list/get/filter-options, non-listed 403, other system []; prod read verified by fuse-ui in UF.2 — done: 0109873
- [x] 5. **Legacy import tool.** `cmd/import-legacy --source-uri --source-db [--dry-run|--verify]` maps eras E1–E5 to `AuditMessage` (kind inference, `businessId` → `tenantId`, `sourceIp` → `actor.ip`, `_id` = `eventId ?? ObjectId hex`) and inserts if absent. (AC 5) — verify: tests per era against a real Mongo; a rerun inserts 0; `--verify` reports seeded missing ids. The real runs are the UF rollout steps, done by a human. — audit-service#7; era tests + Mongo idempotency/verify tests; dev dry-run over real fuse-ui audit_log: 702 read, 0 failed, nothing written — done: 8650661
- [x] 6. **Metrics and monitors.** `fuse.audit.ingest` tagged by `outcome`/`system`/`kind`; monitors in `gfs-bifrost/observability` on dead-letter backlog > 0 and push 5xx. (AC 6) — verify: the series exists in dev after a test publish, and the monitors exist in Datadog. — observability#64 applied (9 add, 1 change, 0 destroy); dev rejected-messages monitor OK→Alert in ~66s after a wrong-system publish — done: ddefd56
      gate: gfs-bifrost/observability#64 applied (2026-10-12: 9 added, 1 changed, 0 destroyed; shipped #61 too; UI threshold 18 codified first)
            [x] confirmed

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-12 [AC 2] `gen-check` fails on stale output: staging a hand-edited `internal/models/audit/gen_audit_message.go` (as a stale commit would be in CI) and running `make gen-check` exited **2** with `generated models are stale: run 'make gen' and commit the result`. Restored afterwards.
- 2026-10-12 [inc 6, AC 6] gfs-bifrost/observability#64 merged (`8417a5b`) and applied to Datadog: `9 added, 1 changed, 0 destroyed`. Monitors 331473607 (rejected, prod), 331473608 (rejected, dev), 331473609 (dead-lettered), 331473610 (5xx). **Fired:** a `system: monitor-proof` message published to `audit.dev.fuse.v1` at 12:56:07Z took the dev monitor from OK to **Alert at 12:57:13Z**, and it **recovered to OK at 13:12:23Z** once the 15-minute window passed. The apply also shipped #61 (stock-sync monitors); the live `snap_poller_businesses_skipped` settings (18, `show_no_data`) were codified first, and stayed unchanged after the apply.
- 2026-10-12 [inc 6, partial] audit-service#8 (`9fc4302`) adds `fuse.audit.ingest{system,outcome,kind}`, and #9 (`ddefd56`) flushes it per request. After #9, Datadog shows `fuse.audit.ingest{environment:dev}`: `stored` 2 and `system_mismatch` 1, from dev smoke publishes. Monitors are in gfs-bifrost/observability#64 (plan: the 4 audit-service monitors and 3 catalog entities are created), **not applied**; see the gate.
- 2026-10-12 [inc 5, AC 5] audit-service#7.
  - **Mapping tests:** 8, covering eras E1–E5, the minted-id preference, ObjectId preservation, and rejection of a row with no performer.
  - **Mongo tests:** an import then a rerun inserts 3, then 0; a dry run stores nothing; `--verify` names exactly the deleted row; imported rows read back through `Get` with tenant and kind.
  - **Read-only dry run** against **fuse-ui dev's real `audit_log`** (`fuse-ui-app` db), into audit-service dev: `read 702, inserted (would) 702, failed 0, present 0`. Nothing was written to either side.
- 2026-10-12 [inc 4, AC 1,4] audit-service#6 (`0109873`; Deploy run 38238541833, prod plan 1 add (fuse-ui-prod invoker), 1 change).
  - **Dev, guard:** with an SA token minted for the service URL, `/api/v1/systems/fuse/events` returned **403 "caller not allowed"** while that SA wasn't in `READ_CALLERS`.
  - **Dev, reads:** with the SA temporarily added to `READ_CALLERS`:
    - `?tenantId=HJF&limit=1` returned the UE.3 event `fe4c3c25-…`, with `kind: config_change`, `details.before.rules: [[1,2]]` intact, `receivedAt` stamped, `total: 1`, `totalCapped: false` and `nextCursor: null`;
    - `GET …/events/{id}` returned **200**;
    - the system-mismatched event returned **404**, because it was never stored;
    - `/systems/other/events` returned `{"events":[],"nextCursor":null,"total":0,…}`;
    - `/filter-options` returned `{"actors":["ue3-smoke"],"tenants":["HJF"]}`.
  - **Reverted** afterwards: `READ_CALLERS` is back to fuse-ui-dev only, and the temporary token-creator grant is removed.
  - CI: 14/14 (first tf-plan run hit a state-lock race with the concurrent #4 deploy; a rerun passed).
- 2026-10-12 [inc 3, AC 3] audit-service#3 (infra, `adabffe`; Deploy run 38235139543, prod plan 9 add, 1 change, 0 destroy, including the M10 with termination protection) and #4 (ingest, `b51b2b1`; run 38237510057). Both subscriptions dead-letter to `audit.<env>.fuse.v1.dlt` and push to `/events/v1/audit/fuse`.
  - **Dev:** published event `fe4c3c25-…` twice and `3f93db0a-…` with `system: other` to `audit.dev.fuse.v1`. The Cloud Run logs show `stored`, then `duplicate`, then `system_mismatch` (ack'd without storing).
  - **Prod:** published only a system-mismatched message (`0683c944-…`), so no synthetic row is stored forever. It was logged as `system_mismatch`, which proves OIDC push auth and the ingest path in prod.
  - Dead-letter holds were empty in both envs.
  - CI: 14/14, including the Mongo job. `make test-mongo`: one row after a double insert; int32 values and nested arrays round-trip.
- 2026-10-12 [inc 2, AC 2] audit-service#2 (`09aa0df`): the `Generated Models` CI job ran `make gen-check` green, installing `@gfs-bifrost/audit` 0.1.0 with `GH_TOKEN`. Tests: a Fuse `config_change` decodes into `AuditMessageJson`, a missing `system` is rejected, and an unregistered kind decodes. Deployed to dev and prod (prod plan 1 in-place change).
- 2026-10-12 [inc 1, AC 1] audit-service#1 (`6505c4e`) was deployed by Deploy run 38231168696. Dev applied; prod was approved after a plan of 2 add, 0 change, 0 destroy. `curl $URL/api/v1/health` returned **403** without a token and **200** `{"status":"ok"}` with `gcloud auth print-identity-token`, on both `audit-service-dev-j677gxplja-nw.a.run.app` and `audit-service-prod-6cprbzyuka-nw.a.run.app`. PR CI: all 12 checks green (quality, secops ×5, tf plan).

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- AC 3, store failure → dead letter after 5 attempts: covered by the subscription's `max_delivery_attempts = 5` and the unit test that a store failure returns 500. Not induced live (it needs Atlas made unavailable).
- AC 4, only the push SA reaches `/events/v1`: covered by `RequireCaller` tests and Cloud Run IAM. Not exercised live with a second invoker's token.
- Prod reads with an allow-listed caller: deliberately not exercised (I didn't touch prod IAM). The first real prod read is fuse-ui-prod's in UF.2.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-12** — Shipped as eight squash-merged PRs, not one branch: audit-service #1 skeleton, #2 codegen, #3 infra + #4 ingest (a stack, split for size), #6 read API, #7 legacy import, #8 metrics, #9 per-request metric flush. Frontmatter branch names #1's; pr records the last. Monitors shipped separately as gfs-bifrost/observability#64.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
(none)

