---
title: "pr-sitrep Go — Port Design"
created: "2026-10-29"
tags: [bifrost, pr-sitrep, golang]
---
# pr-sitrep TypeScript → Go port: design reference

> [!warning] Reference, not the ledger
> This is the planning agent's draft, kept for its file map, layout table and byte-parity risk list.
> Sequencing, unit boundaries, cutover timing and decisions live in [[pr-sitrep Go/Migration State|Migration State]], which supersedes this doc wherever they differ. Known superseded points:
> - Increments 4, 5 and 7 are split there (A1/A2, V1/V2, and X1 only; no 7b because the repo stays polyglot).
> - Cutover is an **afternoon** merge after that day's 09:00 TS post, not "approve before 09:00".
> - `mise.toml` **keeps** node and pnpm. fuse-devtools is polyglot.
> - Monitor 337903215 can't prove a run. Verify through the scheduler's last attempt, logs, and exactly one header posted.
> - The golden generator and `parity.sh` stay **uncommitted**.

## Bottom line and corrections to the agreed shape

The agreed five-step shape holds. Before increment 1, five facts change parts of it:

1. **`go-runtime:0.1-affogato` exists.** audit-service on main (`e1d526e`, "Build FROM the go-runtime rolling tag") builds from `europe-west2-docker.pkg.dev/ilg-platform-ec02/images/go-runtime:0.1-affogato`. Datadog serverless-init is its entrypoint, so the dockerfile sets `CMD` only. audit-service PR #16 carried the same `DD_*` env over unchanged, so `cloud-run.tf` needs no new env.
2. **Swapping the image needs no Terraform change.** `cloud-run.tf` takes `var.image_name`, and `pr-sitrep-on-push.yaml` passes it in after building `apps/pr-sitrep/dockerfile`. Cutover is the dockerfile plus the workflows. In `iac/projects/pr-sitrep` only the `node24-runtime` comment changes.
3. **Fuse already has a Go layout.** audit-service uses `code/cmd/api` with `internal/{adapters,bootstrap,config,core,http/{controllers,middleware,respond},models,observability,repositories}`, chi, a hand-rolled config validator and a `slog` Datadog handler. ilg-merak's `svc-template/AGENTS.md` writes the same layout down as rules. Copy it rather than inventing one. It is still new for fuse-devtools: the repo CLAUDE.md says "node 24, pnpm, biome, vitest", so a human needs to confirm it.
4. **Slack message shape can be checked for parity without posting.** `GET /api/v1/sitrep?format=slack` returns the message plan: kinds, order and text before mrkdwn conversion. The only things it leaves out are mention ids and the `toMrkdwn` step, which offline goldens cover (increment 6).
5. **The README is stale.** It says "The job never retries", but `scheduler.tf` has `retry_count = 3` since `6465a40` today. Fix it at cutover.

The prod run is watched by Datadog monitor 337903215, which counts Cloud Run 2xx responses for `pr-sitrep-prod`. It does not depend on log fields. Its runbook text names the `"Request failed"` log message, so keep that message string verbatim.

## (a) Critical files and boundaries

**TS source of truth** (`apps/pr-sitrep/src`):
- `core/classification.ts`, `core/sitrep.service.ts`, `core/render/{markdown.renderer,slack.renderer,mrkdwn}.ts`
- `adapters/{github.client,github-token,jira.client,slack.client}.ts`
- `config/env/config.ts`, `http/sitrep.controller.ts`, `http/middleware/{correlation,error}.middleware.ts`
- `core/{publish,merge,scheduled-run}.service.ts`, `observability/{logger,tags}.ts`, `cli.ts`

There are 284 vitest `it` cases across 14 spec files. The biggest are classification (68), github.client (36), markdown (24), slack.renderer (20), jira (19) and app (19).

**Deploy surface:**
- `.github/workflows/pr-sitrep-{code-quality,on-push,manual-deploy}.yaml` and `secops.yaml`
- `mise.toml`, root `README.md` and repo `CLAUDE.md`
- `iac/projects/pr-sitrep/cloud-run.tf` (comment only)

**Proposed Go layout** (new for this repo; needs human sign-off):

