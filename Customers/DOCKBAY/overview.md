---
tags: [customer, DOCKBAY]
verified: '2026-11-13'
verified_against: cust sync (config-service)
generated: config-snapshot
title: Dock and Bay — overview
thesis: "Dock and Bay has 2 rest/sftp connectors in production and lands in a SNAP backend. No narrative has been captured; this page is generated from live config."
confidence: high
---
# Dock and Bay — overview

```orient-bluf
{"v": 1, "bluf": "Dock and Bay has 2 rest/sftp connectors in production and lands in a SNAP backend. No narrative has been captured; this page is generated from live config.", "confidence": "high", "action": "none"}
```

## Integration shape

```orient-flow
{"v": 1, "title": "Dock and Bay: channels in", "nodes": [{"id": "s0", "label": "Dock and Bay REST client", "sub": "REST client", "kind": "external"}, {"id": "i0", "label": "fapi", "kind": "service", "service": "fapi", "ev": [1]}, {"id": "s1", "label": "Dock and Bay SFTP drop", "sub": "SFTP drop", "kind": "external"}, {"id": "i1", "label": "sftp-connector", "kind": "service", "service": "sftp-connector", "ev": [1]}, {"id": "pipe", "label": "Fuse core pipeline", "sub": "collector, dedupe-service, snap-adapter", "kind": "external"}, {"id": "wms", "label": "SNAP", "sub": "https://ilg001liveapi.snapfulfil.net/api", "kind": "external", "ev": [1]}], "edges": [{"from": "s0", "to": "i0"}, {"from": "i0", "to": "pipe"}, {"from": "s1", "to": "i1"}, {"from": "i1", "to": "pipe"}, {"from": "pipe", "to": "wms"}]}
```

## Production connectors

| Connector | Type | Use cases | Confirmations | Mappings |
| --- | --- | --- | --- | --- |
| Fulfil.io API Live | rest | no mappings | on | 0 |
| Primary SFTP | sftp | master_data, sales_order, purchase_order | off | 3 |

## Dev connectors

| Connector | Type | Use cases | Confirmations | Mappings |
| --- | --- | --- | --- | --- |
| Fulfil.io Testing | rest | no mappings | on | 0 |
| Primary SFTP | sftp | master_data, sales_order, purchase_order, goods_out_confirmation | on | 4 |

## Evidence

```orient-evidence
{"v": 1, "items": [{"id": 1, "kind": "log", "ref": "cust sync -> config-service (prod), 2026-11-13", "note": "connectors, use cases, confirmation flags and backend type, read live"}]}
```
