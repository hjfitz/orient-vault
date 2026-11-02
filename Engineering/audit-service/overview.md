---
tags:
- waypoint
- audit-service
title: audit-service — overview
verified_paths:
- code/internal
- code/cmd
- code/tools/auditschema
- iac/projects/audit-service
- .github/workflows
- code/dockerfile
- code/Makefile
- code/go.mod
- code/openapi.yaml
- CLAUDE.md
- README.md
- iac/env
- mise.toml
verified: '2026-10-13'
verified_sha: ddefd56
thesis: 'audit-service is the central, private audit trail: it stores each audit event
  once, forever, from per-system Pub/Sub topics and serves events back only system-scoped
  to allow-listed callers.'
confidence: high
---
# audit-service — overview

```orient-bluf
{ "v": 1, "bluf": "audit-service is the central, private audit trail: it stores each audit event once, forever, from per-system Pub/Sub topics and serves events back only system-scoped to allow-listed callers.", "confidence": "high", "action": "Never add a public invoker, a query or index that spans systems, or a log line that carries a message payload." }
```

## Responsibility

- Producers publish `AuditMessage` events from `@gfs-bifrost/audit` to one Pub/Sub topic per reporting system, `audit.<env>.<system>.v1` [1].
- The service stores each event once. A repeated `eventId` is a duplicate, not a second row [2].
- It keeps events forever. No TTL index and no delete route exist [2].
- It serves events back through three system-scoped read routes to callers on an allow-list [3].
- `system` is a required envelope field and the first key of every index and query. `fuse` is the only system today. `tenantId` is optional within a system and is the `businessId` for Fuse [2][4].
- `cmd/import-legacy` copies fuse-ui's old `audit_log` into the trail. A human runs it, once, at cutover [5].

## Why it exists separately

The audit log used to live inside fuse-ui as an `audit_log` collection written by server actions. Other services, starting with sftp-connector's SFTP user lifecycle, also need to report into one trail.

The envelope is meant to work outside the Bifrost suite. So it gets its own service, its own datastore and its own contract package, and it is not a fuse-ui API.

Adding a reporting system takes a topic in bifrost-pubsub and one entry in `local.systems` in `iac/projects/audit-service/remotes.tf` [4].

## Neighbours

```orient-flow
{ "v": 1, "title": "audit-service in context",
  "nodes": [
    { "id": "prod", "label": "Producers", "sub": "fuse-ui first, sftp-connector next", "kind": "external", "ev": [1] },
    { "id": "topic", "label": "audit.<env>.<system>.v1", "sub": "owned by bifrost-pubsub", "kind": "topic", "ev": [4] },
    { "id": "svc", "label": "audit-service", "sub": "private Cloud Run", "kind": "service", "service": "audit-service", "tone": "accent", "ev": [2, 6] },
    { "id": "mongo", "label": "MongoDB Atlas", "sub": "events, _id = eventId", "kind": "store", "ev": [7] },
    { "id": "dlt", "label": "Dead-letter hold", "sub": "7 days, manual re-publish", "kind": "topic", "ev": [4] },
    { "id": "ui", "label": "fuse-ui", "sub": "reader allow-list", "kind": "service", "service": "fuse-ui", "ev": [3, 6] }
  ],
  "edges": [
    { "from": "prod", "to": "topic", "label": "publish" },
    { "from": "topic", "to": "svc", "label": "OIDC push" },
    { "from": "svc", "to": "mongo", "label": "insert once" },
    { "from": "topic", "to": "dlt", "label": "5 store failures", "style": "dashed" },
    { "from": "ui", "to": "svc", "label": "GET /api/v1/systems/{system}" }
  ] }
```

The push path and the read path never touch the same route group. The push service account may only post to `/events/v1`, and readers may only get from `/api/v1/systems`.

## Where the reference lives

[[architecture]] holds the layout, routes, indexes and runtime. [[audit-event-flow]] holds the end-to-end path of one event, with the outcome table. [[known-context]] holds the decisions behind the design and the test gotchas. The repo's `CLAUDE.md` and `README.md` carry the standing rules.

Do not trust two sources:

- `CLAUDE.md` and `README.md` name the reader grant `api_extra_invokers`. The variable is `api_readers` [6].
- **ASSESSED** The service is private only as far as this repo shows. A project-level IAM binding outside this repo could still widen it.

## What deliberately isn't here

- **Producer logic.** Masking, snapshot building and "never block the audited action" live with producers and the `@gfs-bifrost/audit` publisher.
- **Retention or deletion.** Product decision: keep everything.
- **Public ingress.** Every route needs a Google ID token from an allow-listed account, and Cloud Run IAM also gates it [6].
- **Per-kind validation on ingest.** Kinds are open strings, so the service stores an unregistered kind. The Fuse discriminated union is for producers only.
- **Masking on read.** The service returns `details` as stored. The reader masks secrets before anything reaches a browser.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "README.md@ddefd56" },
  { "id": 2, "kind": "code", "ref": "code/internal/repositories/events.go@ddefd56" },
  { "id": 3, "kind": "code", "ref": "code/internal/bootstrap/routes.go@ddefd56" },
  { "id": 4, "kind": "code", "ref": "iac/projects/audit-service/remotes.tf@ddefd56" },
  { "id": 5, "kind": "code", "ref": "code/cmd/import-legacy/main.go@ddefd56" },
  { "id": 6, "kind": "code", "ref": "iac/projects/audit-service/iam.tf@ddefd56" },
  { "id": 7, "kind": "code", "ref": "iac/projects/audit-service/mongo.tf@ddefd56" }
] }
```
