---
tags:
- waypoint
- selector-adapter
title: selector-adapter — architecture
thesis: A push handler decodes the create_record message, the booking use case maps
  it and takes a Firestore claim, and a hand-written SOAP client books it in Selector;
  the handler answers 204 to ack or 503 to redeliver.
confidence: high
verified_paths:
- apps/adapter/internal
- iac
verified: '2026-10-27'
verified_sha: e5f710a
---
# selector-adapter — architecture

```orient-bluf
{ "v": 1, "bluf": "A push handler decodes the create_record message, the booking use case maps it and takes a Firestore claim, and a hand-written SOAP client books it in Selector; the handler answers 204 to ack or 503 to redeliver.", "confidence": "high", "action": "Never call Selector without a claim: Selector books a repeated reference as a new consignment." }
```

## Guardrails

- [technical:G1] Every booking goes through the claim store, and the claim store fails closed. Selector books a repeated `ShipmentReference` again, so a missing or memory-only claim double-books.
  — paths: apps/adapter/internal/core/booking, apps/adapter/internal/adapters/claim
- [technical:G2] An in-flight claim held by another delivery answers 503, and an expired one is reconciled with `DailyShipQuery`, not re-won. Either delivery may already have booked.
  — paths: apps/adapter/internal/adapters/claim, apps/adapter/internal/core/booking/usecase.go
- [technical:G3] Wire structs follow the WSDL `xs:sequence` order. Required value fields are never `omitempty`, and the namespace `http://justshoutgfs.com/Client/Ship/v5/` is sent verbatim.
  — paths: apps/adapter/internal/adapters/selector/types.go
- [policy:G4] Never log a SOAP request or reply body. The password travels in the body, and replies carry recipient PII and base64 labels.
  — paths: apps/adapter/internal/adapters/selector, apps/adapter/internal/http
- [contract:G5] The subscription filter is `recordType = "sales_order" AND selector = "true"`. Changing it recreates the subscription, and the deduper (B1) owns the tag.
  — paths: iac/projects/selector-adapter/pubsub.tf
- [operational:G6] Dev only. `root.hcl` pins dev state and `bifrost-dev-global1`, and `env` accepts only `dev`. Copying wms-gateway's `root.hcl` would send a non-`dev` env to the prod state bucket.
  — paths: iac

## Booking flow

```orient-flow
{ "v": 1, "title": "One push",
  "nodes": [
    { "id": "push", "label": "Push handler", "sub": "decode envelope + canonical", "kind": "step", "ev": [1] },
    { "id": "conn", "label": "ConnectionProvider", "sub": "static env today", "kind": "step", "ev": [6] },
    { "id": "map", "label": "MapShipment", "sub": "GB, UK date, one package", "kind": "step", "ev": [2] },
    { "id": "claim", "label": "Claim", "sub": "won / reclaimed / booked / in flight", "kind": "store", "ev": [4] },
    { "id": "find", "label": "DailyShipQuery", "sub": "reconcile a reclaimed order", "kind": "external", "ev": [5] },
    { "id": "book", "label": "ProcessShipment", "sub": "classified outcome", "kind": "external", "ev": [5] },
    { "id": "reply", "label": "204 / 503", "kind": "step", "ev": [1] }
  ],
  "edges": [
    { "from": "push", "to": "conn" },
    { "from": "conn", "to": "map" },
    { "from": "map", "to": "claim" },
    { "from": "claim", "to": "find", "label": "reclaimed", "style": "dashed" },
    { "from": "claim", "to": "book", "label": "won" },
    { "from": "find", "to": "book", "label": "not found", "style": "dashed" },
    { "from": "book", "to": "reply" }
  ] }
```

`booking.UseCase.Book` returns a `Decision` with `Ack` and a `Reason` [3]. The controller logs the catalogued event for that reason, counts `selector_adapter.shipment.outcome{reason,ack}`, and answers 204 or 503 [1].

| Outcome | Claim | Reply |
|---|---|---|
| Booked (status `SUCCESS`/`NOTE`/`WARNING` **and** a consignment number) | marked booked | 204 |
| Already booked | untouched | 204, Selector not called |
| Another delivery in flight | untouched | 503 |
| Rejected (`ERROR`/`FAILURE`, not `0010`) | released, so a corrected resend can book | 204 |
| Not bookable (non-GB, no postcode, no weight) | never taken | 204 |
| Config fault (`FAILURE 0010`, SOAP fault, 4xx) | released | 503 |
| Not sent (dial or DNS failure) | released | 503 |
| Sent, outcome unknown (timeout, 5xx, no consignment) | marked ambiguous | 503 |
| Claim store unreachable (5 s per call) | n/a | 503 |

## Interfaces

**In.** One route, `POST /events/v1/record/create/sales_order`, behind `RequireCaller`, which checks that the Google ID token's email is `PUSH_CALLER_EMAIL` [1][7]. `GET /health` is open to the app, but Cloud Run IAM still requires the push identity. Malformed pushes and canonicals missing required fields are acked and logged.

**Out.**
- Selector `ClientShipService.asmx`, SOAP 1.1: `ProcessShipment` to book and `DailyShipQuery` to reconcile [5]. The adapter never fetches the WSDL.
- Firestore database `selector-adapter-<env>`, collection `claims`, one document per `{businessId}:{shipmentId}` holding state, `messageId`, `claimedAt`, despatch date, reference and consignments [4].

## Runtime

- Cloud Run `selector-adapter-dev`, max 1 instance, 60 s request timeout, Datadog serverless-init sidecar tailing the shared volume [8].
- `INGRESS_TRAFFIC_ALL`, with `run.invoker` for the push service account only. The runtime account's `datastore.user` is conditioned to its database [8].
- Subscription `selector_adapter.dev.create_record_sales_order.v1.sub`: ack deadline 60 s, retry 10–600 s, 1-day acked retention, no dead-letter policy [9].
- Selector HTTP timeout 30 s. A claim in flight longer than 120 s counts as dead and is reconciled [6].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "apps/adapter/internal/http/controllers/events/salesorder.go@e5f710a" },
  { "id": 2, "kind": "code", "ref": "apps/adapter/internal/core/booking/mapping.go@e5f710a" },
  { "id": 3, "kind": "code", "ref": "apps/adapter/internal/core/booking/usecase.go@e5f710a" },
  { "id": 4, "kind": "code", "ref": "apps/adapter/internal/adapters/claim/firestore.go@e5f710a" },
  { "id": 5, "kind": "code", "ref": "apps/adapter/internal/adapters/selector/booker.go@e5f710a" },
  { "id": 6, "kind": "code", "ref": "apps/adapter/internal/config/config.go@e5f710a" },
  { "id": 7, "kind": "code", "ref": "apps/adapter/internal/http/middleware/middleware.go@e5f710a" },
  { "id": 8, "kind": "code", "ref": "iac/projects/selector-adapter/cloud-run.tf@e5f710a" },
  { "id": 9, "kind": "code", "ref": "iac/projects/selector-adapter/pubsub.tf@e5f710a" }
] }
```
