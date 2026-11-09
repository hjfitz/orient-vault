---
tags: [adhoc-task]
date: 2026-11-06
tldr: "ado-local-mcp working on hjf.shell; orient synced at 1b8ffbf on laptop/VM/GitHub; VM vault (diverged since 3 Nov) merged as e37445d and syncing again; handover no longer copies the vault"
session_id: 0fb571d0-d903-483b-9e8b-1198b51d571f
status: done
---
# Set up ADO MCP on the remote shell, sync orient between machines

## Outcome
ado-local-mcp was already synced to harry@hjf.shell.platform.ilg.software but failed: Arch's nodejs ships without npx, and pacman -S npm fails on a stale sync DB (full -Syu deferred, live sessions running). Remote entry now runs `mise exec node@24 -- npx -y @azure-devops/mcp ...`; connected, PAT returns 200. Backup at ~/.claude.json.bak-ado-*. Sync keeps the remote-divergent entry (KEPT). ado-remote-mcp still fails on both machines (no dynamic client registration).

orient: VM had unpushed 567df31 (usage by machine); cherry-picked onto laptop master as 1b8ffbf, tests green, pushed; VM rebased onto it. Both machines redeployed (web, index; VM orient-mcp rebuilt).
Vault (VM): sync failing since 5 Nov 16:04 — handover vault copy dropped laptop recordings into a sparse-excluded path. Moved them to ~/.local/state/orient/quarantined-recordings-20261106 on the VM (one audio.ogg is the only remaining copy), reapplied sparse rules. 2026-11-09: merged VM history (399 ahead / 319 behind) as e37445d — 59 conflicts: 40 path-only (laptop kept), 17 VM-newer (taken, paths normalised), People notes + this record from laptop. Both vault syncs green. Root cause (vault copied by sync-claude-config --folder) removed from session-handover ship step and from ~/.config/systemd/user/sync-claude-config.service (timer was already disabled). Quarantined recordings remain on the VM.
