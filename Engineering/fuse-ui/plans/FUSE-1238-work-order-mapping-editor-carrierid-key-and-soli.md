---
ticket: FUSE-1238
title: 'Work-order mapping editor: carrierId key and soLineId label'
service: fuse-ui
status: complete
created: '2026-10-09'
updated: '2026-10-19'
repo: /home/hjf/code/fuse/fuse-ui
worktree: /home/hjf/code/fuse/fuse-ui/.claude/worktrees/fuse-1238-wo-keys
branch: hjf/fuse-1238-work-order-mapping-keys
base: origin/main
base_sha: f9a77002f
pr: '296'
tags:
- waypoint
- plan
---
# FUSE-1238 — Work-order mapping editor: carrierId key and soLineId label

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
Add `identifiers.carrierId` ("Carrier") to the Work Order mapping editor key list, and fix the Work Order Confirmation line labels so `soLineId` reads "Line Number" and Snap's internal `line` reads "Snap Line Key". Observable outcome: both labels appear in the editor key pickers. Ticket: FUSE-1238.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] Work Order header keys include `identifiers.carrierId` as "Carrier".
- [x] Work Order Confirmation lines include `soLineId` as "Line Number".
- [x] Work Order Confirmation `line` is labelled "Snap Line Key".

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `code/src/app/server-functions/data/work-order-keys.json` and `work-order-confirmation-keys.json`, consumed by `configuration.func.ts` (`getMappingConfiguration`).
- Canonical: `CanonicalWorkOrder.identifiers.carrierId` (`@gfs-bifrost/types` 10.12.0), `CanonicalWorkOrderConfirmationLine.soLineId`.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- The JSON lists are hand-maintained and not type-checked against `@gfs-bifrost/types`, so fuse-ui pinned on 10.9.0 is fine — source read, `carrierId` absent from installed 10.9.0 but present on pkg-node `origin/main`.

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
- [x] 1. Add `identifiers.carrierId` to `work-order-keys.json` (AC 1) — verify: key present, tests and lint green — done: 5fa339c
- [x] 2. Add `soLineId` and relabel `line` in `work-order-confirmation-keys.json` (AC 2,3) — verify: keys present, tests and lint green — done: 5fa339c

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-09 [inc 1,2] `pnpm run test` 66 suites / 891 tests passed, `lint:fix` exit 0; PR gfs-bifrost/fuse-ui#296 CI all green and squash-merged as 9c6411a. No test pins these labels.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- No screenshot of the editor offering "Carrier"; needs a dev connector with a `work_order` use case. Prod deploy gate not yet approved, so not live in prod.

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
