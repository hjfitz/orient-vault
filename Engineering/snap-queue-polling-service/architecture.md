---
tags:
- waypoint
- snap-queue-polling-service
verified: '2026-10-13'
verified_sha: b16942a
verified_paths:
- apps/snap-queue-polling-service/src
- iac/env
- iac/projects/snap-queue-polling-service
- .github/workflows
- apps/snap-queue-polling-service/CLAUDE.md
- apps/snap-queue-polling-service/tests/mock-server.ts
- apps/snap-queue-polling-service/dockerfile
- iac/projects/snap-adapter
- apps/snap-adapter/src/adapters/firestore
- apps/snap-adapter/src/http/controllers/event.controller.ts
title: snap-queue-polling-service — architecture
thesis: 'A stateless Express poller on Cloud Run runs a two-hop Pub/Sub saga every
  2 minutes: it drains SnapFulfil''s outbound queue per business, maps rows into canonical
  confirmations, claims and publishes them addressed to the originating connector
  or broadcast, then clears each published row off the queue itself.'
confidence: high
---
# snap-queue-polling-service — architecture

```orient-bluf
{ "v": 1, "bluf": "A stateless Express poller on Cloud Run runs a two-hop Pub/Sub saga every 2 minutes: it drains SnapFulfil's outbound queue per business, maps rows into canonical confirmations, claims and publishes them addressed to the originating connector or broadcast, then clears each published row off the queue itself.", "confidence": "high", "action": "Never clear a queue row before its publish resolves, and keep channelSubscribesTo in step with the consumers' confirmation_ready filters." }
```

## Guardrails

- [contract:G1] A queue row is cleared only after its publish resolves, and only by this service. `OutboundQueueClearer` runs after `emit` inside `announceConfirmations`; a rejected publish clears nothing. `snap-adapter` has no clear route left [37][46].
  — paths: apps/snap-queue-polling-service/src/core/snap/confirmations/confirmations.service.ts, apps/snap-queue-polling-service/src/core/snap/confirmations/outbound-queue.clearer.ts
- [technical:G2] Claim each `queueId` (`SET NX`, 10-minute TTL) before publishing, and keep the customer-poll subscription at a 600 s ack deadline. A shorter deadline redelivers a half-finished poll and duplicates confirmations. An unavailable Redis fails open to a publish.
  — paths: apps/snap-queue-polling-service/src/core/cache/cache.service.ts, apps/snap-queue-polling-service/src/core/snap/confirmations/confirmations.service.ts, iac/projects/snap-queue-polling-service/pubsub.tf
- [technical:G3] The routing store is read-only here, and a reader error must throw, never degrade to a miss. A miss falls back to the SNAP attachment, then to broadcast. A throw loses only that consumer's page for the cycle, because `QueueLane` catches per consumer. Keep that catch.
  — paths: apps/snap-queue-polling-service/src/adapters/firestore/routing-metadata.reader.ts, apps/snap-queue-polling-service/src/core/snap/confirmations/queue-lane.ts, apps/snap-queue-polling-service/src/core/snap/confirmations/canonical-confirmation.handler.base.ts
- [contract:G4] Every confirmation publish is addressed: a `source` attribute for its origin connector, or `broadcast=true`, never neither. The envelope `metadata.source` carries that resolved ingress channel, never this service's name.
  — paths: apps/snap-queue-polling-service/src/core/snap/confirmations/confirmations.service.ts, apps/snap-queue-polling-service/src/adapters/pubsub/pubsub.router.ts
- [contract:G5] `channelSubscribesTo` mirrors the consumers' `confirmation_ready` filters, and `ROUTING_AWARE_TYPES` stays in step with the handlers that resolve routing. Clearing a row that no channel takes loses the confirmation.
  — paths: apps/snap-queue-polling-service/src/core/snap/confirmations/confirmation-subscriptions.ts, apps/snap-queue-polling-service/src/core/snap/confirmations/confirmation-failure.ts
- [technical:G6] A connector's absent `confirmationsEnabled` reads as `false`. This is the opposite of the usual "absent means enabled" convention, and it is deliberate so an un-backfilled connector fails closed.
  — paths: apps/snap-queue-polling-service/src/core/config/remote-config.provider.ts, apps/snap-queue-polling-service/src/core/snap/confirmations/confirmations.service.ts

## Runtime shape

An Express 4 app (`bootstrap/app.ts`) with no framework beyond it [1]. Layers follow the org convention: `http/controllers` (thin) → `core/polling`, `core/snap`, `core/stock-sync` (logic) → `adapters/{snap,pubsub,http,fuse-config,firestore,gcs}` (SDK wrappers), with `core/cache` and `core/config` for Redis and remote config. There is no `repositories/` layer, because nothing is persisted.

`bootstrap/factory/controller.factory.ts` builds everything once: the cache, the SNAP circuit breaker, the Pub/Sub router, eight confirmation handlers and the two services [2]. `config/parse.ts` validates env once, and `process.env` is read nowhere else [10].

### The two-stage poll (a saga split across two Pub/Sub hops)

Each invocation must be bounded and get its own ack window, so polling is split in two [3][4][5][6]:

```orient-flow
{ "v": 1, "title": "Poll saga: schedule to publish",
  "nodes": [
    { "id": "sch", "label": "Cloud Scheduler", "sub": "poll_schedule, every 2 min", "kind": "external", "ev": [6] },
    { "id": "t1", "label": "snap_poll_schedule", "sub": "owned by this stack", "kind": "topic", "ev": [5] },
    { "id": "s1", "label": "POST /event/poll/schedule", "sub": "stage 1: chunk businesses", "kind": "service", "service": "snap-queue-polling-service", "ev": [3, 4] },
    { "id": "t2", "label": "snap_poll_customer", "sub": "ack deadline 600 s", "kind": "topic", "ev": [5] },
    { "id": "s2", "label": "POST /event/poll/confirmations", "sub": "stage 2: drain, claim, publish, clear", "kind": "service", "service": "snap-queue-polling-service", "tone": "accent", "ev": [3, 4] },
    { "id": "snap", "label": "SnapFulfil", "sub": "per-business client", "kind": "external", "ev": [13] },
    { "id": "ready", "label": "confirmation_ready", "sub": "+ stock_adjustment_ready", "kind": "topic", "ev": [2] }
  ],
  "edges": [
    { "from": "sch", "to": "t1", "label": "\"trigger\"" },
    { "from": "t1", "to": "s1", "label": "OIDC push" },
    { "from": "s1", "to": "t2", "label": "one message per chunk" },
    { "from": "t2", "to": "s2", "label": "OIDC push" },
    { "from": "s2", "to": "snap", "label": "read queue, clear rows" },
    { "from": "s2", "to": "ready", "label": "publish" }
  ] }
```

