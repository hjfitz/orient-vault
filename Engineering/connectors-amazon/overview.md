---
tags: [waypoint, connectors-amazon]
title: connectors-amazon — overview
thesis: "connectors-amazon is the polling tracking connector for Amazon Logistics UK. It runs on tracking-core's shared connector framework, and its new events reach raw_tracking.v1 through tracking-core's response-publisher."
confidence: high
verified: 2026-11-06
---
# connectors-amazon — overview

```orient-bluf
{ "v": 1, "bluf": "connectors-amazon is the polling tracking connector for Amazon Logistics UK. It runs on tracking-core's shared connector framework, and its new events reach raw_tracking.v1 through tracking-core's response-publisher.", "confidence": "high", "action": "none" }
```

## Responsibility
- Polls Amazon Logistics UK for tracking events through REST, through the internal amazon-logistics-proxy [1].
- Takes batches of due parcels from tracking-core's batch-creator over gRPC, calls the carrier for each, and streams results back to the response-publisher [2].

## In prod (snapshot 2026-11-06)

| Replicas | Carrier calls, 15 days | Failed | Last commit |
| --- | --- | --- | --- |
| 1 | 6.03M | 16k, mostly 100 s timeouts to the proxy | 2026-10-12 |

**Quirks.** Runs on .NET 6, the others on .NET Core 3.1. Re-polled 2.6M delivered parcels. Fills the signatory from proof of delivery.

## Where the reference lives
- The shared mechanism (batching, dedupe, mapping, stop rules) is in [[tracking-core]].
- The fleet view, with every connector side by side, is the MPK page *Polling Connectors* [2].

## What deliberately isn't here
- **Choosing which parcels to poll.** tracking-core's consignment-manager and batch-creator own that.
- **Dedupe, mapping and publishing.** tracking-core's response-publisher owns those.

## Neighbours

```orient-flow
{ "v": 1, "title": "connectors-amazon in context",
  "nodes": [
    { "id": "bc", "label": "batch-creator", "sub": "tracking-core", "kind": "service" },
    { "id": "c", "label": "connectors-amazon", "kind": "service", "tone": "accent" },
    { "id": "car", "label": "Amazon Logistics UK", "sub": "carrier API", "kind": "external" },
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
  { "id": 1, "kind": "code", "ref": "src@de1abab" },
  { "id": 2, "kind": "doc", "ref": "Confluence MPK 353697880 Polling Connectors" }
] }
```
