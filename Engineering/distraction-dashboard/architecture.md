---
tags:
- waypoint
- distraction-dashboard
verified: '2026-10-13'
verified_sha: b628e29
verified_paths:
- code
- iac
- .github/workflows
- code/dockerfile
- code/middleware.ts
- code/pnpm-lock.yaml
- wishlist.md
- CLAUDE.md
- README.md
title: distraction-dashboard — architecture
thesis: A Next.js 15 app on a public Cloud Run service reads the GitHub REST API through
  one cached fetch and gates every route behind a single shared-login middleware;
  it deploys to dev only.
confidence: high
---
# distraction-dashboard — architecture

```orient-bluf
{ "v": 1, "bluf": "A Next.js 15 app on a public Cloud Run service reads the GitHub REST API through one cached fetch and gates every route behind a single shared-login middleware; it deploys to dev only.", "confidence": "high", "action": "Treat middleware.ts as the only gate, and bump the pinned next 15.2.4 before trusting it: the lockfile resolves a version with middleware-bypass advisories." }
```

## Guardrails

- [technical:G1] Every GitHub read goes through the one cached JSON GET in `lib/github/api.ts` (`unstable_cache` 180 s wrapped in React `cache()`). Keep new endpoints behind it and add no per-component pollers. The per-PR fan-out is acceptable only because of this cache.
  — paths: code/lib/github/api.ts, code/components/refresh-control.tsx
- [technical:G2] `middleware.ts` is the only auth gate. Pages and server actions never check the session themselves, so `PUBLIC_PATHS` stays `/login` and `/api/auth/login` and nothing else becomes public.
  — paths: code/middleware.ts, code/lib/auth/jwt.ts, code/app/api/auth
- [contract:G3] The app is read-only. It issues only GET requests to GitHub and holds no write token. A write action such as re-run needs a decision on who may hold a write token first.
  — paths: code/lib/github/api.ts, wishlist.md
- [technical:G4] Never remove a Next-managed `<head>` element from the DOM. React crashes reconciling the head on soft navigation and the page renders blank. `StatusBeacon` appends one link it owns and mutates only that.
  — paths: code/components/status-beacon.tsx
- [technical:G5] View-defining state lives in the URL through `nuqs`, never `useState`. `NuqsAdapter` stays wired once in the root layout. `useState` is for transient UI only.
  — paths: code/app/layout.tsx, code/components/pull-request-table.tsx, code/components/pull-requests-tabs.tsx
- [technical:G6] The beacon, home triage and pipeline board track the default branch, so a feature-branch run never masks a broken `main`. PR buckets stay mutually exclusive in the order draft, blocked, approved, ready, and `isDraft` comes from `pull.draft`.
  — paths: code/lib/github/service.ts, code/components/pull-request-table.tsx, code/components/status-beacon-section.tsx

## Layout and request path

```orient-flow
{ "v": 1, "title": "How a page view reaches GitHub",
  "nodes": [
    { "id": "b", "label": "Browser tab", "sub": "60 s auto-refresh", "kind": "external", "ev": [10] },
    { "id": "lb", "label": "HTTPS load balancer", "sub": "managed cert, no Cloud Armor", "kind": "step", "ev": [4] },
    { "id": "mw", "label": "middleware.ts", "sub": "session cookie check", "kind": "step", "tone": "accent", "ev": [1] },
    { "id": "sc", "label": "Server components", "sub": "and three server actions", "kind": "step", "ev": [5] },
    { "id": "sv", "label": "GithubService", "sub": "shapes the reads", "kind": "step", "ev": [6] },
    { "id": "ca", "label": "Cached GET", "sub": "180 s, shared", "kind": "store", "ev": [2] },
    { "id": "gh", "label": "GitHub REST API", "sub": "gfs-bifrost org", "kind": "external", "ev": [2] }
  ],
  "edges": [
    { "from": "b", "to": "lb" },
    { "from": "lb", "to": "mw", "label": "Cloud Run" },
    { "from": "mw", "to": "sc", "label": "valid session" },
    { "from": "sc", "to": "sv" },
    { "from": "sv", "to": "ca" },
    { "from": "ca", "to": "gh", "label": "miss" }
  ] }
```

