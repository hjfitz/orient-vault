---
tags:
- waypoint
- selector-adapter
title: selector-adapter — overview
thesis: selector-adapter books one GFS Selector carrier shipment per canonical sales
  order taken off create_record, for customers who packed their own goods, and guards
  against booking any order twice.
confidence: high
verified_paths:
- apps/adapter/internal/http/controllers/events
- apps/adapter/internal/core/booking
- apps/adapter/internal/adapters/selector
- iac/projects/selector-adapter/pubsub.tf
verified: '2026-10-27'
verified_sha: e5f710a
---
# selector-adapter — overview

```orient-bluf
{ "v": 1, "bluf": "selector-adapter books one GFS Selector carrier shipment per canonical sales order taken off create_record, for customers who packed their own goods, and guards against booking any order twice.", "confidence": "high", "action": "Treat it as dev-only: it receives nothing until the deduper stamps `selector` (Delivery Backends B1)." }
```

## Responsibility

- It takes a canonical `sales_order` from `create_record` by Pub/Sub push and books it in Selector with one SOAP `ProcessShipment` call [1][2].
- It maps the order to a Selector shipment: GB only, a UK despatch date, one package, carrier defaults from the connection [3].
- It books each order at most once. A Firestore claim per order guards it, and the adapter reconciles an unknown outcome with `DailyShipQuery` [4].
- It publishes nothing. No acknowledgement, tracking or label goes back to the customer.

## Why it exists separately

- **Selector is delivery, not fulfilment.** It books the carrier for an order the customer already packed, so it sits beside snap-adapter, not inside it.
- **It replaces the REST proxy.** `gfs-hybrid-services/selector-rest-proxy` fronts the same SOAP service for direct callers; Fuse calls Selector directly. See [[selector-rest-proxy/overview]].
- **It is Go**, following wms-gateway's runtime and observability pattern.

## Neighbours

```orient-flow
{ "v": 1, "title": "selector-adapter in context",
  "nodes": [
    { "id": "dedupe", "label": "dedupe-service", "sub": "will stamp selector (B1)", "kind": "service", "service": "dedupe-service" },
    { "id": "topic", "label": "create_record", "sub": "owned by bifrost-pubsub", "kind": "topic" },
    { "id": "adapter", "label": "selector-adapter", "sub": "Cloud Run, dev only", "kind": "service", "service": "selector-adapter", "tone": "accent", "ev": [1] },
    { "id": "claims", "label": "Firestore claims", "sub": "selector-adapter-dev", "kind": "store", "ev": [4] },
    { "id": "selector", "label": "Selector", "sub": "ClientShipService.asmx", "kind": "external", "ev": [2] }
  ],
  "edges": [
    { "from": "dedupe", "to": "topic", "label": "publishes" },
    { "from": "topic", "to": "adapter", "label": "push, sales_order + selector" },
    { "from": "adapter", "to": "claims", "label": "claim, mark" },
    { "from": "adapter", "to": "selector", "label": "ProcessShipment, DailyShipQuery" }
  ] }
```

The subscription filters on `selector = "true"`, which nothing stamps yet. snap-adapter, collector and tracking-service read the same topic and ignore the tag.

## Where the reference lives

- [[architecture]]: guardrails, the booking flow, interfaces, runtime.
- [[known-context]]: the decisions behind the rules, history, unknowns.
- `docs/selector-sandbox-findings.md` in the repo: how Selector behaves, measured on the sandbox.
- `Bifrost/Delivery Backends/`: the programme that takes it to real traffic.

## What deliberately isn't here

- **Connection config storage.** config-service will hold `SELECTOR` backends (A3); today a static env provider serves one business.
- **Any Selector UI.** That is a Merak portal (C2), never fuse-ui.
- **Manifesting.** `CommitShipments` stays in Selector.
- **Prod.** There is no prod environment.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "apps/adapter/internal/http/controllers/events/salesorder.go@e5f710a" },
  { "id": 2, "kind": "code", "ref": "apps/adapter/internal/adapters/selector/client.go@e5f710a" },
  { "id": 3, "kind": "code", "ref": "apps/adapter/internal/core/booking/mapping.go@e5f710a" },
  { "id": 4, "kind": "code", "ref": "apps/adapter/internal/core/booking/usecase.go@e5f710a" }
] }
```
