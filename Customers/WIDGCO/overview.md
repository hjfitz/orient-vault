---
tags: [customer, WIDGCO]
verified: '2026-10-22'
verified_against: cust sync (config-service)
generated: config-snapshot
title: Universal Widget Corporation — overview
thesis: "Universal Widget Corporation has 1 shopify connector in dev only and lands in a SNAP backend. No narrative has been captured; this page is generated from live config."
confidence: high
---
# Universal Widget Corporation — overview

```orient-bluf
{"v": 1, "bluf": "Universal Widget Corporation has 1 shopify connector in dev only and lands in a SNAP backend. No narrative has been captured; this page is generated from live config.", "confidence": "high", "action": "none"}
```

## Integration shape

```orient-flow
{"v": 1, "title": "Universal Widget Corporation: channels in", "nodes": [{"id": "s0", "label": "Universal Widget Corporation", "sub": "Shopify store", "kind": "external"}, {"id": "i0", "label": "shopify-connector", "kind": "service", "service": "shopify-connector", "ev": [1]}, {"id": "pipe", "label": "Fuse core pipeline", "sub": "collector, dedupe-service, snap-adapter", "kind": "external"}, {"id": "wms", "label": "SNAP", "sub": "https://ilg001testapi.snapwarehouse.net/api", "kind": "external", "ev": [1]}], "edges": [{"from": "s0", "to": "i0"}, {"from": "i0", "to": "pipe"}, {"from": "pipe", "to": "wms"}]}
```

## Dev connectors

| Connector | Type | Use cases | Confirmations | Mappings |
| --- | --- | --- | --- | --- |
| ILG Test Store | shopify | sales_order, goods_out_confirmation | off | 2 |

## Evidence

```orient-evidence
{"v": 1, "items": [{"id": 1, "kind": "log", "ref": "cust sync -> config-service (dev), 2026-10-22", "note": "connectors, use cases, confirmation flags and backend type, read live"}]}
```
