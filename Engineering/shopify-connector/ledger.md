---
tags: [waypoint, ledger]
title: shopify-connector — work ledger
---
# shopify-connector — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-02 — Raise the follow-redirects floor to 1.16.2

Raise the follow-redirects floor to 1.16.2

follow-redirects 1.16.1 gained a high advisory (GHSA-mrwp-f3q8-3g9p) that failed the dependency audit and both image scans on main and on the Renovate bump. The override floor moves to 1.16.2; lockfile and pnpm-workspace.yaml only.

PR: gfs-bifrost/shopify-connector#357

## 2026-10-22 — Log the userErrors Shopify returns when an order tag write is rejected

Log the userErrors Shopify returns when an order tag write is rejected

Ship: SHIP-1022-order-update-usererrors

OrderUpdateMutationResponseSchema typed userErrors[].field as a string and order as non-null, so every real Shopify rejection of an order tag write logged an opaque ZodError. It now reuses ShopifyUserErrorSchema, treats a null order as an error, and logs the raw response and Zod issues on an unparseable response. The per-store double write (two connectors on one store) is deliberately untouched; the real userError on dev is 'Order tags is invalid' (field tags), cause still unknown.

PR: gfs-bifrost/shopify-connector#349

## 2026-10-20 — Start shopify-connector without Redis when it is unreachable

Start shopify-connector without Redis when it is unreachable

Bound the remote-config Redis init at startup to 10s and fall back to a cache-less remote config, plus startup step logs. Fixes the INC-40 crash loop (zone europe-west2-b Memorystore unreachable). Shipped to prod ahead of QA.

Ship: SHIP-1020-shopify-redis-init
PR: gfs-bifrost/shopify-connector#345

## 2026-10-19 — FUSE-1317

Resolve dictionary lookups and send mapped tracking URLs on Shopify fulfillments

The goods-out carrier rule now gets the mapping's dictionaries, so lookup() resolves there; a miss with no default falls back to the despatch's carrier as before. A new optional header rule targeting shipping.carrierTrackingNumberUrl sends one URL per tracking number (evaluated per despatch, despatches[0] = that parcel), all or none; any gap omits them and logs TrackingUrlsOmitted (support) without blocking the fulfilment. The success log now carries the trackingInfo Shopify stored. Live mappings (Purdy & Figg, Saira) are pinned by sales-order-confirmation.characterisation.spec.ts. Gotcha: a lookup() miss inside concat() returns the other args, so the URL rule's miss surfaces as invalid_url, not unresolved.

PR: gfs-bifrost/shopify-connector#341
PR: gfs-bifrost/shopify-connector#342

## 2026-10-14 — Read the per-connector API cache flag at runtime

Read the per-connector API cache flag at runtime

shopify-connector is the first backend reader of runtime flags. ShopifyApiFactory takes a per-call predicate wired to remote-config 2.4.0 provider.featureFlags.isEnabled('shopify-connector.api-cache-per-connector', {businessId, connectorId}); unresolvable = false, and #332's env var is removed. POST /events/feature-flags/revision (push sub on bifrost.{env}.feature_flag_revision.v1) refetches immediately. Boot awaits ready() for at most 1 s. New metrics: fuse.feature_flag.refresh{trigger,outcome} and api.factory.cache key_mode. Dev proof: the flip reached the service in 3 s, and the next poll covered both Escentric connectors. The characterization harness config fake stubs featureFlags. Stacked on #332 (stack #336).

PR: gfs-bifrost/shopify-connector#335

## 2026-10-14 — Re-date the deepmerge-ts audit allowlist entry

Re-date the deepmerge-ts audit allowlist entry

Root audit-ci.jsonc GHSA-ggr8-5vv4-36mx (deepmerge-ts, high) expired 2026-10-14, and audit-ci failed the DevSecOps dependency audit on main and every PR. The summary step still labels an expired entry 'allowlisted', so the log reads '0 findings gate' while exiting 1. Re-checked: @prisma/config 7.10.0 and 6.19.3 still pin 7.1.5, and only 8.1.0-dev takes 8.0.2. Expiry moved to 2026-10-21. Reproduced locally with main's config (exit 1), and the change gives exit 0.