1. **Stage 1.** Cloud Scheduler (`schedule.tf`, job `daily-run`, `var.poll_schedule`, default `*/2 * * * *`) publishes `"trigger"` to `POST /event/poll/schedule`. `PollingService.registerCustomerForConfirmations()` lists eligible businesses, chunks them by `CUSTOMER_CHUNK_SIZE`, and publishes one customer-poll message per chunk. The message record is `{ backendConfigs }`, with each business's SNAP host and credentials [3].
2. **Stage 2.** The message reaches `POST /event/poll/confirmations`. `PollingService.handleConfirmations()` builds a per-business SNAP client for the chunk. It then runs `getConfirmations` (drain, map, group, resolve routing) and `announceConfirmations` (claim, publish, clear) [3].

The default chunk size is 2 in config and 5 in Terraform (`customer_chunk_size`), so 5 applies when deployed. Stage 2 publishes before it acks, so its subscription uses Pub/Sub's maximum 600 s ack deadline. The Cloud Run request timeout is also 600 s, so a 504 cannot land before the deadline [5][7]. The schedule, stock-sync-schedule and config-revision subscriptions use 20 s. The stock sync due subscription uses 600 s. None sets a dead-letter topic.

**ASSESSED** Stage 1 puts SNAP credentials into a Pub/Sub message body, and Redis also caches them in plaintext (`SNAP_BACKEND:all-backends:v2`). Both are inferred from the schemas [3][26]. Anyone with read access to that topic or cache sees them.

## Endpoints

| Method + path | Auth | Purpose |
| ------------- | ---- | ------- |
| `GET /health/liveness` | none | Always 200 with uptime and a Redis status, even when Redis is down [4] |
| `POST /event/poll/schedule` | none in app | stage 1: fan-out |
| `POST /event/poll/confirmations` | none in app | stage 2: poll and publish. A body that fails validation logs and returns 202 |
| `POST /event/config/revision` | none in app | refresh cached backends and connectors on a `BACKEND_CONFIG` or `CONNECTOR` revision |
| `POST /event/stock-sync/schedule` | none in app | stock sync stage 1: fan-out of due Shopify connectors |
| `POST /event/stock-sync/due` | none in app | stock sync stage 2: pull, export and publish for one connector |
| `POST /debug/trigger` | `x-api-key` | manual full poll and announce for the supplied or all businesses |
| `POST /debug/check` | `x-api-key` | dry-run goods-out fetch with no announce |

The `errorMiddleware` maps exceptions to responses [1]. Missing credentials answer 202, an unhandled config event type answers 204, and a cache or config-API failure answers 500, which makes Pub/Sub redeliver.

**ASSESSED** The `/event/*` routes have no app-level auth. The subscriptions push with an OIDC token for `pubsub_handler_invoker`, but `iam.tf` also grants `roles/run.invoker` to `allUsers` three times, and ingress is `INGRESS_TRAFFIC_ALL` [7][8]. Any caller who can reach the URL can post to them. An org policy outside this repo could still narrow that.

**ASSESSED** `authMiddleware` lets every request through when `API_KEY` is unset [9]. Terraform sets `API_KEY` from `var.public_access_key`, whose default is a fixed string. No tfvars file in this repo overrides it [7][8]. `/debug/trigger` publishes confirmations and clears queue rows.

## Shopify stock sync (a second, separate saga)

Not a confirmation: a 15-minute tick that finds the Shopify connectors due a stock sync, then runs it for each. It has the same two-hop shape as the poll.

```orient-flow
{ "v": 1, "title": "Stock sync: tick to export",
  "nodes": [
    { "id": "sch", "label": "Cloud Scheduler", "sub": "*/15 * * * *", "kind": "external", "ev": [6] },
    { "id": "a", "label": "POST /event/stock-sync/schedule", "sub": "keep connectors due now", "kind": "service", "service": "snap-queue-polling-service", "ev": [11] },
    { "id": "cs", "label": "config-service", "sub": "Shopify connectors", "kind": "service", "service": "config-service", "ev": [26] },
    { "id": "td", "label": "stock_sync_due", "sub": "one message per connector", "kind": "topic", "ev": [5] },
    { "id": "b", "label": "POST /event/stock-sync/due", "sub": "pull, aggregate, export", "kind": "service", "service": "snap-queue-polling-service", "tone": "accent", "ev": [11] },
    { "id": "snap", "label": "SnapFulfil", "sub": "stocktotals, kits", "kind": "external", "ev": [13] },
    { "id": "gcs", "label": "GCS export bucket", "sub": "new JSONL object per run", "kind": "store", "ev": [11] },
    { "id": "ready", "label": "confirmation_ready", "sub": "recordType=stock_sync", "kind": "topic", "ev": [11] }
  ],
  "edges": [
    { "from": "sch", "to": "a" },
    { "from": "cs", "to": "a", "label": "stockSync config" },
    { "from": "a", "to": "td", "label": "due only" },
    { "from": "td", "to": "b", "label": "push" },
    { "from": "b", "to": "snap" },
    { "from": "b", "to": "gcs", "label": "write" },
    { "from": "b", "to": "ready", "label": "GCS pointer" }
  ] }
```

