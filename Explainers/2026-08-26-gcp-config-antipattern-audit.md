---
tags: [explain, audit, terraform, gcp, ilg-platform]
date: '2026-08-26'
repo: https://github.com/ilg-platform/gcp-config
audited_sha: 1dee969
title: ilg-platform/gcp-config — antipattern audit
thesis: "gcp-config at 1dee969 gave an owner-equivalent runner an unreviewed auto-apply. PR #1 gated the pipeline, but the privilege findings F1-F3 and the scope finding F18 are still open."
confidence: high
---
# gcp-config audit: owner-equivalent runner, now behind a gated apply

```orient-bluf
{
  "v": 1,
  "bluf": "gcp-config at 1dee969 gave an owner-equivalent runner an unreviewed auto-apply. PR #1 gated the pipeline, but the privilege findings F1-F3 and the scope finding F18 are still open.",
  "confidence": "high",
  "action": "Strip terraform-runner to the roles this stack needs, move its WIF binding out of its own stack, and branch-protect main."
}
```

## Situation

- **CONFIRMED** The audit covers `ilg-platform/gcp-config` at `1dee969` (2026-08-24): 5 commits, 17 files, about 1,100 lines. Every finding is against code and live GitHub settings, not the READMEs. [1]
- **CONFIRMED** The repo stands up project `ilg-platform-ec02` with WIF-based CI, `deletion_policy = PREVENT`, the default SA disabled and no SA keys in CI. Everything else works against the goal of "a bare project we manage ourselves".
- **CONFIRMED** PR #1 merged on 2026-08-27 and moved the repo onto Terragrunt and the ilg-platform workflows. Its plan read `No changes. Your infrastructure matches the configuration.` [9]
- **CONFIRMED** Statuses below are re-read at `64ab88c` (2026-09-16, current `main`). [10][11][12][13][14]
- **CONFIRMED** The intent is careful, but the privilege model and pipeline gates do not match it. Done right: WIF in CI, `PREVENT`, IAP-only SSH, shielded VM, committed lockfile, `fmt` and `validate` in CI, plan posted to PRs.

## Assessment

### Findings, ranked

**ASSESSED** Severity key: Red means fix before real use, Amber means fix soon, Yellow means hygiene. Status is at `64ab88c` unless marked.

| ID | Sev | Finding | Status |
|---|---|---|---|
| F1 | Red | `terraform-runner` is owner-equivalent, labelled least-privilege | Open, wider: roleAdmin and wifPoolAdmin added [10][11] |
| F2 | Red | The runner's stack manages its own WIF trust binding | Open: binding still in `main.tf`, second one in `workload-identity.tf` [10][11] |
| F3 | Red | Project-scoped SA has write on the shared state bucket | Open: backend still `gfs-terraform-core-tfstate`; own bucket exists but unused [10][13] |
| F7 | Red | Unreviewed auto-apply on push to `main` | Mostly closed by PR #1: `terraform-prod` gate; `main` still unprotected [5][9][14] |
| F9 | Red | Nothing is pinned | Mostly closed: tags, `~> 7.45`, no `run.sh`; tags are rolling [10][17][18] |
| F4 | Amber | `elevated`/`stack` provider split is fiction in CI | Open: aliases still in `providers.tf` [12] |
| F5 | Amber | Ownership inverted: owners hold `viewer`, SRE holds the runner | Open; more grants added since [10] |
| F8 | Amber | Apply re-plans instead of applying the reviewed plan | UNKNOWN: workflow changed to `terragrunt.yaml` |
| F12 | Amber | Seven org folder IDs hard-coded twice | Open [10] |
| F13 | Amber | Reads `terraform-core` remote state for two scalars | Open [19] |
| F18 | Amber | Built the example stack, not the request (VPC, VM, `us-central1`) | Open: VPC and VM modules remain; region default unchanged [10][18] |
| F19 | Amber | `run.sh` can discard work in a sibling clone | Closed: `run.sh` deleted [9] |
| F20 | Amber | Local `apply` is auto-approved; `--local` splits state | Closed: `run.sh` deleted [9] |
| F22 | Amber | Docs are a stale, contradictory work log | Closed per PR #1: HANDOFF deleted, README rewritten [9] |
| F6 | Yellow | SA-key inputs designed in | Open: `*_sa_credentials` variables remain [12][18] |
| F10 | Yellow | Checkov allow-list runs 3 of about 150 checks | Closed: config removed, Trivy scan reports to secops [9] |
| F11 | Yellow | Workflow `paths` filter skips scanner config and scripts | Superseded: workflows replaced; not re-checked |
| F14 | Yellow | Variable defaults duplicate `envs/main.tfvars` | Not re-checked |
| F15 | Yellow | Live project ID exists nowhere in code | Not re-checked |
| F16 | Yellow | Dead output exposes the disabled default SA | Not re-checked |
| F17 | Yellow | Two locals test one variable inconsistently | Open: locals unchanged [12] |
| F21 | Yellow | Generated `backend.tf` dance | Closed: `root.hcl` generates the backend [9][13] |
| F23 | Amber | New: Terragrunt needs `storage.buckets.get`, Terraform does not | Resolved by a plain `generate "backend"` block [9][13] |

