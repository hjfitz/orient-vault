---
title: Fuse MCP Server — Go Rewrite (Overview)
status: planning
owner: Harry Fitzgerald
created: '2026-08-23'
updated: '2026-08-23'
tags: [bifrost, fuse-mcp, golang, mcp, migration, overview]
---

# Fuse MCP Server — Go Rewrite

> **Rationale, target architecture, and the constraints that shape it.** Live progress lives in
> [[Bifrost/Fuse MCP Go/Migration State|Migration State]]. The acceptance baseline is
> `mcp-baseline-ts.json` in this folder.

**Repo:** `~/code/fuse/fuse-mcp` (github `gfs-bifrost/fuse-mcp`, default branch `master`)
**Precedent:** the [[Bifrost/Fuse Mocker Go API/Overview|fuse-mocker Go rewrite]] — same process,
same conventions, and its scars are worth reading before starting this one.

⚠️ **Note two local clones of one repo.** `~/code/fuse/fuse-mcp` and `~/code/fuse/fuse-mcp-server`
are the *same* GitHub repo cloned twice into differently-named directories. Both top-level
checkouts are stale (14+ commits). Only work from a worktree off `origin/master`.

---

## What it is today

A NestJS MCP server exposing the Fuse platform's knowledge base and live-service tooling to
agents. Stack: NestJS 11 + `@rekog/mcp-nest` + `@modelcontextprotocol/sdk` 1.27.1 + zod.

**3,493 prod lines / 1,706 test lines**, plus **244 KB of JSON in `data/`** that is pure data and
ports verbatim.

| module | prod | what it is |
| --- | --- | --- |
| `knowledge` | 810 | 8 lookup tools + the 15-resource table + the prompt; reads `data/*.json` |
| `mocker` | 645 | the 5 `mock-*` tools, over fuse-mocker's HTTP API |
| `config-service` | 503 | config read/write, customer list, SNAP credentials |
| `dedupe` | 450 | the deduper's held-record queue |
| `replay` | 323 | the failure inbox |
| `collector` | 220 | record lookups |
| `fapi` | 201 | `submit-to-fuse` |
| `auth`/`observability`/`health` | 111 | a bearer guard, a 57-line logger, a health route |

Hosted as **one prod-only Cloud Run service** (`fuse-mcp-prod`, `bifrost-prod-global1`) behind a
global HTTPS LB at **`https://mcp.fuse.ilg.software/mcp`**, `min=1 / max=2`, public invoker with
the shared bearer token as the only auth.

---

## The acceptance criterion, established up front

**47 declarations: 30 tools, 15 resources, 1 resource template, 1 prompt.** Captured off the real
TS server over stdio and committed as `mcp-baseline-ts.json`. Verified that the code and the live
hosted server agree exactly — 30 tools in both, zero drift — so the baseline is trustworthy.

This is the whole contract. An MCP server's tool schemas *are* its API, and the descriptions are
what a model reads to decide how to call it: **108 of 118 input fields carry a description**.

### The parity bar is semantic, not byte-exact

The TS schemas carry artifacts that come from `zod-to-json-schema`, not from intent, and Go will
not reproduce them:

| artifact | count | why it is noise |
| --- | --- | --- |
| `$schema: draft-07` header | 30 | a zod-to-json-schema preamble |
| `maximum: 9007199254740991` | 15 | JS `MAX_SAFE_INTEGER` leaking out of `.int()` |
| `additionalProperties: {}` | 3 | an empty-object artifact on record types |

And the Go SDK adds one of its own: it embeds `Cacheable` **without `omitempty`**, so every
`tools/list` / `resources/list` / `prompts/list` response ships `ttlMs: 0, cacheScope: "public"`
that the TS server does not send.

So the harness compares **name, description, the required set, and per-field type / enum /
default / description**, with those five classes on a documented allowlist. Same lesson as the
mocker's two date flavours: a diff is only useful when it knows what it is allowed to ignore.

---

## Why Go, and what the SDK actually gives us

`github.com/modelcontextprotocol/go-sdk` **v1.7.0** — past 1.0, and its `go.mod` declares
`go 1.25.0`, so the installed 1.25.1 suffices. **Spiked end to end before planning**: a working
server driven over both transports by a real SDK client and by raw curl.

**Proven:** typed tools with per-field descriptions, structured *and* text results, `fuse://`
resources and templates, prompts with arguments, stdio and bearer-protected streamable HTTP, and
the tool-error / protocol-error split.

**Two costs to budget, neither structural:**

