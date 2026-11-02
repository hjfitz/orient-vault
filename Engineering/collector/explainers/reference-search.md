---
tags: [waypoint, explainer, collector]
thesis: "The v1 records list route takes one `?reference=` value and returns every non-deleted record of that type, for that business, whose declared reference fields, correlation id or `_id` equal it (or its `#`-toggled twin), from an index-only top-level `$or` paged newest-first."
confidence: high
updated: 2026-10-12
verified: 2026-10-12
verified_sha: 9c4d56d
verified_paths:
  - code/src/core/reference-search.ts
  - code/src/repositories/collection.ts
  - code/src/http/pipes/reference-search.pipe.ts
  - code/src/http/controllers/records.controller.ts
  - code/src/core/use-case-registry.service.ts
  - code/src/core/confirmation-registry.service.ts
  - code/src/core/use-cases.service.ts
  - code/src/models/constants.ts
  - code/src/scripts/ensure-indexes.ts
  - code/src/__test__/integration/reference-search-index-coverage.spec.ts
  - code/package.json
drifted_evidence: []
drift_checked: 2026-10-12
commits_behind: 0
---
# Reference search on the v1 records API

```orient-bluf
{
  "v": 1,
  "bluf": "The v1 records list route takes one `?reference=` value and returns every non-deleted record of that type, for that business, whose declared reference fields, correlation id or `_id` equal it (or its `#`-toggled twin), from an index-only top-level `$or` paged newest-first.",
  "confidence": "high",
  "action": "none"
}
```

## Mechanism

**CONFIRMED** `GET /api/v1/records/:recordType/:businessId?reference=<value>` is the only search surface. Without `reference`, the same route lists the type newest-first. [3][4]

```orient-flow
{
  "v": 1,
  "title": "Reference search path",
  "nodes": [
    { "id": "q", "label": "?reference=#11435", "kind": "external", "ev": [3] },
    { "id": "p", "label": "ReferenceSearchPipe", "sub": "one plain string, trimmed, 1-256", "kind": "step", "ev": [2] },
    { "id": "e", "label": "400", "kind": "external", "tone": "alert", "ev": [2] },
    { "id": "b", "label": "referenceSearchBranches", "sub": "field x variant, plus _id if 24-hex", "kind": "step", "tone": "accent", "ev": [1] },
    { "id": "o", "label": "top-level $or", "sub": "bizKey + deletedAt: null per branch", "kind": "step", "ev": [5] },
    { "id": "i", "label": "per-path index", "sub": "bizKey, path, deletedAt, createdAt desc, _id desc", "kind": "store", "ev": [1] },
    { "id": "r", "label": "paged response", "sub": "total, offset, count, data", "kind": "step", "ev": [4] }
  ],
  "edges": [
    { "from": "q", "to": "p" },
    { "from": "p", "to": "e", "label": "invalid", "style": "dashed" },
    { "from": "p", "to": "b" },
    { "from": "b", "to": "o" },
    { "from": "o", "to": "i" },
    { "from": "i", "to": "r", "label": "sorted merge" }
  ]
}
```

- **CONFIRMED** `ReferenceSearchPipe` rejects a blank value, a repeated or bracketed `reference`, and anything over 256 characters with a 400. It trims the value first. Mongo never sees an operator object. [2]
- **CONFIRMED** `count` defaults to 10 with a maximum of 100. `offset` defaults to 0. [3]
- **CONFIRMED** Every searchable path gets one branch per variant. The paths are the type's reference fields plus `metadata.correlationId`. The twin variant adds or removes a leading `#`. [1]
- **CONFIRMED** A value of 24 hex characters also gets an `_id` branch. [1]
- **CONFIRMED** Each branch carries the type's business key and `deletedAt: null`. Other businesses and soft-deleted records never match. [1][5]
- **CONFIRMED** The branches form one top-level `$or`, sorted `lifecycle.createdAt` descending, then `_id` descending. [1][4][5]
- **CONFIRMED** `referenceSearchIndexes` derives one compound index per searchable path. Each index leads with the business key and ends in the sort keys. [1]
- **CONFIRMED** Each registry entry declares its reference fields once. The same list feeds the indexes and the branches. [6][7]
- **CONFIRMED** A record matching on several fields appears once, because the `$or` selects documents. No match returns 200 with `total: 0`. [4][5]
- **CONFIRMED** Every v1 record carries a top-level `correlationId` lifted from its stored metadata. [5]

**CONFIRMED** Each type searches the fields below, exact and case-sensitive, besides correlation id and `_id`. [6][7]