**ASSESSED** Fix priority from the audit, with the findings each fix closes:

| # | Fix | Closes |
|---|---|---|
| 1 | Branch-protect `main`, require a PR and one review, gate apply behind an environment | F7, F8 in part |
| 2 | Pin module refs, workflow and providers (`~> 7.45`); drop `init -upgrade` | F9 |
| 3 | Remove `projectIamAdmin`, `serviceAccountAdmin`, `iap.admin`; move the WIF binding to `terraform-core`; scope or separate state | F1, F2, F3 |
| 4 | Delete the VPC and VM; give `ilg-platform/github-actions` an SA and WIF binding; agree repo ownership | F18, F5 |
| 5 | One identity per run; drop the aliases and key variables | F4, F6, F17 |
| 6 | `run.sh`: remove the framework-clone sync, `--local` and apply auto-approve | F19, F20, F21 |
| 7 | `.checkov.yaml` to `skip-check:`; widen `paths:` | F10, F11 |
| 8 | Folder IDs from `terraform-core` or a data source; drop dead defaults and outputs | F12 to F16 |
| 9 | Rewrite README as current state; move HANDOFF into the ticket | F22 |

**ASSESSED** Raise two items upstream on `gfs-sre/terraform-framework`: apply the saved plan (F8), and the `us-central1` default every derived repo inherits.

### Identity and privilege

- **CONFIRMED** F1: `terraform/main.tf:64-109` grants editor, `iam.serviceAccountAdmin`, `resourcemanager.projectIamAdmin` and `iap.admin`. `projectIamAdmin` alone lets the SA grant `roles/owner`. [1]
- **CONFIRMED** F1 detail: the editor comment misses that the three added roles, not editor, make the runner dangerous. "This one project" includes minting new owners. [1]
- **CONFIRMED** F2: `terraform_runner_wif` (`main.tf:113-119`) runs in the stack CI executes as `terraform-runner`. The identity CI assumes decides who may assume it. [2]
- **ASSESSED** F2 detail: one push changing `var.github_repository`, or widening the `principalSet` to the pool, applies unseen. The binding belongs in the framework's `terraform-core`.
- **CONFIRMED** F3: the runner holds `objectAdmin` on `gfs-terraform-core-tfstate`, because prefixes are not an IAM boundary. Every other stack's state, with any secrets in outputs, is readable and writable. [3]
- **ASSESSED** F3 detail: the cross-tenant blast radius hides behind the "project-scoped" framing. Fix with a per-stack bucket or IAM Conditions on the object prefix.
- **CONFIRMED** F4: in CI the workflow sets no `TF_VAR_*`, so both `impersonate_service_account` values are null and both aliases are the runner. Every `google.elevated` resource, including `module.gcp_project`, runs project-scoped. [4]
- **CONFIRMED** F4 detail: locally `run.sh` defaults the elevated impersonation to the org-wide `project-factory-6046`. Nothing sets the stack variable, so every local VM plan runs as an org-level principal. The README's "stack prefers terraform-runner" describes code that does not exist. [4]
- **CONFIRMED** F5: `platform-engineering@` holds `roles/viewer`. `group:sre@gfsdeliver.com` can impersonate the runner (`main.tf:121-129`), so it is effectively owner. [1]
- **CONFIRMED** F5 detail: no identity or WIF binding exists for `ilg-platform/github-actions`, which the README says will manage further resources. The stated hand-off is impossible as delivered, and two Terraform roots would own one project. [1]
- **CONFIRMED** F6: `elevated_sa_credentials` and `stack_sa_credentials` accept JSON keys. `.checkov.yaml` enables `CKV2_GCP_5` (no key creation) while the providers invite key use. Remove the variables. [8]

