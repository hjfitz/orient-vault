---
tags: [customer, ESCENTRIC]
verified: '2026-11-10'
verified_against: cust sync (config-service)
generated: config-snapshot
title: Escentric Molecules — overview
thesis: "Escentric Molecules has 2 sftp/shopify connectors in production and lands in a SNAP backend. No narrative has been captured; this page is generated from live config."
confidence: high
---
# Escentric Molecules — overview

```orient-bluf
{"v": 1, "bluf": "Escentric Molecules has 2 sftp/shopify connectors in production and lands in a SNAP backend. No narrative has been captured; this page is generated from live config.", "confidence": "high", "action": "none"}
```

## Integration shape

```orient-flow
{"v": 1, "title": "Escentric Molecules: channels in", "nodes": [{"id": "s0", "label": "Escentric Molecules SFTP drop", "sub": "SFTP drop", "kind": "external"}, {"id": "i0", "label": "sftp-connector", "kind": "service", "service": "sftp-connector", "ev": [1]}, {"id": "s1", "label": "Escentric Molecules Shopify store", "sub": "Shopify store", "kind": "external"}, {"id": "i1", "label": "shopify-connector", "kind": "service", "service": "shopify-connector", "ev": [1]}, {"id": "pipe", "label": "Fuse core pipeline", "sub": "collector, dedupe-service, snap-adapter", "kind": "external"}, {"id": "wms", "label": "SNAP", "sub": "https://ilg005liveapi.snapfulfil.net/api", "kind": "external", "ev": [1]}], "edges": [{"from": "s0", "to": "i0"}, {"from": "i0", "to": "pipe"}, {"from": "s1", "to": "i1"}, {"from": "i1", "to": "pipe"}, {"from": "pipe", "to": "wms"}]}
```

## Production connectors

| Connector | Type | Use cases | Confirmations | Mappings |
| --- | --- | --- | --- | --- |
| Primary SFTP | sftp | master_data, sales_order, purchase_order | off | 3 |
| Shopify UK Production Store | shopify | sales_order, goods_out_confirmation | on | 2 |

## Dev connectors

Dev maps the same use cases per channel as production.

## Evidence

```orient-evidence
{"v": 1, "items": [{"id": 1, "kind": "log", "ref": "cust sync -> config-service (prod), 2026-11-10", "note": "connectors, use cases, confirmation flags and backend type, read live"}]}
```
