---
tags: [waypoint, ledger]
title: snap-queue-polling-service — work ledger
---
# snap-queue-polling-service — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-10-15 — FUSE-1298

Stamp the connector type on the stock_sync export publish

The stock sync export publish now carries a connectorType Pub/Sub attribute (the existing ConnectorType enum, shopify today) beside recordType=stock_sync, so each consumer can filter its subscription to its own connector type. The type is set where stage 1 lists connectors, carried on the stock_sync_due record, and stamped by stage 2; an untyped due message still on the topic across the deploy is treated as shopify and an unknown type is acked as malformed. Verified in dev on GADG's scheduled Shopify connector. Must be live in prod before any subscription filters on it.

PR: gfs-bifrost/snap-adapter#298

## 2026-10-05 — Clear routed confirmations for BYOMA, WILDSMITH and EPARFUM

Clear routed confirmations for BYOMA, WILDSMITH and EPARFUM

Poller Clear-Down D1, first three businesses. Prod allow-list set via Terraform; live 2026-10-05 13:02Z (revision 00089-bpc).

PR: gfs-bifrost/snap-adapter#281

## 2026-10-02 — Clear routed rows off SNAP once their publish resolves

Clear routed rows off SNAP once their publish resolves

Poller Clear-Down C2, PR C of 3. Wires OutboundQueueClearer into announceConfirmations after the confirmation_ready publish resolves; CLEAR_AFTER_PUBLISH_BUSINESS_IDS (dev HJF, prod empty) and CLEAR_AFTER_PUBLISH_CONCURRENCY (3) from Terraform. Dev e2e on HJF: routed pick/pack/goods-out cleared with replay failures recorded; no_subscription/broadcast skips, injected clear failure recovered on re-announce, withheld business not polled. fuse-mocker 0b4f75d adds snapoutbound faults.

PR: gfs-bifrost/snap-adapter#279

## 2026-10-02 — Add the outbound-queue clearer, not yet wired

Add the outbound-queue clearer, not yet wired

Poller Clear-Down C2, PR B of 3. OutboundQueueClearer clears an allow-listed business's routed, published rows when the channel subscribes to the type; broadcast/unrouted/no-subscription/stock_adjustment/no-queueId stay for snap-adapter. Bounded pool, breaker short-circuit, snap.outbound.* metrics. Unit only; wired in PR C.

PR: gfs-bifrost/snap-adapter#278

## 2026-10-02 — Check SNAP's envelope when clearing an outbound row

Check SNAP's envelope when clearing an outbound row

Poller Clear-Down C2, PR A of 3. clearFromOutboundQueue now rejects a 2xx Status:Error, an empty Results or a non-envelope body (SNAP answers an unknown id with HTTP 200). Disposer drop paths log the failure instead of a false Record dropped; row behaviour unchanged. Dev-verified on HJF via a simulator cancel.

PR: gfs-bifrost/snap-adapter#277

## 2026-09-21 — FUSE-1063

Gate SNAP polling on connector confirmationsEnabled

Two independent PRs, both merged: #240 (poll-gate — skips a business before any SNAP call when none of its connectors has confirmationsEnabled, via a cached config-service /business index, refetched on CONNECTOR revisions; fail-open on an unreadable index) and #241 (claim-precheck — drops already-claimed queue items before enrichment in the lanes, cutting announce-time duplicate skips from ~37/cycle to zero in dev). Gate is the connector toggle only; mapping/use-case eligibility stays each downstream connector's concern. Lever B (per-entry Firestore routing pre-read) was designed and rejected by Harry — see plan's Decisions. gotcha: signing off a plan split across two PRs/worktrees means wp signoff's ancestor check can't see both — verified manually via gh pr view + diffing origin/master instead of forcing a false pass. See [[architecture]] Config & credentials / Outbound-queue mechanics.

## 2026-09-17 — FUSE-1063

Connector-level confirmation gating replaces the business-level flag

RemoteConfigProvider.resolveConnectorConfirmationsEnabled (new, mirrors resolveConnectorSource's shape) is now the sole confirmation-emission gate, checked in ConfirmationsService.resolveRoutingSources alongside connector-source resolution. Absent confirmationsEnabled reads as not-enabled, not enabled - deliberate, opposite of this codebase's usual convention (see known-context.md's new "Confirmation eligibility gating" section for why, and the FUSE-808 revert history). The business-level `confirmations` flag is retired as a gate and deleted from the codebase entirely (SnapBackendConfig, cache schema, DTO mapping) - not just left unread.

Scope deliberately narrow: only the boolean toggle moved upstream. Use-case/mapping eligibility stays downstream at each connector (sftp-connector, shopify-connector, fapi) - verified none duplicate this check.

Required a real prod data backfill before shipping (config-service's migrate:confirmations-enabled / migrate:confirmations-enabled-sftp-shopify, run directly against prod via Terraform-state-extracted credentials, 10 connectors touched, applied+verified idempotent).

Review feedback (Harry) led to deleting the local BackendConfigWithConfirmationsSchema mirror in favour of @gfs-bifrost/types' BackendConfigResponseDTO directly, and incidentally fixed a pre-existing broadcastConfirmations cold-cache-miss gap in the same pass.

Docs updated: architecture.md (routing-aware type count corrected 6->7, FGR routingAware fix, new gate description), known-context.md (new section - the FUSE-808 prior-attempt history, load-bearing for any future change to this gate).

PR: snap-adapter#233 (merged d6da428). See [[work-order-family-confirmations]] area docs for the sibling routing-resolution mechanism this reuses.

## 2026-09-14 — FUSE-1078

Routing-store read side signed off (R1/R1b/R1c); attachment retirement descoped to follow-on

Poller now resolves confirmation routing AND Shopify line-extensions from the Firestore store — store-first, SNAP-attachment fallback intact — across good_in/good_out/pick/pack/WOC/RGA. Shipped as 3 stacked PRs: #211 (R1 base read, live in prod, good_out/good_in hits confirmed), #222 (RGA parity), #215 (Shopify line-ext read); R1b/R1c merged 09-11, parked at prod gate then. Reader error propagates -> QueueLane per-consumer catch, never broadcasts (dedicated snap.routing_lookup.error{lane}; poll.failure can't tell SNAP outage from Firestore). recordType asymmetry to remember: ready SO=goods_out_confirmation, made SO=sales_order. Retiring the attachment fallback is NOT done here — descoped to [[../../snap-adapter/plans/FUSE-1078-retire-routing-attachments|retire-routing-attachments]], re-sequenced by Harry to: build per-type gate monitors in gfs-bifrost/observability, remove the attachment WRITE (snap-adapter core/sales-order/attachments/*, work-order/attachments.ts), monitor fallback_attachment->0 as pre-cutover orders drain, then remove the attachment READ (former R2) last. Key paths: apps/snap-queue-polling-service/src/core/snap/confirmations/*, adapters/firestore/routing-metadata.reader.ts, observability/catalog/snap-polling.type.ts.