1. **Stage 1.** The scheduler (`schedule.tf`, `stock_sync`, `var.stock_sync_schedule`) publishes `"trigger"` to `POST /event/stock-sync/schedule`. `StockSyncService.registerDueConnectors()` lists the Shopify connectors through `RemoteConfigProvider.resolveShopifyStockSyncConnectors`. The listing omits `stockSync`, so each connector is fetched singly. A connector is due when `isStockSyncDue` matches the UTC day and `HH:mm` within `STOCK_SYNC_TOLERANCE_MINUTES`. That value must stay under half the tick cadence. Each due connector gets one `{businessId, connectorId}` message on `stock_sync_due` [11].
2. **Stage 2.** `POST /event/stock-sync/due` calls `handleDueConnector()`. It resolves the business's Snap backend and pulls `stocktotals` (paged). It then pulls the owner's kit SKUs from `/v2/products` (`Group2 = MASTERSKU`) and reads each kit from `stocktotalskit/{sku}` one at a time. `aggregateStockTotals` sums per SKU. The service writes a JSONL export to `STOCK_SYNC_EXPORT_BUCKET` under a new object path every run and publishes **one** `confirmation_ready` message tagged `recordType=stock_sync`. That message carries a `GcsPointer`, never the stock. It publishes through `registerStockSyncReady`, not `emit`, because `emit` is keyed by `ConfirmationType` [11][12][13].

What shapes the export:

- **Stock is summed across all of the owner's sites.** `stocktotals` has one row per stock line, split by `Site` and `Facility`, so a `SKUId` repeats. Product rows are pulled with `Status` `00`, `State` `W` and a product `Group1` other than `UNLINK`. A kit row can arrive with null `Status` or `State` and passes [12][13].
- **A kit's quantity is `PotentialKitQty`, and it replaces any physical quantity under that SKU.** A kit with no usable kit rows exports as `isKit: true`, `quantity: 0`.
- **Never the bare `/v2/stocktotalskit` route.** It returns every owner's kits, so one broken bill of materials on a shared host fails the route for everyone. Per-kit reads isolate it.
- **A kit that fails with a Snap 5xx is skipped, loudly.** The service logs `Stock sync kit read failed, kit left out of export`, meters `snap.stock_sync.kit_skipped` and filters the SKU out of the export. The storefront keeps its last level instead of receiving the SKU's physical stock. Any other failure (circuit open, network, parse, an unexpected 404) fails the run. The kit loop gives up one failure short of the circuit breaker's threshold. The breaker is per instance and shared with the confirmation poll [11].
- **A failed run acks and publishes nothing**, so no consumer sees a backlink to a partial export (`snap.stock_sync.export_failed{stage}`). The next tick re-runs it.
- Stock totals and the product listing page with an `$orderby`, because a repeat across pages would inflate the sum. They stop at 200 pages of 500 rows and throw past it [13].

The due subscription's ack deadline is 600 s, for the same reason as the poll: a shorter deadline redelivers mid-run and starts a second sync for the same connector. The two fan-out topics belong to this stack (`pubsub.tf`). A connector that cannot be read back is skipped and metered (`snap.stock_sync.connector_unresolved{reason}`). A failed fan-out publish loses that connector's window for the tick (`snap.stock_sync.due_publish_failed`).

## Confirmation types → topics

Handlers are keyed by an internal `ConfirmationType`, registered in `controller.factory.ts` [2]. Everything publishes on the cross-entity `confirmation_ready` topic with an `attributes.recordType` that subscribers filter on in Terraform. `stock_adjustment` keeps its dedicated topic [2][29].

| `ConfirmationType` | topic | `recordType` attribute | SNAP lane and stage |
| ------------------ | ----- | ----------------------- | ------------------- |
| `good_in` | `confirmation_ready` | `goods_in_confirmation` | RECEIPT, standard receipts |
| `good_out` | `confirmation_ready` | `goods_out_confirmation` | DESPATCH, stage 90, not a work order |
| `stock_adjustment` | `stock_adjustment_ready` | none | STOCK_MOVE |
| `return_goods_authorization` | `confirmation_ready` | `return_goods_authorization` | RECEIPT, return `OrderClass` |
| `pick_confirmation` | `confirmation_ready` | `pick_confirmation` | DESPATCH, stage 29, not a work order |
| `pack_confirmation` | `confirmation_ready` | `pack_confirmation` | DESPATCH, stage 39, not a work order |
| `finished_good_receipt` | `confirmation_ready` | `finished_good_receipt` | RECEIPT, work-order receipts |
| `work_order_confirmation` | `confirmation_ready` | `work_order_confirmation` | DESPATCH, stage 90, `OrderType` `S10` |

`goods_in_confirmation` and `goods_out_confirmation` are publish-only tags (`CROSS_ENTITY_CONFIRMATION_TAGS`). Nothing drains or claims under them. They name the confirmation, not the create-side record. The legacy per-entity PO and SO ready topics are no longer published. Every publish also carries the routing attributes below. The consumers are sftp-connector, fapi, collector and shopify-connector. shopify-connector takes only `goods_out_confirmation` [36]. Do not move `stock_adjustment` onto the cross-entity topic without adding the matching subscriber filter.

**ASSESSED** A work order sitting at stage 29 or 39 is never published and never cleared. Pick and pack exclude `S10` shipments, and the work order confirmation owns only stage 90 [38][39][40]. Whether a fix is planned is **UNKNOWN**; see [[known-context]].

## Routing resolution: Firestore store → attachment fallback → connector lookup

Seven types are routing-aware (`ROUTING_AWARE_TYPES`): every type except `stock_adjustment` [17]. Provenance `{connectorId, source}` resolves in three steps, each a hedge against the one before it finding nothing.

```orient-flow
{ "v": 1, "title": "Routing resolution for one confirmation",
  "nodes": [
    { "id": "c", "label": "Mapped confirmation", "sub": "keyed by shipment or receipt id", "kind": "step", "ev": [21] },
    { "id": "fs", "label": "Firestore routing doc", "sub": "fuse-wms-routing, authoritative", "kind": "store", "ev": [22] },
    { "id": "att", "label": "SNAP header attachment", "sub": "SHH or REH, pre-store orders", "kind": "external", "ev": [24] },
    { "id": "cl", "label": "Connector lookup", "sub": "config-service, Redis-cached", "kind": "service", "service": "config-service", "ev": [26] },
    { "id": "ok", "label": "Publish with source", "sub": "attributes.source", "kind": "step", "tone": "accent", "ev": [14] },
    { "id": "bc", "label": "Publish broadcast", "sub": "broadcast=true", "kind": "step", "ev": [14] },
    { "id": "wh", "label": "Withheld", "sub": "row stays queued, retried next poll", "kind": "step", "tone": "alert", "ev": [14] }
  ],
  "edges": [
    { "from": "c", "to": "fs", "label": "1" },
    { "from": "fs", "to": "ok", "label": "has source" },
    { "from": "fs", "to": "cl", "label": "bare connectorId" },
    { "from": "fs", "to": "att", "label": "no doc", "style": "dashed" },
    { "from": "att", "to": "ok", "label": "has source" },
    { "from": "att", "to": "cl", "label": "bare connectorId" },
    { "from": "att", "to": "bc", "label": "nothing", "style": "dashed" },
    { "from": "cl", "to": "ok", "label": "resolved" },
    { "from": "cl", "to": "wh", "label": "gone or unavailable" }
  ] }
```

