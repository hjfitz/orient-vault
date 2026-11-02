---
tags:
- waypoint
- secops-reporting
verified: '2026-10-13'
verified_sha: 73f60ef
verified_paths:
- api/internal
- api/cmd
- api/tools
- api/Makefile
- api/dockerfile
- mise.toml
- ui
- iac
- .github/workflows
- README.md
- CLAUDE.md
- api/CLAUDE.md
- api/diffcheck
- api/go.mod
title: secops-reporting — architecture
thesis: A layered Go API on scale-to-zero Cloud Run upserts each JobReport into one
  MongoDB collection behind three credentials, serves aggregation-backed reads to
  a Next.js dashboard, and publishes one Pub/Sub event per new report.
confidence: high
---
# secops-reporting — architecture

```orient-bluf
{ "v": 1, "bluf": "A layered Go API on scale-to-zero Cloud Run upserts each JobReport into one MongoDB collection behind three credentials, serves aggregation-backed reads to a Next.js dashboard, and publishes one Pub/Sub event per new report.", "confidence": "high", "action": "Never change a status code, an error body or a scanner name on its own: callers drop any 4xx silently, and the scanner list moves in lockstep with github-actions and the UI types." }
```

## Guardrails

- [contract:G1] The JobReport shape and the scanner list move together: the validator, `ui/lib/secops/types.ts` and github-actions' reporting. A mismatch makes ingest 4xx, and callers drop the report with no visible error. No dev environment exists to rehearse it.
  — paths: api/internal/models/job_report.go, api/internal/models/validate.go, ui/lib/secops/types.ts
- [contract:G2] Status codes and RFC 7807 bodies are contract, because callers treat any 4xx as log-and-drop. Ingest answers on durable storage first. A failed event publish is logged and swallowed, never surfaced.
  — paths: api/internal/httperr/problem.go, api/internal/http/respond.go, api/internal/core/service.go
- [technical:G3] Layering is test-enforced and the route surface is pinned to a golden. Do not weaken `layering_test.go` or `surface_test.go` to pass a change.
  — paths: api/internal/layering_test.go, api/internal/http/surface_test.go, api/internal/http/testdata/request-surface.json
- [technical:G4] Provenance is asymmetric on purpose. GitHub OIDC overrides the body's `source.org` and `source.repo` with the signed claims. Azure DevOps OIDC and the static key never do.
  — paths: api/internal/core/service.go, api/internal/http/auth.go, api/internal/http/oidc.go
- [technical:G5] Dedupe is the unique `idempotencyKey` index plus one `FindOneAndUpdate` returning the document before the write. Do not replace it with read-then-write. The index is ensured before serving whenever Mongo is reachable.
  — paths: api/internal/repositories/collection.go, api/internal/bootstrap/bootstrap.go
- [technical:G6] A Mongo document whose key order carries meaning is a `bson.D`, never a `bson.M`. A map reorders a sort between requests, and a wrong pipeline returns plausible numbers, not an error.
  — paths: api/internal/core

## Layout

```
api/   Go 1.25 ingest + query API — cmd/secops-api/ → internal/http/ (chi router,
       auth guard, oidc, handlers; sibling httperr/ = RFC 7807) → core/ (Service +
       one file per read) → repositories/ (Mongo Collection[T] port) →
       models/ (JobReport + hand-written validator, event summary) →
       config/ (validated env); adapters/pubsub/ (one-topic publisher);
       observability/ (slog handler); bootstrap/ (the only wiring);
       tools/diffcheck/ (the TS-vs-Go differential harness)
ui/    Next.js 15 App Router dashboard, @ilg-platform/ui-toolkit, jose session cookies
iac/   Terraform/Terragrunt — three prod-only projects: secops-pubsub (topic
       only, no compute) → secops-api → secops-ui
```

Both apps deploy to Cloud Run in `bifrost-prod-global1`, `europe-west2`. The layers wire as follows [1][2].

