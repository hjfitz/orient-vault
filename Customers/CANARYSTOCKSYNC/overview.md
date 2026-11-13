---
tags: [customer, CANARYSTOCKSYNC]
verified: '2026-11-13'
verified_against: cust sync (config-service)
generated: config-snapshot
title: FUSE-1300 stock sync canary (test, 20 Oct 26) — overview
thesis: "FUSE-1300 stock sync canary (test, 20 Oct 26) has 2 sftp connectors in dev only. No narrative has been captured; this page is generated from live config."
confidence: high
---
# FUSE-1300 stock sync canary (test, 20 Oct 26) — overview

```orient-bluf
{"v": 1, "bluf": "FUSE-1300 stock sync canary (test, 20 Oct 26) has 2 sftp connectors in dev only. No narrative has been captured; this page is generated from live config.", "confidence": "high", "action": "none"}
```

## Integration shape

```orient-flow
{"v": 1, "title": "FUSE-1300 stock sync canary (test, 20 Oct 26): channels in", "nodes": [{"id": "s0", "label": "FUSE-1300 stock sync canary (test, 20 Oct 26)", "sub": "SFTP drop", "kind": "external"}, {"id": "i0", "label": "sftp-connector", "kind": "service", "service": "sftp-connector", "ev": [1]}, {"id": "pipe", "label": "Fuse core pipeline", "sub": "collector, dedupe-service, snap-adapter", "kind": "external"}, {"id": "wms", "label": "WMS", "sub": null, "kind": "external", "ev": [1]}], "edges": [{"from": "s0", "to": "i0"}, {"from": "i0", "to": "pipe"}, {"from": "pipe", "to": "wms"}]}
```

## Dev connectors

| Connector | Type | Use cases | Confirmations | Mappings |
| --- | --- | --- | --- | --- |
| FUSE-1300 canary SFTP with stockSync | sftp | no mappings | off | 0 |
| FUSE-1300 canary SFTP without stockSync | sftp | no mappings | off | 0 |

## Evidence

```orient-evidence
{"v": 1, "items": [{"id": 1, "kind": "log", "ref": "cust sync -> config-service (dev), 2026-11-13", "note": "connectors, use cases, confirmation flags and backend type, read live"}]}
```
