---
tags: [customer, DAZZA]
verified: '2026-10-22'
verified_against: cust sync (config-service)
generated: config-snapshot
title: Darren Test Customer — overview
thesis: "Darren Test Customer has 10 rest/sftp connectors in dev only. No narrative has been captured; this page is generated from live config."
confidence: high
---
# Darren Test Customer — overview

```orient-bluf
{"v": 1, "bluf": "Darren Test Customer has 10 rest/sftp connectors in dev only. No narrative has been captured; this page is generated from live config.", "confidence": "high", "action": "none"}
```

## Integration shape

```orient-flow
{"v": 1, "title": "Darren Test Customer: channels in", "nodes": [{"id": "s0", "label": "Darren Test Customer REST client", "sub": "REST client", "kind": "external"}, {"id": "i0", "label": "fapi", "kind": "service", "service": "fapi", "ev": [1]}, {"id": "s1", "label": "Darren Test Customer SFTP drop", "sub": "SFTP drop", "kind": "external"}, {"id": "i1", "label": "sftp-connector", "kind": "service", "service": "sftp-connector", "ev": [1]}, {"id": "pipe", "label": "Fuse core pipeline", "sub": "collector, dedupe-service, snap-adapter", "kind": "external"}, {"id": "wms", "label": "WMS", "sub": null, "kind": "external", "ev": [1]}], "edges": [{"from": "s0", "to": "i0"}, {"from": "i0", "to": "pipe"}, {"from": "s1", "to": "i1"}, {"from": "i1", "to": "pipe"}, {"from": "pipe", "to": "wms"}]}
```

## Dev connectors

| Connector | Type | Use cases | Confirmations | Mappings |
| --- | --- | --- | --- | --- |
| Demo Rest | rest | no mappings | on | 0 |
| Resty | rest | no mappings | on | 0 |
| Default SFTP | sftp | purchase_order, sales_order | on | 2 |
| Demo SFTP | sftp | sales_order, master_data, goods_in_confirmation | on | 3 |
| SFTP1 | sftp | purchase_order, sales_order | on | 2 |
| harry test | sftp | no mappings | on | 0 |
| sfthreepee | sftp | sales_order | on | 1 |
| sftpfive | sftp | purchase_order, sales_order, master_data | on | 3 |
| sftpfour | sftp | purchase_order, sales_order, master_data | on | 3 |
| sftptwo | sftp | no mappings | on | 0 |

## Evidence

```orient-evidence
{"v": 1, "items": [{"id": 1, "kind": "log", "ref": "cust sync -> config-service (dev), 2026-10-22", "note": "connectors, use cases, confirmation flags and backend type, read live"}]}
```
