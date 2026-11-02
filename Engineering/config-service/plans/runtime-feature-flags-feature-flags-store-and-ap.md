---
ticket: none
title: 'Runtime feature flags: feature_flags store and /api/v1/feature-flags routes'
service: config-service
status: complete
created: '2026-10-14'
updated: '2026-10-14'
repo: /home/hjf/code/fuse/config-service
worktree: /home/hjf/code/fuse/config-service/.claude/worktrees/runtime-feature-flags
branch: hjf/runtime-feature-flags
base: origin/main
base_sha: 63babd7
pr: '239'
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: medium
---
# none — Runtime feature flags: feature_flags store and /api/v1/feature-flags routes

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
config-service stores runtime feature flags in its own `feature_flags` collection and serves them on `/api/v1/feature-flags`, separate from customer config. This is phase 1, workshop action L3 (no ticket yet). Flag writes publish nothing: evaluators pull a snapshot that refreshes on a TTL. The shared design and the rejected options are in [[runtime-feature-flags-types-featureflagschema-an]]. Done when dev and prod serve the five operations with unique keys and optimistic concurrency, which [[runtime-feature-flags-audited-flag-page]] then drives.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. `GET /api/v1/feature-flags` returns `200 { flags: [...] }` with the API key and 401 without it. `GET /api/v1/feature-flags/{key}` returns the flag, or 404.
- [x] 2. `POST` creates a flag (201, version 1) and returns 409 for a key that already exists. A unique Mongo index enforces key uniqueness.
- [x] 3. `PATCH /{key}` applies a partial update, and a stale `expectedVersion` returns 409. `DELETE /{key}` hard-deletes, and a later GET returns 404.
- [x] 4. A body with an unknown `targets` key (e.g. `businessId`) or an unknown top-level key returns 400 and is not persisted.
- [x] 5. `/api/v1/docs-json` and the committed `openapi.yaml` both describe the five operations.
- [x] 6. Customer-config routes and the `config_revision` publish behave exactly as before. Flag writes publish nothing.
- [x] 7. **GETs return a flag as it stands now.** A flag whose `scheduledChange` is due comes back with `enabled` set to the scheduled value and `scheduledChange: null`, and no write happens on read. `resolveFeatureFlag` from types does this.
- [x] 8. **Writes handle the schedule.**
  - A write folds any due change into the stored flag before applying the update.
  - A `scheduledChange.at` that isn't in the future returns 400.
  - `scheduledChange: null` cancels a pending change.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `code/src/repositories/collection.ts`: `ensureIndexes` (:36-49) gains index options. It is fire-and-forget and only logs `IndexCreationFailed`, so check the index in dev. Also `constants.ts`, `collection-tokens.ts` and `collections.module.ts`.
- New code:
  - `code/src/core/feature-flags/` (the service);
  - `code/src/http/api/v1/feature-flags/` (controller and DTOs);
  - `bootstrap/containers/feature-flags.module.ts`, plus its registration in `bootstrap/root.module.ts`.
- `code/src/shared/openapi-schema.utilities.ts:59`: `toOpenApiSchema` rebuilds every object as `.passthrough()`, so DTOs do not enforce strictness. Read only, not changed.
- `code/openapi.yaml`, which is hand-written and still the source of fuse-ui's client. Also `CLAUDE.md`'s persistence and HTTP tables.
- The `@gfs-bifrost/types` pin moves from 10.13.0 to 10.14.0. pnpm 11 needs a `minimumReleaseAgeExclude` entry to install a freshly published version.
- fuse-mcp `data/api-endpoints.json` and `data/database-collections.json`.
- Guardrails:
  - G1: the revision publish is not used here.
  - G3: no new exception types. Reuse `ConflictException` and `EntityNotFoundException`, which are already mapped in both `DomainExceptionFilter` and `errorMiddleware`.
  - G5: the routes stay under `/api/v1`, behind the API key.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **The service re-parses every write against types' `FeatureFlagSchema` and returns 400 on failure.** The DTO pipeline alone would persist unknown keys. If a typo like `targets.businessId` were saved, every consumer would fall back to its default for that flag. Source: factual and history reviews (`openapi-schema.utilities.ts:59`).
