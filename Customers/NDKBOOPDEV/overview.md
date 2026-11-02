---
tags: [customer, NDKBOOPDEV]
verified: '2026-10-22'
verified_against: cust sync (config-service)
generated: config-snapshot
title: [DEV] Nylah's Bees — overview
thesis: "[DEV] Nylah's Bees has 2 sftp connectors in dev only. No narrative has been captured; this page is generated from live config."
confidence: high
---
# [DEV] Nylah's Bees — overview

```orient-bluf
{"v": 1, "bluf": "[DEV] Nylah's Bees has 2 sftp connectors in dev only. No narrative has been captured; this page is generated from live config.", "confidence": "high", "action": "none"}
```

## Integration shape

```orient-flow
{"v": 1, "title": "[DEV] Nylah's Bees: channels in", "nodes": [{"id": "s0", "label": "[DEV] Nylah's Bees", "sub": "SFTP drop", "kind": "external"}, {"id": "i0", "label": "sftp-connector", "kind": "service", "service": "sftp-connector", "ev": [1]}, {"id": "pipe", "label": "Fuse core pipeline", "sub": "collector, dedupe-service, snap-adapter", "kind": "external"}, {"id": "wms", "label": "WMS", "sub": null, "kind": "external", "ev": [1]}], "edges": [{"from": "s0", "to": "i0"}, {"from": "i0", "to": "pipe"}, {"from": "pipe", "to": "wms"}]}
```

## Dev connectors

| Connector | Type | Use cases | Confirmations | Mappings |
| --- | --- | --- | --- | --- |
| Test Connector | sftp | purchase_order, sales_order, master_data | on | 3 |
| test 2 | sftp | no mappings | on | 0 |

## Evidence

```orient-evidence
{"v": 1, "items": [{"id": 1, "kind": "log", "ref": "cust sync -> config-service (dev), 2026-10-22", "note": "connectors, use cases, confirmation flags and backend type, read live"}]}
```
