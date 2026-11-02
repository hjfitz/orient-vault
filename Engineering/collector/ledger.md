---
tags: [waypoint, ledger]
title: collector — work ledger
---
# collector — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-09-24 — FUSE-1257

Connector-aware confirmation lifecycle: delivered shows processed

failed was terminal, so a redriven or re-polled confirmation stayed Failed in Transaction History forever. Confirmation failures now record their connector in lifecycle.failedConnectorIds ("" when none named); confirmation_made clears its own connector plus "" via Collection.recordDelivery (service markDelivered), flipping failed -> processed only once the list is empty — same rule as replay-service's clear-down, so a partial broadcast stays Failed until the failing connector delivers. Legacy failed records (no list) clear on any delivery. The poller's no_originating_connector notice is ignored. failedConnectorIds is served on /api/v1/records lifecycle. Create-side lifecycle and stock adjustments unchanged.

PR: gfs-bifrost/collector#114

## 2026-09-23 — FUSE-1238

Exclude snap-adapter clear-down failures from WOC/FGR failure subscriptions

The WOC/FGR confirmation_data_failure subscriptions now exclude source=snap-adapter, matching goods-in/out and stock adjustments. snap-adapter's OBQ clear-down failures come after delivery, and failed is terminal. Terraform-only; the filter change replaces both subscriptions. Prod held no WOC/FGR records, so this is preventative.

PR: gfs-bifrost/collector#111

## 2026-09-23 — FUSE-1239

Serve pick, pack, WOC and FGR confirmations on api/v1/records