1. **Firestore store, authoritative once populated.** `snap-adapter` writes `{connectorId, source}` into the named database `fuse-wms-routing` (collection `routing-metadata`, doc id `{businessId}__{entityId}`) before every routed SNAP create. It no longer writes the SNAP routing attachment. This service only reads it: `FirestoreRoutingMetadataReader.getMany`, one batched `getAll` per 50-entry page [22]. Docs are keyed by shipment id on the despatch lane and receipt id on the receipt lane. `getMany` returns the whole per-entity doc (`{routing, lineExtensions, lines}`). Every handler reads `.routing`, and only `GoodsOutConfirmationHandler` also reads `.lineExtensions` and `.lines` (below). The store exists because SNAP's keyed-PUT upserts replace attachment children wholesale, so a resent create wipes the old attachment while Firestore survives. FGR has no attachment fallback, because SNAP writes no routing attachment on a receipt it generates itself. FGR keys off the *work order's* `ShipmentId` (`receipt.Prime`), because SNAP mirrors that id onto every receipt it generates [41]. `stock_adjustment` has `routingAware = false`, so its pages skip the lookup.
2. **SNAP header attachment, the fallback for orders that predate the required store write.** `extractRouting` reads the `SHH`/`TXT` (despatch) or `REH`/`TXT` (receipt) header attachment when the store has no doc. No service writes that attachment now. The read stays live until it is retired [24].
3. **Connector lookup, only when the source holds a bare `connectorId` and no `source`.** `ConfirmationsService.resolveRoutingSources` calls `RemoteConfigProvider.resolveConnectorSource(connectorId)`, which is Redis-cached and backed by config-service `GET /connectors/{id}`. It derives `source` from the connector's `config.type` [14][26].

`CanonicalConfirmationHandlerBase.resolveRouting` picks store over attachment and meters the choice: `snap.routing_lookup.hit`, `.fallback_attachment` and `.miss`, all tagged `type`. The fallback counter is the drain gauge for retiring the attachment read [21].

**Per-line Shopify extensions ride the same store doc.** `GoodsOutConfirmationHandler` resolves each despatch line's Shopify `fulfillmentId` in three tiers: the store doc's `lines` (keyed by the `SOLineId` the write side set before the SNAP create), then `lineExtensions` (keyed by the SNAP `Line` id), then the `SHL` shipment attachment. The write side no longer produces the last two, so they answer only for older orders. The `SOLineId` tier applies to ordered (Level 00) lines only: exploded kit members share their parent's id, and `SOLineId` 0 or -1 fall through. Metrics `snap.line_extension_lookup.soline`, `.line`, `.attachment` and `.miss` (tagged `businessId`) record which tier answered [23].

**Stored lines with no ordered line in SNAP fail the goods-out.** When the doc's `lines` name a `SOLineId` that the shipment has no Level 00 line for, part of the order has left the WMS. `failPartialOrder` claims the queueId and publishes a non-retryable `business_rule` (`stored_lines_unmatched`) `BifrostFailure` to `confirmation_data_failure`. The failure carries the *surviving* lines' confirmation, so a deliberate replay confirms just those. It then clears the queue item and meters `snap.confirmation.partial_order_failed`. A failed publish leaves the item queued to retry. Docs without `lines` skip the check [23].

**A routing-store read failure does not abort the poll.** The handler bases meter `snap.routing_lookup.error` (tagged `lane`) and rethrow. `QueueLane.drainForClient` catches per consumer, logs, bumps `snap.poll.failure` and returns `[]` for that page. Only that consumer's page is lost for the cycle, and the next cycle retries it [18][30]. A throw inside one entry's own mapping is isolated per entry instead: `mapEntriesInIsolation` skips the entry, logs it and meters `snap.confirmation.map_skipped` [31].

**Connector-lookup failure (step 3) can withhold a confirmation.** If `resolveConnectorSource` throws a `FuseConfigApiException` with `connectorResolutionFailure` set, the group is dropped and its rows stay queued. The value is `"gone"` (config-service says the connector no longer exists) or `"unavailable"` (the API call failed). A business with `broadcastConfirmations` still publishes. Withheld groups log `tag: DROPPED_CONFIRMATION` and meter `snap.confirmation.withheld_unresolved_connector` (tagged `{type, businessId, reason}`). A resolved lookup meters `snap.confirmation.connector_source.resolved` or `.unresolved`. Any other error rethrows, because a bare network failure does not prove the connector is gone [14][26].

## Routing vs broadcast (attributes on every confirmation publish)

`ConfirmationsService.buildEmitterAttributes` derives two attributes per customer group, after routing resolution, and `PubsubRouter.emit` serialises them with `recordType` [14][29]:

| attribute | set when |
| --------- | -------- |
| `source` | the group's resolved `routing.source` is present |
| `broadcast = true` | the business has `broadcastConfirmations`, **or** there is neither `source` nor `connectorId` |

The envelope's `metadata.source` carries the same resolved ingress channel as the `source` attribute, so anything that re-sends the envelope keeps the right channel. The poller's own name (`SOURCE`, `snap-queue-polling-service`) stays on failure bodies, failure attributes and the internal poll-trigger message. `routing.connectorId` stays on the envelope metadata, not the attributes.

A confirmation therefore reaches either its originating connector (subscribers filter on `source`) or every connector, never neither. A record with no routing is manual-origin: it was made in SNAP by hand, and broadcast is its only route.

