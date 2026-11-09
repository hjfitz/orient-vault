---
tags: [waypoint, ledger]
title: dedupe-service — work ledger
---
# dedupe-service — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-04 — Renew the zod and multer audit allowlist entries

Renew the zod and multer audit allowlist entries

The two allowlist entries expired 2026-11-04 and turned dependency_audit red on master and every open PR. Renewed 7 days after re-checking: no fixed zod 3.x, platform-express 11.x still pins multer 2.4.0.

PR: gfs-bifrost/dedupe-service#173

## 2026-10-28 — Tag create_record with each backend type the business has

Tag create_record with each backend type the business has

Delivery Backends B1. One <type>="true" attribute per backend type the business has (from config-service GET /business/{id} backends refs), in-process cache 60s fresh / 15min stale fallback, fail-closed nack before the duplicate-check save. Verified on dev with a temporary create_record subscription: HJF snap, Selector-only selector, none untagged.

PR: gfs-bifrost/dedupe-service#169

## 2026-10-28 — Clear the dependency audit and image scan

Clear the dependency audit and image scan

Lockfile bumps for follow-redirects 1.16.2 and body-parser 1.20.9/2.4.0; zod 3 and multer allowlisted for 7 days (no compatible fix); .trivyignore's npm-CLI entries removed since node24-runtime ships no npm. Red on master since 2026-10-26.

PR: gfs-bifrost/dedupe-service#168

## 2026-10-28 — Run on the node24-runtime golden image

Run on the node24-runtime golden image

Node canary for ilg-platform golden images: node24-runtime:0.1-affogato, Datadog in-container (sidecar + shared volume dropped), observability ^2.4.0, enableShutdownHooks so SIGTERM drains instead of killing in-flight requests.

PR: gfs-bifrost/dedupe-service#167

## 2026-10-01 — Clear high dependency advisories blocking audit and image scan

Clear high dependency advisories blocking audit and image scan

axios ^1.20.0, brace-expansion and grpc-js overrides raised, three .trivyignore entries for the node:24 base image's bundled npm. Unblocked Renovate #155 (types 10.8.0). Opened by renovate-clear during the morning digest.

PR: gfs-bifrost/dedupe-service#156

## 2026-08-20 — FUSE-1104

Mongo retries, explicit timeouts, truthful health; Pub/Sub backoff + bounded Cloud Run scaling

Transient Mongo failures now retry with backoff via a cockatiel policy scoped to network/pool-cleared/server-selection/retryable-write/E11000 concurrent-upsert errors; permanent errors pass straight through. New metric dedupe_service.mongo.retry. Explicit MongoClient timeouts and pool sizing (new MONGODB_* env vars) replace the driver defaults that left sockets waiting indefinitely and hung release requests during the 2026-08-12 load test; server selection now fails in 5s instead of 30s.

Health status stops lying: server-heartbeat events un-latch the connection status, which had previously held "UP" forever after the first boot connect — the root cause of the incident running ~9 minutes with a dead Mongo and a green health check. New metric dedupe_service.mongo.heartbeat_failed. /health/liveness is now process-health only; new /health/readiness returns 503 while Mongo is down, for monitors/traffic gating.

Nacked deliveries now back off exponentially (retry_policy 10s -> 600s on all 14 push subscriptions) instead of redelivering immediately; ack deadline raised 20s -> 60s for headroom. Cloud Run bounded to 5 instances x 40 concurrent requests with explicit 1Gi/1CPU limits and a 60s request timeout, replacing the unbounded defaults that OOM-looped the service during the load test.