### Delivery pipeline

- **CONFIRMED** F7: at audit, `main` had no protection (`GET .../branches/main/protection` returned 404, `rulesets` returned `[]`). The SRE workflow applied `-auto-approve` on push with no environment gate. No PR had ever existed. [5]
- **CONFIRMED** F7 detail: runs 32768915100 to 32770463067 were three red applies fixed by three more pushes to `main`. That is debugging in production. [6]
- **CONFIRMED** F7 now: the `terraform-prod` environment gates apply. The same API checks still return 404 and `[]` on 2026-10-12. [5][14]
- **ASSESSED** F8: the inherited workflow ran a fresh `plan` and `apply` at merge, so anything that moved since the PR plan applied unseen. Fix with `plan -out` plus `apply <planfile>`, or an approval that shows the merge-time plan.
- **UNKNOWN** F8 now: this pass did not read the new `terragrunt.yaml` to see whether it applies a saved plan.
- **CONFIRMED** F9: at audit, modules were `?ref=main` (`main.tf:23,133,156`), the workflow was `@main`, and `versions.tf` allowed `>= 5.41` while the lockfile held 7.45.0. `run.sh` ran `init -upgrade` every time. [7]
- **ASSESSED** F9 detail: a renamed resource address in `modules/gcp-project` would plan as destroy-and-recreate on a `PREVENT` project. F7 meant nobody saw it first.
- **CONFIRMED** F9 now: the workflow is `@0.1-affogato`, providers are `~> 7.45`, and modules come from `ilg-platform/terraform-modules` at `?ref=0.1-affogato`. [10][14]
- **ASSESSED** F9 caveat: `0.1-affogato` is a rolling tag, so a compatible change still moves it silently. The switch from `gfs-sre` modules most likely landed in PR #2.
- **CONFIRMED** F10: `.checkov.yaml` used `check:`, an allow-list, so 3 of about 150 GCP checks ran. Two were `#checkov:skip`'d on the resources they exist to catch. `projectIamAdmin` and `iap.admin` are not primitive roles, so they pass. [8]
- **CONFIRMED** F11: the workflow `paths` filter excluded `.checkov.yaml`, `run.sh` and `mise.toml`, so editing them triggered no CI. [7]

### Terraform shape

