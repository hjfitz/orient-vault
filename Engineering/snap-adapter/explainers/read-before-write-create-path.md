---
tags: [waypoint, explainer, snap-adapter]
thesis: "The sales-order create reads the shipment from Snap first and writes only one still at Due Out. It acknowledges a shipment the warehouse already owns and never re-writes it."
confidence: high
updated: '2026-10-12'
verified: '2026-10-12'
verified_sha: ccfcd9a
verified_paths:
  - apps/snap-adapter/src/adapters/snap/fetch-snap-entity.ts
  - apps/snap-adapter/src/adapters/snap/shipment-stage.ts
  - apps/snap-adapter/src/exceptions/snap-entity-state.exception.ts
  - apps/snap-adapter/src/core/sales-order/sales-order.service.ts
  - apps/snap-adapter/src/core/work-order/work-order.service.ts
  - apps/snap-adapter/src/core/puchase-order/purchase-order.service.ts
  - apps/snap-adapter/src/core/return-goods-authorization/return-goods-authorization.service.ts
  - apps/snap-adapter/src/observability/classify-snap-failure.ts
  - apps/snap-adapter/src/http/controllers/event.controller.ts
  - apps/snap-adapter/src/observability/axios-metrics.ts
title: Read-before-write on the create path
drifted_evidence: []
drift_checked: 2026-10-12
commits_behind: 0
---
# Read-before-write on the create path

```orient-bluf
{
  "v": 1,
  "bluf": "The sales-order create reads the shipment from Snap first and writes only one still at Due Out. It acknowledges a shipment the warehouse already owns and never re-writes it.",
  "confidence": "high",
  "action": "none"
}
```

## Mechanism

**CONFIRMED** A keyed `PUT /v2/shipments` replaces the shipment's children. Re-writing a shipment the warehouse has started would wipe live state, so the create reads first. [4]

```orient-flow
{
  "v": 1,
  "title": "Sales-order create",
  "nodes": [
    { "id": "req", "label": "create sales_order", "sub": "Pub/Sub push", "kind": "step", "ev": [6] },
    { "id": "fs", "label": "Persist routing + line metadata", "sub": "Firestore, before any Snap call", "kind": "store", "ev": [6] },
    { "id": "get", "label": "fetchSnapEntity", "sub": "GET /v2/shipments/{id}", "kind": "step", "ev": [1] },
    { "id": "cls", "label": "classifyShipmentForWrite", "sub": "Stage, Status", "kind": "step", "ev": [2] },
    { "id": "put", "label": "PUT /v2/shipments", "sub": "create", "kind": "step", "tone": "accent", "ev": [4] },
    { "id": "ack", "label": "create_acknowledge", "sub": "already_in_wms", "kind": "topic", "ev": [6] },
    { "id": "fail", "label": "failure, nothing published", "sub": "cancelled_in_wms", "kind": "step", "tone": "alert", "ev": [6] }
  ],
  "edges": [
    { "from": "req", "to": "fs" },
    { "from": "fs", "to": "get" },
    { "from": "get", "to": "put", "label": "not found" },
    { "from": "get", "to": "cls", "label": "found" },
    { "from": "cls", "to": "put", "label": "Stage 00" },
    { "from": "cls", "to": "ack", "label": "Stage 10+" },
    { "from": "cls", "to": "fail", "label": "cancelled" },
    { "from": "put", "to": "ack", "label": "400 XDoc, Invalid Order Stage", "style": "dashed" }
  ]
}
```

- **CONFIRMED** The controller persists routing and line metadata to Firestore first. A failed persist raises a transient failure, so Pub/Sub redelivers. [6][5]
- **CONFIRMED** `fetchSnapEntity` returns `undefined` for three not-found shapes. These are an HTTP 404, a 2xx `Status: "Error"` envelope, and an empty `Results` list. [1]
- **CONFIRMED** Any other transport error propagates as the bare `AxiosError`. The failure classifier then decides whether it is transient. [1][5]
- **CONFIRMED** `classifyShipmentForWrite` returns `writable` only for Stage `00`. Header Status `01`, or Stage `91` or `99`, returns `cancelled`. Anything else returns `in_progress`, including a missing Stage. [2]
- **CONFIRMED** `createInSnap` throws `SnapEntityStateException` for a non-writable shipment. The state is `already_in_wms` for `in_progress` and `cancelled_in_wms` for `cancelled`. The method still returns `Promise<string>`. [4][3]
- **CONFIRMED** The controller acknowledges `already_in_wms` by publishing `create_acknowledge`. It publishes no release and no `create_data_failure`. [6]
- **CONFIRMED** The exception fires before the attachment step, so an acknowledged shipment gets no attachments. [4][6]
- **CONFIRMED** For `cancelled_in_wms` the controller logs the failure and publishes nothing. It sends no acknowledge and no release. [6]
- **CONFIRMED** The classifier maps a Snap 400 to `already_in_wms` when every field error is `XDoc` / `Invalid Order Stage`. This catches the race where the warehouse starts the shipment between the GET and the PUT. [5]
- **CONFIRMED** A 400 that mixes that signature with any other error stays `snap_api_error`. [5]
- **CONFIRMED** A request-interceptor rejection carries no `config` or `response`. The metrics interceptor passes it through untouched. A concurrency-slot timeout then classifies as transient `slot_timeout`, and the push returns 503. [7][5]

