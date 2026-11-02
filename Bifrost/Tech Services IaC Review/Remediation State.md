---
title: Tech Services IaC — Remediation State
status: not-started
owner: Harry Fitzgerald
created: '2026-07-25'
updated: '2026-08-26'
tags: [bifrost, ilg-tech-services, terraform, iac, security-review, remediation-state]
---

# Tech Services IaC — Remediation State

> **Single source of truth for progress.** Update Status as fixes land; keep artifact links current. Move superseded notes to the Decision Log — don't delete.

Context + rationale: [[Bifrost/Tech Services IaC Review/Overview|Overview]]
Review: https://claude.ai/code/artifact/bd5179bc-0bae-4267-ab3c-131fcb0deacd · Migration plan: https://claude.ai/code/artifact/5d821b2c-b823-4637-9654-228e133d8eb6

**Repo:** `~/code/tech-services` (= `ilg-tech-services/ilg-tech-services-iac`, default branch `main`, Terraform in `terraform/`)
**Framework it depends on:** `~/code/terraform-framework` (= `gfs-sre/terraform-framework`)
**GCP project:** `ilg-tech-services-tools-1525` · region `europe-west2` · state `stacks/ilg-tech-services/mono` in `gfs-terraform-core-tfstate` (EU)

## Status: IN PROGRESS — Steps 2 and 5 have open PRs

