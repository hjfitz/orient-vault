---
title: pr-sitrep Go — Migration State
programme: pr-sitrep-go
status: planning
owner: Harry Fitzgerald
services:
- fuse-devtools
created: '2026-10-29'
updated: '2026-10-29'
tags:
- bifrost
- migration-state
---
# pr-sitrep Go — Migration State

Why and how: [[pr-sitrep Go/Overview|Overview]]. File map, Go layout table and byte-parity hazards: [[pr-sitrep Go/Port Design|Port Design]].

**Repo:** `~/code/fuse/fuse-devtools` · **worktree:** `.claude/worktrees/pr-sitrep-go` (branch `hjf/pr-sitrep-go`, cut from `origin/main` `6465a40`, upstream unset). Every unit gets its own branch, `hjf/pr-sitrep-go-<unit>`, stacked on the previous unit's branch.

**Coexistence:** Go lives at `apps/pr-sitrep-go/` until `X1`, under the final module path `github.com/gfs-bifrost/fuse-devtools/apps/pr-sitrep`. Nothing under `apps/pr-sitrep/**` changes before `X1`, so `pr-sitrep-on-push.yaml` (path-filtered to that dir) never fires and prod stays on TS.

## Unit status
Legend: ⬜ not started · 🟨 in progress · ✅ merged · ⛔ blocked · ⏸ deferred · ❌ dropped · 🔄 rescoped

### Foundations
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **S1** | ✅ | Go skeleton, config, health, CI, dev deploy path | | medium | sonnet/medium | #10 | **What:** Go 1.27.3 in `mise.toml` (node and pnpm stay), matching the `go.mod` line. `apps/pr-sitrep-go/{go.mod, Makefile, .golangci.yml, dockerfile on go-runtime:0.1-affogato, .dockerignore}`. Full config port. slog Datadog handler (`source:"go"`). `/health`. `pr-sitrep-go-code-quality.yaml`. `secops.yaml` Go jobs, with an explicit `go_version` because the default is 1.25. **`pr-sitrep-go-manual-deploy.yaml` lands here** because `gh workflow run` needs the file on main. Both deploy workflows get the fixed concurrency group `deploy-pr-sitrep-dev`, and dev `notify_on_success` is dropped. Repo `CLAUDE.md` gains a polyglot toolchain section and the Go layout. **Verify:** the 8 `config.spec` cases under the same names, plus Go tests for all 5 cross-field rules (G2/G3 refusals) and the defaults. `/health` body is byte-equal to TS. All CI jobs green, including govulncheck and Trivy. Find out whether paused `pr-sitrep-dev` can be run with `gcloud scheduler jobs run`. |

### Core port
Characterisation: every TS `it` becomes a `t.Run` with the identical name, and a name-set diff shows zero missing (287 tests in total). Goldens come from an **uncommitted** generator that imports the TS. Only the goldens are committed, each carrying the TS sha it came from.

| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **C1** | ✅ | Models + classifier | S1 | high | sonnet/high | #11 | 68 `classification.spec` cases. Struct field order matches TS literal order. Edge goldens: CRLF, NBSP/BOM, emoji at UTF-16 799–800, >200 units, re-run checks with a null app id. `summariseChecks` keeps Map insertion order (slice of keys). |
| **C2** | ✅ | Renderers: markdown, slack, mrkdwn | C1 | high | sonnet/high | #12 | 56 cases (24/20/12). `localeCompare` via `x/text/collate`. Check the node24-runtime ICU locale before trusting the collation golden. Stable sorts. Emoji code points exact. Render goldens from a captured real payload. |
| **A1** | ✅ | GitHub client + app token | C1 | high | sonnet/high | #13 | 51 cases (36 client, 15 token). `mergeable_state`: up to 3 re-reads 1.5 s apart while `unknown`. The long-idle re-read happens **only when the state isn't `unknown` after those retries**, with age measured from `updated_at` against the injected clock. JSON `null` → `""` must not loop. Stdlib RS256, `\n` unescape, PKCS#1/#8, a per-owner token cache with a mutex. 300 s client timeout. |
| **A2** | ✅ | Jira + Slack adapters | C1 | low | sonnet/medium | #14 | 34 cases (19 Jira, 15 Slack). `POST /rest/api/3/search` ported as-is (dormant in prod, may be retired upstream). Slack `users_not_found` → no id. `unfurl_*: false`. Error text `"<system>: <METHOD> <path> failed with <status>: <excerpt>"`. |
| **V1** | ✅ | Core services: sitrep, merge, publish, scheduled run | C2, A1, A2 | high | sonnet/high | #15 | 48 cases (sitrep 18, merge 9, publish 16, scheduled-run 5). Sequential sweep with **no goroutine fan-out**. Stacking is resolved after the sweep. Mentions are looked up first, then posts go out in order, and one failed post doesn't stop the rest. |
| **V2** | ✅ | HTTP, bootstrap, CLI, dev verification | V1 | medium | sonnet/medium | #16 | 19 `app.spec` cases. chi. `x-correlation-id` echoed after trim, else uuid v4. IntegrationError → 502, else 500, logged as `"Request failed"` verbatim. `POST /run` uses `context.WithoutCancel`. JSON: `SetEscapeHTML(false)`, trim the trailing `\n`, `[]` never `null`, U+2028/2029 post-pass. **Verify on dev:** dispatch the Go manual deploy, run `gcloud scheduler jobs run pr-sitrep-dev` (dev never posts), check Datadog `service:pr-sitrep @environment:dev` for "Scheduled sitrep run complete" (this also proves CA roots for outbound TLS), then give dev back to TS. |

### Cutover
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **X1** | 🟨 | Atomic move: Go replaces TS in prod | V2 | high | opus/medium | #17 | `git rm -r apps/pr-sitrep && git mv apps/pr-sitrep-go apps/pr-sitrep`. Rewrite `pr-sitrep-code-quality.yaml` to Go gates. Delete the `pr-sitrep-go-*` workflows. In `secops.yaml`, drop the TS jobs and repoint the Go ones. App README (go-runtime, retries are 3 not 0). `cloud-run.tf` comment. Revertable in one PR. Plan-then-proceed on the terraform-prod gate. Merge **in the afternoon**, after that day's 09:00 TS post. **Verify:** dev as in V2. Next morning, scheduler last attempt is a single 2xx, logs show "Scheduled sitrep run complete", and #bifrost-forge has **exactly one** header. Then run `waypoint-refresh` on the fuse-devtools vault docs (G5, architecture, overview, `waypoint.yaml`). |

### Follow-ups
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **F1** | ⏸ | Same-day idempotency | X1 | medium | sonnet/high | | Stops a retry from double-posting after a partial post. Also covers overlapping runs when an attempt overruns its 600 s deadline and the scheduler retries while the first is still posting (`WithoutCancel`). Options: a per-London-date marker (GCS/Firestore), or retrying only on 429/5xx before the first post. Ticket it after cutover. |

## Gates
- [x] **G1 — Parity: zero byte diff on two separate days** — blocks X1. Run TS and Go locally from one env file that mirrors prod (`GITHUB_ORGS=gfs-bifrost`, `GITHUB_ALL_AUTHORS=true`, `FALLBACK_WINDOW_DAYS=14`, GitHub App key read from **outside the repo**, **no Slack token**, **never `POST /run`**). Fetch `GET /api/v1/sitrep?format=json|markdown|slack` as TS, then Go, then TS again. Strip only `generatedAt` and diff raw bytes. A pass counts only if both TS reads match. Check the GitHub rate limit between passes and stay away from 00:00 UTC. Clears on two days with different PR sets, with the outputs attached to X1's PR as evidence.
  - **Day 1 (2026-10-29 16:16–16:27 GMT): PASS.** 41 live PRs in gfs-bifrost. json 38,092 B, markdown 7,558 B and slack 3,536 B were byte-identical, content types too, and the two TS reads matched in every format. Go built from `hjf/pr-sitrep-go-v2`, TS at `b8d938c`.
  - **Day 2 (2026-10-31 11:01–11:16 GMT): PASS.** 32 live PRs, 13 fewer or different than day 1, with the window since 2026-10-17. json 30,172 B, markdown 5,740 B and slack 1,694 B were byte-identical, content types too, and the two TS reads matched. Run from `main` at `5e0c215`, which has both apps.
