---
tags: [adhoc-task]
date: 2026-11-09
tldr: "Fuse MCP 401 was a stale token after the 2026-10-22 rotation; re-read it from prod state, re-added the server, and cleared a corrupt npx cache that broke shopify-dev-mcp."
session_id: 3d0aa2be-dbe0-4e59-bd69-594cd4fdf58b
status: done
---
# Remediate the Fuse and Shopify dev MCP connections

## Outcome
- `fuse` MCP returned 401 because `~/.claude.json` held the pre-rotation token (fuse-mcp#59 bumped `auth_token_rotation` to 2 on 2026-10-22). Read the current `mcp_auth_token` from prod state (needs Terraform >= 1.14; the PATH default 1.3.0 can't read the state), verified it against the endpoint, re-added the server at user scope. Now Connected.
- `shopify-dev-mcp` failed to start from a corrupt `~/.npm/_npx/8f00c70bd5114901` (ENOTEMPTY). Cleared it and reinstalled; v1.18.0 answers initialize.
- Owed: a session started before the fix must reconnect (`/mcp`) or restart to get the tools. The fuse-mcp README token step should name Terraform >= 1.14.
