# fapi-egress: fapi (REST connector) confirmation egress, early-consume feasibility

Read 2026-09-29. Refs: fapi@f4bd648 (origin/master; prod runs a76ccbc = same code for this area, confirmed by Datadog `version` tag, Cloud Run rev api-gateway-prod-00036-mqp), pkg-node@4d62ab9 (origin/main; pubsub 0.5.0, remote-config 2.2.0, types 10.8.0), bifrost-pubsub@cd25f95, replay-service@d75997f (light touch only). Live prod Pub/Sub config read with read-only `gcloud pubsub subscriptions list/describe` (project bifrost-prod-global1). Datadog: service `rest_connector`, `@environment:prod`.

## 1. Topology (verified)

- Ingress: 8 push subscriptions in prod, all on `bifrost.prod.confirmation_ready.v1` except stock_adjustment (own topic `stock_adjustment_ready`). Endpoint `POST /events/v1/confirmation/ready/:recordType` (controller `code/src/http/controllers/confirmation.controller.ts`). Types = `CONFIRMATION_RECORD_REGISTRY` (`pkg/types/src/confirmations/confirmation-registry.ts`): purchase_order, sales_order, stock_adjustment, return_goods_authorization, pick_confirmation, pack_confirmation, work_order_confirmation, finished_good_receipt. fapi has a sub + route for all 8 (iac/projects/api-gateway/pubsub.tf) so none are unhandled.
- Subscription filters (live == tf): PO `(recordType=purchase_order OR goods_in_confirmation) AND (source="rest" OR broadcast="true")`; SO/pick/pack/WOC/FGR same shape; **RGA: recordType only (no source/broadcast clause)**; **stock_adjustment: no filter at all** (own topic).
- Live sub properties (all 8 fapi subs): ackDeadline 60s, `messageRetentionDuration` 604800s (7d), **no deadLetterPolicy, no retryPolicy (default = immediate redelivery, no backoff)**, expiry never. Topic module creates a `.dlt` topic per topic (bifrost-pubsub `iac/modules/topic/main.tf`) but no fapi sub references it, and the DLT topics have no subscriptions of their own in that module. Only replay's subs have a DLQ (max 5 attempts, 30s min backoff -> `replay.prod.*.dlt`). collector subs on these topics: no DLQ, 10s min backoff on some.
- Envelope in: `BifrostBulkMessage<record>` (bulk), decoded with `PubSubIngestor.ingestBulkEvent(body, getConfirmationSchema(type))` (controller:187). Attributes read: only `broadcast` (controller:126-127); `source` is used only by the subscription filter.
- Envelope out, made: one **single-record** `BifrostMessage` per record, metadata `{...in, source:"rest", recordType, recordId?(stock_adjustment only)}`, attrs `{recordType}` (goods_in_confirmation/goods_out_confirmation for PO/SO; none for stock_adjustment, which goes to `stock_adjustment_made`). `pubsub-emitter.ts:180-240`.
- Envelope out, failure: `BifrostMessage<BifrostFailure>`, `record = {useCase: getConfirmationFailureUseCase(type), stage:"confirmation_made", source:"rest", connectorId, transaction, errors:[...], record:{confirmations:[...]}}`, metadata `{...in, source:"rest", recordType:useCase}` (so `metadata.customer` = businessId is preserved), attrs `{recordType, stage, source:"rest", customer}`. `pubsub-emitter.ts:263-303`, `confirmation.service.ts:416-461`. `transaction` = `new Date().toISOString()` per push (controller:109), so every Pub/Sub redelivery gets a new delivery key.
- Failure-topic consumers by recordType (live): goods_in/out_confirmation -> replay + collector; work_order_confirmation, finished_good_receipt -> replay + collector (collector excludes source=snap-adapter); **pick/pack -> replay only; return_goods_confirmation (RGA) -> replay only; stock_adjustment -> collector only** (no replay sub). So a fapi failure for those types is "recorded" only in one system.

## 2. Handler flow (confirmation.controller.ts / confirmation.service.ts)

