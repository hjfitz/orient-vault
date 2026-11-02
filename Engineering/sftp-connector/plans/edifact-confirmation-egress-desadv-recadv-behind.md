---
ticket: FUSE-1253
title: EDIFACT confirmation egress (RECADV, DESADV, OSTRPT, INVRPT) behind FEATURE_FLAG_EDI_EGRESS
service: sftp-connector
status: complete
created: '2026-09-24'
updated: '2026-10-19'
repo: /home/hjf/code/fuse/sftp-connector
worktree: /home/hjf/code/fuse/sftp-connector/.claude/worktrees/edi-egress
branch: hjf/fuse-1253-edi-assembly
base: origin/master
base_sha: 0057bed36
pr: '287'
tags:
- waypoint
- plan
impl_model: opus
impl_effort: high
programme: edi-support
unit: E8
---
# FUSE-1253 — EDIFACT confirmation egress (RECADV, DESADV, OSTRPT, INVRPT) behind FEATURE_FLAG_EDI_EGRESS

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
[FUSE-1253](https://globalfreight.atlassian.net/browse/FUSE-1253). This adds `edi` as a third SFTP egress file type, with the interchange parties in a new `ediEnvelope` block ([[edi-0-5-0-interchange-envelope-types-ediegress-o]], [[persist-and-validate-ediegress-on-sftp-connector]], UI in [[edifact-egress-option-on-the-sftp-connector-form]]).

An `edi` connector gets an EDIFACT message for **every confirmation type except returns**. The messages are generic EANCOM D.96A; Charlotte Tilbury is config, not code (see the invariant under Assumptions). Each is one EDIFACT interchange (UNB…UNZ) per confirmation, written create-only into the connector's existing folder for that type, behind `FEATURE_FLAG_EDI_EGRESS`:

| Confirmation | Message | BGM (CT's config value) |
|---|---|---|
| goods-in | RECADV | 352 |
| goods-out | DESADV loading | 701 |
| pack | DESADV pack message | 351 |
| pick | OSTRPT | 93E |
| stock adjustment | INVRPT | 78 |
| finished goods receipt (Snap `R10` receipt) | RECADV (production) | 352 |
| work order confirmation (Snap `S10` shipment): **component lines only** | INVRPT (staging) | 78 |

Returns write nothing and report why: the evidence conflicts between a RECADV and an INVRPT return adjustment (FUSE-1213 epic note, FUSE-1255). Every `csv`/`jsonl` connector keeps byte-identical output. This plan is **done in dev only**; prod enablement is FUSE-1256.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. `csv`/`jsonl` confirmation and stock-adjustment output is byte-identical to master, whether the flag is on or off.
- [x] 2. With the flag on in dev, each of the seven covered confirmation types for the `edi` test connector writes one `<MSG>_<docRef>_<ctrlRef>.edi` into that type's folder. Each file holds UNB…UNH…UNT…UNZ with correct counts and matching control refs, parses with `parseEdifact`, and matches the structure of its Charlotte Tilbury sample.
- [x] 3. DESADV pack and DESADV loading carry their package hierarchy (SSCC per package, and for pack, lines under their carton with batch), built from the canonical's package/consignment data.
- [x] 4. Redelivering the same confirmation while its file is still uncollected writes no second file and logs `EdiFileAlreadyExists`.
- [x] 5. An `edi` connector **always ingests normally**, including when its envelope is missing or malformed, the flag is off, or dynamic mapping is off. The same applies to the prod image deployed before any connector is set to `edi`.
- [x] 6. For an `edi` connector, each of these writes nothing and emits an unroutable reason plus a metric (no silent drops):
  - RGA (returns) confirmations;
  - the flag off;
  - dynamic mapping off;
  - a missing or malformed envelope.
> SUPERSEDED 2026-10-19 — narrowed to a missing SSCC when `requireSscc` is set (Harry). A mandatory batch moves to EDI Support unit E16.
- [x] 7. When a confirmation's mapping can't produce a valid message (including a missing mandatory SSCC or batch), no file is written. It emits `EdiMessageInvalid` and `confirmation_data_failure` instead, and the forward metric carries a `fileType` tag.
- [x] 8. A work order confirmation's INVRPT carries **component lines only**. Finished-good lines are never sent there, because the finished goods receipt's RECADV books them, and sending both would double-book the stock in the receiver's ERP.
- [x] 9. No customer- or partner-specific value is hardcoded anywhere in the path. Every code comes from the connector's config, with EANCOM defaults.
> SUPERSEDED 2026-10-05 — sftp-connector is on `@gfs-bifrost/types` `^10.9.0` on master. FUSE-1254 did the 10.x adoption separately (master was already on `^10.7.0`), and increment 5 only took the `^10.8.0` minor (see the 2026-09-29 Decisions entry). So this plan did not take the major, which was the point of this criterion.
- [x] 10. sftp-connector stays on `@gfs-bifrost/types` `^9.5.0`. Adopting types 10.x is FUSE-1254.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `code/src/config/schema.ts:32-37` `GetConnectorDtoSchema`. Here, locally:
  - widen `egressFiletype` to accept `edi`;
  - add a lenient `ediEnvelope`;
  - add a TODO to delete both once FUSE-1254 lands (the FUSE-954 `columnOrder` precedent).
- `code/src/config/config.api.ts`:
  - `getBusinessConnectors` (`:549`) silently drops a connector that fails `safeParse`.
  - `getConnector` (`:650`) and `getConnectorByUsername` (`:686-699`) throw on the same failure.
  - Today that means an `edi` value would break **ingest** for that username. That's why AC 4 exists and why increment 1 ships to prod first.
- `confirmation-egress.service.ts`:
  - `ConfirmationTarget` (`:52-57`) has no connector id.
  - `evaluateConnector` and `selectLegacyTargets` build targets.
  - `fileTypeForEgress` is called at `:372` (dynamic) and `:398` (legacy).
  - `writeConfirmation` (`:432`); the `WriteFailed` catch that publishes `confirmation_data_failure` (`:158-176`); `toMappableRecords` parcel split (`:506-515`).
- `confirmations/stock-adjustment.service.ts` is a separate egress path. It batches records per file and uses a **fixed** transformer (`stock-adjustment.transformer.ts`) rather than mapping rules. INVRPT gets a mapping-rules branch here.
- The pick and pack confirmations route through `confirmations.service.ts:138-144` into the same egress service as goods-out.
- `core/confirmation-transformer.ts` `transformConfirmations` (`:48-60`). Its rows are flat `{...header, ...line}` padded with `""`, and nothing records which rule a column came from.
- New pure core module `confirmations/edi/`.
- `gcs/types.ts:36-62` `ICloudStorageService` and `gcs/storage.service.ts` get a new `createFile`. Test doubles to update:
  - `__fixtures__/storage.service.fixture.ts`
  - `core/file-routing/__fixtures__/file-routing.fixture.ts`
  - inline mocks in the confirmation-egress and stock-adjustment specs
- `operations.ts:56` `FileType`.
- Flag: `app-config/schemas.ts:74-78`, `config.ts:152-155`, and iac `variables.tf:53`, `cloud-run.tf:221`, `env/dev.tfvars`, `env/prod.tfvars`.
- `@gfs-bifrost/edi` goes from `^0.4.1` to `^0.5.0`.
- Guardrails: [[known-context]] G2 (the shared egress window) is bypassed for `edi`. G3 (formats are contractual) is covered under Assumptions.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **Only four codebases read `egressFiletype`: types, config-service, fuse-ui and sftp-connector.**
  - fapi, shopify-connector and the SNAP poller resolve connectors filtered to their own type (`resolve(businessId, REST/SHOPIFY)`), so they never load an SFTP connector.
  - When remote-config fails to fetch or validate one connector in a list, it drops that connector, not the business.
  - So an `edi` value only threatens sftp-connector.
  - Established by a grep across every repo's default branch and a source read of `connector.handler.ts:320-350` (2026-09-24).
- **INVARIANT (Harry, 2026-09-24): customer-agnostic.** Charlotte Tilbury is config (envelope, mapping rules, dictionaries), never code. The durable record is [[2026-09-24-edi-egress-is-customer-agnostic-partners-are-config-never-co]].
- **Work orders map onto Snap's own resources.** The copacking deck's flow (inbound kitting DESADV → INVRPT staging → RECADV production, with SAP consuming components itself) lines up with Snap's resources:
  - the S10 work-order shipment: component pick/fulfil → WOC component lines (`consumed` = `QtyPicked`);
  - the R10 receipt that Snap generates on completion → FGR (`produced` = `QtyReceived`).

  The poller links an R10 to its work order via `SupplierRef` = the work order's ShipmentId/customerRef (`work-order.discriminator.ts`). Established by source read of snap-adapter `origin/master` on 2026-09-24.
- **Type → message mapping.** Goods-in, stock adjustment and the DESADV message family are firm: each has a Charlotte Tilbury sample and a Puig guide. Two parts are inferred and should be confirmed with Charlotte Tilbury, but they don't block the build:
  - pack → DESADV 351 and goods-out → DESADV 701, taken from the sample names and Snap's stage order;
  - pick → OSTRPT, whose `STS` codes are "Not CT-confirmed".
- **Codes Charlotte Tilbury hasn't confirmed come from mapping config, not code.** This covers OSTRPT `STS`, INVRPT `INV` direction and `STS` reason, typically via `lookup()` dictionaries (FUSE-1216/1220). A correction is a config edit.
- **Package hierarchy comes from the data, not the mapping.** Line rows carry a package key column (the SSCC) plus package fields. Assembly groups lines under their `CPS` package. The canonicals carry what's needed:
  - pack: `packages[].sscc`/`packagingCode`/`weight`, plus `lines[].sscc` and `location.batchId`;
  - goods-out: consignment `stockTrackingUnit` and line `batchId`;
  - goods-in and pick: `batchId`.
- **Mapping is config-authored through the connector's existing confirmation CONNECTOR_MAPPING.** Rule column names match `DesadvOut`/`RecadvOut` fields.
  - The EDI code splits header from line using the `from` names in `rules.header` and `rules.lines`.
  - A name used by both is `EdiMessageInvalid`, and so is a simple configType.
  - Established by source read of `confirmation-transformer.ts:58-59,109,305-331`.
- **The parcel split stays.** Line rows from every parcel are regrouped into one message per confirmation. Skipping the split mis-pairs `consignments[]`/`despatches[]` by index (`goods-out-parcels.ts:22-28`).
- **Control ref and idempotency.** ctrlRef = first 14 chars of `sha256(targetConnectorId|recordType|docRef|queueId)`, where docRef is `identifiers.shipmentId` or `receiptId`.
  - The **target** connector id is added to `ConfirmationTarget`, because `metadata.connectorId` is optional and names the origin connector.
  - `queueId` can be `""`, so connector + docRef carry the uniqueness.
- **Create-only only guards uncollected files.** `ifGenerationMatch:0` checks the live object only. Versioning is on (`storage.tf:8`), and customers fetch then delete, so a resend after collection rewrites the same file with the same control ref. The receiver's duplicate-interchange check is the backstop. From PR #226 and the history review.
- **One-file-per-batch was rejected for CSV in PR #226** to keep the window contract. `edi` is a new contract, so this doesn't reopen that decision.
- **Recovery is SNAP poll redelivery, not replay-service.** Replay redrive stamps only `recordType`, which matches no sftp PO/SO delivery subscription (FUSE-1059).
- **A deterministic `EdiMessageInvalid` re-fails on every poll.** Match the existing CSV transform-failure ack/publish behaviour (read it at implementation); the metric makes the loop visible.
- **An `edi` connector never falls back to CSV.** Its mapping is written for EDIFACT, so CSV from it would be junk (G3). That's why every non-EDI path writes nothing and says why. Only a connector with no live CSV confirmation consumer is switched to `edi`.
- **Dynamic confirmation mapping is on in dev and prod** (`dev.tfvars:23`, `prod.tfvars:26`).
- **Decode may silently drop zod-invalid confirmations** (memory note, 07-07). Not verified; increment 4 checks it.
- **Stock adjustments have no batch.** Puig's INVRPT is reported per batch (`PIA NB`), but `CanonicalStockAdjustment` has no batch field, only `from`/`to` `stockTrackingUnit`/`stockId`. It isn't clear whether Snap exposes the batch on the movement. The INVRPT increment is gated on this.
- **The FGR and WOC need poller data that isn't there yet.** FGR lines carry no batch; goods-in gets batch from a stock-consignment lookup in the same receipt code base. WOC component lines carry no batch, though Snap shipment lines have one. And FGR `identifiers.workOrderId` is a TODO ("no real FGR seen yet").
  - The RECADV also needs the originating document number and the work order's PO reference. For CT those are the inbound DESADV number (BGM) and the subcontracting PO (`RFF+DQ`), both caller-supplied codes.
  - Those references have to enter at work-order ingest and come back out on the R10.
  - These are FUSE-1258, which gates increment 6. Inbound kitting DESADV ingest, where the references originate, is FUSE-1259.
- **Returns are out of scope** until one message is confirmed. The evidence is split: RECADV echoing the RMA (Puig detailed-info deck, 3 Sep minutes, US-3PL workbook) against an INVRPT return adjustment (Puig INVRPT guide). Tracked in FUSE-1255.
- UNRESOLVED (batch source for INVRPT, tracked as FUSE-1088): is the batch available from Snap for stock movements? If it is, adding it needs a types change and a poller change outside this plan.
- UNRESOLVED (customer; doesn't block the dev path): one DESADV per shipment and what a re-confirmation means; non-sequential control refs; filename, extension and folder; FGR sharing `purchase_order_confirmations` with RECADV.

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
- [x] 1. Groundwork that is safe in prod: — 598/598 tests, lint + tsc clean; dev regression deploy pending — done: 91cfc5c
  - locally, `egressFiletype` accepts `edi` and `ediEnvelope` is lenient (`.optional().catch(undefined)`), with a TODO pointing at FUSE-1254;
  - every `edi` connector writes nothing and emits an unroutable reason plus a metric, on the confirmation-egress paths (dynamic and legacy) and in stock adjustments;
  - add `createFile(path, contents): "created" | "exists"` (`ifGenerationMatch: 0`, where a 412 returns `"exists"`) to the interface, the service and all four test doubles.

  (AC 1,5,6,8) — verify: unit tests where an `edi` connector (with a valid, missing or malformed envelope) resolves through `getConnector`, `getConnectorByUsername` and `getBusinessConnectors`; a test that `edi` egress writes nothing and emits the reason; a `createFile` 412 test; csv/jsonl golden outputs unchanged; a dev deploy with ingest and CSV confirmations unchanged for the HJF CSV connector. **Merge and deploy to prod** before config-service accepts `edi`.
- [x] 2. EDI assembly core in `confirmations/edi/`: — 39 tests / 7 goldens (2 CT-shaped from config fixtures only); 637/637, lint + tsc clean; PR #278 — done: 0e1efac
  - transformer rows (after the parcel split) → header, packages grouped by the SSCC column, and lines, split on the header/line rule `from` names;
  - local zod validation;
  - docRef, ctrlRef and filename;
  - `ediEnvelope` → `EdiEnvelopeProfile`;
  - a per-type dispatch table (recordType → serializer).

  Serializers are called once they're published. Nothing is wired yet. (AC 2,3,7) — verify: goods-in (RECADV) and goods-out/pack (DESADV 701/351) golden `.edi` fixtures built from canonical fixtures that re-parse with `parseEdifact`, including a multi-carton pack whose lines regroup under the right SSCC; a stable ctrlRef per target connector; a shared header/line column or a missing SSCC gives `EdiMessageInvalid`.
      gate: edi interchange + RECADV + both DESADV serializers published (pkg-node increments 1-4)
            [x] confirmed
- [x] 3. Wire the confirmation-egress path behind `FEATURE_FLAG_EDI_EGRESS` for goods-in, goods-out and pack: — dev flag-on branch image 4e26724: RECADV/DESADV/DESADV pack written + parse; redelivery exists; RGA skipped; invalid → failure; PR #280 — done: 3bbf803
  - flag plumbing and iac, false in both envs;
  - `FileType.EDI`;
  - the target connector id and envelope on `ConfirmationTarget`;
  - an EDI branch in `writeConfirmation` that calls `createFile`;
  - `EdiFileWritten`, `EdiFileAlreadyExists` and `EdiMessageInvalid` events.

  (AC 1,2,3,4) — verify: csv/jsonl golden outputs byte-identical; a flag-off dev deploy whose dev plan shows only the new env var; a branch deploy with the dev flag on, then `mock-send` a receipt, a dispatch and a pack confirmation with `options.connectorId` = the `edi` test connector and confirm `.edi` files appear and parse; re-send the same message and confirm `EdiFileAlreadyExists` and no second file; an RGA writes nothing and reports why; a CSV connector in the same business is unchanged.
      gate: config-service increment 1 is in dev, and the HJF dev test connector is set to `edi` with an envelope and hand-written rules for all five types (a new connector, never a live customer's)
            [x] confirmed — config-service#226 in dev+prod; HJF test connector edi + envelope; rules written for goods-in/goods-out/pack (the three this increment verifies); pick + stock-adjustment rules come with incs 4/5
- [x] 4. Add pick → OSTRPT to the dispatch table and wiring. (AC 2) — verify: golden `.edi` from a pick fixture; in dev, `mock-send` a pick confirmation and get a parsing OSTRPT with `STS` from the mapping. — dev flag-on 52f4a57: OSTRPT_HJFPCK1253P1_0c443d4dbb3ca5.edi parses, STS++21E, UNT+15; PR #281 — done: a7fcb13
      gate: OSTRPT serializer published (pkg-node increment 5)
            [x] confirmed
- [x] 5. Add stock adjustment → INVRPT: an EDI branch in `stock-adjustment.service.ts` that applies the connector's stock-adjustment mapping rules, with one INVRPT per movement (`identifiers.id`) and `INV`/`STS` from the mapping. (AC 2,6,7) — verify: golden `.edi` from stock-adjustment fixtures; in dev, `mock-send` a stock adjustment and get a parsing INVRPT; the csv/jsonl stock-adjustment files are unchanged. — dev flag-on 56e590a: INVRPT_SHOL901253/SADJ901253 parse, GIN+BX+DTM+36 on batch line, redelivery exists, GADG csv/jsonl byte-identical; branch hjf/fuse-1253-edi-stock-adjustments — done: f6a15e3
      gate: INVRPT serializer published (pkg-node increment 6) AND FUSE-1088 decided/built (stock-adjustment batch)
            [x] confirmed — edi 0.6.0 (InvrptSerializer) published; FUSE-1088 data contract built: types 10.8.0 (pkg-node#254, merged 2026-09-29) carries movementRef + from/to batchId/expiry. The poller side (snap-adapter branch hjf/fuse-1088-stock-adjustment-refs, no PR yet) is still in dev verification, so real Snap movements don't carry the fields yet.
- [x] 6. Add the work-order family to the dispatch table: — dev flag-on f54af3c via the real poller + snap-api simulator: RECADV (FGR folder, RFF+ON WO ref, FG batch) + WOC INVRPT (components only, GIN+BX) parse; redelivery exists — done: f6a15e3
  - `finished_good_receipt` → RECADV (production references come from the mapping: originating document number, work-order PO);
  - `work_order_confirmation` → INVRPT, built from **component lines only**, with finished-good lines dropped before assembly.

  (AC 2,8) — verify: a golden `.edi` from FGR and WOC fixtures, where a WOC fixture carrying both roles emits only component `LIN`s; in dev, `mock-send` a `finished_good_receipt` and a `work_order_confirmation` to the `edi` connector and get a parsing RECADV and INVRPT; the FGR RECADV lands in the connector's configured FGR directory.
      gate: FUSE-1258 (FGR/WOC line batch + work-order references) in dev AND the RECADV/INVRPT serializers published
            [x] confirmed — FUSE-1258 shipped in prod poller 3c83850 (2026-09-29)
- [x] 7. Add observability and the failure path: tag `CONFIRMATION_METRIC.FORWARD` with `fileType`; send `EdiMessageInvalid` into `confirmation_data_failure` through the existing `WriteFailed` path; check the decode drop. (AC 6,7,9) — verify: a grep/test that no customer or partner identifier appears in `confirmations/edi/`; in dev, a deliberately broken test-connector mapping writes no file, `confirmation_data_failure` shows up in `replay-list-failures`, and the metric shows `filetype:edi` in Datadog; record what the decode-drop check found. — fileType tag on fuse.confirmation.forward (edi/csv/jsonl seen in dev); failure path shipped in #280; decode drop = warn log + empty made, filed as follow-up; PR #281 — done: a7fcb13
> DEFERRED 2026-09-24 — Harry: dev flag stays off until CT's mappings are known; flag-on checks use throwaway branch deploys.
- [x] 8. Switch the dev flag on permanently in a separate PR (`dev.tfvars` true, prod stays false). (AC 2) — verify: the dev plan shows that one change, and a `mock-send` dispatch after the master deploy still writes `.edi`. — dev.tfvars feature_flag_edi=true on origin/master, prod.tfvars false; live dev rev 00840 FEATURE_FLAG_EDI=true, prod rev 00107 false; post-flip mock-send goods-in wrote RECADV .edi — done: 933d71f
      gate: increments 1-7 merged
            [x] confirmed — 2026-10-05: the done shas of increments 1-7 (91cfc5c, 0e1efac, 3bbf803, a7fcb13, f6a15e3) are all on origin/master; #278, #280, #281, #287 merged

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-14 [FUSE-1256, prod flags on] Prod enablement of the two flags, sftp first and fuse-ui second, one Terraform apply each:
  - sftp-connector#310 (`4e1593e`): `prod.tfvars` `feature_flag_edi` false → true. Prod plan (Deploy run 38534591654) was `0 to add, 1 to change, 0 to destroy` on `sftp-connector-prod-cr` only: image `prod-28c514e` → `prod-4e1593e`, the `container-dependencies` annotation, a redacted sidecar env block (both standing drift) and a redacted main-container env block (the flag). That run also shipped #308 (`@gfs-bifrost/edi` ^0.8.1). Both `terraform-prod` gates approved on that run only; the older parked run 38370398909 (`a8d34bf`) was left alone. Live: `sftp-connector-prod-cr-00109-qvm` Ready, image `prod-4e1593e`, `FEATURE_FLAG_EDI=true`, `FEATURE_FLAG_USE_DYNAMIC_CONFIRMATION_MAPPING=true`. Cloud Run logs for that revision over its first 30 min: 13 entries, none at WARNING or above. Low traffic, so weak evidence; the Datadog `service:sftp_connector env:prod` query returned nothing even over 3 h, so no Datadog check was made.
  - fuse-ui#312 (`d610a91`), merged only after the sftp revision above was live: `prod.tfvars` `feature_flag_edi_egress = true`. Prod plan (run 38535302284) `0/1/0` on `fuse-ui-app-prod`: image, `FEATURE_FLAG_EDI_EGRESS` env, plus standing sidecar and `scaling` min-instance drift (identical `scaling` block in the previous prod plan, run 38370761002). It also shipped Renovate #311. Live: `fuse-ui-app-prod-00067-8pn` Ready, image `prod-d610a91`, `FEATURE_FLAG_EDI_EGRESS=true`; no WARNING+ in 20 min.
  - Before the flips: fapi and shopify-connector source both pin `@gfs-bifrost/types` ^10.13.0 / 10.13.0, past the 10.4.0 floor for an `edi` connector's revision event. Not checked: whether any prod connector is already set to `egressFiletype: "edi"` (`list-customers` doesn't expose it and `config-read` returns credentials). Both flags were off and the CT business doesn't appear in prod `list-customers`, so none is expected, but that is an inference. Charlotte Tilbury's prod connector, its envelope and mapping, and the first real confirmation of each type are still open on FUSE-1256. Not proven in prod: any `EdiFileWritten` or `filetype:edi` forward.
- 2026-10-09 [sign-off] Inc 8 and AC 7 checked live against `origin/master` `0bf3526` (includes `933d71f`):
  - Inc 8: `iac/env/dev.tfvars` has `feature_flag_edi = true` and `prod.tfvars` `false` on master. `933d71f` changes that one line. Cloud Run `sftp-connector-dev-cr-00840-sfx` (image `dev-0bf3526`) has `FEATURE_FLAG_EDI=true`; `sftp-connector-prod-cr-00107-2zg` (image `prod-648ee6e`) has `false`. A `mock-send` goods-in to the HJF `edi` connector (`broadcast: true`, `connectorId` set) wrote `purchase_order_confirmations/RECADV_MOCK-PO-JXG5XAU_385bf7fae1c10f.edi` at 10:20:10Z (UNH/UNT/UNZ refs match, UNT+10). The commit went straight to master with no PR number, so "separate PR" was not literally followed.
  - AC 7, invalid path: a goods-out with no consignments sent the same way wrote no file and put `Invalid EDIFACT message: conn_1435...: packages.0.lines.0.quantity: Invalid input: expected object, received undefined` into replay-service as a `goods_out_confirmation` failure with that connectorId (id `f8056f42`). The failure is per connector (`write_failed`); the same send's REST webhook connector failed separately.
  - AC 7, forward tag: `confirmation-egress.service.spec.ts` pins `fileType: "edi"` on the `FORWARD` metric (delivered and zod_dropped). `FORWARD_FAILURE` carries only `type`.
- 2026-10-05 [sign-off] Read-only checks against `origin/master` `648ee6e`, config-service dev and Datadog:
  - AC 5: config-service dev `GET /api/v1/connectors/conn_1435ca939ecb4c65b728fb0888aae7eb` shows the "hjf test" connector (`FUSE_4366B07EED`) with `egressFiletype: "edi"` and an `ediEnvelope`. Datadog `service:sftp_connector env:dev` on 2026-09-30 13:52–13:56Z (version `caf1a31`) shows it ingesting normally: `Emitting records` on that connectorId for `insdes`, `orders`, `kit` and `asn` files; `File routed` → `archive/`; misrouted test files → `error/` with `File-level ingest failure published`. Missing or malformed envelopes are pinned by `connector.config-handler.spec.ts`: "resolves the connector so its inbound files still ingest" and "treats a malformed envelope as absent rather than failing the connector". The prod-first ordering is shown by the inc 3 gate (config-service#226 came after inc 1 was in prod).
  - AC 6: `confirmation-egress.service.spec.ts` pins `edi_unsupported_type` (returns), `edi_egress_not_enabled`, `edi_requires_dynamic_mapping` and `edi_envelope_missing`, each incrementing the unroutable metric. `stock-adjustment.service.spec.ts` pins the same gates for stock adjustments. Returns writing nothing was also shown in dev (2026-09-24 inc 3).
  - AC 3: the goldens `desadv-goods-out.edi` (`CPS`/`PAC`/`PCI+33E`/`GIN+BJ` per pallet, lines under each with `GIN+BX`) and `desadv-pack.edi` (lines under each carton SSCC with batch) are built from `canonical.fixture.ts`. The spec pins "regroups lines under their carton's SSCC" and "regroups parcels sharing a pallet into one package".
  - AC 9: `git grep -i -E 'tilbury|puig|charlotte|GADG|HJF|DAZZA'` over `code/src/confirmations/edi` (excluding fixtures and tests) found nothing. The same grep over all of `code/src` (excluding fixtures and tests) found no Tilbury/Puig/Charlotte.
  - AC 2, CT structure: dev files were built from the HJF hand-written mappings. Structural match to CT's samples rests on the CT-shaped goldens here (`recadv-goods-in-ct.edi`, `desadv-pack-ct.edi`) and on `@gfs-bifrost/edi`'s CT config fixtures for all four serializers. Full CT conformance is separate work.
  > SUPERSEDED 2026-10-09 — inc 8 landed in `933d71f`.
  - inc 8 is not done: `iac/env/dev.tfvars` has `feature_flag_edi = false`.
- 2026-09-30 [inc 6 + inc 5 real-poller] Throwaway `hjf/fuse-1253-edi-e2e-devflag` (`f54af3c` = master `f6a15e3` + dev flag). Dev plan: image only, 0/1/0. Revision `sftp-connector-dev-cr-00811-bjb`, `FEATURE_FLAG_EDI_EGRESS=true`. Confirmations came from the **real** dev poller `9c33dd3` against the fuse-mocker snap-api simulator (HJF), not `mock-send`. All files parse with `@gfs-bifrost/edi` 0.6.0; UNT counts match; UNB/UNH/UNT/UNZ control refs match.
  - Stock adjustment, 2-line SHOL: `stock_adjustment_confirmations/INVRPT_HJF5025C2F94BAA_67668b88a6068c.edi`. BGM `1_SHOL_HJF5025C2F94BAA_HJF49E6C567C116` (the first line's movementRef, one message per move). LIN 1 `GIN+BX+HJFB-0930C` `DTM+36:20270331:102`; LIN 2 `GIN+BX+HJFB-0930D` `DTM+36:20270430:102`. UNT+16.
  - FGR: `finished_good_receipt_confirmations/RECADV_HJFCBAF4987A6D1_ecc743ba290df2.edi`. `RFF+ON:MOCK-WO-REF-0930C`, a single LIN for the finished good with `PIA+1+FG-0930-C1:NB`, `QTY+194:1`. UNT+10.
  - WOC: `work_order_confirmation_confirmations/INVRPT_HJFCBAF4987A6D1_05a103461b4c3d.edi`. `RFF+ON:MOCK-WO-REF-0930C`, LIN 1/2 are the two components with `GIN+BX+CMP-A-0930C` / `CMP-B-0930C`, and there is **no finished-good LIN** (AC 8). UNT+15.
  - `EdiFileWritten` at 07:54:07 (INVRPT SA), 08:16:08 (RECADV) and 08:18:08 (INVRPT WOC).
  - Redelivery: the same FGR re-published to `confirmation_ready` (same id + queueId) gave `EdiFileAlreadyExists` at 08:18:57 and still one object generation.
  - Incidentally AC 7: three FGRs whose simulator receipts had no DateReceipt gave `EdiMessageInvalid` `documentDate: Invalid input` and published a failure, with no file written.
  - Caveat: mock-originated orders carry routing `source: "mock"`/`"mock-sftp"`, which the sftp `source = "sftp" OR broadcast` filter drops. HJF backend `broadcastConfirmations` was set true for the WO run and reverted after.
  - Dev reverted to master after.
- 2026-09-29 [inc 5 prod] sftp-connector#287 squash `f6a15e3` (+ Renovate #286), prod plan image-only + standing sidecar drift; both gates approved; revision `sftp-connector-prod-cr-00100-6v6` Ready, `FEATURE_FLAG_EDI_EGRESS=false`. First ~25 min: 3 ingest validations, 3 confirmations written + processed, stock-adjustment event handled as before, no warn/error, no EDI events.
- 2026-09-29 [inc 5] Branch `hjf/fuse-1253-edi-stock-adjustments` `f0c3c64` (unmerged, no PR): 738/738, lint + tsc clean; goldens `invrpt-stock-adjustment-batch.edi` (GIN+BX + DTM+36 on the line) and `stock-adjustment.csv/.jsonl`.
- 2026-09-29 [inc 5] Dev flag-on image `56e590a` (revision `sftp-connector-dev-cr-00804-jt8`, FEATURE_FLAG_EDI_EGRESS=true; dev plan = image + standing sidecar drift + redacted env). HJF test connector, new dev-only stock_adjustment mapping; a 10.8.0-valid batch published to `stock_adjustment_ready` (SHOL with from/to batch LOT24117 + expiry, SADJ decrease with no batch):
  - `FUSE_4366B07EED/from_ilg/stock_adjustment_confirmations/INVRPT_SHOL901253_e838a3f9598dd6.edi`: BGM `0002_SHOL_SHOL901253_HJF1253L01`, `GIN+BX+LOT24117`, `DTM+36:20270630:102`, UNT+10. `INVRPT_SADJ901253_525a9c0fe5f1a4.edi`: no GIN/DTM 36, UNT+8. Both parse, and UNB/UNH/UNT/UNZ refs match.
  - Re-publish → `EdiFileAlreadyExists` ×2, one generation each. `stock_adjustment_made` emitted both times (collector).
  - The GADG batch that produced the master-written `2026-09-28-15` windows was replayed direct to sftp's push endpoint (fresh timestamp): `FUSE_D89734E435` csv, `FUSE_4E7E60F55B` and `FUSE_051D67897E` jsonl `2026-09-29-09` byte-identical.
  - No warn/error from this traffic. Dev reverted to master `5da035a` (`00805-x2d`, flag false).
- 2026-09-24 [inc 4+7 prod] sftp-connector#281 squash `a7fcb13`; prod plan image-only + standing sidecar drift; both gates approved; revision `sftp-connector-prod-cr-00096-mwd` Ready; 15:50–15:55Z: confirmation written, inbound file routed, stock-adjustment event handled, no warn/error.
- 2026-09-24 [inc 4+7] Dev branch image `52f4a57`, flag on: pick → `pick_confirmation_confirmations/OSTRPT_HJFPCK1253P1_0c443d4dbb3ca5.edi` (parses, UNT+15, STS++21E, ctrlRef matches); `fuse.confirmation.forward` by filetype: edi delivered (pick), csv + jsonl delivered (GADG goods-in), edi skipped (all-dropped pick). Decode-drop check: all-invalid batch → warn `ValidationFailed`, empty `confirmation_made`, counted delivered, no failure — pre-existing gap, follow-up. Dev reverted to master 3bbf803. 673/673.
- 2026-09-24 [inc 3 prod] sftp-connector#280 squash `3bbf803`; prod plan agreed with Harry (image + new `FEATURE_FLAG_EDI_EGRESS` env block + standing sidecar drift); both gates approved; revision `sftp-connector-prod-cr-00095-jtf` Ready with `FEATURE_FLAG_EDI_EGRESS=false`; first 5 min on it (15:19–15:24Z): 3 confirmation files written, 1 inbound file routed, stock-adjustment event handled, no warn/error, no EDI events.
- 2026-09-24 [inc 3] Dev branch image `4e26724`, flag on, HJF test connector: `RECADV_GADG17354E96C8F_5cb7e197427f7f.edi` (UNT+9), `DESADV_HJFSHP1253W1_a20c25e601fb59.edi` (UNT+25), `DESADV_HJFPCK1253W1_6d70b90e1ed249.edi` (UNT+23, lines under carton SSCC + batch) — all parse, control refs match; re-publish → EdiFileAlreadyExists, one generation; RGA → no file; invalid goods-in → EdiMessageInvalid → WriteFailed → replay failure 949fb193. Dev reverted to master 81b3f6c. 664/664 local.
- 2026-09-24 [inc 2] sftp-connector#278 squash-merged as `0e1efac` (unwired; 637/637, 7 goldens re-parse with @gfs-bifrost/edi, control refs match UNB/UNH/UNT/UNZ). Shipped to prod with #279 (`81b3f6c`, egress `lookup()` dictionaries fix); prod plan = image + standing sidecar drift.
- 2026-09-24 [inc 1] Dev regression on branch image `9593778` (revision `sftp-connector-dev-cr-00784-jlx`); dev reverted to master afterwards.
  - The dev apply changed only the Cloud Run image.
  - HJF ingest (`FUSE_4366B07EED`): INSDES `regression-133629.edi` → connector by username → records resolved → emitted → routed to `archive/`.
  - GADG confirmation: a replayed receipt (correlationId `mock-fuse1253-regression-2`, `broadcast=true`) resolved every business connector through the new schema. It wrote `FUSE_167F5C016A` + `FUSE_D89734E435` CSV and `FUSE_4E7E60F55B` JSONL `purchase_order_confirmations/2026-09-24-1250-confirmation.*`.
  - No WARNING+ logs on the revision.
  - An earlier replay trimmed of the deprecated goods-in fields failed canonical validation and wrote nothing, which is correct behaviour.
- 2026-09-24 [inc 1] Locally: 598/598 tests. These include `edi` connectors with valid, missing and malformed envelopes resolving via the config-handler (ingest by username); `edi` connectors writing nothing plus `edi_egress_not_enabled` on the dynamic and legacy paths and in stock adjustments; and `createFile` returning created/exists/`CloudStorageException`. Lint and tsc are clean.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
> SUPERSEDED 2026-10-19 — decided: AC 7 narrowed to SSCC; the batch requirement is EDI Support unit E16.
- AC 7, the "mandatory batch" part: nothing can make a batch mandatory. edi has `requireSscc` (DESADV) but no batch equivalent, and sftp's local EDI schemas keep `batch` optional. The one exception is an OSTRPT `batches[]` entry, which must have a `batchNumber`. A line with no batch writes no `GIN+BX`; it doesn't fail as `EdiMessageInvalid`. The rest of AC 7 is proven (see Evidence). Either add a batch requirement, or narrow AC 7 to "SSCC when `requireSscc` is set" with a `wp decide` entry. That's Harry's call.
> SUPERSEDED 2026-10-09 — inc 8 is done: `933d71f` turned `feature_flag_edi` on in dev. See the 2026-10-09 Evidence bullet.
- inc 8: not done. The dev flag is still off on master, which Harry deferred on 2026-09-24.
> SUPERSEDED 2026-10-05 — checked live. The HJF test connector (`conn_1435ca939ecb4c65b728fb0888aae7eb`, `FUSE_4366B07EED`) is `egressFiletype: "edi"` with an `ediEnvelope` in config-service dev, and it ingested normally on 2026-09-30. See the sign-off Evidence bullet.
- inc 1: an `edi` connector can't exist in dev until config-service accepts `edi`, so the edi-skip and lenient-envelope paths are proven by unit tests only. Re-check in dev after config-service increment 1: set the HJF test connector to `edi` and confirm it still ingests and writes nothing, with the unroutable reason.

## Rollout & rollback
<!-- Added on demand. Written at plan time; amend in place as it changes.
     `Shared state touched:` is the single home for the five classes git does not own — a dev
     deploy, a prod config write, a Datadog monitor, a CI var or secret, cross-repo IaC. Reverting
     the branch undoes none of them, so if they are not written here they are not written down. -->
- **Order:**
  1. **Increment 1 must be in prod before config-service accepts `edi`** ([[persist-and-validate-ediegress-on-sftp-connector]]; its merge deploys prod). Otherwise saving `edi` on a connector breaks that connector's ingest on today's image.
  2. The pkg-node serializers are published before the sftp increments that use them (increment 2 needs pkg increments 1-4, increment 4 needs 5, increment 5 needs 6, increment 6 needs 2 and 6).
  3. config-service is in dev before increment 3 is verified.
  4. The fuse-ui flag never turns on in prod before this service's prod flag (FUSE-1256).
> SUPERSEDED 2026-10-05 — FUSE-1259 (sftp-connector#293, `75bd776`, 2026-09-30) merged the switch into one `FEATURE_FLAG_EDI` (Terraform `feature_flag_edi`). It gates EDI ingest as well as EDI confirmations. On master it is `false` in both `dev.tfvars` and `prod.tfvars`.
> SUPERSEDED 2026-10-14 — `FEATURE_FLAG_EDI` (sftp-connector) and `FEATURE_FLAG_EDI_EGRESS` (fuse-ui) are now `true` in dev **and** prod; FUSE-1256 turned them on in that order.
- **Flags/config:** `FEATURE_FLAG_EDI_EGRESS` is new. It is false in both envs at increment 3; dev goes false→true at increment 5. Prod stays false until FUSE-1256.
- **One-way doors:** none in prod. After increment 1, a rollback of sftp to an image **older than increment 1** would break ingest for any connector set to `edi`, so treat increment 1 as the rollback floor once a connector uses `edi`.
- **Rollback:** revert increments 2-4 with git; for the flag, flip it off. With the flag off, `edi` connectors write nothing and report why; they never write CSV.
- **Shared state touched:**
  - Dev deploys for increments 1 and 3. Revert dev to master afterwards and announce in #bifrost-general.
  - The HJF dev test connector and its mapping in config-service dev.
  - A dev Terraform apply through manual-deploy.
  - A prod Terraform apply on each merge, with the flag false. The prod plan redacts env diffs, so compare it to the last applied plan, and approve only the newest parked Deploy run.
> SUPERSEDED 2026-10-14 — both prod flags are on (see the 2026-10-14 Evidence bullet). Proof in prod still pending: no connector uses `edi` there yet.
- **Proof in prod:** n/a until FUSE-1256. Proof in dev: `EdiFileWritten` log count, the forward metric tagged `filetype:edi`, and unroutable reasons for uncovered types.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-19 (Harry)** — AC 7 narrowed to 'SSCC when requireSscc is set'. A mandatory batch can't be expressed (edi has requireSscc only, and sftp's EDI schemas keep batch optional), so it becomes EDI Support unit E16 (requireBatch, config-driven). The rest of AC 7 was proven live on 2026-10-09 (see Evidence).

- **2026-09-29** — Inc 5 mapping reach: INVRPT 0.6.0 carries batch per line as GIN (lines.goodsIdentities.BX) and/or PIA NB (lines.batch), and expiry per line as DTM (lines.dates.36), so no package change. movementRef only reaches the header (BGM documentNumber or a header RFF): INVRPT lines have no RFF and LIN 1082 is an..6. Docs group by identifiers.id (the Snap MoveId), so a multi-line move's BGM takes the first line's movementRef when mapped that way; the dev/test mapping uses if(identifiers.movementRef, identifiers.movementRef, identifiers.id).

- **2026-09-29** — Inc 5: the stock-adjustment EDI branch mirrors confirmation egress's gates: flag off -> edi_egress_not_enabled (unchanged); dynamic mapping off -> edi_requires_dynamic_mapping (AC 6); no envelope -> edi_envelope_missing; rules unfetchable -> no_mapping_rules. Rules come from getUserMappingRulesByUseCase(username, stock_adjustment). No fuse.confirmation.forward delivered metric for stock adjustments (they never emitted one; adding it only for edi would be partial), so filetype:edi forward proof doesn't apply to SA.

> SUPERSEDED 2026-10-19 — "withholds stock_adjustment_made so SNAP re-announces" stopped holding when the poller took over outbound-queue clearing (snap-adapter #291, #294). An invalid INVRPT is now lost: no file, no failure, no re-announce.
- **2026-09-29** — Inc 5 failure path: stock adjustments get no confirmation_data_failure. stock_adjustment is a FailureUseCase in types, but sftp has no stock-adjustment confirmation failure mapping (toConfirmationFailure is ConfirmationType-only; FUSE-1265 found the same), so none was invented. An invalid INVRPT logs EdiMessageInvalid, counts fuse.confirmation.forward_failure{type:stock_adjustment}, still writes sibling targets, and withholds stock_adjustment_made so SNAP re-announces (snap-adapter clears the OBQ on made), mirroring confirmation egress withholding made on invalid EDI. Siblings' CSV windows get re-appended on re-announce, same as confirmation egress.

- **2026-09-29** — Inc 5: sftp-connector adopts @gfs-bifrost/types ^10.8.0 for movementRef + from/to batchId/expiry (the decode strips them otherwise). AC 10 (stay on ^9.5.0) was already superseded by FUSE-1254 on master (^10.7.0); Renovate #286 had already merged at ^10.7.0, so there was nothing open to supersede.

- **2026-09-29** — 2026-09-29 correction: FUSE-1088's scope was settled by Jack on 2026-09-24 12:46 (movement ref, batch, expiry: all yes; Puig INVRPT V04 §5.4.11 DTM+36 expiry is mandatory per batch). Earlier entries calling it 'awaiting decision' were wrong — read from status, not comments. Impediment cleared; build (types + poller) started 2026-09-29. Increment 5's gate is now 'built', not 'decided'.

- **2026-09-24** — Harry, 2026-09-24: leave the dev flag OFF for now and don't author partner mappings until CT's are known. Increment 8 (dev flag on) is deferred, not next; flag-on checks keep using throwaway devflag branch deploys. Increments 5 (FUSE-1088) and 6 (FUSE-1258, now in progress) remain the only code left; FUSE-1259 (inbound DESADV) paused as a potential deviation.

- **2026-09-24** — Inc 3 wired every dispatch-table type (not just goods-in/out/pack) and pulled the EdiMessageInvalid → WriteFailed → confirmation_data_failure path forward from inc 7; inc 7 now only owes the fileType forward-metric tag. An invalid EDI message fails the batch after sibling targets are written. UNB prepared time = write time (idempotency is the deterministic name + create-only write). Goods-out BGM defaults to 351; loading messages set codes.documentName '701' in mapping.

- **2026-09-24** — Inc 2 deviations: (a) EDI module applies header/line rules itself (transformConfirmations rows can't carry dotted paths); line rules are prefixed lines./packages. — supersedes 'column names match *Out fields'. (b) Dispatch table already covers pick/OSTRPT, stock_adjustment/INVRPT, FGR/RECADV, WOC/INVRPT component-only, so incs 4-6 shrink to wiring + dev verification. (c) requireSscc defaults false in edi 0.6.0; partner sets codes.requireSscc — AC 3/7 'mandatory SSCC' means when configured. (d) Config can't blank a serializer default (rules engine drops empty strings). (e) edi dep is ^0.6.0, not ^0.5.0. (f) Found: CSV/JSONL egress transformConfirmations never passes mapping.dictionaries so lookup() is dead in egress mappings; separate fix.

- **2026-09-24 (Harry)** — Scope now covers every confirmation type except returns: FGR (Snap R10 receipt) to RECADV, and WOC component lines (Snap S10 shipment) to INVRPT with finished-good lines excluded to avoid double-booking. Returns stay out until one message is confirmed (the evidence is split between RECADV echoing the RMA and an INVRPT return adjustment), tracked in FUSE-1255. FGR/WOC are gated on a poller follow-up (line batch + work-order references); stock-adjustment INVRPT is gated on FUSE-1088.

- **2026-09-24 (Harry)** — INVARIANT: the EDI egress path is customer-agnostic, and Charlotte Tilbury is config, not code. No serializer, assembly step, dispatch table or UI rule may branch on, or hardcode, a customer or partner. Every partner-varying value (association code, BGM document code, NAD/RFF/QTY/DTM qualifiers, INV/STS codes, envelope IDs) is caller- or config-supplied, with an EANCOM D.96A default. CT's sample files are conformance tests driven by a CT config fixture. The type-to-message mapping follows EANCOM practice and Snap's resource model (S10 work-order shipment, R10 finished-goods receipt), not CT.

- **2026-09-24 (Harry)** — Scope widened from goods-out/goods-in to the five confirmation types Charlotte Tilbury's samples and Puig's guides both document: goods-in to RECADV 352, goods-out to DESADV loading 701, pack to DESADV pack 351, pick to OSTRPT 93E, stock adjustment to INVRPT 78. Returns, WOC and FGR stay unmapped (FUSE-1213 epic note, 24 Sep). Codes Charlotte Tilbury hasn't confirmed come from mapping config, not code.

- **2026-09-24 (Harry)** — Config shape switched from a separate ediEgress block to egressFiletype "edi" + an ediEnvelope block (Harry's call). A cross-repo grep showed only types, config-service, fuse-ui and sftp-connector read egressFiletype, and remote-config consumers only resolve their own connector type, so the enum-widening hazard is confined to sftp-connector and handled by ordering (sftp increment 1 in prod first). Types with no EDIFACT message write nothing and report why, and the UI warns which types they are; an edi connector never falls back to CSV.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->

## Handback
- 2026-10-05 [sign-off] Promoted to `known-context.md` → "Egress and mapping gotchas": the transformer-row shape, origin vs target `connectorId`, the four `ICloudStorageService` doubles, bucket versioning being on, and where the Puig guides live. Each was re-checked on `origin/master` `648ee6e`.
- 2026-10-05 [sign-off] No longer true: "`ConfirmationTarget` carries no connector id". This plan added one (`ConfirmationTarget.connectorId`, the egress target, used for control references). Only the first half of that learning, that `metadata.connectorId` names the origin, was promoted.
- 2026-10-05 [sign-off] Not promoted because already fixed: the three "stale durable docs" items. `architecture.md` and `interfaces.md` were refreshed and re-anchored at `c7ecb31` on 2026-10-01. They now say the per-entity PO/SO made topics are gone, the ready subscriptions are cross-entity, and only the FGR directory is configurable.
- 2026-10-05 [sign-off] For Harry, outside the vault: the `reference_sftp_triage_gotchas` memory note still says bucket versioning is off. It is on (`storage.tf`). The memory file wasn't edited.
