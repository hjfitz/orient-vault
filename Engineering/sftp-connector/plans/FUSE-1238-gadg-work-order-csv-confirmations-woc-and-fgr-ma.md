---
ticket: FUSE-1238
title: 'GADG work-order CSV confirmations: WOC and FGR mapping fixes'
service: sftp-connector
status: active
created: '2026-10-09'
updated: '2026-10-09'
repo: /home/hjf/code/fuse/sftp-connector
worktree: none
branch: none
base: origin/master
base_sha: none
pr: null
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: low
---
# FUSE-1238 — GADG work-order CSV confirmations: WOC and FGR mapping fixes

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
Tom Dunn (ILG QA) tested the work-order CSV flows on GADG dev (connector "Primary SFTP") and reported the WOC and FGR egress files
are wrong: line number is Snap's internal key, Qty/Produced columns carry planned quantities, FGR `WorkOrderRef` is the internal id, and
FGR has a Rejected column he doesn't want. All three are mapping edits (inbound-style rules reused on egress), no code. Attached to the
Distraction Duty ticket FUSE-1238 by choice, not a defect ticket of its own. The fifth point, mapping a default carrier on work-order
ingest, needs a canonical field and code in four repos and is blocked on a product question (see UNRESOLVED), so it gets its own
per-service plans once answered; this plan only carries the config half.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. WOC file line number equals the line number Snap holds for the line (`SOLineId`; 1 on every line of Tom's order)
- [ ] 2. WOC file: component rows show the consumed quantity (QtyPicked) in `WOCLines_Qty` with `WOCLines_Produced` blank; the finished-good row the reverse
- [ ] 3. FGR file `WorkOrderRef` is the customer's work-order ref (e.g. `WO-20261007-TD1`), not the internal id
- [ ] 4. FGR file has no `FGRLines_Rejected` column; `FGRLines_Produced` is the only quantity column
- [ ] 5. Pre-edit mappings are saved in this plan and the before/after rules are on FUSE-1238 (config-write leaves no audit record)
- [ ] 6. Tom re-runs his WO test on GADG dev and confirms 1-4 (blank cells on the other role's row are acceptable to him)

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- config-service `CONNECTOR_MAPPING` for GADG / "Primary SFTP" (`sf_c18b98604b4242ec819aba8bbdf4b5f9` / `conn_179b24164937477a8517a4a92976697d`), use cases `work_order_confirmation` and `finished_good_receipt`. Written with the Fuse MCP `config-write` (PUT `{status, mapping}`).
- sftp-connector `code/src/core/confirmation-transformer.ts` (dynamic egress path; rules are stored inbound-style and inverted on egress, `backfillColumns` blanks absent values, `orderColumns` follows `columnOrder`). Read, not changed.
- snap-adapter's poller handlers build the canonicals (`work-order-confirmation.confirmation-handler.ts`, `finished-good-receipt.confirmation-handler.ts`). Read, not changed. See [[work-order-family-confirmations]] but note its FGR parts are stale since the batch/work-order-reference work; trust the handler.
- G3 applies (config is the contract, a mapping edit is a customer-visible release with no diff). The `wp context` path trigger is `code/src/import`, which this plan never touches, so the guardrail will not fire by itself.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- The "line number in the UI" is `SOLineId` — established 2026-10-09 from `snap-get-shipment GADG639BE58F41B`: all three lines carry `SOLineId: 1`, which is what Tom wrote ("1 in the lines table"). So A1 yields 1,1,1; his literal ask, though not unique per line. Snap UI display of `SOLineId` is otherwise undocumented.
- WOC line `soLineId` is populated only for shipment-derived lines (handler l.445); receipt-only by-product lines render blank — source read by the grounding review.
- WOC quantities are role-scoped (`scopeQuantitiesToRole`, handler l.375): `consumed` = QtyPicked on components, `produced` = receipt QtyReceived on the finished good — source read.
- FGR `produced` is never blank (`QtyReceived ?? 0`); FGR `businessWorkOrderId` is blank if the S10 lookup is not a unique hit — source read.
- A deleted rule inside the `rules.lines` array and a shortened `columnOrder` array are replaced wholesale by config-service PUT (arrays replace, objects merge) — config-service CLAUDE.md; the FUSE-1010 ledger shows the proven PUT shape (`status` is required). Read each mapping immediately before writing it.
- The fuse-ui WOC picker (`work-order-confirmation-keys.json`) labels `line` "Line Number" and does not list `soLineId`, so after A1 the live mapping holds a `from` the editor does not offer. Not checked how the editor re-saves an unlisted key. A follow-up fuse-ui change (add `soLineId`, relabel `line` "Snap Line Key") is the root-cause fix and is not in this plan.
- WOC header `WorkOrderRef` maps `identifiers.workOrderId`, the internal hash id, the same class of defect as FGR point 3. Not in Tom's list, left unchanged here.
- FGR `FGRLines_LineNumber` is also Snap's internal key and the FGR canonical has no `soLineId`; fixing it needs a types change. Tom has not raised it.
- UNRESOLVED: the same Primary SFTP connector was accepted by Schuster under FUSE-866 expecting the Snap line key on WOC. Do Tom's expectations replace Schuster's? (Same connector, same file.)
- UNRESOLVED: dropping `FGRLines_Rejected` removes rejected quantity from the FGR file. Does ILG have a consumer for it? Tom asked for a single column, so the plan proceeds unless he says otherwise.
- UNRESOLVED: dev only. GADG prod has no `work_order` mapping as of the 2026-09-24 audit; a prod edit is a separate deliberate step.
- RESOLVED 2026-10-09 (Harry): field is `identifiers.carrierId`. Snap check: the dev tenant's `CARRIER` lookup holds only `NETCOURIER`, but a GADG shipment from 2024 (`GADGS011060`) carries `CarrierId: DHL`, and all 100 most recent GADG shipments carry `NETCOURIER`. So `CarrierId` is not constrained to the lookup, and `OWN` should be accepted. The OpenAPI `maxLength: 1` (shipment/sales-order header, ~l.1660/2459) conflicts with the 15 on the shipment schema (l.1077) and with live data, so it is a spec error. Not proven for a write of `OWN`: proof is the dev check after both services deploy (`snap-get-shipment` shows `CarrierId: OWN`).
- (was UNRESOLVED, carrier point, blocks the code half): see Decisions & deviations. Snap's CARRIER lookup on the GADG dev tenant holds only `NETCOURIER`; the work order Tom created already shows `CarrierId: NETCOURIER`. Is `OWN` valid? `identifiers.carrierId` (his wording, mirrors sales order) or `shipping.carrier.id` (PO and RGA)?

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

- [ ] 1. Snapshot both live mappings (`config-read`) into Evidence below as the rollback copy, and get a real WOC/FGR canonical for Tom's order (replay-service stored copy or the poller's publish log; `mock-generate` if neither) — verify: the WOC canonical's lines carry `soLineId` (if absent, A1's line-number rule would always blank, so stop and re-plan)
- [x] 2. A1: PUT `work_order_confirmation` with `rules.lines` rewritten: `WOCLines_LineNumber` → `soLineId`, `WOCLines_Qty` → `quantities.consumed`, `WOCLines_Produced` → `quantities.produced`; header untouched (AC 1,2) — verify: `config-read` shows exactly those three `to` values and nothing else changed — config-write PUT read back: rules match — done: none
- [x] 3. A2: PUT `finished_good_receipt` with header `WorkOrderRef` → `identifiers.businessWorkOrderId`, the `FGRLines_Rejected` rule deleted from `rules.lines`, and `columnOrder` re-sent without `FGRLines_Rejected` (AC 3,4) — verify: `config-read` shows the rule and the column gone; if the rule survives the PUT, DELETE then POST the mapping — config-write PUT read back: rules match — done: none
- [ ] 4. Prove the egress output at the layer under test: `mock-send` the canonicals from inc 1 with fresh refs and `broadcast: true` (record types `work_order_confirmation` / `finished_good_receipt`), then read the generated CSVs from the connector's GCS dir with gcloud (AC 1,2,3,4) — verify: header row has no Rejected column; WOC line numbers = 1; component rows have Qty and blank Produced, FG row the reverse; FGR `WorkOrderRef` = the `WO-…` ref
      gate: Tom told that test files will appear in his Primary SFTP folder (the mocker writes into his live QA connector), and dedupe has not held the ids (`dedupe-release` if it has)
            [ ] confirmed
