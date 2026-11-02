---
tags:
- waypoint
- fuse-mocker
verified: '2026-10-13'
verified_sha: 3da5077
verified_paths:
- README.md
- CLAUDE.md
- apps/api/internal/core/publisher/targets.go
- apps/snap-api/internal/bootstrap/app.go
- apps/snap-api/internal/http/snapwire/handler.go
- iac/projects/fuse-mocker
title: fuse-mocker — overview
thesis: fuse-mocker is a dev-only tool. It publishes mock canonical messages onto
  Fuse topics, and it simulates SnapFulfil so a dev business's real poller and adapter
  can round-trip against a fake warehouse.
confidence: high
---
# fuse-mocker — overview

```orient-bluf
{ "v": 1, "bluf": "fuse-mocker is a dev-only tool. It publishes mock canonical messages onto Fuse topics, and it simulates SnapFulfil so a dev business's real poller and adapter can round-trip against a fake warehouse.", "confidence": "high", "action": "Keep all four dev-only checks, and never point a production business at snap-api." }
```

## Responsibility

The repo holds two halves that share a Terraform stack and a Mongo cluster.

- **Publishing half** (`apps/api` in Go, `apps/ui` in Next.js). It sends mock canonical messages for a chosen dev customer. It covers one-off sends, generated payloads, presets, jittered schedules and burst or soak load runs. It also keeps an activity log, captures real confirmations for replay, and builds sample ingress files [1][2].
- **Simulator half** (`apps/snap-api`). It is a stateful fake SnapFulfil. It serves the WebAPIv2 wire that snap-adapter and the poller call, plus an operator control plane that advances warehouse state [3][4].
- The publishing half impersonates real producers: connectors and fapi on `create_record_request`, dedupe-service on `create_record`, the poller on the confirmation topics [1].
- It owns no customer data. It reads a dev customer's setup from config-service and caches it.

## Why it exists separately

Developers and agents need realistic canonical traffic against a real dev customer's config without touching a production system. No other service offers that.

The tool is dev-only by construction. Four independent layers enforce it. There is no production workflow and no `prod.tfvars`. Terraform's `env` validation rejects `prod`. Every app refuses to boot when `ENVIRONMENT` starts with `prod` [6][7].

The simulator is a separate app because its callers differ. The real poller and adapter reach it over HTTP as if it were a SnapFulfil tenant. Nothing in `apps/api` references it [3].

## Neighbours

```orient-flow
{ "v": 1, "title": "Publishing half: how a mock message enters Fuse",
  "nodes": [
    { "id": "mcp", "label": "fuse-mcp", "sub": "mock-* tools", "kind": "service", "service": "fuse-mcp", "ev": [12] },
    { "id": "ui", "label": "Operator UI", "sub": "apps/ui", "kind": "step", "ev": [2] },
    { "id": "api", "label": "fuse-mocker API", "sub": "apps/api", "kind": "service", "service": "fuse-mocker", "tone": "accent", "ev": [1, 2] },
    { "id": "cs", "label": "config-service", "sub": "dev customer setup", "kind": "service", "service": "config-service" },
    { "id": "db", "label": "MongoDB", "sub": "presets, schedules, activity", "kind": "store" },
    { "id": "t", "label": "Fuse topics", "sub": "create_record_request, create_record, confirmation_ready", "kind": "topic", "ev": [1] },
    { "id": "p", "label": "Fuse pipeline", "sub": "dedupe, snap-adapter, connectors", "kind": "external" }
  ],
  "edges": [
    { "from": "mcp", "to": "api", "label": "x-api-key" },
    { "from": "ui", "to": "api", "label": "session" },
    { "from": "api", "to": "cs", "label": "read config", "style": "dashed" },
    { "from": "api", "to": "db" },
    { "from": "api", "to": "t", "label": "publish parsed envelope" },
    { "from": "t", "to": "p" }
  ] }
```

The API publishes only canonical envelopes, always marked as mock. The UI and fuse-mcp are its two callers.

