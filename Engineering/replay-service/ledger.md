---
tags: [waypoint, ledger]
title: replay-service — work ledger
---
# replay-service — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-10-19 — FUSE-1319

Place Snap outages at Snap

New failure point `create.snap_unavailable`: wms_submission + first error infrastructure, `service: snap`, code ending `.redelivery_exhausted`. TS derivation and Mongo `$switch` both updated; the parity fixture covers the Snap and Firestore exhausted shapes (Firestore stays `create.snap_adapter_internal`). fuse-ui's label PR must follow this to prod — its "Failed at Snap" filter sends the new key and an older replay 400s.

PR: gfs-bifrost/replay-service#125

## 2026-10-19 — Show where each failure happened in the Retry Queue

Show where each failure happened in the Retry Queue

Ship: SHIP-1019-retry-queue-failure-point. Read-time failurePoint (create.* / confirmation.*) on list + detail with filter and groupBy; /groups honours every list filter; failures with no record business fall back to metadata.customer; a reviewed survey/plan/apply/revert script for existing "" rows (prod apply gated on Harry). Defects split out: FUSE-1318..1322.

PR: gfs-bifrost/replay-service#119
PR: gfs-bifrost/replay-service#121
PR: gfs-bifrost/replay-service#122
PR: gfs-bifrost/replay-service#123

## 2026-10-05 — Notify on dev deploy success in manual-deploy

Notify on dev deploy success in manual-deploy

terraform-apply-dev in manual-deploy now sets notify_on_success, so dev branch deploys are announced by the workflow (message shows the branch). Canary for the github-actions notification change. Draft.

PR: gfs-bifrost/replay-service#107

## 2026-09-30 — Clear red DevSecOps scans (30 Sep CVE batch)

Clear red DevSecOps scans (30 Sep CVE batch)

Raised the brace-expansion override floor to >=5.0.12 (lockfile-only) to clear dependency_audit and the app-tree image finding, and added .trivyignore entries for the npm/pnpm-bundled brace-expansion and undici in the base image (no patched npm yet). Unblocks #103; main's scheduled scan was also red.

PR: gfs-bifrost/replay-service#104

## 2026-09-29 — FUSE-1238

Let an operator set where a confirmation redrive goes

PATCH /failures/:id now takes routing ({ source: rest|sftp|shopify, connectorId? }, or null to clear) for confirmation failures. It replaces the channel that failed on redrive and is recorded in editHistory. GET /:id shows routing and redriveRouting, and a confirmation with nowhere to go is replayable: false with a routing blocking issue, which matches #102's redrive gate. This lets the poller's unroutable/no-originating-connector failures be pointed at a real connector. Verified in dev: a poller notice routed to a rest connector reached fapi only, and clear and invalid-input paths behaved as expected. Stacked on #102. Poller Clear-Down unit B2.

PR: gfs-bifrost/replay-service#103

## 2026-09-29 — FUSE-1238

Redrive a confirmation back to the connector that failed

Confirmation redrives to confirmation_ready carried only attributes.recordType. Every connector subscription except RGA also requires source or broadcast, so redriven pick, pack, goods-in, goods-out, WOC and FGR confirmations reached only the collector while replay history said success. The redrive now stamps attributes.source from the failure's own source (rest/sftp/shopify) and sets metadata.connectorId to the failed connector. It never broadcasts, and failures with no delivery channel (snap-adapter clear-down, the poller's notice) are refused with a 400. Verified in dev: a rest pick redrive reached fapi only and fapi retried the named connector. Poller Clear-Down programme unit B1.

PR: gfs-bifrost/replay-service#102

## 2026-09-24 — FUSE-1257

Clear Retry Queue entries once a confirmation is delivered

The confirmation_made clear-down had never cleared anything: it only accepted a bulk envelope, but fapi, sftp-connector and shopify-connector all publish one record per message. It now accepts both, covers every confirmation type (new replay.{env}.confirmation_made.goods.v1.sub for the 256-char filter cap; RGA's made-side return_goods_authorization maps to the stored return_goods_confirmation), matches on each type's own Record ID via confirmationRecordKey, and is connector-aware — a connector-pinned failure only clears when that connector delivers. Cleared rows keep history (clearedAt + clearedBy), are listed by GET /api/v1/failures?resolved=true and still 404 on replay. The poller's no_originating_connector notice is no longer stored (FUSE-1053's unmet AC). Dev-verified end to end with collector#114.

