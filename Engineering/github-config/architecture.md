---
tags:
- waypoint
- github-config
verified: '2026-10-13'
verified_sha: f4f97bd
verified_paths:
- README.md
- iac
- .github/workflows
- scripts
- mise.toml
title: github-config — architecture
thesis: One shared repository module, called 37 times from a single project, creates
  each gfs-bifrost repo with fixed settings, environments, admin team and branch protection;
  a push to the default branch plans, then applies behind the terraform-prod environment
  using an org-admin PAT.
confidence: high
---
# github-config — architecture

```orient-bluf
{ "v": 1, "bluf": "One shared repository module, called 37 times from a single project, creates each gfs-bifrost repo with fixed settings, environments, admin team and branch protection; a push to the default branch plans, then applies behind the terraform-prod environment using an org-admin PAT.", "confidence": "high", "action": "Archive repos with archived = true, and plan before editing the module, because a module change fans out to every repo." }
```

## Guardrails

- [policy:G1] Decommission a repo with `archived = true` and keep its module block. Removing the block destroys the resource. The provider then archives it because of `archive_on_destroy`, and the repo leaves state, so nothing manages it.
  — paths: iac/modules/repository/main.tf, iac/modules/repository/variables.tf, iac/projects/bifrost-github-config/main.tf
- [technical:G2] Edits to `iac/modules/repository` apply to all 37 module repos in one run. Read the full plan before merging.
  — paths: iac/modules/repository
- [technical:G3] Pass `admin_teams = [github_team.bifrost_admins.id]` on every live repo. The team's admin grant and the reviewers of the `terraform-dev` and `terraform-prod` environments both come from it.
  — paths: iac/modules/repository/main.tf, iac/projects/bifrost-github-config/main.tf
- [policy:G4] Team membership changes only in `teams.tf`. Every member becomes a repo admin on every managed repo and an approver of every `terraform-prod` deploy.
  — paths: iac/projects/bifrost-github-config/teams.tf
- [policy:G5] This stack governs `gfs-bifrost` only (`owner` in the provider). Do not add an `ilg-platform` repo, and do not re-add `secops-reporting`, which left when it moved orgs.
  — paths: iac/projects/bifrost-github-config/providers.tf, iac/projects/bifrost-github-config/main.tf
- [technical:G6] `required_version` in `providers.tf` and `tf_version` in both workflows must agree (`1.3.0`). `mise.toml` says `latest` for local runs only.
  — paths: iac/projects/bifrost-github-config/providers.tf, .github/workflows/on-pr.yaml, .github/workflows/on-push.yaml, mise.toml

## Layout

**CONFIRMED** One Terragrunt project, `iac/projects/bifrost-github-config`, calls one module. `root.hcl` keeps state in `gfs-bifrost-tfstate` (project `bifrost-dev-global1`) under `<env>/bifrost-github-config`, and loads `env/global.tfvars` and `env/<env>.tfvars` [8]. CI always sets `TF_VAR_env` to `prod` [6][7]. The GitHub provider's `owner` is `gfs-bifrost` and `required_version` is `1.3.0` [10].

```
iac/modules/repository/    the one module every repo uses
  main.tf                  repository, team grant, environments, branch protection
  variables.tf / outputs.tf
iac/projects/bifrost-github-config/
  main.tf                  37 module blocks + the repo-template resource: the real repo list
  teams.tf                 bifrost-admins team and its 11 maintainers
  outputs.tf               repo URLs and team info
  providers.tf / variables.tf / terragrunt.hcl
iac/projects/root.hcl      state bucket, tfvars wiring
scripts/                   clone-org, delete-artifacts (manual helpers)
```

## The repository module

**CONFIRMED** The module is the only way a repo is created here, apart from `repo-template`, a standalone `github_repository` with `is_template = true` [1][3]. It creates five things per repo [1]:

