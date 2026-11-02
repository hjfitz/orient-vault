---
tags:
- waypoint
- fuse-devtools
verified: '2026-10-28'
verified_sha: 5e8fcb9
verified_paths:
- README.md
- CLAUDE.md
- apps/pr-sitrep/src
- apps/pr-sitrep/tests
- apps/pr-sitrep/README.md
- apps/pr-sitrep/package.json
- apps/pr-sitrep/dockerfile
- apps/pr-sitrep/audit-ci.jsonc
- .github/workflows
- mise.toml
- iac/projects/pr-sitrep
- iac/projects/root.hcl
- iac/env
title: fuse-devtools — overview
thesis: 'fuse-devtools is a poly-app monorepo of internal Fuse tooling whose one app,
  pr-sitrep, ports the PR-status skill into a private Cloud Run service that prod''s
  scheduler runs each weekday morning, posting the gfs-bifrost PR status to #bifrost-forge
  with merging off.'
confidence: high
---
# fuse-devtools — overview

```orient-bluf
{ "v": 1, "bluf": "fuse-devtools is a poly-app monorepo of internal Fuse tooling whose one app, pr-sitrep, ports the PR-status skill into a private Cloud Run service that prod's scheduler runs each weekday morning, posting the gfs-bifrost PR status to #bifrost-forge with merging off.", "confidence": "high", "action": "If the weekday post is missing, start from the 10:00 run monitor and the pr-sitrep-prod scheduler job. A failed sweep or a failed Slack post both answer 502, so neither passes as a success." }
```

## Responsibility

- The repo holds internal developer tooling and scheduled jobs. Each directory under `apps/` is a self-contained service. `pr-sitrep` is the only one [1].
- `pr-sitrep` sweeps open pull requests across the configured GitHub orgs and classifies each one. It reports the result as JSON, markdown or a Slack post [2].
- It ports the classification logic of the `pr-sitrep` agent skill unchanged. What is new is its own GitHub credential, a token or a GitHub App. It also resolves its own reporting window, and can merge and post by itself [2].
- In prod it runs as the `ilg-platform-ci` GitHub App over every non-bot author in `gfs-bifrost`, with a 14-day window and merging off. It posts to #bifrost-forge at 09:00 Europe/London, Monday to Friday [8][9][10].
- Harry started it and owns it personally. It is not in the Fuse MCP service catalog.

## Why it exists separately

The skill treats "a human invoked me" as the approval to act. A scheduled run has no invoker, so unattended writes carry a different risk and need their own opt-in [3].

Merging and Slack posting therefore default to off. The config loader rejects merging across all authors, and merging with app credentials [3]. The deploy pins merging off and lets only prod post [8]. That risk posture does not belong inside the interactive skill. The monorepo shape also keeps each app's dependencies apart [1].

## Neighbours

```orient-flow
{ "v": 1, "title": "fuse-devtools in context",
  "nodes": [
    { "id": "sched", "label": "Cloud Scheduler", "sub": "pr-sitrep-prod, weekdays 09:00", "kind": "external", "ev": [9, 12] },
    { "id": "dev", "label": "fuse-devtools", "sub": "pr-sitrep on Cloud Run", "kind": "service", "service": "fuse-devtools", "tone": "accent", "ev": [4, 8] },
    { "id": "sm", "label": "Secret Manager", "sub": "app key, Slack token", "kind": "store", "ev": [11] },
    { "id": "gh", "label": "GitHub API", "sub": "as ilg-platform-ci", "kind": "external", "ev": [5, 6] },
    { "id": "jira", "label": "Jira", "sub": "no credential deployed", "kind": "external", "ev": [7] },
    { "id": "slack", "label": "Slack", "sub": "#bifrost-forge, prod only", "kind": "external", "ev": [8, 13] },
    { "id": "dd", "label": "Datadog", "sub": "logs, weekday-run monitor", "kind": "external", "ev": [8, 14] }
  ],
  "edges": [
    { "from": "sched", "to": "dev", "label": "OIDC POST sitrep/run" },
    { "from": "sm", "to": "dev", "label": "env at start", "style": "dashed" },
    { "from": "dev", "to": "gh", "label": "read only" },
    { "from": "dev", "to": "jira", "label": "sprint window if configured", "style": "dashed" },
    { "from": "dev", "to": "slack", "label": "header + one per non-draft PR" },
    { "from": "dev", "to": "dd", "label": "in-container agent", "style": "dashed" }
  ] }
```

