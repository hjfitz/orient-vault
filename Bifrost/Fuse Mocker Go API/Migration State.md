---
title: Fuse Mocker — Go API Migration State
status: complete
owner: Harry Fitzgerald
created: '2026-08-22'
updated: '2026-09-10'
tags: [bifrost, fuse-mocker, golang, migration, migration-state]
---

# Fuse Mocker — Go API Migration State

> **Single source of truth for progress.** Read and updated by the `fuse-mocker-go` skill on
> re-entry. Update Status as units land; never assume progress — read this table. Move
> superseded notes to the Decision Log rather than deleting them.

Rationale + target architecture: [[Bifrost/Fuse Mocker Go API/Overview|Overview]]

**Repo:** `~/code/fuse/fuse-mocker` — now `apps/ui/` (Next) + `apps/api/` (Go), `iac/`, `.github/workflows/`
**Working branch:** `hjf/go-api` in `.claude/worktrees/go-api`, off `origin/main` at `519d15e`

## Status: ✅ Complete. Deployed to dev, fully cut over.

`main` is at `cc806b7`. The Go API owns the HTTP surface, the Pub/Sub push endpoints, the
scheduler and the load-run engine. The Next app is a presentation client.

| verified live, after the final cutover | result |
| --- | --- |
| MCP contract smoke via the load balancer | all checks passed |
| UI at `/login` | `200` |
| a real publish | `bifrost.dev.confirmation_ready.v1`, messageId returned |
| API scaling | `minScale = maxScale = 1`, CPU throttling off |
| `BACKGROUND_LOOPS_ENABLED` | `true`, and the boot log agrees |
| the ten capture push subscriptions | on `/events/v1/confirmation/capture/*` |

**Totals:** ~13k lines of Go (2.1k generated from Zod), **1,335 Go tests** across 25 packages,
365 UI tests, 28 spec paths, and **~9,590 lines plus 90 npm packages removed** from the UI.
build / vet / gofmt / golangci-lint (0 issues) / full `-race` / `terraform validate` / biome /
`next build` / `tsc` all clean.

### The cutover, in the order it had to happen

1. Deploy both services, flags `false`. Nothing observable changes.
2. `api_serves_traffic = true` — the load balancer, fuse-mcp and the push subscriptions move.
3. `X4` — delete the Next API and, critically, gut `instrumentation.ts`.
4. `api_owns_background_loops = true` — only valid after step 3, because two owners fire every
   schedule twice and the symptom is duplicate records rather than an error.

The UI moved onto the API at step 1 rather than step 2, deliberately: six of its capabilities
exist only on the Go API (they were server actions, never routes), so routing it through the load
balancer would have 404'd them until the flip. That also made it the canary.

### Three failures worth remembering

- **The first push to `main` failed at *startup*, no jobs created.** A called workflow cannot hold
  a permission the caller has not granted, and `docker-build-push@0.1-affogato` declares
  `packages: read` — which the API job omitted precisely *because* a Go build pulls no private
  packages. What the callee declares is what matters, not what the build needs.
- **The chi swap silently invalidated the controller test helpers.** They routed through their own
  stdlib `ServeMux` so handlers could read `r.PathValue`; left alone they would have kept passing
  while exercising a path the server no longer takes. A router migration has to move the harness.
- **One test found three stacked bugs.** Round-tripping a stored payload through BSON exposed
  documents decoding as `bson.D`, arrays as `bson.A` (whose *underlying* type is `[]any`, which
  is exactly why it slipped past — a type assertion matches the dynamic type), and `int` encoding
  as `int32`. Every replay path would have failed against real Mongo. Nothing caught it because
  no test had ever encoded a payload.

### The parity harness is the artifact to protect

216 fixtures. 204 hand-written cases pin Zod's semantics; **12 are the Go generators' own output,
emitted by `tools/genfixtures` and run through real Zod — and all twelve pass.** That is the most
direct evidence the generator port is faithful, because the judge is the TypeScript source of
truth rather than the Go interpreter ported alongside it.

It caught four divergences plus a real bug of my own: the canonical schemas hold **two** date
semantics with opposite field order, and I had collapsed them.

### Left for Harry

- **`Z3`** — a `go-run.yaml` reusable is drafted at `go-run.yaml.draft` in this folder. It is the
  only language gap a Go service hits, and two repos hand-roll it now. A cross-team ask in
  `#platform-engineering`, which reads better from a person.