```
code/
  app/            (dashboard) route group in the GLayout shell; /login and /api/auth/* sit outside it
  actions/        three server actions: PR detail, run logs, job logs
  components/     app components; primitives come from @ilg-platform/ui-toolkit
    home/         KPI, nightlies, pull-request and Renovate panels
  lib/
    github/       api.ts (cached fetch) -> service.ts (shaping) -> server components; dto/ holds response types
    auth/         jwt.ts (edge-safe), session.ts (cookies), auth.type.ts
    config.ts     lazy, validated env access
    jira.ts       FUSE key extraction and ticket URLs
    diff.ts, log-parser.ts, log-colorizer.ts, log-presenter.ts   PR diff and CI log rendering
  middleware.ts   the single auth gate
iac/              Terraform/Terragrunt, dev only, no prod.tfvars
```

Data flow: `lib/github/api.ts` (one cached JSON GET per URL) feeds `lib/github/service.ts` (shaping). That feeds server components (`*-section.tsx`, `*-server.tsx`) and then client components (tables, controls). `githubService` is a lazy proxy, so `next build` needs no runtime env [3][6].

| Route | Shows |
| --- | --- |
| `/` | Distraction duty home: KPIs, nightlies, recent PRs, open Renovate PRs |
| `/pull-requests` | Tabs `today` (default, PRs created in the last 24 h) and `queue`; a PR detail modal deep-links through `?pr=repo/number` |
| `/nightlies` | Latest scheduled run per repo on the default branch |
| `/workflows`, `/workflows/[repo]/[runId]` | Pipeline board with history dots, and one run's jobs and logs |
| `/repo/[repoName]` | One repo's PRs and runs |
| `/login`, `POST /api/auth/login`, `POST /api/auth/logout` | Login page and the cookie endpoints |

## The caching model

Every GitHub read goes through **one** cached fetch in `lib/github/api.ts`: `unstable_cache` (180 s, shared across requests) wrapped in React `cache()` (per-render dedupe). The token is read inside the closure, so the secret never becomes part of the cache key [2]. Consequences, all deliberate:

- Calling the same service method from layout, page, beacon and nav badges is nearly free. The code relies on this instead of threading data through props.
- The 60 s client refresh is cheap because most refreshes hit the cache [7].
- Per-PR fan-out (detail, reviews, check runs and a Jira lookup, once per PR) is acceptable only behind this cache.
- Job logs are the one uncached read. They are large, per-view and follow a redirect [2].

## GitHub API surface

All calls are GETs from `GithubAPI` in `api.ts` [2]:

- **Org and repo:** `orgs/{org}/repos` (archived and disabled repos are filtered out), `repos/{org}/{repo}`.
- **Pull requests:** `pulls?state=open`, `pulls/{n}` detail, `/reviews`, `/files`, `/commits`, `/comments`, `issues/{n}/comments`, and `commits/{ref}/check-runs`.
- **Actions:** `actions/runs?per_page=30` (with `&event=schedule` for nightlies), `actions/workflows`, `actions/runs/{id}/jobs`, `actions/jobs/{id}/logs`, and `contents/{path}` to read a workflow file's `on:` block.
- **Search:** `search/issues` for PRs created in the last 24 h and for all open org PRs. Search has its own 30 requests per minute limit, and the cache keeps it near one call per window.

**Not built.** `/deployments`, dependabot and code-scanning alerts, `/rate_limit`, branch protection, and run timing or artifacts are unused. Parsing a workflow's cron into an expected cadence is parked in `wishlist.md`. The nightlies board already flags a run older than 26 h as stale [8].

## Auth: one shared login, enforced in middleware

`POST /api/auth/login` compares the submitted email and password to the `BASIC_AUTH_USER` and `BASIC_AUTH_PASSWORD` env vars with plain `===`. On a match it sets an HS256 `session` cookie through `jose`, `httpOnly`, `sameSite=lax`, `secure` in production, valid 30 days [9][1].

`middleware.ts` decrypts the cookie and redirects everything except `/login` and `/api/auth/login`. Its matcher skips `_next/static`, `_next/image` and any path ending in a file extension. The dashboard layout decrypts the cookie again only to show the email. No page or action enforces a session of its own [1][5].

## Exposure and dependency findings

