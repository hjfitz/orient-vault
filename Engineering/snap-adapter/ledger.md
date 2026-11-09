---
tags: [waypoint, ledger]
title: snap-adapter — work ledger
---
# snap-adapter — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-05 — Run snap-adapter on the golden runtime image

Run snap-adapter on the golden runtime image

Moved snap-adapter and snap-queue-polling-service onto ilg-platform's node24-runtime:0.1-affogato golden image and removed their Datadog serverless-init sidecars. The agent now runs in-container, with DD_* on the app container and the ILG dual-ship kept. snap-adapter gained a SIGTERM handler that closes the server and exits once in-flight creates finish. The poller's existing handler already keeps in-flight polls running through the grace. Both apps were deployed to dev and verified: HJF create via fuse-mocker, poller pickup of a simulator despatch, and a clean shutdown flushed to Datadog. Draft PR.

PR: gfs-bifrost/snap-adapter#319
## 2026-11-06 — Emit snap.breaker.opened, .state and .rejected beside snap.circuit_opened

Emit snap.breaker.opened, .state and .rejected beside snap.circuit_opened

Programme unit A3. Both transport modes now dual-emit the shared breaker metrics: snap.breaker.opened (closed->open, alongside the unchanged snap.circuit_opened), snap.breaker.rejected (each request an open circuit turns away) and a per-host snap.breaker.state gauge (closed 0, half-open 0.5, open 1) on every request and transition. Metrics only, no behaviour change. Dev verified live in both modes under an injected 429 (opened matched circuit_opened exactly; gauge 1 -> 0.5 -> 0 on recovery). Ship: SHIP-1106-snap-breaker-metrics

PR: gfs-bifrost/snap-adapter#325

## 2026-11-06 — Let a 429 trip the SNAP breaker behind SNAP_CB_TRIP_ON_429

Let a 429 trip the SNAP breaker behind SNAP_CB_TRIP_ON_429

Programme unit A2b. New env switch SNAP_CB_TRIP_ON_429 (default off; not set in Terraform, so prod is unchanged on deploy). On, a SNAP 429 counts as an outage in both transport modes via one shared predicate; other 4xx still reset. Dev verified off and on; with the threshold temporarily at 2 the breaker opened live in both transport modes under an injected 429 (first live breaker-open of the adapter transport). Flip after G1 with SNAP_TRANSPORT_GUARD and the 337501612 message update. Ship: SHIP-1106-snap-cb-trip-on-429

PR: gfs-bifrost/snap-adapter#323

## 2026-11-06 — Gate SNAP requests at the axios adapter on the shared breaker, behind SNAP_TRANSPORT_GUARD

Gate SNAP requests at the axios adapter on the shared breaker, behind SNAP_TRANSPORT_GUARD

Programme unit A2a. New env switch SNAP_TRANSPORT_GUARD (interceptors|adapter, default interceptors; not set in Terraform, so prod is unchanged on deploy). Adapter mode runs breaker admission -> token -> slot -> request inside @gfs-bifrost/resilience's PerHostCircuitBreaker at the axios adapter hook, with today's trip rules (5xx/network trip, any 4xx incl 429 resets) and opens counted closed->open only. Intended adapter-mode differences: single half-open probe, no caller waits on a probe holding a slot, closed-admitted callers reaching an opened circuit are turned away. Self-review found and fixed a cockatiel stale-failure clobbering a half-open probe. Dev verified in both modes; switch flips after G1. Ship: SHIP-1106-snap-transport-guard

PR: gfs-bifrost/snap-adapter#322

## 2026-11-05 — Take the semaphore, token bucket and host key from @gfs-bifrost/resilience

Take the semaphore, token bucket and host key from @gfs-bifrost/resilience

Programme unit A1. Deletes the local copies and imports them from @gfs-bifrost/resilience 0.2.0; snap goes to ^0.4.2 so one resilience copy resolves. No behaviour change.

PR: gfs-bifrost/snap-adapter#321

## 2026-11-05 — Give transiently failing SNAP creates about four hours of retries, and never ack a create whose failure wasn't published

Give transiently failing SNAP creates about four hours of retries, and never ack a create whose failure wasn't published

SNAP_MAX_TRANSIENT_DELIVERY_ATTEMPTS (Terraform 30, up from a hard-coded 10). The create_record DLQ now derives from it at budget + 5. A failed create_data_failure publish now nacks instead of silently dropping the record. Ahead of the P&F ~10x peak.

PR: gfs-bifrost/snap-adapter#318

## 2026-10-19 — FUSE-1319

Publish exhausted transient Snap failures as retryable

A transient failure that runs out of its 10 delivery attempts (Snap 5xx, open circuit, slot timeout, routing-store failure) now publishes infrastructure `snap-adapter.<entity>.redelivery_exhausted`, `retryable: true`, naming the dependency that was down (`service: snap` or `firestore`) and the attempt count. Previously these went out as non-retryable Snap rejections / `snap-adapter.unexpected`. The axios interceptor rewrites every write failure to "Snap rejected the creation of an entity", so the 5xx reason is built from the status. Dev-verified with a simulator 503 on HJF and a successful replay. Must be in prod before dedupe-service#160 (FUSE-1311), which holds on `retryable: false`.

PR: gfs-bifrost/snap-adapter#303

## 2026-10-19 — FUSE-1238

Prove work-order CarrierId end to end in dev

Dev end to end proven on 2026-10-19: a kitting DESADV on HJF (connector conn_1435…) with a temporary carrierId = OWN header default became simulator S10 HJFD4AC7656638E carrying CarrierId OWN (correlation 9172b3b8-258b-4336-ae52-764b6afcf6f5). The mapping default was removed afterwards. Real SnapFulfil does not keep it. GADG's dev work order WO-20261016-AP005 reached snap-adapter with carrierId OWN (dedupe's canonical shows it), but GADG dev Snap stored CarrierId NETCOURIER, the only value in its CARRIER lookup. Getting OWN to land is Snap-side lookup config, not Fuse code.