- **CONFIRMED** F12: `main.tf:8-16` embeds seven numeric folder IDs, and `variables.tf:31` repeats the seven names as a validation list. Two sources of truth; use a data lookup or a `terraform-core` output. [1]
- **CONFIRMED** F13: `data.tf` reads `terraform-core` remote state for `org_id` and `billing_account`. Every planner needs read on the bootstrap bucket. Two constants in `main.tfvars` would do. [19]
- **CONFIRMED** F14: `variables.tf` defaults `project_name`, `folder_name`, `group_name` and `group_role`, and tfvars sets the same values. With one environment the `envs/` layout is ceremony.
- **CONFIRMED** F15: `random_project_id = true` means `ilg-platform-ec02` appears only in state and the README. `var.project_id = "ilg-platform"` reads like the ID. Rename it `project_id_prefix` or document it.
- **CONFIRMED** F16: `output "service_account_email"` exposes the disabled default SA. It is a dead output.
- **CONFIRMED** F17: `stack_provider_credentials` tests `!= null && != ""`; `stack_impersonate_service_account` tests only `!= null`. An empty-string key disables impersonation and passes null credentials. [12]

### Scope and local tooling

- **CONFIRMED** F18: the ask was "a bare project… we'd like to manage the project configuration and resources ourselves". The repo also built a VPC, subnet, two firewall rules and a running `e2-small` (about $13/month, idle). [1]
- **CONFIRMED** F18 detail: `os_login.ssh_users` hard-codes one individual's email (`main.tf:175`). Region defaults to `us-central1` for a UK estate on `europe-west2`. All are `terraform-framework-example-stack` leftovers.
- **CONFIRMED** F18 now: the VPC and VM modules remain, from `ilg-platform/terraform-modules`. The `us-central1` defaults remain. [10][18]
- **CONFIRMED** F19: `sync_terraform_framework_repo` (`run.sh:44-81`) ran `checkout` and `reset --hard` in `../terraform-framework`. Its `git status --porcelain` guard misses committed-but-unpushed work. It existed to fetch one constant already vendored in `shared-config/`. [4]
- **CONFIRMED** F20: `run.sh:176` applied without review while destroy asked. `--local` deleted `backend.tf` and created a second state file against the live project. [4]
- **CONFIRMED** F21: `.gitignore` ignored `backend.tf`, and `run.sh` and CI copied it from `backend.gcs.tf.example`. Committing `backend "gcs" {}` with `-backend-config` was enough.
- **CONFIRMED** F22: HANDOFF's "Original request (superseded)" contradicted the live status block. README described an unimplemented `stack` identity flow and called F1 least-privilege. Both carried Slack-nudge timelines, personal names, and `.tf` comments naming people.

### Gaps against the ilg-platform directives

**ASSESSED** The headline gap is structural. `gcp-config` is a `gfs-sre/terraform-framework` stack in the `ilg-platform` org, so it follows none of the org conventions. It also fulfils, and then competes with, the project `ilg-platform/core` has been waiting for. Sources are in [15][16].

