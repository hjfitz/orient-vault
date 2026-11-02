# poller-deferral-semantics — which poller behaviours rely on the OBQ row staying put

Label: poller-deferral-semantics. Date: 2026-09-29. Read-only.

Refs read:
- snap-adapter@3c1578b3c6f813b61fec4dfe5e5bc4f250d9bd99 (origin/master; worktree `.claude/worktrees/early-consume-feasibility`), app `apps/snap-queue-polling-service/src` (paths below are relative to that dir unless stated). Also `iac/projects/snap-queue-polling-service/pubsub.tf`.
- Vault: Engineering/snap-adapter/{architecture,known-context,operations}.md + explainers/work-order-family-confirmations.md (verified 2026-09-13/14, sha a4f2f3f); Engineering/snap-queue-polling-service/{architecture (verified 2026-09-21 @469573c),known-context,overview,operations}.md and plans/FUSE-1063-*.md; Bifrost/"Kit Confirmations & Short-Ship (FUSE-785).md"; Bifrost/"SNAP Polling Log Volume"/{Overview,Migration State}.md.
- /home/hjf/code/fuse/snap-api.openapi.yaml (SnapOutbound entity).
- Fuse MCP lookup-topic stock_adjustment. Datadog metrics (prod, `environment:prod`, 24h / 7d / 8d windows queried 2026-09-29 ~10:00Z) and log patterns for `service:snap-polling-service`.

## 0. Headline

1. The poller almost never clears anything itself. The only two self-clear sites are `ConfirmationDisposer.clearFromOutboundQueue` (goods-out cancelled shipment: goods-out handler line 92; goods-in all-lines-zero-qty: goods-in handler line 106), both log-only terminal exits (tag DROPPED_CONFIRMATION, no collector/replay record). Everything else - published or not - stays on the OBQ. Consequently EVERY exit from the poller that is not "published + downstream confirmation_made" is currently "leave the row, retry next cycle". There are about 20 of them (table in section 3). Under early consume each of them needs an explicit terminal decision.
2. Two of the deferrals are deliberate, documented features: stage-1 business gate and late connector gate (FUSE-1063 plan Intent: "An ineligible confirmation is left unpublished and stays in SNAP's outbound queue, picked up automatically once the connector catches up"). One is a documented, accepted leak (work-order rows at stage 29/39, FUSE-1062). The rest are accidental reliance on the row staying (retry-by-re-poll), several of them silent (no log, no metric).
3. There are live perpetual re-announcers in prod today: ~16 stock-adjustment rows are re-published every 10 minutes (claim TTL = 600000 ms) because nothing downstream clears them; ~30 despatch rows likewise. Datadog evidence in section 5.
4. Early consume is only safe AFTER a durable handoff: consume after `publishMessage` resolves (not at find). Consuming at find (before enrichment/gates/publish) makes each of the exit paths in section 3 a loss.

## 1. Poll pipeline as read (evidence)

