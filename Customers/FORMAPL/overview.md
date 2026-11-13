---
tags: [customer, FORMAPL]
verified: '2026-11-13'
verified_against: cust sync (config-service)
generated: config-snapshot
title: Forma Brands (PL) — overview
thesis: "Forma Brands (PL) has 1 sftp connector in production. No narrative has been captured; this page is generated from live config."
confidence: high
---
# Forma Brands (PL) — overview

```orient-bluf
{"v": 1, "bluf": "Forma Brands (PL) has 1 sftp connector in production. No narrative has been captured; this page is generated from live config.", "confidence": "high", "action": "none"}
```

## Integration shape

```orient-flow
{"v": 1, "title": "Forma Brands (PL): channels in", "nodes": [{"id": "s0", "label": "Forma Brands (PL)", "sub": "SFTP drop", "kind": "external"}, {"id": "i0", "label": "sftp-connector", "kind": "service", "service": "sftp-connector", "ev": [1]}, {"id": "pipe", "label": "Fuse core pipeline", "sub": "collector, dedupe-service, snap-adapter", "kind": "external"}, {"id": "wms", "label": "WMS", "sub": null, "kind": "external", "ev": [1]}], "edges": [{"from": "s0", "to": "i0"}, {"from": "i0", "to": "pipe"}, {"from": "pipe", "to": "wms"}]}
```

## Production connectors

| Connector | Type | Use cases | Confirmations | Mappings |
| --- | --- | --- | --- | --- |
| Primary | sftp | master_data, sales_order, purchase_order | off | 3 |

## Dev connectors

Dev maps the same use cases per channel as production.

## Evidence

```orient-evidence
{"v": 1, "items": [{"id": 1, "kind": "log", "ref": "cust sync -> config-service (prod), 2026-11-13", "note": "connectors, use cases, confirmation flags and backend type, read live"}]}
```
