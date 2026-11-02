---
title: Tech Services IaC — Review & Migration (Overview)
status: review-complete
verdict: three-criticals-block-further-change
owner: Harry Fitzgerald
created: '2026-07-25'
updated: '2026-07-27'
tags: [bifrost, ilg-tech-services, terraform, iac, security-review, platform]
---

# Tech Services IaC — Review & Migration (Overview)

Review of **`ilg-tech-services/ilg-tech-services-iac`** — an **external contribution** (20 of 28 commits from an outside address) that stands up the Tech Services Tools GCP project. It was built on `gfs-sre/terraform-framework`'s "legacy stack" wrapper instead of the **ilg-platform deployment model** the org otherwise follows.

Two deliverables: a **review** (what's wrong) and a **migration plan** (how to get onto the standard). As of 2026-07-25 both are complete; **no remediation work has started**.

Progress lives in [[Bifrost/Tech Services IaC Review/Remediation State|Remediation State]] — read that before acting.

## Deliverables

- **Review — issues, risks, bad practice, security** → https://claude.ai/code/artifact/bd5179bc-0bae-4267-ab3c-131fcb0deacd
- **Migration plan — onto the ilg-platform Terragrunt model** → https://claude.ai/code/artifact/5d821b2c-b823-4637-9654-228e133d8eb6

## Scope and yardstick

- **Subject:** this repo's Terraform, `run.sh`, and workflows only.
- **Yardstick:** the ilg-platform / gfs-bifrost model, which is *not* under review — we're happy in that world.
- **Excluded:** prose documentation (Kyle's contribution, deliberately not reviewed). Inline *code* comments stay in scope — two of them assert security properties the code does not have.
- Every finding was verified first-hand against the working tree, the consumed modules **at their pinned refs**, and the GitHub API. Where the platform model shares a gap it is labelled `absolute gap`, not passed off as a deviation.

## The shape of it

**26 findings: 3 critical, 10 high, 10 medium, 3 low.** 9 disappear on adopting the platform model; 11 need a bespoke fix either way; 6 are gaps the standard doesn't cover either.

The three criticals form one chain — and it is a *trust model* problem, not a syntax one:

1. **CI identity is worse than project-owner.** `iam.tf:19-22` computes `terraform-runner`'s grants as *every role in the human bundle* (15 roles) + `serviceAccountAdmin`. Includes `projectIamAdmin` → it can rewrite the project IAM policy and grant itself `roles/owner`; `secretmanager.admin` → reads every secret payload; `logging.admin` → can delete the evidence.
2. **That credential is mintable from any branch or PR.** WIF principalSet is scoped by `attribute.repository` only — no ref/environment (`main.tf:78`). Workflow grants `id-token: write` on `pull_request` **and has its own path in the trigger filter**, so a PR that rewrites the workflow runs with live credentials pre-review. Verified: `main` has **no branch protection, no rulesets, no environments** (cf. dedupe-service / config-service / fapi — all protected + `terraform-dev`/`terraform-prod`).
3. **Live infra has no mainline source.** `development` holds only 5 modules; Cloud Run, LB, IAP, DNS, VPC connector and Cloud NAT exist **only** on unmerged `feat/ilg-tech-services-modules`, re-resolved from branch tip on every apply (the apply job computes a fresh plan — no artifact).

One theme worth naming on its own: **`run.sh` hand-rolls a subset of Terragrunt in 100 lines of bash** (backend assembly, state prefixing, var-file wiring, impersonation, a three-way config search) — which CI then reimplements independently, so local and CI are only coincidentally the same operation. Terragrunt is already an org dependency, so adopting it deletes code rather than adding a tool. The remedy is replacement, not repair: hardening a bespoke reimplementation of a maintained tool is itself the bad practice, and the individual footguns (H7, M7) are the evidence for it.

Highest-value highs: `allUsers` invoker makes **IAP bypassable** once Phase 4 wires the VPC (the inline comment defending it is wrong — that ingress admits VPC traffic, and IAP is enforced at the LB); **one runtime SA** for all services with project-wide secret access, so a dev compromise reads prod secrets; and the **security gate runs 3 checks** — `.checkov.yaml` uses `check:` (an allowlist), and the repo's own `#checkov:skip=CKV_GCP_49` on a `serviceAccountAdmin` grant proves those IDs aren't the primitive-role blockers their comments claim. **Nothing in the pipeline blocks `roles/owner` today** — which is the stated justification for the entire 15-role human bundle.

## Capability ledger — most of this is duplicated work, some isn't

The framing that matters: much of the repo **re-implements capabilities the platform already provides**, built by someone with no map of what existed. The platform's own onboarding guidance says *"Don't write raw `google_*` resources; check the module catalog. If a module doesn't exist yet, raise it in #platform-engineering"*, and `platform-mcp-server` exists to answer "what exists?" — neither reached this contribution. **Discoverability failure on our side, not competence on theirs.**

**Existed already → reuse and delete:**

| Hand-rolled | Already does it |
|---|---|
| `run.sh` (100 lines: backend, state prefix, var-files, impersonation, config search) | **Terragrunt** + `root.hcl` — already an org dependency (fleet pins 0.50.8, `gruntwork-io/terragrunt-action`) |
| Bespoke CI calling SRE's legacy-stack pipeline | `ilg-platform/github-actions//terragrunt.yaml` — plan-on-PR + comment, apply, env gating, Slack, App-token module auth |
| `.checkov.yaml` (3-rule allowlist) | `secops-terraform.yaml` (Trivy + rego bundle + severity gating) and the wider `secops-*` suite |
| Vendored `shared-config/backend.config.hcl` + `backend.gcs.tf.example` | `root.hcl`'s `remote_state` (template even generates `_backend.tf`) |
| Cloud Run module via SRE framework | `ilg-platform/terraform-modules//compute/cloud-run@v0.1.0` — real and released |
| Repo governance by hand (**still undone**: no protection, no envs) | **`gfs-bifrost/github-config`** — manages `github_branch_protection`, `github_repository_environment`, repos, teams in Terraform. Scoped to `gfs-bifrost` today; extend it |
| Per-repo dependency bumping | centralised `renovate-runner` (no per-repo `renovate.json` by design) |

**Didn't exist → building it was legitimate; re-home rather than discard:**

- **GCP project creation / folder placement / WIF pool bootstrap** — *nothing* in ilg-platform does this (code search for `google_project`/project-factory across the org: zero hits). Genuinely `gfs-sre/terraform-framework`'s domain. Reaching for it here was **correct**.
- **Serverless LB + VPC connector modules** — `terraform-modules//networking/load-balancer` and `//networking/vpc-connector` exist as **`.keep` placeholders**: planned, never built. (Same for `secrets/secret`, `storage/gcs-bucket`.) The work is *wanted*; it just landed in the wrong repo.
- **IAP web, Cloud DNS, Cloud NAT modules** — no equivalent and no placeholder; genuinely new ground, and the IAP work corrected a real Google API-deprecation trap.

➡️ **So: don't delete the six modules — promote them into `ilg-platform/terraform-modules`.** Two fill existing placeholders, the rest are new catalogue entries. That turns duplicated effort into the platform contribution it should have been *and* kills this stack's dependency on an unmerged branch in a second framework (critical #3).

⚠️ **Org-level question this exposes (ours, not theirs):** **two platform surfaces with overlapping scope and no documented boundary.** `gfs-sre/terraform-framework` owns project/IAM/WIF; `ilg-platform` owns service deployment, CI, secops, modules. Nothing states where the seam is — so a newcomer standing up a *project* lands in the SRE framework and reasonably keeps going there for everything above it. **This will recur with the next team until the boundary is written down.** Fix is a paragraph in the platform docs.

## How it was built

Two parallel Explore agents (fleet-pattern survey across ~19 gfs-bifrost iac trees + ilg-platform scaffolds; deep security audit of this repo), then every load-bearing claim re-verified by hand. Two claims were **dropped in verification** rather than published: a suspected silent-apply-failure (a final `test "${{ steps.apply.outcome }}" = "success"` step does re-raise it) and an inflated module-ref count (6/4, not 7/3).

## Next

Review step 1 is a few hours of repo settings + IAM scoping and **should not wait for the migration** — see [[Bifrost/Tech Services IaC Review/Remediation State|Remediation State]]. Nothing is owned or scheduled yet; no Jira ticket exists.
