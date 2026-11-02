---
ticket: FUSE-1147
title: Stop re-PUTting live shipments (slot-timeout masking, already-in-WMS, read-before-write)
service: snap-adapter
status: complete
created: '2026-09-04'
updated: '2026-09-14'
repo: /home/hjf/code/fuse/snap-adapter
worktrees:
- .claude/worktrees/snap-slot-timeout-metrics-guard
- .claude/worktrees/fuse-1147-already-in-wms
- .claude/worktrees/fuse-1147-shipment-precheck
prs:
- '216'
- '217'
- '218'
base: origin/master
base_sha: 95bdc57
tags:
- waypoint
- plan
pr: '218'
---
# FUSE-1147 — stop re-PUTting live shipments

> Plan approved by Harry 2026-09-04 ~11:20 BST (session plan file). This is the vault copy; the
> **Progress** section below is the live ledger.

## Progress (newest first)
- **2026-09-04 12:2x BST** — Dev e2e on stack tip `a239cb3` (rev 00470), GADG `FUSE1147-E2E-1` →
  `GADG2002B8FED5A`: fresh create ✅ (corr `4d9d2b0c`); Stage-00 modify resend ✅ second PUT, LineValue
  16 (corr `f543f3c9`); SNAP auto-allocated to 11; resend → `already_in_wms` via precheck, ack, hold
  intact, SNAP untouched ✅ (corr `12096dac`); manual adapter-shaped re-PUT at Stage 11 → **HTTP 500 NRE
  and the line Price moved 16→17** (partial write — the prod side-effect class in miniature); cancelled
  via `PATCH Status 01` (needs BizId+OwnerId+Site+Warehouse in the body) → resend (corr `89c91303`) →
  `cancelled_in_wms`, 204, no failure publish, no ack, hold intact, SNAP untouched ✅. **#217/#218 dev-verified;
  #216 still unit-only pending the slot-timeout injection.**
- **2026-09-04 12:1x BST** — #216 ← #217 ← #218 restacked; all three drafts; changelog rows v49–51;
  Jira comments. #216 dev e2e (slot-timeout injection) **blocked**: classifier denied
  `gcloud run services update … SNAP_SLOT_ACQUIRE_TIMEOUT_MS=1`; Harry to run or grant.
- **2026-09-04 11:4x BST** — FUSE-1147 filed (Bug, Ready for Refinement; Relates 984/1085).

## Follow-ups not in the PRs
- Config levers (Harry): write concurrency 5→1–2, slot timeout, Cloud Run caps.
- `fuse-mcp` mocker tools (`mock-generate`, `mock-activity`, likely `mock-send`/`mock-load-run`) 404
  against fuse-mocker's Go API — stale paths; verified 2026-09-04. Verification routed via `submit-to-fuse`.
- Work-order adopts the precheck; PO/RGA need a receipt stage table.
- Datadog monitors: `failureMode:unexpected` any count; `cancelled_in_wms`; dedupe loop detector.
- Replay inbox: mark/purge ~4,000 P&F `Invalid Order Stage` entries — never redrive.
- Ops sweep of P&F shipments below Stage 70 with ≥1 500 re-PUT for doubled kit lines.

---

## Context

Every evening since Purdy & Figg's go-live (1–3 Sep 2026), snap-adapter fails PURDYFIGG sales-order
creates in a 5-minute loop for up to 3 hours per order (Wed: 150 failures / 10 orders; Thu: 517 / 40).
Diagnosed 2026-09-04 (see memory `project_purdyfigg_reput_loop_kit_duplication`). The chain:

1. A burst of ~40 orders lands in one Shopify bulk tick while SNAP's write path is slow (PUT latency
   7–37 s avg under 10–15 concurrent creates; reads on the same host stayed at 100–200 ms). The
   per-host `Semaphore(5)` slot wait (30 s) times out for the tail: `SemaphoreAcquireTimeoutError`,
   thrown from a request interceptor **before any request is sent**.
