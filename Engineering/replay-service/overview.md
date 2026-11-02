---
tags:
- waypoint
- replay-service
verified: '2026-10-13'
verified_sha: 43380eb
verified_paths:
- README.md
- CLAUDE.md
- code/src/http/controllers/event.controller.ts
- iac/projects/replay/pubsub.tf
- code/src/core/failure/failure.service.ts
- code/src/http/controllers/failures.controller.ts
- code/src/models/constants.ts
title: replay-service — overview
thesis: 'replay-service is the pipeline''s failure inbox and operator redrive console:
  it stores every captured failure, lets a person repair and replay it, and clears
  it when a later delivery succeeds.'
confidence: high
---
# replay-service — overview

```orient-bluf
{ "v": 1, "bluf": "replay-service is the pipeline's failure inbox and operator redrive console: it stores every captured failure, lets a person repair and replay it, and clears it when a later delivery succeeds.", "confidence": "high", "action": "Keep redrive a human decision: add no automatic retry here, and never publish a record that fails the strict canonical gate." }
```

## Responsibility

- **It captures failures.** It stores each `BifrostFailure` from `create_data_failure` and `confirmation_data_failure` in one `failures` collection [1][2].
- **It knows twelve record types.** Four are create-side: `sales_order`, `purchase_order`, `master_data`, `work_order`. Eight are confirmation-side: the seven confirmation types plus `stock_sync` [3].
- **It serves the admin API** at `/api/v1/failures` behind a shared API key. Operators list, inspect, edit, assign, dismiss and replay failures one at a time or up to 100 at once [4].
- **It replays.** An inbound record re-enters at `create_record_request`. A confirmation goes to `confirmation_ready`, back to the channel that failed [4][6].
- **It holds stock sync runs.** A failed stock sync run replays whole, or one SKU at a time [4][2].
- **It clears down.** A `confirmation_made` ack soft-deletes the matching failures, so nobody can retry a delivered record into a duplicate [1][2].

The admin API is the backend of the fuse-ui Retry Queue. Every triage action there lands here.

## Why it exists separately

It is the one place to inspect, repair and re-send a rejected record. Producers publish the failure and move on. None of them needs its own retry screen or repair workflow.

Redrive stays manual on purpose. A stored record failed strict validation upstream, so a person must fix it before it can pass the replay gate [4].

## Neighbours

```orient-flow
{ "v": 1, "title": "replay-service in context",
  "nodes": [
    { "id": "prod", "label": "Pipeline producers", "sub": "snap-adapter, sftp-connector, shopify-connector, fapi, egress", "kind": "external", "ev": [9] },
    { "id": "cdf", "label": "create_data_failure", "kind": "topic", "ev": [5] },
    { "id": "ccf", "label": "confirmation_data_failure", "kind": "topic", "ev": [5] },
    { "id": "made", "label": "confirmation_made", "sub": "success acks", "kind": "topic", "ev": [5] },
    { "id": "r", "label": "replay-service", "sub": "failure inbox + redrive", "kind": "service", "service": "replay-service", "tone": "accent", "ev": [1, 4] },
    { "id": "m", "label": "failures", "sub": "MongoDB", "kind": "store", "ev": [2] },
    { "id": "ui", "label": "fuse-ui", "sub": "Retry Queue", "kind": "service", "service": "fuse-ui" },
    { "id": "req", "label": "create_record_request", "sub": "to dedupe-service", "kind": "topic", "ev": [9] },
    { "id": "rdy", "label": "confirmation_ready", "sub": "to connectors", "kind": "topic", "ev": [9] }
  ],
  "edges": [
    { "from": "prod", "to": "cdf" },
    { "from": "prod", "to": "ccf" },
    { "from": "prod", "to": "made" },
    { "from": "cdf", "to": "r", "label": "store" },
    { "from": "ccf", "to": "r", "label": "store" },
    { "from": "made", "to": "r", "label": "clear down" },
    { "from": "r", "to": "m" },
    { "from": "ui", "to": "r", "label": "admin API" },
    { "from": "r", "to": "req", "label": "replay inbound" },
    { "from": "r", "to": "rdy", "label": "replay confirmation" }
  ] }
```

Upstream, producers publish failures and the success acks that clear them. Downstream, a replay re-enters the pipeline on the same topics the producers use. dedupe-service reads `create_record_request`. Connectors read `confirmation_ready` [9].

## Where the reference lives

[[architecture]] carries the routes, subscriptions, replay rules, persistence and runtime. [[known-context]] carries the investigation history. Read `origin/main`, not a local checkout: the local `main` lags.

Do not trust these sources:

- `README.md` is the verbatim "Repository Template". None of it describes this service [8].
- The repo `CLAUDE.md` is stale on several points. It describes deep-partial validation on store, an OIDC-authenticated push route, a three-type create filter, a legacy goods-in/out topic and `pendingChanges`. It omits stock sync [7].

## What deliberately isn't here

- **Idempotent intake.** An at-least-once redelivery of one failure creates a second `failures` row, so counts do not equal distinct incidents. See [[known-context#not-deduplicated]].
- **Snapshot history.** The service stores only the diff between edits (`editHistory[].changes`), never a full copy of the record. See [[architecture#diff-not-snapshot]].
- **RGA create-side failures.** The service captures only the RGA confirmation side. This is deliberate, so check why before you "complete" it. See [[known-context]].
- **The poller's `no_originating_connector` notices.** The confirmation was already broadcast, so a retry would duplicate it. The service acks and skips them [1].
- **A consumer for the dead-letter topics.** A Datadog monitor pages a human instead. See [[known-context#dlt-monitored-not-consumed]].
- **The Shopify stock push.** The egress service owns it. This service only holds the failed run and re-sends its pointer [2].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "code/src/http/controllers/event.controller.ts@43380eb" },
  { "id": 2, "kind": "code", "ref": "code/src/core/failure/failure.service.ts@43380eb" },
  { "id": 3, "kind": "code", "ref": "code/src/models/constants.ts@43380eb" },
  { "id": 4, "kind": "code", "ref": "code/src/http/controllers/failures.controller.ts@43380eb" },
  { "id": 5, "kind": "code", "ref": "iac/projects/replay/pubsub.tf@43380eb" },
  { "id": 6, "kind": "code", "ref": "code/src/core/failure/confirmation-redrive-routing.ts@43380eb" },
  { "id": 7, "kind": "code", "ref": "CLAUDE.md@43380eb" },
  { "id": 8, "kind": "code", "ref": "README.md@43380eb" },
  { "id": 9, "kind": "doc", "ref": "fuse://pubsub-topology", "note": "publishers and subscribers of create_data_failure, confirmation_data_failure, confirmation_made, create_record_request, confirmation_ready" }
] }
```
