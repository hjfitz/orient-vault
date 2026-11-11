---
ticket: none
title: 'remote-config: close the connector-cache gaps left by evictOnDelete'
service: pkg-node
status: active
created: '2026-11-09'
updated: '2026-11-11'
repo: /home/harry/code/fuse/pkg-node
worktree: /home/harry/code/fuse/.worktrees/pkg-node-rc-2.7
branch: hjf/remote-config-username-lookup-settled
base: origin/main
base_sha: 9246cf92c
pr: '309'
tags:
- waypoint
- plan
impl_model: opus
impl_effort: high
---
# none — remote-config: close the connector-cache gaps left by evictOnDelete

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
- **2026-11-11: the default-mode lost add is deferred** (Harry: "proceed" on the recommendation). It stays a documented README limit until a lost add is seen in prod. Fixing it needs a cache primitive that tells a failed Redis read from a miss, plus a default change. Revisit it together with the compare-and-set option.
- **2026-11-09: this ships after 2.7.0, not folded into it.** The gaps are in opt-in behaviour, 2.7.0's release gate and "defaults unchanged" claim would be invalidated, and sftp-connector step 4 needs 2.7.0. This reverses my earlier suggestion to Harry to hold the 2.7.0 merge for it, which was made before the reviews found the outage hazard.
- **2026-11-09: a single lookup that hits a tombstone in the re-check behaves as not-found.** Its only consumer, sftp-connector, already maps a missing connector to `ConnectorConfigException`.

