---
ticket: FUSE-1240
title: multi-field reference search in Transaction History
service: fuse-ui
status: complete
created: '2026-09-23'
updated: '2026-09-23'
repo: /home/hjf/code/fuse/fuse-ui
worktree: /home/hjf/code/fuse/fuse-ui/.claude/worktrees/fuse-1240-reference-search
branch: hjf/fuse-1240-search-wiring
base: origin/main
base_sha: cfdb0f56c
pr: '272'
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: high
---
# FUSE-1240 — multi-field reference search in Transaction History

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
[FUSE-1240](https://globalfreight.atlassian.net/browse/FUSE-1240) — UI half of multi-field
Transaction History search; backend is FUSE-1239
([[FUSE-1239-multi-field-reference-search-on-the-v1-records-a]], collector). Support can't find a
record by the reference a customer quotes — today the only lookup is the `?record=` deep link. Add
one search input that sends the typed value to collector's new `?reference=` param for every record
type in the page's current use-case scope and shows the merged matches, with clear loading,
no-results, hidden-by-filters and failure states. Proven when support-shaped searches (customerRef,
sales order number, `#`-toggled Shopify ref, correlation id, Mongo `_id`) find their records on the
preview environment against dev collector, and the same checks pass in prod after release.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. One search input finds records whose Record ID, Correlation ID, Reference, Customer Order
      or SO number equals the typed value, without the user choosing a field or record type.
- [x] 2. A value matching records on several fields or record types shows every match — no
      de-duplication or ranking across types, no field taking silent precedence.
- [x] 3. A search with no matches shows an explicit no-results state naming what was searched;
      matches hidden by the page's other filters say so instead of looking like no results.
- [x] 4. A failing record type is reported by name without hiding the other types' results.
- [x] 5. The search is URL-synced (`?search=`): shareable, Back/Forward-able, and a
      `?search=…&record=…` link opens the record's drawer; plain `?record=` links still work.
- [x] 6. The record drawer shows the Correlation ID when collector supplies it, and it never leaks
      into the Canonical Payload panel or its download.
- [x] 7. The UI never shows unfiltered records as search results — a collector that doesn't honour
      `?reference=` makes search fail closed.
- [x] 8. Transaction History lists every record type collector stores — adding return goods, work
      orders, pick and pack confirmations, work-order confirmations and finished-good receipts — each
      read from `api/v1/records` with the existing table/drawer, and searchable like the rest; RGA's
      confirmation-side status behaviour is verified against source and documented in the PR.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `code/src/modules/transaction-history/` — `transaction-history.const.ts` (`toDisplayRow`,
  `DisplayRow`/`SelectedTransaction`, `TRANSACTION_ENTITIES`), `components/transaction-history-view.tsx`,
  `components/transaction-detail-drawer.tsx`; new `logic/` (+ `logic/__test__/`), `hooks/`,
  `components/transaction-history-search*.tsx`.
- `code/src/app/server-functions/customer/transaction-history.func.ts` — new search-only fan-out
  server function; server-function inputs come from the browser and are validated there.
- `code/src/lib/gen/collector-service.client.d.ts` — regenerated only
  (`gen-collector-service-client`, reads dev collector `/api-json`), never hand-edited.
- Contract consumed: collector `GET /api/v1/records/{recordType}/{businessId}?reference=` plus the
  per-record `correlationId` (collector FUSE-1239 PRs B and C). Record ID matching server-side is
  derived from this repo's `refPaths` chains — editing them won't change what search matches.
- Page URL gains `?search=` as a shareable contract.
- ui-toolkit (`GSearchBox`, from `@ilg-platform/ui-toolkit` 1.35.2 via GitHub Packages).

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- Search scope = the use-case filter's selection (default all), one collector call per type,
  matching entirely server-side — decided with Harry 2026-09-23.
- The page shows 6 record types (`AVAILABLE_USE_CASES`, `transaction-history.const.ts:63-133`:
  purchase_order, goods_in_confirmation, sales_order, goods_out_confirmation, master_data,
  stock_adjustment) — so a default search is 6 collector calls (12 Mongo ops). RGA and work orders
  are searchable in collector but not shown here — source read.
- Browser-invoked server functions run one at a time through Next's router action queue
  (`app-call-server.js` → `app-router-instance.js:108-170`, `runRemainingActions` L51-73), so six
  per-type server-function calls from the client would run sequentially — hence one server function
  that fans out on the server. Source read of installed next.
- Collector ignores unknown query params (no global `ValidationPipe`, `main.ts`), so a collector
  without FUSE-1239 PR B returns the unfiltered newest-first list for `?reference=` — source read.
  PR B also adds a top-level `correlationId` to every record, so a non-empty response whose records
  lack it means collector predates PR B → fail closed (AC 7). No echo field needed from collector.
- openapi-fetch 0.15.2 drops `undefined`/`null` query values but sends `''`, repeats arrays and
  deepObject-encodes objects (`index.mjs:312-321,401`) — the server function must `typeof`-check a
  string and reject blank itself, never mapping blank to "no param".
- `toDisplayRow` rest-spreads everything but `_id`/`lifecycle` into the record body
  (`const.ts:166-179`) — so collector's new `correlationId` would land in the payload panel/download
  unless pulled out first (increment 1).
- `GSearchBox` (toolkit 1.35.2) is controlled, un-debounced, with a `pending` spinner — fits
  submit-to-search; `GSearchInput`/`AppSearchInput` is debounce-only (but `customers-list.tsx:162,356`
  shows the `key=` remount pattern if needed) — source read of installed toolkit.
- jest here runs jsdom with RTL 16.3.2 + jest-dom (imported per spec, no setup file); `renderHook`
  works and a `'use server'` module runs under jest with the API client mocked (mock vars must be
  named `mock*`) — proven with throwaway specs by the facts reviewer. No existing spec does either.
- Collector's request log records `request.path` without the query string
  (`logger.interceptor.ts:51-59`) — dev evidence counts search GETs by correlation id, not by
  `reference=` in the log line.
- Merging to `main` deploys dev only; prod waits on the `terraform-prod` approval (`deploy.yaml`
  `docker-push-prod`, bifrost-admins reviewers). But `main` is shared — every later merge (Renovate
  auto-merges included) parks a run carrying whatever is on `main` — so user-visible search must not
  merge before its collector dependency is in prod. 5 fuse-ui Deploy runs were parked on 2026-09-23:
  `cfdb0f5` (FUSE-1238) plus 4 older than prod's `1b0444b`.
- QA happens on the per-PR preview environment, which runs against dev backends
  (`feature-branch.tfvars` keeps `var.env="dev"`); `manual-deploy` is ruled out (it applies dev
  Terraform with no gate).
- Local runs: copy the main checkout's `code/.env.development.local` (dev collector URI + key);
  `GITHUB_TOKEN=$(gh auth token) pnpm install` (toolkit from GitHub Packages); a throwaway Mongo and
  `BASIC_AUTH_USER` login; `pnpm build` once before `pnpm typecheck` in a fresh worktree (typed
  routes); revert `next dev`'s `next-env.d.ts` edit before committing — ledger/operations recipes.
- RESOLVED 2026-09-23 (Harry) — surface every transaction type: Transaction History shows all 12
  record types collector stores. That wraps in [FUSE-1207](https://globalfreight.atlassian.net/browse/FUSE-1207)
  (RGA, pick, pack, WOC, FGR — Ready for Development, unassigned) plus work orders. RGA and work
  orders are already served on v1; pick/pack/WOC/FGR need collector FUSE-1239 increment 5 first
  (FUSE-1207 assumed they were already served — they aren't). `use-case.const.ts` already carries
  friendly names for the five (FUSE-1207). Pick/pack have no made/failure subscription in collector,
  so they sit at a pre-made status — expected, not a fetcher bug.

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

- [x] 1. Correlation ID kept out of the record body (AC 6) — `toDisplayRow` pulls a string — correlationId lifted off the record body onto row/selection; drawer row only when present; 4 const-spec tests — done: e04dfaa
      `correlationId` onto the row and selected record; drawer gains a "Correlation ID" row hidden when
      absent; the "not captured" note narrows to connector; a no-ticket comment on
      `TRANSACTION_ENTITIES` naming the collector dependency on `refPaths` — verify: extend
      `__test__/transaction-history.const.spec.ts` (string carried; missing/non-string → undefined;
      absent from `record`); `pnpm test`, `pnpm lint`, `pnpm build`. Ships in PR 1, which must reach
      prod before collector PR B's prod approval.
- [x] 2. Extract `toVisibleRows` and `findSelected` from the view, behaviour unchanged (no AC — — toVisibleRows/findSelected extracted to logic/transaction-history-rows.logic.ts; 11-test characterisation spec green before and after the move — done: e04dfaa
      enables 4-5) — spec first against the current inline code (each filter, scope narrowing,
      newest-first order, `findSelected` searching every type not just in-scope ones), then move
      verbatim — verify: the same spec green before and after the move; `pnpm build`.
- [x] 3. Regenerated collector client + search-only `listTransactionChunks` server function (AC 7) — — regen adds reference/correlationId/400 (+ unrelated stock_adjustment failure route drift); searchTransactionChunks validates targets + reference (zero GETs when invalid), parallel fan-out, fail-closed on correlationId-less pages; 606 tests incl. server-function spec with mocked client (proven to fail when guard/validation broken); dev: TESTREF51 + #twin found, blank 400 — done: 7c01995
      `normaliseReference` (typeof string, trim, 1-256, no `#`/case change), `fanOut` (per-type
      results; one type's failure isolated), `reference` required so an unfiltered call is impossible
      by construction, every type checked against `AVAILABLE_USE_CASES`, offsets non-negative ints,
      and the pre-PR-B guard (non-empty page lacking `correlationId` → that type errors) — verify:
      regen diff shows optional `reference` and `correlationId` (flag any unrelated dev drift in the
      PR); jest with the API client mocked: blank / 257-char / non-string → error with zero GETs, one
      type's 500 affects only that type, a correlationId-less page is rejected; dev collector curl by
      a known GADG customerRef returns it and blank returns an explicit 400.
      gate: collector FUSE-1239 PR B merged to master, and dev collector's logged `version` is a master sha (`gh api compare master...sha`) immediately before regenerating
            [x] confirmed
- [x] 4. Search hook, outcome classifier and status component, no page wiring (AC 2,3,4) — — split in two commits: 7a13a3d searchOutcome + status component (7 + 14 tests), 9b17d6b useReferenceSearch with injected fetcher (13 renderHook tests: per-type calls, widen/narrow, Back cache, resubmit, retryFailed, refresh, stale-response drop); suite 554 pass — done: 6f12635
      `use-reference-search` (cache per value×type, in-flight tracking, fetch only missing types on
      scope change, `loadNextChunk`/`retryFailed`/`refresh`), `searchOutcome` (loading / all failed /
      no matches incl. failed types + narrowed scope / hidden by filters / results), status component
      for each state — verify: `renderHook` spec (one call per in-scope type; widen → only new type;
      narrow → none; Back to earlier value → cache; resubmit → none; multi-type results all kept,
      unranked); RTL spec rendering each state (toolkit mocked like `work-order-details.spec.tsx`).
- [x] 5. Search input, `?search=` URL sync and view wiring (AC 1,3,5) — `GSearchBox` in a form — local run vs dev backends (the preview env's data path), GADG: customerRef TESTREF51 (Enter), 11428 + #11428 (button) -> SO + GOC, salesOrder 7821667434781 -> SO + GOC, a GOC _id, an SA correlation id -> 3 SAs; exactly 1 server-action POST per search (the 2 others per page load are an existing layout action), 0 for blank/300-char; Back/Forward across 7 searches + browse; shared link in a new tab; ?search=&record= opens the drawer; plain ?record= unchanged; hidden by Direction=Outbound; narrowed scope -> Search all use cases; Refresh re-runs; found + fixed a stale inline error after Back; 637 tests (view spec mutation-checked x5) — done: 0a7a9fe
      (Enter/button submit, Clear, inline error for blank/too-long with zero requests, disabled while
      pending); submit/Clear push history and drop `record`; popstate re-reads `search`; table shows
      search results when set; page index resets on value change; drawer lookup spans search + browse;
      Refresh re-runs the search; "N matches for "X" · Clear" line — verify: on the preview env against
      dev collector (G1 state), search GADG by customerRef, salesOrder, a `#`-toggled Shopify ref, an
      `_id`, and a correlation id on a non-SO type; Enter and button; Back/Forward across two searches
      and browse; shared link in a new tab; `?search=…&record=…` reload opens the drawer; plain
      `?record=` unchanged; one server-function POST per search in DevTools; screenshots of each state
      (no match, hidden by Direction=Outbound for a sales order, narrowed scope, 300-char paste).
      gate: collector PR B live on dev (same version check as increment 3)
            [x] confirmed
- [x] 6. Surface every record type (AC 8) — `TRANSACTION_ENTITIES` entries (direction, labels from — 6 new TRANSACTION_ENTITIES + fetchers + page seeding; refPaths only collector-declared paths; local run vs dev: against master collector RGA 139/139 + WO 53/53 rows = v1 totals, unserved 4 degrade to the failed-types note; with collector #110 on dev pick 146, pack 107, WOC 19, FGR 19 = v1 totals, drawer Record ID from the first populated refPath + Correlation ID row; 539 tests — done: 2d61691
      `use-case.const.ts`, `refPaths` mirroring collector's Record ID field per type) and v1 fetchers for
      return_goods_authorization, work_order, pick_confirmation, pack_confirmation,
      work_order_confirmation, finished_good_receipt; RGA confirmation-side status checked against
      collector source and written up for the PR — verify: const spec covers each new entry's
      `toDisplayRow`/Record ID; preview env shows rows + drawer for each type for GADG (screenshot per
      type), totals match collector's v1 list, and search finds one record of each new type.
      gate: collector FUSE-1239 increment 5 (pick/pack/WOC/FGR on v1) live on dev
            [x] confirmed
- [x] 7. All-types evidence (AC 1,2) — search each shown type by its fields; a value matching an — local run vs dev backends, GADG, all 12 types: 53 field/_id/correlation-id values (every search field populated on a recent record of each type) — UI match count = sum of collector per-type totals 53/53, expected record shown; multi-type matches incl. 22_9 retestS1 -> SO+SA+RGA+pick+pack, WO-20260819-068SE -> SA+WO+WOC+FGR, #11428 -> SO+GOC; high-fanout correlation 9f61dff0 (2194 SOs) paged 12 pages / 300 rows across 2 chunk loads: 300 unique _ids, 0 repeats, one POST per 100-row chunk — done: 0a7a9fe
      order and its confirmation (they share a customer ref) shows both; match count = sum of per-type
      totals; no `_id` repeats paging to page 5+ on an existing high-fanout correlation id (prefer an
      existing bulk id over seeding — `submit-to-fuse`/`mock-send` reach SNAP dev) — verify: preview
      env screenshots + a per-type totals table in the PR.
      gate: collector PR C on dev
            [x] confirmed
- [x] 8. Prod release (AC 1-8 in prod) — merge PRs 4 and 5, approve their Deploy runs by sha — — released: stack drained bottom-up (#270 fb23e94, #271 181fbca, #272 3f39fbf), prod plan image-only, revision fuse-ui-app-prod-00052-hsg Ready 100%, clean start 17:34Z; logged-in prod search not yet run — see Not verified — done: 3766c13
      verify: prod search finds a known customerRef, salesOrder and correlation id for a real business;
      every record type lists for that business; prod collector logs show the search GETs by
      correlation id; no payload-panel leak.
      gate: collector FUSE-1239 PRs B, C and D live in prod plus 24-48h of clean Atlas Query Targeting
            [x] confirmed

> SUPERSEDED 2026-09-23 — as shipped: incs 1+2 #262, inc 4 #263+#264, inc 6 #265, inc 3 #270,
> inc 5 split into #271 (form + results line) and #272 (wiring), inc 7 evidence in #272; all merged and
> released to prod at 3f39fbf. See Decisions & deviations.

PRs: 1 = incs 1+2 (~300 lines, mergeable now); 2 = inc 3 (~300); 3 = inc 4 (~650); 4 = inc 5 (~400)
+ inc 7 evidence; 5 = inc 6 (new record types). PRs 1-3 show users nothing new and merge as ready;
PRs 4-5 wait on inc 8's gate. 8 increments — one over the 7 guideline because FUSE-1207 was wrapped
in on Harry's call rather than planned separately.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-09-24 [inc 8, restore] Prod had been rolled back: FUSE-1220's older parked Deploy run `746c6af` (35895530653) was approved at 17:37Z on 09-23, three minutes after `3f39fbf` went live, replacing revision 00052 with 00053 at 17:39Z. That left prod with #270/#271 but no #272, so no search box. Restored with run 35964416358 on `ae14bc5` (= `746c6af` + #272 + rules-engine 2.1.1 + ui-toolkit 1.35.3, both Renovate, green). Its first prod plan lost a state-lock race with twin `cbeb1b0`, so it was cancelled and re-run. The plan was 0/1/0 image-only, non-image lines identical to 09-23's. The 6 parked runs from 09-23/24 were cancelled before approving. `fuse-ui-app-prod-00054-vmg` serves 100%, Ready 09:10:30Z, clean logs. 22 older parked runs (09-04 → 09-22, all ancestors of `ae14bc5`) are still approvable. An early `--status waiting` count said 0, which was wrong.
> SUPERSEDED 2026-09-24 — prod did not stay on `3f39fbf`; it was rolled back to `746c6af` at 17:39Z and restored as `ae14bc5` (bullet above).
- 2026-09-23 [inc 8, release] Stack drained bottom-up: #270 → `fb23e94`, #271 → `181fbca` (real
  merge of main into its branch — main had gained FUSE-1220 #267 — resolved to the branch copy after
  proving main's copies equalled inc 3 byte for byte), #272 → `3f39fbf`. main also carried FUSE-1220
  #268 and #269 (merged 17:19Z / 17:25Z by another session), all behind
  `FEATURE_FLAG_MAPPING_DICTIONARIES`, set nowhere in `iac/`. `3f39fbf` tree: jest 669, tsc, biome
  clean. Prod plan 0/1/0, image `prod-6f12635` → `prod-3f39fbf`, other lines identical to the 15:01
  accepted plan; terraform-prod approved on run 35895944915. Prod revision
  `fuse-ui-app-prod-00052-hsg` at 100% traffic, Ready, clean start 17:34:26Z, no WARNING+ logs.
  Superseded parked runs `fb23e94`/`181fbca` cancelled; FUSE-1220's `a2f96c1`/`7445ac8`/`746c6af`
  left parked (rollback hazard, owner told). Dev apply hit a transient GCS read of replay's remote
  state; rerun succeeded, dev also on `3f39fbf`.
- 2026-09-23 [inc 7, AC 1-2] Local fuse-ui against dev backends, GADG: for each of the 12 record
  types, a recent record's every populated search field + `_id` + correlation id (53 values) searched
  in the UI — the "N matches" count equals the sum of collector's per-type `?reference=` totals 53/53
  and the expected `_id` is among the rows (read via each row's own `?record=` click). Cross-type
  matches shown unranked: `22_9 retestS1` → sales order + stock adjustment + RGA + pick + pack;
  `WO-20260819-068SE` → SA + WO + WOC + FGR; `#11428`/`11428` → sales order + goods-out confirmation.
  High-fanout correlation id `9f61dff0…` (2,194 sales orders): 12 pages / 300 rows across two chunk
  loads, 300 unique `_id`s, 0 repeats; one server-function POST per 100-row chunk. Scripts/report in
  scratchpad `fuse-1240-inc7-evidence/`.
- 2026-09-23 [inc 5, AC 1,3,5] Same local run: one server-function POST per search (the two others on
  every page load are an existing `["GADG"]` layout action, present without search too), zero for a
  blank or 300-char value (inline error, URL unchanged); Enter and button submit; Back/Forward across
  7 searches and browse restores box + results (found and fixed: the inline error survived Back);
  shared `?search=` link in a new tab; `?search=TESTREF51&record=<id>` reload opens that drawer with
  its Correlation ID row; plain `?record=` still opens from browse; Direction=Outbound →
  "1 record matches … hidden by the current filters"; `?useCases=purchase_order` → no match + "Search
  all use cases" → widening fetches 1 POST and finds it; Refresh re-runs (1 POST). Screenshots in
  scratchpad `fuse-1240-inc5-evidence/`.
- 2026-09-23 [inc 3, AC 7] Dev collector: `?reference=TESTREF51` → 1 record with `correlationId`,
  `%23TESTREF51` → same record, blank → 400; server-function spec (mocked client) fails when the
  correlationId guard or target validation is removed.
- 2026-09-23 [planning] Facts reviewer proved `renderHook` and a jest-mocked `'use server'` module
  both run in this repo's jest setup (throwaway specs, not committed); dev `/api-json` regenerates
  byte-identical to the checked-in collector client today (no unrelated drift yet).

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- A search in prod (increment 8's verify) — released and healthy, but nobody has searched a real
  business in prod yet; needs a logged-in human. Then check collector-prod logs for the 12-GET burst
  on one correlation id, and Atlas Query Targeting.
- AC 4 and AC 7 live: no record type failed on dev and every dev collector honours `?reference=`, so
  the per-type failure banner and the fail-closed path are proven by unit/spec tests only
  (status component, hook, server-function spec), not observed in a browser.
- The per-PR preview environment itself — evidence ran locally against the same dev backends.

## Rollout & rollback
<!-- Added on demand. Written at plan time; amend in place as it changes.
     `Shared state touched:` is the single home for the five classes git does not own — a dev
     deploy, a prod config write, a Datadog monitor, a CI var or secret, cross-repo IaC. Reverting
     the branch undoes none of them, so if they are not written here they are not written down. -->

- **Order:** PR 1 → prod **before** collector PR B's prod approval (else `correlationId` leaks into
  the payload panel). PRs 2-3 any time after collector PR B is on dev. PR 4 only after collector PRs
  B and C are in prod plus 24-48h clean Query Targeting. FUSE-1238's parked prod run (`cfdb0f5`) needs
  collector #104/#105 in prod first, and any fuse-ui run at or after `cfdb0f5` inherits that.
- **Flags/config:** none.
- **One-way doors:** none.
- **Rollback:** `git revert` per PR, approved to prod by sha. A collector revert of PR B must be
  paired with a revert of PR 4; the AC 7 guard makes an unpaired collector rollback fail closed
  rather than show wrong results.
- **Shared state touched:** fuse-ui's parked Deploy runs (approve by sha — 4 stale runs older than
  prod `1b0444b` were parked on 2026-09-23: `412959c`, `c256359`, `101d4f9`, `6137495`); per-PR
  preview environments on dev backends; any GADG seeding in increment 6 reaches SNAP dev (avoid).
- **Proof in prod:** support-shaped searches return the expected records for a real business; no
  `correlationId` in payload downloads; collector Query Targeting unchanged after release.

## Options considered
<!-- Added on demand. Why this approach and not the others — the thing the planning agent is
     asked for and the plan has otherwise had nowhere to put. Promote to a durable record with
     `wp decide --record` when it is worth defending in a review six months out. -->

- **Chosen — submit on Enter/button** — exact match makes every partial value a guaranteed miss; a
  debounce would fire 6 collector calls per pause and flash "no results"; server functions can't be
  cancelled; support paste-and-Enter.
- **Rejected — debounce / search-on-paste** — for the reasons above.
- **Chosen — other filters keep applying to search results, with a "hidden by filters" escape hatch**
  — one meaning per filter in both modes; nothing hidden silently (sales orders are inbound, so
  Direction=Outbound hides them — a common case).
- **Rejected — clearing filters on search** (throws away the user's settings); **ignoring filters in
  search mode** (filters mean different things per mode).
- **Chosen — one search-only fan-out server function** — the router serialises client-invoked server
  functions; one call fans out in parallel on the server. Browse is left on its current per-type
  loader (its sequential chunking and swallowed errors are a separate defect, not this ticket).
- **Rejected — hand-typing the `reference` param before the regen** — a hand-typed call against a
  pre-PR-B dev collector silently returns unfiltered lists; the regen is the proof PR B is live.
- **Rejected — asking collector to echo `reference`** — the per-record `correlationId` PR B adds is a
  free detector (AC 7).
- **Rejected — server-rendering search in `page.tsx` or a route handler** — two code paths, and a URL
  push doesn't re-run the page; a route handler would allow cancellation but breaks the module's
  server-function pattern.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-09-23** — Sign-off restamp: increments 1-2 (PR #262, branch head 46cbdb4), 4 (#263 d384232 + #264, never stamped) and 6 (#265, stamped at pre-squash 1ad8e6f) landed as squash commits on main — restamped to e04dfaa, 6f12635 and 2d61691, which are ancestors of this branch. Learnings promoted: deploy gate, approval scope, CI races and next-dev files → operations.md; server-function calling model, client-side paging, jest toolkit mocks + 2 guardrails → architecture.md; search semantics + browse defects → known-context.md; new explainer [[transaction-history-reference-search]]. architecture.md/operations.md deliberately not re-anchored — both were already stale on unread FUSE-1220/FUSE-995/DNS commits.

- **2026-09-23** — ACs 4 and 7 ticked on spec-level proof: neither a per-type failure nor a collector that ignores ?reference= can be produced against live dev, and each link is tested — fanOut isolates a throwing type, the hook records per-type failure, searchOutcome carries failures into results, the status banner names them (AC 4); the server-function spec returns a correlationId-less page from a mocked client and gets SEARCH_UNAVAILABLE, mutation-checked (AC 7). Not observed in a browser — stays under Not verified.

- **2026-09-23** — Harry: 'ship them all' — increment 8's 24-48h soak gate overridden ~1h after collector's search reached prod (15:44Z; Atlas: last collector-prod Query Targeting alert 2026-09-21 12:29Z, none since). Prod release carries #267 (FUSE-1220 PR 1/3, merged 17:14Z, flag-gated, 'dev and prod stay unchanged' per its PR).

- **2026-09-23** — PR 4 split into a 3-PR stack by size (928 lines for inc 5 alone, 468 for inc 3): server function (inc 3, hjf/fuse-1240-search-server-function @7c01995) -> search box + results line, unwired (hjf/fuse-1240-search-form @2c6858b) -> view wiring (hjf/fuse-1240-search-wiring @0a7a9fe; tree identical to c03db01, which inc 5 was first stamped with, so restamped). Evidence ran locally against dev backends (the preview env's own data path), not on the preview env itself.

- **2026-09-23** — PRs 1-4 (#262 #263 #264 #265) merged and in prod (fuse-ui 6f12635). Remaining increments 3/5/7/8 go on a fresh branch hjf/fuse-1240-search-wiring off origin/main 6f12635. Gates for 3 and 5 confirmed: collector #108 on master and dev collector logging version 0599b6b = origin/master (includes #108-#110 + Renovate #112) at 15:46Z.

- **2026-09-23** — Inc 6 ticked by hand in wp's own format: wp tick --increment 6 matched the example '- [ ] 6.' inside the template's HTML guidance comment first and stamped that (reverted). Inc 6's verify line said 'search finds one record of each new type' — search isn't on the page until increment 5, so that part is proven collector-side (collector#110 dev run: 12/12 field lookups) and re-checked in increment 7's all-types evidence. Browse is PR 4 = branch hjf/fuse-1240-all-record-types, stacked on #262 (sibling of the #263 → #264 search chain). RGA lifecycle (collector source): create_record → processing, create_acknowledge → processed, create_data_failure → failed, never pending, no confirmation-side lifecycle (no registry entry / collection — hence Return Goods Confirmation stays disabled). Pick/pack: saved from ready with no status, no made/failure subscription → always 'No status'.

- **2026-09-23** — Increment 4 before 3: the hook takes its fetcher as an argument (fetchChunks → SearchChunkResult per type) instead of importing the server function, so it's built and unit-tested now while increment 3 waits on the collector #108 merge + regen; increment 5 wires the real server function in. PR order becomes 1 = incs 1-2 (#262), 2 = inc 4 (branch hjf/fuse-1240-search-hook, stacked on #262), 3 = inc 3.

- **2026-09-23** — Collector (FUSE-1239 incs 3-4) fixed each type's Record ID search fields; increment 6's new refPaths must mirror them — work_order leads workOrder.customerRef, RGA leads identifiers.businessRgaNumber; pick/pack/WOC/FGR follow collector increment 5's choice.

- **2026-09-23** — Harry: surface every transaction type — wrapped FUSE-1207 (RGA, pick, pack, WOC, FGR) plus work orders into this plan as increment 6 (AC 8), gated on collector FUSE-1239 increment 5 serving pick/pack/WOC/FGR on v1; renumbered evidence/release to 7/8; release gate now waits on collector PR D too. Plan activated.
- 2026-09-23 — Base is `origin/main` @ `cfdb0f5`, not stacked on the FUSE-1238 branch: #261 merged
  (and its branch was deleted) while this plan was drafted.
- 2026-09-23 — The planning draft claimed a merge deploys fuse-ui to prod; wrong — prod is gated on
  `terraform-prod` approval. The merge gate on PR 4 stands for a different reason: `main` is shared
  and every later merge parks a run carrying it.
- 2026-09-23 — Increment structure rebuilt from review: the correlation-id compat fix split out as
  increment 1 (it has to reach prod before collector PR B); the pure refactor cut to the two
  functions browse actually uses, spec-first; browse left off the new fan-out function (scope);
  hook/status (unit-only) split from page wiring; a release increment added so the prod gate has an
  increment to sit on.
- 2026-09-23 — `GSearchBox` over a raw `Input type=search` (toolkit-consistent, un-debounced,
  built-in pending state) — facts reviewer found it; taken as the default.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
(none)

