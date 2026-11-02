---
ticket: FUSE-1253
title: edi interchange + generic EANCOM D.96A serializers (RECADV, DESADV, OSTRPT,
  INVRPT) + types edi egress file type
service: pkg-node
status: complete
created: '2026-09-24'
updated: '2026-09-24'
repo: /home/hjf/code/fuse/pkg-node
worktree: /home/hjf/code/fuse/pkg-node/.claude/worktrees/fuse-1253-main
branch: main
base: a6f0027
base_sha: a6f002734
pr: '248'
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: high
programme: "edi-support"
unit: "E1"
---
# FUSE-1253 — edi interchange + generic EANCOM D.96A serializers (RECADV, DESADV, OSTRPT, INVRPT) + types edi egress file type

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
[FUSE-1253](https://globalfreight.atlassian.net/browse/FUSE-1253). This plan covers the package releases that EDIFACT confirmation egress ([[edifact-confirmation-egress-desadv-recadv-behind]]) needs.

- **`@gfs-bifrost/edi`** gets a full interchange envelope, plus serializers for the **five confirmation messages Charlotte Tilbury's samples and Puig's guides both document**. They're built as generic EANCOM D.96A messages. The table below is only where each one is used; the codes that vary by trading partner come from the caller:

  | Message | Used for | Charlotte Tilbury's values (their config) |
  |---|---|---|
  | RECADV | goods-in, finished goods receipt | EAN003, BGM 352 |
  | DESADV (shipment/loading) | goods-out | EAN005, BGM 701 |
  | DESADV (pack) | pack | EAN005, BGM 351 |
  | OSTRPT | pick | EAN002, BGM 93E |
  | INVRPT (stock movement) | stock adjustment, WOC component staging | EAN004, BGM 78 |

- **`@gfs-bifrost/types`** gets the next minor, which widens the SFTP `egressFiletype` to include `"edi"` and adds an optional `ediEnvelope`. It is consumed by [[persist-and-validate-ediegress-on-sftp-connector]] and fuse-ui.

Returns are **not** mapped until one message is confirmed (FUSE-1255).

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. `EdiService.serializeInterchange(...)` wraps one message in UNB…UNZ (UNOC:3 by default).
  - UNB 0020, UNZ 0020 and UNH 0062 all equal the supplied control reference.
  - The UNZ count is 1, and the UNT count equals the message's segment count.
  - Data is release-escaped.
- [x] 2. **No customer-specific values in code.** Each serializer builds the EANCOM D.96A segment structure. Every partner-varying value takes a documented EANCOM default and can be overridden by the caller:
  - the association code/subset;
  - the BGM document code;
  - NAD party qualifiers;
  - RFF/QTY/DTM qualifiers;
  - INV/STS codes.
- [x] 2a. Given a **Charlotte Tilbury config fixture** (test data, not code), each serializer reproduces the segment sequence, qualifiers and codes of the matching sample in `__fixtures__/ct_examples/`. Given no overrides, it produces the EANCOM defaults. Both outputs parse with `parseEdifact`.
- [x] 3. DESADV output carries the package hierarchy: `CPS` per package, `PAC`, `MEA` weight, `PCI 33E` + `GIN+BJ` SSCC, and the pack message's lines under their package with `PCI 36E` + `GIN+BX` batch. Missing mandatory SSCCs or batch fail with `EdiError`, not silently.
- [x] 4. `@gfs-bifrost/types` includes `"edi"` in `EgressFiletype`, and adds `SFTPEdiEnvelope` / `ediEnvelope?` on both `SFTPIngress` arms and `SFTPIngressConfigService`. Qualifiers are plain strings, and there are no defaults.
- [x] 5. Every release has a Package Changelog entry in `code/CLAUDE.md`, and every dist loads under plain Node (CJS and ESM).

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `pkg/edi/src/serializers/`:
  - `edifact.ts:38-51` `wrapMessage` (the reference `"1"` and `EAN005` are hardcoded) and `types.ts:7-10` `MessageSerializer`.
  - `desadv.serializer.ts` and `recadv.serializer.ts`: today they're lean D:01B. They are reworked here.
  - New: `interchange.ts`, `desadv-shipment`, `ostrpt` and `invrpt` serializers.
- `pkg/edi/src/edi.ts:154` `EdiService.serialize`, `config/profile.ts:24-32` `EdiEnvelopeProfile`, and the serializer output types (`DesadvOut` / `RecadvOut`, plus new ones).
- Reference inputs:
  - Samples in `pkg/edi/__fixtures__/ct_examples/`: `RECADV.txt`, `DESADV_LOADING.txt`, `DESADV_PACK_MESSAGE.txt`, `OSTRPT_PICK_MESSAGE.txt`, `INVRPT_STOCK_MOVEMENT.txt`.
  - Guides in `~/code/fuse/edi-guides/PUIG EDI standards EDIFACT/`, and the Confluence decodes 241369176 (RECADV), 241926169 (DESADV), 241631287 (DESADV Shipment), 241827900 (OSTRPT) and 241926145 (INVRPT).
  - Jack's data dictionary 306249733.
- `pkg/types/src/config/types/connectors/sftp.type.ts`, `connector.type.ts:46-74` and `:187-198`; `schemas/connectors/sftp.schema.ts:14-17`, `connector-fragment.schema.ts:30-69`.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **INVARIANT (Harry, 2026-09-24): the egress path is customer-agnostic, and Charlotte Tilbury is config, not code.** No serializer, assembly step or dispatch table may branch on, or hardcode, a customer or partner.
  - The type → message mapping is general EANCOM practice and matches Snap's resource model:
    - goods-in → RECADV
    - goods-out and pack → DESADV
    - pick → OSTRPT
    - stock movement → INVRPT
    - FGR (Snap `R10` receipt) → RECADV
    - WOC components (Snap `S10` shipment) → INVRPT
  - Every place Puig departs from UN D.96A/EANCOM is a caller-supplied value, with the EANCOM default in the serializer: `BGM 352` vs the standard 632, `INV` 1-4, `STS` reasons in place of `INV 4499`, NAD `WH`.
  - The existing D:01B `DesadvSerializer`/`RecadvSerializer` output changes in a 0.x minor. Their only callers are the package's own tests; confirm with a fleet-wide grep at implementation.
- **Codes are inputs, not constants, whether or not Charlotte Tilbury has confirmed them.** OSTRPT `STS` status codes are "Not CT-confirmed" in the data dictionary, and INVRPT `INV`/`STS` reason codes depend on the movement. Both come from the caller (the connector's mapping config), so a correction is a config change, not a release.
- **Pack vs loading split: pack → DESADV 351, goods-out → DESADV 701.** This is inferred from the sample names and Snap's stage order (pack at 39, despatch at 90). The 18 Jun DESADV design page (216891918) still lists "BGM 701 vs 351" as open. Confirm with Charlotte Tilbury, but it doesn't block the build.
- **Envelope from email:** D.96A, `UNOC:3`, ID qualifier 14, EDICOM middleware, one message per file. The Puig guides give no UNB detail ("should be confirmed separately"), so the envelope stays caller-supplied.
- **The types enum widening is safe for remote-config consumers.** They resolve their own connector type only (grep and `connector.handler.ts:320-350`, 24 Sep). sftp-connector is handled by ordering.
- **The version number is "next types minor at merge time".** pkg-node #232 and #233 are also racing for a bump.
- UNRESOLVED (CT, doesn't block): which UNB IDs to use in production, whether a test indicator is expected, and whether RECADV should carry `QVR` for discrepancies.

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
- [x] 1. edi interchange: — 113/113 edi tests; DESADV/RECADV output byte-identical to 0.4.1; plain-Node require+import proven — done: ce38d2e
  - `wrapMessage` options (reference, version, association code), with defaults unchanged;
  - `MessageSerializer.serialize(message, { reference }?)`;
  - `serializers/interchange.ts` plus `EdiService.serializeInterchange({ envelope, controlReference, preparedAt, syntax?, message, includeUna?, segmentSeparator? })`;
  - the changelog entry.

  (AC 1,5) — verify: `outbound.test.ts` cases for the envelope, counts, refs and escaping; the existing assertions unchanged; plain-Node CJS `require` and ESM `import` from `dist`.
      gate: published
            [x] confirmed
- [x] 2. RECADV rebuilt on the EANCOM D.96A structure: `BGM` document code, `DTM`, `RFF` references (`DQ`/`ON`/RMA as the caller supplies), `NAD` parties, `CPS`, `LIN` + `PIA` item/batch, and `QTY` received/accepted. Every code has an EANCOM default and a caller override. It covers goods-in and finished goods receipts through the same shape. (AC 2,2a,5) — verify: a golden test against `RECADV.txt` using the CT config fixture; a defaults golden test; `parseEdifact` round-trips both. — pkg-node#244; CT RECADV + copacking FGR goldens — done: 3993521
- [x] 3. DESADV with the package hierarchy (reference: Puig DESADV V06 / `DESADV_PACK_MESSAGE.txt`): the package hierarchy (`CPS`/`PAC`/`MEA`/`PCI 33E`+`GIN BJ`), then lines under each package (`LIN`, `PIA SA`, `QTY 12`, `RFF`, `PCI 36E`+`GIN BX`). (AC 2,3,5) — verify: a golden test against `DESADV_PACK_MESSAGE.txt` using the CT config fixture; a defaults golden test; a missing SSCC or batch throws `EdiError`. — pkg-node#245; CT pack golden — done: dfe58d7
- [x] 4. DESADV shipment/loading variant, with pallets and no lines (reference: Puig DESADV Shipment V01 / `DESADV_LOADING.txt`): `RFF` SRN/BN/BM/MB, `TDT`, `CPS` per pallet with `PAC`/`PCI`/`GIN BJ` and `DTM 365`, and no lines. (AC 2,3,5) — verify: a golden test against `DESADV_LOADING.txt` using the CT config fixture; a defaults golden test. — pkg-node#245 (same serializer); CT loading golden — done: dfe58d7
- [x] 5. OSTRPT (reference: Puig V04 / `OSTRPT_PICK_MESSAGE.txt`): `RFF`, NAD parties, `STS` status, `LIN` + `PIA SA/NB` + `QTY 46`. (AC 2,5) — verify: a golden test against `OSTRPT_PICK_MESSAGE.txt` using the CT config fixture; a defaults golden test. — pkg-node#246; CT pick golden — done: 4b4e291
- [x] 6. INVRPT stock movement (reference: Puig V04 / `INVRPT_STOCK_MOVEMENT.txt`): NAD parties, `LIN` + `PIA` item/batch, `QTY`, `INV` direction and `STS` reason, all as caller-supplied codes. It covers stock adjustments and WOC component staging through the same shape. (AC 2,5) — verify: a golden test against `INVRPT_STOCK_MOVEMENT.txt` using the CT config fixture, plus one against the copacking deck's staging example; a defaults golden test. — pkg-node#247; CT stock movement + situation + copacking staging goldens — done: 17cc22f

  Increments 2-6 can ship as separate edi minors or be batched. Each is its own PR.
- [x] 7. types next minor: `EgressFiletype` gains `"edi"`, plus `SFTPEdiEnvelope` / `ediEnvelope?` with schemas and the changelog entry. It runs in parallel with the others. (AC 4,5) — verify: config-service `build:check` against a packed tarball; a remote-config test that a REST/SHOPIFY-typed resolve is unaffected by an `edi` SFTP connector in the same business. — types 63/63, remote-config 107/107; config-service build:check + 666 tests green against the packed 10.4.0 — done: 903eb7f
      gate: published
            [x] confirmed

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-09-24 [inc 2-6] Stack pkg-node#244-#248 merged. `@gfs-bifrost/edi` 0.6.0 is published.
  - Each serializer's golden test reproduces its Charlotte Tilbury sample from a test-only config fixture: RECADV (plus the copacking FGR), DESADV pack and loading, OSTRPT pick, and INVRPT movement, situation and copacking staging.
  - A defaults test shows EANCOM codes with no config.
  - 242/242 tests at the release tip, plus lint, build and a test type-check. An inline `codes` override through `EdiService.serialize` is tested.
- 2026-09-24 [inc 7] types 10.4.0 is published (pkg-node#242).
  - Downstream on 10.4.0 in prod: config-service (build and 688 tests), fapi (`7607f05`), shopify-connector (`09b0f4a`, via Renovate #281).
  - A throwaway check reproduced the `edi` backlink-refresh throw on 10.3.0 and showed it fixed on 10.4.0.
  - In dev, both services returned 202 on an `edi` connector's revision events.
- 2026-09-24 [inc 1] edi 0.5.0 is published (pkg-node#241).
  - 113/113 tests; DESADV/RECADV output byte-identical to 0.4.1; plain-Node `require` and `import()` both work.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- End-to-end use of the serializers from sftp-connector is the sftp-connector plan's (increments 2-6 there).

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-09-24** — Serializers ship as a 5-PR stack (pkg-node#244 RECADV, #245 DESADV, #246 OSTRPT, #247 INVRPT, #248 release 0.6.0); no version bump until #248 so one publish carries all four. Default codes where EANCOM has no standard (OSTRPT BGM 23, DOC 270) are UN D.96A picks. CT sample oddities handled as data, not code: RECADV/DESADV 14-digit dates under 203, INVRPT QTY 124 vs 145, BGM 78:::9 vs ::9.

- **2026-09-24** — This plan ships as more than one PR: edi increments on hjf/fuse-1253-edi-egress (pkg-node#241), types increment 7 on hjf/fuse-1253-types-edi-egress (pkg-node#242), so each package publishes independently.

- **2026-09-24** — Increment 1 kept the serializers' default release at D:01B so existing output stays byte-identical; D.96A partners pass options.release. Switching the default to D.96A belongs with the serializer rework in increments 2-6. Also: remote-config's connector backlink refresh is not type-filtered, so fapi and shopify-connector must be on types >=10.4.0 in prod before any connector is saved as edi (gate added to the config-service plan).

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
(none — promoted to known-context.md 2026-09-24)

