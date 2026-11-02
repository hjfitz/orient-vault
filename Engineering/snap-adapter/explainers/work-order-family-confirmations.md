---
tags: [waypoint, explainer, snap-adapter]
thesis: "A completed work order produces two independent confirmations: the WOC from the S10 shipment and the FGR from the R10 receipt. Nothing joins them."
confidence: high
updated: '2026-10-14'
verified: '2026-10-14'
verified_sha: fa3f47a
verified_paths:
  - apps/snap-queue-polling-service/src/core/snap/confirmations/work-order-confirmation.confirmation-handler.ts
  - apps/snap-queue-polling-service/src/core/snap/confirmations/finished-good-receipt.confirmation-handler.ts
  - apps/snap-queue-polling-service/src/core/snap/confirmations/work-order.discriminator.ts
  - apps/snap-queue-polling-service/src/core/snap/confirmations/work-order.batches.ts
  - apps/snap-queue-polling-service/src/core/snap/confirmations/despatch-confirmation.handler.base.ts
  - apps/snap-queue-polling-service/src/core/snap/confirmations/receipt-confirmation.handler.base.ts
  - apps/snap-queue-polling-service/src/core/snap/confirmations/canonical-confirmation.handler.base.ts
  - apps/snap-queue-polling-service/src/core/snap/confirmations/confirmations.service.ts
  - apps/snap-queue-polling-service/src/core/snap/confirmations/confirmation-subscriptions.ts
  - apps/snap-queue-polling-service/src/core/snap/confirmations/outbound-queue.clearer.ts
  - apps/snap-queue-polling-service/src/core/snap/confirmations/types.ts
  - apps/snap-queue-polling-service/src/core/snap/confirmations/constants.ts
  - apps/snap-queue-polling-service/src/core/snap/outbound-queue/despatch.entries.ts
  - apps/snap-queue-polling-service/src/core/snap/outbound-queue/receipt.entries.ts
  - apps/snap-queue-polling-service/src/bootstrap/factory/controller.factory.ts
  - apps/snap-queue-polling-service/src/config/config.schemas.ts
  - apps/snap-adapter/src/http/controllers/event.controller.ts
title: Work-order family confirmations (WOC and FGR)
drifted_evidence: []
drift_checked: 2026-10-12
commits_behind: 0
---
# Work-order family confirmations (WOC and FGR)

```orient-bluf
{
  "v": 1,
  "bluf": "A completed work order produces two independent confirmations: the WOC from the S10 shipment and the FGR from the R10 receipt. Nothing joins them.",
  "confidence": "high",
  "action": "none"
}
```

## Mechanism

**CONFIRMED** The poller reads Snap's outbound queue. Snap pushes nothing. [1]

```orient-flow
{
  "v": 1,
  "title": "Confirmation path",
  "nodes": [
    { "id": "q", "label": "SNAP outbound queue", "sub": "XDoc · Key", "kind": "store", "ev": [1] },
    { "id": "de", "label": "resolveDespatchEntries", "sub": "batch-fetch shipments", "kind": "step", "ev": [1] },
    { "id": "re", "label": "resolveReceiptEntries", "sub": "batch-fetch receipts", "kind": "step", "ev": [1] },
    { "id": "woc", "label": "WorkOrderConfirmationHandler", "sub": "stage 90 · OrderType S10", "kind": "step", "ev": [3] },
    { "id": "go", "label": "GoodsOutConfirmationHandler", "sub": "stage 90 · every other shipment", "kind": "step" },
    { "id": "fgr", "label": "FinishedGoodReceiptHandler", "sub": "OrderType R10", "kind": "step", "ev": [5] },
    { "id": "pub", "label": "announceConfirmations", "sub": "claim by queueId · emit", "kind": "step", "service": "snap-queue-polling-service", "ev": [9] },
    { "id": "topic", "label": "confirmation_ready", "sub": "attributes.recordType", "kind": "topic", "ev": [10] },
    { "id": "clr", "label": "OutboundQueueClearer", "sub": "every published row", "kind": "step", "ev": [11] },
    { "id": "sftp", "label": "sftp-connector", "sub": "writes the customer file", "kind": "service", "service": "sftp-connector" }
  ],
  "edges": [
    { "from": "q", "to": "de", "label": "DESPATCH" },
    { "from": "q", "to": "re", "label": "RECEIPT" },
    { "from": "de", "to": "woc" },
    { "from": "de", "to": "go" },
    { "from": "re", "to": "fgr" },
    { "from": "woc", "to": "pub" },
    { "from": "fgr", "to": "pub" },
    { "from": "pub", "to": "topic" },
    { "from": "pub", "to": "clr", "label": "after publish", "style": "dashed" },
    { "from": "topic", "to": "sftp" },
    { "from": "clr", "to": "q", "label": "clear" }
  ]
}
```

