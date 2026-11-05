---
tags: [waypoint, ledger]
---
# pkg-go — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-05 — Add the types Go module

Add the types Go module

New pkg-go types module: the twelve canonical record types, the stock position arms and the Snap backend DTO, generated from @gfs-bifrost/types 11.5.0. types.Date mirrors dateSchema. Cross-checked against Zod: 143/143 valid fuse-mocker fixtures round-trip through Go and parse again. Step 1 of the regenerate-on-publish pipeline.

PR: gfs-bifrost/pkg-go#9

## 2026-11-05 — Add the resilience Go module

Add the resilience Go module

New pkg-go resilience module: wms-gateway's adapterclient lifted verbatim (a JSON GET client with retries, circuit breaker, shared limiter, single-flight, cache and Observer), with its 51 tests unchanged. Live-verified as snap v0.1.0's Getter against real Snap (GADG dev) and the fuse-mocker simulator (HJF). Merged on green under the no-review window.

PR: gfs-bifrost/pkg-go#8

## 2026-11-05 — Add the snap Go module

Add the snap Go module

New pkg-go snap module: Shipment, Product, StockTotal and Kit, the endpoints and outbound-queue codes generated from @gfs-bifrost/snap 0.4.1, plus wms-gateway's weak envelope decode, paged reader and typed reads behind a transport-agnostic Getter. Live-verified read-only against real Snap (GADG dev) and the fuse-mocker simulator (HJF). Found that Snap ignores $filter on /v2/shipments/{id}, so Shipment checks BizId on the result; wms-gateway's GetShipment has the same gap, flagged and not fixed.

PR: gfs-bifrost/pkg-go#7

## 2026-11-05 — Add the audit Go module

Add the audit Go module

Third pkg-go module: the AuditMessage envelope, Fuse and Secrets Hub kind details and kind constants, generated from @gfs-bifrost/audit 0.3.1 by a generator inside the module (make gen), with a Generated Types gen-check workflow. Publisher lifted from sftp-connector's host, hardened (no panic on nil or panicking topic, nil details refused, canceled reason). The eventId pattern is now case-insensitive, as Zod's is. Replaces the identical envelopes audit-service and the sftp host each generate. Go output cross-checked against the Zod producer unions (6/6). Draft, awaiting review.

PR: gfs-bifrost/pkg-go#6

## 2026-11-05 — Add pubsub and remoteconfig Go modules

Add pubsub and remoteconfig Go modules

First content in gfs-bifrost/pkg-go, as a 3-PR draft stack (native stack #4):
- pubsub: push decoding, BifrostMessage envelope, publisher with ErrOutcomeUnknown.
- remoteconfig client: SNAP and SELECTOR backends, connectors, SFTP-by-username; redacting Secret type.
- remoteconfig resolver: cache-aside, Apply handles config_revision by deleting (never writing) entries, plus MemoryCache and rediscache.
Replaces hand-rolled copies in wms-gateway, selector-adapter, sftp-connector host and tracking-service. Verified read-only against dev config-service; Apply not yet verified live.

PR: gfs-bifrost/pkg-go#1
PR: gfs-bifrost/pkg-go#2
PR: gfs-bifrost/pkg-go#3
