---
ticket: none
title: 'remote-config 2.6/2.7: opt-in connector handling for sftp-connector'
service: pkg-node
status: active
created: '2026-11-05'
updated: '2026-11-05'
repo: /home/harry/code/fuse/pkg-node
worktree: /home/harry/code/fuse/.worktrees/pkg-node-remote-config-2.6
branch: hjf/remote-config-sftp-parity
base: origin/main
base_sha: 957ce3d72
pr: null
tags:
- waypoint
- plan
impl_model: opus
impl_effort: medium
---
# none — remote-config 2.6/2.7: opt-in connector handling for sftp-connector

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

- **2026-11-09:** Stack B review fixes went beyond the plan text.
  - **`evictOnDelete` rejects on a failed cache write.** That's a new failure mode, against the plan's "acks". The primary key is deleted last so that the retry can finish.
  - With `evictOnDelete`, `resolveByUsername` treats a cached alias whose connector now has another username as a miss. This is not in the plan; it closes a stale-alias gap when the old copy was missing or stale in L1.
  - **`backlinkTypes`:** a response with no `config.type` rejects instead of acking.
  - **The server-filtered lookup checks that the username matches exactly.**
  - All of these sit behind opt-ins, so defaults are unchanged (AC 1).

## Intent
<!-- What we are changing and why. Link the ticket. -->
Out-of-ticket. This is the package half of [[move-the-connector-onto-the-shared-remote-config|sftp-connector's move onto remote-config]], which Harry asked for on 2026-11-04. sftp-connector can't adopt `@gfs-bifrost/remote-config` 2.5.1 without changing what customers see. The package validates connectors strictly, its username lookup scans every connector, it throws on a deleted connector, one failing item in a revision skips the rest, its in-memory TTL is fixed at 60 s, and it sends no correlation header. This plan adds each fix as an **opt-in** builder option across two minor releases: **2.6.0** unblocks sftp's mapping increment, and **2.7.0** unblocks its connector-lookup increment. fapi (`^2.5.1`, so it auto-bumps) and shopify-connector (pinned `2.5.1` in both apps) see no change unless they opt in. Done means both versions are published, a compatibility type test and the existing suites pass unedited in behaviour, and the username lookup has been proven against dev config-service.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. With no new option set, every existing behaviour is identical (apart from the FUSE-1350 fix, AC 9): errors, cache keys, index shapes, negative markers, the in-memory TTL (60 s), headers, `processRevision` stopping at the first throw, and an unvalidated cached-connector read. A test pins each default, and a checked-in type test of 2.5.1-shaped calls compiles in every PR.
- [ ] 2. `withConnectorSchema(schema)` applies to the client's `getConnector`, the backlink handler and the mapping handler's connector read. A connector only the supplied schema accepts resolves, its mapping resolves, and the fields the schema keeps survive. A cached connector that fails the supplied schema is refetched.
- [ ] 3. `memTtl` (ms) sets the in-memory TTL in both `memory` and `full` mode. A `requestHeaders` callback adds headers to every Config API request (each page included), can never replace `x-api-key`, and never reaches the feature-flag client.
- [ ] 4. With `evictOnDelete`, a `version -1` backlink (or a 404 on refresh) removes the connector's primary key, its business and storefront index entries, and any username alias that points at it. A username change drops the old alias.
- [ ] 5. With `backlinkTypes`, a backlink for an unlisted connector type is acked without caching or validation.
- [ ] 6. With `lookup: "server-filtered"`, `resolveByUsername` on a miss makes 2 calls (`?type=sftp&userName=`, then one detail GET). On dev config-service it returns the same connector as the scan for every SFTP username.
- [ ] 7. `processRevisionSettled` runs every item of a revision in order, returns each item's outcome, and never throws for a handler error. `ConfigRevisionDispatchException.fromResult` gives an aggregate to throw.
- [ ] 8. 2.6.0 and 2.7.0 are published with their changelog entries, the pkg-node `CLAUDE.md` row, the README sections (cache modes, connector handling, sftp-connector migration) and the Fuse MCP `config-domain.json`/`shared-packages.json` updated. The missing 2.5.0 changelog entry is backfilled.
- [ ] 9. FUSE-1350 is fixed by default: caching one connector (backlink, connector-ID, username or storefront lookup) never creates a business or storefront index, so a later business resolve returns every connector the business owns. 2.5.2 is published and fapi and shopify-connector run it in prod.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `pkg/remote-config/src`: `remote-config.ts` (builder/provider, `:70-72,141,155,263-328`); `config-api/config-api.client.ts` (`:35-45,71-75`) and `config-api.types.ts` (`:14-17,26-47`); `handlers/backlinks/connector.handler.ts` (`:79-93,129-174,303-331,433-452,466-531,661-673,694-705`); `handlers/fragments/connector-mapping.handler.ts:45`; `dispatcher/config-event.dispatcher.ts:44-58`; `cache/types.ts`; `index.ts`; `readme.md`.
- `pkg/cache` is unchanged. `LruCache` `withTtl` is at `memory.cache.ts:327`, with the 60 s default at `:26`.
- config-service (read-only dependency): `GET /v1/connectors?type=sftp&userName=` (`connectors/schemas.ts:10-26`, both repos). For (c): `GET /v1/business/{id}` (connector refs joined on `connector.businessId`, `business.controller.ts:137`) and `GET /v1/business/{id}/storefront` (`:297-341`; known `total`/status gap, [[Engineering/config-service/architecture|config-service architecture]] :174-177).
- Consumer contracts that must hold (compatibility gate):
  - shopify-egress classifies on `ConfigApiException.cause.response.status`/`cause.issues` (`config-api.adaptor.ts:11-18`).
  - shopify-connector's `isMappingNotFound` checks that `endpoint` contains `/mappings/` and that `isAxiosError(cause)` (`config-api.adaptor.ts:209-215`), calls `.handle()` for every connector backlink and `dispatcher.processRevision` for fragments (`:163-197`), and acks errors with a 202 (`config-revision.filter.ts`).
  - fapi branches on `instanceof ConfigApiException` (`confirmation.service.ts:144,288`).
  - shopify's characterization fake stubs `resolveByUsername` (`config-fake.ts:34`).
- Guardrails: G1 (version-gated publish), G3 (`workspace:*` freezes `cache` to an exact version), G6 (`serialiseError` allow-list).

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- Redis is per service: sftp-connector has its own instance (`iac/.../cache.tf:9`, prefix `cfg` today). Within one service, 2.5.x and 2.6+ pods share `rc:*` during a rollout, so **no key format or index value shape may change** in this plan. Established by reading the source (draft plus grounding review).
- The `/v1/connectors` username filter exists and both storage backends honour it (Postgres indexed column; Mongo `config.user.username`). Summaries carry no `config`, so one detail GET follows. Source read. Proven against dev before 2.7.0 publishes (AC 6).
- sftp-connector's `GetConnectorDtoSchema` models use cases as nested `{useCase, mapping?}` (`schema.ts:44-58`). The wire shape is flat `{useCase, status, friendlyName, config}`, so passing that schema would strip every use case to `{useCase}`. sftp's schema must model the flat shape with `config` optional; that's written into its plan. `ConnectorDTOSchema` already accepts `null` use cases (`types connector-dto.schema.ts:45`). Source read.
- The handler's `validateConnectorDTO` throws a plain `Error`, not `ConfigApiException` (`connector.handler.ts:701`), and is unreachable today because the client has already parsed with the same schema. With a custom schema both use that schema, so it stays unreachable, and the plan keeps it as is. Source read (grounding review).
- Raw handler errors in (e)'s outcomes may be `ConfigApiException`s whose axios `cause` carries the request headers, including `x-api-key`. This departs from 2.4.0's "errors never carry the request". It's kept because shopify-egress classifies on `cause`, and `serialiseError` (G6) handles `AggregateError` members (`serialise-error.ts:202-208`). The README tells callers to log through `serialiseError`. Decision below.
- fapi master pins `^2.5.1` (`git show origin/master:code/package.json`, 2026-11-05), so it takes every 2.x minor automatically. shopify pins exactly `2.5.1` in both apps. Checked.
- The latent index bug the history review found is [FUSE-1350](https://gfsdeliver.atlassian.net/browse/FUSE-1350). It isn't observed in prod: in 7 days fapi logged constant cached counts per business and handled 14 connector backlinks, and shopify-connector's logs don't reach Datadog. Harry, 2026-11-05: raise the defect and remediate it at the same time, so it's inc 1, a default fix in 2.5.2.

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

Each stack is merged **in one sitting**, with the version bump on its last PR. #294 (2026-11-02) patch-bumped every package at once, so new public options left unreleased on `main` could ship half-done as a patch. Every PR adds `src/__type-tests__/v2-5-1-compat.ts` (2.5.1-shaped calls, compiled by `tsc`) or keeps it green, and leaves existing specs green with type-only edits at most. Test fixtures use plain values like `"fixture"`, never key-shaped strings (gitleaks).

- [x] 1. FUSE-1350: a business's connector index is created only from a full business fetch, then **release 2.5.2** (AC 9). Its own PR and patch, **default behaviour**, before stack A. — 2.5.2 published; fapi prod 31de60d, shopify-connector prod 8c75d18 (contains 2592b75), both re-checked 14:22Z — done: d641a76
      - `addToBusinessIndex`/`addToStorefrontIndex` (`connector.handler.ts:497-531` and the storefront twin) gain a `createIfMissing` flag. Only `fetchConnectorsForBusiness`/`fetchConnectorsForStorefront` (which hold the complete set) pass `true`. Every other path (`refresh`, `resolveByConnectorId`, `resolveByUsername`, `resolveByType`'s grouping) only appends to an index that already exists.
      - No key or value shape changes, so 2.5.1 pods reading an index written by 2.5.2 (and vice versa) stay correct. An index a 2.5.1 pod already built from one backlink still lives until its TTL. The defect clears fully one TTL (about 605 s for fapi) after the last 2.5.1 pod is gone.
      - Branch `hjf/fuse-1350-business-index-from-full-fetch` in its own worktree; `wp ledger pkg-node --ticket FUSE-1350`.
      — verify: `connector-backlink.handler.spec` "a backlink for one connector does not create the business index", "a backlink extends an existing business index", "resolveWithUnresolved after a single backlink returns every connector of the business", "resolve for another type after a backlink fetches from the API", "resolveByConnectorId does not create the business index", the same for the storefront index; the existing E8/2.2.0 specs (negative marker, unresolved indexed) green unedited; the release gate (type test, pack, scratch install into fapi and shopify); after publish, Renovate PRs in fapi and shopify-connector merged and deployed to prod, then FUSE-1350 closed.

- [x] 2. `memTtl` and `requestHeaders` (AC 1,3). Stack A, PR 1. — pkg-node#299 merged; 213 tests at that commit; mutations caught — done: d9617ab
      - `MemoryCacheConfig.memTtl?`/`FullCacheConfig.memTtl?` (ms) → `.withTtl()` only when set; reject values ≤ 0.
      - `ConfigApiOptions.requestHeaders?` → an axios request interceptor only when present; `undefined` values are dropped and `x-api-key` can't be overridden (case-insensitive); a throwing callback logs a warning with no values. `requestHeaders` is stripped where options are spread into `FeatureFlagClient` (`remote-config.ts:271-272`).
      — verify: `remote-config.spec` "keeps the 60-second in-memory TTL by default", "passes memTtl to the in-memory tier in full mode", "passes memTtl in memory mode", "rejects a non-positive memTtl"; new `config-api.client.spec` (local `node:http` server) "adds callback headers to each request", "calls the callback once per page", "never lets the callback replace x-api-key", "sends the request when the callback throws", "sends no extra headers without a callback"; `feature-flag.client.spec` "ignores requestHeaders"; the type test compiles.

- [x] 3. `withConnectorSchema`, then **release 2.6.0** (AC 1,2,8). Stack A, PR 2. — pkg-node#300 merged; 2.6.0 published (npm view ok); consumer gate fapi 511, shopify 900, egress 633 — done: 91fba57
      - Generic `<T = ConnectorDTO>` on `RemoteConfigBuilder`/`RemoteConfigProvider`/`ConnectorBacklinkHandler`/`ConnectorResolution`; export `ConnectorLike`.
      - The schema goes to the `ConfigApiClient` built in `buildProvider` (shared with the mapping handler) and in `buildApiClient`, and to the handler. Cached connectors are validated only when a schema is set; a failure is treated as a miss.
      - Release: version 2.6.0; changelog `#### 2.6.0` **and the missing `#### 2.5.0`** (ms TTL with a one-hour default, `memory` mode builds, `init()` resolves within 5 s on a Redis outage via cache 0.4.0); pkg-node `CLAUDE.md` row; README "Cache modes" (no longer "not configurable") and a "Connector schema" section with the flat use-case shape warning.
      — verify: `connector-backlink.handler.spec` "validates with the supplied schema on refresh", "keeps a field the supplied schema keeps", "falls back to the API when a cached connector fails the supplied schema", "reads cached connectors unvalidated without a supplied schema"; `connector-mapping.handler.spec` "resolves a mapping for a connector only the supplied schema accepts" (an sftp-shaped fixture: a config-less use case, a `null` use case, a bad `ediEnvelope`); the release gate below; after publish, `npm view @gfs-bifrost/remote-config@2.6.0 --registry=https://npm.pkg.github.com` resolves.

- [x] 4. `evictOnDelete` (AC 1,4). Stack B, PR 3. — pkg-node#304 merged; published in 2.7.0 — done: 5c5ca23
      - Under `withConnectorHandling({ evictOnDelete: true })`, `refresh` on `version -1` or a 404:
        1. Read the cached primary loosely.
        2. `tryDeleteAsync` it (Both tiers).
        3. Remove the ID from the business and storefront indexes, deleting a key that becomes empty.
        4. Delete `connector-alias:<u>` only if it points at this ID.
      - Every refresh compares the old username and drops a stale alias under the same guard. Mapping keys are left to their handler.
      — verify: "evicts the primary key on a version -1 backlink", "removes the connector from the business index on deletion", "deletes an emptied index key", "keeps an alias that points at another connector", "removes the old alias when the username changes", "throws on a deletion backlink without evictOnDelete", "keeps the old alias on a username change without evictOnDelete".

- [x] 5. `backlinkTypes` (AC 1,5). Stack B, PR 4. — pkg-node#305 merged; published in 2.7.0 — done: 5dc9130
      - `withConnectorHandling({ backlinkTypes: [ConnectorType.SFTP] })`: `refresh` reads the raw connector through a new optional `IConfigApiClient.getConnectorRaw?` and checks `config.type`. On a mismatch it logs at debug and returns without caching or validating. Otherwise it validates with the (custom) schema.
      - This also gives fapi and shopify a later opt-in against the types 10.4.0 rollout hazard (org `CLAUDE.md`, "backlink refresh isn't type-filtered").
      — verify: "acks a backlink for an unlisted connector type", "does not cache an unlisted connector type", "validates a listed type with the supplied schema", "caches a non-SFTP connector when backlinkTypes is unset".

- [ ] 6. Username lookup and settled dispatch, then **release 2.7.0** (AC 1,6,7,8). Stack B, PR 5.
      - (b) An optional `IConfigApiClient.getConnectorSummariesByUsername?` (`URLSearchParams`); under `lookup: "server-filtered"`, take the first summary (warn if there's more than one), one `getConnector`, then `cacheConnectorWithIndices`. Zero matches throws the same `No connector found for username` error, and a client without the method falls back to the scan.
      - (e) `processRevisionSettled(record)` → `{ outcomes[], failed }`, in order, never throwing for a handler error; `ConfigRevisionDispatchException.fromResult` (an `AggregateError` subclass). `processRevision` is untouched.
      - Release: version 2.7.0; changelog; `CLAUDE.md` row; README "Connector handling" and "sftp-connector migration" (INC-40 init/fallback under cache 0.4.0, `serialiseError` for outcomes, the release-age exclusion); Fuse MCP `config-domain.json` and `shared-packages.json` (straight to fuse-mcp `master`).
      — verify: "queries userName with type=sftp", "returns the first of several username matches", "falls back to scanning when the client lacks the method", "uses the scan by default", "runs every item when one throws", "reports each item's outcome in order", "marks an item with no handler as skipped", "keeps processRevision stopping at the first throw"; a **dev proof**: a scratch script running the built package against dev config-service, `server-filtered` vs `scan` for every SFTP username, all equal (recorded in Evidence); the release gate.

- [ ] 7. Business lookup via a business-scoped route (AC 1). Its own minor, later. **Not a dependency of sftp-connector**, whose plan keeps the scan for `resolve(businessId)`.
      gate: route chosen. `GET /v1/business/{id}` (refs joined on `connector.businessId`, same set as today's scan, no paging) is preferred over `/business/{id}/storefront` (the `total`/status gap, soft-deleted storefronts listed, live connectors under a deleted storefront). FUSE-1350 (inc 1) shipped.
            [ ] confirmed

      - Under `lookup: "server-filtered"`: refs → type filter after the detail GET → the existing `fetchAndCacheConnectors` and unresolved-to-index loop; a 404 or a non-`^[A-Z0-9]+$` ID → empty plus the type-scoped marker.
      — verify: "lists a business's connectors from the business route", "treats a 404 business as empty and writes the type-scoped marker", "skips the API for a non-uppercase businessId", "reports an unresolved connector and indexes it" (2.3.0 contract), "resolve uses getAllConnectors by default"; a dev proof: `resolve(b, SFTP)` gives the same set under both lookups for every business.

**Release gate (incs 1, 3 and 6):**
1. The type test compiles.
2. `pnpm pack`, then check the packed manifest: `@gfs-bifrost/cache` frozen to `0.4.0`, and the `types` peer floor (`>=10.15.0`) at or below fapi's (`^10.15.0`) and sftp's (`^11.4.1`).
3. Install the tarball (`file:`) into scratch clones of shopify-connector (`apps/shopify-connector`, `apps/shopify-egress-service`) and fapi master `code/`. Run each one's type-check, its `adapters/config` suites, shopify's `__characterization__`, and fapi's `config-api.adapter.spec`, `remote-config-provider.fallback.spec` and `confirmation.service.spec`.
4. `lint:fix`.
5. A `wp ledger pkg-node` entry per PR, and the `#bifrost-forge` post per merge.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
- **2026-11-09: stack B built and opened** (pkg-node#304 `92580f7`, #305 `434fa17`, #306 `1f86463`; native stack #307). Not merged: merging publishes 2.7.0.
  - **Dev proof (AC 6):** the built package against dev config-service, `server-filtered` against `scan` for every SFTP username: **70/70 equal**, 0 diffs, 0 shared usernames (73 connectors). 2 requests per filtered lookup (140 in total) against 2,973 for the scan. Run before and after the review fixes, with the same result.
  - **Release gate,** on the post-review tarball: fapi `007ad5c` `build:check` clean, 529 passed; shopify-connector `84714fc` 902 passed (`shopify-token-management` built first, as its CI does); shopify-egress-service 634 passed, `build:check:tests` clean; the 2.5.1 type test compiles. Manifest: cache `0.4.0` exact, peers `types >=10.15.0`, `zod ^4.4.3`.
  - **Tests:** 308 (80 new). Mutation checks: 26 mutations across the three PRs, all caught.
  - **Review panel** (backend, data, contract, tests): the contract reviewer found nothing. Fixed:
    - eviction deletes the primary key last and rejects on a failed cache write;
    - a rename drops the old alias before caching;
    - stale-alias check on `resolveByUsername` (under `evictOnDelete`);
    - a typeless backlink response rejects;
    - exact-username check on the filtered lookup;
    - failure-path tests.
    
    Documented, not fixed: the index read-modify-write race, the refresh/delete resurrection race, and cleanup after the primary key has expired.
- **2026-11-05: stack A released as 2.6.0** (pkg-node#299 `d9617ab`, #300 `91fba57`, one atomic stack merge, publish run 42055718681, `npm view @gfs-bifrost/remote-config@2.6.0` → cache 0.4.0).
  - **Tests:** 228, with 29 new.
  - **Release gate:** the packed tarball type-checks and passes the full suites in fapi `c0eef2d` (511), shopify-connector `cff1956` (900, including `__characterization__`) and shopify-egress-service (633).
  - **Self-review panel** (backend, contract, tests) led to an end-to-end builder test, batch-path schema coverage, a header test on connector reads, a README correlation fix and type-test coverage of the consumer-used shapes.
  - **Documented:** the schema must accept its own output.
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-11-05 [inc 1, AC 9] **FUSE-1350 fixed on the branch, PR [pkg-node#297](https://github.com/gfs-bifrost/pkg-node/pull/297).**
  - **Dev proof:** the built package (`memory` mode) ran against dev config-service on business DAZZA, which has 8 SFTP and 2 REST connectors.
    - After one SFTP backlink, 2.5.1 sees **1 of 8** SFTP and **0 of 2** REST connectors.
    - 2.5.2 sees **8 of 8** and **2 of 2**.
  - **Suite:** 199/199. 10 of the new specs fail on the 2.5.1 handler.
  - **Mutation checks:** 13 mutations, all caught.
  - **Public types:** the `.d.ts` public surface is identical to 2.5.1.
  - **Self-review:** two rounds, findings and dispositions in the PR Notes. The blocking one: without marker clearing, a business's first connector would stay hidden behind the 2.2.0 empty marker.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- <what remains unproven, and what would prove it>

## Rollout & rollback
<!-- Added on demand. Written at plan time; amend in place as it changes.
     `Shared state touched:` is the single home for the five classes git does not own — a dev
     deploy, a prod config write, a Datadog monitor, a CI var or secret, cross-repo IaC. Reverting
     the branch undoes none of them, so if they are not written here they are not written down. -->

- **Order:** inc 1 (FUSE-1350, 2.5.2) first and alone. Stack A (2 → 3, one sitting) publishes 2.6.0 and unblocks sftp-connector's inc 3. Stack B (4 → 5 → 6, one sitting) publishes 2.7.0 and is one of the gates on sftp-connector's inc 4. Inc 7 later, as its own minor.
- **Flags/config:** builder options only (`memTtl`, `requestHeaders`, `withConnectorSchema`, `withConnectorHandling({ evictOnDelete, backlinkTypes, lookup })`). All are off by default.
- **One-way doors:** a published version can't be unpublished. A defect ships forward as a patch. fapi auto-bumps on `^`, so it **will** run 2.6.0 and 2.7.0 with defaults: AC 1 is what protects it.
- **Rollback:** consumers stay on, or pin back to, 2.5.1. shopify is pinned exactly, and fapi can pin `2.5.1` in one line.
- **Shared state touched:**
  - **GitHub Packages:** two publishes (version-gated).
  - **Renovate:** bump PRs in fapi and shopify-connector.
  - **Fuse MCP data:** `config-domain.json` and `shared-packages.json` (fuse-mcp `master`).
  - **Dev config-service:** read-only proof scripts with the dev API key held in memory, never printed.
  - **(none)** for prod config, Datadog and IaC.
- **Proof in prod:** none from this plan. The defaults are proven by the suites and the compatibility gate. The opt-ins are proven in sftp-connector's plan (dev, then prod shadow).

## Options considered
<!-- Added on demand. Why this approach and not the others — the thing the planning agent is
     asked for and the plan has otherwise had nowhere to put. Promote to a durable record with
     `wp decide --record` when it is worth defending in a review six months out. -->

- **Chosen — opt-in builder options; two minors released at sftp-connector's need boundaries, each stack merged in one sitting.** Defaults can't move because fapi floats on `^`. Two minors cost one extra Renovate bump each, and they unblock sftp's inc 3 weeks before inc 4 needs the rest.
- **Rejected — one 2.6.0 at the end of five stacked PRs.** New public builder options would sit unreleased on `main` across PRs, and a #294-style patch sweep would publish half the feature undocumented. (The 2.4.0 precedent, #275, kept its code unexported; this plan's options are public from PR 1.)
- **Rejected — a mode on `processRevision` for (e).** It would silently change the semantics for anything holding the provider. A separate method is explicit at the call site.
- **Rejected — rebuilding the business index from a business-scoped route.** The index is type-agnostic, so replacing it with one type's IDs would make lookups for other types return `[]`. The real fix for the latent index bug is a type-scoped key, which is a key change needing a dual-read period, so it's out of scope here.
- **Deferred — making (b) and (d) the defaults in a later minor.** (b) is safe (no consumer calls it). (d) changes shopify's deletion error log and metric, so it's observable.
- **Deferred — a minimal `{storefrontId}` probe in `ConnectorMappingHandler`** instead of the full connector schema. It would unblock everyone, but it loosens shopify's `findConnectorMapping` failure behaviour.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-11-05** — Inc 1's design changed during self-review, against the plan text:
  - A single cached connector that has no index to join clears its business's and storefront's empty markers (own type and `all`). Without that, the 2.2.0 negative cache stops self-healing.
  - Business lookups and `resolveByType` build only business indices, written straight after the summary fetch. Only a storefront miss builds a storefront index, because summaries carry no `storefrontId`.
  - `resolveByType` also indexes failed connectors (2.3.0 contract).
  - Still no key or shape change.
- **2026-11-05** — FUSE-1350 is fixed as a default-behaviour patch (2.5.2) ahead of the opt-in series (Harry: "let's raise the defect and remediate it at the same time"). It's a correctness fix with no key or shape change, so making it opt-in would leave fapi and shopify exposed.
- **2026-11-05** — (e) returns raw handler errors (which may carry the axios `cause` and its headers) rather than 2.4.0's message-and-status-only shape. shopify-egress classifies on `cause`, so stripping it would make the outcomes useless to the consumers most likely to adopt them. Containment is `serialiseError` (G6), which handles `AggregateError` members, and the README tells callers to use it. (Claude, from the history review; it changes no default.)

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->

- remote-config 2.5.1's business index is created from a single backlink when its key is missing (`connector.handler.ts:497-531`). Cached `resolve`/`resolveWithUnresolved` calls then miss every other connector of the business, same type or not, until the index expires. That's E8's failure class, live in fapi and shopify today. Filed as FUSE-1350 and fixed in inc 1.
- The org changelog has no remote-config **2.5.0** entry, though 2.5.0 changed the TTL unit, made `memory` mode build and changed `init()` on a Redis outage. Backfilled in PR 2.
- `validateConnectorDTO` in the connector handler throws a plain `Error` and is unreachable while the client parses with the same schema.
- Config-service's `GET /v1/business/{id}` (connector refs joined on `connector.businessId`) matches the scan's connector set; `/business/{id}/storefront` doesn't (it lists soft-deleted storefronts, and its `total` counts only active ones).
- Vault docs to supersede at sign-off: `architecture.md`'s package table (remote-config 2.3.0, cache 0.3.0), the TTL-units gotcha (`:164`, fixed in 2.5.0), and the fixed-60 s in-memory TTL gotcha (`:165`, made configurable by inc 1).
