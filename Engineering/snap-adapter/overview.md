---
tags:
- waypoint
- snap-adapter
verified: '2026-10-13'
verified_sha: b16942a
verified_paths:
- README.md
- apps/snap-adapter/CLAUDE.md
- apps/snap-adapter/package.json
- apps/snap-adapter/src/adapters/firestore
- apps/snap-adapter/src/adapters/snap
- apps/snap-adapter/src/http/controllers/event.controller.ts
- iac/projects/snap-adapter/pubsub.tf
- apps/snap-queue-polling-service/src/core/snap/confirmations/outbound-queue.clearer.ts
title: snap-adapter — overview
thesis: 'snap-adapter is the write side of the SnapFulfil integration: it turns each
  canonical create_record event into a keyed upsert in SNAP and records routing data
  before it writes. It clears nothing off SNAP''s queue.'
confidence: high
---
# snap-adapter — overview

```orient-bluf
{ "v": 1, "bluf": "snap-adapter is the write side of the SnapFulfil integration: it turns each canonical create_record event into a keyed upsert in SNAP and records routing data before it writes. It clears nothing off SNAP's queue.", "confidence": "high", "action": "Work in apps/snap-adapter inside the snap-adapter monorepo. Never add a queue clear-down here; the poller owns it." }
```

## Responsibility

- It consumes `create_record` events for five record types: `sales_order`, `purchase_order`, `master_data`, `return_goods_authorization` and `work_order` [1][2].
- It maps each canonical record to SnapFulfil's API shape and writes it with a keyed `PUT`. Receipts and shipments carry a deterministic id, so a redelivery upserts [4][7].
- Before each create it writes routing provenance, and sales-order line data, to the `fuse-wms-routing` Firestore database [5].
- It publishes the outcome: `create_acknowledge` on success, `create_data_failure` on a terminal failure, and `release_*` for the three legacy types [2][3].
- It caches backend credentials and shipment methods in Redis, and refreshes them on `config_revision`.
- It exposes two routes under `/events/v1`, plus `/health/liveness` [2].

## Why it exists separately

The adapter is an event-driven Pub/Sub consumer. Its sibling `snap-queue-polling-service` is a scheduled poller. The two have different lifecycles and scale, roll back and deploy independently.

Each app keeps its own toolchain: `mise.toml`, lockfile, `audit-ci.jsonc` and Dockerfile. No root workspace ties them together. Both run Vitest [6].

The service is high stakes. If it is down or backed up, new orders, purchase orders, master data, RGAs and work orders do not reach the warehouse. **ASSESSED** A bad enough outage can lose orders, because the team knows of no consumer on the `create_record` dead-letter topic. See [[known-context#no-consumer-on-the-dead-letter-topic]].

## Neighbours

```orient-flow
{ "v": 1, "title": "snap-adapter in context",
  "nodes": [
    { "id": "dd", "label": "dedupe-service", "sub": "sole create_record publisher", "kind": "service", "service": "dedupe-service" },
    { "id": "cr", "label": "create_record", "sub": "5 filtered subscriptions", "kind": "topic", "ev": [3] },
    { "id": "sa", "label": "snap-adapter", "sub": "map, route, write", "kind": "service", "service": "snap-adapter", "tone": "accent", "ev": [2] },
    { "id": "snap", "label": "SnapFulfil", "sub": "keyed PUT per record", "kind": "external", "ev": [4] },
    { "id": "fs", "label": "fuse-wms-routing", "sub": "Firestore", "kind": "store", "ev": [5] },
    { "id": "poller", "label": "snap-queue-polling-service", "sub": "read side", "kind": "service", "service": "snap-queue-polling-service" },
    { "id": "ack", "label": "create_acknowledge", "kind": "topic", "ev": [2] },
    { "id": "fail", "label": "create_data_failure", "kind": "topic", "ev": [2] },
    { "id": "rel", "label": "release_*", "sub": "sales_order, purchase_order, master_data", "kind": "topic", "ev": [2] }
  ],
  "edges": [
    { "from": "dd", "to": "cr" },
    { "from": "cr", "to": "sa", "label": "OIDC push" },
    { "from": "sa", "to": "snap", "label": "create" },
    { "from": "sa", "to": "fs", "label": "write first" },
    { "from": "poller", "to": "fs", "label": "reads", "style": "dashed" },
    { "from": "poller", "to": "snap", "label": "polls and clears queue" },
    { "from": "sa", "to": "ack" },
    { "from": "sa", "to": "fail" },
    { "from": "sa", "to": "rel" }
  ] }
```

dedupe-service is the only production publisher of `create_record`. It also consumes `release_*` and `create_data_failure` to clear its held record. The poller reads the routing store this service writes, and it alone clears SNAP's outbound queue. Connectors and the collector consume `create_acknowledge`.

## Where the reference lives

- [[architecture]] carries the routes, subscriptions, create flow, routing store, SNAP write handling and runtime.
- [[known-context]] carries the dead-letter gap and the reasoning behind the SNAP limits. Re-check any implementation detail there against code.
- `apps/snap-adapter/CLAUDE.md` is the doc of record for SnapFulfil write nuance (RGA creation, deterministic ids, segmented responses). Read it before touching a create path [4].
- [[read-before-write-create-path]] explains the sales-order precheck. [[work-order-family-confirmations]] explains the two work-order confirmations the poller emits.

Do not trust the repo `README.md`. It says the adapter runs Jest and lists `iac/snap-adapter/`. The app runs Vitest and its stack is `iac/projects/snap-adapter` [6][8].

The monorepo is `gfs-bifrost/snap-adapter`. No archived repo shares its name. The wider Fuse team owns it, shared with the poller.

## What deliberately isn't here

- **Clearing SNAP's outbound queue.** The poller clears every published confirmation. The adapter has no `confirmation_made` route or subscription left [9][10].
- **A business-state database.** The only store it owns is the routing database, and the poller reads it. Redis holds config only.
- **A `release_*` topic for RGA and work orders.** Their failures clear the deduper through `create_data_failure`. This asymmetry is deliberate [2].
- **Tracing.** There is no APM. It emits logs and custom metrics.
- **Confirmation mapping.** The poller turns SNAP rows into canonical confirmations.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "apps/snap-adapter/src/adapters/snap/snap-entity.type.ts@b16942a" },
  { "id": 2, "kind": "code", "ref": "apps/snap-adapter/src/http/controllers/event.controller.ts@b16942a" },
  { "id": 3, "kind": "code", "ref": "iac/projects/snap-adapter/pubsub.tf@b16942a" },
  { "id": 4, "kind": "code", "ref": "apps/snap-adapter/CLAUDE.md@b16942a" },
  { "id": 5, "kind": "code", "ref": "apps/snap-adapter/src/adapters/firestore/routing-metadata.store.ts@b16942a" },
  { "id": 6, "kind": "code", "ref": "apps/snap-adapter/package.json@b16942a" },
  { "id": 7, "kind": "code", "ref": "apps/snap-adapter/src/shared/identity-helper/create-deterministic-id.ts@b16942a" },
  { "id": 8, "kind": "code", "ref": "README.md@b16942a" },
  { "id": 9, "kind": "pr", "ref": "gfs-bifrost/snap-adapter#294" },
  { "id": 10, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/outbound-queue.clearer.ts@b16942a" }
] }
```
