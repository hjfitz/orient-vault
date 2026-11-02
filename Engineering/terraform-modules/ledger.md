---
tags: [waypoint, ledger]
title: terraform-modules — work ledger
---
# terraform-modules — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-10-28 — cloud-run: run Datadog in the app container, drop the sidecars

cloud-run: run Datadog in the app container, drop the sidecars

Breaking, shipped by force-moving 0.1-affogato (no consumers on that line). One container, DD_* on the app, datadog_api_key + optional datadog_additional_api_key. Docs moved to the 0.1-affogato convention; v0.1.0 documented as frozen legacy.

PR: ilg-platform/terraform-modules#4

## 2026-08-26 — Framework module consolidation (PR #2, open)

Eleven modules brought in from `gfs-sre/terraform-framework` so consumers can pin a tag instead of a branch. **Open and unmerged** — it is a proposal for Wolf/SRE, introduced in Slack by Harry, not something to merge. Context: [[Bifrost/Platform Terraform Alignment/Overview|Platform Terraform Alignment]].

The reason this exists: `ilg-platform/gcp-config` pinned `?ref=main` and `ilg-tech-services-iac` pinned `?ref=development` *and* `?ref=feat/ilg-tech-services-modules` — a feature branch — in live IaC. A force-move lands in an apply, and the orchestration being branch-tied puts the state backend in reach.

- **Layout**: `project/factory`, `project/iam`, `iam/service-account`, `networking/{vpc,vpc-connector,load-balancer,cloud-nat,dns-zone,iap-web}`, `compute/{vm,cloud-run-service}`. `vpc-connector` and `load-balancer` fill the two `.keep` placeholders that were already planned.
- **Byte-identical, deliberately.** All 44 `.tf` files hashed against source. Keeps consumers' state addresses stable — a repoint is a one-line change with a no-op plan, no `moved` blocks — and reads as a move of SRE's work rather than a rewrite. **Do not tidy the internals**; `project/factory` wraps a nested `module "project_factory"` and flattening it forces `moved` blocks on every consumer.
- **Which ref**: `main` for the five shared modules, the feature branch for the six extras. Verified the feature branch is purely additive (its copies of the shared five match `development` exactly) and that `main` vs `development` differs only by a `project_id` non-empty validation plus whitespace — satisfied by both consumers.
- **Two Cloud Run modules now coexist**: the existing opinionated `compute/cloud-run` (own SA, `${project_name}-${env}` naming, two Datadog sidecars) and the generic `compute/cloud-run-service` (caller supplies name/SA/image, image excluded from drift detection). Different opinions of one resource, not duplicates. Reconciling them is open work.
- **Only edits to copied files**: README usage examples repointed, and READMEs written for `networking/vpc` and `compute/vm` which arrived without one. Committed `.terraform.lock.hcl` files dropped.
- **Versioning is now written down** (README + CLAUDE.md): immutable `vMAJOR.MINOR.PATCH`, never force-moved — explicitly contrasted with `ilg-platform/github-actions`' *rolling* named tags (`0.1-affogato` → `0.2-bonbon`), which are force-moved on purpose. A rolling module tag would mean a stack's next apply planning against different code with no diff in its own repo. While `0.x`, breaking bumps MINOR.
- **No CI in this repo**, so verification was local: hashes, `terraform validate` on all 12 modules against 1.14.9, `fmt -check` clean.

Next after merge: tag `v0.2.0`, repoint both consumers, then delete the `PLATFORM_CI_APP_ID` shadow + `gh_app_owner: gfs-sre` they currently need for the cross-org fetch.
