---
tags: [waypoint, ledger]
---
# pkg-go — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

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
