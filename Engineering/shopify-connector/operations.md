---
tags:
- waypoint
- shopify-connector
verified: '2026-10-09'
verified_sha: bc3c2d23
verified_paths:
- apps/shopify-connector/src/providers/observability
- apps/shopify-connector/src/adapters/shopify/api
- apps/shopify-connector/src/http/filters
- apps/shopify-connector/src/core/confirmations
- apps/shopify-connector/src/core/shopify/use-cases
- .github/workflows
- iac/shopify-connector
- iac/shopify-app
- iac/shopify-egress-service
- packages/shopify-token-management
title: shopify-connector — operations
---
# shopify-connector — operations

## Deploy

Push to `main` fires each app's own `Deploy <app>` workflow (shopify-connector,
shopify-app, shopify-egress-service), path-filtered to its `apps/<app>/**` + `iac/<app>/**`:
dev build+apply, then a `terraform-prod`-gated prod leg. Touching one app does not redeploy
the others, except that the root `pnpm-workspace.yaml`/`pnpm-lock.yaml`/`.npmrc` and
`packages/shopify-token-management` redeploy all three together (every app builds from the repo
root). Manual dev deploy: `gh workflow run
"Manual Deploy <app>" --ref <branch>`.

**Prod ingest levers** are tfvars, not runtime toggles — changing one is a terraform
apply. `iac/shopify-connector/env/prod.tfvars` carries `disable_shopify_poll`,
`disable_token_revalidation`, and (since 2026-08-28) `bulk_ingest_tick_enabled = true`
with `bulk_ingest_enabled_businesses = "PURDYFIGG"` — so prod now runs **both** ingest
paths, not just the metered poll.

**Preview envs (connector only)**: dispatching `shopify-connector-preview-env-deploy`
on an app-only branch still builds a *connector* preview (the dispatched ref is the
deployed branch, no separate branch input) — don't do this by mistake.