```orient-flow
{ "v": 1, "title": "What one module call creates",
  "nodes": [
    { "id": "call", "label": "module block", "sub": "repo_name, admin_teams, flags", "kind": "step", "ev": [3] },
    { "id": "repo", "label": "github_repository", "sub": "from_template or empty", "kind": "step", "tone": "accent", "ev": [1] },
    { "id": "tpl", "label": "repo-template", "sub": "include_all_branches", "kind": "external", "ev": [1] },
    { "id": "team", "label": "admin team grant", "sub": "bifrost-admins", "kind": "step", "ev": [1] },
    { "id": "env", "label": "terraform-dev, terraform-prod", "sub": "reviewers = admin_teams", "kind": "step", "ev": [1] },
    { "id": "bp", "label": "branch protection", "sub": "default branch", "kind": "step", "ev": [1] }
  ],
  "edges": [
    { "from": "call", "to": "repo" },
    { "from": "tpl", "to": "repo", "label": "9 repos", "style": "dashed" },
    { "from": "repo", "to": "team" },
    { "from": "repo", "to": "env" },
    { "from": "repo", "to": "bp" }
  ] }
```

- **Common settings.** `visibility = "internal"`, `delete_branch_on_merge = true`, `allow_merge_commit = false` with squash and rebase allowed, `vulnerability_alerts = true`, `has_wiki = false`, `has_projects = false`, `has_issues = true` [1].
- **From template** (`disable_template = false`, the default). The repo copies `gfs-bifrost/repo-template` with `include_all_branches = true`. `template` sits in `lifecycle.ignore_changes`, so later template drift does not force consumers back in line. Nine repos use this mode: `fapi`, `shopfiy-app`, `collector`, `core-infra`, `snap-queue-polling-service`, `datadog-integration`, `dedupe-service`, `bifrost-pubsub` and `snap-adapter` [1][3].
- **Empty** (`disable_template = true`). A bare repo with `auto_init = true`. The other 28 modules use it [1][3].
- **Archive.** `archived = true` makes a repo read-only. `archive_on_destroy = true` is set in both modes. The `archived` variable text says removing a block would destroy the repo and its history, which is the guidance to follow [1][2].
- **Pages.** `enable_pages` adds a Pages config on `master` with a workflow build. Only `bifrost-tech` sets it [1][3].
- **Branch protection.** One `github_branch_protection` on the default branch, with `required_status_checks { strict = false }` and `enforce_admins = false`. It lists no check contexts and sets no required reviews [1].

## Team management

**CONFIRMED** `teams.tf` defines `bifrost-admins` (`privacy = "closed"`) and sets 11 usernames, all with role `maintainer` [4]. The module grants that team `admin` on every repo and makes it the reviewer of both environments [1]. `repo-template` gets the same grant through its own resource [3]. Individuals join by a line in the `admins` list [4].

## The repo list: read `main.tf`

**CONFIRMED** At this ref `main.tf` holds 37 module blocks, plus `repo-template`: 38 repos. Eight carry `archived = true`: `order-management-system`, `shopfiy-app`, `llm-analytics`, `fuse-localdev`, `testdata-ui`, `bifrost-lang`, `performance-tests` and `snap-queue-polling-service` [3]. `llm-analytics`, `fuse-localdev`, `testdata-ui`, `bifrost-lang` and `performance-tests` were archived together on 2026-08-18. The `shopfiy-app` block passes no `admin_teams` [3]. The `secops` block was removed on 2026-07-27, when the repo moved to `ilg-platform` [3]. Recent additions are `snap-test-automation`, `fuse-devtools`, `observability`, `pkg-go`, `wms-gateway` and `audit-service` [3][14].

**ASSESSED** This list is the authority on archival, because the flag sets it. It was not cross-checked against GitHub, and a repo archived by hand in the UI would drift from it.

## Known defects

- **CONFIRMED** `outputs.tf:26-29` defines `llm_analytics` as `module.collector.repo_url_http`, which returns the wrong repo's URL [13].
- **CONFIRMED** `scripts/delete-artifacts:24` deletes through `$REPO`, which is never set, so a real run calls a malformed path. Both scripts also read `orgs/gfs-bifrost/repos` without paginating, which returns at most 30 repos per call by default [12].

## Build and deploy

