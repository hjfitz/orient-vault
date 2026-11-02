---
title: Tracking Service — Migration State
programme: tracking-service
status: active
owner: Harry Fitzgerald
services:
- tracking-service
- fuse-ui
- observability
created: '2026-10-05'
updated: '2026-10-15'
tags:
- bifrost
- migration-state
---
# Tracking Service — Migration State

> Backfilled 2026-10-07 from git history, the productionisation plan and the working session, once the
> work had already been running for three days. Every ✅ below is merged and, where it says so, live in
> prod. Nothing here is a plan that hasn't been checked against real history.

Narrative and verdict: [[Bifrost/Tracking Service/Overview|Overview]]

**Repos:** `~/code/fuse/tracking-service` (Go API in `apps/api`, retiring Next UI in `apps/web`, Terraform in `iac/`),
`~/code/fuse/fuse-ui` (the order tracker page), `~/code/fuse/observability` (dashboard and monitors).
**Plan of record:** `tracking-service/docs/productionisation.md`. **Cutover runbook:** `docs/cutover.md`.

## Unit status
Legend: ⬜ not started · 🟨 in progress · ✅ merged · ⛔ blocked · ⏸ deferred · ❌ dropped · 🔄 rescoped

### A. Skunkworks build (2026-10-05 → 10-06, live in prod on the legacy `fuse-tracker` stack)
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **A1** | ✅ | Shipments tracked through the pipeline | | none | | | Go API consuming the create and confirmation topics, keyed on businessId + customer ref, republishes folded by content hash. `acce5c4`, `32dee64`. |
| **A2** | ✅ | Support views, Insights, notes | A1 | none | | | Already-in-Fuse, needs attention, lines, bulk lookup, export, channel and action timeline, UK times, esm.fuse.* domain. `b1caf03`, `bbbaaa0`, `c3ac26e`. |
| **A3** | ✅ | Returns (RGAs) and their confirmations | A1 | none | | | `e49cee7`. Parallel record type over shared reducer helpers. |
| **A4** | ✅ | Read-only MCP server and agent notes | A1 | none | | | `8d1d62c`. Stays standalone; folding it into the hosted Fuse MCP is on hold. |
| **A5** | ✅ | Hidden order tracker page in fuse-ui | A1 | none | | #287 | Behind `FEATURE_FLAG_ORDER_TRACKER`, on in dev and prod. Server-side calls with a Google ID token to the private API. |

### B. Productionise as tracking-service (plan: `docs/productionisation.md`)
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **B1** | ✅ | Rename, new stack, new Firestore DB | A1 | high | opus/high | | `9de667a` on `main`. Code and Terraform only: plans are 183/0/0 per env and **nothing is applied**. `DEV_STACK`/`PROD_STACK` still default to `fuse-tracker`. 20 subscriptions, no TTL, indexes from `firestore.indexes.json`. |
| **B2** | ✅ | Cutover, dev | B1 | high | opus/high | | Done 2026-10-14: held apply, export/import, dry-run backfill (0 to rewrite), unhold, dead-lettering on, parity checked. |
| **B3** | ✅ | Cutover, prod | B2 | high | opus/high | tracking-service#5 #6 | Done 2026-10-14: 131,001 docs migrated, hold released 21:50Z, dead-lettering on; 7-day stats and 258 sampled shipments identical. fuse-ui repointed 2026-10-15 (fuse-ui#327). |
| **B4** | ✅ | Destroy the legacy stack | B3 | med | sonnet/medium | tracking-service#7 #8, fuse-ui#327 | 2026-10-15: DB out of state (#7), legacy stack destroyed in both envs (27 resources each), fuse-mcp redeployed onto tracking-service. Old `fuse-tracker` databases deleted 2026-10-15 on Harry's call (exports kept in the migration buckets, 30-day expiry). Legacy files and the stack picker removed (#8); migration buckets emptied and switched off (#9). Nothing left. |
| **B5** | ✅ | Repo standards and CI | B1 | low | sonnet/medium | tracking-service#14 | Done 2026-10-15: branch protection on main (8 required checks, no required review, matching sibling repos), `bifrost-admins` granted admin for CODEOWNERS, PR template from org `.github`; Renovate is the central runner (npm-only, nothing to add for a Go repo). |
| **B6** | ✅ | Datadog sidecar, `fuse.tracking.*` metrics, dead letters | B1 | med | | | In `9de667a`: serverless-init sidecar, ingest/lag/stage/attention/orphan metrics, a DLT and holding pull sub per subscription, `cmd/redrive`. **Only takes effect once the new stack is live.** |
| **B7** | ✅ | Dashboard and monitors in the observability repo | B6 | low | sonnet/medium | observability#70 #71 | Done 2026-10-15: dashboard `ut4-puv-cv7`, 10 monitors, percentile configs. The >30m backlog page is a composite gated on hold mode; both inputs grouped by `subscription_id` (#71) after the first cut sat in No Data. Proven with throwaway monitors. |
| **B8** | ✅ | Platform registration | B3 | low | sonnet/medium | fuse-mcp 2aa2f78 2ac01e5 | Done 2026-10-15: fuse-mcp data files (services, endpoints, collections, topology, dependencies, deployment) + parity-accept; goods-out made recordType corrected to `goods_out_confirmation` (verified live). Waypoint onboarded. Confluence: service page 331776001, changelog 331251735 (monthly children), mapping added to create-pr. |
| **B9** | ✅ | Retire compatibility paths | B3 | med | sonnet/medium | tracking-service#11 | Done 2026-10-15: v1–3 upgrade paths and the `delivered` stats remap removed after checking every stored shipment ≥ v5 and no stats doc holds `delivered` (dev 57, prod 113 docs). |
| **B10** | ✅ | Contract drift check | B3 | low | sonnet/low | fuse-ui#330 | Done 2026-10-15: non-required `Tracker Contract` workflow (PRs touching the client + weekday 07:00 UTC). Reads tracking-service with org `GH_TOKEN` (Harry's PAT) — on the PAT-retirement list. |
| **B11** | ✅ | Cleanup | B3 | low | sonnet/low | tracking-service#12 | Done 2026-10-15: dead spec link fixed, done items marked in productionisation.md. `apps/` → `code/` move remains (with B13). |
| **B12** | ⏸ | snap-adapter: name the record in the confirmation-withheld warning | | low | sonnet/low | | Offered, not answered. Today a withheld return can't be traced from Datadog without walking the create path. |
| **B13** | ⏸ | Retire the standalone UI (`apps/web`) | B3 | med | sonnet/medium | | Later, once fuse-ui covers it: remove the Cloud Run service, LB, cert, DNS (esm.fuse.*) and `AUTH_PASSWORD`, then move `apps/api` to `code/`. |

