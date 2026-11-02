---
tags:
- waypoint
- secops-reporting
verified: '2026-10-01'
verified_sha: 73f60ef
verified_paths:
- iac
- .github/workflows
- api/internal/observability
- api/internal/config
- api/internal/bootstrap
title: secops-reporting — operations
---
# secops-reporting — operations

## Deploy

**Any push to `main` triggers a full deploy** — no path filter, even a
docs-only push redeploys both apps. `on-push.yaml`: `terraform apply` of
`secops-pubsub` (no image) in parallel with the two docker build+pushes,
then `secops-api` apply (needs pubsub + its image), then `secops-ui` apply
(needs the API apply — it reads the API's `remote_state`). The
`terraform-prod` GitHub environment gate (approved by the
`platform-admins` `ilg-platform` org team) sits on the docker-push jobs and
the pubsub apply. Slack notifications are **off** (`notify_on_*: false` —
`SLACK_WEBHOOK_URL` is not set on this repo). The repo's `CLAUDE.md` says direct commits, no PR or review, but recent changes
have in fact gone through PRs (with `tf-output.yaml` plan comments); either way
the merge to `main` is what deploys.

The API is **one Go revision at 100%**: `cloud-run.tf` carries a single
explicit `traffic { LATEST, 100 }` block and no tags. Keep it explicit —
`traffic` is Optional+Computed, so omitting the block leaves whatever was
last applied in place (that's how the Node `node` tag stayed publicly
reachable after the cutover blocks were removed, `1261a2c`). The
cutover-era variables (`go_image_name`, `go_traffic_percent`,
`node_revision`) are gone; **rollback is a revert + push**, or
`gh workflow run manual-deploy.yaml --ref <branch> -f service=api` from a
branch at the wanted sha (its API apply does not depend on the pubsub job
— that state already exists).

Cloud Run: `secops-api-prod` and `secops-ui-prod`, both
`bifrost-prod-global1`/`europe-west2`. Pub/Sub topic
`secops-vulnerability-report-prod` (state `prod/secops-pubsub`). No dev
or staging exists anywhere.

## Secrets

Ingest API key, UI session secret, and the dashboard's basic-auth login
password are all Terraform-generated `random_password`s, held in state as
plain Cloud Run env vars. Get the dashboard login password with:

```bash
cd iac/projects/secops-ui && terraform output -raw basic_auth_password
```

Repo-level GitHub secrets the workflows read: `MONGO_ATLAS_PUBLIC_KEY`/
`PRIVATE_KEY` (Atlas provider), `DATADOG_API_KEY`/`_ILG` (absorbed only —
no sidecar), `GH_TOKEN` (UI's `@ilg-platform/ui-toolkit` install; the API
build pulls from the module proxy and grants `packages: read` only because
the reusable declares it), `SECOPS_INGEST_API_KEY` (static-key fallback
for `secops.yaml`'s own reports). These were `gfs-bifrost` org secrets
pre-move — verify before assuming any are inherited as `ilg-platform` org
secrets.

## Observability {#observability}

**API logs do not reach Datadog.** `internal/observability/handler.go`
emits the fleet's Datadog log shape over `slog` to stdout, but there is no
sidecar and the prod project has no export sink — measured: zero events
over 30 days. They stop in **GCP Cloud Logging**; query the Datadog-shaped
fields there (`@source:go`, not bare `source:`). A dashboard or monitor
for this service has to be built on `gcp.run.*` metrics (Cloud Run
`revision_name` etc.), not on its logs. No metrics are emitted at all.

Useful log lines: `ingested job report` (`idempotencyKey`, `created`,
`scanner`, `repo`), `published vulnerability report event` / `failed to
publish vulnerability report event`, `skipped ensuring indexes because
mongodb is unreachable`, `failed to create the pubsub client —
vulnerability report events are disabled`.

## Real failure modes

- **A wrong HTTP status on ingest**: every caller (the `secops-*` reusable
  workflows) treats a 4xx as log-and-drop — a status-code regression here
  loses security reports with no visible error anywhere in the pipeline.
  Reproducing the exact RFC 7807 shape (not just the code) is load-bearing.
- **A scanner rename/addition landing out of lockstep**: if
  `api/internal/models/validate.go`, `github-actions`' `report-scan.mjs`,
  or a reusable workflow's own `scanner:` literal move independently
  rather than together, the ingest 4xxs the payload — logged, non-fatal,
  and the report is silently dropped. Check all three together before
  assuming a scanner change is safe (`govulncheck` reports 4xx'd until
  `f98b2af` landed — exactly this).
- **A subtly wrong Mongo aggregation change**: `api/internal/core/*.go`
  returns *plausible*, not obviously-wrong, numbers on a broken pipeline —
  a dashboard quietly under-reporting open criticals is a worse failure
  mode than a visible error. The port was proven by a live differential
  harness, not a code read; nothing equivalent now guards a change here.
- **A lost vulnerability-report event is invisible to the caller**: the
  publish failure is logged and swallowed by design; the only signal is
  the `failed to publish…` log line in Cloud Logging. A pubsub client that
  fails to construct at boot disables events entirely (logged) without
  failing the boot.
- **Dropping `VULNERABILITY_REPORT_TOPIC` crash-loops the API**: it is
  required config (fail-closed). It's wired from `secops-pubsub` remote
  state, so a broken/absent pubsub apply breaks the API apply, not just
  the event.
- **Azure DevOps OIDC verification failing outright** once
  `vstoken.dev.azure.com` reaches its 2027-07-01 EOL with no successor —
  a real, dated risk to revisit before then, independent of anything else
  in flight.

## Cross-checking

Chain a repo/org/scanner combination straight through
`GET /api/v1/job-reports`/`/findings` with the same filters the dashboard
uses (`org repo branch scanner severity outcome from to defaultBranch
runId`) to investigate a specific report without going through the UI.
`?idempotencyKey=<provider:runId:runAttempt:scanner>` fetches exactly one
report — it's what an event's `reportPath` resolves to.
