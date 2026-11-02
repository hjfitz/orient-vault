---
title: Fuse MCP Server — Go Rewrite Migration State
status: cutover-complete
owner: Harry Fitzgerald
created: '2026-08-23'
updated: '2026-09-15'
tags:
- bifrost
- fuse-mcp
- golang
- mcp
- migration
- migration-state
---
# Fuse MCP Server — Go Rewrite Migration State

> **Single source of truth for progress.** Read and updated by the `fuse-mcp-go` skill on re-entry.
> Never assume progress — read the ledger. Move superseded notes to the Decision Log.

Rationale + architecture: [[Bifrost/Fuse MCP Go/Overview|Overview]]
Acceptance baseline: `mcp-baseline-ts.json` in this folder — 47 declarations. Superseded in the repo
by `internal/bootstrap/testdata/ts-baseline.json` (440 KB), which adds **output** parity: the 47
declarations *plus* 15 resource reads, 6 template reads, 4 prompt gets and 56 tool calls, captured
off the TS server over stdio. Regenerate with `tools/capture/capture.mjs` — which needs `src/` built,
one reason it stays until `S4`.

**Repo:** `~/code/fuse/fuse-mcp` (merged to `master`) · **worktree:** `.claude/worktrees/go-mcp`

## Status: 🟨 **S4 (teardown) in review — draft [#39](https://github.com/gfs-bifrost/fuse-mcp/pull/39).** The one-way door. Do not merge until the PR's `tf-output` plan (a prod destroy of the TS Cloud Run service, NEG, backend, split rule) has been reviewed and Harry gives the explicit go-ahead — the destroy removes the weight-flip rollback.