The service calls outside systems and nothing in Fuse. No Fuse service calls it, and only the scheduler's service account holds `run.invoker`. An anonymous request gets 403 [12][15].

## Where the reference lives

[[architecture]] holds the classification rules, the HTTP surface, the config invariants, the build and the deploy. `CLAUDE.md` in the repo root holds the monorepo rules. `apps/pr-sitrep/README.md` holds the two traps a rewrite gets wrong, and the deploy and secret setup. [[known-context]] holds ownership and the reasoning behind the opt-in model.

Do not trust:

- [[known-context]] and `waypoint.yaml` where they say the service is not deployed and `iac/` does not exist. Both stopped being true when the deploy stack landed. The root `README.md` layout now matches the repo.

## What deliberately isn't here

- **Merging.** The deploy sets `MERGE_ENABLED=false`, and app credentials refuse it anyway, so prod reports and never merges.
- **Request authentication in the app.** No route checks a caller. Cloud Run IAM is the gate. See [[architecture]].
- **A Jira credential.** The window is the last 14 days, not the active sprint.
- **Posting from dev.** Terraform pauses dev's scheduler job and gives dev no Slack token.
- **Shared code between apps.** A second app that needs the same logic gets a published `@gfs-bifrost/*` package from `pkg-node`, not a shared directory.
- **Fuse platform logic.** The tool reads PR metadata and nothing from Fuse's own services.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "CLAUDE.md@d602d8e" },
  { "id": 2, "kind": "code", "ref": "apps/pr-sitrep/README.md@d602d8e" },
  { "id": 3, "kind": "code", "ref": "apps/pr-sitrep/src/config/env/config.ts@d602d8e" },
  { "id": 4, "kind": "code", "ref": "apps/pr-sitrep/src/http/sitrep.controller.ts@d602d8e" },
  { "id": 5, "kind": "code", "ref": "apps/pr-sitrep/src/adapters/github.client.ts@d602d8e" },
  { "id": 6, "kind": "code", "ref": "apps/pr-sitrep/src/adapters/github-token.ts@d602d8e" },
  { "id": 7, "kind": "code", "ref": "apps/pr-sitrep/src/adapters/jira.client.ts@d602d8e" },
  { "id": 8, "kind": "code", "ref": "iac/projects/pr-sitrep/cloud-run.tf@d602d8e" },
  { "id": 9, "kind": "code", "ref": "iac/projects/pr-sitrep/scheduler.tf@d602d8e" },
  { "id": 10, "kind": "code", "ref": "iac/projects/pr-sitrep/variables.tf@d602d8e" },
  { "id": 11, "kind": "code", "ref": "iac/projects/pr-sitrep/secrets.tf@d602d8e" },
  { "id": 12, "kind": "code", "ref": "iac/projects/pr-sitrep/iam.tf@d602d8e" },
  { "id": 13, "kind": "log", "ref": "Live check 2026-10-28: pr-sitrep-prod on Cloud Run (europe-west2, bifrost-prod-global1) at revision 00002; first #bifrost-forge post 2026-10-28 as the Bifrost Deployments app (bot user deployments); dev's scheduler job paused" },
  { "id": 14, "kind": "url", "ref": "https://github.com/gfs-bifrost/observability/blob/main/iac/projects/bifrost-observability/monitors.fuse-devtools.tf", "note": "[FUSE][PR Sitrep] Weekday run did not succeed: expects a 2xx by 10:00 on weekdays" },
  { "id": 15, "kind": "log", "ref": "Live check 2026-10-28: only pr-sitrep-sched-<env> holds run.invoker; an anonymous request gets 403" }
] }
```