For the seven routing-aware types, a group that still has no origin also increments `fuse.confirmation.manual_origin_broadcast`. It publishes one informational `BifrostFailure` per record to `confirmation_data_failure` (`business_rule` / `no_originating_connector`) after the clear. `stock_adjustment` never populates routing, so flagging it would be a permanent false positive. Keep that set in step with the handlers and with the confirmation-side `FailureUseCase` map beside them, where RGA maps to `return_goods_confirmation`, never the create-side value [17].

That failure publishes through `@gfs-bifrost/pubsub`'s `PubSubRouter` (`adapters/pubsub/confirmation-failure.publisher.ts`), not the local `PubsubRouter`. These are two publish paths, deliberately.

## Outbound-queue mechanics

```orient-flow
{ "v": 1, "title": "One lane, one business, one poll",
  "nodes": [
    { "id": "q", "label": "Read queue", "sub": "$top 1000, one read per lane", "kind": "step", "ev": [13, 19] },
    { "id": "dc", "label": "Drop claimed rows", "sub": "claim key still live", "kind": "step", "ev": [18, 25] },
    { "id": "re", "label": "Resolve entries", "sub": "batch fetch, drop co-tenant rows", "kind": "step", "ev": [20] },
    { "id": "m", "label": "Handlers map owned rows", "sub": "per-entry isolation", "kind": "step", "ev": [30, 31] },
    { "id": "r", "label": "Group and resolve routing", "sub": "gate on connector", "kind": "step", "ev": [14] },
    { "id": "cl", "label": "Claim queueId", "sub": "SET NX, 10 min", "kind": "step", "ev": [14, 25] },
    { "id": "pub", "label": "Publish", "kind": "topic", "ev": [14] },
    { "id": "clr", "label": "Clear row", "sub": "PATCH /processed", "kind": "step", "tone": "accent", "ev": [15] }
  ],
  "edges": [
    { "from": "q", "to": "dc" },
    { "from": "dc", "to": "re" },
    { "from": "re", "to": "m" },
    { "from": "m", "to": "r" },
    { "from": "r", "to": "cl" },
    { "from": "cl", "to": "pub", "label": "claimed or fail-open" },
    { "from": "pub", "to": "clr", "label": "resolved" }
  ] }
```

- **`OutboundQueueDrain`** is the single owner of every read of `/v2/snapoutbound` [19]. Handlers never fetch directly. Each declares a `lane`, the SNAP transaction type its items are keyed by: `DESPATCH`, `RECEIPT` or `STOCK_MOVE`. The drain hands every handler on a lane the same resolved entries. It reads once per transaction type per poll, not once unfiltered, so a business backlogged on one type cannot starve the others. `$top` is 1,000 per request. A failed read, including an open circuit, returns `[]` and never throws [13][32].
- Within the `RECEIPT` lane, three handlers (`return_goods_authorization`, `finished_good_receipt`, `good_in`) partition the *same* unfiltered result set by each handler's own `isOwned` predicate, not by an OData filter. The `DESPATCH` lane splits by `SHIPSTAGE` and `OrderType` the same way [38][41].
- **Co-tenant rows are dropped before enrichment.** Shared SNAP hosts expose one instance-wide queue, so a poll sees other businesses' records. The `DESPATCH` and `RECEIPT` resolvers skip an entry whose record `BizId` differs from the polled business (trimmed, case-folded). They meter `snap.outbound.cross_tenant_entry_skipped`. An absent `BizId` is kept. The stock-movement resolver has no such check [20].
- **Already-claimed items are dropped before enrichment** (`QueueLane.dropClaimed`). Each raw row's `XDoc` is checked against the claim key with a read-only `isConfirmationClaimed`. A hit means the confirmation was published on an earlier cycle and its clear has not landed. Re-enriching it would only feed the announce-time duplicate check. The skip meters `snap.outbound.claimed_entry_skipped{lane,businessId}`. It fails open twice (a lookup error and a rejected lookup promise both read as unclaimed). The 10-minute claim TTL bounds it: after the TTL lapses the item re-enriches and republishes [18][25].
- Enrichment is batched per lane, 25 ids per OData `$filter` call, so adding a handler to an already-drained lane costs no extra SNAP calls [20].

### Clearing

Every published row is cleared by this service. SNAP answers the `PATCH /v2/snapoutbound/{queueId}/processed` with HTTP 200 even for an unknown id, so the client checks the envelope. A `Status` `Error`, empty `Results` or a non-envelope body is a failed clear [13].

```orient-flow
{ "v": 1, "title": "What happens to a published group",
  "nodes": [
    { "id": "pub", "label": "Publish resolved", "sub": "a rejected publish clears nothing", "kind": "topic", "ev": [14] },
    { "id": "g", "label": "Group check", "sub": "channelSubscribesTo", "kind": "step", "ev": [15, 16] },
    { "id": "skip", "label": "Row stays queued", "sub": "no_subscription or no_queue_id", "kind": "step", "ev": [15] },
    { "id": "patch", "label": "PATCH /processed", "sub": "3 at a time, breaker stops the rest", "kind": "step", "tone": "accent", "ev": [15] },
    { "id": "done", "label": "Cleared", "sub": "snap.outbound.cleared", "kind": "step", "ev": [15] },
    { "id": "fail", "label": "Clear failed", "sub": "re-announces after claim TTL", "kind": "step", "tone": "alert", "ev": [15] }
  ],
  "edges": [
    { "from": "pub", "to": "g" },
    { "from": "g", "to": "skip", "label": "no channel takes it", "style": "dashed" },
    { "from": "g", "to": "patch", "label": "everything else" },
    { "from": "patch", "to": "done" },
    { "from": "patch", "to": "fail" }
  ] }
```