> [!info] 2026-09-15 — **S4 built + pushed as draft [#39](https://github.com/gfs-bifrost/fuse-mcp/pull/39)** (worktree `.claude/worktrees/s4-ts-teardown` off `origin/master` `8fe1df8`). Deletes `src/`, the Node toolchain, `.trivyignore` (all node:24 CVEs), `tools/capture`, the TS Docker image + `Code Quality` workflow + the three TS secops jobs; `Dockerfile.golang` → `Dockerfile`. TF: removes the TS Cloud Run service + NEG + backend + the weighted `path_matcher` (url_map → 100% Go), drops `go_traffic_percent` (var/output/tfvar) and the split-era image derivation + `check` block (Go service now reads `var.image_name`). Go: removes the protocol-cap middleware; **keeps** the null-arg crash-fix + panic backstop. **Output parity dropped, declaration parity kept** — see the decision log; this also cleared a pre-existing `master` red (the output golden had drifted from `data/` and its regenerator `capture.mjs` was being deleted). All local gates green: go build/vet/test/-race, golangci-lint 0, `make parity` (47 declarations), terraform fmt/validate. 80 files, +116/−12210 (bulk is `src/`). **S2 also corrected ⬜→✅ this session** (its weighted split shipped and S3 soaked it; the glyph was stale). Not merged — awaiting the tf-output plan review + explicit go-ahead.

Five PRs — [#28](https://github.com/gfs-bifrost/fuse-mcp/pull/28) the port,
[#30](https://github.com/gfs-bifrost/fuse-mcp/pull/30) the url_map fix + 75/25,
[#31](https://github.com/gfs-bifrost/fuse-mcp/pull/31) the protocol cap,
[#32](https://github.com/gfs-bifrost/fuse-mcp/pull/32) metrics,
[#33](https://github.com/gfs-bifrost/fuse-mcp/pull/33) 100%.

**Verified at 100%**: 50/50 requests to the Go backend and **0 to TypeScript** on a clean
post-propagation window, 10/10 parity passes, zero 5xx over 20 minutes.

**Measured**: Go average Cloud Run latency **17.7ms against Node's 59.9ms**; memory ~3%; image
10.7 MB. 335 tests, race- and lint-clean.

**Dashboard**: [u54-iz6-ag5](https://app.datadoghq.com/dashboard/u54-iz6-ag5).
**Docs**: [Go Codebase Structure](https://globalfreight.atlassian.net/wiki/spaces/Bifrost/pages/280428847)
· [Go Preferred Libraries](https://globalfreight.atlassian.net/wiki/spaces/Bifrost/pages/280494357).

### `S4` — the teardown, deliberately not done yet
The TypeScript service stays deployed at weight 0 because **that warm instance is the rollback**:
dropping `go_traffic_percent` takes effect in minutes with no build and no cold start. When it goes,
so do `src/`, its NEG and backend service, the weighted `path_matcher`, the Node toolchain,
`.trivyignore` **in full** (every entry is a `node:24` base-image CVE), the `image_scan` job for the
TypeScript Dockerfile, and — importantly — the **protocol-cap middleware**, which only exists to
make the two servers negotiate alike.

---

## ⚠️ Read before touching anything

1. **Two clones of one repo.** `~/code/fuse/fuse-mcp` and `~/code/fuse/fuse-mcp-server` are the
   same GitHub repo in two directories. Both are 14+ commits stale. Work only in the worktree.
2. **Prod-only. A push to `master` deploys straight to production** — no dev environment exists.
   `code-quality.yaml` *does* run on push (unlike fuse-mocker's), but **nothing gates Deploy**:
   both trigger on the same push and run concurrently, with no `needs:` between them. `secops.yaml`
   and `tf-output.yaml` are PR-only, so a direct commit gets no security scan and no plan review at
   all. Land the port behind the traffic split, at 0%.
3. **`deploy-sitrep.mjs` reads `~/code/fuse/fuse-mcp-server/data/*.json` off local disk.**
   Embedding the JSON is fine; moving or renaming `data/` breaks the morning digest silently.
4. **The token was leaked into a transcript** (see the Overview). Rotation is Harry's call and is
   independent of this work.

---

## Unit ledger

Status: ⬜ not started · 🟨 in progress · ✅ merged · ⛔ blocked

### Tranche 0 — Foundations

| Unit | What | Prereqs | Status |
| --- | --- | --- | --- |
| `M0` | Go skeleton: `go.mod` (`github.com/gfs-bifrost/fuse-mcp`), `cmd/fuse-mcp/main.go`, the `internal/` layer dirs, `Makefile`, `.golangci.yml`, `mise.toml` go pin, `go-code-quality.yaml`, `secops.yaml` gains `lang: go`. Serves nothing yet, deploys nothing. | — | ✅ |
| `M1` | Config + observability: env struct (no validation layer today — add a light one, keep every var's current default behaviour), the slog handler writing JSON lines to `LOG_FILE` with `status` = level and `httpStatus` = code, `source: "go"`. | `M0` | ✅ |
| `M2` | Transports + auth: `StdioTransport`, and `StreamableHTTPHandler` with `Stateless: true` / `JSONResponse: false` to mirror the TS exactly. Bearer check **hand-rolled, not** the SDK's `auth.RequireBearerToken` — that helper emits a different `WWW-Authenticate` (only when a metadata URL or scopes are set) and a plain-text body, both already part of this endpoint's contract. Unauthenticated `GET /health` returning `ok` (**not** `/healthz`). | `M1` | ✅ |
| `M3` | **The parity harness** — the gate for everything after it. Two halves, both driving an in-process server over `mcp.NewInMemoryTransports()`: **declaration parity** (tools/resources/templates/prompts vs the baseline, semantic, five artifact classes allowlisted) and **output parity** (the offline surface's actual bytes vs a golden capture). Fault-inject both before trusting them. | `M0` | ✅ |

### Tranche 1 — The knowledge surface (no network)

| Unit | What | Prereqs | Status |
| --- | --- | --- | --- |
| `K1` | `data/` via `go:embed` + typed readers. Fixes the current re-read-and-reparse-per-call for free. | `M1` | ✅ |
| `K2` | The 15 static resources + the `fuse://service/{name}` template. Resource `name` is the table's **`id`** (`services`), not its `name` (`Service Catalog`) — that column is dead. Template params **do not reach the handler** — re-match with `uritemplate` off a shared const. A template miss is a **success** carrying `{error, available}`, compact-encoded, where a hit is indented — not an error result. | `K1` `M2` | ✅ |
| `K3` | The `new-feature` prompt. **Hand-validate both required arguments** — the SDK does not enforce `Required`. | `K1` | ✅ |
| `K4` | The 8 knowledge tools. Preserve each one's match semantics exactly — exact / substring / bidirectional / separator-stripped — and the miss-message text, which the tests assert and models read. | `K1` `M3` | ✅ |

### Tranche 2 — The HTTP clients

| Unit | What | Prereqs | Status |
| --- | --- | --- | --- |
| `A1` | The five outbound clients (config-service, dedupe, replay, collector, mocker). Credentials read **per call**; 404 a distinguished non-error in four of them; the mocker client deliberately keeps the parsed error body. `User-Agent: fuse-mcp-server/1.0`. | `M1` | ✅ |

### Tranche 3 — The live tools, one module per unit

Each unit owes: exact tool names, descriptions, schemas (via the enum-mutation helper where a
field is constrained), the verbatim failure strings, the confirm gates, and `businessId`
uppercasing. Each is gated on `M3`.

| Unit | Module | Tools | Prereqs | Status |
| --- | --- | --- | --- | --- |
| `T1` | config-service | `lookup-config`, `list-customers`, `get-business-config`, `get-snap-connection`, `config-read`, `config-write` | `A1` `M3` | ✅ |
| `T2` | dedupe | `dedupe-summary`, `dedupe-list`, `dedupe-get-record`, `dedupe-release`, `dedupe-release-all` | `A1` `M3` | ✅ |
| `T3` | replay | `replay-list-failures`, `replay-get-failure`, `replay-retry` | `A1` `M3` | ✅ |
| `T4` | collector | `get-fuse-records`, `get-fuse-record` | `A1` `M3` | ✅ |
| `T5` | fapi | `submit-to-fuse` — incl. the REST-connector-apiKey resolution walk and Basic auth | `A1` `M3` | ✅ |
| `T6` | mocker | `mock-send`, `mock-generate`, `mock-schedule`, `mock-load-run`, `mock-activity` | `A1` `M3` | ✅ |

The six were ported in parallel, one agent per module, each handed its exact baseline declarations
so nothing was guessed. Every module was declaration-verified against the baseline before landing.

### Tranche 4 — Ship

| Unit | What | Prereqs | Status |
| --- | --- | --- | --- |
| `S1` | Docker + a second Cloud Run service, its own NEG and backend service, and `go_traffic_percent` (default **0**). Applying it changes nothing observable. | all of Tranche 3 | ✅ |
| `S2` | The `url_map` gains `route_rules` with `weighted_backend_services`. Deploy at **0%** and verify the Go service directly on its own Cloud Run URL. | `S1` | ✅ |
| `S3` | **Soak.** Went straight to 75/25 on Harry's call (internal tooling, not mission-critical), then to 100%. Verified at each step with `soakcheck … -repeat N` plus per-backend LB access-log counts on a clean post-propagation window. | `S2` | ✅ |
| `S4` | Retire the TS service: delete `src/`, its NEG/backend, the split rule, and the Node toolchain. Update `README`/`AGENTS.md` (both already stale). | `S3` | 🟨 |

---

## Gates

- **`M3` green is the gate for `K4` and all of Tranche 3.** No tool ships without its declaration
  matching the baseline. Fault-inject `M3` first — a parity harness that cannot fail is worse than
  none, which is exactly how it went on the mocker.
- **The split stays at 0% until the full 47 declarations match** and the Go service has been driven
  directly on its own Cloud Run URL.
- **Each soak step is verified before the next**, and the previous weight is the rollback.
- **`S4` only after 100% has soaked.** Deleting the TS service removes the rollback.

---

## Acceptance & parity

- Run the harness with **`make parity`** — declaration parity *and* output parity, both driving an
  in-process server over `mcp.NewInMemoryTransports()`. Output parity is the stronger half; all the
  fiddly per-tool match semantics live in the fixture.
- The declaration allowlist lives in **`internal/parity/diff.go`** and is closed. Beyond the five
  classes in the Decision Log it also tolerates: `additionalProperties` in all three permissive
  spellings (`{}`, `true`, absent — but **not** `false`, which is a real constraint),
  `_meta.securitySchemes`, `_meta["io.modelcontextprotocol/serverInfo"]`, and `resultType`. Anything
  else is a real difference. **Eleven fault-injection tests** prove the diff before it is trusted.
- **Fault-inject the fixture, not just the harness.** The first capture passed a one-directional
  `lookup-type` match, an emitted-but-empty search category, an unstable trace sort and a lost
  directory match — four real regressions, none noticed because no captured case exercised those
  branches. The fixture now covers reverse-direction matches, partial-category searches, empty
  arguments and directory addressing; **seven injected faults** are caught.

## Cutover & discipline

**Local gates before any push** (nothing in CI gates Deploy — see §2 above), run in the worktree:
```
make fmt-check && go build ./... && go vet ./... && go test ./... && go test -race ./... && make lint
make parity
mise x terraform@1.9.0 -- terraform -chdir=iac/projects/fuse-mcp validate   # if iac/ was touched
```
Terraform ≥1.5 is required for the config's `check` block; `mise.toml` pins **1.9.0** to match CI.

**Verify a live change with soakcheck:**
```
go run ./tools/soakcheck -url https://mcp.fuse.ilg.software/mcp -token "$MCP_AUTH_TOKEN" -repeat 20
```
Then **confirm both backends actually served it** — a soak that reached only one backend is a false
pass, and that has happened once (R19):
```
gcloud logging read 'resource.type="http_load_balancer" AND resource.labels.backend_service_name="fuse-mcp-go-prod-backend"' \
  --project bifrost-prod-global1 --freshness=10m --limit 999 --format=json | jq length
```
`gcloud compute url-maps validate` is a **red herring** — it cannot simulate weighted randomness.

---

## Risk register

| id | risk | mitigation |
| --- | --- | --- |
| **R1** ★ | **Schema drift is invisible.** The current server has **zero** tests covering tool registration, names, descriptions or schemas — the schemas in `*.tools.ts` are the only spec. A subtly wrong Go schema degrades every model's ability to call the tool, and nothing would fail. | `M3`, gating everything. The baseline is committed, not derived at test time. |
| **R2** ★ | **Prod-only, and a push to `master` deploys ungated** (CI is PR-only). | Land behind the split at 0%; treat `master` as production. |
| **R3** | **Enum schemas use a stringly-typed property key** (`s.Properties["env"]`). Renaming a json tag nil-panics at boot. | Boot-time, not runtime, so it fails fast — and `M3` catches a *missing* enum. Keep the mutation helper adjacent to its struct. |
| **R4** | **Prompt `Required` is not enforced by the SDK.** | Hand-validate in `K3`, with a test that omitting each argument errors. |
| **R5** | **A plain `error` from a low-level handler emits `"code": 0`**, an illegal JSON-RPC code. Prompts and resources are low-level only. | Always `&jsonrpc.Error{...}`. Assert the code in tests for the resource-miss and prompt-validation paths. |
| **R6** | **A traffic split would break a session-bound server.** | Verified both sides are stateless before choosing the split; `Stateless: true` mirrors `statelessMode: true`. A test should assert the option is set. |
| **R7** | **`deploy-sitrep.mjs` reads `data/*.json` off local disk.** Moving or renaming the directory silently breaks the morning digest. | `go:embed` keeps the files in place. Do not relocate `data/`. |
| **R8** | **The LB caps every tool call at 30s** (`timeout_sec`). Language-independent, but a Go rewrite changing latency characteristics could surface it. | Watch latency during the soak. |
| **R9** | Failure strings are the user-visible contract and are asserted by the existing tests. | Port them verbatim; `M3` does not cover them, so the per-module tests must. |
| **R10** ★ | **`json.Marshal` HTML-escapes `<`, `>`, `&`** into `\u003c`/`\u003e`/`\u0026`; JavaScript does not. The knowledge base is full of `BifrostMessage<T>`, so this changes the bytes of a tool's answer. | Every encode goes through `internal/shared`, which uses `json.Encoder` with `SetEscapeHTML(false)` and trims the trailing newline `Encode` adds. Pass-through payloads use `json.Indent` on the original bytes instead, which cannot escape or drop anything. |
| **R11** ★ | **The Go SDK infers `additionalProperties: false` and *enforces* it** — a call with an unknown argument returns an error result, where the Zod schemas answer normally. Mid-split the same call would fail on one backend and succeed on the other. | Every tool registers with `tools.InputSchema[T]()`, which relaxes it to permissive. Verified by calling a tool with an extra argument before and after. |
| **R12** | **A Go struct would silently drop a field added to `data/*.json` later**, and the golden could not catch it because the golden predates the field. | Entities are projected from their original bytes (`knowledge.Raw[T]` / `adapters.Result.Data`), so only the fields a tool actually matches on are declared. |
| **R13** | **A `.go` suffix on a non-Go file breaks the whole toolchain** — `Dockerfile.go` made `go build ./...` fail on its first `#`. | Named `Dockerfile.golang`. Caught locally; it would have gone red on the first push. |
| **R14** ★★ | **A `tools/call` carrying `"arguments": null` killed the whole process.** The SDK unmarshals arguments into a map to apply schema defaults, JSON null sets that map to nil, and writing a default into a nil map panics — in a goroutine the SDK spawns, so `net/http` never sees it. It fires for any tool declaring a default, which is most of the live ones. The TypeScript server answers the same request with a clean error and stays up, so this was a crash the cutover would have introduced; on Cloud Run with two instances a client could have taken the service down with a handful of requests. | Fixed at the cause (null arguments normalise to `{}`, so the caller gets the schema's own validation message) with a panic-recovery middleware outside it as a backstop. Both verified against a running binary. |
| **R17** ★ | **A green `terraform plan` is not a green apply.** The first apply failed: a `path_matcher` cannot carry both `default_service` and `default_route_action` (`Exactly one of default backend service or route action`) — enforced by the Compute API, invisible to the provider schema. | Benign, because a url_map update is atomic: the rejected update left the previous routing intact, verified with `gcloud compute url-maps describe` plus a live request. Fixed by dropping the redundant `default_service`. |
| **R18** ★★ | **The split exposed a protocol-version incompatibility neither server shows in isolation.** The Go SDK answers `2025-11-25` when asked for its own latest; the TypeScript server tops out at `2025-06-18`. A client initialising against Go then sent `MCP-Protocol-Version: 2025-11-25` and the next request landing on Node was **400ed** — intermittent, and indistinguishable from a flake. | Capped in `internal/bootstrap/middleware.go`: clamp the `initialize` *result* (the request parses into an unexported type, so it cannot be rewritten on the way in) and answer `server/discover` as unsupported, as Node does. **Statelessness was not the only axis the split required — anything negotiated per-connection needs the same check.** |
| **R19** ★ | **A soak taken before load-balancer propagation is a false pass.** My first 12-pass soak went green having never once reached the Go backend; confirmed afterwards from LB access logs (0 requests to it over 20 minutes). | Always confirm both backends actually served, per-backend, from `resource.labels.backend_service_name` in the LB access logs. `gcloud compute url-maps validate` is a **red herring** — it cannot simulate weighted randomness and appears to report the first weighted entry. |
| **R16** | **CI gates can be weaker than they look.** Three found while getting this green: `golangci-lint-action@v6` installs the v1 linter, which cannot read a v2 config *or* target go1.25 at all; `.golangci.yml` carried a v1 `issues.exclude-dirs` key that `golangci-lint run` ignores **silently**, so the exclusions had never applied; and the container scan only ever looked at the default `Dockerfile`, so a second production image would have shipped unscanned. | Action pinned to v9 with an explicit linter version; `make lint` now runs `config verify` so the local gate matches CI; a second `image_scan_go` job added. The Go pin also moved 1.25.1 → **1.25.14** because govulncheck gates on the stdlib it was built against — 1.25.1 carried 26 advisories with nothing here to fix. |
| **R15** | **The SDK re-encodes tool arguments** for any tool declaring a default: it unmarshals into `map[string]any`, applies defaults and re-marshals. So a forwarded payload reaches the wire with sorted keys and `<`/`>`/`&` escaped. | Left alone, deliberately. JSON is order-insensitive and the escapes decode identically, so downstream receives the same data — and JavaScript's own `JSON.parse` loses the same integer precision, so it is not a regression. Bypassing it would mean abandoning the typed-args contract every module uses. |

---

## Open decisions

| id | question | lean |
| --- | --- | --- |
| **D1** | Add a `dev.tfvars` + dev leg as part of this, or stay prod-only? | **Resolved: stay prod-only.** The traffic split is the safety mechanism. A dev environment is a real gap but it is its own change, and doing both at once muddles the rollback story. |
| **D2** | Does the Go server keep the stdio transport? | **Resolved: yes.** It costs almost nothing (`server.Run(ctx, &mcp.StdioTransport{})`), the README documents it as a fallback, and it is how the parity harness drives the server without a port. |
| **D3** | Light env validation, or keep bare `process.env`-equivalent reads? | **Resolved: light validation.** Added for the transport/auth invariants only (the TS already hard-fails on a missing `MCP_AUTH_TOKEN` in HTTP mode), and keep every downstream credential pair degrading to a per-tool message. Validating those at boot would turn a partially-configured server into a dead one. |

---

## Decision log

| date | decision |
| --- | --- |
| 2026-09-15 | **Output parity dropped at `S4`; declaration parity kept** (Harry, over regenerating the golden from Go or a last capture.mjs run). **Supersedes the 2026-08-23 "baseline captures output" decision below.** The output golden was the TS server's bytes over the `data/` knowledge base at capture time; once the TS server is retired it can't be regenerated (its capturer, `capture.mjs`, needs the TS build), and it tracked mutable `data/` rather than the server's contract — it was already red on `master` from unrelated data edits. Declaration parity (identity + every tool/resource/template/prompt) is the durable acceptance gate — a wrong schema is what silently degrades a calling model — and stays; `ts-baseline.json` is stripped to its 47 declarations. Removed `compare{ResourceReads,TemplateReads,PromptGets,ToolCalls}` and the `Report` output counts; `Compare` is now identity + declarations. |
| 2026-08-23 | **Cutover is a weighted LB traffic split, then a soak** (Harry). 0 → 10 → 50 → 100 via one variable. Chosen over a hostname switch or an in-place replace. Safe **only because both servers are stateless** — verified, not assumed. |
| 2026-08-23 | **The parity bar is semantic, not byte-exact**, with five documented artifact classes allowlisted: three from `zod-to-json-schema` (`$schema`, `MAX_SAFE_INTEGER`, `additionalProperties: {}`) and the Go SDK's unconditional `Cacheable` (`ttlMs: 0`, `cacheScope`). |
| 2026-08-23 | **`data/` is `go:embed`'d**, not read from disk. One artifact, no runtime path dependency, and it fixes the current per-call re-parse. The files stay exactly where they are because an external script reads them. |
| 2026-08-23 | **Cleanup scope**: stale docs are fixed as part of the port (`README` and `AGENTS.md` both omit tools that exist). Dead prod env vars and the two broken local MCP registrations are recorded as follow-ups rather than folded in — one touches production config, the other Harry's machine, and neither belongs in a port commit. |
| 2026-08-23 | **Per-caller authorization is out of scope**, despite `auth.TokenInfoFromContext` making it possible inside tool handlers. It is a genuine improvement over one shared token and deserves its own ticket. |
| 2026-08-23 | **Flat coexistence, not an `apps/` reshape.** The TypeScript server is temporary — it goes at `S4` — so a monorepo split would only be undone again. The Go tree sits at the repo root beside `src/`. |
| 2026-08-23 | **The baseline captures output, not just declarations.** The whole offline surface is deterministic, so `tools/capture/capture.mjs` drives the TS server over stdio and records the actual bytes of every resource read, template read, prompt get and tool call. This is a far stronger gate than declaration parity alone, and it is where all the fiddly match semantics actually live. |
| 2026-08-23 | **A self-cleaning pending list, not a red test.** `testdata/pending.json` lists what is not yet ported so the completeness gate runs green throughout instead of being red for the whole port (which would hide real regressions). An entry for something now implemented fails just as loudly as something missing and unlisted, so the list can only shrink; the file is deleted when it empties. |
| 2026-08-23 | **Auth is hand-rolled, not the SDK's `auth.RequireBearerToken`.** That helper emits `WWW-Authenticate` only when a resource-metadata URL or scopes are configured, in a different format, and answers with a plain-text body. Both are already part of this endpoint's contract, and scripts read the JSON body. |
| 2026-08-23 | **`Capabilities: &mcp.ServerCapabilities{}`, not nil.** nil gets the SDK's historical `{"logging":{}}` default, which this server does not implement — advertising a capability a client can then use is worse than advertising none. Tools/prompts/resources are still inferred from what is registered. |
| 2026-08-23 | **`parity` is its own package.** The allowlist is not bootstrap's concern, and the tools package's tests need it without importing bootstrap — which the layering test forbids and which would be a cycle. |
| 2026-08-23 | **The Go image path is derived in Terraform**, not threaded through CI. The terragrunt reusable workflow exposes one image-name input and its remaining slots read from `secrets`, which would mask an image tag in every plan. A `check` block asserts the two images stay in the same registry, so a CI naming change fails at plan time rather than on a pull of a tag nobody pushed. |

---

## Measured baseline (2026-08-23, `origin/master` @ `3d6e30a`)

- **30 tools, 15 resources, 1 template, 1 prompt.** Code and the live hosted server agree exactly.
- **118 tool input fields; 108 carry a description.**
- 3,493 prod TS lines / 1,706 test lines / 8 spec files / 90 test cases.
- `data/`: 15 files, 244 KB, 3,220 lines of JSON. Nothing writes to it at runtime.
- Cloud Run `fuse-mcp-prod`, `min=1 / max=2`, 1 CPU / 512 Mi **plus two Datadog sidecars at 1 CPU /
  512 Mi each** — the revision is really 3 CPU / 1.5 GiB.
- LB: `EXTERNAL_MANAGED`, `timeout_sec = 30`, access logs at `sample_rate = 1.0`.
- Existing tests cover client behaviour (URL/query/header construction, status handling, confirm
  gates, missing-credential messages) and the `data/` contract. **Nothing covers tool
  registration, schemas, resources, the template, the prompt, the HTTP wiring, or `main.ts`.**