- **ASSESSED** The service faces the public internet. `cloud-run.tf` sets `ingress = "INGRESS_TRAFFIC_ALL"` and grants `roles/run.invoker` to `allUsers`, and the code comment says auth is enforced in the app. The load balancer has no Cloud Armor or IAP, and the default `*.run.app` URL answers directly [4]. Org-level policy outside this repo could narrow that.
- **ASSESSED** The pinned `next` 15.2.4 sits in advisory ranges. `pnpm audit --prod` on the committed lockfile on 2026-10-13 lists the critical flight-protocol RCE (fixed in 15.2.6) and two high App Router middleware bypasses (fixed in 15.5.16 and 15.5.18). The gate is middleware only, so a bypass would reach the org's PR diffs and CI logs. I did not test reachability against the live service [11].
- **ASSESSED** The same audit lists 3 critical and 29 high advisories in total across `next`, `axios`, `postcss`, `sharp`, `nanoid`, `form-data` and `source-map-js`. The repo has no `secops` workflow, so no CI step runs an audit [11][12].
- **CONFIRMED** The dockerfile declares `ARG GITHUB_TOKEN` and `ENV GITHUB_TOKEN` in the shared `base` stage, so the runner image inherits the build token. `docker-build-push@0.1-affogato` passes `secrets.npm_token`, which is `GH_TOKEN`, as that build arg [13][14].
- **CONFIRMED** `GITHUB_TOKEN`, `BASIC_AUTH_PASSWORD` and `SESSION_SECRET` are plain Cloud Run env vars, with no Secret Manager. Anyone with `run.viewer` on the project can read them, and `wishlist.md` says so. Terraform state holds the session secret and both variables [4].
- **ASSESSED** The app token is the org-wide `GH_TOKEN` per the README. `wishlist.md` calls it read-scoped, but nothing in the repo shows its scope.
- **CONFIRMED** The login route has no rate limit or lockout. Cloud Run caps the service at 3 instances [9][4].

## URL is the state

View-defining state (filters, sort, tabs, the selected PR) lives in the URL through `nuqs` (`useQueryState` with typed parsers). The product is a pinned tab you bookmark and share, so a URL-encoded view has to survive the 60 s refresh and a link to a teammate. It costs nothing extra, because the root layout sets `dynamic = "force-dynamic"` and reads are cached. `useState` stays for transient UI: modals, loading flags, in-modal log search [5][10].

## Domain semantics

- PR queue buckets are mutually exclusive, in order: **draft, blocked** (changes requested, or CI failing or pending), **approved**, **ready**. "All" hides drafts. Default sort is oldest reviewable first [15].
- `isDraft` comes from `pull.draft`. GitHub's `state` is only `open` or `closed`, and conflating them was a real bug [6].
- Diff stats are not on the PR list endpoint, only on the per-PR GET. Merge-readiness chips ("Conflicts" for `dirty`, "Behind base" for `behind`) read `mergeable_state` from that same detail [6][15].
- Review state is each reviewer's latest substantive review. `COMMENTED` and `PENDING` are ignored, and a standing `CHANGES_REQUESTED` beats any approval [6].
- Pipeline board: "Red for" is the oldest failure in the current consecutive streak, and "Flaky" is three or more pass/fail transitions in the last 10 runs. History dots run oldest to newest [16].
- Nightlies are the latest `event=schedule` run on the default branch. A repo drops out if its workflow no longer declares a cron or its workflow file was deleted [6].
- Runs of deleted workflows are filtered out, because GitHub keeps serving them. A repo deleted while still in a cached list drops out instead of failing the board [6].

## UI gotchas

- **Wrap `GDataTable` in `overflow-clip`, never `overflow-hidden`.** A hidden wrapper becomes the scroll container for the sticky header and displaces it over the first rows [15].
- **Route-level `loading.tsx` paints skeletons on client navigation.** In-page `<Suspense>` only covers initial streaming.
- **Log and terminal panes stay always dark.** Everything else uses semantic tokens.

## No test suite, and `build:check` does not type-check {#no-tests}

`pnpm test` is an echo, by design. The bar before pushing is `lint:fix` and `build:check`, then a real run: log in through `POST /api/auth/login`, feed the cookie to headless Chrome (`playwright-core` and system `google-chrome`), and screenshot. Exercise soft navigation by clicking sidebar links. The head-reconciliation bug passed every full-load smoke test [10].

`build:check` is `next build`, and `next.config.mjs` sets `typescript.ignoreBuildErrors` and `eslint.ignoreDuringBuilds`. A type error therefore passes the CI gate. Only Biome lint can fail it [3][17].

## Build and deploy

