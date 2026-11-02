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
title: renovate-runner — architecture
thesis: One workflow with three triggers and three jobs runs a pinned Renovate image
  against config.js, whose last-match-wins packageRules enable only @gfs-bifrost and
  @ilg-platform npm bumps; a shell script then renders the daily Slack report, carrying
  a second copy of the automerge allowlist.
confidence: high
---
# renovate-runner — architecture

```orient-bluf
{ "v": 1, "bluf": "One workflow with three triggers and three jobs runs a pinned Renovate image against config.js, whose last-match-wins packageRules enable only @gfs-bifrost and @ilg-platform npm bumps; a shell script then renders the daily Slack report, carrying a second copy of the automerge allowlist.", "confidence": "high", "action": "Edit the automerge rules in config.js and branch_automerges in build-daily-report.sh together." }
```

## Guardrails

- [contract:G1] `config.js` `packageRules` are the automerge policy and run last-match-wins: disable everything, re-enable the two scopes, then override per repo. Add a carve-out after the rule it overrides, and give each allowlist entry a comment that names its CI coverage.
  — paths: config.js
- [contract:G2] `branch_automerges` in `build-daily-report.sh` repeats the allowlist and the `order-management-system` carve-out. It tags PRs in Slack from its own copy, so change both files together.
  — paths: config.js, scripts/build-daily-report.sh
- [technical:G3] Never use the `latest` Renovate image. `select-renovate-image-tag.sh` pins a release at least 10 to 14 days old that has a GHCR manifest, and the workflow caches the choice for the ISO week.
  — paths: scripts/select-renovate-image-tag.sh, .github/workflows/renovate.yaml
- [technical:G4] Do not add a `repositories:` list to the "Mint Renovate app token" step. It scopes the token to a subset and breaks `autodiscover`. Inclusion and exclusion live in the App install and `autodiscoverFilter`.
  — paths: .github/workflows/renovate.yaml, config.js
- [policy:G5] Add an archived repo to `autodiscoverFilter` as `!owner/repo`. Renovate cannot open or update PRs on a read-only repo, so leaving it discoverable only produces zombie PRs.
  — paths: config.js
- [policy:G6] Only the scheduled run and a manual run with the Slack box ticked post to Slack. `repository_dispatch` runs open PRs and stay silent.
  — paths: .github/workflows/renovate.yaml

## Layout

```
.github/workflows/renovate.yaml   scheduled + manual + repository_dispatch workflow
.github/workflows/ci.yaml         shell checks and fixture smoke tests
config.js                         the Renovate policy (repos, rules, grouping)
scripts/
  select-renovate-image-tag.sh    pins a soaked, stable Renovate image tag
  summary.sh                      renders the GitHub Job Summary from the NDJSON log
  build-daily-report.sh           builds the once-daily #bifrost-forge Slack payload
  build-slack-payload.sh          older short notifier, not wired into the workflow
tests/fixtures/                   NDJSON logs for every outcome branch
tests/preview.sh, Makefile        run the scripts locally against a fixture
```

## Triggers and jobs

**CONFIRMED** Three triggers feed one workflow [2]:

| Trigger | Behaviour |
| --- | --- |
| **Schedule** `0 9 * * 1-5` | The only trigger that always posts to Slack. 09:00 UTC is 10:00 London in summer and 09:00 in winter, because cron runs in UTC only |
| **Manual** `workflow_dispatch` | A "Notify Slack" checkbox, default on |
| **`repository_dispatch`** `pkg-node-published` | Opens PRs promptly and never posts to Slack. `concurrency: renovate-${{ github.event_name }}` collapses a publish burst to one run in flight plus one queued |

`pkg-node` fires the dispatch from its publish template, using an App token scoped to the `renovate-runner` repo. It sends the package name and version, which the workflow logs but does not use to scope the run [2][8].

```orient-flow
{ "v": 1, "title": "The workflow's three jobs",
  "nodes": [
    { "id": "trig", "label": "schedule / manual / dispatch", "kind": "external", "ev": [2] },
    { "id": "pin", "label": "Select image tag", "sub": "cached per ISO week", "kind": "step", "ev": [2, 4] },
    { "id": "run", "label": "renovate job", "sub": "Renovate vs config.js", "kind": "step", "tone": "accent", "ev": [1, 2] },
    { "id": "log", "label": "renovate-log artifact", "sub": "NDJSON, 1-day retention", "kind": "store", "ev": [2] },
    { "id": "sum", "label": "summary job", "sub": "Job Summary, has_updates", "kind": "step", "ev": [6] },
    { "id": "note", "label": "notify job", "sub": "schedule or ticked manual", "kind": "step", "ev": [2, 5] },
    { "id": "slack", "label": "#bifrost-forge", "kind": "external", "ev": [2] }
  ],
  "edges": [
    { "from": "trig", "to": "pin" },
    { "from": "pin", "to": "run" },
    { "from": "run", "to": "log" },
    { "from": "log", "to": "sum" },
    { "from": "log", "to": "note" },
    { "from": "note", "to": "slack", "label": "webhook" }
  ] }
```

- **`renovate`.** Pins and caches the image tag, loads or pulls the image, mints an App installation token (`owner: gfs-bifrost`), resolves the bot identity, runs `renovatebot/github-action` with `config.js`, and uploads the NDJSON log with debug level [2].
- **`summary`.** Renders the Job Summary and sets `has_updates` [2][6].
- **`notify`.** Mints the App token again to read PR check state, builds the Slack payload, validates it with `jq`, and posts it to the `SLACK_FORGE_WEBHOOK_URL` webhook. It runs only on the schedule, or on a manual run with the checkbox ticked [2][5].

