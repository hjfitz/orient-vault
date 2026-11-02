---
tags:
- waypoint
- fuse-mcp
verified: '2026-10-01'
verified_sha: 660d14d
verified_paths:
- internal/observability
- .github/workflows
- iac
title: fuse-mcp — operations
---
# fuse-mcp — operations

## Deploy

Push to `master` → `deploy.yml` → Cloud Run, straight to prod — there is no dev
environment and no leg. `deploy.yml` runs concurrently with
`code-quality.yaml`/`go-code-quality.yaml`, with no `needs:` between them, so a
red quality check does not block a deploy already in flight. `secops.yaml`
(gitleaks, node dependency-audit, semgrep for both toolchains, and a Trivy
scan per production image — `image_scan` for `Dockerfile`, `image_scan_go`
for `Dockerfile.golang`) runs on PRs and a 06:00 cron, never on a push to
`master`; `tf-output.yaml` (posts a `terragrunt plan` PR comment) is PR-only
and path-filtered to `**.tf`/`**.hcl`/`**.tfvars`. A direct commit to
`master` therefore triggers neither.

`go_traffic_percent = 100` (`iac/env/prod.tfvars`): Go serves everything, the
TS service stays deployed and warm at weight 0. **Rollback is lowering that
number and applying** — a weight change, not a redeploy. Verify a risky
change on the Go service's own Cloud Run URL before it can reach the LB.

Terraform: `iac/projects/fuse-mcp`, Terragrunt, `europe-west2`,
`bifrost-prod-global1`. The prod revision is really **3 CPU / 1.5 GiB**, not
the 1 CPU / 512 Mi the app itself requests — two Datadog `serverless-init`
sidecars (one per org, GFS + ILG) each add another 1 CPU / 512 Mi.

## Observability (no APM)

Logs + custom metrics only.

- **The logging contract is deliberately unmodernised**: a hand-rolled logger
  (57 lines in the TS original; the Go `slog` handler reproduces the same
  shape) writes JSON lines to `LOG_FILE`, tailed by the two sidecars. `status`
  holds the Datadog log-level string; the actual HTTP status code lives in
  `httpStatus` — a deliberate naming carry-over, not a bug.
  `source: "go"` (mirroring the fuse-mocker Go port's convention) is how the
  two implementations are told apart in Datadog while both stay deployed,
  since both keep `DD_SERVICE=fuse-mcp`.
- **Only the Go server emits custom metrics** (the TS one emits none), so a
  TS-vs-Go comparison has to come from `gcp.run.*` by `service_name` or the LB
  access logs. Five, DogStatsD, `fuse.` namespace, declared once in
  `internal/observability/metrics.go` and **contractual with the dashboard** —
  a rename flattens a graph and fails nothing: `fuse.mcp.request` /
  `.request.duration` (tags `mcpMethod`, `tool`, `outcome`),
  `fuse.mcp.downstream` / `.downstream.duration` (tags `target`,
  `environment`, `outcome`), and `fuse.mcp.panic` — any non-zero value there
  is a bug, not a threshold. An absent `mcpMethod`/`tool` is tagged `unknown`
  rather than omitted, so a grouped graph keeps the series. Emission is gated
  on `LOG_FILE` being set (the sidecars that tail it are the same containers
  that accept DogStatsD) and degrades to a no-op, so a local run sends nothing
  and a broken socket never fails a request.
- **Dashboard**: "FUSE — MCP Server (Go cutover)"
  (`app.datadoghq.com/dashboard/u54-iz6-ag5`) — verified 22 of 24 widgets
  against real data as of the migration doc's last update; the two empty ones
  are panic counters, which is the intended state (no panics to show).
- **`DD_ENV = "serverless"`**, not `prod` — consistent with the fleet-wide
  compute-type convention seen on every other Cloud Run service this session;
  disambiguate by `environment`/`@environment`, never `DD_ENV`.

## Real failure modes

- **A `tools/call` with `null` arguments**: was a full-process crash before the
  fix landed (see [[known-context]]); now normalises to `{}` and answers the
  schema's own validation message, with a panic-recovery middleware as backup.
  If a Cloud Run instance is mysteriously restarting under load, check this
  path hasn't regressed.
- **A cross-backend protocol-version mismatch during the split**: presents as
  intermittent 400s that look exactly like network flakiness. Confirmed fixed
  by a version cap in `internal/bootstrap/middleware.go` — if a similar
  intermittent-400 pattern reappears, check whether something else
  per-connection (not just the protocol version) has diverged between the two
  implementations.
- **A soak that appears to pass but never actually reached the Go backend**:
  happened once already — LB config propagation lags a Terraform apply. Always
  confirm both backends actually served real requests via
  `resource.labels.backend_service_name` in the LB access logs before trusting
  a green soak. `gcloud compute url-maps validate` cannot simulate weighted
  routing and is not a substitute for this check.
- **The LB hard-caps every tool call at 30s** (`timeout_sec`), independent of
  which backend serves it — a slow downstream call (config-service, dedupe,
  etc.) can hit this regardless of the Go/TS split.

- **Every `mock-*` call returns a Next.js 404 page**: `MOCKER_STAGING_URL` is
  wired to the fuse-mocker dev state's `api_service_url` (the Go API). The UI
  service's `service_url` no longer serves `/api/v1`, so pointing the env var
  there reproduces this. An absent or unapplied mocker state degrades the env
  vars to empty and the tools report "not configured".
- **A red `parity` job after an intended `data/*.json` change**: refresh the
  baseline with `make parity-accept` (needs `dist/` built), not a bare
  `tools/capture` overwrite, which drops Go-only tools from the declarations.
  `parity` runs as its own job in `go-code-quality.yaml`, separate from
  `quality`.

## Gotchas from shipping the audit tools (2026-10-22)
- `printf '<json-rpc>' | go run ./cmd/fuse-mcp` prints nothing: stdin EOF closes the server before it answers. Build the binary and hold stdin open (`{ printf …; timeout 4 tail -f /dev/null; } | ./bin`) to capture `tools/list`.
- `parity_test.go`'s failure hint says to recapture with `tools/capture/capture.mjs`; don't — it drops the Go-only declarations. New tools are hand-added to the baseline; only data edits need `make parity-accept`.
- A stacked PR gets no CI and no `tf-output` plan comment until it targets `master`. Stack members merge only via `PUT …/pulls/N/merge-async`, and GitHub rebases the children itself after each merge.
- A new env var on a service whose env list holds `MCP_AUTH_TOKEN` shows in the plan as a masked `+ env {}`; confirm name and value with `gcloud run services describe` after apply.
- The hosted MCP has no dev leg, so the audit tools' success path is only provable in prod: they answer the fixed 403 text until audit-service lists `fuse-mcp-prod-sa` (proves the token is minted and accepted).

## Cross-checking

There is no separate MCP for investigating fuse-mcp itself — its own logs (via
the shared JSON-lines-to-file contract) and the `u54-iz6-ag5` dashboard are the
primary tools. Correlate a specific tool call by its request path in the LB
access logs plus the app log line it produced.
