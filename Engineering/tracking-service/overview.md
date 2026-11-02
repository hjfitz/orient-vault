---
tags:
- waypoint
- tracking-service
title: tracking-service — overview
thesis: tracking-service follows every Fuse shipment and return end to end. It folds
  every create, acknowledge, failure and confirmation event into one Firestore record
  per order, kept forever, and serves that record to fuse-ui's order tracker and fuse-mcp's
  tracking-* tools. It is separate because nothing else in Fuse joins an order's whole
  journey.
confidence: high
verified: '2026-10-15'
verified_sha: 9f01957
verified_paths:
- apps/api
- iac/projects/tracking-service
---
# tracking-service — overview

```orient-bluf
{ "v": 1, "bluf": "tracking-service follows every Fuse shipment and return end to end. It folds every create, acknowledge, failure and confirmation event into one Firestore record per order, kept forever, and serves that record to fuse-ui's order tracker and fuse-mcp's tracking-* tools. It is separate because nothing else in Fuse joins an order's whole journey.", "confidence": "high", "action": "none" }
```

## Responsibility
- One record per sales order (a **shipment**) and per RGA (a **return**), keyed on business + customer
  reference (returns: business + RGA number) [1].
- Each record carries an event timeline, a derived status and stage times, a despatch state, an attention
  lane (needs action or running late), support notes, and daily stats and insights [1][2].
- A private read API, `/api/v1`, for fuse-ui's order tracker page (the L2 support work queue) and
  fuse-mcp's `tracking-*` tools [3].

## Why it exists separately
Every other service sees one stage of an order. collector stores record snapshots per record type,
replay holds failures, and dedupe holds duplicates. Support used to answer "where is order X" by walking
logs and several UIs. tracking-service only reads the bus. It publishes nothing and calls no service, so
it can't change the pipeline it watches [1][4].

## Neighbours
```orient-flow
{ "v": 1, "title": "tracking-service in context",
  "nodes": [
    { "id": "bus", "label": "Fuse topics", "sub": "create_*, confirmation_*, *_failure", "kind": "topic", "ev": [4] },
    { "id": "svc", "label": "tracking-service", "sub": "private Cloud Run, Go", "kind": "service", "service": "tracking-service", "tone": "accent", "ev": [3] },
    { "id": "fs", "label": "Firestore", "sub": "database tracking-service, no TTL", "kind": "store", "ev": [5] },
    { "id": "dlt", "label": "Dead-letter hold", "sub": "7 days, cmd/redrive", "kind": "topic", "ev": [4] },
    { "id": "ui", "label": "fuse-ui", "sub": "/order-tracker", "kind": "service", "service": "fuse-ui", "ev": [6] },
    { "id": "mcp", "label": "fuse-mcp", "sub": "tracking-* tools", "kind": "service", "service": "fuse-mcp-server", "ev": [6] }
  ],
  "edges": [
    { "from": "bus", "to": "svc", "label": "20 filtered push subs" },
    { "from": "svc", "to": "fs", "label": "transactional fold" },
    { "from": "bus", "to": "dlt", "label": "5 failed attempts", "style": "dashed" },
    { "from": "ui", "to": "svc", "label": "GET /api/v1 (ID token)" },
    { "from": "mcp", "to": "svc", "label": "GET /api/v1 (ID token)" }
  ] }
```
Pub/Sub pushes with an OIDC token from `tracking-service-push-{env}`. The readers hold `run.invoker`
through `api_extra_invokers` [6].

## Where the reference lives
- `apps/api/README.md` is the deep reference: event → stage table, metrics, push responses, backfills,
  returns. `apps/api/CLAUDE.md` lists the invariants.
- `docs/cutover.md` is the record of the 2026-10-14/15 move off the legacy `fuse-tracker` stack.
  `docs/archive/` holds the first-build specs, and where they disagree with the code, the code wins.
- Read [[architecture]] for structure and guardrails, [[operations]] for running it, and
  [[known-context]] for the history behind the rules.

## What deliberately isn't here
- **A UI.** fuse-ui's `/order-tracker` page is the UI, and #1 retired the standalone web app.
- **An MCP server.** fuse-mcp serves the `tracking-*` tools over this API.
- **Any write to the pipeline.** No publishing, no retries, no releases. The tracker links to replay's
  retry queue and Transaction History in fuse-ui instead.
- **Carrier delivery.** The status model keeps `delivered` for carrier proof of delivery, which doesn't exist yet.
- **PII handling.** Deferred to a fuse-ui BFF.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "README.md@9f01957" },
  { "id": 2, "kind": "code", "ref": "apps/api/internal/core/reduce.go@9f01957" },
  { "id": 3, "kind": "code", "ref": "apps/api/internal/http/router.go@9f01957" },
  { "id": 4, "kind": "code", "ref": "iac/projects/tracking-service/pubsub.tf@9f01957" },
  { "id": 5, "kind": "code", "ref": "iac/projects/tracking-service/firestore.tf@9f01957" },
  { "id": 6, "kind": "code", "ref": "iac/projects/tracking-service/iam.tf@9f01957" }
] }
```
