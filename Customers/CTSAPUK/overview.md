---
tags: [customer, CTSAPUK]
verified: '2026-11-10'
verified_against: cust sync (config-service)
generated: config-snapshot
title: Charlotte Tilbury SAP (UK) — overview
thesis: "Charlotte Tilbury SAP (UK) has 2 sftp connectors in dev only and lands in a SNAP backend. No narrative has been captured; this page is generated from live config."
confidence: high
---
# Charlotte Tilbury SAP (UK) — overview

```orient-bluf
{"v": 1, "bluf": "Charlotte Tilbury SAP (UK) has 2 sftp connectors in dev only and lands in a SNAP backend. No narrative has been captured; this page is generated from live config.", "confidence": "high", "action": "none"}
```

## Integration shape

```orient-flow
{"v": 1, "title": "Charlotte Tilbury SAP (UK): channels in", "nodes": [{"id": "s0", "label": "Charlotte Tilbury SAP (UK)", "sub": "SFTP drop", "kind": "external"}, {"id": "i0", "label": "sftp-connector", "kind": "service", "service": "sftp-connector", "ev": [1]}, {"id": "pipe", "label": "Fuse core pipeline", "sub": "collector, dedupe-service, snap-adapter", "kind": "external"}, {"id": "wms", "label": "SNAP", "sub": "https://ilg002testapi.snapwarehouse.net/api", "kind": "external", "ev": [1]}], "edges": [{"from": "s0", "to": "i0"}, {"from": "i0", "to": "pipe"}, {"from": "pipe", "to": "wms"}]}
```

## Dev connectors

| Connector | Type | Use cases | Confirmations | Mappings |
| --- | --- | --- | --- | --- |
| Main SFTP | sftp | master_data, sales_order, purchase_order | off | 3 |
| Secondary SFTP | sftp | master_data, sales_order, purchase_order | off | 3 |

## Evidence

```orient-evidence
{"v": 1, "items": [{"id": 1, "kind": "log", "ref": "cust sync -> config-service (dev), 2026-11-10", "note": "connectors, use cases, confirmation flags and backend type, read live"}]}
```
