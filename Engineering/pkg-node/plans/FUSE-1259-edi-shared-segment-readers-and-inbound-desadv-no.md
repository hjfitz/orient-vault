---
ticket: FUSE-1259
title: 'edi: shared segment readers and inbound DESADV normalizer'
service: pkg-node
status: complete
created: '2026-09-30'
updated: '2026-09-30'
repo: /home/hjf/code/fuse/pkg-node
worktree: /home/hjf/code/fuse/pkg-node/.claude/worktrees/fuse-1259-desadv-inbound
branch: hjf/fuse-1259-desadv-inbound
base: b32c43d67
base_sha: b32c43d67
pr: '257'
tags:
- waypoint
- plan
programme: edi-support
unit: I4
impl_model: opus
impl_effort: high
---
# FUSE-1259 — edi: shared segment readers and inbound DESADV normalizer

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
[FUSE-1259](https://gfs-bifrost.atlassian.net/browse/FUSE-1259) / EDI Support unit **I4** (absorbs **I5**). Give `@gfs-bifrost/edi` an inbound **DESADV** normalizer so an ASN can become a purchase order and a kitting DESADV a work order, entirely through connector mapping rules. Built the way Harry set out on 2026-09-30: each EDIFACT segment is read once, by a shared reader, into the intermediary, keyed by its raw qualifier. INSDES/ORDERS/PRICAT are recomposed on the same readers, so the segments carry over to the next partner and CT's lost INSDES parties (I5) come along for free. Cross-linked: [[../../sftp-connector/plans/FUSE-1259-ingest-inbound-desadv-as-purchase-orders-and-wor|sftp-connector plan]] consumes 0.8.0.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. Every dotted path and value that INSDES/ORDERS/PRICAT produce today, over every synthetic and CT fixture, is still produced with the same value and the same line count after the refactor.
- [x] 2. BGM, LIN, NAD, QTY, PIA, RFF, DTM, FTX, GIN, CPS/PAC/MEA/PCI, TDT, CNT and PRI are each parsed by one shared reader, and no normalizer parses a segment inline. RECADV/INVRPT keep their public shapes.
- [x] 3. CT's INSDES exposes every NAD party under its raw qualifier (`parties.WH/OB/LSP/IV/CN/CA` and the rest), line-level `references.<q>`, and every PIA composite (the `NB` batch). The existing role-alias keys are unchanged.
- [x] 4. `normalize()` on both CT ASN fixtures and a kitting fixture gives a DESADV intermediary with header refs/parties, one line per LIN (sub-lines linked through `subLine.parentLine`, never collapsed), and each line's enclosing package and SSCC.
- [x] 5. Nothing in `src` recognises a partner's codes (`CMP`, `ZZZ:KITTING`, `SRN`). CT exists only in fixtures.
- [x] 6. edi 0.7.0 (readers + widening) and 0.8.0 (DESADV) are published, and the package docs and org changelog describe the raw-qualifier keying.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `pkg/edi/src/normalizer/`: `finders.ts`, `line-readers.ts`, `party.ts`, `qualifiers.ts` become the shared reader set; `insdes/orders/pricat/recadv/invrpt.normalizer.ts` recompose on them; new `desadv.normalizer.ts`.
- `pkg/edi/src/normalizer/intermediary.ts`: the header comment still says parties are keyed "by the *resolved* role". It changes to raw qualifier, with role aliases noted as deprecated.
- `pkg/edi/src/edi.ts` / `index.ts`: register DESADV and export `DesadvIntermediary*`. **`DesadvLine`/`DesadvPackage` are already exported as outbound serializer shapes**, so the new names must not collide.
- **Public contract:** the flattened intermediary paths that FUSE-1231 connector mappings address (`parties.deliveryParty.gln`, `line.quantities.ordered.value`, …). Additive only.
- Shared package → `fuse-mcp-server/data/shared-packages.json` (edi version + DESADV inbound).

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **The Puig DESADV guides describe the outbound pack and loading messages, not the inbound ASN.** No inbound DESADV spec exists. Requirements come from CT's two ASN samples plus the copacking deck. Established by reading both PDFs against the fixtures: MS/MR and SU/ST point in opposite directions.
- **I5 is half done already.** INSDES already keys QTY by raw qualifier (`quantities.113` exists), so what remains is raw NAD parties, every PIA composite and line RFFs. Established from source by two reviewers. The `ordered` alias fallback `["12","21"]` is **not** changed; a CT mapping reads `quantities.113` directly.
- **No customer ingests EDI in prod** (programme R4). The additive design is safe even if that's wrong, and the sftp plan checks it before merge.
- **No normalizer-output snapshots exist today.** `parser.test.ts` only pins segment hashes. Hence increment 1. Established by the structure reviewer.
- **Role aliases are derived from built-in defaults only, not from `EdiMessageProfile`.** The connector never passes a profile (there is no EDI_PROFILE surface).
- UNRESOLVED: a **real CT kitting DESADV** file. Until one exists, the kitting fixture is synthesised from the copacking deck (`RFF+ZZZ:KITTING`, `RFF+SRN`, kit `LIN…:SK`, components `LIN…:SK:CMP:ZZZ+1:1`).

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
Increments 1–3 are **one PR** (edi 0.7.0), because publishing is gated on the version and a no-bump P2 on `main` would ride silently into the next release. Increment 4 is a **stacked PR** (0.8.0).

- [x] 1. Characterisation guard, committed first and generated from current code (AC 1). — 9 fixtures pinned incl. dates as ISO (18 tests, suite 260 green); mutating INSDES documentNumber or readDates fails the goldens — done: f3c0b12
  - *What:* a golden per fixture (every INSDES/ORDERS/PRICAT synthetic and CT fixture) of `normalize()` output flattened to dotted keys, plus `lines.length`. A helper asserts every golden key is present with an equal value and the line count matches, with new keys allowed.
  - *Verify:* `pnpm --filter @gfs-bifrost/edi test` is green on unchanged source; the goldens are committed.
- [x] 2. Extract the shared segment readers and recompose all five normalizers with zero output change (AC 1, 2, 5). — 5 normalizers on shared readers; goldens untouched (266 green, tsc+biome clean); INVRPT's own INV/STS reads stay local (no other message uses them) — done: f3c0b12
  - *Readers:*
    - `splitHeader` / `sliceGroups`, with the terminator set as a parameter per message, so each keeps its current set
    - `readDocument` (BGM)
    - `readLin` (C212 and C829)
    - `readQuantities` (`invalid: "zero"` for INSDES and `"skip"` for ORDERS, keeping today's semantics)
    - an FTX-measure/price reader (moving INSDES's inline FTX+PRD/INV parsing and dropping its "CT carries…" comment)
    - `readPackaging` (PAC), `readPrices` (PRI), `readTotals` (CNT)
  - *Re-pointing:* RECADV's `findRff` and RECADV/INVRPT's `findDtm` also move onto the shared readers, so "segments map once" is true everywhere.
  - *Verify:* the guard shows zero diff; the RECADV/INVRPT tests are unchanged and green; lint and `build` pass.
- [x] 3. Additive widening, which absorbs I5. Then edi **0.7.0** (AC 1, 3, 6). — goldens unchanged; 9 new tests (CT INSDES raw parties OB/LSP/DP/IV/CA/BY/CN/WH, line RFF+ON, NB batch from 2nd C212, PIA precedence IN=C); 275 green; PCI/TDT readers moved to inc 4 where first used — done: f3c0b12
  - *What:*
    - `readAllParties` raw-keyed on INSDES/ORDERS, with the role aliases (`withRoleAliases`, built-in defaults only) kept alongside
    - two-pass `readItemIds`: pass 1 reproduces today's value exactly; pass 2 adds the other C212s and function codes for code lists not yet present
    - line-level `references`, `item.{id,type,codeList,agency}`, `subLine.{indicator,parentLine}`
    - new readers: GIN (`goodsIds.<7405>`), PCI and TDT
  - *Docs:* the `intermediary.ts` keying comment, the edi README and CLAUDE.md, the pkg-node root version table (already stale: it says 0.5.0 but the real version is 0.6.0), and the org Package Changelog.
  - *Verify:* the guard is green; new tests show CT INSDES has `parties.WH/OB/LSP/IV/CN/CA`, line `references.ON`, the SSCC fixture has `itemIds.NB = "2293"`, and a precedence test holds: `PIA+1+A:SA+B:IN` then `PIA+1+C:IN` still gives `IN=C`. No existing fixture has a multi-C212 PIA, so without this test a precedence change would go unnoticed.
- [x] 4. `DesadvNormalizer` built only from the shared readers plus a CPS walker (`readPackages`), then edi **0.8.0** (AC 4, 5, 6). — 34 DESADV tests on CT ASN (3 lines, 1 untagged pkg), ASN+SSCC (10 lines, 10 distinct SSCCs, level-3 PL2), pack (case SSCC + line GIN BX), loading (packages, no lines, TDT); kitting fixture keeps kit + components as lines with codeList CMP / parentLine 1; 315 green; no partner codes in src — done: 196198c
  - *Header:* `documentName`, `documentNumber`, `messageFunction`, `dates`, `references`, and raw `parties`.
  - *Lines:* the ORDERS/INSDES line slots plus `package.{id,parentId,level,type}`, `sscc` (nearest ancestor) and `outerSscc`. No sub-line collapse and no QTY alias. A LIN-less loading DESADV gives packages with no lines.
  - *Fixtures:* both CT ASNs, the synthetic kitting fixture, and a V06-shaped multi-level synthetic (pallet → box SSCC, line `RFF+CR`, `GIN+BX`). `ct-examples.test.ts` normalizes the ASNs.
  - *Verify:*
    - DESADV_INBOUND gives one handling unit `{id:"1"}` (its bare `CPS+1`) with no SSCC, and 3 lines (`item.type=SK`, `quantities.21`, `dates.36`, `itemIds.NB`) with `references.SRN/CR` and `parties.SU/ST/WH`
    - WITH_SSCC gives 10 lines, each with its own `sscc`, `quantities.47E.value=180` and `package.type=PL2`
    - kitting gives 1+n lines, with components carrying `item.codeList=CMP` and `subLine.parentLine=1`
    - `normalize({messageType:"ORDERS"})` on a DESADV throws `EdiMessageTypeMismatchError`
    - the guard stays green
        gate: Harry accepts the synthetic kitting fixture for now (swap to CT's real file tracked), or the real file arrives
              [x] confirmed (Harry, 2026-09-30: use the deck-derived file, swap in CT's real one when it arrives)

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-09-30 [publish] edi 0.7.0 published by the Publish Packages run 36723292936 on f3c0b12, and 0.8.0 by the run on 196198c; `npm view @gfs-bifrost/edi version` → 0.8.0. sftp-connector took ^0.8.0 from the registry and passed its 775 tests (sftp-connector#292).
- 2026-09-30 [inc 4] `desadv-inbound.test.ts`: 34 tests on CT DESADV_INBOUND (1 untagged package, 3 lines), WITH_SSCC (10 lines, 10 distinct SSCCs, level-3 PL2), the pack message (case SSCC, line GIN BX, RFF+CR), the loading message (packages only, TDT) and the kitting fixture (components codeList CMP, parentLine 1). `grep -rlE "CMP|KITTING|ZZZ|SRN" pkg/edi/src` outside tests found nothing. Downstream, the dev e2e (sftp plan) turned both CT ASNs into Snap receipts and the kitting file into an S10.
- 2026-09-30 [inc 3] `raw-qualifier-keys.test.ts`, 9 tests: CT INSDES raw parties OB/LSP/DP/IV/CA/BY/CN/WH, `deliveryParty` equal to `DP`, line `references.ON = 5194302`, `NB` from a later C212, and PIA precedence `IN=C`. The goldens are unchanged.
- 2026-09-30 [inc 1-2] Goldens were generated from unchanged source over 9 fixtures and passed untouched through the reader refactor. Mutations (INSDES documentNumber, readDates) fail them. The ORDERS close-vs-skip boundary isn't reachable by any fixture, so it's pinned in `segment-readers.test.ts`.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- A real CT kitting DESADV. The fixture is built from the copacking deck; swap it in when CT supplies one.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-09-30** — Both PRs were squash-merged (#256 → f3c0b12, #257 → 196198c), so increment stamps now point at the squash commits on main; the branch shas no longer exist. This worktree is detached at main for sign-off.

- **2026-09-30** — Increment 4 lives on the stacked branch hjf/fuse-1259-desadv-normalizer (worktree .claude/worktrees/fuse-1259-desadv-normalizer, PR stacked on #256), so wp tick stamped the base worktree's HEAD; the stamp was corrected by hand to 0453a9d. Sign-off must be run once both PRs have merged to main.

- **2026-09-30** — Shared readers take per-message policy as parameters rather than unifying behaviour: line-group terminators (skip vs close) and the unparseable-QTY policy (INSDES 0, ORDERS drop, PRICAT 0-if-missing/drop-if-non-numeric) are preserved exactly, so the refactor is a zero-diff. Unifying them would be an output change and belongs in its own decision.
- 2026-09-30 — **Rejected alternatives:**
  - *Raw-only parties on INSDES/ORDERS:* breaks FUSE-1231 paths.
  - *Resolved roles or a `despatched` alias for DESADV:* invents semantics the field-map should choose.
  - *PRICAT-style sub-line collapse:* would swallow kit components.
  - *`normalize({messageType: string[]})`:* widens the public API; the connector detects and then declares instead.
  - *Adding SSCC/batch/expiry to canonicals:* there's no Snap receipt-line target yet.
  - *June design's DESADV → GoodsOutConfirmation:* the wrong direction for an ASN.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
(promoted to known-context.md 2026-09-30)