- [x] **G2 — Cutover window** — blocks X1. Merge only after that day's 09:00 TS post has landed in #bifrost-forge, so the next morning's run is Go's first and nothing double-posts.
  - **Cleared 2026-10-31.** The scheduled cutover job fired a day late (a usage-limit pause), on a Saturday. Fri 2026-10-30's TS run made one scheduler attempt (09:00:02, 200, 75.6 s), logged `Scheduled sitrep run complete` (prs 33, posted 7, source nodejs), and posted exactly one `PR status — 2026-10-30` header plus 6 PR messages to #bifrost-forge. Nothing runs at weekends, so merging on Saturday keeps Monday 2026-11-02 09:00 as Go's first run and nothing double-posts.


## Risks
- **R1 ★ Byte parity** — Known hazards: JSON escaping, nil → `null`, U+2028/2029, `Encode`'s trailing `\n`, Map order, JS regex/`\s`/`trim`/UTF-16 vs Go, zod coercion, `localeCompare`. Mitigated by characterisation goldens in C1, C2, A1 and V2, plus the G1 bracket. Express differences that are declared and accepted: ETag/304, `X-Powered-By`, case-insensitive routing, the HTML 404, a malformed POST body, `stack` in non-prod errors. See Port Design §(d). — open.
- **R2 ★ G3 rests on one check** — The ilg-platform-ci app has `pull_requests:write`, not read-only, so the `loadConfig` refusal of `MERGE_ENABLED` with app creds or `GITHUB_ALL_AUTHORS` is the only thing stopping merges. Port it exactly and test all 5 cross-field rules in S1. — open.
- **R3 Double post on retry** — `retry_count = 3` (PR #9) plus a 502 after a partial post means the header and every PR get posted again. The port keeps this behaviour. Fixed by F1. — standing.
- **R4 Shared dev state** — Both deploy workflows apply the same dev Terraform state, and the last apply wins. The fixed concurrency group `deploy-pr-sitrep-dev` serialises them (S1). Give dev back to TS after every Go verification until X1. — standing.
- **R5 The monitor can't prove a run** — Monitor 337903215 (`sum(last_2h)` of any 2xx) is passing with No Data right now. X1 verifies via the scheduler's last attempt, logs, and the Slack header count instead. — standing.
- **R6 GitHub rate limit in parity** — Each pass costs a full sweep per format, times three. Check `/rate_limit` between passes. — open.
- **R7 Datadog API key in plaintext env** — `DD_ADDITIONAL_ENDPOINTS` carries a key in the Cloud Run env. It should move to Secret Manager. Out of scope here; flagged separately. — open.

## Decision log
- **2026-10-31** — **Cut over (X1, #17 → `ba9780f`).** The prod plan was the image plus `DD_VERSION`, with the service-level `scaling` 0→null no-op also seen in #9. `terraform-prod` was approved, and `pr-sitrep-prod-00006-b8v` (`prod-ba9780f`) is Ready and takes 100% of traffic. Go logged `pr-sitrep is listening` (source go, prod) and the startup probe passed at 11:13:50. The scheduler was not run by hand. **Rollback target: `pr-sitrep-prod-00005-4fd`.** X1 stays 🟨 until Monday's 09:00 run is verified.
- **2026-10-29** — **Cutover is scheduled for Fri 2026-10-30 13:07, after day-2 parity and the 09:00 TS post. The first Go prod run is Mon 2026-11-02 09:00, verified at 09:23.** Both are session-only cron jobs (`3d9144fb`, `605c5e6a`). If the session ends first, run the same steps by hand from #17's notes.
- **2026-10-29** — **After any apply, check `status.traffic` before reading a run as Go's.** On dev the Go revision went Ready about 4 minutes after its startup probe passed, and a run in that window went to the TS revision.
- **2026-10-29** — **Dev verification resumes, runs and re-pauses `pr-sitrep-dev`.** A paused job refuses `jobs run` (`FAILED_PRECONDITION: Job.state must be ENABLED`). The three steps run in one command, and dev never posts. Terraform still holds `paused`, so the next apply re-asserts it anyway. No human invoker.
- **2026-10-29** — **Sequential merges, not a long stack.** Code review is suspended this week and main has no required reviews. Each unit merges once green, so later units branch from main, and every merge is announced in the #bifrost-forge thread.
- **2026-10-29** — **Go mimics Express routing** (case-insensitive, trailing slash, 404 for an unrouted method, HEAD follows GET). That leaves ETag/304, `X-Powered-By`, the HTML 404 page, and `stack` in non-prod errors as the only declared differences.
- **2026-10-29** — **Programme, not a single plan.** The port is 8 PRs plus a calendar-gated parity check across several sessions. The unit ledger fits that better than one oversized plan.
- **2026-10-29** — **Go layout accepted** for fuse-devtools: `cmd/pr-sitrep` (+ `cmd/sitrep` CLI) and `internal/{config,models,core/{classify,render,sitrep},adapters/{github,jira,slack},exceptions,http/{controllers,middleware,respond},observability,bootstrap}`. Copied from audit-service and ilg-merak's `svc-template/AGENTS.md`. Interfaces are declared in the consuming package. Clock and sleep are injected; no `shared/clock`.
- **2026-10-29** — **fuse-devtools stays polyglot.** `mise.toml` keeps node and pnpm next to go, and the repo `CLAUDE.md` documents both toolchains (S1). No post-cutover tidy-up unit is needed.
- **2026-10-29** — **No TS freeze.** Harry is the only maintainer. Any TS behaviour change during the stack carries the matching Go change and regenerated goldens in the same PR. Renovate dependency bumps without behaviour changes need nothing.
- **2026-10-29** — **Defaults:** Go 1.27.3 (svc-template; audit-service is on 1.26.9). Log `source:"go"`; message strings and meta keys stay verbatim. Scheduler retries stay at 3 on cutover day. The golden generator and `parity.sh` stay uncommitted, so G1 (no cross-app imports) needs no waiver.
- **2026-10-29** — **Idempotency is out of scope** for the port, because a port shouldn't change behaviour. Deferred to F1.
- **2026-10-29** — **Vault G5 knowingly overridden** by PR #9 (`retry_count` 0 → 3 with backoff). The fuse-devtools durable docs still say 0. They get refreshed at X1 rather than now.

## Scar tissue
- **Dev never posts, and nobody can invoke pr-sitrep by hand.** Only `pr-sitrep-sched-{dev,prod}` holds `run.invoker`, and impersonating it is refused even for a project Owner. Never add a human invoker binding (guardrail G5 privacy). Dev is verified through `gcloud scheduler jobs run`, and GET parity runs locally.
- **`DD_ENV=serverless` in both envs.** Query dev logs as `service:pr-sitrep @environment:dev`, not `env:dev`.
- **Keep `"Request failed"` verbatim.** The monitor runbook names it.
- **The sweep is sequential.** Parallelising it changes GitHub request pressure and when `mergeable_state` gets read.
- **`POST /run` survives a dropped client** (`WithoutCancel`), matching Node. This is part of why R3 exists, and F1 has to account for it.
- **On-push path breadth:** anything under `apps/pr-sitrep/**` deploys to prod. Don't touch that dir before X1, not even a README.
- **`secops` nightly may go red again after cutover**, as the Go dependency and container scans start covering `apps/pr-sitrep`. Triage per the root CLAUDE.md order.
