# contract-fit: can the poller express its own failures in the existing envelope?

Date 2026-09-29. Read-only. Refs read (all after `git fetch origin`):

| repo | ref | sha |
|---|---|---|
| pkg-node | origin/main | 4d62ab9 (types 10.8.0, pubsub 0.5.0, observability 2.2.0) |
| snap-adapter | origin/master (worktree early-consume-feasibility) | 3c1578b |
| collector | origin/master | f19ce57 |
| replay-service | origin/main | d75997f |
| fapi | origin/master | f4bd648 |
| sftp-connector | origin/master | f6a15e3 |
| shopify-connector | origin/main | 835c061 |

Paths below are relative to the repo's tree at that sha. Poller = `apps/snap-queue-polling-service/src` (abbrev `P/`).

## 1. The failure envelope (pkg-node types 10.8.0)

`BifrostFailure` (`pkg/types/src/pubsub/types/bifrost-failure.type.ts:38-61`, schema `.../schemas/bifrost-failure.schema.ts:50-59`):

- required: `useCase: FailureUseCase`, `stage: FailureStage`, `source: string (min 1)`, `errors: FailureError[] (min 1)`
- optional: `upstream {topic, subscription?, inboundMessageId?, attempts?}`, `record: Record<string, unknown>`, `connectorId`, `transaction`
- there is NO `businessId`, NO `recordId`, NO `queueId` on BifrostFailure. Customer = envelope `metadata.customer` (+ Pub/Sub attribute `customer`). `metadata.recordId?` exists on the envelope (`bifrost-message.type.ts:1-9`), `metadata.recordType?`, `metadata.connectorId?`, `metadata.source?`.
- `record` is an untyped `z.record(string, unknown)` (schema line 56) - the envelope itself never checks the record is canonical. Canonical-ness is enforced only by consumers (replay deep-partial) and by AGENTS.md convention.
- `FailureAttributes` = `{recordType: FailureUseCase, stage, source, customer}` all required (`:63-68`); Pub/Sub attributes are validated only if a publisher calls the schema (poller's publisher does not; `PubSubRouter.publishToTopic` does no validation, `pkg/pubsub/src/router.ts:91-110`).
- `FailureError` union (`failures.type.ts`): `validation{field}`, `dependency{dependency,operation,code,retryable}`, `infrastructure{service,code,retryable}`, `business_rule{rule}`; all carry `problem`.

`FailureUseCase` members (`bifrost-failure.type.ts:3-19`): sales_order, purchase_order, master_data, stock_adjustment, stock_sync, goods_in_confirmation, goods_out_confirmation, pick_confirmation, pack_confirmation, config_revision, customer_creation, return_goods_authorization, return_goods_confirmation, work_order, work_order_confirmation, finished_good_receipt.

- All eight confirmation record types have a confirmation-side name. Only `stock_adjustment` has NO distinct confirmation-side name (shares the create-side value; RGA has `return_goods_confirmation`).
- CONFIRMATION_RECORD_REGISTRY (`pkg/types/src/confirmations/confirmation-registry.ts:47-92`) maps: purchase_order->goods_in_confirmation, sales_order->goods_out_confirmation, stock_adjustment->stock_adjustment, return_goods_authorization->return_goods_confirmation, pick/pack/WOC/FGR->same name. Poller's own map `P/core/snap/confirmations/confirmation-failure.ts:19-28` duplicates it by hand (does not import the registry).
- Registry businessId accessors: goods in/out use `identifiers.bizId`; the other six use `identifiers.businessId`. Registry carries the strict canonical `schema` per type (no deep-partial variant).

`FailureStage` (`:21-29`): ingest_request, ingest, wms_submission, release, confirmation_ready, confirmation_made, config, unknown. `confirmation_ready` = "failed on the way out of / at confirmation_ready" and is what the poller uses (`confirmation-failure.ts:30`), sftp-connector uses it for write failures, fapi/snap-adapter use `confirmation_made`. There is no dedicated "poller map/find" stage; nothing in replay/collector switches on stage (only metric tag in replay `event.controller.ts:158`). Adding a stage is a types minor bump but currently stage is purely informational.

`deepPartialify` (`pkg/types/src/shared/deep-partial.ts:25-81`): makes every object key optional at every depth, drops `.default()`, keeps leaf validators (so a present-but-wrong-typed value, e.g. a bad date string, still fails). It does NOT special-case ZodPipe/discriminated unions beyond `ZodUnion`. It is a validator, not a builder: it does not construct a partial canonical from raw SNAP data.

Observability catalogue: `CONFIRMATION_METRIC` (`pkg/observability/src/catalog/confirmations.type.ts:7-20`) has FAILURE_EMITTED = `confirmation.failure.emitted`, RETRIEVED, PUBLISHED, UNROUTABLE, FORWARD_*; `FAILURE_STAGE` in observability is only ingest|wms_submission (`catalog/replay.type.ts:31-34`) - a different, narrower enum than the types package. `SNAP_POLLING_METRIC` is NOT in pkg-node: it is local to the poller (`P/observability/catalog/snap-polling.type.ts:4-53`), including CONFIRMATION_UNPARSEABLE, CONFIRMATION_MAP_SKIPPED, POLL_FAILURE, CONFIRMATION_WITHHELD_*, CLAIMED_ENTRY_SKIPPED, CROSS_TENANT_ENTRY_SKIPPED, CONFIRMATION_CLAIM_FAIL_OPEN. `MANUAL_ORIGIN_BROADCAST_METRIC` is also local with a TODO to move.

Fuse MCP: `lookup-type BifrostFailure` -> "No types matching" (MCP only lists canonicals). `lookup-topic confirmation_data_failure` lists publishers fapi, snap-adapter, sftp-connector (poller missing) and says collector subscribes only to WOC/FGR; actual collector IaC now has PO/SO/SA/WOC/FGR (see section 4). MCP entry is stale on both points.

## 2. What the poller already publishes on the failure topic

`IConfirmationFailurePublisher` / `ConfirmationFailurePublisher` (`P/adapters/pubsub/confirmation-failure.publisher.ts`): `PubSubRouter.publishToTopic(CONFIRMATION_DATA_FAILURE_TOPIC_NAME, failure, metadata, attributes)`. Topic env is wired (`P/config/config.schemas.ts:49`, IaC `iac/projects/snap-queue-polling-service/cloud-run.tf:89`) and the publisher IAM binding exists (`.../pubsub.tf:205`).

Only ONE call site: `ConfirmationsService.announceConfirmations` (`confirmations.service.ts:336-358`) -> `buildManualOriginFailure(type, customer, record)`. That failure is:
- `useCase` = confirmation-side value, `stage` = confirmation_ready, `source` = `"snap-queue-polling-service"` (`P/shared/constants.ts:3`), one `business_rule` error `no_originating_connector`, `record` = the full canonical, one message per record, metadata = the announce metadata (no `source`, `recordType` overwritten with the failure use case).
- It is NOT a real failure ("nothing failed" per the code comment) - it is an informational marker for manual-origin (no connector) orders, emitted AFTER the confirmation_ready emit succeeded, for the 7 routing-aware types (not stock_adjustment).

Every real drop point in the poller (map/validate/route/withhold/publish) does NOT use the failure publisher: they only `logger.*` + a local metric (table in section 5). So the poller has the capability and the topic, but zero real failure emissions today.

## 3. Natural key: queueId

- OBQ row (`SnapOutboundMessage`, `pkg/types/src/snap/types/entities/outbound.type.ts`): `Host, XDoc, Transaction, Key, Message, Error, Batch, DateCreated, DateProcessed, Stage`. No BizId/businessId on the row. `XDoc` is the row id; `clearFromOutboundQueue(queueId)` = `PATCH /v2/snapoutbound/{queueId}/processed` (`P/adapters/snap/api.client.ts:153-157`).
- Poller stamps `identifiers.queueId = item.XDoc` (despatch/receipt bases; stock adjustment uses `stockMovement.xDoc`, `stock-adjustment.confirmation-handler.ts:145`) - grep of `queueId` in all eight handlers: goods-in :325, goods-out :293, stock-adjustment :145, RGA :338, pick :166, pack :202, WOC :183, FGR :89 (the latter six via `id` = XDoc).
- Canonical types: `queueId` REQUIRED on GoodsInConfirmation, GoodsOutConfirmation, CanonicalStockAdjustment; OPTIONAL on RGA, pick, pack, WOC, FGR (grep, `pkg/types/src/canonical/{types,schemas}`). Present in all 8 with the schema, so it survives Zod at boundaries.
- Connectors pass the canonical through, so it survives into `confirmation_made` (snap-adapter `event.controller.ts:203-216` reads `record.identifiers.queueId` to clear; a record without it is "not clearable" and produces a failure). fapi/sftp/shopify reference queueId only in field docs/fixtures (no stripping).
- Uniqueness: claim key is `confirmation_claim:{businessId}:{queueId}` with the comment "queueId is only unique per SNAP tenant" (`P/core/cache/cache.service.ts:117-120`); on shared SNAP hosts the queue is instance-wide and co-tenant rows appear (`outbound-queue/cross-tenant.ts`, `RoutingLaneEvent.CrossTenantEntrySkipped`). Natural key for a ledger = (SNAP host/tenant, XDoc), not queueId alone. The OBQ row does not say which business owns it; owner (`BizId`) is learned only by fetching the shipment/receipt/movement (enrichment).
- Collector does NOT key on queueId: confirmation collections upsert on business keys (`{receiptId,bizId}`, `{shipmentId,bizId|businessId}`, `{id,businessId}`; `ConfirmationRegistryService`), and `markFailed` matches on the same keys. Replay clear-down matches `useCase+businessId+record.identifiers.shipmentId` and only handles pick/pack. So a queueId-keyed ledger does not exist anywhere downstream today; two OBQ rows for the same receipt/shipment overwrite one collector doc.
- `isClearable` = truthy `identifiers.queueId` (`confirmations.service.ts:68-72`). In `claimConfirmations` a record with no queueId gets `claim: undefined`, is treated as publishable, is never claimed and can never be cleared (optional queueId types).

## 4. Who accepts what (failure topic consumers)

Failure topic subscriptions at the read shas:

| failureUseCase (attribute recordType) | replay sub | collector sub |
|---|---|---|
| goods_in_confirmation | yes (goods sub, `pubsub.tf:115`) | yes, `NOT source="snap-adapter"` (collector `pubsub.tf:29-34`) |
| goods_out_confirmation | yes | yes |
| return_goods_confirmation | yes | NO |
| pick_confirmation | yes | NO |
| pack_confirmation | yes | NO |
| work_order_confirmation | yes | yes |
| finished_good_receipt | yes | yes |
| stock_adjustment | NO (not in either replay filter; replay `isConfirmationRecordType` also lacks it) | yes |

Replay intake (`replay-service code/src/http/controllers/event.controller.ts:207-284`):
- Decodes `BifrostFailureSchema` (single or bulk), requires `isConfirmationRecordType(useCase)`, then `deepPartial(schema).safeParse(record)` per confirmation; on `ValidationError`/`DecodeError` it ACK-AND-DROPS with only a metric (`FAILURE_DROPPED`) and a log (`:265-281`). Stored via `saveCreateFailure`: `businessId` is derived ONLY from `record.identifiers.businessId` (else `""`; `failure.service.ts:659-687`), NOT from `metadata.customer`. Record id from `metadata.recordId` else per-type identifier (`derive-record-id.ts`).
- Stores `failure.record` unparsed (the deep-partial parse is a gate only; `z.object` strips unknown keys but the stored copy is the original). A record with no `record` at all is stored as `{}` (`unwrapConfirmations`).
- Missing record => `{}` stored, businessId `""`: appears in the global queue, invisible in per-business filters/stats.
- Replayability gate is the STRICT canonical schema (`failures.controller.ts:628-640`, `derive-replayability.ts`); a partial/unmappable record is stored but `replayable:false` until PATCHed.
- Redrive republishes `[record]` to `CONFIRMATION_READY_TOPIC` with attributes `{recordType}` ONLY (`failure.service.ts:748-756`, `pubsub.service.ts:238-259`); RGA maps back to `return_goods_authorization`. IMPORTANT: connector confirmation_ready subscriptions all require `attributes.source = "<channel>" OR attributes.broadcast = "true"` (fapi `api-gateway/pubsub.tf:152,182,274,307,337,371`; sftp `bifrost-sftp-connector/pubsub.tf:13,251-378`; shopify `pubsub.tf:320`). The poller sets `source` / `broadcast` attributes (`P/adapters/pubsub/pubsub.router.ts:93-102`); replay's redrive sets neither, and its metadata handling copies only envelope metadata (`replayMetadata`, "a redrive must never invent one"). From source alone, a replayed confirmation is delivered to no connector subscription (only the collector's unfiltered-by-source ready sub) while replay records `status: success`. Needs live confirmation (open question).
- DLT: both replay confirmation failure subs dead-letter after 5 attempts to `replay.{env}.confirmation_data_failure.v1.dlt`; no subscription is defined on that topic anywhere in `iac/projects/replay` (grep `google_pubsub_subscription"` finds only 4 subs, none on the DLTs) so exhausted messages are not retained anywhere queryable.
- Collector failure intake (`event.controller.ts:942-1000`): never upserts; `markFailed` matches by business key and returns 0 for unheld ("FailureForUnheldRecord" log only); no `record` => `FailureWithoutRecord` log only; collector failure subs have no DLT (retry_policy only). Collector "holds" a confirmation only if it consumed the earlier `confirmation_ready`; a failure for a row that never reached confirmation_ready (map/validate failure) is a no-op, so for early failures replay is the only durable store, and for stock_adjustment nothing is (replay no sub, collector no-op).
- LIFECYCLE `failed` is the highest rank and terminal (`collector models/lifecycle.ts:36-41`). Poller's manual-origin failure has `source="snap-queue-polling-service"`, which passes the collector filter `NOT source="snap-adapter"`, so for goods_in/goods_out/WOC/FGR it marks the already-broadcast confirmation `failed` in collector; a later `confirmation_made` cannot demote it. Existing defect (informational failure treated as real failure). For pick/pack/RGA it lands in replay's retry queue as a replayable failure (a replay would re-broadcast).

