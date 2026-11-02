# replay-service — early-consume feasibility (read-only study, 2026-09-29)

Refs read (all remote default branches, fetched 2026-09-29):
- replay-service@d75997f (origin/main; prod deploys of main up to cf6b637 confirmed `success` 2026-09-24, d75997f `waiting` at read time). Detached worktree used, removed at end.
- snap-adapter@3c1578b (poller apps/snap-queue-polling-service, apps/snap-adapter clear-down)
- fapi@f4bd648, sftp-connector@f6a15e3, shopify-connector@835c061, collector@f19ce57, pkg-node@4d62ab9 (types 10.8.0), observability@81d508f
- replay-service open draft PR #96 (FUSE-1257, head b88b757) read via gh (read-only)
- Vault: Engineering/replay-service (verified 2026-09-02 @bbe37e4; STALE vs d75997f: says goods-in/out ride legacy topics — superseded by #85; says wrapped fapi failures stored with empty businessId — fixed by #91)
- Datadog prod, 30d window.

## 1. What replay-service is (facts)

Failure inbox + manual redrive console. Mongo `failures` collection (no TTL, no retention; iac mongo.tf has no expiry). Three push subscriptions in, all OIDC push, ack_deadline 20s, 30s min backoff, dead_letter max 5 attempts to a DLT that NOTHING subscribes to.

| Subscription (replay.{env}.*) | Topic | Filter (attributes.recordType) | Handler |
|---|---|---|---|
| create_data_failure.v1.sub | create_data_failure | sales_order, purchase_order, master_data, work_order | /event/create-failure |
| confirmation_data_failure.v1.sub | confirmation_data_failure | pick_confirmation, pack_confirmation, work_order_confirmation, finished_good_receipt | /event/confirmation-failure |
| confirmation_data_failure.goods.v1.sub | confirmation_data_failure | goods_in_confirmation, goods_out_confirmation, return_goods_confirmation | same |
| confirmation_made.v1.sub | confirmation_made | pick_confirmation, pack_confirmation | /event/confirmation-made |
(iac/projects/replay/pubsub.tf:19-194, replay-service@d75997f)

NOT captured at all: `stock_adjustment` failures (a valid FailureUseCase in pkg-node 10.8.0 and what fapi's registry stamps: confirmation-registry.ts failureUseCase "stock_adjustment"); create-side RGA; any recordType not in the filter. A message whose recordType matches no subscription is simply never delivered to replay (no error, no metric). Collector subscribes stock_adjustment failures but with `NOT attributes.source = "snap-adapter"` (collector pubsub.tf:34), so a snap-adapter clear-down failure for stock_adjustment lands nowhere.

### Stored record
`FailureRecord` (failure.service.ts:96-135): id (fresh randomUUID per message, no idempotency key -> redelivery = duplicate row, failure.service.ts:223), useCase, businessId (derived from record.identifiers.businessId; master_data from product.identifiers.businessId; "" if absent -> invisible in per-business queue, failure.service.ts:659-688), record (deep-partial-validated canonical), metadata (envelope metadata verbatim), createdAt, replayHistory[{timestamp,messageId,status,by}], editHistory (diffs), stage, source, errors, upstream, connectorId, transaction, dismissed*/cleared*/assigned* fields, soft delete via deletedAt.
Repository `save` is upsert + `$unset deletedAt` (collection.ts:92-104) with read-modify-write callers (addReplayHistory, updateFailure, assignFailure) -> lost-update and "resurrect a soft-deleted row" races.

### Ingest exit paths
- Store OK -> 201 (event.controller.ts:148-159; confirmation route 251-264).
- useCase not in the schema map -> ack + skip, metric `fuse.replay.failure_skipped` only (event.controller.ts:128-135, 227-234).
- Deep-partial validation fails (`deepPartialify(canonical)`; present values must still type-check) -> ValidationError -> ack-and-drop, metric fuse.failure.dropped{reason=validation}, log (event.controller.ts:137-146, 164-179). Whole message dropped: for a bulk/wrapped envelope one bad confirmation drops ALL (confirmation-failure route 236-249 "all-or-nothing").
- Envelope decode/Zod fail (PubSubEventSchema, BifrostFailureSchema, min(1) errors, source min(1)) -> ack-and-drop (pubsub.service.ts).
- Transient (Mongo DatabaseError) -> nack -> 5 attempts -> DLT (unconsumed).
- Prod 30d: fuse.failure.dropped{reason:validation} = 32 events (Datadog, environment:prod). Cause not established (no matching logs found with my queries) -> open question.

### Monitoring of those paths (prod, verified live via Datadog monitor search)
- Drop monitors (ids 303413082, 302536180) query `replay_service.event.create_failure_dropped` — that metric returns no data in prod; the live metric is `fuse.failure.dropped`. 32 real drops occurred in 30d and the monitors stayed OK / No Data. They are dead.
- DLT monitor (303413085) scoped to `subscription_id:replay.*.create_data_failure.v1.sub` only: the two confirmation_data_failure subs and confirmation_made sub are NOT covered. Only "oldest unacked age >300s on replay.*" (303413083) covers them, which does not fire for DLT'd or dropped messages.
- Net: confirmation-side ingest loss (drop or DLT) is silent to alerting.

### Producers into confirmation_data_failure (source-verified) and what they send
| Producer | useCase / recordType attr | Envelope | Record | Stage | Publish-failure handling |
|---|---|---|---|---|---|
| snap-queue-polling-service (poller) | goods_in/out_confirmation, pick/pack, etc. via FAILURE_USE_CASE map | single | valid canonical | confirmation_ready | only emits for `no_originating_connector` manual-origin broadcast notice (confirmations.service.ts:336-358, confirmation-failure.ts). Nothing for map/validate/route/withhold failures. |
| snap-adapter clear-down | goods_in/out, return_goods_confirmation, or raw recordType e.g. stock_adjustment (event.controller.ts:62-79) | single | the DELIVERED canonical | confirmation_made, source snap-adapter | `publish` returns false -> log + metric only (confirmation-error.service.ts:57-66). Handler already returned 202 before doing the work (event.controller.ts:151). |
| fapi | getConfirmationFailureUseCase(type) | single failure, `record:{confirmations:[..]}` | canonical batch | confirmation_made, source "rest" | try/catch -> log event only (confirmation.service.ts:416-455). Overwrites metadata.source with fapi's source (pubsub-emitter.ts:275-281) |
| sftp-connector | useCase map (operations.ts:14-21) | bulk `record: BifrostFailure[]` | per-confirmation (invalid rec or valid) | confirmation_ready | catch -> logger.error only (confirmation-egress.service.ts:290-303). Push is acked, "never nack a write failure" (line 212-215) |
| shopify-connector | goods_out_confirmation | single | canonical | confirmation_ready | only `connector_unresolvable`; delivery errors not published as failures here; publish error -> log (confirmation.failure-publisher.ts:60-70) |

Prod 30d intake (fuse.failures.received, environment:prod, by source/stage/recordtype): goods_out_confirmation from snap-queue-polling-service/confirmation_ready = 39,269 (the manual-origin notice re-emitted every poll because the row stays on the OBQ); goods_in_confirmation poller 52; pick_confirmation poller 3; goods_out_confirmation snap-adapter/confirmation_made (clear-down failures) 63; goods_out_confirmation rest/confirmation_made 77. Zero for pack/WOC/FGR/RGA and zero sftp/shopify confirmation-side. (Create-side: sales_order snap-adapter 3,761; master_data 1,133; sftp 228+11+1; PO 53.)

## 2. Redrive (verified at d75997f)

`redriveFailure` (failures.controller.ts:610-722): getReplayTarget -> strict canonical `safeParse(failure.record)` gate (400/ValidationError if fails; no replayHistory written on gate rejection) -> publish -> addReplayHistory.
- Inbound types -> CREATE_RECORD_REQUEST_TOPIC, single, attrs {recordType}.
- Confirmation types -> CONFIRMATION_READY_TOPIC, single-element bulk envelope, attrs ONLY {recordType}. goods_in/goods_out publish as recordType goods_in_confirmation / goods_out_confirmation (FUSE-1059 #85 fixed; vault stale). return_goods_confirmation publishes recordType return_goods_authorization (failure.service.ts:724-735).
- metadata preserved verbatim except fresh timestamp; no `source` invented (#94) (pubsub.service.ts:251-259).
- History status "success" = Pub/Sub publish accepted, nothing more. Publish error -> history "failed", rethrown. Publish OK then history write fails -> catch writes "failed" (or throws) though message is out.
- Nothing is cleared/resolved by a successful redrive. The row stays in the queue as "Failed again"/replayed until a confirmation_made clears it.
- Bulk replay: max 100 ids, 5 concurrent, per-id result.
- x-user is attribution only; API-key guard.

### The known claim: VERIFIED, still unfixed at d75997f
Redrive stamps only {recordType}. Delivery subscriptions on confirmation_ready are channel-filtered:
- fapi: PO/SO/pick/pack/WOC/FGR: `(recordType=..) AND (attributes.source = "rest" OR attributes.broadcast = "true")` (fapi pubsub.tf:~152-372). RGA: recordType only.
- sftp-connector: pick/pack/PO(goods_in)/SO(goods_out)/FGR/WOC: `AND (attributes.source = "sftp" OR attributes.broadcast = "true")` (pubsub.tf:13); RGA: recordType only (pubsub.tf:220 comment).
- shopify-connector goods_out: `AND (attributes.source = "shopify" OR attributes.broadcast = "true")`.
The poller stamps source and/or broadcast attributes (pubsub.router.ts:93-102, confirmations.service.ts:252-269); replay does not. So a redriven pick/pack/goods_in/goods_out/WOC/FGR matches NO connector subscription. Collector subscriptions filter on recordType only (collector pubsub.tf:290-460) so collector alone receives it. replayHistory records "success" with a messageId. The replay-service PR #96 body states the same gap ("Not fixed here; flagged for a follow-up") and its verification transcript notes publishing to confirmation_ready without source/broadcast is consumed only by collector + fuse-mocker. Only RGA redrives reach connectors.
Fix direction (not designing): stamping broadcast="true" would fan out to every connector; faithful targeting needs source attr (channel) derived from connectorId/stored provenance, and stored metadata.source is unreliable because fapi/sftp overwrite it with their own service name.

### Clear-down (confirmation_made) is broken on current main
handleConfirmationMade decodes with decodeBulkMessage (BulkEventSchema requires `record` array, pubsub.service.ts:41-44,199-223). fapi emits confirmation_made as one single-record BifrostMessage per record (pubsub-emitter.ts comment "Every confirmation_made topic carries one single-record BifrostMessage") and sftp/shopify likewise -> every real ack fails Zod -> ValidationError -> ack-and-drop. Also subscription is pick/pack only, matched by shipmentId only. Consequence today: a failure that later succeeds (or was redriven successfully) never leaves the queue. PR #96 (draft, unmerged) fixes this and extends to all types, connector-aware, and stops storing manual-origin notices. Prod counters `confirmation_made_handled/dropped/cleared` are all empty in the 30d window (no pick/pack made traffic on the subscribed filter).

### snap-adapter clear-down failures and redrive
These (63 prod/30d) are post-delivery: the customer already got the confirmation, only the OBQ clear failed. replay stores them under the same useCase as delivery failures. A redrive republishes the confirmation on confirmation_ready = a second delivery to the customer (once the attribute gap is fixed), not a retry of the clear. Today it would be black-holed by the same attribute gap. Nothing in replay distinguishes them except stage=confirmation_made + source=snap-adapter (fapi delivery failures share stage confirmation_made). Under early consume the clear-down path and this failure class disappear, but historical rows and any residual mark-processed failure need a defined home.

## 3. Matrix: recordType x (stored? redrivable? lands where?)

Legend. "Downstream-failure": a connector failed to deliver (fapi/sftp/shopify -> confirmation_data_failure). "Poller-failure": poller failed to map/validate/route before publishing.

| recordType (registry key) | failure useCase / attr | Stored by replay? | Redrivable? | Redrive lands where | Poller-pre-publish failure holdable? | Evidence |
|---|---|---|---|---|---|---|
| purchase_order (goods-in) | goods_in_confirmation | Yes (goods sub; businessId from identifiers.businessId, required in type) | Yes after strict gate (usually needs PATCH) | confirmation_ready recordType=goods_in_confirmation, attrs {recordType} only: collector only; fapi/sftp filtered out (need source/broadcast) => connectors never see it | No: poller never publishes a failure for map/validate/route errors; only manual-origin notice (52 prod/30d) | failure.service.ts:720-721; fapi pubsub.tf PO sub; sftp pubsub.tf:117 |
| sales_order (goods-out) | goods_out_confirmation | Yes | Yes | same: collector only; fapi/sftp/shopify all channel-filtered => black hole | No (39,269 manual-origin notices stored; raw/unmapped never sent) | failure.service.ts:722-723; shopify pubsub.tf goods_out filter |
| stock_adjustment | stock_adjustment (registry) | NO: not in either replay subscription filter nor in schema maps | NO: getReplayTarget default -> null -> 400 | n/a; poller publishes stock adjustments on the per-entity stock_adjustment_ready topic (no recordType), replay has no publisher grant for it | No | confirmation-schema.ts; pubsub.tf filters; controller.factory.ts:43 |
| return_goods_authorization | return_goods_confirmation (stored) -> recordType return_goods_authorization on redrive | Yes (confirmation side only; create-side RGA deliberately not stored) | Yes | confirmation_ready recordType=return_goods_authorization; fapi and sftp RGA subs have NO channel filter => actually delivered (the only type that is) | No (poller failure never published; poller RGA is broadcast-only) | failure.service.ts:724-735; fapi pubsub.tf rga sub; sftp pubsub.tf:42 |
| pick_confirmation | pick_confirmation | Yes (confirmation sub) | Yes | confirmation_ready recordType=pick_confirmation: collector only; fapi/sftp filtered out | No (3 manual-origin notices; map/validate failures never published) | failure.service.ts:700-704; poller pick handler validateCanonicalConfirmations drops + metric CONFIRMATION_HANGING |
| pack_confirmation | pack_confirmation | Yes | Yes | same as pick | No | failure.service.ts:705-709 |
| work_order_confirmation | work_order_confirmation | Yes | Yes | collector only; fapi WOC (channel-filtered) and sftp WOC (channel filter) miss it | No | failure.service.ts:710-714 |
| finished_good_receipt | finished_good_receipt | Yes | Yes | collector only; fapi/sftp FGR channel-filtered | No | failure.service.ts:715-719 |

Downstream-failure holdability: storing works for 7 of 8 types (not stock_adjustment) provided the producer publishes the failure with a matching recordType and the record passes the deep-partial. A record that is a valid canonical (all downstream failures, since the poller validated it) is stored losslessly (strict parse output re-published; Zod strips unknown keys). fapi's `{confirmations}` wrapper is split per confirmation (#91) and sftp's bulk failure envelope accepted (#92), but validation is all-or-nothing per message.
Pre-canonical / partly-canonical (poller-side): replay cannot faithfully hold these. (a) the poller does not send them; (b) a raw SNAP-shaped record must not go on the bus (AGENTS.md canonical-first); (c) if sent as partial canonical it survives the deep-partial only if present fields type-check, else the whole message is ack-and-dropped; (d) businessId "" if identifiers.businessId missing; (e) even when stored, "replay" republishes a strict-validated canonical to confirmation_ready, so unmappable rows stay unreplayable until PATCHed by a human. There is no replay path that re-runs the poller's mapping from SNAP raw.

## 4. Dependence on the OBQ safety net (per exit path)

| Path | Today | Depends on row staying on OBQ? | If row already consumed |
|---|---|---|---|
| Poller drops invalid canonical (validateCanonicalConfirmations) | log+metric, no failure sent; row re-polled every cycle | YES (only recovery is fixing mapping then re-poll) | Lost permanently; nothing in replay |
| Poller withholds (connector not enabled / unresolved connector) | logged, row stays, "enabling releases backlog" | YES (feature) | Lost/or must be re-parked in replay; replay cannot represent "deferred until enabled" |
| Manual-origin notice | stored (39k rows) because re-announced per poll | YES (flood is a symptom) | Emitted once; fine but informational |
| Failure publish fails at any producer (fapi/sftp/snap-adapter/shopify/poller) | log only; nothing recorded in replay; row still on OBQ -> re-announced | YES | Lost with only a log line |
| Failure lands, filtered out (stock_adjustment, unknown recordType) | Never reaches replay; OBQ re-announce | YES | Lost |
| Ingest drop (validation/decode) | ack-and-drop, dead monitors; OBQ re-announce | YES | Lost; 32 drops/30d already |
| DLT after 5 attempts | sits unconsumed; no monitor for confirmation subs | YES | Lost |
| Delivery failed -> stored -> operator redrive | redrive black-holed (attrs) but row still on OBQ, so a later poll re-announces and actually delivers | YES (accidentally masks the redrive bug) | Redrive is the ONLY route and it does not deliver (except RGA) |
| Clear-down failure (snap-adapter) | stored; redrive = duplicate | n/a | class disappears; residual mark-processed failure needs home |
| Redrive success recorded | "success" = published, not delivered; no auto-resolve (clear-down broken) | n/a | operator can't tell delivered vs not |

## 5. Gaps (also in structured output)
See StructuredOutput. Highlights: G1 redrive attribute black hole (7/8 types incl. every type early-consume most needs); G2 stock_adjustment has no replay sink; G3 no failure is ever produced for poller map/validate/route/withhold drops; G4 producers' failure publish is best-effort log-only; G5 ingest drop/DLT alerting dead or absent for confirmation side; G6 clear-down route rejects real single-record acks; G7 no dedupe / no TTL; G8 redrive of clear-down failure duplicates delivery; G9 read-modify-write races; G10 all-or-nothing drop; G11 deep-partial drops pre-canonical.

## 6. Open questions
- What were the 32 prod validation drops (which producer/recordType)? Logs not found via service:replay*.
- Are `metadata.source` / `metadata.recordType` (overwritten by fapi/sftp on failure publish, e.g. recordType "purchase_order" vs attr "goods_in_confirmation") read by connectors on replayed messages?
- Does PR #96's manual-origin skip merge/deploy before early consume? Prod backlog of ~39k rows needs a one-off dismiss (stated in PR body).
- What Pub/Sub retention/backlog exists on the unconsumed DLTs in prod (not queried; needs gcloud).
- Whether a redriven message with broadcast="true" plus stored metadata.connectorId would narrow correctly in fapi (sftp narrows by metadata.connectorId in selectTargets; fapi unverified).
