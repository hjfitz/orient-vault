---
title: Charlotte Tilbury EDI Onboarding — Migration State
programme: charlotte-tilbury-edi-onboarding
status: blocked
owner: hjf
services:
- sftp-connector
- config-service
- fuse-ui
created: '2026-09-30'
updated: '2026-10-12'
tags:
- bifrost
- migration-state
---
# Charlotte Tilbury EDI Onboarding — Migration State

<!-- Onboarding Charlotte Tilbury (Puig SAP, via Accenture) onto Fuse's EDI capability. Everything here
     is CONFIG and customer work, never code — the capability lives in Bifrost/EDI Support. Split
     2026-09-30 from "EDI Confirmation Egress". Units reference EDI Support units by id (e.g. EDI
     Support E11) in Notes; the `Deps` column only resolves units within this ledger. -->

## Unit status
Legend: ⬜ not started · 🟨 in progress · ✅ merged · ⛔ blocked · ⏸ deferred · ❌ dropped · 🔄 rescoped

### CT — Onboarding
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **CT1** | ✅ | CT inbound files ingest (INSDES / PRICAT / ORDERS) | | medium | sonnet/medium | sftp-connector#275 | Built on EDI Support I3 (FUSE-1231); CT samples in `pkg/edi/__fixtures__/ct_examples/` |
| **CT2** | ⛔ | CT partner mappings + envelope authored and proven in dev | | medium | sonnet/medium | | Blocked on CT supplying mappings. Config only: `ediEnvelope`, `codes.*` (e.g. RECADV BGM 352, loading DESADV 701), NAD/RFF/QTY qualifiers; compare output to CT's samples. Needs EDI Support E11 (✅) |
| **CT3** | ⛔ | CT connector live on `edi` in prod (FUSE-1256, CT part) | CT2 | high | opus/high | | Needs EDI Support G2 (prod flags on). Customer-visible cutover — confirm with Harry |
| **CT4** | ⛔ | agree CT's returns confirmation message (FUSE-1255, agreement) | | medium | sonnet/low | | Waiting on Accenture; 6 Oct answer "same structure, only the data changes" leans RECADV. Since 2026-10-12 this only sets CT's returns mapping (RECADV default, or INVRPT); EDI Support E12 no longer waits on it |
| **CT5** | ⛔ | CT inbound qualifiers kept (extra NAD roles, QTY+113) | | low | sonnet/low | | Config on top of EDI Support I5 once it exists |

## Gates
- [ ] **CT supplies partner mappings** — blocks CT2, CT3.
- [ ] **Accenture agrees the returns message** — blocks CT4.
- [ ] **EDI Support G2 (prod flags on)** — blocks CT3.

## Risks
- **R1 ★ CT specifics leaking into code** — mitigation: every CT value is config (EDI Support Scar tissue) — status: holding.

## Decision log
- **2026-10-13** — **Resends are not a CT3 blocker.** EDI Support I7 dropped: Accenture asked only that an accidental duplicate not overwrite, which the deduper already holds; a changed resend "should not happen" and, if one comes, is an amendment like for every customer. I8 shipped (edi 0.8.1). Remaining CT3 dependency from these samples: CT's mappings (CT2).
> SUPERSEDED 2026-10-13 — "resends must not overwrite" over-read Accenture; I7 dropped, not a CT3 blocker.
- **2026-10-12** — **Real samples proven in dev; CT2 mapping inputs known.** Accenture's 6 Oct PRICAT/INSDES/DESADV2 all reach `archive/` on HJF dev. CT's mappings must read: SKU `line.itemIds.SA` (not `primaryItemId`, which is CT's `PIA+1` division code `CT90` / `0302`); INSDES due date `dates.76`, qty `QTY+113`; PRICAT description `descriptions.DSC`; supplier GLN `506033232001T` into the supplier dictionary. Detail in EDI Support decision log (same date). Blockers before CT3: EDI Support **I7** (changed resend must not overwrite) and **I8** (zero date → 1899).
> SUPERSEDED 2026-10-13 — "resends must not overwrite" over-read Accenture; I7 dropped, not a CT3 blocker.
- **2026-10-12** — CT4 no longer gates EDI Support E12: the returns message is per-connector config (RECADV default). Accenture's 6 Oct answers (FUSE-1213): cancellations manual, no acks expected, resends must not overwrite (I4's changed-resend gap is a CT3 prerequisite), filenames `<MESSAGE>_<timestamp>`; real CT PRICAT/INSDES/DESADV2 samples attached to the epic — worth running through ingest under CT2.
- **2026-09-30** — Split out of "EDI Confirmation Egress"; this programme is CT's config + go-live only.
- **2026-09-24** — CT is config and test fixtures, never code (Harry: "has to be invariable").

## Scar tissue
- **CT is config + fixtures, never code** — see EDI Support.
- **CT's samples start at UNH (no UNB)** and use D:96A with subsets (RECADV EAN003, BGM 352) — reproduced by config in `pkg/edi` test fixtures (`src/__tests__/fixtures/ct-*-config.ts`).