## 5. Exit paths for an OBQ row today (and if it were already processed)

See structured exit_paths. Summary of what evidence supports "the safety net":
- `dropClaimed` (`queue-lane.ts:107-142`): claimed rows are skipped pre-enrichment; claim TTL 10 min (`config.schemas.ts:64`, default 600000).
- Claim is taken BEFORE publish (`claimConfirmations` then `emit`, `confirmations.service.ts:287-334`). If `emit` throws, the claim persists for 10 min, the exception aborts the `for (group ...)` loop (no try/catch) so later groups in that poll are not announced, the poll push handler 5xxs (`event.controller.ts:145`, no catch) and Pub/Sub redelivers; on redelivery the already-claimed rows are skipped as "duplicate" until the TTL expires. Today that is a 10-minute delay (row still on OBQ); with early consume it is a permanent loss.
- `tryClaimConfirmation` returning `unavailable` fails OPEN (publish anyway): duplicates are possible; with early consume a duplicate publish is the only remaining safety.
- `resolveDespatch/Receipt/MovementEntries`: `parseKeyVal`+`ZodUtils.parse` throws on a malformed `Key`; in despatch/receipt the throw is inside `items.map` so ONE bad row rejects the whole lane resolve for that business (whole lane poll fails, `POLL_FAILURE`); movement `Promise.all` likewise (also any single stock-movement fetch error). Existing poison-row/head-of-line block; row can never be consumed by the current flow and would block its neighbours.
- SNAP record not returned for a queue item: `return []`, no log and no metric in despatch/receipt (comment: "dropped, not failed - the queue item stays put").
- Customer not in `enabledCustomersById`: silent `return []` (no log, no metric) at `confirmations.service.ts:107-109`. Combined with connector `confirmationsEnabled=false` withholding this is the "disabled = deferred" feature; under early consume it is silent loss.
- Poller already consumes some rows itself (`ConfirmationDisposer`): cancelled shipment (goods-out) and all-zero-quantity receipt (goods-in) call `clearFromOutboundQueue` with only a log `IngestEvent.RecordDropped` tagged DROPPED_CONFIRMATION; clear failure -> `logger.error("Confirmation drop failed")` and row stays. These are deliberate terminal consumes with no ledger/failure record (`confirmation.disposer.ts`).