## Intent
<!-- What we are changing and why. Link the ticket. -->
Close the connector-cache gaps that `@gfs-bifrost/remote-config` 2.7.0 documents for `evictOnDelete` ([[remote-config-2-6-2-7-opt-in-connector-handling-|parent plan]], stack B, pkg-node#304-306). The goal: a deleted connector stops being served from the cache, and stops being listed in a business or storefront index, even when a refresh races the delete or the connector's cached copy has already expired. sftp-connector, the first `evictOnDelete` consumer, gets that guarantee behind the same option. Every other consumer's defaults are unchanged. Out-of-ticket; Harry, 2026-11-09: "let's plan the fix with waypoint".

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. With `evictOnDelete`, deleting a connector never writes back a cached copy of an index. A connector another instance added to the same business within `memTtl` is still listed after the delete.
- [ ] 2. With `evictOnDelete`, a refresh that fetched the connector before its `version -1` was applied leaves no primary key, index entry or alias behind. That holds whichever instance applies the delete, and both orderings are proven in a two-instance spec.
- [ ] 3. With `evictOnDelete`, deleting a connector whose cached copy has already expired still stops it being served or listed. The next `resolve`/`resolveWithUnresolved`/`resolveByStorefrontId` for its business or storefront makes no config-service call for that id, and the deleted connector isn't in the result.
- [ ] 4. Without `evictOnDelete`, every behaviour is identical to 2.7.0. Existing specs pass unedited in behaviour, and the 2.5.1 type test compiles. The 2.3.0 contract holds: a 404 for a connector the list returned stays `unresolved`.
- [ ] 5. The windows that remain are written in the README "Limits" paragraph, correct at every merge.
- [ ] 6. 2.8.0 is published with its changelog row, the pkg-node `CLAUDE.md` row, the README, and fuse-mcp `config-domain.json` (the CONNECTOR entry rewritten).

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- **`pkg/remote-config/src/handlers/backlinks/connector.handler.ts`:** `refreshOrEvict`, `evictConnector`, `removeFromIndex`, `cacheConnectorWithIndices` and its seven callers, `resolveWithUnresolved`, `resolveByStorefrontId`, `resolveByUsername`, `resolveByConnectorId`.
- **`pkg/remote-config/readme.md`:** the "Connector handling" section and its "Limits" bullet.
- **`pkg/remote-config/src/__tests__/connector-backlink.handler.spec.ts`:** the new two-instance harness.
- **Cache keys:** a new `connector-deleted:{connectorId}` key. Existing keys and value shapes are unchanged, because 2.7.x and 2.8.0 instances share Redis during a rollout.
- **`@gfs-bifrost/cache` 0.4.0:** no change. Read-only reference: `cache.service.ts` `tryGetAsync` serves L1 first (`:391-425`), and reconnect deletes keys whose writes failed (`:261-325`; see `pkg/cache/CLAUDE.md`).
- **Consumers:**
  - sftp-connector ([[move-the-connector-onto-the-shared-remote-config|its plan]], step 4 gate) is the only `evictOnDelete` user.
  - fapi (`^2.x`) and shopify-connector (exact pin) don't opt in.
- **fuse-mcp `data/config-domain.json:238`:** the CONNECTOR `cacheKeyPattern` and `fetchBehavior` are wholly stale (`connector:{businessId}`).

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **Deletes are final:** config-service connector ids are `conn_${uuid}`, never reused (`storefront.service.ts:158`), and deletes are hard. Seed fixtures and sftp-connector's black-box mock use fixed ids (`conn_123`), so specs and fixtures must use unique ids, or a tombstone suppresses a re-created fixed id for a TTL. Established: source read, history review.
- **Only one delete path publishes `version -1`: the per-connector delete** (`storefronts.controller.ts:287`, best-effort publish).
  - Storefront delete hard-deletes its connectors and publishes nothing.
  - Business delete soft-deletes and publishes nothing (`business.controller.ts:181` `// TODO: dispatch event????`).
  
  So no consumer-side mechanism here can tombstone those; see Learnings. Established: source read (factual review).
- **Redis ordering:** one node-redis client per `CacheService` runs commands in send order. Retried writes settle before a later command on that connection. Across a reconnect (heartbeat recycle or socket error) a dropped command can land late; `disableOfflineQueue` keeps that narrow. The tombstone ordering argument rests on this. Established: source read of `redis.cache.ts` and `@redis/client`.
- **Failed reads look like misses:** `tryGetAsync` swallows Redis errors and timeouts and returns `undefined`. A tombstone read therefore fails open while Redis is down. That's an accepted, documented window, not a defect. Established: source read (`cache.service.ts:421-424`).
- **`rc:` isn't a real prefix:** `CacheService` stores the `rc:` key prefix and never applies it, so Redis keys are unprefixed. The sftp-connector plan assumes `rc:` separates them from its old `cfg` keys. That needs checking there before step 4 (new keys here: `connector-deleted:*`). Established: source read, both reviews.
> SUPERSEDED 2026-11-11: resolved. Harry said "proceed" to the recommendation, so it is deferred and documented as a known limit (see Decisions).
- **UNRESOLVED: is the default-mode lost add worth a cache release and a second default change?**
  - The race: two *new* connectors for one business are added on different instances within `memTtl`. The second instance writes its stale in-memory index back, and one connector is silently missing from that business's lookups until the index TTL. It's older than 2.7.0, and rare: fapi saw 14 connector backlinks in 7 days.
  - Fixing it safely needs a cache primitive that tells "Redis failed" from "not found". Dropping the in-memory copy before reading turns a Redis outage into the 2.5.2 silent-omission bug.
  - Recommendation: defer, record it as a known limit, and revisit if a lost add is ever observed. Raised with Harry, 2026-11-09.

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
- [x] 1. **Clear, don't rewrite, an index on delete** (AC 1,4,5). Opt-in under `evictOnDelete`. `removeFromIndex` deletes the business and storefront index keys outright instead of writing back a copy with one id removed. Deleting a key isn't a read-modify-write, so a stale in-memory copy can't drop another instance's addition. — two-instance harness reproduces the lost add on 2.7.0 and passes after; 311 tests — done: a26ceba
      - **Cost:** one full fetch of that business or storefront (list plus one GET per connector) per delete per consuming service. Deletes are an admin action.
      - **Tests:** first add the two-instance harness: two real `CacheService` + `LruCache` over one Map-backed `INetworkCache`, both `init()`-ed. The existing single-Map mocks can't model memory copies.
      - **README Limits:** remove the "two instances changing one index" sentence.
      — verify: harness spec "keeps a connector another instance added within memTtl when a delete lands" (red on 2.7.0 first, then green), "deletes the business index on deletion", "deletes the storefront index on deletion", "the next resolve rebuilds the index from config-service"; 2.7.0's eviction specs updated where they asserted a rewritten list.

- [x] 2. **Write a deletion tombstone** (AC 2,3,4). Under `evictOnDelete`, a `version -1` backlink writes `connector-deleted:{id}` (`trySetAsync` Both, throwing on `false`) before any other removal. It's written even when nothing was cached. Only an authoritative `-1` writes it; a 404 on refresh evicts as now but writes none. An update backlink for a tombstoned id is acked without a GET. — 7 specs, 4 mutations caught; 318 tests — done: cec575a
      — verify: "writes a deletion tombstone", "writes it when the connector was never cached", "rejects when the tombstone can't be written", "writes no tombstone on a 404", "acks an update backlink for a deleted connector without calling config-service".

- [x] 3. **Re-check the tombstone after every cache write** (AC 2). Under `evictOnDelete`, `cacheConnectorWithIndices` reads `connector-deleted:{id}` after writing the primary key, index entries and alias. If it's present, it evicts with the copy it just wrote. The caller then drops the connector: — two-instance race specs for refresh, byId, scan and server-filtered username, business resolve; 6 mutations caught; 329 tests — done: 75c7604
      - list calls (`resolve`/`resolveWithUnresolved`/`resolveByStorefrontId`/`resolveByType`) leave it out;
      - single calls (`resolveByConnectorId`/`resolveByUsername`/refresh) behave as for a not-found.
      
      Name each of the seven callers in the spec matrix. The ordering argument and its reconnect caveat go in the README.
      — verify: two-instance race specs (a deferred `getConnector` on A, a `-1` on B, then A's fetch released): "leaves no primary key", "leaves no business index entry", "restores no username alias", the same for `resolveByConnectorId`'s fetch and for a business resolve; "a single lookup throws not-found when the re-check finds a tombstone"; mutation-check the re-check.

- [x] 4. **Prune tombstoned ids when reading, then release 2.8.0** (AC 3,5,6). Under `evictOnDelete`: — 11 specs, 5 mutations caught; dev proof HJF 12 -> 11, 0 config-service requests; 340 tests — done: 2fa6010
      - On a partial miss in `resolveWithUnresolved`/`resolveByStorefrontId`, read the tombstones of the ids whose primary key is missing.
      - Remove tombstoned ids from the index. This is best effort: a failed write isn't thrown on a read path.
      - If the rest are cached, serve them with no config-service call. If pruning empties the index, fall through to the existing marker check and fetch; never return `[]` without one.
      - `resolveByUsername` deletes an alias that points at a missing, tombstoned primary.
      
      Release: version 2.8.0, the org changelog row, the pkg-node `CLAUDE.md` row, README "Limits" rewritten to the remaining windows, and fuse-mcp `config-domain.json` CONNECTOR entry rewritten (straight to fuse-mcp `master`).
      — verify: under "when the index lists a deleted connector whose primary key has expired": "removes it from the business index", "resolves from cache without calling config-service", the same for the storefront index, "fetches when pruning empties the index"; "deletes a username alias that points at a deleted connector"; "without evictOnDelete still refetches on a partial miss"; the release gate (2.5.1 type test, pack, fapi and shopify-connector suites against the tarball); a dev proof with a script against the built package and dev config-service: synthetic `-1` records through `processRevisionSettled`, with the gap-3 state seeded (primary removed, index still listing it).

- [ ] 5. **Reconcile an index against config-service on a complete fetch** (AC 3). Opt-in. This is the only backstop for deletes that emit no `-1` (storefront or business deletes, or a lost publish) and for tombstones that have expired.
      - For indexed ids absent from the fetched summaries and with no cached primary key, GET each: a 404 removes it from the index; a 200 for the same business keeps it.
      - Capped per business per TTL, because of the FUSE-952 load lesson.
      - A 404 for an id the list *did* return stays `unresolved` (the 2.3.0 contract).
      
      gate: prod logs from an `evictOnDelete` consumer show repeated "Partial cache miss" for one business beyond the tombstone TTL, or config-service ships delete events for storefront and business deletes and they still leave orphans.
            [ ] confirmed
      — verify: "removes an indexed connector config-service 404s", "keeps an indexed connector config-service returns", "leaves the index on a 503", "fetches at most once per business per TTL", "still reports a listed 404 as unresolved".

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-11-11 [AC 6] **2.8.0 published.**
  - pkg-node#309 was squash-merged as `f730dc0`, after 2.7.0 (`c3c89b4`).
  - The publish run succeeded, and `npm view @gfs-bifrost/remote-config@2.8.0` resolves.
  - Fuse MCP `config-domain.json` CONNECTOR entry rewritten, and `shared-packages.json` updated (fuse-mcp `30b38bd`, `go test ./internal/...` green after `make parity-accept`).
  - The branch commits stamped on incs 1–4 were squashed into `f730dc0`.
- 2026-11-11 [incs 1–4, AC 1–6 except publish] **Draft pkg-node#309** (`3ebd33f`), stacked on #306 as stack #307.
  - **Lost update (AC 1):** the two-instance harness (a real `CacheService` + `LruCache` per instance over one shared network cache) made 2.7.0 drop a connector another instance added. That spec failed on 2.7.0 and passes after inc 1.
  - **Races (AC 2):** the two-instance race specs (fetch held, `-1` on another instance, fetch released) cover refresh (acks), by-id (404-shaped), scan and server-filtered username, business, storefront and by-type. Nothing deleted is left cached, listed or aliased.
  - **Expired copy (AC 3), dev proof against dev config-service (read-only):** business HJF, 12 SFTP connectors. One connector's primary key was removed and a synthetic `-1` sent: 0 requests. The next `resolveWithUnresolved(HJF, sftp)` returned 11 connectors without the target, 0 unresolved, 0 requests. Run on `2fa6010` and again on the final build.
  - **Defaults (AC 4):** the packed 2.8.0 passes fapi `007ad5c` (529), shopify-connector `84714fc` (902) and shopify-egress-service (634). `build:check` everywhere, plus `build:check:tests` in egress. The 2.5.1 type test compiles. The default-mode specs pin no tombstone write and no tombstone read.
  - **Tests:** 354 (46 new). 25 mutations, all caught.
  - **Review panel** (backend, data, tests) found real issues, fixed in `6e45546`:
    - empty markers are now cleared with a dropped index; a stale one would hide a live connector;
    - a failed eviction warns on a lookup instead of failing it;
    - a failed index drop warns;
    - added: the storefront and by-type races, the refresh-ack spec, and the failure-path specs;
    - fixed: two vacuous default-mode specs.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- **Races and in-memory windows can't be reproduced on dev.** The two-instance harness specs are the only race evidence.

## Rollout & rollback
<!-- Added on demand. Written at plan time; amend in place as it changes.
     `Shared state touched:` is the single home for the five classes git does not own — a dev
     deploy, a prod config write, a Datadog monitor, a CI var or secret, cross-repo IaC. Reverting
     the branch undoes none of them, so if they are not written here they are not written down. -->
- **Order:**
  - Wait until 2.7.0 (pkg-node#304-306) merges. Then incs 1–4 merge as one stack in one sitting, with the version bump in inc 4. Incs 1–3 carry no bump, so nothing publishes between them, and each keeps README "Limits" true at its merge.
  - **sftp-connector:** if 2.8.0 publishes after its step 4 starts its 7-day prod shadow on 2.7.0, the shadow restarts on 2.8.0, because `evictOnDelete` gains a new reject mode (a failed tombstone write nacks). Update that plan's step 4 gate to name the version actually shadowed.
- **Flags/config:** none new. Everything rides on `withConnectorHandling({ evictOnDelete: true })`.
- **One-way doors:** publishing 2.8.0. fapi auto-takes it with defaults, protected by AC 4.
- **Rollback:** consumers pin back to 2.7.x. Tombstone keys expire on the consumer's Redis TTL, and older versions ignore them.
- **Shared state touched:**
  - GitHub Packages: one publish, version-gated.
  - Renovate bump PRs in fapi and shopify-connector.
  - fuse-mcp `data/config-domain.json`, straight to `master`.
  - Dev config-service: read-only proof script, with the dev API key held in memory and never printed.
  - **(none)** for prod config, Datadog and IaC.
- **Proof in prod:** none from this plan. sftp-connector's step 4 proves it, by showing no "Partial cache miss" for a business after one of its connectors is deleted.

## Options considered
<!-- Added on demand. Why this approach and not the others — the thing the planning agent is
     asked for and the plan has otherwise had nowhere to put. Promote to a durable record with
     `wp decide --record` when it is worth defending in a review six months out. -->
- **Chosen: clear the index on delete, plus a tombstone checked after writes and when reading.** No cache release is needed, defaults are unchanged, and the windows left are bounded by `memTtl` and documented.
- **Rejected: re-read the index from Redis (drop the in-memory copy first) in every read-modify-write.** During a Redis outage `tryGetAsync` returns `undefined`, indistinguishable from "no index". With `createIfMissing` that rewrites an index holding only the new ids, which is the 2.5.2 class. Making it safe needs a cache primitive that reports "failed" separately. It would also add 2N Redis GETs to every complete fetch.
- **Rejected: a compare-and-set primitive in cache 0.5.0 (Lua).** It needs a cache minor, a Renovate fan-out and a remote-config republish, and it still doesn't protect against old-version writers. All that to close a one-round-trip window. Revisit together with the UNRESOLVED default-mode lost add.
- **Rejected: a lock via `trySetIfNotExistsAsync`.** Its release has no owner check, it rejects while Redis is disconnected, and it adds contention to the fetch path.
- **Rejected: pruning an index to the fetched summaries without a GET.** A typed fetch would drop a live connector of another type (FUSE-1350).
- **Rejected: checking the tombstone on every in-memory hit.** One Redis GET per connector per resolve defeats the in-memory tier. Accept the `memTtl` window instead; sftp-connector can lower `memTtl`.
- **Rejected: write versions on the primary value.** That's a shape change, which is not allowed during a shared-Redis rollout, and deletes are final anyway.
- **Rejected: treating a listed 404 as deleted, or caching other-type connectors during reconcile.** The first narrows the 2.3.0 `unresolved` contract that sftp-connector's AC 5 relies on. The second undoes `backlinkTypes`.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-11-11** — Inc 4 drops the index instead of removing tombstoned ids from it (the plan said 'remove ... best effort'). Rewriting has the same stale in-memory lost-update hazard inc 1 removed; dropping it costs one list fetch on the next lookup.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
- **Dropping an index unmasks the 2.2.0 empty markers.** `*-connectors-empty:{id}:{type|all}` is read only while the index is empty, and joins never clear it. So anything that deletes an index must delete its markers too, or a typed lookup returns `[]` for a live connector until the marker expires.
- **`CacheService.tryGetAsync` serves the in-memory copy first.** So every index read-modify-write in the connector handler works from a copy up to `memTtl` (60 s) old, not a fresh one. A lost update can silently drop a live connector from a fully cached index. In default mode this happens for two new connectors within `memTtl` on different instances.
- **`rc:` isn't applied:** `CacheService` stores `keyPrefix` and never applies it, so remote-config's Redis keys are unprefixed.
- **Storefront and business deletes publish no `config_revision`** (config-service `business.controller.ts:181` TODO). Every consumer cache keeps their connectors until TTL. Candidate config-service follow-up.
- **cache 0.4.0's reconnect loop deletes every key whose write failed during an outage.** A tombstone re-written by a redelivered `-1` in the gap between "Connected" and the loop can be erased. The window is narrow, but it's real.
- **`architecture.md` is stale:** its package table (remote-config 2.3.0, cache 0.3.0) and the TTL-unit and fixed-60 s gotchas are out of date. The org changelog has no cache 0.3.0 or 0.4.0 rows; the reconnect behaviour is only in `pkg/cache/CLAUDE.md`.
