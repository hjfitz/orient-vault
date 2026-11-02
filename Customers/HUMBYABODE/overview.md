---
tags: [customer, HUMBYABODE]
verified: '2026-10-22'
verified_against: cust sync (config-service)
generated: config-snapshot
title: HumbyAbode — overview
thesis: "HumbyAbode has 1 shopify connector in dev only. No narrative has been captured; this page is generated from live config."
confidence: high
---
# HumbyAbode — overview

```orient-bluf
{"v": 1, "bluf": "HumbyAbode has 1 shopify connector in dev only. No narrative has been captured; this page is generated from live config.", "confidence": "high", "action": "none"}
```

## Integration shape

```orient-flow
{"v": 1, "title": "HumbyAbode: channels in", "nodes": [{"id": "s0", "label": "HumbyAbode", "sub": "Shopify store", "kind": "external"}, {"id": "i0", "label": "shopify-connector", "kind": "service", "service": "shopify-connector", "ev": [1]}, {"id": "pipe", "label": "Fuse core pipeline", "sub": "collector, dedupe-service, snap-adapter", "kind": "external"}, {"id": "wms", "label": "WMS", "sub": null, "kind": "external", "ev": [1]}], "edges": [{"from": "s0", "to": "i0"}, {"from": "i0", "to": "pipe"}, {"from": "pipe", "to": "wms"}]}
```

## Dev connectors

| Connector | Type | Use cases | Confirmations | Mappings |
| --- | --- | --- | --- | --- |
| HumbyAbode Stock Sync (ILG Test Store) | shopify | no mappings | on | 0 |

## Evidence

```orient-evidence
{"v": 1, "items": [{"id": 1, "kind": "log", "ref": "cust sync -> config-service (dev), 2026-10-22", "note": "connectors, use cases, confirmation flags and backend type, read live"}]}
```