1. **Enums cannot come from a struct tag.** `jsonschema:"enum=dev,prod"` is *hard-rejected at
   startup* — the tag parser refuses any value matching `^\S*=`. The fix is to infer the schema
   then mutate it:
   ```go
   s, _ := jsonschema.For[LookupServiceIn](nil)
   s.Properties["env"].Enum = []any{"dev", "prod"}
   ```
   ~3 lines per constrained field. The real cost is that `s.Properties["env"]` is a **stringly-typed
   reference** — rename the field's json tag and it nil-panics. Fail-fast at boot, but a genuine
   loss of the compile-time safety zod had.
2. **`PromptArgument.Required` is advertisement only.** The SDK does not enforce it; a
   `prompts/get` with no arguments reaches the handler. Every required prompt argument must be
   hand-validated. One prompt today, so one nil-check — but it is a silent-gap class if more
   arrive.

**And one thing to get right or it is illegal protocol:** a plain `error` returned from a
*low-level* handler (prompts and resources are low-level only) marshals as `"code": 0`, which is
not a valid JSON-RPC code. Always return `&jsonrpc.Error{Code: jsonrpc.CodeInternalError, …}`.

### Descriptions: how they actually attach

The whole struct-tag value **is** the description. Not `description=…`:

```go
Name string `json:"name" jsonschema:"the service to look up, e.g. config-service"`
```

Required/optional is derived **only** from the `json` tag: a field is optional iff it carries
`,omitempty` or `,omitzero`. Two footguns worth designing around — a pointer field *without*
`omitempty` is still **required** (and becomes `type: ["null","string"]`), and a slice or map
renders as `["null","array"]` rather than `"array"`.

---

## Target architecture

```
fuse-mcp/
├── cmd/fuse-mcp/main.go        transport selection, boot
├── internal/
│   ├── bootstrap/              registration: tools, resources, prompts — the only layer that
│   │                           knows everything
│   ├── tools/                  one file per module: knowledge, config, dedupe, replay,
│   │                           collector, fapi, mocker
│   ├── knowledge/              the data/*.json readers (go:embed)
│   ├── adapters/               the five outbound HTTP clients
│   ├── auth/                   the bearer check
│   ├── config/                 the environment
│   ├── observability/          the slog handler
│   └── shared/
├── data/*.json                 UNCHANGED, and go:embed'd
└── iac/, .github/workflows/
```

Layer names follow the org contract as `snap-adapter` implements it, same as the mocker. There is
no `core` / `repositories` split worth having here: this service has no datastore and almost no
domain logic — it is schemas, HTTP clients, and JSON files.

### `data/` is embedded with `go:embed`

One artifact, no runtime path dependency, and it keeps the files exactly where they are in the
repo — which matters, because **`deploy-sitrep.mjs` reads
`~/code/fuse/fuse-mcp-server/data/{services,deployment}.json` off local disk** for the morning
digest. Embedding does not break that (the files stay); *moving or renaming the directory would*,
silently. Don't.

Note the current server re-reads and re-parses every JSON file **on every single call** — no
caching. Embedding fixes that for free.

### Observability

The current logger is 57 hand-rolled lines writing JSON to `LOG_FILE`, tailed by **two** Datadog
`serverless-init` sidecars (one per org). Keep that contract exactly — the app's only obligation
is to write JSON lines to the file.

Reuse the mocker's slog handler shape, with one deliberate carry-over: `status` holds the Datadog
**log level** string and the HTTP code lives in `httpStatus`. The existing code already does this
and comments why.

`source` is `"go"` here as it is in the mocker, which is also how the two services are told apart
during the traffic split, since both keep `DD_SERVICE=fuse-mcp`.

There is currently **no metrics, no tracing, and no correlation propagation** — the port should
not invent any. It is out of scope and the sidecars handle shipping.

---

## The cutover: weighted LB split, then soak

`fuse-mcp` has **no dev environment** — no `dev.tfvars`, no dev leg, straight from a push to
`master` into prod. So the rewrite gets verified by taking real traffic gradually rather than by
living somewhere safe first.

**This is only safe because both servers are stateless**, and that had to be checked rather than
assumed. The TS side runs `statelessMode: true`; the Go SDK has the matching
`StreamableHTTPOptions{Stateless: true}` — "does not read or set the `Mcp-Session-Id` header, and
uses a temporary session per request". So a request may land on either server mid-conversation and
still work. `JSONResponse: false` mirrors the TS `enableJsonResponse: false`, keeping SSE framing.

Mechanically: a second Cloud Run service, its own serverless NEG and backend service, and the
`url_map` gains a `route_rules` block with `weighted_backend_services`. The LB is already
`EXTERNAL_MANAGED`, which is the prerequisite — no scheme migration needed.

