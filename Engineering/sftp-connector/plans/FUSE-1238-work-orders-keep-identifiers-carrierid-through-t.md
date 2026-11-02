---
ticket: FUSE-1238
title: 'Work orders: keep identifiers.carrierId through the inbound translator'
service: sftp-connector
status: complete
created: '2026-10-09'
updated: '2026-10-19'
repo: /home/hjf/code/fuse/sftp-connector
worktree: /home/hjf/code/fuse/sftp-connector/.claude/worktrees/fuse-1238-wo-carrier
branch: hjf/fuse-1238-work-order-carrier-id
base: origin/master
base_sha: 39f059f93
pr: '304'
tags:
- waypoint
- plan
---
# FUSE-1238 — Work orders: keep identifiers.carrierId through the inbound translator

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
Keep a connector mapping default for `identifiers.carrierId` on inbound work orders. The work order translator validates with `CanonicalWorkOrderSchema`, and Zod strips keys the resolved `@gfs-bifrost/types` does not know; the lockfile pinned 10.9.0, which predates `carrierId` (added in 10.12.0), so the default was dropped before emit. Raising the floor to `^10.12.0` fixes it with no translator code change.

Part of the GADG work-order CSV confirmation effort, config side in [[FUSE-1238-gadg-work-order-csv-confirmations-woc-and-fgr-ma]]. Ticket: FUSE-1238. PR: gfs-bifrost/sftp-connector#304.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. A header default `{ key: identifiers.carrierId, value: OWN }` survives `WorkOrderTranslator.translate` into the validated canonical
- [x] 2. `@gfs-bifrost/types` resolves to 10.12.0 in the lockfile and a fresh-day install passes frozen-lockfile in CI
- [x] 3. The carrier reaches a work order in dev end to end once snap-adapter is also deployed there

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `code/src/import/translators/work-order.translator.ts` (`assignDefaults` -> `allocateDefaultValues`, then `validateRecords(CanonicalWorkOrderSchema, ...)`)
- `@gfs-bifrost/types` 10.12.0 (`CanonicalWorkOrder.identifiers.carrierId`)
- `code/pnpm-workspace.yaml` `minimumReleaseAgeExclude`

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- A mapped value wins over the default — `allocateDefaultValues` in rules-engine, source read
- A header default only reaches the canonical if no rule maps the field — covered by the test config having no header rule for it

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

- [x] 1. Raise the types floor to `^10.12.0`, patch the lockfile for types only, add `minimumReleaseAgeExclude` for `10.12.0` (AC 2) — verify: `pnpm why @gfs-bifrost/types` shows one version, 10.12.0 — done: 0bf3526
- [x] 2. Translator test for the carrier header default (AC 1) — verify: passes on 10.12.0; 10.9.0's work order schema has no `carrierId`, so it fails there — done: 0bf3526
- [x] 3. Dev end-to-end check with snap-adapter (AC 3) — verify: a work order from a mapped default carries the carrier to snap — dev e2e on HJF/simulator: S10 HJFD4AC7656638E has CarrierId OWN — done: 0bf3526

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-19 **Real SnapFulfil substitutes the carrier.** GADG's dev mapping carries the default `identifiers.carrierId = OWN`. Its work order `WO-20261016-AP005` (correlation `776af3a6-cc2d-45ca-95ee-55a5a402d068`, created 2026-10-16 11:03Z by snap-adapter-dev-00537, which includes the fix) reached snap-adapter with `carrierId: "OWN"`, per dedupe-service's forwarded canonical. Real GADG dev Snap accepted the create, and S10 `GADGDFD78D24007` reads **`CarrierId: "NETCOURIER"`**. That is the only value in GADG dev Snap's CARRIER lookup. Fuse delivers the value; Snap swaps in its own. Making `OWN` land is Snap-side config (the CARRIER lookup), not Fuse code.
- 2026-10-19 [inc 3] (AC 3) **Dev end to end on HJF, against the snap-api simulator.** Dev was on master (sftp `dev-7071412`, snap-adapter `dev-76f6fbf`; both include the FUSE-1238 merges).
  - Added a temporary header default `identifiers.carrierId = OWN` to HJF's `work_order` mapping (`conn_1435…`), and restored the original right after.
  - Dropped kitting DESADV `kit-10191238.edi` (BGM `E2EK10191238`) into `FUSE_4366B07EED/to_ilg/create_work_order/`. It went to `archive/` at 08:51:46Z.
  - Correlation `9172b3b8-258b-4336-ae52-764b6afcf6f5`: sftp "Records to send resolved" 08:51:41, then snap-adapter "Entity created in SNAP" 08:51:44.
  - The simulator's S10 shipment `HJFD4AC7656638E` (CustomerRef `E2EK10191238`) carries **`CarrierId: "OWN"`**. The 09-30 baseline `HJF265DA74BD20F` from the same file shape, without the default, carries none.
- 2026-10-09 [inc 1,2] sftp-connector#304 merged as 0bf3526. Full suite 854 tests, `lint:fix` exit 0, `build:check` exit 0, CI green. `pnpm why` resolves types 10.12.0. Dev Cloud Run revision `sftp-connector-dev-cr-00840-sfx` runs image `dev-0bf3526`.
- 2026-10-09 [inc 1] Unpacked `@gfs-bifrost/types@10.9.0`: no `carrierId` in `work-order.schema.js`, so the new test fails on the old resolution.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
> SUPERSEDED 2026-10-19 — checked against real dev Snap; see the GADG Evidence bullet.
- Real SnapFulfil acceptance of `OWN`: the simulator doesn't validate `CarrierId` against the CARRIER lookup. The only real-Snap signal is indirect: a GADG shipment accepted the non-lookup `DHL`.
- Dev end-to-end carrier check (AC 3) — owed once snap-adapter is also in dev.
- Prod: Deploy run for 0bf3526 is parked at the first prod gate; sftp-connector has two gates.

## Decisions & deviations
- 2026-10-09 Lockfile edited by hand for types only (version, specifier, integrity). A full `--lockfile-only` regen with pnpm 11.0.8 rewrote ~190 unrelated `supports-color` lines. Also cleared a red `proxy-addr` critical in its own PR, sftp-connector#305, before merging this one.
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