- **The Confluence changelog row and the `#bifrost-forge` post.**
- **Two small follow-ups**: `apps/ui/src/lib/auth/session.ts` still exports `encrypt`,
  `createSession` and `updateSession` at zero importers now the API mints sessions; and
  `lib/load/caps.const.ts` duplicates the API's tier thresholds, matching today with nothing
  enforcing it.

### Verified live, not just by unit test

Done by building and running the real binary, because a green suite does not prove a service boots.

- **It boots** and emits exactly the fleet Datadog shape: `message` / `timestamp` /
  lowercase `level` duplicated as `status` / base tags / correlation fields, flat, no `requestor`.
  Found and fixed a duplicate `environment` key on the boot line this way.
- **`GET /api/v1/health`** 200 unauthenticated; **`401 {"error":"unauthorised"}`** without a key
  (British spelling preserved — the MCP may match on it); **api key and session cookie both
  authenticate**; **login returns `{"message":…}` not `{"error":…}`** (the preserved
  inconsistency); **`503` not a panic** when Mongo is unconfigured; **400 vs 404** on ids;
  graceful shutdown on SIGTERM.
- **The Docker image builds**: 12.5 MB, distroless, non-root, and **no secret in the image
  config** — clean by construction, since a Go build authenticates against no private registry.
  (The Node Dockerfile once leaked a GH token this way.)
- **Terraform**: `validate` passes, `fmt` reports no diff, and every variable without a default is
  supplied by tfvars, `root.hcl` or the reusable workflow. Both cutover flags default false, so
  applying changes nothing.
- **Index parity checked by hand** against the TypeScript, including the `single_running_run`
  unique-partial index that is what actually enforces one concurrent load run.
- **Comment conventions audited**: zero ticket references, zero change-narrating comments,
  density 7–20% concentrated in the packages where the "why" matters.
- A local Mongo-backed read could not be exercised: the machine's Mongo requires auth and the
  sandbox's Docker daemon cannot start containers. The repository layer has 123 unit tests and
  `R5`'s dev deploy is the real gate for this.

### ⚠️ CI only runs on pull requests in this repo

`code-quality`, `secops` and `tf-plan` all trigger on `pull_request` plus a nightly cron.
`deploy.yaml` triggers on push to `main`. So the documented direct-commits-to-`main` convention
means **every deploy to dev happens with no CI gate**, and the nightly finds out hours later.

Fine for a one-line fix; not fine for a language rewrite. The branch is therefore landing via a
PR purely so the gates run before anything deploys. Worth fixing properly regardless — adding
`push:` to the branch triggers would cost nothing and close the hole.

---

## Cutover & discipline

Now it is cut over, two flags in `iac/env/dev.tfvars` are the standing revert levers — each
reverts in **one Terraform apply**:

- **`api_serves_traffic`** — the load balancer, fuse-mcp and the ten push subscriptions.
- **`api_owns_background_loops`** — the scheduler and the load engine, pinning the API to one
  always-on instance (`min=max=1`, `cpu_idle=false`).

**Never true in two places at once.** Two owners double-fire every schedule and the symptom is
duplicate records, not an error. The Next app's `instrumentation.ts` must never start the loops
again.

**No CI on a direct push** (CI triggers on `pull_request` only; a push to `main` deploys to dev
with no gate), so run the gates locally before every push:

```
cd apps/api && make fmt-check && go build ./... && go vet ./... && TZ=UTC go test ./... && make lint
cd ../ui   && pnpm lint && pnpm test && pnpm build
```

Anything touching canonical data also owes a **`make parity`** run — the golden harness is the
standing detector for `@gfs-bifrost/types` bumps. Every endpoint stays under `/api/v1` or
`/events/v1`, and a test walks the built chi router against `openapi.yaml` in **both** directions,
so a new route must be added to the spec or the build fails.

---

## ⚠️ Read this before touching the repo

**Every push to `main` deploys to dev, and there is no PR flow.** That convention is fine for
one-file fixes and actively dangerous for a language rewrite — a half-finished unit on `main` is
a broken tool for whoever is using the mocker that afternoon.

