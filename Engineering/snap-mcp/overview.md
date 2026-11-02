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
title: snap-mcp — overview
thesis: 'snap-mcp is a stateless MCP server that lets agents read and write the SnapFulfil
  WMS for any tenant: it holds no customer config and takes each tenant''s connection
  per call, and it stays apart from fuse-mcp because the system and the credential
  model differ.'
confidence: high
---
# snap-mcp — overview

```orient-bluf
{ "v": 1, "bluf": "snap-mcp is a stateless MCP server that lets agents read and write the SnapFulfil WMS for any tenant: it holds no customer config and takes each tenant's connection per call, and it stays apart from fuse-mcp because the system and the credential model differ.", "confidence": "high", "action": "Do not store tenant credentials here. Callers pass host, username and password on every tool call." }
```

## Responsibility

- The server exposes the SnapFulfil WebAPIv2 surface, all 43 entities, as 15 MCP tools [1].
- Five tools are generic and take an entity name: `snap-list-entities`, `snap-get`, `snap-search`, `snap-lookup` and `snap-write`.
- Ten are per-entity wrappers that carry domain context in their descriptions. They delegate to the generic ones [1].
- Agents use it to chain from a Datadog log reference (a ShipmentId, an order reference, a SKU) to the live WMS record.
- A write needs `confirm: true`. A read that fails schema validation still returns its raw data with a warning [1][2].

## Why it exists separately

The server fronts a different system from fuse-mcp. fuse-mcp serves Fuse's own platform knowledge behind its own shared token. snap-mcp talks to SnapFulfil and needs per-tenant credentials.

Every tool takes the tenant's `host`, `username` and `password` as parameters [1]. The caller reads them from the Fuse MCP `get-snap-connection` tool, which pulls them live from config-service. This server keeps no copy to drift. One deployment addresses any tenant.

The only credential it owns is its own bearer token, `MCP_AUTH_TOKEN` [3].

## Neighbours

```orient-flow
{ "v": 1, "title": "snap-mcp in context",
  "nodes": [
    { "id": "agent", "label": "MCP client", "sub": "an agent, bearer token", "kind": "external", "ev": [3] },
    { "id": "fmcp", "label": "fuse-mcp", "sub": "get-snap-connection", "kind": "service", "service": "fuse-mcp", "ev": [4] },
    { "id": "cfg", "label": "config-service", "sub": "BACKEND_CONFIG", "kind": "service", "service": "config-service", "ev": [4] },
    { "id": "smcp", "label": "snap-mcp", "sub": "15 tools, stateless", "kind": "service", "service": "snap-mcp", "tone": "accent", "ev": [1] },
    { "id": "snap", "label": "SnapFulfil WMS", "sub": "per-tenant host, Basic auth", "kind": "external", "ev": [2] },
    { "id": "dd", "label": "Datadog", "sub": "two accounts via sidecars", "kind": "external", "ev": [5] }
  ],
  "edges": [
    { "from": "agent", "to": "fmcp", "label": "ask for a connection", "style": "dashed" },
    { "from": "fmcp", "to": "cfg" },
    { "from": "agent", "to": "smcp", "label": "tool call + connection" },
    { "from": "smcp", "to": "snap", "label": "GET, or gated write" },
    { "from": "smcp", "to": "dd", "label": "request log lines" }
  ] }
```

The agent is the courier: it carries the connection from fuse-mcp to snap-mcp. The two servers never call each other.

## Where the reference lives

[[architecture]] holds the request path, the client cache, the tolerant-read rule and the hosting. [[known-context]] holds ownership and the history of the cache bug. The README holds the tool tables. Read `origin/main`, not a local tree: two checkouts of this repo exist (`snap-mcp` and `snap-mcp-server`) and either may lag.

Do not trust three sources:

- `package.json` still describes "read-only access". `snap-write` creates, updates and deletes.
- The `iac/env/prod.tfvars` comment about a `snap_credentials` variable is stale. No such variable exists.
- The last bullet under Unknowns in [[known-context]] still asks about the cache bug. Pull request 23 fixed it.

## What deliberately isn't here

- **Stored SNAP credentials.** Callers supply them per call.
- **A hard validation gate on reads.** A mismatched record comes back raw with `validated: false`, so an unverified entity stays useful.
- **Sessions.** The HTTP transport is stateless, so any Cloud Run instance serves any call.
- **A dev environment.** Only `prod.tfvars` exists.
- **A repo agent guide.** The repo has no `CLAUDE.md` or `AGENTS.md`.
- **Business logic.** The server only maps tool calls to SNAP routes. Fuse behaviour belongs to snap-adapter and the poller.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "src/snap/snap.tools.ts@6bcd233" },
  { "id": 2, "kind": "code", "ref": "src/snap/snap-api.service.ts@6bcd233" },
  { "id": 3, "kind": "code", "ref": "src/auth/bearer-token.guard.ts@6bcd233" },
  { "id": 4, "kind": "code", "ref": "README.md@6bcd233", "note": "Credentials section names get-snap-connection and BACKEND_CONFIG" },
  { "id": 5, "kind": "code", "ref": "iac/projects/snap-mcp/cloud-run.tf@6bcd233" }
] }
```