PR: gfs-bifrost/replay-service#96

## 2026-09-24 — FUSE-1238

Redrive keeps metadata.source as stored

A redrive defaulted an absent metadata.source to "replay", a value no delivery subscription matches, so a redriven order's confirmation would be black-holed the same way as snap-adapter's overwrite. Metadata is now republished verbatim apart from a fresh timestamp; an absent source stays absent and the poller resolves the channel from the connector. Companion to snap-adapter#253.

PR: gfs-bifrost/replay-service#94

## 2026-09-23 — FUSE-1238

Accept sftp-connector's bulk confirmation failure envelope

sftp-connector publishes confirmation write failures as one message with record = BifrostFailure[]. The confirmation-failure route only parsed an object record, so these were acked and dropped and never reached the Retry Queue (latent: none in 30 days). New ingestBulkEvent/isBulkEvent, used on this route only; each failure is stored individually. Dev-verified alongside a regression check of the fapi wrapper path.

PR: gfs-bifrost/replay-service#92

## 2026-09-23 — FUSE-1238

Store each fapi-wrapped confirmation failure as its own retry-queue entry

fapi publishes one confirmation_data_failure per failed delivery with record: { confirmations: [...] }. Replay stored the wrapper as one row with empty businessId/recordId, so it was hidden from customer-filtered Retry Queue views, had no reference, and was never replayable. /event/confirmation-failure now stores one failure per wrapped confirmation. The existing prod backlog (77 PURDYFIGG wrappers from 2026-09-16, false connector_unresolvable failures from the fapi filter gap) is left for a separate dismissal step. sftp's bulk envelope is still unsupported (none seen in 30 days).

PR: gfs-bifrost/replay-service#91

## 2026-09-16 — FUSE-1059

Route goods-in/out confirmation redrives onto cross-entity confirmation_ready

Goods-in/out confirmation redrives now publish to the cross-entity confirmation_ready topic, tagged attributes.recordType = goods_in_confirmation/goods_out_confirmation (the same ready-side values the poller stamps), instead of the legacy unfiltered purchase_order_confirmation_ready/sales_order_confirmation_ready topics added in FUSE-1078. Replay no longer publishes to either legacy per-entity ready topic — the env vars, their remote-state locals, and the two Publisher IAM grants were removed. Every other record type (pick/pack/WOC/FGR/RGA) already rode the cross-entity branch; goods-in/out simply joins it. Part of the FUSE-1059 legacy PO/SO confirmation-topic decommission sequence — gated: not to be merged to prod until fapi's and sftp-connector's cross-entity PO/SO ready subscriptions are live in prod, otherwise a redriven PO/SO confirmation reaches no subscriber.

PR: gfs-bifrost/replay-service#85

## 2026-08-26 — FUSE-1078

Fix goods-in/out/RGA confirmation replay routing

Fixed replay routing for the three confirmation types added in #74, found via a smoke-test dry-run cross-checking real Terraform in fapi/sftp-connector/collector before firing test messages — the previous routing would have silently dropped every replay of these types. goods_in_confirmation/goods_out_confirmation now redrive onto the legacy, unfiltered per-entity topics (purchase_order_confirmation_ready/sales_order_confirmation_ready) — the topics these confirmation types actually rode at the time, not the cross-entity confirmation_ready topic nothing subscribed to under these names. return_goods_confirmation stays on the cross-entity confirmation_ready topic but is now tagged attributes.recordType = "return_goods_authorization", the pre-existing live value real subscribers filter on. Added new env vars PURCHASE_ORDER_CONFIRMATION_READY_TOPIC/SALES_ORDER_CONFIRMATION_READY_TOPIC (remote-state sourced) plus matching publish IAM grants, since replay had never published to either topic before.

PR: gfs-bifrost/replay-service#75

## 2026-06-23 — FUSE-794

Bifrost metadata and logger traceability rollout — replay slice

