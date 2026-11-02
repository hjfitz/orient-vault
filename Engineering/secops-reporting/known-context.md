---
tags: [waypoint, secops-reporting]
verified: '2026-08-24'
verified_paths: []
title: secops-reporting — known context
---

# secops-reporting — known context

`known-context.md` is exempt from staleness checks — this is interview/investigation
truth, not a claim about current source. Re-verify against code before trusting a
specific implementation detail below.

**The deepest, most volatile source for this service right now is the
vault's `Bifrost/SecOps API Go/Overview.md` and `Migration State.md`** —
confirmed directly by Harry that another agent is actively rewriting
`api/` in Go **as of this exact onboarding pass**. Unlike the other
migration docs referenced this session (fuse-mcp, fuse-mocker,
shopify-connector), this one should be assumed stale within *hours*, not
days or weeks. Read it fresh before touching anything on the API side.

## Ownership {#ownership}

Confirmed 2026-08-24: genuinely a **two-person project**, Harry and the
CTO. Different from every other `ilg-platform` repo onboarded this
session — not a shared ownerless platform effort, not someone else's
repo Harry merely consumes. Direct co-ownership, with the informal
"commit straight to main, no review" convention that implies.

## Both OIDC ingest paths are real and live, not one theoretical

Confirmed directly by Harry: GitHub Actions OIDC and Azure DevOps OIDC are
**both** active, in-use ingest paths — this isn't a GitHub-only service
with speculative ADO support bolted on. Every `secops-*` reusable workflow
in `ilg-platform/github-actions` reports into this exact API. Don't
assume the Azure DevOps path is dead code or aspirational; it's a real
production auth route with real callers.

## A live, previously-unknown bug found only by building the Go migration's own verification gate

`diffcheck` (the differential harness proving the Go port trustworthy)
ran TypeScript-against-itself before any porting started, and found the
TypeScript service is non-deterministic in two places: `/health/*`
returns a live `timestamp`/`uptime` (expected), and **all five `summary`
breakdown arrays reorder between identical requests** because the sort has
no tiebreak among equal counts — 22 of 86 differential test cases only
matched once array order was allowed to vary. This is a **pre-existing bug
in the currently-running TypeScript service**, not something the Go port
would introduce, and it means the dashboard's chart ordering is *already*
arbitrary today. Deliberately not being fixed as part of the port (fixing
it now would show up as a spurious diff against the very gate proving the
port correct) — it's queued as a deliberate, separate change for *after*
cutover.

## A stale doc, caught mid-migration, not yet fixed

`api/CLAUDE.md` states the `JobReport` schema has six scanner types; the
real schema has **seven** (`nuget-audit`/`dotnet-vulnerable` was added in
the SecOps 0.2 release and the doc wasn't updated). The Go migration's own
plan explicitly defers fixing this doc to its `S4` (decommission) unit —
ported from the schema directly, not the doc, in the meantime.

## The Azure DevOps OIDC issuer has a real, dated expiry with no successor yet

`vstoken.dev.azure.com` — the issuer this service's Azure DevOps OIDC guard
verifies against — is deprecated per Microsoft as of 2026-07-01, EOL
2027-07-01, with no documented replacement issuer for this specific
no-service-connection token type. This is a real, dated operational risk
independent of the Go rewrite; the migration explicitly ports the existing
behaviour as-is and treats the eventual replacement as a separate problem.

## Unknowns

- Current real-time progress of the Go rewrite — check
  `Bifrost/SecOps API Go/Migration State.md` directly rather than trusting
  anything cached here, given how actively it's moving.
- Whether the summary-array non-determinism has been queued as a formal
  ticket for post-cutover, or exists only as a note in the migration doc's
  risk register.
- Whether a successor to the deprecated Azure DevOps OIDC issuer has
  emerged since this pass.
