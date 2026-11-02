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
title: fuse-devtools — architecture
thesis: pr-sitrep is a layered Express app that sweeps open PRs through GitHub, Jira
  and Slack adapters, gives each PR two independent verdicts, and merges or posts
  only when opt-in flags allow it; it runs as a private Cloud Run service whose only
  caller is prod's weekday scheduler, because its routes carry no authentication.
confidence: high
---
# fuse-devtools — architecture

```orient-bluf
{ "v": 1, "bluf": "pr-sitrep is a layered Express app that sweeps open PRs through GitHub, Jira and Slack adapters, gives each PR two independent verdicts, and merges or posts only when opt-in flags allow it; it runs as a private Cloud Run service whose only caller is prod's weekday scheduler, because its routes carry no authentication.", "confidence": "high", "action": "Keep run.invoker limited to the scheduler's service account and never add allUsers. Cloud Run IAM is the only thing between the internet and POST /api/v1/sitrep/run." }
```

## Guardrails

- [technical:G1] Apps share nothing. There is no root `package.json` or pnpm workspace, no cross-app import, and each app owns its lockfile, tsconfig, biome config, audit config and dockerfile. Shared code becomes a published `@gfs-bifrost/*` package.
  — paths: CLAUDE.md, apps/pr-sitrep/package.json
- [contract:G2] Unattended writes are opt-in. `MERGE_ENABLED` and `SLACK_ENABLED` default to false, and `GET /api/v1/sitrep` never merges or posts. The deploy pins `MERGE_ENABLED=false` and enables Slack only when `env == "prod"`, so dev never posts.
  — paths: apps/pr-sitrep/src/config/env/config.ts, apps/pr-sitrep/src/core/merge.service.ts, apps/pr-sitrep/src/core/publish.service.ts, apps/pr-sitrep/src/http/sitrep.controller.ts, iac/projects/pr-sitrep/cloud-run.tf, iac/projects/pr-sitrep/variables.tf
- [technical:G3] `MERGE_ENABLED` never combines with `GITHUB_ALL_AUTHORS` or with GitHub App credentials. `loadConfig` throws: merging is only safe for one author's own PRs, and the app is granted read access only.
  — paths: apps/pr-sitrep/src/config/env/config.ts
- [technical:G4] Never act on one read of `mergeable_state`. The client re-reads while it is `unknown` and once more for a long-idle PR.
  — paths: apps/pr-sitrep/src/adapters/github.client.ts
- [technical:G5] The service stays private and the run stays at-most-once. Only the scheduler's service account holds `run.invoker`, with no `allUsers` member, and the job has `retry_count = 0` because a run that posted and then failed would post twice.
  — paths: iac/projects/pr-sitrep/iam.tf, iac/projects/pr-sitrep/scheduler.tf
- [technical:G6] Mention a Slack user only by a looked-up id. An unresolved author degrades to plain `@login`, never a guessed id.
  — paths: apps/pr-sitrep/src/core/publish.service.ts

## Poly-app monorepo, one app

```
apps/pr-sitrep/          own lockfile, tsconfig, biome.json, audit-ci.jsonc, dockerfile, src/, tests/
iac/env/*.tfvars         global (region), dev and prod (project, log level), shared by every app
iac/projects/root.hcl    Terragrunt root: tfvars, GCS state per env
iac/projects/pr-sitrep/  cloud-run, iam, scheduler, secrets, variables, outputs
.github/workflows/       pr-sitrep-code-quality, pr-sitrep-on-push, pr-sitrep-manual-deploy, secops (shared)
mise.toml                node 24, pnpm 9.15.4, terraform 1.9.0, terragrunt 0.50.8
```

Source layout under `apps/pr-sitrep/src/`:

```
main.ts, cli.ts        HTTP entrypoint; one-off CLI run (--format json|markdown|slack)
bootstrap/             app.ts (Express wiring), factories/sitrep.factory.ts
http/                  health.controller, sitrep.controller, middleware/ (correlation, error)
core/                  classification, sitrep, merge, publish, scheduled-run, render/
adapters/              github.client, github-token, jira.client, slack.client
config/env/config.ts   one Zod schema plus cross-field rules, validated once at startup
models/, exceptions/, observability/, shared/
tests/                 mirrors src: adapters, config, core, http (14 specs, vitest)
```

The repo has no root `package.json`, so every command runs from `apps/pr-sitrep/`. [1]

```orient-flow
{ "v": 1, "title": "A scheduled run",
  "nodes": [
    { "id": "caller", "label": "Cloud Scheduler", "sub": "OIDC POST /api/v1/sitrep/run", "kind": "external", "ev": [20, 21] },
    { "id": "run", "label": "ScheduledRunService", "sub": "sweep, merge, publish", "kind": "service", "service": "fuse-devtools", "tone": "accent", "ev": [3] },
    { "id": "sit", "label": "SitrepService", "sub": "search, facts, classify", "kind": "step", "ev": [4] },
    { "id": "gh", "label": "GitHub API", "sub": "per-org installation token", "kind": "external", "ev": [5, 22] },
    { "id": "jira", "label": "Jira", "sub": "sprint window", "kind": "external", "ev": [6] },
    { "id": "mrg", "label": "MergeService", "sub": "only MERGEABLE rows", "kind": "step", "ev": [7] },
    { "id": "pub", "label": "PublishService", "sub": "header, then per non-draft PR", "kind": "step", "ev": [8] },
    { "id": "slack", "label": "Slack", "kind": "external", "ev": [9] }
  ],
  "edges": [
    { "from": "caller", "to": "run" },
    { "from": "run", "to": "sit" },
    { "from": "sit", "to": "gh", "label": "read" },
    { "from": "sit", "to": "jira", "label": "window if credentialed", "style": "dashed" },
    { "from": "run", "to": "mrg", "label": "if MERGE_ENABLED (off when deployed)", "style": "dashed" },
    { "from": "mrg", "to": "gh", "label": "squash merge, delete branch", "style": "dashed" },
    { "from": "run", "to": "pub", "label": "if SLACK_ENABLED (prod only)" },
    { "from": "pub", "to": "slack" }
  ] }
```

## Runtime shape

Plain Express 5. `http/` holds thin controllers plus correlation and error middleware. `core/` holds classification, merge, publish, rendering and the scheduled-run orchestration. `adapters/` hold the GitHub, Jira and Slack clients over `fetch`. `config/env/config.ts` validates every variable once, so an invalid or missing value stops the process at start-up. `bootstrap/factories/sitrep.factory.ts` wires the services. It picks the GitHub token source, and the Jira and Slack clients are `null` when their credentials or flag are absent [10][11].

**GitHub credentials.** `GithubClient` asks a `GithubTokenSource` port for a token per request, keyed by the org it is calling. `StaticGithubToken` returns `GITHUB_TOKEN`. `GithubAppTokens` signs an RS256 app JWT, looks up the org's installation and mints an installation token. It caches one token per org and re-mints when fewer than five minutes remain [22][5].