1. `isConfirmationType(type)` else 400 (l.112). Unreachable from the 8 fixed subs.
2. `parseEnvelope` (l.126), `ingestBulkEvent` (l.187): PubSubValidationError / PubSubDecodeError.
3. `extractBusinessId` from **record[0] only** (service l.585-601); throws BusinessIdExtractionException if array empty or RGA has no `identifiers.businessId`.
4. `routeConfirmations` (service l.69-143): `connectorRegistry.getByBusinessId` -> remote-config `resolve(businessId, REST)` (cache then API) -> filters: `isActive===ACTIVE` -> `receivesType` (stock_adjustment needs `stockAdjustmentsEnabled===true`) -> has `webhookUrl` -> `isDeliverable` (valid URI + secret key; logs+metrics `errors.connector_configuration`, drops connector) -> `candidateConnectors`.
   - candidates==0: `reportNoCandidateConnectors` = metric `fuse.confirmation.unroutable{type,businessId,reason}` + warn log `Confirmation could not be routed`; **no failure published, returns false** (l.102-110). Reasons: no_connectors / no_active_connectors / use_case_inactive (stock adj disabled) / no_confirmation_mappings / misconfigured.
   - `selectTargets` (l.156-168): broadcast or no `metadata.connectorId` -> all candidates; else the candidate with that connectorId. If candidates>0 but none match the named id: metric+log `connector_unresolvable` **and** publishes a `business_rule` failure (l.118-127, 376-414).
   - Deliver sequentially per target (l.130-140). Per target: up to `maxRetries`=3 (hard-coded, connector-registry.service.ts:325) POSTs of the raw confirmation array to `webhookUrl`, headers `x-webhook-secret-key` + `x-correlation-id` (NOT HMAC; a static shared secret header, no signature, no idempotency key), axios timeout 30s (axios-instance.factory.ts:10), backoff 1s, 2s (no wait after final). Any non-2xx / network error counts as a failed attempt (no distinction of 4xx vs 5xx; 4xx is retried too).
   - Success: `tryEmitConfirmationMade` **per successful connector** (l.216) after delivery only; errors swallowed (l.340-347 log only `MadeEmitFailed`).
   - Exhausted: `tryEmitConfirmationFailure` (dependency error `fapi.confirmation_webhook_delivery_failed`, `retryable:false`) errors swallowed (l.453-460 log only `FailureEmitFailed`).
5. Controller returns 204 unless an exception escapes (l.161-181). `DeliveryUnsuccessful` (warn log) also fires for unroutable (misleading).

## 3. HTTP status returned to Pub/Sub per error class (all-exceptions.filter.ts)

