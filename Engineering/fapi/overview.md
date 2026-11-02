---
tags:
- waypoint
- fapi
verified: '2026-10-13'
verified_sha: ced057d
verified_paths:
- README.md
- CLAUDE.md
- code/src/services/confirmation.service.ts
- code/src/services/pubsub-emitter.ts
- code/src/http/controllers/api.controller.ts
- code/src/http/controllers/legacy.controller.ts
- code/src/http/controllers/health.controller.ts
- code/src/http/guards/remote-config-guard.ts
- code/src/config/config.service.ts
- code/src/http/interceptors/rate-limit.interceptor.ts
- iac/projects/api-gateway/pubsub.tf
title: fapi — overview
thesis: 'fapi is the public REST edge of Fuse: it validates customer records into
  create_record_request, forwards WMS confirmations to customer webhooks, and keeps
  a config cache warm.'
confidence: high
---
# fapi — overview

```orient-bluf
{ "v": 1, "bluf": "fapi is the public REST edge of Fuse: it validates customer records into create_record_request, forwards WMS confirmations to customer webhooks, and keeps a config cache warm.", "confidence": "high", "action": "Do not add a customer route without tenancy enforcement, and do not treat API_KEY as an auth path." }
```

## Responsibility

The repo is `gfs-bifrost/fapi`. The Cloud Run service and iac project are `api-gateway`. The app logs as `bifrost-api`.
All three names mean this service. The Bifrost/Fuse team owns it. It runs three independent flows [1]:

- **Ingress.** A customer system POSTs records over HTTP Basic auth. fapi validates them and publishes each one to `create_record_request` [2][5].
  The v2 routes take canonical records. The v1 routes take ILG-shaped JSON or CSV and map them to canonical [11].
- **Egress.** Pub/Sub pushes WMS confirmations to fapi. fapi POSTs each to the customer's registered webhook [3].
  It then publishes `confirmation_made` once at least one delivery succeeds [4].
  fapi records a confirmation that should have reached a REST connector and did not as a `confirmation_data_failure` against that connector [4].
- **Config consumer.** A push subscription on config revisions keeps the RemoteConfig cache warm: connectors, mappings and routing [12].

The repo also ships two documentation deployables: a Prism sandbox and a Next.js developer portal. [[architecture]] covers both.

## Why it exists separately

fapi is the only connector fronted by a public, customer-operated HTTP API. SFTP and Shopify run on infrastructure Fuse controls end to end.
The caller sends arbitrary request shapes and expects an accept or reject answer in the same request.
Validation, auth and tenancy therefore run inline, before anything reaches the pipeline [6].

## Neighbours

```orient-flow
{ "v": 1, "title": "fapi in context",
  "nodes": [
    { "id": "cust", "label": "Customer systems", "sub": "REST callers", "kind": "external", "ev": [2] },
    { "id": "f", "label": "fapi", "sub": "api-gateway", "kind": "service", "service": "fapi", "tone": "accent", "ev": [1] },
    { "id": "crr", "label": "create_record_request", "kind": "topic", "ev": [5] },
    { "id": "d", "label": "dedupe-service", "kind": "service", "service": "dedupe-service", "ev": [9] },
    { "id": "p", "label": "snap-queue-polling-service", "kind": "service", "service": "snap-queue-polling-service", "ev": [9] },
    { "id": "cr", "label": "confirmation_ready", "sub": "source=rest or broadcast", "kind": "topic", "ev": [8] },
    { "id": "h", "label": "Customer webhook", "kind": "external", "ev": [4] },
    { "id": "m", "label": "confirmation_made and failure", "sub": "single-record envelopes", "kind": "topic", "ev": [5] },
    { "id": "cs", "label": "config-service", "sub": "via config_revision", "kind": "service", "service": "config-service", "ev": [12] },
    { "id": "r", "label": "Redis", "sub": "config and rate-limit cache", "kind": "store", "ev": [1] }
  ],
  "edges": [
    { "from": "cust", "to": "f", "label": "POST v1/v2, Basic" },
    { "from": "f", "to": "crr" },
    { "from": "crr", "to": "d" },
    { "from": "p", "to": "cr" },
    { "from": "cr", "to": "f", "label": "push" },
    { "from": "f", "to": "h", "label": "POST, 3 tries" },
    { "from": "f", "to": "m" },
    { "from": "cs", "to": "f", "label": "revision push" },
    { "from": "f", "to": "r" },
    { "from": "f", "to": "cs", "label": "GET connectors on miss", "style": "dashed" }
  ] }
```

