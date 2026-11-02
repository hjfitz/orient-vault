---
tags:
- waypoint
- replay-service
verified: '2026-10-09'
verified_sha: 3d0482b
verified_paths:
- code/src/observability
- code/src/core/failure
- code/src/http/controllers
- .github/workflows
- iac/projects/replay
- iac/env
title: replay-service — operations
---
# replay-service — operations

## Deploy

`on-push.yaml` on push to `main`/`master` — **no path filter**, a docs-only push
redeploys. Dev auto-applies; prod is plan + `terraform-prod`-gated apply. Manual
dev-only deploy: `gh workflow run manual-deploy.yaml --ref <branch>`. Cloud Run
service `replay-{env}`, `europe-west2`, ingress public (`allUsers`), Direct VPC
egress `PRIVATE_RANGES_ONLY`. Prod keeps one instance warm (`min_instance_count = 1` in
`iac/env/prod.tfvars`); dev scales to zero.

## Observability (no APM)

Logs + custom metrics only, dual-shipped to GFS + ILG Datadog orgs.

- **Naming split — check which one your query keys on**: Cloud Run service =
  `replay-{env}` (what `gcp.run.*` carries); app logs/metrics/traces =
  `service:replay_service` (custom metrics emit under the fleet namespace as `fuse.replay.*`). The
  sidecar hardcodes `DD_SERVICE=replay` / `DD_ENV=serverless` — disambiguate
  dev/prod by the `environment` tag, never `DD_ENV`.
- **Correlation**: set through the `@gfs-bifrost/observability` `Correlation` facade
  (`correlationId`, `businessId`, `flow: "redrive"`, `recordType`/`recordId`); each redrive
  runs in its own child scope so bulk fan-out stays isolated. Log messages come from the
  shared event catalogue plus three local ones in `code/src/observability/events/`
  (failure intake, redrive, clear-down). UNRESOLVED: whether these appear in Datadog nested
  under `requestor` or as flat top-level attributes since the catalogue adoption; check a
  live log line before building a query on either.
- **Live monitors** (verified 2026-08-24, all notifying `@team-fuse-developers`):
  - `[Replay] Ingest lag high` — an unacked message older than 5 min on any
    `replay.*` subscription; on `create_data_failure` this means replay is
    falling behind; would also catch a poison-loop on a subscription with no
    DLT policy.
  - `[Replay] Failure dead-lettered on create_data_failure` — fires the instant
    a message exhausts retries onto the unconsumed DLT; see
    [[known-context#dlt-monitored-not-consumed]].
  - `[Replay] Failures dropped forever (unparseable create_data_failure)` — real
    permanent data loss, not a false alarm.
  - `[Replay] 5xx rate high` — Retry Queue screen or create-failure ingest
    availability; 4xx is deliberately excluded (internet scanner noise + bad
    API keys are expected background).

## Real failure modes

- **replay-service itself down for an extended period**: incoming
  `create_data_failure`/`confirmation_data_failure` messages redeliver with
  backoff, then dead-letter after 5 attempts into an **unconsumed** topic —
  caught by the dead-letter monitor, not silently lost, but recovery is manual
  (someone has to notice the alert and act, there's no auto-redrive off a DLT).
- **A malformed/unparseable failure payload**: ack-and-dropped immediately,
  **permanent loss**, its own dedicated alert. If this fires, the fix is on the
  *producer* side (fix the shape being published), not here.
- **A record that won't replay**: the strict-schema revalidation at replay time
  is the intended gate, not a bug — `GET /failures/:id`'s `replayable`/
  `blockingIssues` tells you exactly what's wrong before you try, using the
  identical schema the replay call itself will run.
- **A replay 400 that isn't the schema gate**: `No replay topic configured for
  use case: <x>` means the destination env var is unset on the running revision
  (or the record type has no `getReplayTarget` case) — an infra/deploy problem,
  not a bad record. Two destination env vars feed replay:
  `CREATE_RECORD_REQUEST_TOPIC` and `CONFIRMATION_READY_TOPIC`, each with its own
  `roles/pubsub.publisher` grant in `iac/projects/replay/iam.tf`.
- **A confirmation redrive 400 about routing**: `Cannot redrive: failure source … is not a
  delivery channel and no routing is set`. The failure came from snap-adapter's clear-down
  or the poller rather than a connector, so there is nobody to send it to; set `routing`
  on it via `PATCH` (the detail view shows `replayable: false` first).
- **A redrive that reports success but nothing arrives**: connector subscriptions on
  `confirmation_ready` filter on `attributes.source` (or `broadcast`), plus `connectorId`
  narrowing. Check the failure's `redriveRouting` against a real connector on that channel
  before assuming a publish problem.
- **A failure stays in the Retry Queue after its confirmation was delivered**: clear-down
  did not match it. Check the delivery's `recordType` is on one of the two `confirmation_made`
  subscription filters, the ack carries `identifiers.businessId` and the type's record identifier
  (otherwise a `ConfirmationMissingIdentifiers` warn and no clear), and, for a connector-pinned
  failure, that the ack's `metadata.connectorId` names that connector. A drop shows in
  `replay.confirmation_made_dropped`; a successful clear in `replay.confirmation_failures_cleared`.
- **A confirmation failure never appears in the queue**: a `no_originating_connector` notice is
  acked and skipped on purpose (`replay.confirmation_failure_informational_skipped`); it is the
  poller's record of a broadcast that already went out.
- **A large bulk-replay burst**: capped at 100 ids per call, 5-at-a-time, so a
  big batch can't burst SNAP/connectors all at once — but 100 ids at 5
  concurrent still means real downstream load; don't assume bulk-replay is free
  just because the call itself returns quickly.

## Cross-checking

`mcp__fuse__replay-list-failures` / `replay-get-failure` / `replay-retry` hit
this service's live API directly (prod retries require `confirm: true`) — use
these for investigation and redrive rather than hand-rolling API calls.
