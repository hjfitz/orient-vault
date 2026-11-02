---
tags:
- waypoint
- fuse-mcp
verified: '2026-10-13'
verified_sha: d455b6e
verified_paths:
- internal
- src
- cmd
- data
- tools
- iac
- Dockerfile
- Dockerfile.golang
- .github/workflows
- go.mod
- Makefile
- .golangci.yml
- internal/auth
- internal/config
- embed.go
- mise.toml
- README.md
- AGENTS.md
title: fuse-mcp — architecture
thesis: A stateless Go MCP server serves 61 declarations from embedded JSON and calls
  seven Fuse services. One shared bearer token, enforced in-app, is the only gate,
  and a parity baseline guards the surface.
confidence: high
---
# fuse-mcp — architecture

```orient-bluf
{ "v": 1, "bluf": "A stateless Go MCP server serves 61 declarations from embedded JSON and calls seven Fuse services. One shared bearer token, enforced in-app, is the only gate, and a parity baseline guards the surface.", "confidence": "high", "action": "Never weaken the in-app bearer check: both Cloud Run services are public invokers, so it is the only gate." }
```

## Guardrails

- [contract:G1] Auth is in-app only. Both Cloud Run services grant `allUsers` the invoker role, so `RequireBearerToken` on `/mcp` is the sole gate. An empty token rejects everything, and an HTTP boot without a token fails. `/health` stays the only open route.
  — paths: internal/auth/bearer.go, internal/bootstrap/http.go, internal/config/config.go, iac/projects/fuse-mcp/cloud-run-go.tf
- [contract:G2] A production write needs `confirm: true`, checked before credentials are looked up. Today that is `config-write`, `submit-to-fuse`, `dedupe-release`, `dedupe-release-all`, `replay-retry` and `replay-update`. A new write tool gets the same gate.
  — paths: internal/tools/config.go, internal/tools/dedupe.go, internal/tools/replay.go, internal/tools/fapi.go
- [contract:G3] Tool names, field names, descriptions and metric names are the API. Models key off the first three, and the Datadog dashboard keys off the metric names. Rename none of them.
  — paths: internal/tools, internal/observability/metrics.go, internal/bootstrap/testdata/ts-baseline.json
- [technical:G4] A `data/*.json` edit and a refreshed parity baseline land in the same commit, through `make parity-accept`. A bare `tools/capture` overwrite drops the Go-only tools from the declarations and the gate still passes.
  — paths: data, Makefile, tools/accept, tools/capture, internal/bootstrap/testdata/ts-baseline.json
- [technical:G5] Encode output through `internal/shared`, never `json.Marshal`, and register every tool with `InputSchema[T]()`, never bare inference. Failures return as text results, and `IsError` is never set.
  — paths: internal/shared/result.go, internal/tools/schema.go
- [technical:G6] Keep all three receiving middlewares in `internal/bootstrap/middleware.go`. The null-arguments normaliser and the panic recovery are both load-bearing. The protocol-version cap stays until `src/` is retired.
  — paths: internal/bootstrap/middleware.go, internal/bootstrap/server.go

## Two implementations, one repo — Go serves all of it

The repo holds two servers side by side. The TypeScript server is `src/` (NestJS 11, `@rekog/mcp-nest`). The Go server is `cmd/fuse-mcp/main.go` and `internal/`, on the official `modelcontextprotocol/go-sdk` v1.7.0 [26].

A load balancer splits traffic by weight. `go_traffic_percent` is 100, so Go serves every request. The TypeScript service stays deployed at weight 0, so a rollback is one weight change [6][7].

The Go side declares 61 things: 44 tools, 15 resources, 1 resource template and 1 prompt [10][11]. Fourteen tools are Go-only: `replay-update`, `lookup-snap-instance` and the twelve `tracking-*` tools. A rollback to TypeScript loses them.

