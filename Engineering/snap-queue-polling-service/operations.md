---
tags:
- waypoint
- snap-queue-polling-service
verified: '2026-10-09'
verified_sha: c5e7bcb
verified_paths:
- apps/snap-queue-polling-service/src/observability
- apps/snap-queue-polling-service/src/core/snap/confirmations/confirmation-failure.ts
- apps/snap-queue-polling-service/src/core/stock-sync
- apps/snap-queue-polling-service/src/http/middleware/error.middleware.ts
- .github/workflows
- iac/projects/snap-queue-polling-service
- apps/snap-queue-polling-service/src/core/snap/confirmations/outbound-queue.clearer.ts
- apps/snap-queue-polling-service/src/adapters/snap
- apps/snap-queue-polling-service/src/config
- iac/env
title: snap-queue-polling-service — operations
---
# snap-queue-polling-service — operations

## Deploy

Push to `master`/`main` (path-filtered to `apps/snap-queue-polling-service/**` +
`iac/projects/snap-queue-polling-service/**` + `iac/env/**` + the workflow file) triggers
`snap-queue-polling-service-on-push.yaml`: docker build+push dev → `terragrunt apply
dev` → plan prod + docker push prod → `terragrunt apply prod`, gated by the
`terraform-prod` GitHub environment approval. `snap-adapter`'s workflow filters on
`iac/env/**` too, so an `iac/env/*.tfvars` edit redeploys both apps, dev and then gated
prod; touching one app's code or its own project never redeploys the other.

Manual dev-only deploy: `gh workflow run "Manual Deploy snap-queue-polling-service"
--ref <branch>` (`workflow_dispatch`).