Plan: [[FUSE-1238-work-orders-write-carrierid-to-the-snap-shipment]].

## 2026-10-15 — FUSE-1308

Build the stock sync export from the business's catalogue

The poller's stock sync export took one line per stocktotals row SKU. On a shared SNAP host those rows can carry another business's product, so GADG's dev export listed seven other customers' SKUs and wrote three of them into GADG's dev Shopify. The SKU set now comes from /v2/products filtered by BizId, and the rows only add numbers to it. A catalogue product with no sellable stock exports at 0. Stock rows and kit rows are scoped by BizId instead of OwnerId, matching wms-gateway's GET /stock (GADGET2's TTRS3 now counts), and OwnerId joins the stocktotals $orderby. Verified on dev GADG: 115 lines, the same SKU set as GET /stock, no foreign SKUs. Open follow-up: kit figures differ from the gateway because SNAP works out PotentialKitQty per owner while the gateway pools components across owners.

PR: gfs-bifrost/snap-adapter#299

## 2026-10-13 — Tie the poller's claim TTL to its request timeout

Tie the poller's claim TTL to its request timeout

Closes Poller Clear-Down D3: keep the confirmation claim, and set its TTL from the Cloud Run request timeout via one Terraform local, along with both 600s ack deadlines. No value changes.

PR: gfs-bifrost/snap-adapter#295

## 2026-10-13 — Retire snap-adapter's stock adjustment clear-down

Retire snap-adapter's stock adjustment clear-down

Poller clears stock adjustments at publish (#293), so snap-adapter's stock_adjustment_made clear-down, its /confirmation/made route, subscription and confirmation_data_failure publishing are removed. Stale poller comments fixed.

PR: gfs-bifrost/snap-adapter#294

## 2026-10-12 — Clear stock adjustments off SNAP's outbound queue after publish

Clear stock adjustments off SNAP's outbound queue after publish

Poller Clear-Down, ahead of D3: drops the stock_adjustment clear skip, ending the PURDYFIGG/SAIRA stock-move re-announce loop.

PR: gfs-bifrost/snap-adapter#293

## 2026-10-12 — Retire snap-adapter's confirmation_made clear-down

Retire snap-adapter's confirmation_made clear-down

Poller Clear-Down D2: removes snap-adapter's seven confirmation_made subscriptions now the poller clears every published confirmation; stock_adjustment_made unchanged.

PR: gfs-bifrost/snap-adapter#292

## 2026-10-12 — Clear every published confirmation off SNAP's outbound queue

Clear every published confirmation off SNAP's outbound queue

Poller Clear-Down: removes the clear-after-publish allow-list and clears broadcast and channel-only groups, closing D1 and unblocking D2.

PR: gfs-bifrost/snap-adapter#291

## 2026-10-12 — Clear routed confirmations for PURDYFIGG

Clear routed confirmations for PURDYFIGG

Poller Clear-Down D1, fifth batch: prod allow-list gains PURDYFIGG after the 2026-10-12 G6 re-audit and FUSE-1118 reaching prod.

PR: gfs-bifrost/snap-adapter#290

## 2026-10-09 — Clear routed confirmations for STUBBLE (D1 fourth batch)

Clear routed confirmations for STUBBLE (D1 fourth batch)

Adds STUBBLE to the prod clear-after-publish allow-list (Poller Clear-Down D1). Its hold was on 157 poisoned routing docs, which were fleet-wide and repaired on 2026-09-24; STUBBLE has none with source snap-adapter.

PR: gfs-bifrost/snap-adapter#288

## 2026-10-09 — Clear routed confirmations for SAIRA (D1 third batch)

Clear routed confirmations for SAIRA (D1 third batch)

Adds SAIRA to the prod clear-after-publish allow-list (Poller Clear-Down D1). SAIRA's Shopify connector is in the no-fulfillment-ID re-announce loop (3 orders, ~375 publishes/day); the clear ends it and records one redrivable failure per order.

PR: gfs-bifrost/snap-adapter#287

## 2026-10-09 — FUSE-1238

Work orders: write CarrierId to the Snap shipment

Map identifiers.carrierId (types 10.12.0) onto the S10 work order shipment CarrierId, mirroring sales-order, no default; bumps @gfs-bifrost/types to ^10.12.0 in apps/snap-adapter. Merged and deployed to dev (7f7df3b); prod gate pending, end-to-end proof pending sftp-connector in dev.

PR: gfs-bifrost/snap-adapter#286

## 2026-10-01 — FUSE-1078

Stop writing the SNAP routing attachment

snap-adapter drops the SHH/REH KeyLine 0 routing TXT attachment for every entity type. Firestore routing-metadata (required pre-create write, #275) is the only copy now, so routed creates make one fewer SNAP PUT. The routing_metadata.* metrics are removed. The poller still falls back to existing attachments until the read-removal increment. Verified on dev HJF: no attachment on the new SO/PO, and the goods-out resolved via soline.

PR: gfs-bifrost/snap-adapter#276

## 2026-10-01 — Inc 6/6 — Make Firestore the only copy of Fuse line metadata

Inc 6/6 — Make Firestore the only copy of Fuse line metadata

The pre-create Firestore write is required (503 + Pub/Sub backoff on failure, 20s bound per write, exhaustion publishes create_data_failure as before); ROUTING_STORE_REQUIRED deleted from config/controller/Terraform; the SHL Shopify extension attachment and Line-keyed lineExtensions write removed (poller still reads both for pre-cutover orders); hasAttachments made honest so plain Shopify orders skip the attachments GET. Pulled forward from the 14-day soak because the SNAP attachment is the leg that fails under load. 'Keep the dedupe hold on exhaustion' dropped: since FUSE-847 create_data_failure is itself the release. Dev-verified on HJF; prod SAIRA already resolved a goods-out via soline.

PR: gfs-bifrost/snap-adapter#275

## 2026-10-01 — Raise the axios and grpc-js override floors in both apps

Raise the axios and grpc-js override floors in both apps

Seven axios advisories (fixed in 1.20.0) and GHSA-m9gg-hp2v-232j in @grpc/grpc-js (fixed in 1.14.5) turned both apps' prod dependency audits red on master and on every open PR. Override floors raised; lockfiles edited by hand because pnpm 10.30.3 --lockfile-only rewrote ~140 unrelated lines each.

PR: gfs-bifrost/snap-adapter#272

## 2026-09-30 — Inc 5/6 — Pair attachment lines to SNAP lines by SOLineId

Inc 5/6 — Pair attachment lines to SNAP lines by SOLineId

Post-create attachments pair each canonical line to the ordered (Level 00) SNAP line with its SOLineId instead of by array position, so an exploded kit or reordered lines no longer attach to the wrong line and extra SNAP lines no longer throw. A canonical line with no ordered SNAP line is skipped and metered (line_attachment.unmatched). Verified in unit tests (6 of 8 fail on the old pairing), the black-box harness (9/9) and HJF dev. The black-box SNAP mock now defaults Level to 00 as SNAP does.

PR: gfs-bifrost/snap-adapter#270

## 2026-09-30 — Inc 3/6 (part 2) — Fail a goods-out whose stored lines have no ordered line in SNAP

Inc 3/6 (part 2) — Fail a goods-out whose stored lines have no ordered line in SNAP

When the routing doc's lines name a SOLineId the shipment has no Level 00 line for, the goods-out is not confirmed in part: the poller publishes a non-retryable business_rule failure (stored_lines_unmatched) carrying the surviving lines' confirmation, then clears the queue item. Replay holds it as redrivable, so a deliberate replay confirms just the surviving lines. Verified on HJF dev. fuse-mcp pubsub-topology.json should list this service as a confirmation_data_failure publisher after it ships.

PR: gfs-bifrost/snap-adapter#269

## 2026-09-30 — Inc 3/6 (part 1) — Poller resolves goods-out line extensions by SOLineId

Inc 3/6 (part 1) — Poller resolves goods-out line extensions by SOLineId

For ordered (Level 00) lines the poller looks up the routing doc's lines by SOLineId, then the Line-keyed entry, then the SHL attachment, and meters the tier (line_extension_lookup.soline/line/attachment/miss). Kit members never take the first tier; SOLineId 0/-1 fall through; the reader keeps docs that carry only lines. Verified through the real dev poller (soline = 2 per poll for HJF). Metrics count per mapping, so compare tiers as ratios.

PR: gfs-bifrost/snap-adapter#267

## 2026-09-30 — Inc 2/6 — Write Fuse line metadata to Firestore before the SNAP create

Inc 2/6 — Write Fuse line metadata to Firestore before the SNAP create

Sales-order lines carrying extensions are written to the routing doc as lines keyed by SOLineId, in the same pre-create write as routing, so an order acked as already_in_wms still has its Shopify fulfillmentId recorded. A SOLineId shared by lines with different extensions is omitted and metered (soline_collision). Governed by ROUTING_STORE_REQUIRED; SHL attachment and Line-keyed write untouched. Verified on HJF dev and in the black-box harness. Stack: #264 -> #266 -> #267 -> #269.

PR: gfs-bifrost/snap-adapter#266

## 2026-09-30 — Raise the brace-expansion override floor to 5.0.11 in both apps

Raise the brace-expansion override floor to 5.0.11 in both apps

Two new high advisories (GHSA-6j4f-fj2g-mc7p, GHSA-qhr7-859c-m2p7) turned both apps' prod dependency audits red on master; override floor moved 5.0.9 -> 5.0.11 in snap-adapter and the poller. Lockfiles edited by hand because pnpm 10.30.3 --lockfile-only rewrote ~125 unrelated lines each.

PR: gfs-bifrost/snap-adapter#265

## 2026-09-30 — Keep line metadata when a redelivery rewrites routing

Keep line metadata when a redelivery rewrites routing

Routing upsert in the snap-adapter Firestore store now uses mergeFields, so a redelivery no longer wipes lineExtensions/lines already on routing-metadata/{BizId}__{ShipmentId}. Inc 1 of 6 of the persist-line-metadata-before-create plan (AC 1). Verified on dev HJF (lineExtensions survive a redelivery) and against the real Firestore emulator; mergeFields throws on an absent listed field, so the mask is built from present fields. The already_in_wms path was not exercised (simulator control-plane key not fetched).

PR: gfs-bifrost/snap-adapter#264

## 2026-09-29 — FUSE-1088

Carry movement reference, batch and expiry on stock adjustment confirmations

Poller stock-adjustment handler: identifiers.movementRef = <SiteId>_<MoveType>_<MoveId>_<MoveLineId> (Jitterbit EntityID shape); from/to stockId (fixes mis-cased FromStockID read) + batchId/expiry via Stock Detail by stock id (best-effort; absent once stock is consumed). Also fixes multi-line moves: fetch per-line route instead of /{MoveId} Results[0] (every line was mapped to line 1). Verified locally vs live GADG dev (12 moves); dev deploy clean but no movement arrived — e2e needs a human stock hold in dev Snap UI. types 10.8.0.

PR: gfs-bifrost/snap-adapter#263

## 2026-09-24 — FUSE-1258

Carry batch and work-order references on FGR and WOC

Poller FGR handler resolves its S10 work order (ShipmentId = Prime, then reverse WOC receipt search, exactly-one match) and stamps workOrderId/businessWorkOrderId/salesOrder/workOrder.customerRef; FGR line batch from inbound stock consignment (Type IC); WOC component batch from stock movements into the WO consignment → stock detail (S10 lines have no batch; component stock is de-assigned on close). Single-batch-per-SKU rule. Lookup errors retry next poll. Verified locally vs live GADG dev on 3 WOs; true dev e2e needs a human to progress a WO in Snap UI. types 10.5.0.

PR: gfs-bifrost/snap-adapter#257

## 2026-09-24 — FUSE-1238

Keep metadata.source as the ingress channel through snap-adapter and the poller

snap-adapter's create-failure, confirmation-failure, acknowledge and release producers overwrote metadata.source with "snap-adapter". A retry-queue redrive re-sent that value, so the redriven order's Firestore routing doc stored source "snap-adapter" and the poller stamped it onto the confirmation: no delivery subscription matched, so it was never delivered or cleared and re-published every poll cycle (Dock and Bay dev; 157 prod routing docs, STUBBLE 28 despatches since 17 Sep). Producers now leave metadata.source untouched; the poller's confirmation envelope carries the resolved routing channel instead of its own name. The Pub/Sub source attribute and BifrostFailure.source still name the emitter (collector filters on the attribute). Invariant: `metadata.source` is which connector emitted the record, set once at ingress and never overwritten by anything that handles it. Existing poisoned routing docs and held failures need a separate data repair.

PR: gfs-bifrost/snap-adapter#253

## 2026-09-21 — FUSE-1194

Resolve the stock sync export bucket via remote state

snap-queue-polling-service now resolves the stock sync export bucket's name
from core-infra's new terraform_remote_state output rather than a hard-coded
string, and exposes it as the STOCK_SYNC_EXPORT_BUCKET Cloud Run env var --
mirrors the existing config_service_api_key_ref remote-state read already in
remote.tf. Paired with core-infra#14, which provisions the bucket + this
service's write IAM; this side needed no IAM change, only the read wiring.
Couldn't run a full terragrunt plan locally until core-infra#14 actually
merges and dev auto-applies -- terraform_remote_state reads real deployed
state, not a sibling PR's plan output, so planning right now correctly
errors on the output not existing yet. Sets up FUSE-1195 (the Snap pull ->
JSONL write -> confirmation_ready publish), which reads this env var instead
of hard-coding the bucket.

PR: gfs-bifrost/snap-adapter#243

## 2026-09-21 — FUSE-1063

Poll only confirmation-eligible businesses; skip already-claimed queue items

snap-queue-polling-service now withholds a confirmation unless its target connector's confirmationsEnabled toggle is true, checked in the same withhold/fail-open pass that already resolves connector source provenance — an ineligible confirmation stays claimable in SNAP's outbound queue and is picked up automatically once the connector's config catches up. The business-level confirmations flag was retired as a gate entirely (the now-fully-unused field was dropped); the per-connector toggle is the sole eligibility gate, with use-case/mapping eligibility staying at each downstream connector. Businesses with no confirmation-enabled connector are no longer polled at all — a new config-service read (GET /business, paged) is reduced to one boolean per business and cached, refetched on any CONNECTOR revision event, failing open to polling everyone if the index is unreadable. In prod this dropped 14 of 30 businesses that were being polled every 2 minutes for nothing. Already-published queue items are also no longer re-enriched every cycle: each lane now peeks at the INC-30 claim key straight off the raw outbound-queue row and drops items whose claim is still live before any shipment/receipt/stock-movement fetch runs, rather than fully enriching and only then dropping them as duplicates at announce time (~37 wasted enrichments per cycle in dev, 44 in 18 minutes in prod). The announce-time tryClaimConfirmation dedupe remains authoritative and unchanged; a cache error on the new pre-check fails open (reads as unclaimed).

PR: gfs-bifrost/snap-adapter#241
PR: gfs-bifrost/snap-adapter#240
PR: gfs-bifrost/snap-adapter#233

## 2026-09-16 — FUSE-1059

Decommissioned legacy PO/SO per-entity confirmation topics

Retired the four legacy per-entity confirmation topics (purchase_order/sales_order
confirmation_ready/made) in favour of the existing cross-entity confirmation_ready/
confirmation_made topics, discriminated by attributes.recordType. 11 increments across
7 repos (fapi, sftp-connector, shopify-connector, snap-adapter, replay-service, collector,
bifrost-pubsub), plus an 8th repo (fuse-mocker) found and fixed after the fact — it was
never in the plan's named consumer list and its dev capture subs/publish targets went
dangling after the topic deletion (fuse-mocker#16, draft, held for review).

Key gotcha: recordType is asymmetric between ready and made for sales_order
(goods_out_confirmation vs sales_order) — see [[bifrost-pubsub/known-context]]. Also:
two "atomic swap" PRs this session (sftp#264, snap-adapter#229) shipped as destroy+create
in one apply despite their own commit messages claiming add-only — verified safe via
push_endpoint equality, now a memory entry (reference_atomic_terraform_swap_push_endpoint_check).

The one-way door (Inc 8, deleting the 4 topics + 4 DLTs + 16 outputs) executed only after
a same-day pre-apply sweep: zero references to the outputs across all 6 named consumers,
zero IAM bindings/subscriptions on all 8 topic+DLT resources, and a clean CI terraform plan
(0 add, 0 change, 8 destroy) reviewed and approved before merge. Inc 9 (observability cleanup)
also caught and fixed two dashboards that would have flipped to permanent no-data.

PR: bifrost-pubsub#14 (the deletion). Full PR list: snap-adapter#232, fapi#135,
sftp-connector#269, shopify-connector#267, replay-service#85, observability#42,
fuse-mocker#16 (draft, follow-up needed).

## 2026-09-14 — FUSE-1147

Stop re-PUTting live shipments — loop broken, prod-verified

Ended the PURDYFIGG evening re-PUT loop (150-517 create failures/evening in 5-min cycles since P&F go-live). Root cause: a SemaphoreAcquireTimeoutError (per-host Semaphore(5), 30s) thrown pre-dispatch had no axios config, so axios-metrics.ts getRequestStart() threw a TypeError that MASKED it -> classified 'unexpected'/non-transient -> release_sales_order + create_data_failure -> dedupe hard-deletes the hold -> next bulk tick re-collects and re-PUTs a shipment SNAP already holds (Invalid Order Stage 400 / 500 NRE; the 500s doubled kit-component lines on live shipments).

Fix = 3 stacked PRs, sales orders only: C1 #216 null-guard the metrics interceptor (a no-config/no-response error nacks as slot_timeout->503->backoff, deduper intact); C3 #217 classify a 400 whose only field errors are XDoc 'Invalid Order Stage' as new mode already_in_wms -> ack via EntityAcknowledgeService, no release; C2 #218 read-before-write (fetch-snap-entity.ts + shipment-stage.ts) — only Stage 00 writable, else throw SnapEntityStateException(already_in_wms|cancelled_in_wms). 'Already in WMS' is a thrown typed state, not a new return type: ISnapService.createInSnap stays Promise<string>. Ack keeps the dedupe hold because dedupe stores-before-forwarding and doesn't subscribe to create_acknowledge — so no dedupe-side change was needed (C4 dropped).

Prod-verified 2026-09-14 (live since 09-10 13:56, rev snap-adapter-prod-00076 = 2c3659a): already_in_wms acks firing (39 PURDYFIGG / ~200 fleet), zero failureMode:unexpected, zero requestStart masking, zero release_sales_order; residual failures are only the designed transient 503/backoff path. PURDYFIGG still creating normally.

Key paths: apps/snap-adapter/src/observability/{axios-metrics,classify-snap-failure,snap-failure.type,snap.recorder}.ts; adapters/snap/{fetch-snap-entity,shipment-stage}.ts; exceptions/snap-entity-state.exception.ts; core/sales-order/sales-order.service.ts; http/controllers/event.controller.ts.

Gotchas: GET /v2/shipments/{id} for a missing id on ilg005 returns HTTP 200 {Status:Error, Message:'No matching entity'} (not 404) — fetch-snap-entity handles all 3 not-found shapes. A keyed PUT replaces the shipment's children, wiping the SHH routing attachment — never rewrite a shipment the warehouse has started. Follow-ups (separate): work-order/PO/RGA adopt the precheck; SNAP write concurrency/slot-timeout/Cloud Run config levers; Datadog monitors (failureMode:unexpected any-count, cancelled_in_wms); purge ~4000 P&F Invalid Order Stage replay entries; ops sweep sub-Stage-70 shipments with a 500 re-PUT for doubled kit lines.

## 2026-09-11 — FUSE-1078

Choke SNAP traffic; move routing provenance to a Firestore store

Two workstreams under one ticket. Traffic: added a per-host token-bucket rate limiter (default 10 req/s, burst 20) beneath the existing 5-slot semaphore, a per-host circuit breaker (5 consecutive 5xx/network failures opens for 30s, 4xx resets the count), and bounded semaphore waits (30s, transient-nack) closing an unbounded-queue hole that could push a delivery past the 300s ack deadline. Every traffic knob was then promoted to a Terraform tfvar, so choking SNAP traffic during an incident is a 2-minute apply rather than a code PR, and retry_policy backoff was added to the 8 subscriptions that lacked it.

Routing: SNAP wipes a shipment's routing-provenance attachment (connectorId/source) whenever a retried create re-PUTs the entity, which is exactly when provenance matters most. A new named Firestore database (fuse-wms-routing) was provisioned, then every routed create began shadow-writing {connectorId, source} to it before the SNAP create — proven live: a failed create kept its provenance in the store where the attachment approach would have lost it. A ROUTING_STORE_REQUIRED flag then let a write failure hard-fail (typed RoutingPersistenceException, classified transient, Pub/Sub redelivers) instead of silently degrading — off by default; the rollback lever is an env-var flip on the revision, not a redeploy. The five routing-aware confirmation handlers (goods-in/out, pick/pack, work-order-confirmation) were switched to resolve {connectorId, source} from the store first with attachment fallback. RGA was then brought into the same parity, reversing an earlier "RGA stays scope-parity" decision after full parity across SO/PO/RGA/WO was requested. Shopify's per-line fulfillmentId (the SHL attachment) got the identical shadow-write/read treatment as its own data class subject to the same wipe-on-retry defect.

Also cleared two CI gates found blocking PRs in this stream: the adapter's audit leg was switched to honour audit-ci.jsonc instead of failing on any severity, and zocker (test-only) was moved out of prod deps after it pulled a vulnerable faker chain into the prod audit. And stopped a 404 from the shipment_methods config lookup being logged as an exception on every delivery — UserConfigService already fell back to the default shipment method on any config API failure, so the no-config case is common and was pure noise, not a correctness gap.

PR: gfs-bifrost/snap-adapter#224
PR: gfs-bifrost/snap-adapter#222
PR: gfs-bifrost/snap-adapter#215
PR: gfs-bifrost/snap-adapter#212
PR: gfs-bifrost/snap-adapter#211
PR: gfs-bifrost/snap-adapter#210
PR: gfs-bifrost/snap-adapter#209
PR: gfs-bifrost/snap-adapter#208
PR: gfs-bifrost/snap-adapter#207
PR: gfs-bifrost/snap-adapter#176
PR: gfs-bifrost/snap-adapter#175
PR: gfs-bifrost/snap-adapter#162

## 2026-09-11 — FUSE-1176

Scope the confirmation-claim key to businessId

CacheService.tryClaimConfirmation was keying its idempotency claim on queueId alone. queueId is only unique per SNAP tenant, so two businesses whose independent SNAP hosts happened to produce the same queueId within the claim's TTL could collide — silently dropping the second business's confirmation as a false duplicate, never published, never retried, nothing left behind to investigate. The Redis claim key now includes businessId; same-business claims are unaffected. Same bug class as FUSE-1165/1166 elsewhere in the FUSE-967 epic — a latent structural gap, not a symptom being chased; no incident had been observed.

PR: gfs-bifrost/snap-adapter#225

## 2026-09-01 — FUSE-866

Join work-order-confirmation shipment/receipt lines by Line key

Fixed duplicate/mislabelled Work Order Confirmation lines. Snap mirrors every work-order line onto both the S10 shipment and the R10 receipt, so the old handler concatenated component lines from the shipment with finished-good lines from the receipt, emitting one row per document per key (4 rows for a 2-line work order) with roles assigned by document rather than meaning. Lines are now joined on Snap's Line key (full outer join) for one canonical row per key; a receipt-only key (an unplanned by-product) surfaces instead of vanishing. Role now comes from the planned quantity (QtyRequired -> component, QtyOrdered -> finished good), with actuals as a tiebreak and a warn log if a line is genuinely unclassifiable. consumed now reads QtyPicked instead of QtyShipped, since a work order never despatches and QtyShipped was structurally always 0. produced/rejected now come from the matched receipt line as an enrichment lookup rather than a second row source; a component row carries no produced value and a finished-good row carries no consumed value, rather than a literal 0 that would render as a real 0 in the customer's file.

PR: gfs-bifrost/snap-adapter#204

## 2026-08-10 — FUSE-876

Exclude work orders from default confirmations; emit finished-good receipt confirmations

Work order shipments (OrderType=S10) no longer reach pick, pack or goods-out confirmations — DespatchConfirmationHandlerBase now checks the fetched shipment's OrderType before per-stage enrichment and skips a completed work order instead of publishing it as a standard customer confirmation. Finished-good receipts (OrderType=R10, auto-generated by Snap off a completed work order) were similarly excluded from goods-in confirmations via an OData filter change, alongside the existing RGA exclusion. Both were initially left unowned on Snap's outbound queue pending the emission half of this ticket. That second half then added a handler draining finished-good receipts from Snap's RECEIPT queue and publishing them to confirmation_ready as a CanonicalFinishedGoodReceipt (recordType=finished_good_receipt) — the RECEIPT queue is now partitioned three ways (RGA / FGR / goods-in), each receipt fetched by exactly one handler, discriminated on OrderType rather than OrderClass since the value-add OrderClass codes are rejected outright on some businesses. Header produced/rejected totals are summed from the lines rather than Snap's LineQty, which aggregates ordered/advised and overstates production on a short receipt. Adds the confirmation_made subscription filtered to finished_good_receipt so emitted records actually clear down. Verification against the mock harness surfaced a genuine production bug where RGA_RECEIPT_FILTER and FGR_RECEIPT_FILTER could both match the same receipt (matching on different fields); RGA_RECEIPT_FILTER now explicitly excludes the finished-good OrderType, with tests asserting the partition is mutually exclusive.

PR: gfs-bifrost/snap-adapter#168
PR: gfs-bifrost/snap-adapter#167

## 2026-08-07 — FUSE-785

Stamp kit line roles, dual-publish goods-out to confirmation_ready

Every despatch confirmation line now carries a role (standard | kit_component), derived from Snap's Level check code, so consumers no longer infer "this is an exploded kit component" from an absent Shopify fulfillment reference. Applied to pick, pack and goods-out, since all three map the same shipment.ShipmentLines array and a kit shipment passing stages 29 -> 39 -> 90 explodes on all three confirmations. An unrecognised Level code ships as stock and warns rather than dropping the line, since treating an unknown code as a kit member would silently under-fulfil something the customer ordered. Goods-out is now also dual-published to confirmation_ready tagged recordType=goods_out_confirmation, alongside its existing per-entity topic — additive and inert until a subscription matches that filter.

PR: gfs-bifrost/snap-adapter#169

## 2026-07-28 — FUSE-635

Create work orders in Snap

Added a work_order record type to the create pipeline: a filtered create_record subscription pushes to /events/v1/record/create/work_order, a successful create publishes to create_acknowledge (recordType=work_order, stage=wms_submission, source=snap-adapter), and an irrecoverable failure publishes to create_data_failure with no acknowledge. A work order is created in Snap as a value-add shipment (OrderType=S10) since Snap has no dedicated work-order entity — confirmed against the legacy Jitterbit transform and a live GADG dev ORDTYPE lookup; the canonical's docstring claim of OrdType=WO is not a code Snap recognises. Line roles map onto Snap's two quantity fields on one line array: produced finished goods ride QtyOrdered, consumed components ride QtyRequired. No service-side defaults — OrderClass, StockStatus, CustomerId, currency and shipping lane map straight through from the canonical; the only literals are the S10 create-protocol constant and LineValue: 0 (a work order has no sale value). First consumer of @gfs-bifrost/snap in this monorepo, which also closed a gap where SalesOrderService never checked for Snap's 2xx-with-Status:"Error" write rejection.

PR: gfs-bifrost/snap-adapter#155

## 2026-07-24 — FUSE-1000

Config-service becomes sole source of Snap credentials; retire local providers

Snap credentials are now resolved exclusively via config-service. Deleted FEATURE_FLAG_USE_CONFIG_SVC_CREDS, the hardcoded SNAP_API_USER_CREDS fallback map, and the also-dead USE_SNAP_CUSTOMER_CREDS flag; CustomerHttpRouter now always resolves via UserConfigService and throws SnapMissingCredentialsException immediately on a config-service miss instead of silently falling back. Verified config-service's BACKEND fragment already covered every business previously in the hardcoded secret (7/7 dev, 5/5 prod) before removing the snap-adapter-{env}-snap-creds GCP secret and its IAM binding. A follow-up deleted the deprecated LocalUserConfigProvider and its hardcoded 7-business credential list outright, along with its feature flag and the now-dead SNAP_API_USER_CREDS parsing — post-deploy logs showed 13 customers with confirmations enabled, including businesses never in the old hardcoded list, confirming RemoteConfigProvider was genuinely driving resolution. In the same window: migrated the test runner from Jest to Vitest (24 specs converted, same 295 passing count), consolidated iac to a shared iac/{env,projects} layout so both apps load the same env files with state keys preserved, and did post-monorepo cleanup removing the poller's dead SNAP_API_ACCESS_CREDENTIALS config and aligning its pnpm version pin across packageManager/mise/dockerfile.

PR: gfs-bifrost/snap-adapter#151
PR: gfs-bifrost/snap-adapter#150
PR: gfs-bifrost/snap-adapter#127
PR: gfs-bifrost/snap-adapter#126
PR: gfs-bifrost/snap-adapter#125

## 2026-07-22 — FUSE-1050

Enrich RGA confirmation lines with batch/expiry from Stock Detail

ReturnGoodsAuthorizationHandler now fetches Stock Detail (GET /v2/stockdetail via fetchStockDetail(consignmentId)) per receipt, keyed on receipt.ConsignmentId with a fallback to ReceiptId — the same source PackConfirmationHandler already reads for S39 batch/expiry/serial capture. Lines are enriched with identifiers.batchId, product.upcDescription and dates.expiry, matched to a line by SKUId (a flat map lookup; RGA receipts don't split a SKU across multiple batches, unlike goods-in). A Stock Detail fetch failure is logged and the confirmation still goes out with no batch/expiry rather than being dropped. Stock Detail fetches are bounded with chunkPromises (chunk size 25) instead of an unbounded Promise.all, matching the goods-in/goods-out handlers. Bumps @gfs-bifrost/types to ^7.7.0 for the new CanonicalRGALine fields.

PR: gfs-bifrost/snap-adapter#143

## 2026-07-14 — FUSE-892

Clear down pick/pack confirmations from Snap OBQ

Added two confirmation_made push subscriptions filtered to recordType=pick_confirmation / pack_confirmation, reusing the existing 202-first clear-down (PATCH /v2/snapoutbound/{queueId}/processed). Irrecoverable clear-down failures (and unclearable records) now publish to confirmation_data_failure via a new ConfirmationErrorService, then ack (never nack) the source message so a redelivery can't re-poll a duplicate — closing the pre-existing TODO(FUSE-901). Transient Snap failures are emitted retryable; a failed failure-publish is error-logged and metered. Clear-downs get their own metrics (CONFIRMATION_HANDLED / CONFIRMATION_FAILED), kept off the create-flow event_handled. Requires @gfs-bifrost/types ^7.6.0 for pick/pack in FailureUseCase.

PR: gfs-bifrost/snap-adapter#138

## 2026-07-07 — FUSE-952

Absorb snap-adapter + snap-queue-polling-service into one monorepo

Restructured snap-adapter to an apps/ + iac/ monorepo layout (mirrors shopify-connector), moving code/ to apps/snap-adapter/ and iac/ to iac/snap-adapter/ as a pure git mv (history preserved, terraform state keys unchanged). snap-queue-polling-service — the read/egress poller — was then absorbed into the same repo as apps/snap-queue-polling-service + iac/snap-queue-polling-service (squash import; history stayed in the archived snap-queue-polling-service repo). Workflows were split per-app with path filters. The poller's dead SNAP_API_ACCESS_CREDENTIALS plumbing was dropped in the same pass — it parsed into config but had zero readers, so no SNAP secret needed provisioning for it at cutover. A follow-up fixed the adapter's image build, which broke because the relocated .dockerignore started excluding .env from the build context.

PR: gfs-bifrost/snap-adapter#124
PR: gfs-bifrost/snap-adapter#123
PR: gfs-bifrost/snap-adapter#122

## 2026-07-03 — FUSE-984

Make SO/PO/RGA creates idempotent under Pub/Sub redelivery

A Pub/Sub redelivery now upserts the same SNAP record instead of creating a duplicate (prod evidence: WILDSMITH SO-26839 produced two shipments). All three create paths (sales order, purchase order, RGA) derive a deterministic id from the customer's OrdRef1/OrdRef2 reference pair. PO/RGA creates switched from POST /v2/receipts to PUT /v2/receipts/{id} for a keyed upsert, since a POST with a colliding client id silently mints a fresh AUTO id. A record missing its idempotency key now fails loud with a new terminal invalid_deterministic_id mode, published to create_data_failure, rather than falling back to a random id that could collide across orders. The compensating delete-on-error for SO/PO was removed, since under deterministic keys a rejected re-PUT would otherwise delete the live record an earlier delivery created. Create handlers now log messageId and deliveryAttempt on every log line. Re-sending a changed record now updates the SNAP record in place on all three paths (modify-via-resend).

PR: gfs-bifrost/snap-adapter#120

## 2026-06-29 — FUSE-616

Remove businessId casts and fallbacks

Removed the `as string` casts from the RGA service now that businessId is required on CanonicalRGA (@gfs-bifrost/types@7.0.0) rather than optional. Confirmation clear now prefers identifiers.businessId over identifiers.bizId, keeping bizId only as a compat fallback for in-flight Pub/Sub messages predating the 7.0.0 deployment. Bumped @gfs-bifrost/types to ^7.0.0.

PR: gfs-bifrost/snap-adapter#112

## 2026-06-23 — FUSE-794

Bifrost metadata + logger traceability

The acknowledge, error and release producers now stamp source="snap-adapter", recordType and recordId onto the outbound BifrostMessage.metadata (via extractRecordId) — previously these rode only on Pub/Sub attributes; the recordType subscription discriminator is unchanged, the envelope field is log-enrichment only. At the create and confirmation decode points the controller now lifts inbound metadata.source and metadata.connectorId onto the correlation namespace alongside correlationId/businessId/flow/recordType/recordId, so every downstream log line carries them under requestor. CorrelationDetails gained optional source/connectorId fields. Bumped @gfs-bifrost/types to ^6.3.0 for the additive metadata fields, and narrowed releaseEvent's signature from unknown to BifrostMessage<Record<string, unknown>> so the release re-emit can enrich the envelope without a risky cast.

PR: gfs-bifrost/snap-adapter#108

## 2026-06-11 — FUSE-953

Replace VPC connector + NAT with Direct VPC egress

Cloud Run now uses Direct VPC egress (network_interfaces on the existing subnet) instead of a Serverless VPC Access connector, keeping the same private-range reachability to Redis at zero fixed cost. Egress switched from ALL_TRAFFIC to PRIVATE_RANGES_ONLY, so public calls (SNAP API, Pub/Sub, Datadog) leave via Cloud Run's managed egress rather than being hairpinned through the VPC. The Cloud Router, NAT gateway and VPC connector — fixed-cost resources billed 24/7 — were deleted; the VPC and subnet remain since both Redis's authorized_network and direct egress still need them.

PR: gfs-bifrost/snap-adapter#101

## 2026-06-05 — FUSE-816

Subscribe to create_record for RGA; move to /events/v1 grammar

Added a filtered subscription on the cross-entity create_record topic (attributes.recordType = "return_goods_authorization") so RGA flows through the standard SnapRouter framework with a stub ISnapService (createInSnap no-ops until FUSE-848; no create_acknowledge is published for empty resourceIds). The whole events API was hard-cut onto /events/v1 with platform vocabulary (POST /events/v1/record/create/:recordType, /events/v1/confirmation/made/:confirmationType, /events/v1/config/revision) — the kebab→snake pathToEntity normaliser was deleted and legacy/kebab paths now 404, with all 8 Terraform push endpoints moved to match. Confirmation metric/log type tags changed value (kebab to snake_case). A follow-up fixed the black-box test suite, which was still posting to the removed kebab paths and had gone undetected because CI was killed on the original PR.

PR: gfs-bifrost/snap-adapter#99
PR: gfs-bifrost/snap-adapter#98

## 2026-05-18 — FUSE-799

Emit BifrostFailure on Snap creation failure

Snap creation failures are now published as a structured BifrostMessage<BifrostFailure> on the create_data_failure topic, using the contract from @gfs-bifrost/types 2.11.0 (RFC FUSE-836). Landed in three stages: a new EntityErrorService first published a placeholder body to an entity_error topic with a use_case attribute; a follow-up pointed the adapter at the canonical create_data_failure topic (bifrost-pubsub) with use_case reflecting the real entity type; a final pass replaced the placeholder body with a real BifrostFailure built by a new pure mapper (to-bifrost-failure.ts) that composes classifySnapFailure output into the discriminated FailureError union (validation / dependency / infrastructure), and widened the publish attributes to the full FailureAttributes shape (useCase / stage / source / customer). The old DeadLetterService and its dead formatError path were dropped as redundant with classifySnapFailure.

PR: gfs-bifrost/snap-adapter#86
PR: gfs-bifrost/snap-adapter#84
PR: gfs-bifrost/snap-adapter#83

## 2026-04-21 — FUSE-770

Always release on failure

Removed the shouldRelease and canResubmit fields from SnapFailure and stripped them from every branch of classifySnapFailure — mode, statusCode and detail are retained for observability. handleSnapFailure now calls releaseService.releaseEvent unconditionally on any classified failure, removing the "retaining event in deduper" else-branch. Previously nmfc_missing, nmfc_fetch_failed and unexpected failures were not released; now every failure mode releases.

PR: gfs-bifrost/snap-adapter#79

## 2026-02-27 — FUSE-667

Handle stock adjustment made message

Added a subscription and handler for the stock adjustment made message, plus a Zod schema to make what's confirmable clearer. Migrated the service to pnpm in the same PR.

PR: gfs-bifrost/snap-adapter#60

## 2026-02-05 — FUSE-706

Config-service driven credentials for Snap

Moved SNAP credential resolution to config-service instead of the per-user AxiosSingleton approach. Removed the AxiosSingleton class and the old per-user credentials feature flag, added backlink handling for backend events, and added a cache-aside pattern for fetching upstream credentials. CustomerHttpRouter now resolves credentials via config-driven lookup.

PR: gfs-bifrost/snap-adapter#59

## 2025-11-17 — FUSE-487

Use customer instances; add Snap API credentials secret

Moved the adapter onto per-customer SNAP instances. Added a Secret Manager secret for the Snap API user credentials, granted the Cloud Run service account access to its latest version, and injected it into the Cloud Run environment.

PR: gfs-bifrost/snap-adapter#48
PR: gfs-bifrost/snap-adapter#47

## 2025-11-14 — FUSE-327

ILG Datadog integration

Added ILG Datadog integration to the service.

PR: gfs-bifrost/snap-adapter#46

## 2025-11-13 — FUSE-446

Set shipping address ID to add1

SalesOrderService now uses the existing shippingAddressId from CanonicalSalesOrder when generating the addressId for SnapShipment, instead of always minting a new one. Falls back to generating a new unique ID when shippingAddressId is absent.

PR: gfs-bifrost/snap-adapter#45

## 2025-10-20 — FUSE-409

Update @gfs-bifrost/types to v1.1.5, rename Value field

Updated @gfs-bifrost/types to v1.1.5 and renamed the 'Value' field to match the new type shape.

PR: gfs-bifrost/snap-adapter#40

## 2025-10-09 — FUSE-268

Move shared types to @gfs-bifrost/types

Moved shared types to @gfs-bifrost/types and updated the SNAP service implementations to use them.

PR: gfs-bifrost/snap-adapter#36

## 2025-10-08 — FUSE-250

Add config revision event handling

Added config revision event handling to the Snap Adapter.

PR: gfs-bifrost/snap-adapter#37

## 2025-09-22 — FUSE-214

Interim fetch ID on payload

Added an interim fetch ID to the outbound payload.

PR: gfs-bifrost/snap-adapter#27

## 2025-09-15 — FUSE-221

Fix duplicate record creation in SNAP

Fixed a bug causing records to be created twice in SNAP.

PR: gfs-bifrost/snap-adapter#21

## 2025-09-05 — FUSE-203

Add shipment lookups for connector address resolution

Added SNAP shipment lookup support to the adapter, using an interim fetch ID on the payload to resolve shipment records for connector use.

PR: gfs-bifrost/snap-adapter#17