- **Publish, then clear.** Since #294 `snap-adapter` has no confirmation-made route, so no downstream flow clears rows [37][46]. `announceConfirmations` hands a group's published rows to `OutboundQueueClearer` once the publish resolves [14][15].
- **Which groups skip.** Only a group routed to a `source` whose channel does not subscribe to its type skips (`no_subscription`), because clearing a row no channel takes would lose it. `channelSubscribesTo` mirrors the consumers' filters: `rest` and `sftp` take the routing-aware types, and `shopify` takes only `good_out` [16]. A row with no `queueId` skips too (`no_queue_id`). Both meter `snap.outbound.clear_skipped{reason}`.
- **Everything else clears.** That includes broadcast and unrouted groups and `stock_adjustment`. A broadcast reaches every channel, and each consumer records a failure for any connector it cannot deliver to. Stock adjustments go to `stock_adjustment_ready` [15].
- **Bounds.** Clears run at `CLEAR_AFTER_PUBLISH_CONCURRENCY` (default 3) and never reject. An open breaker stops the group's remaining PATCHes. A failed clear leaves the row queued, and it re-announces once the claim expires: a duplicate, never a loss. Failures meter `snap.outbound.clear_failed{reason}`, with reasons `snap_error`, `not_cleared`, `invalid_response`, `circuit_open`, `request_failed` and `no_client`.
- **Dropped rows clear through `ConfirmationDisposer`.** Items this service drops are zero-received-qty goods-ins, cancelled goods-out shipments, and goods-outs failed for unmatched stored lines. The disposer logs and swallows a failed clear [23].
- **ASSESSED** Per the topology registry, stock adjustments reach collector, shopify-connector and sftp-connector but not fapi, so the "every channel subscribes" comment in the clearer overstates it. This is harmless while stock adjustments never carry a source [36][15].

## Per-handler SNAP reads beyond the queue

The drain supplies raw entries. Anything else a confirmation needs is the handler's own call. Pick and pack fetch the shipment's `SHH` attachment only for the routing fallback, and goods-in fetches its receipt's `REH` only for the same reason [38][39][41].

| Type | Extra reads and mapping rules |
| ---- | ----------------------------- |
| Pick and pack | Both fetch Stock Detail by `AssignRef` (`fetchAssignedStockDetail`, `AssignType eq 'OC'`). Picked stock points at its shipment there, and its `Consignment` is the receipt it came in on. That attribute data is unrecoverable once the order moves past the stage. **Pick** builds lines at batch grain: stock rows group by SKU + batch + status, sorted by `StockId` because the fetch sets no `$orderby`. A repeated SKU across shipment lines takes the first line's order quantities (`snap.confirmation.batch_attribution_ambiguous`, log `AmbiguousSkuAttribution`). A line with quantity but no matching stock row reports no batch (`snap.confirmation.batch_not_matched`). **Pack** keeps one batch per line (the lowest `StockId`, so it is stable across polls; a SKU packed from several batches logs `SeveralBatchesOnLine`). It reads its cartons with `fetchAssignedStu`, keyed on `Ref`, because `Consignment` becomes the carrier note once Snap assigns one [38][39] |
| Goods-out and pack | StUs are read consignment-scoped (`fetchStu(consignmentId, OUTBOUND)`), one call, so both sides of the join key on the same id. Goods-out once derived its set from `shipment.ShipmentDespatch[].Stu`, a different collection that shipped zeroed physicals and empty `dimensions` when despatch was empty. An unmatched StU is warned on, never silently zeroed [23][39] |
| RGA | Reads Stock Detail and matches it to receipt lines per line, not per SKU (quantity, then status, each row used once, since a return can repeat a SKU with a batch per line). Ambiguous or unmatched lines log `AmbiguousStockMatch` or `StockDetailNotFound`. Carrier tracking comes from the `REH` receipt-header attachment of type `RET_TRACK`, because SNAP's return station leaves `receipt.CarrierTrackingNumber` empty. Return receipts are those whose `OrderClass` is one of `CUSRTN`, `CUSUNK`, `ECMRTN`, `KNOWNRET`, `UNKNOWNRET`, `WHSRTN`, and not a finished-good receipt [40][42] |
| WOC | Reads the paired `R10` receipt and joins its lines onto the `S10` shipment's by the Snap `Line` key, because Snap mirrors every work-order line onto both documents. Role comes from the planned quantities (actuals only break a tie). `consumed` comes from `QtyPicked`, since `QtyShipped` is structurally zero (a work order never despatches). `produced` and `rejected` come from the matched receipt line. Quantities are scoped to the role, so the inapplicable side is absent rather than a real-looking zero. A receipt-only key is emitted as an unplanned by-product. WOC also stamps the consumed component batch. Snap de-assigns component stock when the work order closes, so the handler reads the stock movements into the work order's consignment, then Stock Detail for the From/To stock ids. One distinct batch per SKU is stamped, else none [43] |
| FGR | Emits only the receipt's produced lines (`selectFinishedGoodLines`). The mirrored components are dropped and `quantities.totalLines` counts what is emitted. A receipt where no line looks produced is logged and passed through whole. It resolves the S10 work order behind the R10 receipt (`Prime`, then `SupplierRef`, then `SupplierOrder`, then `CustomerRef`; exactly one match or none) to stamp the work-order and sales-order references. It reads the receipt's inbound stock consignment for the produced batch per line. A lookup error throws so the entry retries next poll. An empty or ambiguous result degrades to no batch and no references [41][44] |
| Stock adjustment | Fetches each queued movement by its full natural key (`/v2/stockmovements/{site}/{type}/{moveId}/{line}`; the move id alone returns every line of the move). It stamps `identifiers.movementRef`. It reads batch and expiry of the from and to stock off one Stock Detail lookup per poll, by `FromStockId` and `ToStockId`. Best-effort: a failed lookup sends the adjustment without batch or expiry (`StockAdjustmentFetchEvent.Failed`) [45] |

Both work-order types end to end: [[work-order-family-confirmations]].

## Resilience

- **Per-host SNAP circuit breaker** (`adapters/snap/circuit-breaker.ts`). It is in-memory, per Cloud Run instance, with one policy per SNAP host and a consecutive-failure threshold (`SNAP_CIRCUIT_BREAKER_CONSECUTIVE_FAILURES`, default 5). It trips on 5xx, network errors and 429, and never on a single business's other 4xx. An open circuit short-circuits the queue read to `[]` rather than throwing, so a SNAP outage does not replay the whole backlog every 2 minutes. The queue read always goes through the breaker, because that call is the recovery probe [27][32].
- **HTTP retry.** The SNAP client retries transient failures (no response, 5xx, 429, 408) up to 2 times with jittered backoff. A request that exhausts its retries counts as one failure against the breaker [28].
- A Redis-tier circuit breaker owned by `@gfs-bifrost/cache` is separate from the SNAP breaker. Redis init failure is logged and the service continues without it [25].

