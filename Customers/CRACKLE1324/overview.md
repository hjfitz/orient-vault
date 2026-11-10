---
tags: [customer, CRACKLE1324]
verified: '2026-11-10'
verified_against: cust sync (config-service)
generated: config-snapshot
title: FUSE-1324 dev canary (crackle) — overview
thesis: "FUSE-1324 dev canary (crackle) has 1 rest connector in dev only and lands in a SNAP backend. No narrative has been captured; this page is generated from live config."
confidence: high
---
# FUSE-1324 dev canary (crackle) — overview

```orient-bluf
{"v": 1, "bluf": "FUSE-1324 dev canary (crackle) has 1 rest connector in dev only and lands in a SNAP backend. No narrative has been captured; this page is generated from live config.", "confidence": "high", "action": "none"}
```

## Integration shape

```orient-flow
{"v": 1, "title": "FUSE-1324 dev canary (crackle): channels in", "nodes": [{"id": "s0", "label": "FUSE-1324 dev canary (crackle)", "sub": "REST client", "kind": "external"}, {"id": "i0", "label": "fapi", "kind": "service", "service": "fapi", "ev": [1]}, {"id": "pipe", "label": "Fuse core pipeline", "sub": "collector, dedupe-service, snap-adapter", "kind": "external"}, {"id": "wms", "label": "SNAP", "sub": "https://crackle.devtools.fuse.freightops.dev/api", "kind": "external", "ev": [1]}], "edges": [{"from": "s0", "to": "i0"}, {"from": "i0", "to": "pipe"}, {"from": "pipe", "to": "wms"}]}
```

## Dev connectors

| Connector | Type | Use cases | Confirmations | Mappings |
| --- | --- | --- | --- | --- |
| Crackle REST canary | rest | no mappings | on | 0 |

## Evidence

```orient-evidence
{"v": 1, "items": [{"id": 1, "kind": "log", "ref": "cust sync -> config-service (dev), 2026-11-10", "note": "connectors, use cases, confirmation flags and backend type, read live"}]}
```