```orient-flow
{ "v": 1, "title": "API layers and ports",
  "nodes": [
    { "id": "boot", "label": "bootstrap", "sub": "only wiring", "kind": "step", "ev": [1] },
    { "id": "http", "label": "http", "sub": "router, guard, handlers", "kind": "step", "ev": [2] },
    { "id": "core", "label": "core", "sub": "Service, pipelines", "kind": "step", "tone": "accent", "ev": [3] },
    { "id": "repo", "label": "repositories", "sub": "Collection port", "kind": "step", "ev": [4] },
    { "id": "mongo", "label": "MongoDB", "sub": "job_reports", "kind": "store", "ev": [4] },
    { "id": "pub", "label": "adapters/pubsub", "sub": "Publisher port", "kind": "step", "ev": [5] },
    { "id": "topic", "label": "secops-vulnerability-report", "kind": "topic", "ev": [32] }
  ],
  "edges": [
    { "from": "boot", "to": "http", "label": "builds", "style": "dashed" },
    { "from": "http", "to": "core", "label": "one call per handler" },
    { "from": "core", "to": "repo", "label": "port it declares" },
    { "from": "repo", "to": "mongo" },
    { "from": "core", "to": "pub", "label": "port it declares" },
    { "from": "pub", "to": "topic" }
  ] }
```

Apply order is pubsub, then API, then UI. `secops-api/remote.tf` reads the topic from `prod/secops-pubsub` state. `secops-ui/remote.tf` reads the API URL and key from `prod/secops-api`, and the DNS zone name from ilg-platform's core-infra state (`ilg-platform-tfstate`). The UI's A record lives in the ilg-platform zone (`dns.tf`) [32][33]. `on-push.yaml` encodes the ordering [43].

`api/internal/layering_test.go` pins these rules [6]:

- Nothing in `core`, `repositories`, `models`, `config`, `observability`, `shared` or `adapters` imports `http`.
- Nothing in those layers or `http` imports `bootstrap`.
- `core` never imports the Mongo client, the repository package or the pubsub adapter. It declares the ports itself and may import `bson`.

`api/internal/http/surface_test.go` pins the exact route set and each route's query parameters against `testdata/request-surface.json` [7].

`api/diffcheck` is a committed 8.7 MB ELF binary, added in `49420e7` with `tools/diffcheck`. `api/.gitignore` ignores `bin/` and `secops-api`, not this file. The dockerfile copies only `cmd` and `internal`, so the binary never ships in the image [8][9]. **UNKNOWN** Whether committing it was intentional.