PR: gfs-bifrost/shopify-connector#334

## 2026-10-14 — Cache the Shopify API instance per connector behind a flag

Cache the Shopify API instance per connector behind a flag

Two connectors on one Shopify store (Escentric UK + PL on escentric-sandbox) — the API factory cached by shop, so the second connector was never polled. New SHOPIFY_API_CACHE_PER_CONNECTOR flag (on in dev, off in prod) keys the cache by shop + connector. Draft; dev verification owed. Bulk tick still assumes one bulk connector per shop.

PR: gfs-bifrost/shopify-connector#332

## 2026-10-12 — FUSE-1118

Skip goods-out lines with no Shopify reference instead of failing the confirmation

A despatched line with no Shopify fulfillment-order line id (a warehouse-added free item, e.g. SAIRA MC1/HFO10) is skipped like a kit component; the rest is fulfilled. Warn log 'Lines with no Shopify reference skipped' (audience support) plus metric fuse.confirmations.lines_skipped. Verified in dev on GADG. Draft.

PR: gfs-bifrost/shopify-connector#329

## 2026-10-05 — Drop the unused GraphQL Nest packages

Drop the unused GraphQL Nest packages

Out-of-ticket, clears the red nightly DevSecOps Scans. @nestjs/graphql and @nestjs/apollo were declared but unused, and were the only prod path to braces@3.0.3 (GHSA-vfj7-8cjw-p6xm, HIGH, no patched release). Removed; audit passes.

PR: gfs-bifrost/shopify-connector#310

## 2026-10-02 — Record each Shopify connector remote-config couldn't resolve

Record each Shopify connector remote-config couldn't resolve

Poller Clear-Down E8. On remote-config 2.3.0 (pinned in both apps): a fan-out goods-out records a retryable failed leg per unresolved Shopify connector; a routed confirmation naming an unreadable connector records the same retryable failure instead of no_connectors/source_mismatch. Merged 4dec081.

PR: gfs-bifrost/shopify-connector#308

## 2026-10-02 — Broadcast legs reach a terminal outcome

Broadcast legs reach a terminal outcome

Three stacked PRs. #302: publishMade always requires redelivery when made can't be published (routed + fan-out) and an already-fulfilled fan-out re-emits made; new getGoodsOutConfirmationStates reads each connector's goods-out mapping independently via remote-config's cache (absent = mapping 404 only). #301: fan-out (broadcast or no connectorId) path — no connector / no goods-out mapping benign; inactive mapping/connector, unreadable config/mapping = one failure on that leg (connectorId on body + envelope); business lookup failure = retryable, no connector, ack; E5 exhaustion now records on fan-out too. #303: delivery outcomes fail the shop that failed; not-in-shop fails only the origin connector when no shop delivered; non-numeric FO ids rejected before calling Shopify (fan-out only — Shopify answers them with GraphqlQueryError). Dev-verified on ACADEMIC/UWDG. Port with goods-out if it ever moves to shopify-egress-service. Poller Clear-Down E1.

PR: gfs-bifrost/shopify-connector#302
PR: gfs-bifrost/shopify-connector#301
PR: gfs-bifrost/shopify-connector#303

## 2026-10-01 — Bound goods-out confirmation redelivery with a retry budget

Bound goods-out confirmation redelivery with a retry budget

Poller Clear-Down E5. goods_out_confirmation sub gets retry_policy 10s-600s and a dead_letter_policy (max 10) so Pub/Sub sends deliveryAttempt; the DLT has no publisher grant. Per confirmation in the batch, a ConfirmationRedeliveryRequiredException at attempt 10 is recorded as a retryable shopify-connector.redelivery_exhausted failure and the loop continues; unpublishable keeps rejecting. Verified on dev: attempts 1-12 rejected, exhaustion logged from 10, recorded and 202 once restored (replay 98bb2ec5). Draft, awaiting review.

PR: gfs-bifrost/shopify-connector#300

