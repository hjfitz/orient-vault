---
title: SecOps Ingest API — Go Rewrite Migration State
status: in-progress
owner: Harry Fitzgerald
created: '2026-08-24'
updated: '2026-09-10'
tags: [ilg-platform, secops, golang, migration, migration-state]
---

# SecOps API — Go Rewrite Migration State

> **Single source of truth for progress.** Read and updated by the `secops-api-go` skill on re-entry.
> Never assume progress — read the ledger.

Rationale + design: [[Bifrost/SecOps API Go/Overview|Overview]]

**Repo:** `~/code/fuse/secops-reporting` (`ilg-platform/secops-reporting`) ·
**worktree:** `.claude/worktrees/api-go` · commits land straight on `origin/main` (no PRs, this
repo's convention) · latest as of this doc: `1261a2c`

## Status: ✅ **Done. `S4` shipped 2026-08-27. Node fully decommissioned.**

`api/src`, the Node toolchain, and the Node Cloud Run traffic target are all gone. `secops-api-prod`
runs a single untagged revision, 100% latest, Go image only (`secops-api-prod-00028-xcl` as of the
last apply — every push rolls a fresh one). No rollback lever remains beyond reverting the commits.

**Correction, 2026-08-27 — the first S4 apply (`ba6f74f`) did not actually clear the Node route,
despite what was reported at the time.** `google_cloud_run_v2_service.traffic` is Optional+Computed:
removing both `dynamic "traffic"` blocks from `cloud-run.tf` meant the field was *absent* from the
config, and Terraform's behaviour for an absent Optional+Computed field is to leave whatever was
already applied untouched — not reset it to the resource's implicit default. The two-entry traffic
spec from `997b6ec` (golang 100%, node 0%-but-tagged) survived the apply unchanged. Caught by
actually checking live state after the deploy rather than trusting the apply's success: both
`status.traffic` and `spec.traffic` still carried the `node` tag, and
`https://node---secops-api-prod-...run.app/health/liveness` answered `HTTP 200` — the deleted,
unmaintained NestJS code was live and publicly reachable against the same production Mongo for the
duration between the two applies. Fixed in `1261a2c`: one explicit static `traffic` block (`type =
LATEST, percent = 100`, no tag) replaces the omitted field, which does force Cloud Run to clear
the stale target — reverified after that apply: `status.traffic` is a single untagged 100% entry,
and the node URL now answers `404`.
**Lesson for the next Go port that removes a Cloud Run traffic split: an empty/absent `dynamic` block
is not the same as an explicit one asserting the default. Verify the live resource state after a
traffic-clearing apply, don't infer it from the apply's exit code.**

---

## ⚠️ Read before touching anything

1. **Commit straight to `main`. No PRs, no review.** Repo-scoped and deliberate (two-person project).
2. **Any push to `main` triggers a full deploy** — no path filter, docs-only pushes redeploy. Gated by
   the `terraform-prod` GitHub environment, approved by the `platform-admins` ilg-platform team.
3. **Prod-only. No dev or staging.** `env = prod` everywhere.
4. **The API applies before the UI** — the UI reads the API's Terraform `remote_state`.
5. **No load balancer.** The raw Cloud Run URL is the hardcoded `report_api_url` default in
   `ilg-platform/github-actions`. Do not rename the service.
6. **A 4xx is log-and-drop at the caller.** Getting a status wrong loses security reports silently
   rather than failing loudly.

---

## Unit ledger

Status: ⬜ not started · 🟨 in progress · ✅ done · ⛔ blocked

### Tranche 0 — Foundations

| Unit | What | Prereqs | Status |
| --- | --- | --- | --- |
| ✅ `G0` | Go skeleton beside `api/`: `go.mod`, `cmd/secops-api`, `internal/` layers, `Makefile`, `.golangci.yml` (v2 schema + `config verify` in `make lint`), Go patch pin in `mise.toml`, `go-code-quality.yaml`, `secops.yaml` gains `lang: go` + a Go image scan. | — | ✅ |
| `G1` | Config (one package owns every `os.Getenv`; same required/optional set and defaults) + the house slog handler writing to **stdout** — see the Overview, this differs from fuse-mcp deliberately. | `G0` | ✅ `8abd0ff` |
| ✅ `G2` | **`tools/diffcheck`** — the gate. 86 cases over endpoint × filter combinations. Proven TS-vs-TS (86/86, 0 differed) and fault-injected (19 tests). | `G0` | ✅ |
| `G3` | Request-surface parity test against the captured OpenAPI golden: paths, methods, per-endpoint query-param sets. | `G0` | ✅ `dd0605a` |

### Tranche 1 — Data layer

| Unit | What | Prereqs | Status |
| --- | --- | --- | --- |
| `D1` | Mongo connection + the generic `Collection[T]` port, mirroring `ICollection`. Indexes **awaited at startup**, not fire-and-forget. Driver code `11000` → conflict. | `G1` | ✅ `12e612c` |
| `D2` | `JobReport` models + validation. The Zod discriminated union on `scanner` becomes explicit per-variant validation — **seven** scanners, not the six `api/CLAUDE.md` claims (`dotnet-vulnerable` was added; the doc is stale). Keep the `findings[].scanner == scan.scanner` refinement. | `G0` | ✅ `4d75566` |

### Tranche 2 — Query core

`core/job-report.service.ts` is 968 lines and nine methods over shared helpers. **The helpers land
first**, in one unit, so the method units cannot each invent their own — that is exactly how six
parallel agents ended up with three implementations of the same schema mutator on fuse-mcp.

| Unit | What | Prereqs | Status |
| --- | --- | --- | --- |
| `Q0` | The shared query layer: `buildQuery`, `currentSnapshotStage`, `currentSnapshotFilter`, `freshnessCutoff`, `fixableExpr`, `fixableCond`, `severityCond`, `switchBranch`, `toRecord`, and the paging envelope. Plus the constants: `DEFAULT_BRANCHES = [main, master]`, `DEFAULT_FRESHNESS_WINDOW_DAYS = 5`, default offset 0 / count 20. | `D1` `D2` | ✅ `0028a01` |
| `Q1` | `ingest` (+ the `verifiedSource` override) and `list`. | `Q0` | ✅ `0028a01` |
| `Q2` | `findings` — report-level rank and open/resolved computed *before* the unwind, then carried per row. | `Q0` | ✅ `0028a01` |
| `Q3` | `summary` — five breakdowns, `trend`, `posture`. | `Q0` | ✅ `0028a01` |
| `Q4` | `tree` + `coverage`. | `Q0` | ✅ `4680069` |
| `Q5` | `worklist` + `facets` + `pipelineRuns`. | `Q0` | ✅ `4680069` |

### Tranche 3 — HTTP

| Unit | What | Prereqs | Status |
| --- | --- | --- | --- |
| `H1` | Router (chi), the `/api` prefix with `/health/*` **outside** it, the 10 MB body limit, RFC 7807 error responses reproduced byte-for-byte, and the 404 shape. | `G1` | ✅ `5aa143f` |
| `H2` | Query-param binding and validation for all eight read endpoints, matching the DTO schemas exactly — including `defaultBranch`/`fixable` accepting only the literal `"true"`/`"false"` (**not** loose truthiness) and the `count` bounds (1–100, default 20). | `H1` `D2` | ✅ `5aa143f` |
| `H3` | The guard: `x-api-key` timing-safe, GitHub OIDC (JWKS, issuer, audience, org allowlist, sets `verifiedSource`), Azure DevOps OIDC (JWKS, fixed audience, issuer pinned per org GUID, **no** `verifiedSource`), GitHub-then-fall-through-to-ADO. | `H1` | ✅ `5aa143f` |
| `H4` | Wire the controllers to the service; serve an OpenAPI document whose request surface matches the golden. | `H1` `H2` `Q1`–`Q5` | 🟨 `5aa143f` — handlers wired and the surface pinned by `G3`'s test, but **no OpenAPI document is served**: `/api/docs` and `/api/docs-json` exist on the TypeScript service and do not exist on the Go one. Decision needed, see below. |

### Tranche 4 — Ship

| Unit | What | Prereqs | Status |
| --- | --- | --- | --- |
| `S1` | Dockerfile (distroless static, `CGO_ENABLED=0 -trimpath`) + a **temporary shadow Cloud Run service** `secops-api-go-prod` against the same MongoDB. No caller points at it. | all above | ✅ `426943a` `dcbf8d1` |
| `S1a` | Push, and get the shadow service applied through the `terraform-prod` gate. | `S1` | ✅ — superseded by the `21e5c0a` pivot to weighted-revision cutover (see Decision Log); no separate shadow service was ever applied |
| `S2` | Run `diffcheck` TS-vs-Go across the full matrix until clean. This is the gate — same data, same instant. | `S1` | ✅ 104 cases, 103 matched, 1 known divergence, 0 differed — clean at 75/25 (`430e4c5`) and reconfirmed clean at 100/0 (`997b6ec`) |
| `S3` | Point `secops-api-prod` at the Go image. One variable; the previous image tag is the rollback. | `S2` | ✅ `997b6ec`, deployed 2026-08-26. `go_traffic_percent = 100`. Node revision `secops-api-prod-00020-pqr` (tag `node`) stays deployed at 0% — untouched, still the instant no-rebuild rollback. |
| `S4` | Delete the shadow service, `api/src`, the Node toolchain and its CI. Update `CLAUDE.md` ×2 and the README. | `S3` **held** | ✅ `ba6f74f` (source/CI/docs) + `1261a2c` (the actual traffic-clear — see the Status correction; the first apply didn't clear the Node route despite reporting success). Deployed 2026-08-27. |

---

## Gates

- **`G2` green TS-vs-TS, and fault-injected, before any porting is trusted.** A differential harness
  that cannot fail is worse than none.
- **`Q0` lands before `Q1`–`Q5`**, and those may then be done in parallel.
- **`S2` clean before `S3`.** No caller moves until the shadow service matches on real data.
- **`S4` only after `S3` has held.** Deleting the TypeScript image removes the cheap rollback.

---

## Risk register

| id | risk | mitigation |
| --- | --- | --- |
| **R1** ★★ | **968 lines of Mongo aggregation is the whole risk of this port.** `$facet`, `$unwind`, `$expr`, latest-per-lane ranking and freshness windows, and a wrong pipeline returns *plausible* numbers rather than an error — a dashboard that quietly under-reports open criticals is worse than one that breaks. | `diffcheck` against the live service on the same data. Reading the pipelines is not enough; only a differential comparison catches a subtly wrong rank or cutoff. |
| **R2** ★ | **Live data changes nightly**, so any stored response fixture rots and a "failure" may be a new scan rather than a regression. | The harness is live-vs-live at the same instant, and re-runs a differing case to separate a real difference from a scan landing mid-comparison. |
| **R3** ★ | **A 4xx is silently dropped by every caller.** A wrong status code loses security reports with no error anywhere. | Reproduce RFC 7807 exactly, statuses included; assert the bodies, not just the codes. |
| **R4** ★ | **Provenance is a security property.** The GitHub OIDC path overrides `source.org`/`source.repo` from signed claims so a caller cannot lie; the Azure DevOps path deliberately does not. Getting this backwards either breaks the dashboard or lets a repo impersonate another. | Port the asymmetry deliberately, with a test each way. |
| **R5** | **Any push to `main` deploys.** No PR gate, no path filter. | Run every local gate first. The `terraform-prod` environment approval is the only checkpoint. |
| **R6** | **No LB, and the Cloud Run URL is hardcoded in the platform's reusables.** Renaming the service breaks every scanner in the estate. | Keep the service name; cut over by changing its image. |
| **R7** | **`api/CLAUDE.md` is stale on the scanner list** — it says six, the schema has seven. | Ported from the schema, not the doc. Fix the doc at `S4`. |
| **R9** ★ | **The TypeScript service is non-deterministic in two places**, found by running the harness against itself rather than assumed: `/health/*` returns a `timestamp` and `uptime`, and **all five `summary` breakdown arrays reorder between identical requests** (the sort has no tiebreak among equal counts) — 22 of 86 cases only match once order is allowed for. So array order cannot be asserted on those, and the dashboard's chart ordering is *already* arbitrary today. That is a pre-existing bug in the TypeScript service, not something the port introduces. | The harness reports a pure reordering separately from a difference — surfaced, not hidden, because order *is* contract on the paged endpoints. Values are still compared either way, so a reordering that also changes a count still fails. **Worth fixing in the port** by adding a deterministic tiebreak, but that would then show as a diff against the TypeScript service — so do it as a deliberate, separate change *after* cutover, not during. |
| **R8** | **No Datadog sidecar here.** Copying fuse-mcp's observability would write logs to a file nothing tails and metrics to a socket nothing listens on. | Log to stdout; metrics explicitly out of scope. |

---

## Non-negotiables & operational specifics (carried from the retired skill)

Load-bearing detail the `secops-api-go` skill held that isn't otherwise in this doc. The programme is
cut over, but a future maintainer still needs these.

- **Getting the ingest key** (to run `diffcheck`, or any authenticated call):
  `cd iac/projects/secops-api && TF_VAR_env=prod terragrunt output -raw ingest_api_key`. The live API
  is `https://secops-api-prod-6cprbzyuka-nw.a.run.app`; its OpenAPI document is at `/api/docs-json`.
- **Adding or renaming a scanner is a three-way lockstep** with `ilg-platform/github-actions`'
  `report-scan.mjs` and every reusable's `scanner:` literal — not a schema-only change. (The real
  seventh scanner is `govulncheck`; `dotnet-vulnerable` was never one — see the 2026-08-24 correction.)
- **`DEFAULT_FRESHNESS_WINDOW_DAYS = 5` is deliberately wide** so a repo whose cron skipped a day does
  not read as a false all-clear. `DEFAULT_BRANCHES = [main, master]`. Don't tighten either casually.
- **Response shape is coupled to the UI two-directory-wide.** The API's response-shape contract and
  `ui/lib/secops/types.ts` **mirror each other** — any shape change is a two-repo-directory change, and
  the API applies before the UI (which reads the API's Terraform `remote_state`).
- **`POST /api/v1/job-reports` idempotency** is a unique index on `idempotencyKey` plus an upsert whose
  "was this new?" answer comes from `returnDocument: before` being null (→ 202); driver code `11000`
  maps to conflict. Don't substitute a read-then-write.
- **`vstoken.dev.azure.com` (Azure DevOps OIDC) is deprecated 2026-07-01, EOL 2027-07-01** with no
  documented successor for the no-service-connection token this guard verifies. Ported as-is; replacing
  it is its own problem — the full writeup lives in `secops-ci`'s README.

---

## Decision log

| date | decision |
| --- | --- |
| 2026-08-24 | **Cutover is a shadow service, then one image variable** — not a weighted LB split. There is no LB, and the Cloud Run URL is the hardcoded default in the platform's reusable workflows. Adding an LB purely to migrate is disproportionate; a shadow service on the same MongoDB gives better verification anyway. |
| 2026-08-24 | **The acceptance gate is differential, not a fixture.** Nest's OpenAPI document carries no response schemas, and the data changes nightly. Comparing live-against-live on the same database at the same moment is both stronger and the only thing that does not rot. |
| 2026-08-24 | **Not generating from the OpenAPI spec.** `oapi-codegen` is the house tool where a spec is the contract, but this spec declares one component schema and no response types — generating from it would produce stubs with untyped answers. The spec pins the request surface only. |
| 2026-08-24 | **`MicahParks/keyfunc/v3` for JWKS.** `golang-jwt/jwt/v5` cannot fetch or cache remote JWKS. Hand-rolling it is security-sensitive code with cache invalidation attached — the "prefer a maintained library" test in the Preferred Libraries page exists for precisely this. |
| 2026-08-24 | **Logs to stdout, metrics out of scope.** Verified there are no Datadog sidecars and no `LOG_FILE` on this service, so the fuse-mcp file-sink rule does not transfer and DogStatsD would go nowhere. |
| 2026-08-24 | **A reordering is not a failure, but it is reported.** Established empirically: the TypeScript service returns equal-count rollup groups in a different order between two identical requests, so requiring positional equality would keep the gate permanently red. Values are compared regardless, and a reordering on a paged endpoint — where order *is* deterministic contract — still shows up in the output for a human to judge. |
| 2026-08-24 | **Shared query helpers land before the nine methods.** On fuse-mcp, six parallel agents each invented their own schema mutators. Sequencing `Q0` first removes that. |
| 2026-08-26 | **Ramped to 100% Go (`S3`), decommission (`S4`) deliberately held.** Re-verified the diffcheck gate live immediately before ramping (104/103/1/0, same pattern as 75/25) and again immediately after. Harry chose to let `S3` hold rather than run straight into `S4` in the same session — matches this doc's own gate that deleting the TypeScript image removes the cheap rollback. `S4` scope is mapped (see the ledger row) but not started. |
| 2026-08-27 | **`S4` shipped, in two applies.** The first (`ba6f74f`: `api/src` + Node toolchain + CI + docs deleted) was reported as clearing the Node Cloud Run traffic target too, but did not — see the Status correction. A second apply (`1261a2c`) actually cleared it, found and fixed by checking live `status.traffic`/`spec.traffic` and curling the node-tagged URL after the first apply rather than trusting its green CI run. Also same-day: `f98b2af` (a separate session, merged in cleanly, zero file overlap) added a real seventh scanner, `govulncheck`, directly to the Go service — `api/CLAUDE.md` was updated in the `S4` commit to describe seven scanners, not six, and to distinguish `govulncheck` (real) from `dotnet-vulnerable` (the corrected hallucination) explicitly, since both are "a scanner that isn't in the original six." |


## Resolved decisions

**The `terraform-prod` gate for `S1a`/`S3`.** Resolved by the `21e5c0a` pivot away from a standalone
shadow service to weighted-revision cutover inside `secops-api-prod` itself (see Decision Log,
2026-08-24) — the separate `secops-api-go-prod` service described in the original draft of this
section was never applied. `S3`'s ramp to 100% (`997b6ec`, 2026-08-26) went through the same
`terraform-prod` gate: a one-line `go_traffic_percent` change, self-approved via the
`pending_deployments` API after the plan (this exact diff, described in prose since the reusable's
`apply -auto-approve` leaves no CI plan to read) was agreed with Harry first.

## Awaiting a decision

**The OpenAPI document.** The TypeScript service serves Swagger at `/api/docs` and
`/api/docs-json`, unguarded. Nothing in either repo consumes it — checked — and Nest generates it
with no response schemas at all, so its only real value is as a route listing. The Go service does
not serve it. Two options: drop it, or serve a hand-written document from a `go:embed`ed file (one
file, no dependency). Worth noting the document is what made `G3` possible at all, so it does get
used, just not by software. Not a blocker either way.

## Things found in the source, to fix *after* the cutover

Each is reproduced faithfully in the Go port and pinned by a test, so none of them can be "fixed" by
accident while the two services are being compared. Each needs its own change, where the numbers
moving is the visible point of it.

- **`severity` has no effect on `/summary`** — the shared query has no severity clause and no facet
  adds one, so a severity-filtered summary returns the unfiltered rollup.
- **The worklist's `fixable` gate is one-way**, where the findings read negates the expression. So
  `fixable=false` is the same as not asking on one endpoint and a real filter on the other.
- **All five `summary` breakdowns reorder between identical requests** — no tiebreak among equal
  counts. This is the one the harness surfaces on every run.
*(Two entries about `dotnet-vulnerable` were removed from this list on 2026-08-24. They were not
defects. See the correction below.)*


## Correction, 2026-08-24 — `dotnet-vulnerable` was never a scanner

The port carried a seventh scanner, `dotnet-vulnerable`, that **does not exist**. `ScannerSchema` in
the TypeScript service has six values and always has. The string appears in that file exactly once,
in a comment describing the tool `nuget-audit` shells out to — `dotnet list package --vulnerable`.

The differential gate caught it: three of its four findings were the Go build answering **200** on
`scanner=dotnet-vulnerable` where the real service answers **400**. Had it not been caught, the UI's
scanner filter would have worked against one revision and 400'd against the other, at random, for
the duration of the split.

What makes it worth writing down is how far it travelled before the gate stopped it:

- Two rows on the *fix after cutover* list above described it as missing from `fixableExpr` and from
  coverage's `hasDeps`. Neither was a defect — nothing can be missing a value that does not exist.
- A test, `TestTheFixabilitySwitchOmitsDotnetVulnerable`, pinned one of those non-defects in place, so
  it would have outlived the mistake and defended it.
- `api/CLAUDE.md` correctly said six. A comment in `models/job_report.go` asserted the doc was *stale*
  and that "the schema is the truth" — overriding a correct document with an invented fact, then
  citing the invention as authoritative.
- It reached the commit messages, the PR body, and this document.

**The lesson is not "check the schema".** It is that the error was *asserted more confidently at each
retelling*, and the confident retelling is what stopped anyone re-checking it. The fix is now covered
by two named gate cases rather than by its absence, so what both services do with an unknown scanner
is asserted rather than assumed.

## Where the cutover stands, 2026-08-26

**Live at 100% Go / 0% Node**, by weighted Cloud Run revision inside the one service — not a load
balancer, which does not exist for this service (its URL is the hardcoded `report_api_url` in every
`secops-*` reusable and what the UI reads from remote state, so it could not change).

- Go: `secops-api-prod-00025-h5n`, tagged `golang`, 100%. (Ramped from 75% in `997b6ec`; the prior
  75%-traffic revision was `secops-api-prod-00024-zt5` — every push rolls a fresh revision, so the Go
  side's name moves even when nothing about the port itself changed.)
- Node: `secops-api-prod-00020-pqr`, tagged `node`, 0%. **Do not delete this revision** — it is still
  the rollback target, deployed and addressable even though it serves no traffic.
- Rollback: `go_traffic_percent = 0` in `iac/env/prod.tfvars`, one apply, no rebuild.
- Gate: **104 cases, 103 matched, 1 documented divergence, 0 differed**, run live against both
  services and the same database at the same moment. Confirmed clean twice: once at 75/25
  (`430e4c5`) and again immediately after the ramp to 100/0 (`997b6ec`).
- Dashboard: [SecOps API — Go/Node cutover](https://app.datadoghq.com/dashboard/shp-pia-pbv/secops-api--gonode-cutover),
  31 widgets, every one verified to return data, broken out by `revision_name`.

**Next: `S4`.** Deliberately not started — see the Status line above and the Decision Log.

**The one documented divergence:** a body that is not JSON. The TypeScript service puts V8's raw
`JSON.parse` message in `detail`; the Go service answers the same 400 with the generic
`"Validation failed"`. Matching it would mean reproducing V8's error text and leaking parser
internals to a caller. The gate prints it every run and still fails on any *other* difference to that
case.

**Both revisions are tagged, and the gate is runnable at any time** — this closed a gap that appeared
the moment Go took traffic: the main URL became a mixture and stopped being a Node baseline.

```
cd api && SECOPS_API_KEY=<key> go run ./tools/diffcheck \
  -ts https://node---secops-api-prod-6cprbzyuka-nw.a.run.app \
  -go https://golang---secops-api-prod-6cprbzyuka-nw.a.run.app
```

Run it after **any** push to main, not just an intentional one: there is no path filter on the deploy,
so every push rebuilds the Go image under a new SHA and rolls a fresh, unverified revision straight
into whatever `go_traffic_percent` is set to. A docs-only commit does it too. Verified green against
`00024-zt5` while it was serving 75%.

**Also found and corrected:** this service's logs never reach Datadog at all — no agent sidecar, no
export sink from the prod project, zero events over 30 days. A code comment described Cloud Logging
as "the whole delivery path", which reads as though the path ends somewhere useful. Monitoring has to
be built on `gcp.run.*` metrics, which is what the dashboard does.
