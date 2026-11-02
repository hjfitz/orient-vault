---
tags: [customer, FUSEDEV]
verified: '2026-10-22'
verified_against: cust sync (config-service)
generated: config-snapshot
title: Fuse Development Customer — overview
thesis: "Fuse Development Customer has 3 rest/sftp connectors in dev only and lands in a SNAP backend. No narrative has been captured; this page is generated from live config."
confidence: high
---
# Fuse Development Customer — overview

```orient-bluf
{"v": 1, "bluf": "Fuse Development Customer has 3 rest/sftp connectors in dev only and lands in a SNAP backend. No narrative has been captured; this page is generated from live config.", "confidence": "high", "action": "none"}
```

## Integration shape

```orient-flow
{"v": 1, "title": "Fuse Development Customer: channels in", "nodes": [{"id": "s0", "label": "Fuse Development Customer REST client", "sub": "REST client", "kind": "external"}, {"id": "i0", "label": "fapi", "kind": "service", "service": "fapi", "ev": [1]}, {"id": "s1", "label": "Fuse Development Customer SFTP drop", "sub": "SFTP drop", "kind": "external"}, {"id": "i1", "label": "sftp-connector", "kind": "service", "service": "sftp-connector", "ev": [1]}, {"id": "pipe", "label": "Fuse core pipeline", "sub": "collector, dedupe-service, snap-adapter", "kind": "external"}, {"id": "wms", "label": "SNAP", "sub": "https://tests.com", "kind": "external", "ev": [1]}], "edges": [{"from": "s0", "to": "i0"}, {"from": "i0", "to": "pipe"}, {"from": "s1", "to": "i1"}, {"from": "i1", "to": "pipe"}, {"from": "pipe", "to": "wms"}]}
```

## Dev connectors

| Connector | Type | Use cases | Confirmations | Mappings |
| --- | --- | --- | --- | --- |
| test rest | rest | no mappings | on | 0 |
| Dev SFTP | sftp | sales_order, master_data | on | 2 |
| TestConnector | sftp | sales_order | on | 1 |

## Evidence

```orient-evidence
{"v": 1, "items": [{"id": 1, "kind": "log", "ref": "cust sync -> config-service (dev), 2026-10-22", "note": "connectors, use cases, confirmation flags and backend type, read live"}]}
```