Cross-service Bifrost-metadata and logger-traceability rollout, replay's slice, building on the published @gfs-bifrost/types 6.3.0 optional source/connectorId/recordId/recordType fields on BifrostMessageMetadata. Bumped @gfs-bifrost/types ^6.2.0 -> ^6.3.0; the local BifrostMessageMetadataSchema now accepts the four new optional fields so ingest no longer strips them and a stored failure's metadata round-trips unchanged through the redrive republish. publishMessage only sets source="replay" when it is genuinely absent, so replay never clobbers the original producer's source/connectorId/recordId/recordType. CorrelationDetails expanded to { correlationId, businessId, flow, recordType, recordId } (flow now includes redrive) and spread onto every log line under requestor, matching the snap-adapter reference pattern. At the ingest decode point replay sets flow="redrive" and lifts businessId (from metadata.customer), recordType, and recordId onto the namespace — connectorId is deliberately not lifted onto the log namespace since replay has no connector context in scope, though the wire value is still preserved verbatim on republish.

PR: gfs-bifrost/replay-service#36

## 2026-06-17 — FUSE-953

Direct VPC egress and Datadog sidecar consolidation

Cloud Run switched from a Serverless VPC Access connector to Direct VPC egress (network interfaces on the existing subnet), with egress mode changed from ALL_TRAFFIC to PRIVATE_RANGES_ONLY so public calls (Pub/Sub, Mongo Atlas, Datadog) leave via Cloud Run's managed egress instead of being hairpinned through the VPC NAT (#28). The Cloud Router, NAT gateway, and VPC connector were deleted as fixed-cost resources no longer needed; the VPC and subnet remain. Part of a fleet-wide rollout of the same network lever piloted on dedupe-service.

Separately (#33), the two Datadog serverless-init sidecars (GFS + ILG) were consolidated into one dual-shipping agent and right-sized, removing ~94 lines of duplicate sidecar IaC, with logger.ts/metrics.ts adapted to the single agent — a forward-port of a change that had originally merged to the stale master branch but never reached main.

PR: gfs-bifrost/replay-service#33
PR: gfs-bifrost/replay-service#28

## 2026-06-17 — FUSE-952

Restore replay CI on master and main

Replay's CI had been red for months on both master and main. On master (#32), every code-quality job failed at pnpm install --frozen-lockfile because pnpm/action-setup used version: latest, which enforces a supply-chain lockfile check that false-positives on the @gfs-bifrost GitHub Packages tarball entries; pinned pnpm to 10.24.0 across the workflow, packageManager, and mise.toml. Also fixed the test harness: test-app.ts was overriding the DI tokens as strings ("MONGO_DB"/"MONGO_CONNECTION") when the real tokens are Symbols, so the override silently missed and the app booted against a real absent Mongo; corrected an AllExceptionsFilter import path; deleted an orphaned business.controller.e2e-spec.ts scaffold left over from the collector template; and fixed a stale import path in pubsub-core.service.spec.ts.

On main (#34), the keystone fix covered three independent failures: the same pnpm-pin fix (main's workflow used version: "10", which floats to a 10.x that ignores the .npmrc ${GITHUB_TOKEN} interpolation and fails pnpm install with ERR_PNPM_FETCH_401); the same orphaned business.controller.e2e-spec.ts deletion; and a dependency-audit fix for two high advisories pulled transitively via @google-cloud/pubsub > google-gax (@grpc/grpc-js and protobufjs), resolved with range-scoped overrides.

PR: gfs-bifrost/replay-service#32
PR: gfs-bifrost/replay-service#34

## 2026-06-04 — FUSE-832

Listen to and store create failure requests

Replay now consumes the global create_data_failure topic via a new POST /event/create-failure endpoint and a single unfiltered push subscription (replay.{env}.create_data_failure.v1.sub); the handler discriminates on the useCase inside the BifrostFailure payload, so new entity types need no IaC changes. Failed records are validated with a deep partial of the canonical schema (they already failed strict validation upstream), with invalid shapes rejected and not stored. Failure validation details (stage, source, structured errors[], upstream) are persisted and exposed via GET /api/v1/failures/:id. Use cases outside the replay registry (only purchase_order, sales_order, master_data at this point) are ack'd and skipped with a create_failure_skipped metric. Replays continue to republish the stored (partial) record to the create-request topic unchanged. Bumped @gfs-bifrost/types ^2.13.1 -> ^4.4.0 for BifrostFailureSchema + deepPartialify.

PR: gfs-bifrost/replay-service#24
