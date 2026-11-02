---
tags:
- waypoint
- tracking-service
title: tracking-service — operations
verified: '2026-10-15'
verified_sha: 9f01957
verified_paths:
- .github/workflows
- iac/projects/tracking-service
- apps/api/cmd/redrive
---
# tracking-service — operations

## Deploy
- `deploy.yaml`: a push to `main` builds `tracking-service-api:<env>-<sha>`, applies dev, then builds and
  plans prod; the prod apply waits on the `terraform-prod` environment (approve via `pending_deployments`
  after reading the plan). Most merges plan as an image roll: 0 add / 1 change / 0 destroy.
- PRs get a dev plan comment (`tf-plan.yaml`), the Go gates and emulator job (`api-code-quality.yaml`) and
  SecOps scans (`secops.yaml`).
- Never push while a Deploy run is in flight.

## Hold and dead letters
- `ingest_hold = true` in `iac/env/tracking-service/<env>.tfvars` answers every push with 503 so Pub/Sub
  keeps messages (7-day retention). `dead_letter_enabled` must be false while holding, or the backlog
  dead-letters in minutes; validation enforces it.
- A message that fails 5 times lands on `….dlt` and is held on `….dlt.sub` for 7 days.
  `cmd/redrive -subscription <dlt-sub> -dry-run` replays it through the push path; redriving is idempotent.

## Observability
- Logs: `service:tracking-service project_id:bifrost-<env>-global1` (the `env` tag is `serverless`).
- Metrics: `fuse.tracking.*` tagged `environment:<env>`: `events.ingested`, `events.duplicate_folded`,
  `events.unprocessable`, `store.errors`, `ingest.lag`, `push.held`, `stage.duration`, `attention.count`,
  `orphans` (gauges: read with `max`).
- The platform Pub/Sub monitors (backlog, oldest unacked age, ack-deadline headroom, backlog not draining)
  cover its subscriptions. The tracking-service dashboard and its own monitors belong in the observability
  repo (`*.tracking-service.tf`).

## Health checks
- `num_undelivered_messages` ≈ 0 on all 40 subscriptions (20 push + 20 `.dlt.sub`).
- No 5xx from `tracking-service-api-<env>`; 503s only while held.
- Compare against fuse-ui's order tracker or `tracking-get-stats` for a sanity read.

## Real failure modes
- A store error returns 500 and Pub/Sub retries with 10–600 s backoff; persistent errors dead-letter.
- A new query without its composite index fails in prod only (the emulator doesn't enforce indexes);
  `indexes_test.go` is the guard.
