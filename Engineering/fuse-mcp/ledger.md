---
tags: [waypoint, ledger]
title: fuse-mcp — work ledger
---
# fuse-mcp — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-10-22 — Clear the nightly govulncheck and MCP SDK findings

Clear the nightly govulncheck and MCP SDK findings

Go raised to 1.26.10 (GO-2026-6809 in crypto/x509, reached from soakcheck) and the TypeScript server's @modelcontextprotocol/sdk 1.31.0 -> 1.32.0 (GHSA-22jm-h49p-29qw). The nightly Code Quality Go and DevSecOps runs had been red since 2026-10-21; fixed in its own PR because it blocked SHIP-1022-audit-mcp-tools.

PR: gfs-bifrost/fuse-mcp#61

## 2026-10-22 — Add read-only audit tools to the MCP

Add read-only audit tools to the MCP

audit-search and audit-get-event read the production Fuse audit log in audit-service as fuse-mcp-prod-sa and return a default-deny, per-kind allow-list projection (never snapshots or credentials). Shared token rotated separately. Ship: SHIP-1022-audit-mcp-tools.

PR: gfs-bifrost/fuse-mcp#56
PR: gfs-bifrost/fuse-mcp#57
PR: gfs-bifrost/fuse-mcp#58
PR: gfs-bifrost/fuse-mcp#59

## 2026-10-13 — Add secrets-hub and the audit secrets topic to MCP data

Add secrets-hub and the audit secrets topic to MCP data

services/api-endpoints/pubsub-topology/shared-packages/event-contracts updated; parity baseline accepted; go test green. Direct to master.

PR: gfs-bifrost/fuse-mcp@5e89e3c (direct commit)

## 2026-10-09 — Build with Go 1.26.9 to clear the stdlib vulnerability gate

Build with Go 1.26.9 to clear the stdlib vulnerability gate

govulncheck and the Go image scan failed on master for stdlib GO-2026-6617, fixed only in Go 1.26.9. Module, CI, mise and the Go image moved to 1.26. Merged and deployed.

PR: gfs-bifrost/fuse-mcp#55

## 2026-10-09 — Add tracking-service tools to the Go server

Add tracking-service tools to the Go server

Twelve read-only tracking-* tools over tracking-service's private API, using a metadata-server identity token. Replaces the stdio MCP the service shipped. List rows are compacted; record/payloads only on request. API URL read from the fuse-tracker tfstate, falling back to tracking-service's after cutover. Draft; merge after the tracking-service PR granting fuse-mcp-prod-sa invoker.

PR: gfs-bifrost/fuse-mcp#54

## 2026-09-29 — Add lookup-snap-instance tool (SNAP instance to database to site)

Add lookup-snap-instance tool (SNAP instance to database to site)

New MCP tool mapping ILG SNAP instances (ilg001-005) to database and warehouse sites; static data in data/snap-instances.json, plus a live includeBusinesses join over config-service GET /api/v1/backend (credentials never decoded). Added to the parity baseline as a Go-only tool. Not merged: a merge to master deploys ungated.

PR: gfs-bifrost/fuse-mcp#46