2. `observability/axios-metrics.ts` `getRequestStart()` reads `config.requestStart` on an undefined
   config (the semaphore error has no `config`/`response`) → `TypeError: Cannot read properties of
   undefined (reading 'requestStart')`, **masking** the semaphore error.
3. `classifySnapFailure` already maps `SemaphoreAcquireTimeoutError` → `slot_timeout`, `transient: true`
   (503 → Pub/Sub backoff, deduper intact). It never sees it; the TypeError falls to `unexpected`,
   `transient: false` → `handleSnapFailure` publishes `release_sales_order` + `create_data_failure`.
4. dedupe-service's release route hard-deletes the held record. The next bulk tick re-collects the
   order (still unfulfilled + tagged + inside the 3 h window) and dedupe promotes it as new.
5. The re-PUT hits a shipment SNAP already holds. SNAP's segmented upsert answers
   `HEADER_POST SUCCEEDED / LINE_UPDATE: Invalid Order Stage` (400) once the shipment has left Stage 00,
   or a 500 null-reference mid-write. Both are classified permanent → step 3–4 again.
6. Side effects of the re-PUTs: the keyed PUT replaces children, wiping the SHH routing attachment
   (→ `goods_out_confirmation: no originating connector` in the replay inbox), and the 500 writes
   duplicate kit-component explosions on live shipments (FG1208D_V2 has 10 components;
   PURD3814090866D shipped with 30 lines). Duplication tracks the 500s, not the 400s.

`Invalid Order Stage` means the shipment exists and the warehouse is working it (SNAP `SHIPSTAGE`:
00 Due Out, 10/11 Allocate(d), 20–29 Pick(ed), 30–39 Pack(ed), 40–49 Marshall(ed), 50 Final Check,
60–69 Load(ed), 70 Shipped, 90 Fulfilled, 91 Cancelled, 99 Purged). Treating it as a create failure,
and clearing the deduper on it, is the wrong model: "we failed" is not "SNAP does not have it".

FUSE-984 (deterministic ids) and FUSE-1085 (500 classification) are live and working. The Firestore
routing stack (#209–#215) covers only the confirmation-routing loss. Config levers (concurrency,
slot timeout, Cloud Run caps) are deliberately out of scope here — revisit separately.

## Goal

Four code changes in snap-adapter (plus a narrow dedupe-side change), ordered so each one is
shippable alone and the first two are safe to ship today:

- **C1** null-guard the metrics interceptor so a slot timeout nacks as designed (un-arms the loop).
- **C2** read-before-write in the sales-order create path, branching on SNAP `Stage` so an order
  already in the warehouse is acknowledged, never re-PUT.
- **C3** classify `Invalid Order Stage` as "already in WMS" → acknowledge, no release (belt to C2's
  braces; also covers the race where the shipment appears between GET and PUT).
- **C4** make dedupe release conditional on failures that mean "not in WMS".

## Decisions taken (Harry, 2026-09-04)

- **Already-in-WMS outcome publishes `create_acknowledge`** (the existing `EntityAcknowledgeService`),
  so downstream sees the record acknowledged and the dedupe hold stays. dedupe-service stores the
  record *before* forwarding it (`saveAndDuplicateCheck` upsert, then publish), and does not subscribe
  to `create_acknowledge`, so **no dedupe-service change is needed** for the hold to survive — the
  loop is broken purely by snap-adapter not publishing `release_*`/`create_data_failure`.
- **Only Stage `00` (Due Out) is writable.** Anything the warehouse has started (`10` onward) is
  read-only from Fuse. `91` Cancelled / `99` Purged / header `Status "01"` are terminal, never
  released.
