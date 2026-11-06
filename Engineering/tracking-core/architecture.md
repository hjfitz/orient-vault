---
tags:
- waypoint
- tracking-core
title: tracking-core — architecture
thesis: 'Four .NET Core 3.1 parts around one Mongo collection: consignment-manager
  fills active-parcels from shipments.v2.identified, batch-creator leases due parcels
  to connectors over gRPC, response-publisher dedupes, maps and publishes, and a NuGet
  framework runs each connector''s loop. Polling config lives in prod etcd.'
confidence: high
verified: '2026-11-06'
verified_paths:
- src
- schema
verified_sha: c081108
---
# tracking-core — architecture

```orient-bluf
{ "v": 1, "bluf": "Four .NET Core 3.1 parts around one Mongo collection: consignment-manager fills active-parcels from shipments.v2.identified, batch-creator leases due parcels to connectors over gRPC, response-publisher dedupes, maps and publishes, and a NuGet framework runs each connector's loop. Polling config lives in prod etcd.", "confidence": "high", "action": "There are no retries or dead letters: a failed poll just waits for the next cycle, so a broken carrier credential burns calls until someone notices." }
```

## Guardrails
- [technical:G1] The connector framework calls the carrier for every parcel in a batch at once, with no rate limit or backoff. Raising `BatchLimit` raises concurrent calls to the carrier.
  — paths: src/Gfs.Fenghuang.Tracking.Core.Frameworks.Connector
- [operational:G2] A parcel stops being polled only when it reaches DELIVERED with that state's etcd key off, or when it expires after 90 days. Switching a carrier off means disabling its etcd keys or adding it to the Mongo `untracked` list.
  — paths: src/Gfs.Fenghuang.Tracking.Core.BatchCreator, src/Gfs.Fenghuang.Tracking.Core.ConsignmentManager
- [contract:G3] `raw_tracking.v1` is shared with the webhook and file paths, and has no formal schema; `schema/tracking-event-schema.json` is an example payload. Changing a field changes it for every consumer downstream.
  — paths: schema, src/Gfs.Fenghuang.Tracking.Core.ResponsePublisher

## Structure

```orient-flow
{ "v": 1, "title": "One poll cycle",
  "nodes": [
    { "id": "con", "label": "Connector", "sub": "CarrierConnectorWorker", "kind": "service" },
    { "id": "etcd", "label": "etcd", "sub": "batch keys per state", "kind": "store" },
    { "id": "bc", "label": "batch-creator", "sub": "gRPC", "kind": "service", "ev": [2] },
    { "id": "ap", "label": "active-parcels", "sub": "findOneAndUpdate", "kind": "store" },
    { "id": "car", "label": "Carrier API", "kind": "external" },
    { "id": "rp", "label": "response-publisher", "sub": "dedupe on date + code", "kind": "service", "ev": [3] },
    { "id": "map", "label": "tracking-mapper", "sub": "sidecar", "kind": "service" },
    { "id": "rt", "label": "raw_tracking.v1", "kind": "topic" }
  ],
  "edges": [
    { "from": "etcd", "to": "con", "label": "enabled states" },
    { "from": "con", "to": "bc", "label": "next batch" },
    { "from": "bc", "to": "ap", "label": "oldest due, up to 100" },
    { "from": "con", "to": "car", "label": "all at once" },
    { "from": "con", "to": "rp", "label": "results" },
    { "from": "rp", "to": "map" },
    { "from": "rp", "to": "rt", "label": "one message per new event" }
  ] }
```

| Part | What it does |
| --- | --- |
| consignment-manager | Subscribes to `shipments.v2.identified` and upserts `active-parcels`. Skips contracts in `untracked` [1] |
| batch-creator | gRPC. Per carrier and state (IN_TRANSIT, DELIVERED, DELETED), returns up to `BatchLimit` parcels whose `LastRequestedAt` is older than `TargetPollingMinutes` [2] |
| Connector framework | NuGet package, versions 0.4.12–0.6.2 across the connectors. Sleeps 30 s when a batch comes back short |
| response-publisher | Dedupes against stored events, maps through the tracking-mapper sidecar, publishes to `raw_tracking.v1`. The legacy topic is configured but `ShouldPublishToLegacy=false` [3] |

## Interfaces
- **In:** `shipments.v2.identified` (Pub/Sub); gRPC from connectors.
- **Out:** `raw_tracking.v1`. Fields: id, a parcel block (shipment IDs, carrier, consignment and parcel number, service, contract, company), received and reported dates, status code and description, and optional signatory, location, depot, delivery window, additional data and the raw carrier payload.
- **Credentials:** connectors hold their own; most in a SealedSecret, four (DPD, DPD Local, Panther, FedEx) from `carrier-credentials-manager`.

## Runtime
- GKE `prod-uk1-primary-cluster`, namespace `fenghuang`. Manifests under `deploy/k8s/fenghuang/tracking/`.
- About 1.53M parcels added to `active-parcels` and 114.7M batches handed out in 15 days (snapshot 2026-11-06).

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "src/Gfs.Fenghuang.Tracking.Core.ConsignmentManager/Subscriber/MessageHandler/ConsignmentHandler.cs@c081108" },
  { "id": 2, "kind": "code", "ref": "src/Gfs.Fenghuang.Tracking.Core.BatchCreator/Services/V1/TrackingBatchService.cs@c081108" },
  { "id": 3, "kind": "code", "ref": "src/Gfs.Fenghuang.Tracking.Core.Shared/Publishers/EventPublisherLegacy.cs@c081108" }
] }
```
