---
tags: [waypoint, ledger]
---
# orient — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-06 — Give the orient MCP a Waypoint system lens and correct service headers

Give the orient MCP a Waypoint system lens and correct service headers

orient-entity gains kind=system: purpose and owner from Systems/<name>/system.yaml, members by type with owners, docs with verified dates, and the open ## Unknowns. Membership comes from the sidecars table (each service's own waypoint.yaml system:), the same source wp system status reads. system.yaml and Unknowns are not indexed, so mcp/internal/vault/system.go reads them. Service doc lines now end in STALE etc. from the wp doctor verdict in documents.meta.attention, so the MCP needs no git.

Root cause of the wrong service header (owner=bifrost, nulls, no system): src/index/writer.ts merged entities.sidecar as found.sidecar ?? sidecar, so the wp onboard skeleton yaml stuck forever. 7 services were affected, and so was the web /service header. The fresh sidecar now wins. The live index was re-swept with 0 divergent. Gotcha: the sidecars table is never pruned.

Direct to master on hjfitz/orient: b6e3fa7 (indexer), 38061ee (MCP + spec). Redeployed web and rebuilt mcp/bin/orient-mcp. Running Claude Code sessions need a restart to load it. Plan: [[mcp-system-lens-and-correct-service-metadata]].

## 2026-11-03 — Make orient safe to run on several machines: durable data in the vault, the vault in git

Make orient safe to run on several machines: durable data in the vault, the vault in git

The vault is a git repo synced by orient-vault-sync (scripts/vault-sync.sh): a 90 s timer plus a kick from every writer (wp, cust, orient saves and .knowledge stores, a Claude Code PostToolUse hook). It merges, never rebases; a conflict aborts and notifies. Origin is still the local stand-in ~/.local/state/orient/vault-remote.git until Plan B (go-remote-and-bootstrap-a-fresh-machine) moves it to hjfitz/orient-vault.

Durable records moved out of the state dir to <vault>/.knowledge/records/<host>/ (host from ~/.config/orient/host), one writer per file. Recordings live at .knowledge/recordings/<host>/, with audio git-ignored and pruned at 14 days; another host's recordings are read-only (409). plan-status and todo-defers are append-only JSONL. The manifest has one writer (config manifestWriter). The writers are versioned in ~/projects/orient-writers and linked into ~/.claude by directory. The sync-claude-config copier is retired.

Gotchas: the audio of four 2026-10-19 recordings was lost because the prune ran on service start before any dry run. wp tick used to tick the template's example increment 6; fixed in writers 01dbcf2, but images/remote-compute-vm-image-packer-ubuntu-24-04 and remote-compute/first-workstation-stack-module-and-one-engineer- already have the example ticked. orient commits 8196526..11aaab0 (direct to master, no PR). See [[architecture]] and [[known-context]] under Systems/orient.
