---
tags:
- waypoint
- parcel-portal
title: parcel-portal — operations
verified: '2026-11-13'
verified_sha: 621357e
verified_paths:
- docs/runbook.md
- .github/workflows
- iac/projects/parcel-portal-svc/datadog.tf
- iac/projects/parcel-portal-sftp/datadog.tf
- iac/env
- .trivyignore.yaml
---
# parcel-portal — operations

`docs/runbook.md` in the repo is the full runbook, with some stale lines (see [[overview]]). This is the short path and what bites.

## Deploy
- Per app: `svc-on-push.yaml`, `ui-on-push.yaml`, `sftp-on-push.yaml` and `gateway-on-push.yaml` on a push to `main` touching that app's paths (sftp and gateway watch their own `cmd` and `internal` packages, not all of `apps/svc`). Dev applies straight away. svc and ui then run `dev-smoke.yaml`, report-only.
- **One `terraform-prod` approval releases the whole prod chain.** The gate sits on the first prod job, the image build; the prod plan and `apply -auto-approve` after it have no gate of their own. So the plan to share with Harry first is the one `tf-plan-pr.yaml` comments on a PR touching `iac/` (every app, dev and prod), not the in-run plan, which runs after the click.
- `supersede` cancels older runs of the same workflow parked at the gate, so a waiting run is the latest for its app.
- **Prod (snapshot 2026-11-13, from GitHub runs and deployments): no portal build has been applied.** The only run past the gate is svc's first, on 28 Oct (`8cdbe66`, still the unrenamed template with `system = "template"`); its prod apply changed `svc-template-prod`, 0 added and 1 changed. Every run since is cancelled or waiting at the gate: svc at `621357e`, ui at `8dabeb2`, sftp and gateway at `10e2963`. Prod is held at unit D1 and gate G7 (building outside Fuse, Oli Denton) in the Parcel Portal programme, which also says the svc and ui prod deploys go together. The prod SFTP host is off (`sftp_host_enabled = false`).
- `<app>-manual-deploy.yaml` deploys a branch to dev. Dev deploys announce failures only.
- svc publishes `openapi.yaml` after a prod deploy as the release `svc-openapi-v<info.version>`. `public-openapi.yaml` isn't released; the gateway serves it at `/openapi.json`.
- GCP grants for the deploy runner live in `ilg-merak/gcp-config`, not here.
- **Red today (snapshot 2026-11-13):**
  - `dev-smoke.yaml` has failed every nightly run since 5 Nov, its first: dev refuses the smoke account's sign-in. It is report-only, so no deploy is held.
  - Container scans pass only through `.trivyignore.yaml`: three entries for the platform runtime images' copies of `golang.org/x/net` and `zlib1g`, expiring 2026-11-16. The scans fail again then unless those images are rebuilt.

## Access
- Calling svc needs `roles/run.invoker` on `svc-parcel-<env>`; the repo grants it to the ui's, the gateway's and the push SA, and in dev to the named `debug_invokers` (prod ignores them). Humans call it with an ID token (`runbook.md`, *Calling svc*).
- `apps/svc/cmd/debug-mcp` is a local MCP for dev: dev hosts only, no manifest calls, no gate approval, secrets redacted.
- Bootstrap admin: `admin@parcel-portal.invalid`; password in the secret `svc-parcel-bootstrap-admin-password` in the env's project, never printed.
- SFTP: logins are the SFTP users a GFS admin sets under Settings → Customers → the customer → Access, each with its own keys. Nothing is in Terraform and there is no shared account. Terraform owns the host keys, the static IP and the canary's key (login `_canary`).

## Observability
- Datadog services `svc-parcel`, `gateway-parcel`, `sftp-parcel` and `ui-parcel`. Logs are slog JSON with a `correlationId` per request and an `actorId` on every signed-in line; the fixed messages are in `apps/svc/internal/observability/catalog.go`. Query the log's own `@env`, not the `env:` tag: the shared Cloud Run module tags every service `env:serverless`. Everything goes to the GFS Datadog org only.
- Terraform owns 15 monitors (10 in `iac/projects/parcel-portal-svc/datadog.tf`, 5 in `iac/projects/parcel-portal-sftp/datadog.tf`, the sftp ones only while the host serves), a tabbed dashboard `[Parcel <env>] Parcel Portal`, 13 log metrics `parcel.<env>.*` and the GCP integration. **They exist only where `datadog_monitors_enabled` is true, which is dev** (`iac/env/dev.tfvars`); prod doesn't set it (snapshot 2026-11-13).
- The SFTP canary job uploads every 5 minutes and logs `SFTP canary PASS`. It logs to Cloud Logging only; Datadog sees its runs as the metric `gcp.logging.user.parcel_sftp_canary_runs`.

## Failure modes
- **An import stuck or failing:** Pub/Sub retries 10 to 600 s, then `svc-parcel-inbound-files-dead-letter`. An upload under an unknown slug 422s until the tenant exists, then imports on retry.
- **A dispatch that may have booked:** the attempt is `outcome_unknown` and the order stays held; the next dispatch reconciles with `DailyShipQuery` and voids anything it can't adopt.
- **Selector down:** `503 carrier_unavailable`; the order and shipment are unchanged.
- **A shipment manifested behind the portal's back:** Selector auto-commits; *Refresh status* picks it up.
- **An SFTP login change that doesn't land:** svc republishes the users snapshot after every change and retries from 30 s to 5 min; a revoke or disable answers 503 if its own write fails. Until it lands, the host signs in against its last good copy. `"SFTP users not published"` in the svc logs, and its monitor, mean it is stale.
- **A carrier password that won't open** (another key, another tenant's row, altered): `422 carrier_not_configured`; enter the password again.
- **Rollback:** redeploy the previous image through the workflow (`runbook.md`, *Rolling back a deploy*). Migrations only move forward.
