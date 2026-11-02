# snap-adapter confirmation_made clear-down — feasibility input (label: snap-adapter-cleardown)

Date read: 2026-09-29. Read-only. No secrets reproduced (a SNAP credential was fetched via the Fuse MCP solely to issue two read-only GETs; it is not recorded here).

## Refs read (exact shas)
- snap-adapter@3c1578b (origin/master; worktree `.claude/worktrees/early-consume-feasibility`), apps/snap-adapter + apps/snap-queue-polling-service (poller, for comparison only) + iac/projects/snap-adapter
- collector@f19ce57 (origin/master), replay-service@d75997f (origin/main), fapi@f4bd648, sftp-connector@f6a15e3, shopify-connector@835c061 (origin/main), bifrost-pubsub@cd25f95, pkg-node@4d62ab9, observability@81d508f
- Prod snap-adapter revision observed in Datadog logs: `1135a8334e` (2026-09-24). master is 3+ commits ahead (incl. c610247 FUSE-1238 log-leak fix). None of the commits between touch event.controller / confirmations / pubsub adapters / snap-adapter iac (git log 1135a83..origin/master on those paths: only c610247).
- Waypoint: Engineering/snap-adapter architecture.md, known-context.md, plans/FUSE-1059. Fuse MCP lookup-topic (confirmation_made, confirmation_data_failure). Datadog prod logs+metrics. replay-service prod failure inbox (read-only). SNAP prod OBQ rows (read-only GET).

## 1. What clear-down does (source)
- Route: `POST /events/v1/confirmation/made/:recordType` (event.controller.ts:106-113 -> `handleConfirmationMade`, :162-239).
- **First statement is `res.sendStatus(202)` (event.controller.ts:163)**, before decoding or any SNAP call. Pub/Sub therefore always sees success: there is NO nack/503/redelivery path on this route (contrast the create route, which returns 503 for transient SNAP failure, :329-331).
- Decode: `pubsubIngestor.ingestEvent(req.body, z.record(...))` (:167). On throw: `ErrorEvent.MessageDecodeFailed` log with full payload, `return` (:171-177). No metric, no failure publish.
- recordType used for logging/failure mapping comes from the URL path param (static per subscription), not the message attribute.
- Clearable check: `ClearableRecordSchema` = `identifiers.queueId: string` (empty string passes) + (`identifiers.bizId` or `identifiers.businessId`) (models/confirmations/schemas/clearable-record.schema.ts). `businessId` falls back to `""` (:195-196).
- Clear call: `ConfirmationsService.clearFromOutboundQueue(businessId, queueId)` = `customerHttpRouter.forCustomer(businessId)` then **`PATCH /v2/snapoutbound/{queueId}/processed`**, no body (adapters/confirmations/confirmations.service.ts:18-24). Keyed by queueId (= SNAP OBQ `XDoc`, e.g. `SPLU031080`) and business (for credentials/host). Verb PATCH, no idempotency key.
- The poller has its own identical call (`apps/snap-queue-polling-service/src/adapters/snap/api.client.ts:153-156`) already used to *drop* rows early: `ConfirmationDisposer.clearFromOutboundQueue` for cancelled shipments (goods-out) and zero-quantity receipts (goods-in); failure there is log-only (`confirmation.disposer.ts:7-24`) and the row stays for the next poll. So there is precedent for poller-side marking, with a swallowed-failure semantics.
- SNAP OpenAPI (snap-api.openapi.yaml ~11567-11601): `PATCH /api/v2/snapOutbound/{id}/processed` documents 200/400/404 only; behaviour when the row is already processed is NOT documented and there is no test in snap-adapter for it (grep of event.controller.spec: only clearable/not-clearable/irrecoverable cases).
- Success path: `ConfirmationEvent.Processed` log + `snap.confirmation_handled` metric (snap.recorder.ts:124-131). Failure: `ConfirmationEgressEvent.ClearFailed` ("Confirmation clear-down failed") log + `snap.confirmation_handled.failure` metric + `emitConfirmationFailure`.

