---
tags:
- waypoint
- fuse-ui
verified: '2026-10-09'
verified_sha: f9a7700
verified_paths:
- code/src/observability
- .github/workflows
- iac/projects/fuse-ui
- code/src/config.ts
- iac/env
- code/src/lib/api-client/fuse-tracker
title: fuse-ui — operations
---
# fuse-ui — operations

## Deploy

`deploy.yaml` on push to `main` (and also to the stale `master` branch — its
trigger is `branches: [main, master]`); `manual-deploy.yaml` for on-demand dev deploys;
`tf-plan.yaml` for plan-only. Each Deploy run applies dev, plans prod, then **parks at
the `terraform-prod` environment gate** (bifrost-admins approve, via the UI or the
`pending_deployments` API) — merging to `main` never reaches prod on its own. The prod
service is `fuse-ui-app-prod` (europe-west2, `bifrost-prod-global1`), not `fuse-ui`.

- **An approval ships the run's whole tree**: every commit on `main` between the live
  prod image's sha and the run's sha, not just the PR that triggered it. Several sessions
  merge to `main` concurrently, so before approving list
  `git log <prod-sha>..<run-sha>` and account for every foreign commit (its PR's notes on
  flags/ordering).
- **Every merge parks its own run**, so after one is approved the older parked runs are
  rollback hazards — approving one later would roll prod back to its older sha. Approve by
  sha, newest only.
