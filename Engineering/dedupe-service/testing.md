---
tags:
- waypoint
- dedupe-service
verified: '2026-10-09'
verified_sha: 9643f2b
verified_paths:
- code/src/__test__
- code/vitest.config.ts
- tests
- code/tsconfig.test.json
- code/src/bootstrap/main.ts
- .github/workflows/code-quality.yaml
- docker-compose-4pipeline.yaml
title: dedupe-service — testing
---
# dedupe-service — testing

Vitest (migrated from Jest), with `mongodb-memory-server` for real Mongo behaviour and
`supertest` against an in-process app built by the test harness. Two typecheck targets:
`build:check` (src) and `build:check:tests` — `code-quality.yaml` runs both as matrix legs
alongside `test` and `lint`, and specs are excluded from the shipped image.

## The characterization suite is a safety net, not ordinary coverage

`code/src/__test__/e2e/` plus `utils/{test-app,seams}.ts` exist to pin **current observable
behaviour** — the create gate by side effect, the release routes and config revision, the record
admin API and its api-key guard, Mongo outage and recovery, route-level failure handling, and the
exact metric names, tags and log fields.

That last one is deliberate — the suite asserts observability output because dashboards and
monitors depend on it, and a framework swap is exactly the kind of change that would silently
rename a metric. Log assertions key on the catalogue event messages and meta (`Record dropped`
with `reason: "duplicate"`, `Record published to topic`), so renaming an event trips them too.

**Consequence:** if one of these tests fails after a refactor, the default assumption is that
the refactor changed behaviour, not that the test is stale. Don't "fix" a characterization test
to match new output without deciding, explicitly, that the behaviour change is intended. Several
*have* been rewritten on exactly that basis — the fail-closed blacklist, the ack-last create
route, the crash fixes — so updating one is legitimate, but only as a decision, never as cleanup.

## The harness

`utils/test-app.ts` boots the real app through the same `createApp()` Nest uses and returns a
supertest agent on the underlying Express instance, so the whole Nest stack is exercised over real
URLs. `config` parses `process.env` once at import, so every import of app code must be
dynamic and inside `setupTestApp()` — the harness checks that and throws a diagnostic rather than
letting it surface as a connect timeout. It needs vitest's default module isolation: under
`--no-isolate` the e2e `vi.mock` calls leak into the unit specs.

`utils/seams.ts` fakes only what cannot run locally — Pub/Sub (capturing publishes, with a
`failPublishesWith` seam) and Redis. Mongo is a real in-memory server and config-service a real
HTTP server on an ephemeral port, so the app's own axios client, retry policy and breaker are
genuinely exercised. `stopMongo`/`startMongo` drive the outage specs.

## Layers

| Layer | Where |
| --- | --- |
| unit | alongside source in `__tests__/` per module |
| in-process e2e | `code/src/__test__/e2e/` via the harness |
| blackbox | `tests/` — separate Dockerised suite, on every PR and a 06:00 cron |

The blackbox suite runs entirely locally on `docker-compose-4pipeline.yaml` — Mongo, Redis, the
Pub/Sub emulator, an in-repo config-service stub (`tests/config-server/`) and the service image
built from `code/`. It does not target a deployed environment, and it no longer needs a real
config-service key.
