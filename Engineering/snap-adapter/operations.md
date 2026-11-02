---
tags:
- waypoint
- snap-adapter
verified: '2026-10-14'
verified_sha: b16942a
verified_paths:
- apps/snap-adapter/src/observability
- .github/workflows
- iac/projects/snap-adapter
- iac/env
- apps/snap-adapter/docker-compose-4pipeline.yaml
- apps/snap-adapter/tests
title: snap-adapter — operations
---
# snap-adapter — operations

## Deploy

Push to `master`/`main` (path-filtered to `apps/snap-adapter/**` +
`iac/projects/snap-adapter/**` + `iac/env/**` + the workflow file) triggers
`snap-adapter-on-push.yaml`: docker build+push dev → `terragrunt apply dev` → plan
prod + docker push prod → `terragrunt apply prod`, gated by the `terraform-prod`
GitHub environment approval. The poller's workflow filters on `iac/env/**` too, so an
`iac/env/*.tfvars` edit redeploys both apps, dev and then gated prod; app and per-project
changes deploy independently of `snap-queue-polling-service`.

Manual dev-only deploy: `gh workflow run "Manual Deploy snap-adapter" --ref <branch>`.

Cloud Run service: `snap-adapter-{env}` (matches the repo/app name — no naming
footgun here, unlike the poller).

## Observability (no APM)

Logs + custom metrics only, via `@gfs-bifrost/observability` /
`@ilg-platform/observability` (`fuse.*`/`snap.*` namespaces, typed recorders — `SnapRecorder`,
`RequestRecorder` — and the `*Event`/`FuseEventLogger.event()` catalogue from
`@gfs-bifrost/observability`, with app-local events in `src/observability/events/`).
Failure logs carry classified facets (`errorMessage` etc.), never the serialised
transport error: a raw AxiosError embeds the request preamble, including the
`Authorization` line, which key-based redaction can't reach.

- **Datadog `service` tag**: `snap-adapter`. Distinguish dev/prod via `environment`,
  not `env` (sidecar stamps `DD_env: serverless`).
- **Customer identity**: the `customer` field in logs is the Fuse businessId
  (uppercase, e.g. `GADG`) — matches SNAP's own `BizId` directly, so a log's customer
  tag can be pasted straight into a SNAP OData filter (`BizId eq 'GADG'`).
- **`snap_adapter.snap.request*` metrics** are the concurrency-health signal — this
  is exactly what root-caused the May 2026 overload incidents (see
  [[known-context]]). Watch these first if SNAP writes start failing broadly.
- **Log correlation**: `Correlation.set`/`.get` scopes carry `correlationId`,
  `businessId`, `flow` (`create`/`config`), `recordType`, `recordId`,
  `connectorId`, `deliveryAttempt` — trace one create attempt (including its
  redeliveries) by `correlationId` + `deliveryAttempt`.
- **`messageSource`**: originating connector rides under `messageSource`, not the
  bare SDK-reserved `source` key (which Datadog's own ingestion pipeline uses as
  `ddsource`) — grep `messageSource` for connector-level faceting, not `source`.
