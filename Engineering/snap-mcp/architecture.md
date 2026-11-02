---
tags:
- waypoint
- snap-mcp
verified: '2026-10-13'
verified_sha: 6bcd233
verified_paths:
- src
- iac/projects/snap-mcp
- .github/workflows
- README.md
- package.json
- Dockerfile
- .trivyignore.yaml
- mise.toml
title: snap-mcp — architecture
thesis: A flat NestJS app serves 15 MCP tools over a bearer-guarded, stateless streamable-HTTP
  endpoint on public Cloud Run, builds one SNAP client per host-and-credentials connection
  supplied on each call, and keeps no datastore.
confidence: high
---
# snap-mcp — architecture

```orient-bluf
{ "v": 1, "bluf": "A flat NestJS app serves 15 MCP tools over a bearer-guarded, stateless streamable-HTTP endpoint on public Cloud Run, builds one SNAP client per host-and-credentials connection supplied on each call, and keeps no datastore.", "confidence": "high", "action": "Keep the SNAP client cache keyed on host, username and password, and never log tool arguments." }
```

## Guardrails

- [contract:G1] The server stores no tenant credentials. Every tool takes `host`, `username` and `password`, and the only secret the service owns is `MCP_AUTH_TOKEN`.
  — paths: src/snap/snap.tools.ts, src/snap/snap-api.service.ts
- [technical:G2] The SNAP client cache key is host plus username plus password. Several tenants share one SNAP host, and a host-only key ran every call as whichever business called first.
  — paths: src/snap/snap-api.service.ts
- [technical:G3] Every write checks `confirm: true` before the request leaves, and `snap-write` validates the method against the entity registry first.
  — paths: src/snap/snap.tools.ts
- [technical:G4] Never log tool arguments. The request logger records method, path, status, duration, MCP method and tool name only, because arguments carry SNAP passwords.
  — paths: src/observability/request-logger.middleware.ts, src/observability/log-line.ts
- [technical:G5] Reads stay tolerant. A record that fails Zod validation returns raw with `validated: false`; do not turn that into a failure without checking the unverified entities first.
  — paths: src/snap/snap-api.service.ts, src/snap/snap.tools.ts
- [contract:G6] `/health` is the only unguarded route. The MCP endpoint stays behind `BearerTokenGuard`, header-only and timing-safe.
  — paths: src/auth/bearer-token.guard.ts, src/mcp-server.module.ts, src/health/health.controller.ts

## Request path

The service is small and flat. `src/main.ts` boots Nest, `src/snap/snap.tools.ts` holds every `@Tool`, and `src/snap/snap-api.service.ts` wraps the SNAP HTTP client. The entity registry, the circuit breaker and the error parser come from `@gfs-bifrost/snap`. There is no datastore and no `core` or `repositories` layer [1][2][3].

```orient-flow
{ "v": 1, "title": "One tool call",
  "nodes": [
    { "id": "c", "label": "MCP client", "sub": "POST /mcp", "kind": "external", "ev": [4] },
    { "id": "g", "label": "BearerTokenGuard", "sub": "401 without the token", "kind": "step", "ev": [5] },
    { "id": "t", "label": "SnapTools", "sub": "15 @Tool methods", "kind": "service", "service": "snap-mcp", "tone": "accent", "ev": [1] },
    { "id": "r", "label": "Entity registry", "sub": "route, schema, write flags", "kind": "step", "ev": [1] },
    { "id": "a", "label": "SnapApiService", "sub": "client per connection", "kind": "step", "ev": [2] },
    { "id": "b", "label": "Per-host breaker", "sub": "5 transient failures", "kind": "step", "ev": [2] },
    { "id": "s", "label": "SnapFulfil host", "sub": "Basic auth, 15 s timeout", "kind": "external", "ev": [2] }
  ],
  "edges": [
    { "from": "c", "to": "g" },
    { "from": "g", "to": "t", "label": "token ok" },
    { "from": "t", "to": "r", "label": "resolve path" },
    { "from": "t", "to": "a" },
    { "from": "a", "to": "b" },
    { "from": "b", "to": "s", "label": "GET or write" }
  ] }
```

## Transport and auth

`main.ts` branches on `useHttp`, which is `MCP_TRANSPORT=http` or the `--http` flag. The Dockerfile sets the variable. [4]