```orient-flow
{ "v": 1, "title": "Simulator half: the boundary with the real poller and adapter",
  "nodes": [
    { "id": "ops", "label": "Operator UI", "sub": "Snap section", "kind": "step", "ev": [3] },
    { "id": "sim", "label": "snap-api simulator", "sub": "/api/v1 control, /api/v2 wire", "kind": "service", "service": "fuse-mocker", "tone": "accent", "ev": [3, 4] },
    { "id": "db", "label": "MongoDB", "sub": "snap_entities, businesses", "kind": "store", "ev": [8] },
    { "id": "sa", "label": "snap-adapter", "sub": "writes orders", "kind": "service", "service": "snap-adapter", "ev": [4] },
    { "id": "sq", "label": "snap-queue-polling-service", "sub": "reads the queue", "kind": "service", "service": "snap-queue-polling-service", "ev": [4, 5] },
    { "id": "cs", "label": "config-service", "sub": "BACKEND_CONFIG host", "kind": "service", "service": "config-service", "ev": [9] },
    { "id": "t", "label": "confirmation_ready", "kind": "topic" },
    { "id": "c", "label": "Confirmation consumers", "sub": "fapi, sftp-connector, shopify-connector", "kind": "external" }
  ],
  "edges": [
    { "from": "ops", "to": "sim", "label": "seed, advance, arm faults" },
    { "from": "sa", "to": "sim", "label": "PUT /api/v2" },
    { "from": "sq", "to": "sim", "label": "GET queue, stock; PATCH processed" },
    { "from": "sim", "to": "db" },
    { "from": "cs", "to": "sq", "label": "host points at simulator", "style": "dashed" },
    { "from": "sq", "to": "t", "label": "builds confirmation" },
    { "from": "t", "to": "c" }
  ] }
```

The boundary is exact.

- **The simulator emits nothing onto Pub/Sub.** It has no Pub/Sub client and no config-service secret [8]. The real poller reads the queue and builds the confirmation.
- **A business needs two records.** config-service holds a `BACKEND_CONFIG` whose host is the simulator's URL plus `/api`. The simulator holds a tenant with the same credentials. Its `/api/v2` checks HTTP Basic against that tenant [9][11].
- **State moves only on operator command.** Writes arrive over `/api/v2`. An operator advances a shipment or receipt, or posts a stock adjustment, on `/api/v1`. Each transition drops an outbound-queue item the poller reads [3][5].
- **It serves only the routes it models.** A poller or adapter change that calls a new SnapFulfil route needs the simulator extended first [4].
- **Rows must satisfy the poller's schemas.** Despatch-stock rows carry every column the poller requires [10].
- **ASSESSED** The HJF dev business points at this simulator today. The org notes say so, and this pass did not read its config-service record.

## Where the reference lives

[[architecture]] holds the layout, publish contract, auth model, deployment shape and generated canonical layer. [[known-context]] holds the SNAP field lore behind the generators. Read it before simplifying one.

Do not trust three sources:

- The repo `CLAUDE.md` still describes two apps and two Cloud Run services. It omits `apps/snap-api` and the third service [13].
- `CLAUDE.md` says three legacy topics get no attributes. Two of them now stamp `recordType`; one remains bare [1].
- `lookup-service("fuse-mocker")` in the Fuse MCP still describes a Node-only stack.

## What deliberately isn't here

- **Production deployment.** The tool never runs in production. This is an enforced invariant, not a missing feature.
- **Hand-ported canonical types.** A generator builds the Go canonical layer from `@gfs-bifrost/types`, so there is no second source of truth.
- **A shared dependency tree.** There is no root workspace. Each app is its own module.
- **Real WMS behaviour beyond what the poller needs.** snap-api is a controllable fake. SnapFulfil itself and the real tenants are out of scope.
- **Customer configuration.** config-service owns it. The mocker only reads it.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "apps/api/internal/core/publisher/targets.go@3da5077" },
  { "id": 2, "kind": "code", "ref": "apps/api/internal/bootstrap/app.go@3da5077" },
  { "id": 3, "kind": "code", "ref": "apps/snap-api/internal/bootstrap/app.go@3da5077" },
  { "id": 4, "kind": "code", "ref": "apps/snap-api/internal/http/snapwire/handler.go@3da5077" },
  { "id": 5, "kind": "code", "ref": "apps/snap-api/internal/core/outboundqueue/outboundqueue.go@3da5077" },
  { "id": 6, "kind": "code", "ref": "apps/api/internal/config/config.go@3da5077" },
  { "id": 7, "kind": "code", "ref": "iac/projects/fuse-mocker/variables.tf@3da5077" },
  { "id": 8, "kind": "code", "ref": "iac/projects/fuse-mocker/cloud-run-snap-api.tf@3da5077" },
  { "id": 9, "kind": "code", "ref": "apps/snap-api/internal/http/controllers/businesses.go@3da5077" },
  { "id": 10, "kind": "code", "ref": "apps/snap-api/internal/core/wms/enrichment.go@3da5077" },
  { "id": 11, "kind": "code", "ref": "apps/snap-api/internal/core/tenant/tenant.go@3da5077" },
  { "id": 12, "kind": "code", "ref": "apps/api/scripts/mcp-contract-smoke.sh@3da5077" },
  { "id": 13, "kind": "code", "ref": "CLAUDE.md@3da5077" }
] }
```
