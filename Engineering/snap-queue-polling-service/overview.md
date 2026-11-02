---
tags:
- waypoint
- snap-queue-polling-service
verified: '2026-10-13'
verified_sha: b16942a
verified_paths:
- README.md
- apps/snap-queue-polling-service/CLAUDE.md
- apps/snap-queue-polling-service/package.json
- apps/snap-queue-polling-service/src/adapters/gcs
- apps/snap-queue-polling-service/src/adapters/firestore
- apps/snap-queue-polling-service/src/core/config/remote-config.provider.ts
title: snap-queue-polling-service — overview
thesis: 'snap-queue-polling-service is the read side of the SnapFulfil integration:
  it turns SnapFulfil''s outbound queue into addressed canonical confirmations, then
  clears each published row itself.'
confidence: high
---
# snap-queue-polling-service — overview

```orient-bluf
{ "v": 1, "bluf": "snap-queue-polling-service is the read side of the SnapFulfil integration: it turns SnapFulfil's outbound queue into addressed canonical confirmations, then clears each published row itself.", "confidence": "high", "action": "Work in apps/snap-queue-polling-service inside the snap-adapter monorepo. The standalone repo of the same name is archived." }
```

## Responsibility

- Every 2 minutes it polls SnapFulfil's outbound queue (`/v2/snapoutbound`) for each eligible business [2].
- It maps queued rows into eight canonical confirmation types and publishes them to Pub/Sub [3].
- It addresses each publish to the connector that created the order, or broadcasts it when no origin exists.
- After a publish resolves, it clears the row off SNAP's queue. Nothing else clears published rows [1].
- Every 15 minutes it also runs the Shopify stock sync. It writes a JSONL export to GCS and publishes a pointer to it [4].

## Why it exists separately

The poller is a scheduled reader. Its sibling `snap-adapter` is an event-driven writer. The two have different lifecycles and deploy separately.

They share the WMS estate and the config-service `/backend` credentials. They share no code path. The monorepo keeps no root package so each app deploys on its own [8].

## Neighbours

```orient-flow
{ "v": 1, "title": "snap-queue-polling-service in context",
  "nodes": [
    { "id": "snap", "label": "SnapFulfil", "sub": "outbound queue", "kind": "external", "ev": [1] },
    { "id": "p", "label": "snap-queue-polling-service", "sub": "poll, map, publish, clear", "kind": "service", "service": "snap-queue-polling-service", "tone": "accent", "ev": [2, 3] },
    { "id": "ready", "label": "confirmation_ready", "sub": "+ stock_adjustment_ready", "kind": "topic", "ev": [3, 7] },
    { "id": "cons", "label": "Confirmation consumers", "sub": "sftp-connector, fapi, shopify-connector, collector", "kind": "external", "ev": [7] },
    { "id": "fail", "label": "confirmation_data_failure", "sub": "no-origin and partial-order notes", "kind": "topic", "ev": [3] },
    { "id": "fs", "label": "Firestore", "sub": "fuse-wms-routing, read-only", "kind": "store", "ev": [5, 10] },
    { "id": "sa", "label": "snap-adapter", "sub": "writes routing docs", "kind": "service", "service": "snap-adapter", "ev": [11] },
    { "id": "cs", "label": "config-service", "sub": "backends, connectors", "kind": "service", "service": "config-service", "ev": [6] },
    { "id": "redis", "label": "Redis", "sub": "claims, config cache", "kind": "store", "ev": [6] },
    { "id": "gcs", "label": "GCS bucket", "sub": "stock sync export", "kind": "store", "ev": [4] }
  ],
  "edges": [
    { "from": "snap", "to": "p", "label": "poll queue" },
    { "from": "p", "to": "snap", "label": "clear row after publish" },
    { "from": "p", "to": "ready", "label": "publish" },
    { "from": "ready", "to": "cons" },
    { "from": "p", "to": "fail", "style": "dashed" },
    { "from": "sa", "to": "fs", "label": "writes" },
    { "from": "fs", "to": "p", "label": "routing" },
    { "from": "cs", "to": "p", "label": "backends" },
    { "from": "p", "to": "redis" },
    { "from": "p", "to": "gcs", "label": "export" }
  ] }
```

Routing comes from the store `snap-adapter` writes at create time. The poller reads it to address each publish. Consumers filter on `recordType` and `source`, so a confirmation reaches its origin connector only.

## Where the reference lives

[[architecture]] carries the saga, topics, routing resolution, clearing and runtime. [[known-context]] carries incident history and the reasoning behind the gates.

The repo is `gfs-bifrost/snap-adapter`, app dir `apps/snap-queue-polling-service`. The wider Fuse team owns it, shared with `snap-adapter`. A same-named local checkout exists. It is the archived standalone repo and its pushes fail [8].

Search Datadog and Cloud Run for `snap-polling-service`, not the repo name. The repo name never appears there.

Do not trust three things:

- The repo `README.md` layout. It still shows `iac/<app>/` and a Jest `snap-adapter`.
- The app `CLAUDE.md` iac paths. The real stack is `iac/projects/snap-queue-polling-service` [9].
- Any note saying a downstream flow in `snap-adapter` clears published rows. That route is gone.

## What deliberately isn't here

- **Canonical record creation.** `snap-adapter` writes records into SnapFulfil. This service only reads confirmations back.
- **Customer delivery.** sftp-connector, fapi and shopify-connector turn a confirmation into a file or webhook. They also own mapping and use-case eligibility.
- **Business state.** There is no database. Redis holds cache and claim keys. Firestore is read-only here.
- **Routing metadata writes.** `snap-adapter` owns the Firestore database and the write path [10][11].
- **Topic definitions.** `bifrost-pubsub` owns the confirmation topics. This stack owns its four scheduler and fan-out topics.
- **Tracing.** Fuse has no APM. This service ships logs and custom metrics only.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/snap/confirmations/outbound-queue.clearer.ts@b16942a" },
  { "id": 2, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/polling/polling.service.ts@b16942a" },
  { "id": 3, "kind": "code", "ref": "apps/snap-queue-polling-service/src/bootstrap/factory/controller.factory.ts@b16942a" },
  { "id": 4, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/stock-sync/stock-sync.service.ts@b16942a" },
  { "id": 5, "kind": "code", "ref": "apps/snap-queue-polling-service/src/adapters/firestore/routing-metadata.reader.ts@b16942a" },
  { "id": 6, "kind": "code", "ref": "apps/snap-queue-polling-service/src/core/config/remote-config.provider.ts@b16942a" },
  { "id": 7, "kind": "doc", "ref": "fuse://pubsub-topology", "note": "publishers and subscribers of confirmation_ready and stock_adjustment_ready" },
  { "id": 8, "kind": "code", "ref": "README.md@b16942a" },
  { "id": 9, "kind": "code", "ref": "apps/snap-queue-polling-service/CLAUDE.md@b16942a" },
  { "id": 10, "kind": "code", "ref": "iac/projects/snap-queue-polling-service/iam.tf@b16942a" },
  { "id": 11, "kind": "code", "ref": "apps/snap-adapter/src/adapters/firestore/routing-metadata.store.ts@b16942a" }
] }
```