- **stdio** creates a bare Nest context with the Nest logger off, because the protocol owns stdio.
- **HTTP** refuses to boot without `MCP_AUTH_TOKEN`. It listens on `PORT` (default 3000) on all interfaces and creates the `LOG_FILE` directory. It writes only to `console.error` [4].
- **MCP endpoint** is `mcp`, streamable HTTP only, stateless, with `enableJsonResponse` off. Stateless mode is why any instance serves any call [6].
- **`BearerTokenGuard`** is passed to `McpModule.forRoot`. It compares the `Authorization: Bearer` value with `MCP_AUTH_TOKEN` using `timingSafeEqual`. An empty configured token fails closed. It sets `WWW-Authenticate: Bearer realm="snap-mcp"` on failure [5][6].
- **`/health`** is a separate controller that returns `ok` with no guard. Google's front end reserves `/healthz` on `run.app`, so the route is `/health` [7].

**CONFIRMED** An unauthenticated `POST` and `GET` to `https://snap.mcp.fuse.ilg.software/mcp` returned 401, and `/health` returned 200, on 2026-10-13 [14].

## The SNAP client: one per connection {#credential-cache}

`SnapApiService.clientFor` builds a `SnapClient` with a 15 s timeout and retry on, and caches it in a `Map` keyed on `JSON.stringify([host, username, password])`. Each tenant gets its own client, and a rotated password gets a fresh one. The map has no eviction, so it grows with distinct credential sets and holds the passwords in process memory [2].

