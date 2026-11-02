---
title: Platform Terraform Alignment — Overview
status: three-prs-open-awaiting-review
owner: Harry Fitzgerald
created: '2026-08-26'
updated: '2026-08-26'
tags: [bifrost, ilg-platform, ilg-tech-services, gfs-sre, terraform, terragrunt, iac, platform]
---

# Platform Terraform Alignment — Overview

Bringing the two GCP stacks built on `gfs-sre/terraform-framework`'s "legacy stack" wrapper onto the ilg-platform model — Terragrunt, the `iac/env` + `iac/projects` layout, and the shared reusable workflows — and consolidating the framework's Terraform modules into `ilg-platform/terraform-modules` so they can be pinned to a tag.

Continues, and partly executes, [[Bifrost/Tech Services IaC Review/Remediation State|Tech Services IaC — Remediation State]] (Step 2 and Step 5). Progress for the tech-services repo stays tracked there; this doc covers the cross-repo activity, since `gcp-config` sits outside that review's scope.

## Why now

The driver is **branch-pinned module sources**, not tidiness. Across the two repos, modules are pinned to three mutable branches — one of them a feature branch — in live IaC:

| Repo | Modules | Pinned to |
|---|---|---|
| `ilg-platform/gcp-config` | `gcp-project`, `gcp-net-vpc`, `gcp-compute-vm` | `?ref=main` |
| `ilg-tech-services-iac` | `gcp-project`, `gcp-net-vpc`, `gcp-iam-service-account`, `gcp-project-iam` | `?ref=development` |
| `ilg-tech-services-iac` | six more, incl. Cloud Run / LB / IAP / DNS / NAT / VPC-connector | `?ref=feat/ilg-tech-services-modules` |

A force-move or a deleted branch lands straight in an apply, and because the orchestration is branch-tied it can reach the state backend and therefore the project. **Wilders and Kyle hit the same thing independently**, so it is not repo-specific. SRE had already expressed intent to move to Terragrunt like the other teams.

## How this is being run

**These are proposals, not merges.** Wolf owns this territory and there is active work to repair the relationship and pull SRE into the platform model — Oli's steer is to lead with the concern, the why and a suggested fix, kept open and dialogue-y. Concretely:

- Nothing is merged, nothing is self-approved, no reviewer is requested on the PRs. **Harry introduces them in Slack himself.**
- PR bodies carry the technical driver and the open questions. **The antipattern audit stays internal** — see [[Explainers/2026-08-26-gcp-config-antipattern-audit|the audit]]; it is not for the PR.
- Where possible the change is a **verbatim move of Wolf's work**, not a rewrite of it — which is both the lower-risk engineering choice and the better collaborative one.

An earlier attempt pushed the gcp-config change straight to `main`, applied it and verified it; Harry called it back and it was **fully reverted** (tree byte-identical to `1dee969`, infrastructure restored) so the work could go through review instead.

## The three PRs

