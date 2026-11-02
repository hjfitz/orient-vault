---
ticket: "none"
title: "Migrate remaining raw logger calls onto the FUSE-995 event-catalogue seam"
service: "snap-queue-polling-service"
status: draft
created: "2026-09-22"
updated: "2026-09-22"
repo: "/home/hjf/code/fuse/snap-adapter"
worktree: "unknown"
branch: "unknown"
base: "origin/master"
base_sha: "unknown"
pr:
tags: [waypoint, plan]
---
# none — Migrate remaining raw logger calls onto the FUSE-995 event-catalogue seam

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
FUSE-995 (PR #236, merged 2026-09-17) moved every raw `logger.*` call in this app onto the
`FuseEventLogger.event()` catalogue seam — except it migrated the sibling receipt-side warning
("Receipt line consignment not matched" → `ReceiptLineMatchEvent.ConsignmentNotFound`) but left
the SNAP-request-failure logging (`metrics.interceptor.ts`, `fetch-outbound-queue.ts`) and other
remaining raw sites untouched. Once the StU warning is replaced by a metric (see the sibling
"Replace the per-item StU-not-found warn with a metric" plan) and the double-logging fix lands,
migrate what's left onto the existing catalogue rather than leaving mixed raw/structured logging
in the same handler family. Uses an already-adopted fleet convention, not a new one.

Source: techdebt. Originated from `waypoint-ideate` on 2026-09-22, prompted by a Datadog
log-volume investigation into ~400k logs/day on this service.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] <observable outcome>

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- <component / path / contract>

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- <assumption> — <how it was established: source read, ticket, asked>
- UNRESOLVED: <question that needs a human decision>

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

- [ ] 1. <increment> — verify: <how>
- [ ] 2. <increment> — verify: <how>

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- <YYYY-MM-DD> [inc <n>] <what was run, against what, and the observable result>

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- <what remains unproven, and what would prove it>

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