Before the fix, the key was the host alone. Every call to a shared host then ran as whichever business called first. See [[known-context#credential-cache-real]].

The `host` value is a caller-supplied URL. Nothing in this repo or in `SnapClientBuilder.withHost` restricts it to SnapFulfil hosts [2][8]. **ASSESSED** A holder of the bearer token can make the service send Basic-auth requests to any host it can reach. Cloud Run has no VPC connector here, and `snap-write` returns the raw response body. The Google metadata server needs a header the client cannot set, which limits the reach. Source: no allow-list in [2] or [8].

## Per-host resilience

`PerHostCircuitBreaker` from `@gfs-bifrost/snap/resilience` trips after 5 consecutive transient failures per host. It uses `isTransientSnapError`, the predicate the SNAP-facing Fuse services share. One struggling tenant host cannot suppress traffic to a healthy one. An open circuit raises `SnapCircuitOpenError`, which the tools return as plain text and not as an error result [2][9].

## Tolerant reads, gated writes {#tolerant-reads}

- **Reads** (`getRecords`) throw when SNAP reports `Status: "Error"`. If the envelope parses but a record fails Zod validation, the raw data still returns with `validated: false` and a `warning`. The tool is for investigation, and many entities were typed from the OpenAPI spec without a live host to check [2][1].
- **Writes** need `confirm: true`. `snap-write` resolves the route (`detail` or a named special route), checks the method against the registry's write flags or the route's method, builds the path, then checks `confirm` before sending [1].
- SNAP reports a write failure two ways: HTTP 2xx with `{Status: "Error"}`, caught by `assertSnapWriteOk`, or a non-2xx with the same nested field-error body. `writeRejectionError` sends both through `parseSnapErrorBody`, so the caller sees the field errors either way [1][2].
- **OData limits.** `snap-search` defaults to 10 records and caps at 100. An entity whose list route rejects OData returns a text refusal if a filter, order or non-default `top` is given [1].

## Tool inventory

| Generic (any of the 43 entities) | Per-entity wrapper |
| --- | --- |
| `snap-list-entities`, `snap-get`, `snap-search`, `snap-lookup`, `snap-write` | `snap-get-shipment`, `snap-search-shipments`, `snap-get-receipt`, `snap-search-receipts`, `snap-get-customer-return`, `snap-search-customer-returns`, `snap-get-product`, `snap-get-stock-totals`, `snap-get-outbound-queue`, `snap-get-stock-movements` |

The wrappers delegate to `snapGet` or `snapSearch`. They exist to carry stage codes and key field names in their descriptions, since a model reads those to choose a call [1].

## Hosting

```orient-flow
{ "v": 1, "title": "Hosting",
  "nodes": [
    { "id": "c", "label": "MCP client", "kind": "external", "ev": [10] },
    { "id": "lb", "label": "Global HTTPS load balancer", "sub": "snap.mcp.fuse.ilg.software", "kind": "step", "ev": [10] },
    { "id": "cr", "label": "Cloud Run snap-mcp-prod", "sub": "1 to 2 instances", "kind": "service", "service": "snap-mcp", "tone": "accent", "ev": [11] },
    { "id": "sc", "label": "Datadog sidecars", "sub": "GFS and ILG accounts", "kind": "step", "ev": [11] },
    { "id": "dd", "label": "Datadog", "kind": "external", "ev": [11] }
  ],
  "edges": [
    { "from": "c", "to": "lb", "label": "HTTPS 443" },
    { "from": "lb", "to": "cr", "label": "serverless NEG" },
    { "from": "cr", "to": "sc", "label": "log file on shared volume" },
    { "from": "sc", "to": "dd" }
  ] }
```

- **Cloud Run** in `bifrost-prod-global1`, `europe-west2`. It runs 1 to 2 instances at 1 CPU and 512Mi, with an HTTP startup probe on `/health`. `run.invoker` is granted to `allUsers`, and the bearer token is the whole gate [11].
- **Token.** `MCP_AUTH_TOKEN` is a Terraform `random_password` passed as a plain env var, with no Secret Manager. It sits in Terraform state and in a sensitive output. Bumping `auth_token_rotation` in `prod.tfvars` rotates it [11][12].
- **Logging.** One JSON line per request goes to `LOG_FILE` on a shared memory volume. Two `serverless-init` sidecars tail it into Datadog. The load balancer logs every request (`sample_rate = 1.0`). The app's log line carries no request body or tool argument [13]. **ASSESSED** The load balancer log carries no body either, since it records request metadata; the app log is the only source read here [10].
- **Load balancer.** A managed certificate, port 80 redirecting to 443, and a serverless NEG. The DNS A record lives in the ilg-platform project's zone, read from `ilg-platform-tfstate` [10].
- **Environments.** Prod only. `iac/env/` has `global.tfvars` and `prod.tfvars` and no dev file.

## Build, test and deploy

- pnpm 10.24.0, Node 24 (`mise.toml` and the Dockerfile), Jest 30, Biome 2.0.6, `tsc --noEmit` for `build:check`. There is no `build:check:tests` script [15].
- **CI:** `code-quality.yaml` (test, lint and build in a matrix, on push, pull request and nightly), `secops.yaml` (secrets, dependency audit, Terraform and Semgrep scans), `tf-output.yaml` (plan comment on Terraform changes), `deploy.yml` and `manual-deploy.yaml` [16].
- `code-quality.yaml` sets up Node 22 while the image and `mise.toml` use Node 24.
- `deploy.yml` runs on a push to `main`. It builds and pushes the image, then runs `apply -auto-approve` against prod. **ASSESSED** No approval gate is declared in the workflow. The reusable workflow in `ilg-platform/github-actions` could still add one [16].
- `.trivyignore.yaml` scopes each Node CVE entry to a `paths` entry for the npm copy bundled in the base image. Never widen an entry by dropping `paths`, because the same CVE may also hit a real dependency.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "src/snap/snap.tools.ts@6bcd233" },
  { "id": 2, "kind": "code", "ref": "src/snap/snap-api.service.ts@6bcd233" },
  { "id": 3, "kind": "code", "ref": "src/app.module.ts@6bcd233" },
  { "id": 4, "kind": "code", "ref": "src/main.ts@6bcd233" },
  { "id": 5, "kind": "code", "ref": "src/auth/bearer-token.guard.ts@6bcd233" },
  { "id": 6, "kind": "code", "ref": "src/mcp-server.module.ts@6bcd233" },
  { "id": 7, "kind": "code", "ref": "src/health/health.controller.ts@6bcd233" },
  { "id": 8, "kind": "url", "ref": "https://github.com/gfs-bifrost/pkg-node/blob/ab780a5/pkg/snap/src/client/snap-client.ts", "note": "withHost sets the base URL with no host check" },
  { "id": 9, "kind": "code", "ref": "src/snap/snap-circuit-open.error.ts@6bcd233" },
  { "id": 10, "kind": "code", "ref": "iac/projects/snap-mcp/load-balancer.tf@6bcd233" },
  { "id": 11, "kind": "code", "ref": "iac/projects/snap-mcp/cloud-run.tf@6bcd233" },
  { "id": 12, "kind": "code", "ref": "iac/env/prod.tfvars@6bcd233" },
  { "id": 13, "kind": "code", "ref": "src/observability/request-logger.middleware.ts@6bcd233" },
  { "id": 14, "kind": "log", "ref": "curl -X POST and GET https://snap.mcp.fuse.ilg.software/mcp returned 401; GET /health returned 200 (2026-10-13)" },
  { "id": 15, "kind": "code", "ref": "package.json@6bcd233" },
  { "id": 16, "kind": "code", "ref": ".github/workflows/deploy.yml@6bcd233" }
] }
```
