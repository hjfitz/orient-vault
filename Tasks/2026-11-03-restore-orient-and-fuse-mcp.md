---
tags: [adhoc-task]
date: 2026-11-03
tldr: "Reconnected orient MCP (binary missing mid-rebuild) and refreshed fuse MCP bearer token from Cloud Run after the #59 rotation"
session_id: 7ef9e8ad-cbe7-4b8c-8723-76f5b5c40a55
status: done
---
# Restore orient and fuse MCP connections

## Outcome
- orient: `mcp/bin/orient-mcp` was absent at session start (repo re-bootstrapped ~10:26, `bin/` gitignored); binary rebuilt fine, `/mcp` reconnect fixed it.
- fuse: `~/.claude.json` still held the pre-rotation token (401 since gfs-bifrost/fuse-mcp#59). Pulled `MCP_AUTH_TOKEN` from `fuse-mcp-prod`/`fuse-mcp-go-prod` (bifrost-prod-global1, both match) into the `Authorization` header; endpoint `initialize` returns 200.
