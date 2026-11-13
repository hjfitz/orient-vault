---
title: Native Dispatch — Migration State
programme: native-dispatch
status: planning
owner: Harry
services:
- parcel-portal
created: '2026-11-13'
updated: '2026-11-13'
tags:
- bifrost
- migration-state
---
# Native Dispatch — Migration State

<!-- The single source of truth for PROGRESS. The Overview carries the narrative and the verdict;
     this doc is the live ledger a session reads to know what is done and what is next.
     `wp programme status/next/tick` read and write the `## Unit status` tables below, so keep the
     table shape intact. Requirements and their sources are in [[Native Dispatch/Requirements]]. -->

## Unit status
Legend: ⬜ not started · 🟨 in progress · ✅ merged · ⛔ blocked · ⏸ deferred · ❌ dropped · 🔄 rescoped

### S — Shipped on 12 Nov, before this programme (TCA test session)
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **S1** | ✅ | Hide the API key section of the customer admin UI | | low | sonnet/low | ilg-merak/parcel-portal#131 | UI only. The API, keys and Swagger are unchanged, and re-enabling is a plain revert (see T10). |
| **S2** | ✅ | Generate an SFTP key pair in the admin's browser | | high | opus/high | ilg-merak/parcel-portal#132, #133, #135 | RSA 4096 in WebCrypto; the private key is downloaded once and never reaches svc; `source` column (migration 019), contract 5.13.0. Not verified in browsers other than Chromium, or on Windows. |
| **S3** | ✅ | Submit the packaging preset's size and weight units | | low | sonnet/medium | ilg-merak/parcel-portal#134 | The ui-toolkit select doesn't pass its `name`, so FormData lost the unit fields. Fixed in the portal; the toolkit bug belongs to ilg-platform and isn't filed. |
| **S4** | ✅ | Round a commodity's customs value and the shipment's total weight | | med | sonnet/medium | ilg-merak/parcel-portal#136 | FIP was rejected with "missing Wrong customs amount": 3 × 0.95 went out as 2.8499999999999996. Verified on dev: FIP, FIGR and the 3-parcel order all validate. |

### L — Dispatch lifecycle
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **L1** | ⬜ | Void a dispatched label from the order page | | med | sonnet/high | | **R01.** Void exists only on the shipment page: `DeleteShipments`, then the order returns to Ready. Add it to a dispatched order's page, and say plainly when a manifested shipment can't be voided. Verify on dev with the test carrier; the live endpoint only with Harry's go-ahead. |
| **L2** | ⬜ | Remove an order from the list (delete, not just cancel) | L1 | med | sonnet/medium | | **R01.** Cancel only voids orders that were never booked, and a voided order stays dead; there is no delete route. Oliver decides what he means first (G6). |

