---
tags:
- waypoint
- fuse-mcp
verified: '2026-10-13'
verified_sha: d455b6e
verified_paths:
- README.md
- AGENTS.md
- iac/env/prod.tfvars
- iac/projects/fuse-mcp
- internal/bootstrap/server.go
- internal/knowledge
- internal/tools
- internal/adapters
- data/services.json
- embed.go
- mise.toml
- .github/workflows/deploy.yml
title: fuse-mcp — overview
thesis: fuse-mcp gives AI agents Fuse's platform knowledge and live service tools
  over MCP. The Go server takes 100% of traffic; the TypeScript server idles at weight
  0 as the rollback.
confidence: high
---
# fuse-mcp — overview

```orient-bluf
{ "v": 1, "bluf": "fuse-mcp gives AI agents Fuse's platform knowledge and live service tools over MCP. The Go server takes 100% of traffic; the TypeScript server idles at weight 0 as the rollback.", "confidence": "high", "action": "Do not edit src/ to change behaviour: it does not serve traffic. Go owns every tool." }
```

## Responsibility

- It serves 15 embedded knowledge resources, one resource template and one prompt. The data is `data/*.json` compiled into the binary [1][2].
- It serves 44 tools. Nine read only the embedded data, and `lookup-snap-instance` does unless the caller passes `includeBusinesses`. The other 34 call live Fuse services [3].
- The live tools cover config-service, dedupe-service, replay-service, collector, fapi, fuse-mocker and tracking-service.
- Production writes need `confirm: true`. That covers `config-write`, `submit-to-fuse`, both dedupe releases and both replay writes [4].
- Each tool is a schema plus a description. For an MCP server that surface is the API, and models read the descriptions.

## Why it exists separately

It is the one place Fuse knowledge and live-service access reach models. Its consumer is an agent, not a human or a service.
That consumer needs stable tool names, stable schemas and descriptions that read well.

Go serves all of it. `go_traffic_percent` is 100 in `iac/env/prod.tfvars`, and the TypeScript service stays deployed at weight 0 [5][6].
Lowering that number is the rollback. It is a weight change, not a redeploy. A rollback is lossy: 14 tools exist only in Go [7].

## Neighbours

```orient-flow
{ "v": 1, "title": "fuse-mcp in context",
  "nodes": [
    { "id": "ag", "label": "AI agents", "sub": "Claude Code, Cursor", "kind": "external", "ev": [2] },
    { "id": "m", "label": "fuse-mcp", "sub": "Go, POST /mcp", "kind": "service", "service": "fuse-mcp", "tone": "accent", "ev": [2, 5] },
    { "id": "kb", "label": "data/*.json", "sub": "go:embed", "kind": "store", "ev": [8] },
    { "id": "cs", "label": "config-service", "kind": "service", "service": "config-service", "ev": [3] },
    { "id": "dd", "label": "dedupe-service", "kind": "service", "service": "dedupe-service", "ev": [3] },
    { "id": "rp", "label": "replay-service", "kind": "service", "service": "replay-service", "ev": [3] },
    { "id": "co", "label": "collector", "kind": "service", "service": "collector", "ev": [3] },
    { "id": "fa", "label": "fapi", "kind": "service", "service": "fapi", "ev": [3] },
    { "id": "mo", "label": "fuse-mocker", "sub": "dev only", "kind": "service", "service": "fuse-mocker", "ev": [3] },
    { "id": "tr", "label": "tracking-service", "sub": "read-only, ID token", "kind": "service", "service": "tracking-service", "ev": [9] }
  ],
  "edges": [
    { "from": "ag", "to": "m", "label": "bearer token" },
    { "from": "m", "to": "kb", "label": "knowledge" },
    { "from": "m", "to": "cs" },
    { "from": "m", "to": "dd" },
    { "from": "m", "to": "rp" },
    { "from": "m", "to": "co" },
    { "from": "m", "to": "fa", "label": "as the business" },
    { "from": "m", "to": "mo" },
    { "from": "m", "to": "tr" },
    { "from": "fa", "to": "cs", "label": "apiKey lookup", "style": "dashed" }
  ] }
```

Agents call one endpoint. The tools reach each service with that service's own credential, resolved per call [3][9].
`submit-to-fuse` authenticates as the business: it reads the business's REST connector `apiKey` from config-service [3].
The dashed edge shows that dependency.

## Where the reference lives

[[architecture]] carries the layout, the parity harness, the traffic split, auth and the build. [[known-context]] carries
the leaked-token note and two bugs found only under the split. The unit history is in `Bifrost/Fuse MCP Go/Migration State`.

Do not trust three sources:

- The `README.md` "Migration status" section still says the split ramps `0 → 10 → 50 → 100`. It is at 100 [5].
- The `mise.toml` header still says the TypeScript server serves production until the split reaches 100% [10].
- `data/services.json` still lists this service as Node 22 and NestJS, under the directory `fuse-mcp-server` [13].
  The same catalog entry feeds `lookup-service`. [[known-context]] repeats the pre-Go picture.

Two local checkouts of this repo exist, `~/code/fuse/fuse-mcp` and `~/code/fuse/fuse-mcp-server`. They are the same GitHub repo.
The repo records no owner. **UNKNOWN** whether ownership has moved to the wider team, as [[known-context]] expected.

## What deliberately isn't here

- **A dev environment.** A push to `master` builds both images and applies Terraform straight to prod. Nothing gates it [11].
- **Per-caller authorization.** One shared bearer token gates every tool [2][12]. Per-caller auth is out of scope.
- **Customer data and a datastore.** The server holds no state. It reads embedded JSON and calls services.
- **SNAP access.** The snap MCP owns it. `get-snap-connection` only hands over the connection for that server to use.
- **Metrics invented for the port.** Logs go to a file that two Datadog sidecars ship, as before.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "internal/knowledge/resources.go@d455b6e" },
  { "id": 2, "kind": "code", "ref": "internal/bootstrap/http.go@d455b6e" },
  { "id": 3, "kind": "code", "ref": "internal/bootstrap/server.go@d455b6e" },
  { "id": 4, "kind": "code", "ref": "internal/tools/config.go@d455b6e" },
  { "id": 5, "kind": "code", "ref": "iac/env/prod.tfvars@d455b6e" },
  { "id": 6, "kind": "code", "ref": "iac/projects/fuse-mcp/load-balancer.tf@d455b6e" },
  { "id": 7, "kind": "code", "ref": "internal/bootstrap/testdata/ts-baseline.json@d455b6e" },
  { "id": 8, "kind": "code", "ref": "embed.go@d455b6e" },
  { "id": 9, "kind": "code", "ref": "internal/adapters/tracking.go@d455b6e" },
  { "id": 10, "kind": "code", "ref": "mise.toml@d455b6e" },
  { "id": 11, "kind": "code", "ref": ".github/workflows/deploy.yml@d455b6e" },
  { "id": 12, "kind": "code", "ref": "internal/auth/bearer.go@d455b6e" },
  { "id": 13, "kind": "code", "ref": "data/services.json@d455b6e" }
] }
```