- **Routing-store metrics**: the Firestore write emits
  `snap.routing_store.written`/`.skipped`/`.failure`, and the sales-order Shopify
  line data in the same write emits `snap.line_extension_store.soline_collision` (lines
  sharing a `SOLineId` with differing extensions, dropped from the doc).
  `snap.line_attachment.unmatched` counts a canonical line with no ordered SNAP line to
  hang its customisation attachments on. A `snap.routing_store.failure` is a create
  failure: the delivery 503s as `routing_persistence` and is counted in
  `snap.entity_not_created{failure_mode:routing_persistence}` (see
  [[architecture#routing-store]]). No Datadog monitor watches `snap.routing_store.failure`
  or that `failure_mode` yet; the general "Entity creation failed" monitor
  (`snap.entity_not_created{environment:prod} > 0`) catches the create failure.
  `snap.entity_already_in_wms` — tagged by how it was detected (`precheck` vs
  `write_rejection`) — counts records SNAP already held that the app acknowledged without
  writing, and is deliberately kept **off** the create-failure metrics.

## Real failure modes

- **SNAP overloaded / degraded**: per-host circuit breaker trips on consecutive
  5xx/network failures, short-circuiting further requests to that host during the
  cooloff. Semaphore + token bucket cap concurrency/rate before that point is ever
  reached under normal load.
- **A single create fails transiently** (5xx/429/timeout, under the retry budget) — or
  is rejected **before it ever reaches SNAP** (a concurrency-slot acquire timeout, an
  open circuit breaker): both classify as transient, so the response is `503` with no
  publish and Pub/Sub redelivers with 10s–600s backoff. Silent from the outside
  until/unless it exhausts. A pre-dispatch rejection carries no request/response, so
  the failure-metrics interceptor passes it through untouched — the classifier sees the
  real slot-timeout/open-circuit error and files it transient, not a permanent
  `unexpected` fault.
- **A create exhausts its retry budget, or fails permanently (4xx/validation)**: the
  app publishes `entity_error`/`create_data_failure` itself and returns `204` — this
  is captured and replayable via replay-service; **not** a loss.
- **SNAP already holds the record** (`already_in_wms`): the pre-write shipment read
  finds a later-stage shipment, or a keyed re-PUT is rejected with only an
  `XDoc`/"Invalid Order Stage" field error. The record is live and unchanged, so the
  app **acknowledges it as if created**, keeps the deduper hold, and publishes nothing
  else. Metered as `snap.entity_already_in_wms`, **not** as a create failure — failure
  monitors are unaffected. Not a loss.
- **SNAP has cancelled or purged the record** (`cancelled_in_wms` — shipment Stage
  91/99 or header Status 01): terminal, but the **deduper hold is kept and nothing is
  published**. A release — including the one the deduper performs off
  `create_data_failure` — would send the order straight back onto the cancelled
  shipment, so the create is deliberately left silent.
- **The routing-store write fails**: always transient (`RoutingPersistenceException` →
  `503`/redelivery), with no flag to roll it back. A sustained Firestore outage stops
  every routed create until it recovers. Each create exhausts after 10 attempts into
  `entity_error`/`create_data_failure`, held by replay, and the deduper releases off it
  so the source can re-send.
- **A create fails in a way the app can't cleanly handle** (crash, hang, infra-level
  delivery failure) **and** exhausts Pub/Sub's own dead-letter delivery count: routed
  to a DLT topic with **no configured consumer** — this *is* a loss. See
  [[known-context#no-consumer-on-the-dead-letter-topic]]. This is the standing gap to
  flag before calling this service "safe against downtime."
- **SNAP write returns opaque partial success** (`Successes: 0/1` with no obvious
  reason): don't trust the top-level message — `collectSnapFieldErrors`' structural
  walk of the response is what actually surfaces the per-field reason; check the log's
  `fieldErrors`/`snapResponseBody` rather than re-deriving it by hand.

## Black-box harness and dev end-to-end

- **Black-box harness** (`apps/snap-adapter/docker-compose-4pipeline.yaml`, the one CI runs; the plain `docker-compose.yml` is a stale pre-monorepo variant). Run `docker compose -f docker-compose-4pipeline.yaml up -d --build`, then `tests/start-test.sh`, with `GITHUB_TOKEN` set for the private packages. The Firestore emulator uses the `google-cloud-cli:emulators` image with a bash TCP healthcheck: an HTTP probe crashes the gRPC emulators. That gotcha is written only as a compose-file comment. Expected external-call counts per case live in `tests/test-cases.ts`.
- **Host-port collisions**: on a machine running other emulators (e.g. a shopify-connector stack holding 8085), remap or strip host ports, or run under its own compose project name. Two overlapping runs double every external-call count.
- **Stacked PRs get no CI.** `code-quality` and `blackbox-testing` trigger only on PRs into `main`/`master`, so a PR whose base is another branch runs nothing until it is retargeted. Run the harness locally before relying on a new e2e case.
- **Pre-PR checks**: `apps/snap-adapter` has no `build:check:tests` script. `tsc -p tsconfig.json --noEmit` showed 10 errors in spec/fixture files on master as of 2026-09-30, none from that work, so compare against master's count, not zero.
- **Dev e2e through the fuse-mocker snap-api simulator** (business HJF, whose `BACKEND_CONFIG` host points at it): the real adapter and poller run against simulated SNAP activity. To move a shipment past Stage `00` (picked/packed/despatched), call the simulator control plane: `POST https://crackle.devtools.fuse.freightops.dev/api/v1/businesses/HJF/shipments/{id}/advance` with `{"toStage": "picked|packed|despatched"}` and header `x-api-key`. The key is the `snap_api_key` output of the fuse-mocker Terraform stack (dev state); read it, use it, delete the local copy. The `snap` MCP's `snap-write` can't change a shipment's Stage (PATCH → 405). Since fuse-mocker `2885dd6`/`15477b0` the simulator's despatch stock, stock consignment and StU rows pass the poller's schemas, so a full goods-out completes. Its SNAP timeout fault never persists the write, so a "PUT landed but timed out" redelivery can't be reproduced; that path is covered by controller unit tests.

## Debug / cross-checking

Chain a SNAP entity id (`ShipmentId`/`ReceiptId`/`queueId`) found in a
`correlationId`-scoped log directly into the `snap` MCP tools
(`snap-get-shipment`, `snap-get-receipt`, `snap-get-outbound-queue`) by business id,
same pattern as the polling service.