## The automerge policy {#automerge-policy}

**CONFIRMED** `config.js` `packageRules`, in order [1]:

- **Disable everything** (`matchPackageNames: ['*']`).
- **`@gfs-bifrost/*` enabled** from `https://npm.pkg.github.com`.
- **`@gfs-bifrost/*` patch and minor**: one group, `automerge: true`, `platformAutomerge: false`. It applies to every repo, because each has build and test CI on PRs.
- **`@gfs-bifrost/*` major**: a separate group, `automerge: false`.
- **`@ilg-platform/*` enabled** the same way. Its patch and minor group has `automerge: false`, and there is no pkg-node dispatch fast path for it.
- **`@ilg-platform/*` major**: never auto-merged.
- **`order-management-system` carve-out**: patch and minor automerge off for that repo, because it has no CI on PRs.
- **`@ilg-platform/*` carve-in** for patch and minor, scoped by `matchRepositories`: `distraction-dashboard`, `fuse-billing`, `secops`, `one-time-secrets` and `ilg-platform/ui-toolkit`. An inline comment lists each one's CI coverage. `one-time-secrets` deploys straight to prod on merge.

Global settings: `enabledManagers: ['npm']`, `rangeStrategy: 'bump'`, `prHourlyLimit: 2`, `prConcurrentLimit: 10`, `rebaseWhen: 'conflicted'`, `recreateClosed: false`, `onboarding: false`, `requireConfig: 'optional'`, `dependencyDashboard: false`. A `hostRules` entry sends `RENOVATE_NPMRC_TOKEN` to `npm.pkg.github.com` [1].

**CONFIRMED** The daily report derives eligibility from the branch name and repo, because automerge is not in the log. `branch_automerges` matches the group slug (`*gfs-bifrost-packages-(patchminor)*`) and repeats the carve-out and the allowlist. It then reads check state per PR through the GraphQL API [5].

**ASSESSED** One allowlist entry matches nothing. `gfs-bifrost/secops` moved to `ilg-platform/secops-reporting` on 2026-07-27, and GitHub now redirects the old name [11]. The App token is minted for `owner: gfs-bifrost`, which covers only that installation's repos. So `ilg-platform/ui-toolkit` is probably never discovered either [2]. This rests on the App's installation settings, which sit outside the repo. The same dead names sit in `build-daily-report.sh:75` [5].

## Autodiscovery and exclusions

**CONFIRMED** `autodiscover: true` with three negative filters: `snap-queue-polling-service`, `order-management-system` and `shopfiy-app`. All three carry `archived = true` in github-config [1][9]. The `repositories` list is empty and holds only commented test entries [1].

## Image tag selection {#image-pinning}

**CONFIRMED** `select-renovate-image-tag.sh` pages through `renovatebot/renovate` releases (100 per page, up to `MAX_PAGES=5`). It keeps stable releases at least `MIN_AGE_DAYS` (14) old that have a manifest on GHCR, checked with `docker manifest inspect`. If none qualifies, it lowers the window one day at a time to `MIN_AGE_FLOOR_DAYS` (10), then fails [4]. A 45-minute step timeout bounds the walk [2]. The tag is cached for the ISO week under `renovate-chosen-tag-<year>-W<week>`. That also keeps the 1 GB image tarball cache key stable [2].

To force reselection, delete the cache entry: `gh cache delete 'renovate-chosen-tag-YYYY-Www' --repo gfs-bifrost/renovate-runner` [7].

## Build and test

**CONFIRMED** `ci.yaml` runs on pull requests, pushes to `main` and manual dispatch. It runs `bash -n` on every script, `shellcheck --severity=error`, and a smoke test that runs `tests/preview.sh` in all three modes against every fixture plus `no-log` [3]. `tests/preview.sh` and the Makefile give the same local previews [10].

## Security notes

- **CONFIRMED** `renovate.yaml:43` interpolates `github.event.client_payload.package` and `.version` straight into a `run:` script. `renovate.yaml:207-211` and `:253-260` pass them as shell arguments the same way. A `repository_dispatch` sender can inject shell, and the job holds the App private key and PAT. The sender today is `pkg-node`, which controls both values [2][8].
- **CONFIRMED** No `permissions:` block exists in either workflow, so `GITHUB_TOKEN` takes the repo default [2][3].
- **CONFIRMED** Third-party actions are pinned by mutable tag: `actions/checkout@v4`, `actions/cache@v4`, `actions/create-github-app-token@v1`, `renovatebot/github-action@v41.0.1` and `slackapi/slack-github-action@v2.1.1` [2]. The Renovate image is pinned by tag, not digest [4].
- **CONFIRMED** `RENOVATE_NPMRC_TOKEN` takes `secrets.GH_TOKEN`, a PAT, and the App private key and Slack webhook are also repo secrets. None is committed. `config.js` reads the token from `process.env` [1][2].
- **CONFIRMED** The release lookup calls `api.github.com` with no token (`select-renovate-image-tag.sh:38`), so it shares the anonymous rate limit [4].

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
  { "id": 8, "kind": "url", "ref": "https://github.com/gfs-bifrost/pkg-node/blob/ab780a5/.github/workflows/template-publish-node.yaml", "note": "dispatch step and its app token" },
  { "id": 9, "kind": "url", "ref": "https://github.com/gfs-bifrost/github-config/blob/f4f97bd/iac/projects/bifrost-github-config/main.tf", "note": "the three archived repos" },
  { "id": 10, "kind": "code", "ref": "tests/preview.sh@ad82526" },
  { "id": 11, "kind": "log", "ref": "gh api repos/gfs-bifrost/secops (2026-10-13) returns full_name ilg-platform/secops-reporting" }
] }
```