**Shared tfstate bucket gotcha**: `gs://gfs-bifrost-tfstate/<env>/` holds a
subdirectory per service, and fuse-ui runs its own preview-env system in the same
bucket under `dev-pr-<n>` naming (ours is `dev-<branch-slug>`). A bare `dev-*` prefix
sweep can misclassify and destroy **another service's** state — this actually
happened 2026-08-07 (fuse-ui's `dev-pr-198/199/200` were swept and one was deleted).
Discovery is still scoped to `<env>/bifrost-shopify-connector/`, never a bare prefix —
but the sweep no longer trusts tfstate alone. A reaper enumerates the **live** preview
resources by label — the environment label plus `labels.service` (fuse-ui stamps the
same `dev-<slug>` environment labels in this project, so the service label is what keeps
the two apart) — and clears whatever Terraform holds no state for. It skips any env that
still has state or holds a lock, so it never races the terraform path, and cross-checks
branch liveness, reaping a still-live branch's env only once it is older than
`MIN_AGE_MINUTES`; service accounts and scheduler jobs, which carry no labels, are
matched by the same `sha1(env)` project-name prefix. Scheduled runs always reap; a
**manual** dispatch reports only (dry-run) unless `reap_for_real` is ticked.

## Observability (no APM)

Logs + custom metrics only (`domain:fuse` tag on everything).

- **Datadog `service` tags**: `shopify-connector` (connector) / `shopify-app` (app) —
  both **env-agnostic** (the sidecar's `DD_SERVICE` comes from `project_name`, not
  env-qualified). Disambiguate dev/prod via `@environment` (`custom.environment`),
  **not** `env` — the sidecar hard-codes `DD_ENV=serverless`.
- **Cloud Run service names** (`shopify-connector-{env}-cr`, `shopify-app-{env}`,
  `shopify-egress-service-{env}-cr`) are
  a *separate* Datadog entity from the log service — `gcp.run.*` infra metrics key on
  `service_name` (the Cloud Run name), not the log `service` tag.
- **Correlation fields** ride flat/top-level on every connector log line:
  `correlationId`, `businessId`, `connectorId`, `shopName`, `flow`, `recordType`,
  `recordId` (for sales orders, the customer's own `order.customerRef` — searchable by
  the value the customer holds), plus a static `channel: "shopify"` tag. These were
  de-nested from a `requestor.*` block in FUSE-1000 — any monitor/query still on
  `@requestor.*` is stale.
- **`@connectorId` means two different things depending on the flow**, and a facet can't tell
  them apart. On the create/ingest path it is *the connector being polled*. On the sales-order
  confirmation path the controller sets it once from the envelope's `metadata.connectorId`: *the
  connector the confirmation says it came from*, a routing input, not proof of where it landed.
  The acknowledgement and failure controllers set no `connectorId` at all. Filter on `flow` as
  well before building a monitor or query on `@connectorId`.
- **What a goods-out confirmation sent Shopify is on its success line.** `Confirmation dispatched
  successfully` carries `fulfillmentIds` and `trackingInfo` (company, number, url), read back from
  `fulfillmentCreate`. A `url` there can be Shopify's own link for a carrier it knows (`EVRI`), not
  ours. `Tracking URLs omitted from the fulfillment; numbers and carrier still sent` (warn,
  `audience: support`, `reason` `unresolved` / `invalid_url` / `rule_failed`, `resolved`/`total`) means
  a mapping's tracking URL rule produced nothing usable. The fulfillment still went, without links.
- **Correlation + logging run on the SDK.** `FuseObservabilityModuleBuilder`
  (`@gfs-bifrost/observability/nest`, wired in `app.module.ts` as
  `.forService("shopify-connector").withChannel("shopify")`) auto-applies the correlation
  middleware. Classes inject the logger with `@InjectFuseLogger()` (`FuseEventLogger`) and log
  through typed event descriptors, `logger.event(SomeEvent.Name, {...})`, not free-text
  `logger.log/warn` strings. Fleet-wide events come from `@gfs-bifrost/observability`; the
  Shopify-specific ones live in `providers/observability/catalog/*-event.type.ts` — search logs by
  the event name, not message text. Per-flow fields are set through `Correlation.set`
  (`@gfs-bifrost/observability/correlation`). The hand-rolled `logger.service.ts` /
  `logger.utils.ts` / `namespace.provider.ts` / `correlation-id.middleware.ts` are all
  deleted — anything referencing the old cls-hooked logger/namespace shape is stale.
- **Metrics** are emitted through the SDK's `ObservabilityMetricsService`
  (`@ilg-platform/observability-nest`, DogStatsD under the hood) — the local
  `MetricsService` proxy and `dd-trace` are both gone. The service now **sits on** the
  shared `@gfs-bifrost/observability` `fuse.*` catalogue (`REQUEST_METRIC`,
  `ERROR_METRIC`, `CONFIRMATION_METRIC`, `CONFIG_METRIC`) for the fleet-wide domain
  metrics, alongside a **local Shopify-specific catalog**
  (`providers/observability/catalog/`) for what has no fleet equivalent:
  `records.collected`, the `graphql.*` cost/throttle/retry set (`graphql.throttled`,
  `graphql.throttle.budget_remaining`, `graphql.throttle.restore_rate`, `graphql.retry`,
  `graphql.retry.exhausted`), `api.factory.cache.*`, the
  poll latency/collected counts, and `SHOPIFY_CONFIRMATION_METRIC`
  (`confirmations.skipped`, `confirmations.nothing_to_fulfill`). The `token.*` lock/refresh metrics and
  their events are no longer in this catalogue: they come from `packages/shopify-token-management`
  (`TOKEN_METRIC`, `TokenEvent`) and are emitted through the same metrics service and logger. The `graphql.*` set comes
  out of `adapters/shopify/api/graphql.recorder.ts`, tagged
  `businessId`/`connectorId`/`shopName`/`operationName`, and covers mutations as well as
  queries. **`records.collected` is still mis-scoped on the poll path — it counts
  store-responses, not orders** (see [[known-context]]); the bulk reap path stamps a
  `source: bulk` tag (`INGEST_SOURCE`) on the same metric so the two ingest lanes split.
- **This service's monitors and dashboards are Terraform, in `gfs-bifrost/observability`**
  (`monitors.shopify-connector.tf` / `dashboards.shopify-connector.tf`), not in this repo's IaC.
  Two Terraform states managing one Datadog resource revert each other silently, so a
  `datadog_monitor` appearing in this repo is a defect, not a pattern to copy.
- **Confirmation source-mismatch monitors** (checked 2026-10-05): `[FUSE][Shopify Connector]
  Confirmation Source Mismatch — prod` (`318683760`) and `— dev` (`318683764`), on
  `sum(last_5m):avg:fuse.confirmation.unroutable{reason:source_mismatch,environment:prod}.as_count() >= 1`
  (dev the same with `environment:dev`), notifying `@team-bifrost @slack-bifrost-notifications`.
  Three things to know: the query has no `service` scope (only this service emits
  `source_mismatch` today, so it holds for now); the dev copy notifies Slack too; and the message
  text still says the subscription isn't filtered on source, which stopped being true when the
  `source`/`broadcast` filter shipped. `No Data` is the healthy state for this counter.
- **No ingest-window monitor exists** as of 2026-08-24 — see
  [[known-context#r1-permanent-order-loss]]. This is the single highest-value
  observability gap on this service.

## Real failure modes

- **A missed poll past a connector's retrieval window**: permanent order loss, no
  alert, no test can see it (stateless window, no watermark). The only lever today is
  `disable_shopify_poll` (pause, doesn't extend the window) + a Cloud Run traffic
  rollback to the prior revision (the actual fix) — not yet a rehearsed combined
  runbook.
- **A confirmation handler throwing**: caught by
  `ConfirmationProcessingExceptionFilter`, logged, replies `202` — Pub/Sub **acks and
  does not redeliver**, so a failed confirmation shows in logs, never as a stuck
  subscription. Same silent-202 shape for the fire-and-forget Shopify tagging on
  ack/failure handlers. Two things soften this: a confirmation that can't be delivered
  (routed, or any fan-out leg that takes goods-out) is published to `confirmation_data_failure`
  (see architecture), so look there for replayable ones; and if that publish, or the
  `confirmation_made` publish, itself fails, the filter replies **500** and Pub/Sub
  redelivers (`ConfirmationRedeliveryRequiredException`). That redelivery is bounded: from
  delivery attempt 10 the controller records a retryable `shopify-connector.redelivery_exhausted`
  failure instead of nacking again, so a stuck confirmation ends up in the failure inbox rather than
  looping.
- **The poll path itself throwing**: the opposite — it throws, so Pub/Sub redelivers.
  Deliberately asymmetric from the confirmation path.
- **Shopify GraphQL throttling**: detected even when it arrives as HTTP 200 with a
  `THROTTLED` body error (not just 429) — retried in place rather than failing the
  order outright. Two retries, each wait capped at 5s; past that the request throws and
  the poll re-runs on redelivery. `graphql.throttled` counts every throttle, absorbed
  ones included, so it is not itself an alarm; `graphql.retry.exhausted` is the one
  that means a request actually failed — though it covers 5xx and transient network
  exhaustion too, not throttles alone.
- **A shop's token going stale/invalid**: `handleTokenPersistError`
  (`packages/shopify-token-management/src/token-provider-base.ts`) currently never
  releases the lock on a persist failure — see [[known-context]] for why this is the
  single most dangerous known defect in the tree right now.

## Cross-checking

Chain a Shopify order id or SKU found in logs against the `snap` MCP tools
(`snap-search-shipments`, etc.) by business id, same pattern as the SNAP-side
services.
