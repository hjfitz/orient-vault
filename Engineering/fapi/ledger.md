---
tags: [waypoint, ledger]
title: fapi — work ledger
---
# fapi — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-04 — FUSE-1153

Capture the raw API request on ingress

fapi now stamps the request it actually received on metadata.capture of every record it publishes to create_record_request: route, headers (any name matching auth|token|secret|key|cookie|session|password dropped) and the raw body exactly as sent, decoded with the declared charset and keeping a BOM. It is captured by a body-parser verify hook (bootstrap/body-parsers.ts, shared with the integration tests), ahead of v1's legacy mapping and v2's Zod defaulting, and threaded to bulk-ingest through the @ApiRequestCapture() param decorator. The body is left out above 256 KB, or 16 MB across a request's records, sized against prod request sizes (max 83 KB) and dedupe-service's 1 MB Datadog log line; route and headers are kept, a "Raw request body not captured" warning is logged, and an oversized body isn't held in memory. Types were bumped to ^11.4.1 (identical to Renovate #178). Self-reviewed twice by review-panel (second pass added the capacity persona) and verified in dev against the published envelopes. Follow-ups: FUSE-1344 (dedupe-service logs and stores the capture), collector dedup of captures (sibling ticket).

PR: gfs-bifrost/fapi#184

## 2026-10-20 — Start fapi on a cache-less remote config when Redis is unreachable

Start fapi on a cache-less remote config when Redis is unreachable

When the remote-config Redis init times out or fails, rebuild the provider with no cache and make ConfigApiAdapter wait for init, so requests no longer hang on cache writes. Fixes the INC-40 REST hang (zone europe-west2-b Memorystore unreachable). Shipped to prod ahead of QA.

Ship: SHIP-1020-fapi-redis-init
PR: gfs-bifrost/fapi#179

## 2026-10-14 — Make the work-order docs examples produce a work order the warehouse accepts

Make the work-order docs examples produce a work order the warehouse accepts

The published work-order examples passed fapi validation but Snap rejected them after the 202 (no UoM, no component ordered qty, no currency or shipment date, literal class KIT). Both examples now carry every field a work order needs, with YOUR_* placeholders; finished-good lines send required: 0 so Snap doesn't treat the finished good as stock to pick. Verified end to end in dev (GADG074F3BC7C95). Found while investigating ILG QA's GADG work-order API testing.

PR: gfs-bifrost/fapi#175

## 2026-10-13 — Reference the config-service API key at latest instead of reading it

Reference the config-service API key at latest instead of reading it

Programme H5: drop google_secret_manager_secret_version data source (value in state); secret_key_ref version=latest. Draft — merging queues a gated prod deploy; rotate the key after, since old state versions hold it.

PR: gfs-bifrost/fapi#172

## 2026-10-02 — Record each REST connector remote-config couldn't resolve

Record each REST connector remote-config couldn't resolve

Poller Clear-Down E8. On remote-config 2.3.0's resolveWithUnresolved: a fan-out records a retryable config_service dependency failure per unresolved REST connector (connectorId on body + envelope); a routed confirmation whose connector couldn't be loaded records the same retryable failure instead of connector_unresolvable. Merged 66c7a4d.

PR: gfs-bifrost/fapi#166

## 2026-10-02 — Drop non-null assertions Biome's unsafe fix breaks

Drop non-null assertions Biome's unsafe fix breaks

Out-of-ticket housekeeping. lint:fix's unsafe Biome rewrite of non-null assertions in legacy-to-canonical.mapper.spec.ts broke build:check; assertions written null-safely so lint:fix is a no-op. Test-only.

PR: gfs-bifrost/fapi#164

## 2026-10-02 — Broadcast legs reach a terminal outcome

Broadcast legs reach a terminal outcome

