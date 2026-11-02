---
tags: [customer, ESCENTRICPL]
verified: '2026-10-22'
verified_against: cust sync (config-service)
generated: config-snapshot
title: Escentric Molecules PL — overview
thesis: "Escentric Molecules PL has 1 sftp connector in production and lands in a SNAP backend. No narrative has been captured; this page is generated from live config."
confidence: high
---
# Escentric Molecules PL — overview

```orient-bluf
{"v": 1, "bluf": "Escentric Molecules PL has 1 sftp connector in production and lands in a SNAP backend. No narrative has been captured; this page is generated from live config.", "confidence": "high", "action": "none"}
```

## Integration shape

```orient-flow
{"v": 1, "title": "Escentric Molecules PL: channels in", "nodes": [{"id": "s0", "label": "Escentric Molecules PL", "sub": "SFTP drop", "kind": "external"}, {"id": "i0", "label": "sftp-connector", "kind": "service", "service": "sftp-connector", "ev": [1]}, {"id": "pipe", "label": "Fuse core pipeline", "sub": "collector, dedupe-service, snap-adapter", "kind": "external"}, {"id": "wms", "label": "SNAP", "sub": "https://ilg003liveapi.snapfulfil.net/api", "kind": "external", "ev": [1]}], "edges": [{"from": "s0", "to": "i0"}, {"from": "i0", "to": "pipe"}, {"from": "pipe", "to": "wms"}]}
```

## Production connectors

| Connector | Type | Use cases | Confirmations | Mappings |
| --- | --- | --- | --- | --- |
| Primary SFTP | sftp | purchase_order, sales_order, master_data, goods_in_confirmation | off | 4 |

## Dev connectors

| Connector | Type | Use cases | Confirmations | Mappings |
| --- | --- | --- | --- | --- |
| Primary SFTP | sftp | purchase_order, sales_order, master_data | off | 3 |
| Gadgets Test | shopify | no mappings | on | 0 |
| Shopify PL Dev Store | shopify | sales_order, goods_out_confirmation | on | 2 |

## Evidence

```orient-evidence
{"v": 1, "items": [{"id": 1, "kind": "log", "ref": "cust sync -> config-service (prod), 2026-10-22", "note": "connectors, use cases, confirmation flags and backend type, read live"}]}
```