- A PR's `tf-plan` can fail `Error acquiring the state lock` on `dev/fuse-ui` while a Deploy
  run's dev apply holds it, and a dev apply can fail loading another stack's remote state
  (e.g. replay's) on a transient GCS read — both clear on rerunning the failed job.

Cloud Run behind a GCP load balancer
(`iac/projects/fuse-ui/{cloud-run,load-balancing,dns,network}.tf`), own MongoDB
(`mongo.tf`), Secret Manager refs (`secrets.tf`) for things like `SESSION_SECRET`.
The DNS zone is read from the ilg-platform `core-infra` state (`remote.tf`); the Bifrost
`core_infra` read stays only for the config-service key. `SHOPIFY_CONNECTOR_URI` and
`SHOPIFY_CONNECTOR_API_KEY` come from shopify-connector's own remote state, deliberately
not wrapped in `try`, so an environment that can't read it fails the apply instead of
shipping a dead Test button (previews fall back to dev's state).

**Feature flags are Terraform variables** (`feature_flag_*` in `variables.tf`, default `false`, set per
environment in `iac/env/{dev,prod}.tfvars`, passed as Cloud Run env in `cloud-run.tf`). Dictionaries (prod since 2026-10-14), EDI egress
(prod since 2026-10-14) and the order tracker are on in both. The tracker also needs
`fuse_tracker_api_url`, the IAM-private tracking-service API's Cloud Run URL, which doubles as the ID
token audience. The app refuses to boot with the tracker flag on and no valid URL. The
`run.invoker` grant for fuse-ui's runtime service account lives in tracking-service's IaC
(`api_extra_invokers`), not here, so a new environment needs both sides applied. Keep
`feature_flag_edi_egress` off wherever sftp-connector's own EDI flag is off, and turn sftp's on first.

`AUDIT_LOG_RETENTION_DAYS` (`variables.tf` → `cloud-run.tf`, set in both
`iac/env/{dev,prod}.tfvars`) is the TTL on the `audit_log` collection, and is
**24855 — a placeholder, not a chosen retention window**. MongoDB's TTL
`expireAfterSeconds` is a 32-bit signed int, so 24855 days (~68 years) is the
largest whole-day "keep forever" that doesn't overflow and throw on every
`ensureAuditLogIndexes()` call. Left unset, no TTL index is created at all and
rows are kept indefinitely — which matters because config-change rows carry full
before/after snapshots of connector documents, credentials included.

**Per-PR preview environments** are a first-class feature here
(`fuse-ui-preview-env-{deploy,destroy,sweep}.yaml`), unlike most backend services
in the fleet — `dev-pr-<n>` naming in the shared `gs://gfs-bifrost-tfstate` bucket.
The nightly sweep no longer decides teardown from tfstate presence alone: it
enumerates live Cloud Run services, service accounts and Atlas users, cross-checks
each against its PR, and reaps only the **stateless orphans** — resources
Terraform holds no state for, which the old state-only path missed permanently (a
service could outlive its state and keep serving while its PR was commented
"ALREADY GONE"). It skips any env that still has state or holds a lock so it never
races the terraform path, and reaps an env only once it is older than
`MIN_AGE_MINUTES`. An **open PR's env is never reaped** — those are surfaced in a
"Needs attention — not reaped" list instead; reaping is limited to
closed/merged/gone PRs. A manual (`workflow_dispatch`) run **reports only unless
`reap_for_real` is ticked**; the scheduled run always reaps. The
shared-bucket/prefix-based discovery pattern is still fleet-wide and has caused one
real cross-service incident (a different service's sweep destroying fuse-ui's own
preview state) — see [[known-context]].

Previews read **dev config-service**, so a dev runtime feature flag applies to every
preview as well; tfvars-based preview isolation doesn't cover it. Live checks use a
throwaway key (e.g. `fuse-ui.smoke-test`) and delete it afterwards.

## Observability (no APM)

Logging runs on the shared `@gfs-bifrost/observability` SDK (over
`@ilg-platform/observability`), which replaced the local winston stack
(`observability/logger/{format,logger,transports}.ts` and `tags.ts` are gone).
Domain log lines are catalogued events (`@gfs-bifrost/observability` `event()`), with
fuse-ui's own in `observability/events/` (auth, bootstrap, client error, master data).
Server code logs through two Next bundles: `observability/server-only-bundle.ts`
is the **eager** one (pino + DogStatsD socket), guarded by `import 'server-only'`
so an accidental client/edge import is a build error;
`observability/hmr-safe-bundle.ts` is the **lazy** twin
(`FuseObservabilityLazyBuilder`, built on first server-side use) for `'use server'`
actions reachable from a client/edge graph, keeping the Node-only socket off the
client path. `getRequestLogger()` (`observability/logger/server-logger.ts`)
child-binds the authenticated user. `proxy.ts` derives the `correlationId` via
`ensureCorrelationId(req.headers)` from `@ilg-platform/observability-next/middleware`
(no longer the hand-rolled `x-request-id`-or-uuid) and writes it back onto the
request-id header — trace a session's activity by that correlation id. Datadog is
dual-shipped to the GFS + ILG orgs like the rest of the fleet.

Two operator-portal `fuse.*` metrics are emitted: **`fuse.support_flow.action`**
from the server actions (`replay` / `dedupe_release` / `credential_link` /
`config_save` / `dismiss` / `assign` / `unassign`) and **`fuse.bff.dependency`**
from the BFF api-clients (`config` / `collector` / `replay` / `dedupe` / `ots` / `fuse-tracker`) and the
retrieval-condition preview call (`shopify-connector`).
fuse-ui-only vocab lives in local per-domain catalogue files under
`observability/metrics/`; shared primitives come from the package.

### Browser RUM

Datadog browser RUM (errors + Core Web Vitals) via `@datadog/browser-rum`,
initialised once client-side by `observability/rum/datadog-rum.tsx` (a
`'use client'` component rendered in the root layout). Config is resolved
server-side (`config.rum`) and passed across the server→client boundary as a prop
— `NEXT_PUBLIC_*` is build-time-inlined and can't carry per-env runtime values.
Every RUM value is IaC-driven (Cloud Run `DD_RUM_*` env from
`iac/projects/fuse-ui/{variables,cloud-run}.tf` + `iac/env/global.tfvars`); only
the always-on `track*` toggles and a `beforeSend` live in code. `beforeSend`
(`observability/rum/scrub-url.ts`) redacts sensitive query-param values from RUM
event URLs before they leave the browser (name-substring match, biased to
over-redact). An empty `applicationId`/`clientToken` disables RUM (the init
no-ops), and **Session Replay is deferred** (`sessionReplaySampleRate` 0).

## Real failure modes

- **The order tracker page is blank or errors with the flag on**: the tracker API is private, so a
  403 from it means the ID-token identity lacks `run.invoker` (tracking-service IaC), and an
  unreachable API surfaces as "The tracker API could not be reached" in the page, not a 500. Look at
  `fuse.bff.dependency` for `fuse-tracker`.

- **A build-time boundary break**: importing anything that pulls in server-only
  dependencies (e.g. a file that touches the Mongo client) from a component
  meant to run client-side breaks the client bundle — and only `next build`
  catches it, not `tsc`/lint. Watch for this when refactoring across the
  `lib/db`/`server-functions` boundary.
- **A silently-swallowed formatting error**: at least one date-formatting helper
  has thrown internally on a specific `Intl` option combination
  (`dateStyle` + `timeZoneName` together) and been caught by a wrapper that
  rendered a bare `—` instead of surfacing the error — so a green CI run and even
  a manual smoke-test can look fine while a real formatting bug hides behind a
  silent fallback. Don't trust "it didn't throw" as proof a date/time render path
  is correct; check the actual rendered value.
- **A cross-service remote-state dependency**: this app's Terraform reads from
  dedupe-service's remote state for at least one output — deploy dedupe-service
  first if both are changing together, or a fuse-ui apply can fail or read stale
  values.
- **Client-visible errors from server components**: `error.tsx`/`global-error.tsx`
  exist as Next's error boundaries; a thrown error in a Server Component surfaces
  through these rather than a raw 500 — check here first for "the page is blank"
  reports before assuming an API call failed silently.

## Evidence-gathering for UI changes

Screenshot evidence for a fuse-ui change typically needs: a local Mongo, dev
config pointed at real (or seeded) data, and Puppeteer — headless clipboard
operations need an explicit CDP permission grant, they don't work by default.

`next dev` (16.x, no `agentRules` set in `next.config.ts`) writes untracked
`code/AGENTS.md` + `code/CLAUDE.md` and rewrites the tracked `code/next-env.d.ts` on every
local run. Nothing ignores them — delete/restore them after a local run and never stage them.

A fresh worktree has no `.next/types/routes`, so `pnpm run typecheck` fails with a wall of
`AppHref` errors until `pnpm exec next typegen` has run. In component specs, `jest.mock` paths
must be relative: the SWC transform rewrites `@/` only in imports. The ESM-only
`@ilg-platform/ui-toolkit/*` subpaths need a `virtual: true` mock.