| # | Repo | What | State |
|---|---|---|---|
| [1](https://github.com/ilg-platform/gcp-config/pull/1) | `ilg-platform/gcp-config` | Terragrunt + platform workflows | Open, green, plan `No changes` |
| [2](https://github.com/ilg-platform/terraform-modules/pull/2) | `ilg-platform/terraform-modules` | 11 framework modules brought in, byte-identical; tagging documented | Open, no CI in that repo; verified locally |
| [45](https://github.com/ilg-tech-services/ilg-tech-services-iac/pull/45) | `ilg-tech-services-iac` | Terragrunt + platform workflows | Open, **plan red by design** — see blockers |

Both structural PRs are behaviour-neutral: gcp-config plans `No changes` after a full refresh of all 21 resources; tech-services moves 24 files of which 22 are byte-identical, with module sources untouched.

## What we learned doing it

- **Terragrunt's `remote_state` block calls `storage.buckets.get`; Terraform's own GCS backend never does.** SRE grants each stack runner only `objectAdmin` on `gfs-terraform-core-tfstate`, so `remote_state` 403s there — which is why the old workflow worked and Terragrunt did not. Fixed without losing the convention by emitting the backend from a plain `generate "backend"` block in `root.hcl` (`generate` is codegen and makes no GCS call). Note `terraform-template` pairs `generate` *with* `remote_state`, which would still fail here. Terragrunt 0.50.8 also demands both `project` and `location` in a `remote_state` gcs config.
- **`terragrunt.yaml` reads the module-fetch app id from a fixed variable name**, `vars.PLATFORM_CI_APP_ID` — true at both `0.1-affogato` and `0.2-bonbon` (the only difference between those tags is `auth@v2`→`v3`). Consumers whose app is recorded under another name must shadow it. The real fix is a `gh_app_id` input; not raised, because adopting it means force-moving a rolling tag across every consumer.
- **The `feat/ilg-tech-services-modules` branch is purely additive** — its copies of the five shared modules are byte-identical to `development`. `main` vs `development` differs in only two modules (a `project_id` non-empty validation, and whitespace), and both consumers pass a non-empty `project_id`, so `main` is safe as the canonical source for the shared five.
- **`gcp-project` is a pure passthrough** to the public `terraform-google-modules/project-factory/google`. Worth knowing, but the framework dependency is invariant per Harry, so it stays.
- **Leaving the framework pipeline drops Checkov.** The platform's `secops-terraform.yaml` is Trivy-based. gitleaks + Trivy remain; `CKV_*` coverage stops.
- **Make the diff read as moves.** Splitting a file into topic files, or merging two together, in the same PR that relocates them destroys git's rename detection. Check `git diff -M --summary` before pushing.

## Blockers and prerequisites

- **`ilg-tech-services-iac` needs repo variable `PLATFORM_CI_APP_ID = 3896251`** and a **`terraform-prod` environment** with required reviewers. Harry has push but **not admin** there, so both need someone else. Until the variable is set the plan job fails at module fetch — the expected failure, verified as `Failed to download module`.
- **`gcp-config` carries a `PLATFORM_CI_APP_ID` shadow** of its own (same value) plus `gh_app_owner: gfs-sre`. **Delete both once the modules live in ilg-platform** — until then that repo cannot fetch an ilg-platform module at all.
- **No branch protection on `ilg-platform/gcp-config`'s `main`**, so its PR gate is voluntary.

## Open decisions

| Decision | Leaning |
|---|---|
| Reconcile the two Cloud Run modules — platform's opinionated `compute/cloud-run` (own SA, Datadog sidecars) vs the framework's generic `compute/cloud-run-service` | Both kept and documented for now; genuinely different opinions of one resource, not duplicates |
| Add a `gh_app_id` input to `terragrunt.yaml` | Yes, but needs a deliberate go-ahead — adoption means force-moving a rolling tag |
| Re-add Checkov coverage | Only if wanted; belongs upstream in `secops-terraform.yaml`, not per-repo |
| `gcp-config`: move state into its own project bucket | > SUPERSEDED 2026-09-14 — the bucket now exists (`ilg-platform-tfstate`, created by `gcp-config` commit `1c23fec`, output `tfstate_bucket_name`), but `gcp-config`'s own backend stays on `gfs-terraform-core-tfstate` by Harry's decision. The bucket's first tenant is the new `ilg-platform/core-infra` stack — see [[ilg-platform DNS Migration/Overview]]. Would close the last convention gap (prefix stays `stacks/ilg-platform/main`, bucket stays cross-tenant). Deferred — Harry chose to keep the existing backend |
| `gcp-config`: VPC + example VM, and their `us-central1` region | Now a standalone decision, not forced. Untouched in PR #1 |

## After the PRs land

1. Tag `terraform-modules` **`v0.2.0`**, then repoint both consumers — each should plan clean, given the byte-identical copies.
2. Delete the `PLATFORM_CI_APP_ID` shadow and `gh_app_owner: gfs-sre` from both repos.
3. Trim `terraform-runner`'s roles in `gcp-config` (`resourcemanager.projectIamAdmin` makes it owner-equivalent) and move its WIF binding out of its own state.

## Links

- Audit of `gcp-config`, internal: [[Explainers/2026-08-26-gcp-config-antipattern-audit|antipattern audit]]
- Tech-services review + progress: [[Bifrost/Tech Services IaC Review/Overview|Overview]] · [[Bifrost/Tech Services IaC Review/Remediation State|Remediation State]]
- IAM coexistence with SRE's authoritative model: [[Bifrost/SRE Terraform Framework — Bifrost Coexistence|SRE Terraform Framework — Bifrost Coexistence]]