`SitrepService.run` resolves the author (`GITHUB_AUTHOR`, the token's own login, or none under `GITHUB_ALL_AUTHORS`), resolves the window, and searches each org for open PRs updated since the window start. An installation token has no user behind it, so app mode needs `GITHUB_AUTHOR` or `GITHUB_ALL_AUTHORS`. It then gathers facts per PR one at a time, because the mergeability retries sleep and sequential calls keep GitHub request pressure predictable. Under `GITHUB_ALL_AUTHORS` it drops bot authors [4][3].

The window is the active sprint's start date from Jira (`project = FUSE AND sprint in openSprints()`). Without Jira credentials, or with no active sprint, it falls back to the last `FALLBACK_WINDOW_DAYS` days. The deploy sets no Jira credential and sets that fallback to 14 [6][4][20].

## Two independent verdicts per PR

```orient-flow
{ "v": 1, "title": "The merge bar, in order",
  "nodes": [
    { "id": "d", "label": "Draft?", "kind": "step", "ev": [12] },
    { "id": "m", "label": "mergeable_state clean?", "kind": "step", "ev": [12] },
    { "id": "c", "label": "No failing check?", "kind": "step", "ev": [12] },
    { "id": "r", "label": "Approved, no changes requested?", "kind": "step", "ev": [12] },
    { "id": "b", "label": "Base is default branch?", "kind": "step", "ev": [12] },
    { "id": "s", "label": "No hold phrase in body?", "kind": "step", "ev": [12] },
    { "id": "ok", "label": "MERGEABLE", "kind": "step", "tone": "accent", "ev": [12] },
    { "id": "h", "label": "HOLD, with the first reason", "kind": "step", "tone": "alert", "ev": [12] }
  ],
  "edges": [
    { "from": "d", "to": "m", "label": "no" },
    { "from": "m", "to": "c", "label": "yes" },
    { "from": "c", "to": "r", "label": "yes" },
    { "from": "r", "to": "b", "label": "yes" },
    { "from": "b", "to": "s", "label": "yes" },
    { "from": "s", "to": "ok", "label": "yes" },
    { "from": "d", "to": "h", "label": "yes", "style": "dashed" },
    { "from": "m", "to": "h", "label": "no", "style": "dashed" },
    { "from": "c", "to": "h", "label": "no", "style": "dashed" },
    { "from": "r", "to": "h", "label": "no", "style": "dashed" },
    { "from": "b", "to": "h", "label": "no", "style": "dashed" },
    { "from": "s", "to": "h", "label": "no", "style": "dashed" }
  ] }
```

- **Merge bar.** `MERGEABLE` or `HOLD`. The first failing step above sets the reason. A check counts as failing only when completed with a conclusion other than success, skipped or neutral. The latest approving or changes-requesting review per reviewer decides the review step, and a dismissal clears it [12].
- **Check runs are deduplicated** the way branch protection reads them. Only the newest run (highest id) per app and check name counts, so a failed run that was re-run and passed no longer blocks [12].
- **Report bar.** `draft`, `blocked`, `ready`, `incomplete`, `needs-review`, first match wins in that order. `blocked` means a non-clean `mergeable_state`, failing CI or changes requested. `ready` means approved, clean and CI not failing. `incomplete` means the PR is not ready and its body has no usable Evidence section. Everything else is `needs-review` [12].
- **Evidence** is judged from a heading named Evidence, Testing or Verification. Empty, a placeholder or all-unchecked boxes count as outstanding. A URL, a code fence, a passed-test count or more than 200 characters counts as present [12].
- **Stacking.** A PR whose base is another open PR's head branch gets `stackedOnOpenPR`. The merge bar holds it, but its hold reason names the stack only when no earlier step already holds it [4][12].

Two traps are load-bearing. GitHub computes `mergeable_state` asynchronously, so the client re-reads up to three times, 1.5 s apart, while it reads `unknown`. It re-reads once more when the PR has sat idle for `REFRESH_DAYS`, because a stale value can read clean without ever saying `unknown` [5].

## HTTP surface

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Returns 200 with service name and environment. Cloud Run's startup probe |
| GET | `/api/v1/sitrep?format=json\|markdown\|slack` | Runs a sweep and returns the report. Read-only. An unknown format is a 400 |
| POST | `/api/v1/sitrep/run` | The scheduler target. Sweeps, then merges and posts per the two flags, and returns window, summary, merges and posts |

An `IntegrationError` answers 502 and any other error 500. The body is `{ error, correlationId }`, plus the stack outside prod. The service echoes an inbound `x-correlation-id` or mints a UUID [13][14].

A failed Slack post fails the run: it is recorded as `posted: false` in `posts`, and the `POST` answers 502 with the same body. The posts that went out stay up, and the scheduler does not retry [8][14].

**Authentication.** No route, middleware or guard checks the caller. The `GET` runs a full sweep with the service's credential and returns PR titles, URLs and authors. The `POST` posts, and merges when the flags allow. The deployed service is reachable over HTTPS but private: Cloud Run IAM grants `run.invoker` only to `pr-sitrep-sched-<env>`, so an anonymous request gets 403 before the app sees it [21][23].

## Configuration and write defaults

Every value comes from the environment, and one Zod schema rejects bad values at start. The defaults are `ENVIRONMENT=local`, `PORT=3000` and `LOG_LEVEL=info`. `GITHUB_ORGS` is required [3].

Rules `loadConfig` enforces after the schema [3]:

- Exactly one GitHub credential: `GITHUB_TOKEN`, or `GITHUB_APP_CLIENT_ID` with `GITHUB_APP_PRIVATE_KEY`. The two app values must be set together.
- App credentials need `GITHUB_AUTHOR` or `GITHUB_ALL_AUTHORS`, and refuse `MERGE_ENABLED` (G3).
- `MERGE_ENABLED` with `GITHUB_ALL_AUTHORS` fails (G3).
- `SLACK_ENABLED` without `SLACK_BOT_TOKEN` fails.

`MERGE_ENABLED` and `SLACK_ENABLED` both default to false, per G2.

- **Merge.** `MergeService` skips every row unless the flag is on. When on, it squash-merges each `MERGEABLE` row and deletes the head branch. A failed branch delete does not fail the merge. One failed merge is recorded and the rest continue [7][5].
- **Slack.** `PublishService` posts one header, then one message per non-draft PR so each keeps its own thread and reactions. Drafts never reach the channel, and a sweep with no non-draft PRs posts nothing. The header reads "open PRs since sprint start" with a sprint window, or "open PRs active since <date>" without one. Each message is a separate call, and one failed post does not stop the rest [8][15].
- **Mentions.** For each non-bot, non-draft author it builds an email from the login (strip a `_gfsdev` suffix, turn `-` into `.`, add `SLACK_EMAIL_DOMAIN`) and looks up the Slack id. A failed lookup is logged and degrades to `@login` [8].
- **Defaults baked into the schema.** The Jira base URL is `https://globalfreight.atlassian.net`, the Jira project is `FUSE`, and the Slack channel id defaults to #bifrost-forge's. The deploy does not override the channel [3][20].

## Secrets

The service takes one GitHub credential as env vars: `GITHUB_TOKEN` (a PAT; write scope only for merging), or `GITHUB_APP_CLIENT_ID` plus `GITHUB_APP_PRIVATE_KEY`. It also takes `JIRA_API_TOKEN` with `JIRA_EMAIL`, and `SLACK_BOT_TOKEN`. Each token travels only in an `Authorization` header [5][6][9][22]. The app key must be RSA, and literal `\n` sequences from a single-line secret are turned back into newlines [22]. The start-up log lists the orgs and both flags, never a credential [2].

Deployed, the app key comes from Secret Manager secret `pr-sitrep-github-app-key` (dev and prod) and the Slack token from `pr-sitrep-slack-bot-token` (prod only). Both were created by hand with `gcloud`. Terraform reads them through data sources and grants the runtime service account `secretAccessor`, so their values never enter state [24][15].

Client error messages carry the request path and a 200-character excerpt of the upstream body, and the error handler returns that message to the caller [5][22][13].

**ASSESSED** A credential does not reach a log or response through this code. An upstream error body could echo request data, and the 200-character excerpt would pass it to the caller. Source: no client puts a credential into an error string [5][6][9][22].

## Build, test and CI

- Node 24, pnpm 9.15.4, TypeScript 5 with CommonJS output, Biome 1.9.4, vitest 2 and zod 4. Run `lint:fix`, `build:check`, `build:check:tests` and `test` from the app directory [1][16].
- `pr-sitrep-code-quality.yaml` runs the four scripts on node 24 through the shared `node-run` workflow, filtered to `apps/pr-sitrep/**`. `secops.yaml` runs secret, dependency, code and container scans on pull requests and pushes. It has no nightly schedule, because the shared dependency-audit workflow false-fails fleet-wide [17][18].
- The dockerfile builds on `node:24` and prunes dev dependencies. It runs on the platform's `node24-runtime:0.1-affogato` golden image: distroless, `nonroot`, with the Datadog agent as the entrypoint. The dockerfile sets `CMD` only, because an `ENTRYPOINT` would bypass the agent [19].
- `audit-ci.jsonc` has an empty allowlist, and the container scan uses no `.trivyignore`.

## Deploy

```orient-flow
{ "v": 1, "title": "Push to main, pr-sitrep paths",
  "nodes": [
    { "id": "bd", "label": "Build dev image", "kind": "step", "ev": [25] },
    { "id": "ad", "label": "Apply dev", "sub": "terragrunt apply", "kind": "step", "ev": [25] },
    { "id": "bp", "label": "Build prod image", "kind": "step", "ev": [25] },
    { "id": "pp", "label": "Plan prod", "kind": "step", "ev": [25] },
    { "id": "ap", "label": "Apply prod", "sub": "terraform-prod reviewers", "kind": "step", "tone": "accent", "ev": [25] }
  ],
  "edges": [
    { "from": "bd", "to": "ad" },
    { "from": "ad", "to": "bp" },
    { "from": "bp", "to": "pp" },
    { "from": "pp", "to": "ap" }
  ] }
```

- `pr-sitrep-on-push.yaml` triggers on a push to `main` that touches `apps/pr-sitrep/**`, `iac/projects/pr-sitrep/**`, `iac/projects/root.hcl`, `iac/env/**` or itself. `pr-sitrep-manual-deploy.yaml` deploys a dispatched branch to dev only. Both use the `ilg-platform/github-actions` reusable workflows at `0.1-affogato`, and apply notifies Slack through the workflow webhook [25][26].
- `iac/projects/root.hcl` loads `global.tfvars` plus the env's tfvars and keeps state in `gfs-bifrost-tfstate` (dev) or `gfs-bifrost-tfstate-prod` [27].
- The stack is one Cloud Run v2 service `pr-sitrep-<env>` in `bifrost-<env>-global1`, europe-west2: 0 to 1 instances, 1 CPU, 512 Mi, a 600 s request timeout and a `/health` startup probe. Around it sit a runtime service account, a scheduler service account with the only `run.invoker` binding, a Cloud Scheduler job, and `secretAccessor` grants [20][21][23][24].
- The scheduler job POSTs `/api/v1/sitrep/run` with an OIDC token at `0 9 * * 1-5` Europe/London, a 600 s attempt deadline and no retries. It is paused in every env except prod [23][28].
- The container sets `GITHUB_ALL_AUTHORS=true`, `GITHUB_ORGS=gfs-bifrost`, the `ilg-platform-ci` client id, `FALLBACK_WINDOW_DAYS=14` and `MERGE_ENABLED=false`. `SLACK_ENABLED` and the Slack token appear only when `local.slack_enabled` holds, which is `slack_enabled && env == "prod"` [20][28].
- Logs ship to Datadog from inside the container as `service:pr-sitrep`, dual-shipped to the ILG org. A monitor in `gfs-bifrost/observability` alerts when no 2xx run lands by 10:00 on a weekday, which covers a failed sweep, a failed Slack post and a run that never fired [20][29].

Live state on 2026-10-28: `pr-sitrep-prod` is at revision 00002 and `pr-sitrep-dev` exists. The prod job runs, and dev's is paused. It posts as the "Bifrost Deployments" Slack app (bot user `deployments`), first on 2026-10-28 [15].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "CLAUDE.md@d602d8e" },
  { "id": 2, "kind": "code", "ref": "apps/pr-sitrep/src/main.ts@d602d8e" },
  { "id": 3, "kind": "code", "ref": "apps/pr-sitrep/src/config/env/config.ts@d602d8e" },
  { "id": 4, "kind": "code", "ref": "apps/pr-sitrep/src/core/sitrep.service.ts@d602d8e" },
  { "id": 5, "kind": "code", "ref": "apps/pr-sitrep/src/adapters/github.client.ts@d602d8e" },
  { "id": 6, "kind": "code", "ref": "apps/pr-sitrep/src/adapters/jira.client.ts@d602d8e" },
  { "id": 7, "kind": "code", "ref": "apps/pr-sitrep/src/core/merge.service.ts@d602d8e" },
  { "id": 8, "kind": "code", "ref": "apps/pr-sitrep/src/core/publish.service.ts@d602d8e" },
  { "id": 9, "kind": "code", "ref": "apps/pr-sitrep/src/adapters/slack.client.ts@d602d8e" },
  { "id": 10, "kind": "code", "ref": "apps/pr-sitrep/src/bootstrap/factories/sitrep.factory.ts@d602d8e" },
  { "id": 11, "kind": "code", "ref": "apps/pr-sitrep/src/bootstrap/app.ts@d602d8e" },
  { "id": 12, "kind": "code", "ref": "apps/pr-sitrep/src/core/classification.ts@d602d8e" },
  { "id": 13, "kind": "code", "ref": "apps/pr-sitrep/src/http/middleware/error.middleware.ts@d602d8e" },
  { "id": 14, "kind": "code", "ref": "apps/pr-sitrep/src/http/sitrep.controller.ts@5e8fcb9" },
  { "id": 15, "kind": "log", "ref": "Live check 2026-10-28: pr-sitrep-prod (europe-west2, bifrost-prod-global1) at revision 00002, pr-sitrep-dev exists; prod scheduler at 09:00 weekdays with retry_count 0, dev paused; secrets created by hand with gcloud; first #bifrost-forge post 2026-10-28 as the Bifrost Deployments app (bot user deployments)" },
  { "id": 16, "kind": "code", "ref": "apps/pr-sitrep/package.json@d602d8e" },
  { "id": 17, "kind": "code", "ref": ".github/workflows/pr-sitrep-code-quality.yaml@d602d8e" },
  { "id": 18, "kind": "code", "ref": ".github/workflows/secops.yaml@d602d8e" },
  { "id": 19, "kind": "code", "ref": "apps/pr-sitrep/dockerfile@d602d8e" },
  { "id": 20, "kind": "code", "ref": "iac/projects/pr-sitrep/cloud-run.tf@d602d8e" },
  { "id": 21, "kind": "code", "ref": "iac/projects/pr-sitrep/iam.tf@d602d8e" },
  { "id": 22, "kind": "code", "ref": "apps/pr-sitrep/src/adapters/github-token.ts@d602d8e" },
  { "id": 23, "kind": "code", "ref": "iac/projects/pr-sitrep/scheduler.tf@d602d8e" },
  { "id": 24, "kind": "code", "ref": "iac/projects/pr-sitrep/secrets.tf@d602d8e" },
  { "id": 25, "kind": "code", "ref": ".github/workflows/pr-sitrep-on-push.yaml@d602d8e" },
  { "id": 26, "kind": "code", "ref": ".github/workflows/pr-sitrep-manual-deploy.yaml@d602d8e" },
  { "id": 27, "kind": "code", "ref": "iac/projects/root.hcl@d602d8e" },
  { "id": 28, "kind": "code", "ref": "iac/projects/pr-sitrep/variables.tf@d602d8e" },
  { "id": 29, "kind": "url", "ref": "https://github.com/gfs-bifrost/observability/blob/main/iac/projects/bifrost-observability/monitors.fuse-devtools.tf", "note": "[FUSE][PR Sitrep] Weekday run did not succeed: expects a 2xx by 10:00 on weekdays" }
] }
```