### Shared pipeline

- **CONFIRMED** Entry resolution drops an entry whose record Snap does not return. The item stays queued for the next poll. It also skips entries that belong to another tenant. [1]
- **CONFIRMED** Each handler claims its own entries, then maps them in pages of 50. [2][6]
- **CONFIRMED** Each handler validates its canonical records. It drops an unparseable record and increments a metric. [3][5]
- **CONFIRMED** `announceConfirmations` claims each record by `identifiers.queueId` to drop duplicates. It then emits one message per customer group, with the records as an array. [9]
- **CONFIRMED** WOC and FGR publish to `confirmation_ready` with `attributes.recordType` set to their own name. Every subscriber must filter on that attribute at the subscription. [10]
- **CONFIRMED** Emission sets `attributes.source`. It sets `attributes.broadcast` when a group has no connector and no source. [9]

### Clear-down

- **CONFIRMED** After publish, `OutboundQueueClearer` clears each published row off the queue, for every business. It is the only clear-down. snap-adapter has no `confirmation_made` route. [11][13]
- **CONFIRMED** It clears broadcast, unrouted and stock-adjustment groups too. It skips only a routed group whose source channel does not subscribe to the type, and a row with no `queueId`. [11][14]
- **ASSESSED** A WOC or FGR that sftp-connector then fails to deliver is not re-announced. sftp-connector records it on `confirmation_data_failure`, and replay redrives it from there. This pass did not re-read the connector.
- **ASSESSED** A row whose clear fails stays queued and is picked up on the next poll. The queueId claim, whose TTL equals the poller's request timeout, suppresses a repeat publish while it holds. [9]

### WOC: the work-order confirmation

- **CONFIRMED** The WOC handler owns despatch entries at stage `FULFILLED` (90) whose `OrderType` is `S10`. The goods-out handler takes every other shipment at that stage. [2][3][4]
- **CONFIRMED** It reads two documents: the S10 shipment and the matching R10 receipt. It finds the receipt with filters tried in order: `SupplierRef` = shipment id, `SupplierOrder` = shipment id, `SupplierRef` = the shipment's `CustomerRef`. The first single match wins. [3][4]
- **CONFIRMED** An ambiguous or absent match reports consumed components only. The handler logs a search error and runs the next filter. [3]
- **CONFIRMED** Snap mirrors every work-order line onto both documents. The handler joins them on the `Line` key. A receipt-only key surfaces as an extra line. [3]
- **CONFIRMED** Role comes from planned quantities. `QtyRequired` alone marks a component. `QtyOrdered` alone marks a finished good. Actuals break a tie. An unclassifiable line defaults to component and logs a warning. [3]
- **CONFIRMED** `consumed` comes from `QtyPicked`. `produced` and `rejected` come from the matched receipt line. The side that does not apply is absent, not zero. [3]
- **CONFIRMED** A component line carries `location.batchId` when Snap shows exactly one batch for its SKU. The batch comes from stock movements into the work order's consignment, then Stock Detail by stock id. More than one batch leaves it off and logs a warning. [3][8]
- **CONFIRMED** Finished-good lines on the WOC carry no batch. The produced batch is on the FGR. [3]
- **CONFIRMED** Routing is order-wide. The per-shipment Firestore store wins when it has an entry. The shipment's `SHH` header attachment is the fallback. Routing rides the envelope metadata, not the canonical record. [2][7]

### FGR: the finished-good receipt

