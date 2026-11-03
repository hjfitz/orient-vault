---
tags: [waypoint, ledger]
---
# orient — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-03 — Make orient safe to run on several machines: durable data in the vault, the vault in git

Make orient safe to run on several machines: durable data in the vault, the vault in git

The vault is a git repo synced by orient-vault-sync (scripts/vault-sync.sh): a 90 s timer plus a kick from every writer (wp, cust, orient saves and .knowledge stores, a Claude Code PostToolUse hook). It merges, never rebases; a conflict aborts and notifies. Origin is still the local stand-in ~/.local/state/orient/vault-remote.git until Plan B (go-remote-and-bootstrap-a-fresh-machine) moves it to hjfitz/orient-vault.

Durable records moved out of the state dir to <vault>/.knowledge/records/<host>/ (host from ~/.config/orient/host), one writer per file. Recordings live at .knowledge/recordings/<host>/, with audio git-ignored and pruned at 14 days; another host's recordings are read-only (409). plan-status and todo-defers are append-only JSONL. The manifest has one writer (config manifestWriter). The writers are versioned in ~/projects/orient-writers and linked into ~/.claude by directory. The sync-claude-config copier is retired.

Gotchas: the audio of four 2026-10-19 recordings was lost because the prune ran on service start before any dry run. wp tick used to tick the template's example increment 6; fixed in writers 01dbcf2, but images/remote-compute-vm-image-packer-ubuntu-24-04 and remote-compute/first-workstation-stack-module-and-one-engineer- already have the example ticked. orient commits 8196526..11aaab0 (direct to master, no PR). See [[architecture]] and [[known-context]] under Systems/orient.