Cloud Run service names: `snap-polling-service-dev` / `snap-polling-service-prod` —
**not** the repo name (see [[overview#naming-three-spellings-one-service]]).

Topic names and publisher IAM come from the `bifrost-pubsub` remote state
(`iac/projects/snap-queue-polling-service/remote.tf`). A newly-added topic — most recently
`confirmation_data_failure` — must be applied there first, or this app's plan fails on the
missing output rather than on anything in its own stack. The same goes for `core-infra`'s
`stock_sync_export_bucket_name` output (`remote.tf`). The stock sync topics and their
subscriptions are this stack's own (`pubsub.tf`), not `bifrost-pubsub`'s.

## Observability (no APM)

Fuse has no tracing — logs + metrics only, via `@gfs-bifrost/observability` wrapping
`@ilg-platform/observability`.

- **Datadog `service` tag**: `snap-polling-service`. Distinguish dev/prod by the
  `environment` tag, not `env` — the serverless-init sidecar stamps `DD_env:
  serverless` on everything.
- **Two metric namespaces**: fleet `fuse.*` (`fuse.request`, `fuse.confirmation.*`,
  `fuse.errors.*`) and WMS-specific `snap.*` (`snap.poll.request/.success/.failure/
  .latency` tagged `snap_host`, `snap.circuit_breaker.state`, `snap.poll.failure`
  aggregated with no `snap_host`, `snap.poll.skipped_circuit_open`,
  `snap.confirmation.hanging/.unparseable/.claim.duplicate/.claim.fail_open`,
  `snap.routing_lookup.hit/.fallback_attachment/.miss` (tagged `type`) and `.error`
  (tagged `lane`) for routing-doc resolution,
  `snap.confirmation.connector_source.resolved/.unresolved`, and
  `snap.confirmation.withheld_unresolved_connector` (tagged `type`, `businessId`,
  `reason`)), `snap.line_extension_lookup.soline/.line/.attachment/.miss` (tagged
  `businessId`; which tier resolved a goods-out line's extensions),
  `snap.confirmation.partial_order_failed` (tagged `businessId`),
  `snap.confirmation.batch_attribution_ambiguous` / `.batch_not_matched` (tagged `type`,
  `businessId`; pick and pack batch guesses), the stock sync fan-out
  `snap.stock_sync.due_published` / `.due_publish_failed` (tagged `businessId`) and
  `.connector_unresolved` (tagged `reason`), the stock sync run
  `snap.stock_sync.export_lines` / `.export_published` / `.kit_skipped` (tagged `businessId`)
  and `.export_failed` (tagged `businessId`, `stage`), and clear after publish
  `snap.outbound.cleared` (tagged `type`, `businessId`) with `.clear_failed` / `.clear_skipped`
  (also tagged `reason`).
  `fuse.confirmation.manual_origin_broadcast` (tags `type`, `businessId`) counts records
  published with no originating connector, i.e. broadcast to every connector. The old
  flat `snap-polling-service.*` prefix and `snap.request*` names are retired — repoint
  any dashboard/monitor still on them.
- **Lookup counters count mappings, not confirmations.** `snap.routing_lookup.*` and `snap.line_extension_lookup.*` increment each time an item is mapped. The poll runs every 2 minutes (`poll_schedule` `*/2 * * * *`), and an item still on the outbound queue and not yet claimed is re-mapped on every poll. So a stuck or unconfirmed goods-out multiplies its counts. Compare tiers as ratios, or watch for a tier going to zero, rather than reading absolute counts as orders. `routing_lookup.*` carries no `businessId` and dev and prod both report under `env:serverless`, so filter by `environment`.
- **Log tags to grep**: `DROPPED_CONFIRMATION`, `DROP_GOODS_IN_CONFIRMATION_LINE`.
  Correlation (`correlationId`, `businessId`, `flow`, `recordType`/`connectorId`) rides
  every log line via the SDK's `Correlation` facade — trace one poll cycle by
  `correlationId`.
- **Errors are logged as chosen facets, never the raw error.** A serialised transport error
  carries the raw request preamble including the `Authorization` line, which key-based log
  redaction can't reach; `serialiseError` (from `@gfs-bifrost/observability`) emits only
  name/message/code/status/stack plus method/url/baseURL/params, and the error middleware's
  response body gets the same treatment. Don't log a caught axios error directly.
- **Cross-check with SNAP directly** using the `snap` MCP tools (`snap-get-outbound-
  queue`, `snap-search-receipts`, `snap-get-shipment`) by business id, chaining a
  `queueId`/`ReceiptId` found in a log into the live WMS record.

## Real failure modes

- **SNAP outage / 5xx**: per-host circuit breaker trips after 5 consecutive
  failures, `snap.poll.skipped_circuit_open` fires, queue reads short-circuit to `[]`
  instead of throwing — the service doesn't hammer SNAP or replay the whole backlog
  every 2 min. Self-healing once SNAP recovers.
- **Redis down**: config cache miss falls back to a fresh config-service fetch;
  confirmation claims fail `"unavailable"` and **fail open** — confirmations still
  publish, at the cost of losing INC-30 dedup protection until Redis recovers. This is
  a deliberate tradeoff (never silently drop confirmations because a cache is down).
- **A business's outbound-queue backlog blows the ack deadline (INC-30)**: bounded by
  the 600s ack deadline mitigation + the queueId claim (see
  [[known-context#inc-30]]) — a redelivered poll now gets filtered to "duplicate" and
  doesn't re-publish, rather than the pre-fix behaviour of one publish per redelivery.
- **A single business's bad SNAP credentials (4xx)**: does not trip the shared
  per-host circuit breaker (host breaker only trips on 5xx/network) — isolated to
  that business's poll failing, other businesses on the same host are unaffected.
- **A confirmation with no originating connector**: published with `broadcast="true"` to
  every connector, counted on `fuse.confirmation.manual_origin_broadcast`, and — for the
  seven routing-aware types — mirrored as an informational `BifrostFailure`
  (`no_originating_connector`) onto `confirmation_data_failure`. Normal for a
  hand-made-in-SNAP record, not an error. **Nothing downstream treats it as
  informational**: replay-service subscribes to that topic filtered on `recordType` and
  derives replayability from `useCase`, not from the error type — so one of these can sit
  in the exceptions inbox looking retryable, and a Retry re-announces a confirmation that
  already went out. Treat a Retry on one of these as a duplicate-confirmation risk.
  UNRESOLVED: which of the seven record types actually reach a subscriber. The app's own
  CLAUDE.md claims replay covers pick/pack/WOC/FGR and collector additionally marks WOC/FGR
  failed in Customer Transaction History; the Fuse MCP topology lists replay as the only
  subscriber and doesn't yet list this service as a publisher at all.
- **A confirmation's originating connector can't be resolved**: when the routing store
  carries a bare `connectorId` but no `source`, the connector-source lookup
  (`resolveConnectorSource`, step 3 of routing resolution in [[architecture]]) can throw a
  `FuseConfigApiException` with `connectorResolutionFailure` set — `"gone"` (config-service
  says the connector no longer exists) or `"unavailable"` (the config-API call itself
  failed). The whole customer group is then **withheld**: left on the outbound queue,
  retried next cycle, nothing published — **unless** the business has
  `broadcastConfirmations`, which still broadcasts it. Withheld groups log
  `tag: DROPPED_CONFIRMATION` and meter `snap.confirmation.withheld_unresolved_connector`
  (tagged `type`, `businessId`, `reason`); a lookup that resolves meters
  `snap.confirmation.connector_source.resolved`/`.unresolved`. Any other error (a bare
  axios/network failure) rethrows rather than being read as "connector doesn't exist".

- **A goods-out whose stored lines name a `SOLineId` SNAP no longer has**: failed rather than
  confirmed in part. A non-retryable `business_rule` / `stored_lines_unmatched` failure (record
  = the surviving lines' confirmation) goes to `confirmation_data_failure`, the queue item is
  cleared and `snap.confirmation.partial_order_failed` fires. Expect it in the exceptions inbox
  for an order edited or partly cancelled in SNAP after Fuse created it; replay confirms only
  the surviving lines.
- **A published confirmation's row won't clear** (allow-listed businesses only): the
  publish went out, the `PATCH .../processed` didn't take (`snap.outbound.clear_failed`,
  split by `reason`: `snap_error`, `not_cleared`, `invalid_response`, `circuit_open`,
  `request_failed`, `no_client`). The row stays queued and re-announces, so a stuck clear
  is a duplicate-confirmation risk, never a loss. An open SNAP circuit stops the group's
  remaining clears and logs `Outbound queue clear stopped: SNAP circuit open` once. A
  monitor in the `observability` repo fires above 10 failures in 30 minutes per business.
- **A stock sync run fails**: acks and publishes nothing, logs `Stock sync run failed` (or
  `Stock sync has no Snap backend for business`) and meters `snap.stock_sync.export_failed`
  by `stage`; the next 15-minute tick retries. A monitor pages on any in the last day. A
  single kit that Snap 5xxs is left out of the export instead (`Stock sync kit read failed,
  kit left out of export`, error level, `snap.stock_sync.kit_skipped`), so the storefront
  keeps its last level for it; another monitor fires on that log. A tick that matches no
  connector logs `Stock sync schedule evaluated` with `dueConnectors: 0`.

## Debug endpoints (ops use, not customer-facing)

`POST /debug/trigger` (force a full poll+announce, including clear after publish for an
allow-listed business) and `POST /debug/check` (dry-run
goods-out fetch, returns JSON, does not announce) — both behind `x-api-key` when
`API_KEY` is set (`publicAccessEnabled = !!API_KEY`); if `API_KEY` is unset, these are
open. `/event/*` routes are protected only by the Pub/Sub push subscription's OIDC
token at the infra layer, not by app code.

## Stage-2 time budget

`snap-polling-service` runs with a Cloud Run request timeout of `timeoutSeconds=600`
(`cloud-run.tf`), matching the 600s ack deadline on the poll and stock-sync-due
subscriptions, so a stage-2 chunk has the full 600 s. Clear after publish shares that budget:
at the default concurrency of 3, about 1000 rows take about 100 s (an estimate). A
timed-out invocation leaves rows published but uncleared. That risks a duplicate, never a
loss, because they re-announce. To turn clearing down in an incident, use
`clear_after_publish_concurrency` (a Terraform variable) or remove the business from
`clear_after_publish_business_ids`.
