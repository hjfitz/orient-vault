---
tags:
- waypoint
- dedupe-service
verified: '2026-10-01'
verified_sha: d00d3a1
verified_paths:
- iac
- .github/workflows
- code/src/observability
- code/src/config.ts
- code/src/scripts
- iac/env
title: dedupe-service — operations
---
# dedupe-service — operations

## Deploy

Cloud Run via GitHub Actions. `manual-deploy.yaml` deploys a branch to dev (and applies dev
Terraform, so branch infra is testable pre-merge); merge to the default branch deploys prod via
`on-push.yaml`. `code-quality.yaml`, `secops.yaml` and `tf-output.yaml` gate PRs.

Terragrunt lives in `iac/projects/dedupe-service` with per-env tfvars in `iac/env/`.

## Configuration

All runtime config is Cloud Run env vars: `MONGODB_CONNECTION_STRING`, `MONGODB_DB`
(`dedupe-<env>`), `CREATE_RECORD_TOPIC`, `CONFIG_SERVICE_BASE_URL`, `REDIS_HOST`/`PORT`/`TTL_MS`
and the Redis circuit-breaker and retry knobs. Two API keys, not one: `CONFIG_SERVICE_API_KEY`
comes from Secret Manager, while the record admin API's `API_KEY` is a `random_password`
generated in `iac/projects/dedupe-service/api-key.tf` and handed to fuse-ui through the `api_key`
output. Nothing reads `process.env` outside `code/src/config.ts`.

The Mongo pool, timeout and retry knobs (`MONGODB_MAX_POOL_SIZE`, `MONGODB_*_TIMEOUT_MS`,
`MONGODB_RETRY_*`) are validated in `code/src/config.ts` but **are not set in Terraform**, so
every environment runs their code defaults. Retuning them needs a `cloud-run.tf` change, not just
a tfvar. UNRESOLVED: whether leaving them unwired was deliberate (defaults judged right) or simply
not finished when the knobs were added.

## Observability

Datadog, via a `serverless-init` sidecar dual-shipping to the GFS and ILG accounts. Logging and
metrics run through `@gfs-bifrost/observability` (the Fuse adaptor over
`@ilg-platform/observability`), built once in `code/src/observability/observability.ts` via
`FuseObservabilityBuilder` — deliberately with no `.withChannel()`, since dedupe is an internal
pipeline stage, not an origin channel. There is no winston, `cls-hooked` or `dd-trace` in the
service and no hand-rolled logger format or transports; the SDK owns all of it.

Local metrics are namespaced `dedupe.*`, defined per group under
`code/src/observability/*-metric.type.ts`; request latency / cold-start and Mongo up/latency come
from the shared `fuse.*` catalogue the SDK exports (`REQUEST_METRIC`, `CONFIG_METRIC.MONGO_*`).
Alongside the blacklist counters `dedupe.sku.blacklisted` (full drop) and `dedupe.sku.lines_removed`
(partial strip) and the event-handled / invalid-event counters, the ones that carry operational
meaning are the drop and nack signals: `dedupe.event.nacked`, `dedupe.event.dropped_permanent`,
`dedupe.event.dropped_config_unavailable`, `dedupe.sku.blacklist_unavailable`,
`dedupe.config_revision.exception`, `dedupe.hold_bookkeeping_failed`,
`dedupe.errors.unhandled_rejection`, plus the Mongo pair `dedupe.mongo.retry` /
`dedupe.mongo.heartbeat_failed`. `dedupe.record.invalid` is create-path only — the release path
emits `dedupe.record.invalid_release` so it cannot mask a create drop in the silent-publish-drop
monitor.

Log lines come from the SDK's shared event catalogue plus four local ones in
`code/src/observability/events/` (gate, SKU blacklist, cache, record admin). Correlation context is
stamped per request through the SDK's `Correlation` facade — `requestIdMiddleware` opens the root
scope and handlers enrich it via `Correlation.set` — carrying the canonical `flow: "create"` on
create, `"release"` on the release routes and `"config"` on config revision; `recordType` rides the
same scope once known. `index.ts` owns
unhandled rejections: its `process.on("unhandledRejection", …)` meters
`dedupe.errors.unhandled_rejection` and logs with service context, keeping one bad promise from
taking the container down.

## Failure modes

- **Silent drop is now the exception, not the rule.** The create route acks last: a transient
  failure answers 503 and Pub/Sub redelivers under the subscriptions' 10s → 600s backoff. This
  closes the ack-first path described in
  [[Engineering/dedupe-service/known-context|known-context]]. What is still acked-and-gone is a
  permanent payload failure (`dedupe.event.dropped_permanent`), a record whose blacklist could not
  be determined (`dedupe.event.dropped_config_unavailable`), an invalid release
  (`dedupe.record.invalid_release`) and a failed config revision
  (`dedupe.config_revision.exception`). There are still no dead-letter
  topics, so for those four the metric is the only signal and recovery is a re-send, not a
  redelivery.
- **Mongo outage** no longer reads as healthy: heartbeats un-latch the connection status, so
  `/health/readiness` returns 503 while `/health/liveness` stays 200 — an outage must not read as
  "restart me". Transient driver errors retry with backoff; boot refuses to start without Mongo.
- **Redis outage** degrades the blacklist path but cannot wedge boot or the write path; calls are
  bounded and breaker-guarded, and a blacklist read timeout is treated as a cache miss.
- **config-service unavailable** on a cache miss now **fails closed** — the record is neither
  forwarded nor stored, so a later sighting is treated as new rather than held.
- **Scaling is bounded** at 5 instances × 40 concurrent requests, with load queueing in the
  Pub/Sub backlog by design. Prod keeps one instance warm (`min_instance_count = 1` in
  `iac/env/prod.tfvars`); dev scales to zero, so cold starts are still possible there.

## Routine operations

- **Releasing a held record** is support self-serve through fuse-ui; the underlying calls are
  `DELETE /api/v1/record/:recordType/:id` and the Fuse MCP `dedupe-release` tools.
- **Dedupe-key collisions**: after a change to a type's dedupe key, `pnpm run fix:dedupe-collisions`
  reports records that violate the new key's uniqueness (`--apply` to write; `--fill-missing` to
  invent a missing reference). Run it before deploying the key change: a colliding pair fails the
  unique-index build at boot and the revision never goes healthy.
- **Timestamp backfill**: `pnpm run backfill:timestamps` is idempotent and run once per
  environment after deploy, seeding `createdAt`/`updatedAt` on rows that predate them.
- **Blackbox tests** run on every PR and a 06:00 cron (`blackbox-testing.yaml`) against a
  self-contained docker-compose stack, not a deployed environment — a green run says nothing
  about dev or prod.