## The HTTP surface — 11 endpoints, base `/api/v1`

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/job-reports` | `202` `{created}`; dedupe-upsert on `idempotencyKey`; a *new* report also publishes the event |
| GET | `/job-reports` | paged `{total, offset, count, data}` |
| GET | `/findings` | reports flattened to one row per finding; per-row open/resolved computed before the unwind |
| GET | `/summary` | bySeverity/byScanner/byRepo/byOutcome/byFixable + trend + posture |
| GET | `/tree` | org → repo rollup |
| GET | `/worklist` | top-N prioritised findings (array, not paged) |
| GET | `/coverage` | per-repo scanner coverage + staleness |
| GET | `/facets` | distinct orgs/repos/branches — populates filter-bar dropdowns |
| GET | `/pipeline-runs` | job reports grouped by CI run (`ci.provider`+`runId`+`runAttempt`); backs the Reports view |
| GET | `/health/liveness`, `/health/readiness` | **open**, outside the `/api` prefix |

No OpenAPI document is served. The Node service served `/api/docs` and `/api/docs-json`; the Go router registers neither [2].

Shared filters (`internal/core/query.go`'s `buildQuery`): `org repo branch scanner severity outcome from to defaultBranch runId idempotencyKey`, plus `offset`/`count` where paged [10]. Binding rules sit in `internal/http/query.go` [11]:

- `scanner`, `severity`, `outcome` and `status` accept only their enum values. An unknown query parameter is ignored.
- `count` runs 1–100 and defaults to 20. `offset` is at least 0, and `?offset=` empty is accepted where `?count=` empty is rejected.
- `from` and `to` must be UTC ISO-8601 ending in `Z`.
- `defaultBranch` and `fixable` accept only the literal strings `"true"` and `"false"`.

`defaultBranch=true` scopes to `branch ∈ {main, master}` unless an explicit `branch` is set. That is the dashboard and services "shipped posture" view. Reports and Findings default to all branches for investigation. `idempotencyKey` is an exact match that exists only because the outbound event's `reportPath` needs it.

The guard is attached **per route**, not as subrouter middleware, so routing happens first. An unknown path under `/api/v1` answers 404, not 401, and a wrong method is also a 404 [2][12].

## The JobReport schema is the contract — a real three-way lockstep

`api/internal/models/job_report.go` and `validate.go` hold a hand-written **discriminated union on `scanner`** [13][14]. It has **seven** variants: `semgrep`, `trivy-image`, `gitleaks`, `audit-ci`, `trivy-iac`, `nuget-audit`, `govulncheck`. Each has its own validator function and finding shape, inside an envelope of `ci`, `source` and `scan.summary`. Validation enforces `findings[].scanner == scan.scanner`.

`govulncheck` is package-shaped (`package` + `advisoryUrl`, no `location`). It branches wherever `trivy-image`, `audit-ci` and `nuget-audit` already do: `validate.go`, `core/query.go`'s fixable expression and `core/coverage.go`'s dependency rollup [10][15]. `dotnet-vulnerable` was never a scanner. It entered the port as a hallucination that the diffcheck gate caught. Do not reintroduce it.

Decoding rules [12]:

- The body limit is 10 MB.
- Unknown fields are dropped, not rejected.
- An explicit `null` anywhere is rejected, because no field is nullable.
- `findings` is required but may be empty, because an error scan reports none.
- `idempotencyKey` must be non-empty. Nothing else constrains its format.

Renaming or adding a scanner is a **three-way lockstep**: this validator, github-actions' `report-scan.mjs` (`VALID_SCANNERS` and the parse dispatch), and every reusable workflow's own `scanner: <literal>` in its `report:` job. If one lags, the ingest 4xxs the payload, which is logged, non-fatal and silently dropped. **ASSESSED** The two github-actions halves live outside this repo; the repo's `api/CLAUDE.md` and code comments are the source. `trivy`→`trivy-image` and `tfsec`→`trivy-iac` were renamed and `nuget-audit` added together in the 0.2 release. A one-off backfill script migrated the Mongo history and was deleted with the Node toolchain. With no dev or staging, a scanner change lands live.

`ui/lib/secops/types.ts` mirrors the Go types by hand. Keep the two in sync manually.

## Auth — three credentials, one guard, deliberately asymmetric {#auth}

`internal/http/auth.go` holds the guard. The verifiers sit in `oidc.go` on `MicahParks/keyfunc/v3`, with the JWKS fetched lazily on first use [3][16]. The guard accepts any of:

1. **`x-api-key`** header, compared with `subtle.ConstantTimeCompare`. This is the original static path and what the UI server uses.
2. **GitHub Actions OIDC.** JWKS from `token.actions.githubusercontent.com`. It verifies issuer, the configured audience (`secops-ingest`) and expiry, then checks an org allowlist. It **sets the verified source**, and `core/service.go`'s `Ingest` *overrides* the body's `source.org` and `source.repo` with the claims, so a caller cannot lie about which repo it is.
3. **Azure DevOps OIDC.** JWKS from `vstoken.dev.azure.com`, audience fixed at `api://AzureADTokenExchange`, and the issuer pinned per allowed org GUID. Allowlisting and issuer verification are one check, because the GUID sits in the issuer URL. It **does not set the verified source**. Its claims are opaque GUIDs (`org_id`, `prj_id`, `rpo_id`), and stamping them would replace readable dashboard data. GUID-to-name resolution is a planned follow-up.

```orient-flow
{ "v": 1, "title": "How the guard decides",
  "nodes": [
    { "id": "req", "label": "Guarded request", "kind": "step", "ev": [3] },
    { "id": "key", "label": "x-api-key matches", "kind": "step", "ev": [3] },
    { "id": "gh", "label": "GitHub OIDC verifies", "sub": "audience + org allowlist", "kind": "step", "ev": [16] },
    { "id": "ado", "label": "Azure DevOps OIDC verifies", "sub": "issuer = allowed org GUID", "kind": "step", "ev": [16] },
    { "id": "okc", "label": "Handler, source from claims", "kind": "step", "tone": "accent", "ev": [3, 5] },
    { "id": "okb", "label": "Handler, source from body", "kind": "step", "ev": [3, 5] },
    { "id": "no", "label": "401 problem body", "kind": "step", "tone": "alert", "ev": [3] }
  ],
  "edges": [
    { "from": "req", "to": "key" },
    { "from": "key", "to": "okb", "label": "yes" },
    { "from": "key", "to": "gh", "label": "no, Bearer token" },
    { "from": "gh", "to": "okc", "label": "yes" },
    { "from": "gh", "to": "ado", "label": "no" },
    { "from": "ado", "to": "okb", "label": "yes" },
    { "from": "ado", "to": "no", "label": "no" }
  ] }
```