Two-stage saga.
- Stage 1: scheduler -> `POST /event/poll/schedule` -> `PollingService.registerCustomerForConfirmations` (core/polling/polling.service.ts:19-38) -> `getAllConfiguredBusinesses()` (core/config/remote-config.provider.ts:62-102) -> chunks of `CUSTOMER_CHUNK_SIZE` (default 2, config/config.schemas.ts:81) -> one `snap_poll_customer` message per chunk. `deriveCredentialsForCustomer` drops silently any business without a backend (polling.service.ts:45-53, 91-97).
- Stage 2: push subscription `snap_poll_customer.v1.sub` -> `POST /event/poll/confirmations` -> `PollingService.handleConfirmations` (polling.service.ts:70-89): `getConfirmations` (drain + map + validate + group + gates) then `announceConfirmations` (claim + emit). Subscription has `ack_deadline_seconds = 600` and NO `dead_letter_policy` / `retry_policy` (iac/projects/snap-queue-polling-service/pubsub.tf, poll_subscription block): an erroring stage 2 is redelivered immediately and indefinitely; there is no DLT for the poll message.
- Drain: `OutboundQueueDrain` -> three `QueueLane`s (DESPATCH, RECEIPT, STOCK_MOVE). `SnapApiHttpClient.fetchFromOutboundQueue` (adapters/snap/api.client.ts:194-217) reads `GET /v2/snapoutbound?$top=1000&$filter=Transaction eq '<lane>'` - no `$orderby`, no BizId filter (shared hosts return co-tenant rows), no paging, `todo: make this configurable`.
- `QueueLane.drainForClient` (core/snap/confirmations/queue-lane.ts:80-108): fetch -> `dropClaimed` (skip rows whose Redis claim key is live) -> resolve entries -> each registered consumer's `mapOwnedEntries(...).catch(...)` which logs `ConfirmationMappingEvent.Failed`, bumps `snap.poll.failure`, returns `[]` (lines 90-100). Rejections of the whole client drain are only logged + `poll.failure` (lines 54-67).
- Handlers then `confirmationsToCanonical` -> `validateCanonicalConfirmations` -> `groupByCustomer` inside ONE try/catch per type for the whole array (confirmations.service.ts:88-138); the catch is `logConfirmationError` (log only).
- Late gate `resolveRoutingSources` (confirmations.service.ts:155-237), then `announceConfirmations` (271-362): per group `claimConfirmations` (SET NX per `identifiers.queueId`, key `confirmation-claim:{customer}:{queueId}`, TTL `REDIS_CONFIRMATION_CLAIM_TTL_MS` default 600000, config/config.schemas.ts:64) -> `pubsubRouter.emit` (awaits server-acked `publishMessage`, adapters/pubsub/pubsub.router.ts:131-144) -> for routing-aware types with no origin, one informational `BifrostFailure` per record to `confirmation_data_failure` (lines 336-358). Claim is set BEFORE emit; if emit throws the claim persists for up to 10 min and the row is skipped by `dropClaimed`/duplicate-check until it lapses, then re-announced (the OBQ row is the recovery).
- The poller marks processed only via `SnapApiHttpClient.clearFromOutboundQueue` = `PATCH /v2/snapoutbound/{queueId}/processed` (api.client.ts:153-157), reached only through `ConfirmationDisposer` (swallows its own error: logs "Confirmation drop failed" and returns; the row then just stays).
- Everything else is cleared by snap-adapter on `confirmation_made` (architecture docs; snap-adapter `POST /confirmation/made/:recordType`). Out of scope here.
- OpenAPI: SnapOutbound has `DateProcessed`; `GET /snapOutbound/next` is documented as "next open (unprocessed) record" - so processed rows may be retained on the SNAP side with `DateProcessed` set (unverified; see open questions). The spec itself notes uncertainty whether `/{id}/processed` and plain `PATCH /{id}` are distinct operations.

## 2. The known leads, verified one by one

### 2.1 Stage-1 gate (business not polled at all)
- Code: remote-config.provider.ts:62-102. A business is polled iff `backend.broadcastConfirmations` OR the cached business index says `hasConfirmationEnabledConnector === true` (fetched from config-service `getAllBusinesses`, lines 140-157; `connector.confirmationsEnabled === true`, absent = false). Otherwise it is skipped with an aggregate info log and `snap.poll.skipped_ineligible_business{businessId}`.
- Row effect: rows never read; they accumulate on SNAP. Documented as intended (Engineering/snap-queue-polling-service/architecture.md "Config & credentials"; FUSE-1063 Intent). "Enabling releases the backlog" is literally how it behaves: next stage-1 after a CONNECTOR revision event flips the cached boolean.
- Fails open: unreadable index -> every configured business polled (lines 104-137, `snap.poll.business_index_unavailable`), so the late gate becomes the only gate then.
- Cache: index set with default network TTL (`REDIS_TTL_MS` default 604800000 = 1 week; config.schemas.ts:63) and refreshed only on CONNECTOR backlinks (`saveBacklinks` 393-436). If a revision event is lost, an enable could take up to a week to release a backlog (medium-low confidence; not observed).
- Scale (prod, Datadog `snap.poll.skipped_ineligible_business`, 24h): ~24 prod businesses skipped on essentially every one of ~719 cycles (gadg, academic, phlur, bfa, drsams, drsamspl, lisapl, lisauk, sistaco, aymstudio, escentric, escentricpl, shackleton, eadem, nuzest, dockbay, jolovespl, discovered, ...). Their OBQ backlog depth is unknown (would need SNAP read access with tenant creds; not done).
- If marked processed at find time: unaffected as long as skipped businesses are still not polled. But it is the one place where "not consuming" is the product decision (customer disabled confirmations; backlog is the deferred delivery). If an operator later enables a connector, the poller will then read up to 1000 rows/lane/business per cycle of potentially stale rows. No change from early consume; but note there is NO record anywhere (collector/replay) of these confirmations - they exist only as SNAP rows.

