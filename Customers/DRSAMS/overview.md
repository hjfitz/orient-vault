---
tags: [customer, DRSAMS]
verified: '2026-11-13'
verified_against: cust sync (config-service)
generated: config-snapshot
title: Dr Sams (UK) — overview
thesis: "Dr Sams (UK) has 1 sftp connector in production and lands in a SNAP backend. No narrative has been captured; this page is generated from live config."
confidence: high
---
# Dr Sams (UK) — overview

```orient-bluf
{"v": 1, "bluf": "Dr Sams (UK) has 1 sftp connector in production and lands in a SNAP backend. No narrative has been captured; this page is generated from live config.", "confidence": "high", "action": "none"}
```

## Integration shape

```orient-flow
{"v": 1, "title": "Dr Sams (UK): channels in", "nodes": [{"id": "s0", "label": "Dr Sams (UK)", "sub": "SFTP drop", "kind": "external"}, {"id": "i0", "label": "sftp-connector", "kind": "service", "service": "sftp-connector", "ev": [1]}, {"id": "pipe", "label": "Fuse core pipeline", "sub": "collector, dedupe-service, snap-adapter", "kind": "external"}, {"id": "wms", "label": "SNAP", "sub": "https://ilg005liveapi.snapfulfil.net/api", "kind": "external", "ev": [1]}], "edges": [{"from": "s0", "to": "i0"}, {"from": "i0", "to": "pipe"}, {"from": "pipe", "to": "wms"}]}
```

## Production connectors

| Connector | Type | Use cases | Confirmations | Mappings |
| --- | --- | --- | --- | --- |
| Main SFTP | sftp | master_data, sales_order, purchase_order, goods_out_confirmation | off | 4 |

## Dev connectors

Dev maps the same use cases per channel as production.

## Evidence

```orient-evidence
{"v": 1, "items": [{"id": 1, "kind": "log", "ref": "cust sync -> config-service (prod), 2026-11-13", "note": "connectors, use cases, confirmation flags and backend type, read live"}]}
```
