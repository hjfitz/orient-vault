---
tags:
- waypoint
- secops-reporting
verified: '2026-10-13'
verified_sha: 73f60ef
verified_paths:
- README.md
- CLAUDE.md
- api/CLAUDE.md
- iac/CLAUDE.md
- ui/CLAUDE.md
- api/internal/http
- api/internal/core/service.go
- api/internal/core/summary.go
- api/internal/core/worklist.go
- iac/projects/secops-api
- .github/workflows
- ui/lib/secops/api.ts
title: secops-reporting — overview
thesis: 'secops-reporting is the single ingest and read point for security-scan reports:
  a Go API stores each JobReport once, serves the dashboard, and publishes new reports
  to Pub/Sub. The Go rewrite is live and the Node service is gone; the OpenAPI document
  and three read-path defects remain open.'
confidence: high
---
# secops-reporting — overview

```orient-bluf
{ "v": 1, "bluf": "secops-reporting is the single ingest and read point for security-scan reports: a Go API stores each JobReport once, serves the dashboard, and publishes new reports to Pub/Sub. The Go rewrite is live and the Node service is gone; the OpenAPI document and three read-path defects remain open.", "confidence": "high", "action": "Never change a status code, an error body or a scanner name without the matching change in github-actions: callers drop any 4xx silently." }
```

## Responsibility

- **Ingest.** `POST /api/v1/job-reports` validates a JobReport against a seven-scanner union. It stores one document per `idempotencyKey` in MongoDB and answers 202 [1][2].
- **Read.** Eight guarded read endpoints back the dashboard: reports, findings, summary, tree, worklist, coverage, facets and pipeline runs [3].
- **Announce.** A report that creates a new document publishes a `VulnerabilityReportSummary` to Pub/Sub. A replay publishes nothing [4].
- **Dashboard.** `ui/` is a Next.js app behind one shared login. Its server reads the API with the ingest key [5].
- **Callers.** Harry confirmed on 2026-08-24 that every `secops-*` reusable workflow reports here. GitHub Actions and Azure DevOps OIDC are both live. This repo holds only the allowlists [6].

**State of the Go rewrite.** The programme note `Bifrost/SecOps API Go/Migration State` still reads `status: in-progress`. Its ledger shows every unit done except one.

- **Finished.** The API is Go only. Traffic reached 100% on 2026-08-26. The 2026-08-27 change removed `api/src` and the Node traffic target. At the ref there is no `api/src`, and `cloud-run.tf` holds one untagged 100% block [7][8].
- **Open: OpenAPI document.** The Node service served `/api/docs` and `/api/docs-json`. The Go router serves neither, and nobody has decided whether to keep it [8].
- **Open: three read defects, carried over on purpose.** `/summary` ignores `severity`. Worklist `fixable=false` equals unset. The five summary breakdowns have no tiebreak, so their order varies [9][10].
- **Open: `tools/diffcheck`.** The harness and an 8.7 MB binary stay in the tree. No Node baseline remains to run them against [11].

## Why it exists separately

Scan results need one home. Every `secops-*` reusable workflow can then POST a JobReport without knowing storage, dashboards or per-org auth.

The repo moved from `gfs-bifrost/secops` to `ilg-platform/secops-reporting` on 2026-07-27. It is a platform tool, not a Fuse service. The GCP project, Terraform state, Mongo cluster and domain did not change.

Harry and the CTO co-own it. No other `ilg-platform` repo has that ownership shape.

## Neighbours