- **Three PRs, all off `origin/master`, sales orders only this round:** C1 (null guard, ships today)
  → C3 (classify `Invalid Order Stage` as already-in-WMS; ends the current loop shape within one
  cycle) → C2 (read-before-write; removes the harmful PUT entirely). C3 before C2 because C3 is the
  safety net for C2's GET→PUT race and is the smaller change. PO/RGA/WO adopt C2's seam later.
- **C4 (dedupe release semantics) is dropped as a separate change** — see first bullet.

## Empirical facts fixed during planning

- `GET /v2/shipments/{id}` for a missing id on ilg005 (P&F prod) returns **HTTP 200** with body
  `{"Status":"Error","Message":"No matching entity"}` — shape (b) below. Design still tolerates
  (a) a real 404 `AxiosError` and (c) `Status:"Success", Results: []`.
- `SnapShipment.Stage` and `.Status` are `string | null | undefined`; no Stage enum exists in
  `@gfs-bifrost/snap` or the app.
- A failed **GET** is deliberately left as a bare `AxiosError` by `handleEntityCreationErrors`
  (`axios-metrics.ts:90-113`; spec `axios-metrics.spec.ts:22-26`); `classifySnapFailure`'s bare
  `AxiosError` branch (`classify-snap-failure.ts:296`) makes it `snap_api_error`, transient per status.

## Design principle

"Already in WMS" is expressed as a **thrown, typed state**, not a new return type. `ISnapService.createInSnap`
stays `Promise<string>` (5 implementers + fixture + ~15 controller stubs untouched). The sales-order
service throws `SnapEntityStateException`; `classifySnapFailure` maps it (C2) and the 400 signature (C3)
onto the same new mode `already_in_wms`; `handleSnapFailure` gets one third path for both detection
routes. PO/RGA/WO adopt later by adding the precheck + throw in their own `createInSnap`.

Prerequisite: a FUSE ticket (defect) for the branch name — create via `create-defect` or Harry supplies.
Each PR: own worktree `~/code/fuse/snap-adapter/.claude/worktrees/<slug>` from `origin/master`, deps
installed inside it; `pnpm run lint:fix`, `pnpm run build:check`, `pnpm run build:check:tests`,
`pnpm test` in `apps/snap-adapter`; no ticket numbers in code comments.

## Increments

Three stacked PRs, all merged to `origin/master` and deployed to prod (running revision
`snap-adapter-prod-00076`, sha `2c3659a2`). Merge order was C1 → C3 → C2.

