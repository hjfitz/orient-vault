---
title: EDI Support — Migration State
programme: edi-support
status: active
owner: hjf
services:
- pkg-node
- sftp-connector
- config-service
- fuse-ui
- snap-adapter
- fuse-mocker
- fapi
- shopify-connector
- collector
created: '2026-09-30'
updated: '2026-10-13'
tags:
- bifrost
- migration-state
---
# EDI Support — Migration State

<!-- The single source of truth for PROGRESS on Fuse's GENERAL, customer-agnostic EDIFACT capability:
     ingress (EDIFACT → canonical) and egress (canonical → EDIFACT) over SFTP. Customer onboarding
     lives in its own programmes (first: Bifrost/Charlotte Tilbury EDI Onboarding), which depend on
     units here. Split 2026-09-30 from "EDI Confirmation Egress" (set up retrospectively the same
     day); every ✅ shipped 2026-09-16 → 30 before the programme existed. `wp programme` reads and
     writes the tables below — keep their shape. Rows marked "candidate" have no ticket yet. -->

## Unit status
Legend: ⬜ not started · 🟨 in progress · ✅ merged · ⛔ blocked · ⏸ deferred · ❌ dropped · 🔄 rescoped

### I — Ingress (EDIFACT → canonical)
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **I1** | ✅ | EDIFACT parsing + normalizers in `@gfs-bifrost/edi` (FUSE-965) | | medium | opus/high | pkg-node (edi 0.1–0.4.x) | INSDES → sales order, PRICAT → master data, ORDERS → purchase order, RECADV intermediary; 0.4.1 in-package tokenizer (zero runtime deps) |
| **I2** | ✅ | mapping dictionaries + `lookup()` (FUSE-1215/1216/1217/1220/1221/1222) | | medium | sonnet/medium | pkg-node, config-service, fuse-ui, sftp-connector, shopify-connector | Code tables (carriers, qualifiers) as config, not rule text |
| **I3** | ✅ | SFTP ingests `.edi` through the mapping pipeline (FUSE-1231) | I1 | medium | opus/high | sftp-connector#275 | Action folder declares the message type; intermediary flattened to lined-CSV-shaped rows; misroute/parse errors → `create_data_failure` + `error/` |
| **I4** | ✅ | inbound DESADV → purchase orders (ASN) and work orders (kitting) (FUSE-1259) | I3 | medium | opus/high | pkg-node#256, pkg-node#257, sftp-connector#292 | Un-paused 2026-09-30: CT sends no ORDERS, so DESADV is how inbound goods and work orders arrive. New inbound DESADV normalizer; PO folder takes ORDERS or DESADV, WO folder takes DESADV; kit vs component lines by mapping rules; originating doc number + PO refs onto the canonical (echoed back on RECADV). Planned 2026-09-30, two plans cross-linked: `Engineering/pkg-node/plans/FUSE-1259-edi-shared-segment-readers-and-inbound-desadv-no.md` (shared segment readers → edi 0.7.0, DESADV normalizer → 0.8.0) and `Engineering/sftp-connector/plans/FUSE-1259-ingest-inbound-desadv-as-purchase-orders-and-wor.md` (accepted type sets, dev e2e = H3). No types or snap-adapter change needed. Known exposure: PO/WO keyed PUT on a changed resend, to close before CT3 (SUPERSEDED 2026-10-13 — not an exposure: a changed resend is an amendment by Fuse's rules; see I7, dropped) |
| **I5** | 🔄 | keep every NAD party and QTY keyed by its raw qualifier; mapping rules choose | I3 | low | sonnet/medium | | Candidate — no ticket. Reframed 2026-09-30 from a per-business EDI profile: INSDES keeps only BY/SU/DP (CT sends BY, DP, WH, OB, LSP, IV, CN, CA… — the rest are dropped) and treats only QTY 12/21 as ordered (CT sends 113). RFF/DTM/FTX/LOC are already raw-keyed and PRICAT already keys parties by raw NAD — extend that; no new config fragment. **Folded into I4 2026-09-30** (pkg-node plan increment 3): QTY 113 is already raw-keyed, so what remains is raw parties + every PIA composite + line RFFs |
| **I6** | ⬜ | honour the interchange charset (UNOA/UNOC) on ingest | I3 | low | sonnet/low | | Candidate — no ticket. Ingest decodes UTF-8 regardless of the declared syntax |
| **I7** | ❌ | a changed PO/WO resend under the same reference must not overwrite the original | I4 | medium | opus/high | | Candidate — no ticket. Prerequisite for CT3 (Accenture 6 Oct). Checked 2026-10-12: dedupe-service holds only an *identical* resend (`isEqual` vs the stored record, PO keyed on `supplier.reference`, WO on `workOrder.customerRef`); a changed one is forwarded as an amendment by design, and snap-adapter then PUTs the receipt / S10 shipment over the original. Open question: amendments are wanted for other customers, so the hold-on-change rule has to be per-connector/business config, not a fleet-wide change | | Dropped 2026-10-13 (Harry): it would break a core Fuse rule. The deduper holds identical resends; a changed resend is an amendment and reaches Snap, for every customer. Accenture asked only that an accidental duplicate not overwrite (already held) and said a changed resend "should not happen" (SAP cancels and recreates). Whether Snap refuses an amendment once a receipt/S10 is in progress is Snap's behaviour, unverified; snap-adapter surfaces any rejection as a failure |
| **I8** | ✅ | an all-zero EDIFACT date (`DTM+361:00000000:102`) reads as absent, not 1899-11-30 | I1 | low | sonnet/low | pkg-node#269 | Candidate — no ticket. Found 2026-10-12 on CT's real DESADV2: `parseEdifactDate` (`pkg/edi/src/mapping/coerce.ts:12`) builds `Date.UTC(0,-1,0)`. Harmless until a mapping reads `line.dates.361` (expiry) — then Snap gets 1899. Reject any date that doesn't round-trip |

