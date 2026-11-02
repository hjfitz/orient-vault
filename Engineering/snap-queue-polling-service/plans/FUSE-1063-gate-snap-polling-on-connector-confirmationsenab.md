---
ticket: FUSE-1063
title: Gate SNAP polling on connector confirmationsEnabled
service: snap-queue-polling-service
status: complete
created: '2026-09-18'
updated: '2026-09-21'
repo: /home/hjf/code/fuse/snap-adapter
worktree: /home/hjf/code/fuse/snap-adapter/.claude/worktrees/fuse-1063-poll-gate
branch: hjf/fuse-1063-gate-polling-on-connector-config
base: origin/master
base_sha: 121c5148e5bf20b64d46104dbf22365985b60edd
pr: '240'
tags:
- waypoint
- plan
---
# FUSE-1063 — Gate SNAP polling on connector confirmationsEnabled

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
Extension of [FUSE-1063](https://globalfreight.atlassian.net/browse/FUSE-1063) (the first plan,
[[FUSE-1063-skip-confirmation-emission-for-connectors-not-co]], is complete and live in prod as
`8275c2c`). That change applied the per-connector `confirmationsEnabled` gate **late** — after SNAP's
outbound queue had been read and every entry enriched — and removed the old business-level poll
filter, so every configured business is now polled every 2 minutes. In prod 14 of 30 businesses
have no confirmation-enabled connector (GADG prod has none and sits on the *test* SNAP tenant) and
are enriched for nothing each cycle; items already published but not yet cleared downstream are
re-enriched every cycle and only deduped at claim time (44 "claim skipped duplicates" in 18 min).