### 2.2 Late gate (connector not enabled)
- Code: `resolveRoutingSources` confirmations.service.ts:155-237. For a group with `routing.connectorId`: `resolveConnectorConfirmationsEnabled` (remote-config.provider.ts:231-263, Redis-cached string "true"/"false", refreshed by CONNECTOR backlink, `fetchAndCacheConnector` 321-352). If not enabled and not `broadcastConfirmations`: warn `Withholding confirmation` (tag DROPPED_CONFIRMATION) + `snap.confirmation.withheld_ineligible_connector`, return null (lines 189-203). The group is dropped BEFORE `claimConfirmations`, so it is not claimed and is re-enriched on EVERY poll (2 min). Confirmed by plan evidence: "PHLUR good_in x4 still enriches every cycle: withheld by the late gate, never claimed".
- Intent: deferral is deliberate ("stays in SNAP's outbound queue, picked up automatically once the connector catches up", FUSE-1063 Intent). Lever B (pre-read routing per entry to drop before enrichment) was designed and rejected.
- It catches the mixed-business case (one enabled + one disabled connector, e.g. PURDYFIGG) because connector identity isn't knowable from a raw queue row (rows carry only XDoc/Key/Transaction; architecture.md).
- Prod evidence (7d): `withheld_ineligible_connector` bfa/good_in 2880 (09-22) + 1024 (09-23) then zero. Since the stage-1 gate landed (merged 2026-09-21, #240) the business is skipped instead. Live withholds today are near zero in prod (24h = none).
- If marked processed at find time: the withheld confirmations are LOST (never published, never in collector/replay); the FUSE-1063 "backlog released when enabled" semantics disappear. If consumed only after publish (not at find): unchanged.

### 2.3 Unresolved connector (deleted / config-service unavailable)
- Same function, catch at lines 204-230: `FuseConfigApiException.connectorResolutionFailure` = `"gone"` (connector no longer exists) or `"unavailable"` (config call failed). Unless `broadcastConfirmations`, group withheld with `IngestEvent.RecordDropped` (log) + `snap.confirmation.withheld_unresolved_connector{type,businessId,reason}`; row stays and is retried every cycle. Any other exception rethrows -> `getConfirmations` throws -> stage 2 HTTP error -> Pub/Sub redelivery of the whole poll.
- `"gone"` is PERMANENT (a deleted connector never returns) yet it is treated like a transient: retried forever, no terminal record, no failure envelope. Prod 7d: reason=gone pick 4522, pack 4522, good_out 1939, RGA 8 (all on 09-22/09-23 only, then zero - again masked by stage-1 skip of that business). This is evidence of a live infinite-retry-on-permanent-error defect pattern that only the stage-1 gate is now hiding.
- `"unavailable"` is the transient class (config-service outage) - a clear case that MUST defer, because a config-service outage would otherwise convert to permanent loss if rows were already consumed.

### 2.4 broadcastConfirmations override
- Business-level flag on the SNAP backend record (`SnapBackendConfig.broadcastConfirmations`). Effects: (1) stage-1: polled even with no eligible connector (remote-config.provider.ts:74); (2) late gate: ineligible connector no longer withholds (confirmations.service.ts:185); (3) unresolved connector no longer withholds (212-214); (4) publish attribute `broadcast=true` to all connectors (buildEmitterAttributes 252-269).
- So for broadcast businesses "disabled = deferred" does not apply at all; a disabled connector is bypassed at the poller and the confirmation is published anyway. Row clearing then depends entirely on some connector emitting `confirmation_made`. Not a deferral, but an important caveat: for broadcast businesses the poller already has no OBQ-based gate, and the effective safety net is only the OBQ re-announce when no connector clears.

### 2.5 Manual-origin (no routing provenance)
- `groupByCustomer` key `customer::connectorId::source`; routing resolved store -> attachment -> miss (canonical-confirmation.handler.base.ts:241-260, `snap.routing_lookup.hit|fallback_attachment|miss`). No origin -> `buildEmitterAttributes` sets `broadcast=true` (confirmations.service.ts:261-266), and for the 7 routing-aware types `announceConfirmations` (336-358) increments `fuse.confirmation.manual_origin_broadcast` and publishes one informational business_rule failure `no_originating_connector` per record via `ConfirmationFailurePublisher` (confirmation-failure.ts:80-96) to `confirmation_data_failure`. `stock_adjustment` is deliberately excluded (ROUTING_AWARE_TYPES, confirmation-failure.ts:36-45) since it never has provenance.
- This is a TERMINAL outcome at first publish (published, claimed, broadcast). It does not depend on the row staying for correctness. BUT the failure record is re-published on EVERY re-announce (each 10-min claim lapse) because the row stays: prod 7d `manual_origin_broadcast` sistaco/good_out 7029 (09-22) + 2484 (09-23), drsams 473+163, lisauk, lisapl, academic, champo (still live: 33/15/22/35/-/107/80 per day), wildsmith, purdyfigg. Each is a re-publish noise event of a handful of stuck rows, not new orders (for example sistaco ~7000/day = ~6 rows x 144 re-announces). Under early consume this stops.
- Manual origin can be a false positive: snap-adapter's routing store write is non-fatal in shadow mode (`ROUTING_STORE_REQUIRED` off; snap-adapter architecture.md), so a Fuse-created order whose Firestore write failed AND whose SNAP attachment was wiped by a keyed re-PUT is classified manual-origin and broadcast. Terminal, but mis-targeted (potentially to the wrong connector). Not OBQ-dependent.
- Firestore reader ERROR is a defer (2.6), a MISS is not.

### 2.6 Routing provenance lookups failing
- `FirestoreRoutingMetadataReader.getMany` (adapters/firestore/routing-metadata.reader.ts:48-62): errors propagate; comment says "the poll aborts before anything is claimed and the next cycle retries" - explicit reliance on the row staying. `DespatchConfirmationHandlerBase.mapOwnedEntries` (56-67) and `ReceiptConfirmationHandlerBase` (167-182) meter `snap.routing_lookup.error{lane}` and rethrow; the throw escapes the page loop, so the whole consumer for that business/lane is `[]` for the cycle (QueueLane catch, queue-lane.ts:90-100). Vault known-context: "Reader-error vs miss is load-bearing... Never let a reader error silently degrade to a miss/broadcast".
- SNAP attachment fallback: goods-out/pick/pack/WOC `fetchShipmentAttachments` throws on failure (row-level failure inside `mapEntriesInIsolation` -> log `ConfirmationMappingEvent.Failed` + `snap.confirmation.map_skipped`, row stays). RGA swallows both stock-detail and attachment failures and degrades (return-goods-authorization handler 240-270): RGA publishes without batch/expiry/routing attachment on a transient fetch error, and the row is later cleared downstream so the degraded record is final (existing data-quality defect, independent of early consume; note that it means an attachment fetch failure can flip a routed RGA to manual-origin broadcast).
- Prod 7d: `routing_lookup.error` = none; `routing_lookup.miss` good_out = 36,732 (inflated by re-maps of stuck rows), good_in 11.
- If marked processed at find: a Firestore or SNAP-attachment outage during a poll would strand every row read that cycle with no publish. Must not consume before routing resolved and publish acked.

### 2.7 Stock adjustments (no gate)
- `StockAdjustmentHandler` (core/snap/confirmations/stock-adjustment.confirmation-handler.ts): `routingAware` never applies; `groupByCustomer` therefore has no routing; late gate is skipped because `group.routing?.connectorId` is absent (confirmations.service.ts:160-162); published with `broadcast=true`. Stage-1 still applies. No per-connector `confirmationsEnabled` gate applies to stock adjustments at all.
- Topic: `stock_adjustment_ready` (dedicated, `BifrostBulkMessage<CanonicalStockAdjustment>`), subscribers collector, shopify-connector, sftp-connector (Fuse MCP lookup-topic). Made side `stock_adjustment_made` (publishers shopify-connector, sftp-connector; subscriber snap-adapter clears; collector bespoke).
- Behaviour: rows unaccepted by any connector are re-published every claim lapse. Datadog (prod, 2h, 10-min buckets, `fuse.confirmation.published{type:stock_adjustment}`): constant 16-17 per bucket; `snap.outbound.claimed_entry_skipped{lane:stock_move}` 64-65 per bucket = 16 rows x 4 skipped 2-min cycles + 1 republish cycle. 24h total published 2018 = ~14 rows x 144/day. So ~16 stock movements are stuck and re-announced forever, ~2.3k publishes/day. Whether they are stuck because no connector has a stock-adjustment mapping/enabled (business decision) or because a connector fails silently is not determined here.
- Local drops that leave the row (all silent-to-collector): direction cannot be determined -> `logger.warn` and drop (handler:116-133; moveTypes not in the table, SOWN/SADJ with ambiguous owners); `CanonicalStockAdjustmentSchema` invalid -> `ConfirmationParsingEvent.Failed` + `snap.confirmation.unparseable` and dropped (35-54). No failure published. These are exactly the states where "consume" loses data unless a failure is recorded. Prod 7d `confirmation.unparseable` and warn `Stock movement dropped` = none observed (30 min sample), so currently rare/never.
- No cross-tenant filter on the movement lane (`resolveMovementEntries`, core/snap/outbound-queue/movement.entries.ts) unlike despatch/receipt (`isCrossTenant`). On a shared SNAP host, business A's client reads business B's movement row; group.customer = B (`identifiers.businessId = BizId`) is then looked up in the chunk's enabled set (confirmations.service.ts:100-109): if B is not in A's chunk it is dropped SILENTLY (no log, no metric), if B is in the chunk it publishes under B. Under early consume A's client could mark B's row processed. See gap.
- Per-item movement fetch: `fetchStockMovement` is a plain `Promise.all` per 50-chunk; one 404/5xx rejects the entire movement drain for that business for the cycle (poison-pill risk), row stays.

### 2.8 Kit components / Level 20
- The poller never drops or defers them. `resolveLineRoles` (kit-line.discriminator.ts) stamps `role: kit_component` for Level "20", `standard` otherwise (unknown level -> warn + standard); pick, pack and goods-out canonicals carry `role`. The kit short-ship/`nothing_to_fulfill` handling is downstream in shopify-connector (Bifrost note "Kit Confirmations & Short-Ship (FUSE-785)"; FUSE-785 #214, FUSE-1057 #254). No OBQ reliance in the poller for kits. The one downstream reliance worth noting: shopify-connector "acks cleanly" the solo-short-shipped kit, which must still produce `confirmation_made` for the row to clear; under early consume that is moot.

### 2.9 Businesses not in enabledCustomers / unknown business ids
- `enabledCustomers` passed to `getConfirmations` is simply the chunk's backend configs (polling.service.ts:76-81). `getConfirmations` drops any group whose `group.customer` (data BizId) is not in that map with NO log, NO metric (confirmations.service.ts:100-109). `groupByCustomer` uses exact `identifiers.bizId` / `businessId`.
- Cross-tenant logic elsewhere trims/uppercases for SNAP's padded fixed-width fields (cross-tenant.ts) but this lookup is exact-match: a BizId with different case/padding vs config `businessId` would vanish silently and stay on the OBQ forever. Latent, not observed (low confidence).
- Rows for businesses not configured at all (no backend record) are never read (no client).
- `dropClaimed` uses `snapClient.businessId` for the claim key read while announce uses `group.customer`; if they differ the pre-check never matches (only wasted enrichment; announce claim still dedupes).

### 2.10 Handlers not registered / `filter` argument
- `if (!handler) continue` (confirmations.service.ts:84-86) is unreachable in production: raw types come only from registered lanes. The `filter` argument is used only by `DebugController.handleCheck` (`["good_out"]`, http/controllers/debug.controller.ts:89-93), which does not announce - but it runs the full mapping, so it still triggers the disposer's PATCH for cancelled goods-out rows (dry-run has a write side effect on SNAP).
- Manual `/debug/trigger` runs the full announce path with no filter.

### 2.11 Rows no handler owns (silent, never consumed)
- Despatch: `mapOwnedEntries` filters `entry.key.Stage === this.stage && isOwned` (despatch-confirmation.handler.base.ts:49-51): handlers own only stages 29 (pick), 39 (pack), 90 (goods-out / WOC). A despatch row at any other stage is owned by nobody -> never read, never claimed, never cleared, no log, no metric.
- Work orders (`OrderType S10`) at 29/39 are explicitly excluded from pick and pack (`isOwned`, pick handler 43-45, pack handler 45-47) ("Left on the queue") - FUSE-1062 "work order queued at 29/39 is never cleared", known and accepted; status of a fix unconfirmed (vault known-context). They are re-resolved (shipment batch fetch) every cycle for the life of the row. Not in Datadog as a specific metric; count unknown.
- Receipts: RECEIPT lane has no Stage filter; `isGoodsIn` is the catch-all default for anything that is not R10 or an RGA OrderClass (return-goods.discriminator.ts:43-47), so every receipt row is owned by some handler (and every stage is announced as a confirmation - whether SNAP emits several rows per receipt at different stages was not verified).
- Row whose record SNAP does not return (`resolveDespatchEntries` 37-39, `resolveReceiptEntries` 37-39: `if (!shipment) return []`, comment "dropped, not failed - the queue item stays put"): silent, no metric. A purged/archived/non-visible shipment leaves a permanent orphan row.
- Cross-tenant despatch/receipt rows are skipped with `snap.outbound.cross_tenant_entry_skipped` (prod 7d nuzest despatch 202, receipt 1) and MUST stay for the owning tenant's own poll.
- `$top=1000` with no ordering: any permanent orphans (above) plus stuck rows consume the 1000 window; if a business accumulates >=1000 unresolvable rows per lane, fresh rows may never be returned (depends on SNAP default order, unverified). Relevant to the ~24 stage-1-skipped prod businesses whose backlog depth is unknown.

### 2.12 Poison rows / head-of-line blocking
- One malformed `Key` throws inside `resolveDespatchEntries`/`resolveReceiptEntries` (`parseShipmentKey`/`parseReceiptKey` via `ZodUtils.parse`, no per-item try) -> the whole lane drain for that business rejects -> only a `SNAP poll attempts failed` warn + `snap.poll.failure` (queue-lane.ts:54-67). Every other row for that business+lane is blocked every cycle until someone clears the bad row. Row stays.
- One record that throws inside `confirmationsToCanonical` (any handler) aborts the entire type's raw array for ALL businesses in the chunk (`try` wraps map+validate+group for the whole array, confirmations.service.ts:88-138, catch = log only). Row-level isolation exists only around `mapConfirmation` (SNAP reads), not around canonical mapping.
- `snap.poll.failure` prod 7d = none observed for polled businesses; `Outbound queue fetch failed` ~90 per 30 min across environments (chronic failing business, likely dev tenants per the Log Volume programme; env not separable in that pattern query).

### 2.13 Enrichment / transient errors (defer by throwing)
- Goods-out: `fetchStockConsignment`, `fetchStu`, `fetchDespatchStock`, `fetchShipmentAttachments` all throw on error -> entry-level isolation -> log + `confirmation.map_skipped`, row stays (goods-out handler 100-141; map-entries-in-isolation.ts).
- Pick/Pack: `fetchStockDetail`/`fetchStu` throw likewise; pick/pack rely on data "unrecoverable once the order progresses" (handler comments) - the batch/expiry is captured at poll time; a delayed retry after the shipment has progressed can capture different stock detail (existing hazard, already true today).
- Goods-in: `fetchStockConsignment` failures are silently swallowed by `partitionSettledPromises` (handler 116-125): if some consignment fetches fail transiently the confirmation is published with a PARTIAL consignment set (no retry, cleared downstream) - existing data-loss defect. If ALL fail / none found: warn "Stock consignment not found for receipt" and `return null` -> `snap.confirmation.hanging{good_in}` via `onMapped` (prod 7d = 2), row stays. Whether "not found" is SNAP eventual consistency (transient) or permanent is not established.
- SNAP circuit open or fetch failure of the OBQ read itself: `fetchOutboundQueue` returns `[]` (fetch-outbound-queue.ts:31-47), nothing happens; row is untouched (safe under either model).
- Goods-out cancelled shipments (`Status "01"`) and goods-in with zero-received lines: cleared by the poller itself (the only two self-consume paths; log-only record; `RecordDropped` event). Pick/pack/WOC do not check cancelled status and publish for cancelled shipments. Also `handleLineDrops` (goods-in 482-520) removes zero-qty lines from a published confirmation (log event only).

### 2.14 Publish path
- `emit` failure after `claimConfirmations` succeeded: claim TTL 10 min -> row invisible to the poller for up to 10 min, then re-announced; stage 2 returns non-2xx -> immediate Pub/Sub redelivery (no dead-letter, no backoff) hits `dropClaimed` (claimed) and skips. Recovery therefore relies on the OBQ row + claim lapse.
- Claim `unavailable` (Redis down) fails OPEN (publishes anyway; `snap.confirmation.claim.fail_open`, prod 7d none). Duplicates then possible; OBQ still has the row.
- INC-30 background: redelivery of the stage-2 message re-fetches and re-publishes (>1000 dupes observed); durable fix is the claim.
- After a successful `emit` group N and a throw on group N+1 the loop aborts; claims for later groups were not yet set; redelivery re-drains and republishes remaining groups; earlier groups are claimed. Correct today because rows remain.

## 3. Exit-path table (poller-side)

Legend: dep = today's recovery depends on the row remaining on the OBQ. "If processed at find" = if the SNAP row were marked processed when the poller reads it.

| # | Exit / path | Trigger | Today | Recorded where | Terminal | Silent | dep | If processed at find |
|---|---|---|---|---|---|---|---|---|
| 1 | Stage-1 skip | business has no confirmationsEnabled connector and no broadcast | not polled; rows accumulate on SNAP | metric `poll.skipped_ineligible_business` + aggregate info log | no (deferred by design) | no | yes (feature) | n/a - never read; product decision |
| 2 | Stage-1 fail-open | business index unreadable | polls everyone; late gate takes over | log+metric | n/a | no | n/a | n/a |
| 3 | Late gate: connector disabled | routed group, connector `confirmationsEnabled!==true`, no broadcast | withheld, unclaimed, re-enriched every poll | log warn + metric `withheld_ineligible_connector` | no | no (but no durable record) | yes (feature) | LOST (never published, nothing in collector/replay) |
| 4 | Connector gone | config-service says connector deleted | withheld forever, retried every poll | log + metric reason=gone | no (should be terminal) | no | yes (accidental) | LOST |
| 5 | Connector unavailable | config API error | withheld this cycle | log + metric reason=unavailable | no (transient) | no | yes | LOST on a config outage |
| 6 | Other exception in resolveRoutingSources | non-connector-resolution error | throws -> stage 2 5xx -> redelivery | error middleware log | no | no | yes | LOST |
| 7 | Broadcast override | `broadcastConfirmations` | bypasses 3,4,5 and stage-1; broadcast attr | published | yes at publish | no | n/a | safe after publish |
| 8 | Manual origin (no provenance) | routing miss on routing-aware type | published broadcast + informational failure to confirmation_data_failure | collector/replay (informational; replay skips) | yes at publish | no | no (but failure re-emitted every re-announce) | safe after publish |
| 9 | Routing reader (Firestore) error | getAll throws | consumer returns [] for business/lane this cycle | metric `routing_lookup.error`, `poll.failure`, log | no | no | yes (documented) | LOST for that cycle's batch |
| 10 | Per-entry SNAP enrichment error | goods-out/pick/pack/WOC fetch throws | entry skipped, retried next poll | log + `confirmation.map_skipped` | no | no | yes | LOST |
| 11 | Goods-in consignment not found | no consignments for receipt | `return null`, warn, hanging metric | warn + `confirmation.hanging` | no | no | yes | LOST |
| 12 | Goods-in partial consignment fetch | some fetches rejected | published with partial data | none | yes (wrongly) | YES | no | same as today (existing defect) |
| 13 | RGA enrichment degraded | stock-detail/attachments fail | published without batch/expiry/routing attachment | log event RgaFetchEvent.Failed | yes | no | no | same as today (existing defect) |
| 14 | Canonical mapping throws | record-level bug in `confirmationsToCanonical` | whole type array dropped for all businesses in chunk; retried | log only | no | no | yes | LOST (and blast radius = chunk) |
| 15 | Canonical validation fails | Zod safeParse false | record dropped, rebuilt every poll | `ConfirmationParsingEvent.Failed` + `confirmation.unparseable`; NOT to failure topic | no | no (log/metric only) | yes | LOST, no collector/replay record |
| 16 | Stock adj direction undeterminable | MoveType/owner unknown | dropped, warn every poll | log warn only | no | partially | yes | LOST |
| 17 | Unknown business group | group.customer not in chunk's set (incl. cross-tenant movement rows, BizId case/padding mismatch) | dropped silently | none | no | YES | yes | LOST, and can consume ANOTHER tenant's row |
| 18 | Cross-tenant despatch/receipt row | BizId differs on shared host | skipped before enrichment | log event + `cross_tenant_entry_skipped` | no (owner will consume) | no | yes | must NOT consume |
| 19 | Record not returned by SNAP | shipment/receipt lookup returns nothing | `return []`, row stays forever | none | no | YES | yes | LOST unless recorded |
| 20 | Row no handler owns | despatch Stage not 29/39/90; WO (S10) at 29/39 | never read/claimed/cleared | none (FUSE-1062 known) | no | YES | yes (accepted leak) | safe to consume WITHOUT publishing (decision) |
| 21 | Malformed Key (poison) | `parse*Key` throws | whole lane for that business rejected each poll | warn + `poll.failure` | no | no | yes | blocks lane today; consuming the poison row unblocks it |
| 22 | SNAP read failure / circuit open | 5xx / breaker | fetch returns [] | log/metric | n/a | no | n/a | safe (nothing read) |
| 23 | Claim duplicate | claim key live | skipped (pre-check, or announce) | `claim.duplicate`, `claimed_entry_skipped` | n/a | no | yes (dedupe cache, TTL 10 min) | mostly redundant after early consume |
| 24 | Claim store down | Redis error | fail open, publish | `claim.fail_open` | n/a | no | n/a | duplicates only |
| 25 | Publish emit failure | `publishMessage` rejects after claim | claim held 10 min; stage 2 5xx; retried after lapse | error log | no | no | yes | LOST (row already consumed, claim set) |
| 26 | Self-clear cancelled/zero-qty | goods-out Status 01; goods-in all lines zero | PATCH processed; RecordDropped log | log tag DROPPED_CONFIRMATION only | yes | no durable record | no | already consumed today; PATCH failure = stays |
| 27 | Published, awaiting made | normal | row stays until confirmation_made | collector at ready | yes at publish | no | yes (today) | safe after publish ack IF downstream handles duplicates and errors |
| 28 | Published, never made (no mapping/connector) | downstream never emits made | re-published every 10 min forever | metrics only | no | no | yes (accidental at-least-once) | consuming ends the loop; downstream must record the non-delivery |

## 4. Legitimately-wait vs safely-consumable

States that legitimately need to wait on the OBQ (or need a durable replacement record before consume):
- Stage-1 skipped businesses (row 1): product-level deferral. Keep unconsumed (or consciously choose discard).
- Late-gate disabled connector (3): intended deferral. Needs either "leave unconsumed" or a parked/replayable record.
- Connector unavailable (5) and config/route errors (6): transient; never consume while gate outcome unknown.
- Routing reader error / SNAP enrichment error / missing consignments / mapping throw / claim-store-plus-publish failure (9,10,11,14,25): transient or unknown; consume only after a successful publish, or after being escalated to a recorded terminal failure.
- Cross-tenant rows (18, and movement-lane rows for another tenant, 17): never consume from another tenant's client.
- Connector gone (4), unparseable (15), direction-unknown (16), record-not-returned (19), poison key (21): currently deferred accidentally; need an explicit terminal failure (collector/replay record) BEFORE they can be consumed. They are not safe to consume as-is.

States that can be consumed safely (provided consume happens after the handoff, not at find):
- Successfully published groups (27), including broadcast (7) and manual-origin (8): consume after `publishMessage` resolves. The publish ack (plus the existing informational failure for manual origin) is the durable handoff.
- Rows that are not confirmations by design: work orders at stage 29/39 (20), goods-out cancelled and goods-in zero-qty (26 already), despatch rows at unowned stages, subject to a decision that they need no record.
- Stock adjustments once published (16 stuck ones become a downstream-mapping question, not an OBQ one).
- Claim dedupe (23) becomes redundant (replaced by consume) but is still needed while consume can fail/retry after publish.

## 5. Prod Datadog evidence (2026-09-29)

- `fuse.confirmation.published` prod 24h: stock_adjustment 2018, good_out 4562, good_in 9. 2h at 10-min buckets: stock_adjustment 16,16,16,16,17,1,17,16,20,17,21; good_out 32-58 (mixed new + re-announce).
- `snap.outbound.claimed_entry_skipped` prod 10-min buckets: despatch 28-31, stock_move 64-65 (approx 16 stuck movement rows, approx 7 stuck despatch rows in the claimed state).
- `snap.confirmation.claim.duplicate` = 0 (24h): the pre-check absorbs duplicates.
- `snap.poll.skipped_ineligible_business` 24h: ~24 prod businesses at 719 = every cycle.
- 7d/8d daily: withheld_unresolved_connector (gone) pick 5045/1792, pack 5042/1792, good_out 2161/768 on 09-22/09-23 then 0; withheld_ineligible_connector bfa 2880/1024 then 0; `manual_origin_broadcast` sistaco 7029/2484 then 0, champo still 33..107/day, wildsmith 1-5/day, purdyfigg ~1/day. Withheld paths disappeared coincident with the stage-1 gate rollout (merged 2026-09-21), i.e. they are masked, not fixed.
- `confirmation.unparseable`, `confirmation.map_skipped`, `poll.failure`, `claim.fail_open`, `routing_lookup.error`: no data in 7d (paths currently quiet in prod). `confirmation.hanging` good_in = 2 (7d). `outbound.cross_tenant_entry_skipped` nuzest despatch 202, receipt 1 (7d).
- Logs (prod, 30 min): "Consignment StU not found" warn = 951 (consistent with Log Volume programme: goods-out rows re-mapped repeatedly; goods-out is mapped with zeroed physicals rather than failing).
- Caveat: `snap.*` metrics report per emitted event, not per distinct row; re-announce loops inflate counts. Log status filters behaved inconsistently (status:(warn OR error) returned 0 while the pattern query showed warns), so absence of hits in logs is weak evidence; absence in metrics is stronger.

## 6. Existing defects noticed (matter regardless)

1. Connector "gone" is treated as transient and retried forever (4). Only masked by stage-1 skipping.
2. Goods-in publishes partial consignment data when some fetches fail (12).
3. RGA publishes degraded data on transient enrichment failures (13).
4. Poison-pill head-of-line blocking at lane level (bad Key) and at type/chunk level (mapping throw) (14, 21).
5. Silent orphan classes with no metric: unowned stage, record-not-returned, unknown-customer group (17, 19, 20).
6. Movement lane lacks the cross-tenant guard that despatch/receipt have (17).
7. `$top=1000` no ordering, no paging: stuck/orphan rows can starve fresh rows once a business accumulates >=1000 per lane.
8. Debug `/check` dry-run mutates SNAP (PATCH processed for cancelled goods-out).
9. Customer-poll subscription has no dead-letter policy and no backoff: stage-2 failures redeliver immediately and forever.
10. Explainer `work-order-family-confirmations.md` states FGR is "broadcast-only, skips routing store" but source has `routingAware = true` with `routingKeyOf = receipt.Prime` (finished-good-receipt handler 38-49); doc is stale relative to 3c1578b.

## 7. Open questions

- Does SNAP keep processed rows (DateProcessed set) and can they be re-opened or listed? Spec hints rows persist (`DateProcessed`, `/next` = "next open"); the poller's GET has no unprocessed filter, so either the list endpoint hides processed rows by default or it would re-read them. Not verified against a live tenant. This determines whether mark-processed is a recoverable action.
- Is `/v2/snapoutbound/{id}/processed` PATCH idempotent, and what does it do to a row that is already processed or unknown (404)? Not tested (read-only ground rule).
- Backlog depth on the ~24 prod businesses skipped by stage-1 (need SNAP read with tenant creds; not done to avoid handling secrets).
- Why are the ~16 stock-adjustment rows and ~7-30 despatch rows never cleared downstream (no mapping? connector failure?). Belongs to the connector investigators.
- Does SNAP emit multiple RECEIPT rows per receipt at different stages? The receipt lane has no stage filter.
- Are there real despatch OBQ rows at stages other than 29/39/90 (row 20)? Count of WO rows stuck at 29/39?
- Is the stage-1 eligibility cache (TTL default 1 week) refreshed reliably by CONNECTOR revision events? A lost event could delay backlog release by up to a week.
- FUSE-1062 (WO at 29/39) fix status: vault says unconfirmed.
