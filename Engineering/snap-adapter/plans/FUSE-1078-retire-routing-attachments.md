---
ticket: FUSE-1078
title: Retire routing attachments
service: snap-adapter
status: active
created: '2026-09-14'
updated: '2026-10-19'
repo: /home/hjf/code/fuse/snap-adapter
worktree: none
branch: none
base: origin/master
base_sha: 8a73992ea
pr: '276'
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: medium
---
# Retire routing attachments

<!-- MULTI-REPO PLAN. Anchored in snap-adapter; increments span gfs-bifrost/observability
     (monitors), snap-adapter (attachment WRITE removal), and snap-queue-polling-service (attachment
     READ removal). branch/worktree are "none" — no single diff; sign-off gates on increments +
     verification + ACs. The follow-on to the now-complete
     [[../../snap-queue-polling-service/plans/routing-metadata-to-firestore-read-side|read-side plan]]. -->

> SUPERSEDED 2026-10-01 — re-planned after the line-metadata stack shipped (see `## Re-plan 2026-10-01` below). The intent, prerequisites and increments from 2026-09-14 are kept below it as the record.

## Re-plan 2026-10-01
**Goal (Harry):** move Fuse metadata entirely to Firestore; SNAP carries no Fuse routing or line data.

**What changed since 2026-09-14** (all in prod by 2026-10-01, see [[persist-fuse-line-metadata-to-firestore-before-s]]):
- The pre-create Firestore write is **required** for every entity type with a routing key (`569d42b`, #275): a failed write 503s and redelivers; `ROUTING_STORE_REQUIRED` is deleted. Every routed create since 14:07Z on 2026-10-01 has its routing in Firestore or was not created.
- The Shopify line half is already done: the SHL extension attachment and `lineExtensions` writes are gone (#275); goods-out reads `lines[SOLineId]` first (#267).
- **What is left in SNAP:** the routing attachment (SHH `KeyLine 0` for sales orders and work orders, REH for purchase orders and RGAs) written by `writeRoutingMetadata` after every create, and the poller's attachment reads.

**Prod evidence 2026-10-01** (`snap.routing_lookup.*`, daily, last 14 days): `fallback_attachment` fell from thousands per day (pick/pack/good_out/good_in, up to 09-23) to near zero from 09-24: good_out 81, 5, 0, 0, 1, 1, 0, 6; good_in 0-2 per day; pick/pack/RGA 0. (`hit` fell too, from ~22k to ~4k/day for good_out, when the claim precheck stopped re-mapping claimed items.) So the drain is essentially complete; the residue is a handful of long-lived or store-missing orders.

**Why the old gate shape is dropped:** the monitored calendar drain existed because the attachment write kept running and nothing guaranteed a store copy. Both are now false for new orders, so the remaining risk is only the small set of open pre-store orders. Backfilling them to Firestore removes that risk directly and lets the read go without a long wait.

**SNAP traffic effect (estimate):** increment 1 removes one PUT per routed create; increment 4 removes one attachments GET per mapped confirmation per poll across six handlers (roughly 50-100 of the poller's ~1,150 SNAP requests per 20 minutes, ~5-9%).

**Open before increment 4:** `good_in` miss > hit (2026-09-11 observation; a miss broadcasts via manual-origin) — understand it; WOC stuck queue entries — covered by the backfill if they have attachments, otherwise clear them.

## Intent
The read side (FUSE-1078 R1/R1b/R1c) resolves confirmation **routing** and Shopify **line-extensions**
from the Firestore store store-first, with the SNAP **attachment** as fallback — live in prod for
routing. This plan retires the attachment mechanism, **re-sequenced by Harry (2026-09-14)**: build the
per-type gate monitors, **remove the attachment write** first (so new orders carry this data only in
Firestore), lean on the store read, monitor `fallback_attachment → 0` per type as pre-cutover orders
drain, then **remove the attachment read** last. This replaces the old hard 4-week prod-drain gate with
a monitored rollout. Observable proof: no service writes or reads the routing/line-extension attachment,
`snap.routing_lookup` shows only `.hit`/`.miss` (no `.fallback_attachment`), and the SNAP call count per
poll drops for the five despatch/receipt handlers, with no regression to manual-origin broadcast.

## Prerequisites & blockers
<!-- Kept at the top for visibility; the per-increment gate: lines are the machine-checked version. -->
- **[deploy gate] R1c read (#215) + Shopify line-extension store write (#224) must be live in prod**
  before the attachment **write** is removed (increment 2). The attachment carries **both** routing and
  Shopify line-extensions; removing the write with the line-extension store-read/write not yet in prod
  would drop Shopify `fulfillmentId` data (neither attachment nor live store). As of 2026-09-11 both were
  merged but parked — **re-check current prod state first.**
- **[measurement] The per-type retirement-gate monitors (increment 1) must exist** before the drain can
  be judged. They are not in `gfs-bifrost/observability` yet (checked 2026-09-11: `monitors.snap-adapter.tf`
  has no `routing_lookup`/`fallback_attachment` monitor).
- **[soak] Drain window** — the store-write went live in prod ~2026-09-08/10; the PO goods-in tail is the
  longest (working assumption ≥4 weeks). The read removal cannot land until the monitors read
  `fallback_attachment==0` per type.

## Acceptance criteria
- [ ] 1. Per-type retirement-gate monitors exist in `gfs-bifrost/observability`: `fallback_attachment==0
  AND hit>0` per confirmation type (positive control — flat-zero alone can't be told from broken
  instrumentation), scoped `environment:prod`.
- [x] 2. snap-adapter no longer writes the routing/line-extension attachment on order create; new orders
  carry this data only in Firestore (safe because `ROUTING_STORE_REQUIRED` hard-fails the create if the
  store write fails — no order lands with neither attachment nor store entry).
- [ ] 3. As pre-cutover orders drain, `fallback_attachment` trends to 0 per type in prod, evidenced by the
  monitors (with Datadog links recorded here). Manual-origin SNAP orders still broadcast with the
  manual-origin failure event — no change.
- [ ] 4. The poller no longer reads the attachment fallback: `extractRouting` (base/goods-in/RGA) and the
  `fetchShipmentAttachments` calls in pick/pack/WOC/goods-in are deleted, goods-out stops fetching the
  `SHL` attachment, `extensions/routing.ts` is retired (legacy `routing` key tolerated-and-ignored in
  `line-extensions.reader.ts`), the `fallback_attachment` metric is removed, and `CLAUDE.md` + fuse-mcp
  data files are updated. `snap.routing_lookup` then shows only `.hit`/`.miss`.
- [ ] 5. `stock_adjustment` is untouched (its cross-entity migration is FUSE-1181–1185, separate).

## Affected boundaries
Three repos.
- **gfs-bifrost/observability** — `iac/projects/bifrost-observability/monitors.snap-adapter.tf` (new
  per-type `routing_lookup` gate monitors). Metric `snap.routing_lookup.{hit,fallback_attachment,miss}`,
  tagged `type` + `environment`; scope `environment:prod` (**not** `env:` — the sidecar pins
  `env:serverless`). Error is tagged `lane`, not `type`.
- **snap-adapter** (create side, attachment WRITE) — `apps/snap-adapter/src/core/sales-order/attachments/`
  (`shared.ts`, `shopify.ts`), `apps/snap-adapter/src/core/work-order/attachments.ts`. These stamp the
  routing + Shopify line-extension attachments the poller reads as fallback.
- **snap-queue-polling-service** (poller, attachment READ — the former read-side R2) —
  `core/snap/confirmations/despatch-confirmation.handler.base.ts` (`extractRouting`), the pick/pack/WOC/
  goods-in `fetchShipmentAttachments` calls, `goods-out.confirmation-handler.ts` (`SHL`), `extensions/
  routing.ts`, `line-extensions.reader.ts`. See [[../../snap-queue-polling-service/plans/routing-metadata-to-firestore-read-side|the read-side plan]] and
  [[../../snap-queue-polling-service/known-context#Confirmation routing store (FUSE-1078, promoted 2026-09-14)|its promoted known-context]].

## Assumptions & uncertainty
- **Positive-control hole (from the read-side review, 2026-09-11):** in prod only `good_out` and `good_in`
  carry confirmation traffic; `pick`/`pack`/`WOC`/`RGA` had zero prod events in a 7-day window. The gate's
  `hit>0` positive control is therefore unsatisfiable in prod for a no-traffic type. Positive control **is**
  established in dev (pick/pack/good_out/WOC all show hits). Resolve the gate wording: prod
  `fallback_attachment==0` for types with traffic + a dev positive-control for the rest. **UNRESOLVED —
  confirm the intended gate shape before the read removal (increment 4).**
- **WOC stuck queue entries (FUSE-1062 class):** the `work_order_confirmation` gate may be held open by
  entries that re-announce indefinitely; clear or age-exclude them before increment 4 for that type
  (no backfill — Harry, 2026-09-02).
- **Idempotency of the queue-clear** — established as benign for the made side; not load-bearing here.
- **The attachment write removes both data classes at once** — routing (all despatch/receipt types) and
  Shopify line-extensions (`SHL`, goods-out only). The deploy gate above exists because of the second.
- `good_in` prod showed miss (13) > hit (2) over 7d on 2026-09-11 — understand this before removing the
  fallback (a miss already broadcasts via manual-origin; low volume, but not zero).

## Increments
<!-- Re-planned 2026-10-01. Each increment is its own PR off origin/master unless noted. -->
- [x] 1. **snap-adapter — stop writing the routing attachment** for every entity type: delete `writeRoutingMetadata` from `ISnapService`, its five implementations (sales order, purchase order, RGA, work order, master data no-op), `buildRoutingAttachment`, the controller call, the `routing_metadata.*` metrics/events and fixtures; adjust the black-box external-call counts (one fewer PUT on routed creates). — verify: unit, lint, build, harness; dev HJF sales order and purchase order carry no SHH/REH routing TXT attachment and the poller resolves both via `routing_lookup.hit`. No gate: the required pre-create write has been live since `569d42b`. — #276, prod rev snap-adapter-prod-00085-t4m 2026-10-01 15:32Z — done: eabf63b
- [x] 2. **Backfill the residual fallback population to Firestore** (replaces the drain): per business, find open shipments/receipts whose store doc lacks `routing` (and, for Shopify goods-out, lacks `lines`/`lineExtensions`) while the SNAP SHH/REH (and SHL) attachment carries it; write it with a one-off script, dry run first, prod writes confirmed per business. — verify: before/after counts per business; `routing_lookup.fallback_attachment` and `line_extension_lookup.attachment` at 0 for 48h including a PURDYFIGG evening.
      gate: increment 1 in prod
            [x] confirmed 2026-10-01 (eabf63b live 15:32Z)
- [x] 3. **Update the `repair-shopify-confirmation` skill** to diagnose and repair through Firestore `lines` rather than SNAP SHL attachments. Its Case A/B classifier keys on `AttachmentInd: "0"`, which every order created after #275 (2026-10-01 14:07Z) has by design, and after increment 4 an attachment backfill would do nothing. — verify: dry run against one post-cutover PURDYFIGG order and one pre-cutover order. — skill rewritten 2026-10-01 (Firestore `lines` repair via `write_lines.py`; Case B1 = poller's `stored_lines_unmatched`); skills dir is not a git repo, so no sha
- [ ] 4. **snap-queue-polling-service — remove the attachment read:** delete `extractRouting` (despatch base, goods-in, RGA), the `fetchShipmentAttachments` calls in pick/pack/WOC/goods-in/RGA/goods-out, the attachment tier in goods-out line resolution, `extensions/routing.ts`, and the `fallback_attachment` / `line_extension_lookup.attachment` metrics; update `CLAUDE.md` and the fuse-mcp data files. — verify: tests; dev e2e on HJF through the simulator for a routed and a manual-origin confirmation of each lane; prod `routing_lookup` shows only hit/miss; `snap.poll.request` per mapped confirmation drops by one.
      gate: increment 2 shows zero fallbacks for 48h, increment 3 merged, `good_in` miss>hit understood
            [ ] confirmed
- [ ] 5. **observability — alert on the now-fatal write:** a monitor on `snap.entity_not_created{failure_mode:routing_persistence}` and `snap.routing_store.failure` in prod (replaces the 2026-09-14 per-type drain monitors). — verify: `terragrunt plan` shows only the monitor; it reads the live metric. No gate; can go first.

## Increments (2026-09-14 version, superseded)
- (was 1). **observability — build the per-type retirement-gate monitors.** In `monitors.snap-adapter.tf`,
  one monitor per routing-aware confirmation type on `sum(routing_lookup.fallback_attachment{type,environment:prod})==0
  AND sum(routing_lookup.hit{type,environment:prod})>0`, `notify_no_data=false`, scoped `environment:prod`.
  — verify: `terragrunt plan` shows only the new monitors; each exists in Datadog post-apply and reads the
  live metric. No gate — actionable now.
- (was 2). **snap-adapter — remove the attachment WRITE.** Delete the routing/line-extension attachment
  stamping in `core/sales-order/attachments/{shared,shopify}.ts` and `work-order/attachments.ts`; confirm
  `ROUTING_STORE_REQUIRED` remains on so a store-write failure fails the create. — verify: unit/build;
  dev deploy; a new order writes routing + line-ext to Firestore and carries **no** routing/`SHL` attachment;
  the poller resolves it store-first (`routing_lookup.hit`, no `fallback_attachment`) end-to-end.
  gate: R1c read (#215) AND Shopify line-extension store write (#224) live in prod.
        [ ] confirmed
- (was 3). **Drain + monitor.** Watch the increment-1 monitors until `fallback_attachment==0` per type
  (types with prod traffic) over the drain window; record Datadog links here. Clear/age-exclude WOC stuck
  entries. This is a monitored wait, not a code change — it is the gate on increment 4.
  gate: increment 2 live in prod (attachment write stopped).
        [ ] confirmed
- (was 4). **snap-queue-polling-service — remove the attachment READ (former read-side R2).** Delete
  `extractRouting` (base/goods-in/RGA), the `fetchShipmentAttachments` calls in pick/pack/WOC/goods-in,
  the goods-out `SHL` fetch, `extensions/routing.ts` (legacy `routing` key tolerated-and-ignored in
  `line-extensions.reader.ts`), and the `fallback_attachment` metric; update `CLAUDE.md` + fuse-mcp data.
  — verify: tests; dev deploy; routed + manual-origin confirmations both behave; Datadog shows only
  `.hit`/`.miss`; SNAP call count per poll drops for the five handlers.
  gate: increment 1 monitors show `fallback_attachment==0 AND hit>0` per type over the drain window
        (positive control for no-traffic types resolved per Assumptions); WOC stuck entries cleared.
        [ ] confirmed

## Verification
### Evidence
- 2026-10-01 [inc 1] #276 (`393cb90`). Unit 586/586, lint and build:check clean, black-box 9/9 (routed PO 1 SNAP call, routed SO 2). Dev HJF on the branch: SO `HJF35CB1A8C9841` and PO `HJF9A845B03D780` have Firestore `routing` (the SO also has `lines`) and **no** SHH/REH attachment (`GET /v2/attachments/...` → `[]`). Control `HJFF693D5DEFD2A` (master, 13:50) still carries the `{"routing":…}` TXT row. Poller announced pick, pack and good_out at 15:08:07Z: `line_extension_lookup.soline{businessid:hjf}`=2, `routing_lookup.hit` pick 1 and pack 1, `fallback_attachment` 0. (`routing_lookup.*` has no businessid and reports under env:serverless, so prod and dev share it.) Dev reverted to master; queue items cleared.
- 2026-10-01 [inc 3] Repair recipe on dev HJF: SO `HJF7256645431D6` was created via the Shopify channel with no line extensions, so its doc held `routing` only. `write_lines.py` dry run listed both fields. The refusals fired for a key not on SNAP (`3`) and for a gid-form id. `--apply` wrote `lines.`1``/`2` and `routing` survived; a one-line re-run left line 1 intact. A bare `lines.1` mask returns 400. After despatch the poller announced good_out at 15:40:07Z and `line_extension_lookup.soline{businessid:hjf}`=2, with no miss. Queue items cleared.
- 2026-10-05 [sign-off, inc 2 gate] Datadog, from the backfill (2026-10-02T07:42Z) to 2026-10-05 ~19:30Z, about 84h covering the PURDYFIGG evenings of 10-02, 10-03 and 10-04: `snap.routing_lookup.fallback_attachment` and `snap.line_extension_lookup.attachment` have **no points at all**. As a check that the metrics still report: both series had points up to the 10-01 12:00-24:00 bucket (PURDYFIGG `line_extension_lookup.attachment` 89 then 42; `fallback_attachment` good_in/good_out 1-6 per 12h). Meanwhile `routing_lookup.hit` kept reporting through 10-05: good_out 1,775 / 3,284 / 1,364 per day, and pick, pack and RGA too. Over the same window, prod `good_in` had 2 hits and 2 misses (dev 1 hit). Misses elsewhere, all environments: pick 15, and 1 each for good_out, pack and RGA. The zero-fallback result holds in every environment. PURDYFIGG `line_extension_lookup.miss` ran until about 16:00Z on 10-02, then stopped once the 23 line-less orders were repaired through Firestore `lines`. Prod `snap-adapter` runs `prod-eabf63b` (#276). Increment 4 has not started: no PR in `gfs-bifrost/snap-adapter` removes the attachment read, and master `7c436f9` still calls `fetchShipmentAttachments` in the pick, pack, WOC, goods-in, goods-out and RGA handlers. Increment 5 has not started either: `gfs-bifrost/observability`'s `monitors.snap-adapter.tf` has no `routing_store.failure` or `failure_mode:routing_persistence` monitor. The existing "[FUSE][Snap Adapter] Entity creation failed" monitor (`snap.entity_not_created{environment:prod} > 0`) covers the create failure in general.
- 2026-10-02 [inc 2] Prod backfill applied 07:42Z. Script: `plans/FUSE-1078-backfill.py`.
  - Survey: re-run 2026-10-01 19:08-19:19Z across the 14 polled businesses, read-only (517 SNAP calls). It covered 2,210 open shipments, 255 open receipts and 24 queued items.
  - Writes: 142, none failed.
    - Shopify `lineExtensions` added to existing docs: PURDYFIGG 67, SAIRA 21.
    - Routing, creating docs: EPARFUM 37 (35 PO receipts, 2 SOs), BYOMA 12, SPORTLUX 2, WILDSMITH 2, MANUCURIST 1. The MANUCURIST attachment's source is `snap-adapter`, copied verbatim.
  - Pilot: `PURD09124D32FED`, read back through `FirestoreRoutingMetadataReader` with routing and `lineExtensions`.
  - Check: `backfilledBy=fuse-1078-backfill` query returns 142 docs, matching the plan per business.
  - Not backfillable:
    - 307 open orders have routing nowhere (manual-origin, MANUCURIST 163, WILDSMITH 64); step 4 doesn't change them.
    - 23 open PURDYFIGG Shopify orders have no line ids anywhere and need the repair skill.
  - Gate: 48h of zero `fallback_attachment` / `line_extension_lookup.attachment` still to run.
### Not verified
- Increment 4's gate: `good_in` miss > hit is still not understood. In the post-backfill window prod `good_in` has 2 hits and 2 misses (dev: 1 hit), too little traffic to settle it. `routing_lookup.*` does carry an `environment` tag, contrary to the 10-01 inc 1 bullet. Increments 4 and 5 have not started.
- AC 1 and AC 3 still describe the 2026-09-14 per-type drain monitors, which the 2026-10-01 re-plan dropped. They need re-wording to the re-planned gate (backfill plus 48h of zero fallbacks) before they can be ticked. That is the plan owner's call, not a fact to check.
> SUPERSEDED 2026-10-05 — #215 and #224 were both live in prod before increment 1 shipped (see the line-metadata plan's 2026-09-30 assumption check). Increments 1-3 are done. The text below is the 09-14 version.
- Everything. To confirm before increment 2: R1c/#215 + #224 live in prod (re-check — parked 09-11).
- To confirm before increment 4: the positive-control gate shape for no-prod-traffic types; WOC stuck
  entries cleared; the `good_in` miss>hit observation understood.

## Rollout & rollback
- **Order:** monitors (inc 1, ungated) → remove attachment write (inc 2, gated on #215/#224 prod) → drain +
  monitor (inc 3) → remove attachment read (inc 4, gated on the drain). Removing the write **before** the
  read is the point: it makes the store the sole source for new orders, so `fallback_attachment` goes cold
  naturally and the monitors can prove it before the read is deleted.
- **One-way-ish:** removing the attachment write makes new orders depend solely on the Firestore store —
  safe because `ROUTING_STORE_REQUIRED` fails the create if the store write fails (no order with neither).
  Reversible by re-instating the write, but in-flight orders created during a gap would carry no attachment.
- **Rollback:** each increment is `git revert` + re-apply per repo; the read removal (inc 4) is the least
  reversible in effect (re-adding the fallback helps only future orders).
- **Shared state touched:** prod Terraform (observability monitors, snap-adapter, poller); Datadog monitors.
  No topic/DLT deletion. Parked-deploy discipline applies (approve newest run only).
- **Proof in prod:** per type, `routing_lookup.fallback_attachment → 0` while `.hit` continues at the
  pre-cutover rate; SNAP `fetchShipmentAttachments` call rate drops for the five handlers post-inc-4.

## Options considered
- **Chosen — remove write first, monitor, remove read last** (Harry, 2026-09-14). Turns the old hard 4-week
  prod-drain gate into a monitored rollout, and lets the read-side waypoint be "done on merge."
- **Rejected — the original read-side R2** (remove the read fallback gated on a 4-week calendar drain, write
  untouched): kept the attachment write alive, so `fallback_attachment` never went cold on its own and the
  gate was a timer, not a signal.

## Handback
<!-- Append-only, newest first. Written by `wp handback`, never by hand.
     Sign-off never clears this section — a refuted approach is exactly what a
     later session needs and what ## Learnings would have deleted. -->

### 2026-10-01 17:01
- **stopped:** Inc 2 survey paused at 16:00Z 2026-10-01 at Harry's request, during PURDYFIGG's evening create burst; resume in the morning. Script: scratchpad fuse1078_backfill.py (session-only path; copy it out if the session ends). 9 of 14 businesses surveyed, plan files plan_<BIZ>.json: PURDYFIGG 74 writes (Shopify lineExtensions; 23 open Shopify orders have line ids nowhere and need the repair skill), SAIRA 21, EPARFUM 37 (doc creates), BYOMA 12 (doc creates), BABYMORI/CHAMPO/DOCKBAY/KAPPAHL 0. Still to survey: MANUCURIST (killed mid-run), PHLUR, SAMMCK, SPORTLUX, STUBBLE, WILDSMITH. Nothing written to prod. The creds file was deleted, so re-fetch with get-snap-connection. Re-survey PURDYFIGG/SAIRA before applying, since the plans are a snapshot.
- **turn:** me

## Decisions & deviations

- **2026-10-19** — Not a sign-off: #276 merged but inc 4 and 5 remain, so the plan stays active (doctor's UNCLOSED is a false trigger for this multi-PR plan). Gate data for inc 4 (Datadog, prod, snapshot 2026-10-19): routing_lookup.fallback_attachment last seen 2026-10-14 (good_in, 1), and good_out last on 2026-10-08. line_extension_lookup.attachment last seen 2026-10-12. Zero since, while hit kept reporting (701-2464/day). So the 48h zero clause looks met. good_in over 6d: hit 14, miss 6, so miss no longer exceeds hit, but 'understood' still needs a look at those misses. Inc 3 is ticked. Inc 5 (monitor) has no gate.

- **2026-10-01** — Inc 2 backfill design. Scope is the 14 businesses the prod poller polls; the other 16 have no confirmation-enabled connector. Candidates are open shipments and receipts (Stage lt '90') plus every non-STOCK_MOVE outbound-queue item. SNAP attachments are read only when the Firestore doc lacks routing, or lacks lines and lineExtensions on a shopify-sourced shipment. SHL rows are copied verbatim into lineExtensions[Line], not lines[SOLineId]: an exact copy of what the poller reads today, with no SOLineId inference and no partial-order trap. Writes use update masks with an exists/absent precondition, so a re-run on a created doc gets 409, not an overwrite, and each write is stamped backfilledBy=fuse-1078-backfill plus backfilledAt so the set can be found or rolled back. survey (read-only, 1 SNAP call/s) writes a plan file per business; apply writes only that file.

- **2026-10-01** — Inc 1 shipped with no flag or soak: the removed write duplicates the required Firestore write that already gates the create, and the reader has preferred Firestore in prod since 09-24.

- **2026-10-01** — Re-planned (Harry: move entirely to Firestore). The monitored calendar drain is replaced by a backfill of the residual pre-store orders, because the required pre-create write (569d42b) guarantees new routed orders are in Firestore and prod fallback_attachment has been ~0-6/day since 09-24. Added: stop the routing attachment write for every entity type first; update repair-shopify-confirmation (its AttachmentInd classifier is invalid for orders created after #275); remove the poller read last; replace the drain monitors with an alert on routing_persistence create failures.
- **2026-09-14 — split out of the read-side plan at its sign-off.** The read-side waypoint (R1/R1b/R1c)
  signed off on merge; R2 + the monitor-build + the post-retirement no-attachment AC moved here, and the
  attachment-**write** removal (snap-adapter) was added as the new leading step. Ticket stays FUSE-1078
  (umbrella); a dedicated ticket may be warranted if this is scheduled as its own unit of work.

## Learnings
<!-- Durable facts surfaced while working this plan. Promote at sign-off, then clear. -->
