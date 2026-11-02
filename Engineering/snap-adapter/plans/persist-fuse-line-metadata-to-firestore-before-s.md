---
ticket: none
title: Persist Fuse line metadata to Firestore before SNAP create
service: snap-adapter
status: complete
created: '2026-09-30'
updated: '2026-10-05'
repo: /home/hjf/code/fuse/snap-adapter
worktree: none
branch: none
base: origin/master
base_sha: b22516a
pr: '264'
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: high
---
# none — Persist Fuse line metadata to Firestore before SNAP create

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

<!-- MONOREPO, MULTI-PR PLAN. Spans both apps in gfs-bifrost/snap-adapter (snap-adapter write side,
     snap-queue-polling-service read side). Each increment is its own PR off origin/master, so
     branch/worktree are "none" here. Precursor to [[FUSE-1078-retire-routing-attachments]]: that
     plan's inc 2 (remove attachment write) must not delete the SHL half before inc 6 here. -->

## Intent
Shopify sales orders lose their `fulfillmentId` when SNAP is slow. The shipment PUT (or the
attachment PUT after it) times out but lands; the redelivery finds the shipment past Stage `00`,
acks it as `already_in_wms` and never writes the SHL attachment or the Firestore line extension.
Both are keyed by SNAP's post-create `Line` id, so they can only be written after the create. The
goods-out confirmation then carries no `fulfillmentId` and shopify-connector fails on every retry
(PURDYFIGG, 2026-09-29: PURD12ADC65267F / #6458777, correlation `18ba7999-…`; see
`Support/2026-09-30-purdyfigg-shopify-confirmations-no-fulfillment-id.md`).
Change: write all Fuse-owned metadata (routing + per-line data keyed by `SOLineId`, which the
adapter sets before the PUT) to Firestore in one write **before** `createInSnap`, have the poller
read it by `SOLineId`, make that write required, then stop putting Fuse metadata in SNAP
attachments. Proof: an order acked via `already_in_wms` still confirms to Shopify with its
fulfillment id, and `snap.line_extension_lookup.soline` carries new goods-out traffic.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. A routing upsert on redelivery no longer removes line metadata already on the Firestore doc.
- [x] 2. Every Shopify-sourced sales order has `lines.{SOLineId}.extensions.shopify.fulfillmentId` in Firestore before its shipment PUT, so an order acked via `already_in_wms` still has it.
- [x] 3. Goods-out resolves `fulfillmentId` for standard (Level `00`) lines from `lines[SOLineId]`, falling back to the Line-keyed store entry then the SHL attachment; kit components get none; the tier used is metered. A shipment whose Level `00` lines are a strict subset of the stored `lines` is failed, not partially confirmed.
- [x] 4. In prod, a failed Firestore write of Fuse metadata stops the create (transient, redelivered) instead of being swallowed, without releasing a shipment SNAP already holds.
- [x] 5. Post-create attachment building pairs SNAP lines to canonical lines by `SOLineId` + Level `00`, not array index; an exploded kit no longer throws.
- [x] 6. snap-adapter writes no Fuse-specific metadata into SNAP attachments for sales orders, and "Line item has no fulfillment ID" stays at 0 for orders created after cutover.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- snap-adapter `src/adapters/firestore/routing-metadata.store.ts` — `upsert()` whole-doc `set()`, `upsertLineExtensions()` merge. New merged write uses `set(…, { mergeFields })`.
- snap-adapter `src/http/controllers/event.controller.ts` — `persistRoutingMetadata` (pre-create, skips when no connectorId/source), `createInSnap` call, `acknowledgeAlreadyInWms`, `handleSnapFailure` exhaustion path. See [[read-before-write-create-path]].
- snap-adapter `src/core/sales-order/sales-order.service.ts` — `parseFromCanonicalToSnap` (`SOLineId: line.soLineId ?? idx + 1`, :198), `handleAttachments`, `getLineAttachments` (index pairing :418-449), `persistLineExtensions`; `src/core/sales-order/attachments/shopify.ts`.
- snap-adapter `ISnapService` type alias (`snap-service.type.ts`), 5 implementations + `http/__fixtures__/snap-service.fixture.ts`.
- snap-adapter `src/observability/classify-snap-failure.ts` (`RoutingPersistenceException` transient, :290); `snap-metric.type.ts` (`snap.line_extension_store.*`).
- snap-adapter `iac/projects/snap-adapter/{variables,cloud-run}.tf` — `ROUTING_STORE_REQUIRED` (default false, no prod override).
- snap-adapter `tests/test-runner.ts` Firestore-emulator validator (:274-326).
- poller `src/adapters/firestore/routing-metadata.reader.ts` (`getMany`, doc gate at :88, entityId skip :73-76) — interface shared by despatch **and** receipt bases.
- poller `src/core/snap/confirmations/goods-out.confirmation-handler.ts` (store/attachment resolution ~:133-227, `solLineId: line.SOLineId ?? -1`), `kit-line.discriminator.ts`.
- Firestore `fuse-wms-routing` / `routing-metadata/{BizId}__{ShipmentId}` — doc gains `lines`.
- Consumers of goods-out `fulfillmentId`: shopify-connector `sales-order-confirmation.handler.ts` (filters `KIT_COMPONENT` before the throw).
- Fuse MCP `database-collections.json` (doc shape) at sign-off.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- Prod `ROUTING_STORE_REQUIRED=false` on `snap-adapter-prod` — read from the live Cloud Run revision 2026-09-30. FUSE-1078's plan assumes it is on; it is not.
- R1c (#215, store-first line-extension read) and W6 (#224, Line-keyed store write) are both in prod — poller `prod-9c33dd3` contains the store read; snap-adapter `prod-b7ad73c` contains `a4f5d94` (#224). Checked 2026-09-30.
- Poller prod `9c33dd3` equals origin/master for the poller app (only `b22516a` after it, adapter-only). No poller backlog ships with inc 3 today — re-check `git log prod..sha` at approval.
- shopify-connector never sets `soLineId` in code, so the adapter's `idx + 1` fallback applies — source read. A connector mapping rule could still set it: not checked per business (gate on inc 2).
- SNAP keeps the SOLineId Fuse sends and kit components carry the parent's — prod PURD0A95243F3B3 (Level `00` lines on 1/2/3, every Level `20` line on its parent's id) and staging GAD3171547 (repeated SKUs on distinct ids). The documented "degenerate SOLineId" example GAD2265160 is a manual test order, not Fuse-created.
- The precheck acks anything not at Stage `00` (`shipment-stage.ts:17-29`), so the loss needs SNAP to have allocated before redelivery; a Stage `00` redelivery re-PUTs and rewrites attachments. SNAP auto-allocates quickly (FUSE-1147 plan).
- The routing `set()` wiping `lineExtensions` has already happened: the 09-21 PURDYFIGG redrive rewrote 118 routing docs (`Customers/PURDYFIGG/ledger.md` 09-24), masked by the attachment fallback.
- Firestore `mergeFields` throws if a listed field is absent from the data (`document.js:753`) and cannot be combined with `merge` — the mask must be built from the fields actually present.
- Partial orders (resolved 2026-09-30, Harry): **fail the order.** When the stored `lines` carry a SOLineId for which SNAP has no Level `00` line (interface-errored import), goods-out does not confirm the surviving lines; it publishes a confirmation failure instead. Mirrors the `repair-shopify-confirmation` Case B rule (SAIRA #36174).
- Exhaustion under inc 4 (resolved 2026-09-30, Harry deferred to the proposed default): on an exhausted `RoutingPersistenceException`, publish the failure but keep the dedupe hold, as `cancelled_in_wms` does.
- Out of scope: the canonical arriving with no `extensions` (INC-33 index-zip bail-out in shopify-connector) — `miss` must stay a distinct tier so this shows. SNAP-visible DUTY/DELINS/customisation attachments are also skipped on `already_in_wms`; not fixed here. Recovery of the stuck 09-29 orders is separate work (inc 6 gate).

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

- [x] 1. Store: routing `upsert()` writes with `mergeFields` built from present fields, so it no longer replaces `lineExtensions`/`lines` (AC 1) — verify: store unit test (routing → `upsertLineExtensions` → routing again; `lineExtensions` survive; absent-field mask doesn't throw); emulator e2e asserts both fields after a redelivered create. — store spec (5 tests, 2 fail on old set()); real Firestore emulator: routing upsert after lineExtensions+lines keeps both; empty routing ok — done: 9a4a80f
- [x] 2. Adapter: one pre-create write of routing + `lines: { "<SOLineId>": { extensions } }`. Shared pure `resolveSoLineId(line, idx)` used by `parseFromCanonicalToSnap` and the new builder; optional `getFuseMetadata(snap, canonical)` on `ISnapService` (sales order only); controller writes when routing **or** lines are present; skip SOLineId ≤ 0; on a SOLineId shared by lines with differing extensions, omit the key and emit `snap.line_extension_store.soline_collision`; keep `entityId` on the doc. Legacy SHL attachment and Line-keyed write untouched; failure still governed by `ROUTING_STORE_REQUIRED` (AC 2) — verify: controller unit test replaying the incident (attempt 1 `createInSnap` rejects 599 → 503; attempt 2 precheck `already_in_wms` → doc has `lines`, ack published); service unit tests (repeated SKU, kit line, collision, no-routing-but-lines); extend `test-runner.ts` validator to assert `lines`; dev e2e on HJF (fuse-mocker simulator) shows `lines."1"`, `"2"` on the doc. — unit tests (service, store, controller incident replay); dev e2e pending — done: 52789ee
      gate: no Shopify-connected business's `sales_order` mapping sets `soLineId` (or sets only unique values) — checked via config-service per business
            [x] confirmed 2026-09-30: prod config-service has 2 Shopify connectors (`?type=shopify`: SAIRA, PURDYFIGG); both `sales_order` mappings read in full, neither sets `soLineId`
- [x] 3. Poller: goods-out resolves `lines[String(SOLineId)].extensions` for Level `00` lines only, then `lineExtensions[Line]`, then the SHL attachment; SOLineId ≤ 0 or -1 skips the first tier; `getMany` keeps lines-only docs (both despatch and receipt bases compile); new `snap.line_extension_lookup.{soline,line,attachment,miss}`; when stored `lines` holds a SOLineId with no Level `00` SNAP line, publish a goods-out confirmation failure instead of the confirmation (AC 3) — verify: unit tests (standard line via `soline`; kit component gets none; repeated SKU; SOLineId 0/-1 fall through; legacy-only doc; attachment-only; lines-only doc not dropped; 2-line stored order vs 1-line SNAP shipment → failure published, no confirmation); dev e2e once inc 2 is on dev: an HJF goods-out carries `fulfillmentId` counted under `soline`. Before inc 2 is on dev, only `line`/`attachment`/`miss` can be exercised. — tiers + metrics + reader (#267); partial-order failure (#268); dev e2e via real poller incl. replay capture — done: b1e60a9
> SUPERSEDED 2026-10-01 — increment 4 as a standalone prod flip is dropped; its code and its AC move into increment 6. Prod has recorded 33,655 `snap.routing_store.written` and no `snap.routing_store.failure` since the shadow write shipped (2026-09-10 to 2026-10-01), and while the attachments exist they back up a failed write, so making the write required before 6 buys almost nothing. Numbering is kept so ledger entries and PR titles still read.
- [x] 4. Folded into increment 6 (no change of its own; the exhausted-failure code, the dev flip and the flag deletion are all in 6).
- [x] 5. `getLineAttachments` pairs each canonical line to the SNAP line with the same SOLineId and Level `00` (customisations and the legacy Shopify extension); if unmatched, skip that line and emit a metric instead of throwing (AC 5) — verify: unit tests (exploded kit at Stage 10+, reordered lines, extra SNAP lines, missing line). Independent; gates nothing but inc 6. — unit tests (6 of 8 fail on old pairing), black-box 9/9, dev HJF attachments on the right lines — done: 67fb35d
- [x] 6. Make the Firestore write the only copy: (a) on an exhausted `RoutingPersistenceException`, publish the failure but keep the dedupe hold (no release); (b) delete `handleShopifyLineExtensionAttachment` and its call, `persistLineExtensions`, and stop `hasAttachments` counting `extensions`; (c) delete `ROUTING_STORE_REQUIRED` (config, controller branch, Terraform var) so store writes are unconditional and a failed write is never swallowed (AC 4, 6) — verify: controller unit tests (store rejects → 503; redelivery succeeds; exhausted → failure published, no `release_sales_order`); dev HJF order has no `{"shopify"}` attachment and goods-out resolves via `soline`; prod "Line item has no fulfillment ID" = 0 for post-cutover orders over 7d; prod plan shows only the env var removal. Before the PR: set `ROUTING_STORE_REQUIRED=true` in dev Terraform and confirm a clean dev create, so required-write behaviour is exercised across entity types while the attachments still exist (not yet done). — unit/harness/dev e2e green; env var removed in dev apply; prod approval pending the plan share — done: 5984800
      gate: incs 2, 3, 5 in prod (done 2026-10-01); at least one PURDYFIGG or SAIRA goods-out resolved via `soline` in prod before the prod approval (dev has; prod had none at 13:05Z only because no post-deploy order had despatched yet)
            [x] confirmed 2026-10-01: SAIRA goods-out at 13:08:05Z resolved via `soline` (doc `SAIRA93C9B0AFA6`); dev HJF via `soline` with no other copy present
> SUPERSEDED 2026-10-01 — the 14-day ratio gate below is dropped (Harry): the attachment is the leg that fails under SNAP load, so soaking behind it proves little, and the tier counters count per poll, not per order. FUSE-1078 amendment and the stuck 09-29 orders move to the follow-ups list.
      gate (old): incs 2, 3, 5 in prod; `soline` ≥ 99.5% of (`soline`+`line`+`attachment`) for orders created after inc 2, `miss` = 0, `soline_collision` = 0 and `snap.routing_store.failure` = 0 per business, over 14d incl. PURDYFIGG peak; stuck 09-29 orders resolved; FUSE-1078 plan amended

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-05 [sign-off, AC 6] Read-only prod checks. (a) shopify-connector `Confirmation dispatch failed` with `@error` "Line item has no fulfillment ID", by day: 09-29 120, 09-30 432, 10-01 1,345, 10-02 1,459, then none on 10-03, 10-04 or 10-05 to ~19:30Z. After the 14:07Z cutover on 10-01, 24 PURDYFIGG shipments failed. Their Firestore docs (read via the REST API, no writes) were all created before the cutover: `PURD91B0BF21CC3` on 09-16, the other 23 between 20:20 and 21:35Z on 2026-09-30. The 23 had `lines` written between 12:38 and 12:51Z on 10-02 (doc `updateTime`), the repair-skill fix for the orders that had line ids nowhere, and their failures stop by 12:50Z. `PURD91B0BF21CC3` has no `lines`; its last failure was 10-02 16:02Z. No order created after the cutover has failed this way in about 4 days. (b) PURDYFIGG `snap.line_extension_lookup.miss` and `.line` stop after the 10-02 12:00-16:00Z bucket, while `.soline` carries 300-1,200 per 4h bucket through 10-05. (c) Prod runs adapter `prod-eabf63b` (`snap-adapter-prod-00085-t4m`) and poller `prod-0f2024c`. #276 also removed the routing attachment, so no Fuse metadata goes into SNAP attachments for sales orders. In `signoff-ro` (`7c436f9`), `persistRoutingMetadata` runs before `createInSnap` and throws `RoutingPersistenceException` on failure (AC 4). The store `upsert` uses `set(data, { mergeFields: Object.keys(data) })` (AC 1).
- 2026-10-01 [inc 6] Merged #275 as `569d42b` and deployed to prod: run 36873824885, prod plan 0 add / 1 change / 0 destroy (image tag, `ROUTING_STORE_REQUIRED` removed, standing `container-dependencies` / `env` drift), identical to the plan shared beforehand; revision `snap-adapter-prod-00084-hhb`, `ROUTING_STORE_REQUIRED` absent from the live revision, `FIRESTORE_DATABASE_ID` present. Smoke over the 30 minutes spanning the cutover: no ERROR-severity logs, `snap.routing_store.written` 33 with no `failure` series, no `snap.entity_not_created`; first PURDYFIGG prod `soline` = 1 at ~13:57Z. The poller's parked run for `569d42b` (docs-only path match, same code as live `0f2024c`) was cancelled; the poller was not redeployed. Every increment is now in prod.
- 2026-10-01 [inc 6] Built as one change (`5984800`): required pre-create write (failure → `RoutingPersistenceException` → 503; 20s bound per write; Firestore SDK retries UNAVAILABLE/RESOURCE_EXHAUSTED 100ms ×1.3), `ROUTING_STORE_REQUIRED` deleted from config/controller/Terraform, SHL extension attachment and `lineExtensions` write deleted, `hasAttachments` made honest (duty, notes, header and line customisations). Unit 602/602, lint/build 0; harness 9/9 (Minimum fields 2 calls, line-extensions case 3). Dev HJF (`dev-5984800`): order with extensions + note → doc `HJF__HJFF693D5DEFD2A` `lines` 1/2, no `lineExtensions`; simulator attachments DELINS + routing only, 0 × SHL; advanced → goods-out announced 13:52:07Z, dev `soline{hjf}` = 2, no other tier, `routing_store.written` 1, no failure. Dev apply: `ROUTING_STORE_REQUIRED -> null`, 0/1/0. Dev reverted to `c1bfebc`.
- 2026-10-01 [inc 6 gate] Prod: SAIRA doc `SAIRA__SAIRA93C9B0AFA6` (created 12:40Z by the new adapter) carries `lines` 1/2; SAIRA's 2-line goods-out announced 13:08:05Z with prod `soline{saira}` = 2 and `line{saira}` = 2 in the same minute (a second, pre-deploy SAIRA order). No PURDYFIGG `soline` yet at 13:52Z (its post-12:26Z orders had not despatched); PURDYFIGG `line` tier 356 in 90 min, `routing_store.failure` none.
- 2026-10-01 Prod deploy of #269 and #270: poller `0f2024c` (run 36862324366, revision `snap-polling-service-prod-00087-ht2`) then adapter `c1bfebc` (run 36863050757, revision `snap-adapter-prod-00083-jlr`). Both prod plans were 0 add / 1 change / 0 destroy with the identical shape to the previous approved pair (image tag, poller `VERSION`, standing drift); one commit each since the last deploy, no IaC changes. No ERROR-severity logs in 30 minutes; no `snap.routing_store.failure`, `snap.confirmation.partial_order_failed`, `snap.line_attachment.unmatched` or `soline_collision` series. PURDYFIGG `line_extension_lookup.miss` holds steady at ~6 per poll (the same lines re-mapped each cycle, not growing; likely the stuck 09-29 queue items, unverified); no `soline` yet because no order written by the new adapter has reached goods-out. Prod now has every increment except 6.
- 2026-10-01 All five PRs merged to master: #264 `40e1303`, #266 `96a482d`, #267 `171816f`, #269 `0f2024c` (re-approved after the claim fix `6ef76fc`), #270 `c1bfebc`; plus the audit fixes #265 `afe599f` and #272 `e1df353`. Prod is on #264, #266 and #267 only; #269 (partial-order failure) and #270 (attachment pairing) are merged but not yet deployed to prod.
- 2026-10-01 [inc 1-3] Prod deploy: poller `171816f` (run 36855815120, finished 2026-10-01T12:22:58Z) then adapter `96a482d` (run 36855058844, finished 2026-10-01T12:26:06Z); both prod plans were 0 add / 1 change / 0 destroy (image tag, poller `VERSION`, and the standing `container-dependencies` / `env` drift seen in the last applied plans). Cloud Run revisions `snap-adapter-prod-00082-swv` and `snap-polling-service-prod-00086-2mk` ready; no ERROR-severity logs in the first 25 minutes. Datadog first 45 minutes: `snap.routing_store.written` 58 with no `failure` series, `snap.line_extension_store.written` 17 with no `soline_collision`; poller lookups began after its deploy: PURDYFIGG `line` 25 and `miss` 11, STUBBLE `miss` 2, no `soline` yet (no order created by the new adapter had reached goods-out). Increment 6's 14-day clock starts here (earliest 2026-10-15); older parked Deploy runs were cancelled so none can roll prod back.
- 2026-09-30 [inc 5] Unit tests (`handleAttachments - pairing canonical lines to SNAP lines`, 8 tests): exploded kit (ordered Level `00` line takes the attachment, Level `20` members do not), reordered SNAP lines, extra ordered SNAP lines ignored, a canonical line with no SNAP line skipped and metered (`snap.line_attachment.unmatched`) while the rest still attach, SNAP holding more lines than the order does not throw, lines sharing a SOLineId pair in order, routing-store `lineExtensions` keyed by the paired SNAP `Line`; 6 of the 8 fail against the old index pairing. Black-box harness run locally: 9/9 (the mock now defaults `Level` to `00` as SNAP does, and the two sales-order samples' `level: "1"` became `"00"`). Dev, HJF, adapter `dev-67fb35d`: order `MOCK-SO-WPINC7A` → simulator SHL attachments on SNAP Line 1 (WRAP + TXT extension) and Line 2 (TXT extension), Firestore `lines` 1/2 and `lineExtensions` 1/2. Dev given back to master.
- 2026-09-30 [inc 3] Partial order, dev HJF, poller on `dev-b1e60a9` (adapter on master, so the `lines` map was written by hand): order `MOCK-SO-WPINC6A` (SNAP holds ordered lines 1 and 2), doc `HJF__HJFBC0118E43257` given `lines` 1, 2, 3; advanced to despatched. At 15:52:04Z the poller logged `Goods-out failed: stored lines have no ordered line in SNAP` (unmatched `3`), dropped the queue item, and announced no `good_out` (pick and pack announced as normal). Replay held the failure (`598c0dab-…`, `goods_out_confirmation`, `stage confirmation_ready`, `source snap-queue-polling-service`, `business_rule` / `stored_lines_unmatched`, `attempts 0`), its record is the two surviving lines with their fulfillment ids, and `replayable: true` with no blocking issues. Dev given back to master; simulator queue items cleared; key file deleted; the replay failure is left in dev.
- 2026-09-30 [inc 3] Dev e2e through the real poller, HJF, both apps on `dev-eedfa2c`, simulator on `dev-15477b0`: order `MOCK-SO-WPINC5A` → doc `HJF__HJF744E539D9101` with `lines."1"`/`"2"`; advanced picked → packed → despatched; poller announced `good_out` for HJF at 15:24:08Z with no `Confirmation parse failed` / `mapping failed`. Datadog `snap.line_extension_lookup.soline{businessid:hjf}` = 2 per poll cycle from then on, with no `line`, `attachment` or `miss` for HJF. Dev given back to master (`dev-afe599f`); queue items cleared, key file deleted.
- 2026-09-30 [inc 2] Black-box harness run locally (`docker compose -f docker-compose-4pipeline.yaml` with the emulator's host port remapped, then `tests/start-test.sh`): all 9 cases PASS, including the new `Sales Order - line extensions persisted to Firestore by SOLineId` (5 external calls; routing doc has `lines."1"`/`"2"`). Datadog `snap.line_extension_store.soline_collision` showed 1 at 14:29:10Z, the collision order sent during the dev check.
- 2026-09-30 [inc 3] Dev, HJF, both apps on `dev-eedfa2c` (stack head): order `MOCK-SO-WPINC3A` → doc `HJF__HJF9A36AAEBBEA8` with `lines."1"`/`"2"`; advanced picked → packed → despatched through the simulator control plane (`/api/v1/businesses/HJF/shipments/{id}/advance`, key read from fuse-mocker's `snap_api_key` tfstate output). The real reader (`FirestoreRoutingMetadataReader.getMany`, run against dev Firestore) returned the doc with `routing`, `lineExtensions` and `lines`. Poller announced pick and pack for HJF at 14:46:07Z. Dev given back to master (`dev-afe599f`, both services); my three queue items cleared, key file deleted.
- 2026-09-30 [inc 2] Unit tests: service `getFuseMetadata` (index-derived and explicit SOLineId, repeated SKU, kit line, no-extension line, SOLineId 0/-1, collision omitted + metered, identical shared extensions kept), store `lines` (written, replaced, keeps `lineExtensions`), controller incident replay (attempt 1 `createInSnap` 599 → 503; attempt 2 `already_in_wms` → 204, ack published, `lines` written on both deliveries ahead of the create) and no-routing-but-lines. `lint` and `build:check` exit 0; full suite 605/605; `tsc -p tsconfig.json` still 10 errors (all pre-existing).
- 2026-09-30 [inc 2] Dev e2e, HJF via fuse-mocker (branch build `dev-52789ee` on `snap-adapter-dev`): order `MOCK-SO-WPINC2A` (2 lines, Shopify extensions, repeated SKU) → doc `routing-metadata/HJF__HJF89401FFAFE5C` had `lines."1"` = `…/9100001`, `"2"` = `…/9100002` alongside the legacy `lineExtensions` `1`/`2`; order `MOCK-SO-WPINC2B` (two lines sharing `soLineId` 5 with different extensions, a third on 6) → doc `HJF__HJFA81828F24354` had only `lines."6"`, key `5` omitted, legacy `lineExtensions` `1`/`2`/`3` intact. Dev given back to master (`dev-afe599f`).
- 2026-09-30 [inc 1] Dev e2e, HJF via fuse-mocker (branch build `dev-9a4a80f` confirmed on `snap-adapter-dev`): sent a 2-line Shopify sales order carrying `extensions.shopify.fulfillmentId` on both lines (correlation `mock-wp-inc1-merge-fields`) → doc `routing-metadata/HJF__HJF2A4B003A9887` had `routing.source=mock-shopify` and `lineExtensions."1"`/`"2"`. Redelivered the same order with no line extensions (`mock-wp-inc1-merge-fields-redeliver`), so nothing post-create rewrites `lineExtensions` and only the pre-create routing upsert touches the doc → `updatedAt` moved 13:51:56 → 13:53:08 and both `lineExtensions` entries were still present. Dev given back to master (`dev-b22516a`) afterwards.
- 2026-09-30 [inc 1] Store spec (`routing-metadata.store.spec.ts`, 5 tests) against an in-memory Firestore fake: `upsert` after `upsertLineExtensions` keeps `lineExtensions`, keeps pre-existing `lines`, replaces `routing`, tolerates empty routing. The two keep-tests fail on the old whole-doc `set()`. Real Firestore emulator (`google-cloud-cli:emulators`, ad-hoc script, not committed): routing upsert → `upsertLineExtensions` → `lines` merge → routing upsert again leaves both fields and the routing map; empty routing writes `{}`. `lint` and `build:check` exit 0; full suite 584/584.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- [inc 2] `snap.line_extension_store.soline_collision` was not observed in Datadog (dev metrics not queried); the collision order's Firestore doc and the unit test are the evidence. The e2e harness case (`Sales Order - line extensions persisted to Firestore by SOLineId`) was calibrated by CI's black-box job, not run locally.
- [inc 5] An exploded kit at attachment time was not reproduced in dev (the simulator explodes kits at fulfilment, after the attachment step); the unit tests carry it. `snap.line_attachment.unmatched` was not queried in Datadog.
- [inc 2] The incident path end to end (PUT lands, times out, redelivery acked `already_in_wms`) is covered by the controller unit test only, as planned.
> SUPERSEDED 2026-09-30 — the simulator gap below was fixed in fuse-mocker (2885dd6, 15477b0) and the goods-out re-run; see the [inc 3] e2e bullet in Evidence.
- [inc 3] The goods-out through the real dev poller did not complete: `Confirmation mapping failed` on every poll for queue item `HJF6D0EAAAFC2B4`, a schema error listing every SnapStU field, because the simulator's `/v2/stuconsignment` returns link rows (`{BizId, Consignment, Stu, Type}`) where the poller's `fetchStu` expects full StU records. It fails in the fetch, before the SOLineId resolution, so `snap.line_extension_lookup.soline` has not been observed from the poller (no data in Datadog). Needs the simulator's StU rows extended, or the metric read in prod after inc 2 and 3 ship.
> SUPERSEDED 2026-10-05 — PURDYFIGG's first prod `soline` came at ~13:57Z on 2026-10-01, and `soline` has carried its goods-out since (see Evidence). The first sentence below still stands: AC 4 rests on unit tests and the #210 dev injection, not on a live prod failure.
- [inc 6] A Firestore write failure was not induced live in dev; the 503/redelivery/exhaustion contract rests on the controller unit tests and the #210 dev failure-injection proof. PURDYFIGG has not yet produced a prod `soline` resolution (none of its post-12:26Z orders had despatched by 13:52Z).
- [inc 1] The dev redelivery took the Stage `00` re-PUT path, not `already_in_wms`: the simulator's `/api/v1` control plane needs a separate `x-api-key` (fuse-mocker `snap-api` Terraform output) that was not fetched, so the shipment could not be advanced past Stage `00`. The lines-omitted redelivery isolates the routing upsert instead. No Datadog log lines were found for the shipment (dev logs not searchable by shipment id / `service:snap-adapter*`), so the evidence is the Firestore doc and the Cloud Run image tag.
- [inc 1] The docker e2e harness (`tests/start-test.sh`, redelivered create asserting both fields) was not run; inc 2 extends its validator to assert `lines`, which covers it. Store behaviour is proven against the real emulator only.
- [AC 6] The increment's 7-day window for "Line item has no fulfillment ID" = 0 on post-cutover orders isn't over yet. About 4 days were observed (10-01 14:07Z to 10-05), with zero. `PURD91B0BF21CC3` (created 09-16, no `lines`) stopped failing at 16:02Z on 10-02 for a reason not checked here.
- The incident path end to end in dev: fuse-mocker's timeout fault stops before persisting, so it can't make a PUT that lands and times out. The controller unit test in inc 2 is the proof; a "persist-then-timeout" fault mode in fuse-mocker would allow a dev replay.

## Rollout & rollback
<!-- Added on demand. Written at plan time; amend in place as it changes.
     `Shared state touched:` is the single home for the five classes git does not own — a dev
     deploy, a prod config write, a Datadog monitor, a CI var or secret, cross-repo IaC. Reverting
     the branch undoes none of them, so if they are not written here they are not written down. -->

> SUPERSEDED 2026-10-01 — 4 is folded into 6; see the note above increment 4.
- **Order:** 1 → 2 (adapter) and 3 (poller) in either order — both additive; the current reader ignores `lines`. 4 only after 2 has soaked. 5 any time. 6 last, metric-gated.
- **Order (current):** 1 → 2 (adapter) and 3 (poller) in either order — both additive; the current reader ignores `lines`. 5 any time. 6 last, after 2, 3 and 5 are in prod and its 14-day metric gate holds.
> SUPERSEDED 2026-10-01 — prod never runs `ROUTING_STORE_REQUIRED=true` as a separate step; increment 6 makes store writes unconditional and deletes the flag. Dev runs it true ahead of 6.
- **Flags/config:** `ROUTING_STORE_REQUIRED` false → true for prod, set explicitly in the snap-adapter Terraform (not a manual revision edit, which the next apply would undo). Inc 6 then deletes the flag; 4 and 6 deliberately do not share a switch, because a shared boolean cannot express 'required on, attachments still on' during the soak.
- **One-way doors (current):** inc 6, which now also makes a failed Firestore write fatal for every entity type with a routing key (a Firestore outage stops all creates for up to the 10-attempt retry budget, then publishes a failure and keeps the dedupe hold).
> SUPERSEDED 2026-10-01 — wording above covers the combined increment 6.
- **One-way doors:** inc 6. Orders created after it carry `fulfillmentId` only in Firestore `lines`: rolling inc 6 back does not restore their attachments, and deploying a poller older than inc 3 would strand them. Once inc 6 is live, the poller must never go to prod below inc 3.
> SUPERSEDED 2026-10-01 — there is no separate flag flip to roll back.
- **Rollback:** 1–3, 5 git revert; 4 flip the variable back; 6 forward-only (revert restores the attachment write for new orders only).
- **Rollback (current):** 1–3, 5 git revert; 6 forward-only (a revert restores the attachment write and the flag for new orders only).
- **Shared state touched:** dev deploys of both apps; prod Terraform env change (inc 4); Datadog monitors for `line_extension_lookup` / `soline_collision` (in `gfs-bifrost/observability`, alongside FUSE-1078's inc 1); Fuse MCP `database-collections.json`; amendment to the FUSE-1078 plan.
- **Proof in prod:** `snap.line_extension_lookup.soline` rising for new PURDYFIGG/Shopify goods-out while `attachment` falls; shopify-connector "Line item has no fulfillment ID" baseline 25 orders / 24h on 2026-09-30.
- **Deploy approval:** a prod approval ships all of master — `git log prod..<run sha>` before each approval.

## Options considered
<!-- Added on demand. Why this approach and not the others — the thing the planning agent is
     asked for and the plan has otherwise had nowhere to put. Promote to a durable record with
     `wp decide --record` when it is worth defending in a review six months out. -->

- **Chosen — pre-create Firestore write keyed by `SOLineId`** — the only per-line key known before the PUT; one write carries routing and line data; removes the post-create step that is skipped on `already_in_wms`, and removes Fuse data from SNAP's replace-children PUT.
- **Rejected — run `handleAttachments` on the `already_in_wms` path** (proposed in the support record) — a post-create attachment PUT on a live shipment is safe (SAIRA backfill precedent), but it pairs lines by index against an exploded kit and adds SNAP calls exactly when SNAP is slow; it also keeps Fuse data in SNAP.
- **Rejected — key by SKU** — repeated SKUs on distinct lines (GAD3171547).
- **Rejected — key by SNAP `Line` or canonical `line.line`** — `Line` exists only after the create; the Shopify mapping doesn't set canonical `line`.
- **Rejected — separate Firestore doc for line data** — two non-atomic writes and a second read in the poller.
- **Rejected — force `SOLineId = idx + 1` for everyone** — changes the SOLineId connectors see on pick/pack confirmations. Held in reserve if collisions appear.
- **Rejected — a new `LINE_METADATA_STORE_REQUIRED` flag** — routing and lines ride one write, so one flag governs it.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-01** — Inc 6 pulled forward (Harry, 2026-10-01): the SNAP attachment is the unreliable leg under load, so there is nothing to soak behind; go Firestore-only with a sensible retry policy. Policy as built: Firestore SDK retries UNAVAILABLE/RESOURCE_EXHAUSTED with 100ms x1.3 backoff; the store bounds each write at 20s; a failure throws RoutingPersistenceException (transient) -> 503 -> Pub/Sub redelivery 10s..600s, 10 attempts -> create_data_failure. 'Keep the dedupe hold on exhaustion' is dropped: since FUSE-847 the deduper releases off create_data_failure itself, so the only way to keep the hold is to publish nothing (no replay record, order stuck until a human releases); today's publish-and-release lets Shopify re-collect and self-heal once Firestore is back. hasAttachments made honest (duty, notes, header and line customisations) because its flatMap clause counted any line, so every order paid a line-id GET.

- **2026-10-01** — Increment 4 folded into 6. Evidence: prod routing-store writes 33,655 with no failures over 30d; before 6 the SHL attachment backs up a failed write, so 'required' only matters once the attachment is gone. Correction to my earlier framing: AC 4 is a precondition for 6, not the incident fix (that is incs 2+3). 6 now carries the exhausted-failure code, the attachment removal and the flag deletion, gated on 2, 3, 5 in prod plus snap.routing_store.failure = 0 over 14d; dev runs the flag true first.

- **2026-10-01** — Inc 4 and 6 do not share a flag. 4 flips the existing ROUTING_STORE_REQUIRED in prod on its own gate (reversible, 7d soak); 6 deletes the attachment writes AND the flag, making store writes unconditional, so the unsafe state (attachments gone, writes optional) cannot exist. A shared boolean can't express 'required on, attachments still on' during the soak and would tie the reversible switch to the forward-only one. The flag applies to every entity type with a routing key, so a Firestore outage with it on stops all creates (up to the 10-attempt retry budget) — accepted.

- **2026-09-30** — Inc 3 partial order built (option 2): the goods-out handler gets the failure publisher (as it already has the disposer) and, in mapConfirmation, publishes a business_rule failure (rule stored_lines_unmatched, no retryable flag) whose record is the surviving lines' confirmation, then clears the queue item and returns null; a failed publish leaves the item queued to retry. Replay stores it as a redrivable failure (replayable: true), so support can replay to confirm just the surviving lines when the warehouse legitimately removed a line — the false-positive escape hatch. Clear-after-publish caveat: if the clear fails the item is re-mapped and a duplicate failure is published each poll.

- **2026-09-30** — Inc 3 split: tier resolution (soline → line → attachment → miss), the four lookup metrics and the lines-aware reader are in #267; the partial-order failure (AC 3, second half) is NOT built. The handler's confirmationsToCanonical returns canonicals only, so publishing a failure needs a new seam from the handler to ConfirmationsService (agent stop condition: new architectural concept). Kit components keep tiers 2 and 3, and only standard lines are metered so a kit member is never a miss; miss counts every business, so monitors must filter to Shopify businesses.

- **2026-09-30** — Inc 2: only lines that carry extensions are written to `lines` (an entry with empty extensions would say nothing), so the poller's partial-order check in inc 3 keys off lines that need a fulfillmentId; an order arriving with no extensions writes no `lines` and shows as `miss`. `getFuseMetadata(snap, canonical)` keeps the snap arg for the ShipmentId used in the collision log.
- 2026-09-30 — Partial orders fail rather than partially confirm (Harry). Exhausted store failures keep the dedupe hold (Harry deferred to the proposed default).
- 2026-09-30 — Stuck 09-29 orders recovered out-of-band via `repair-shopify-confirmation` (33 shipments / 41 SHL rows, collector ids, `BF…` LineIds; pilot PURD12ADC65267F confirmed 13:18Z). Root cause of the create timeouts is SNAP's database timing out during Purdy & Figg's bulk order drops (Harry), not Fuse.
- 2026-09-30 — New plan rather than an amendment to FUSE-1078: this is an incident fix that must land before that plan's monitored drain, which is parked. FUSE-1078 is amended to point here (inc 6 gate).
- 2026-09-30 — Resolve `lines[SOLineId]` only for Level `00` lines, keeping the documented invariant that only the ordered line carries a `fulfillmentId` (types 9.0.0 `role`), rather than letting kit components inherit it.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