- **CONFIRMED** `on-pr.yaml` runs on `pull_request` when `.tf` or `.hcl` files change. It runs `terragrunt plan` and comments the plan on the PR (`tg_comment: "1"`) [6].
- **CONFIRMED** `on-push.yaml` runs on pushes to `main` or `master`. A `terraform-plan` job runs first, then `terraform-apply` runs `apply -auto-approve` with `environment: terraform-prod` as the approval gate [7].
- **CONFIRMED** Both workflows set `TF_VAR_github_admin_token` from `secrets.GH_TOKEN`. They authenticate to GCP for the state bucket with `GOOGLE_DEV_SERVICE_ACCOUNT_JSON` through `google-github-actions/auth@v1` [6][7]. The token variable is described as "a github PAT which has admin over the org" [5].
- **CONFIRMED** Terraform `1.3.0`, Terragrunt `0.50.8`, provider `integrations/github >= 6.0.1`. `.terraform.lock.hcl` is git-ignored, so the provider floats [5][6][7].
- **CONFIRMED** No workflow in this repo is a reusable-workflow caller. The steps are `actions/checkout@v2`, `google-github-actions/auth@v1` and `gruntwork-io/terragrunt-action@v2`, all on mutable tags [6][7].

## Security notes

- **CONFIRMED** `on-pr.yaml:11` puts the org-admin PAT in the workflow environment, and `on-pr.yaml:25-32` runs `terragrunt plan` on the PR branch. A plan executes the branch's Terraform, so any author who can push a branch to this repo can read the PAT. The trigger is `pull_request`, not `pull_request_target`, so fork PRs get no secrets. **ASSESSED** Who can push branches depends on repo settings outside this stack. [6]
- **CONFIRMED** Neither workflow sets a `permissions:` block, so the `GITHUB_TOKEN` takes the repo or org default [6][7].
- **CONFIRMED** `modules/repository/main.tf:134-143` protects the default branch with no required review and no named check, and `enforce_admins = false`. The README promises one approving review, which this does not do [1][9].
- **CONFIRMED** The apply is gated by `terraform-prod` (`on-push.yaml:35`), and this stack creates that environment for itself. Its reviewers are `bifrost-admins`, the same 11 people who can merge [1][4][7].
- **CONFIRMED** `.gitignore` excludes `*.tfvars` except under `env/`, and the committed tfvars hold no credentials. `env/global.tfvars:2,5` holds `project_name = "hsci-github-config"` and `gcp_project = "gfs-selector-rest-prod-uk1"`. Nothing in the stack's resources reads either value [11].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "iac/modules/repository/main.tf@f4f97bd" },
  { "id": 2, "kind": "code", "ref": "iac/modules/repository/variables.tf@f4f97bd" },
  { "id": 3, "kind": "code", "ref": "iac/projects/bifrost-github-config/main.tf@f4f97bd" },
  { "id": 4, "kind": "code", "ref": "iac/projects/bifrost-github-config/teams.tf@f4f97bd" },
  { "id": 5, "kind": "code", "ref": "iac/projects/bifrost-github-config/variables.tf@f4f97bd" },
  { "id": 6, "kind": "code", "ref": ".github/workflows/on-pr.yaml@f4f97bd" },
  { "id": 7, "kind": "code", "ref": ".github/workflows/on-push.yaml@f4f97bd" },
  { "id": 8, "kind": "code", "ref": "iac/projects/root.hcl@f4f97bd" },
  { "id": 9, "kind": "code", "ref": "README.md@f4f97bd" },
  { "id": 10, "kind": "code", "ref": "iac/projects/bifrost-github-config/providers.tf@f4f97bd" },
  { "id": 11, "kind": "code", "ref": "iac/env/global.tfvars@f4f97bd" },
  { "id": 12, "kind": "code", "ref": "scripts/delete-artifacts@f4f97bd" },
  { "id": 13, "kind": "code", "ref": "iac/projects/bifrost-github-config/outputs.tf@f4f97bd" },
  { "id": 14, "kind": "pr", "ref": "gfs-bifrost/github-config#18" }
] }
```
