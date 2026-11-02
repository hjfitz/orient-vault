---
tags:
- waypoint
- snap-mcp
verified: '2026-10-01'
verified_sha: e078dbe
verified_paths:
- .github/workflows
- iac/projects/snap-mcp
title: snap-mcp — operations
---
# snap-mcp — operations

## Deploy

Cloud Run behind a global HTTPS load balancer, `iac/projects/snap-mcp`. **No
dev environment** — `iac/env/` has only `global.tfvars`/`prod.tfvars`, so a
push to the default branch deploys straight to production, same posture as
fuse-mcp. `deploy.yml` handles the push-triggered deploy; `manual-deploy.yaml`
covers on-demand deploys; `secops.yaml` and `tf-output.yaml` provide dependency
audit/Trivy scanning and a Terraform plan comment respectively.

## Observability

No dedicated Datadog dashboard found for this service specifically during this
onboarding pass (unlike fuse-mcp's `u54-iz6-ag5`) — check whether one exists
before assuming there's nothing to look at. `MCP_AUTH_TOKEN` failures surface
as 401s with a `WWW-Authenticate` header; a per-host circuit-open state
surfaces as a plain-text tool result (`SnapCircuitOpenError`), not an
exception — grep tool-call logs for that message rather than expecting a
thrown error.

## Real failure modes

- **A SNAP host trips its circuit breaker** (5 consecutive transient
  failures): further calls to that host return a text result explaining the
  circuit is open rather than hanging or retrying — check `@gfs-bifrost/snap`'s
  own `isTransientSnapError` predicate if a host seems to trip when it
  shouldn't (e.g. a 4xx from bad credentials must not count as transient).
- **A credential change for a host already cached in-process**: silently
  ignored — see [[known-context#credential-cache-real]]. If a tool call
  behaves as though it's using stale/wrong SNAP credentials, restart the
  process (a new Cloud Run revision) rather than assuming the credentials
  passed in are wrong.
- **A write rejected by SNAP**: surfaces as a text result with the real field
  errors (via `parseSnapErrorBody`), regardless of whether SNAP signalled the
  rejection as a 2xx-with-error-body or a genuine non-2xx — don't assume a
  bare "Request failed" message means the field-level detail wasn't
  available; check `writeRejectionError`'s handling before concluding SNAP
  gave no reason.
- **A read against an entity not yet live-verified**: may come back with
  `validated: false` and raw data — this is expected behaviour for those
  entities, not a bug, see [[known-context]].

## Cross-checking

This service is itself one half of the standard investigation pattern used
throughout Fuse: find a reference (ShipmentId, SalesOrder ref, SKU, queueId)
in a Datadog log, then look it up here by business id via
`get-snap-connection` (Fuse MCP) → the relevant `snap-get-*`/`snap-search-*`
tool.
