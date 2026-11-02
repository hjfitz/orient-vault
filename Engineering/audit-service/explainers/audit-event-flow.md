---
tags: [waypoint, explainer, audit-service]
thesis: "An audit event travels producer → per-system topic → OIDC push → one idempotent row keyed by eventId, and is read back only through system-scoped, allow-listed queries."
confidence: high
updated: 2026-10-12
verified: 2026-10-12
verified_sha: ddefd56
verified_paths:
  - code/internal/core/ingest/ingest.go
  - code/internal/http/controllers/ingest.go
  - code/internal/repositories/events.go
  - code/internal/repositories/read.go
  - code/internal/core/query/query.go
  - code/internal/bootstrap/routes.go
  - code/internal/core/legacy/legacy.go
  - iac/projects/audit-service/pubsub.tf
  - iac/projects/audit-service/remotes.tf
drifted_evidence: []
drift_checked: 2026-10-12
commits_behind: 0
---
# How an audit event reaches the trail and comes back out

```orient-bluf
{ "v": 1, "bluf": "An audit event travels producer → per-system topic → OIDC push → one idempotent row keyed by eventId, and is read back only through system-scoped, allow-listed queries.", "confidence": "high", "action": "none" }
```

## Mechanism

```orient-flow
{ "v": 1, "title": "Audit event path",
  "nodes": [
    { "id": "p", "label": "Producer", "sub": "createAuditPublisher", "kind": "service", "ev": [1] },
    { "id": "t", "label": "audit.<env>.<system>.v1", "kind": "topic", "ev": [2] },
    { "id": "s", "label": "Push subscription", "sub": "OIDC, 5 attempts", "kind": "step", "ev": [2] },
    { "id": "i", "label": "/events/v1/audit/{system}", "kind": "step", "service": "audit-service", "tone": "accent", "ev": [3, 4] },
    { "id": "d", "label": "DLT hold", "sub": "7 days", "kind": "topic", "tone": "alert", "ev": [2] },
    { "id": "m", "label": "events", "sub": "_id = eventId", "kind": "store", "ev": [5] },
    { "id": "r", "label": "/api/v1/systems/{system}", "kind": "step", "service": "audit-service", "ev": [6, 7] },
    { "id": "c", "label": "Allow-listed caller", "sub": "fuse-ui SA", "kind": "service" },
    { "id": "l", "label": "import-legacy", "sub": "human-run", "kind": "step", "ev": [8] }
  ],
  "edges": [
    { "from": "p", "to": "t", "label": "publish, never blocks" },
    { "from": "t", "to": "s" },
    { "from": "s", "to": "i", "label": "push" },
    { "from": "i", "to": "m", "label": "stored / duplicate" },
    { "from": "s", "to": "d", "label": "5 × store failure", "style": "dashed" },
    { "from": "l", "to": "m", "label": "same insert" },
    { "from": "c", "to": "r" },
    { "from": "r", "to": "m", "label": "system-scoped" }
  ] }
```

1. **CONFIRMED** The producer builds an `AuditMessage` and calls the `@gfs-bifrost/audit` publisher. It validates, publishes with `system`/`producer`/`auditKind`/`schemaVersion` attributes, races a 3 s timeout, and never rejects [1].
2. **CONFIRMED** Each system has its own topic. audit-service owns one push subscription per topic, listed in `local.systems` [2][9].
3. **CONFIRMED** Pub/Sub pushes with an OIDC token for the push SA. The route admits only that email [6].
4. **CONFIRMED** Ingest decodes the envelope and checks `system` against the URL and the `system` attribute [4]. The outcome decides the response [3][2]:

| Outcome | Response | Effect |
|---|---|---|
| `stored`, `duplicate` | 204 | One row exists |
| `invalid`, `system_mismatch` | 204 | Counted, not stored; redelivery would never succeed |
| `store_failed` | 500 | Retried at 10–600 s backoff, dead-lettered after 5 attempts |

5. **CONFIRMED** The store writes the raw message as relaxed Extended JSON, so open `details` survive. `_id` is the `eventId`, `occurredAt` becomes a date, and the service stamps `receivedAt`. A duplicate key reports `duplicate`, not an error [5].
6. **CONFIRMED** Reads always filter on `system` first. Every index leads with it [5][10]. The list pages newest first on `(occurredAt, _id)` with an opaque cursor [10]. It returns 25 by default, 100 at most, and stops counting the total at 1000 [7]. Empty results encode as `[]`, never `null` [7].
7. **CONFIRMED** `import-legacy` maps each fuse-ui `audit_log` row to a Fuse `AuditMessage`. It keeps the minted `eventId`, else the ObjectId hex, as the id. It inserts through the same store, so a rerun inserts nothing [8].

## Boundaries

- **CONFIRMED** Topics and their `.dlt` belong to bifrost-pubsub. Subscriptions, the DLT hold and IAM belong here [2][9].
- **CONFIRMED** Reads need an ID token whose email is in `READ_CALLERS`. Cloud Run IAM admits the same `api_readers` list [6].
- **ASSESSED** Masking and snapshot shape are the producer's job: the service stores `details` as given and validates only the envelope [4][5].

## Constraints

- **CONFIRMED** No query or index may span systems [5][10].
- **CONFIRMED** Nothing expires. There is no TTL index and no delete route [5][6].
- **CONFIRMED** Kinds are open strings, so the service stores an unregistered kind [4].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "url", "ref": "https://github.com/gfs-bifrost/pkg-node/blob/bad70b0/pkg/audit/src/publisher/audit-publisher.ts", "note": "@gfs-bifrost/audit publisher" },
  { "id": 2, "kind": "code", "ref": "iac/projects/audit-service/pubsub.tf@ddefd56" },
  { "id": 3, "kind": "code", "ref": "code/internal/http/controllers/ingest.go@ddefd56" },
  { "id": 4, "kind": "code", "ref": "code/internal/core/ingest/ingest.go@ddefd56" },
  { "id": 5, "kind": "code", "ref": "code/internal/repositories/events.go@ddefd56" },
  { "id": 6, "kind": "code", "ref": "code/internal/bootstrap/routes.go@ddefd56" },
  { "id": 7, "kind": "code", "ref": "code/internal/core/query/query.go@ddefd56" },
  { "id": 8, "kind": "code", "ref": "code/internal/core/legacy/legacy.go@ddefd56" },
  { "id": 9, "kind": "code", "ref": "iac/projects/audit-service/remotes.tf@ddefd56" },
  { "id": 10, "kind": "code", "ref": "code/internal/repositories/read.go@ddefd56" }
] }
```

## Related

- [[architecture]] (audit-service), [[operations]] (audit-service)