| Record type | Reference fields |
| --- | --- |
| `sales_order` | `order.customerRef`, `customer.order`, `identifiers.salesOrder` |
| `purchase_order` | `supplier.reference`, `identifiers.purchaseOrder`, `identifiers.businessOrderNumber`, `identifiers.id` |
| `goods_in_confirmation` | `order.supplierRef`, `order.purchaseOrder` |
| `goods_out_confirmation` | `order.customerRef`, `order.customerOrder`, `customer.order`, `order.salesOrder`, `identifiers.shipmentId` |
| `pick_confirmation`, `pack_confirmation` | `identifiers.customerRef`, `order.customerOrder`, `identifiers.salesOrder`, `identifiers.shipmentId` |
| `work_order` | `workOrder.customerRef`, `identifiers.salesOrder` |
| `work_order_confirmation` | `workOrder.customerRef`, `identifiers.id` |
| `finished_good_receipt` | `customer.reference`, `identifiers.businessReceiptId`, `identifiers.id` |
| `return_goods_authorization` | `identifiers.businessRgaNumber` |
| `stock_adjustment` | `identifiers.reference`, `identifiers.id` |
| `stock_sync` | `identifiers.connectorId`, `identifiers.runId` |
| `master_data` | `product.identifiers.skuId` |

## Boundaries

- **CONFIRMED** One request searches one record type. A caller that wants every type fans out itself. [3][8]
- **CONFIRMED** Matching is exact. The `#` twin is the only normalisation. [1]
- **CONFIRMED** A correlation id finds only a record's latest ingest. Each save overwrites `metadata` with the new envelope's metadata. An id from an older log line can find nothing. [5]
- **CONFIRMED** The legacy `/:businessId/*` routes have no `reference` parameter and return no `correlationId`. [3]
- **CONFIRMED** The plain list, without `reference`, sorts on `lifecycle.createdAt` alone. Search pages add the `_id` tiebreak and stay deterministic. [4]

## Constraints

- **CONFIRMED** The query shape is load-bearing. Wrapping the `$or` in an `$and`, as `withNotDeleted` does, loses the index-only plan. [1][5]
- **CONFIRMED** Hoisting the business key or `deletedAt` out of the branches loses it too. So does merging the `#` twin into a two-value `$in`. [1][5]
- **CONFIRMED** The integration spec runs `explain()` against the real registry indexes on an in-memory Mongo. It fails on a collection scan or in-memory sort. It fails when the find examines more than one page of documents, or when the count examines any. [10]
- **ASSESSED** Without that plan, a high-fanout value, such as a bulk file's shared correlation id, makes the count fetch the whole business. The spec's control collection, built without the search indexes, examines documents. [10]
- **CONFIRMED** Only a plain string may reach Mongo. The pipe exists because the query parser would otherwise hand Mongo an operator object. [2]
- **CONFIRMED** Indexes build at boot. Each registry's `onModuleInit` calls `ensureIndexes()` on every collection it declares. [6][7]
- **CONFIRMED** `pnpm run ensure:indexes` pre-builds the same indexes before a deploy. It reports what it created per collection. [9][11]
- **ASSESSED** The Record ID fields mirror fuse-ui's `refPaths`. A change to one list needs a change to the other, or search stops finding what the page displays. The collector repo's own docs state the pairing. This pass did not read fuse-ui.

## Evidence

```orient-evidence
{
  "v": 1,
  "items": [
    { "id": 1, "kind": "code", "ref": "code/src/core/reference-search.ts@9c4d56d", "note": "variants, branches, per-path indexes, sort" },
    { "id": 2, "kind": "code", "ref": "code/src/http/pipes/reference-search.pipe.ts@9c4d56d", "note": "plain string, trimmed, 1-256, else 400" },
    { "id": 3, "kind": "code", "ref": "code/src/http/controllers/records.controller.ts@9c4d56d", "note": "v1 list route, count and offset pipes, reference query" },
    { "id": 4, "kind": "code", "ref": "code/src/core/use-cases.service.ts@9c4d56d", "note": "search branch vs plain list, paged shape" },
    { "id": 5, "kind": "code", "ref": "code/src/repositories/collection.ts@9c4d56d", "note": "findAnyPaginatedWithLifecycle, correlationId lift, save overwrites metadata" },
    { "id": 6, "kind": "code", "ref": "code/src/core/use-case-registry.service.ts@9c4d56d", "note": "reference fields and indexes for non-confirmation types" },
    { "id": 7, "kind": "code", "ref": "code/src/core/confirmation-registry.service.ts@9c4d56d", "note": "reference fields and indexes for confirmation types" },
    { "id": 8, "kind": "code", "ref": "code/src/models/constants.ts@9c4d56d", "note": "served record types" },
    { "id": 9, "kind": "code", "ref": "code/src/scripts/ensure-indexes.ts@9c4d56d", "note": "pre-build script runs both registries" },
    { "id": 10, "kind": "code", "ref": "code/src/__test__/integration/reference-search-index-coverage.spec.ts@9c4d56d", "note": "explain() assertions per served type" },
    { "id": 11, "kind": "code", "ref": "code/package.json@9c4d56d", "note": "ensure:indexes script" }
  ]
}
```

## Related

- [[architecture]] covers query API gotchas, persistence and guardrails
- [[known-context]] explains why an old correlation id misses
