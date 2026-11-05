---
ticket: none
title: 'Joined-up mock traffic: confirm the sales orders the mocker mocked'
service: fuse-mocker
status: active
created: '2026-11-05'
updated: '2026-11-05'
repo: /home/harry/code/fuse/fuse-mocker
worktree: /home/harry/code/fuse/fuse-mocker/.claude/worktrees/joined-up-confirmations
branch: hjf/joined-up-confirmations
base: origin/main
base_sha: 847b9b725
pr: null
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: medium
---
# Joined-up mock traffic: confirm the sales orders the mocker mocked

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
Out-of-ticket. Today the mocker can mock a sales order and, separately, a goods-out confirmation, but nothing ties the two together. The recent-orders picker copies the reference and nothing else, and load-run orders can't be picked at all. This change lets the mocker confirm sales orders it mocked itself. Each confirmation mirrors its order: `order.salesOrder`, `customerRef`, `customer.order`, lines, SKUs and line ids, the ordered quantity fully shipped, and the site. It publishes on `confirmation_ready` / `goods_out_confirmation` with `broadcast` set and the original `metadata.connectorId`, and is still mock-marked. A confirmation can be sent straight from an activity row, or automatically after `confirmAfterSeconds` on schedules and load runs.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. A goods-out confirmation derived from a generated sales order passes the canonical gate. Its salesOrder, customerRef, customer.order, line numbers, SKUs, soLineId/solLineId, quantities and site match the order.
- [ ] 2. A sales order that a schedule generated can be re-parsed after it comes back out of Mongo. That fixes today's replay failure (`dates.created: expected date, received bson.DateTime`).
- [ ] 3. Every activity row for a published send records the channel and connectorId it resolved.
- [ ] 4. `POST /api/v1/activity/{id}/confirm` publishes the derived confirmation with `broadcast="true"`, the original `metadata.connectorId`, `source` `mock`/`mock-<channel>` and correlation id `<order corr>-confirm`. On dev, sftp-connector or fapi receives it.
- [ ] 5. In the UI, picking a recent sales order fills in the whole derived confirmation (payload, target, broadcast, connector), not just the reference.
- [ ] 6. A schedule with `confirmAfterSeconds` sends a matching confirmation once the delay is up, within one scheduler tick, recorded under activity source `auto_confirm`.
- [ ] 7. A load run with `confirmAfterSeconds` sends one confirmation per published order, with enqueue failures counted and never failing the message.
- [ ] 8. No change to the dev-only checks, to who owns the loops (G4), or to existing response shapes (G5). Every contract change is additive.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- **Publish path:** `apps/api/internal/core/send/send.go` (`buildMetadata` resolves `connectorID` and then throws it away). See [[architecture#The publish path — the canonical validation gate publishes the PARSED envelope]].
- **Generators:** new `apps/api/internal/core/generators/goods_out_from_sales_order.go`. The existing `goods_out_confirmation.go` keeps its SNAP comments.
- **Payload round-trip:** `apps/api/internal/repositories/payload.go` (`NormalisePayload`) and `models/canonical/interpret.go` (`deriveDate`). Read only; the generated layer is not edited (G3).
- **New package `apps/api/internal/core/confirm`.** It's a sibling of `core/replay`, which re-sends the same target and payload and drops Options, so it can't be reused for this.
- **Scheduler:** `core/scheduler/{scheduler,execute}.go`. `fire` wraps `Send` in `runResult`, and `ClaimDue` claims every due item with no limit through `FindOneAndUpdate` in a bounded errgroup.
- **Load runs:** `core/load/loop.go` (`fireBatch` → `sendSafely` → `sendOne`, with panic recovery) and `core/load/caps.go`. `apps/ui/src/lib/load/caps.const.ts` duplicates the tiers.
- **Repositories:** new `repositories/pending_confirmations.go` and `indexes.go`. This becomes the API's sixth collection.
- **HTTP:**
  - controllers: `controllers/{activity,reference,schedules,loadruns}.go`
  - DTOs: `dto/{recent_orders,run_requests}.go`, which list request fields one by one, so a new field must be added by hand
  - `bootstrap/{app,factory}.go`
  - `bootstrap/routes_test.go` checks the routes against the spec in both directions
- **Contract:** `apps/api/openapi.yaml` (G5, fuse-mcp), the `ActivitySource` enum, and `apps/api/scripts/mcp-contract-smoke.sh`.
- **UI:**
  - `apps/ui/src/modules/send/{send.action.ts,components/send-view.tsx}`
  - `apps/ui/src/lib/send/recent-orders.ts`
  - `apps/ui/src/modules/activity/components/activity-view.tsx` (hard-coded `SOURCE_OPTIONS`)
  - the generated `apps/ui/src/lib/gen/mocker-api.client.d.ts` (regenerate with `pnpm gen-mocker-api-client`)
- **Downstream, read only:** consumers of `confirmation_ready` / `goods_out_confirmation`. fapi, sftp-connector and shopify-connector all filter on `source=<own> OR broadcast="true"`.
- **Mocker's own capture subscription:** `iac/projects/fuse-mocker/pubsub-capture.tf` (`capture_goods_out_confirmation`, filtered on recordType only).
- **Out of scope:** the fuse-mcp `mock-*` tools (Go and TS) get their own plan in fuse-mcp-server. That covers the `auto_confirm` filter value, `confirmAfter` arguments, and the `data/api-endpoints.json` and `data/database-collections.json` files.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **Use target `confirmation_ready` with recordType `goods_out_confirmation`.** `sales_order_confirmation_ready` has no `PlannedAttributes`, so it can't carry `broadcast`. All three confirmation topic env vars point at the same topic (`cloud-run-api.tf:120-131`). Established by reading source; checked by the grounding reviewer.
- **Downstream matching uses `order.salesOrder`, `order.customerRef` and `customer.order`.** It doesn't use `identifiers.shipmentId`: on real confirmations that is snap-adapter's hash. fapi and sftp-connector pass the references through without a lookup. shopify-connector looks up the Shopify fulfillment order from `customer.order`, so a mocked Shopify order always ends in `confirmation_data_failure`. Established from a cross-repo source read this session.
- **`broadcast="true"` reaches every goods-out consumer subscribed for the business.** No attribute can target a single connector. Established from each consumer's `pubsub.tf`.
- **The BSON date bug is real and live today.** It reproduced with a throwaway `go test -overlay`: `GenerateSalesOrder` emits `time.Time`, which comes back from Mongo as `bson.DateTime`, and `deriveDate` rejects it.
- **`gen_schema.go` was generated at `@gfs-bifrost/types` 10.2.0, while `canonschema` resolves 10.15.0.** Increment 1 runs `make gen-check` and `make parity` first, so the "passes the gate" check runs against the current schema. Established from the history review.
- **Manual confirms record source `one_off` with `sourceId` = the order's activity id; automatic ones record `auto_confirm`.** Defaulted: this follows replay and needs no new value for manual confirms.
- **Rows from before increment 3 have no `connectorId`.** The confirm re-resolves it from the business's connectors using the stored channel prefix in `metadata.source`; with no channel, it sends without a connectorId. Defaulted, so existing dev rows stay confirmable.
- **`confirmAfterSeconds` is an integer from 1 to 3600, matching `minIntervalSeconds`.** A claimed item that never got published (process restart) is marked failed, not retried. Defaulted.
- **Replay stays unchanged.** A replayed confirm row goes out with no broadcast and reaches no consumer; re-confirming from the order is the supported path. Defaulted to keep replay's documented "drops the impersonation" behaviour.
- RESOLVED 2026-11-05 (recommended default taken): **Fan-out.** For a business with several goods-out connectors, accept that a broadcast confirmation goes to all of them (shopify ends in `confirmation_data_failure`, fapi may log an unresolvable connector)? Or refuse the confirm when the order had no connectorId? Recommended: accept; it's dev only.
- RESOLVED 2026-11-05 (recommended default taken): **Self-capture.** `capture_goods_out_confirmation` has no source filter, so the mocker captures its own confirmations, filed under `sales_order_confirmation_ready` because of the push-map quirk. At load-run volume that buries real producer captures (14-day TTL). Recommended: the capture handler skips envelopes whose correlation id starts with `mock-`. That is one small extra commit inside increment 6, before auto-confirm adds volume.
- RESOLVED 2026-11-05 (recommended default taken): **Load-run confirmation records.** One `auto_confirm` activity row per confirmation, or only counts on the run's summary row (the documented one-row-per-run design, Migration State E2)? Recommended: summary counts only, with per-order rows for schedules. Increment 7's check depends on this.
- RESOLVED 2026-11-05 (recommended default taken): **Idempotency.** Should a second manual confirm of the same order get a 409 (sftp would otherwise write a second file)? Recommended: 409 when a published confirm row already carries that `sourceId`, with `?force=true` to override.

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

Every increment is its own direct commit to `main`, and each one auto-deploys to dev with no CI gate. Run the local gates before every push. Any increment that changes `openapi.yaml` regenerates the UI client and updates `CLAUDE.md` in the same commit.

- [x] 1. **Pure generator.** Add `DeriveGoodsOutConfirmation(seed, order, opts, r, now)`. It takes a parsed sales order and nothing calls it yet. — 25 generator tests incl. generate→parse→derive→bulk-envelope gate; schema regenerated to types 10.15, make parity 216/216 — done: a83c598
  - IDs: `salesOrder` is `identifiers.salesOrder`, falling back to `shipmentId`, then `id`. Copy `customerRef`, `type` and `class`. Copy `customer.order` only when present. `customer.id` falls back to `ECOM`.
  - Site and warehouse: map `identifiers.site`/`warehouse` to `location.*` and to each line's `identifiers.siteId`/`warehouse`.
  - Lines: `solLineId` is `soLineId`, falling back to `atoi(line)`, then the index plus one. Every quantity equals `ordered`.
  - Formats: dates are `goodsOutISOLayout` strings, and numbers are plain floats.
  - Run `make gen-check && make parity` first. Regenerate if they're stale. (AC 1)
  - verify: `TZ=UTC go test ./internal/core/generators/` covers determinism with a seeded Rand and a fixed clock, and has one test per mirrored field. The decisive test runs `GenerateSalesOrder` → `Parse(SchemaSalesOrder)` → derive → `Parse(EnvelopeSchema(goods_out, bulk))` and expects zero issues; a variant does the same with a string quantity `"3"`.
- [ ] 2. **BSON fix in `NormalisePayload`.** Convert `bson.DateTime` to `time.Time`, int32/int64 to numbers, and nested `bson.D`/`bson.M` to maps. (AC 2)
  - verify: `payload_decode_test` round-trips a `GenerateSalesOrder` output through BSON and parses it with no issues. On dev, replaying a generated schedule send that fails today now publishes.
- [ ] 3. **Activity provenance.** `buildMetadata` returns the `connectorID` it resolved. `ActivityEntry`, `ActivityDTO` and the spec's `ActivityDto` gain optional `channel` and `connectorId`. (AC 3,8)
  - verify: send_test `TestAChannelSendRecordsItsResolvedConnectorOnTheActivityRow` and `TestAnExplicitConnectorIDWinsOnTheActivityRow`. Run `mcp-contract-smoke.sh`. On dev, `mock-send` a `sales_order` with channel `sftp`; `GET /activity/{id}` then shows the connectorId.
- [ ] 4. **`core/confirm` and the two endpoints.** Add `GET /api/v1/activity/{id}/confirmation` (preview) and `POST /api/v1/activity/{id}/confirm`.
  - Checks on the row: it was published, it's a create target, its recordType is `sales_order`, and it has a payload. A missing row is a 404. A malformed id, a non-sales-order row or a row with no payload is a 400. A publish failure is a 502.
  - Derive: re-parse the stored payload, re-resolve a missing connectorId, then send with `broadcast` and the connectorId.
  - Apply the idempotency answer.
  - Write the openapi entries in the same commit. (AC 4,8)
    gate: the Fan-out and Idempotency questions are answered
          [x] confirmed
  - verify: `routes_test`, controller tests for 400/404/502, and a core test with a fake publisher asserting `broadcast="true"`, `metadata.connectorId` and source `mock-sftp`. On dev, confirm the increment 3 order for HJF:
    - `GET /confirmations/sent` shows it.
    - The confirmation is captured under `sales_order_confirmation_ready`.
    - A Datadog search on `<corr>-confirm` shows sftp-connector or fapi receiving it, and shows what any other connector did with it.
- [ ] 5. **UI picker pre-fills the derived confirmation.** `RecentOrder` gains `id`, `channel` and `connectorId` (additive). The picker only lists `sales_order` rows. Selecting one calls the preview endpoint through a server action, fills the editor, sets the target to `confirmation_ready`/`goods_out_confirmation`, and sets broadcast and the connector. Sending still goes through `/messages`. (AC 5)
  - verify: a derive-action case in `apps/ui/src/modules/send/__test__/send.action.spec.ts`, then `pnpm lint && pnpm test && pnpm build`. On dev, screenshot the filled-in editor, then send it.
- [ ] 6. **Queue, drain and schedule `confirmAfterSeconds`.**
  - New `pending_confirmations` collection with indexes `{status, dueAt}` plus a TTL on `createdAt`. A shared `EnqueueMany`.
  - Normalisation runs on read.
  - `Outcome.Record` carries the parsed order out of the send.
  - `fire` splits out the outcome and enqueues when OK, which covers run-now too.
  - `Engine.Tick` drains after schedules fire: a claim guarded on `status: pending`, a per-tick cap, and bounded concurrency, deriving at drain time.
  - New `auto_confirm` source: in `ActivitySources`, the spec enum and the activity-view `SOURCE_OPTIONS`.
  - Schedule create and PATCH DTOs validate `confirmAfterSeconds` (create target and `sales_order` only).
  - Apply the self-capture answer as its own commit, before this. (AC 6,8)
  - verify: scheduler_test `TestATickDrainsDueConfirmations`, `TestALostClaimIsNotPublished` and `TestADrainFailureIsRecordedNotRetried`. A test sends an order through Mongo and back, then derives from it. On dev, a schedule with `confirmAfterSeconds: 30` gets a matching `auto_confirm` confirmation within one tick of the delay.
- [ ] 7. **Load-run `confirmAfterSeconds`.**
  - `sendSafely` and `sendOne` return the outcome.
  - `fireBatch` collects the outcomes under its mutex and calls one `EnqueueMany` per batch.
  - An enqueue failure is logged and counted, and leaves `sent` and `failed` unchanged.
  - Add the field to the load-run request DTO by hand.
  - `confirmAfter` doubles the effective rate in `Risk`, and `caps.const.ts` mirrors that.
  - Record per the load-run answer. (AC 7,8)
    gate: the Load-run confirmation records question is answered
          [x] confirmed
  - verify: loop_test `TestABatchEnqueuesOneBulkInsert` and `TestAnEnqueueFailureDoesNotFailTheMessage`. On dev, a 20-message burst with `confirmAfterSeconds: 30` produces 20 confirmations, counted in the Datadog `fuse.mocker.publish{recordType:goods_out_confirmation}` metric.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-11-05** — DeriveGoodsOutConfirmation takes (seed, order, r, now) with no Options: the order is the source of every value an option would override, so an options bag would only invite a mismatched confirmation.
- 2026-11-05: Open questions settled with the recommended defaults (Harry: "let's action the plan"): accept broadcast fan-out in dev; capture handler skips `mock-` correlation ids (own commit before inc 6); load-run auto-confirms are counted on the run summary row, not one row each; a second manual confirm of the same order is 409 unless `?force=true`.
- 2026-11-05: **The generator is derived, not reused.** `GenerateGoodsOutConfirmation` keeps its random behaviour for the free-form send path. The new derive is a separate function, so existing presets and fuse-mcp `mock-generate` output don't change.
- 2026-11-05: **The simulator isn't driven.** Moving the order through the snap-api simulator so the real poller confirms it was rejected for now. It only works for simulator-backed businesses, and it would make `apps/api` call snap-api. It's a candidate follow-up.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
- **Replaying a schedule-generated sales order fails today.** Its `time.Time` dates come back from Mongo as `bson.DateTime`, which `deriveDate` rejects. `TestARoundTrippedPayloadStillParsesCanonically` only covers string dates.
- **All three goods-out consumers accept own-source or broadcast.** fapi (`rest`), sftp-connector and shopify-connector each gate on their own source or `broadcast="true"`. No attribute targets one connector, so a mock confirmation reaches consumers only when it's broadcast.
- **The mocker captures its own goods-out confirmations.** Its capture subscription has no source filter, and the push-map quirk files them under `sales_order_confirmation_ready`.
- **Replay can't deliver a confirmation.** Both replay paths drop channel, connectorId and broadcast, so a replayed confirmation reaches no consumer.
- **`operations.md` is stale on logging.** Since 847b9b7, `ResolveSink` writes to stdout with the Datadog agent in the container, so the sidecar `/shared-volume` paragraph is wrong.
- **`gen_schema.go` is 13 minor versions behind `@gfs-bifrost/types`.** It is still at 10.2.0, while `canonschema` resolves 10.15.0.