A Bearer token only ever matches one provider. The guard tries GitHub first when configured, then falls through to Azure DevOps. Each path is enabled only when its config is non-empty. `config.GitHubOIDC.Enabled()` needs the audience **and** an allowlist. Azure needs the allowlist.

The allowlists are the `allowed_oidc_orgs` and `allowed_azure_devops_oidc_org_ids` locals in `iac/projects/secops-api/main.tf`. That is 16 GitHub orgs and one Azure DevOps org GUID, `globalfreightsolutions` [17]. 
**ASSESSED** Any repo in an allowlisted org can mint a token that passes the GitHub path. The upsert filter is `idempotencyKey` alone and `$set` writes the whole body [5][18]. An authenticated caller that reuses another report's key overwrites that report, and under OIDC it restamps the source as its own repo. Nothing in the repo binds a key to a repo.

**ASSESSED** The UI server holds the same key that ingests [31], so its compromise grants write access. Nothing in the repo issues a read-only credential.

⚠️ `vstoken.dev.azure.com` is deprecated as of 2026-07-01, with end of life on 2027-07-01 and no documented successor issuer for this token type. It is ported as-is.

## Error contract — RFC 7807, and callers drop a wrong status silently

`internal/httperr/problem.go` renders every failure as Problem Details (`application/problem+json`). The field order matches what the TypeScript service emitted, and `instance` is the full request URI **including the query string** [19]. The package comment states that callers treat any 4xx as **log-and-drop**, so a wrong status code loses a security report with no visible error anywhere. **ASSESSED** The callers are the github-actions reusables, outside this repo.

- A rejected report or query answers 400 with the fixed detail `"Validation failed"`. The reason goes to the log only.
- A duplicate-key conflict answers 409. Any other failure answers 500 with fixed text.
- A non-JSON body gets the generic detail, not V8's parser text. This is one deliberate, tested divergence from the Node service.
- Responses disable HTML escaping, so `<`, `>` and `&` in a rule id stay literal [12][20].

## The query core — where the real risk lives

`internal/core/` is about 1,200 non-test lines. `query.go` holds the shared helpers: `buildQuery`, the snapshot, freshness and fixable expressions, and the paging defaults. Each read has its own file: `reports.go`, `summary.go`, `tree.go`, `worklist.go`, `coverage.go`, `facets.go`, `pipeline_runs.go` [10]. They use `$facet`, `$unwind`, `$expr` and latest-per-lane ranking. **A wrong pipeline here returns plausible numbers, not an error.**

- **Current posture** keeps the latest report per lane (org, repo, branch, scanner) that is under five days old. The window is wide on purpose, so a repo whose cron skipped a day does not read as all-clear. `defaultBranches` is `main` and `master`. Do not tighten either casually [10].
- **Ties.** `$rank` takes one sort field. Two reports in one lane within the same millisecond both rank 1 and double-count for a cycle.
- **Full history, not snapshot.** `/findings` browses every report and computes `open` or `resolved` per row before the unwind. The summary `trend` is daily ingest volume, not an open-issue count [45][21].
- **Known defects, reproduced from the Node service and still present at the ref.** `/summary` ignores `severity`. Worklist `fixable=false` behaves as unset, while `/findings` negates the expression. The five summary breakdowns have no tiebreak among equal counts, so their order varies between identical requests [21][22]. Each needs its own change, where the numbers moving is the point.
- **Worklist order.** Secrets rank above everything, then severity, fixability and recency. The sort keys are a `bson.D` for that reason.

The port was proven by `tools/diffcheck`, which diffed both services live over the same database. The harness and its `make diffcheck` target still exist. The Makefile target needs `BASE_TS`, `BASE_GO` and `SECOPS_API_KEY` [23][24]. No Node baseline remains, so it now serves only as a regression comparison between two Go revisions. **UNKNOWN** Whether anyone intends to use it that way.

## Mongo — native driver, no ODM