```orient-flow
{ "v": 1, "title": "Inbound: from an agent to a tool",
  "nodes": [
    { "id": "ag", "label": "AI agents", "sub": "mcp.fuse.ilg.software/mcp", "kind": "external", "ev": [1, 6] },
    { "id": "lb", "label": "Load balancer", "sub": "weights 100 − N / N", "kind": "step", "ev": [6, 7] },
    { "id": "ts", "label": "TypeScript service", "sub": "weight 0, rollback", "kind": "service", "ev": [5, 6] },
    { "id": "go", "label": "Go service", "sub": "Cloud Run, port 3000", "kind": "service", "service": "fuse-mcp", "tone": "accent", "ev": [4] },
    { "id": "au", "label": "Bearer check", "sub": "shared token, 401 on miss", "kind": "step", "tone": "alert", "ev": [2] },
    { "id": "mw", "label": "Middlewares", "sub": "recover, normalise, cap", "kind": "step", "ev": [8] },
    { "id": "tl", "label": "Tools, resources, prompt", "kind": "step", "ev": [9] },
    { "id": "kb", "label": "data/*.json", "sub": "go:embed", "kind": "store", "ev": [9] }
  ],
  "edges": [
    { "from": "ag", "to": "lb", "label": "POST /mcp" },
    { "from": "lb", "to": "go", "label": "N %" },
    { "from": "lb", "to": "ts", "label": "100 − N %", "style": "dashed" },
    { "from": "go", "to": "au" },
    { "from": "au", "to": "mw" },
    { "from": "mw", "to": "tl" },
    { "from": "tl", "to": "kb", "label": "knowledge" }
  ] }
```

Both Cloud Run services are public invokers, so a caller can also reach the Go service on its own `run.app` URL, past the load balancer. The bearer check still applies there [1][4][5].

```orient-flow
{ "v": 1, "title": "Outbound: from a tool to a Fuse service",
  "nodes": [
    { "id": "tl", "label": "internal/tools", "sub": "one file per module", "kind": "step", "service": "fuse-mcp", "tone": "accent", "ev": [9] },
    { "id": "cl", "label": "Client", "sub": "x-api-key, per-call creds", "kind": "step", "ev": [19] },
    { "id": "fc", "label": "FapiClient", "sub": "Basic businessId:apiKey", "kind": "step", "ev": [18] },
    { "id": "tc", "label": "TrackingClient", "sub": "Google ID token", "kind": "step", "ev": [20, 21] },
    { "id": "cs", "label": "config-service", "kind": "service", "service": "config-service", "ev": [15] },
    { "id": "gp", "label": "dedupe, replay, collector, mocker", "kind": "external", "ev": [19, 22] },
    { "id": "fa", "label": "fapi", "kind": "service", "service": "fapi", "ev": [18] },
    { "id": "tr", "label": "tracking-service", "sub": "private to Cloud Run IAM", "kind": "service", "service": "tracking-service", "ev": [20] },
    { "id": "md", "label": "Metadata server", "sub": "token cached to 5 min before expiry", "kind": "step", "ev": [21] }
  ],
  "edges": [
    { "from": "tl", "to": "cl" },
    { "from": "tl", "to": "fc" },
    { "from": "tl", "to": "tc" },
    { "from": "cl", "to": "cs" },
    { "from": "cl", "to": "gp" },
    { "from": "fc", "to": "fa", "label": "as the business" },
    { "from": "fc", "to": "cs", "label": "apiKey lookup", "style": "dashed" },
    { "from": "tc", "to": "tr", "label": "read-only calls" },
    { "from": "tc", "to": "md", "label": "mint token" }
  ] }
```

## Go layout

```
cmd/fuse-mcp/main.go     transport selection, boot, graceful shutdown
internal/
  bootstrap/             tool/resource/prompt registration, HTTP mux, middlewares: the only layer that knows everything
  tools/                 one file per module: knowledge, config, snap, dedupe, replay, collector, fapi, mocker, tracking
  knowledge/             data/*.json readers (go:embed)
  adapters/              Client, FapiClient, TrackingClient, and the metadata-server token source
  auth/                  hand-rolled bearer check
  config/                environment, read once at boot; downstream credentials, read per call
  observability/         slog handler, request logger, dogstatsd metrics
  parity/                the parity harness: baseline loader, comparer and artifact allowlist
  shared/                the tool result shape and JSON encoding
data/*.json              one copy, go:embed'd into the Go binary
embed.go                 the embed directive; stays at the root to reach data/
tools/                   node scripts (capture, accept) and the Go soakcheck
```

No `core` or `repositories` layer exists: the service has no datastore and almost no domain logic. `internal/layering_test.go` enforces the direction. Only `bootstrap` imports `tools`, nothing imports `bootstrap`, and `knowledge` and `adapters` never import each other [28]. `parity` is its own package so a test-only import cannot form a cycle with `bootstrap`.

