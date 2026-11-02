---
tags:
- waypoint
- distraction-dashboard
verified: '2026-10-13'
verified_sha: b628e29
verified_paths:
- README.md
- CLAUDE.md
- code/lib/github/api.ts
- code/lib/jira.ts
- iac/projects/distraction-dashboard/cloud-run.tf
- .github/workflows/deploy.yaml
title: distraction-dashboard — overview
thesis: distraction-dashboard is a read-only Next.js console with one shared login.
  It shows the gfs-bifrost org's failing CI, nightlies and open PRs to the duty dev,
  runs in dev only, and no Fuse pipeline depends on it.
confidence: high
---
# distraction-dashboard — overview

```orient-bluf
{ "v": 1, "bluf": "distraction-dashboard is a read-only Next.js console with one shared login. It shows the gfs-bifrost org's failing CI, nightlies and open PRs to the duty dev, runs in dev only, and no Fuse pipeline depends on it.", "confidence": "high", "action": "none" }
```

## Responsibility

- It shows the whole `gfs-bifrost` org in one view: failing default-branch CI, nightly runs, open PRs and open Renovate PRs [1][2].
- It reads the GitHub REST API directly and read-only, with one org token. It has no database and no write path [3].
- The pinned browser tab is the interface. A favicon and title beacon shows the failing count, and the page refreshes every 60 s. It sends no notifications [2].
- It links each PR to its Jira ticket when the branch, title or a commit carries a `FUSE-` key. The link is the only Jira contact [4].

## Why it exists separately

It is a single-purpose operational console over the GitHub API. It holds no customer or pipeline data.

Folding it into fuse-ui would put two audiences and two auth models behind one app. fuse-ui serves customer configuration. This serves CI health for the duty dev.

The product philosophy is deliberate [2]:

- **Shared, not personal.** Every view is the whole org. There is no "my PRs" lens, because it would fight the product.
- **A pull, not a push.** The tab is the interface, and there are no Slack or email nudges.
- **Honest signal.** Boards track the default branch, so a feature-branch run never masks a broken `main`.

`wishlist.md` holds parked features and says why each waits. Check it before proposing anything new.

**Dev only, by design.** It deploys to `bifrost-dev-global1` at `distraction.freightops.dev`. There is no `prod.tfvars` and no production stage [5][6].

**ASSESSED** Harry maintains it as his own initiative, and the whole team uses it. The git log shows 30 of 60 commits from Harry and 27 from Renovate. The 2026-08-24 interview in [[known-context]] says the same.

## Neighbours

```orient-flow
{ "v": 1, "title": "distraction-dashboard in context",
  "nodes": [
    { "id": "team", "label": "Duty dev and team", "sub": "browser tab, shared login", "kind": "external", "ev": [2] },
    { "id": "dd", "label": "distraction-dashboard", "sub": "Next.js on Cloud Run, dev", "kind": "service", "service": "distraction-dashboard", "tone": "accent", "ev": [5] },
    { "id": "gh", "label": "GitHub REST API", "sub": "gfs-bifrost org, read-only", "kind": "external", "ev": [3] },
    { "id": "ui", "label": "ui-toolkit", "sub": "@ilg-platform/ui-toolkit", "kind": "service", "service": "ui-toolkit", "ev": [7] },
    { "id": "ga", "label": "github-actions", "sub": "reusable build and deploy", "kind": "service", "service": "github-actions", "ev": [6] },
    { "id": "ci", "label": "core-infra", "sub": "DNS zone name", "kind": "service", "service": "core-infra", "ev": [8] },
    { "id": "jira", "label": "Jira", "sub": "links only", "kind": "external", "ev": [4] }
  ],
  "edges": [
    { "from": "team", "to": "dd", "label": "login, 60 s refresh" },
    { "from": "dd", "to": "gh", "label": "cached GET" },
    { "from": "ui", "to": "dd", "label": "npm package" },
    { "from": "ga", "to": "dd", "label": "build, apply to dev" },
    { "from": "ci", "to": "dd", "label": "zone name via remote state" },
    { "from": "dd", "to": "jira", "label": "ticket links", "style": "dashed" }
  ] }
```

Nothing in the Fuse pipeline consumes it. Its only inputs are the GitHub API and the shared component library. The `github-actions` workflows build and deploy it, and `core-infra` supplies the DNS zone. The Fuse MCP service catalog does not list it.

**ASSESSED** It faces the public internet. Cloud Run takes all ingress and grants `run.invoker` to `allUsers`, so the in-app login is the only gate. See [[architecture]] for the exposure and the dependency findings.

## Where the reference lives

[[architecture]] holds the layout, the caching model, the GitHub API surface, the auth gate and the deploy path. `CLAUDE.md` in the repo root carries the product philosophy and the UI gotchas. `design.md` records the design language. [[known-context]] holds ownership history.

Do not trust two things. `README.md` says the session cookie lasts 24 h, but the code sets 30 days [1][9]. The `CLAUDE.md` section "GitHub API surface" lists nightlies and merge-readiness chips as unbuilt, but both shipped [2].

## What deliberately isn't here

- **Notifications.** The whole point is a pull interface.
- **Personalised views.** `CLAUDE.md` rejects "my PRs" and "waiting on me" lenses.
- **Write actions.** `wishlist.md` parks "re-run from dashboard" until someone decides who may hold a write token.
- **A test suite.** `pnpm test` is an echo. See [[known-context#no-tests]].
- **A dependency audit.** The repo has no `secops` workflow. See [[architecture]].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "README.md@b628e29" },
  { "id": 2, "kind": "code", "ref": "CLAUDE.md@b628e29" },
  { "id": 3, "kind": "code", "ref": "code/lib/github/api.ts@b628e29" },
  { "id": 4, "kind": "code", "ref": "code/lib/jira.ts@b628e29" },
  { "id": 5, "kind": "code", "ref": "iac/projects/distraction-dashboard/cloud-run.tf@b628e29" },
  { "id": 6, "kind": "code", "ref": ".github/workflows/deploy.yaml@b628e29" },
  { "id": 7, "kind": "code", "ref": "code/package.json@b628e29" },
  { "id": 8, "kind": "code", "ref": "iac/projects/distraction-dashboard/remote.tf@b628e29" },
  { "id": 9, "kind": "code", "ref": "code/lib/auth/session.ts@b628e29" }
] }
```