- **CONFIRMED** The FGR handler owns every receipt with `OrderType` `R10`. It has no stage filter. [4][5]
- **CONFIRMED** It calls Snap. It finds the originating S10 work order with `ShipmentId` = `Prime`, then `SupplierRef`, then `SupplierOrder`, then `CustomerRef` = `SupplierRef`. The first single match wins. [4][5]
- **CONFIRMED** From the work order it sets `workOrderId`, `businessWorkOrderId`, `workOrder.customerRef` and `salesOrder`. With no match, the receipt publishes without them. [5]
- **CONFIRMED** A lookup error propagates. The entry stays queued and retries on the next poll. [5]
- **CONFIRMED** It keeps only finished-good lines, where `QtyOrdered` is above 0. If a receipt has lines but none match, it logs a warning and returns all of them. [4][5]
- **CONFIRMED** Each kept line carries `produced` from `QtyReceived` (0 if absent) and `rejected` from `QtyRejected`. `totalProduced` sums them, and `totalLines` counts them. [5]
- **CONFIRMED** A kept line carries `location.batchId` when the receipt's consignment shows exactly one batch for its SKU. [5][8]
- **CONFIRMED** The FGR is routing-aware. It reads the routing doc keyed by the receipt's `Prime`, falling back to the receipt id. [5][6][7]

## Boundaries

- **CONFIRMED** The poller produces canonical records and clears their queue rows once published. It never renders a customer file. [11]
- **ASSESSED** sftp-connector's egress mapping renders the customer file.
- **CONFIRMED** WOC and FGR are independent records on independent subscriptions. `identifiers.finishedGoodReceiptId` on the WOC is the only cross-reference. It is absent unless the receipt search finds exactly one match. [3]
- **CONFIRMED** Neither handler interprets customers or files. Routing passes through as envelope metadata. [7]

## Constraints

- **CONFIRMED** `Prime` and `ConsignmentId` are self-referential on both documents. No key links a work order to its receipt, so each side finds the other by candidate-filter search. [4]
- **ASSESSED** Snap stamps the work order's `ShipmentId` on the receipt's `Prime`, un-suffixed. That is why the FGR search leads with it. We saw it on three GADG dev work orders and the HJF simulator. The WOC search does not use `Prime`. [4]
- **CONFIRMED** `QtyShipped` is structurally 0 on a work order. Read consumed quantity from `QtyPicked`. [3]
- **ASSESSED** A broken or unconfigured egress no longer leaves queue entries accumulating. The row is cleared at publish, so a lost delivery is only recoverable from replay. [11]

## Evidence

```orient-evidence
{
  "v": 1,
  "items": [
    { "id": 1, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/outbound-queue/despatch.entries.ts@ccfcd9a", "note": "entry resolution: drop absent records, skip other tenants" },
    { "id": 2, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/despatch-confirmation.handler.base.ts@ccfcd9a", "note": "stage and owner filter, pages of 50, SHH header routing" },
    { "id": 3, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/work-order-confirmation.confirmation-handler.ts@ccfcd9a", "note": "S10 handler: receipt search, line join, role, batch" },
    { "id": 4, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/work-order.discriminator.ts@ccfcd9a", "note": "S10 and R10 constants, candidate filters, finished-good line filter" },
    { "id": 5, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/finished-good-receipt.confirmation-handler.ts@ccfcd9a", "note": "R10 handler: work-order lookup, kept lines, routing" },
    { "id": 6, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/receipt-confirmation.handler.base.ts@ccfcd9a", "note": "receipt lane: pages of 50, store lookup only when routing-aware" },
    { "id": 7, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/canonical-confirmation.handler.base.ts@ccfcd9a", "note": "store routing wins, attachment is the fallback" },
    { "id": 8, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/work-order.batches.ts@ccfcd9a", "note": "one batch or none per SKU" },
    { "id": 9, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/confirmations.service.ts@ccfcd9a:L255-375", "note": "announce: claim, emit, clear" },
    { "id": 10, "kind": "code", "ref": "apps/snap-queue-polling-service/src/bootstrap/factory/controller.factory.ts@ccfcd9a:L70-81", "note": "WOC and FGR register on confirmation_ready with recordType" },
    { "id": 11, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/outbound-queue.clearer.ts@fa3f47a", "note": "clear after publish, every business; skip rules" },
    { "id": 13, "kind": "code", "ref": "apps/snap-adapter/src/http/controllers/event.controller.ts@fa3f47a", "note": "no confirmation_made route" },
    { "id": 14, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/confirmation-subscriptions.ts@fa3f47a", "note": "clear only if the source channel subscribes to the type" }
  ]
}
```

## Related

[[Engineering/snap-adapter/architecture|snap-adapter architecture]] ·
[[Engineering/snap-adapter/known-context|known-context]] ·
[[2026-08-24-work-order-lines-mirrored-across-both-snap-documents|why the WOC lines doubled]]