| TS | Go |
|---|---|
| `main.ts`, `cli.ts` | `cmd/pr-sitrep/main.go`, `cmd/sitrep/main.go` (audit-service has two cmds too) |
| `config/env/config.ts` | `internal/config` |
| `models/*.ts` | `internal/models` (pull request, sitrep and GitHub port DTOs) |
| `models/ports.ts` interfaces | small interfaces in the package that calls them (`core/sitrep` declares `Github`, `Jira`, `Slack`), per svc-template |
| `core/classification.ts` | `internal/core/classify` |
| `core/render/*` | `internal/core/render` |
| `core/*.service.ts` | `internal/core/sitrep` (sweep, merge, publish, scheduled run) |
| `adapters/*` | `internal/adapters/{github,jira,slack}` (token code in `github`) |
| `exceptions/*` | `internal/exceptions` (`ConfigurationError`, and `IntegrationError{System, Status}` for github, jira and slack) |
| `http/*` | `internal/http/{controllers,middleware,respond}` |
| `observability/*` | `internal/observability` (`slog` handler adapted from audit-service) |
| `bootstrap/*` | `internal/bootstrap` (wiring plus routes) |
| `shared/clock.ts` | dropped: pass `func() time.Time` and a sleep func through constructors (svc-template rule) |

Imports go one way: `bootstrap` → all; `http` → `core` → (interfaces only); `adapters` → `models`/`exceptions`. `core` imports no `net/http`.

## (b) Increments

During the stack, the Go code lives at **`apps/pr-sitrep-go/`**. Its `go.mod` module path is already the final one, `github.com/gfs-bifrost/fuse-devtools/apps/pr-sitrep`. A binary module's path doesn't have to match its directory, so the move at cutover rewrites no imports.

Nothing under `apps/pr-sitrep/**` changes until increment 7, so `pr-sitrep-on-push.yaml` (filtered to that path) never fires and prod stays on TS until then.

**1. Skeleton: toolchain, config, logging, health, CI** (about 700 lines)
- Build:
  - `mise.toml`: add `go = "1.27.3"` (svc-template) or `1.26.9` (audit-service). Pick one; it must equal the `go.mod` `go` line.
  - `apps/pr-sitrep-go/{go.mod, Makefile (copy audit-service: fmt-check, vet, test-race, lint), .golangci.yml, go-audit-allow.jsonc, dockerfile, .dockerignore}`.
  - dockerfile: `golang:<pin>` build stage with `CGO_ENABLED=0`, then `FROM go-runtime:0.1-affogato`, `USER nonroot:nonroot`, `ENV PORT=3000`, `CMD ["/app/pr-sitrep"]`.
- Config: port all of it, with the zod-equivalent rules spelled out in risk 4.
- `observability`: copy audit-service's handler. Keep base tags `domain/service/environment/host`; `source` is a decision (risk 10).
- `/health` and `main` (startup failure prints to stderr and exits 1).
- Workflows:
  - `pr-sitrep-go-code-quality.yaml`: hand-rolled like audit-service's, with setup-go from `go.mod`, fmt-check, build, vet, `test -race` and golangci-lint. Path-filtered to `apps/pr-sitrep-go/**` plus itself.
  - `secops.yaml`: add `secops-dep-go.yaml@0.2-bonbon` with `working_directory: apps/pr-sitrep-go` and an explicit `go_version`, because its default is `"1.25"`. Also add `secops-code` with `lang: go` and a second `secops-container` job.
- **Verify:**
  - The 8 `config.spec` cases are translated with the same names and pass.
  - All CI jobs are green, including govulncheck and Trivy on the go-runtime image.
  - `docker run` serves `GET /health`, and the body matches TS byte-for-byte (`{"status":"ok","service":"pr-sitrep","environment":"local"}`).

**2. Models and classification** (about 1,100 lines; mostly tests)
- `classify.go` with `IsBotLogin`, `DetectSelfHold`, `ExtractTicketKey`, `EvaluateEvidence`, `CountWorkingDaysBetween`, `SummariseChecks`, `ResolveReviewDecision`, `Classify` and `Summarise`.
- The model structs declare fields in TS object-literal order, so JSON keys come out in the same order.
- **Verify:**
  - All 68 `classification.spec` cases are ported as `t.Run("<identical it string>")`.
  - A name-set check (a small script diffing `it("…")` against `t.Run("…")`) shows zero missing names.
  - Goldens generated by the TS functions for edge inputs pass. Inputs: CRLF bodies, NBSP and BOM whitespace, an emoji at UTF-16 offset 799–800, more than 200 UTF-16 units, re-run checks with a null app id.