## Boundaries

- **CONFIRMED** Only the sales-order service reads before it writes. Work-order, purchase-order and RGA `createInSnap` PUT with no precheck, so a redelivery re-PUTs them. [8][9][10]
- **CONFIRMED** The Stage vocabulary belongs to Snap. Fuse treats `00` (Due Out) as writable and `91` (Cancelled) and `99` (Purged) as terminal. Every other value counts as in progress. [2]
- **CONFIRMED** After a successful PUT, `handleAttachments` fetches the shipment again with `fetchSnapEntity`. It pairs lines by `SOLineId`. It throws an attachment error if Snap no longer returns the shipment. [4]
- **CONFIRMED** Confirmation, release and failure envelopes are outside this path. It covers the create side only. [6]

## Constraints

- **CONFIRMED** A keyed PUT replaces children. This is why a non-`00` shipment is a hard branch, not a warning. [4][2]
- **CONFIRMED** `fetchSnapEntity` treats every `Status: "Error"` envelope as not found. An unrecognised message logs an event, then the write proceeds. [1]
- **CONFIRMED** The shipment id is deterministic. A rejected re-PUT never triggers a compensating delete, because that would delete the live shipment an earlier delivery created. [4]
- **CONFIRMED** The acknowledge path keeps the dedupe hold intact. dedupe-service stores the record before it forwards, and no dedupe-service code or Terraform references `create_acknowledge`. [11][12]
- **ASSESSED** The hold is what stops a released order being re-collected and re-PUT. The deduper's own release topics and `create_data_failure` subscription clear it, so a failure that publishes either re-opens the gate. [6][11]
- **UNKNOWN** The per-create cost of the extra GET. No measurement of Snap read latency under write saturation backs a figure.

## Evidence

```orient-evidence
{
  "v": 1,
  "items": [
    { "id": 1, "kind": "code", "ref": "apps/snap-adapter/src/adapters/snap/fetch-snap-entity.ts@ccfcd9a", "note": "three not-found shapes; bare AxiosError rethrow" },
    { "id": 2, "kind": "code", "ref": "apps/snap-adapter/src/adapters/snap/shipment-stage.ts@ccfcd9a", "note": "stage and status vocabulary; classifyShipmentForWrite" },
    { "id": 3, "kind": "code", "ref": "apps/snap-adapter/src/exceptions/snap-entity-state.exception.ts@ccfcd9a", "note": "already_in_wms and cancelled_in_wms states" },
    { "id": 4, "kind": "code", "ref": "apps/snap-adapter/src/core/sales-order/sales-order.service.ts@ccfcd9a:L380-496", "note": "line attachments by SOLineId; createInSnap read, classify, PUT" },
    { "id": 5, "kind": "code", "ref": "apps/snap-adapter/src/observability/classify-snap-failure.ts@ccfcd9a:L173-360", "note": "XDoc 400 rule, state exception, routing persistence, slot_timeout" },
    { "id": 6, "kind": "code", "ref": "apps/snap-adapter/src/http/controllers/event.controller.ts@ccfcd9a:L344-547", "note": "persist first, create, acknowledge or publish nothing" },
    { "id": 7, "kind": "code", "ref": "apps/snap-adapter/src/observability/axios-metrics.ts@ccfcd9a:L116-141", "note": "failure interceptor passes through an error with no config or response" },
    { "id": 8, "kind": "code", "ref": "apps/snap-adapter/src/core/work-order/work-order.service.ts@ccfcd9a:L222-240", "note": "PUT with no precheck" },
    { "id": 9, "kind": "code", "ref": "apps/snap-adapter/src/core/puchase-order/purchase-order.service.ts@ccfcd9a:L276-300", "note": "PUT with no precheck" },
    { "id": 10, "kind": "code", "ref": "apps/snap-adapter/src/core/return-goods-authorization/return-goods-authorization.service.ts@ccfcd9a:L215-232", "note": "PUT with no precheck" },
    { "id": 11, "kind": "doc", "ref": "dedupe-service code/src/core/create-request.service.ts@c8aa319:L128-150", "note": "saveAndDuplicateCheck runs before the forward publish" },
    { "id": 12, "kind": "doc", "ref": "dedupe-service iac/projects/dedupe-service/pubsub.tf@c8aa319", "note": "release_* and create_data_failure subscriptions; no create_acknowledge" }
  ]
}
```

## Related

[[work-order-family-confirmations]] ·
[[architecture]] ·
known-context: *SNAP itself degrades hard under concurrency*, *SNAP write-response parsing has burned real incidents twice*
