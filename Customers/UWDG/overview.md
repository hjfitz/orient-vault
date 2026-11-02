---
tags: [customer, UWDG]
verified: '2026-10-22'
verified_against: cust sync (config-service)
generated: config-snapshot
title: UniveralWidgerts — overview
thesis: "UniveralWidgerts has 4 rest/sftp/shopify connectors in dev only. No narrative has been captured; this page is generated from live config."
confidence: high
---
# UniveralWidgerts — overview

```orient-bluf
{"v": 1, "bluf": "UniveralWidgerts has 4 rest/sftp/shopify connectors in dev only. No narrative has been captured; this page is generated from live config.", "confidence": "high", "action": "none"}
```

## Integration shape

```orient-flow
{"v": 1, "title": "UniveralWidgerts: channels in", "nodes": [{"id": "s0", "label": "UniveralWidgerts REST client", "sub": "REST client", "kind": "external"}, {"id": "i0", "label": "fapi", "kind": "service", "service": "fapi", "ev": [1]}, {"id": "s1", "label": "UniveralWidgerts SFTP drop", "sub": "SFTP drop", "kind": "external"}, {"id": "i1", "label": "sftp-connector", "kind": "service", "service": "sftp-connector", "ev": [1]}, {"id": "s2", "label": "UniveralWidgerts Shopify store", "sub": "Shopify store", "kind": "external"}, {"id": "i2", "label": "shopify-connector", "kind": "service", "service": "shopify-connector", "ev": [1]}, {"id": "pipe", "label": "Fuse core pipeline", "sub": "collector, dedupe-service, snap-adapter", "kind": "external"}, {"id": "wms", "label": "WMS", "sub": null, "kind": "external", "ev": [1]}], "edges": [{"from": "s0", "to": "i0"}, {"from": "i0", "to": "pipe"}, {"from": "s1", "to": "i1"}, {"from": "i1", "to": "pipe"}, {"from": "s2", "to": "i2"}, {"from": "i2", "to": "pipe"}, {"from": "pipe", "to": "wms"}]}
```

## Dev connectors

| Connector | Type | Use cases | Confirmations | Mappings |
| --- | --- | --- | --- | --- |
| rest-test | rest | pick_confirmation, pack_confirmation | on | 2 |
| UWDGSFTP | sftp | purchase_order, sales_order, goods_in_confirmation, stock_adjustment, return_goods_authorization, return_goods_confirmation, pick_confirmation, pack_confirmation | on | 8 |
| Primary Shopify | shopify | no mappings | on | 0 |
| shopify | shopify | sales_order, goods_out_confirmation | on | 2 |

## Evidence

```orient-evidence
{"v": 1, "items": [{"id": 1, "kind": "log", "ref": "cust sync -> config-service (dev), 2026-10-22", "note": "connectors, use cases, confirmation flags and backend type, read live"}]}
```