```orient-flow
{ "v": 1, "title": "secops-reporting in context",
  "nodes": [
    { "id": "gh", "label": "secops-* reusables", "sub": "GitHub Actions OIDC", "kind": "service", "service": "github-actions", "ev": [6] },
    { "id": "ado", "label": "Azure DevOps pipelines", "sub": "OIDC, org GUID allowlist", "kind": "external", "ev": [6] },
    { "id": "api", "label": "secops-api", "sub": "Go ingest + read", "kind": "service", "service": "secops-reporting", "tone": "accent", "ev": [2] },
    { "id": "mongo", "label": "MongoDB Atlas", "sub": "job_reports", "kind": "store", "ev": [2] },
    { "id": "topic", "label": "secops-vulnerability-report", "sub": "no subscriber", "kind": "topic", "ev": [4] },
    { "id": "ui", "label": "secops-ui", "sub": "Next.js dashboard", "kind": "service", "service": "secops-reporting", "ev": [5] },
    { "id": "user", "label": "Dashboard users", "sub": "shared login", "kind": "external", "ev": [5] }
  ],
  "edges": [
    { "from": "gh", "to": "api", "label": "POST job-reports" },
    { "from": "ado", "to": "api", "label": "POST job-reports" },
    { "from": "api", "to": "mongo", "label": "upsert, aggregate" },
    { "from": "api", "to": "topic", "label": "new reports only" },
    { "from": "ui", "to": "api", "label": "GET, x-api-key" },
    { "from": "user", "to": "ui", "label": "session cookie" }
  ] }
```

Upstream, CI jobs push reports. Downstream, the UI pulls reads, and the topic has no consumer. The `secops-pubsub` Terraform project owns the topic. A draft plan for an issue-writer consumer exists, with no code at the ref [12].

## Where the reference lives

[[architecture]] holds the layers, endpoints, auth, query core and deploy order. `api/CLAUDE.md` carries the Go contract rules. [[operations]] covers deploy and logs.

Do not trust four sources:

- [[known-context]] predates the cutover. It calls the rewrite in progress, and `waypoint.yaml` still says TypeScript and NestJS.
- `ui/CLAUDE.md` points at `api/src/models`, which no longer exists.
- `README.md` and `CLAUDE.md` name a `secops-api-go` skill that is no longer installed.
- `CLAUDE.md` says commit straight to `main`, but recent changes landed as PRs.

Read source from `origin/main`. The checkout at `~/code/fuse/secops-reporting` sits at `5e6bd54`, 30 commits behind, with three uncommitted edits.

## What deliberately isn't here

- **Dev or staging.** Everything is `env = prod`, by design for a two-person tool.
- **Azure DevOps GUID-to-name resolution.** Its claims are opaque GUIDs, so the guard authenticates without restamping `source`. The resolver is a planned follow-up.
- **A consumer of the topic.** A subscription belongs to the consumer's own Terraform project.
- **Datadog logs or metrics.** API logs stop in Cloud Logging, and the service emits no metrics [13].
- **Per-user dashboard identity.** One env-defined user logs in; there are no accounts [5].
- **Deploy notifications.** `notify_on_*` is off because the repo has no Slack webhook secret [14].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "api/internal/models/validate.go@73f60ef" },
  { "id": 2, "kind": "code", "ref": "api/internal/core/service.go@73f60ef" },
  { "id": 3, "kind": "code", "ref": "api/internal/http/router.go@73f60ef" },
  { "id": 4, "kind": "code", "ref": "api/internal/core/vulnerability_report.go@73f60ef" },
  { "id": 5, "kind": "code", "ref": "ui/lib/secops/api.ts@73f60ef", "note": "UI reads with x-api-key; login in ui/app/api/auth/login/route.ts" },
  { "id": 6, "kind": "code", "ref": "iac/projects/secops-api/main.tf@73f60ef", "note": "OIDC org and GUID allowlists" },
  { "id": 7, "kind": "code", "ref": "iac/projects/secops-api/cloud-run.tf@73f60ef" },
  { "id": 8, "kind": "doc", "ref": "Bifrost/SecOps API Go/Migration State.md", "note": "unit H4 and the awaiting-a-decision section" },
  { "id": 9, "kind": "code", "ref": "api/internal/core/summary.go@73f60ef" },
  { "id": 10, "kind": "code", "ref": "api/internal/core/worklist.go@73f60ef" },
  { "id": 11, "kind": "code", "ref": "api/tools/diffcheck/main.go@73f60ef" },
  { "id": 12, "kind": "doc", "ref": "Engineering/secops-reporting/plans/vulnerability-report-issue-writer.md" },
  { "id": 13, "kind": "code", "ref": "api/internal/observability/handler.go@73f60ef" },
  { "id": 14, "kind": "code", "ref": ".github/workflows/on-push.yaml@73f60ef" }
] }
```