PR D (wraps in FUSE-1207's backend half): pick/pack/WOC/FGR resolve on the v1 list + single-record routes (confirmation registry, identifiers.businessId), each with the {businessId, deletedAt, lifecycle.createdAt} list index plus the search index family (21 indexes). Pick/pack refs live under identifiers.*, not order.* (poller mapping). No lifecycle backfill needed. Stack merged up with master #107 first. Dev-verified 12/12 lookups on GADG.

PR: gfs-bifrost/collector#110

## 2026-09-23 — FUSE-1239

Declare reference-search fields for every served record type

PR C: goods-in/out, PO, WO, RGA, stock adjustment and master data declare their Order Ref equivalents plus Record ID fields (first-required-identifier rule on fuse-ui's refPaths), 17 new indexes, served-types guard test. Every collection proven sorted-merge + 0-doc count on 7.0/8.0; dev-verified 21/21 field lookups on GADG.

PR: gfs-bifrost/collector#109

## 2026-09-23 — FUSE-1239

Add ?reference= search to the v1 records list route

PR B: ?reference= exact-matches one value against the type's declared fields, correlation id on every type, and _id for 24-hex values; a leading # ignored both ways as separate $or branches (a two-value $in lost the sorted merge + index-only count on 7.0). ReferenceSearchPipe 400s anything but one plain string (Express 4 extended parser makes ?reference[$ne]=x an operator). v1 responses carry correlationId; legacy routes unchanged. Prod approval waits for fuse-ui#262 in prod. Dev-verified on GADG.

PR: gfs-bifrost/collector#108

## 2026-09-23 — FUSE-1239

Add index-covered reference-search indexes and branch query

PR A of the Transaction History reference search: one {businessKey, path, deletedAt, lifecycle.createdAt, _id} index per searchable path (sales_order customerRef/customer.order/salesOrder + metadata.correlationId on all 8 v1-served collections) and Collection.findAnyPaginatedWithLifecycle, which puts deletedAt:null inside each $or branch — the wrapped $and form fetches every match to count a shared correlation id. No route change; ensure:indexes script kept as optional tooling (prod builds at boot). explain() spec proves sorted-merge find + 0-doc count on Mongo 7.0 and 8.0. Plan: [[FUSE-1239-multi-field-reference-search-on-the-v1-records-a]].

PR: gfs-bifrost/collector#106

## 2026-09-23 — Capture lifecycle status for stock adjustments

Capture lifecycle status for stock adjustments

Out-of-ticket (EM, out of sprint). Stock adjustments were the only confirmation type with no lifecycle status: delivery was recorded only as confirmedAt, so Transaction History showed them all as No status. stock_adjustment_made now advances status to processed. A dedicated confirmation/failure/stock_adjustment route (with a confirmation_data_failure sub excluding snap-adapter) marks delivery failures failed, reusing #105's parsing. backfill:stock-adjustment-status fixes already-confirmed adjustments (676 on dev); prod needs it run after deploy.

PR: gfs-bifrost/collector#107

## 2026-09-23 — FUSE-1238

Mark goods-in/out confirmations failed when delivery fails

Goods-in/out confirmations whose delivery failed stayed at no status: collector had no confirmation_data_failure subscription for them and the PO/SO confirmation services had no markFailed. Added both, excluding source=snap-adapter (its OBQ clear-down failures come after delivery, and failed is terminal). The failure handler now accepts sftp-connector's bulk envelope and fapi's { confirmations: [...] } wrapper. The wrapper case was also silently dropping fapi WOC/FGR failures.

PR: gfs-bifrost/collector#105

## 2026-09-23 — FUSE-1238

Serve goods-in/out confirmations on api/v1/records

The records API now resolves goods_in_confirmation / goods_out_confirmation to the confirmation registry (registered under their create-side names purchase_order/sales_order), scoped by identifiers.bizId, so Transaction History can read ingest time and lifecycle status for confirmations. Pick/pack/WOC/FGR are deliberately not served yet because their collections lack a lifecycle.createdAt index.

PR: gfs-bifrost/collector#104

## 2026-09-15 — FUSE-1059

Accept goods-in/out made recordType on collector's made subs

collector's cross-entity confirmation_made subs for goods-in/out now accept goods_in_confirmation / goods_out_confirmation as well as purchase_order / sales_order — the made side moving onto the confirmation-naming principle the ready and failure sides already follow. The made handler resolves the push-path :recordType against the confirmation registry (keyed purchase_order / sales_order), so those subs keep their purchase_order / sales_order push path and registry lookup, and only their filter widens to accept the new wire value; the Terraform for_each set became a push-path-to-filter map to decouple the two. WOC/FGR subs are unchanged since their wire value already equals their registry key. Both wire values accepted so this doesn't depend on the made publishers' rename deploying first — nothing live changes since the cross-entity made PO/SO path is pre-prod. Pairs with the made publishers (fapi/sftp/shopify) switching to the new wire value and with snap-adapter's equivalent made-subs change. Follow-up: narrow to the new value only once the publishers are in prod.

PR: gfs-bifrost/collector#94

## 2026-08-20 — FUSE-1104

Pub/Sub exponential backoff on push subscriptions

Nacked deliveries now back off exponentially — retry_policy (10s to 600s) added on every subscription. Collector already nacked transient failures correctly (DatabaseError -> 500 via the exception filter), but with no retry_policy Pub/Sub redelivered immediately; during the 2026-08-12 load test that meant instant-retry pressure against a struggling Mongo. Behaviour-neutral on the happy path — only changes redelivery pacing on nack. Cloud Run concurrency/instance bounds (same unbounded defaults dedupe-service had) deliberately left to a follow-up ticket.

PR: gfs-bifrost/collector#80

## 2026-06-23 — FUSE-971

Persist record lifecycle metadata + api/v1/records read API

New read API GET /api/v1/records/{recordType}/{businessId} (paginated, newest-first) plus /{id} (single record by Mongo _id, scoped to the business) — returns records with their _id and lifecycle metadata. Foundation for the Customer Transaction History epic (FUSE-967). Every record now carries lifecycle: { createdAt, status }, written once at first ingest via $setOnInsert; createdAt derived from the envelope timestamp, status initialised null as the slot for FUSE-967's later status model. Existing read routes stay byte-identical — lifecycle is stripped from the legacy find/findPaginated paths; only the new api/v1 routes expose it. Also fixed stock-adjustment confirmedAt mis-stamping seconds-valued timestamps to 1970, via a shared toEpochDate helper that also backs lifecycle.createdAt. Added an idempotent backfill:lifecycle script to stamp lifecycle onto pre-existing documents (not yet run in any environment).

The single-record route keeps businessId in the path rather than as a query param, to preserve the approved route shape while keying on _id to sidestep the compound-key problem (PO is id+dueIn, stock-adjustment is id+lineId).

PR: gfs-bifrost/collector#49

## 2026-06-23 — FUSE-794

Bifrost metadata + logger traceability

Cross-service rollout, collector's slice (observer/consumer only — collector doesn't publish, so no producer work). Replaced the correlationId-only cls-hooked store with a CorrelationDetails object (correlationId, businessId, source, flow, recordType, recordId) plus getCorrelationDetails()/setCorrelationDetails(patch) merge semantics; getRequestId/setRequestId retained as thin wrappers so existing request-id middleware/interceptors keep working. The winston jsonLogFormat now spreads the full CorrelationDetails onto every log line under requestor instead of just correlationId, so logs can be filtered by businessId/source/flow/recordType. Every event handler lifts source=collector and a route-inferred flow (create/confirmation/release) after decode; single-record handlers also lift recordId/businessId from the canonical identifiers, while bulk handlers (stock_adjustment ready, confirmation) set only source/flow/recordType since there's no single recordId on a batch. Bumped @gfs-bifrost/types to ^6.3.0.

connectorId deferred — not in scope anywhere in collector's namespace and would need a new lookup.

PR: gfs-bifrost/collector#50

## 2026-06-16 — FUSE-952

Migrate Pub/Sub ingestion to @gfs-bifrost/pubsub

Pub/Sub ingestion now uses the shared @gfs-bifrost/pubsub package — PubSubIngestor is provided by EventModule and injected directly into the event controller; the hand-rolled decode/validate PubsubService and its duplicated envelope schemas were deleted. Decode/validation failures still ack (no Pub/Sub redelivery): AllExceptionsFilter maps the package's PubSubValidationError/PubSubDecodeError onto the same 204 responses it already produced for the app's own ValidationError/DecodeError. Correlation-id propagation preserved via the ingestor's onCorrelationId hook. Dropped the @google-cloud/pubsub dependency — collector only ingests over HTTP push and never publishes. Part of a 2-repo set on this migration alongside replay-service.

PR: gfs-bifrost/collector#46

## 2026-06-15 — FUSE-849

Persist RGA create_record events

RGA create_record events are now persisted — POST /events/v1/record/create/return_goods_authorization validates the record against CanonicalReturnGoodsAuthorizationSchema and saves it to a new return_goods_authorizations Mongo collection, replacing the FUSE-817 ack-only stub. return_goods_authorization is registered as a use case with the same registry/collection/service shape as sales_order — upserts on identifiers.id, indexed on businessId/id/deletedAt. Invalid payloads stay ack'd (204) via the shared AllExceptionsFilter mapping validation failures to 204 platform-wide, matching every other record type's anti-redelivery behaviour rather than the ticket's original "400 on bad payload" framing. No Terraform changes needed — the filtered create_record subscription and push endpoint already existed from FUSE-817.

PR: gfs-bifrost/collector#43

## 2026-06-11 — FUSE-953

Replace VPC connector + NAT with Direct VPC egress

Cloud Run now uses Direct VPC egress (network_interfaces on the existing subnet) instead of a Serverless VPC Access connector — same private-range reachability, zero fixed cost. Egress switched ALL_TRAFFIC to PRIVATE_RANGES_ONLY so public calls (Pub/Sub, Datadog, MongoDB Atlas) leave via Cloud Run's managed egress instead of being hairpinned through the VPC NAT. Cloud Router, NAT gateway, and the VPC connector — fixed-cost resources billed 24/7 — were deleted; VPC and subnet remain. Fleet rollout of the network lever piloted on dedupe-service; collector has no Redis and reaches MongoDB Atlas over a public connection string, so nothing actually uses the private path post-change, but the VPC/subnet are kept per the rollout pattern.

Known rollout-window effect: while Terraform applies, the old revision (still on connector + ALL_TRAFFIC) loses public egress when the NAT is destroyed, causing a brief run of 500s on the draining instance since Mongo is public; Pub/Sub push retries redelivered successfully against the new revision.

PR: gfs-bifrost/collector#39

## 2026-06-05 — FUSE-817

Events API hard-cut to /events/v1 action-first grammar

Events API hard-cut onto /events/v1 with the shared action-first grammar: POST /events/v1/record/request/:recordType, /record/release/:recordType, /confirmation/ready/:recordType, plus confirmation/ready/stock_adjustment and confirmation/made/stock_adjustment (mirroring the topics) and an RGA stub at record/create/return_goods_authorization. Legacy /event prefix and the old record-first shapes now 404. All 11 Terraform push endpoints moved. Route param renamed :useCaseName to :recordType (param surface only — the UseCaseName enum/registry and useCase log-field keys are untouched, left for a separately scoped rename PR). Added a new filtered subscription on the cross-entity create_record topic (recordType=return_goods_authorization) as an ack-only stub — nothing persisted yet, pending FUSE-849. Sibling PRs shipped the same grammar in dedupe-service (FUSE-814) and snap-adapter (FUSE-816).

Follow-up fix: the black-box test suite still posted to the removed /event/<type>/<action> shapes (CI was killed on the original PR so this didn't surface pre-merge) — updated to the new /events/v1 routes to clear the red black-box-tests workflow on master.

PR: gfs-bifrost/collector#36
PR: gfs-bifrost/collector#37

## 2026-06-04 — FUSE-676

Collect stock adjustments + fix flat-key upsert filters

Stock adjustments are now collected — stock_adjustment_ready (bulk) and stock_adjustment_made events land in a new stock_adjustments collection, upserted by identifiers.id + lineId. Made events derive a confirmedAt stamp from event metadata; ordering-safe both directions (a late ready can't demote a confirmed record, an early made still produces a complete one). New routes: GET /:businessId/stock_adjustment (paginated adjustment trail) and GET /:businessId/stock_adjustment/summary?sku= (per-SKU stock computed from confirmed adjustments only). Also fixed the OpenAPI schema transformer breaking on zod v4 enums (def.entries vs v3 def.values).

While implementing this, found and fixed a pre-existing bug affecting SalesOrderService, PurchaseOrderService, MasterDataService, and the confirmation services: upsert/soft-delete filters used "record."-prefixed keys that never match the flat stored document shape, so MongoDB materialised the filter fields into a junk record fragment on first insert. Dedupe worked by accident against that junk field, but it leaked into every API response, every event upsert hit an unindexed path (collection scan per event), and confirmation queries/indexes targeted the wrong field. Filters and indexes changed to the flat keys; legacy documents still dedupe correctly since the real flat fields were always written by $set, so no migration was needed.

PR: gfs-bifrost/collector#32
PR: gfs-bifrost/collector#33
PR: gfs-bifrost/collector#34
PR: gfs-bifrost/collector#35
