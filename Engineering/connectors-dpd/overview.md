---
tags:
- waypoint
- connectors-dpd
title: connectors-dpd — overview
thesis: connectors-dpd is the polling tracking connector for DPD, and DPD Local through
  a second deployment of the same image. It runs on tracking-core's shared connector
  framework, and its new events reach raw_tracking.v1 through tracking-core's response-publisher.
confidence: high
verified: '2026-11-06'
verified_paths:
- src
verified_sha: fad40eb
---
# connectors-dpd — overview

```orient-bluf
{ "v": 1, "bluf": "connectors-dpd is the polling tracking connector for DPD, and DPD Local through a second deployment of the same image. It runs on tracking-core's shared connector framework, and its new events reach raw_tracking.v1 through tracking-core's response-publisher.", "confidence": "high", "action": "none" }
```

## Responsibility
- Polls DPD for tracking events through the geopostuk XML API [1]. A second deployment of the same image polls DPD Local.
- The repo also holds a JSON client that nothing calls.
- Takes batches of due parcels from tracking-core's batch-creator over gRPC and calls the carrier for each.
- Streams results back to tracking-core's response-publisher [2].

## In prod (snapshot 2026-11-06)

| Replicas | Carrier calls, 15 days | Failed | Last commit |
| --- | --- | --- | --- |
| 4 (dpd), 3 (dpd-local) | 25.2M (dpd), 21.1M (dpd-local) | 3.33M (dpd, mostly not-found); 1.08M (dpd-local, including 686k 400s) | 2025-05-07 |

**Quirks.** Per-contract credentials from carrier-credentials-manager. The only connectors that pause a contract after a credential error. DPD Local has no repo of its own.

## Where the reference lives
- The shared mechanism (batching, dedupe, mapping, stop rules) is in [[tracking-core]].
- The fleet view, with every connector side by side, is the MPK page *Polling Connectors* [2].

## What deliberately isn't here
- **Choosing which parcels to poll.** tracking-core's consignment-manager and batch-creator own that.
- **Dedupe, mapping and publishing.** tracking-core's response-publisher owns those.

## Neighbours

```orient-flow
{ "v": 1, "title": "connectors-dpd in context",
  "nodes": [
    { "id": "bc", "label": "batch-creator", "sub": "tracking-core", "kind": "service" },
    { "id": "c", "label": "connectors-dpd", "kind": "service", "tone": "accent" },
    { "id": "car", "label": "DPD", "sub": "carrier API", "kind": "external" },
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
  { "id": 1, "kind": "code", "ref": "src@fad40eb" },
  { "id": 2, "kind": "doc", "ref": "Confluence MPK 353697880 Polling Connectors" }
] }
```
