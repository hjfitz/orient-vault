---
tags:
- waypoint
- connectors-inpost
title: connectors-inpost — overview
thesis: connectors-inpost is the polling tracking connector for InPost. It runs on
  tracking-core's shared connector framework, and its new events reach raw_tracking.v1
  through tracking-core's response-publisher.
confidence: high
verified: '2026-11-06'
verified_paths:
- src
verified_sha: 0ecd13f
---
# connectors-inpost — overview

```orient-bluf
{ "v": 1, "bluf": "connectors-inpost is the polling tracking connector for InPost. It runs on tracking-core's shared connector framework, and its new events reach raw_tracking.v1 through tracking-core's response-publisher.", "confidence": "high", "action": "none" }
```

## Responsibility
- Polls InPost for tracking events through REST, OAuth [1].
- Takes batches of due parcels from tracking-core's batch-creator over gRPC and calls the carrier for each.
- Streams results back to tracking-core's response-publisher [2].

## In prod (snapshot 2026-11-06)

| Replicas | Carrier calls, 15 days | Failed | Last commit |
| --- | --- | --- | --- |
| 4 | 7.4k | 1 | 2026-10-08 |

**Quirks.** Almost idle. A webhook replacement is an open PR in tracking-webhooks (#2).

## Where the reference lives
- The shared mechanism (batching, dedupe, mapping, stop rules) is in [[tracking-core]].
- The fleet view, with every connector side by side, is the MPK page *Polling Connectors* [2].

## What deliberately isn't here
- **Choosing which parcels to poll.** tracking-core's consignment-manager and batch-creator own that.
- **Dedupe, mapping and publishing.** tracking-core's response-publisher owns those.

## Neighbours

```orient-flow
{ "v": 1, "title": "connectors-inpost in context",
  "nodes": [
    { "id": "bc", "label": "batch-creator", "sub": "tracking-core", "kind": "service" },
    { "id": "c", "label": "connectors-inpost", "kind": "service", "tone": "accent" },
    { "id": "car", "label": "InPost", "sub": "carrier API", "kind": "external" },
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
  { "id": 1, "kind": "code", "ref": "src@0ecd13f" },
  { "id": 2, "kind": "doc", "ref": "Confluence MPK 353697880 Polling Connectors" }
] }
```
