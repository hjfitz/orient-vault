---
ticket: none
title: 'Repository seam: one repository per aggregate, still on Mongo'
service: config-service
status: complete
created: '2026-10-28'
updated: '2026-10-28'
repo: /home/hjf/code/fuse/config-service
worktree: /home/hjf/code/fuse/config-service/.claude/worktrees/cloudsql-a1
branch: hjf/cloudsql-a1-repository-seam
base: origin/main
base_sha: 6a88e5410
pr: 'gfs-bifrost/config-service#262, #263, #265, #266, #267, #268, #269, #271, #272'
tags:
- waypoint
- plan
programme: Config Service Cloud SQL
unit: A1
impl_model: opus
impl_effort: medium
---
# Repository seam: one repository per aggregate, still on Mongo

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
Config Service Cloud SQL programme, units **A1 and A2** (and the groundwork for A3), out-of-ticket, prep for Merak. Today 8 core services hold 14 `ICollection<T>` injections, write Mongo filters and update documents inline, return `WithId<…>` from `mongodb`, and 6 core files hand-build aggregation pipelines. After this plan, core depends on one repository interface per aggregate in `repositories/`, the Mongo implementations hold every filter, pipeline and `$set`, and nothing in `core/` imports `mongodb` except the transaction session (removed in A3). **No behaviour change**: the proof is the dev contract snapshot (`pnpm run contract:snapshot`) re-run after each increment and showing no diff, plus the existing suites.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. No file under `code/src/core/` injects an `ICollection<T>` or imports `../../repositories/collection`; each service takes repository interfaces through DI tokens. (production code; test files see Not verified)
- [x] 2. No file under `code/src/core/` imports from `mongodb`, except `ClientSession` on the business delete path (A3 removes that); `git grep -n 'from "mongodb"' code/src/core` shows only that. (production code; the exception also covers `MongoClient`, see Decisions)
- [x] 3. `core/*/mongo-queries/` and the inline pipelines in `connectors.service.ts`, `business-information/constants.ts` and `storefront/constants.ts` live in `repositories/mongo/`.
- [x] 4. Repositories return stored records without `_id` (`Stored<T>` = `T & { metadata }`), and Mongo errors leave them only as application exceptions (`FeatureFlagsService` no longer imports `MongoServerError`).
- [x] 5. After each increment is on dev, `contract:snapshot` against dev shows no diff, and a create/patch/delete per touched resource returns the same status, body shape, `X-Resource-Version` and `config_revision` publish as before.
- [x] 6. Every query that moved has an integration test against real Mongo in its new home, so no filter loses coverage when the core unit tests switch to mocking repositories.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `code/src/core/**` services and their unit tests (mock repositories instead of collections).
- `code/src/repositories/` — new per-aggregate interfaces (`*.repository.ts`), Mongo implementations under `repositories/mongo/`, DI tokens in `collection-tokens.ts` / `collections.module.ts`. `Collection<T>` stays as the implementations' helper until F1.
- HTTP contract of all 52 `/api/v1` routes: unchanged, proven by the A0 snapshot ([[architecture#persistence-surface]]).
- No Fuse MCP data change (no route, topic or collection changes).

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- `repositories/` already exists as the persistence layer, so per-aggregate repositories in it are not a new layer — agents.md *Directory responsibilities* (DB queries belong in repositories), and the programme ledger approved by Harry names `repositories/mongo/`.
- No response carries `_id` after A5 — dev contract snapshot 2026-10-28, all 19 GET routes; so stripping `_id` in the repositories is behaviour-neutral.
> SUPERSEDED 2026-10-28 — the cascade is not inside the transaction: no session reaches its writes (increment 4, pinned by an integration test). See Decisions.
- Business delete cascades across six collections (business, backends, shipment methods, DDP, storefronts, connectors) inside one transaction — `business-information.service.ts:154-200` read. So the business repository lands after the small aggregates' repositories and drives them through the same session.
- **Backend invariants that sit below the HTTP surface** (from the Delivery Backends session, 2026-10-28; its programme owns these rules). The backend repository must keep every one:
  - Create is a plain `insert`, never `save`. The unique index `BACKEND_CONFIG_UNIQUE_INDEX` on `{businessId, type, metadata.deletedAt}` is what turns a second create into the 409. `deletedAt` is in the key on purpose, because a partial index can't express "missing".
  - Update writes back by the fetched row's `_id`, not by `{businessId, type}`, which also matches soft-deleted rows. Which row that filter hit depended on the query plan, so a route diff won't show a regression.
  - Delete stays filtered on `{businessId, type}`. Without `type`, deleting a SNAP backend would remove a Selector one.
  - The list pipeline projects `{ configs: 0 }` (an exclusion), so Selector rows keep their fields. An inclusion projection silently drops endpoint, carrier and the rest.
  - The business refs `$lookup` in `core/business-information/constants.ts` filters `metadata.deletedAt` and projects `{ _id: 0, backendId: 1, type: 1 }`. C1's Postgres join needs the same tombstone filter.
  - Out of the repository's scope, so left where they are: the SNAP-only revision dispatch gate in both controllers, and `toBackendResponse`'s per-type field mapping.
- Storefront delete **hard**-deletes its connectors and itself (`deleteRecordMany`), while business delete **soft**-deletes — source read. Carried over exactly; not this plan's to change.
> SUPERSEDED 2026-10-28 — the guard matches for connector saves of a just-read document, so an unchanged connector write keeps its version (increment 3). See [[architecture#persistence-surface]].
- `save(record, { filter })` is an upsert on the filter, and `version` increments on every write (the `$$ROOT` guard never matches) — [[architecture#persistence-surface]]. Repository methods keep that.

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

- [x] 1. Small aggregates (A2): `BackendRepository`, `ShipmentMethodRepository`, `DdpRuleRepository`, `FeatureFlagRepository`, plus `softDeleteForBusiness` on the first three for the cascade. Move `backend-config/mongo-queries/`. Translate the duplicate-key `MongoServerError` into `ConflictException` (AC 1,2,3,4 for these services; 5,6) — verify: unit + integration suites; dev deploy, snapshot no diff; create/patch/delete a backend (`?type=SNAP`), shipment method, DDP rule and feature flag on a dev test business, each matching the pre-change response and revision event — shipped to prod at dbb4f25 — done: 222cbf9
- [x] 2. Connectors: `ConnectorRepository` covering `ConnectorsService` (global list pipeline, lookup with `businessId`) and `SftpAuthStatusHandler` (find + partial update of `config.auth/user/isActive`); named methods for the `config.type`, `config.isActive`, `config.user.username` queries C1 turns into columns (AC 1,2,3,4,5,6) — verify: suites; dev snapshot no diff; a mock `customer_creation` push for a dev SFTP connector writes the same fields — done: b5805f8
- [x] 3. Storefront: `StorefrontRepository`, and `StorefrontService` moved onto it and onto `ConnectorRepository` (connector CRUD, mappings, credential cycle, storefront-with-connectors pipelines, the hard-delete). Largest increment; the 2,900-line spec switches to repository mocks (AC 1,2,3,4,5,6) — verify: suites; dev snapshot no diff; full storefront + connector + mapping + credential-cycle round trip on dev — done: abbca36
- [x] 4. Business: `BusinessRepository` including the warehouse-routing and SKU-blacklist field operations, and the cascade driving the other repositories through the existing session (AC 1,2,3,4,5,6) — verify: suites incl. the cascade integration test; dev snapshot no diff; create, patch and delete a dev test business with a storefront, connector, backend, shipment method and DDP rule, confirming every child is soft-deleted — done: 5bb05ac

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-28 [inc 4, business, #271 + #272] AC 1,2,3,4,5,6.
  - **Prod `5bb05ac`:** config-service-prod-00043-rpf, 100%, re-checked 5 min later. Read-only GETs, all 200: business list (33, no `_id`, `offset` paging consistent), detail with refs, routing, blacklist, backend, shipping and storefronts on 5 businesses. DDP answered 404 where a business has no rules, as before. Datadog on the new version showed no new warning or error.
  - **Dev `5bb05ac`:** `contract:snapshot` matches the committed contract. A 52-step round trip on throwaway SHIPBIZCHK/SHIPBIZCHK2 matched the local `main` baseline status and version on every step, including the cascade: all five child types answered 404 after the delete while the other business kept its own. The only warnings were the 8 `Record failed validation` lines every snapshot run produces.
  - **Local parity with `abbca36`:**
    - GET contract identical on 19 routes.
    - 52-step HTTP sequence identical.
    - 17 `config_revision` events identical (private emulator; backend ids masked).
    - End-state rows of both businesses identical in all six collections, including `deletedAt` and versions.
  - **Suites:** unit 994; integration 532 (15 skipped). The integration suite includes the cascade, its non-atomic failure case, and soft-deleted-business exclusion and re-create refusal.
  - **Mutation-checked:**
    - the live filters on the storefront-id read and the connector cascade;
    - `softDelete` ignoring the modified count;
    - the storefront/connector cascade skipped;
    - the backend lookup's live filter;
    - `insert` via `save`;
    - `existsLiveOrDeleted` with a live filter;
    - `countLive` unfiltered.
  - **AC check on `5bb05ac`:**
    - No production file under `core/` injects a collection or holds a pipeline (AC 1, 3).
    - The only core `mongodb` import is `ClientSession`/`MongoClient` in the business service (AC 2; see Decisions).
    - Every Mongo repository strips `_id` (AC 4).
- 2026-10-28 [inc 3, storefront, #268 + #269] AC 1,2,4,5,6.
  - **Prod `abbca36`:** config-service-prod-00042-jfp, 100%, re-checked 5 min later. Read-only GETs on 5 businesses all 200: storefront list, storefront with connectors (no `_id`), connector list, connector detail. Datadog on the new version shows only the routine "Entity not found" pattern.
  - **Dev `abbca36`:** `contract:snapshot` matches the committed contract exactly. A scripted round trip on throwaway SHIPSFCHK (REST connector only) passed: PATCH storefront without `_id` and with `metadata` (v2, then v3 on an identical body); connector same-body PATCH stays v1; identical mapping replace keeps the version, a changed one bumps it; credential cycle bumps twice (5→7); 429 on re-cycle; deletes and 404s as before.
  - **Local parity with `b5805f8`:** GET contract identical on 19 routes. A 60-step storefront, connector (SFTP/Shopify/REST), mapping and credential sequence was identical, versions included, except `_id` on the 3 PATCH storefront bodies (approved).
  - **Suites:** unit 903; integration 498 (15 skipped). Mutation-checked: `_id` re-attach and its key order, `findLive` live filter, mapping-event `$nin`, count status, `update` not upserting, `findInBusiness` including soft-deleted.
- 2026-10-28 [inc 2, connectors, #267] Prod `b5805f8` (config-service-prod-00041-dj4, 100%, re-checked 75 s later): health UP; connectors by type 31+4+3 = 38 = all; no `_id`; detail carries `businessId`; Datadog: no warnings or errors on the new version. Dev `b5805f8`: contract snapshot identical; type filters 70+16+15 = 101 = all; `count`/`offset` paging; detail and 404. The SFTP callback's write path was not exercised on dev (it would overwrite a real connector's credentials, and a throwaway SFTP connector triggers real provisioning); it rests on the local parity run and the integration tests. Local parity with `dbb4f25`: GET contract identical, 17-step connector + callback sequence identical. Unit 798, integration 487 (15 skipped).
- 2026-10-28 [inc 1, prod] AC 5 prod: `dbb4f25` live (config-service-prod-00040-h9j, 100%, re-checked 60 s later). Read-only GETs: backend list 33 SNAP rows with no `_id`, business SNAP backend 200 v2 with exactly `backendId, broadcastConfirmations, businessId, credentials, host, type`, SELECTOR 404, shipment methods 200, flags 200 with no `_id`. Datadog on the new version: only the routine "Entity not found" warning pattern; no index-creation failure.
- 2026-10-28 [inc 1, dev] AC 5 dev half: dev on `dbb4f25` (google 7.46.2). `contract:snapshot` against dev matches the committed contract exactly (19 routes). A scripted round trip on throwaway business SHIPSEAMCHK: shipment methods, DDP, SNAP and SELECTOR backends, a feature flag, and the business delete each answered the expected status and version (409 on duplicates, 1→2 bumps, SNAP delete leaving SELECTOR, SELECTOR list keeping `endpoint`). Temporary subscriptions caught `config_revision` SHIPMENT_METHOD v1/v2/-1, DDP_RULES v1/v2/-1, BACKEND_CONFIG v1×2/v2×2/-1 (fragment + resource link on create and update, as the controller dispatches), nothing for SELECTOR, and `feature_flag_revision` created v1 / updated v2 / deleted. No events for other businesses.
- 2026-10-28 [inc 1, feature flags, #265] AC 1,2,4,5 (local half): origin/main (:3201) and the branch (:3202) booted against one seeded private Mongo; contract:snapshot identical on 19 GET routes with a flag seeded; 12-step flag write sequence identical (201, duplicate 409 now raised by the repository, stale-version 409, strict 400, DELETE 204/404). AC 6: repository spec pins every filter and every `_id` strip (strip mutation-checked).
- 2026-10-28 [inc 1, DDP rules, #263] AC 1,2,4,5 (local half): GET contract identical; 12-step DDP write sequence identical. AC 6: soft-delete, re-create-over-tombstone and delete-scope integration tests (delete scope mutation-checked).
- 2026-10-28 [inc 1, shipment methods, #262] AC 1,2,4,5 (local half): GET contract identical; 12-step shipment-method write sequence identical. AC 6: same three integration tests plus repository filter spec (delete scope mutation-checked). Upsert-over-soft-deleted behaviour confirmed against Mongo 7 and pinned.
- 2026-10-28 [inc 1] Suites at 3b1bce1: unit 747 passed; integration 455 passed, 15 skipped (private mongo:7 replica set).

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- AC 1/2 read literally ("no file under `core/`") still fail on test files: four core integration specs seed through `Collection`, and 12 core test files import `mongodb` types (`WithId`, `ObjectId`). Production code meets both. Follow-up, not blocking A1.
- SHIPBIZCHK and SHIPBIZCHK2 remain on dev as soft-deleted businesses, with their children soft-deleted, and SHIPBIZCHK's SNAP backend pointed at a fake host until the delete.
- Storefront increment on dev: SFTP and Shopify connector writes were not exercised there (an SFTP create provisions a real user; a Shopify one starts a poller). They rest on the local parity run, which covers all three types.
- SHIPSEAMCHK and SHIPSFCHK remain on dev as soft-deleted businesses (the API's delete is soft; SHIPSFCHK's storefront and connector were hard-deleted first).

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->
- **2026-10-28** — Increment 4 shipped as a two-PR stack (#271 repositories, #272 service switch). **The cascade keeps its transaction wrapper and passes no session**, exactly as before. The old code never threaded the session through, so the cascade was never atomic, and threading it now would be a behaviour change. It also can't be done as written: the cascade's writes run concurrently on one session. A3 owns this. **AC 2's exception therefore covers `MongoClient` as well as `ClientSession`** (both serve `MongoUtilities.transaction`). The dead `clientSession` parameter stays for A3 to remove with the wrapper. Business create became a plain `insert` (the overwrite path of the old upsert was unreachable). The write types narrowed to the fields callers pass, so Postgres never stores the ref arrays.
- **2026-10-28** — Increment 3 shipped as a two-PR stack (#268 repositories, #269 service switch), ~1,560 + ~2,320 lines: the converted service spec has to land with the service, so there was no smaller seam. Storefront create/update split into `insert` and a non-upserting `update` (a partial-field upsert can create a row with no `businessId`, which Postgres can't express); `update` still bumps the version on every PATCH, as the old `save(dto)` did. The PATCH read-back keeps its projection but drops a connector lookup whose output the controller discards. PATCH storefront drops `_id` (Harry approved). The connector list's dead `useCases`/filter bugs were documented with a TODO, not fixed, since fixing them changes responses.
- **2026-10-28** — Increment 1 shipped as four PRs (#262 shipment methods, #263 DDP rules, #265 feature flags, #266 backends), not one, to stay near the 700-line target. `softDeleteForBusiness` was **not** added to the small aggregates' interfaces: no caller needs it until increment 4 routes the business cascade through the repositories, so adding it now would be speculative. The cascade still reaches those collections directly until then; harmless, because the Postgres flag (C5) can't exist before group A is complete.
- **2026-10-28** — Backend updates write back by the live row's `_id`, found inside the repository (`replaceActive`), rather than the service passing an `_id` down. Core never sees a driver id; the live-row invariant from the Delivery Backends session holds.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