**3. Renderers** (about 1,100 lines)
- `markdown`, `slack` and `mrkdwn`, with the exact emoji code points (`⚠️` is U+26A0 U+FE0F).
- `orderWithinState` uses `golang.org/x/text/collate` (en-US) for `localeCompare`, and `sort.SliceStable` for both the author sort and the createdAt sort.
- **Verify:**
  - 56 cases ported (24 markdown, 20 slack, 12 mrkdwn), same name-set check.
  - A login-collation golden matches Node: a list such as `alice, Bob, ab-c, abc, x_gfsdev, X-1, 9z`, sorted by `localeCompare` in the TS app and committed as `testdata`.
  - Render goldens of a captured real payload (markdown, Slack plan, and post texts through `toMrkdwn` with a fixed mentions map) are byte-equal to TS output.

**4. Adapters** (about 1,400 lines; split into 4a GitHub plus token and 4b Jira plus Slack if the 500–700-line target matters)
- GitHub client:
  - Base URL is injected so tests use `httptest`; clock and sleeper are injected too.
  - Re-read `mergeable_state` up to 3 times at 1.5s intervals while it is `unknown`, then once more if the PR is at least `REFRESH_DAYS` old. Age is measured before the retries.
  - Pagination rules: search stops at `seen >= total_count` or an empty page; reviews and check runs stop on a page shorter than 100.
  - Default branches are cached for the process lifetime, behind a mutex.
  - Squash merge, then delete the branch and ignore a failed delete.
- App token:
  - stdlib RS256 with JWT header `{"alg":"RS256","typ":"JWT"}` and claims `iat=now-60`, `exp=now+540`, `iss=clientId`.
  - Before parsing the key, replace literal `\n` sequences with newlines. Accept PKCS#1 or PKCS#8 keys; reject non-RSA keys with `got <type>`.
  - Cache one token per owner (mutex) and refresh it when less than 5 minutes remain.
- Jira: `POST /rest/api/3/search`, take the first `active` sprint, fall back to the window rule. A Jira error is still a 502, not a fallback.
- Slack: `ok:false` with `users_not_found` returns no id; post with `unfurl_*: false`.
- Error message text stays the same: `"<system>: <METHOD> <path> failed with <status>: <200-char excerpt>"`.
- **Verify:** 85 cases ported (github 36, token 15, jira 19, slack 15). Any request-shape assertion (URL, query, headers, body keys) checks the same values TS sends.

