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
title: github-config — overview
thesis: github-config is the Terraform that creates, configures and archives every
  gfs-bifrost GitHub repository and owns the bifrost-admins team. Its main.tf, not
  the Fuse catalog, is the authority on which repos exist and which are archived.
confidence: high
---
# github-config — overview

```orient-bluf
{ "v": 1, "bluf": "github-config is the Terraform that creates, configures and archives every gfs-bifrost GitHub repository and owns the bifrost-admins team. Its main.tf, not the Fuse catalog, is the authority on which repos exist and which are archived.", "confidence": "high", "action": "Archive a repo with archived = true, and treat any change to modules/repository as an org-wide change." }
```

## Responsibility

- **Repository lifecycle.** 37 `module "repository"` blocks, plus one standalone `repo-template` resource, define 38 repos. Eight carry `archived = true`, so 30 are live [3].
- **Uniform settings.** Every repo is internal, squash and rebase only, with vulnerability alerts on. It also gets `terraform-dev` and `terraform-prod` environments and branch protection [1].
- **One team.** `bifrost-admins` has 11 maintainers. The team holds admin on every repo and reviews both environments [1][4].
- **Archival authority.** An `archived` variable on the module is what makes a repo read-only [2]. The decommissioned `order-management-system`, `snap-queue-polling-service` and `shopfiy-app` were each archived this way [3].

## Why it exists separately

Repo existence, settings and team access are org concerns. No single service should own them. A new repo then starts from the same settings every time. Decommissioning becomes one reviewed line, where a manual UI click is easy to forget.

## Neighbours

```orient-flow
{ "v": 1, "title": "github-config in context",
  "nodes": [
    { "id": "pat", "label": "GH_TOKEN", "sub": "org-admin PAT, CI secret", "kind": "external", "ev": [6, 7] },
    { "id": "ghc", "label": "github-config", "sub": "Terragrunt, GitHub provider", "kind": "service", "service": "github-config", "tone": "accent", "ev": [3] },
    { "id": "mod", "label": "modules/repository", "sub": "37 module blocks", "kind": "step", "ev": [1, 3] },
    { "id": "tpl", "label": "repo-template", "sub": "template for new repos", "kind": "external", "ev": [1, 3] },
    { "id": "repos", "label": "gfs-bifrost repos", "sub": "30 live, 8 archived", "kind": "external", "ev": [3] },
    { "id": "team", "label": "bifrost-admins", "sub": "11 maintainers", "kind": "store", "ev": [4] },
    { "id": "env", "label": "terraform-dev / terraform-prod", "sub": "environments per repo", "kind": "step", "ev": [1] },
    { "id": "state", "label": "gfs-bifrost-tfstate", "sub": "GCS state bucket", "kind": "store", "ev": [8] }
  ],
  "edges": [
    { "from": "pat", "to": "ghc", "label": "provider auth" },
    { "from": "ghc", "to": "mod" },
    { "from": "mod", "to": "repos", "label": "create, configure, archive" },
    { "from": "tpl", "to": "repos", "label": "from_template mode", "style": "dashed" },
    { "from": "team", "to": "repos", "label": "admin on all" },
    { "from": "mod", "to": "env", "label": "reviewers = team" },
    { "from": "ghc", "to": "state" }
  ] }
```

Nothing consumes this stack's outputs at run time. The consumers are the repos it creates. Fuse service repos such as `dedupe-service`, `bifrost-pubsub` and `audit-service` exist because of a module block here [3]. A push to `main` or `master` plans, then applies behind the `terraform-prod` environment [7].

## Where the reference lives

[[architecture]] holds the module, the repo list rules and the CI flow. [[known-context]] holds ownership and archival history. Read `iac/projects/bifrost-github-config/main.tf` for the live repo list [3].

Do not trust the `README.md` on branch protection. It promises "1 approving review", and the module requires none [1][9]. Its status-check requirement lists no checks.

## What deliberately isn't here

- **Any `ilg-platform` repo.** This stack governs `gfs-bifrost` only [5].
- **`secops-reporting`.** It left this stack when it moved orgs. See [[secops-reporting]].
- **Repository contents, CI and Actions secrets.** The stack manages no Actions secret, variable, ruleset or webhook [1].
- **Per-repo access beyond `bifrost-admins`.** The module grants no other team or collaborator [1].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "iac/modules/repository/main.tf@f4f97bd" },
  { "id": 2, "kind": "code", "ref": "iac/modules/repository/variables.tf@f4f97bd" },
  { "id": 3, "kind": "code", "ref": "iac/projects/bifrost-github-config/main.tf@f4f97bd" },
  { "id": 4, "kind": "code", "ref": "iac/projects/bifrost-github-config/teams.tf@f4f97bd" },
  { "id": 5, "kind": "code", "ref": "iac/projects/bifrost-github-config/providers.tf@f4f97bd" },
  { "id": 6, "kind": "code", "ref": ".github/workflows/on-pr.yaml@f4f97bd" },
  { "id": 7, "kind": "code", "ref": ".github/workflows/on-push.yaml@f4f97bd" },
  { "id": 8, "kind": "code", "ref": "iac/projects/root.hcl@f4f97bd" },
  { "id": 9, "kind": "code", "ref": "README.md@f4f97bd" }
] }
```