## The parity harness — the gate for the whole rewrite

The TypeScript server had no tests covering tool registration, names, descriptions or schemas. A subtly wrong Go schema could degrade every model's ability to call a tool with nothing failing. So a committed baseline, `internal/bootstrap/testdata/ts-baseline.json`, pins the surface [10][11].

- **Declaration parity.** Every tool, resource, template and prompt matches the baseline on name, description, required set and per-field type, enum, default and description. The test expects 61 declarations.
- **Output parity.** The offline surface returns the same bytes: 15 resource reads, 6 template reads, 4 prompt gets and 56 tool calls. Any `data/*.json` edit moves these bytes.
- **Refresh with `make parity-accept`** (`tools/accept`), never a bare `capture.mjs` overwrite. It merges back only the four payload sections and refuses if the set of entries moved [12].
- **The baseline is no longer a pure TypeScript capture.** The Go-only tools are added to its declarations by hand. `capture.mjs` needs `src/` built to `dist/main.js`, which is the remaining reason `src/` stays.
- **The comparison is semantic.** A closed allowlist in `internal/parity/diff.go` strips generator artifacts from both sides, such as the Go SDK's `Cacheable` fields and zod's `$schema`. Anything not on the list fails.
- **`tools/soakcheck` runs the same comparison against a deployed server.** Point it at the Go service's own URL, or at the load balancer repeatedly.

## Registration mechanics (Go-SDK specifics)

- **A struct tag's whole value is the description**: `jsonschema:"the service to look up"`, not `description=...`.
- **Required or optional derives only from the `json` tag.** A pointer field without `omitempty` is still required.
- **Enums cannot come from a struct tag.** `InputSchema[T]` takes mutators such as `WithEnum` and `WithDefault`. A mutator naming a renamed property panics at boot, which fails fast.
- **Bare inference closes `additionalProperties`, and the SDK enforces it.** `InputSchema` relaxes that, plus the `"null"` alternative on pointers and slices [14].
- **`PromptArgument.Required` is advertisement only.** Every required prompt argument needs a hand-written check.
- **A plain `error` from a low-level handler marshals as `"code": 0`**, an illegal JSON-RPC code. Return `&jsonrpc.Error{Code: jsonrpc.CodeInternalError, ...}`.
- **Never call `json.Marshal` on output.** It escapes `<`, `>` and `&`, which JavaScript does not, and the knowledge base is full of `BifrostMessage<T>` [13].

## Auth and transport

A shared static bearer token gates `/mcp`. It is compared in constant time, read from the `Authorization` header only, and answers 401 with `WWW-Authenticate: Bearer realm="fuse-mcp"` [2]. The check is hand-rolled, not the SDK's `auth.RequireBearerToken`, because the SDK helper changes the error shape clients already rely on.

- **`/health` is open on purpose, and it is not `/healthz`.** Google's `run.app` frontend intercepts `/healthz` [1].
- **The server is stateless.** `StreamableHTTPOptions{Stateless: true}` means no `Mcp-Session-Id`. `GET` and `DELETE` on `/mcp` answer 405 [1].
- **The token lives in Terraform state.** `random_password.mcp_auth_token` feeds a plain env var on both Cloud Run services. Bumping `auth_token_rotation` in `iac/env/prod.tfvars` regenerates it [5][7].
- **Both stdio and streamable HTTP are supported.** `MCP_TRANSPORT=http` is baked into `Dockerfile.golang`, not set in Terraform [27][3].
- **Confirmation is caller-asserted.** `confirm: true` is a field the model sets. It is a speed bump, not an authorization check [15][16][17][18].

## Credentials and downstream calls

Each downstream URL and key resolves per call from the environment, as `<PREFIX>_<ENV>_URL` and `<PREFIX>_<ENV>_KEY`. A missing pair costs only the tools that need it, and the server still boots [3]. `staging` resolves to the dev deployments, because this service is prod-only [3].