```
go_traffic_percent:  0  →  10  →  50  →  100  →  retire the TS service
                     soak at each step
```

One variable drives it, so each step and every rollback is a one-line change.

**What to watch during a soak**, using the LB's own access logs (`sample_rate = 1.0`, so every
request is logged with the backend it hit) plus Datadog split on `source`:
- error rate on the Go backend versus the TS backend
- latency — the LB's `timeout_sec = 30` is a hard cap on any single tool call, whatever the language
- the parity diff staying clean against `mcp-baseline-ts.json`

---

## Constraints and invariants

- **Every tool returns text content, never structured content.** The universal shape is
  `{"content":[{"type":"text","text":"<2-space-indented JSON or prose>"}]}`. Errors are ordinary
  text results — `isError` is never set anywhere in the current server. Reproduce that: models
  read these strings, and the tests assert them verbatim.
- **Production-write confirm gates** on five tools: `config-write`, `submit-to-fuse`,
  `dedupe-release`, `dedupe-release-all`, `replay-retry`. All `confirm` defaulting false, checked
  **before** the credentials check. `mock-load-run`'s `confirm` is a different thing — it is
  forwarded to the mocker's advisory-cap flow, not a local gate.
- **`environment` defaults to `"staging"` on every live tool**, and "staging" maps to the **dev**
  deployments in Terraform. A prod-only service whose tools mostly address dev.
- **Match semantics differ per tool on purpose** — exact, substring, bidirectional substring, and
  separator-stripped normalised. `lookup-service` is fuzzy; the `fuse://service/{name}` template
  is exact. Do not unify them.
- **404 is a distinguished non-error** in four of the five HTTP clients: `{data: nil, status: 404}`.
  The mocker client is deliberately different and *keeps* the parsed error body, because a mocker
  400 carries the canonical-validation issues, which are the useful part.
- **Credentials are read per call**, not captured at construction — every client re-reads
  `process.env`. Preserve that; it is what lets a missing pair degrade to a per-tool message
  rather than a boot failure.
- **`businessId` is uppercased** in every tool that takes one.
- **Auth is a shared static bearer token**, timing-safe compared, header only, with
  `WWW-Authenticate: Bearer realm="fuse-mcp"` on failure. `@nestjs/jwt` and `@nestjs/passport` are
  in `package.json` but `src/` imports neither — dead weight, do not port.
- **The transport is baked into the image** (`ENV MCP_TRANSPORT=http` in the Dockerfile), not set
  in Terraform. stdio remains a supported code path.
- **`/health` is deliberately unauthenticated and deliberately not `/healthz`** — Google's
  frontend intercepts `/healthz` on `run.app`.

---

## Recorded, not fixed here

- ⚠️ **The live `MCP_AUTH_TOKEN` was printed into a session transcript** by an exploring subagent
  on 2026-08-23. It is the shared bearer token, it appears in four files on Harry's machine, and
  rotating it means bumping `auth_token_rotation` in `iac/env/prod.tfvars` (currently `"1"`) and
  updating those four registrations. **Harry's call, flagged immediately.**
- **Dead production config**: `SERVICE_NAME`, `FAPI_STAGING_KEY`, `FAPI_PRODUCTION_KEY` are set on
  the service and read by nothing — the fapi tool resolves the per-business REST connector key
  from config-service now. CI still ships the two fapi keys as `tf_var_extra_3/4`.
- **Two dead MCP registrations** in `~/.claude/settings.local.json` and
  `~/code/fuse/.claude/settings.local.json`, both pointing at `fuse-mcp-server/dist/index.js`
  which does not exist (the build emits `main.js`). Already broken before this work.
- **CI runs Node 22 while the Dockerfile and `mise.toml` pin Node 24.**
- **`DD_ENV = "serverless"`** rather than `prod` — consistent with the fleet's compute-type
  convention, but worth a second look.
- **An SDK perf smell**: `serverResourceTemplate.Matches` recompiles the URI template regexp on
  every `resources/read`. Irrelevant at this volume.

## Opportunity worth its own ticket, not this port

`auth.TokenInfoFromContext(ctx)` works **inside** tool handlers, so per-caller authorization is
available — the write tools (`config-write`, `dedupe-release-all`, `replay-retry`) could gate on
who is calling rather than on possession of one shared token. Genuinely better than today. Out of
scope for a port whose job is to change nothing observable.

---

## Related

- [[project_fuse_mocker_go_api]] — the precedent, and its scars
- [[reference_gfs_bifrost_checkouts]], [[reference_ilg_platform_workflows]]
- [[reference_cross_env_tfstate_read]] — how this service reads dev *and* prod service state
- `snap-mcp-server` — the sibling MCP service, same prod-only posture
