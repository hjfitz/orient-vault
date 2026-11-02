---
tags: [customer, HJF]
verified: '2026-10-22'
verified_against: cust sync (config-service)
generated: config-snapshot
title: HJF_DEV — overview
thesis: "HJF_DEV has 2 rest/sftp connectors in dev only and lands in a SNAP backend. No narrative has been captured; this page is generated from live config."
confidence: high
---
# HJF_DEV — overview

```orient-bluf
{"v": 1, "bluf": "HJF_DEV has 2 rest/sftp connectors in dev only and lands in a SNAP backend. No narrative has been captured; this page is generated from live config.", "confidence": "high", "action": "none"}
```

## Integration shape

```orient-flow
{"v": 1, "title": "HJF_DEV: channels in", "nodes": [{"id": "s0", "label": "HJF_DEV REST client", "sub": "REST client", "kind": "external"}, {"id": "i0", "label": "fapi", "kind": "service", "service": "fapi", "ev": [1]}, {"id": "s1", "label": "HJF_DEV SFTP drop", "sub": "SFTP drop", "kind": "external"}, {"id": "i1", "label": "sftp-connector", "kind": "service", "service": "sftp-connector", "ev": [1]}, {"id": "pipe", "label": "Fuse core pipeline", "sub": "collector, dedupe-service, snap-adapter", "kind": "external"}, {"id": "wms", "label": "SNAP", "sub": "https://crackle.devtools.fuse.freightops.dev/api", "kind": "external", "ev": [1]}], "edges": [{"from": "s0", "to": "i0"}, {"from": "i0", "to": "pipe"}, {"from": "s1", "to": "i1"}, {"from": "i1", "to": "pipe"}, {"from": "pipe", "to": "wms"}]}
```

## Dev connectors

| Connector | Type | Use cases | Confirmations | Mappings |
| --- | --- | --- | --- | --- |
| Dev | rest | no mappings | on | 0 |
| hjf test | sftp | purchase_order, sales_order, master_data, goods_in_confirmation, goods_out_confirmation, stock_adjustment, return_goods_confirmation, pack_confirmation, pick_confirmation, finished_good_receipt, work_order_confirmation, work_order | off | 12 |

## Evidence

```orient-evidence
{"v": 1, "items": [{"id": 1, "kind": "log", "ref": "cust sync -> config-service (dev), 2026-10-22", "note": "connectors, use cases, confirmation flags and backend type, read live"}]}
```
