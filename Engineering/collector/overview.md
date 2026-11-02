---
tags:
- waypoint
- collector
verified: '2026-10-13'
verified_sha: 9c4d56d
verified_paths:
- README.md
- CLAUDE.md
- iac/projects/collector/pubsub.tf
- iac/projects/collector/cloud-run.tf
- code/src/core/stock-sync/stock-sync.service.ts
- code/src/models/constants.ts
- code/src/http/guards/api-key.guard.ts
- code/src/http/controllers/event.controller.ts
title: collector — overview
thesis: 'collector is Fuse''s read model: it taps the pipeline''s Pub/Sub topics,
  upserts each canonical record and confirmation into MongoDB, and serves them to
  fuse-ui. It never publishes.'
confidence: high
---
# collector — overview

```orient-bluf
{ "v": 1, "bluf": "collector is Fuse's read model: it taps the pipeline's Pub/Sub topics, upserts each canonical record and confirmation into MongoDB, and serves them to fuse-ui. It never publishes.", "confidence": "high", "action": "Keep collector observer-only: never publish, forward or dedupe from it." }
```

## Responsibility

- Taps the pipeline through 35 push subscriptions on the ingest, acknowledge, failure, release and confirmation topics [1].
- Validates each event against the canonical Zod schema from `@gfs-bifrost/types`. It then upserts one document per business key [2][4].
- Stores 13 collections: seven record types and six confirmation types [3]. The record types are purchase order, sales order, master data, work order, RGA, stock adjustment and stock sync run.
- Stamps a collector-owned `lifecycle.status` on each document from the events it sees: `pending`, `processing`, `processed` or `failed` [5].
- Serves the data to fuse-ui on `/api/v1/records` and on the older `/:businessId/*` routes. The v1 surface covers all 13 types and searches by reference [6][10].
- Copies each stock sync run's export and result files into its own bucket [9].
- Belongs to the Bifrost/Fuse team, with no separate on-call.

## Why it exists separately

Collector holds the one durable, queryable view of everything that moved through the pipeline, across all record types. Processing services keep their own state for their own jobs.

It has no path back into the pipeline, on purpose. Nothing downstream reads its output, and publishing from a read model would blur its job.

## Neighbours

```orient-flow
{ "v": 1, "title": "collector in context",
  "nodes": [
    { "id": "ing", "label": "Ingress paths", "sub": "sftp-connector, fapi, shopify-connector, replay", "kind": "external", "ev": [11] },
    { "id": "ded", "label": "dedupe-service", "kind": "service", "service": "dedupe-service", "ev": [11] },
    { "id": "sa", "label": "snap-adapter", "kind": "service", "service": "snap-adapter", "ev": [11] },
    { "id": "poll", "label": "snap-queue-polling-service", "kind": "service", "service": "snap-queue-polling-service", "ev": [11] },
    { "id": "egr", "label": "Egress connectors", "sub": "fapi, sftp-connector, shopify-connector, shopify-egress-service", "kind": "external", "ev": [11] },
    { "id": "c", "label": "collector", "sub": "read model", "kind": "service", "service": "collector", "tone": "accent", "ev": [1] },
    { "id": "m", "label": "MongoDB Atlas", "sub": "13 collections", "kind": "store", "ev": [3] },
    { "id": "b", "label": "collector-<env>-storage", "sub": "stock sync files", "kind": "store", "ev": [9] },
    { "id": "ui", "label": "fuse-ui", "kind": "service", "service": "fuse-ui", "ev": [6] }
  ],
  "edges": [
    { "from": "ing", "to": "c", "label": "create_record_request" },
    { "from": "ded", "to": "c", "label": "create_record (RGA)" },
    { "from": "sa", "to": "c", "label": "acknowledge, failure, release" },
    { "from": "poll", "to": "c", "label": "confirmation_ready" },
    { "from": "egr", "to": "c", "label": "confirmation_made, failure" },
    { "from": "c", "to": "m", "label": "upsert" },
    { "from": "c", "to": "b", "label": "copy" },
    { "from": "ui", "to": "c", "label": "api/v1/records" }
  ] }
```

Event arrows are push subscriptions, and most carry a `recordType` filter. Collector answers each one and publishes nothing. The known HTTP caller is fuse-ui, which reads with an API key [6][11].

## Where the reference lives

[[architecture]] holds the routes, subscriptions, persistence, lifecycle and runtime. [[reference-search]] explains the `?reference=` query. [[known-context]] holds history and traps. The repo's `CLAUDE.md` is the working reference [13].

Do not trust these sources:

- `README.md` is the untouched repository template.
- The `@dedupe/core` package name [12] and any dedupe-shaped metric name are fork leftovers. Collector does no deduplication.
- `CLAUDE.md` is wrong on at least four points:
  - It calls the stock adjustment key unscoped.
  - It calls the guard's path skip dead code. **ASSESSED** The business routes make it live; see [[architecture]].
  - It says the master-data summary pages in memory.
  - It gives the dockerfile pnpm version as 11.0.8.
- The claim that Cloud Run's OIDC gate protects the ingest routes. `cloud-run.tf` grants `run.invoker` to `allUsers` [8], so **ASSESSED** the routes accept any caller that reaches the URL.
- The Fuse MCP's collector entry says work orders are not collected. They are, off `create_record_request` [1].

## What deliberately isn't here

- **Deduplication.** dedupe-service owns it. A repeat lands on the same document and moves nothing else.
- **Publishing.** Nothing here publishes, and the pipeline never reads collector.
- **Work order lifecycle.** Collector subscribes only to the request, so a work order stays `pending`.
- **Pick and pack lifecycle.** Collector stores both, and their `status` stays null.
- **Stock sync failure.** The run goes `pending`, then `processed`. No failure subscription exists.
- **RGA release.** The platform deprecated RGA release, and no `release_return_goods_authorization` topic exists.
- **Ingest authentication.** No guard covers `events/v1/*` [2][7].
- **Mapping or enrichment.** Collector stores the canonical as it arrives.
- **Topic definitions.** bifrost-pubsub owns the topics. This service owns its subscriptions.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "iac/projects/collector/pubsub.tf@9c4d56d", "note": "35 subscriptions, filters, push routes" },
  { "id": 2, "kind": "code", "ref": "code/src/http/controllers/event.controller.ts@9c4d56d" },
  { "id": 3, "kind": "code", "ref": "code/src/models/constants.ts@9c4d56d", "note": "13 collections, 7 use cases, 6 confirmation types" },
  { "id": 4, "kind": "code", "ref": "code/src/repositories/collection.ts@9c4d56d" },
  { "id": 5, "kind": "code", "ref": "code/src/models/lifecycle.ts@9c4d56d" },
  { "id": 6, "kind": "code", "ref": "code/src/http/controllers/records.controller.ts@9c4d56d" },
  { "id": 7, "kind": "code", "ref": "code/src/http/guards/api-key.guard.ts@9c4d56d" },
  { "id": 8, "kind": "code", "ref": "iac/projects/collector/cloud-run.tf@9c4d56d" },
  { "id": 9, "kind": "code", "ref": "code/src/core/stock-sync/stock-sync.service.ts@9c4d56d" },
  { "id": 10, "kind": "code", "ref": "code/src/http/controllers/business.controller.ts@9c4d56d" },
  { "id": 11, "kind": "doc", "ref": "fuse://pubsub-topology", "note": "publishers of each subscribed topic" },
  { "id": 12, "kind": "code", "ref": "code/package.json@9c4d56d" },
  { "id": 13, "kind": "code", "ref": "CLAUDE.md@9c4d56d" }
] }
```