### O — Order page and editing
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **O1** | ⬜ | Show recipient email and phone beside the address | | low | sonnet/low | | **R05.** Read-only: Phil accepted that. Stored and sent already; only the page is missing. Editable would need `OrderEdit` fields and a re-validation, and isn't asked for now. |
| **O2** | ⬜ | Show total weight on the order, as the sum of its parcels | | med | sonnet/high | | **R04.** Show the sum, and stop the export preferring the file's stated total once parcels exist (`core/exports/csv.go:82-85`). Whether it is ever editable is Q5; the proposal is no. |
| **O3** | ⬜ | Carrier service as a dropdown | | med | sonnet/high | | **R06.** A customer-readable list of the account's services (the list route is admin-only), a select on the order form, and a check on save rather than only at dispatch. Contract bump. |
| **O4** | ⬜ | Add and remove product lines on an order | | med | sonnet/high | | **R02.** Lines are edit-only today. Re-validate after each change, keep the customs fields for Canada, keep a re-import replacing the order, and keep dispatched orders read-only. |
| **O5** | ⬜ | Product weight | | low | sonnet/medium | | **R03.** No per-item weight exists; the parcel weight is editable in Packing. Wait for G1 to say which one Yusen means. |
| **O6** | ⬜ | A Despatch button at the foot of the order page | | low | sonnet/low | | **R09.** One dispatch panel with a second trigger in a bottom bar. Don't render a second panel under the same key: that is the C23 bug class in the Parcel Portal programme. |
| **O7** | ⬜ | One view for a shipment and its order | O1, O2, L1 | med | sonnet/high | | **R08.** Shipments rows open the order page, and the order page carries the labels, tracking, void, booking summary, contact details and weights. |
| **O8** | ⬜ | Say why an order needs packing | | low | sonnet/low | | **R07.** Needs packing means the order is valid but the file gave no parcel size, weight or preset. Say that on the badge or the order page. |
| **O9** | ⬜ | Warn about unsaved products and parcels before dispatching | | low | sonnet/medium | | Found by the review of the order-page PR. The address form now warns when it has unsaved changes; the Products and Packing panels keep their own state, so editing them and clicking Dispatch books the saved values. Needs that state lifted, or each panel reporting dirty. |
| **O10** | ⬜ | Keep what a shipment booked, so a voided export row keeps its weight | | low | sonnet/medium | | Found by the review of O2. The export reads the order's current parcels, so a voided shipment shows the new weight after a repack. Store the booked weight on the shipment at booking (a migration). |

### I — CSV import
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **I1** | ⬜ | Fill a parcel's size and weight from a preset named in the CSV | | med | sonnet/high | | **R11, a bug.** Import keeps the preset name as text and never reads the preset (`core/mapping/orders.go:202`, `core/imports/ingest.go:94-104`), so the order shows Ready and dispatch refuses it. Read the tenant's presets at import and fill the parcel; an unknown name becomes a row problem. Verify on the dev TCA customer: import a file naming a preset, then Check with carrier. Until it ships, saving the Packing panel fills the dimensions. |
| **I2** | ⬜ | ConsigneeReference: column, order field, order page, search, Selector | | med | sonnet/high | | **R10.** An optional column, a migration, a contract bump, and `ConsigneeReference` set on the Selector request (it is on the wire and never filled). Check with Phil that it isn't the Container ID (Q2). |
| **I3** | ⬜ | A number of packages on a single CSV row | | med | sonnet/high | | **R12.** Needs the call with Phil (G1): the column, how it combines with Parcel Number, and whether an order may have no product lines. |

### X — Integrator contract
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **X1** | ⏸ | Required, optional and ignored fields for Yusen US | | low | sonnet/low | | **R13.** The fields Chris names are in Selector2's REST schema, not here (G2). If that is the spec going out, hand this to the Selector2 programme. If it is `public-openapi.yaml`, nothing needs removing and the answer is a short required/optional table. |

