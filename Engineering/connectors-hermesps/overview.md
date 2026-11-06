---
tags: [waypoint, connectors-hermesps]
title: connectors-hermesps — overview
thesis: "connectors-hermesps is the polling tracking connector for Evri ParcelShop. It runs on tracking-core's shared connector framework, and its new events reach raw_tracking.v1 through tracking-core's response-publisher."
confidence: high
verified: 2026-11-06
---
# connectors-hermesps — overview

```orient-bluf
{ "v": 1, "bluf": "connectors-hermesps is the polling tracking connector for Evri ParcelShop. It runs on tracking-core's shared connector framework, and its new events reach raw_tracking.v1 through tracking-core's response-publisher.", "confidence": "high", "action": "none" }
```

## Responsibility
- Polls Evri ParcelShop for tracking events through legacy hermesworld REST API in the repo; prod runs the connectors-hermes image [1].
- Takes batches of due parcels from tracking-core's batch-creator over gRPC, calls the carrier for each, and streams results back to the response-publisher [2].

## In prod (snapshot 2026-11-06)

| Replicas | Carrier calls, 15 days | Failed | Last commit |
| --- | --- | --- | --- |
| 1 | 799k | 55k | 2024-07-02 |

**Quirks.** The repo is not what runs. To be retired with connectors-hermes (CID-315).

## Where the reference lives
- The shared mechanism (batching, dedupe, mapping, stop rules) is in [[tracking-core]].
- The fleet view, with every connector side by side, is the MPK page *Polling Connectors* [2].

## What deliberately isn't here
- **Choosing which parcels to poll.** tracking-core's consignment-manager and batch-creator own that.
- **Dedupe, mapping and publishing.** tracking-core's response-publisher owns those.

## Neighbours

```orient-flow
{ "v": 1, "title": "connectors-hermesps in context",
  "nodes": [
    { "id": "bc", "label": "batch-creator", "sub": "tracking-core", "kind": "service" },
    { "id": "c", "label": "connectors-hermesps", "kind": "service", "tone": "accent" },
    { "id": "car", "label": "Evri ParcelShop", "sub": "carrier API", "kind": "external" },
    { "id": "rp", "label": "response-publisher", "sub": "tracking-core", "kind": "service" },
    { "id": "rt", "label": "raw_tracking.v1", "kind": "topic" }
  ],
  "edges": [
    { "from": "c", "to": "bc", "label": "next batch (gRPC)" },
    { "from": "c", "to": "car", "label": "poll" },
    { "from": "c", "to": "rp", "label": "results (gRPC)" },
    { "from": "rp", "to": "rt" }
  ] }
```

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "src@29e1fed" },
  { "id": 2, "kind": "doc", "ref": "Confluence MPK 353697880 Polling Connectors" }
] }
```