**5. Services, HTTP, bootstrap, CLI, and a dev deploy path** (about 1,300 lines)
- `SitrepService` processes PRs **one at a time, with no goroutine fan-out**, and resolves stacking after the sweep. Also port `MergeService`, `PublishService` (mention lookups first, then posts in order; a failed post doesn't stop the rest) and `ScheduledRunService`.
- HTTP layer:
  - chi routes.
  - Correlation id: `x-correlation-id` echoed after trim, else a uuid v4.
  - Error mapping: `IntegrationError` → 502, anything else → 500, body `{error, correlationId}`, logged as `"Request failed"`.
  - `POST /run` returns 502 if any post failed. The run uses `context.WithoutCancel(r.Context())` so a dropped client doesn't abort it, matching Node.
- `cmd/sitrep` takes `--format` and pretty-prints like `JSON.stringify(x,null,2)`.
- Add `pr-sitrep-go-manual-deploy.yaml`. It is a copy of the manual-deploy workflow with `working_directory: apps/pr-sitrep-go` and the same `iac/projects/pr-sitrep`, so it targets `pr-sitrep-dev` (scheduler paused, Slack off). Give it `notify_on_failure` only, per the org rule.
- **Verify:**
  - 67 cases ported (sitrep 18, merge 9, publish 16, scheduled-run 5, app 19), plus `go test -race`.
  - Dispatch to dev, then with an identity token: `/health` returns 200; `GET ?format=json|markdown|slack` returns 200; `POST /api/v1/sitrep/run` returns 200 with `"posts":[]`.
  - Datadog shows `service:pr-sitrep env:dev` JSON logs ("Gathered open pull requests", "Classified…", "Scheduled sitrep run complete").
  - This also proves the go-runtime image has CA roots for outbound TLS.

**6. Parity gate** (a script plus evidence; nothing deploys)
- Add `apps/pr-sitrep-go/scripts/parity.sh`. It starts TS (`node dist/main.js`, PORT 3101) and Go (PORT 3102) locally from **one env file** that copies prod: `GITHUB_ORGS=gfs-bifrost`, `GITHUB_ALL_AUTHORS=true`, `FALLBACK_WINDOW_DAYS=14`, no Jira, the same GitHub App key (dev secret `pr-sitrep-github-app-key`).
- For each format it fetches TS, then Go, then TS again. It removes only `generatedAt`, then diffs **raw bytes**. A run counts only if the two TS responses are identical, meaning the data didn't move; otherwise it retries, up to N times. Don't run it near 00:00 UTC, because the idle-day counts would change mid-run.
- Second pass with a PAT and Jira creds to exercise the Jira path. If `/rest/api/3/search` is gone, both must fail identically (502 with the same message).
- **Pass criterion:** zero byte diff on json, markdown and slack on two separate days with different PR sets. Attach the outputs as PR evidence. Make the cutover PR depend on it.

**7. Cutover**
- `git rm -r apps/pr-sitrep`, then `git mv apps/pr-sitrep-go apps/pr-sitrep`.
- Workflows:
  - Rewrite `pr-sitrep-code-quality.yaml` to the Go gates.
  - Delete the `pr-sitrep-go-*` workflows.
  - `secops.yaml`: drop the node dep-audit, `lang: ts` and node container jobs, and point the Go jobs at `apps/pr-sitrep`.
  - The on-push and manual-deploy workflows need no change (same dir and dockerfile).
- `mise.toml`: drop node and pnpm. Update the repo `CLAUDE.md` toolchain section, both READMEs (go-runtime, retries) and the `cloud-run.tf` comment.
- **Timing:** merge so that dev applies first. Verify dev as in increment 5. Approve the `terraform-prod` gate **before 09:00**, then hit prod `GET /health` and `GET ?format=json` (read-only) as the scheduler SA. Let the 09:00 scheduled run be "the run": a manual run on a day that has already posted would post twice.
- **Verify:**
  - Prod 09:00 run returns 2xx (monitor 337903215 stays OK).
  - The #bifrost-forge messages match the previous day's TS posts in shape and order.
  - Prod logs show `"Scheduled sitrep run complete"`.
- **Rollback:** `gcloud run services update-traffic` back to the last TS revision immediately, then revert the PR to bring Terraform back in line.

## Answers to the open questions

- **Layout:** as in the table, following audit-service and svc-template. It needs human confirmation as a new convention for this repo, and the repo CLAUDE.md must be rewritten at cutover.
- **Coexistence:** yes. Keep Go at `apps/pr-sitrep-go` until increment 7. Prod can't switch before the parity gate because the deploy workflow's path filter never sees Go code until the move. The `terraform-prod` approval is a second guard, not the main one.
- **Idempotency:** out of scope, because a port shouldn't change behaviour. TS double-posts today: a 502 after a partial post gets retried, and the retry reposts the header and every PR. Go keeps that, including `WithoutCancel`, so a timed-out attempt still finishes. File a follow-up ticket for same-day idempotency to land after cutover, for example a GCS or Firestore marker per London date, or retrying only on 429/5xx-before-post.
- **Libraries:**
  - Router: chi v5 (audit-service precedent; `NotFound`/`MethodNotAllowed` can be overridden).
  - Validation: hand-rolled, collecting every issue, like audit-service's `config.validator`. No validator library.
  - Logging: `log/slog` JSON handler from audit-service.
  - JWT: stdlib `crypto/rsa` and `encoding/base64`; no golang-jwt.
  - Also `google/uuid` and `golang.org/x/text/collate`. That makes three direct dependencies, which keeps govulncheck noise low.

## (c) Options considered and rejected

- **Build Go under `apps/pr-sitrep/` alongside TS.** Every stacked PR would fire the prod deploy pipeline and its approval gate. Rejected.
- **Replace on a long-lived branch with one big PR.** It can't be reviewed against the 500–700-line target, and it gives up the green-main checkpoints. Rejected.
- **Stdlib `ServeMux`.** It would work for three routes, but it answers a wrong method with 405, Express answers 404, and audit-service uses chi. Rejected in favour of chi.
- **golang-jwt.** It adds a dependency for about 20 lines of RS256. Rejected.
- **Comparing prod TS against dev Go for parity.** Prod has no human invoker and the two calls are minutes apart. Running both locally with one credential is more reliable. Rejected.
- **Parallelising the PR sweep in Go.** It changes GitHub request pressure and when `mergeable_state` gets read. Rejected.
- **Real Slack posts to a scratch channel for parity.** It needs a bot in a test channel and human sign-off. The offline post-text goldens cover the same ground. Rejected.

## (d) Parity risks and what I couldn't establish

1. **JSON encoding:**
   - Go's encoder escapes `< > &` by default; turn that off with `SetEscapeHTML(false)`.
   - `Encode` adds a trailing `\n` that Express doesn't send; trim it.
   - **Nil slices encode as `null`.** `failing`, `prs`, `merges`, `messages` and `posts` must be initialised as `[]`.
   - Go escapes U+2028/U+2029 and Node doesn't.
   - Use `omitempty` only on `rawExcerpt` and the two `error` fields. Everything else that can be null is a pointer (`holdReason`, `ticketKey`, `reviewDecision`, `stackedOnOpenPR`, `sha`, `ts`, `sprintName`, `author`).
   - Keep GitHub's timestamps as the raw strings, not reformatted. Format `generatedAt` as `toISOString` does (always 3 millisecond digits, `Z`).
2. **Ordered maps.** `summariseChecks` relies on JS `Map` insertion order. In Go, `failing` order needs a slice of keys alongside the map, or the hold reasons will reorder.
3. **JS vs RE2 regex and string semantics:**
   - JS `\s` and `.trim()` cover Unicode whitespace and BOM; Go `\s` is ASCII and `TrimSpace` doesn't trim BOM.
   - In JS multiline mode, `$` and `.` treat `\r` as a line end. Expect CRLF bodies.
   - `.length > 200` and `.slice(0, 800)` count UTF-16 units. A slice that cuts a surrogate pair gives JSON a lone `\ud83d`, which a Go string can't hold. That residual edge case stays documented.
4. **zod vs a hand-rolled validator:**
   - An empty-but-set variable is an error for optional strings and enums, so use `os.LookupEnv`.
   - `z.coerce.number` follows `Number()`: `""` → 0 (passes `nonnegative`, fails `positive`), whitespace is trimmed, `0x`/`1e1` are accepted.
   - Booleans accept exact `true`/`false` only.
   - `z.email()` uses lookaheads that RE2 lacks, so it has to be done in code. `z.url()` is approximated.
   - zod's own error *wording* won't match; the custom rule messages and their order will.
5. **`localeCompare` collation.** I couldn't confirm Node's default ICU locale in `node24-runtime`. Before trusting the increment-3 golden, check `Intl.Collator().resolvedOptions().locale` in that image.
6. **Express behaviour Go won't copy exactly (declared differences):**
   - Express sets an `ETag` (and answers 304) and `X-Powered-By`.
   - Express routing ignores case and a trailing slash.
   - Express's 404 page is HTML (`Cannot GET`).
   - A malformed JSON body on `POST /run` gives 500 in TS; Go ignores the body. The scheduler sends none.
   - TS includes `stack` in error bodies outside prod; Go has no equivalent.
   - Content types stay `application/json; charset=utf-8` and `text/markdown; charset=utf-8`.
   - A repeated `?format=` is treated as `json`, and an empty `?format=` gives 400.
7. **Search order.** `/search/issues` with no sort is GitHub's "best match", which may not be stable between calls. Increment 6's TS/Go/TS bracket catches this. If it isn't stable, compare a sorted copy too.
8. **Go-specific HTTP behaviour.** Go's HTTP client has no default timeout; Node's undici times out after 300s on headers and body, so set the same on the Go client. Concurrent requests need mutexes on the token and default-branch caches.
9. **Jira endpoint.** Atlassian may have retired `POST /rest/api/3/search`. Prod has no Jira creds, so it's dormant. Port it as-is and flag it.
10. **Log `source` tag.** TS sends `"nodejs"`; audit-service sends `"go"`. The only monitor is metric-based, so it's safe to change, but someone needs to choose. Message strings and meta keys stay verbatim.
11. **Test translation.** The goldens in increments 2–3 need a transitional generator that imports `apps/pr-sitrep/src` from inside the Go dir. That breaks "no cross-app imports" for the length of the stack. Delete it at cutover and keep the frozen goldens.

### Critical files for implementation
- `/home/hjf/code/fuse/fuse-devtools/.claude/worktrees/pr-sitrep-go/apps/pr-sitrep/src/core/classification.ts`
- `/home/hjf/code/fuse/fuse-devtools/.claude/worktrees/pr-sitrep-go/apps/pr-sitrep/src/adapters/github.client.ts`
- `/home/hjf/code/fuse/fuse-devtools/.claude/worktrees/pr-sitrep-go/apps/pr-sitrep/src/core/render/markdown.renderer.ts`
- `/home/hjf/code/fuse/fuse-devtools/.claude/worktrees/pr-sitrep-go/apps/pr-sitrep/src/config/env/config.ts`
- `/home/hjf/code/fuse/fuse-devtools/.claude/worktrees/pr-sitrep-go/.github/workflows/pr-sitrep-on-push.yaml`
- Reference precedent: `/home/hjf/code/fuse/audit-service` at `e1d526e` (`code/dockerfile`, `code/internal/observability/log.go`, `code/internal/config/config.go`, `.github/workflows/{code-quality,secops}.yaml`)