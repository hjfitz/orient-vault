---
tags:
- waypoint
- audit-service
title: audit-service — operations
verified_paths:
- iac/projects/audit-service
- .github/workflows
- code/internal/http/controllers/ingest.go
verified: '2026-10-12'
verified_sha: ddefd56
---
# audit-service — operations

**URLs.** dev `https://audit-service-dev-j677gxplja-nw.a.run.app`, prod
`https://audit-service-prod-6cprbzyuka-nw.a.run.app`. Private: call with a Google ID token
whose audience is the URL.

**Deploy.** Merge to `main` → Deploy workflow applies dev, plans prod, applies prod behind the
`terraform-prod` environment. `gh workflow run manual-deploy.yaml --ref <branch>` deploys a
branch to dev.

**Metric.** `fuse.audit.ingest{system,outcome,kind,environment}`; `outcome` is one of `stored`,
`duplicate`, `invalid`, `system_mismatch`, `store_failed`.

**Monitors** (gfs-bifrost/observability, `monitors.audit-service.tf`):
- *Audit messages rejected (lost)*: `invalid` or `system_mismatch` in prod. Those messages are
  acked and gone, so this is the only signal. A dev copy notifies nobody.
- *Audit message dead-lettered*: store failures exhausted 5 attempts. The message is on the
  hold subscription `audit-service.<env>.<system>.v1.dlt.sub` for 7 days: fix Atlas, then
  re-publish from there to `audit.<env>.<system>.v1`.
- *5xx rate high*: store failures or broken reads.

**Failure modes.**
- Atlas unavailable → ingest returns 500 → Pub/Sub retries with backoff, then dead-letters.
  Reads 500. Producers are unaffected (their publisher never blocks).
- A producer emits the wrong `system`, or a malformed envelope → acked, counted, not stored.
- A new reader gets 403 "caller not allowed" until its SA is in `api_readers` (tfvars), which
  sets both Cloud Run invoker and `READ_CALLERS`.

**Legacy import.** README runbook: dry run, run, `-verify`. Prints counts only. Run once at
cutover; idempotent, so a rerun is safe.
