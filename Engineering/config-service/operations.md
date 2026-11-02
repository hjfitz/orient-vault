---
tags:
- waypoint
- config-service
verified: '2026-10-09'
verified_sha: 6f0b36b
verified_paths:
- code/src/observability
- .github/workflows
- iac/projects/config-service
- code/scripts
- code/package.json
title: config-service — operations
---
# config-service — operations

## Deploy

Default branch `main`. Standard flow: branch → PR → review → merge. **Prod deploys
on every push to `main`, with no path filter** — even a docs-only change redeploys.
Dev docker+apply run automatically; prod is `terraform-plan-prod` →
`docker-push-prod` (gated by the `terraform-prod` GitHub environment approval) →
`terraform-apply-prod`. Manual dev-only deploy:
`gh workflow run manual-deploy.yaml --ref <branch>`.

Infra (`iac/projects/config-service`, Terragrunt): Cloud Run in `europe-west2` with
a Datadog `serverless-init` sidecar dual-shipping to GFS + ILG orgs. The
`config_revision`/`customer_creation` topics are owned by a separate
`bifrost-pubsub` repo/state — this service only creates its own push subscription;
adding a new topic dependency means a new `terraform_remote_state` output, not a
`google_pubsub_topic` here.

## Data migrations

One-off backfills live in `code/scripts/`, run **manually per environment**, not
part of deploy: `migrate:egress-filetype`, `migrate:column-ordering`,
`migrate:confirmations-enabled` and `migrate:confirmations-enabled-sftp-shopify` (each + rollback), `migrate:connector-business-id` (+
rollback, supports `--dry-run`, writes through the raw driver so it neither bumps
`metadata.version` nor publishes a revision event, and deliberately includes
soft-deleted connectors). `pnpm run seed` points at `scripts/seed-mongodb.ts`, but the file lives at
`src/__fixtures__/seed-mongodb.ts`, so the script fails as written.

## Observability (no APM)

Logs + custom metrics only.

- Datadog service: `config-service`, disambiguated by `@environment`
  (dev/prod) — same `DD_SERVICE` in every env.
- **Cross-service tracing is by flat top-level correlation fields** (no `requestor`
  nesting): `flow`, `businessId`, `connectorId`, `correlationId`, set through the
  `@gfs-bifrost/observability` `Correlation` facade. Trace a flow by `@correlationId`.
  Logging runs on that package's Express-singleton builder
  (`observability/observability.ts`), with a local event catalogue in
  `observability/events/`.
- `MONGO_LATENCY` wraps every query (`Collection`); `COLD_START` fires on boot.
- **A malformed push event to `/events/customer-creation` logs a `warn`
  ("Pub/Sub event decode failed…") and is 204-dropped** — there is no DLQ for this
  path. If an SFTP-connector auth-status callback appears to have vanished, look in
  logs here, not in a dead-letter topic.

## Real failure modes

- **Pub/Sub outage during a write**: the HTTP write still succeeds (Mongo is the
  source of truth); the `config_revision` publish fails silently (caught, logged,
  not rethrown). Downstream caches simply don't get invalidated until the next
  successful publish or their own TTL — a deliberate tradeoff, not a bug.
- **A malformed SFTP-provisioning callback**: dropped with a 204 ack and a warn log,
  never retried. If a connector's `auth`/`user`/`isActive` block never gets
  populated after provisioning, this is the first place to check.
- **A connector-config field added to only one of the two required places**: it
  round-trips through Mongo fine but is silently stripped from every API response —
  looks like "the write didn't work" when it actually did; see
  [[known-context]] for the two-place footgun.
- **Config-service itself down**: existing downstream traffic keeps running on
  cached config; new writes and any cold cache-miss fail until it recovers — see
  [[known-context]] for the confirmed criticality model.

## Cross-checking

Use `mcp__fuse__lookup-config`, `list-customers`, and `get-business-config` for
read-side investigation; `mcp__fuse__config-write` for writes (prod requires
`confirm: true`) — these hit this service's live API directly, so what they return
is ground truth, not a cached view.
