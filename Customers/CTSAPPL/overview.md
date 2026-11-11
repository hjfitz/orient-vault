---
tags: [customer, CTSAPPL]
verified: '2026-11-11'
verified_against: cust sync (config-service)
generated: config-snapshot
title: Charlotte Tilbury SAP (PL) — overview
thesis: "Charlotte Tilbury SAP (PL) has 1 sftp connector in dev only and lands in a SNAP backend. No narrative has been captured; this page is generated from live config."
confidence: high
---
# Charlotte Tilbury SAP (PL) — overview

```orient-bluf
{"v": 1, "bluf": "Charlotte Tilbury SAP (PL) has 1 sftp connector in dev only and lands in a SNAP backend. No narrative has been captured; this page is generated from live config.", "confidence": "high", "action": "none"}
```

## Integration shape

```orient-flow
{"v": 1, "title": "Charlotte Tilbury SAP (PL): channels in", "nodes": [{"id": "s0", "label": "Charlotte Tilbury SAP (PL)", "sub": "SFTP drop", "kind": "external"}, {"id": "i0", "label": "sftp-connector", "kind": "service", "service": "sftp-connector", "ev": [1]}, {"id": "pipe", "label": "Fuse core pipeline", "sub": "collector, dedupe-service, snap-adapter", "kind": "external"}, {"id": "wms", "label": "SNAP", "sub": "https://ilg003testapi.snapwarehouse.net/api", "kind": "external", "ev": [1]}], "edges": [{"from": "s0", "to": "i0"}, {"from": "i0", "to": "pipe"}, {"from": "pipe", "to": "wms"}]}
```

## Dev connectors

| Connector | Type | Use cases | Confirmations | Mappings |
| --- | --- | --- | --- | --- |
| Main SFTP | sftp | master_data, sales_order, purchase_order | on | 3 |

## Evidence

```orient-evidence
{"v": 1, "items": [{"id": 1, "kind": "log", "ref": "cust sync -> config-service (dev), 2026-11-11", "note": "connectors, use cases, confirmation flags and backend type, read live"}]}
```
