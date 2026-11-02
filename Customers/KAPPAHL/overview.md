---
tags: [customer, KAPPAHL]
verified: '2026-10-22'
verified_against: cust sync (config-service)
generated: config-snapshot
title: KappAhl — overview
thesis: "KappAhl has 1 sftp connector in production and lands in a SNAP backend. No narrative has been captured; this page is generated from live config."
confidence: high
---
# KappAhl — overview

```orient-bluf
{"v": 1, "bluf": "KappAhl has 1 sftp connector in production and lands in a SNAP backend. No narrative has been captured; this page is generated from live config.", "confidence": "high", "action": "none"}
```

## Integration shape

```orient-flow
{"v": 1, "title": "KappAhl: channels in", "nodes": [{"id": "s0", "label": "KappAhl", "sub": "SFTP drop", "kind": "external"}, {"id": "i0", "label": "sftp-connector", "kind": "service", "service": "sftp-connector", "ev": [1]}, {"id": "pipe", "label": "Fuse core pipeline", "sub": "collector, dedupe-service, snap-adapter", "kind": "external"}, {"id": "wms", "label": "SNAP", "sub": "https://ilg004liveapi.snapfulfil.net/api", "kind": "external", "ev": [1]}], "edges": [{"from": "s0", "to": "i0"}, {"from": "i0", "to": "pipe"}, {"from": "pipe", "to": "wms"}]}
```

## Production connectors

| Connector | Type | Use cases | Confirmations | Mappings |
| --- | --- | --- | --- | --- |
| KappAhl | sftp | purchase_order, sales_order, master_data, goods_in_confirmation, goods_out_confirmation | on | 5 |

## Dev connectors

| Connector | Type | Use cases | Confirmations | Mappings |
| --- | --- | --- | --- | --- |
| KappAhl | sftp | purchase_order, sales_order, master_data | on | 3 |

## Evidence

```orient-evidence
{"v": 1, "items": [{"id": 1, "kind": "log", "ref": "cust sync -> config-service (prod), 2026-10-22", "note": "connectors, use cases, confirmation flags and backend type, read live"}]}
```