## 2026-09-30 — FUSE-1238

Record routed Shopify confirmations that cannot be delivered

shopify-connector now publishes a confirmation_data_failure for every routed goods-out confirmation it cannot deliver (unresolvable connector, no confirmations config, source mismatch, Shopify fulfillment-order skips, Shopify/config API errors), treats an already-fulfilled order as delivered so a lost made re-emits on redelivery, and nacks the push when the failure or made cannot be published. Broadcast and unnamed confirmations keep log-and-ack. Poller Clear-Down unit A3.

PR: gfs-bifrost/shopify-connector#294

## 2026-09-24 — FUSE-1253

types 10.4.0 bump superseded by Renovate

Closed shopify-connector#282: Renovate shopify-connector#281 (merged 2026-09-24 13:17) already moved @gfs-bifrost/types to 10.4.0 and rules-engine to 2.1.1. The FUSE-1253 gate (this service on types >=10.4.0 in prod before config-service accepts edi) is met once #281's deploy reaches prod.

PR: gfs-bifrost/shopify-connector#281

## 2026-09-24 — FUSE-1253

Bump @gfs-bifrost/types to 10.4.0

Needed before any SFTP connector is saved with egressFiletype edi. remote-config's connector backlink refresh validates every connector revision with this service's schema, so on types 10.3.0 an edi connector's revision event throws, and the config-event handler 500s and redelivers. Types-only lockfile change.

PR: gfs-bifrost/shopify-connector#282

## 2026-09-24 — FUSE-1238

Document metadata.source as the ingress channel

CLAUDE.md described metadata.source as the emitter's FUSE-794 provenance id, the reading that led other producers to overwrite it with their own names. Now documented as the ingress channel (rest/sftp/shopify), carried unchanged by every downstream hop. Docs-only.

PR: gfs-bifrost/shopify-connector#280

## 2026-09-23 — FUSE-1222

Pass mapping dictionaries into sales-order translation

mapToCanonical now passes the resolved mapping dictionaries into both header and line applyTranslationRules calls, so lookup() works for Shopify customers. Dictionaries already survive remote-config and the provider schema on types 10.3.0; rules-engine 2.1.0 was already on main. Unknown dictionary fails that order via the existing create_data_failure path with the dictionary name logged. Verified end-to-end on dev against the ILG Test Store.

PR: gfs-bifrost/shopify-connector#279

## 2026-09-23 — Fix shopify-app browserslist advisories, renew deepmerge-ts allowlist

Fix shopify-app browserslist advisories, renew deepmerge-ts allowlist

Out-of-ticket CI hygiene: the DevSecOps audit went red on main and every open PR because all three apps/shopify-app/audit-ci.jsonc allowlist entries expired 2026-09-23 (the audit summary still labels expired entries "allowlisted", so it reads as 0 findings and fails anyway). browserslist GHSA-c83g-rgw3-j3cx / GHSA-73wf-gq98-2v4g fixed via lockfile update to 4.29.0 (previously blocked by minimumReleaseAge). deepmerge-ts GHSA-ggr8-5vv4-36mx renewed 7 days: @prisma/config exact-pins 7.1.5, no reachable fix.

PR: gfs-bifrost/shopify-connector#275

## 2026-09-23 — Only adjust Shopify inventory for connectors with stock adjustments enabled

Only adjust Shopify inventory for connectors with stock adjustments enabled

Out-of-ticket (flag from FUSE-668; shared-topic move is FUSE-1182). Inventory is adjusted only on active stores whose connector has config.stockAdjustmentsEnabled: true; absent counts as off. Toggled off: no Shopify inventory write, no STOCK_ADJUSTMENT_MADE (SNAP row not cleared), info log + fuse.confirmation.unroutable reason:use_case_inactive. Mixed businesses adjust only the enabled stores. stockAdjustmentsEnabled now hydrated onto ShopifyConnectorConfig next to outboundTagsEnabled. Companion: fapi#144.

PR: gfs-bifrost/shopify-connector#274

## 2026-09-23 — FUSE-1252

