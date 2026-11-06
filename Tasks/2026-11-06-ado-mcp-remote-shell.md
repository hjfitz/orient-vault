---
tags: [adhoc-task]
date: 2026-11-06
tldr: "Got ado-local-mcp connecting on hjf.shell — repointed it at mise's node@24 npx (system Arch node has no npm)"
session_id: 0fb571d0-d903-483b-9e8b-1198b51d571f
status: done
---
# Set up the Azure DevOps MCP on the remote shell

## Outcome
ado-local-mcp was already synced to harry@hjf.shell.platform.ilg.software but failed: Arch's nodejs ships without npx, and pacman -S npm fails on a stale sync DB (full -Syu deferred, live sessions running). Remote entry now runs `mise exec node@24 -- npx -y @azure-devops/mcp ...`; connected, PAT returns 200. Backup at ~/.claude.json.bak-ado-*. Sync keeps the remote-divergent entry (KEPT). ado-remote-mcp still fails on both machines (no dynamic client registration).