## 2. HTTP client resilience for the PATCH (customer.http-router.ts)
- Per-host: token bucket (10 rps / burst 20), semaphore (5 concurrent, 30s slot timeout), circuit breaker (5 consecutive 5xx/network failures -> open, half-open after 30s), request timeout 120s, `SNAP_RETRY_MAX_ATTEMPTS=1` in-process retry (iac env passes var default 1).
- Retry interceptor (retry.interceptor.ts:40-59): a response-bearing 5xx/429 is retried; a **no-response failure (timeout/reset) is retried only for GET/HEAD/OPTIONS/PUT/DELETE — PATCH is excluded**, so `socket hang up` on the clear-down PATCH is not retried at all. Any other 4xx is permanent.
- `responseFailureMetricInterceptor` wraps POST/PUT/PATCH failures in `EntityCreationException` (axios-metrics.ts:96-113); `classifySnapFailure` unwraps it.
- Classification (classify-snap-failure.ts): 5xx/429/no-response = transient, except "structural" SNAP messages; 4xx = permanent `snap_api_error`; circuit open / slot timeout = transient (`circuit_open` / `slot_timeout`); missing creds = `missing_credentials`.

## 3. What is published on failure, and where it lands
- `ConfirmationErrorService.publish` -> `router.publishToTopic(CONFIRMATION_DATA_FAILURE_TOPIC, failure, {...metadata, recordType, recordId}, attributes{recordType: failure.useCase, stage:"confirmation_made", source:"snap-adapter", customer})` (adapters/pubsub/confirmation-error.service.ts:22-71). One attempt (Pub/Sub client's own retries); on throw: `logger.warn` and return false.
- useCase: `CONFIRMATION_FAILURE_USE_CASE_MAP` (event.controller.ts:66-79): purchase_order->goods_in_confirmation, sales_order->goods_out_confirmation, return_goods_authorization->return_goods_confirmation; everything else passes through (pick/pack/WOC/FGR/stock_adjustment).
- Error shape (to-confirmation-failure.ts:92-125): `missing_credentials` -> dependency/snap-credentials retryable:false; `snap_api_error` -> dependency/snap `snap-adapter.<useCase>.obq_clear_down_failed` retryable = transient; **any other mode (circuit_open, slot_timeout, unexpected) -> infrastructure retryable:false**.
- If the failure publish returns false: `confirmationLogger.error(...)` + `messagesFailed` metric only (:253-261). Already acked. Dropped.
- Consumers of confirmation_data_failure (IaC):
  - replay-service: two subs, filter pick/pack/WOC/FGR and goods_in/goods_out/return_goods_confirmation, **no source filter**, retry_policy 30s, dead_letter_policy max 5 -> `replay.<env>.confirmation_data_failure.v1.dlt` (replay pubsub.tf:70-150). Handler stores each as a redrivable failure; validation/decode errors are ack-and-dropped (metric `FAILURE_DROPPED` + log) (replay event.controller.ts ~214-290).
  - collector: filters carry `AND NOT attributes.source = "snap-adapter"` for every type ("OBQ clear-down failures come after delivery, so they must not mark any confirmation failed") (collector pubsub.tf:26-33).
  - **stock_adjustment**: replay filter does not include it; collector's stock_adjustment filter excludes snap-adapter. => a snap-adapter stock_adjustment clear-down failure has NO consumer.
- Replay redrive: `getReplayTarget` maps every confirmation useCase to `confirmation_ready` (failure.service.ts ~692-760) with no awareness of `source`/`stage`. A snap-adapter clear-down failure is `replayable: true`; replaying it re-publishes the whole already-delivered canonical to `confirmation_ready` (=> re-delivery to the customer connector).

## 4. Subscription config (iac/projects/snap-adapter/pubsub.tf)
- 8 clear-down subscriptions, all push to `/events/v1/confirmation/made/<type>`, ack_deadline 300s (`snap_event_ack_deadline_seconds`), `expiration_policy.ttl=""`:
  - cross-entity `confirmation_made` topic: rga (`return_goods_authorization`), po (`purchase_order` OR `goods_in_confirmation`), so (`sales_order` OR `goods_out_confirmation`), pick, pack, fgr (`finished_good_receipt`), woc (`work_order_confirmation`).
  - legacy `stock_adjustment_made` topic (unfiltered) -> `/confirmation/made/stock_adjustment`.
- retry_policy 10s-600s on all EXCEPT the WOC subscription (pubsub.tf:442-465 has none => default immediate redelivery on non-2xx).
- **No `dead_letter_policy` on any confirmation_made subscription** (only the 5 create_record subs have one, pointing at `create_record_topic_dlt_id`, which known-context.md says has no consumer). The `confirmation_made` topic module creates a `.dlt` topic (bifrost-pubsub modules/topic/main.tf) that nothing uses for these subs. `ack_event_delivery_attempts=10` and `MAX_TRANSIENT_DELIVERY_ATTEMPTS` (event.controller.ts:83) apply to create only.
- Because the handler always answers 202, retry_policy only matters when the *platform* returns non-2xx (Cloud Run 429/503: max_instance_count=3 x concurrency 30 = 90 in flight; cold-start failure; instance crash). Then Pub/Sub retries with backoff for the default 7-day subscription retention and then drops silently (no DLT).
- Cloud Run (cloud-run.tf): no `resources`/`cpu_idle`/startup-boost settings on the main container (=> API default request-based CPU allocation, i.e. CPU throttled when no request in flight); no SIGTERM/graceful-shutdown handling in src/index.ts (only `uncaughtException`/`unhandledRejection` recorders). Because the 202 is sent first, Cloud Run considers the request finished while the PATCH (up to 120s x2) is still running. Confidence medium-low on the CPU behaviour (IaC-inferred); empirically 16k/week succeed so it mostly works while other requests keep the instance warm.
- Express 4.22: `handleConfirmationMade` is an `async` handler with no outer try/catch after the 202; any throw outside the inner try (e.g. from a logger/metric call) becomes an unhandled rejection, recorded only.

## 5. Who else consumes confirmation_made
(Subs are independent copies of the topic; removing snap-adapter's subs does not affect the others.)
- **collector** (pubsub.tf:652-680): subs for work_order_confirmation, finished_good_receipt, purchase_order|goods_in_confirmation, sales_order|goods_out_confirmation (+ legacy stock_adjustment_made). Handler upserts and sets `lifecycle.status = processed` ("the connector's success ack, so it means the customer got this"). No collector made-sub for pick/pack/RGA. NOTE: Fuse MCP lookup-topic says collector "subscribes to every type" — IaC does not; doc drift.
- **replay-service** (pubsub.tf:155-190): pick|pack only; clears matching failures (useCase+businessId+shipmentId) in its failures collection (has DLT).
- **Datadog/observability**: dashboards use `gcp.pubsub.topic.send_message_operation_count{topic_id:*confirmation_made.v1}` as "true delivery" (data_egress.json, product_scorecard.json); monitor "Confirmation delivery lagging" watches `oldest_unacked_message_age{subscription_id:*confirmation*}` > 300s (includes snap_adapter made subs). **No monitor exists on `snap.confirmation_handled.failure`** (monitors.snap-adapter.tf lists only create-path, polling-mapping and latency monitors).
- No billing/tracking/orient consumer found (grep of fuse-billing, fuse-devtools, config-service, dedupe, fuse-ui: only a generated client typedef).
- Publishers: fapi, sftp-connector, shopify-connector. fapi emits one made per delivered record after ANY connector's delivery success (confirmation.service.ts deliverConfirmation -> tryEmitConfirmationMade; failure to emit is `MadeEmitFailed` log only, :318-355), so broadcast to N connectors can produce N made messages for the same queueId => N PATCHes. sftp-connector documents the safety-net dependency explicitly: "Publishes no failure: Snap holds the outbound-queue entry until a confirmation_made, so the record redelivers once the config is fixed — a failure would double-write" (confirmation-egress.service.ts:810-812).
- confirmation_made is the **"delivered successfully" signal** for: collector lifecycle=processed; replay failure clear-down (pick/pack); dashboards' ready-vs-made funnel; snap-adapter OBQ clear. It is NOT tied to anything else.

## 6. Live evidence (prod, 2026-09-29)
- Volume: `snap.confirmation_handled` (snap-adapter, prod) 16,418 / 16,847 / 16,233 / 9,152 per week (last is partial); `snap.confirmation_handled.failure` 18 / 5 / 0 / 1 per week (24 in ~4 weeks, ~0.04%). Only one "Confirmation clear-down failed" log survives in the 30d search (2026-09-25); "Confirmation not clearable": 0. Older failure logs are outside log retention, so failure *reasons* for the other 23 are unknown.
- Replay prod inbox holds two snap-adapter clear-down failures (search "socket"): goods_out_confirmation PURDYFIGG #6369469 (2026-09-16) and #6423783 (2026-09-25), both reason `socket hang up`, `retryable:true`, `replayable:true`, `attempts:0` (never actioned).
- **Outcome ambiguity proven**: for #6423783 (queueId SPLU031080) the PATCH failed with `ECONNRESET socket hang up` on a reused keep-alive socket at 14:36:26Z, yet SNAP OBQ shows `DateProcessed 2026-09-25T15:36:26.153` (BST, same second): SNAP DID process it. A "failed" clear-down was recorded, marked retryable/replayable, for a confirmation that was delivered and cleared. Replaying it would re-send a delivered goods-out.
- For #6369469 (queueId SPLU016608) SNAP OBQ shows `DateProcessed: null` on 2026-09-29, 13 days after the failure: this PATCH genuinely did not land and the row is still on the OBQ; the recorded failure has attempts 0, no alert, no owner. (Stage field on that row reads "00" vs Key Stage="90" — unexplained; poller behaviour for it not examined here.)
- Log content: the 9/25 ClearFailed log (prod revision 1135a83) carried the raw axios request preamble incl. a Basic Authorization header (`request._header`). Fixed on master by FUSE-1238 (c610247: shared `serialiseError` allow-list, @gfs-bifrost/observability 2.2.0); prod was still on the older revision when observed. Not a gap for the feasibility study, but confirms clear-down errors were logged verbatim.

## 7. Exit paths / terminal outcomes (handleConfirmationMade and its delivery)

| # | Path | Trigger | Today | Recorded where | Terminal? | Silent? | Depends on row staying on OBQ? |
|---|------|---------|-------|----------------|-----------|---------|-------------------------------|
| 1 | Success | PATCH 2xx | row processed; Processed log + metric | log+metric | yes | no | n/a |
| 2 | Decode/bulk/schema failure | ingestEvent throws (e.g. bulk array envelope) | 202 already sent, log with payload, return | log only (no metric) | yes for the message (acked) | yes | YES: row stays, re-announced |
| 3 | Not clearable | no queueId / business id | log + metric + failure publish | replay (except stock_adjustment) | yes | no (unless stock_adjustment) | yes (row stays) |
| 4a | Clear fails, permanent | 4xx incl. 404/400 (incl. maybe already-processed), missing creds | failure publish (retryable false) | replay; stock_adjustment nowhere | yes | no / yes for stock_adjustment | yes |
| 4b | Clear fails, transient | 5xx after 1 retry, timeout/reset (PATCH not retried), 429 | failure publish, retryable:true | replay; stock_adjustment nowhere | yes (no auto retry) | no / yes | yes; and row may actually be processed (see 6) |
| 4c | Clear fails, infra | circuit open, slot timeout (30s), config/redis error | failure publish, retryable:false | replay | yes | no | yes; outage => burst of false failure records |
| 5 | Failure publish fails | Pub/Sub publish error | error log + `messagesFailed` metric | log+metric only | yes (acked) | effectively yes | YES |
| 6 | Crash/SIGTERM/CPU throttle after 202 | scale-in, OOM, throttled idle instance mid-PATCH | nothing recorded; message already acked | nowhere | n/a | yes | YES |
| 7 | Endpoint unavailable | Cloud Run 429/503/cold-start failure | Pub/Sub retries 10-600s (WOC: immediate), 7d retention, no DLT | Pub/Sub backlog metrics/monitor (>300s) | after 7d dropped | after 7d yes | yes |
| 8 | Duplicate made (broadcast) | N connectors deliver same queueId | N PATCHes; 2nd..Nth outcome on processed row UNKNOWN (untested) | if error: spurious failure in replay | yes | no | n/a |
| 9 | Unhandled exception after 202 | throw outside inner try | unhandledRejection recorder | log/metric only | yes | yes | yes |
| 10 | Replay redrive of a clear-down failure | operator hits replay | re-publishes delivered canonical to confirmation_ready => re-delivery | replay history | n/a | n/a | n/a |

## 8. What would change in snap-adapter
Option A - poller marks (early consume), snap-adapter clear-down retired:
1. Remove/disable the 8 made subscriptions (pubsub.tf), the `/confirmation/made/:recordType` route, `ConfirmationsService`, `ClearableRecord*`, `ConfirmationErrorService`, `CONFIRMATION_FAILURE_USE_CASE_MAP`, `CONFIRMATION_DATA_FAILURE_TOPIC` env + publisher IAM (iam.tf:56). `CustomerHttpRouter` stays (create path). Unsubscribing drops any unacked backlog: drain first.
2. Cutover overlap: rows already announced but awaiting made need clearing during transition => keep the handler until the backlog is gone, and make 404/400 on an already-processed row a *success* (currently it emits a failure). Requires confirming SNAP's PATCH semantics on a processed row (cannot be tested read-only).
3. The poller must own what snap-adapter had: per-tenant credentials, breaker/rate-limit, and an explicit answer to "PATCH ambiguous (timeout/reset)". Evidence above: reset can mean processed OR not. A blind retry needs to be verified idempotent; a GET of the row's `DateProcessed` after an ambiguous failure is a cheap disambiguator.
4. A failed *mark* is not a *delivery* failure; publishing it as `confirmation_data_failure` (redrivable) produces the duplicate-delivery hazard in row 10. Needs its own record type/handling.
5. Add the missing monitor on mark failures.
Option B - keep confirmation_made informational in snap-adapter: keep the subs but turn the handler into a no-op/metric (or a verify-only GET of DateProcessed). No topology change; collector/replay unaffected. The only loss is the `snap.confirmation_handled` signal and the "awaiting clear-down" semantics of the poller's re-read/skip tile.
In both options collector (processed = delivered) and replay (clear pick/pack failures) keep working unchanged because their subscriptions are independent.

## 9. Open questions
- SNAP behaviour of PATCH /processed on an already-processed row (200 idempotent? 400? 404?) and whether repeated PATCH from broadcast N-made produces error/failure records. Untestable read-only; prior failure reasons for the other ~23 metric failures are outside log retention.
- Why row SPLU016608 (unprocessed 13 days, Stage "00") is not visibly being re-delivered or alerted (poller claim TTL / `$top:1000` window / stage filter) — poller investigators.
- Does fapi/shopify/sftp ever publish made in bulk shape today (snap-adapter would drop it, path 2)? fapi comments say they moved to single-record; not re-verified for shopify/sftp at runtime.
- Actual Cloud Run CPU allocation in prod (IaC unspecified; not checked with gcloud).
- Whether the second replay failure's `metadata.source: snap-adapter` (vs `shopify` on the newer one) reflects an old metadata-forwarding bug (9/16 revision) — cosmetic.