### E — Egress (canonical → EDIFACT)
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **E1** | ✅ | edi 0.5.0 interchange + types 10.4.0 `edi` / `ediEnvelope` | | medium | sonnet/medium | pkg-node#241, #242 | UNB…UNZ around one message. Plan: pkg-node `edi-0-5-0-…` |
| **E2** | ✅ | edi 0.6.0 EANCOM D.96A serializers (RECADV/DESADV/OSTRPT/INVRPT) | E1 | medium | opus/high | pkg-node#244–#248 | Partner codes via `codes.*`; EANCOM defaults |
| **E3** | ✅ | remote-config consumers on types ≥10.4 | E1 | high | sonnet/low | fapi#147, shopify-connector#281 | Backlink refresh isn't type-filtered — see Scar tissue |
| **E4** | ✅ | config-service persists + validates `ediEnvelope` | E1, E3 | medium | sonnet/medium | config-service#226 | Plan: config-service `persist-and-validate-ediegress-…` |
| **E5** | ✅ | fuse-ui EDIFACT egress option on the SFTP connector form (flagged) | E4 | medium | sonnet/medium | fuse-ui#275 | Plan: fuse-ui `edifact-egress-option-…` |
| **E6** | ✅ | sftp: tolerate `edi` + create-only file writes | E1 | high | sonnet/medium | sftp-connector#277 | Umbrella plan `edifact-confirmation-egress-desadv-recadv-behind` inc 1 |
| **E7** | ✅ | sftp: EDI assembly core (mapping → message → interchange) | E2 | medium | opus/high | sftp-connector#278 | Inc 2 |
| **E8** | ✅ | sftp: egress wired behind `FEATURE_FLAG_EDI` | E6, E7, E4 | high | opus/high | sftp-connector#280 | Inc 3 |
| **E9** | ✅ | pick → OSTRPT + `fileType` metric tag | E8 | low | sonnet/low | sftp-connector#281 | Incs 4 + 7 |
| **E10** | ✅ | stock adjustments → INVRPT | E8, D1 | medium | sonnet/medium | sftp-connector#287 | Inc 5 |
| **E11** | ✅ | FGR → RECADV, WOC → INVRPT (components only) | E8, D2, H1 | medium | sonnet/medium | — (wired in #280) | Proven end to end 2026-09-30 via the Snap simulator. Inc 6 |
| **E12** | ✅ | returns confirmation → RECADV by default, INVRPT when the connector's returns mapping declares it (FUSE-1255) | E8 | medium | sonnet/medium | sftp-connector#307, fuse-ui#304 | Rescoped 2026-10-12: the message is the partner's choice, so it's config, not a gate. Branches: sftp-connector `hjf/fuse-1255-edi-returns-confirmation` (`32b11fc`), fuse-ui `hjf/fuse-1255-edi-returns` (`2e775ae`, drops the "Not sent as EDIFACT" warning; merge after sftp). Dev-verified 2026-10-12 on the HJF `hjf test` connector via mocker (`broadcast: true`): RECADV with `RFF+ALQ` RMA, INVRPT `BGM+78`/`INV+2`/`STS+++DEV` via a `messageType` header rule, bad messageType → retryable failure. Which message CT uses is CT4 |
| **E13** | ⬜ | fuse-ui create-connector form offers EDIFACT | E5 | low | sonnet/low | | Candidate — no ticket. Create still hardcodes `csv`; EDIFACT is edit-only |
| **E14** | ⏸ | receive partner acknowledgements (CONTRL / APERAK) | E8 | medium | opus/high | | Candidate — no ticket; deferred in the original plan. Only if a partner requires it. Deferred 2026-10-12: Accenture say SAP/EDICOM exchange no acknowledgements with us |
| **E15** | ❌ | daily stock situation INVRPT (stock per batch per business, on a schedule) | E2, E8 | medium | opus/high | | Moved out of the programme 2026-10-12 (Harry: "scoped for the sprint"). Likely home: the SFTP stock sync sprint tickets FUSE-1299–1306 (stockSync schedule + `stock_sync` mapping), which an EDIFACT connector's mapping would point at INVRPT BGM 35 — unconfirmed |
| **E16** | ⬜ | per-connector batch requirement (`requireBatch`): a DESADV/RECADV line with no batch fails as `EdiMessageInvalid` and writes no file | E8 | low | sonnet/medium | | Candidate — no ticket. Split out of FUSE-1253 AC 7 on 2026-10-19 (Harry). `@gfs-bifrost/edi` has `requireSscc` but no batch equivalent, and sftp's local EDI schemas keep `batch` optional, so today a line with no batch just omits `GIN+BX`. Config-driven like `requireSscc`; build only for a batch-managed receiver that needs it |

### D — Data the messages need
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **D1** | ✅ | stock adjustments carry movementRef + from/to batch + expiry (FUSE-1088) | | medium | opus/high | pkg-node#254, snap-adapter#263 | Also fixed multi-line moves reporting only line 1 |
| **D2** | ✅ | FGR/WOC carry batch + work-order references (FUSE-1258) | | medium | opus/high | pkg-node#249, snap-adapter#257 | |
| **D3** | ✅ | stock adjustment CSV/JSONL follows mapping rules when present (FUSE-1088) | D1 | medium | sonnet/medium | sftp-connector#288 | No rules → fixed file byte-identical |
| **D4** | ⬜ | SFTP standard template reproduces the standard stock adjustment file (FUSE-1279) | D3 | low | sonnet/low | | Few customers; Ready for Refinement |
| **D5** | ✅ | collector on types 10.8.0 | D1 | low | sonnet/low | collector#119 | Otherwise Transaction History strips the new fields |

### R — Robustness found along the way
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **R1** | ✅ | records failing validation go to the Retry Queue (FUSE-1265) | | medium | sonnet/medium | sftp-connector#282 | |
| **R2** | ✅ | sftp on types 10.x; reject missing customer refs (FUSE-1254) | | high | opus/medium | sftp-connector#283 | Retired the local EDI mirrors |
| **R3** | ✅ | `lookup()` dictionaries reach confirmation egress (FUSE-1221) | | low | sonnet/low | sftp-connector#279 | |

### H — Test harness
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **H1** | ✅ | Snap simulator serves the poller's new reads | D1, D2 | medium | opus/high | fuse-mocker 9d15612, 642efa6, 9ec3dd2 | Direct to `main` |
| **H2** | ✅ | fuse-mcp `mock-*` tools point at the mocker's Go API | | low | sonnet/low | fuse-mcp#47 | + parity baseline 59330cb |
| **H3** | ✅ | EDI ingress end to end through the mocker (drop `.edi` → canonical → Snap simulator) | I3, H1 | low | sonnet/medium | sftp-connector#292 (dev e2e) | Candidate — no ticket. Egress is proven this way; ingress has only been exercised with hand-dropped files |

### G — General availability
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **G1** | ✅ | dev flag `FEATURE_FLAG_EDI` on permanently | E11 | low | sonnet/low | | Harry 2026-09-29: off until a partner's mappings are known. Umbrella plan inc 8 |
| **G2** | ⬜ | prod flags on (sftp first, then fuse-ui) — capability live, no connector on `edi` yet | G1 | high | sonnet/medium | | Part of FUSE-1256. Terraform flag flips, plan shared first. Inert until a connector is set to `edi` |
| **G3** | ⬜ | EDI support explainer + integration guide | E11, I3 | low | sonnet/low | | Candidate — no ticket. Waypoint explainer for sftp-connector; developer-portal guide (cf. FUSE-1129) |

## Gates
- [x] **remote-config consumers on types ≥10.4 in prod before any `edi` connector exists** — blocks E4, E8. Cleared 2026-09-24.
- [x] **Stock adjustment data scope decided (FUSE-1088)** — blocks D1, E10. Jack, 2026-09-24.
- [x] **FUSE-1258 in the prod poller** — blocks E11. Poller `3c83850`, 2026-09-29.
> SUPERSEDED 2026-10-12 — returns message is per-partner config (E12 rescoped); a partner's choice now gates only that partner's mapping (CT: CT4).
- [ ] **A partner specifies a returns confirmation message** — no longer holds a unit here; CT's answer is CT4 in its own programme.
- [x] **Harry re-decides inbound DESADV** — blocks I4. Back in scope 2026-09-30.
- [x] **Harry agrees the dev flag can go on** — blocks G1 (and so G2). Cleared 2026-10-06: Harry turned `feature_flag_edi` on in dev (sftp-connector `933d71f`).

## Risks
- **R1 ★ Partner-specific code creeping into the capability** — mitigation: partners are config (`ediEnvelope`, mapping rules, `codes.*`, dictionaries, a future inbound profile) and test fixtures only — status: holding.
- **R2 ★ fuse-ui offers EDIFACT before sftp can write it** — mitigation: G2 flips sftp first — status: both off.
- **R3 Snap-simulator drift** — mitigation: a poller change that calls a new Snap route needs the simulator extended (H1 pattern) — status: current at 9ec3dd2.
- **R4 Ingress silently drops what it can't map** — extra NAD roles, raw-keyed qualifiers, charset — mitigation: I5 / I6 — status: open, no customer on EDI ingress in prod yet.

## Decision log
- **2026-10-19** — **E16 added** (Harry). FUSE-1253's AC 7 is narrowed to "SSCC when `requireSscc` is set", because nothing in edi or sftp can make a batch mandatory. The batch requirement becomes its own config-driven unit, not a sign-off blocker on the merged E8 plan.
- **2026-10-13** — **I7 dropped** (Harry). A per-connector "hold a changed resend" would make one customer treat an amendment as an error, against the deduper's rule for everyone (hold identical, forward changed). It came from over-reading Accenture: their words were that a changed PO/WO resend "should not happen" and an accidental duplicate must not overwrite, which the deduper already does. No CT3 blocker remains from resends. If CT ask what happens to a late change, the answer is: identical duplicates are held; a change is an amendment that Snap accepts or refuses depending on the order's progress.
- **2026-10-12** — **I8 shipped: `@gfs-bifrost/edi` 0.8.1** (pkg-node#269, merged and published). A non-calendar date such as `00000000` is absent rather than 1899-11-30. Reaches sftp-connector when Renovate bumps its `^0.8.0` pin; nothing reads `line.dates.361` until CT's mapping does.
- **2026-10-12** — **CT's first real files ingest end to end in dev** (Accenture's 6 Oct PRICAT, INSDES, DESADV2 from FUSE-1213, dropped on HJF `FUSE_4366B07EED`). DESADV2 → receipt in the Snap simulator first time. INSDES and PRICAT failed canonical validation on the dev test mappings only, then reached `archive/` once those mappings gained coalescing rules for CT's qualifiers (below). Tokenizer handled a released apostrophe (`L?'HOSPITALET`). One ingest bug → **I8**. CT2 mapping must use: SKU from `line.itemIds.SA` (CT's `PIA+1` carries `CT90:GB` / `0302:GD`, so `primaryItemId` is *not* the SKU and INSDES has no LIN item number); INSDES due date `dates.76`, quantity `QTY+113`; PRICAT description `descriptions.DSC`; DESADV supplier GLN `506033232001T` (not in any dictionary yet → `UNKNOWN`). DESADV2 repeats one SKU on two lines (100 + 30) in one package.
> SUPERSEDED 2026-10-13 — I7 dropped; a changed resend is an amendment, not a gap. See the 2026-10-13 entry.
- **2026-10-12** — **I7 added; E14 deferred** (Harry agreed). I7: the deduper only holds identical resends, so a changed PO/WO resend still overwrites in Snap — a real build unit before CT3, with the open question that the rule must be configurable, since other customers rely on amendments. E14: no partner on the horizon sends CONTRL/APERAK.
- **2026-10-12** — **E15 (daily stock situation INVRPT) is out of this programme** — scoped into the sprint (Harry). Tracked there, not here.
- **2026-10-12** — E12 shipped: sftp-connector#307 in prod (`28c514e`, Harry approved; inert while prod `FEATURE_FLAG_EDI` is off). fuse-ui#304 merged but **held at the prod gate** behind FUSE-1205 (Ready for QA) sharing the same deploy — approve fuse-ui run at `1c9d422` (or later) once that passes, then cancel the older parked runs.
- **2026-10-12** — G1 found already done: dev `feature_flag_edi = true` since 2026-10-06 (`933d71f`, Harry); the ledger had it deferred. Mock-driven EDI egress runs can stamp `broadcast: true` on `mock-send` instead of toggling the backend's `broadcastConfirmations`.
- **2026-10-12** — **E12 rescoped: the returns message is config, RECADV by default** (Harry: "rescope E12 with RECADV as default"). An EDIFACT connector's returns mapping may declare INVRPT instead (the Puig INVRPT-guide "return adjustment"); otherwise RECADV echoing the RMA. Unblocks E12 from Accenture; CT's choice moves to CT4. Accenture (Edurne, 6 Oct, FUSE-1213) said only "same structure, only the data changes" for returns, read as leaning RECADV, not agreed in writing.
> SUPERSEDED 2026-10-13 — I7 dropped; a changed resend is an amendment, not a gap. See the 2026-10-13 entry.
- **2026-10-12** — **Accenture's 6 Oct answers recorded** (FUSE-1213, Jack): cancellations are a manual ops process, not interfaced; a changed PO/WO resend under the same reference "should not happen" and duplicates must not overwrite, so I4's changed-resend exposure is a requirement before CT3; SAP/EDICOM expect no acknowledgements from us (E14 is the other direction, still candidate-only); inbound filenames are `<MESSAGE>_<yyyyMMddHHmmss>`. Real CT samples (PRICAT, INSDES, DESADV2) are attached to the epic; no kitting sample yet.
- **2026-09-30** — **One flag, `FEATURE_FLAG_EDI`, gates EDI in both directions** (Harry: "let's gate it all behind the same flag"; sftp-connector#293). Ingest had been on everywhere through `ACCEPTED_FILE_TYPES`; now a `.edi` file is ignored while the flag is off. Off in dev and prod. G1/G2 now switch ingress and egress together.
- **2026-09-30** — **Agents merge EDI Support PRs as they go** (Harry: "you can merge the edi work as you go. this is the rule with this programme and only this programme"). Flag flips, prod environment approvals and Terraform applies still need his confirmation.
- **2026-09-30** — **Ingress is built from reusable segment readers** (Harry: "map each part of the EDI file to the intermediary type… different segments can be reused across different customers, and we map from the intermediary type to the canonical type. Reuse is key"). Each segment/group (NAD, RFF, DTM, QTY, PIA/LIN, GIN, CPS/PAC, FTX, MEA, LOC) maps once into a shared intermediary shape keyed by raw qualifier; a message normalizer is composition of those readers; intermediary → canonical stays config (flatten + mapping rules). Applies to I4 and absorbs I5.
- **2026-09-30** — I4 (inbound DESADV) back in scope and next: CT sends no ORDERS, so it's the only inbound path for POs and work orders. I5 reframed from a per-business EDI profile to raw-qualifier-keyed parties/quantities picked by mapping rules. E15 added: the daily stock-situation INVRPT CT's guide requires, which nothing in Fuse produces yet.
- **2026-09-30** — Split "EDI Confirmation Egress" into **EDI Support** (this; general capability) and **Charlotte Tilbury EDI Onboarding** (Harry: "focus on the latter" = general). Flag enablement and the returns message are general units; CT's mappings/connector are CT's.
- **2026-09-30** — Template gap logged as FUSE-1279, not a blocker ("very few customers integrating this way").
- **2026-09-29** — Dev flag stays off until a partner's mappings are known; flag-on checks use throwaway branch deploys.
- **2026-09-29** — Inbound DESADV (FUSE-1259) paused as a potential deviation.
- **2026-09-29** — Stock adjustment CSV/JSONL is mapping-driven only when the mapping has rules; rules-fetch failure skips rather than falls back.
- **2026-09-24** — `edi` is an SFTP egress file type + `ediEnvelope`, not a new connector type.
- **2026-09-24** — The capability is customer-agnostic, invariably (Harry). Durable record: sftp-connector decision `2026-09-24-edi-egress-is-customer-agnostic-partners-are-config-never-co`.

## Scar tissue
- **Segments map once, into the intermediary, keyed by raw qualifier** — a normalizer composes shared segment readers; never re-parse a segment ad hoc per message or per customer.
- **Customer-agnostic, always** — a partner branch in code is a defect; partners are config + test fixtures.
- **remote-config's connector backlink refresh isn't type-filtered** — every consumer must accept a new `egressFiletype` value before config-service stores one.
- **config-service persists PATCH defaults** — no `.default()` on new connector-config fields.
- **One EDIFACT message per file, one transaction at a time** — `normalizeAll`/interchange fan-out was removed (edi 0.4.0) on purpose.
- **WOC INVRPT carries component lines only** — the FGR's RECADV books the finished goods.
- **Mocker-created records carry `source` `mock`/`mock-sftp`** — sftp's FGR/WOC subscriptions need `broadcast`; set the backend's `broadcastConfirmations` for a mock-driven run, then unset.
- **fuse-mcp data changes need `make parity-accept`**, or the Go parity check goes red on master.
- **A merge commit trips the comment-density hook** on teammates' comments — rebase your own branch; never edit the hook.
- **`wp tick --increment 6` stamps the template example** — hand-tick increment 6.