Upstream of ingress is the customer. Downstream of ingress is dedupe-service, which gates every record. Upstream of egress is the SNAP poller, which publishes `confirmation_ready` [10].
fapi receives only confirmations routed to a REST connector, plus explicit broadcasts [8]. Collector and replay-service consume the `confirmation_made` and failure topics [10].

## Where the reference lives

[[architecture]] carries the endpoint map, auth, the egress routing rules, topics, env and deploys.
`CLAUDE.md` in the repo root is the deep reference. The repo's own rule: update it in the same change as the code [9].
[[known-context]] holds history and traps. Some of its entries are marked superseded.

Do not trust three sources:

- `README.md` omits the egress and config-consumer halves and its env and topic lists are out of date.
- `CLAUDE.md` and `README.md` list `GET /health/readiness`. The route does not exist [13].
- `CLAUDE.md` still says PO and SO have their own `*_made` topics. They publish to the shared `confirmation_made` topic [5].

## What deliberately isn't here

- **Field defaulting.** A direct API submission skips the per-connector `CONNECTOR_MAPPING` that SFTP and Shopify customers get. config-service holds a `DEFAULT_MAPPING` for this gap. Nothing in fapi, dedupe-service or snap-adapter consumes it. A thin request still returns 202 and fails later on `create_data_failure` [9].
- **A second auth scheme.** Only HTTP Basic against RemoteConfig authenticates customers. The app needs the `API_KEY` env var to boot, and no guard reads it [6][7].
- **Tracing.** Logs and metrics only, through `@gfs-bifrost/observability` [9].
- **Stock reads.** `GET /api/v1/stock`, `GET /api/v2/stock` and `GET /api/v1/customer/:accountId/stock` return 501. The first two are rate-limited ahead of a planned wms-gateway proxy. fapi has no call to wms-gateway at this commit [2][11][14].
- **Legacy return-goods and work-order POSTs.** `POST /api/v1/return-goods` and `POST /api/v1/work-orders` return 501. They exist for sandbox and documentation parity [11].
- **Dedupe, SNAP mapping and delivery to SFTP or Shopify.** dedupe-service, snap-adapter, sftp-connector and shopify-connector own those.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "code/src/app.module.ts@ced057d" },
  { "id": 2, "kind": "code", "ref": "code/src/http/controllers/api.controller.ts@ced057d" },
  { "id": 3, "kind": "code", "ref": "code/src/http/controllers/confirmation.controller.ts@ced057d" },
  { "id": 4, "kind": "code", "ref": "code/src/services/confirmation.service.ts@ced057d" },
  { "id": 5, "kind": "code", "ref": "code/src/services/pubsub-emitter.ts@ced057d" },
  { "id": 6, "kind": "code", "ref": "code/src/http/guards/remote-config-guard.ts@ced057d" },
  { "id": 7, "kind": "code", "ref": "code/src/config/config.service.ts@ced057d" },
  { "id": 8, "kind": "code", "ref": "iac/projects/api-gateway/pubsub.tf@ced057d" },
  { "id": 9, "kind": "code", "ref": "CLAUDE.md@ced057d" },
  { "id": 10, "kind": "doc", "ref": "fuse://pubsub-topology", "note": "publishers and subscribers of confirmation_ready and confirmation_made" },
  { "id": 11, "kind": "code", "ref": "code/src/http/controllers/legacy.controller.ts@ced057d" },
  { "id": 12, "kind": "code", "ref": "code/src/http/controllers/config-event.controller.ts@ced057d" },
  { "id": 13, "kind": "code", "ref": "code/src/http/controllers/health.controller.ts@ced057d" },
  { "id": 14, "kind": "doc", "ref": "Engineering/wms-gateway/overview", "note": "fapi is the intended caller; the proxy is not wired in fapi" }
] }
```