| Error | Status | Pub/Sub effect |
|---|---|---|
| PubSubValidationError (bad envelope/structure/**any single record failing canonical Zod**), PubSubDecodeError | 204 (l.231-239) | ack, dropped |
| BusinessIdExtractionException | 204 | ack, dropped |
| ConfigApiException (config-service request failed or response failed validation) | 204 (l.240-244, comment says "not retryable via redelivery", which is not true of a transient failure) | ack, dropped |
| ConnectorConfigurationException | 204 (never thrown; config problems handled in `isDeliverable`) | n/a |
| ZodError | 204 | ack |
| HttpException (400 bad type, 401 missing Bearer) | 4xx | nack -> immediate redelivery, 7d |
| PubSubConfigurationException | 500 | nack |
| any other Error / non-Error | 500 (l.278-286) | nack -> hot redelivery, no backoff, no DLQ, 7d then silently expired |
| uncaughtException / unhandledRejection | `process.exit(1)` (main.ts:33-40); no `enableShutdownHooks` found | in-flight requests (Cloud Run concurrency default) abort, all non-2xx -> redelivery |

## 4. Exit-path / terminal-outcome table

(see structured output for the same rows; extra notes here)

| # | Path | Today | Recorded where | Terminal | Silent | OBQ-net dependent |
|---|---|---|---|---|---|---|
| 1 | Webhook 2xx, made published | made per delivered connector; snap-adapter clears row | made event -> collector/snap-adapter | yes | no | n/a (this is the success path) |
| 2 | Webhook exhausts 3 attempts, failure published | ack 204; failure -> confirmation_data_failure | replay/collector (type-dependent) | yes (no auto retry by fapi) | no | no, but row still stays on OBQ until someone clears; snap-adapter clears only on made |
| 3 | Webhook exhausted AND failure publish throws | ack 204; log `Confirmation failure event could not be emitted` only | log only, no metric found | no durable record | **yes** | **yes** (row stays -> re-announced -> retried) |
| 4 | Webhook 2xx AND made publish throws (or fails partway through the per-record loop) | ack 204; log `Confirmation made event could not be emitted` only; webhook delivered | log only | delivered but unacknowledged | **yes** | **yes**: row never cleared -> re-announced -> duplicate webhook delivery. Under early consume it is harmless to delivery but collector's delivered-status (made-driven) never updates |
| 5 | 0 candidate connectors (no_connectors / no_active_connectors / no_confirmation_mappings / misconfigured / use_case_inactive) | ack 204; metric + warn log; NO failure record; no made | metric+log only | yes for fapi (drops) | **yes** | **yes**: disabled connector is "deferred": the row stays on OBQ and is re-announced (evidence below) |
| 6 | Named connectorId not among candidates but other candidates exist | ack; failure business_rule published | replay/collector | yes | no | no |
| 7 | Named connectorId and ZERO candidates (e.g. the named connector was disabled/deleted and it was the only REST connector) | falls into path 5: metric+log only, no failure | metric+log | drops | **yes** | **yes** |
| 8 | Multi-connector broadcast, partial success | per-connector isolation: success -> made (one per success, so N made for N successes), failure -> failure record. Both can be emitted for the same records | made + failure | yes (each) | no | n/a |
| 9 | Inbound envelope invalid / any single record fails canonical Zod in a bulk | ack 204; whole bulk dropped (`ingestBulkEvent` throws on first bad record, l.65-72 of pkg-node ingest.ts); log `payload` + metric `errors.pubsub_decode` | log (contains payload) + metric | drops | **yes** (log-only) | **yes** |
| 10 | Empty record array / RGA missing `identifiers.businessId` | 204 ack, log+metric `errors.generic` | log/metric | drops | **yes** | **yes** |
| 11 | Config API unavailable/failed during `resolve` (getAllConnectors on cache miss) | ConfigApiException -> 204 ack; log `Config API error`+ `fuse.errors.config_api` | log/metric | drops | **yes** | **yes** |
| 12 | Config API partially failing: `fetchAndCacheConnectors` uses allSettled, failed `getConnector` calls become null and are filtered | resolve returns fewer (possibly zero) connectors with no throw -> path 5 (`no_connectors`) or wrong target set | metric+log | drops | **yes** | **yes** |
| 13 | Negative cache marker: an empty result is cached type-scoped for the cache TTL | a business that gains a REST connector is treated as connector-less until marker expires or connector creation populates the positive index (self-heals per remote-config 2.2.0 notes) | metric+log | drops | yes | yes |
| 14 | Unexpected exception (generic Error) | 500 -> nack -> immediate redelivery loop, no backoff, no DLQ, 7d retention then Pub/Sub deletes silently | none beyond error log | not terminal (until 7d, then silent loss) | after 7d yes | n/a: fapi's own sub is the queue here |
| 15 | Crash / SIGTERM / scale-down mid-handling | connection drop -> redelivery. Webhook may already have been delivered -> duplicate | none | not terminal | duplicates undetected (no idempotency key) | n/a |
| 16 | Handler slower than ack deadline (60s): 3x30s timeouts + 3s backoff = ~93s per failing connector, sequential across targets | Pub/Sub treats as failed -> redelivers while first invocation continues: duplicate webhooks, duplicate made/failure events; `transaction` differs each time so replay sees separate delivery keys | none | not deduped | yes | n/a |

## 5. Evidence from prod (Datadog, `service:rest_connector @environment:prod`)

- 14d: `Confirmation push accepted` 5,949; `Confirmation processed` (real delivery to a webhook) only 15. Almost all traffic is unroutable broadcast.
- 7d, `Confirmation could not be routed` by (reason,type): no_connectors/sales_order 1,307 (11 businesses); use_case_inactive/stock_adjustment 666 (1 business, PURDYFIGG); no_connectors/stock_adjustment 415 (7 businesses); no_connectors/purchase_order 8 (2). 7d `push accepted` shows `broadcast=true` for all sales_order (1,307) and stock_adjustment (1,081) and 11 of 20 purchase_order; **every unroutable log correlated was broadcast=true**, non-broadcast (source=rest) PO pushes produced no unroutable line.
- 1,307 broadcast SO pushes for 11 businesses in 7 days with 0 REST connectors is the OBQ re-announce loop at work (rows never cleared because no consumer delivers/makes). PURDYFIGG stock_adjustment `use_case_inactive` 666/7d = same loop. Under early consume each would be announced once and then gone.
- Zero `Confirmation forward attempts exhausted`, zero failure-emitted, zero validation/decode drops, and zero confirmation-path `Config API error` in 14-30d. The two `Config API error` lines (2026-09-28 11:02/11:04) are from the config-revision consumer (`flow: config`, 404 on `/connectors/<id>`), not the confirmation path. So the lossy paths are code-evidenced and currently rare, not observed to have fired.
- Config API axios client has `timeout: 0` (log line config dump), i.e. a hung config-service call is unbounded until Cloud Run's request timeout.

## 6. Answers to the brief

- Does made publish only after delivery? Yes: `deliverConfirmation` only reaches `tryEmitConfirmationMade` when `forwardToConnector` returns undefined. But it publishes once per successful *connector* (duplicate made for multi-connector broadcast) and swallows publish errors.
- Success/error terminal? Success and exhaustion-failure are terminal and recorded (subject to the swallow paths 3/4). Unroutable, decode, businessId, config API outcomes are dropped with log/metric only.
- DLQ: none on fapi subs. Non-acked messages redeliver immediately for 7 days then vanish without a DLT record.
- Under early consume: fapi's own sub redelivery becomes the only retry for a transient fapi failure, and fapi acks (204) every class of failure that it considers non-retryable, including transient config-service failures. Paths 3, 5, 7, 9, 10, 11, 12 would each become permanent silent loss (log/metric only).

## 7. Open questions

- Does the poller re-announce with new `correlationId`/`queueId` such that fapi's per-push `transaction` and failure records dedupe anywhere? (poller reviewers)
- Does collector's own `confirmation_ready` subscription persist every announced confirmation (a possible durable "seen" record that early consume could lean on)? Not read here.
- replay-service redrive attributes vs fapi sub filters (memory note says redrive stamps only `{recordType}`, which would not match fapi's `source="rest" OR broadcast="true"` filter except for RGA). Not verified here; matters for whether a fapi failure in replay is actually actionable.
- Is `stock_adjustment` failure with no replay sub intended (collector-only)?
- Is the Pub/Sub ack-deadline redelivery (path 16) actually observed? Not verified in logs; based on push semantics and code timings.
- Cloud Run request timeout/concurrency not set in tf (defaults assumed: 300s, 80).