```orient-flow
{ "v": 1, "title": "Push to main to dev",
  "nodes": [
    { "id": "p", "label": "Push to main", "sub": "or manual-deploy on any branch", "kind": "step", "ev": [12] },
    { "id": "d", "label": "docker-build-push", "sub": "GH_TOKEN as build arg", "kind": "step", "ev": [12, 14] },
    { "id": "ar", "label": "Artifact Registry", "sub": "dev-<sha> tag", "kind": "store", "ev": [12] },
    { "id": "tg", "label": "terragrunt apply", "sub": "-auto-approve, dev only", "kind": "step", "ev": [12] },
    { "id": "cr", "label": "Cloud Run", "sub": "0 to 3 instances, 512Mi", "kind": "service", "service": "distraction-dashboard", "tone": "accent", "ev": [4] },
    { "id": "lb", "label": "HTTPS load balancer", "sub": "serverless NEG", "kind": "step", "ev": [4] },
    { "id": "dns", "label": "DNS A record", "sub": "ilg-platform zone", "kind": "step", "ev": [18] }
  ],
  "edges": [
    { "from": "p", "to": "d" },
    { "from": "d", "to": "ar" },
    { "from": "ar", "to": "tg", "label": "image tag" },
    { "from": "tg", "to": "cr" },
    { "from": "tg", "to": "lb" },
    { "from": "tg", "to": "dns" }
  ] }
```

- **Toolchain.** pnpm 9.15.4, Node 22, Biome 1.9.4, Terraform 1.9.0 and Terragrunt 0.50.8 (`mise.toml`) [17].
- **Pipelines.** `deploy.yaml` builds and applies to dev on every push to `main`. `manual-deploy.yaml` deploys any branch to dev. `tf-plan-pr.yaml` comments a plan on `.tf` and `.hcl` changes. `code-quality.yaml` runs `test`, `lint` and `build:check`. All call `ilg-platform/github-actions@0.1-affogato`. There is no `secops` workflow [12].
- **Runtime.** Cloud Run in `bifrost-dev-global1`, europe-west2, 1 CPU, 512Mi, 0 to 3 instances, port 3000. The image is `output: "standalone"` on `node:22-alpine` and runs as a non-root user [4][13].
- **DNS.** The A record lives in the ilg-platform zone (project `ilg-platform-ec02`). The zone name comes from ilg-platform's core-infra remote state, not the Bifrost one [18].
- **Package auth.** The docker build and the Code Quality install both need GitHub Packages auth for `@ilg-platform/ui-toolkit`, wired from the org `GH_TOKEN` secret. A 403 on install means check that token's `read:packages` access to `ilg-platform` first [12][13].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "code/middleware.ts@b628e29" },
  { "id": 2, "kind": "code", "ref": "code/lib/github/api.ts@b628e29" },
  { "id": 3, "kind": "code", "ref": "code/lib/github/index.ts@b628e29" },
  { "id": 4, "kind": "code", "ref": "iac/projects/distraction-dashboard/cloud-run.tf@b628e29" },
  { "id": 5, "kind": "code", "ref": "code/app/(dashboard)/layout.tsx@b628e29" },
  { "id": 6, "kind": "code", "ref": "code/lib/github/service.ts@b628e29" },
  { "id": 7, "kind": "code", "ref": "code/components/refresh-control.tsx@b628e29" },
  { "id": 8, "kind": "code", "ref": "code/components/home/home-nightlies.tsx@b628e29" },
  { "id": 9, "kind": "code", "ref": "code/app/api/auth/login/route.ts@b628e29" },
  { "id": 10, "kind": "code", "ref": "CLAUDE.md@b628e29" },
  { "id": 11, "kind": "code", "ref": "code/pnpm-lock.yaml@b628e29", "note": "next 15.2.4, resolved against pnpm audit on 2026-10-13" },
  { "id": 12, "kind": "code", "ref": ".github/workflows/deploy.yaml@b628e29" },
  { "id": 13, "kind": "code", "ref": "code/dockerfile@b628e29" },
  { "id": 14, "kind": "doc", "ref": "ilg-platform/github-actions .github/workflows/docker-build-push.yaml at tag 0.1-affogato (d52202b), lines 84-86", "note": "docker build --build-arg GITHUB_TOKEN=secrets.npm_token" },
  { "id": 15, "kind": "code", "ref": "code/components/pull-request-table.tsx@b628e29" },
  { "id": 16, "kind": "code", "ref": "code/components/workflow-runs-list-server.tsx@b628e29" },
  { "id": 17, "kind": "code", "ref": "code/next.config.mjs@b628e29" },
  { "id": 18, "kind": "code", "ref": "iac/projects/distraction-dashboard/remote.tf@b628e29" }
] }
```