- **Where the values come from.** Terraform reads the other stacks' remote state: `api_key` and the service URL for dedupe, collector and replay in both environments, and the mocker's dev outputs. The config-service keys come from CI secrets [22][4][23].
- **Per-client timeout is 20 s.** The load balancer caps a whole call at 30 s [19][6].
- **fapi needs no key of its own.** It authenticates as the business. The tool resolves the first REST connector `apiKey` from config-service per submission [18].
- **tracking-service is private to Cloud Run IAM.** The client mints a Google ID token from the metadata server per audience. The URL falls back from the `fuse-tracker` stack's state to the `tracking-service` stack's [20][21][22].
- **A path argument is appended to the base URL unvalidated** in `config-read` and `config-write` [15][19]. Go's URL parser reads `https://host` + `@other.example/x` as userinfo `host` and host `other.example`. A `path` that begins with `@` therefore redirects the request and still carries the `x-api-key` header.

## The traffic-split mechanism

A second Cloud Run service (`cloud-run-go.tf`) has its own serverless NEG and backend service. The `url_map` carries a `route_rules` block with `weighted_backend_services`, driven by the one `go_traffic_percent` variable [4][6][7]. The variable defaults to 0, and only `prod.tfvars` sets it to 100.

- **Safe because both servers are stateless.** Neither reads or sets `Mcp-Session-Id`, so a request may land on either backend mid-conversation.
- **Statelessness is not enough on its own.** Anything negotiated per connection needs the same check. The Go SDK negotiates a newer protocol than the TypeScript server accepts, so `capProtocolVersion` clamps `initialize` to `2025-06-18` and answers `server/discover` as unsupported [8].
- **Two instances at most.** Go runs `min_instance_count` 1 whenever its weight is above zero, and 0 otherwise. The TypeScript service keeps 1. Both use the same service account [4][5].
- **Verification.** The load balancer's access logs sample at 100%. Both servers keep `DD_SERVICE=fuse-mcp`, and the `source` attribute on each log line is `go` on the Go server and absent on the TypeScript one [4][6].

Retiring `src/` is the open unit. It needs a plan for `tools/capture`, and the protocol cap can go once nothing can route to TypeScript. Unit history is in [[../../Bifrost/Fuse MCP Go/Migration State|Migration State]].

## Module → tool mapping

