---
title: "orient Sync — Migration State"
programme: "orient-sync"
status: active
owner: "hjf"
services: ["orient"]
created: "2026-11-12"
updated: "2026-11-12"
tags: [bifrost, migration-state]
---
# orient Sync — Migration State

<!-- The single source of truth for PROGRESS. The Overview carries the narrative and the verdict
     (the survey, the strategy); this doc is the live ledger. `wp programme status/next/tick` read
     and write the `## Unit status` tables below, so keep the table shape intact. -->

orient has no PRs or CI: a unit ships as commits on a `sync` branch in its own worktree, rebased and fast-forwarded onto `master` by the lead, then deployed (`pnpm deploy:all`, a named sha). The `PR` column holds the commit range. Builders are sonnet, one at a time. Each unit: build, `review-panel`, one consolidated fix round, gates on a quiet host (`typecheck`, lint count, `ui:check`, `ui:build`, `pnpm test`), deploy by sha, live check, tick, decision log, push.

## Unit status
Legend: ⬜ not started · 🟨 in progress · ✅ merged · ⛔ blocked · ⏸ deferred · ❌ dropped · 🔄 rescoped

Sequencing: S0 → S1 → S2 → S3 → S4 → S5 in series (they share the kernel cache, the adapters and the SPA data layer); S6 can run any time and is scheduled last. No interval is shortened below 5 minutes until S2 has landed.

### Runner and cache
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **S0** | ⬜ | Job runner in the kernel | | med | sonnet/high | | `src/core/kernel/jobs.ts`: a named job with an interval, jitter, a busy guard (no overlapping runs), exponential back-off with a cap on failure, a clean stop on shutdown (`core/main.ts:43-48` today abandons in-flight work), and a status record (lastRun, lastOk, lastError, nextRun, runs, failures). Intervals from `ORIENT_*` env with a `num()` fallback. Port onto it: the boot-only PR warm (`delivery/prs.ts:48`), the two 5-minute timers (`delivery/sprint.ts:312-325`, `today.ts:848`), and the four copy-pasted `look/tick` loops (`runs.ts:116`, `slack.ts:389`, `recordings.ts:246`, `usage/index.ts:119`; they poll only while an SSE page is open, so keep that rule as a job option). `GET /api/v1/health` gains the job list. Behaviour-preserving apart from back-off and visibility; no interval changes yet. Tests with fake timers: no overlap, back-off, stop, status. |
| **S1** | ⬜ | One cache | S0 | med | sonnet/high | | The kernel `SwrCache` is the only cache for PR and Jira data. Remove the duplicates (`delivery/jira.ts:22` slots, `pr/slots.ts:4`, `delivery/prs.ts:20` re-implementing `ops/last-good.ts`) and the adapter Maps that sit beneath the kernel TTL (`adapters/github.ts:167`, `jira-board.ts`, `jira.ts:93`), so `asOf` is truthful. Route every PR reader through `prs:open` (`domain/one-to-one.ts:103`, `focus-context.ts:114`, `ticket-prs.ts:73`). In-flight dedupe in the adapters (`github.ts:195`, `jira-board.ts:380`). Stop caching failures for the full TTL (`github.ts:246,467`). Keep SWR semantics and tag invalidation by orient's own writes (`prs` after a review write, `jira` after a Jira write). One `STORY_POINTS_FIELD`. |
| **S2** | ⬜ | Cheaper, rate-limit-aware GitHub | S1 | **high** | sonnet/high | | Replace about 143 REST calls per refresh with one GraphQL query per org (pull requests, review state, check rollup), or ETag conditional requests if GraphQL cannot give the fields; the builder measures both against the live account before choosing and records the call count. Read `x-ratelimit-remaining`, `x-ratelimit-reset` and `Retry-After`; on 403 or 429 stop calling until the reset, serve the last good value flagged rate-limited, never retry in a loop; keep a rolling budget so the job runner can lengthen an interval when the remaining budget is low. `adapters/github-actions.ts:227` uses `GITHUB_API`, not a literal host. The token is never logged. Verification: call count per refresh before and after, from a counting fetch wrapper in the tests. |
| **S3** | ⬜ | Disk snapshots | S1 | med | sonnet/medium | | Snapshot the kernel cache's PR and Jira keys to `~/.local/state/orient/cache/` (not the vault, not `index.sqlite`), restored on boot with their original `asOf` so a deploy shows data at its true age instead of empty. A schema version and the orient version in the file; an unreadable, old or mismatched file is ignored, never fatal. Written atomically, mode 0600, on a job interval and at shutdown; no tokens, no headers, nothing from `~/.secrets`. Size cap. Tests: restore keeps `asOf`, corrupt file ignored, version mismatch ignored, atomic write. |