Two stacked PRs on E5 (#160). #161: confirmation_made published once per push and a made that can't be published rejects (routed + fan-out; stock unchanged). #162: a fan-out (broadcast or no connectorId) records one confirmation_data_failure per REST connector it couldn't reach — inactive (anything not 'active'), misconfigured, or webhook failure — with the leg's connectorId on body and envelope, source rest, so a redrive targets that connector; no webhookUrl = doesn't take confirmations, benign; a fan-out connector-lookup failure records a retryable failure naming no connector and acks. Dev-verified on HJF (webhook example.com): leg recorded, redrive routed to that connector only. GADG avoided for e2e (active 'Fulfil.io Testing' REST connector). Poller Clear-Down E1.

PR: gfs-bifrost/fapi#161
PR: gfs-bifrost/fapi#162

## 2026-10-01 — Bound confirmation_ready redelivery with a retry budget

Bound confirmation_ready redelivery with a retry budget

Poller Clear-Down E5. The seven confirmation_ready subs get retry_policy 10s-600s and a dead_letter_policy (max 10) so Pub/Sub sends deliveryAttempt; the DLT deliberately has no publisher grant. On attempt 10 the controller records any 5xx-bound error as a retryable fapi.redelivery_exhausted failure and acks (fan-out names no connector); if that can't be published it keeps rejecting. ack_deadline_seconds 60 -> 300. Verified on dev: attempts 1-12 rejected with growing backoff while the failure topic was unpublishable, exhaustion logged from attempt 10, recorded and 204 once restored (replay c27d339b). Draft, awaiting review.

PR: gfs-bifrost/fapi#160

## 2026-10-01 — Scope the RGA confirmation subscription to REST and broadcasts

Scope the RGA confirmation subscription to REST and broadcasts

The RGA confirmation_ready sub was recordType-only on the false premise that the poller broadcasts RGA (it routes RGA since snap-adapter#222), so every SFTP/Shopify-routed RGA reached fapi and, since fapi#155, recorded a spurious failure. Added the source="rest" OR broadcast="true" clause (in-place replace, self-healing while rows stay on the OBQ — must precede Poller Clear-Down C2). Dev-verified with three test RGAs + real GADG traffic. In prod 2026-10-01 (api-gateway-prod 50578d2, shipped with #155). Poller Clear-Down A4.

PR: gfs-bifrost/fapi#159

## 2026-09-30 — Clear red DevSecOps scans

Clear red DevSecOps scans

Bump brace-expansion override to >=5.0.12 (audit + app-tree image finding); trivyignore three npm-bundled base-image CVEs (brace-expansion, undici) with no patched npm released. Follow-up: move Nest build tooling out of dependencies.

PR: gfs-bifrost/fapi#156

## 2026-09-30 — FUSE-1238

Record a routed confirmation that fapi cannot deliver

A routed confirmation (names a connector, not broadcast) with no deliverable REST connector was only counted and logged, and a config-service outage while reading connectors was acked as a 204 drop. Both now publish a confirmation_data_failure to replay, and a failure that cannot be published rejects the push so Pub/Sub redelivers. Broadcast, unnamed and stock_adjustment confirmations are unchanged. Verified in dev with the real attribute shape. Poller Clear-Down unit A1.

PR: gfs-bifrost/fapi#155

## 2026-09-29 — Count only 5xx as request failures, and log rejected ingest batches

Count only 5xx as request failures, and log rejected ingest batches

The availability monitor was flapping on DOCKBAY's 400 validation rejections (19 since 28 Sep, zero 5xx). request.failure is now 5xx-only; rejected ingest batches log 'Record batch rejected' at warn with validationErrors.

PR: gfs-bifrost/fapi#154

## 2026-09-24 — FUSE-1253

Bump @gfs-bifrost/types to 10.4.0

Needed before any SFTP connector is saved with egressFiletype edi. remote-config's connector backlink refresh validates every connector revision with this service's schema, so on types 10.3.0 an edi connector's revision event throws, and the config-event handler 500s and redelivers. Types-only lockfile change.

PR: gfs-bifrost/fapi#147

## 2026-09-23 — Only deliver stock adjustments to REST connectors that enable them

Only deliver stock adjustments to REST connectors that enable them

Out-of-ticket (flag from FUSE-668; moving stock_adjustment onto shared topics is FUSE-1181–1185). A stock_adjustment now goes only to active REST connectors with config.stockAdjustmentsEnabled: true; absent counts as off. Toggled off: no webhook POST, no stock_adjustment_made (so the SNAP row isn't cleared), no failure; fuse.confirmation.unroutable tagged reason:use_case_inactive, matching sftp/shopify. Switched-off connectors are no longer validated for stock adjustments. Other confirmation types unchanged; confirmationsEnabled still not a gate here. Companion: shopify-connector#274.

PR: gfs-bifrost/fapi#144

## 2026-09-22 — FUSE-1037

Add per-customer rate limiting on the stock endpoint

Added GET /api/v1/stock and GET /api/v2/stock as authenticated 501 stubs, since FUSE-1035
(the WMS gateway proxy) and its own dependencies aren't built yet — there was nothing real
to wire these routes to. Both carry the new @RateLimited() decorator, applied next to their
auth decorator: a service-wide, per-customer, Redis-backed RateLimitInterceptor (an interceptor,
not a guard, so it always runs after auth whatever the decorator order) returning 429 once
RATE_LIMIT_MAX_REQUESTS is exceeded within RATE_LIMIT_WINDOW_MS. One budget per business is
shared across every rate-limited route, so v1 and v2 draw from the same bucket. Verified live on
dev, re-run after the refactor: 501/401 auth behaviour, the 429 boundary at exactly the
configured limit, cross-customer isolation, and recovery after the window elapsed. Found and
fixed a real bug during verification — @gfs-bifrost/cache's tryGetAsync silently re-populates
fapi's per-instance LRU on every network hit, permanently sticking the counter after the second
request on an instance; fixed by evicting the local cache entry after each read.

PR: gfs-bifrost/fapi#142

## 2026-09-16 — FUSE-1059

Decommission legacy PO/SO confirmation topics

Swapped fapi's PO/SO confirmation-ready subscriptions from the legacy per-entity `purchase_order_confirmation_ready`/`sales_order_confirmation_ready` topics onto the shared cross-entity `confirmation_ready` topic, alongside the five record types already there. The sales-order filter is `recordType = "goods_out_confirmation"`, not `"sales_order"`, since the ready and made sides stamp different values for a sales order — a symmetric filter would match nothing and silently drop every SO confirmation. Add and remove happened in one Terraform apply, since a ready confirmation delivered twice fires a customer webhook twice and is not idempotent. `stock_adjustment` was left untouched on its own per-entity ready topic.

A follow-up PR normalised the made-side naming: fapi now stamps `goods_in_confirmation`/`goods_out_confirmation` on `confirmation_made` for goods-in/out confirmations instead of echoing its internal `purchase_order`/`sales_order` record type, so the made side agrees with the ready and failure sides (create-side names the record; confirmation-side ready/made/failure name the confirmation).

A third PR then retired the legacy made-side publish entirely: fapi no longer dual-publishes PO/SO made confirmations to both the legacy per-entity topics and the cross-entity topic — each now publishes once, to the cross-entity `confirmation_made` topic only. The two now-unused legacy topic env vars, their remote-state locals, and their Publisher IAM grants were removed. First of ~11 PRs across 7 repos on the FUSE-1059 legacy-topic decommission, under the FUSE-927 epic.

PR: gfs-bifrost/fapi#127
PR: gfs-bifrost/fapi#129
PR: gfs-bifrost/fapi#135

## 2026-09-16 — FUSE-1056

Resolve confirmation webhook target by connectorId + filter source/broadcast

Confirmation webhooks now target the originating connector: a confirmation carrying `metadata.connectorId` forwards only to that connector instead of broadcasting to every active, webhook-configured REST connector, by filtering the business's already-fetched connector list rather than a second lookup. An unresolvable connectorId publishes a `connector_unresolvable` `confirmation_data_failure` and forwards to nobody, instead of broadcasting; no connectorId or `broadcast=true` keeps the existing broadcast-to-all behaviour. Connector config is now validated at candidate selection rather than delivery — an invalid `webhookUrl` or missing `webhookSecretKey` drops that connector from the candidates and is reported, so a broadcast still reaches the healthy connectors, and if every webhook connector is misconfigured the reason is the new `misconfigured` (distinct from the legitimate webhook-less `no_confirmation_mappings` case). Exception handling was centralised in `AllExceptionsFilter`; `extractBusinessId`'s bare `Error` throws became a typed `BusinessIdExtractionException`, acked 204 instead of falling to the generic 500 branch and redelivering forever. Fixed a metadata-stripping bug where `connectorId`/`source` were silently dropped on every confirmation decode, by adopting `@gfs-bifrost/pubsub`'s `PubSubIngestor`. Adopted `@gfs-bifrost/types` 9.5.0's confirmation record registry, collapsing eight per-confirmation-type enumeration sites onto one shared registry.

Two follow-up PRs then added the deferred subscription-level `source`/`broadcast` filter (`recordType AND (attributes.source = "rest" OR attributes.broadcast = "true")`), first to the PO/SO `confirmation_ready` subs and then to the remaining pick/pack/WOC/FGR subs — without it, fapi was receiving every business's confirmations regardless of delivery channel and manufacturing `confirmation_data_failure`s for Shopify/SFTP-origin ones another connector already delivers, tripping the egress webhook delivery failures monitor for at least one real business. RGA was deliberately left `recordType`-only in both passes, since the poller broadcasts RGA to every connector and a `source`-scoped filter would diverge from that fan-out.

PR: gfs-bifrost/fapi#123
PR: gfs-bifrost/fapi#134
PR: gfs-bifrost/fapi#137

## 2026-08-11 — FUSE-873

Fire finished good receipt webhooks

Added a new `finished_good_receipt` confirmation webhook — a `recordType`-filtered push subscription on the shared cross-entity `confirmation_ready` topic forwards FGR confirmations to every active, confirmation-enabled REST connector's webhook, identical to the existing RGA/pick/pack/WOC route, with no new topics, IAM grants, or env vars. `confirmation_made` is published on success, tagged `recordType=finished_good_receipt`, and a terminal delivery failure publishes to `confirmation_data_failure` (`useCase=finished_good_receipt`) so the downstream OBQ clear-down can retry. No egress mapping is applied — the canonical FGR array is POSTed as-is, matching every other confirmation type on this route and the precedent already set for `work_order_confirmation`. Bumped `@gfs-bifrost/types` to `^8.4.0` for `CanonicalFinishedGoodReceipt(Schema)` and the `finished_good_receipt` `FailureUseCase` member.

PR: gfs-bifrost/fapi#107

## 2026-07-17 — FUSE-888

Fire pick/pack confirmation webhooks + route confirmation failures

Pick/pack confirmations now flow through fapi's webhook egress: two new `recordType`-filtered push subscriptions on the shared `confirmation_ready` topic (`pick_confirmation`, `pack_confirmation`) forward to the customer's REST webhook via the existing generic confirmation flow and publish `confirmation_made` on success. No new topics or IAM — they reuse the shared `confirmation_made` publisher grant. Pick/pack terminal failures initially log-and-continued pending FUSE-901.

A follow-up PR then extended terminal-failure publishing to every confirmation type — purchase_order, sales_order, stock_adjustment, return_goods_authorization, pick_confirmation, and pack_confirmation all now publish to `confirmation_data_failure` when webhook delivery exhausts retries (previously only RGA did this). Renamed `CREATE_DATA_FAILURE_TOPIC` → `CONFIRMATION_DATA_FAILURE_TOPIC`, since this service never used it for anything but confirmation failures and RGA publishing there was a directional mismatch (create_data_failure is ingress-side; this flow is egress-side) — fully migrated with nothing left pointing at the old topic. Bumped `@gfs-bifrost/types` to `^7.6.0` for the pick/pack `FailureUseCase` members.

PR: gfs-bifrost/fapi#77
PR: gfs-bifrost/fapi#84

## 2026-07-17 — FUSE-991

Stamp ApiCapture + dual-publish SO/PO/MD to create_record_request

REST ingress now stamps a fieldless `ApiCapture` (`capture: { type: "api" }`) on the create envelope for all four ingress record types — the REST channel has no raw inbound payload to point at, so the marker carries only the discriminator. Switchover-prep: SO/PO/MD now dual-publish to the central `create_record_request` topic (recordType-tagged) alongside their legacy per-entity topics; RGA was unchanged, already cross-entity only. The emitter's `TopicMap` was widened to support multi-topic fan-out per entity. Nothing consumes SO/PO/MD on `create_record_request` yet (dedupe filters it to `return_goods_authorization`) — this PR is switchover-prep with no subscription changes. One of a 4-PR FUSE-991 set across sftp/dedupe/fapi/shopify, opened together.

PR: gfs-bifrost/fapi#86

## 2026-06-29 — FUSE-616

Remove businessId fallbacks now that field is required

Removed the `business-id-extractor`'s fallback-to-empty-string (`?? ""`) for sales-order and return-goods cases, now that `businessId` is required on `CanonicalSalesOrder` and `CanonicalRGA` (`@gfs-bifrost/types@7.0.0`) rather than dead code guarding an impossible path. Deleted the now-impossible `describe("when businessId is undefined")` test blocks for both cases. Bumped `@gfs-bifrost/types` to `^7.0.0`.

PR: gfs-bifrost/fapi#61

## 2026-06-23 — FUSE-794

Bifrost metadata + logger traceability

Bumped `@gfs-bifrost/types` to `^6.3.0` and replaced fapi's local `BifrostMessageMetadata`/`BifrostMessage` fork with a re-export of the shared types, so egress metadata can carry the new optional `source`/`connectorId`/`recordId`/`recordType` fields. `source="fapi"` plus the canonical `recordType` are now stamped on every outbound envelope: ingress create emits, `confirmation_made` emits, the single-record `stock_adjustment_made` emit, and the `create_data_failure` emit. `recordId` is stamped only on single-record envelopes (ingress create, `stock_adjustment_made`); bulk envelopes carry `source`+`recordType` only, with `recordId` kept per-record on the logger. `CorrelationDetails` expanded to `{ correlationId, businessId, flow, recordType, recordId }`, spread onto every log line under `requestor`. Inbound metadata is lifted onto the CLS namespace at the two decode points: confirmation events (`flow=confirmation`) and config-revision events (`flow=config`). `connectorId` was deliberately left unset — fapi is REST ingress with no connectorId cleanly in scope on ingress or confirmation egress paths.

PR: gfs-bifrost/fapi#58

## 2026-06-15 — FUSE-830

Fire RGA confirmation webhook (confirmation_made + entity_error)

RGA confirmations now fire the customer webhook — removed the FUSE-829 validate-and-ack short-circuit, so return-goods flows through the same `routeConfirmations` path as the other confirmation types (POSTs the canonical RGA array with `x-correlation-id`, retry/backoff, `confirmationsEnabled` gate). A successful RGA confirmation now publishes `confirmation_made` to the cross-entity topic discriminated by `attributes.recordType=return_goods_authorization` (fapi was the first publisher there). An RGA delivery that exhausts retries publishes a `BifrostFailure` to `create_data_failure` (`entity_error`) — other confirmation types keep their existing log-and-continue behaviour. Added `CONFIRMATION_MADE_TOPIC` and `CREATE_DATA_FAILURE_TOPIC` env vars with matching IaC. Bumped `@gfs-bifrost/types` to `^5.5.0` for the new RGA use-case keys. Webhook delivery reuses the generic REST-connector webhook (`RestIngress.webhookUrl`) — there is no separate RGA webhook config, since RGA egress mapping (FUSE-825) was decided as Won't do.

PR: gfs-bifrost/fapi#49

## 2026-06-11 — FUSE-953

Replace VPC connector + NAT with Direct VPC egress

Switched Cloud Run to Direct VPC egress (network interfaces on the existing custom subnet) instead of a Serverless VPC Access connector, keeping the same private-range reachability at zero fixed cost. Egress mode changed from ALL_TRAFFIC to PRIVATE_RANGES_ONLY — Redis traffic stays on the VPC, while public calls (Pub/Sub, Datadog, config-service) leave via Cloud Run's managed egress instead of being hairpinned through the VPC and NAT. Deleted the Cloud Router, NAT gateway, and VPC connector (fixed-cost resources billed 24/7); the VPC and subnet remain since Redis's `authorized_network` and direct egress both need them. Part of a fleet-wide rollout of the FUSE-953 network lever, piloted on dedupe-service. During the deploy window the old revision briefly lost public egress when the NAT was destroyed, producing a short burst of Datadog-sidecar timeout errors from the draining instance with no impact on app traffic.

PR: gfs-bifrost/fapi#43

## 2026-06-05 — FUSE-829

Subscribe to and ack RGA confirmations

Added a filtered Pub/Sub subscription on the tagged cross-entity `confirmation_ready` topic with `filter = "attributes.recordType = \"return_goods_authorization\""` — the first subscription-level `recordType` filter in this repo. Added the `return_goods_authorization` confirmation type, validating `BifrostBulkMessage<CanonicalReturnGoodsAuthorization>` at the boundary and acking 204. RGA does not fire customer webhooks yet — it short-circuits before the generic connector-forwarding path; webhook delivery needed RGA-specific config and was deferred to FUSE-830. All push routes were moved onto the Events API v1 grammar (`/events/v1/<domain>/<stage>/:recordType`) in the same change, with no legacy aliases kept. Confirmation metric/log `type` tags changed value (`purchase-order` → `purchase_order` etc.), requiring updated Datadog facets.

PR: gfs-bifrost/fapi#40

## 2026-06-02 — FUSE-675

Handle stock adjustment ready events

Added a new push subscription on `stock_adjustment_ready`, targeting `POST /events/confirmation/stock-adjustment`, with publisher IAM on `stock_adjustment_made`. `ConfirmationController` validates the new `stock-adjustment` confirmation type against `CanonicalStockAdjustmentSchema` and forwards to every REST connector registered for the business through the existing confirmation flow. `ConfirmationService.extractBusinessId` reads `identifiers.businessId` for stock adjustments (PO/SO use `identifiers.bizId`). `PubsubEmitter.emitConfirmationMade` publishes stock adjustments as one single-record `BifrostMessage<CanonicalStockAdjustment>` per adjustment, matching the envelope shopify-connector publishes, rather than the bulk envelope the order confirmation topics use. New required env var `STOCK_ADJUSTMENT_MADE_TOPIC`. On failure (no connector succeeds) the event is still acked with 204 and no made-event is emitted, matching the existing PO/SO confirmation handling.

PR: gfs-bifrost/fapi#38

## 2026-04-17 — FUSE-318

Directory restructure + config-service-backed auth guard

Moved controllers/middlewares to `src/http` and types to `src/models`/`src/models/dto`, adhering to the preferred directory structure ahead of active development. Followed up with `RemoteConfigApiKeyGuard`, replacing the static-env-var `ApiKeyGuard`: it extracts `businessId` from the request body and validates the `x-api-key` header against the business's REST connector, resolved cache-first with a config-service API fallback via `RemoteConfigProvider`. BusinessId extraction was split into composable Zod schemas — a canonical v2 schema and a `@deprecated` legacy v1 schema (JSON + CSV `AccountID`-column extractor) isolated for later removal. Missing/wrong key both throw an opaque `UnauthorizedException`; unresolvable business throws `BadRequestException`. Bumped `@gfs-bifrost/types` to 2.7.0 to pick up `RestIngressSchema` on `IngressBindingSchema`, without which config-service responses for REST connectors failed validation.

PR: gfs-bifrost/fapi#15
PR: gfs-bifrost/fapi#16

## 2026-03-09 — FUSE-629

Config event handler + config-service hookup

Added the initial config-event handling pipeline: a `ConfigEventModule`/`ConfigEventService` with a dispatcher pattern to register and dispatch fragment/backlink revision events, replacing inline controller logic in `ConfigEventController`. Added a `ConfigApiAdapter` that fetches warehouse routing, DDP rules, and connector details from config-service, with caching for performance and resilience. The global exception filter now handles `ConfigApiException` by acking with HTTP 204, preventing infinite Pub/Sub retry loops on unrecoverable errors. New `CONFIG_SERVICE_URL`/`CONFIG_SERVICE_API_KEY` env vars with matching Terraform IAM/env wiring for Cloud Run, plus a `CONFIG_API_EXCEPTION` metric. Bumped `@gfs-bifrost/types` to 1.7.0 and dropped the local `ConfigPayload`/`ConfigRevisionMessage` types in favour of the shared package.

PR: gfs-bifrost/fapi#3
PR: gfs-bifrost/fapi#4
