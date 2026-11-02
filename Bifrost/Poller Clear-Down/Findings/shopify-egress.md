# shopify-egress — shopify-connector confirmation egress under "consume SNAP row on find"

Date: 2026-09-29. Read-only. Investigator label: shopify-egress.

## Refs read
- shopify-connector@835c061 (origin/main, 2026-09-29). Prod deploy at time of Datadog read = version 099cf3f (Cloud Run revision shopify-connector-prod-cr-00046-6ps), differs from 835c061 only by Renovate/preview commits (44aebf9, a4d8007 are the only non-Renovate ones after 099cf3f; neither touches confirmations).
- snap-adapter@3c1578b (worktree early-consume-feasibility): poller emit attributes, claim TTL, made-side subscriptions.
- replay-service@d75997f (origin/main): redrive attributes, confirmation_data_failure subscription.
- Waypoint: Engineering/shopify-connector/{architecture,known-context,ledger}.md, plans/FUSE-1057-*.md; Monitors/2026-09-29-shopify-confirmation-delivery-failing-purdyfigg.md, Monitors/2026-09-23-shopify-fulfillment-invalid-quantity-purdyfigg.md.
- Fuse MCP lookup-topic: confirmation_ready, confirmation_made, stock_adjustment_ready/made, confirmation_data_failure.
- Datadog prod (service:shopify-connector @environment:prod), 7d/14d windows ending 2026-09-29 ~10:00Z.

## 1. Headline

