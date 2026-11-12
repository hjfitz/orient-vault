---
title: "orient Sync — Overview"
status: active
verdict: go
owner: "hjf"
services: ["orient"]
created: "2026-11-12"
updated: "2026-11-12"
tags: [bifrost]
---
# orient Sync — Overview

## Deliverables
- [[orient Sync/Migration State|Migration State]] — the live source of truth for progress
- Seven units, S0 to S6: a job runner in the core kernel, one cache, cheaper rate-limit-aware GitHub reads, disk snapshots, warm sources and config-driven coverage, a freshness surface, and deploy housekeeping.

## Verdict
**Go.** Harry asked (2026-11-12) for background services that keep GitHub pull requests and Jira up to date in orient, with any tech debt cleaned up on the way, and agreed the approach: **in-process jobs inside `orient-core` plus a disk snapshot**, not a new process. Write-back (moving a Jira ticket when its PR merges) is out of scope unless Harry asks for it.

## Why this needs a programme
Seven changes share one fragile surface (the kernel cache, the GitHub and Jira adapters, the SPA's data layer) and one hard external limit (GitHub's 5,000 requests an hour). A faster poll on today's code would exceed that limit, so the order matters: the job runner and the single cache come first, the cheaper GitHub reads before any interval is shortened, and snapshots only once there is one cache to snapshot.

## Starting state (two read-only surveys, 2026-11-12; the lead spot-checked the load-bearing claims)
Paths are under `src/`. Builders verify every citation before relying on it.
- **Nothing refreshes PR or Jira data on its own schedule.** The kernel's stale-while-revalidate cache (`core/kernel/cache.ts`, 60 s TTL, 10 s retry after a failure) refetches behind a read. The PR list is warmed once at boot (`core/modules/delivery/prs.ts:48`); two 5-minute timers exist (`delivery/sprint.ts:312-325`, `core/modules/today.ts:848`). The SPA polls every 60 s while a tab is visible (`ui/src/lib/data.svelte.ts:10`).
- **All of it is in memory**, so every deploy empties it. `tickets` reads `asOf: null` right after a deploy; `work:statuses`, `knowledge:open-prs` and the ticket page have no warm-up either.
- **Cost.** GitHub REST: a search per org plus three calls per PR (pull, check-runs, reviews), about 143 calls for 47 PRs per refresh, no ETags, no `Retry-After` or rate-limit header handling, failures cached for the full TTL (`adapters/github.ts:167,195-248`). One refresh a minute would be about 8,600 calls an hour.
- **No scheduler.** `orient-index` has its own timers (`scripts/index-watch.ts:276,356,371-373`); the core has ad hoc intervals (`core/kernel/index-watch.ts:65`, `focus-watch.ts:156`) and four copy-pasted `look/tick` loops (`delivery/runs.ts:116`, `slack.ts:389`, `recordings.ts:246`, `usage/index.ts:119`). Failures are mostly bare `catch {}`; only focus-watch backs off.
- **Five cache mechanisms**: adapter Maps (`github.ts:167`, `jira-board.ts`, `jira.ts:93`), the kernel `SwrCache`, bespoke slot caches (`delivery/jira.ts:22`, `pr/slots.ts:4`), and `adapters/exec.ts` `runJson` (CLI only). Some PR readers bypass `prs:open` (`domain/one-to-one.ts:103`, `focus-context.ts:114`, `ticket-prs.ts:73`). The adapter caches sit under the kernel TTL, so `asOf` can understate age by up to 60 s.
- **Coverage is in code**: orgs `gfs-bifrost` and `ilg-platform` (`domain/open-prs.ts:9`), Jira project `FUSE` (`adapters/jira-board.ts:10`, `lib/ticket-key.ts:1`).
- **The UI hides age** unless a value is stale or errored (`ui/src/lib/components/SourceNote.svelte`); `/api/v1/health` lists module names only.
- **Units on the VM**: `orient-core`, `orient-index`, `orient-scribe` and the 90 s `orient-vault-sync.timer` are running and healthy; `desk`, `tunnel` and `vault-follow` exist in `systemd/` but are not installed here. Adding a unit means `systemd/`, `scripts/install-units.sh`, `scripts/deploy.sh`, a `package.json` script and the docs, which is the cost the in-process choice avoids.

## Strategy
- **In-process jobs.** The PR and Jira data live only in the core's memory, so a separate process cannot warm them; the one cross-process bridge is `index.sqlite`, which is disposable. A `CoreModule.start()` hook is the existing no-plumbing route. A separate `orient-sync` unit would survive core restarts, but the snapshot gives the same benefit.
> SUPERSEDED 2026-11-12 — no worktree. `CLAUDE.md:22` forbids git worktrees on this machine (a second `node_modules` is too heavy), and the Notes programme's own ledger says the same. Sync units run one at a time in the main checkout on `master`, staged by explicit path, and only while no Notes builder is running: the full-suite gates run on the working tree, so it has to be clean. S0 to S5 therefore wait for the Notes unit in flight to deploy.
- **Series, in a separate worktree.** S0 to S5 run one at a time on a branch in its own worktree (the Notes programme holds the shared checkout), rebased and fast-forwarded onto `master` by the lead, then deployed by sha as before: `gate_no_runs`, `pnpm deploy:all`, a live check, a tick. Full-suite gates run only on a quiet host.
- **Review.** Each unit gets a `review-panel` (backend, tests, plus security on S2 and S3 where tokens and files are involved, plus frontend on S5) before it is deployed.

## Scar tissue
See the State doc. The short form: reads never wait on a source once a key has a value; the index database is not for snapshots; tokens are never logged or snapshotted.

## Next
S0, driven by `waypoint-programme`.