Review complete 2026-07-25. Remediation began 2026-08-26 with two PRs, both **open, unmerged and unreviewed** — see [[Bifrost/Platform Terraform Alignment/Overview|Platform Terraform Alignment]] for the cross-repo picture (it also covers `ilg-platform/gcp-config`, which is outside this review's scope).

- [ilg-tech-services-iac#45](https://github.com/ilg-tech-services/ilg-tech-services-iac/pull/45) — Terragrunt + platform workflows (Step 5, and part of Step 2)
- [ilg-platform/terraform-modules#2](https://github.com/ilg-platform/terraform-modules/pull/2) — the six feature-branch modules + five shared ones promoted (Step 2)

Findings still have not been shared with the contributors or the Tech Services team; Harry introduces the PRs in Slack himself.

⬜ not started · 🟨 in progress · ✅ done · ⛔ blocked · ⏸ deferred · ❌ won't do

## Step 1 — stop the bleeding (hours, mostly repo settings; do NOT wait for the migration)

- [ ] ⬜ **Protect `main`** — currently no protection and no rulesets; require a PR + 1 approval
- [ ] ⬜ **Gate applies on a GitHub environment** with required reviewers (fleet norm is `terraform-prod`; this repo has no environments at all)
      → **prefer extending `gfs-bifrost/github-config`** to this org rather than clicking settings — it already manages `github_branch_protection` + `github_repository_environment` + teams in Terraform (currently `owner = "gfs-bifrost"` only)
- [ ] ⬜ **Ref-scope both WIF principalSets** — add `attribute.ref`/environment to `terraform-runner` (`main.tf:78`) and `deploy-sa` (`iam.tf:115-123`); repo-scoping alone lets any branch/PR mint the credential
- [ ] ⬜ **Drop `secretmanager.secretAccessor` from `deploy-sa`** (`mono.tfvars:31-38`) — Cloud Run resolves `secret_env` as the *runtime* SA, so this grant only lets CI logs dump every project secret
- [ ] ⛔ **HOLD the org-wide deploy-WIF widening** (open PR #9, branch `hjf/org-scoped-deploy-wif`) until H3 is fixed — it turns "one named repo's CI can take over the project" into "any repo anyone creates in the org can". Reasonable *after* the scoping fix, risky before.

## Step 2 — restore reviewability (a day)

- [x] 🟨 **Decide first: re-home the 6 modules into `ilg-platform/terraform-modules`?** → **decided: promote.** Done in [terraform-modules#2](https://github.com/ilg-platform/terraform-modules/pull/2) — 11 modules, byte-identical, `gcp-serverless-lb`→`networking/load-balancer` and `gcp-vpc-access-connector`→`networking/vpc-connector` fill the two placeholders exactly as anticipated. Awaiting review. LB + VPC-connector fill existing `.keep` placeholders; IAP/DNS/NAT/cloud-run-shape are new catalogue entries. Deciding *now* means pinning once to the right place instead of twice. (Cloud Run itself should just switch to the released `//compute/cloud-run@v0.1.0`.)
- [x] 🟨 **~~Land `feat/ilg-tech-services-modules`~~ superseded** — the modules are promoted instead, so nothing needs landing on the framework's branch. Verified the branch is **purely additive**: its copies of the five shared modules are byte-identical to `development`. Tag `v0.2.0` on `terraform-modules` once #2 merges. (The convention — exact semver for modules, rolling tags for workflows — is now written down in that repo's README + CLAUDE.md.)
- [ ] ⬜ **Pin all 10 module `?ref=`s** to that tag (6 on the feature branch, 4 on `development`)
- [x] 🟨 **Pin the CI `uses:`** off `@development` → #45 deletes that workflow outright and moves to `ilg-platform/github-actions@0.2-bonbon`
- [x] 🟨 **Fix `.checkov.yaml`** → **decided: Trivy-only.** #45 deletes it as dead config once the framework pipeline goes. Consequence flagged in the PR: `CKV_*` coverage stops, gitleaks + Trivy remain. Re-implementing the primitive-roles policy belongs upstream in `secops-terraform.yaml`, not per-repo.

## Step 3 — reduce identity blast radius (a few days)

- [ ] ⬜ Split plan (read-only) from apply; take `projectIamAdmin` out of the auto-computed set (`iam.tf:19-22`)
- [ ] ⬜ Per-service runtime SAs with **per-secret** `secretAccessor` (currently one `runtime-sa` for all 4 services, project-wide access — `cloud_run.tf:20`)
- [ ] ⬜ Replace project-wide `run.admin` on `deploy-sa` with per-service `run.developer`
- [ ] ⬜ Make `terraform-runner`'s role set **explicit** so widening CI's power is a visible diff line (today adding a human role silently grants it to CI)

## Step 4 — close exposure gaps

- [ ] ⬜ **Remove `allUsers` invoker** from the two public services and confirm the LB→IAP path still serves (the IAP service agent grant at `iap.tf:36-46` should be sufficient); then validate `x-goog-iap-jwt-assertion` in-app
- [ ] ⬜ **SSL policy** — `MODERN` / `min_tls_version = TLS_1_2`; needs a new input on `gcp-serverless-lb` (no TLS floor today ⇒ TLS 1.0). Real deviation: 4 fleet repos already do this
- [ ] ⬜ **Logging** — LB `log_config`, connector-subnet flow logs, NAT `log_config` (no audit trail on the internet-facing or legacy-DB paths)
- [ ] ⬜ **Authoritative** `run.invoker` + IAP bindings (currently additive ⇒ out-of-band `allUsers` is never detected or reverted) + a scheduled plan that fails on non-empty diff
- [ ] ⬜ **Artifact Registry** — `immutable_tags`, a cleanup policy, repo-scoped IAM (tag substitution is currently possible from dev CI)
- [ ] ⬜ Narrow IAP access off `domain:gfsdeliver.com` to a team group; drop the `hello-world-prod` grant (stock demo image, live public surface, no owner)
- [ ] ⬜ Egress firewall + explicit allows to the legacy CIDRs (no firewall rules exist; default internet route intact behind the allowlisted NAT IP)

## Step 5 — adopt Terragrunt (this IS the fix for H7/M7, not an optional follow-up)

**Replace `run.sh`, don't repair it.** It's 100 lines hand-rolling a subset of a professionally maintained tool — backend assembly, state prefixing, var-file wiring, impersonation, and a three-way `shared-config` search — which CI then reimplements independently, so local and CI only coincidentally do the same thing. Terragrunt is already an org dependency (fleet pins 0.50.8, run via `gruntwork-io/terragrunt-action`), so this **deletes** code rather than adding a tool. Hardening the script means investing in a bespoke reimplementation and then throwing it away.

- [x] 🟨 Done in [#45](https://github.com/ilg-tech-services/ilg-tech-services-iac/pull/45), awaiting review. Deletes `run.sh`, `shared-config/`, `backend.gcs.tf.example` as planned; `root.hcl` declares it once. **24 files relocate, 22 byte-identical.** The zero-diff acceptance test is **not yet demonstrated** — the plan job fails at module fetch until repo variable `PLATFORM_CI_APP_ID = 3896251` is set (needs admin; Harry has push only). `terraform validate` passes on both roots locally.
      → `root.hcl` emits the backend with a plain `generate` block, **not** `remote_state`: `remote_state` has Terragrunt manage the bucket, which calls `storage.buckets.get`, and `terraform-runner` holds only `objectAdmin` on `gfs-terraform-core-tfstate`. This is why the old workflow worked and a naive Terragrunt adoption 403s.
      → `vm-provisioner-root` deliberately stays **out** of `iac/projects/`: own bucket, per-VM `vm/<slug>` prefix set at apply time, and `module "vm"` must keep its name or VM state is orphaned.
- [ ] ⬜ Prereq: merge open PRs **#9** (org-scoped WIF — see the HOLD above) and **#10** (secops scans), then update #10's `terraform_scan` path to the new layout
- [ ] ⬜ *Only if this slips:* delete the `--local` flag and commit `backend.tf` — two lines that remove the estate-duplication path. Nothing more on a file scheduled for deletion.

## Open decisions

| Decision | Options | Leaning |
|---|---|---|
| `manual-deploy` semantics for a mono-env stack | branch `apply` (fleet norm) / `plan`-only / omit | **Implemented as a `plan`/`apply` choice input**, with `apply` gated on `terraform-prod`. Revisit if `plan`-only is still preferred |
| ~~Checkov vs Trivy~~ | — | **Resolved 2026-08-26: dropped.** See Step 2 |
| Who owns the remediation | us / the contributors / Tech Services | Undecided — findings not yet shared |
| ~~Re-home the 6 modules?~~ | — | **Resolved 2026-08-26: promoted**, all 11 rather than 6. See Step 2 |
| Document the `gfs-sre` ↔ `ilg-platform` boundary | write it down / leave implicit | Write it down — a newcomer standing up a *project* currently lands in SRE's framework and keeps going there. Cheap fix, prevents recurrence |

## Decision log

- **2026-08-26** — Remediation started as **PRs, not merges**. Wolf owns this territory and there is active relationship-repair work (Oli's steer: lead with the concern and the why, keep it dialogue-y). Nothing merged, nothing self-approved, no reviewer requested; Harry introduces them in Slack. The review artifacts stay internal — the PRs carry the technical driver and open questions, not the findings list.
- **2026-08-26** — Modules **copied verbatim**, byte-identical, rather than tidied on the way across. Keeps consumers' state addresses stable (no `moved` blocks, no-op repoint) *and* reads as a move of Wolf's work rather than a rewrite of it. Both reasons matter.
- **2026-08-26** — Took `main` as canonical for the five shared modules, not `development`. Verified the only differences are a `project_id` non-empty validation and whitespace, and that both consumers pass a non-empty `project_id`. `feat/ilg-tech-services-modules` is purely additive.
- **2026-08-26** — Kept the framework module sources in both structural PRs. Harry: consuming the gfs-sre modules is **invariant**. An earlier revision had inlined the public `project-factory` and deleted the VPC/VM to dodge a cross-org fetch — unnecessary, since `terragrunt.yaml` parameterises both the app id and the owner. Restoring them made the gcp-config migration fully behaviour-neutral.
- **2026-07-25** — Review framed against the ilg-platform model as the ideal state; that model is explicitly **not** under review. Docs excluded (Kyle's), inline code comments included.
- **2026-07-25** — Two audit claims dropped rather than published: silent apply failures (a final `test` step does re-raise) and a 7/3 module-ref split (actually 6/4). Verify before repeating.
- **2026-07-25** — Migration recommended **after** the criticals, not instead of them; state deliberately stays in `gfs-terraform-core-tfstate` so the migration needs zero state operations.
- **2026-07-27** — Capability ledger added on Harry's call: assess what already exists (or is planned) in platform engineering before treating anything as a defect, since the contributor likely wanted to prove themselves and had no map of the estate. Verified: project creation exists **nowhere** in ilg-platform (so using SRE's framework for that layer was right), while LB/VPC-connector are `.keep` placeholders in `terraform-modules` (so that work was wanted, just built in the wrong repo) — hence *promote, don't discard*. Surfaced the two-platform-surface boundary gap as an **org-level** action, not a contribution defect.
- **2026-07-27** — H7 reframed on Harry's call: the finding is *"bespoke reimplementation of a maintained tool"*, with the footguns as evidence — not a list of bugs to patch in `run.sh`. Remedy is **adopt Terragrunt**, since emulating a professionally maintained tool by hand is the actual bad practice. Interim mitigation capped at two lines (`--local` removal + commit `backend.tf`). Artifacts updated.

## Related, deliberately out of scope

**Platform-side, not this contribution:** `core-infra`'s deployer SAs are trusted by `attribute.repository_owner` across **three whole orgs** (`gfs-bifrost`, `ilg-platform`, `ilg-tech-services`) — see `~/code/fuse/core-infra/iac/projects/core-infra/workload-identity.tf` + `iac/env/global.tfvars`, verified against current `origin/master`. So any repo in any of those orgs can impersonate the dev/prod deployer SAs. Same ref-scoping class as C2 above. Kept out of the review artifact because it's ours, not theirs — but worth its own look.

**Also noted:** the ilg-platform `repo-template`'s own `secops.yaml` references two workflows that 404 on `main` and omits the terraform scan; and its generated backend lacks the terragrunt `location` key that broke dedupe's prod apply. Copy `dedupe-service`'s secops config, not the template's.
