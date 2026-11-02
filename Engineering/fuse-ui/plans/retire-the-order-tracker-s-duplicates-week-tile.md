---
ticket: none
title: Retire the order tracker's duplicates week tile
service: fuse-ui
status: complete
created: '2026-10-19'
updated: '2026-10-19'
repo: /home/hjf/code/fuse/fuse-ui
worktree: /home/hjf/code/fuse/fuse-ui/.claude/worktrees/retire-duplicates-tile
branch: hjf/retire-duplicates-tile
base: origin/main
base_sha: dd6eec753
pr: '339'
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: low
---
# none — Retire the order tracker's duplicates week tile

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
Out-of-ticket, and the fuse-ui half of [[stop-republished-copies-contending-on-the-shared]] (tracking-service).

tracking-service stops counting the daily `duplicates` stat, because republished copies were contending on the shared stats docs. The order tracker's week-stats "duplicates" tile would then show a misleading, falling number.

This plan removes the tile and re-vendors tracking-service's reworded openapi. Per-shipment copy counts stay: they keep counting. What proves it: the week stats render without the tile, and the weekday tracker-contract drift check is green against tracking-service `main`.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. The order tracker's week stats no longer show a duplicates total, on any business or the all-business view.
- [x] 2. The per-shipment copy counts are unchanged: "N duplicates collapsed", ×N on timeline events, and the detail sheet's duplicates.
- [x] 3. `code/src/lib/api-client/fuse-tracker/openapi.yaml` is byte-identical to tracking-service `main`'s `apps/api/openapi.yaml`, and `tracker-contract.yaml` passes.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `code/src/modules/order-tracker/components/week-stats.tsx:134-137`: the `stats.totals.duplicates` tile.
- `code/src/lib/api-client/fuse-tracker/openapi.yaml`, the vendored contract, and `code/src/lib/gen/fuse-tracker.client.d.ts` if regeneration changes it.
- `.github/workflows/tracker-contract.yaml`, the weekday drift check (not a required check).

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **The tile reads `stats.totals.duplicates` with no guard.** It would throw if the field disappeared. The field stays in tracking-service, so this change is safe in either deploy order. Established from source by the factual reviewer.
- **Copy counts were never a support request.** They were agent-built (fuse-ui 71ce17a #287, d6fc38c #292). Established from vault history by the history reviewer.
- **"Held as duplicate" in the work queue is a different thing and is not touched.** It reads `already_in_fuse` (`work-queue.tsx:391`) and dedupe-service's hold; both were requested in C5.
- **The tracking-service change only rewords the openapi text.** No schema shape changes, so regenerated types should not change.

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

This plan has one increment: it is the small half of a cross-repo change.

- [x] 1. **Remove the week tile and re-vendor the contract** (AC 1,2,3). Delete the tile, adjust the week-stats layout, copy tracking-service `main`'s `openapi.yaml`, and run the client generator. — tile gone, per-shipment counts shown; prod f1f4841 — done: 9932443
  - verify: `pnpm lint typecheck test build`;
  - verify: dev screenshots of the week stats (no tile) and of a PURDYFIGG shipment's table tooltip, timeline and detail sheet (counts still shown);
  - verify: `tracker-contract.yaml` green on the branch.
      gate: tracking-service inc 2 ("copies write no counter docs") merged to `main`
            [x] confirmed

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-19 [inc 1] **Prod.** #339 is merged as `f1f4841`, and its prod apply's plan was image-only (`prod-4978257…` → `prod-f1f4841…`). The first prod plan hit a state-lock race with #338's apply (`Error acquiring the state lock`, `gs://gfs-bifrost-tfstate-prod/prod/fuse-ui/default.tflock`); re-running the failed jobs succeeded. (AC 1)
- 2026-10-19 [inc 1] **Locally, against real dev tracking-service data** (`next dev` on :3017, a localhost proxy adding an identity token):
  - `/order-tracker?section=insights` contains "Already in Fuse" and not "Duplicates collapsed" (screenshot `week-stats.png` on `hjf/retire-duplicates-tile-evidence`).
  - `?shipment=HJF/HJF-DUPSTAT-1` shows `×1 · last 19 Oct 2026, 12:32` on its timeline (`detail-sheet.png`). (AC 1,2)
- 2026-10-19 [inc 1] **Gates and contract.** `pnpm lint` is clean, `pnpm test` passes 96/1178, and `NODE_ENV=production pnpm build` passes. The PR's `drift` (tracker-contract) check is green, and the vendored openapi is byte-identical to tracking-service `main` @389adbc. (AC 3)

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- No screenshot taken in prod itself; the change is a pure removal, and the identical page was verified locally against dev data.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
(none)
