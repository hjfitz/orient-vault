---
tags:
- waypoint
- tracking-service
title: tracking-service — architecture
thesis: One Go binary takes Pub/Sub pushes on /events/v1/{topic}/{recordType}, folds
  each event into a per-order ledger in one MongoDB transaction with an order-independent
  reducer, and serves derived records from /api/v1. Identity is business + customer
  reference; every served field is recomputed from the ledger.
confidence: high
verified: '2026-10-15'
verified_sha: 9f01957
verified_paths:
- apps/api/internal
- apps/api/cmd
- iac/projects/tracking-service
---
# tracking-service — architecture

```orient-bluf
{ "v": 1, "bluf": "One Go binary takes Pub/Sub pushes on /events/v1/{topic}/{recordType}, folds each event into a per-order ledger in one MongoDB transaction with an order-independent reducer, and serves derived records from /api/v1. Identity is business + customer reference; every served field is recomputed from the ledger.", "confidence": "high", "action": "Never join on the Snap ShipmentId, and never count a flip of a derived flag: identity is business + customer reference, and a failure counts once (G1, G2)." }
```

## Guardrails
- [contract:G1] A shipment's identity is business + normalised customer reference (then `~SO:`, then `~SNAP:`); a return's is business + RGA number. The Snap ShipmentId is display and search only, never a join key.
  — paths: apps/api/internal/core/extract.go, apps/api/internal/core/snapid.go
- [technical:G2] Count a record once, on its first failure of each kind, through `Ledger.FirstFailures` and `FailureMarks`. Never count a flip of a derived flag. Stats are summed on read from each record's marks, plus `keptCounters`/`returnKeptCounters` for history no record holds; nothing increments a shared counter.
  — paths: apps/api/internal/core/failures.go, apps/api/internal/store/marks.go, apps/api/internal/store/mongo_marks.go
- [technical:G3] The reducer must not depend on arrival order: every derived field is a min, max, set union or `FactKey` max in the ledger, ordered by Pub/Sub `publishTime`. The shuffle tests in `core` are the contract.
  — paths: apps/api/internal/core/reduce.go, apps/api/internal/core/returns_reduce.go
- [technical:G4] A query change needs its index in `mongo_indexes.go` (`EnsureIndexes` creates them on start). `mongo_explain_test.go` fails when a query shape plans to a COLLSCAN or a blocking sort, or a declared index serves no shape.
  — paths: apps/api/internal/store/mongo_indexes.go, apps/api/internal/store/mongo_explain_test.go
- [policy:G5] Backfills and `recompute-stats` run against prod by a human, dry-run first; `recompute-stats` with ingest held. Gate stored-state remaps on `ledgerVersion`, never on field presence.
  — paths: apps/api/cmd, apps/api/internal/core/upgrade.go
- [contract:G6] Cross-entity topics are subscribed one recordType per subscription with a Terraform `filter`; goods-out is `goods_out_confirmation` on both ready and made. Never discriminate in code.
  — paths: iac/projects/tracking-service/pubsub.tf

## Structure
```orient-flow
{ "v": 1, "title": "Ingest path",
  "nodes": [
    { "id": "push", "label": "POST /events/v1/{topic}/{recordType}", "sub": "http/push.go", "kind": "service", "ev": [1] },
    { "id": "decode", "label": "Decode envelope", "sub": "core/decode.go, extract.go", "kind": "service", "ev": [2] },
    { "id": "dedupe", "label": "Republish check", "sub": "content hash per dedupe group", "kind": "service", "ev": [3] },
    { "id": "reduce", "label": "Reducer + rules", "sub": "ledger → derive, attention", "kind": "service", "tone": "accent", "ev": [4] },
    { "id": "fs", "label": "MongoDB txn", "sub": "record + event doc + marks + seen row", "kind": "store", "ev": [5] }
  ],
  "edges": [
    { "from": "push", "to": "decode" },
    { "from": "decode", "to": "dedupe" },
    { "from": "dedupe", "to": "reduce", "label": "new content" },
    { "from": "reduce", "to": "fs" }
  ] }
```
Imports flow `cmd → http → core → store/model`, never `store → core`. `internal/config` is the only
package that reads env [6].