| Directive | ilg-platform standard | As built at 1dee969 | Gap and status now |
|---|---|---|---|
| Where the platform project's config lives | `ilg-platform/core`; its `root.hcl` carries `TODO-platform-*` placeholders awaiting this project | Same project in a separate repo with a different state bucket; still manages VPC, VM, IAM | Red. Two roots for one project; `core` still says it does not exist. Open |
| Orchestration | Terragrunt; `root.hcl` generates backend and providers; terraform 1.9.0, terragrunt 0.50.8 | Raw Terraform, hand-written `providers.tf`, 185-line `run.sh`, terraform 1.14.9 | Amber. Closed by PR #1 except the 1.14.9 pin, forced by the state's writer version |
| Layout | `iac/env/*.tfvars` plus `iac/projects/<name>/` | `terraform/` flat root, `envs/main.tfvars`, prefix `stacks/ilg-platform/main` | Yellow. Layout closed; prefix unchanged |
| Provider pinning | `~> 6.41` | `>= 5.41`, lockfile 7.45.0 | Amber. Now `~> 7.45`, one major ahead of the fleet |
| Shared modules | `ilg-platform/terraform-modules` by tag; raise gaps rather than fork | `gfs-sre/terraform-framework` at `?ref=main`; no org module existed for project, VPC or IAM | Red. Now `ilg-platform/terraform-modules` at `0.1-affogato` |
| CI rails | `github-actions@0.1-affogato`, WIF, GitHub-App fetch, `environment_name` | SRE reusable workflow `@main`, its own App (id 3896251) and WIF pool | Red. Closed by PR #1 (see the correction below) |
| Apply gating | Every prod apply gated by `terraform-prod`; ungated apply is the named failure mode | Push-to-`main` `-auto-approve` | Red. Closed by the gate; branch protection still absent |
| Plan on PR | `tf-plan-pr.yaml` on every `.tf`/`.hcl` PR | Mechanism present, no PR ever opened | Amber. Closed |
| Auth | WIF only; trust anchor is the `core-infra` pool | WIF on SRE's pool; key variables; self-managed binding | Amber. Open: own pool created, key variables remain |
| State | Per-estate bucket, per-project prefix | Shared SRE bucket with unconditional `objectAdmin` | Red. Open (F3) |
| Region | `europe-west2` everywhere | `us-central1` defaults | Amber. Open |
| Labels | `default_labels = {project, env, build}`, `github_sha` | `{stack, managed-by}` on two resources | Yellow. Not re-checked |
| Secops | `secops.yaml` reporting to `secops-reporting` | Inline gitleaks plus 3-check checkov; reports go nowhere | Amber. Closed: `secops.yaml` added |
| Repo hygiene | `CLAUDE.md`, PR template, current-state README | None; README plus HANDOFF log | Yellow. HANDOFF gone; no `CLAUDE.md` at repo root on 2026-10-12 |
| IAM ownership | Additive member grants; `core-infra` owns WIF; coexistence advice: drop `projectIamAdmin` from SRE runners | Runner with the F1 role set, SRE as token creator, owners as `viewer` | Red. Open (F1, F5) |

- **ASSESSED** Decide the seam: `gcp-config` is project birth plus a deployer SA plus a state bucket, exported as outputs. `core` owns everything inside the project, on Terragrunt, gated by `terraform-prod`. Then delete the VPC and VM.
- **ASSESSED** Two platform gaps are ours to close: `github-actions` has no raw-`terraform.yaml` reusable, and `terraform-modules` had no project, VPC or IAM module. The 2026-07-29 coexistence doc lists both. [15]
- **ASSESSED** The mechanical items (pins, region, labels, layout, secops, `CLAUDE.md`) are pointless until the team decides the seam. Half of them land in a repo that should shrink to about 40 lines.

### Migration plan and what ran

- **CONFIRMED** The plan called the move to Terragrunt and `ilg-platform/github-actions` feasible. The project exists under `PREVENT`, so it is a state migration, not a rebuild. [9]
- **ASSESSED** The plan set five decisions and five phases, tabled below. Status is at `64ab88c`. [9][10][13]

| Item | Plan | Status |
|---|---|---|
| D1 | Remove `module.gcp_project` from state with `removed {}`; SRE's `terraform-core` owns project birth | Not done |
| D2 | Rails migration in `gcp-config` first, fold into `core` later | Rails done; fold-in not done |
| D3 | Delete the VPC and VM before migrating | Not done |
| D4 | Keep and trim `terraform-runner` once its WIF binding moves out | Not done; roles widened |
| D5 | New `ilg-platform-tfstate` bucket in `europe-west2`, later `core`'s bucket too | Bucket exists; backend not repointed |
| P0 | Branch protection; pin refs to SHAs; destroy VPC and VM; add state bucket and `core-infra` binding | Pins and bucket done; rest open |
| P1 | `iac/` layout, `moved {}` and `removed {}`, four workflows, `CLAUDE.md`, README rewrite | Done in PR #1, except `CLAUDE.md` |
| P2 | Pull and push state, then a zero-diff plan | Not done |
| P3 | SRE removes the repo from `github_repositories_extra`, revokes grants; ownership agreed in writing | UNKNOWN |
| P4 | Fold into `core` | Not started |

