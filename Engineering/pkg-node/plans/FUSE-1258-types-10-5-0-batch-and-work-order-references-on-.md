---
ticket: FUSE-1258
title: types 10.5.0 batch and work-order references on FGR and WOC
service: pkg-node
status: complete
created: '2026-09-24'
updated: '2026-10-05'
repo: /home/hjf/code/fuse/pkg-node
worktree: /home/hjf/code/fuse/pkg-node/.claude/worktrees/fuse-1258
branch: hjf/fuse-1258-types-fgr-woc-refs
base: origin/main
base_sha: 9b54c84ac
pr: '249'
tags:
- waypoint
- plan
programme: edi-support
unit: D2
---
# FUSE-1258 — types 10.5.0 batch and work-order references on FGR and WOC

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
[FUSE-1258](https://globalfreight.atlassian.net/browse/FUSE-1258), types half. `@gfs-bifrost/types` 10.4.0 → 10.5.0, optional fields only: `location.batchId` on `CanonicalFinishedGoodReceiptLine` and `CanonicalWorkOrderConfirmationLine`; `identifiers.salesOrder` + `workOrder.customerRef` on `CanonicalFinishedGoodReceipt`; `SnapStockMovement.FromStockId`. Consumer: [[Engineering/snap-adapter/plans/FUSE-1258-carry-batch-and-work-order-references-on-fgr-and|snap-adapter FUSE-1258]].

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. Type and Zod schema carry the new optional fields in lockstep; nothing existing changes shape.
- [x] 2. 10.5.0 publishes and the poller builds/tests against it.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `pkg/types/src/canonical/{types,schemas}/finished-good-receipt.*`, `work-order-confirmation.*`, `pkg/types/src/snap/types/entities/stock-movement.types.ts`, `pkg/types/package.json`. Changelog row in `/home/hjf/code/CLAUDE.md` (not a repo). fuse-mcp `canonical-types.json` owed after publish.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- Version race: open PRs #232 (FUSE-1201) and #233 (FUSE-1195) both bump 10.2.0 → 10.3.0, already stale vs main's 10.4.0; whichever merges after this renumbers — gh pr diff, 2026-09-24.
- `batchId` goes under `location`, as pick/pack lines have it — source read.

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

- [x] 1. Add the fields + bump 10.5.0 (AC 1) — verify: `pnpm build` (tsc) clean, vitest 63/63, biome clean — done: 14fb813
- [x] 2. Publish 10.5.0 via PR merge (AC 2) — verify: registry shows 10.5.0 — published 2026-09-24T18:31Z from squash 324ae1254 (see sign-off Evidence) — done: 324ae1254
      gate: Harry reviews and merges the pkg-node PR
            [x] confirmed — PR #249 merged by harry-fitzgerald_gfsdev 2026-09-24T18:30Z

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-05 [sign-off] inc 2 / AC 2: PR #249 was merged by Harry (`harry-fitzgerald_gfsdev`) at 2026-09-24T18:30Z as squash `324ae1254`. The squash replaced branch sha `14fb813`. `gh api /orgs/gfs-bifrost/packages/npm/types/versions` shows `10.5.0` published 2026-09-24T18:31Z. The poller took it through Renovate snap-adapter#256 (`^10.5.0`, 2026-09-25) and is now on `^10.9.0`. snap-adapter master `7c436f9` has every check green, including build, test and black-box tests.
- 2026-10-05 [sign-off] AC 1: on `origin/main` (`6776d65`), the FGR line and the WOC line both have `location.batchId?: string`. `CanonicalFinishedGoodReceipt` has `identifiers.salesOrder?` and `workOrder?: { customerRef? }`. `SnapStockMovement.FromStockId?: string | null` sits beside the mis-cased `FromStockID`. The schemas match. The squash diff removes only the old `version` line in `package.json`, so nothing existing changed shape. fuse-mcp `canonical-types.json` on `master` already describes the FGR/WOC batch and references, so the follow-up named in Affected boundaries is done.
- 2026-09-24 [inc 1] `pkg/types`: `lint:fix` no fixes, `tsc` exit 0, vitest 8 files / 63 tests pass; `pnpm pack` → gfs-bifrost-types-10.5.0.tgz consumed by the poller (503/503 tests, local blackbox 9/9).

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
> SUPERSEDED 2026-10-05 — 10.5.0 is published; see the sign-off Evidence bullet.
- Publish (increment 2).

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-09-24** — FGR work-order references: identifiers.workOrderId/businessWorkOrderId already existed; added identifiers.salesOrder and workOrder.customerRef, mirroring CanonicalWorkOrder's names. Added SnapStockMovement.FromStockId (Snap's real casing) rather than renaming the mis-cased FromStockID, which would be breaking.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