Working rule for this programme: **the Go app is not wired into `deploy.yaml` until `R5`.** Until
then `apps/api` builds and tests in CI but ships nothing. After `R5` it deploys as a *separate*
Cloud Run service that no traffic reaches until `X3`. Units that change the live path — `M0`,
`X2`, `X3`, `X4` — get verified locally *and* on a manual dev deploy before the push that lands
them, and are never pushed at the end of a day.


### `X4` (decommission) is gated on `X3`, not just on `X2`

Six things must be true before `apps/ui/src/lib/**` and `app/api/v1/**` can be deleted. Found by
actually rewiring the UI rather than by reading the file list, and four are still open:

1. ✅ **A targets endpoint.** No endpoint served the target descriptors the send / schedules /
   load / activity / confirmations pages read (`envelope`, `recordTypes`, `plannedAttributes`,
   the generatable sets, the derived confirmation-target list), so the target registry existed in
   both languages. `GET /api/v1/targets` closes it.
2. ⬜ **`lib/load/caps.const.ts` is a fifth client-safe module**, beyond the four this plan
   listed — the load view is a client component and imports the tier thresholds for its
   pre-flight confirm dialog. Its values match the API's tiers exactly today, so there is no
   drift, but nothing enforces that. Either expose the tiers on an endpoint and read them, or
   accept the duplication knowingly.
3. ⬜ **`lib/auth/session.ts` must survive** — `proxy.ts`, `layout.tsx`, the login route and the
   logout action all use it. Logout calls the API *and* clears the local cookie, because a
   `Set-Cookie` on a server-side fetch never reaches the browser.
4. ⬜ **The login page still POSTs from the browser to `/api/auth/login`.** Repointing it at
   `/api/v1/auth/login` only works **after** `api_serves_traffic` flips — before the flip that
   path is not a Next route and would 404. So login moves in `X4`, and `X4` therefore comes
   **after** `X3`, not after `X2`.
5. ✅ **`MOCKER_API_URL` is wired in IaC.** It was missing, which would have stopped the UI
   booting in dev. It points at the load balancer deliberately.
6. ⬜ **`openapi-typescript` marks a `default`-bearing request-body field as required**, so
   `PresetInput.randomiseReferences` and `ScheduleInput.enabled` are sent explicitly. If they
   should be genuinely optional, drop the `default` from the schema and document the server-side
   default in the description instead.

The sequencing that follows: **deploy → verify → `X3` flip → verify → `X4`.**


### `X4` measured, not guessed

Every `@/lib/*` import from code that survives the deletion, counted directly:

| module | imported by | fate |
| --- | --- | --- |
| `publisher/targets.const` | 5 pages | **replaced** by `GET /api/v1/targets` |
| `generators/generate` | 3 pages | **replaced** by the same endpoint |
| `observability/datadog-link` | 5 views | **keep** — client-safe, no server deps |
| `send/recent-orders` | 1 action, 1 view | **keep** — client-safe |
| `send/origin` | 1 view | **keep** — client-safe |
| `load/caps.const` | 1 client view | **keep** — the fifth client-safe module |
| `auth/session` | `proxy.ts`, `layout.tsx`, the logout action | **keep** — server-side but load-bearing |
| `scheduler/engine`, `load/engine`, `db/ensure-indexes` | `instrumentation.ts` only | **delete** once the API owns the loops |

So `X4` is five steps, in order:

1. Repoint the eight pages onto `GET /api/v1/targets` and regenerate the client.
2. Gut `instrumentation.ts` — no scheduler, no load engine, no index ensure. This is what makes
   `X3`'s loop-ownership flip safe rather than a race.
3. Move the login POST from `/api/auth/login` to `/api/v1/auth/login`. **Only valid after `X3`.**
4. Delete `app/api/**` (20 route handlers) and all of `lib/` except `api/`, `auth/session.ts`,
   `observability/datadog-link.ts`, `send/origin.ts`, `send/recent-orders.ts`,
   `load/caps.const.ts`.
5. Drop the now-dead dependencies: `@gfs-bifrost/{types,pubsub,observability}`,
   `@google-cloud/pubsub`, `mongodb`, `winston`, `hot-shots`. **Keep `jose`** — `session.ts` uses it.

Size: **~9,200 prod lines and ~3,900 test lines removed** from the UI. The 33 UI spec files go
with `lib/`; the 1,078 Go tests are what replace them.

---

## Unit ledger

Status: ⬜ not started · 🟨 in progress · ✅ merged · ⛔ blocked

### Tranche 0 — Repo + toolchain (no behaviour change)

