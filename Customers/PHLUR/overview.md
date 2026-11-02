---
tags: [customer, PHLUR]
verified: '2026-10-22'
verified_against: cust sync (config-service)
generated: config-snapshot
title: Phlur UK — overview
thesis: "Phlur UK has 2 rest/sftp connectors in production and lands in a SNAP backend. No narrative has been captured; this page is generated from live config."
confidence: high
---
# Phlur UK — overview

```orient-bluf
{"v": 1, "bluf": "Phlur UK has 2 rest/sftp connectors in production and lands in a SNAP backend. No narrative has been captured; this page is generated from live config.", "confidence": "high", "action": "none"}
```

## Integration shape

```orient-flow
{"v": 1, "title": "Phlur UK: channels in", "nodes": [{"id": "s0", "label": "Phlur UK REST client", "sub": "REST client", "kind": "external"}, {"id": "i0", "label": "fapi", "kind": "service", "service": "fapi", "ev": [1]}, {"id": "s1", "label": "Phlur UK SFTP drop", "sub": "SFTP drop", "kind": "external"}, {"id": "i1", "label": "sftp-connector", "kind": "service", "service": "sftp-connector", "ev": [1]}, {"id": "pipe", "label": "Fuse core pipeline", "sub": "collector, dedupe-service, snap-adapter", "kind": "external"}, {"id": "wms", "label": "SNAP", "sub": "https://ilg005liveapi.snapfulfil.net/api", "kind": "external", "ev": [1]}], "edges": [{"from": "s0", "to": "i0"}, {"from": "i0", "to": "pipe"}, {"from": "s1", "to": "i1"}, {"from": "i1", "to": "pipe"}, {"from": "pipe", "to": "wms"}]}
```

## Production connectors

| Connector | Type | Use cases | Confirmations | Mappings |
| --- | --- | --- | --- | --- |
| Phlur Live API | rest | no mappings | on | 0 |
| Main SFTP | sftp | purchase_order, sales_order, master_data, goods_out_confirmation | off | 4 |

## Dev connectors

| Connector | Type | Use cases | Confirmations | Mappings |
| --- | --- | --- | --- | --- |
| Phlur Dev API | rest | no mappings | on | 0 |
| Main SFTP | sftp | purchase_order, sales_order, master_data, goods_in_confirmation, goods_out_confirmation | off | 5 |

## Evidence

```orient-evidence
{"v": 1, "items": [{"id": 1, "kind": "log", "ref": "cust sync -> config-service (prod), 2026-10-22", "note": "connectors, use cases, confirmation flags and backend type, read live"}]}
```