### T — TCA trial and carried findings
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **T1** | 🟨 | Prove the connection against TCA's live endpoint | | med | none | | **R17.** On 13 Nov Oliver asked to test-print against TCA live (11:07 UTC), Harry said yes, and Oliver reports a label was generated (14:06). Not confirmed by us: what was created at the carrier. Left: note the consignment and cancel it (L1), answer bill-on-scan and http or https, and try a multi-pack (every live booking Oliver has seen is a single parcel). |
| **T2** | ⬜ | Allow ShipperId 0 on a carrier connection | | med | sonnet/medium | | **R14.** Relax `CHECK (shipper_id > 0)` (migration 004), `core/carriers/connection.go:211`, and any OpenAPI minimum; prove a 0 reaches the request XML; then set TCA's live connection to 0. |
| **T3** | ✅ | Allow weight 0 on a packaging preset | | low | sonnet/medium | ilg-merak/parcel-portal#137 | **R16, approved by Harry on 13 Nov.** `core/packaging/presets.go:134` rejects it. The preset is the box's own weight; a parcel with no weight must still fail before dispatch. |
| **T4** | ⬜ | TCA's five packing templates on dev | T3 | low | sonnet/low | | **R16.** Five presets at 0.000 kg, with the sizes from Oliver's TCA config (for example 22.9 × 20.3 × 10.2 cm), made through the admin API; check one with Check with carrier. |
| **T5** | ✅ | TCA export settings: tracking link and time zone | | low | sonnet/low | | **R15.** Link template `https://tracking.justshoutgfs.com/ConsLink.asp?ConsNumber={consignment}` (Oliver, 12 Nov), and the site time zone, on the customer's Export tab on dev. **Done 13 Nov** (dev TCA customer, via the admin API): the link is set; the time zone already read America/New_York and was left, so confirm the site's zone with Oliver. |
| **T6** | ⏸ | Bench printing on Windows | | high | opus/high | | WebUSB can't claim a printer that the Windows driver owns. Options: WinUSB through Zadig on one PC per printer, or the browser print dialog for the trial. No software on benches, so QZ is a fallback only (T7). Needs the printer models and Yusen IT's driver policy (G3). See `docs/printing.md` in the repo. |
| **T7** | ⏸ | QZ Tray as a per-bench option | | high | opus/high | | Designed on 12 Nov, not built. Three PRs: a `transport` field with migration 020, a `label-print` adapter, and the UI. Unsigned QZ prompts on every print, so silent printing needs signing, a later and separate decision. Adds the LGPL `qz-tray` dependency. Harry's yes or no (G4). |
| **T8** | ⬜ | Fix the red dev smoke test | | low | sonnet/low | | Red since at least 6 Nov: dev refuses the `smoke-test@` account. Re-provision it with the dev admin and set `DEV_SMOKE_ADMIN_PASSWORD`. It changes dev state, so Harry first. |
| **T9** | ✅ | Plain error text when a packaging save fails | | low | sonnet/low | ilg-merak/parcel-portal#140 | The raw OpenAPI error is shown (`settings/packaging/actions.ts`). |
| **T10** | ❌ | Re-enable the API key UI | | low | sonnet/low | | **Dropped (Harry, 13 Nov: "api key - won't come back").** The UI stays hidden (S1). The API and the keys stay up, so TCA's API test needs no UI. |
| **T11** | ⏸ | DDP on FIP | | med | sonnet/high | | The portal hardcodes DDU and sends customs only for Canada. **Answered 12 Nov:** Oliver, passing on Chris's advice, says to test with DDP for everything, and Canada is the only country noted so far; his TCA server config also shows FIP with Terms Of Sale DDP and Shipment Content "Stationary Products". Send DDP for every shipment in test, and settle where Shipment Content comes from. |
| **T12** | ⏸ | Customer self-serve for SFTP keys | | med | sonnet/high | | Undecided. Today only a GFS admin generates or adds a key (S2). |
| **T13** | ✅ | Say "Native Dispatch" in user-facing text | | med | sonnet/low | ilg-merak/parcel-portal#139 | "Parcel Portal" is still hardcoded in UI titles, the sign-in card and the gateway docs title. The export's `salesChannel` is the literal "Parcel Portal" (`core/exports/csv.go:20`) and goes into customers' files, so tell Oliver when it merges. **Approved (Harry, 13 Nov: "rename to native dispatch").** No customer is on prod yet, so no live file carries the old value. |
| **T14** | ✅ | Renew or fix the three Trivy ignores that expire on 16 Nov | | low | sonnet/low | ilg-merak/parcel-portal#138 | `.trivyignore.yaml` entries for CVE-2026-78661, CVE-2026-76844 and CVE-2026-85091 stop applying on 2026-11-16, so the scan goes red that day. **Approved to renew (Harry, 13 Nov).** First check whether the runtime images now carry the patch; renew only what is still needed, with a new expiry and the reason. |
| **T15** | ✅ | Correct `docs/runbook.md` and `apps/svc/README.md` | | low | sonnet/low | ilg-merak/parcel-portal#141 | Found by the 13 Nov doc refresh; re-check each claim when the unit starts. The runbook says one SFTP account, one carrier tenant, no list-tenants call and no void. The README says nothing enforces the carrier-services list (dispatch does) and that the ui sends `X-Expected-Tenant` (it doesn't; the stale-tab guard is svc-only), and its package listing omits directories. |
| **T16** | ⬜ | Round package dimensions down to whole cm | | low | sonnet/medium | | **R18 (Oliver, 12 Nov).** `wholeCM` rounds up; Despatch Cloud rounds down (0 of 116 live bookings had decimals), so dim weight would move. Floor each side, keep weight decimals, and settle a side under 1 cm (it would floor to 0). Test through the real request builder. |