| Module | Tools |
| ------ | ----- |
| knowledge | 9 tools (`lookup-service`, `lookup-topic`, `lookup-type`, `lookup-config`, `lookup-endpoints`, `lookup-dependency`, `lookup-changelog-page`, `trace-data-flow`, `search`), the 15-resource table and the `new-feature` prompt |
| config-service | `config-read`, `config-write`, `list-customers`, `get-business-config`, `get-snap-connection` |
| snap | `lookup-snap-instance` (static `data/snap-instances.json`; `includeBusinesses` also reads config-service `/api/v1/backend` live and decodes only `businessId` and host, so credentials cannot reach the result) |
| dedupe | `dedupe-summary`, `dedupe-list`, `dedupe-get-record`, `dedupe-release`, `dedupe-release-all` |
| replay | `replay-list-failures`, `replay-get-failure`, `replay-retry`, `replay-update` (PATCH a held failure's record, metadata or reason; full replacement) |
| collector | `get-fuse-record`, `get-fuse-records` |
| fapi | `submit-to-fuse` |
| mocker | `mock-send`, `mock-generate`, `mock-schedule`, `mock-load-run`, `mock-activity` (dev only; the URL is fuse-mocker's `api_service_url` output, read in `iac/projects/fuse-mcp/remotes.tf`) |
| tracking | 12 read-only tools: `tracking-search-shipments`, `tracking-get-shipment`, `tracking-get-timeline`, `tracking-lookup-refs`, `tracking-list-attention`, `tracking-search-returns`, `tracking-get-return`, `tracking-get-return-timeline`, `tracking-get-stats`, `tracking-get-insights`, `tracking-list-businesses`, `tracking-get-notes` |

**Match semantics differ per tool on purpose**: exact, substring, bidirectional substring and separator-stripped normalised. Do not unify them.
`get-snap-connection` returns a business's SNAP host, username and password in clear. That is its job, so the bearer token is as sensitive as those credentials.
`mock-load-run`'s `confirm` is a different thing from the production gate. It is forwarded to fuse-mocker's own advisory-cap flow.

## Build / test / deploy

- **Go is pinned to `1.26.9`** in `go.mod` and `mise.toml`. `govulncheck` gates on the standard library it was built with, and the fix for the current advisory ships only in 1.26.9. CI and `Dockerfile.golang` use the floating `1.26` [26][24][27].
- **`golangci-lint-action` is v9 with an explicit linter version.** `make lint` runs `config verify`, so a stale config key cannot be silently ignored.
- **TypeScript is a pnpm workspace with Jest**, unchanged from before the port.
- **CI.** `code-quality.yaml` (TypeScript) and `go-code-quality.yaml` (Go) both run on push and PR. The Go `parity` job is separate from `quality`, so a standing parity failure no longer hides vet, lint and test results [24].
- **`deploy.yml` triggers on the same push, concurrently, with no `needs:`.** Nothing gates Deploy [23]. It builds both images, then applies Terraform.
- **`secops.yaml` runs on PRs and a 06:00 cron, never on a push to `master`.** `tf-output.yaml` is PR-only and path-filtered to `**.tf`, `**.hcl` and `**.tfvars` [25]. Both use `pull_request`, not `pull_request_target`.
- **Two production images ship per push**, `Dockerfile` (TypeScript) and `Dockerfile.golang` (Go, distroless static, non-root), each with its own container scan. Both the TypeScript image and its scan go when `src/` does [25][27].
- **Deploy target.** Cloud Run in `europe-west2`, project `bifrost-prod-global1`. Prod only: no dev environment or leg exists.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "internal/bootstrap/http.go@d455b6e" },
  { "id": 2, "kind": "code", "ref": "internal/auth/bearer.go@d455b6e" },
  { "id": 3, "kind": "code", "ref": "internal/config/config.go@d455b6e" },
  { "id": 4, "kind": "code", "ref": "iac/projects/fuse-mcp/cloud-run-go.tf@d455b6e" },
  { "id": 5, "kind": "code", "ref": "iac/projects/fuse-mcp/cloud-run.tf@d455b6e" },
  { "id": 6, "kind": "code", "ref": "iac/projects/fuse-mcp/load-balancer.tf@d455b6e" },
  { "id": 7, "kind": "code", "ref": "iac/env/prod.tfvars@d455b6e" },
  { "id": 8, "kind": "code", "ref": "internal/bootstrap/middleware.go@d455b6e" },
  { "id": 9, "kind": "code", "ref": "internal/bootstrap/server.go@d455b6e" },
  { "id": 10, "kind": "code", "ref": "internal/bootstrap/parity_test.go@d455b6e" },
  { "id": 11, "kind": "code", "ref": "internal/bootstrap/testdata/ts-baseline.json@d455b6e" },
  { "id": 12, "kind": "code", "ref": "Makefile@d455b6e" },
  { "id": 13, "kind": "code", "ref": "internal/shared/result.go@d455b6e" },
  { "id": 14, "kind": "code", "ref": "internal/tools/schema.go@d455b6e" },
  { "id": 15, "kind": "code", "ref": "internal/tools/config.go@d455b6e" },
  { "id": 16, "kind": "code", "ref": "internal/tools/dedupe.go@d455b6e" },
  { "id": 17, "kind": "code", "ref": "internal/tools/replay.go@d455b6e" },
  { "id": 18, "kind": "code", "ref": "internal/tools/fapi.go@d455b6e" },
  { "id": 19, "kind": "code", "ref": "internal/adapters/client.go@d455b6e" },
  { "id": 20, "kind": "code", "ref": "internal/adapters/tracking.go@d455b6e" },
  { "id": 21, "kind": "code", "ref": "internal/adapters/idtoken.go@d455b6e" },
  { "id": 22, "kind": "code", "ref": "iac/projects/fuse-mcp/remotes.tf@d455b6e" },
  { "id": 23, "kind": "code", "ref": ".github/workflows/deploy.yml@d455b6e" },
  { "id": 24, "kind": "code", "ref": ".github/workflows/go-code-quality.yaml@d455b6e" },
  { "id": 25, "kind": "code", "ref": ".github/workflows/secops.yaml@d455b6e" },
  { "id": 26, "kind": "code", "ref": "go.mod@d455b6e" },
  { "id": 27, "kind": "code", "ref": "Dockerfile.golang@d455b6e" },
  { "id": 28, "kind": "code", "ref": "internal/layering_test.go@d455b6e" }
] }
```
