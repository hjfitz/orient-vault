---
tags:
- waypoint
- wms-gateway
verified_paths:
- README.md
- apps/gateway/cmd
- apps/gateway/openapi.yaml
- apps/gateway/internal/bootstrap
- apps/gateway/internal/core
- apps/gateway/internal/adapters/configservice
- iac/projects/wms-gateway
- iac/env
- .github/workflows/deploy.yaml
verified: '2026-10-13'
verified_sha: a23a517
title: wms-gateway — overview
thesis: wms-gateway is an internal, read-only Go gateway that resolves a business's
  WMS from config-service and returns bare canonical records; SNAP is the only WMS
  it fronts.
confidence: high
---
# wms-gateway — overview

```orient-bluf
{ "v": 1, "bluf": "wms-gateway is an internal, read-only Go gateway that resolves a business's WMS from config-service and returns bare canonical records; SNAP is the only WMS it fronts.", "confidence": "high", "action": "Keep it read-only and internal: add no WMS write, no publish and no customer auth here. fapi owns the public edge." }
```

## Responsibility

- Given a `businessId`, it reads that business's backend from config-service. It then reads the WMS record, maps it to the canonical shape and validates it [1][2].
- It returns the bare canonical record, with no `BifrostMessage` envelope [1].
- Three routes exist [3]:
  - a sales order by shipment
  - a paged list of stock positions (products and kits)
  - one position by SKU
- Stock comes from a per-business snapshot of SNAP, not a read per request. [[architecture]] has the mechanism.
- The one inbound event is config-service's `config_revision` push. It only drops cached backend config [4].

## Why it exists separately

- **Multiple WMSes are a goal.** The service is a WMS gateway, but the code is SNAP-shaped today. See [[known-context]].
- **Other teams may query it.** The Fuse team owns it, so its contract lives in its own `openapi.yaml`, not behind fapi's [3].
- **Credentials and the SNAP concurrency cap stay off the public edge.** snap-adapter cannot serve reads: it is write-only and event-driven.

## Neighbours

```orient-flow
{ "v": 1, "title": "wms-gateway in context",
  "nodes": [
    { "id": "fapi", "label": "fapi", "sub": "customer edge; stock routes return 501", "kind": "service", "service": "fapi", "ev": [7] },
    { "id": "gw", "label": "wms-gateway", "sub": "internal-only Cloud Run", "kind": "service", "service": "wms-gateway", "tone": "accent", "ev": [3, 5] },
    { "id": "cs", "label": "config-service", "sub": "backend config per business", "kind": "service", "service": "config-service", "ev": [2] },
    { "id": "snap", "label": "SnapFulfil WMS", "sub": "one host per business", "kind": "external", "ev": [2] },
    { "id": "redis", "label": "Redis", "sub": "response caches", "kind": "store", "ev": [6] },
    { "id": "rev", "label": "config_revision", "sub": "owned by bifrost-pubsub", "kind": "topic", "ev": [4, 6] }
  ],
  "edges": [
    { "from": "fapi", "to": "gw", "label": "planned proxy, not wired", "style": "dashed" },
    { "from": "gw", "to": "cs", "label": "GET /backend/{businessId}" },
    { "from": "gw", "to": "snap", "label": "GET, Basic auth" },
    { "from": "gw", "to": "redis" },
    { "from": "cs", "to": "rev", "label": "publishes" },
    { "from": "rev", "to": "gw", "label": "push", "style": "dashed" }
  ] }
```

**CONFIRMED** Nothing calls the gateway yet. fapi has no gateway URL or client, and its stock routes answer 501 until a proxy exists [7]. Cloud Run grants `run.invoker` to the Pub/Sub push account only, because `caller_service_account` is unset in both env files [5][8].

## Where the reference lives

[[architecture]] holds the guardrails, request path, interfaces, errors and the canonical codegen. [[operations]] holds deploy and failure modes. [[known-context]] holds intent and the SNAP behaviour the code relies on.

Do not trust three sources:

- `README.md` and `CLAUDE.md` still say `iac/` is empty and deployment is not wired. The `deploy.yaml` workflow and `iac/projects/wms-gateway` exist [5][9].
- The root `mise.toml` pins Go 1.25.1, but `go.mod` needs 1.27.1.
- Fuse MCP `services.json` held no entry for this service when it was last read in this vault. A dependency lookup now returns it.

## What deliberately isn't here

- **Customer auth, tenancy, rate limiting and the public OpenAPI.** fapi owns them.
- **Any WMS write, Pub/Sub publish or event envelope.** Every API route is a `GET` [3].
- **Choosing the WMS by request parameter.** The gateway resolves it from the business's backend config.
- **Business config storage.** config-service owns it; the gateway only reads and caches it [2].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "apps/gateway/internal/core/salesorder/salesorder.go@a23a517" },
  { "id": 2, "kind": "code", "ref": "apps/gateway/internal/adapters/configservice/request.go@a23a517" },
  { "id": 3, "kind": "code", "ref": "apps/gateway/internal/bootstrap/app.go@a23a517" },
  { "id": 4, "kind": "code", "ref": "apps/gateway/internal/core/configrevision/configrevision.go@a23a517" },
  { "id": 5, "kind": "code", "ref": "iac/projects/wms-gateway/iam.tf@a23a517" },
  { "id": 6, "kind": "code", "ref": "iac/projects/wms-gateway/pubsub.tf@a23a517" },
  { "id": 7, "kind": "url", "ref": "https://github.com/gfs-bifrost/fapi/blob/ced057d/code/src/http/controllers/api.controller.ts", "note": "fapi master: stock route documented as 501 until the gateway proxy is wired" },
  { "id": 8, "kind": "code", "ref": "iac/env/prod.tfvars@a23a517" },
  { "id": 9, "kind": "code", "ref": ".github/workflows/deploy.yaml@a23a517" }
] }
```
