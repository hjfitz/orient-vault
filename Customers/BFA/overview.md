---
tags: [customer, BFA]
verified: '2026-11-10'
verified_against: cust sync (config-service)
generated: config-snapshot
title: Built for Athletes — overview
thesis: "Built for Athletes has 1 sftp connector in production and lands in a SNAP backend. No narrative has been captured; this page is generated from live config."
confidence: high
---
# Built for Athletes — overview

```orient-bluf
{"v": 1, "bluf": "Built for Athletes has 1 sftp connector in production and lands in a SNAP backend. No narrative has been captured; this page is generated from live config.", "confidence": "high", "action": "none"}
```

## Integration shape

```orient-flow
{"v": 1, "title": "Built for Athletes: channels in", "nodes": [{"id": "s0", "label": "Built for Athletes", "sub": "SFTP drop", "kind": "external"}, {"id": "i0", "label": "sftp-connector", "kind": "service", "service": "sftp-connector", "ev": [1]}, {"id": "pipe", "label": "Fuse core pipeline", "sub": "collector, dedupe-service, snap-adapter", "kind": "external"}, {"id": "wms", "label": "SNAP", "sub": "https://ilg001liveapi.snapfulfil.net/api", "kind": "external", "ev": [1]}], "edges": [{"from": "s0", "to": "i0"}, {"from": "i0", "to": "pipe"}, {"from": "pipe", "to": "wms"}]}
```

## Production connectors

| Connector | Type | Use cases | Confirmations | Mappings |
| --- | --- | --- | --- | --- |
| Main SFTP | sftp | purchase_order, goods_in_confirmation | off | 2 |

## Dev connectors

| Connector | Type | Use cases | Confirmations | Mappings |
| --- | --- | --- | --- | --- |
| Main SFTP | sftp | purchase_order | off | 1 |

## Evidence

```orient-evidence
{"v": 1, "items": [{"id": 1, "kind": "log", "ref": "cust sync -> config-service (prod), 2026-11-10", "note": "connectors, use cases, confirmation flags and backend type, read live"}]}
```
