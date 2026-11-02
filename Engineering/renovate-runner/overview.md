---
tags:
- waypoint
- renovate-runner
verified: '2026-10-13'
verified_sha: ad82526
verified_paths:
- config.js
- .github/workflows
- scripts
- tests/preview.sh
- Makefile
- README.md
title: renovate-runner — overview
thesis: 'renovate-runner is the one central Renovate bot for gfs-bifrost: a scheduled
  workflow whose config.js sets which @gfs-bifrost and @ilg-platform bumps open PRs
  and which auto-merge. That file is the org''s automerge policy.'
confidence: high
---
# renovate-runner — overview

```orient-bluf
{ "v": 1, "bluf": "renovate-runner is the one central Renovate bot for gfs-bifrost: a scheduled workflow whose config.js sets which @gfs-bifrost and @ilg-platform bumps open PRs and which auto-merge. That file is the org's automerge policy.", "confidence": "high", "action": "Change an automerge rule in config.js and in build-daily-report.sh together, or the Slack report mislabels PRs." }
```

## Responsibility

- **One Renovate runner.** A GitHub Actions workflow runs Renovate against every repo its GitHub App can see. Only the `npm` manager is on [1][2].
- **A narrow scope.** A catch-all rule disables every package. Two rules re-enable only `@gfs-bifrost/*` and `@ilg-platform/*` [1].
- **The automerge policy.** `@gfs-bifrost` patch and minor bumps auto-merge in every repo but one. `@ilg-platform` patch and minor bumps auto-merge only for a named list. Majors never do [1].
- **A daily report.** The scheduled run posts every open Renovate PR to `#bifrost-forge`, with auto-merge tags and stalled branches [2][5]. The run page also carries a Job Summary table [6].

## Why it exists separately

One config file means the policy, the image pinning and the report change once. Consumer repos carry no `renovate.json`, because onboarding is off [1]. A new repo needs no setup. It is discoverable, or it appears in a negative filter if archived [1]. The `renovate-clear` and morning-digest skills read this file as the policy.

## Neighbours

```orient-flow
{ "v": 1, "title": "renovate-runner in context",
  "nodes": [
    { "id": "pkg", "label": "pkg-node", "sub": "fires pkg-node-published", "kind": "service", "service": "pkg-node", "ev": [8] },
    { "id": "rr", "label": "renovate-runner", "sub": "workflow + config.js", "kind": "service", "service": "renovate-runner", "tone": "accent", "ev": [2] },
    { "id": "ghcr", "label": "ghcr.io/renovatebot/renovate", "sub": "tag pinned, 14-day soak", "kind": "external", "ev": [4] },
    { "id": "app", "label": "Renovate GitHub App", "sub": "token for owner gfs-bifrost", "kind": "external", "ev": [2] },
    { "id": "repos", "label": "gfs-bifrost repos", "sub": "autodiscovered", "kind": "external", "ev": [1] },
    { "id": "npm", "label": "npm.pkg.github.com", "sub": "package versions", "kind": "store", "ev": [1] },
    { "id": "slack", "label": "#bifrost-forge", "sub": "daily report", "kind": "external", "ev": [2] },
    { "id": "ghc", "label": "github-config", "sub": "creates this repo", "kind": "service", "service": "github-config", "ev": [9] }
  ],
  "edges": [
    { "from": "pkg", "to": "rr", "label": "repository_dispatch" },
    { "from": "ghc", "to": "rr", "style": "dashed" },
    { "from": "ghcr", "to": "rr", "label": "image pull" },
    { "from": "rr", "to": "app", "label": "mint token" },
    { "from": "app", "to": "repos", "label": "open PRs" },
    { "from": "rr", "to": "npm", "label": "version lookups" },
    { "from": "rr", "to": "slack", "label": "schedule only" }
  ] }
```

A package publish in `pkg-node` triggers a run, so new versions become PRs without waiting for the schedule. That run never posts to Slack. Only the weekday 09:00 UTC schedule and a manual run with the box ticked do [2][8].

## Where the reference lives

[[architecture]] holds the rules, workflow and image selection. [[known-context]] holds the ownership and the stale-entry history. `config.js` itself is the source of truth. Read it directly instead of trusting any paraphrase, including the table in this vault.

The `README.md` is slightly stale. It says the workflow has two triggers, and it has three. It also omits `ci.yaml` and the daily report script from its layout [2][3][7].

## What deliberately isn't here

- **Per-repo Renovate config.** `onboarding: false` stops a consumer defining its own behaviour [1].
- **Any manager except npm.** No GitHub Actions, Docker or Terraform bumps run here [1].
- **A `latest` Renovate image.** The script always picks a pinned release [4].
- **A Slack post per publish.** Only the daily run posts [2].
- **Deciding whether a PR is safe.** Each repo's own CI does that. The runner only enables automerge where CI exists [1].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "config.js@ad82526" },
  { "id": 2, "kind": "code", "ref": ".github/workflows/renovate.yaml@ad82526" },
  { "id": 3, "kind": "code", "ref": ".github/workflows/ci.yaml@ad82526" },
  { "id": 4, "kind": "code", "ref": "scripts/select-renovate-image-tag.sh@ad82526" },
  { "id": 5, "kind": "code", "ref": "scripts/build-daily-report.sh@ad82526" },
  { "id": 6, "kind": "code", "ref": "scripts/summary.sh@ad82526" },
  { "id": 7, "kind": "code", "ref": "README.md@ad82526" },
  { "id": 8, "kind": "url", "ref": "https://github.com/gfs-bifrost/pkg-node/blob/ab780a5/.github/workflows/template-publish-node.yaml", "note": "dispatches pkg-node-published" },
  { "id": 9, "kind": "url", "ref": "https://github.com/gfs-bifrost/github-config/blob/f4f97bd/iac/projects/bifrost-github-config/main.tf", "note": "module renovate_runner" }
] }
```
