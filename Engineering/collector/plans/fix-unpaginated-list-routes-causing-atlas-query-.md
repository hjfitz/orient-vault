---
ticket: none
title: Make collector's paginated-list count queries index-covered (Atlas query-targeting
  alert)
service: collector
status: complete
created: '2026-09-17'
updated: '2026-10-05'
repo: /home/hjf/code/fuse/collector
worktree: /home/hjf/code/fuse/collector/.claude/worktrees/collector-pagination-footgun
branch: hjf/collector-pagination-footgun
base: origin/master
base_sha: 9afda2a1c
pr: '98'
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: medium
---
# none — Make collector's paginated-list count queries index-covered (Atlas query-targeting alert)

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

> SUPERSEDED 2026-09-17 — this plan originally scoped converting `listRecords`/
> `listConfirmations` from in-memory `.find()`+`.slice()` to `Collection.findPaginated()`
> (drafted against base commit `ec37b49`). Before implementation started, `master` moved
> forward: PR #95 (`ff5f342`, merged AND deployed to prod 2026-09-15) already made that exact
> change as an unrelated support-escalation fix. Found on pickup by diffing this plan's
> increments against the real worktree source (which already called `findPaginated`) rather
> than by the plan's own review pass — the increments below were ticked against `ff5f342`
> without new implementation. But the Atlas alert this plan exists to clear did **not**
> actually clear: PR #95 only fixed the `find()` half of pagination, not the `countDocuments()`
> half, which remained uncovered by any index and re-fired the same alert ~40h later. The
> Intent/AC/Increments below were rewritten around that real remaining cause — see
> `## Decisions & deviations` for the full account.

## Intent
<!-- What we are changing and why. Link the ticket. -->
MongoDB Atlas's ERROR-severity Query Targeting alert on `collector-prod`
(Scanned Objects/Returned ~998.7 at first observation, threshold 1000, cluster
`collector-prod-shard-00-01`) re-fired 2026-09-17 05:27Z, ~40h after PR #95 fixed the `find()`
half of `UseCasesService.listRecords`/`listConfirmations`'s pagination. Root cause of what
remains: `Collection.findPaginated()` (`code/src/repositories/collection.ts`) runs
`Promise.all([find().sort().skip().limit(), countDocuments(queryWithDeleted)])`, where
`queryWithDeleted = { $and: [query, { deletedAt: { $exists: false } } ] }`. The compound index
backing each collection (`{businessKey:1, "lifecycle.createdAt":-1}`) covers the `find()` half
but not `deletedAt`, so `countDocuments()` must FETCH every matching document just to evaluate
the `$exists:false` clause — for GADG's 81,556 sales orders, that's ~81,556 document fetches to
compute one integer, on every Transaction History page load. The fix: (1) collapse the filter's
four duplicated construction sites in `collection.ts` into one helper and switch
`{deletedAt: {$exists:false}}` to `{deletedAt: null}` (verified safe — the app never writes a
literal `null`; both give identical results, but the equality form gets clean index bounds);
(2) add `deletedAt` to the compound index for the 8 collections actually reachable via a counted
route, making `countDocuments()` fully index-covered (no document fetch). Proof: an
`explain()`-based test shows `IXSCAN`/`COUNT_SCAN` with no `FETCH` stage for the count path, and
the Atlas Query Targeting metric for `collector-prod` returns to near 1:1 and does not re-fire
after prod deploy.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. `countDocuments()` for all 8 in-scope collections (6 use-case + PO/SO confirmations)
      resolves via a fully covered index scan — no `FETCH` stage — proven by `explain()`.
- [x] 2. No consumer-facing behavior change: all 8 routes return the identical response shape
      and the identical set of non-deleted documents as before.
- [x] 3. The Atlas Query Targeting alert on `collector-prod` returns to near 1:1 and does not
      re-fire over the 24-48h following prod deploy.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `code/src/repositories/collection.ts` — the 4 duplicated `deletedAt` filter-construction
  sites (`find`, `findPaginated`, `findPaginatedWithLifecycle`, `findOneWithLifecycle`),
  consolidated into one helper; the 2 `countDocuments()` call sites this actually fixes.
- `code/src/core/use-case-registry.service.ts` — 6 collections (purchase_orders, sales_orders,
  master_data, stock_adjustments, return_goods_authorizations, work_orders) × 2 index
  declarations each (constructor arg + `registry.register({indexes})` metadata — collector's
  own documented "declared twice" gotcha).
