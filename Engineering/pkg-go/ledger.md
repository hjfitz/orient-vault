---
tags: [waypoint, ledger]
---
# pkg-go — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

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
