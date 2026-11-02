---
ticket: FUSE-1238
title: 'Work orders: write CarrierId to the Snap shipment'
service: snap-adapter
status: complete
created: '2026-10-09'
updated: '2026-10-19'
repo: /home/hjf/code/fuse/snap-adapter
worktree: /home/hjf/code/fuse/snap-adapter/.claude/worktrees/fuse-1238-wo-carrier
branch: hjf/fuse-1238-work-order-carrier-id
base: origin/master
base_sha: c5e7bcb23
pr: '286'
tags:
- waypoint
- plan
---
# FUSE-1238 — Work orders: write CarrierId to the Snap shipment

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
Work orders are created in Snap as S10 shipments, but `identifiers.carrierId` (added to `CanonicalWorkOrder` in types 10.12.0) was dropped on the way. Map it through to the shipment `CarrierId`, mirroring `sales-order.service.ts`, with no default (snap-adapter holds none). Ticket: FUSE-1238. Proof: `snap-get-shipment` on a created work order shows the carrier (e.g. `OWN`).

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. A canonical work order with `identifiers.carrierId` produces a Snap shipment carrying `CarrierId` with that value.
- [x] 2. A work order without `carrierId` writes no `CarrierId` (no default).
- [x] 3. In dev, a work order sent end to end shows `CarrierId` on the Snap shipment.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `apps/snap-adapter/src/core/work-order/work-order.service.ts`
- `@gfs-bifrost/types` `CanonicalWorkOrder.identifiers.carrierId` (10.12.0); dependency bumped in `apps/snap-adapter` only
- Upstream producer: sftp-connector must emit `identifiers.carrierId`

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- `CarrierId` is a valid optional field on the Snap shipment write schema — confirmed by the parent when scoping; compiled against `@gfs-bifrost/snap` types.
- `snap-queue-polling-service` has a separate lockfile and does not read the field — bump not needed.

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
- [x] 1. Bump `@gfs-bifrost/types` to `^10.12.0` and regenerate the lockfile (AC 1) — verify: `pnpm@11.0.8 install --frozen-lockfile` passes
- [x] 2. Map `CarrierId` in the work order service with two unit tests (AC 1,2) — verify: vitest, positive test fails without the line
- [x] 3. Verify end to end in dev once sftp-connector is also deployed (AC 3) — verify: `snap-get-shipment` shows `CarrierId` — dev e2e on HJF/simulator: S10 HJFD4AC7656638E has CarrierId OWN — done: 7f7df3b

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
- 2026-10-09 [inc 1,2] vitest 588 passed, biome clean, `tsc -p tsconfig.build.json` clean; PR #286 CI all green (incl. black-box tests); merged as 7f7df3b.
- 2026-10-09 [inc 2] Deploy run 37908974186 deployed dev: Cloud Run `snap-adapter-dev-00525-4hp` runs image `dev-7f7df3b`; prod plan succeeded and is waiting at the `terraform-prod` gate (not approved).

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
> SUPERSEDED 2026-10-19 — checked against real dev Snap; see the GADG Evidence bullet.
- Real SnapFulfil acceptance of `OWN`: the simulator doesn't validate `CarrierId` against the CARRIER lookup. The only real-Snap signal is indirect: a GADG shipment accepted the non-lookup `DHL`.
- AC 3: end-to-end `CarrierId` on a real Snap shipment, pending sftp-connector in dev.
- Prod rollout: gate pending; a parked older Deploy run (c5e7bcb, 37900629776) must be rejected or left so it is never approved after this one.
- Changelog: Confluence page 151519235 not appended (page too large to rewrite safely).

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