`internal/repositories/connection.go` connects at startup with a 5s bound [4][25]. A failed connection is **recorded, not fatal**: the process comes up and readiness answers 503. The status is set once during `Connect` and nothing re-probes it. **An outage that starts after boot leaves readiness at `UP`, and a boot against an unreachable cluster leaves it at 503 until the instance restarts.** **ASSESSED** Nothing in the repo calls readiness: `cloud-run.tf` configures only a startup probe on liveness [29].

`collection.go` is the generic `Collection[T]` port over the one collection, `job_reports`. The document shape is flat: `JobReport` plus `receivedAt`. Dedupe is a unique index on `idempotencyKey` plus `FindOneAndUpdate(..., upsert, ReturnDocument(Before))`. A missing `Before` document means the report is new. `$set` writes the body on every call and `$setOnInsert` writes `receivedAt` only once, so a replay rewrites the stored body and keeps its receive time. Driver code `11000` maps to `ErrConflict`, which is a concurrent first write of the same key [18][5].

The four indexes are listed in `bootstrap.go` and **awaited before serving**: the unique `idempotencyKey`, `scan.scanner`, `receivedAt` descending, and the lane index on org, repo, branch, scanner and `receivedAt`. They are skipped when the connection is down. The driver ignores the context deadline on index creation and would blow Cloud Run's startup grace. A failure logs rather than kills, a deliberate divergence from the Node service [1].

## Outbound event — one topic, publisher only

`core/service.go`'s `Ingest` publishes a `models.VulnerabilityReportSummary` (`core/vulnerability_report.go`) **only when the upsert created a new document** [5][26]. A replay publishes nothing. The publisher is `internal/adapters/pubsub.Client`, a thin wrapper over `cloud.google.com/go/pubsub/v2` bound to one topic [27]. The topic is `secops-vulnerability-report-prod`, owned by `iac/projects/secops-pubsub`. `secops-api` grants its own service account `roles/pubsub.publisher` in `pubsub.tf` [32][35].

The summary is not the full report:

- `ci`, `source` and `scan` pass through verbatim. The summary carries counts, never `findings`.
- `alertWorthy` is true for any critical or high count, the dashboard's own posture bar.
- `topFindings` previews up to five critical, then high, with `location` or `package` collapsed into one `locator` string.
- `reportPath` is relative, `/api/v1/job-reports?idempotencyKey=…`.
- Message attributes are `scanner` and `alertWorthy`. `eventSchemaVersion` is `1.0` and versions independently of `schemaVersion` [26][28].

Publish runs **synchronously** in the request path. The service scales to zero, and Cloud Run can freeze CPU after the response, so a goroutine is unsafe. A failure is **logged and swallowed**: storage already succeeded, and a non-2xx would make a stored report look dropped to log-and-drop callers. A pubsub client that fails to build does not stop boot. Events are disabled and logged, and ingest continues [1].

No subscription exists in this repo. A subscription is the consumer's own project's concern. A draft plan for an issue-writer consumer is in the vault, with no code at the ref.

## Config — `internal/config/config.go` owns every `os.Getenv`

Required, boot fails if absent: `INGEST_API_KEY`, `MONGODB_CONNECTION_STRING`, `MONGODB_NAME` and `VULNERABILITY_REPORT_TOPIC`. The topic is required on purpose, so it matches the fail-closed posture for Mongo. Optional, empty means that path is off: `GITHUB_OIDC_AUDIENCE`, `GITHUB_OIDC_ALLOWED_ORGS` and `AZURE_DEVOPS_OIDC_ALLOWED_ORG_IDS`. `NODE_ENV` is still read and wins over `ENVIRONMENT`, matched by prefix. That is a deliberate port, not a leftover. `cloud-run.tf` sets all of them [29][30].

## Runtime

The API runs on Cloud Run with 0–3 instances, a static distroless image running as non-root, and a startup probe on `/health/liveness` [29][8]. HTTP timeouts are 60s read, 60s write, 10s header and 120s idle. Shutdown allows 8s, under Cloud Run's 10s [1]. Both services accept public traffic (`allUsers` invoker), and the app enforces auth [46][47]. The UI runs at 0–3 instances with 512Mi and one CPU, behind a global HTTPS load balancer with a managed certificate at `secops.platform.ilg.software` [31][34].