### Sources and surface
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **S4** | ⬜ | Warm sources, coverage in config | S0, S1, S2 | low | sonnet/medium | | A job for each source with no warm-up: `tickets` (`delivery/tickets.ts:125` has no `start`), `work:statuses`, `knowledge:open-prs`, and the ticket page's issues that are open on a recent page. The orgs (`domain/open-prs.ts:9`) and Jira projects (`adapters/jira-board.ts:10`, `lib/ticket-key.ts:1`) move into the vault config next to `external.jiraBase`, with today's values as the default so nothing changes on deploy. Intervals chosen from the budget S2 reports. |
| **S5** | ⬜ | Freshness surface | S0, S1 | low | sonnet/medium | | `SourceNote.svelte` always shows the age, and says so when a value is rate-limited, errored or restored from a snapshot; a Sync view of the job list (last run, next run, failures) from the health route. Page-level `setInterval`s (`ui/src/routes/pr/[owner]/[repo]/[number]/+page.svelte:46,70`, `ci/[run]/+page.svelte:37`) move onto `ui/src/lib/data.svelte.ts` as its own rule says. Frontend lens in review; 390 px check. |
| **S6** | ⬜ | Deploy housekeeping | | low | sonnet/low | | The leftover `deployed/web` and `deploy-web.lock`; `deploy.sh` never restarts `orient-scribe` (decide: restart it or document why not); the false "Failed" line (ELIFECYCLE 143) logged on each deploy; `gate_no_runs` and `runs_in_core` referenced only by the retired `docs/cutover-u13.md` (verify before touching: the deploy flow does call `gate_no_runs`); hard-coded 5-minute constants left after S0. Records: CLAUDE.md and INSTALL.md describe the job runner and the snapshot. |

## Gates
- [x] **G1 — Approach agreed (in-process jobs plus disk snapshot, write-back out of scope)** — blocks S0. Cleared 2026-11-12 by Harry ("sure - sounds like a plan").

## Risks
- **R1 ★ GitHub rate limit** — about 143 calls a refresh against 5,000 an hour; more frequent polling on today's code would exceed it. Mitigation: S2 before any interval below 5 minutes, a budget that lengthens intervals, `Retry-After` honoured, a visible rate-limited state (S5) — open.
- **R2 ★ Two programmes, one repo** — Notes builders use the shared checkout; Sync works on a `sync` branch in a worktree. Sync owns `src/core/kernel/`, `src/core/modules/delivery/`, `src/adapters/{github,jira*}.ts`, `src/domain/{open-prs,ticket-prs,one-to-one,focus-context}.ts`, `ui/src/lib/delivery/`, `ui/src/lib/data.svelte.ts`; Notes owns `ui/src/lib/workspace/`, `ui/src/lib/editor/`, `src/core/modules/pages/`, `src/edit/`, `src/render/`. Shared hot files (`core/main.ts`, the module registry, `api/types/*`) are rebased by the lead; the full suite runs only on a quiet host, never beside a Notes builder's suite — open.
- **R3 ★ A snapshot is a new trust boundary** — a file the core reads at boot. Mitigation: outside the vault, mode 0600, schema and version checked, size-capped, no secrets in it, ignored (not fatal) when wrong — open until S3.
- **R4 A runner that hides failures** — today's bare `catch {}`. The runner records every failure in the status record and the log, with the error text capped and never containing a token — open until S0.
- **R5 Jira Cloud limits** — not measured. S4 adds jobs; S2's budget idea applies to Jira too if needed — standing.
- **R6 Deploys stay cold until S3** — S0 to S2 deploy with an empty cache, as today — standing.

## Decision log
<!-- Dated, newest first. -->
- **2026-11-12** — **Programme opened.** Harry: "let's /orchestrate some background services for orient too. i'd like to keep github pull requests as well as jira up to date. If there's any tech debt or normalisation that needs to be cleaned up as a part of this, let's cover that". Two read-only surveys (data flow; background services) found no scheduler, an in-memory cache emptied by every deploy, about 143 GitHub calls per refresh with no rate-limit handling, five cache mechanisms and four copy-pasted poll loops (full list in the Overview). The lead spot-checked: the PR list is warmed only at boot (`prs.ts:48`); TTL 60 s and retry 10 s (`cache.ts`); a 5-minute interval in `sprint.ts`; `PR_ORGS` hard-coded; the UI poll 60 s; the live `/api/v1/prs` answered `stale: true` (a stale value served while a refetch ran); `tickets` read `asOf: null` after the deploy. **Decision (Harry, "sure - sounds like a plan"):** in-process jobs in `orient-core` plus disk snapshots, not a new `orient-sync` unit (a separate process cannot warm the core's memory, and `index.sqlite` is disposable); write-back stays out of scope. Order S0 to S5 in series, S6 last, in a worktree beside the Notes programme.

## Scar tissue
- **Reads never wait on a source once a key has a value** — the kernel cache's stale-while-revalidate contract (`core/kernel/cache.ts`); every consumer assumes it.
- **Jobs live in `orient-core`** — the PR and Jira caches are the core's memory; do not add a unit to warm them.
- **`index.sqlite` is disposable** — it is rebuilt from the vault; snapshots go under `~/.local/state/orient/`, never into it or the vault.
- **Tokens** (`GITHUB_TOKEN`, `JIRA_API_TOKEN`, from env or `~/.secrets` via `src/config.ts`) are never logged, never in a snapshot, never in a status record.
- **orient's own writes invalidate by tag** (`prs` after a review write at `core/modules/pr/review.ts:252`, `jira` after a Jira write); keep that when the caches are merged.
- **`orient-index` exit 3 never restarts** — leave the unit's restart policy alone.