The PURDYFIGG ~29h loop was closed at its ROOT CAUSE only (kit_component lines are now filtered by role, 05813b6 #194, 2026-08-10). The MECHANISM that made it silent and infinite is NOT closed:

1. `ConfirmationProcessingExceptionFilter` (`http/filters/confirmation-processing.filter.ts:17-48`) is `@Catch()` on the whole confirmation controller and ALWAYS replies HTTP 202. Any exception (Zod decode error, config fetch failure, Pub/Sub publish failure, Shopify error) is logged + `errors.*` metric and then ACKED. It never nacks and never publishes a `confirmation_data_failure`. Datadog: 4,962 of 4,962 POST /events/confirmations/sales-order responses in 7d were 202 (zero non-202).
2. `ShopifySalesOrderService.processConfirmations` (`core/shopify/use-cases/shopify-sales-order.service.ts:199-240`) runs the per-store handler under `Promise.allSettled`; a rejected store is logged (`Confirmation dispatch failed`, error) + `confirmation.forward.failure` metric and `continue`d. Returns `[]`. Controller (`confirmation-events.controller.ts:164`) `if (!fulfillments?.length) continue;` so no `confirmation_made`, no failure event.
3. `ConfirmationFailurePublisher` (the only publisher of `confirmation_data_failure` in this service) is called from exactly ONE site: `selectTargets` when a named connectorId is a Shopify connector for the business but is inactive/unmapped (`shopify-sales-order.service.ts:293`). Nothing else in the service ever publishes a confirmation-side failure.

Today's only recovery for every one of these is: row stays on the OBQ, poller's Redis claim (`REDIS_CONFIRMATION_CLAIM_TTL_MS` default 600000 = 10 min, snap-adapter@3c1578b apps/snap-queue-polling-service/src/config/config.schemas.ts:64) expires, poller re-announces. That is a SAFETY NET, and for the failing cases it is an infinite retry with no terminal state. LIVE TODAY (not historical):
- PURDYFIGG customer order 14425863324028: `ConfirmationException: Line item has no fulfillment ID` 80 times, first 2026-09-28T18:08Z, last seen 2026-09-29T09:56Z (~every 12 min), still looping. No replay record (per 2026-09-29 monitor note: replay-list-failures returned 0). Tracked as FUSE-1118 (Backlog since 2026-08-19).
- PURDYFIGG customer order 14476640387452: `Confirmation has no fulfillable line items; order left unfulfilled` 250 times, first 2026-09-27T08:48Z, last 2026-09-29T09:58Z. This is a short-shipped kit ack path. It is "acked" from the pipeline's point of view but NEVER cleared on SNAP (no made published), so it re-announces forever.
- PURDYFIGG 120 more `Confirmation dispatch failed` in 7d (80 no-fulfillment-ID + 40 "One or more fulfillment orders could not be fulfilled in Shopify") plus 40 `Shopify fulfillment creation returned errors` (userErrors, e.g. "Invalid fulfillment order line item quantity requested" per 2026-09-23 note; 17 in 30d on 3 days as of that note).

Under early consume (row marked processed at poll time) EVERY one of the above becomes a permanent, unrecorded (log-only) loss. The connector has no terminal-failure path for delivery errors today.

## 2. Ingress to the connector

- Subscription (`iac/shopify-connector/projects/bifrost-shopify-connector/pubsub.tf:315-340`): topic confirmation_ready, ack 20s, filter `attributes.recordType = "goods_out_confirmation" AND (attributes.source = "shopify" OR attributes.broadcast = "true")`, push to /events/confirmations/sales-order, OIDC, expiration never. NO retry_policy, NO dead_letter_policy (default Pub/Sub retry = immediate redelivery on non-ack). architecture.md still says filter is recordType-only; that is stale (widened by f9ffaaf #254, 2026-09-07).
- Legacy topic migration is DONE for this service: the old sales_order_confirmation_ready subscription was removed in 05813b6; legacy sales_order_confirmation_made dual-publish stopped (ledger line ~76, eefc696 #258, FUSE-1059 completed 2026-09-16 per MCP). architecture.md "dual-publish" statement is stale. Made is published once to confirmation_made with `attributes.recordType = goods_out_confirmation` (`app.module.ts:62-66`). snap-adapter made-SO subscription accepts both `sales_order` and `goods_out_confirmation` (snap-adapter iac/projects/snap-adapter/pubsub.tf:326), so this is fine. NB the Fuse MCP still says made side keeps `sales_order`; it is stale for shopify.
- Filter dependency: `source` is stamped by the poller only when the connector source resolves (`buildEmitterAttributes`, snap-adapter confirmations.service.ts), `broadcast=true` when customer.broadcastConfirmations or (no source and no connectorId). If the poller ever stops stamping, this subscription silently receives nothing (CLAUDE.md line 197 says so). Not a loss today because the row stays on OBQ; under early consume any confirmation the filter excludes is unconsumed AND already cleared.
- Envelope: `BifrostBulkMessage<GoodsOutConfirmation>` (record = ARRAY). Decoded with `BifrostBulkMessageSchema(GoodsOutConfirmationSchema)` (`pubsub.service.ts:78-103`, all-or-nothing Zod). One schema-invalid element rejects the whole array; the thrown Zod/`PubsubEventDecodeException` goes to the filter -> 202 -> whole batch dropped (log + errors.zod_validation metric only). Version skew between the poller's `@gfs-bifrost/types` and shopify-connector's (Renovate now at 10.7.0, #287) can therefore silently drop batches (types 9.0.0 made `role` required; 10.0.0 required customer reference).
- Batch processing is a sequential `for` loop inside one HTTP request (`confirmation-events.controller.ts:149-173`). Ack deadline is 20s. Per confirmation: 1 basicOrder query, 1 parent query, 1..N FO pagination queries, 1 fulfillmentCreate per FO group, each GraphQL call with 8s timeout and up to 2 retries (store.api.ts / constants.ts). A batch of ~5+ confirmations under Shopify throttling can exceed 20s; Pub/Sub then redelivers the whole batch while the first request is still running (no evidence gathered on request duration or batch size — open question). Effects: concurrent double-processing (see 4.x).

## 3. Routing / gating exit paths (service level)

`processConfirmations` (`shopify-sales-order.service.ts:131-250`):
- getByBusinessId throws (config API/remote-config failure) -> exception -> filter 202, whole remaining batch dropped. (log + errors.generic)
- No active + mapped connector (`:154-176`): log `No routable connector for business; confirmation skipped` (warn), metric `confirmation.unroutable{reason=no_connectors|no_active_connectors|no_confirmation_mappings}`, return undefined. No made, no failure. 8,269 in 7d (SISTACO 6,534; DRSAMS 455; LISAPL 337; LISAUK 314; CHAMPO 275; ACADEMIC 190; DRSAMSPL 53; BFA 52; AYMSTUDIO 44; SHACKLETON 12; WILDSMITH 3), all `no_connectors`. These are broadcast confirmations (or source=shopify attributes) for businesses with no Shopify connector; presumably another consumer (fapi/sftp) delivers them. That is correct only if another consumer exists; nothing here checks.
- `broadcast || !connectorId` -> all eligible connectors (fan-out).
- connectorId names no connector of the business (`:267-277`): debug log + metric `source_mismatch`; return undefined; NOTHING published (comment/plan says failure was later added: see f9ffaaf; the code at origin/main only publishes for the `connector_unresolvable` branch, the `source_mismatch` branch at :267-277 still just meters. The filter now makes it near-unreachable but not impossible: e.g. connector deleted after ingest). Monitor exists in observability repo per plan.
- connectorId is a Shopify connector but inactive / no salesOrderConfirmationMappings (`:283-300`): warn log + metric `connector_unresolvable` + `ConfirmationFailurePublisher.publishUnroutable` -> `confirmation_data_failure` (recordType/useCase `goods_out_confirmation`, stage `confirmation_ready`, source `shopify`, error `business_rule`/`connector_unresolvable`, `customer` attribute = businessId, record = the confirmation). This is the ONLY terminal+recorded path. Replay consumes it (replay iac/projects/replay/pubsub.tf:106-141, filter includes goods_out_confirmation, DLT after 5). If `publishFailure` throws it is caught and only logged (`confirmation.failure-publisher.ts:56-63`, event `Confirmation failure event publish failed`, error) -> then undefined -> no made -> today OBQ re-announces (retry), under early consume LOST.
- "Disabled connector = deferred, enabling releases the backlog" is real for goods-out only via the poller: the poller withholds when `confirmationsEnabled` is false; at shopify, `isActive=false` -> `connector_unresolvable` failure (if connectorId named) else `no_active_connectors` skip (if broadcast/no connectorId).
- Fan-out partial success (`:209-249`): if ANY store succeeded, `successfulResults` is non-empty -> the controller publishes made (clears the OBQ row) even though other stores failed (log only). Only relevant to broadcast/no-connectorId across >1 Shopify connectors, but is a lossy exit even today.

## 4. Handler exit paths (`core/confirmations/sales-order-confirmation.handler.ts`)

Return convention: `undefined` = "skip", `[]` = "short-ship", `throw` = failure; the service treats `undefined`, `[]` and rejection identically (no made). Only a non-empty fulfillments array publishes made.

| # | Path | Line | Today | Log level visible in prod? |
|---|------|------|-------|----|
| 1 | mapping is not a LinedMappingConfig | :73-78 | throw -> swallowed | error |
| 2 | header rule for fulfillmentOrderId missing | :317-325 | throw -> swallowed | error |
| 3 | fulfillmentOrderId unresolved/invalid (`!isValidId`) | :95-103 | warn log, return undefined | warn |
| 4 | FO not found in store OR status FULFILLED/ON_HOLD/CLOSED/CANCELLED | :106-117, :620-654 | debug log, return undefined | DEBUG - NOT shipped (log_level=info prod), invisible |
| 5 | line-item mapping rules missing id/quantity | :358-363 | throw -> swallowed | error |
| 6 | standard line with no fulfilment id (FUSE-1118) | :393-403 | throw -> swallowed; whole confirmation aborted (one bad line blocks all lines) | error |
| 7 | all lines kit_component / zero qty (short-ship) | :128-157 | warn + metric `nothing_to_fulfill` + ILG_SUBSTITUTED tag (only if outboundTagsEnabled, background), return undefined -> NO made | warn |
| 8 | lines not matchable to any FO | :176-187 | throw -> swallowed | error |
| 9 | fulfillmentCreate userErrors on any FO group | :220-251 | error log; earlier groups may already be fulfilled; throw at end -> swallowed | error |
| 10 | Shopify transport errors (throttle/5xx/timeouts/401/token lock) | store.api.ts | retried in-process (2 retries, 8s timeout, waits capped 5s) then throw -> swallowed. No permanent-vs-transient distinction at the confirmation layer | error |
| 11 | success | :253 | returns fulfillments -> controller publishes made -> tag ILG_FULFILLED (fire-and-forget) | info |

Path 4 is the worst for "recorded": it is what a confirmation hits when (a) the order was cancelled/deleted in Shopify, (b) the order is already FULFILLED because a previous attempt succeeded but made was never published (publish threw, instance crashed, timeout after Shopify accepted), (c) the FO is ON_HOLD. All are silent (debug) and never clear the row today (re-announce every ~12 min forever); under early consume they are unrecorded. Note path 4 (b) means the current design is NOT self-healing after a lost made: the retry sees FULFILLED and skips instead of re-emitting made, so the row is never cleared. In a broadcast fan-out path 4 is also the intentional "not on this store" no-op, so it cannot simply be turned into a failure without distinguishing cases.

Duplicate / non-idempotent Shopify writes: `fulfillmentCreate` has no idempotency key. `executeGraphqlRequest` retries mutations on AbortError (the 8s client timeout), FETCH FAILED, ETIMEDOUT, ECONNRESET, 5xx (`store.api.ts:216-258`, `network.utils.ts`). A timeout where Shopify did apply the mutation is retried and hits userErrors or duplicates. Partial multi-FO application: groups are fulfilled one by one, a later group failing throws after earlier groups were created (no compensation; rerun then sees a mix).

No per-shop circuit breaker exists at origin/main (grep for circuit/cockatiel/@gfs-bifrost/resilience in shopify-connector src = only Redis circuit breaker config). Rate limiting = throttle-aware retry only (2 retries). No cross-request throttle budget.

## 5. Controller exit paths (`confirmation-events.controller.ts`)

- `publishEntity(SALES_ORDER_CONFIRMATION_MADE ...)` (:167-171) is awaited, single publish to confirmation_made. If it throws: filter -> 202, tagging skipped, fulfillment already created in Shopify, made lost. Retry then hits path 4(b) silently. (Today this leaves a permanently un-cleared row.)
- The loop is not per-item guarded: an exception on confirmation k drops k+1..n for that delivery (acked).
- `tagOrdersFulfilled` uses `applyTagInBackground` (fire-and-forget, cosmetic, `outboundTagsEnabled`-gated). Background work after the 202 is sent on Cloud Run request-based CPU may be throttled; cosmetic only.
- Unhandled exceptions all end in the filter: `ErrorEvent.UnhandledError` log with `audience: support` + `errors.generic|zod_validation|unknown` metric. Not a durable operator record; not queryable per-record except by log search. Monitor 303425509 (`forward.failure + order.tags.update.failure > 5 / 15m`) is the only alert; it flaps at ~1-2 (below crit 5) on the looping PURDYFIGG orders and the metric has no businessId tag (per 2026-09-23 triage).

## 6. Stock adjustments (`/events/confirmations/stock-adjustment`)

Subscription `stock_adjustment_ready`: ack 600s, no filter, no retry policy, no DLT (`pubsub.tf:343-366`). Topic is `BifrostBulkMessage<CanonicalStockAdjustment>` (array). Same class of exceptions: controller has the same filter -> 202. Made = `STOCK_ADJUSTMENT_MADE` (to its own topic `stock_adjustment_made`, snap-adapter clears; collector persists), published only `if (results?.length)`.

| Path | Today | Notes |
|------|-------|-------|
| no connectors / none active | warn log + `confirmation.unroutable{no_connectors|no_active_connectors}`; undefined; no made | 1,479 in 7d (`Stock adjustment could not be routed to an active connector`). Other consumers (sftp) publish made for their businesses. |
| stockAdjustmentsEnabled false on all active connectors (`use_case_inactive`) | info log + metric, undefined, no made. INTENTIONAL: ledger says "SNAP row not cleared" — the row is deferred until the flag is turned on ("enabling releases the backlog") | early consume destroys this feature: adjustments while off are gone forever |
| SKU missing / quantity missing / variant not found / not stocked at an active location / invalid response / userErrors | handler returns undefined (logged error/warn; NOT thrown so not even counted as rejected) -> no made | row re-announced today; under early consume permanent inventory drift |
| Shopify error thrown | rejected in allSettled -> `Stock adjustment dispatch failed` log; no made | same |
| NON-IDEMPOTENT: `inventoryAdjustQuantities` delta (increase/decrease) with `referenceDocumentUri` only as metadata; no dedupe by reference | success path publishes made; if made publish fails or the request is redelivered after 600s ack / retried mutation on timeout, the delta is applied twice | risk exists today; early consume actually REDUCES re-application risk from OBQ re-announce but not from Pub/Sub redelivery or in-process mutation retry |
| partial multi-store success | made published if any store succeeded | others lost |
| SET type | idempotent (`ignoreCompareQuantity: true`) | fine |

No confirmation_data_failure path exists for stock adjustments at all (stock adjustments have no confirmation-side failure topic in Fuse per MCP; `confirmation_data_failure` recordType values list has no stock_adjustment).

## 7. What else the service does (not egress-terminal but sales-order-related)
- `create_acknowledge` (filtered sales_order, retry 30s, DLT after 5) -> tag ILG_RECEIVED; `create_data_failure` (filtered sales_order, no DLT) -> tag ILG_ERRORED. Tag-only; cosmetic.
- shopify-egress-service (apps/shopify-egress-service, FUSE-1196, 9936111) is scaffold only: health controller, AllExceptionsFilter, no Pub/Sub subscription and no business logic; FUSE-1197/1198 own the move. Relevant: egress is planned to move to a new service, so any terminal-outcome fix should target the new service's handler design rather than patching the swallowing filter here.

## 8. Replay / failure-record actionability
- Replay redrive for goods_out_confirmation publishes to confirmation_ready with attributes `{ recordType }` ONLY (`replay-service failure.service.ts:748-759 confirmationTarget`, `failures.controller.ts:653-664`). shopify-connector's subscription requires `source = "shopify" OR broadcast = "true"`. A redriven Shopify goods_out confirmation therefore does NOT match the Shopify subscription and would never be delivered to shopify-connector (it would reach any other consumer with a recordType-only filter, e.g. collector/fapi/sftp, which for a Shopify order are the wrong channel). So the only recorded failure shopify produces (connector_unresolvable) is not actually replayable back to Shopify today unless replay copies source/broadcast/connectorId. (Unverified end-to-end: I did not run a redrive. Evidence is from source on both sides.)
- Replay's made-clear subscription (clears failures resolved by a successful made) is filtered to pick/pack only (replay iac pubsub.tf:~150, comment "Filtered to pick/pack"), so a shopify failure record is never auto-cleared after success. (Not verified whether a manual path exists.)
- replay derives businessId for goods_out from `record.identifiers.businessId` (failure.service.ts:665-684) while goods-out confirmations are keyed `identifiers.bizId` in shopify's code (`confirmation.identifiers.bizId`); pkg-node changelog says goods-in/out carry both. If businessId is absent the failure has empty businessId. Not verified with a live record.

## 9. Exit-path / terminal outcome table (summary)

See structured output. Terminal+recorded today: (a) success -> confirmation_made (collector persists, snap-adapter clears); (b) connector_unresolvable -> confirmation_data_failure (replay+DLT). Everything else is either silent skip, logged-only swallow, or infinite re-announce.

## 10. Datadog evidence (prod, service:shopify-connector)
- 7d messages: `Confirmation processed` 13,231; `Confirmation dispatched successfully` 13,225; `No routable connector...` 8,269; `Order has more than one fulfillment order - only the first is mapped by the template` 5,728 (from ingest side); `Confirmation has no fulfillable line items` 250 (one order); `Confirmation dispatch failed` 121; `Shopify fulfillment creation returned errors` 40.
- `Confirmation dispatch failed` by error (7d): all PURDYFIGG: 80 "Line item has no fulfillment ID", 40 "One or more fulfillment orders could not be fulfilled in Shopify", 1 "Shopify GraphQL Query Failure".
- 14d distinct failing orders: order 14425863324028 looping (80x), ~19 other orders each failed once on 09-17, 09-23, 09-24, 09-25, 09-28 (one-shot: consistent with either a successful later retry OR with the retry then hitting path 4(b) silently; not determined).
- HTTP: 4,962/4,962 confirmation POSTs returned 202 in 7d.

## 11. Gaps (concrete)
See structured output gaps list. Key ones:
1. Blanket-202 filter: no nack, no DLT, no failure event for any exception. (major/blocker)
2. Promise.allSettled swallow persists; only the kit-component root cause was fixed. FUSE-1118 still open; live loop. (blocker)
3. Silent "skip" returns (invalid FO id, FO not found/cancelled/fulfilled/on-hold [debug], short-ship) publish neither made nor failure. (blocker)
4. Lost made after successful fulfilment is unrecoverable (retry sees FULFILLED and skips). (major)
5. Mutation retry / Pub/Sub redelivery duplicates; no idempotency key; ack 20s vs sequential batch. (major)
6. Batch-level poison: all-or-nothing Zod, sequential loop without per-item isolation. (major)
7. Unroutable failure publish failure is log-only. (major)
8. source_mismatch branch publishes nothing. (minor)
9. Fan-out partial success clears the row. (minor)
10. Stock adjustment: undefined/handler-swallowed errors, deferred-while-disabled feature, non-idempotent delta, no failure topic. (major)
11. Filter dependency on poller stamping source/broadcast; replay redrive strips them. (major)
12. Monitor is a sum>5/15m on a metric with no businessId tag and flaps on one looping order; would not detect a burst of lost confirmations under early consume unless volume >5. (minor)
13. No per-shop circuit breaker / throttle budget; 8s timeout + retry of mutations. (minor)
14. Token/auth failures (revoked/uninstalled app, token lock contention) throw and are swallowed per shop forever. (major)

## 12. Open questions
- Request duration and batch size distribution for POST /events/confirmations/sales-order vs the 20s ack deadline (no duration in the request log; not measured). Are there Pub/Sub redeliveries today (same correlationId processed twice)?
- For the one-shot failed PURDYFIGG orders, were the SNAP OBQ rows eventually cleared? (needs SNAP OBQ read via get-snap-connection; not done to keep scope read-only-light.)
- Does any consumer other than shopify-connector handle no_connectors businesses (SISTACO etc.) for goods_out with broadcast? Presumed fapi/sftp; not verified here.
- Are stock adjustments for Shopify businesses with stockAdjustmentsEnabled=false intended to be re-released on enabling in practice (ledger says so)? Confirm with owner.
- Do Shopify orders exist in "order-level FO id maps to a different FO than the confirmation FO" states where status check on the mapped FO gives a false skip (path 4) while other FOs remain unfulfilled? Not tested.
- Does replay copy `failure.metadata` (incl. connectorId, source) into the redrive envelope? It passes failure.metadata as envelope metadata, but Pub/Sub ATTRIBUTES (source/broadcast) are what the shopify filter reads; confirm end-to-end with a dev redrive.
