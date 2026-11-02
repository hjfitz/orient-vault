---
tags: [waypoint, terraform-modules]
verified: '2026-08-24'
verified_paths: []
title: terraform-modules — known context
---

# terraform-modules — known context

`known-context.md` is exempt from staleness checks — this is interview/investigation
truth, not a claim about current source. Re-verify against code before trusting a
specific implementation detail below.

## Ownership

Shared, ownerless platform effort (`#platform-engineering`), not
Fuse-team-owned — same as `github-actions`. Harry is a regular contributor
here too (confirmed 2026-08-24).

## The adoption gap is real, verified, and expected {#adoption-gap}

Confirmed directly: grepped every Fuse service's `iac/` tree onboarded this
session (snap-adapter, snap-queue-polling-service, shopify-connector,
config-service, fuse-ui, replay-service, fuse-mcp, snap-mcp, fuse-mocker,
bifrost-pubsub) for the `terraform-modules` git source string. **Zero
matches.** Every one of them hand-rolls its own `google_cloud_run_v2_service`
resource directly, even though `compute/cloud-run` matches their shape
closely (app container + two Datadog sidecars + shared `emptyDir` +
startup probe — exactly the pattern seen repeated verbatim across this
session's onboarding). The only local consumer of the module at all is
`repo-template-ilg`, the scaffold template for brand-new services.

**Confirmed expected, not an oversight**: new services adopt the module via
the template; migrating already-running services onto it isn't currently a
priority. Don't treat the module's existence as evidence that any specific
running service uses it — check that service's own `iac/` directly, the
same way every other repo's Terraform should be verified rather than
assumed this session.

## The MCP catalog overstates current scope

`services.json`'s description implies working modules for "Cloud Run,
Pub/Sub, IAM and friends." Only Cloud Run exists; the rest are `.keep`
placeholders. This is a milder variant of the staleness pattern seen
repeatedly across every other service this session — here it's
overstatement of planned-vs-built rather than a factual drift, but the
practical lesson is the same: verify against the actual directory tree, not
the catalog's prose.

## Same org-rename and cross-org-fetch context as github-actions

Canonical org is `ilg-platform`; both this repo's and consumers' README
examples still show the old `gfs-platform` source string (GitHub redirects
it, so both currently resolve) — the repo's own CLAUDE.md explicitly says
not to mass-rewrite this. The private cross-org module fetch needs the same
GitHub-App-token handling that `github-actions`' `terragrunt.yaml` already
provides; a bare `terraform init` with only the default `github.token`
cannot fetch this module at all.

## Unknowns

- Whether any of the planned (`.keep`) modules — particularly
  `pubsub/topic`/`pubsub/subscription`, which would overlap with
  `bifrost-pubsub`'s hand-rolled topic module — have a concrete timeline, or
  are purely aspirational scaffolding for now.
- Whether there's a plan to eventually migrate any *existing* Fuse service
  onto `compute/cloud-run`, or whether it's intended to remain
  new-services-only indefinitely.