- [x] **C1 — null-guard the metrics interceptor so a pre-dispatch error nacks as designed** (PR #216, merged 2026-09-07)
  — done: d4f048d358d45b664ec7efc31ad64e1a25cd5fd1
- [x] **C3 — `already_in_wms` failure mode + controller third path (classify Invalid Order Stage)** (PR #217, merged 2026-09-10)
  — done: 05a7545708a63166c1d09b764b9b6a8c3db273e8
- [x] **C2 — read-before-write on sales orders (precheck + `SnapEntityStateException`)** (PR #218, merged 2026-09-10)
  — done: 2c3659a232f28a55e5d96c9608e856c9ef9e48cc

---

## PR1 — C1: stop the metrics interceptor masking pre-dispatch errors (~120 lines, ships today)

**`apps/snap-adapter/src/observability/axios-metrics.ts`**
- `getRequestStart(...configs)`: `config?.requestStart` (guard like `removeRequestStart` already does).
- `responseFailureMetricInterceptor(error)`: early `return Promise.reject(error)` when
  `!error?.config && !error?.response` — the request never left the process (slot timeout, open breaker),
  so no `snap.request.failure{snap_host:unknown}`, no bogus latency, no "Unable to find request start
  time" warn per timed-out message. Fix the unguarded `error.response?.config` on the last
  `removeRequestStart` call while there. Both `SemaphoreAcquireTimeoutError` (axios.builder.ts:36-38)
  and `SnapCircuitOpenException` (customer.http-router.ts:109-114) are request-interceptor rejections
  and hit this handler with no config — C1 fixes both.

**Tests**
- `observability/__test__/axios-metrics.spec.ts` (spy `SnapRecorder.prototype.requestFailed`):
  `describe("responseFailureMetricInterceptor with a SemaphoreAcquireTimeoutError (no config, no response)")`
  → `it("rejects with the original error instance")`, `it("does not wrap it in an EntityCreationException")`,
  `it("does not record a request failure")`; same first `it` for `SnapCircuitOpenException`;
  `describe("… PUT AxiosError whose config carries no requestStart")` → `it("still rejects with an
  EntityCreationException")`; `describe("… GET AxiosError")` → `it("rejects with the bare AxiosError")`
  (pins the behaviour C2 relies on).
- `http/__tests__/event.controller.spec.ts`, mirroring the existing "fails transiently (5xx)" block with
  `createInSnap.mockRejectedValue(new SemaphoreAcquireTimeoutError(30_000))`:
  `describe("when the concurrency slot times out before the request is sent")` → `it("should return 503
  so Pub/Sub redelivers with backoff")`, `it("should not release the event from the deduper")`,
  `it("should not publish to the create-data-failure topic")`, `it("should not publish a
  create-acknowledge event")`.
- Classify spec unchanged (`slot_timeout` already covered at lines 630-640).

---

## PR2 — C3: `already_in_wms` mode + controller third path (~400 lines)

**`observability/snap-failure.type.ts`**: add `"already_in_wms"` to `SnapFailureMode`; add optional
`detail.resourceId?: string; detail.stage?: string` (populated by PR3).

**`observability/classify-snap-failure.ts`**: `isAlreadyInWmsRejection(status, errors)` = `status === 400`
and every field error is `column:"XDoc"`, `error:"Invalid Order Stage"` (don't require the segment — a
HEADER_POST variant should still match). Apply in both `snap_api_error` builders (the
`EntityCreationException` branch ~line 199 and the bare `AxiosError` branch ~line 298):
`mode = isAlreadyInWmsRejection(...) ? "already_in_wms" : "snap_api_error"`, `transient: false` for
the new mode. A mixed rejection (Invalid Order Stage + any other error) stays `snap_api_error`. No
`cancelled` signature here — no SNAP 400 body evidence exists yet.

**`adapters/pubsub/to-bifrost-failure.ts`**: `case "already_in_wms"` → non-retryable `dependency`
error, code `snap-adapter.${entityType}.already_in_wms` (never published in practice; must not fall
to the `default` → infrastructure arm).

**`observability/snap-metric.type.ts` / `snap.recorder.ts`**: new metric `entity_already_in_wms`
(→ `snap.entity_already_in_wms{detected_by: precheck|write_rejection}`), new tag `detected_by`,
recorder method `entityAlreadyInWms(resourceId, entityType, detectedBy, stage?)` logging
`"Entity already exists in SNAP; acknowledged without writing"` at info, audience support.
Deliberately **not** `entity_not_created` — it isn't a failure and must not trip failure monitors.

**`http/controllers/event.controller.ts` `handleSnapFailure`**: first thing after
`classifySnapFailure(err)`: `if (failure.mode === "already_in_wms") return this.acknowledgeAlreadyInWms(...)`
→ recorder call, one info log (mode, statusCode, stage, fieldErrors), `entityAcknowledgeService.publish
(entityType, message)`, return `{...failure, transient:false}` (→ 204). No release, no
`create_data_failure`. Attachments/routing are skipped because the throw happens inside `createInSnap`
(before controller lines 357-365).

**Tests**
- `classify-snap-failure.spec.ts`: `describe("AxiosError with a 400 whose only field errors are XDoc
  Invalid Order Stage (real re-PUT shape)")` using the verbatim prod body (`Message:"Successes: 0/1"`,
  `Results[0].Errors` = LINE_UPDATE XDoc error + HEADER_POST/ADDRESS_UPDATE/CONTACT_UPDATE `SUCCEEDED`)
  → `it("classifies the mode as already_in_wms")`, `it("is not transient — the shipment is live,
  redelivery would only rewrite it")`, `it("still records the LINE_UPDATE field error for the log")`;
  same 400 wrapped in `EntityCreationException` → `it("classifies the mode as already_in_wms")`;
  mixed 400 → `it("stays snap_api_error — a mixed rejection is a real rejection")`; 500 carrying the
  field error → `it("stays snap_api_error — only a 400 carries the already-in-WMS signature")`.
- `to-bifrost-failure.spec.ts`: `it("maps already_in_wms to a non-retryable snap dependency error, not
  infrastructure")`.
- `event.controller.spec.ts`: `describe("when SNAP rejects the re-PUT with Invalid Order Stage (400) —
  shipment already live")` (`createInSnap.mockRejectedValue(new AxiosError(... status 400, data: body))`,
  `hasAttachments.mockReturnValue(true)`) → `it("should return 204 No Content status")`, `it("should
  not release the event from the deduper")`, `it("should not publish to the create-data-failure topic")`,
  `it("should publish a create-acknowledge event so downstream sees the record accepted")`, `it("should
  not write attachments")`, `it("should not write routing metadata")`.

---

## PR3 — C2: read-before-write on sales orders (~500 lines, stacked on PR2)

**New `exceptions/snap-entity-state.exception.ts`** (export from `exceptions/index.ts`):
`SnapEntityState = "already_in_wms" | "cancelled_in_wms"`;
`SnapEntityStateException(state, entityType, resourceId, stage?, status?)`.

**New `adapters/snap/fetch-snap-entity.ts`**: `fetchSnapEntity<T>(client, url): Promise<T | undefined>` —
`undefined` for all three not-found shapes: HTTP 404 `AxiosError`; 2xx `{Status:"Error"}` (the real one
on ilg005: `Message:"No matching entity"`; any other `Status:"Error"` message also → `undefined` but
with a warn so new messages surface in dev); 2xx `Status:"Success"` with empty `Results`. Any other
transport failure rethrows the bare `AxiosError` (→ classifier bare-AxiosError branch → transient per
status → 503).

**New `adapters/snap/shipment-stage.ts`**: `SHIPMENT_STAGE = { DUE_OUT:"00", CANCELLED:"91", PURGED:"99" }`,
`SHIPMENT_STATUS = { ACTIVE:"00", CANCELLED:"01" }`, `classifyShipmentForWrite(shipment) →
"writable" | "in_progress" | "cancelled"`: Status 01 or Stage 91/99 → cancelled; Stage 00 → writable;
anything else, including a missing Stage on an existing shipment → in_progress.

**`core/sales-order/sales-order.service.ts`**
- `createInSnap`: resolve client → `fetchSnapEntity<SnapShipment>(client, `/v2/shipments/${data.ShipmentId}`)`
  → if found and not `writable`, throw `SnapEntityStateException(cancelled ? "cancelled_in_wms" :
  "already_in_wms", SnapEntities.SALES_ORDER, data.ShipmentId, Stage, Status)` → else existing PUT
  unchanged. One `why` comment: a keyed PUT replaces the shipment's children, so never rewrite one the
  warehouse has started; the deterministic id makes a redelivery or re-collected order land on the same id.
- `getLineAttachments` (361-385): use `fetchSnapEntity` too; `undefined` → existing
  `SnapException.AttachmentCreationError`; fixes the latent `Results?.[0].ShipmentLines` TypeError.

**Classifier / types / failure mapper**: add `"cancelled_in_wms"` to `SnapFailureMode`; classifier branch
for `SnapEntityStateException` (before the `SemaphoreAcquireTimeoutError` check): `mode: err.state`,
`transient:false`, `detail {message, entityType, resourceId, stage}`; `to-bifrost-failure` case for
`cancelled_in_wms`.

**Controller `cancelled_in_wms` path**: after the error log + `entityNotCreated` and before the transient
check: `return {...failure, transient:false}` — **no release, no `create_data_failure`, no ack**. Decided
here (not open): dedupe's `create_data_failure_sales_order.v2.sub` → `/events/v2/record/release/sales_order`
deletes the hold, so publishing the failure would restart the re-collect loop against a cancelled
shipment. Visibility comes from `snap.entity_not_created{failure_mode:cancelled_in_wms}` + the error log;
add a Datadog monitor on it (observability repo) as a follow-up.

**Tests**
- New `adapters/snap/__test__/fetch-snap-entity.spec.ts`: 404 → undefined; `Status:"Error" No matching
  entity` → undefined; `Success` + empty Results → undefined; one result → first result; 503 → rethrows
  the AxiosError unchanged; no-response network error → rethrows unchanged.
- New `adapters/snap/__test__/shipment-stage.spec.ts`: `it.each` over `00→writable`, `10/21/70/90→
  in_progress`, `91/99→cancelled`, `undefined→in_progress`; `it("classifies header Status 01 as
  cancelled even at stage 00")`.
- `core/sales-order/__test__/sales-order.service.spec.ts` (add a `fetchShipment(overrides)` helper beside
  `fetchSuccess`): scenario describes for absent (404 / Status Error / empty Results) → PUTs; Stage 00 →
  PUTs (modify-via-resend preserved); Stage 21 → does not PUT, throws `SnapEntityStateException`,
  state `already_in_wms`, carries the stage; Stage 91 / 99 / Status 01 → `cancelled_in_wms`; lookup 503 →
  does not PUT, propagates unchanged; existing "no compensating delete / propagates the SNAP rejection"
  tests move under "when Snap rejects the PUT for an absent shipment" with `get` resolving empty Results;
  `handleAttachments`: `it("throws AttachmentCreationError rather than a TypeError when the shipment
  lookup has no Results")`.
- `classify-snap-failure.spec.ts`: `SnapEntityStateException` already/cancelled → mode, not transient,
  stage in detail.
- `event.controller.spec.ts`: precheck-already-live → 204, no release, no failure, ack published, no
  attachments, no routing; cancelled → 204, no release, no failure, **no ack**; lookup 503 → `it("should
  return 503 even though the failed call was the lookup, not the write")`.

---

## Risks / edge cases

- One extra SNAP GET per SO create; reads stayed 100–200 ms during Thursday's burst. If queue depth
  worsens, gate behind an env flag later (not in scope).
- GET→PUT race (allocated between calls) lands in C3 → ack, 204. Covered.
- Stage 00 + 500 NRE mid-write is unchanged from today (structural → permanent → release + failure); it
  is the legitimate modify path.
- Duplicate acks: a genuine customer resend of an in-progress order produces a second ack; downstream
  already tolerates at-least-once delivery. Say so in the PR body.
- Work-order also PUTs `/v2/shipments` (`core/work-order/work-order.service.ts:225`) and has the same
  exposure; PO/RGA need a receipt stage table. Follow-ups, not this round.
- Existing `snap.entity_not_created` monitors unaffected by `already_in_wms` (separate metric).

## Verification

**Prod — loop confirmed gone (verified 2026-09-14).** Full stack live in prod since 2026-09-10
~13:56 BST (#218 merge `2c3659a2` = running Cloud Run revision `snap-adapter-prod-00076`). PURDYFIGG
prod activity since deploy (`service_name:snap-adapter-prod @businessId:PURDYFIGG`):

- **The `already_in_wms` handling fires as designed** — `Entity already exists in SNAP; acknowledged
  without writing` ×39 (with the C2 precheck `SNAP already holds this entity; skipping the write` ×39);
  ~200 fleet-wide. The exact case that used to arm the loop is now acknowledged: hold intact, SNAP
  untouched, no release.
- **No loop signature recurred**: zero `failureMode:unexpected`, zero `Cannot read properties of
  undefined (reading 'requestStart')`, zero `release_sales_order`. At go-live the loop threw 150–517
  failures/evening in tight 5-min cycles; none of that shape appeared across the 09-10 / 09-11
  evenings (nor since).
- **Residual failures are the designed transient path only**: `unable to make request to SNAP` → 503
  → retry / backoff / retries-exhausted (28 / 19 / 13) — Pub/Sub nack-and-redeliver with the deduper
  intact, i.e. C1 working. Not the old hard-fail-and-release.
- PURDYFIGG still creating normally: `Successfully created data in SNAP` ×1080 through 2026-09-14
  09:40, confirmations flowing (`confirmation made` ×1340, `cleared down` ×1339).

**Dev e2e (2026-09-04, pre-merge)** on stack tip `a239cb3` (rev 00470), GADG `FUSE1147-E2E-1` →
`GADG2002B8FED5A`: fresh create ✅; Stage-00 modify resend ✅ (second PUT); resend against an
allocated shipment → `already_in_wms` via precheck, ack, hold intact, SNAP untouched ✅; cancel via
`PATCH Status 01` → resend → `cancelled_in_wms`, 204, no failure/ack, hold intact, SNAP untouched ✅.
#216's dev slot-timeout injection was blocked pre-merge (classifier denied the `gcloud` env-var
change); **superseded by the prod evidence above** — the zero `requestStart` masking + the transient
503/backoff path confirm C1 is live and correct.

## Dev end-to-end verification plan (per PR; `gh workflow run "Manual Deploy snap-adapter" --ref <branch>`,
announce in #bifrost-general per the `verify` skill)

PR1: burst ~50 SOs for one dev business via `mcp__fuse__mock-load-run` so the 5-slot semaphore queues
past 30 s → logs show `failureMode:slot_timeout transient:true`, zero `reading 'requestStart'`, zero
`failureMode:unexpected` for those messages; `snap.entity_not_created{failure_mode:slot_timeout}` rises,
`snap.request.failure{snap_host:unknown}` does not; `mcp__fuse__dedupe-list` shows holds intact.

PR2+PR3: (1) fresh create via `mcp__fuse__mock-send` → GET then PUT, `Successfully created data in
SNAP`, ack; confirm the not-found message matched (no warn). (2) Stage-00 modify: resend with a changed
qty → second PUT 200, ack, `snap-get-shipment` shows the change. (3) Move the shipment past 00 in dev
(`snap-write` allocate) and resend → `Entity already exists in SNAP; acknowledged without writing`
with `detectedBy:precheck`, metric `snap.entity_already_in_wms{detected_by:precheck}`,
`dedupe-get-record` still held, SHH routing attachment intact, no `release_sales_order`, no
`create_data_failure`. (4) C3 evidence: `snap-write` the same payload straight at the allocated shipment
(`confirm:true`) to capture the live 400 body and confirm it matches the classifier fixture. (5) Cancel a
dev shipment and resend → `failureMode:cancelled_in_wms`, 204, hold intact, no release/ack. (6) Fresh PO
and RGA creates unchanged.

## Follow-ups (not in these PRs)
- Config levers: SNAP write concurrency 5→1–2, slot timeout, Cloud Run caps (Harry to revisit).
- Adopt the precheck seam in work-order (shares `SHIPMENT_STAGE`), then PO/RGA with a receipt stage table.
- Datadog monitors: `failureMode:unexpected` (a TypeError in our code should page); `cancelled_in_wms`;
  dedupe loop detector (same recordId promoted >2× in an hour).
- Replay inbox: mark/purge the ~4,000 P&F `Invalid Order Stage` entries so none is redriven onto a live
  shipment.
- Ops: sweep P&F shipments below Stage 70 whose order had ≥1 500 re-PUT for doubled component lines.