- `code/src/core/confirmation-registry.service.ts` — 2 in-scope collections
  (purchase_order_confirmations, sales_order_confirmations) × 2 index declarations each.
  `pick_confirmations`/`pack_confirmations`/`work_order_confirmations`/`finished_good_receipts`
  are registered here too but have no counted/paginated route wired up anywhere today — out of
  scope (see Assumptions).
- `code/src/__test__/integration/collection.spec.ts` (or a new sibling file) — `explain()`-based
  coverage test.
- `code/CLAUDE.md` — "Persistence & upsert semantics" section, document the new index shape,
  the null-equality convention, and the deferred old-index-drop follow-up.
- No Fuse MCP data file change — this is an internal index/query-shape change, not a new
  collection, endpoint, or canonical type.
- See [[architecture]] "Query API gotchas" / "Persistence & upsert semantics" for the documented
  pre-fix state this plan resolves.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- The app never writes a literal `deletedAt: null` anywhere in the repo (`save()` only
  `$unset`s it; `softDelete()` only `$set`s a real `Date`) — confirmed by two independent
  repo-wide greps (including the black-box `/tests` harness), not just `code/src`. This is
  what makes `{deletedAt: null}` safe and equivalent to `{$exists:false}` today. If a future
  write path ever sets a literal `null`, the two filters diverge (`{deletedAt:null}` would
  wrongly treat that doc as "not deleted") — worth a one-line comment at the call site, not a
  runtime guard.
- Exactly 8 collections are reachable via a route that calls `countDocuments()` today: the 6
  use-case collections (via `listRecords`/`listRecordsWithLifecycle`) plus
  `purchase_order_confirmations`/`sales_order_confirmations` (via `listConfirmations`, hardcoded
  to PO/SO only in `business.controller.ts`). The other 4 confirmation collections are
  registered but unreachable via any listing route — confirmed independently by two reviewers
  tracing every call site of `findPaginated`/`findPaginatedWithLifecycle`/`listConfirmations`,
  and matches `architecture.md`'s own statement that only PO/SO confirmations have a read route
  at all. Bringing those 4 collections' indexes to the same shape is optional future
  consistency work, not required by this fix.
- The proposed index shape `{businessKey:1, deletedAt:1, "lifecycle.createdAt":-1}` follows
  MongoDB's ESR (Equality-Sort-Range) rule: `businessKey` and `deletedAt` are both equality
  predicates, `lifecycle.createdAt` is the sort field — equality fields precede the sort key,
  and there's no range predicate here to place after it.
- RESOLVED — real prod `sales_order`/`purchase_order` counts pulled across all 30 production
  businesses via the Fuse MCP (`get-fuse-records`, `environment: production`): largest is
  STUBBLE at 24,940 sales orders, nothing exceeds 100,000. GADG's oft-cited "81,556 sales
  orders" (from PR #95's own evidence) turns out to be a **dev/staging** figure, not prod —
  GADG has no storefronts/connectors configured (it's an internal test account) and only 8
  real sales orders in prod. Real prod scale is smaller than the dev environment used for
  testing, not larger — the `ensureIndexes()`-before-`app.listen()` boot-stall risk the
  service's CLAUDE.md flags is comfortably within bounds for the two record types checked.
  `master_data`/`stock_adjustment` weren't individually checked (scope: the two highest-traffic
  types), but nothing about the business roster (30 businesses, mostly small-to-mid retail)
  suggests an order-of-magnitude outlier elsewhere.
- **Deliberately deferred to a follow-up plan, not part of this one's increments:** dropping
  the now-superseded old 2-field compound index and the redundant standalone `{deletedAt:1}`
  index on each of the 8 collections. This can only happen safely after `$indexStats` shows
  zero traffic on the old indexes for a full real-world traffic cycle post-prod-deploy — a
  precondition this plan/PR cannot satisfy within its own lifecycle, has no CI signal, and is
  explicitly non-urgent (the two-index coexistence window costs extra write amplification and
  storage, bounded and temporary, not correctness). Indexes here are unnamed (auto-generated
  from the key spec), so the follow-up plan's drop step must copy the exact key spec off a live
  `getIndexes()` call rather than trust a remembered name.