- **ASSESSED** Risks: the 7-to-6 provider downgrade needs a zero-diff plan first. A stale SRE clone could recreate the project after `removed {}`. Terragrunt 0.50.8 needs `location` in `root.hcl`. Frame the work as the README's own hand-off, with Wolf.
- **ASSESSED** Effort: P0 half a day, P1 one day, P2 two hours with SRE on call, P4 half a day. No new workflow or module needed.
- **CONFIRMED** What ran: PR #1 (`hjf/terragrunt-platform-structure`, +383/-779, 28 files) covered Terragrunt, the platform structure and the reusable workflows, keeping the existing backend. [9]
- **CONFIRMED** Not done: D1 (`main.tf` still holds `gcp_project`), D3 (VPC and VM remain), P2 (backend is still the SRE bucket). A state bucket now exists in the project. [10][13]
- **CONFIRMED** An initial attempt went straight to `main`, applied, and was fully reverted at Harry's call. The revert matched `1dee969` byte for byte. One transient failure: the `iap.admin` re-grant had not propagated when the IAP tunnel call fired; a re-run cleared it. [9]
- **CONFIRMED** Landed: `iac/env/`, `iac/projects/root.hcl`, split `.tf` files and `moved.tf`. Deleted: `run.sh`, `shared-config/`, `HANDOFF.md`, `.checkov.yaml`, the SRE workflow. Added: `deploy`, `tf-plan-pr`, `manual-deploy`, `secops` workflows and the `terraform-prod` environment with a required reviewer. [9][14]

### Correction and new finding from PR #1

- **CONFIRMED** An intermediate revision inlined the public `project-factory` module and deleted the VPC and VM. Its reasoning: the ilg-platform CI App cannot read a `gfs-sre` repo. Harry corrected it: consuming the framework was then invariant. [9]
- **CONFIRMED** `terragrunt.yaml` parameterises the app id and `gh_app_owner`. Setting `PLATFORM_CI_APP_ID = 3896251`, passing the framework key and `gh_app_owner: gfs-sre` made the cross-org fetch work. The plan then showed no changes after refreshing all 21 resources. [9]
- **ASSESSED** That invariant has since moved: modules now come from `ilg-platform/terraform-modules`. The lesson stands: check the workflow's parameters before redesigning around an unreachable dependency. [10]
- **CONFIRMED** Residual platform gap: `terragrunt.yaml` mints its module token for one `gh_app_owner`. A repo needing both `gfs-sre` and `ilg-platform` modules cannot have both in one run. [9]
- **CONFIRMED** F23: Terragrunt calls `storage.buckets.get` whenever it manages a backend, even with `skip_bucket_creation = true`. The runner holds only `objectAdmin`, so it got a 403. Raw Terraform's GCS backend never makes that call. [9]
- **CONFIRMED** The fix: `root.hcl` emits the backend with a plain `generate "backend"` block, not `remote_state`. `generate` makes no GCS call. The template pairs `generate` with `remote_state`, which would still 403 here. [13]
- **CONFIRMED** This still upgrades F3 less sharply: `root.hcl` owns the backend, but the prefix stays `stacks/ilg-platform/main` and the cross-tenant bucket remains. [13]
- **ASSESSED** Moving state into the project closes both. Terragrunt 0.50.8 would then need `project` and `location` in the `remote_state` block, and the project had `storage.googleapis.com` disabled.
- **CONFIRMED** Still open at PR #1: F1 to F6, F12, F13 and F18. Also open: terraform 1.14.9 against the fleet's 1.9.0, `us-central1`, CI on the SRE WIF pool, no branch protection. Some have moved since. [9][10]

## Open items

