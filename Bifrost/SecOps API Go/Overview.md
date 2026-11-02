---
title: SecOps Ingest API — Go Rewrite Overview
status: planning
owner: Harry Fitzgerald
created: '2026-08-24'
tags: [ilg-platform, secops, golang, migration]
---

# SecOps Ingest API — Go Rewrite

> **Rationale, target design, and the constraints that shape it.** Live progress lives in
> [[Bifrost/SecOps API Go/Migration State|Migration State]].

Third Go port after [[project_fuse_mocker_go_api|fuse-mocker]] and [[project_fuse_mcp_go_rewrite|fuse-mcp]],
following the same process and the conventions now written up in Confluence:
[Go Codebase Structure](https://globalfreight.atlassian.net/wiki/spaces/Bifrost/pages/280428847) ·
[Go Preferred Libraries](https://globalfreight.atlassian.net/wiki/spaces/Bifrost/pages/280494357).

## What it is

`ilg-platform/secops-reporting`'s `api/` — a NestJS ingest service. Security scanners in the
platform's `secops-*` reusable workflows POST **JobReports**; the service validates them against a
Zod discriminated union, dedupes into MongoDB by `idempotencyKey`, and serves eight read endpoints
that back the dashboard.

**Measured baseline** (`origin/main` @ `5e6bd54`): **2,792 production lines**, 1,501 test lines,
42 source files. Already laid out in the org layer structure (`http` / `core` / `repositories` /
`models` / `config` / `exceptions`), so the port is close to a one-for-one mapping.

The weight is not in the line count — it is in `core/job-report.service.ts` (968 lines of Mongo
aggregation) and the three auth paths.

## Why Go here

The same argument as the others, plus one specific to this service: **`min_instance_count = 0`**.
It scales to zero, so every scanner report after an idle period pays a cold start. Go's start time
is the direct win, on top of the ~3× latency and ~10× memory improvements measured on fuse-mcp.

## The surface — 11 endpoints

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/api/v1/job-reports` | 202, dedupe-upsert on `idempotencyKey` |
| GET | `/api/v1/job-reports` | paged `{total, offset, count, data}` |
| GET | `/api/v1/findings` | reports flattened to one row per finding; per-row open/resolved |
| GET | `/api/v1/summary` | bySeverity/byScanner/byRepo/byOutcome/byFixable + trend + posture |
| GET | `/api/v1/tree` | org → repo rollup |
| GET | `/api/v1/worklist` | top-N prioritised findings (array, not paged) |
| GET | `/api/v1/coverage` | per-repo scanner coverage + staleness |
| GET | `/api/v1/facets` | distinct orgs/repos/branches |
| GET | `/api/v1/pipeline-runs` | job reports grouped by CI run |
| GET | `/health/liveness`, `/health/readiness` | **unguarded**, and outside the `/api` prefix |

Shared filters on every read: `org repo branch scanner severity outcome from to defaultBranch runId`,
plus `offset`/`count` where paged, and `ruleId`/`status`/`fixable` on findings.

## Acceptance criterion

The OpenAPI document Nest generates has **no response schemas** — every response is
`{"description": ""}` — so it pins the *request* surface (paths, methods, query params) and nothing
about the answers. Two gates instead:

1. **Request-surface parity** against the captured spec: paths, methods, and each endpoint's query
   parameter set. A stored golden, because it does not depend on data.
2. **Differential response parity**, live against live. The data changes nightly, so a stored
   response golden would rot. `tools/diffcheck` queries the TypeScript service and the Go service
   over a matrix of endpoint × filter combinations **at the same moment, against the same MongoDB**,
   and diffs the JSON. This is a stronger gate than any fixture: it is the real aggregation logic on
   real data.

Everything below the query layer is unit-tested against the existing `ICollection` port, which the
TypeScript service already defines — the service takes it by constructor and knows nothing about the
driver. That seam ports directly.

## Error contract — RFC 7807, reproduce exactly

Captured from the live service. Every failure is Problem Details:

```json
{"type":"https://tools.ietf.org/html/rfc7231#section-6.5.1","title":"Bad Request",
 "status":400,"detail":"Validation failed","instance":"/api/v1/job-reports"}
```

`instance` is the full request URI **including the query string**. 401 uses the RFC 7235 type with
`detail: "Invalid or missing credentials"`; 404 is `detail: "Cannot GET <path>"`. Callers matter
here: the reusable workflows treat a 4xx as **log-and-drop**, so a wrong status silently loses
security reports rather than failing loudly.

## Auth — three credentials, one guard

1. **`x-api-key`** compared timing-safely against config.
2. **GitHub Actions OIDC** — JWKS from `token.actions.githubusercontent.com`, verified issuer +
   configured audience, then an org allowlist. **Sets `verifiedSource`**, and the service *overrides*
   the body's `source.org`/`source.repo` with it, so a caller cannot lie about which repo it is.
3. **Azure DevOps OIDC** — JWKS from `vstoken.dev.azure.com`, audience fixed at
   `api://AzureADTokenExchange`, issuer pinned per allowed org GUID (allowlisting and issuer
   verification are the same check). **Deliberately does not set `verifiedSource`** — its claims are
   GUIDs, and overriding `source` with them would replace readable dashboard data with opaque ids.

A Bearer token only ever matches one provider, so the guard tries GitHub then **falls through** to
Azure DevOps on failure rather than rejecting. Each path is enabled only when configured; an empty
audience or empty allowlist disables it.

⚠️ `vstoken.dev.azure.com` is **deprecated as of 2026-07-01, EOL 2027-07-01** with no documented
successor for this token type. Port as-is; the replacement is a separate problem.

## Cutover — a shadow service, then one variable

**There is no load balancer.** The API is addressed by its raw Cloud Run URL, which is *hardcoded as
the default* `report_api_url` in the platform's reusable workflows and read by the UI through
`terraform_remote_state`. So the weighted-LB split used for fuse-mcp is not available, and adding an
LB just to migrate is disproportionate.

Instead:

1. Deploy the Go API as a **second, temporary Cloud Run service** (`secops-api-go-prod`) against the
   **same MongoDB**. No caller points at it.
2. Run `diffcheck` TS-vs-Go across the filter matrix. Same data, same instant — any difference is a
   real difference.
3. When it matches, point `secops-api-prod` at the Go image. One Terraform variable; the previous
   image tag is the rollback and needs no rebuild.
4. Delete the shadow service.

This gives exhaustive verification against production data with **zero caller impact**, and a
cutover that is one variable rather than a routing change.

## Observability — do **not** copy fuse-mcp here

Checked, not assumed: this service has **no Datadog sidecars** and **no `LOG_FILE`**. So:

- Logs go to **stdout**, which Cloud Logging collects. The fuse-mcp rule (write to `LOG_FILE`, never
  stdout) exists because of the sidecar and the stdio transport, and neither applies here.
- **DogStatsD would go nowhere.** Metrics are therefore out of scope unless a sidecar is added first
  — that is a deliberate decision to surface, not something to slip in.

The house slog handler shape (message/timestamp/status, flat base tags, `source: go`) still applies.

## Libraries

Per the Confluence page, and all already house-approved: `chi/v5` for routing (nine routes with a
shared prefix and a guard — past `ServeMux`'s comfortable range), `go.mongodb.org/mongo-driver/v2`,
`log/slog`, stdlib `net/http` clients, stdlib `testing`.

One genuinely new dependency: **JWKS verification**. `golang-jwt/jwt/v5` (already in the fleet) does
not fetch or cache remote JWKS. `MicahParks/keyfunc/v3` (v3.8.1, 2026-07-27) is its standard
companion and handles caching and rotation. Rolling that by hand is security-sensitive code with a
cache-invalidation problem attached — this is exactly the case the "prefer a maintained library"
test is for.