| Unit | What | Prereqs | Status |
| --- | --- | --- | --- |
| `M0` | Monorepo reshape: `code/` → `apps/ui/`; repoint all four workflows' `working_directory` + add `apps/ui/**` path filters; repoint `docker-build-push`'s `working_directory`. Zero functional change. | — |✅ |
| `M1` | Go skeleton `apps/api/`: `go.mod` (`github.com/gfs-bifrost/fuse-mocker/apps/api`), `cmd/api/main.go`, the layer dirs, `Makefile`, `.golangci.yml`, root `mise.toml` go pin, `api-code-quality.yaml`, `secops.yaml` gains `lang: go`. Serves `GET /health/liveness` + `GET /api/health` only. Not deployed. | `M0` |✅ |
| `M2` | Observability + config foundation: slog handler emitting the fleet's flat Datadog JSON; tee sink to `/shared-volume/logs/app.log` under `DATADOG_ENABLED`; `correlation` package over `context.Context` mirroring `ExtendedCorrelationDetails` + the 6-value `Flow`; dogstatsd with the 4-key context-tag allowlist; env config with the prod refusal. | `M1` |✅ |
| `M3` | Contract freeze: `apps/api/openapi.yaml` for the measured 20-route surface; `oapi-codegen` wired into `make gen`. No handlers yet. | `M1` |✅ |

### Tranche 1 — Canonical parity (the gate for everything downstream)

| Unit | What | Prereqs | Status |
| --- | --- | --- | --- |
| `C1` | `apps/api/tools/canonschema/`: walks the Zod tree of the 12 record schemas + 2 envelope schemas, emits committed Go structs + a normalisation table (defaults, coercions, date parsing, `dutyPaid`) + the 5 runtime enum const sets. `make gen` regenerates; CI fails on a regeneration diff. | `M1` |✅ |
| `C2` | Golden parity harness: fixtures through TS `safeParse` and the Go validator, output JSON byte-compared. Fault-inject it (break one default, one coercion, one date format) and confirm it goes red. | `C1` |✅ (coverage expansion in flight) |

### Tranche 2 — Read paths

| Unit | What | Prereqs | Status |
| --- | --- | --- | --- |
| `R1` | Mongo repositories: all five collections, `ensureIndexes` parity incl. the `single_running_run` partial-unique index and the three TTLs (activity 30d, load_runs 90d, captured 14d). | `M2` | ✅ |
| `R2` | config-service adapter (6 endpoints, uniform 404→nil), `CustomerSeed` fan-out, the two 5-minute caches. | `M2` |✅ |
| `R3` | Auth: `x-api-key` constant-time compare, HS256 session-cookie verify against the same `SESSION_SECRET`, `?token=` push-token verify. | `M2` |✅ |
| `R4` | Read endpoints: activity list/detail, presets list/detail, schedules list/detail, load-runs list/detail, customers, health. | `R1` `R2` `R3` `M3` | ✅ |
| `R5` | Shadow deploy: second Cloud Run service, `min=0`, **not** on the LB, **not** owning the background loops. Read-path parity tested against the live Next API. | `R4` | ✅ |

### Tranche 3 — Generators + publish

| Unit | What | Prereqs | Status |
| --- | --- | --- | --- |
| `G1` | The 13 generators + `helpers` (`mockReference` exactly 15 chars, `mockShortRef` 13, `mockCustomerRef`) + config-defaults resolution (option > configDefault > fallback). Golden fixtures vs TS. | `C2` `R2` | ✅ |
| `G2` | `POST /api/v1/generate`. | `G1` | ✅ |
| `G3` | Target registry + publisher + `sendMessage`'s twelve ordered gates + `POST /api/v1/messages`. Publishes the **parsed** envelope. | `C2` `G1` | ✅ |
| `G4` | Presets write paths + `POST /presets/{id}/send` (reference re-roll with `setIfPresent` semantics — never adds a key the payload lacks). | `G3` | ✅ |
| `G5` | Replay: `activity/{id}/replay`, `confirmations/captured/{id}/replay`. Replays go out unimpersonated. | `G3` | ✅ |
| `G6` | Sample files: reverse mapping (`indexArrayPaths`, first-rule-wins-unless-empty, `defaults` deliberately omitted) + CSV/JSON/JSONL. | `G1` `R2` | ✅ |

### Tranche 4 — Background engines

