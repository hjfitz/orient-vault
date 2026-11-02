---
ticket: FUSE-1088
title: types 10.8.0 movement reference, batch and expiry on CanonicalStockAdjustment
service: pkg-node
status: complete
created: '2026-09-29'
updated: '2026-10-05'
repo: /home/hjf/code/fuse/pkg-node
worktree: /home/hjf/code/fuse/pkg-node/.claude/worktrees/fuse-1088
branch: hjf/fuse-1088-types-stock-adjustment-refs
base: origin/main
base_sha: b53043c52
pr: '254'
tags:
- waypoint
- plan
programme: edi-support
unit: D1
---
# FUSE-1088 — types 10.8.0 movement reference, batch and expiry on CanonicalStockAdjustment

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
[FUSE-1088](https://gfsdeliver.atlassian.net/browse/FUSE-1088), types side of [[FUSE-1088-carry-movement-reference-batch-and-expiry-on-sto|snap-adapter FUSE-1088]]. `@gfs-bifrost/types` 10.8.0 adds optional `identifiers.movementRef`, and `batchId` + `expiry` on both `from` and `to`, to `CanonicalStockAdjustment` and its schema. Proven when the poller builds against the packed tarball and its canonicals pass the new schema.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. `CanonicalStockAdjustment` + schema carry `identifiers.movementRef?: string`, `from|to.batchId?: string` and `from|to.expiry?: Date` in lockstep, all optional.
- [x] 2. Version 10.8.0, with a Package Changelog row in the org contract.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `pkg/types/src/canonical/types/stock-adjustment.types.ts`, `pkg/types/src/canonical/schemas/stock-adjustment.schema.ts`
- Consumer: snap-queue-polling-service (stamps it). sftp-connector's fixed stock-adjustment transformer does not read it yet.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- Naming follows pick/pack/RGA lines (`batchId`, `expiry: Date`); goods-in's string expiry is the outlier. Checked by reading every canonical's batch/expiry fields.
- No open pkg-node PR bumps types except Renovate #253, which doesn't touch the version. Whichever types PR merges next after 10.7.0 takes 10.8.0.

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

- [x] 1. Add the fields, bump to 10.8.0, add the changelog row (AC 1,2) — verify: types build/lint/test; poller tsc + suite against the packed tarball — poller green against packed tarball — done: 42e3ee2

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-05 [sign-off] AC 1: on `origin/main` (`6776d65`), `stock-adjustment.types.ts` has `identifiers.movementRef?: string` and `batchId?: string` + `expiry?: Date` on both `from` and `to`. `stock-adjustment.schema.ts` matches them with `z.string().optional()` and `dateSchema.optional()`. PR #254 merged 2026-09-29 as squash `4d62ab933`, and its only removed lines are the version bump and a changelog line, so nothing existing changed shape. The squash replaced branch sha `42e3ee2`.
- 2026-10-05 [sign-off] AC 2: `gh api /orgs/gfs-bifrost/packages/npm/types/versions` shows `10.8.0` published 2026-09-29T09:27Z, one minute after the merge. The org contract (`/home/hjf/code/CLAUDE.md`) has the `@gfs-bifrost/types` 10.8.0 Package Changelog row. Consumers: snap-adapter's poller is on `^10.8.0` from its FUSE-1088 PR #263 (now `^10.9.0`, master CI green on `7c436f9`), and sftp-connector is on `^10.9.0`. fuse-mcp `canonical-types.json` on `master` already describes `movementRef` and the batch/expiry fields.
- 2026-09-29 [inc 1] types `build` 0, `lint` 0, 64/64 tests. Packed `gfs-bifrost-types-10.8.0.tgz`; the snap poller type-checks and passes 557/557 against it. Live GADG dev canonicals (12 moves) validate against the new schema, including after a JSON round-trip, which exercises `dateSchema` on expiry.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
> SUPERSEDED 2026-10-05 — 10.8.0 is published (2026-09-29T09:27Z); see the sign-off Evidence bullet.
- Not published. That is a manual step after merge.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-09-29** — Batch/expiry sit on from/to rather than in identifiers/dates, because each side of a move is its own stock row. expiry is a Date, matching this canonical's other dates and the pick/pack/RGA precedent.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
