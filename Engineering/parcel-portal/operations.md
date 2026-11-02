---
tags:
- waypoint
- parcel-portal
title: parcel-portal — operations
verified: '2026-10-29'
verified_sha: 696cbd4
verified_paths:
- docs/runbook.md
- .github/workflows
- iac/projects/svc/datadog.tf
- iac/projects/sftp/datadog.tf
---
# parcel-portal — operations

`docs/runbook.md` in the repo is the full runbook. This is the short path and what bites.

## Deploy
- Per app: `svc-on-push.yaml`, `ui-on-push.yaml`, `sftp-on-push.yaml` on a push to `main` touching that app. Dev applies straight away; prod waits at the `terraform-prod` environment, and the plan is shared with Harry before the gate is approved.
- `<app>-manual-deploy.yaml` deploys a branch to dev. Dev deploys announce failures only.
- svc publishes its contract after a prod deploy as the release `svc-openapi-v<info.version>`.
- GCP grants for the deploy runner live in `ilg-merak/gcp-config`, not here.

## Access
- Calling svc needs `roles/run.invoker` on `svc-parcel-<env>`; the repo grants it only to the ui's SA and the push SA. Humans call it with an ID token (`runbook.md`, *Calling svc*).
- Bootstrap admin: `admin@parcel-portal.invalid`; password in the secret `svc-parcel-bootstrap-admin-password` in the env's project, never printed.
- SFTP: user `tca` at the static IP; the authorised keys are `authorized_keys` in `iac/env/<env>.tfvars`. The canary's key is added on top by Terraform.

## Observability
- Datadog services `svc-parcel`, `ui-parcel`, `sftp-parcel` and `sftp-parcel-canary`. Logs are slog JSON with a `correlationId` per request; the fixed messages are in `apps/svc/internal/observability/catalog.go`.
- **10 monitors are Terraform (`iac/projects/svc/datadog.tf`, `iac/projects/sftp/datadog.tf`) and off** until a `DATADOG_APP_KEY` secret exists and `datadog_monitors_enabled = true` (snapshot 2026-10-29).
- The SFTP canary job uploads every 5 minutes and logs `SFTP canary PASS`.

## Failure modes
- **An import stuck or failing:** Pub/Sub retries 10 to 600 s, then `svc-parcel-inbound-files-dead-letter`. An upload under an unknown slug 422s until the tenant exists, then imports on retry.
- **A dispatch that may have booked:** the attempt is `outcome_unknown` and the order stays held; the next dispatch reconciles with `DailyShipQuery` and voids anything it can't adopt.
- **Selector down:** `503 carrier_unavailable`; the order and shipment are unchanged.
- **A shipment manifested behind the portal's back:** Selector auto-commits; *Refresh status* picks it up.
- **Rollback:** redeploy the previous image through the workflow (`runbook.md`, *Rolling back a deploy*). Migrations only move forward.