| Unit | What | Prereqs | Status |
| --- | --- | --- | --- |
| `E1` | Scheduler: 15s ticker, `findOneAndUpdate` atomic claim, uniform jitter, re-anchor `nextRunAt` on timing change or false→true enable, never auto-disable on failure. | `G3` `R1` | ✅ |
| `E2` | Load engine: burst + soak, the three advisory cap tiers (WARN/CONFIRM/HARD_MAX), per-second concurrent batches with drift correction, resumability (`classifyRunningRun`), one summary activity row per run. | `G3` `R1` | ✅ |
| `E3` | Confirmations capture push endpoint: `?token=` auth, ack-don't-retry (200 on bad input, 500 only on a storage failure), dedupe on `(messageId, recordIndex)`. | `G3` `R1` `R3` | ✅ |

### Tranche 5 — Cutover

| Unit | What | Prereqs | Status |
| --- | --- | --- | --- |
| `X1` | The six action-only capabilities get real endpoints: captured-confirmations list + detail, sent-confirmations list, recent-orders picker, connector list (send), SFTP connector list (files), validate-without-send. Plus login/logout ownership (open decision D3). Spec addition to `openapi.yaml`. | `R4` `G1` | ✅ |
| `X2` | UI rewire: `openapi-typescript` client generated from `apps/api/openapi.yaml`; all nine `*.action.ts` files call the client instead of `lib/`; the eight `page.tsx` direct-`lib` reads become client calls. Four client-safe lib modules stay. | `X1` + all of Tranche 3 | ✅ |
| `X3` | **Traffic cutover — the one atomic step.** LB `path_rule` `/api/*` → api backend; repoint all 10 Pub/Sub push endpoints; transfer background-loop ownership (api `min=max=1` + `cpu_idle=false`, ui drops to `min=0`). Must land as a single terragrunt apply. | `X2` + all of Tranche 4 | ✅ |
| `X4` | Decommission: delete `apps/ui/src/app/api/v1/**` and `apps/ui/src/lib/**` (minus the four client-safe modules); drop `@gfs-bifrost/{types,pubsub,observability}`, `@google-cloud/pubsub`, `mongodb`, `winston`, `hot-shots`, `jose` from the UI. | `X3` | ✅ |

### Tranche 6 — Close-out

| Unit | What | Prereqs | Status |
| --- | --- | --- | --- |
| `Z1` | Docs: repo `CLAUDE.md` + `README.md` rewritten for the monorepo; **fix the stale load-caps section** (it still documents the pre-`e3cabc2` hard caps); Confluence `266534922` updated. | `X3` | ✅ |
| `Z2` | MCP smoke: all five `mock-*` tools round-tripped against the Go API, including a deliberate 400 to confirm the validation-issues body still parses. | `X3` | ✅ |
| `Z3` | Platform: propose a `go-run.yaml` reusable in `#platform-engineering`. The platform repo's own rule is to add a missing workflow centrally once, not hand-roll per repo — `fuse-tui`'s inline Go CI is a ready-made spec. | `M1` | 🟨 drafted, left for Harry |

---

## Gates

- **`C2` green is the gate for Tranche 3 and 4.** No unit touching canonical data ships without
  parity fixtures passing. `C2` must itself be fault-injected first — a parity harness that
  cannot fail is worse than none.
- **`R5` read-path parity green before any write path deploys.**
- **Full parity + `Z2` MCP smoke before `X3`.** `X3` is the only step that is awkward to reverse
  (10 push subscriptions + LB routing + which service owns the schedules).
- **Only one service owns the scheduler and load engine at any moment.** During `R5`→`X3` the Go
  service must have the loops *compiled but not started* — gate them on an env flag that is
  false until `X3` flips it.

---

## The fuse-mcp contract (do not drift)

`fuse-mcp`'s `src/mocker/` calls these with `x-api-key`, base URL from `MOCKER_STAGING_URL`.
Error bodies keep their parsed body — the 400's validation issues are the useful part, and the
MCP surfaces them. Fourteen endpoints across five tools:

| tool | endpoints |
| --- | --- |
| `mock-send` | `POST /api/v1/messages` |
| `mock-generate` | `POST /api/v1/generate` |
| `mock-schedule` | `GET/POST /api/v1/schedules`, `PATCH/DELETE /api/v1/schedules/{id}`, `POST /api/v1/schedules/{id}/run-now` |
| `mock-load-run` | `GET/POST /api/v1/load-runs`, `GET /api/v1/load-runs/{id}`, `POST /api/v1/load-runs/{id}/cancel` |
| `mock-activity` | `GET /api/v1/activity`, `GET /api/v1/activity/{id}` |