## 6. What can legally go on the bus for an unmappable / unroutable / unpublishable row

Canonical-only rule (AGENTS.md): raw SNAP objects (`SnapOutboundMessage`, `SnapShipment`) must not be published, so a `record` = raw SNAP payload is out. Legal options within existing types:

1. Row maps but fails strict validation (the only case where a canonical exists): publish `BifrostFailure{useCase: registry.failureUseCase, stage: confirmation_ready, source: poller, errors:[validation{field,problem}...], record: <the DeepPartial canonical>}` with `metadata.customer = identifiers.businessId|bizId`, `metadata.recordId`. `deepPartialify(registry.schema)` validates it; replay accepts it, stores it non-replayable until PATCHed. The handlers currently discard this canonical inside `validateCanonicalConfirmations` (`records.filter`), keeping only the Zod issues in a log.
2. Row cannot be mapped (enrichment threw, SNAP record missing, unparseable Key, unknown movement direction, cancelled): there is no canonical. The only envelope-legal shape is a MINIMAL partial canonical of identifiers derivable from the row and its parsed Key, e.g. `record: { identifiers: { queueId, shipmentId|receiptId|id..., businessId? } }` - identifiers are optional at deep-partial depth so replay accepts it. Limits: (a) `businessId` is unknown before enrichment (no BizId on the OBQ row); the polling client's businessId is not necessarily the owner on shared hosts, so `metadata.customer`/`attributes.customer` may be wrong, and replay would store businessId `""` unless identifiers.businessId is set; (b) replay's strict gate cannot pass, so recovery is manual and there is no way for replay to re-run the mapping from a queueId; (c) nothing in the OBQ row beyond XDoc/Key/Transaction/DateCreated/Stage/Error fits a canonical field, so diagnostics must go in `errors[].problem` or `metadata`, not the record; (d) stock_adjustment has no replay subscription and its collector failure route is a no-op for unheld records, so no durable consumer exists for it.
3. Row is valid but unroutable (no connector match, withheld, connector unresolvable): canonical exists; the same failure shape works, but the record types where the collector has no failure sub (pick/pack/RGA) rely on replay alone; and for `withheld_ineligible_connector` the semantic today is "defer until enabled" - a failure record would turn a feature into a queue of terminal errors unless a separate status is introduced.
4. Cannot publish at all (Pub/Sub down): the failure topic is the same transport; the only durable options are keep the row on the OBQ, nack the poll message, or an out-of-band store. `topic.publishMessage` is awaited so the poller can mark the row processed only after the server ack (design note, verified in code that emit is awaited, not verified against the SDK).

