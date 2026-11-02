---
tags:
- waypoint
- wms-gateway
verified_paths:
- .github/workflows
- iac
- apps/gateway/internal/observability
- apps/gateway/internal/config
- apps/gateway/internal/core/stock
- apps/gateway/internal/core/configrevision
- apps/gateway/internal/adapters/cache
- apps/gateway/Makefile
verified: '2026-10-09'
verified_sha: 1a1f48d
---
# wms-gateway — operations

## Deploy

- Cloud Run v2 service `wms-gateway-{env}` in europe-west2, with the Datadog serverless-init sidecar and a
  `/shared-volume` log volume. Max 5 instances, 512Mi, 1 CPU, 60 s request timeout. The startup probe hits
  `/liveness/health` every second (30 tries) so a first check landing before the app listens costs 1 s, not 10.
- **Redis:** a BASIC-tier Memorystore instance per env (`cache.tf`, 1 GB, `REDIS_7_0`) on a dedicated VPC and
  subnet (`networking.tf`), shared by every instance for the response caches. Cloud Run reaches it by Direct
  VPC egress with `PRIVATE_RANGES_ONLY`; config-service, SNAP and Datadog keep the managed path. Host and port
  arrive as `NETWORK_CACHE_HOST` / `NETWORK_CACHE_PORT`.
- **Ingress is internal-only**, a deliberate divergence from the fleet default. fapi reaches it
  service-to-service. `run.invoker` is bound to `caller_service_account`, which defaults to empty (no fapi
  binding), and to the Pub/Sub push service account `wmsgw<env>-ps`. `caller_service_account` is set only by
  uncommenting the placeholder in `iac/env/{dev,prod}.tfvars`.
- **Config revision subscription** (`pubsub.tf`): a push subscription on bifrost-pubsub's `config_revision` topic
  to `/events/v1/config/revision`, OIDC-signed by the push SA, retry backoff 10 s to 600 s, no expiry. The route
  has no API key, so any principal with `run.invoker` can call it; harmless, since all it does is drop cached
  config. UNRESOLVED: whether Cloud Run counts the push as internal under `INTERNAL_ONLY` ingress was still to
  be confirmed on a dev apply (look for a `Config revision applied` log line after a test revision).
- `deploy.yaml`: push to `main` builds the image, then `terragrunt apply` to **dev** automatically. Prod
  runs plan → docker push → `terraform-prod` environment approval → apply. `manual-deploy.yaml` is the
  dev-only on-demand deploy of a branch (`gh workflow run manual-deploy.yaml --ref <branch>`).
- Reusable workflows are pinned at `ilg-platform/github-actions@0.1-affogato`. The app dir is
  `apps/gateway`, and the Dockerfile is the lowercase `dockerfile`, which the workflow has to be told.
- Inbound auth is a generated `SERVICE_AUTH_KEY` (`api-key.tf`), exposed as a Terraform output for fapi.
  Outbound config-service auth is an API key from Secret Manager, read via core-infra remote state.

## CI

`code-quality.yaml` runs fmt/build/vet/test/race/lint on `apps/gateway/**`. Locally, `make lint` fails with "Go language
version ... lower than the targeted Go version" because mise's golangci-lint is built with Go 1.25 and `go.mod` is 1.27.1;
build one with the module's toolchain: `GOBIN=<dir> go install github.com/golangci/golangci-lint/v2/cmd/golangci-lint@latest`
from `apps/gateway`. `gen-check.yaml` fails when the
generated canonical layer or `openapi.yaml` is stale. `secops.yaml` covers secrets, Go SAST, the Go dependency audit and the
container scan. The Node audit and Terraform jobs were dropped, so add them back if those surfaces grow.
Renovate raises `@gfs-bifrost/*` bumps (the codegen input); those PRs go through the same checks.

## Observability

Datadog `service:wms-gateway`, metrics namespace `fuse.` plus `wms_gateway.*`: `startup.duration`,
`stock.snapshot.build` and `.duration` (tagged by outcome, including `timeout`) and `stock.position.skipped`.
Config revisions count as `fuse.config_revision.applied` (result `ok` or `error`). Names and log
events are copied from pkg-node's `@gfs-bifrost/observability` catalogue (`internal/observability/catalog.go`,
`events.go`). SNAP metrics are tagged `snap_host` and `businessId`. Correlation ID is `x-request-id`. A
failed config fetch counts as `fuse.errors.config_api`, but a 404 there means an unconfigured business, not
a failure. Log lines for the sidecar file are held until its health port answers (up to 30 s, 1 MiB), because
the sidecar skips what a file already holds when it starts. Stdout gets them immediately. Whether any dashboard or monitor exists for this service is not known (see `known-context.md`).

## Failure modes (from code, not incident history)

- **SNAP down or slow:** retries (`SNAP_MAX_RETRY`, default 5), then the per-business breaker opens after 5
  consecutive faults and calls fail fast with `ErrCircuitOpen` for 30 s. The caller sees 502. A 4xx counts as
  healthy for the breaker.
- **SNAP concurrency saturated:** callers queue on the shared limiter (`snap.slot_wait`). The cap is
  service-wide 20 divided by max instances (4 per instance), and old and new revisions overlap during a deploy.
- **config-service unavailable:** a cached backend config still serves; otherwise the fetch fails after its
  retries and the request gets 503 `config_unavailable`. A business with no backend is 404
  `backend_not_configured`. A config change reaches the instance that receives the revision push at once;
  other instances pick it up within the 60 s memory tier and adapter TTLs. A config read in flight when the push
  lands can re-store the old config in Redis, where it lives up to 10 minutes.
- **Redis down:** at boot it is logged and skipped; mid-run each cache write still lands in memory, so the
  service degrades to per-instance caches rather than failing.
- **Stale reads by design:** the SNAP response cache (30 min default) serves repeated identical GETs
  without calling SNAP. It is shared across instances when Redis is up and per instance otherwise. Stock is the
  exception: it bypasses that cache, but is served from a per-instance snapshot up to
  `STOCK_SNAPSHOT_MAX_AGE_SECONDS` (270) old, so two instances can disagree by that much. Anything promising a
  freshness bound has to account for both.
- **Stock snapshot build slow or failing:** a build is bounded by `STOCK_SNAPSHOT_BUILD_TIMEOUT_SECONDS` (50,
  under the 60 s request timeout), after which callers get 504 `upstream_timeout`. A build reads many SNAP pages
  through the shared limiter, so it competes with other reads for the per-instance slots. A page failing fails
  the whole build and records one breaker fault. SNAP rejecting the credentials is a 502
  `backend_credentials_rejected`.
- **SNAP type drift:** a field arriving as the wrong type is absorbed by weak decode. A structural change
  fails decode (`snap.response.invalid{reason}`) or canonical validation, both surfacing as 502.