The local `~/code/fuse/fuse-mcp` checkout is **stale** and has no `src/mocker/` — read the remote
(`gh api "repos/gfs-bifrost/fuse-mcp/contents/src/mocker?ref=master"`).

---

## Risk register

| id | risk | mitigation |
| --- | --- | --- |
| **R1** ★ | **No PR flow + push-deploys-to-dev.** A half-landed unit breaks the tool for the team mid-afternoon. | Go app out of `deploy.yaml` until `R5`; live-path units (`M0`, `X2`–`X4`) verified on a manual dev deploy first; never push those late in the day. |
| **R2** ★ | **Canonical defaults/coercions are load-bearing**, because the *parsed* envelope is what gets published. A validation-only Go port publishes different bytes and Snap rejects them. | `C1` recovers defaults with values from the Zod tree; `C2` byte-compares output. |
| **R3** ★ | **`fuse-mcp` breaks silently.** Five tools, 14 endpoints, and the 400-body shape is depended on. | `M3` freezes the spec from the measured surface; `Z2` smokes every tool before cutover. |
| **R4** | **`to*Dto` mappers spread `...rest`**, so any Mongo field currently leaks into API responses automatically. Go structs are explicit — a field the UI reads could silently vanish. | Enumerate the real document fields per collection during `R1`; diff a live response against the Go response in `R5`. |
| **R5** | **Snap field lore lives in TS comments.** Losing it reintroduces the incident where all 1,000 orders in a GADG burst failed on a 21-char reference. | Port the comments with the code. `mockReference` = exactly 15 chars has a test; keep it. |
| **R6** | **`source: "nodejs"` → `"go"`** may break existing Datadog log queries, dashboard `r2r-76f-65i`, and any monitor filtering on it. | Open decision D1. Audit the dashboard + monitors before flipping. |
| **R7** | **`@gfs-bifrost/types` minor bumps land often** (see the org changelog). The generator must be re-run or Go drifts. | Committed generated files + CI failing on a regeneration diff + `C2` as the standing detector. Renovate bumps `types` here. |
| **R8** | **Two instances running the scheduler double-fire every schedule.** | Loops behind an env flag, false until `X3`; `X3` transfers ownership in one apply. |
| **R9** | No `go-run.yaml` reusable exists; Go CI is hand-rolled per repo. | `M1` copies `fuse-tui`'s 7-step workflow; `Z3` proposes the reusable centrally. |

---

## Open decisions