Two levers, agreed with Harry: **(A)** skip a business before any SNAP call when none of its
connectors has `confirmationsEnabled: true` (and it isn't a `broadcastConfirmations` business) —
connector toggle only, mapping/use-case rules stay downstream at each connector; the skip is total
(that business's manual-origin broadcasts and stock_adjustments stop too). **(C)** in the lanes,
skip queue items whose claim key already exists so published-but-uncleared items are not
re-enriched. Explicitly rejected: a per-entry routing pre-read in the lanes (lever B). Untouched:
the `$top=1000` single-page cap and the 10-min claim TTL.

Two independent PRs off `origin/master`: PR-1 = increments 1–3 (+ docs) — snap-adapter **#240**;
PR-2 = increment 4 (+ docs) — snap-adapter **#241**, on its own worktree/branch
(`.claude/worktrees/fuse-1063-claim-precheck`, `hjf/fuse-1063-skip-claimed-before-enrichment`).
Both opened as drafts 2026-09-18 and marked ready for review the same day on Harry's say-so;
Confluence changelog rows (Snap Polling Service - Changelog v39) and the bundled #bifrost-forge
post are done. Both PRs linked on FUSE-1063 in one comment. Black-box harness needed two follow-up
commits: #240 mocks `GET /business` (the harness counted the unmatched call as a SNAP call), #241
lowers the expected SNAP-call totals for the cases that run with live claims (56 → 40, 22 → 11).

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. A business none of whose connectors has `confirmationsEnabled: true` (including a business
      with no connectors) is not polled: no `/v2/snapoutbound` read, no enrichment, nothing published.
      (inc 3) — verified live in dev (34→25 polled) and in prod evidence, 2026-09-18.
- [x] 2. A business with at least one `confirmationsEnabled: true` connector, or with backend
      `broadcastConfirmations: true`, is polled exactly as today. (inc 3) — verified live in dev,
      2026-09-18: eligible businesses (ACADEMIC, GADG) unaffected.
- [x] 3. Flipping a connector's `confirmationsEnabled` in config-service changes whether its business
      is polled on the next cycle, via the CONNECTOR revision event — no redeploy, no cache TTL wait.
      (inc 3) — verified live in dev via WIDGCO toggle, 2026-09-18.
- [x] 4. If the business index cannot be read (config-service down, unparseable cache), every
      configured business is polled (fail open) and the outcome is logged + metered. (inc 3) —
      provider spec: fail-open on reject and on unparseable cache.
- [x] 5. `broadcastConfirmations` reaches stage 2 (it is currently stripped by the stage-1→2 Pub/Sub
      schema), so the late gate's broadcast bypass and the poll filter's broadcast exemption both work.
      (inc 1) — event.controller spec: handleConfirmations receives broadcastConfirmations.
- [x] 6. A queue item whose confirmation claim key already exists is dropped before enrichment: no
      shipment/receipt/movement fetch and no handler call for it; an unclaimed item flows as today.
      (inc 4) — drain spec + live in dev, 2026-09-18: claim-skipped-duplicates dropped to zero.
- [x] 7. A claim-read failure never drops an item (fail open); the announce-time claim remains the
      authoritative dedupe. Items the service clears itself (zero-qty goods-in, cancelled shipments)
      still flow and are still disposed. (inc 4) — cache.service spec: throw → false (unclaimed).

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `apps/snap-queue-polling-service/src/core/polling/schemas.ts` — stage-2 wire schema (AC 5).
> SUPERSEDED 2026-09-18 — parsed with a local `BusinessIndexEntrySchema` (businessId +
> connectors[].{connectorId, confirmationsEnabled}) instead of the package schema; see
> Decisions & deviations.
- `src/adapters/fuse-config/fuse-config.api.ts` — **new inter-service read**: config-service
  `GET /api/v1/business?offset=` (paged; `CustomerInformationResponseDTOSchema` from
  `@gfs-bifrost/types` ^10.2.0, `connectors: ConnectorRefDTO[]` carries `confirmationsEnabled`).
  Fuse MCP `service-dependencies.json` needs the new snap-queue-polling-service → config-service
  `/business` edge at sign-off.
- `src/core/config/remote-config.provider.ts` (+ `cached-backend.schema.ts`, `src/core/cache/types.ts`)
  — business-eligibility cache, stage-1 filter in `getAllConfiguredBusinesses`, CONNECTOR-revision
  refresh in `saveBacklinks`. `/debug/trigger` + `/debug/check` inherit the filter (explicit
  `customers` body still overrides).
- `src/core/cache/cache.service.ts` (+ `IConfirmationClaimService`) — read-only claim check.
- `src/core/snap/confirmations/queue-lane.ts`, `outbound-queue.drain.ts`, `confirmations.service.ts`
  — claim pre-check between queue read and enrichment; drain now takes the claim service.
- `src/observability/catalog/snap-polling.type.ts` — three new metric names.
- See [[architecture]] "The two-stage poll" / "Config & credentials" / "Outbound-queue mechanics".

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- The gate is the boolean connector toggle only; mapping presence (`useCases`) is ignored here —
  Harry, explicitly, 2026-09-18 ("other rules like not having mappings are handled at the connector").
- A zero-enabled business is skipped entirely, including STOCK_MOVE — Harry chose "skip entirely"
  over "keep polling STOCK_MOVE only", 2026-09-18.
- Skipping is safe for the 14 prod businesses: pre-FUSE-1063 most were not polled at all (backend
  `confirmations: false`, verified via config-service `/backend` 2026-09-18), and the 7 that flipped
  backend-false → connector-true (NUZEST, LISAUK, LISAPL, SHACKLETON, ACADEMIC, AYMSTUDIO, DISCOVERED)
  keep being polled under this change.
- `@gfs-bifrost/cache` `tryGetAsync` never throws and returns `undefined` when Redis is down, so a
  claim pre-read is fail-open by construction; it back-fills the per-instance LRU (60 s default), so
  a claim can read as present for up to 60 s after Redis expiry — one extra skipped cycle, harmless
  against a 10-min claim TTL. Established by the planning agent reading pkg-node `origin/main`.
- `PagedApiResponseSchema` requires `{total, offset, count, data}` and config-service's
  `GET /v1/business` returns exactly that (business.controller.ts L87-112) — read from config-service
  `origin/main`.
- Local `node_modules` in the main checkout is on types 7.7.0; the worktree was `pnpm install`ed and
  resolves 10.2.0 — verified.

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

- [x] 1. Add `broadcastConfirmations` to the stage-2 wire schema (`core/polling/schemas.ts`) (AC 5) — — event.controller spec: handleConfirmations receives broadcastConfirmations; 18/18 green across both touched specs — done: 46c0509
      verify: event.controller spec asserts `handleConfirmations` receives the flag.
- [x] 2. `ConfigApi.getBusinesses(offset)` + `getAllBusinesses()` paging over config-service — fuse-config.api spec: pages to total, concatenates, throws on bad shape, rejects on 503; local schema because the live index omits useCases — done: 037dc44
      `GET /business`, parsed with `PagedApiResponseSchema(CustomerInformationResponseDTOSchema)`
      (foundational) — verify: fuse-config.api spec — pages to `total`, concatenates, throws
      `FuseConfigApiException` on an unparseable page, rejects on 503.
- [x] 3. Business-eligibility cache + stage-1 filter in `RemoteConfigProvider`: cache the derived — dev: 34→25 polled, 9 skipped; WIDGCO toggle refetched via CONNECTOR revision and left the skipped set next cycle; eligible businesses still publish — done: b316df7
      `{businessId, hasConfirmationEnabledConnector}` list under `BUSINESS_INDEX:confirmation-eligibility`,
      filter `getAllConfiguredBusinesses()` (keep when `broadcastConfirmations`, or index unavailable,
      or an enabled connector exists), refetch-all on any CONNECTOR revision in `saveBacklinks`, one
      aggregate skip log per run + `poll.skipped_ineligible_business{businessId}` +
      `poll.business_index_unavailable` (AC 1,2,3,4) — verify: provider spec (skip / keep / broadcast
      keep / absent-from-index skip / fail-open on reject and on unparseable cache / literal cache
      key / no refetch on hit / refetch once per CONNECTOR revision batch / none on BACKEND_CONFIG);
      live in dev: skip log lists the expected businesses, `Found N configured customers` drops,
      `poll.request{businessId}` zero for a skipped business, ACADEMIC still publishes.
- [x] 4. Claim pre-check in the lanes (PR-2): `IConfirmationClaimService.isConfirmationClaimed` — dev: claimed items skipped pre-enrichment on all three lanes, announce-time duplicate skips went from ~37/cycle to zero; 439/439 green — done: 758e22e
      (`cache.service.ts`, same key as `tryClaimConfirmation`, catch → false); `QueueLane` drops
      already-claimed items between `fetchOutboundQueue` and `resolve` via `chunkPromises`, one
      aggregate log per (business, lane) + `outbound.claimed_entry_skipped{lane,businessId}`;
      `OutboundQueueDrain(claimService)` built in `ConfirmationsService`'s constructor body (AC 6,7)
      — verify: cache.service spec (present → true, absent → false, throw → false, literal key);
      drain spec (claimed item never reaches the resolver / consumers, unclaimed does, claim-read
      rejection keeps the item, metric tagged `{lane, businessId}`); live in dev: skip log on the
      cycle after a publish, `Confirmation claim skipped duplicates` for that business drops to zero
      within the TTL window.
- [x] 5. Docs: app `CLAUDE.md` (two-stage poll step 1, Config & credential resolution, INC-30 note, — CLAUDE.md updated in PR #240 (e36baba) + PR #241 (758e22e), both merged to origin/master; architecture.md re-anchored at 469573c; fuse-mcp-server service-dependencies.json updated (cb4ad2e, pushed to master) — done: 52e15d2
      metrics list), Waypoint [[architecture]] (Config & credentials, Outbound-queue mechanics,
      re-anchored by hand), Fuse MCP `service-dependencies.json` (new `/business` edge). — verify:
      PR review checklist.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-09-18 [AC 6, AC 7 / inc 4] Deployed `hjf/fuse-1063-skip-claimed-before-enrichment`
  (`758e22e`) to dev (run 35340290186, announced in #bifrost-general; replaces the PR-1 build, so
  dev is back to 34 polled). Baseline on the previous build: every cycle logged ~37
  `Confirmation claim skipped duplicates` (GADG pick 12 / pack 13 / good_out 5 / good_in 1,
  ACADEMIC stock_adjustment 5 / good_out 1). First cycles on `758e22e`: 11:38:03
  `Skipping already-claimed queue items` GADG DESPATCH `{skippedCount: 25, remainingCount: 5}`,
  GADG RECEIPT `{1, 0}`, ACADEMIC STOCK_MOVE `{5, 0}`, ACADEMIC DESPATCH `{1, 0}`; 11:40:03 GADG
  DESPATCH `{30, 0}` — and **zero** `Confirmation claim skipped duplicates` lines on the new build.
  The 5 GADG good_out items still enriched at 11:38 were ones whose 10-min claim had lapsed; they
  republished (`Confirmations ready to announce good_out count: 5`) and were skipped at 11:40. At
  11:42:03 GADG DESPATCH `{skippedCount: 5, remainingCount: 25}` — the pick/pack claims from
  11:32 lapsed and those 25 re-enriched and republished, i.e. the TTL boundary behaves exactly as
  before. PHLUR `good_in` ×4 still enriches every cycle: withheld by the late gate, never claimed
  — the accepted residual of rejecting lever B (and what PR-1 removes for PHLUR by not polling it).
- 2026-09-18 [inc 4] Unit + regression suite 439/439 green in the PR-2 worktree (5 new
  `isConfirmationClaimed` tests, 7 new drain tests); `tsc --noEmit` clean; `biome check` clean.
- 2026-09-18 [AC 3 / inc 3] Live connector toggle in dev on WIDGCO's only connector
  (`conn_a0ecff14910b4832904683b922ea0a6a`, `confirmationsEnabled: false → true` via
  `PATCH /api/v1/storefronts/…/connectors/…`). Correlation IDs separate the three paths: the
  11:28:03 poll (`flow: confirmation`) did the one cold-cache fetch (`Fetched config from config
  API resource: all_businesses count: 39`, two `businesses_page` reads); the PATCH landed as
  `Backlink config event received` at 11:30:03 (`flow: config`) and refetched the index under
  that correlation; the 11:30:03 poll itself made **no** fetch (served from cache) and its skipped
  set went 9 → 8 with WIDGCO gone (`polledCount: 26`). Reverse direction: PATCH back to `false`
  landed as `Backlink config event received` + refetch at 11:31:09 (`flow: config`); the 11:32:03
  poll again made no fetch of its own and its skipped set went 8 → 9 with WIDGCO back
  (`polledCount: 25`). Steady-state polls between revisions never touched config-service.
- 2026-09-18 [AC 1, AC 2 / inc 3] Deployed `hjf/fuse-1063-gate-polling-on-connector-config`
  (`b316df7`) to dev via `snap-queue-polling-service-manual-deploy.yaml` (run 35339502663,
  announced in #bifrost-general). Direct before/after on consecutive stage-1 runs: 11:26:02
  (`121c514`, master) `Found 34 configured customers`; 11:28:03 (`b316df7`) `Found 25 configured
  customers` preceded by `Skipping businesses with no confirmation-enabled connector`
  `{skippedCount: 9, polledCount: 25, skipped: [DOCKBAY, BFA, SISTACO, DRSAMS, DRSAMSPL,
  ESCENTRIC, WIDGCO, JOLOVESPL, PHLUR]}` — every one of those has only `confirmationsEnabled:
  false` connectors in the dev index. Same 11:28 cycle still published for eligible businesses:
  ACADEMIC `stock_adjustment` ×5 and `good_out`, GADG `good_in`/`pick`/`pack`/`good_out` — i.e.
  no change for anyone with an enabled connector. PHLUR's per-cycle `good_in` ×4 (visible on
  every pre-deploy cycle) is gone.
- 2026-09-18 [inc 1-3] Unit + regression suite 447/447 green in the PR-1 worktree; `tsc --noEmit`
  clean; `biome check --write` applied formatting only.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- Fail-open on a live Redis outage (AC 7) — unit-tested only; not reproducible in dev without
  breaking Redis.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->
- 2026-09-18 — The plan said to parse the business index with the package's
  `CustomerInformationResponseDTOSchema`. Checked the live response first (staging
  `GET /api/v1/business`): connector refs carry `connectorId`/`storefrontId`/`friendlyName`/
  `confirmationsEnabled` only — **no `useCases`** — while `ConnectorRefDTOSchema` in types
  10.2.0 requires `useCases`. The package schema would have rejected every real page, tripping
  the fail-open and silently polling everyone. Parsed with a local narrow schema instead (the
  same pattern `ConnectorSourceSchema` already uses for `GET /connectors/{id}`). The
  config-service ↔ types mismatch is a separate defect to raise, not fixed here.
- 2026-09-18 — Lever B (per-entry Firestore routing pre-read in the lanes, dropping ineligible
  entries before enrichment) was designed and rejected by Harry in favour of A + C: it needed
  `DespatchEntry`/`ReceiptEntry` type changes across 13 consumers, an FGR special case (routing keyed
  by `receipt.Prime`), and a wider-than-today failure blast radius on a Firestore read error. The
  one mixed prod business (PURDYFIGG) keeps re-enriching its one disabled connector's entries.
- 2026-09-18 — Tracked as an extension of FUSE-1063 (already merged, Jira still *Code Review*) rather
  than a new ticket — Harry's call.
- 2026-09-21 — Both PRs are now merged: #240 (increments 1–3, 5) squashed as `f654123`, #241
  (increment 4) squashed as `469573c`. `wp signoff` run from the PR-1 worktree
  (`fuse-1063-poll-gate`) reports increment 4's `done: 758e22e` as unreachable — expected: that
  sha lives on the sibling PR-2 branch/worktree (`fuse-1063-claim-precheck`), never merged into
  this one, and squash-merging means neither branch's pre-squash commits become ancestors of
  `origin/master` either. Verified manually instead: `gh pr view 241` shows MERGED, and
  `git show origin/master:apps/snap-queue-polling-service/CLAUDE.md` carries both PRs' doc edits
  combined. Treating this as a real PASS on independent verification, not a tool false-negative
  to paper over — a plan spanning two independently-mergeable PRs is outside what a single
  `worktree`/`branch`/`pr` frontmatter block (and its ancestor check) was built to represent.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
(none — all promoted into [[architecture]] "Build / test / deploy" (the two black-box harness
gotchas), "Config & credentials" (the stale prod `confirmations` flag, and the raw
`/v2/snapoutbound` row shape), 2026-09-21. The stage-1→2 `broadcastConfirmations` strip was fixed
by increment 1 itself, not an ongoing gotcha, so it wasn't promoted separately.)
