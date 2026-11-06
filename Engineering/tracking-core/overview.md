---
tags:
- waypoint
- tracking-core
title: tracking-core — overview
thesis: tracking-core is the engine behind every polling connector. It decides which
  parcels to track, hands each connector batches of due parcels, and dedupes, maps
  and publishes their results to raw_tracking.v1. About 5.44M of the 6.25M tracking
  events in 15 days came through it.
confidence: high
verified: '2026-11-06'
verified_paths:
- src
verified_sha: c081108
---
# tracking-core — overview

```orient-bluf
{ "v": 1, "bluf": "tracking-core is the engine behind every polling connector. It decides which parcels to track, hands each connector batches of due parcels, and dedupes, maps and publishes their results to raw_tracking.v1. About 5.44M of the 6.25M tracking events in 15 days came through it.", "confidence": "high", "action": "Read the prod etcd keys before reasoning about a connector's polling interval: no repo holds them." }
```

## Responsibility
- **consignment-manager** subscribes to `shipments.v2.identified` and fills the Mongo collection `active-parcels` [1]. It tracks every carrier unless the contract is on the `untracked` list. Parcels expire after 90 days.
- **batch-creator** answers each connector's gRPC request with up to 100 parcels due for a poll, oldest `LastRequestedAt` first [2].
- **response-publisher** dedupes results on (date, code), maps them through the tracking-mapper sidecar, and publishes one `raw_tracking.v1` message per new event [3].
- **The connector framework** (`Gfs.Fenghuang.Tracking.Core.Frameworks.Connector`, a NuGet package) runs each connector's loop. A connector only supplies its carrier client.

## Why it exists separately
Fifteen carrier connectors share one polling mechanism. Keeping batching, dedupe and publishing here means a connector is only a carrier client.

## Neighbours

```orient-flow
{ "v": 1, "title": "tracking-core in context",
  "nodes": [
    { "id": "sid", "label": "shipments.v2.identified", "kind": "topic" },
    { "id": "cm", "label": "consignment-manager", "kind": "service", "tone": "accent" },
    { "id": "ap", "label": "active-parcels", "sub": "Mongo, 90-day expiry", "kind": "store" },
    { "id": "bc", "label": "batch-creator", "kind": "service", "tone": "accent" },
    { "id": "con", "label": "Connectors", "sub": "connectors-*", "kind": "service" },
    { "id": "rp", "label": "response-publisher", "kind": "service", "tone": "accent" },
    { "id": "rt", "label": "raw_tracking.v1", "kind": "topic" }
  ],
  "edges": [
    { "from": "sid", "to": "cm" },
    { "from": "cm", "to": "ap" },
    { "from": "con", "to": "bc", "label": "next batch" },
    { "from": "bc", "to": "ap" },
    { "from": "con", "to": "rp", "label": "results" },
    { "from": "rp", "to": "rt" }
  ] }
```

## Where the reference lives
- [[architecture]] and [[known-context]] in this folder. The repo's `agents.md` and `schema/` docs.
- The system view: `Systems/carrier-integrations/`. The fleet page: MPK *Polling Connectors* (353697880).

## What deliberately isn't here
- **Carrier clients.** Each lives in its own `connectors-*` repo.
- **Webhook and file tracking.** Those publish to `raw_tracking.v1` directly: [[tracking-webhooks]], [[tracking-file-processor]].
- **Status derivation.** `shipment-tracking-status-deriver` (ECM) consumes `raw_tracking.v1`.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "src/Gfs.Fenghuang.Tracking.Core.ConsignmentManager/Subscriber/MessageHandler/ConsignmentHandler.cs@c081108" },
  { "id": 2, "kind": "code", "ref": "src/Gfs.Fenghuang.Tracking.Core.BatchCreator/Services/V1/TrackingBatchService.cs@c081108" },
  { "id": 3, "kind": "code", "ref": "src/Gfs.Fenghuang.Tracking.Core.ResponsePublisher@c081108" }
] }
```
