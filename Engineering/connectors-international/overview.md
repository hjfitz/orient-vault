---
tags: [waypoint, connectors-international]
title: connectors-international — overview
thesis: "connectors-international is the polling tracking connector for GFS International. It runs on tracking-core's shared connector framework, and its new events reach raw_tracking.v1 through tracking-core's response-publisher."
confidence: high
verified: 2026-11-06
---
# connectors-international — overview

```orient-bluf
{ "v": 1, "bluf": "connectors-international is the polling tracking connector for GFS International. It runs on tracking-core's shared connector framework, and its new events reach raw_tracking.v1 through tracking-core's response-publisher.", "confidence": "high", "action": "none" }
```

## Responsibility
- Polls GFS International for tracking events through REST, to a GFS-run service over plain HTTP [1].
- Takes batches of due parcels from tracking-core's batch-creator over gRPC and calls the carrier for each.
- Streams results back to tracking-core's response-publisher [2].

## In prod (snapshot 2026-11-06)

| Replicas | Carrier calls, 15 days | Failed | Last commit |
| --- | --- | --- | --- |
| 1 | 2.31M | 4.1k (504s) | 2025-02-07 |



## Where the reference lives
- The shared mechanism (batching, dedupe, mapping, stop rules) is in [[tracking-core]].
- The fleet view, with every connector side by side, is the MPK page *Polling Connectors* [2].

## What deliberately isn't here
- **Choosing which parcels to poll.** tracking-core's consignment-manager and batch-creator own that.
- **Dedupe, mapping and publishing.** tracking-core's response-publisher owns those.

## Neighbours

```orient-flow
{ "v": 1, "title": "connectors-international in context",
  "nodes": [
    { "id": "bc", "label": "batch-creator", "sub": "tracking-core", "kind": "service" },
    { "id": "c", "label": "connectors-international", "kind": "service", "tone": "accent" },
    { "id": "car", "label": "GFS International", "sub": "carrier API", "kind": "external" },
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
  { "id": 1, "kind": "code", "ref": "src@3047702" },
  { "id": 2, "kind": "doc", "ref": "Confluence MPK 353697880 Polling Connectors" }
] }
```