### C. Support tooling: the order tracker as an L2 work queue (2026-10-07)
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **C1** | ✅ | First feedback round: one definition per number, attention lanes | A5 | med | opus/high | #289 | Tracker API `53bee46`, `20b9d2f`, `e17d9b9`, `0585898`. Failed counts a record once on its first failure (the 76 vs 15 was one Saira order rejected 57 times). Needs action vs Running late, overdue means past the end of the next London working day, attempts and age from the first failure. Prod stats rebuilt with ingest held. |
| **C2** | ✅ | Tracker moves out of Central Admin | C1 | low | sonnet/medium | #290 | `/order-tracker`, own layout, top-nav entry behind the flag; the old URL redirects (308) with its query string. |
| **C3** | ✅ | App-wide header on phones, dark-mode wordmark | C2 | low | sonnet/medium | #291 | The header overflowed by 438px at 390px on every page. The existing ILG logo is inlined with its navy letters following the text colour. |
| **C4** | ✅ | API additions for the work queue | C1 | med | opus/medium | | Tracker API `1401bac`: `GET /stats/businesses`, `firstSeen`/`lastSeen`/`byBusiness` on failure reasons, `lastNote` on rows. No new indexes. |
| **C5** | ✅ | L2 work queue | C2, C4 | med | opus/high | #292 | Needs action grouped by customer, today per customer, recurring failures, What to do, held duplicates, Orders in flight on the customer page. Every failed record links to its retry-queue item and to Transaction History. Live in prod (`d6fc38c`). |
| **C6** | ✅ | Per-connector confirmation status | C4 | med | opus/high | tracking-service#10 | Done 2026-10-15: ported from the uncommitted 10-07 work; ledger v6 shipments / v3 returns, pre-C6 docs seeded on read with one `unknown` connector; no backfill needed. Verified in dev (made to A, failed on B → action lane; later made to B clears it). |
| **C7** | ✅ | Order tracker UX-review fixes | C5 | low | sonnet/medium | fuse-ui#331 #332, tracking-service#13 | Done 2026-10-15: items 1, 3–16, 18 + three minors (#331); per-connector breakdown on list dots and the sheet, hidden for seeded-`unknown`-only records (#332); item 4's summary keeps the failing field for new failures (tracking-service#13). |
| **C8** | ✅ | Sort by date and date windows | B3, C5 | low | sonnet/medium | fuse-ui#329 | Done 2026-10-15: sort by last activity / received + date windows; all 8 `createdAt` indexes READY in both databases. Squash commit kept the WIP subject (noted on the PR). |

## Gates
- [x] **G1 — Harry signs off the cutover plan** (2026-10-14: Harry handed the cutover over to run autonomously) — blocks B2, B3, B4. One-way door. The review pack: new-stack plans 183/0/0 per env, legacy stack plan unchanged, observability plan, and `docs/cutover.md`. Not yet shared.
- [x] **G2 — Cutover complete (B3 merged)** (2026-10-14) — blocks B7, B9, C8. Date sorting needs the new database's indexes, the observability PR needs the metrics to exist, and the compat paths can only go after the backfill.