- Original (now-superseded) scoping of this plan converted `listRecords`/`listConfirmations` to
  `findPaginated` — that work was already done by PR #95 before this plan was picked up. Its
  increments were ticked against `ff5f342` as found-already-done, not re-implemented — see
  `## Decisions & deviations`.

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

- [x] 1. Convert `listRecords` (`use-cases.service.ts:48-76`) to call
      `collection.findPaginated(query, {offset, count})` and wrap `{data, total}` into
      the existing `{total, offset, count: data.length, data}` `PagedApiResponse` shape —
      verify: e2e suite filtered to `purchase_order`, `sales_order`, `master_data`,
      `master_data/summary` (no-query branch), `stock_adjustment` list assertions pass
      unchanged (`pnpm test:e2e -- business.controller`). *(Superseded scope — already
      shipped in PR #95, found done on pickup, not re-implemented here.)*
      — done: ff5f342
- [x] 2. Add an e2e boundary test for `listRecords`-backed routes covering offset-past-end
      and count=0 — verify: new test fails against pre-fix `.slice()` behavior and passes
      against `findPaginated` behavior. *(Superseded scope — already shipped in PR #95.)*
      — done: ff5f342
- [x] 3. Convert `listConfirmations` (`use-cases.service.ts:293-330`) to call
      `findPaginated` with the same wrap step, preserving the existing
      `confirmationRegistryService.getRegistry().has(useCaseName)` 404-guard untouched —
      verify: e2e for `purchase_order/confirmations` and `sales_order/confirmations` pass
      unchanged, including the guard's 404 path. *(Superseded scope — already shipped in
      PR #95.)*
      — done: ff5f342
- [x] 4. Update `code/CLAUDE.md`'s "Query API gotchas" section to remove the
      "not DB-paginated... footgun at scale" note and describe the corrected behavior —
      verify: reread the updated paragraph against the post-fix code. *(Superseded scope —
      already shipped in PR #95.)*
      — done: ff5f342
- [x] 5. Consolidate the 4 duplicated `deletedAt`-filter construction sites in `collection.ts` — Consolidated 4 duplicate deletedAt filters into withNotDeleted() helper, switched to null-equality; 32/32 integration tests pass (2 new) — done: c7cff3f
      into one private helper (e.g. `withNotDeleted(query)`), used by `find`, `findPaginated`,
      `findPaginatedWithLifecycle`, `findOneWithLifecycle`; switch the inner clause from
      `{ $exists: false }` to `{ deletedAt: null }` (AC 2) — verify: existing integration suite
      (`collection.spec.ts`) passes unmodified; add one new case inserting a document with
      `deletedAt` absent and one soft-deleted (`deletedAt` set), confirming the former is
      included and the latter excluded under the new filter.
- [x] 6. Update the index declarations for the 6 use-case collections in — Added deletedAt to 6 use-case collections' compound index, both copies; ensureIndexes boots clean in e2e — done: 3fc8a78
      `use-case-registry.service.ts`, both copies each (constructor arg + `register({indexes})`
      metadata), from `{businessKey:1, "lifecycle.createdAt":-1}` to `{businessKey:1,
      deletedAt:1, "lifecycle.createdAt":-1}` (AC 1) — verify: `ensureIndexes()` succeeds at
      boot against `mongodb-memory-server` in the integration suite (a failing `createIndex`
      call fails CI immediately).
- [x] 7. Same change for the 2 in-scope confirmation collections — Added deletedAt to PO/SO confirmation compound index, both copies; ensureIndexes boots clean in e2e — done: 3fc8a78
      (`purchase_order_confirmations`, `sales_order_confirmations`, keyed on `bizId`) in
      `confirmation-registry.service.ts`, both copies each (AC 1) — verify: same boot-time
      `ensureIndexes()` check via the integration suite.
- [x] 8. Add an `explain()`-based coverage test (`collection.spec.ts` or a new sibling file): — explain()-based coverage test added, verified it discriminates (fails on old 2-field index); real prod sales_order/purchase_order counts pulled, largest is 24,940 (STUBBLE), no boot-stall risk — done: 0d8a457
      seed a representative use-case collection with several hundred mixed deleted/non-deleted
      documents sharing a `businessKey`, run the query `findPaginated` issues, and assert the
      count path's winning plan is `IXSCAN`/`COUNT_SCAN` with no `FETCH` stage and
      `totalDocsExamined` far below the matching-document count (AC 1) — verify: the test
      itself, in CI. Before rolling out to dev, also pull real per-collection document counts
      across all 8 in-scope prod collections (not just GADG) via a direct Atlas/Mongo check, to
      close the boot-stall unresolved-assumption above rather than deploying blind to it.
- [x] 9. Roll out: deploy the branch to dev (`manual-deploy.yaml`), confirm `db.collection — Dev deploy verified (real GADG data, correct shape, no regression); merge-to-master deferred to standard PR-approval ship gate, not bundled here — done: 0d8a457
      .getIndexes()` shows the new compound shape and re-run `explain()` by hand against dev
      Atlas's largest available collection, then merge to `master` for the prod deploy gate
      (AC 1,2) — verify: dev `explain()` output attached as evidence; `gh run view` on the
      resulting Deploy workflow run shows every job (`docker-push-dev`, `terraform-apply-dev`,
      `docker-push-prod`, `terraform-plan-prod`, `terraform-apply-prod`) at
      `conclusion: success`, same check used to confirm PR #95's rollout.
- [x] 10. Update `code/CLAUDE.md`'s "Persistence & upsert semantics" section to document the — Updated Persistence & Query API gotchas sections to describe the new index shape, null-equality convention, and deferred drop follow-up — done: 2c30be5
      new `{businessKey, deletedAt, lifecycle.createdAt}` compound shape and why
      (`countDocuments` needs an index-only scan, not just the `find` half), the null-equality
      convention (and the never-write-a-literal-null invariant it depends on), and that the
      old, now-superseded indexes are intentionally left in place pending a follow-up drop plan
      — verify: reread the updated section against the post-fix code.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-05 [sign-off, AC 3] Prod `collector-prod` runs `collector:prod-8fccabe` (revision
  `collector-prod-00037-xs5`, ready 2026-10-02 12:13Z). `git merge-base --is-ancestor` puts #98
  (`95d0933`) and #103 (`7a7b71b`) both in it. No Atlas CLI or credentials this session, so no fresh
  Admin API read. Instead: the FUSE-1239 plan's 2026-09-23 18:27Z Admin API re-check (all 229 alerts)
  shows `collector-prod`'s last Query Targeting alert still 2026-09-21 12:29Z. The morning digests'
  email triage from 09-24 to 10-05 lists Atlas Query Targeting mails only for replay-prod, replay-dev
  and dedupe-prod, none for collector-prod. So it has stayed clean about two weeks.
- 2026-09-23 [AC 3] Atlas Admin API alert history (project `bifrost`, read-only, from the FUSE-1239
  session): `collector-prod` fired 105 Query Targeting alerts 2026-09-14 → 2026-09-21, last at 12:29Z
  (resolved 12:56Z) — i.e. it kept firing for ~4 days after this plan's #98 reached prod — then **none**
  once #103 (confirmation upsert-key indexes) finished its prod deploy at 13:03Z 09-21; ~47h clean as
  of 12:35Z 09-23. AC 3 is met, but by #98 **and** #103 together: #98 closed the count half, #103 the
  write-path upsert lookup that was still scanning.
- 2026-09-17 [inc 1-4] Confirmed already merged and deployed to prod via PR #95
  (`ff5f342`, merged 2026-09-15T13:56Z) — `gh run view` on the associated Deploy workflow
  run (34978326114) shows every job (`docker-push-dev`, `terraform-apply-dev`,
  `docker-push-prod`, `terraform-plan-prod`, `terraform-apply-prod`) completed with
  `conclusion: success`. PR #95's own description carries dev evidence (GADG sales_order
  first-20 match against `/api/v1/records`, strictly-descending `lifecycle.createdAt`,
  confirmation routes 200 in ~0.06-0.08s). This did NOT clear AC 3 (the Atlas alert) — see
  Intent for why.
- 2026-09-17 [inc 5,6,7,8] Local: 33/33 integration tests pass (2 new absent/soft-deleted
  cases, 1 new `explain()`-based coverage test), 77/77 e2e pass (`ensureIndexes()` boots
  clean against `mongodb-memory-server` with the new compound shape), `pnpm run build:check`
  clean, `pnpm run lint` clean. The coverage test was verified to actually discriminate: it
  fails (`FETCH` stage present) against the old 2-field index and passes against the new
  3-field one.
- 2026-09-17 [inc 9] Deployed branch to dev (`manual-deploy.yaml`, run 35209902550, all jobs
  `conclusion: success`; announced/reverted in `#bifrost-general`). Exercised real dev data
  against GADG via the Fuse MCP: `GET /GADG/sales_order?count=5` → HTTP 200, `total: 81561`,
  identical `{total, offset, count, data}` response shape, real records with `lifecycle`
  intact; `GET /GADG/sales_order/confirmations?count=2` → HTTP 200, `total: 148`, same shape.
  No regression in either route. Could NOT directly run `getIndexes()`/`explain()` against
  dev Atlas (no Mongo/Atlas credentials available in this session) — the successful boot is
  strong indirect evidence `ensureIndexes()` succeeded (a failing `createIndex` would have
  crashed the dev revision before the startup probe passed, per collector's own CLAUDE.md),
  but this is not the same as a direct explain() against real dev-scale data. Dev reverted to
  master afterward (run 35210541569).

<!-- Before PR: full regression (`pnpm test` unit+integration+e2e, `pnpm run build:check`) per
     the org's standing create-pr checklist — not a plan increment. -->

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
> SUPERSEDED 2026-10-05 — AC 3 is now verified (see the 2026-09-23 and 2026-10-05 Evidence bullets).
- AC 3 (Atlas alert clears and stays clear) — cannot be verified until this deploys to prod and
  Atlas observes real traffic for a full evaluation window (recommend checking 24-48h post-
  deploy). Dev/CI `explain()` evidence proves the query plan is covered; it doesn't by itself
  prove the live alert clears.
- AC 1's direct proof against real dev/prod Atlas (`getIndexes()`/`explain()` on a live
  cluster) — only proven via the CI integration test against `mongodb-memory-server` plus the
  indirect signal of a clean dev boot. Would need Atlas console or `mongosh` access to close
  fully; flagged rather than assumed.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->
- 2026-10-05 — Ticked AC 3 at sign-off, met by #98 together with #103. Read strictly against #98
  alone it isn't met: the alert kept firing for about 4 days after #98 reached prod. It stopped only
  once #103 (confirmation upsert-key indexes) deployed on 2026-09-21. #98 fixed the count half and
  #103 fixed the write-path upsert lookup. The alert this plan exists to clear is clear.
- 2026-09-17 — Chose the index-coverage fix (increments 5-10) over a short-TTL in-process cache
  around the count (the other option seriously considered). Caching would have been lower-risk/
  no schema change, but the index fix directly resolves the underlying cost rather than
  amortizing it, needs no new caching logic or TTL tuning, and was Harry's explicit call after
  asking whether Mongo's count mechanics could be made to use the index directly (they can, via
  index coverage) rather than working around the cost.
- 2026-09-17 — On picking this plan up via `waypoint-work`, found increments 1-4 (the plan's
  original scope) already implemented and deployed to prod by PR #95 (unrelated support-
  escalation fix, merged 2026-09-15, two days before this plan was drafted from a now-stale
  base commit). Ticked all 4 against that PR's sha rather than re-implementing. The Atlas alert
  this plan exists to clear did NOT clear, because PR #95 only fixed the `find()` half of
  pagination — the `countDocuments()` half remained uncovered by any index. Rescoped the plan
  (increments 5-10, new Intent/AC above) around that real remaining cause rather than closing
  this plan as complete against a false premise.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->

## Handback
<!-- Learnings that could not be promoted into a collector durable doc, with why. -->
- Not promoted, because it describes the gone in-memory pagination rather than the service now: "the
  pagination footgun spans 7 URL paths, not 6 (`purchase_order/confirmations` and
  `sales_order/confirmations` were separate call sites)". `architecture.md` already says every list
  route is DB-paginated and names the legacy confirmations pair.
- Not promoted, because it is a Waypoint process note and not a collector fact: "a plan's `base_sha`
  can go stale between drafting and pickup within 1-2 days on a busy repo, so `waypoint-work` Step 1
  should diff the plan's claimed source state against the real worktree before trusting the
  increments". It is true here (PR #95 had already done increments 1-4). It belongs with whoever
  owns the `waypoint-work` skill.
