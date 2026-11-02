---
tags: [customer, SAIRA]
verified: '2026-10-22'
verified_against: cust sync (config-service)
generated: config-snapshot
title: Saira Skin — overview
thesis: "Saira Skin has 1 shopify connector in production and lands in a SNAP backend. No narrative has been captured; this page is generated from live config."
confidence: high
---
# Saira Skin — overview

```orient-bluf
{"v": 1, "bluf": "Saira Skin has 1 shopify connector in production and lands in a SNAP backend. No narrative has been captured; this page is generated from live config.", "confidence": "high", "action": "none"}
```

## Integration shape

```orient-flow
{"v": 1, "title": "Saira Skin: channels in", "nodes": [{"id": "s0", "label": "Saira Skin", "sub": "Shopify store", "kind": "external"}, {"id": "i0", "label": "shopify-connector", "kind": "service", "service": "shopify-connector", "ev": [1]}, {"id": "pipe", "label": "Fuse core pipeline", "sub": "collector, dedupe-service, snap-adapter", "kind": "external"}, {"id": "wms", "label": "SNAP", "sub": "https://ilg004liveapi.snapfulfil.net/api", "kind": "external", "ev": [1]}], "edges": [{"from": "s0", "to": "i0"}, {"from": "i0", "to": "pipe"}, {"from": "pipe", "to": "wms"}]}
```

## Production connectors

| Connector | Type | Use cases | Confirmations | Mappings |
| --- | --- | --- | --- | --- |
| Saira Skin Live Shopify | shopify | sales_order, goods_out_confirmation | on | 2 |

## Dev connectors

Dev maps the same use cases per channel as production.

## Evidence

```orient-evidence
{"v": 1, "items": [{"id": 1, "kind": "log", "ref": "cust sync -> config-service (prod), 2026-10-22", "note": "connectors, use cases, confirmation flags and backend type, read live"}]}
```