- **The list GET returns `{ flags: [...] }`, not a bare array.** The generated document emits array DTOs as `{root?: [...]}`, the defect that stopped fuse-ui's regen. Source: history review, [[generated-openapi-as-the-single-source-of-truth]].
- **DTO class names are unique and match the `openapi.yaml` schema names.** That makes the later move to the generated spec a no-op for fuse-ui's `FeatureFlag` alias. Swagger keys components by class name. Source: history review.
- **Every successful PATCH increments `metadata.version`.** `updatePartial` always increments (`collection.ts:83-85`), and nothing increments only on a real change. `expectedVersion` is optional optimistic concurrency. Source: factual review.
- **The unique index's E11000 duplicate-key error maps to `ConflictException` explicitly.** Source: factual review.
- **Delete is a hard delete, and a deleted key can be recreated.** A soft delete under a plain unique index would burn the key forever. Source: default taken.
- **`updatedBy` comes from fuse-ui's `x-user` header when present, otherwise `"admin"`.** Any API-key holder can set that header, so it is informational and never shown as the actor. fuse-ui's audit row is the record. Source: history review (Audit Service programme; known-context #no-audit-trail).
- **The `FeatureFlagChanged` log is an operational event, not a second audit trail.** It carries key, version and enabled, not before and after. Source: known-context #no-audit-trail; Audit Service programme decision "config-service dropped as a producer".
- **fuse-mcp `config-write` can call these routes with the API key**, so "flips only through fuse-ui" isn't enforced in v1. This sits with the who-may-flip question in [[runtime-feature-flags-audited-flag-page]].
> SUPERSEDED 2026-10-14: Harry approved the prod deploy on 14 Oct, ahead of the freeze, so this no longer gates anything.
- UNRESOLVED: does the 1 Nov peak freeze cover config-service merges? The answer decides whether this lands in prod by 31 Oct or waits.

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

- [x] 1. **Persistence.** `Collection` accepts index options, and the `feature_flags` collection gets its token, module registration and a unique index on `key`. (AC 2) — unique key index; 3 index tests; mutation-checked — done: 00d4cc8
  — verify:
  - an integration spec: a second insert with the same key fails with E11000;
  - the existing collections' index specs are unchanged;
  - in dev after deploy: no `IndexCreationFailed` log for `feature_flags`, and `getIndexes()` shows `key_1` with `unique: true`.
- [x] 2. **`FeatureFlagsService`** (create, get, list, patch, delete). It re-parses against `FeatureFlagSchema` (400 on failure). It serves every read through `resolveFeatureFlag(flag, now)`. On every write it folds a due change first, and it rejects a `scheduledChange.at` that isn't in the future. It maps (AC 2,3,4,7,8): — 24 service integration tests vs Mongo 7; 3 mutation checks — done: 00d4cc8
  - E11000 to `ConflictException`;
  - a stale `expectedVersion` to `ConflictException`;
  - an unknown key to `EntityNotFoundException`.

  (AC 2,3,4,7,8)

  — verify:
  - unit tests:
    - create on an existing key throws Conflict;
    - a patch with a stale `expectedVersion` throws Conflict;
    - get or delete of an unknown key throws NotFound;
    - `targets: { businessId: [...] }` and an unknown top-level key are rejected;
    - a past `scheduledChange.at` is rejected;
    - a get for a flag whose change is due returns the scheduled `enabled` with `scheduledChange: null` and writes nothing;
    - a patch on such a flag stores the folded state plus the patch;
  - an integration test: a patch increments the version.

      gate: `@gfs-bifrost/types@10.14.0` published and pinned here ([[runtime-feature-flags-types-featureflagschema-an]] inc 1)
            [x] confirmed
- [x] 3. **Read routes.** `GET /feature-flags` and `GET /feature-flags/{key}`, the module wiring, and the `openapi.yaml` paths and schemas. (AC 1,5) — 6 HTTP tests vs real Mongo; generated spec names checked — done: c083f3a
  — verify:
  - controller specs;
  - in dev, GET with the key returns `200 {"flags":[]}`, and without it 401;
  - `/api/v1/docs-json` lists both operations.
- [x] 4. **Write routes.** `POST`, `PATCH` and `DELETE`, their DTOs, `updatedBy` from `x-user`, the `FeatureFlagChanged` log, and the `openapi.yaml` entries. (AC 2,3,4,5,6) — 17 write-route HTTP tests vs real Mongo — done: 8b1ae2b
  — verify:
  - specs:
    - a duplicate POST returns 409;
    - a PATCH with a version mismatch returns 409;
    - with no `x-user`, `updatedBy` is `"admin"`.
  - a dev round trip with `x-user`:
    - POST returns 201 at v1;
    - PATCH with `expectedVersion=1` gives v2, and repeating it gives 409;
    - a POST with `targets.businessId` returns 400, and GET shows nothing was persisted;
    - DELETE succeeds, and a GET afterwards returns 404;
    - a PATCH that schedules `enabled: true` two minutes ahead reads `enabled: false` with the schedule before T, then `enabled: true` with `scheduledChange: null` after T, with no write in between (the version is unchanged).
  - `npx openapi-typescript code/openapi.yaml` emits all five operations;
  - the existing customer-config spec suite is unchanged.
- [x] 5. **Docs and MCP.** CLAUDE.md persistence and HTTP tables. fuse-mcp `api-endpoints.json` and `database-collections.json` plus `make parity-accept`, pushed to master from a worktree. (AC 1,5) — CLAUDE.md + fuse-mcp a686a6e; dev round trip; prod gate still open — done: 8b1ae2b
  — verify:
  - after fuse-mcp's deploy, `lookup-endpoints config-service` lists `/api/v1/feature-flags`;
  - in prod after approval, `GET /api/v1/feature-flags` returns `200 {"flags":[]}`.

      gate: prod approval only after `git log <prod-sha>..<run-sha>` is reviewed and every foreign commit is accounted for, and after the freeze question is answered
            [x] confirmed

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-14 [inc 5] (AC 1,5) **Prod.** Harry said to approve and deploy. Prod was on 6f0b36b. `6f0b36b..815b0e5` is 6 commits: Renovate #236 and #237, which bump types to 10.12/10.13 and are additive, plus #239–#242. Nothing else rode along. The prod plan changed the image plus the known standing drift (container-dependencies, the sidecar env reorder, the `-ps@` invoker flip-flop) and nothing more. Deploy run 38565511306 approved, `terraform-apply-prod` green, and `config-service-prod` is on `prod-815b0e54…` (revision 00035-b2m). fuse-mcp `config-read` production `GET /api/v1/feature-flags` returns `200 {"flags":[]}`. The 25 older parked Deploy runs were cancelled. One, 35326288564 at 11d4771, is stuck on GitHub: cancel, force-cancel and gate review all return 409/422. Because it can't be approved either, it can't roll prod back.
- 2026-10-14 [inc 4] **Log-field fix (#242, merged as 815b0e5).** The change log's `version` field was landing on Datadog's reserved service-version tag: the 12:34Z dev logs show `version: "1"/"2"/"3"`. It's renamed to `flagVersion`. After the redeploy, the 12:42:53Z create log carries `custom.flagVersion: 1`, and the `version` tag is the deploy sha `815b0e54…`.
- 2026-10-14 [inc 5] (AC 1,5) **fuse-mcp master a686a6e:**
  - `api-endpoints.json` has the 5 feature-flag operations;
  - `database-collections.json` has `feature_flags`, and its note now says seven wired collections;
  - `config-domain.json` has a `featureFlags` section;
  - `make parity-accept` updated the baseline, and `go test ./internal/...` has 0 failures.

  config-service CLAUDE.md (in #241) has the routes and collection rows, the corrected version-increment claim, and the `$`-pipeline gotcha.
- 2026-10-14 [inc 4] (AC 2,3,4,5,6) **Dev, live round trip** after #241 merged as 8b1ae2b (Deploy run 38564385256, dev apply green), via fuse-mcp `config-write`/`config-read`:
  - POST `config-service.smoke-test` returned 201 at v1, with `updatedBy: admin` and the `$5 off…` description preserved.
  - POST with `targets.businessId` returned 400 `Unrecognized key: "businessId"`, and a GET of that key returned 404, so nothing was stored.
  - PATCH `{enabled:false, expectedVersion:1}` returned 200 at v2. Repeating it returned 409 "is at version 2, not 1".
  - PATCH with `scheduledChange {at: 12:36:20Z, enabled: true}` returned v3 with `enabled: false`. A GET at 12:36:23 returned `enabled: true`, `scheduledChange: null`, still v3, so no write happened.
  - DELETE returned 204, and a GET afterwards returned 404.
  - `/api/v1/docs-json` lists all 5 operations plus `CreateFeatureFlagRequestDto` and `UpdateFeatureFlagRequestDto`.
  - Datadog shows the "Feature flag changed" logs: created, updated ×2 and deleted.
- 2026-10-14 [inc 4] (AC 2,3,4) **`feature-flags.write.controller.integration.spec.ts`, 17/17:**
  - POST: 201 at v1; the version header; `x-user` becomes `updatedBy`, with an `admin` fallback; a duplicate gives 409; a `targets.businessId` typo gives 400 with nothing stored; an unknown key gives 400; a past schedule gives 400.
  - PATCH: `[false, 2]`; a stale version gives 409; an unknown key gives 404; a scheduled flip gives `[true, 2]`; null cancels.
  - DELETE: 204, then 404; an unknown key gives 404.

  Integration suite: 412 passed / 15 skipped.
- 2026-10-14 [inc 3] (AC 1,5) **Dev, live.** #240 merged as c083f3a, and Deploy run 38562877652 `terraform-apply-dev` succeeded. Against `https://config.fuse.freightops.dev`:
  - `/health` returns 200;
  - `GET /api/v1/feature-flags` with no key returns 401, and so does `/{key}`;
  - with the key (fuse-mcp `config-read`), `GET /api/v1/feature-flags` returns `200 {"flags":[]}`, and `GET /api/v1/feature-flags/config-service.smoke-test` returns 404;
  - `/api/v1/docs-json` lists `/api/v1/feature-flags` [get] and `/api/v1/feature-flags/{key}` [get], with components `FeatureFlagListResponseDto` and `FeatureFlagResponseDto`.
- 2026-10-14 [inc 3] (AC 1,5) **`feature-flags.controller.integration.spec.ts`, 6/6 through the real Nest app** (supertest, real Mongo):
  - list: `{flags: []}` when empty; every flag listed; a due scheduled change is served as `{enabled: true, scheduledChange: null}`.
  - get one: returns the full flag at v1 with `updatedBy`; `X-Resource-Version: 1`; an unknown key gives 404.

  The generated Swagger document (`SwaggerModule.createDocument` on `RootModule`) has `/api/v1/feature-flags` and `/{key}` with components `FeatureFlagResponseDto` and `FeatureFlagListResponseDto`. `openapi.yaml` uses the same names, and `openapi-typescript@7` emits both paths and a typed `FeatureFlagResponseDto`. Integration suite: 395 passed / 15 skipped.
- 2026-10-14 [inc 1] (AC 2) **Dev:** #239 merged as 00d4cc8 and Deploy run 38562008330 applied dev, with `docker-push-dev` and `terraform-apply-dev` green. Dev logs show boot at 12:14:47Z. `service:config-service @environment:dev "Index creation failed"` returns 0 hits in 2 h.
- 2026-10-14 [inc 1,2] **Mutation checks** (each fix was restored afterwards):
  - dropping `unique: true` fails the 2 index tests;
  - removing `resolveFeatureFlag` from `get` fails "returns the scheduled value once the change is due";
  - switching `setFields` to a pipeline `$set` fails "increments the version", "rejects a stale expectedVersion" and the update path's `$`-description test.
- 2026-10-14 [inc 2] (AC 2,3,4,7,8) **`feature-flags.service.integration.spec.ts`, 24/24 against real Mongo 7**, one assertion each:
  - create: returns v1; omitted targets and schedule stored as `null`; `updatedBy` recorded; a duplicate gives `ConflictException`; `targets.businessId`, an unknown top-level key and a past `scheduledChange.at` each give `ValidationException`; a `$`-description survives.
  - get: unknown key gives `EntityNotFoundException`; a due change returns the scheduled `enabled`; a pending change leaves it unchanged; resolving a due change doesn't write (the stored `enabled` is still false).
  - list: returns every flag with due changes applied.
  - update: applies a partial change; increments the version; a stale `expectedVersion` gives a conflict; folds a due change before the patch; `scheduledChange: null` cancels a pending change; a past schedule gives a validation error; a `$`-description survives; unknown key gives not-found.
  - delete: removes the flag; the key can be recreated at v1; unknown key gives not-found.
- 2026-10-14 [inc 1] (AC 2) **`collection.integration.spec.ts`, 3/3:** `feature_flags.key_1` is `unique: true`; a second insert of the same key fails with E11000; `business_information.businessId_1` stays non-unique.
- 2026-10-14 [inc 1,2] (AC 6) **Regression suites:** unit 693/693, and the full integration suite 389 passed / 15 skipped, against a throwaway `mongo:7 --replSet rs0` on :27031. `check-code` is clean, and lint is clean apart from 2 existing warnings. The lockfile diff from pnpm is only the types 10.13.0 → 10.14.0 bump.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- Load from evaluating instances. It's negligible by estimate (about 0.33 rps for shopify at max scale), and it isn't measured until phase 2.

## Rollout & rollback
<!-- Added on demand. Written at plan time; amend in place as it changes.
     `Shared state touched:` is the single home for the five classes git does not own — a dev
     deploy, a prod config write, a Datadog monitor, a CI var or secret, cross-repo IaC. Reverting
     the branch undoes none of them, so if they are not written here they are not written down. -->

- **Order:**
  - The work goes out as three stacked PRs: PR1 is inc 1+2, PR2 is inc 3, PR3 is inc 4+5.
  - PR1 waits on types 10.14.0. Write routes live in dev unblock pkg-node inc 4 and fuse-ui inc 1.
  - Merge the stack in one sitting so prod takes a single approval. Every merge to `main` queues a prod deploy, and there is no path filter.
- **Flags/config:** a new `feature_flags` collection in dev and prod Mongo.
- **One-way doors:** none in v1. The routes and collection are additive, and nothing reads flags in prod until phase 2.
- **Rollback:** `git revert` per PR. The collection can be dropped.
- **Shared state touched:**
  - dev deploys (manual-deploy applies dev Terraform, so check the plan first);
  - throwaway dev flags `config-service.smoke-test`, deleted after the check;
  - the dev and prod Mongo collection;
  - the fuse-mcp master commit.
- **Proof in prod:** `GET /api/v1/feature-flags` returns 200, and the config-service 5xx monitor stays flat.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-14** — Learnings promoted to architecture.md (re-anchored at 815b0e5): G4 now says DTOs are passthrough, so unknown keys persist unless the service re-parses; metadata.version effectively increments on every write; the feature_flags row; the $-string pipeline gotcha. Increment stamps re-pointed at the squash shas on main (00d4cc8, c083f3a, 8b1ae2b).

- **2026-10-14** — Harry, 2026-10-14: scheduled changes are in v1, and customer targeting moves to a later iteration. A schedule lives on the flag (scheduledChange { at, enabled }). This service serves resolved state on GET with no write, folds a due change on the next write, and rejects an at that isn't in the future. fuse-ui reads these routes directly (no cache) as the first adopter, so the read routes are now on fuse-ui's hot path too.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
(none)
