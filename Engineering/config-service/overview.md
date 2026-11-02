---
tags:
- waypoint
- config-service
verified: '2026-10-13'
verified_sha: 63babd7
verified_paths:
- CLAUDE.md
- code/src/main.ts
- code/src/bootstrap
- code/src/core/pubsub
- code/src/http/events
- iac/projects/config-service
title: config-service — overview
thesis: 'config-service is the single source of truth for per-customer Fuse configuration:
  a REST API over MongoDB that announces every change on config_revision so cached
  readers refresh.'
confidence: high
---
# config-service — overview

```orient-bluf
{ "v": 1, "bluf": "config-service is the single source of truth for per-customer Fuse configuration: a REST API over MongoDB that announces every change on config_revision so cached readers refresh.", "confidence": "high", "action": "Do not treat config_revision as canonical bus traffic: it carries no recordType and no BifrostMessage<CanonicalX>." }
```

## Responsibility

- It stores businesses, storefronts, connectors with their per-use-case mappings, and Snap backend configs [1].
- It also stores warehouse routing, shipment methods, DDP rules and SKU blacklists [1].
- Every mutating write publishes a `config_revision` event after the Mongo write, so downstream caches refresh [2].
- It is the target of the Fuse MCP `config-write` tool. A change to a write endpoint's shape or validation changes what that tool can do [1].
- It receives one push event: the SFTP provisioning callback that writes `auth`, `user` and `isActive` onto a connector [3].

## Why it exists separately

Every other service treats customer setup as read-through-cache config and never owns a copy of it. Centralising it here is what makes the `@gfs-bifrost/remote-config` cache pattern coherent across the fleet.

**CONFIRMED** An outage is not a fleet-wide outage. Readers serve cached config (Redis plus an in-process LRU) and refresh off `config_revision`. What breaks at once is any new config change and any cold cache miss. Per [[known-context]], confirmed with the team on 2026-08-24.

## Neighbours

```orient-flow
{ "v": 1, "title": "config-service in context",
  "nodes": [
    { "id": "ui", "label": "fuse-ui", "sub": "full config CRUD", "kind": "service", "service": "fuse-ui" },
    { "id": "mcp", "label": "fuse-mcp-server", "sub": "config-read, config-write", "kind": "service", "service": "fuse-mcp-server" },
    { "id": "cs", "label": "config-service", "sub": "REST API, x-api-key", "kind": "service", "service": "config-service", "tone": "accent", "ev": [2, 4] },
    { "id": "mongo", "label": "MongoDB", "sub": "Atlas replica set", "kind": "store", "ev": [6] },
    { "id": "rev", "label": "config_revision", "sub": "owned by bifrost-pubsub", "kind": "topic", "ev": [2, 5] },
    { "id": "cons", "label": "Fuse services", "sub": "via remote-config cache", "kind": "external" },
    { "id": "sftp", "label": "sftp-connector", "sub": "provisions SFTP users", "kind": "service", "service": "sftp-connector" },
    { "id": "cc", "label": "customer_creation", "sub": "SFTP auth status", "kind": "topic", "ev": [3, 5] }
  ],
  "edges": [
    { "from": "ui", "to": "cs", "label": "HTTP" },
    { "from": "mcp", "to": "cs", "label": "HTTP" },
    { "from": "cs", "to": "mongo" },
    { "from": "cs", "to": "rev", "label": "best-effort publish" },
    { "from": "rev", "to": "cons", "label": "refresh" },
    { "from": "sftp", "to": "cc" },
    { "from": "cc", "to": "cs", "label": "push", "style": "dashed" }
  ] }
```

Most services call config-service over HTTP on a cache miss: fapi, snap-adapter, sftp-connector, shopify-connector, dedupe-service and wms-gateway among them. The topics belong to bifrost-pubsub. This service owns only its push subscription on `customer_creation` [5][7].

## Where the reference lives

[[architecture]] holds the runtime shape, the auth model, the event contracts and persistence. [[interfaces]] holds the full route table. `CLAUDE.md` in the repo root is the deep agent reference [1]. [[known-context]] holds the traps found along the way.

Do not trust three sources:

- `README.md` describes a pre-NestJS Express layout that no longer exists.
- The hand-written `code/openapi.yaml` is no longer served. The Nest-generated document at `/api/v1/docs-json` is the contract.
- The Fuse MCP catalogue says config-service publishes `customer_creation`. It subscribes to it.

**ASSESSED** The local checkout at `~/code/fuse/config-service` sits on a stale branch with uncommitted edits. Read `origin/main` through `git show`, not the working tree.

## What deliberately isn't here

- **Audit trail and session identity.** `updatedBy` is the constant `"admin"` [2]. A separate audit effort in fuse-ui snapshots before and after responses around each write.
- **Transactional publish.** The revision publish is best-effort and never fails the HTTP write. See [[architecture#publish-is-best-effort]].
- **Canonical data processing.** No ingest, dedupe or routing of orders or master data. The rest of the Fuse pipeline owns that.
- **The topics.** bifrost-pubsub defines `config_revision` and `customer_creation` [7].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "CLAUDE.md@63babd7" },
  { "id": 2, "kind": "code", "ref": "code/src/core/pubsub/config.dispatcher.ts@63babd7" },
  { "id": 3, "kind": "code", "ref": "code/src/http/events/events.controller.ts@63babd7" },
  { "id": 4, "kind": "code", "ref": "code/src/main.ts@63babd7" },
  { "id": 5, "kind": "code", "ref": "iac/projects/config-service/pubsub.tf@63babd7" },
  { "id": 6, "kind": "code", "ref": "iac/projects/config-service/mongo.tf@63babd7" },
  { "id": 7, "kind": "code", "ref": "iac/projects/config-service/remote.tf@63babd7" }
] }
```