Add write_orders to prod shopify-app scopes

Prod shopify-app deliberately lacked write_orders (PR #226), but SAIRA had outbound order-tagging enabled, so every orderUpdate tag write failed with an access-denied scope error and no reinstall could fix it. Added write_orders to the prod TOML and the Cloud Run SCOPES env (global.tfvars), matching dev, and documented the three scope surfaces (Partner dashboard first, then TOML and SCOPES) in CLAUDE.md.

PR: gfs-bifrost/shopify-connector#278

## 2026-09-17 — FUSE-1228

Apply configured carrier mapping to confirmation tracking company

Goods Out Confirmations now honor a configured carrier mapping rule — a Header Mapping rule targeting `shipping.carrierId` (e.g. stripping an internal prefix via `substring(...)`) now overrides the carrier name shown as Shopify's fulfillment tracking company; previously it was silently ignored, so the raw carrier id was always used regardless of configuration. Tracking numbers remain untouched, still sourced from the despatch per FUSE-1068. The configured DSL expression is evaluated against the confirmation's own `shipping.carrierId` field via `@gfs-bifrost/rules-engine`'s `applyTranslationRules`, matching the field the Fuse UI's mapping editor exposes for the "From" side. Found triaging Purdy & Figg's (PURDYFIGG) report that Shopify tracking showed `GFS_EVRI` instead of their configured `EVRI`.

PR: gfs-bifrost/shopify-connector#268

## 2026-09-16 — FUSE-1059

Stamp goods_out_confirmation on the made side, stop legacy dual-publish

Shopify now stamps `goods_out_confirmation` (not `sales_order`) on the goods-out `confirmation_made` event, matching the `recordType` naming already used on ready and failure — both the cross-entity attribute (`app.module.ts`) and the confirmation flow's envelope `recordType` (via `Correlation`/`prepareMessage`) were aligned; create-side `sales_order` stamps (collector, failure publisher) were untouched. Once every made-side subscriber (snap-adapter, collector) could read the cross-entity topic, shopify-connector stopped dual-publishing made confirmations on the legacy per-entity topic — messages now publish once via the existing `crossEntityTopics` map entry, and the dead `SALES_ORDER_CONFIRMATION_READY` topics-map registration (never actually published) was removed along with its env vars, config, and IAM wiring.

PR: gfs-bifrost/shopify-connector#258
PR: gfs-bifrost/shopify-connector#267

## 2026-09-07 — FUSE-1057

Route confirmations to the originating Shopify connector, filter by source/broadcast

A confirmation now goes only to the connector its order arrived through, rather than being attempted against every active, mapping-configured Shopify connector — previously a customer with more than one storefront saw each confirmation land on all of them. No `connectorId` or `broadcast=true` still fans out to all connectors, so single-connector customers are unchanged. A named Shopify connector that can't receive a confirmation (inactive or unmapped) now publishes to the new `confirmation_data_failure` topic (`business_rule`/`connector_unresolvable`) for replay, instead of being silently mis-delivered. Foreign-channel confirmations were initially just skipped and counted via a new `source_mismatch` monitor (added in the `observability` repo, not here) to measure real volume before failing them; once the monitor confirmed prod volume and snap-adapter's `source`/`broadcast` attribute stamping reached prod, the `confirmation_ready` subscription was widened to filter on `source`/`broadcast` as well as `recordType`, and a `connectorId` naming a connector on another channel now also publishes a `confirmation_data_failure` instead of skipping silently.

PR: gfs-bifrost/shopify-connector#239
PR: gfs-bifrost/shopify-connector#254

## 2026-08-24 — FUSE-1078

Retry Shopify GraphQL throttles instead of failing the order; allowlist js-yaml + nanoid advisories

Shopify signals a cost-based throttle as HTTP 200 with a `THROTTLED` entry in the GraphQL `errors` array, not a 429 — a status-code predicate never sees it, and the SDK's own retry only covers 429/503, so `GRAPHQL_REQUEST_RETRIES` stays `0`. Added a throttle classifier that reads the response body for both the 200+`THROTTLED` and 429 shapes, and a retry loop around GraphQL requests (`GRAPHQL_THROTTLE_MAX_RETRIES=2`, `THROTTLE_MAX_WAIT_MS=5s`, equal-jitter backoff) computed from Shopify's own points-deficit-over-restore-rate, falling back to `Retry-After` then backoff. Mutations (`mutate()`) gained the same cost extraction, logging and classification query() already had — dev's largest throttle episode to date was entirely on the mutation side. Added `graphql.throttled`/`graphql.retry` metrics; a monitor is deliberately deferred until real values are observed. Fixed against prod SAIRA being continuously throttled since 2026-08-18 with nothing alerting on it.

Also allowlisted two HIGH dependency advisories blocking DevSecOps fleet-wide: `GHSA-5p4m-2wfm-xmqj` (js-yaml, no patched 4.x release exists, arrives transitively via `dd-trace`'s wasm rewriter which parses only trusted internal YAML) and `GHSA-2v37-7h3g-55p8` (nanoid, patched upstream but only reachable as a build-time transitive of postcss with fixed internal sizes).

PR: gfs-bifrost/shopify-connector#197
PR: gfs-bifrost/shopify-connector#230

## 2026-08-10 — FUSE-785

Fulfil kit orders by role, cut over to confirmation_ready

Kit orders now fulfil instead of looping. SNAP explodes a kit's bill-of-materials onto the despatch, and only the ordered line carries a Shopify reference — the handler previously threw on the first component line, was swallowed, and left `confirmation_made` never published, the OBQ never cleared, and SNAP re-announcing indefinitely (~29h on PURDYFIGG, 04-05 Aug). It now drops `role: kit_component` lines before id resolution and fulfils the ordered line with its own quantity, logging the exclusion at debug; a `standard` line with no fulfillment reference still throws, as does a confirmation with nothing fulfillable. Cut over the subscription to `confirmation_ready` filtered on `attributes.recordType = "goods_out_confirmation"`, removing the legacy `sales_order_confirmation_ready` subscription in the same change to avoid double-processing. Bumped `@gfs-bifrost/types` `^8.2.0` → `^9.0.0`, which requires `role` on every line (producer side: snap-adapter #169, dev-deployed; prod gated on the poller's prod run).

PR: gfs-bifrost/shopify-connector#194

## 2026-07-17 — FUSE-991

Dual-publish sales_order to create_record_request (switchover-prep)

Switchover-prep: `sales_order` now dual-publishes to the central `create_record_request` topic (with `attributes.recordType = "sales_order"`) alongside its legacy per-entity topic, using the same canonical envelope — routing only, priming the cross-entity cutover with nothing yet consuming the copy. Added the `PUBSUB_TOPIC_ID_CREATE_RECORD_REQUEST` env var and a `roles/pubsub.publisher` IAM grant on the shared topic, mirroring the existing `create_sales_order_request` wiring. No ingest capture (`ShopifyCapture.rawPayload`) yet — the raw order payload is discarded after canonicalisation today; deferred to a follow-up. One of a 4-PR FUSE-991 set opened together across the connectors.

PR: gfs-bifrost/shopify-connector#167

## 2026-07-02 — FUSE-794

Traceability metadata (requestor block, source, connectorId/recordType/recordId) on egress

Logs now carry full request context — the `requestor` block spreads `businessId`/`connectorId`/`shopName`/`flow`/`recordType`/`recordId`, and `integration:shopify` rides every log line. Shopify order identifiers were added to collector failure lines so support can trace an order by the customer's own reference or the Shopify order number. Outbound message metadata is stamped `source: "shopify"` (the integration, not the service name — sftp-connector still stamps its service name, noted as a follow-up). Raw-payload and happy-path log dumps were removed, misnamed routine token-lifecycle logs re-levelled off error/warn, customer-facing failures tagged `audience:support`, and the Cloud Run liveness probe / scheduled poll excluded from the request access log. The local `EventMetadata` fork was collapsed onto the shared `@gfs-bifrost/types` `BifrostMessageMetadata` (bumped `^5.6.0` → `^6.3.0`), and `connectorId`/`recordType`/`recordId` are now lifted from the correlation namespace onto every published envelope.

PR: gfs-bifrost/shopify-connector#151
PR: gfs-bifrost/shopify-connector#152
PR: gfs-bifrost/shopify-connector#153
PR: gfs-bifrost/shopify-connector#161

## 2026-06-17 — FUSE-952

Skip inactive Shopify connectors when polling

Scheduled and manual polls now skip inactive Shopify connectors — `ShopifySalesOrderService.collect()` polls only connectors whose ingress `isActive` is `active`; `inactive`/`pending`/`failed`/unset are skipped. Previously every connector returned by `getAll()`/`getByBusinessId()` was polled, so deliberately-disabled stores were hit on every cycle, burning Shopify API quota. Confirmations, order-tagging and stock-adjustment paths were unaffected — they already excluded inactive connectors. Added a debug log (`Skipping inactive connectors during poll`) reporting skipped/active counts. `isActive: boolean` was made a required field on `ShopifyConnectorConfig` so a forgotten field can't silently disable polling.

PR: gfs-bifrost/shopify-connector#148

## 2026-06-11 — FUSE-953

Replace VPC connector + NAT with Direct VPC egress

Cloud Run now uses Direct VPC egress (network_interfaces on the existing subnet) instead of a Serverless VPC Access connector, keeping private-range reachability to Redis at zero fixed cost. Egress switched from `ALL_TRAFFIC` to `PRIVATE_RANGES_ONLY` so public calls (Shopify API, Pub/Sub, Datadog) leave via Cloud Run's managed egress instead of being hairpinned through the VPC. Cloud Router, NAT gateway, and the VPC connector were deleted from the networking module (fixed-cost resources billed 24/7); VPC and subnet remain since Redis `authorized_network` and direct egress both need them. Preview envs now share dev's VPC/subnet instead of dev's connector. Also fixed a drive-by crash in `salesOrderFailureHandler` (`TypeError` reading `.id` on a failure record with no `identifiers`), which with no DLQ had been redelivering indefinitely.

PR: gfs-bifrost/shopify-connector#140

## 2026-06-05 — FUSE-944

Tag fulfilled orders with ILG_FULFILLED, modelled as an explicit state machine

Shopify orders are now tagged `ILG_FULFILLED` when ILG fulfils or partially fulfils them, fired after a fulfillment is successfully created during sales-order confirmation processing (fire-and-forget — tag failures are logged and metered, never affect confirmation processing). The per-connector `outboundTagsEnabled` gate (FUSE-883) applies automatically. The outbound tag state machine is now explicit code — `core/shopify/order-tags.ts` declares `(start | ILG_ERRORED) ⇄ ILG_RECEIVED → ILG_FULFILLED` as a transition table plus one pure function (`transitionOrderTags`), replacing the old implicit `REPLACEABLE_ORDER_TAGS` filter. `ILG_FULFILLED` is now terminal — later ack/failure events can no longer add `ILG_RECEIVED`/`ILG_ERRORED` alongside it. No-op transitions skip the Shopify write, so replays and repeated confirmations no longer burn an `orderUpdate` mutation. `IOrderTaggingService.replaceTags*` renamed to `applyTag*` to match the new mechanism.

PR: gfs-bifrost/shopify-connector#134
PR: gfs-bifrost/shopify-connector#135

## 2026-06-04 — FUSE-883

Gate outbound tagging on connector outboundTagsEnabled flag

Outbound order tagging is now opt-in per connector — `ILG_RECEIVED`/`ILG_ERRORED` tags are only written to stores whose connector has `outboundTagsEnabled: true`; absent or `false` means disabled, and skipped connectors emit a structured info log rather than an error. Removed `FEATURE_FLAG_UPDATE_ORDER_TAGS` entirely (config schema, `FeatureFlags`, env samples, IaC). Bumped `@gfs-bifrost/types` `^3.0.1` → `^4.3.0` so the flag survives `ConnectorDTOSchema` validation inside `remote-config` (pkg-node#111) — verified the field was previously silently stripped on the older version. Added a `ShopifyOrderTaggingService` spec covering the opt-in/opt-out/mixed-business branches and an integration test for the disabled path.

PR: gfs-bifrost/shopify-connector#129
PR: gfs-bifrost/shopify-connector#131

## 2026-05-11 — FUSE-800

Subscribe and ack use-case acknowledgement

Plumbing pre-work for outbound Shopify tags (epic FUSE-723, unblocks FUSE-802) — no business logic yet, tagging lands in a later ticket. Added `AcknowledgementEventsController` at `POST /events/acknowledgements/sales-order`, validating the inbound `BifrostMessage<CanonicalSalesOrder>` envelope, setting the correlation id, logging the acknowledgement, and returning `202 Accepted`. Subscribed the connector to the cross-entity `create_acknowledge` topic via a Pub/Sub attribute filter (`attributes.use_case = "sales_order"`) so master-data and purchase-order traffic on the same topic is dropped at the broker. No publisher exists for `create_acknowledge` yet, so the subscription sits idle until one lands.

PR: gfs-bifrost/shopify-connector#103

## 2026-05-07 — FUSE-801

Subscribe and ack use-case failure

Plumbing pre-work for outbound Shopify tags (epic FUSE-723), mirroring FUSE-800 on the failure side of the use-case state machine — no business logic yet, the next ticket applies the `ILG_ERRORED` tag. Added `FailureEventsController` at `POST /events/failures/sales-order`, validating the inbound `BifrostMessage<CanonicalSalesOrder>` envelope, setting the correlation id, logging the failure, and returning `202 Accepted`. Subscribed the connector to the cross-entity `create_data_failure` topic via a Pub/Sub attribute filter (`attributes.use_case = "sales_order"`) so other record types on the topic are dropped at the broker. No publisher exists for `create_data_failure` yet, so the subscription sits idle until one lands.

PR: gfs-bifrost/shopify-connector#105

## 2026-03-19 — FUSE-666

Handler for stock adjustment ready events

Added a Pub/Sub subscription for the stock adjustment ready event. Moved confirmations onto their own controller and added an interface for the namespace service.

PR: gfs-bifrost/shopify-connector#59

## 2026-01-23 — FUSE-387

Listen for apropos config

Wired up listening for config events covering SKU blacklisting, warehouse routing, connectors, and connector mappings (DDP rules not yet covered — no events implemented for those).

PR: gfs-bifrost/shopify-connector#37

## 2026-01-20 — FUSE-377

Subscribe to events

Subscribed the connector to events.

PR: gfs-bifrost/shopify-connector#33

## 2026-01-05 — FUSE-551

Import DDP package

Introduced the DDP package and linked DDP rules to a connector (connectors introduced in a basic form, with connector IDs matching the business ID for now). Also migrated the package manager to pnpm, aligning with the rest of the Fuse services, and renamed the poller to collector (plus related method names) to better clarify the domain.

PR: gfs-bifrost/shopify-connector#26

## 2025-11-12 — FUSE-435

Adds shopify-to-canonical mapping

Moved the DSL in from sftp-connector and added `flatten` support so arrays can be referenced as variables. Added the base sales order transformer and mapping rules, imported the Shopify GraphQL schema for reference, and imported supporting types. First pass — mappings expected to change and evolve as this is tested further.

PR: gfs-bifrost/shopify-connector#19

## 2025-10-29 — FUSE-373

Emit Shopify sales orders to Event Bus

Implemented Shopify polling to retrieve sales orders from multiple stores and publish them to a dedicated Pub/Sub topic. Introduced `PubsubModule` for managing Pub/Sub connections and message publishing, and a new `EventsController` handling Shopify polling and sales order confirmation events (merging the former `ConfirmationsController` and `ShopifyPollController`). Configured Pub/Sub topics and subscriptions via Terraform and added a Cloud Scheduler job to trigger the poll. Added a feature flag to control entity event emission.

PR: gfs-bifrost/shopify-connector#14