| Item | Owner | By |
|---|---|---|
| Strip `projectIamAdmin`, `serviceAccountAdmin`, `iap.admin` from the runner; move its WIF binding out of its own stack (F1, F2) | Harry with SRE | unscheduled |
| Repoint the backend to the in-project bucket (F3, F23) | Harry | unscheduled |
| Branch-protect `main` and require a PR (F7) | Harry | unscheduled |
| Decide D1 and D3: project ownership and VPC/VM removal (F18) | Harry | unscheduled |
| Collapse the `elevated`/`stack` aliases and drop key variables (F4, F6, F17) | Harry | unscheduled |
| Re-check F8, F11, F14-F16 and labels against current `main` | Harry | unscheduled |

## Evidence

```orient-evidence
{
  "v": 1,
  "items": [
    { "id": 1, "kind": "code", "ref": "terraform/main.tf@1dee969:L64-129", "note": "runner roles, own WIF binding, SRE impersonation, folder IDs, VM email (cited lines per finding)" },
    { "id": 2, "kind": "code", "ref": "terraform/main.tf@1dee969:L113-119", "note": "terraform_runner_wif binding" },
    { "id": 3, "kind": "doc", "ref": "gcp-config README section CI at 1dee969", "note": "objectAdmin on gfs-terraform-core-tfstate" },
    { "id": 4, "kind": "code", "ref": "terraform/providers.tf@1dee969", "note": "elevated and stack providers; run.sh L44-81 and L165-176 carried F19, F20 and the init -upgrade" },
    { "id": 5, "kind": "log", "ref": "gh api repos/ilg-platform/gcp-config/branches/main/protection returned 404; .../rulesets returned []", "note": "at audit and again 2026-10-12" },
    { "id": 6, "kind": "log", "ref": "GitHub Actions runs 32768915100 to 32770463067", "note": "three consecutive red applies" },
    { "id": 7, "kind": "code", "ref": "terraform/versions.tf@1dee969", "note": "open provider floors; main.tf L23,133,156 and terraform.yml L23 carried the main refs" },
    { "id": 8, "kind": "doc", "ref": ".checkov.yaml at 1dee969", "note": "check: allow-list, CKV2_GCP_5, skips" },
    { "id": 9, "kind": "pr", "ref": "ilg-platform/gcp-config#1", "note": "Terragrunt move, plan evidence, revert, correction, F23" },
    { "id": 10, "kind": "code", "ref": "iac/projects/gcp-config/main.tf@64ab88c", "note": "current roles, WIF binding, module sources, VPC and VM, folder IDs" },
    { "id": 11, "kind": "code", "ref": "iac/projects/gcp-config/workload-identity.tf@64ab88c", "note": "in-project WIF pool, wifPoolAdmin role" },
    { "id": 12, "kind": "code", "ref": "iac/projects/gcp-config/providers.tf@64ab88c", "note": "aliases and credential locals" },
    { "id": 13, "kind": "code", "ref": "iac/projects/root.hcl@64ab88c", "note": "generate backend block, SRE bucket and prefix" },
    { "id": 14, "kind": "code", "ref": ".github/workflows/deploy.yaml@64ab88c", "note": "terragrunt.yaml@0.1-affogato, environment_name terraform-prod" },
    { "id": 15, "kind": "doc", "ref": "Bifrost/SRE Terraform Framework — Bifrost Coexistence", "note": "2026-07-29 coexistence analysis" },
    { "id": 16, "kind": "doc", "ref": "ilg-platform/core and ilg-platform/terraform-template CLAUDE.md", "note": "org Terraform conventions" },
    { "id": 17, "kind": "pr", "ref": "ilg-platform/gcp-config#2", "note": "moves pointers to immutable tags" },
    { "id": 18, "kind": "code", "ref": "iac/projects/gcp-config/variables.tf@64ab88c", "note": "us-central1 defaults, SA credential variables" },
    { "id": 19, "kind": "code", "ref": "iac/projects/gcp-config/data.tf@64ab88c", "note": "terraform_remote_state read of terraform-core" }
  ]
}
```
