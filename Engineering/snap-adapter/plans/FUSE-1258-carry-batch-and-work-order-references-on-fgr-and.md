---
ticket: FUSE-1258
title: Carry batch and work-order references on FGR and WOC
service: snap-adapter
status: complete
created: '2026-09-24'
updated: '2026-10-05'
repo: /home/hjf/code/fuse/snap-adapter
worktree: /home/hjf/code/fuse/snap-adapter/.claude/worktrees/fuse-1258
branch: hjf/fuse-1258-fgr-woc-batch-refs
base: origin/master
base_sha: 5fb41d50f
pr: '257'
tags:
- waypoint
- plan
programme: edi-support
unit: D2
---
# FUSE-1258 — Carry batch and work-order references on FGR and WOC

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
[FUSE-1258](https://globalfreight.atlassian.net/browse/FUSE-1258). The poller's finished good receipt (FGR) and work order confirmation (WOC) gain the batch on each line and, on the FGR, the originating work order's id and customer references. EDIFACT egress (FUSE-1253 increment 6: FGR → RECADV, WOC components → INVRPT) needs both. Done when a published FGR carries `identifiers.workOrderId`/`workOrder.customerRef` and a line `location.batchId`, and a WOC component line carries its consumed `location.batchId`. The types half is [[Engineering/pkg-node/plans/FUSE-1258-types-10-5-0-batch-and-work-order-references-on-|pkg-node FUSE-1258]] (types 10.5.0).

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. FGR lines carry the produced batch where Snap records exactly one for the SKU.
- [x] 2. WOC component lines carry the consumed batch where Snap records exactly one for the SKU.
- [x] 3. An FGR carries the originating work order's id and customer references (`workOrderId`, `businessWorkOrderId`, `salesOrder`, `workOrder.customerRef`).
- [x] 4. Existing FGR/WOC CSV and JSONL outputs are unchanged unless a mapping selects the new fields.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `apps/snap-queue-polling-service/src/core/snap/confirmations/finished-good-receipt.confirmation-handler.ts`, `work-order-confirmation.confirmation-handler.ts`, `work-order.discriminator.ts`, new `work-order.batches.ts` — see [[work-order-family-confirmations]] (its "FGR is receipt-only / doesn't use the Snap client" claim becomes false; update at sign-off).
- `apps/snap-queue-polling-service/src/adapters/snap/api.client.ts` + `types.ts`: new `fetchStockMovementsIntoConsignment`, `fetchStockDetailByStockIds`.
- Canonical types `CanonicalFinishedGoodReceipt`, `CanonicalWorkOrderConfirmationLine` (`@gfs-bifrost/types` 10.5.0) → fuse-mcp `canonical-types.json` owed after publish.
- Blackbox harness `tests/mock-server.ts`, `tests/test-cases.ts` (call counts 21→23, 56→58; FGR MD5).
- NOT touched: `goods-in.confirmation-handler.ts`, `goods-in.matching.ts`, `receipt-confirmation.handler.base.ts`, `fetchStockConsignment` (FUSE-1077's area).

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- R10 `Prime` = the S10 `ShipmentId` (un-suffixed) — live GADG dev: 3/3 WO receipts (GADG084D74AF50F, T2SP031777, GADG5EA0A755B06[-1]) plus FUSE-1055's routing evidence. Hand-made `2SPR876001` (SupplierRef F876FGR) has no S10 — degrades to no references.
- R10 `SupplierRef` = S10 `CustomerRef` — live: all 20 R10s sampled.
- Produced batch is on `/v2/stockconsignment` `Type eq 'IC'` `BatchId` for the receipt's consignment — live: GADG084D74AF50F (TTRS4 → `E2E`), GADG7896F1CD757 (TTRS4 → `TEST-01`).
- Component batch: S10 shipment lines carry **no** batch field, `despatchstock` is empty for WOs, OC stock consignment rows and `AssignRef` stock detail are gone at stage 90 (Snap auto-deassigns with `SDEA` by `SNAPFULFIL` at WO close). Stock movements `ToAssignType eq 'OC' and ToAssignRef eq <consignment>` survive; their `FromStockId`/`ToStockId` resolve via `/v2/stockdetail` `Batch` — live: GADG084D74AF50F (ToStockId merged away, FromStockId SCJU76BX3M → `TEST 123`), T2SP031777 (both → `TEST`), GADG7896F1CD757 (both → `TEST 123`).
- UNRESOLVED: in a real kitting tenant where components are *consumed* (not de-assigned back to stock, as GADG dev does), the source stock record may be depleted and removed, leaving neither stock id resolvable → no component batch. Only observable against a real CT-style kitting WO.

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

- [x] 1. Adapter reads: `fetchStockMovementsIntoConsignment`, `fetchStockDetailByStockIds` (AC 1,2) — verify: api.client spec (filter shape, escaping, dedupe, chunking) — done: 3c83850
- [x] 2. FGR work-order resolution + produced batch (AC 1,3) — verify: FGR spec + live-fixture test + discriminator spec — done: 3c83850
- [x] 3. WOC component batch via movements → stock detail (AC 2) — verify: WOC spec + live-payload spec against real GADG7896F1CD757 movement/stock — done: 3c83850
- [x] 4. Blackbox harness counts + FGR MD5 (AC 4) — verify: local docker blackbox 9/9 against packed types 10.5.0 — done: 3c83850
- [x] 5. Dev verification after types publish + lockfile regen (AC 1-4) — verify: dev-deployed poller publishes an FGR/WOC for a GADG work order carrying the new fields — done on HJF through the snap-api simulator rather than GADG (dev poller `9c33dd3`, 2026-09-30 Evidence bullet), since a GADG work order can only be progressed by hand in the Snap UI
      gate: @gfs-bifrost/types 10.5.0 published and snap-adapter lockfile regenerated
            [x] confirmed 2026-09-24: lockfile regenerated against the published types 10.5.0 (`6f89f07`, Evidence)

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-05 [sign-off, AC 3-4] Read-only checks. (a) AC 4: on sftp-connector `origin/master` (`648ee6e`), `ConfirmationEgressService.process` skips any type with no registered transformer when dynamic mapping is off. The only transformers are purchase order, sales order and stock adjustment, so FGR and WOC only ever render through a mapping, and a field no mapping selects never reaches a CSV or JSONL file. (b) AC 3: in `signoff-ro` (`7c436f9`), `FinishedGoodReceiptConfirmationHandler` sets `workOrderId` from `ShipmentId`, `businessWorkOrderId` and `workOrder.customerRef` from `CustomerRef`, and `salesOrder` from `SalesOrder` on the matched S10. `salesOrder` is covered by the FGR spec (`SO-100`) only, because every dev work order has a null `SalesOrder`. (c) Datadog `fuse.confirmation.published` since the 2026-09-29 prod deploy: dev has 5 `finished_good_receipt` and 1 `work_order_confirmation`; prod has none of either. Prod poller is `prod-0f2024c`, which contains `3c83850`.
- 2026-09-30 [dev e2e, real poller] Dev poller `9c33dd3` (revision `snap-polling-service-dev-00422-cqw`, includes `3c83850`) against the fuse-mocker snap-api simulator (HJF, `9ec3dd2`). A mock `work_order` (MOCK-WO-E2E0930C, customerRef MOCK-WO-REF-0930C) landed as S10 `HJFCBAF4987A6D1`. Components picked with batches CMP-A-0930C / CMP-B-0930C (SPI moves into `OC`/consignment). The R10 (ReceiptId = Prime = S10 id, SupplierRef = CustomerRef) was received with FG batch FG-0930-C1. Then S10 → 90.
  - FGR: the WO resolved by Prime (no "No work order matched" log). sftp wrote `RECADV_HJFCBAF4987A6D1_ecc743ba290df2.edi` with `RFF+ON:MOCK-WO-REF-0930C` (workOrder.customerRef) and `PIA+1+FG-0930-C1:NB`, finished-good line only, UNT+10.
  - WOC: component batches came from `ToAssignType eq 'OC' and ToAssignRef eq …` moves plus Stock Detail by the moves' stock ids. sftp wrote `INVRPT_HJFCBAF4987A6D1_05a103461b4c3d.edi` with `RFF+ON:MOCK-WO-REF-0930C` and LIN 1/2 = HJF-SKU-1 `GIN+BX+CMP-A-0930C`, CU32555 `GIN+BX+CMP-B-0930C`. No finished-good LIN. UNT+15.
  - Both files parse with `@gfs-bifrost/edi` 0.6.0, with matching control refs.
  - Not directly observed: `identifiers.workOrderId` / `businessWorkOrderId` / `salesOrder` on the published FGR. Collector's MCP can't list FGR, and the files only carry `workOrder.customerRef`.
  - Mock-originated WOs carry routing `source: "mock"` / `"mock-sftp"`, so sftp's `source = "sftp" OR broadcast` filter drops them. HJF backend `broadcastConfirmations` was set true for the run, then back to false.
- 2026-09-29 [prod] Shipped in poller `3c83850` (revision `snap-polling-service-prod-00084-7jv`, 13:18Z) with #257 + #263 + parked FUSE-1050/1192/1193/Renovate #261; plan (7 add stock-sync infra + image/env) shared and agreed with Harry. First 20 min: healthy, stock-sync tick evaluated, `Consignment StU not found` warn at pre-existing rate (~390/20min on b7ad73c). No stock adjustment / FGR / WOC through the new revision yet — first real one still to check. Note: collector on types ^10.7.0 strips the new fields, so Transaction History won't show them yet.
- 2026-09-24 [inc 5, partial] Dev deploy of 6f89f07 (Manual Deploy run 36043226632; plan 0/1/0 = image + standing VERSION-env drift; revision snap-polling-service-dev-00405-qv5 running dev-6f89f07). No R10/S10 entries were open on the GADG dev outbound queue, and Snap refuses to reopen a processed one (PATCH GAOB001346 → "Cannot update fields"). So no FGR/WOC went through the deployed revision. That revision did publish a good_out (DOCKBAY), and its errors were the pre-existing FUSEDEV/HJF 404s seen on master. Dev reverted to master 5fb41d5 (run 36043933551, revision 00406-8c8, polling normally).
- 2026-09-24 [inc 5, partial] Branch handlers run locally against live GADG dev Snap for 3 completed WOs. FGR: GADG084D74AF50F workOrderId=GADG084D74AF50F, businessWorkOrderId=workOrder.customerRef=E2E09031538EMIB, TTRS4 batchId=E2E; T2SP031777 → TESTINGMEWO / TESTINGME; GADG7896F1CD757 → WO-20260819-00024 / TEST-01. WOC components: TTRS3 TEST 123, TTRS TEST, TTRS3 TEST 123. All schema-valid. salesOrder absent because Snap SalesOrder is null on every dev WO.
- 2026-09-24 Lockfile regenerated to types 10.5.0 (6f89f07); 503/503, lint 0, tsc 0, local blackbox 9/9 against the registry package.
- 2026-09-24 [inc 4] Local blackbox (`docker-compose-4pipeline.yaml` + `tests/start-test.sh`, scratch copy with types pinned to the packed 10.5.0 tarball, host ports stripped): 9/9 PASS; call counts 23/58/40/11. Published FGR carried `identifiers.workOrderId: FGR001`, `businessWorkOrderId: WORKORDER-1`, `workOrder.customerRef: WORKORDER-1`, line `location.batchId: KITBATCH001`; new FGR MD5 `ece5818eebd538526cfa820332f9799d`.
- 2026-09-24 [inc 1-3] poller vitest 503/503 (was 461), `lint` exit 0, `build:check` exit 0 — against packed types 10.5.0 swapped into node_modules (not committed).
- 2026-09-24 [inc 2,3] Live GADG dev Snap reads (snap MCP) establishing the field sources — see Assumptions.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
> SUPERSEDED 2026-10-05 — types 10.5.0 was published, and the dev e2e ran on 2026-09-30 through the real dev poller (HJF, simulator). See Evidence.
- Dev e2e (increment 5): blocked on publishing types 10.5.0; CI install is red until then.
- Component batch on a WO whose components are genuinely consumed (see UNRESOLVED).
- No prod FGR or WOC has gone through the new code yet (none published in prod since 2026-09-29). `identifiers.workOrderId`, `businessWorkOrderId` and `salesOrder` were not seen on a published dev FGR: collector's MCP can't list FGRs, and the EDI files carry only `workOrder.customerRef`. The local live-Snap run and the black-box harness are the evidence for those fields.
- AC 4 is structural: sftp-connector FGR/WOC egress is mapping-only (`confirmation-egress.service.ts` `serialise` — no registered transformer for either type), so unselected fields can't reach CSV/JSONL. fapi's WOC webhook sends the canonical, so it gains the additive fields.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-09-29** — 2026-09-29: rebased onto master (was conflicting on the poller lockfile after the Renovate ^10.5.0 bump #256); the lockfile commit dropped as redundant, branch is one commit 8b51b36; 561/561, lint + tsc clean. Rebased rather than merged because commit-mode comment-density checks a merge commit against HEAD and counts master's incoming teammate comments as added. Re-confirmed from the snap MCP entity registry: tasks and stockMovements are read-only, so a dev work order can only be progressed by a person in the Snap UI.

- **2026-09-24** — Dev e2e through the deployed revision needs a fresh completed WO (human RF pick + receipt in GADG dev Snap). Processed snapOutbound entries can't be reopened via API, and the Snap API has no task-actioning route. Local live-Snap run of the branch handlers used as interim evidence.

- **2026-09-24** — FUSE-1077 overlap check: #246 rewrites goods-in.confirmation-handler.ts and deletes goods-in.matching.ts; #249/#255 add api.client methods after fetchStockDetail. This change touches none of those functions and does not reuse goods-in.matching (it is being deleted); new api.client methods are appended at the end of the class to keep the textual conflict trivial.

- **2026-09-24** — WOC finished-good lines get no batch (only components are in scope); the produced batch lives on the FGR.

- **2026-09-24** — FGR → WO candidate order: ShipmentId=Prime first (FUSE-1055 already trusts Prime for routing), then the exact inverse of the WOC's receipt candidates. businessWorkOrderId = WO CustomerRef, matching the WOC; the original businessWorkOrderId is hashed into ShipmentId at create time and is not recoverable from Snap.

- **2026-09-24** — New Snap lookups (FGR work-order search, FGR IC stock, WOC movements/stock) let errors propagate so mapEntriesInIsolation skips the entry and the next poll retries; the sibling WOC receipt search degrades on error instead. Chosen so a transient Snap blip can't publish a batch-less/reference-less confirmation that then gets cleared.

- **2026-09-24** — One batch per line or none: a SKU resolving to >1 distinct batch leaves batchId off and logs a warn. Splitting FGR/WOC lines to batch grain (as FUSE-1077 does for goods-in/pick) is out of scope.

- **2026-09-24** — Deviation from the ticket hint: WOC component batch is NOT on shipment lines and the goods-out/pick pattern (OC stockconsignment / AssignRef stockdetail) is empty at stage 90 because Snap de-assigns component stock at WO close; used stock movements into the WO consignment → stockdetail by From/ToStockId instead (verified live on 3 GADG WOs).

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