Consumption after the publish ack of confirmation_ready would fit the envelope contract (record + ledger via collector/replay), but a ledger keyed by queueId does not exist downstream and collector/replay key on business identifiers.

## 7. Version skew

- Poller, snap-adapter, collector, fapi: `@gfs-bifrost/types ^10.7.0`, lock 10.7.0; shopify 10.7.0 exact; sftp `^10.8.0`; replay `^10.7.0`. All carry every FailureUseCase/stage listed above (added in 7.6.0/8.4.0/9.3.0/6.x) and `queueId` on all eight canonicals. 10.8.0 only adds stock-adjustment batch/expiry/movementRef.
- Poller lockfile also resolves `@gfs-bifrost/types@9.5.0` because `@gfs-bifrost/pubsub@0.5.0` froze `types` to 9.5.0 (`apps/snap-queue-polling-service/pnpm-lock.yaml` lines ~2580). Only type shapes flow through pubsub (router does no validation), so failure publishing is unaffected, but `PubSubIngestor` in the poller/snap-adapter validates envelopes with 9.5.0 schemas. Any new BifrostFailure field or stage added in types >9.5 would be stripped by pubsub-side ingestion (the pubsub 0.4.1 lesson in CLAUDE.md).
- A new FailureUseCase/FailureStage member needs types minor bump, and replay/collector filters + `CONFIRMATION_RECORD_TYPES`/`isConfirmationRecordType` lists updated; replay's filter length cap (256 chars) already forced a second subscription (`pubsub.tf:63-68`).

## 8. Open questions

- Live state of connector confirmation_ready subscriptions and replay redrive delivery (source/broadcast attributes) - not queried.
- Whether the poller's manual-origin failure actually marked collector rows failed in prod (Datadog not queried).
- Whether any process reads the replay confirmation DLT (no sub in IaC).
- Google SDK ack semantics for `publishMessage` were assumed, not read.