## Risks
- **R1 ★ Zero-loss cutover** — ingest is held so the new subscriptions build a backlog, and event ids are Pub/Sub message ids (the same on every subscription), so replay is idempotent. The hold drained in ~12 minutes on both envs — closed 2026-10-14.
- **R2 ★ New indexes exist only in the new database** — anything that needs one (date sorts, windows) must not ship against the legacy stack. Default queries and the lane filters use the existing indexes — standing.
- **R3 Metrics that don't exist yet** — percentile tag configs for `fuse.tracking.*` can't be created before the new stack emits them, configured after cutover in B7 — closed 2026-10-15.
- **R4 Per-connector failure rule** — a delivery that names no connector clears every connector's earlier failure, because fan-out publishes the made message without one. A single connector behaves exactly as before — accepted and shipped with C6, 2026-10-15.
- **R5 Held-duplicate links** — the deduper keys a held order on its own id, which can differ from the customer reference. The link is matched on exact references so it is absent rather than wrong — standing.
- **R6 Tracker page verified without sign-in** — the page was checked against prod data and locally, never signed in by an agent. Jack signed in and verified the first round. Later releases haven't had that second pair of eyes — open.

## Decision log
- **2026-10-15** — Harry: finish everything without human interaction. Read as the C6 ship decision. Cutover finished (legacy stack, databases, migration buckets and files gone); B5–B11 and C6–C8 shipped by parallel agents. B12/B13 stay paused. The 2026-10-09 429s were a 3×80 instance cap hit under slow stats-document transactions; no config change, since more instances would contend on the same hot documents.
- **2026-10-07** — Per-connector confirmation status: a record stays failed (and in Needs action) while any connector's latest outcome is a failure with no later delivery to that connector. A made with no connector clears all earlier failures (R4). Harry approved building it.
- **2026-10-07** — The tracker is the L2 team's work queue: every failed record links to its retry-queue item and to Transaction History. The retry-queue link is left out when no matching failure is found, because the Exceptions page opens a failure only by id. Harry asked for this explicitly.
- **2026-10-07** — The order tracker leaves Central Admin for `/order-tracker`. The nav entry follows `FEATURE_FLAG_ORDER_TRACKER`, which is on in prod, so everyone using fuse-ui sees it. Harry asked for the move.
- **2026-10-07** — Overdue despatch means not despatched by the end of the next London working day (Mon–Fri) after reaching the WMS. `dueOut` no longer drives attention; ops don't work to it. Jack's call, built as `DESPATCH_CUTOFF`.
- **2026-10-07** — One definition per number: a record is counted once, on its first failure of each kind. The stored counters were recounted with ingest held, and reason codes are re-filed under today's families when read.
- **2026-10-07** — Productionisation agreed: name `tracking-service`, a new Firestore database kept forever (no TTL), zero-loss cutover, Datadog and dead letters, CI emulator job. Not doing: a load test, a server cache, PII work (later, in the fuse-ui BFF), folding the MCP into the hosted Fuse MCP (on hold).
- **2026-10-06** — Despatch is two-step (`none` → `reported` → `confirmed`, or `confirmation_failed`). `delivered` is reserved for carrier proof of delivery, which doesn't exist yet.
- **2026-10-06** — Goods-out `confirmation_made` is `goods_out_confirmation` from every producer; the `sales_order` route is dead.
- **2026-10-05** — Identity is businessId + customer reference (returns: the RGA number). Support searches by it and it rides unchanged through Snap onto every confirmation.

## Scar tissue
- **Identity is businessId + customer reference** — the derived Snap ShipmentId is display and search only, never a join key.
- **Count a record once, on its first failure** — counting each flip of a derived flag turned one Saira order into 57 failures and the headline into 76 against 15. Never count a flip.
- **A human runs `recompute-stats` and the backfills against prod, never an agent** — dry-run first, with ingest held. This was broken on 2026-10-07 (three runs, each with a dry run and ingest held) and is recorded here so it isn't repeated.
- **Recompute must diff every counter, reason code and duration bucket** — it once skipped a day whose totals already matched, and stale per-business reason codes survived (`0585898`).
- **Lane-filtered attention pages must read on until the page is full** — the attention query is ordered oldest-due first and the lane filter ran after each page, so Running late came back empty behind older failures (`e17d9b9`).
- **Don't push to `main` while a Deploy run is in flight** — a push cancelled the image jobs in both runs.
- **Approving the fuse-ui prod gate ships everything on `main` since the live sha** — check `git log` first and cancel older parked runs afterwards.
- **A failed lookup is never "no failure"** — cross-service lookups degrade by omitting the link, never by counting zero.
