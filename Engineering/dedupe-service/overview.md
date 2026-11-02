---
tags:
- waypoint
- dedupe-service
verified: '2026-10-13'
verified_sha: c8aa319
verified_paths:
- code/src
- CLAUDE.md
- iac/projects/dedupe-service
title: dedupe-service — overview
thesis: 'dedupe-service is the single gate between ingress and the WMS: it holds identical
  resends, strips blacklisted SKUs, and is the only production publisher of create_record.'
confidence: high
---
# dedupe-service — overview

```orient-bluf
{ "v": 1, "bluf": "dedupe-service is the single gate between ingress and the WMS: it holds identical resends, strips blacklisted SKUs, and is the only production publisher of create_record.", "confidence": "high", "action": "Do not move dedupe into a connector, and do not publish create_record from anywhere else." }
```

## Responsibility

- Every canonical record on `create_record_request` passes the gate. The gate holds an identical resend,
  strips blacklisted SKUs, and forwards the rest to `create_record` [2].
- It handles five record types: `sales_order`, `purchase_order`, `master_data`, `return_goods_authorization`
  and `work_order` [3].
- It stores every record it sees in MongoDB. A stored record is what makes a later identical resend a duplicate.
- It clears a stored record when a release or failure event arrives, or when support deletes it through the admin
  API [4].
- It keeps the per-business SKU blacklist in Redis and refreshes it on `config_revision`.

## Why it exists separately

The gate is a deliberate single choke point. Every ingress path inherits the same dedupe and blacklist rules
without reimplementing them. Connectors stay ignorant of dedupe.

The boundary is intentional. Dedupe logic does not move upstream into a connector, and a connector never
publishes `create_record` directly. The topology registry lists dedupe-service as the sole production
publisher [1]. This stack grants its service account publish rights on the topic [5].

## Neighbours

```orient-flow
{ "v": 1, "title": "dedupe-service in context",
  "nodes": [
    { "id": "ing", "label": "Ingress paths", "sub": "sftp-connector, fapi, shopify-connector, replay, fuse-mocker", "kind": "external", "ev": [1] },
    { "id": "req", "label": "create_record_request", "kind": "topic", "ev": [8] },
    { "id": "rel", "label": "release_* and create_data_failure", "sub": "clear a held record", "kind": "topic", "ev": [8] },
    { "id": "d", "label": "dedupe-service", "sub": "gate + blacklist", "kind": "service", "service": "dedupe-service", "tone": "accent", "ev": [2] },
    { "id": "out", "label": "create_record", "sub": "attributes.recordType", "kind": "topic", "ev": [5] },
    { "id": "sa", "label": "snap-adapter", "sub": "all 5 record types", "kind": "service", "service": "snap-adapter", "ev": [1] },
    { "id": "col", "label": "collector", "sub": "RGA only", "kind": "service", "service": "collector", "ev": [1] },
    { "id": "mongo", "label": "MongoDB", "sub": "held records", "kind": "store", "ev": [3] },
    { "id": "redis", "label": "Redis", "sub": "SKU blacklist", "kind": "store", "ev": [9] },
    { "id": "cs", "label": "config-service", "sub": "owns the blacklist", "kind": "service", "service": "config-service", "ev": [9] }
  ],
  "edges": [
    { "from": "ing", "to": "req" },
    { "from": "req", "to": "d" },
    { "from": "rel", "to": "d", "label": "release" },
    { "from": "d", "to": "out", "label": "forward" },
    { "from": "out", "to": "sa" },
    { "from": "out", "to": "col" },
    { "from": "d", "to": "mongo" },
    { "from": "d", "to": "redis" },
    { "from": "d", "to": "cs", "label": "blacklist on miss", "style": "dashed" }
  ] }
```

Upstream, five ingress paths publish to `create_record_request`. Downstream, snap-adapter consumes all five
record types from `create_record`, and collector consumes only RGA. fuse-ui and the Fuse MCP dedupe tools call
the admin API at `/api/v1/record` [4], per [[known-context]].

## Where the reference lives

[[architecture]] carries the routes, subscriptions, persistence and runtime. `CLAUDE.md` in the repo root is the
deep reference for dedupe semantics, the same-`correlationId` redelivery rule, the `IDeduper` contract and the
admin query surface [6]. Read it before you touch the gate.

Do not trust three sources:

- `README.md` still describes Firestore and a purchase-order-only service.
- `CLAUDE.md` is stale on counts and the create route. It says 12 subscriptions where 14 exist, and it calls
  the 204 unconditional, but the route acks after the work.
- [[known-context]] still describes an ack-first gate and a migration to NestJS that has not landed. Both are
  out of date: Nest owns every HTTP route [7].

## What deliberately isn't here

- **Canonical conversion.** Records arrive already canonical. Connectors own conversion.
- **Business mapping or enrichment.** The gate forwards the record it receives. Stripping blacklisted lines is
  gating, not mapping.
- **WMS knowledge.** Nothing here knows SnapFulfil exists. snap-adapter owns that.
- **Recovery of lost records.** The gate nacks a transient failure so Pub/Sub redelivers. replay-service owns
  anything beyond that.
- **Topics and the blacklist itself.** bifrost-pubsub defines the topics, and config-service owns the blacklist
  [10]. This service owns its subscriptions and a cached copy.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "doc", "ref": "fuse://pubsub-topology", "note": "publishers and subscribers of create_record_request and create_record" },
  { "id": 2, "kind": "code", "ref": "code/src/core/create-request.service.ts@c8aa319" },
  { "id": 3, "kind": "code", "ref": "code/src/factory.ts@c8aa319" },
  { "id": 4, "kind": "code", "ref": "code/src/http/controllers/record.controller.ts@c8aa319" },
  { "id": 5, "kind": "code", "ref": "iac/projects/dedupe-service/iam.tf@c8aa319" },
  { "id": 6, "kind": "code", "ref": "CLAUDE.md@c8aa319" },
  { "id": 7, "kind": "code", "ref": "code/src/bootstrap/main.ts@c8aa319" },
  { "id": 8, "kind": "code", "ref": "iac/projects/dedupe-service/pubsub.tf@c8aa319" },
  { "id": 9, "kind": "code", "ref": "code/src/core/cache/cache.service.ts@c8aa319" },
  { "id": 10, "kind": "code", "ref": "iac/projects/dedupe-service/remotes.tf@c8aa319" }
] }
```