## Config & credentials

`RemoteConfigProvider` pulls backends from config-service, caches them in Redis, and refreshes them on `BACKEND_CONFIG` revision events [26].

**Which businesses are polled.** `getAllConfiguredBusinesses` also reads config-service's paged business index (`GET /business`). It parses the index with a local schema, because the package `ConnectorRefDTOSchema` requires a `useCases` field the live index omits. It caches one boolean per business (`hasConfirmationEnabledConnector`) under `BUSINESS_INDEX:confirmation-eligibility`. A business is polled only if that is true or its backend has `broadcastConfirmations`. A business with no eligible connector, or no connectors, is skipped before any SNAP read. Stage 1 logs one aggregate `Skipping businesses with no confirmation-enabled connector` line and meters `snap.poll.skipped_ineligible_business{businessId}`. Any `CONNECTOR` revision refetches the whole index, because a revision names a connector, not a business. An unreadable index fails open and polls everyone (`snap.poll.business_index_unavailable`) [26].

**Which connectors receive.** The connector-level gate runs per group after enrichment, because connector identity is not knowable from a raw queue row (`/v2/snapoutbound` rows carry only `XDoc`, `Key` and `Transaction`). `resolveConnectorConfirmationsEnabled` has the same cache-first shape as `resolveConnectorSource`, and one fetch caches both facts. `resolveRoutingSources` checks it for any group with a `routing.connectorId`. An ineligible connector's confirmations are withheld like an unresolved connector's (`confirmation.withheld_ineligible_connector`), unless the business broadcasts. They are not cleared from SNAP's queue. Mapping and use-case eligibility is **not** checked here. Each downstream connector keeps that concern [14].

`broadcastConfirmations` is a second per-business flag from `BACKEND_CONFIG` (cached, optional, absent means off). It rides `SnapBackendConfig` → `CustomerConfig` → the group and decides the `broadcast` attribute.

**Env and credentials.** SNAP credentials come only from config-service backends. `SNAP_API_ACCESS_CREDENTIALS` (`user:pass@host`, comma-separated) and `USE_SERVICE_MOCKS` still parse into config, but no source file reads them and Terraform does not set them [7][10]. Topic names come from `bifrost-pubsub` remote state (`remote.tf`): `CONFIRMATION_READY_TOPIC_NAME`, `STOCK_ADJUSTMENT_TOPIC_NAME` and `CONFIRMATION_DATA_FAILURE_TOPIC_NAME`. That stack must have applied its outputs before this one plans. The stock sync adds `STOCK_SYNC_DUE_TOPIC_NAME`, `STOCK_SYNC_TOLERANCE_MINUTES` (default 2) and `STOCK_SYNC_EXPORT_BUCKET`. The bucket name comes from `core-infra` remote state, so that output must exist first. `CLEAR_AFTER_PUBLISH_CONCURRENCY` bounds the clearer [7][10].

`FIRESTORE_DATABASE_ID` (+ optional `FIRESTORE_PROJECT_ID`) is required config for the routing reader. It names the database `fuse-wms-routing` (`variables.tf`). The value is duplicated per project rather than put in `iac/env/*.tfvars`, because an `iac/env` edit redeploys both apps. It must match `snap-adapter`'s copy. IAM is asymmetric by design: `snap-adapter` owns the database and writes (`roles/datastore.user`), and this service only reads (`roles/datastore.viewer`, `iam.tf`) [8].

## Infra layout and runtime

Terraform lives in `iac/projects/snap-queue-polling-service/*.tf`: `cloud-run.tf`, `redis.tf`, `pubsub.tf`, `schedule.tf`, `remote.tf`, `iam.tf`, `networking.tf`. Shared per-environment values sit in `iac/env/*.tfvars` at the monorepo root. Each project includes `iac/projects/root.hcl` through terragrunt.

| Thing | Value |
| ----- | ----- |
| Git repo, CI, image name | `snap-queue-polling-service` |
| Cloud Run service, Datadog `service` tag, custom-metric prefix | `snap-polling-service` (`snap-polling-service-{env}`) |
| Envelope `metadata.source` on failures and poll triggers | `snap-queue-polling-service` |

- **Cloud Run.** 2 vCPU, 4 GiB, 600 s request timeout, ingress open to all, no explicit scaling block. A Datadog `serverless-init` sidecar (image tag `latest`, 256 Mi) tails logs from a shared in-memory volume and dual-ships logs and dogstatsd metrics to the GFS and ILG accounts. Direct VPC egress carries private ranges only (Redis); Pub/Sub, Datadog, GCS and config-service use the public path [7].
- **Redis.** Memorystore, `BASIC` tier, Redis 7, 1 GB. The cache layers an in-process LRU of 1,000 entries over Redis under the key prefix `snap-polling:`. The default TTL is one week. The confirmation claim TTL is 10 minutes [10][25].
- **Pub/Sub.** This stack owns four topics, each with a push subscription using the OIDC invoker service account: `snap_poll_schedule`, `snap_poll_customer`, `stock_sync_schedule` and `stock_sync_due` (`bifrost.<env>.<name>.v1`). It also holds a `config_revision` subscription on the `bifrost-pubsub` topic, and publisher grants on the confirmation, stock-adjustment and failure topics [5][8].
- **Schedules.** Two Cloud Scheduler jobs: `daily-run` (poll) and `stock-sync-schedule` [6].

## Build / test / deploy