The API has no Datadog sidecar and no log sink. Logs are `slog` JSON on stdout and stop in Cloud Logging, so monitoring uses `gcp.run.*` metrics [36]. The service emits no metrics.

## UI auth

`ui/middleware.ts` gates every route except `/login` and `/api/auth/login` on a `session` cookie (HS256, 30 days, `SESSION_SECRET`) [37]. The login route compares the posted email and password with `===` against `BASIC_AUTH_USER` and `BASIC_AUTH_PASSWORD`, and always issues the `admin` role [38]. **ASSESSED** The route has no rate limit or constant-time compare in the repo, and the Cloud Run service is public. The 32-character generated password limits the exposure. Reads go through a shared `unstable_cache` of 180 seconds keyed on the URL, so one user's read serves every user [39]. The Reports modal reads through the session-gated `app/api/report-findings` route, so the key never reaches the browser [48].

## Build / test / deploy

- API: Go **1.25.14 pinned exactly** (`mise.toml`, `api/dockerfile`), because govulncheck gates on the stdlib the binary was built against [8][40]. The gates are `make fmt-check`, `go build`, `go vet`, `go test` and `go test -race`. `make lint` runs golangci-lint v2 after `config verify`, since an unknown key is otherwise silently ignored. govulncheck follows. `api/Makefile` is the entry point.
- UI: pnpm 9.15.4, Node 22, Biome 1.9.4. `pnpm run build:check` runs `next build`, which ignores type and lint errors by config [49]. The UI has no tests (`"test"` echoes) [41].
- **PRs are in use in practice.** Recent changes (renovate, CVE fixes, the DNS move) landed as PRs, with `tf-output.yaml` planning on them. The repo's `CLAUDE.md` still says commit straight to `main`. Any push to `main`, docs-only included, triggers `on-push` and a full deploy [43].
- **Deploy gating.** `on-push.yaml` declares the `terraform-prod` environment on the pubsub apply and on both image pushes. The API and UI applies wait on those jobs [43]. **ASSESSED** The reusable workflows in github-actions honour that input. Approval rules live in GitHub settings, and the repo's `CLAUDE.md` names the `platform-admins` team.
- UI dependency audit: `ui/audit-ci.jsonc` has an empty allowlist [50]. `ui/package.json` `pnpm.overrides` floors `picomatch`, `sharp`, `postcss` and `nanoid` [41]. `ui/.trivyignore` lists four postcss and nanoid CVEs, and each entry carries `exp:2026-08-26` [42]. **ASSESSED** Trivy skips an entry past its `exp:` date, so these ignores are dead, and the overrides now floor the same packages. `ui/dockerfile` upgrades `libcrypto3` and `libssl3` in the runner stage and strips npm.
- Workflows: `on-push.yaml`, `manual-deploy.yaml` (pick `api` or `ui`, deploys any branch to prod), `code-quality.yaml` (UI only, `node-run` reusable), `go-code-quality.yaml` (API, hand-rolled because no `go-run` reusable exists [51]), `tf-output.yaml` (plans all three projects on PR) and `secops.yaml`. The last runs seven jobs over five `secops-*@0.2-bonbon` reusables against this repo. `secops-dep-node` covers the UI only, since the API has no npm tree [43][44].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  {"id": 1, "kind": "code", "ref": "api/internal/bootstrap/bootstrap.go@73f60ef"},
  {"id": 2, "kind": "code", "ref": "api/internal/http/router.go@73f60ef"},
  {"id": 3, "kind": "code", "ref": "api/internal/http/auth.go@73f60ef"},
  {"id": 4, "kind": "code", "ref": "api/internal/repositories/connection.go@73f60ef"},
  {"id": 5, "kind": "code", "ref": "api/internal/core/service.go@73f60ef"},
  {"id": 6, "kind": "code", "ref": "api/internal/layering_test.go@73f60ef"},
  {"id": 7, "kind": "code", "ref": "api/internal/http/surface_test.go@73f60ef"},
  {"id": 8, "kind": "code", "ref": "api/dockerfile@73f60ef"},
  {"id": 9, "kind": "code", "ref": "api/.gitignore@73f60ef"},
  {"id": 10, "kind": "code", "ref": "api/internal/core/query.go@73f60ef"},
  {"id": 11, "kind": "code", "ref": "api/internal/http/query.go@73f60ef"},
  {"id": 12, "kind": "code", "ref": "api/internal/http/handlers.go@73f60ef", "note": "notFound, decodeReport"},
  {"id": 13, "kind": "code", "ref": "api/internal/models/job_report.go@73f60ef"},
  {"id": 14, "kind": "code", "ref": "api/internal/models/validate.go@73f60ef"},
  {"id": 15, "kind": "code", "ref": "api/internal/core/coverage.go@73f60ef"},
  {"id": 16, "kind": "code", "ref": "api/internal/http/oidc.go@73f60ef"},
  {"id": 17, "kind": "code", "ref": "iac/projects/secops-api/main.tf@73f60ef"},
  {"id": 18, "kind": "code", "ref": "api/internal/repositories/collection.go@73f60ef"},
  {"id": 19, "kind": "code", "ref": "api/internal/httperr/problem.go@73f60ef"},
  {"id": 20, "kind": "code", "ref": "api/internal/http/respond.go@73f60ef"},
  {"id": 21, "kind": "code", "ref": "api/internal/core/summary.go@73f60ef"},
  {"id": 22, "kind": "code", "ref": "api/internal/core/worklist.go@73f60ef"},
  {"id": 23, "kind": "code", "ref": "api/tools/diffcheck/main.go@73f60ef"},
  {"id": 24, "kind": "code", "ref": "api/Makefile@73f60ef"},
  {"id": 25, "kind": "code", "ref": "api/internal/http/health.go@73f60ef"},
  {"id": 26, "kind": "code", "ref": "api/internal/core/vulnerability_report.go@73f60ef"},
  {"id": 27, "kind": "code", "ref": "api/internal/adapters/pubsub/pubsub.go@73f60ef"},
  {"id": 28, "kind": "code", "ref": "api/internal/models/vulnerability_report_summary.go@73f60ef"},
  {"id": 29, "kind": "code", "ref": "iac/projects/secops-api/cloud-run.tf@73f60ef"},
  {"id": 30, "kind": "code", "ref": "api/internal/config/config.go@73f60ef"},
  {"id": 31, "kind": "code", "ref": "iac/projects/secops-ui/cloud-run.tf@73f60ef"},
  {"id": 32, "kind": "code", "ref": "iac/projects/secops-pubsub/pubsub.tf@73f60ef"},
  {"id": 33, "kind": "code", "ref": "iac/projects/secops-ui/remote.tf@73f60ef"},
  {"id": 34, "kind": "code", "ref": "iac/projects/secops-ui/load-balancing.tf@73f60ef"},
  {"id": 35, "kind": "code", "ref": "iac/projects/secops-api/pubsub.tf@73f60ef"},
  {"id": 36, "kind": "code", "ref": "api/internal/observability/handler.go@73f60ef"},
  {"id": 37, "kind": "code", "ref": "ui/middleware.ts@73f60ef"},
  {"id": 38, "kind": "code", "ref": "ui/app/api/auth/login/route.ts@73f60ef"},
  {"id": 39, "kind": "code", "ref": "ui/lib/secops/api.ts@73f60ef"},
  {"id": 40, "kind": "code", "ref": "mise.toml@73f60ef"},
  {"id": 41, "kind": "code", "ref": "ui/package.json@73f60ef"},
  {"id": 42, "kind": "code", "ref": "ui/.trivyignore@73f60ef"},
  {"id": 43, "kind": "code", "ref": ".github/workflows/on-push.yaml@73f60ef"},
  {"id": 44, "kind": "code", "ref": ".github/workflows/secops.yaml@73f60ef"},
  {"id": 45, "kind": "code", "ref": "api/internal/core/reports.go@73f60ef"},
  {"id": 46, "kind": "code", "ref": "iac/projects/secops-api/iam.tf@73f60ef"},
  {"id": 47, "kind": "code", "ref": "iac/projects/secops-ui/iam.tf@73f60ef"},
  {"id": 48, "kind": "code", "ref": "ui/app/api/report-findings/route.ts@73f60ef"},
  {"id": 49, "kind": "code", "ref": "ui/next.config.mjs@73f60ef"},
  {"id": 50, "kind": "code", "ref": "ui/audit-ci.jsonc@73f60ef"},
  {"id": 51, "kind": "code", "ref": ".github/workflows/go-code-quality.yaml@73f60ef"}
] }
```
