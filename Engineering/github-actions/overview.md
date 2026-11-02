---
tags:
- waypoint
- github-actions
verified: '2026-10-13'
verified_sha: af46124
verified_paths:
- README.md
- CLAUDE.md
- .github/workflows
- .github/actions
- .github/CODEOWNERS
- policies
title: github-actions — overview
thesis: 'github-actions is the platform''s shared CI/CD library: reusable workflows
  and actions that service repos call by rolling tag. A tag move changes every pinned
  caller at once, and no team owns the repo.'
confidence: high
---
# github-actions — overview

```orient-bluf
{ "v": 1, "bluf": "github-actions is the platform's shared CI/CD library: reusable workflows and actions that service repos call by rolling tag. A tag move changes every pinned caller at once, and no team owns the repo.", "confidence": "high", "action": "Before you move a tag, search the org for its callers and run one real caller against the change." }
```

## Responsibility

- It holds ten reusable workflows: `docker-build-push`, `terragrunt`, `node-run` and seven `secops-*` scans [1].
- It holds seven actions. Three render scan output, two gate allowlists, and `node-setup` and `secops-report` are plumbing [2].
- It holds five deprecation shims at the pre-0.2 secops filenames, and one Rego policy bundle for Trivy [3][4].
- It holds `on-tag.yaml`, a Slack notice on `v*` tags. That one is a trigger, not a reusable [5].
- Every scan reports its result to the secops ingest API. Reporting never gates CI [6].

## Why it exists separately

One versioned library gives every repo the same build, scan and deploy behaviour. A fix reaches callers through one tag move.
No service repo hand-rolls its own copy.

The repo is deliberately not Fuse-owned. Its `CLAUDE.md` calls it a shared effort with no owning team and no ticket queue [7].
A missing input or convention gets raised in `#platform-engineering` and added here once. Nobody forks it into a service repo.

## Neighbours

```orient-flow
{ "v": 1, "title": "github-actions in context",
  "nodes": [
    { "id": "c", "label": "Caller repos", "sub": "Fuse services, libraries, UIs, infra", "kind": "external", "ev": [8] },
    { "id": "ga", "label": "github-actions", "sub": "workflows + actions, rolling tags", "kind": "service", "service": "github-actions", "tone": "accent", "ev": [1, 2] },
    { "id": "ar", "label": "Artifact Registry", "sub": "image push", "kind": "store", "ev": [9] },
    { "id": "tm", "label": "terraform-modules", "sub": "git module fetch, App token", "kind": "service", "service": "terraform-modules", "ev": [10] },
    { "id": "sr", "label": "secops-reporting", "sub": "ingest API, OIDC", "kind": "service", "service": "secops-reporting", "ev": [6] },
    { "id": "np", "label": "GitHub Packages", "sub": "npm installs", "kind": "external", "ev": [9, 11] },
    { "id": "sl", "label": "Slack", "sub": "deploy and release notices", "kind": "external", "ev": [9, 5] }
  ],
  "edges": [
    { "from": "c", "to": "ga", "label": "uses: …@rolling-tag" },
    { "from": "ga", "to": "ar", "label": "docker push" },
    { "from": "ga", "to": "tm", "label": "module fetch", "style": "dashed" },
    { "from": "ga", "to": "sr", "label": "scan reports" },
    { "from": "ga", "to": "np", "label": "installs" },
    { "from": "ga", "to": "sl", "label": "notices" }
  ] }
```

Callers pin a tag. Two lines exist: `0.1-affogato` and `0.2-bonbon`. Local checkouts of 27 Fuse-adjacent repos show terragrunt and
docker-build-push still on 0.1, and the secops scans mostly on 0.2 [8]. The org-wide caller set is **UNKNOWN**: only checkouts under `~/code/fuse` were read.

## Where the reference lives

`README.md` is the caller-facing reference for inputs, secrets and examples. `CLAUDE.md` holds the edit-safely rules [7].
[[architecture]] holds the layout, the two tag lines and the auth paths. [[known-context]] holds ownership and the incident that made consumer search a rule.

Do not trust four sources:

- The README title and most examples say `gfs-platform`. The canonical org is `ilg-platform`; both names resolve. Do not sweep it [13].
- The README node default table says `20` in places. The workflow YAML says `22` [11][13].
- `CLAUDE.md` says the docker builds pass the token as a build arg. `docker-build-push` now passes a BuildKit secret [9].
- `CLAUDE.md` calls `0.1-affogato` untouched. It is a separate branch that takes backports [12].

## What deliberately isn't here

- **Build, test and lint tooling.** The repo is YAML plus zero-dependency Node scripts. The proof is a caller run.
- **App-token auth on the npm path.** GitHub Packages rejects App tokens, so installs use `npm_token` or `github.token` [11].
- **A `permissions:` block on the `report` jobs.** They inherit the caller's token so an under-permissioned caller no-ops.
- **Direct commits to `main`.** The repo uses a normal branch and PR flow.
- **Per-service deploy logic.** Callers own their inputs, Dockerfiles and approval environments.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": ".github/workflows/secops-dep-node.yaml@af46124" },
  { "id": 2, "kind": "code", "ref": ".github/actions/secops-report/action.yaml@af46124" },
  { "id": 3, "kind": "code", "ref": ".github/workflows/secops-dependency-audit.yaml@af46124" },
  { "id": 4, "kind": "code", "ref": "policies/README.md@af46124" },
  { "id": 5, "kind": "code", "ref": ".github/workflows/on-tag.yaml@af46124" },
  { "id": 6, "kind": "code", "ref": ".github/actions/secops-report/report-scan.mjs@af46124" },
  { "id": 7, "kind": "code", "ref": "CLAUDE.md@af46124" },
  { "id": 8, "kind": "log", "ref": "git -C ~/code/fuse/<repo> grep -E 'github-actions/\\.github/(workflows|actions)/[^ ]+@[^ ]+' origin/HEAD -- .github, over the 27 repo checkouts, 2026-10-13" },
  { "id": 9, "kind": "code", "ref": ".github/workflows/docker-build-push.yaml@af46124" },
  { "id": 10, "kind": "code", "ref": ".github/workflows/terragrunt.yaml@af46124" },
  { "id": 11, "kind": "code", "ref": ".github/workflows/node-run.yaml@af46124" },
  { "id": 12, "kind": "log", "ref": "git ls-remote origin: refs/heads/0-1-affogato d52202b, refs/tags/0.1-affogato d52202b, refs/tags/0.2-bonbon af46124 (= main); merge-base of the two lines ed195e6" },
  { "id": 13, "kind": "code", "ref": "README.md@af46124" }
] }
```