## Gates
<!-- A precondition that is NOT a unit — another programme reaching prod, a monitor reading real
     volume, a sign-off. Check the box when it clears; say what it blocks. Not code, so it can't be
     inferred from a diff — this is the structural version of "do not action yet". -->
- [ ] **G1 — Call with Phil on single-line multi-parcel and product weight** — blocks I3, O5. Phil said it "might need a call". It settles Q3 and Q4: the package-count column, how it combines with Parcel Number, whether an order may have no product lines, and which weight is meant.
- [ ] **G2 — Chris says which spec goes to Yusen US** — blocks X1. Selector2's REST API or `public-openapi.yaml` (Q6).
- [ ] **G3 — Printer models and Yusen IT's driver-swap policy** — blocks T6. Oliver has not answered.
- [ ] **G4 — Harry's yes or no on the QZ Tray pilot** — blocks T7. It accepts the LGPL dependency and the `transport` field.
- [x] **G5 — Harry decides whether the API key UI comes back** — blocks T10. Cleared 13 Nov: Harry, "api key - won't come back". T10 is dropped.
- [ ] **G6 — Oliver says what is missing for cancelling a dispatched label** — blocks L2. Void from the order page, deleting the order, or voiding after manifest (Q1).
- [x] **G7 — Oliver says which countries need DDP on FIP** — blocks T11. Cleared 12 Nov: test with DDP for everything; Canada is the only country noted (R19).
- [x] **G8 — Harry decides whether user-facing text and the export say Native Dispatch** — blocks T13. Cleared 13 Nov: Harry, "rename to native dispatch". T13 is approved.
- [ ] **G9 — Oliver or Phil confirms Manhattan reads the export's weight in kilograms** — blocks O2. The column was the file's own unit, and O2 makes it kilograms always. Dev is unaffected; this must be settled before any prod launch (Q9).

## Risks
<!-- ★ marks the load-bearing ones. Each: the risk, the mitigation, and its current status. -->
- **R1 ★ A live carrier account sits behind the trial** — a test label on TCA's live CSS box is a real consignment and may bill on scan. Mitigation: note every live consignment, void it before any manifest (L1), and no agent calls CommitShipments, PrintManifest or ProcessCarrierDispatch on any endpoint — open.
- **R2 ★ A Ready order that can't be dispatched** — until I1 ships, an order that names a preset in the CSV shows Ready and fails at dispatch. Mitigation: I1 first; meanwhile save the Packing panel to fill the dimensions — open.
- **R3 ★ Additive feedback grows while TCA wants an account now** — Mitigation: wave 1 is only what blocks TCA's first manual order; the rest follows — open.
- **R4 The export total can differ from what Selector booked** — after a parcel weight is edited, Selector gets the new sum and the export to Manhattan can keep the file's stated total. Mitigation: O2 — open.
- **R5 No named decision-maker on Yusen's side** — the 13 Nov catch-up wants one, and an org chart, to raise on Monday 16 Nov at 11:00 — open.
- **R6 The API key UI is hidden while TCA plans an API test** — Harry decided on 13 Nov that it stays hidden. The API and the keys stay up, so the test needs no UI — closed.
- **R7 Two programmes share one repo** — new ledger entries use `--programme "Native Dispatch"`; units A–D and the prod gate D1 stay in Parcel Portal — standing.