| id | question | current lean |
| --- | --- | --- |
| **D2** | Does `meta.serviceName` stay `fuse-mocker` or become `fuse_mocker` (the fleet's snake_case convention, and the Datadog `service` tag)? Changing it splits historical data. | Keep `fuse-mocker` — the Cloud Run `DD_SERVICE` and dashboard already use it; the fleet convention is not worth a data split on a dev tool. |
| **D3** | Who owns login? Options: Go API serves `POST /api/auth/login` and sets the cookie (single auth owner), or the UI keeps it (fewer moving parts at cutover). | Go API owns it. `proxy.ts` only needs to *verify* the cookie, which it can do with the same secret. |
| **D4** | Does the Go app live at `apps/api/` with `go.mod` at that level, or `apps/api/code/go.mod` mirroring `fuse-tui`'s `code/`-rooted convention? | `apps/api/go.mod`. `fuse-tui`'s `code/` exists to mirror the *single-app* Node template; in a poly-app monorepo `apps/<name>/` already plays that role. |
| **D5** | Keep the six action-only capabilities as endpoints (`X1`), or drop any that only the UI ever needed? | Keep all six as endpoints — they become MCP-reachable for free, which is a real gain. |

**D6 — RESOLVED 2026-08-22 (Harry): every endpoint under `/api/v1` or `/events/v1`, nothing else.**
The mocker's Cloud Run container declares no `startup_probe`, so there is no infra-mandated
`/health/liveness` to exempt and the rule applies literally. Three routes move —
`/api/health` → `/api/v1/health`, `/api/auth/login` → `/api/v1/auth/login`, and
`/api/v1/confirmations/capture/{recordType}` → `/events/v1/confirmation/capture/{recordType}`
(the last repoints all 10 push subscriptions, in `X3`). `proxy.ts`'s matcher must exclude
`events/v1` too.

---

## Measured baseline (2026-08-22, HEAD `e3cabc2`)

Established during planning; re-measure before claiming a delta.

- `code/src` total **17,133** lines TS/TSX. `app/` 1,905 · `modules/` 5,316 · `lib/` 9,410 (of
  which 3,865 tests ⇒ 5,545 prod) · `observability/` 208 · root 269 · misc 25.
- **20 route handlers**, **9 server-action files**, **6 capabilities action-only**.
- **33 spec files, 357 test cases**, all under `src/lib/`. Zero tests for route handlers,
  server actions, or views.
- Five Mongo collections; three TTL indexes; two unique indexes; one partial-unique index.
- Six publish targets; 12 canonical record schemas; 13 generators; 5 runtime enums.
- 10 Pub/Sub push subscriptions.
- Cloud Run: `min=max=1`, `cpu_idle=false`, one app container + `serverless-init` sidecar,
  in-memory `/shared-volume`.

### Verified findings worth not re-deriving

- `z.toJSONSchema` succeeds on all 12 record schemas (24/24, input and output modes) but **loses
  dates entirely (`{}`), loses default *values*, and loses coercion** — hence the Zod-tree
  walker. A generic walker recovers 9 defaults with values, 38 `z.coerce.number()` fields and 17
  pipes/transforms on `CanonicalSalesOrderSchema` alone, with zero unhandled node types.
- The repo `CLAUDE.md`'s load-cap section is **stale** — it documents burst ≤5000@≤50/s and soak
  ≤24h@≤10/s, but `caps.const.ts` at HEAD has three advisory tiers with hard maxima of
  10,000/s, 100,000 total and 30 days.
- `presetInputSchema.businessId` has **no `.toUpperCase()`** transform, unlike every other input
  schema. The HTTP route stores whatever case the caller sent; only the UI action normalises.
  Preserve the quirk or fix it deliberately — don't change it by accident.
- `goods_out_confirmation` / `goods_in_confirmation` are publishable recordTypes but **not**
  generatable by name; only the `dispatch` / `receipt` aliases have generators.
- `POST /api/v1/load-runs` **enumerates** its fields (unlike `/messages`, which spreads), so a
  new input silently vanishes unless added there explicitly.
- `dedupe-service`/`sftp-connector`'s `withRequestId(fn)` evaluates `fn()` once at client
  construction — a latent bug. Read the correlation id inside the round-tripper instead.

---

## Decision log

| date | decision |
| --- | --- |
| 2026-08-22 | **D1 RESOLVED: the Go service emits `source: "go"`.** Audited exhaustively — all 340 dashboards in the org enumerated: `ddsource` appears zero times, exactly one dashboard references `nodejs` (`3rw-7ar-3qz`, hard-scoped to fuse-ui), and no Fuse-owned dashboard defines a `source` template variable. Nothing filters the mocker on it. Two things no MCP tool exposes and so remain unchecked: log pipeline/processor config, and SLOs. |
| 2026-08-22 | **`fuse-mocker` becomes a poly-app monorepo** (`apps/api` Go + `apps/ui` Next), not a move into `fuse-devtools`. Keeps DNS, LB, Mongo, `api_key`, dashboard `r2r-76f-65i`, Confluence `266534922`. Harry. |
| 2026-08-22 | **Canonical schemas are generated from `@gfs-bifrost/types`, never hand-ported**, with golden parity fixtures as the proof. Rejected: hand-porting (creates a second source of truth that drifts on every `types` bump) and a TS validator sidecar (keeps Node in the deployment). Harry. |
| 2026-08-22 | Generation is a **Zod-tree walk, not `z.toJSONSchema`** — empirically established: JSON Schema drops dates, default values and coercion. |
| 2026-08-22 | The **HTTP contract is spec-first** (`openapi.yaml` → `oapi-codegen` for Go, `openapi-typescript` for the UI), matching `fuse-ui`'s existing generated-client pattern. |
| 2026-08-22 | The Go app is **kept out of `deploy.yaml` until `R5`**, and background loops sit behind an env flag until `X3`, because pushes to `main` auto-deploy and there is no PR flow. |