| Package | Holds |
|---|---|
| `cmd/api` | Wiring only |
| `cmd/redrive`, `cmd/backfill-*`, `cmd/recompute-stats` | One-off tools over the same core |
| `internal/http` | Handlers, DTOs, metrics emission, the minute gauges |
| `internal/core` | All logic: decode, items, reducer, rules (preexisting, deadlines, attention), summary, insights, queries, returns |
| `internal/store` | `Store` interface; MongoDB and in-memory implementations |
| `internal/model` | Types only |

## Interfaces
**In.** 20 push subscriptions, `tracking-service.{env}.<topic>.<recordType>.v1.sub` [7]:

| Topic | recordTypes |
|---|---|
| `create_record_request`, `create_record`, `create_acknowledge`, `create_data_failure` | `sales_order`, `return_goods_authorization` |
| `confirmation_ready`, `confirmation_made` | `pick_confirmation`, `pack_confirmation`, `goods_out_confirmation`, `return_goods_authorization` |
| `confirmation_data_failure` | `pick_confirmation`, `pack_confirmation`, `goods_out_confirmation`, `return_goods_confirmation` |

Responses: `204` for handled, redelivered, republished or unprocessable (logged at `WARNING`); `500`
only on a store error; `503` while `INGEST_HOLD=true`. Dead-lettering after 5 attempts into a
per-subscription DLT with a 7-day `.dlt.sub` hold [7].

**Read API.** `/api/v1` shipments and returns: search, bulk lookup, CSV export, detail by id or by
business + reference, events, notes (writable), stats, per-business stats, insights, businesses. The
contract is `apps/api/openapi.yaml`; fuse-ui vendors a copy [1].

**Out.** None. It publishes nothing and calls no other service.

## Persistence
MongoDB Atlas: an M10 cluster `tracking-service-{env}` (autoscaling to M20, backup and point-in-time
recovery, termination protection in prod), database `tracking-service-{env}`, reached through
`MONGODB_URI`/`MONGODB_DATABASE` [8]. Each record type keeps its records, events, marks and notes in
collections of its own (`shipments`, `shipmentEvents`, `shipmentMarks`, `shipmentNotes`, and the
`return*` twins), plus `keptCounters`/`returnKeptCounters` for imported history such as the frozen
`duplicates`, and `seen`. Large blobs (`ledgerJson`, `recordJson`, `timelineJson` …) are opaque JSON
strings. Only `seen` has a TTL (8 days, past Pub/Sub's retention); everything else is kept forever.
Stats, insights and the businesses list are aggregated on read [5].

Firestore served until the 2026-11-11 cut. Both databases were deleted on 2026-11-12, after a final
export to the tracking-service migration bucket (30-day lifecycle).

Idempotency: an event doc's id is the `messageId` (`messageId-i` for bulk), and every applied delivery
also writes a `seen` row in the same transaction; `Apply` is a no-op when either exists. A republished copy (same content hash in its dedupe group) writes no event and is counted
on the record [3]. `core.Upgrade` runs on every read, so a `ledgerVersion` bump re-derives lazily, and
`backfill-upgrade` makes it eager.

## Runtime
Cloud Run `tracking-service-api-{env}` (europe-west2), port 8080, `/health`, 0–3 instances,
IAM-private, with a Datadog serverless-init sidecar when `DATADOG_ENABLED=true` [9]. Deploy is
`deploy.yaml`: push to `main` applies dev, then prod behind the `terraform-prod` environment.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "apps/api/internal/http/router.go@9f01957" },
  { "id": 2, "kind": "code", "ref": "apps/api/internal/core/decode.go@9f01957" },
  { "id": 3, "kind": "code", "ref": "apps/api/internal/core/dedupe.go@9f01957" },
  { "id": 4, "kind": "code", "ref": "apps/api/internal/core/reduce.go@9f01957" },
  { "id": 5, "kind": "code", "ref": "apps/api/internal/store/mongo.go@e34d821" },
  { "id": 6, "kind": "code", "ref": "apps/api/CLAUDE.md@9f01957" },
  { "id": 7, "kind": "code", "ref": "iac/projects/tracking-service/pubsub.tf@9f01957" },
  { "id": 8, "kind": "code", "ref": "iac/projects/tracking-service/mongo.tf@e34d821" },
  { "id": 9, "kind": "code", "ref": "iac/projects/tracking-service/cloud-run-api.tf@9f01957" }
] }
```