- pnpm 10.30.3 through `mise` (`node = 24`). `pnpm test` runs Vitest. `snap-adapter` also runs Vitest, with configs kept per app. There is no `build:check:tests` script. Lint is Biome [10][32].
- CI is `.github/workflows/snap-queue-polling-service-*.yaml`. `code-quality` (test, lint, build:check) is path-filtered to this app and runs daily. `on-push` deploys: dev build and apply, then a `terraform-prod`-gated prod leg. It is path-filtered on `apps/snap-queue-polling-service/**`, `iac/projects/snap-queue-polling-service/**` and `iac/env/**`, so an `iac/env/*.tfvars` edit also redeploys `snap-adapter`. `manual-deploy` is `workflow_dispatch` to dev only. `blackbox-testing` and `tf-output` complete the set [35].
- Reusable workflows are pinned at `ilg-platform/github-actions/...@0.1-affogato`. The region is `europe-west2`, and the projects are `bifrost-dev-global1` and `bifrost-prod-global1`.
- The runner stage of `dockerfile` force-upgrades alpine `libcrypto3` and `libssl3`, because `node:24-alpine` still ships an openssl the dependency audit flags. Do not drop it without checking that the base image caught up [34].
- The black-box harness (`tests/mock-server.ts`) plays both SNAP and config-service on one Express app. It counts every request it does not exclude as a SNAP call (`expectedExternalCalls`). It excludes `/logs`, `/health`, `/backend*` and `/business*`. Any new config-service read must be added to that exclusion list and given a mock route, or the `Manual trigger` and `Check Endpoint` tests fail on call totals. The unit suite cannot catch it [33].
- The harness's Redis flush between cases does **not** clear the service's in-memory LRU tier, which `@gfs-bifrost/cache` back-fills on a Redis read hit (60 s default). A case that depends on that carryover should set `skipRedisFlush: true` rather than bake a 60-second timing assumption into its expected call total [33].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "apps/snap-queue-polling-service/src/bootstrap/app.ts@b16942a" },
  { "id": 2, "kind": "code", "ref": "apps/snap-queue-polling-service/src/bootstrap/factory/controller.factory.ts@b16942a" },
  { "id": 3, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/polling/polling.service.ts@b16942a" },
  { "id": 4, "kind": "code", "ref": "apps/snap-queue-polling-service/src/http/controllers/event.controller.ts@b16942a" },
  { "id": 5, "kind": "code", "ref": "iac/projects/snap-queue-polling-service/pubsub.tf@b16942a" },
  { "id": 6, "kind": "code", "ref": "iac/projects/snap-queue-polling-service/schedule.tf@b16942a" },
  { "id": 7, "kind": "code", "ref": "iac/projects/snap-queue-polling-service/cloud-run.tf@b16942a" },
  { "id": 8, "kind": "code", "ref": "iac/projects/snap-queue-polling-service/iam.tf@b16942a" },
  { "id": 9, "kind": "code", "ref": "apps/snap-queue-polling-service/src/http/middleware/auth.middleware.ts@b16942a" },
  { "id": 10, "kind": "code", "ref": "apps/snap-queue-polling-service/src/config/parse.ts@b16942a" },
  { "id": 11, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/stock-sync/stock-sync.service.ts@b16942a" },
  { "id": 12, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/stock-sync/aggregate-stock-totals.ts@b16942a" },
  { "id": 13, "kind": "code", "ref": "apps/snap-queue-polling-service/src/adapters/snap/api.client.ts@b16942a" },
  { "id": 14, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/confirmations.service.ts@b16942a" },
  { "id": 15, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/outbound-queue.clearer.ts@b16942a" },
  { "id": 16, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/confirmation-subscriptions.ts@b16942a" },
  { "id": 17, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/confirmation-failure.ts@b16942a" },
  { "id": 18, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/queue-lane.ts@b16942a" },
  { "id": 19, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/outbound-queue.drain.ts@b16942a" },
  { "id": 20, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/outbound-queue/cross-tenant.ts@b16942a" },
  { "id": 21, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/canonical-confirmation.handler.base.ts@b16942a" },
  { "id": 22, "kind": "code", "ref": "apps/snap-queue-polling-service/src/adapters/firestore/routing-metadata.reader.ts@b16942a" },
  { "id": 23, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/goods-out.confirmation-handler.ts@b16942a" },
  { "id": 24, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/despatch-confirmation.handler.base.ts@b16942a" },
  { "id": 25, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/cache/cache.service.ts@b16942a" },
  { "id": 26, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/config/remote-config.provider.ts@b16942a" },
  { "id": 27, "kind": "code", "ref": "apps/snap-queue-polling-service/src/adapters/snap/circuit-breaker.ts@b16942a" },
  { "id": 28, "kind": "code", "ref": "apps/snap-queue-polling-service/src/adapters/http/interceptors/retry.interceptor.ts@b16942a" },
  { "id": 29, "kind": "code", "ref": "apps/snap-queue-polling-service/src/adapters/pubsub/pubsub.router.ts@b16942a" },
  { "id": 30, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/receipt-confirmation.handler.base.ts@b16942a" },
  { "id": 31, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/map-entries-in-isolation.ts@b16942a" },
  { "id": 32, "kind": "code", "ref": "apps/snap-queue-polling-service/CLAUDE.md@b16942a" },
  { "id": 33, "kind": "code", "ref": "apps/snap-queue-polling-service/tests/mock-server.ts@b16942a" },
  { "id": 34, "kind": "code", "ref": "apps/snap-queue-polling-service/dockerfile@b16942a" },
  { "id": 35, "kind": "code", "ref": ".github/workflows/snap-queue-polling-service-on-push.yaml@b16942a" },
  { "id": 36, "kind": "doc", "ref": "fuse://pubsub-topology", "note": "subscribers of confirmation_ready and stock_adjustment_ready" },
  { "id": 37, "kind": "pr", "ref": "gfs-bifrost/snap-adapter#294", "note": "retires snap-adapter's stock adjustment clear-down" },
  { "id": 38, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/pick.confirmation-handler.ts@b16942a" },
  { "id": 39, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/pack.confirmation-handler.ts@b16942a" },
  { "id": 40, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/return-goods-authorization.confirmation-handler.ts@b16942a" },
  { "id": 41, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/finished-good-receipt.confirmation-handler.ts@b16942a" },
  { "id": 42, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/return-goods.discriminator.ts@b16942a" },
  { "id": 43, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/work-order-confirmation.confirmation-handler.ts@b16942a" },
  { "id": 44, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/work-order.discriminator.ts@b16942a" },
  { "id": 45, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/stock-adjustment.confirmation-handler.ts@b16942a" },
  { "id": 46, "kind": "code", "ref": "apps/snap-adapter/src/http/controllers/event.controller.ts@b16942a", "note": "no confirmation-made clear route remains" }
] }
```
