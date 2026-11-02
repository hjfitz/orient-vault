---
ticket: FUSE-1259
title: Ingest inbound DESADV as purchase orders and work orders
service: sftp-connector
status: complete
created: '2026-09-30'
updated: '2026-09-30'
repo: /home/hjf/code/fuse/sftp-connector
worktree: /home/hjf/code/fuse/sftp-connector/.claude/worktrees/fuse-1259-desadv-inbound
branch: hjf/fuse-1259-desadv-inbound
base: origin/master
base_sha: 9eddde711
pr: '292'
tags:
- waypoint
- plan
programme: edi-support
unit: I4
impl_model: sonnet
impl_effort: medium
---
# FUSE-1259 — Ingest inbound DESADV as purchase orders and work orders

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
[FUSE-1259](https://gfs-bifrost.atlassian.net/browse/FUSE-1259) / EDI Support unit **I4**. An EDIFACT **DESADV** dropped into `to_ilg/create_purchase_order/` becomes a purchase order (an ASN, Snap receipt), and one dropped into `to_ilg/create_work_order/` becomes a work order (kitting, Snap S10). Both go through the existing flatten → connector mapping rules → `create_record_request` pipeline, and kit vs component roles are decided by mapping rules and dictionaries, never by code. Consumes `@gfs-bifrost/edi` 0.8.0 from [[../../pkg-node/plans/FUSE-1259-edi-shared-segment-readers-and-inbound-desadv-no|the pkg-node plan]]. Proven on HJF in dev against the fuse-mocker Snap simulator, which also delivers programme unit **H3**.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. A DESADV in the PO action directory becomes one canonical purchase order per file, and a receipt with the mapped refs and lines is created in Snap (simulator in dev).
- [x] 2. A kitting DESADV in the WO action directory becomes one work order with a finished-good line and component lines, with roles and quantities set only by mapping rules and a dictionary, and an S10 is created in Snap.
- [x] 3. ORDERS in the PO directory and INSDES/PRICAT in their directories produce the same rows as before, apart from the new keys edi 0.7.0 adds.
- [x] 4. A misrouted file fails the file with `EdiMessageTypeMismatchError` naming the accepted types: INSDES into WO gives declared `DESADV`; INSDES into PO gives `ORDERS or DESADV`; DESADV into sales order fails. The file lands in `error/` and a `create_data_failure` is published.
- [x] 5. A DESADV whose mapping yields no required reference (`workOrder.customerRef`, `supplier.reference`) becomes a per-record validation failure on the retry queue, not a Snap write. An over-length mapped value (a 16-character BGM into `PurchaseOrder`, limit 13) is rejected visibly and never silently truncated.
- [x] 6. (by composition with FUSE-1258's dev e2e, see Not verified) The reference a work order is ingested with comes back on the finished-good RECADV (`RFF+ON` from `workOrder.customerRef`).
- [x] 7. No sftp-connector source recognises a partner's codes. CT exists only in test fixtures and in HJF's dev config.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `code/src/import/csv/edi-to-json.ts`: `messageTypeByAction` (1:1 today) becomes an accepted set per action. Before `flattenObject`, the header drops every array key except `lines`, so `packages[]` is not repeated onto every row.
- `code/src/import/translators/{purchase-order,work-order}.translator.ts`: **no code change expected**, tests only. `purchase-order.translator.spec.ts` doesn't exist yet and is created here.
- `code/package.json`: `@gfs-bifrost/edi` `^0.6.0` → `^0.8.0`.
- **Downstream, reference only, no change:**
  - snap-adapter `core/puchase-order` and `core/work-order`: the field tables were verified by the fact-check reviewer.
  - poller `finished-good-receipt.confirmation-handler.ts`: reads `customerRef` from the linked S10's `CustomerRef`.
  - fuse-mocker `snapvalidate.go` (length caps) and `wms/enrichment.go` (`ensureWorkOrderReceipt` mints the R10 on the S10's first stage advance).
- Guardrail: [[sftp-connector/known-context|known-context]]: "validation → Retry Queue" and "customer refs only from mapping" both apply.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **The action directory declares the message type, and one file carries one message.** This holds already (FUSE-1231) and is kept. Routing by content inside one directory would be a new ticket.
- **One mapping per (username, use case), so the PO mapping serves ORDERS and DESADV.** First-non-empty-wins across rules to one `to` makes a coalesce; `messageType` is also on every row. New rules use **raw** keys only (`parties.SU.gln`), because 0.7.0 gives ORDERS raw parties too; the role aliases remain for FUSE-1231-era paths only. CT sends no ORDERS, so the mapping isn't shaped around ORDERS.
- **No types or snap-adapter change is needed for the ACs.** PO: `supplier.reference`→SupplierRef, `identifiers.purchaseOrder`→PurchaseOrder, `asnNumber`→ASNumber. WO: `workOrder.customerRef`→CustomerRef, `identifiers.salesOrder`→SalesOrder. `businessWorkOrderId`/`customer.reference` reach no Snap field, and `businessWorkOrderId` only feeds the ShipmentId hash (`createDeterministicId(businessId, connectorId, customerRef, businessWorkOrderId ?? id)`), so egress must not expect it echoed. Verified by the fact-check reviewer against snap-adapter `origin/master`.
- **Recorded reference hypothesis** (egress umbrella plan; FUSE-1258 proved `customerRef` → `RFF+ON`): kitting BGM → `workOrder.customerRef` (16 characters, within the 20 limit), and `RFF+DQ` → `identifiers.salesOrder` (≤15). To be confirmed by Harry, not reopened.
- **Snap length caps are expected behaviour.** snap-adapter rejects and never truncates, so data is shortened at source. A wrongly chosen field fails late, at snap-adapter after dedupe.
- **Mapping must cover schema-required fields:**
  - PO line: `product.unitOfMeasure` (`QTY+47E` has no unit, so it needs a default) and `identifiers.lineNumber`.
  - WO line: `workOrderId`, `line`, `skuId` (top level) and a `product.unitOfMeasure` default.
  - Header: `identifiers.customerId` and `identifiers.businessId`. Mapping `identifiers.id` replaces the factory `identifiers` block, so everything else in it must be mapped or defaulted.
  - Both need a header `groupBy: ["documentNumber"]`, or one file splits into several records.
- **`getHeaderValues` sums only `quantities.ordered` into `LineQty`.** The DESADV mappings therefore set `ordered` as well as `advised`, and no code fix is made.
- **Known exposure, not fixed here:** snap-adapter's PO/WO create paths do a keyed PUT that replaces child lines (only sales orders read before writing). A *changed* resend passes dedupe and re-PUTs a live S10, and prod has 0 WO mappings, so CT would be the first. This must be closed before CT goes live (CT3), as a follow-up.
- UNRESOLVED: routing. Will EDICOM send ASNs and kitting DESADVs to separate directories, and can one file mix the two?
- UNRESOLVED: references. Which CT ref is the PO number (`SRN`/`CR`/`DQ`), and does BGM → `customerRef`, DQ → `salesOrder` hold for kitting?
- UNRESOLVED: is a component QTY per kit or a total? If per kit, rules can't multiply across rows, and that is code.
- UNRESOLVED: repeated SKUs. WITH_SSCC has 10 pallets of one SKU. One receipt line each, or aggregated (code)?
- UNRESOLVED: file extension. CT's samples are `.txt`, and the connector routes `.edi` only.
- UNRESOLVED: BGM message function. What should a replace (5) or cancel (1) DESADV do? Dedupe holds a repeat, and Fuse has no amendment path.
- UNRESOLVED (config-only, CT onboarding): the meaning of QTY `21` vs `47E`; which item id is CT's Snap SKU (LIN `SK` vs PIA `SA`, which differ between the two samples); SSCC/batch pre-advice into Snap (a types + snap-adapter follow-up).

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
- [x] 1. Adopt edi `^0.8.0` and make the action directories accept sets of message types, with only `lines` fanning out, in `edi-to-json.ts` (AC 3, 4, 7). — routing 05f0476 + edi ^0.8.0 bump; misroute tests assert declared/detected (INSDES→WO declared DESADV; INSDES→PO 'ORDERS or DESADV'; DESADV→SO); no-UNH multi-type rejected; INSDES/PRICAT/ORDERS rows ⊇ 0.6.0 baseline; DESADV rows carry line.sscc, no packages.*; 775 green on published 0.8.0 — done: caf1a31
  - *Routing:* `create_purchase_order: ["ORDERS","DESADV"]`, `create_work_order: ["DESADV"]`. Detect the type; normalize with it as declared if it is in the set; otherwise throw `EdiMessageTypeMismatchError(accepted.join(" or "), detected)`. With no UNH: a single-type directory keeps today's behaviour (the declared type); a multi-type directory **rejects** the file rather than guessing.
  - *Test moves:* the "no EDIFACT message type" test moves from `create_work_order` to `create_return_goods_authorization`.
  - *Verify:*
    - Unit tests for each AC 4 misroute, asserting the mismatch error's `declared` and `detected`; before this change INSDES→WO failed with a different error.
    - Row goldens for existing INSDES/ORDERS/PRICAT fixtures, produced through the real `flattenObject` + `toRow`: equal apart from added keys, with equal row counts.
    - DESADV rows have no `packages.*` key.
- [x] 2. Translator specs proving config is enough (AC 1, 2, 5). This is the shape of HJF's dev mappings, and the fixture mappings live in `__fixtures__`. — PO spec (6): ASN → 1 valid PO, supplier id/ref, purchaseOrder from RFF+ON, 2 lines advised 10/5, same mapping reads ORDERS, no supplier.reference → invalid. WO kitting (5): 1 valid WO, roles finished_good/component/component from dictionary, produced 10 / consumed 10,20, customerRef = BGM, no role → invalid. Suite 775 green (run against local edi 0.8.0 build) — done: 9ffcb1f
  - *PO:* the ASN mapping (raw-key rules, required defaults, `groupBy`) gives a valid `CanonicalPurchaseOrder` from both CT ASNs: 3 lines and 10 lines.
  - *WO:* the kitting mapping with a `desadv_line_role` dictionary (`CMP → component`) and `lookup`/`if(eq…)` rules gives one FINISHED_GOOD line (`produced`) and n COMPONENT lines (`consumed`).
  - *Failure cases:* a mapping with no `customerRef` or `supplier.reference` gives an invalid record, which goes to the retry queue.
  - *Verify:* `test`, `lint`, `build:check` and `build:check:tests` pass.
- [x] 3. Dev end to end on HJF through the fuse-mocker simulator. This must be done before the PR leaves draft, and it delivers H3 (AC 1, 2, 4, 5, 6). — dev e2e on HJF/simulator (caf1a31): 2 ASN receipts, kitting S10, misroutes → error/ + create_data_failure, resend held (dedupeCount 1, 1 receipt), 16-char PO rejected 'Invalid Length', ORDERS + INSDES regressions OK; see Verification
  - *Setup:* write HJF's `purchase_order`/`work_order` mappings and dictionary (from inc 2), and seed the fixture SKUs in the mocker as **plain products**, not kits, because `explodeKits` would eat the finished-good line.
  - *Checks:*
    - Drop an ASN `.edi` → receipt in the simulator with refs and lines (10 lines for WITH_SSCC).
    - Drop a kitting `.edi` → S10 with FG + components and `CustomerRef`.
    - Resend the same BGM → held in `dedupe-list`, and no second Snap write.
    - INSDES into WO, and DESADV into the sales-order directory → `error/` + `create_data_failure`.
    - A mapping pushing the 16-character BGM into `purchaseOrder` → visible rejection in `replay-list-failures`.
    - Advance the S10 → the R10 is minted and the FGR RECADV carries `RFF+ON` = the ingested ref. This needs a throwaway dev deploy with `FEATURE_FLAG_EDI_EGRESS` on; revert it afterwards.
  - *Dev state:* use fresh BGMs per run, check the deployed `version` sha in the logs, and revert dev to master afterwards.
        gate: HJF dev connector config written (shared dev state, see Rollout)
              [x] confirmed (2026-09-30: purchase_order widened, work_order + dictionaries created, SKUs seeded; the flag deploy was not needed, see Decisions)

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-09-30 [prod] #292 was squash-merged as `3de918e`. Deploy run 36726577236 had a prod plan of 0/1/0: the image bump plus the standing container-dependencies/sidecar-env drift, agreed with Harry. Both `terraform-prod` gates were approved, and revision `sftp-connector-prod-cr-00102-4sb` is Ready on `prod-3de918e`. It booted at 14:30:54Z; prod files have flowed since (validated → acknowledged → routed), with no error-level logs.
- 2026-09-30 [inc 3, dev e2e] Setup: sftp-connector branch `caf1a31` on dev (Manual Deploy 36724391504; logs `version: caf1a31…`), with HJF (`FUSE_4366B07EED`) backed by the fuse-mocker snap simulator (`9ec3dd2`). The HJF `purchase_order` mapping was widened additively for DESADV, and a `work_order` mapping was created with the `desadv_line_role` (CMP → component) and `wo_type` dictionaries. SKUs were seeded as plain products. Files T=09301350:
  - **(AC 1) CT SSCC ASN, BGM `E2ES09301350`:** valid 1 → `create_acknowledge` → `archive/`. Simulator receipt `HJF008D4AB33ABA`: 10 lines of 65183860 × 180, Supplier PUIG, SupplierRef = PurchaseOrder = BGM.
  - **(AC 1) CT plain ASN, 16-character BGM `0000125909301350`:** receipt `HJF774F2093F327`, PurchaseOrder X380752 (RFF+CR), ASNumber 0029225554 (RFF+SRN), SupplierRef = BGM, 3 lines using the LIN SK material codes (65172716 × 260, 65177588 × 4500 / 9600).
  - **(AC 2) Kitting DESADV `E2EK09301350`:** S10 `HJF265DA74BD20F`, CustomerRef = BGM, SalesOrder = SUB09301350 (RFF+SRN). Lines: E2E-KIT-1259 ordered 2 with no required (finished good); E2E-CMP-1259A 4/4 and E2E-CMP-1259B 2/2 (components). Roles came from the dictionary only.
  - **(AC 4) Misroutes:**
    - INSDES in `create_work_order` → `EDIFACT message type mismatch: caller declared "DESADV" but the file's UNH is "INSDES"` → `error/` + `create_data_failure`.
    - DESADV in `create_sales_order` → declared "INSDES" / UNH "DESADV" → `error/` + `create_data_failure`.
  - **Dedupe:** resending the SSCC ASN under a new filename, same BGM → dedupe-list `reference E2ES09301350`, `dedupeCount 1`, "Identical purchase order … held as a duplicate". The simulator still has exactly 1 receipt with that SupplierRef.
  - **(AC 5) Long reference:** HJF simulator `strictValidation` was switched on, then back off. A plain ASN without RFF+CR, so the 16-character BGM maps to PurchaseOrder, gave replay failure `0000999909301350`: "PurchaseOrder - Invalid Length; OwnerId - MANDATORY; Warehouse - MANDATORY" → `error/`. Rejected, not truncated.
  - **(AC 3) Regressions:**
    - ORDERS `E2EO09301350` in the PO folder → receipt `HJFF7499511BC21` (SEEBURGER, 2 lines), unchanged.
    - INSDES `E2EL09301350` in the SO folder → shipment `HJFDD1285F1DF2C`, archived.
    - A first INSDES attempt failed on `dates.dueOut` because the test file lacked HJF's DTM+2. A second failed while strict validation was on ("Shipment not found … attachments"). Neither was a code regression.
- 2026-09-30 [inc 1-2] Local suite 775/775, tsc and biome clean on published edi 0.8.0. Misroute errors carry declared/detected. INSDES/PRICAT/ORDERS rows are a superset of the edi 0.6.0 baseline. The PO and WO translator specs pass through the real EDI path.


### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- (AC 6) FGR RECADV echo not observed directly for a DESADV-ingested WO; no FEATURE_FLAG_EDI_EGRESS dev deploy was done. It holds by composition:
  - this run proved the kitting BGM reaches S10 `CustomerRef`;
  - FUSE-1258's dev e2e (2026-09-30, same simulator) proved S10 `CustomerRef` → R10 `SupplierRef` → FGR `workOrder.customerRef` → `RFF+ON` on the RECADV.
  A direct check needs a throwaway flag deploy (Harry's call).
- A real CT kitting DESADV has not been run; the kitting file is built from the copacking deck.
- Strict simulator validation also flagged HJF's receipt mapping missing `OwnerId`/`Warehouse`. That's dev config, not code; left as is.


## Rollout & rollback
<!-- Added on demand. Written at plan time; amend in place as it changes.
     `Shared state touched:` is the single home for the five classes git does not own — a dev
     deploy, a prod config write, a Datadog monitor, a CI var or secret, cross-repo IaC. Reverting
     the branch undoes none of them, so if they are not written here they are not written down. -->
- **Order:**
  1. edi 0.7.0 is published.
  2. edi 0.8.0 is published.
  3. This PR is merged.

  sftp-connector's `^0.6.0` pin means no edi release reaches prod until this PR.
- **Flags/config:** no flag. Ingress file type is not a connector setting, so any SFTP user could already drop `.edi`. Before merging, check prod for EDI ingress:
  - Datadog `service:sftp_connector` `fileType:edi` over the full retention window
  - `.edi` objects in the prod bucket, including `error/`
  - prod mapping rules whose `from` uses intermediary paths

  Expected: none (R4).
- **One-way doors:** none. The change is additive; a DESADV without a mapping fails into `error/`.
- **Rollback:** `git revert` restores the 1:1 routing and the edi pin.
- **Shared state touched:**
  - dev deploy of the branch, reverted to master afterwards
  - HJF dev connector `purchase_order`/`work_order` mappings, dictionaries and mocker seed data (left in place as the H3 harness)
  - one throwaway dev deploy with `FEATURE_FLAG_EDI_EGRESS=true`, reverted
- **Proof in prod:** none until a customer sends DESADV. The CT onboarding programme (CT2/CT3) owns that.

## Handback
<!-- Append-only, newest first. Written by `wp handback`, never by hand.
     Sign-off never clears this section — a refuted approach is exactly what a
     later session needs and what ## Learnings would have deleted. -->

### 2026-09-30 14:23
- **stopped:** sftp increments 1-2 committed locally (05f0476, 9ffcb1f), not pushed: they need @gfs-bifrost/edi ^0.8.0, which publishes only when pkg-node #256 then #257 merge. Local runs used the 0.8.0 build copied into this worktree's node_modules (not committed). After publish: bump code/package.json to ^0.8.0 + lockfile with pnpm 11, re-run suite, tick inc 1, push, open draft PR, then inc 3 (dev e2e on HJF) once Harry OKs the throwaway FEATURE_FLAG_EDI_EGRESS dev deploy.
- **turn:** me

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-09-30** — The FGR RECADV echo (AC 6) is proven by composition rather than a throwaway FEATURE_FLAG_EDI_EGRESS dev deploy. This run showed the kitting BGM → S10 CustomerRef; FUSE-1258's same-day simulator run already showed S10 CustomerRef → R10 SupplierRef → FGR workOrder.customerRef → RFF+ON. That avoids flipping the dev flag Harry wants off. A direct check stays available if he wants one.

- **2026-09-30** — PO folder keeps ORDERS alongside DESADV (Harry agreed 2026-09-30): the UNH picks the normalizer, and the mapping does the rest. A file with no UNH in a multi-type folder is rejected, not read as accepted[0].
- 2026-09-30 — **Detect-then-declare in the connector** rather than `normalize({messageType: string[]})`. It avoids widening edi's public API, and a double parse of one message per file is cheap.
- 2026-09-30 — **Only `lines` fans out.** DSLRunner re-sets every variable on every rule, so flattening `packages[]` onto every row costs rules × variables × rows on a large ASN. Package data reaches rules through the per-line `package.*`/`sscc` slots.
- 2026-09-30 — **Test scaffolding is not separate increments.** The draft's separate "translator proof" and "dev e2e" items were folded into 2 and 3, each with its own verification, and the snap-adapter and fuse-mocker "plans" were dropped as reference-only (structure review).

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
(promoted to known-context.md 2026-09-30)