## Decision log
<!-- Dated, newest first. Written as decisions are taken; a decision worth defending in six months
     is a durable record instead (`wp decide --record`). -->
- **2026-11-13** — **Wave 1 is merging.** Merged: T9 (#140), T14 (#138), T3 (#137), T13 (#139), T15 (#141). T14 removed the Trivy ignores instead of renewing them, because the platform has rebuilt both runtime images and every container scan passes with an empty list; Harry had said to renew, and the PR says so. Found while checking the DM: Oliver asked on 12 Nov for dimensions to be rounded down (R18, T16) and relayed Chris's advice to test with DDP for everything (R19, T11). Oliver also planned a TCA trial account for the afternoon of 13 Nov.
- **2026-11-13** — **The export and user-facing text will say Native Dispatch** (Harry: "rename to native dispatch"). Unit T13. The export's `salesChannel` changes with it; Oliver is told when it merges.
- **2026-11-13** — **The expiring Trivy ignores are renewed** (Harry: "trigy ignore - renew them"). Unit T14, due before 16 Nov.
- **2026-11-13** — **The API key UI stays hidden** (Harry: "api key - won't come back"). T10 is dropped and R6 closed. The API and keys stay up.
- **2026-11-13** — **Programme created.** Harry asked for the Teams feedback from Phil, Pete and Chris to be broken into requirements and fed into a new programme, with the portal's orient docs brought up to date. The 17 requirements and their sources are in [[Native Dispatch/Requirements|Requirements]], each checked against `origin/main` at `621357e`. Findings that changed the plan: the preset-dimensions complaint is a real bug (R11); "cancel label / set live again" mostly exists on the shipment page (R01); ShipperId 0 needs a migration (R14); Chris's legacy fields are Selector2's, not ours (R13).
- **2026-11-13** — **Weight 0 on a packing template is approved** (Harry: "allow weight 0 and make the templates"). Units T3 and T4. It was paused for this work and is next.
- **2026-11-13** — **The name is Native Dispatch**, chosen in the team catch-up. The repo, service and system ids stay `parcel-portal`; the old programme folder keeps its name.
- **2026-11-13** — **Phil narrows R05 to read-only** contact details, after Pete asked why they would ever change.
- **2026-11-13** — **A live test print against TCA** was asked for by Oliver and agreed by Harry; Oliver reports it worked. Recorded as T1; what was created at the carrier isn't confirmed.
- **2026-11-12** — **Oliver's answers:** send ShipperId 0 (T2), and use `{consignment}` for the tracking link (T5).

## Scar tissue
<!-- Do not change, and why. A constraint someone has already been burned by — a deliberate,
     permanent divergence from the reference approach. -->
- No agent calls CommitShipments, PrintManifest or ProcessCarrierDispatch, on any endpoint — Oliver ("dont do commit calls"); a commit on the shared sandbox closes out everyone's TEST account, and on TCA's live box it manifests real consignments.
- No agent approves a prod gate, and the svc and UI prod deploys go together — prod is held at D1 in the Parcel Portal programme, which also holds G7 (building outside Fuse, Oli Denton). Merging is otherwise free once CI is green and `review-panel` has been run.
- Nothing about an order is defaulted: dimensions, weight and a mapped carrier service must be present before dispatch — the service's own guardrail. T3, I1 and O4 must keep it.
- Dispatch is at-most-once: claim with a lease, reconcile with `DailyShipQuery`, then book. Never retry `ProcessShipment` blindly; void it — the service's own guardrail, and the reason L1 goes through `DeleteShipments` rather than a database edit.
- Nothing is sent to `tca.gfsdeliver.com` by an agent without Harry's own go-ahead, and TCA's credentials are never printed, written to a file or returned in a report. Harry's yes to Oliver on 13 Nov was for Oliver's test.
- Messages to Oliver go from Harry's account and open by saying it is Claude writing on Harry's behalf.