- [x] 5. Record the before/after rules on FUSE-1238 as a Jira comment and in Evidence (AC 5) — verify: comment exists and names both use cases — FUSE-1238 comment 24911 — done: none
- [ ] 6. Ask Tom to re-run a WO end to end on GADG dev and confirm the four points (AC 6) — verify: Tom's reply, linked in Evidence
      gate: Tom has confirmed the re-test result
            [ ] confirmed

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-09 [inc 6] Carrier chain in dev: types 10.12.0 (pkg-node#265), snap-adapter#286, sftp-connector#304/#305 and fuse-ui#296 merged and deployed to dev; header default `identifiers.carrierId = OWN` added to GADG Primary SFTP `work_order` mapping (config-read back). A mock-send of a work order with `carrierId: OWN` (correlation `mock-fuse1238-wo-carrier-1`) published but never reached dedupe or Snap, cause not found, so the end-to-end proof is still owed. Tom Dunn messaged (5 DMs) to re-run a WO CSV and confirm the files and that Snap shows `CarrierId: OWN`.
- 2026-10-09 [inc 2,3] `config-write` PUT on GADG dev Primary SFTP, both returned 200 and the response body (read back from config-service) shows the intended rules. WOC `lines`: `WOCLines_LineNumber`→`soLineId`, `WOCLines_Qty`→`quantities.consumed`, `WOCLines_Produced`→`quantities.produced`, header and `groupBy` unchanged, no `columnOrder` (as before). FGR: header `WorkOrderRef`→`identifiers.businessWorkOrderId`; `FGRLines_Rejected` rule gone from `lines`; `columnOrder` is the seven remaining columns. The second GADG connector (AlexP-Test) was not touched.
- 2026-10-09 [inc 1] `snap-get-shipment GADG639BE58F41B` (GADG dev Snap): S10, `CustomerRef: WO-20261007-TD1`, three lines all `SOLineId: 1` (components TTRS3 picked 2, TTRS2 picked 4; finished good TTRS4 ordered 1), `CarrierId: NETCOURIER`. Matches Tom's CSVs and his "1 in the lines table".
- 2026-10-09 [inc 1] live mappings read with `config-read` before any edit (rollback copy). WOC `lines`: `WOCLines_Role`→`role`, `WOCLines_SkuId`→`skuId`, `WOCLines_LineNumber`→`line`, `WOCLines_Qty`→`quantities.required`, `WOCLines_Produced`→`quantities.ordered`; header `AccountID`→`identifiers.businessId`, `WorkOrderRef`→`identifiers.workOrderId`, `CustomerWORef`→`identifiers.businessWorkOrderId`, `Warehouse`→`location.warehouse`; `groupBy: [WorkOrderRef]`; no `columnOrder`. FGR header: `AccountID`→`identifiers.businessId`, `ReceiptRef`→`identifiers.id`, `WorkOrderRef`→`identifiers.workOrderId`, `Warehouse`→`location.warehouse`; lines `FGRLines_SkuId`→`skuId`, `FGRLines_LineNumber`→`line`, `FGRLines_Produced`→`quantities.produced`, `FGRLines_Rejected`→`quantities.rejected`; `groupBy: [ReceiptRef]`; `columnOrder`: AccountID, ReceiptRef, WorkOrderRef, Warehouse, FGRLines_SkuId, FGRLines_LineNumber, FGRLines_Produced, FGRLines_Rejected. Both `status: active`, `friendlyName` "Work Order Confirmations" / "Finished Good Receipt Confirmations".

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- A self-driven end-to-end on GADG is not possible: GADG's backend is the real dev Snap (`ilg001testapi`), not the snap-api simulator, and `replay-retry` does not regenerate an egress file. Only Tom's re-test (inc 6) proves the poller → mapping chain; inc 4 proves the mapping layer.
- The soLineId = line number reading rests on one order where every line is 1.
- Unmatched R10 receipt (WOC finished-good Produced blank) and non-unique S10 (FGR `WorkOrderRef` blank) are not exercised.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- 2026-10-09 Scope split by the review: this plan is config-only (`branch: none`, no PR) and covers Tom's WOC/FGR points. The carrier point is a different shape of work (canonical type 10.x, snap-adapter, sftp-connector lockfile plus a `minimumReleaseAgeExclude` entry in `code/pnpm-workspace.yaml`, fuse-ui keys, fuse-mcp data) and, per Waypoint's one-plan-per-service rule, will be planned per service once these are answered: (1) is `OWN` a valid Snap carrier on GADG (the CARRIER lookup holds only `NETCOURIER`; the OpenAPI spec says `CarrierId` maxLength 1, but the dev shipment already holds the 10-character `NETCOURIER`, so the spec is probably wrong); (2) `identifiers.carrierId` or `shipping.carrier.id`. Also noted by review for that work: types 10.11.0 is already claimed by pkg-node PR #262 (take the next free version at merge time); fapi's `POST /api/v2/work-orders` and collector strip the new field until they bump `types`; the changelog row goes in the org contract `/home/hjf/code/CLAUDE.md`, not a repo file.
- 2026-10-09 Dropped from the first draft: a snap-adapter default of `UnitOfMeasure` "EA" for the API work-order path (snap-adapter holds no defaults; Matt's FUSE-1297 is docs-only and says the code is correct). That ticket owns the API/Swagger and unit-of-measure report.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
- The fuse-ui work-order-confirmation picker labels `line` "Line Number", but `line` is Snap's internal line key; the customer-visible number is `soLineId` (`SOLineId`, defaulting to the 1-based array position at WO create), and the picker does not list it.
- `config-write` mapping edits bypass the fuse-ui audit trail (and config-service has no revision-history endpoint), so the before/after must be recorded by hand.
- A newly published `@gfs-bifrost/types` version needs an exact-version `minimumReleaseAgeExclude` entry in `code/pnpm-workspace.yaml` (precedent 10.4.0, 10.8.0, edi 0.8.0).
- Snap's CARRIER lookup on the GADG dev tenant has a single value, `NETCOURIER`; a work order created without a carrier already carries it.
