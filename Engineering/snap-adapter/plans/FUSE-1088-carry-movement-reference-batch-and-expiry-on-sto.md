---
ticket: FUSE-1088
title: Carry movement reference, batch and expiry on stock adjustment confirmations
service: snap-adapter
status: complete
created: '2026-09-29'
updated: '2026-10-05'
repo: /home/hjf/code/fuse/snap-adapter
worktree: /home/hjf/code/fuse/snap-adapter/.claude/worktrees/fuse-1088
branch: hjf/fuse-1088-stock-adjustment-refs
base: origin/master
base_sha: d80b2c35d
pr: '263'
tags:
- waypoint
- plan
programme: edi-support
unit: D1
---
# FUSE-1088 — Carry movement reference, batch and expiry on stock adjustment confirmations

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
[FUSE-1088](https://gfsdeliver.atlassian.net/browse/FUSE-1088). Scope settled by Jack Bailey on 2026-09-24: movement reference, batch and expiry, all yes. The poller's stock adjustment confirmation now carries `identifiers.movementRef` (Snap's movement-line key, which Jitterbit sent as `EntityID`) and a `batchId` + `expiry` on each of `from` and `to`, read off Stock Detail by the move's stock ids. Proven when a live GADG dev move of each type maps to a canonical carrying those fields and passing `CanonicalStockAdjustmentSchema`. Types side: [[FUSE-1088-types-10-8-0-movement-reference-batch-and-expiry|pkg-node FUSE-1088]] (types 10.8.0).

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. Every stock adjustment carries `identifiers.movementRef` = `<SiteId>_<MoveType>_<MoveId>_<MoveLineId>`.
- [x] 2. `from.stockId` is populated from Snap's `FromStockId` (it was always empty, read from the mis-cased `FromStockID`).
- [x] 3. `from.batchId`/`from.expiry` and `to.batchId`/`to.expiry` come from the Stock Detail row of that side's stock id, where one exists.
- [x] 4. A failed Stock Detail lookup still publishes the adjustment, without batch/expiry, and logs `StockAdjustmentFetchEvent.Failed`.
- [x] 5. Each line of a multi-line move is reported as itself, not as the move's first line.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `apps/snap-queue-polling-service/src/core/snap/confirmations/stock-adjustment.confirmation-handler.ts`, `types.ts` (`SnapStockAdjustment`)
- `adapters/snap/api.client.ts`: new `fetchStockDetailByStockIds` (same signature and body as FUSE-1258's on #257), `fetchStockMovement` now takes the natural key
- `core/snap/outbound-queue/movement.entries.ts`
- Canonical type `CanonicalStockAdjustment` (`@gfs-bifrost/types` 10.8.0)
- Blackbox: `tests/mock-server.ts`, `tests/test-cases.ts` call counts

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- `EntityID` = site_type_moveId_lineId: the example `0002_SADJ_SADJ001072_PBWCQCABEY` has exactly that shape, and those four values are the natural key of Snap's `/v2/stockmovements/{site}/{type}/{moveId}/{line}` route (confirmed live on GADG dev) and the four the `STOCK_MOVE` queue key carries. The example move is not in dev, so not matched row-for-row.
- Stock Detail is current state, so a consumed or zeroed stock row has no batch by poll time: seen live on `SDISS`/`SDISI`.
- Snap's `DateExpiry` has no zone. It parses as container-local time, UTC on Cloud Run, same as pick/pack.

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

- [x] 1. Populate movementRef, fix FromStockId, and read batch/expiry off Stock Detail per side. Blackbox call counts +1 per client (AC 1,2,3,4) — verify: unit suite + live GADG dev run — live GADG dev 10/10 valid, batch+expiry where stock row exists — done: 191ab1d
- [x] 2. Fetch each queued movement by its full natural key, not the move id's first line (AC 5) — verify: live multi-line move `6HOL00122` yields both lines — 6HOL00122 both lines reported — done: 191ab1d

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-05 [sign-off, AC 1-5] Read-only checks. (a) AC 4: Datadog has one `Stock adjustment auxiliary data fetch failed` warn (`resource: stock_detail`, `businessId: HJF`) at 2026-09-30T07:48:06Z from dev `snap-polling-service` version `9c33dd3`. That is the first-attempt move in the 09-30 bullet below, which was still published without batch. In `signoff-ro` (`7c436f9`), `fetchStockById` logs `StockAdjustmentFetchEvent.Failed` and returns an empty map, so the move is still mapped. (b) Prod: the poller is on `prod-0f2024c` (revision `snap-polling-service-prod-00087-ht2`), which contains `191ab1d`. `fuse.confirmation.published{environment:prod,recordtype:stock_adjustment}` from `snap-polling-service` since 2026-09-29T13:18Z is 16,795: PURDYFIGG 16,297, SAIRA 494, CHAMPO 4. Prod has logged no Stock Detail fetch failure. (c) AC 1, 2, 3, 5 rest on the 09-30 dev e2e and the 09-29 live GADG runs below.
- 2026-09-30 [dev e2e, real poller] Dev poller `9c33dd3` (revision `snap-polling-service-dev-00422-cqw`, includes `191ab1d`) against the fuse-mocker snap-api simulator (HJF, `9d15612`/`642efa6`, which now serves the per-line `/v2/stockmovements/{site}/{type}/{moveId}/{line}` route and Stock Detail by `StockId eq … or …` with the live column set). A 2-line SHOL (HJF-SKU-1 ×3 batch HJFB-0930C exp 2027-03-31, CU32555 ×2 batch HJFB-0930D exp 2027-04-30), move `HJF5025C2F94BAA`, gave 2 STOCK_MOVE items and 2 published `stock_adjustment` records (collector, staging): `movementRef` `1_SHOL_HJF5025C2F94BAA_HJF49E6C567C116` / `…_HJF7E60D6C5B0A9`, `from/to.stockId` HJF067C33D13C4B / HJFB5D0DADD45B1, `batchId` + `expiry` on both sides, sequence 1001/1002, `to.status` 01. sftp (EDI flag-on throwaway) wrote `INVRPT_HJF5025C2F94BAA_67668b88a6068c.edi` with `GIN+BX` + `DTM+36` per line, UNT+16; it parses with `@gfs-bifrost/edi` 0.6.0. Queue items cleared at 07:54Z. First attempt (move HJFF9A536AC58F9) carried stockIds but no batch: the simulator's Stock Detail rows lacked columns `SnapStockDetailSchema` requires, so the poller's best-effort fetch failed and it published without batch. That was a simulator gap, fixed in `642efa6`, not a poller bug.
- 2026-09-29 [prod] Shipped in poller `3c83850` (revision `snap-polling-service-prod-00084-7jv`, 13:18Z) with #257 + #263 + parked FUSE-1050/1192/1193/Renovate #261; plan (7 add stock-sync infra + image/env) shared and agreed with Harry. First 20 min: healthy, stock-sync tick evaluated, `Consignment StU not found` warn at pre-existing rate (~390/20min on b7ad73c). No stock adjustment / FGR / WOC through the new revision yet — first real one still to check. Note: collector on types ^10.7.0 strips the new fields, so Transaction History won't show them yet.
- 2026-09-29 [inc 1,2] Dev deploy of `927597a` (run 36549822442, revision `snap-polling-service-dev-00415-99g`). The plan was image, VERSION, and the standing sidecar `container-dependencies` annotation and sensitive env, the same as master's last dev apply. From 09:35 to 09:57Z no new STOCK_MOVE queue items arrived: ACADEMIC's 5 were already claimed and skipped; GADG had none. Snap exposes no write route that creates a stock movement (stockMovements, tasks and stockDetail are NO_WRITE), so there is no in-dev published confirmation. Dev was reverted to master `3c1578b` (revision 00416).
- 2026-09-29 [inc 1,2] Rebased onto `3c1578b` (Renovate types ^10.7.0). The lockfile resolves published types 10.8.0 (`927597a`, 5-line diff, frozen install OK). Lint 0, `build:check` 0, 557/557. Blackbox in an isolated compose project (`fuse1088bb`, no container names, no host ports): 9/9 PASS, with call counts 22 / 62 / 46 / 11 as predicted.
- 2026-09-29 [inc 2] Live GADG dev, branch build: `6HOL00122` lines `RHQ376NPAJ` (LIZTEST) and `RHQ376Q2DT` (SKU-1) map to two distinct canonicals with their own movementRef. On master `/v2/stockmovements/6HOL00122` returns both lines and the code takes `Results[0]` for both queue items. 22 of 1,075 recent GADG dev moves are multi-line.
- 2026-09-29 [inc 1] Live GADG dev, branch build against packed types 10.8.0 (`resolveMovementEntries` → `mapOwnedEntries` → `confirmationsToCanonical` → `validateCanonicalConfirmations`): 10 moves across SADJ±, SHOL, SREL, SREC, SREG, SRET, SDISS, SDISI, SOWN, 10/10 valid, and valid after a JSON round-trip. Batch+expiry present on SHOL/SREL (both sides) and SREC/SREG (to side); SRET batch only; SADJ on non-batch SKUs, SDISS/SDISI and SOWN have none.
- 2026-09-29 [inc 1,2] Poller unit suite 557/557, `lint` 0, `build:check` 0.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
> SUPERSEDED 2026-10-05 — the 2026-09-30 dev e2e published two stock adjustments through the real dev poller (`9c33dd3`), and prod has published them since 2026-09-29. See Evidence.
- No published stock adjustment confirmation from the branch revision in dev: no STOCK_MOVE item arrived in the window. Proving it needs a stock movement made in the Snap UI while the branch is on dev. The live-Snap local run is the evidence for the mapping.
- The field values on prod payloads (`movementRef`, `from`/`to` batch and expiry) were not inspected. Prod is evidenced only by publish volume and the absence of fetch failures. Collector was on types ^10.7.0 when this shipped, so Transaction History may not show the new fields.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-09-29** — Both from and to batch/expiry are exposed. Jitterbit's BatchID rule (from-batch, else to-batch) is left to the mapping/serializer, per Jack's 'expose both' scope.

- **2026-09-29** — Batch/expiry come from Stock Detail by FromStockId/ToStockId, in one ORed lookup per poll. fetchStockDetailByStockIds copies FUSE-1258's (#257) signature and body so either merge order resolves trivially; not based on that unmerged branch. No cross-tenant guard added to STOCK_MOVE (out of scope).

- **2026-09-29** — Fixed a second pre-existing bug beyond the FromStockID one: movements were fetched by MoveId and Results[0] taken, so each line of a multi-line move came back as line 1. It would have stamped line 1's movementRef on every line. Kept as its own commit (a9b3479) so it can be dropped.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
