---
tags: [customer, REMUK]
verified: '2026-10-22'
verified_against: cust sync (config-service)
generated: config-snapshot
title: REM — overview
thesis: "REM has 1 sftp connector in dev only. No narrative has been captured; this page is generated from live config."
confidence: high
---
# REM — overview

```orient-bluf
{"v": 1, "bluf": "REM has 1 sftp connector in dev only. No narrative has been captured; this page is generated from live config.", "confidence": "high", "action": "none"}
```

## Integration shape

```orient-flow
{"v": 1, "title": "REM: channels in", "nodes": [{"id": "s0", "label": "REM", "sub": "SFTP drop", "kind": "external"}, {"id": "i0", "label": "sftp-connector", "kind": "service", "service": "sftp-connector", "ev": [1]}, {"id": "pipe", "label": "Fuse core pipeline", "sub": "collector, dedupe-service, snap-adapter", "kind": "external"}, {"id": "wms", "label": "WMS", "sub": null, "kind": "external", "ev": [1]}], "edges": [{"from": "s0", "to": "i0"}, {"from": "i0", "to": "pipe"}, {"from": "pipe", "to": "wms"}]}
```

## Dev connectors

| Connector | Type | Use cases | Confirmations | Mappings |
| --- | --- | --- | --- | --- |
| SFTP Test | sftp | purchase_order, sales_order | on | 2 |

## Evidence

```orient-evidence
{"v": 1, "items": [{"id": 1, "kind": "log", "ref": "cust sync -> config-service (dev), 2026-10-22", "note": "connectors, use cases, confirmation flags and backend type, read live"}]}
```