First two slices of the 4-PR FUSE-1104 sequence; redelivery idempotency and process-then-ack followed under FUSE-1078 (#121/#122).

PR: gfs-bifrost/dedupe-service#118
PR: gfs-bifrost/dedupe-service#120

## 2026-08-17 — FUSE-1078

Redeliveries forward instead of holding; ack only after the create push succeeds

A Pub/Sub redelivery now forwards instead of being held as a duplicate: the gate holds only when an identical record arrives under a new correlationId (a genuine customer resend) — a same-correlationId redelivery of the last sighting now forwards. Without this, once the service started nacking on failure, a record whose forward publish had failed would redeliver, be read as identical, and get stuck held-but-never-forwarded. Hold bookkeeping was also made non-fatal: a failed recordDuplicateHold logs and increments a metric instead of throwing, since the gate write has already stamped the duplicate's correlationId by that point.

The create gate now acks only after the work is done, instead of acking as its first statement — the FUSE-1104 fix for the incident where every downstream failure after that early ack was silently lost (~54k records in the 2026-08-12 dev load test). Transient failures (Mongo, forward-publish, unknown errors) now nack with a 503 so Pub/Sub redelivers with backoff; permanent payload failures (Zod/decode/validation) still ack-and-drop. New metrics dedupe_service.event.nacked and dedupe_service.event.dropped_permanent. No delivery-attempt budget or DLQ by design — nack-with-backoff bounded by message retention is the intended shape, mirroring the team's app-retry-over-DLQ stance.

Third and fourth slices of the 4-PR FUSE-1104 hardening stack (infra backoff #118, Mongo retries/health #120, this pair).

PR: gfs-bifrost/dedupe-service#121
PR: gfs-bifrost/dedupe-service#122

## 2026-07-28 — FUSE-633

Dedupe and forward work order create requests

New work order use case: a filtered Pub/Sub push subscription on the cross-entity create_record_request topic (attributes.recordType = "work_order") dedupes and gatekeeps work order create requests, mirroring the existing return-goods-authorization flow. New create_work_order Mongo collection, keyed on identifiers.id + identifiers.businessId; identical resends are held, new or changed records forward to the shared create_record topic tagged recordType=work_order.

SKU blacklist applies to work order lines the same way it does for the other three record types. Record admin API (/api/v1/record/work_order) came along for free, since the admin surface is generic over registered record types. New filtered create_record_request push subscription for work_order in Terraform (dev + prod).

No release/failure wiring for work_order at this point — the ticket's ACs didn't ask for RGA's create_data_failure-driven release path (FUSE-847) to be extended to work orders, so this PR is forward-only.

PR: gfs-bifrost/dedupe-service#95

## 2026-07-16 — FUSE-991

Preserve ingest capture through dedupe; dual-publish SO/PO/MD to create_record

Ingest capture now survives the dedupe gate: handleCreateRequest decodes the create-request envelope with BifrostCreateRequestSchema and forwards metadata.capture unchanged, instead of the previous BifrostMessageSchema decode which silently stripped it. Covers all four record types. A malformed capture degrades to no-capture rather than dropping the record; only a genuinely invalid envelope still throws.

SO/PO/MD now also publish to the central create_record topic (recordType-tagged) alongside their legacy per-entity create_* topics, via registerMultiple — switchover prep; RGA already published to create_record only. No subscription changes yet, so the create_record copies for SO/PO/MD have no consumer. Release / config-revision paths unchanged, still decode with BifrostMessageSchema and carry no capture.

One of a 4-PR FUSE-991 set (sftp / dedupe / fapi / shopify), opened together.

PR: gfs-bifrost/dedupe-service#76

## 2026-07-09 — FUSE-1000

Migrate test suite from Jest to Vitest

Test runner swapped Jest -> Vitest: pnpm test now runs vitest run; jest.config.ts/jest.setup.ts replaced by vitest.config.ts/vitest.setup.ts. Test tooling only, no source/runtime behaviour change. Dropped jest, @jest/globals, @types/jest, babel-jest, @babel/*, ts-node; added vitest + @vitest/coverage-v8.

All 13 spec files plus the express fixture ported to Vitest APIs (jest.* -> vi.*, jest.requireActual -> an async vi.importActual factory). One test-mock fix was needed with no production code touched: under Vitest, new vi.fn(() => obj)() returns the constructed instance rather than the impl's object, so cache.service.spec's NetworkCacheBuilder mock was changed to a class mock so the builder methods survive new.

PR: gfs-bifrost/dedupe-service#71

## 2026-06-25 — FUSE-847

Clear dedupe entries for all record types off create_data_failure

sales_order, purchase_order and master_data joined RGA (FUSE-818) in having create_data_failure clear their dedupe gate, so a permanently-failed record can be safely retried/replayed.

Added a dedicated v2 release route for the failure contract: POST /events/v2/record/release/:recordType handles BifrostMessage<BifrostFailure> (canonical nested at failure.record), distinct from the v1 release_* shape (canonical at the top level) — the route, not subscription-name sniffing, selects the contract. Also fixed the RGA path from FUSE-818, which had the same latent unwrap mismatch.

Four create_data_failure subscriptions (RGA + one per type), each filtered on attributes.recordType, push to the new v2 route; release_* subscriptions stayed on v1 for SO/PO/MD as an interim redundant clear — step 1 of the FUSE-978 consolidation that later retires release_*.

PR: gfs-bifrost/dedupe-service#65

## 2026-06-23 — FUSE-794

Bifrost metadata + logger traceability

Bumped @gfs-bifrost/types to ^6.3.0 for the optional source/connectorId/recordId/recordType fields on BifrostMessageMetadata. The outbound create_record envelope metadata is now enriched: inbound metadata is preserved verbatim, and only genuinely-absent fields are defaulted (source falls back to "dedupe-service", recordId falls back to the existing per-type extractRecordId).

connectorId deliberately left unpopulated — not available in the dedupe gate without a new network call or a cache-contract change. Inbound source/recordId weren't yet surfaced through @gfs-bifrost/pubsub's BifrostMessageSchema at this point (its metadata schema was still the narrow 3-field shape and stripped them on decode), so the producer took the default branch until pubsub's schema later widened.

PR: gfs-bifrost/dedupe-service#62

## 2026-06-16 — FUSE-920

Strip blacklisted SKU lines instead of dropping whole orders

Blacklisted lines are now stripped from an order rather than dropping the whole order; an order is dropped only when every line is blacklisted (master_data stays all-or-nothing, being a single product). IDeduper.isSkuBlacklisted(): boolean replaced with applySkuBlacklist(): SkuBlacklistResult ({record, removedSkus, fullyBlacklisted}) across all four dedupers — the controller forwards the slimmed record but dedupes/persists the original record so identical replays stay held.

New metric dedupe-service.sku.lines_removed per recordType for partial strips; sku.blacklisted still fires on a full drop.

Also fixed a CI issue in the same PR: granted packages: read to the docker-build-push jobs in both deploy workflows. Every dedupe-service deploy had been hitting startup_failure since the ilg-platform/github-actions@0.1-affogato tag was force-moved to require that permission.

PR: gfs-bifrost/dedupe-service#55

## 2026-06-15 — FUSE-818

Clear RGA dedupe entries off create_data_failure

RGA dedupe entries now clear off create_data_failure via a filtered subscription (attributes.recordType = return_goods_authorization) driving the deduper's existing release stage, rather than adding a new grammar stage — RGA has no release_* topic and release already means "remove the dedupe entry" regardless of trigger. The release metric is tagged source=release|failure so failure-driven clears stay distinguishable from the normal release path.

return_goods_authorization added to releaseRecordTypes so the existing postRelease handler accepts it. Wired but inert for RGA at this point: release()/doesExist were still stubs, so it acked without clearing until the RGA dedupe store landed in FUSE-815.

PR: gfs-bifrost/dedupe-service#47

## 2026-06-12 — FUSE-815

Dedupe and gatekeep RGA records onto create_record

RGA create requests are now gatekept for real: the FUSE-814 stub held every record; fresh or changed RGA records are promoted to the cross-entity create_record topic, identical redeliveries are dropped. Promoted messages carry attributes.recordType = "return_goods_authorization", the attribute downstream subscription filters discriminate on.

RGA records are validated at the boundary against CanonicalReturnGoodsAuthorizationSchema; invalid records are acked and logged, never forwarded. New Mongo collection create_return_goods_authorization, deduped on identifiers.id + identifiers.businessId, mirroring the sales-order pattern. SKU blacklist now applies to RGA lines, consistent with the other record types.

PR: gfs-bifrost/dedupe-service#51

## 2026-06-10 — FUSE-953

Replace VPC connector + NAT with Direct VPC egress

Cloud Run switched to Direct VPC egress (network_interfaces on the existing subnet) instead of a Serverless VPC Access connector, keeping private-range reachability to Redis at zero fixed cost. Egress mode changed ALL_TRAFFIC -> PRIVATE_RANGES_ONLY, so public calls (Pub/Sub, Datadog intake, config-service) now leave via Cloud Run's managed egress instead of being hairpinned through the VPC.

Cloud Router, the NAT gateway and the VPC connector were deleted as unneeded fixed-cost resources billed 24/7; VPC/subnet remain for Redis's authorized_network and the direct egress attachment.

Pilot for the same network change across the rest of the fleet (collector, replay, snap-adapter, snap-queue-polling-service, fapi, fuse-ui); sftp-connector (and possibly shopify-connector) keep a NAT for static-IP allowlists.

PR: gfs-bifrost/dedupe-service#49

## 2026-06-05 — FUSE-814

Hard-cut to /events/v1 record routes; RGA ack-only subscription stub

Consolidated the request/release routes onto one vocabulary: POST /events/v1/record/request/:recordType and POST /events/v1/record/release/:recordType (recordType in sales_order/purchase_order/master_data/return_goods_authorization), replacing the legacy /event mount as a hard cut — no DLQ on these subs, so a deploy-window push just retries.

DedupeRouter now holds one registration per record type instead of two (create_X/release_X). New filtered subscription on the cross-entity create_record_request topic (recordType=return_goods_authorization) pushes to the same request route; the RGA gatekeeper is a stub that holds every record until FUSE-815 lands. Metric/log type tags changed value (create_sales_order -> sales_order) to align with the platform recordType vocabulary, so Datadog facets/monitors pinned to the old values needed updating.

PR: gfs-bifrost/dedupe-service#46

## 2026-01-09 — FUSE-573

Cache for the deduper

Added a cache layer to the dedupe lookup path.

PR: gfs-bifrost/dedupe-service#16

## 2025-12-01 — FUSE-328

Point service to both Datadog tenants

Dedupe-service dual-ships metrics and logs to both the GFS and ILG Datadog tenants. Adds the hot-shots dependency for multi-region metrics broadcasting, two Datadog sidecar containers on Cloud Run (one per tenant), separate per-tenant log files in the logger, and separate Datadog API keys threaded through Terraform variables and the deploy/on-push/tf-output workflows. Biome bumped to v2.3.8 alongside.

PR: gfs-bifrost/dedupe-service#14
