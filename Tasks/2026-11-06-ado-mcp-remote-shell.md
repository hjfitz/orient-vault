---
tags: [adhoc-task]
date: 2026-11-06
tldr: "orient hosted on the VM; scribe split (laptop records, VM processes, relay controls) — scribe plan 5/6, inc 6 gated on 3 real meetings; vault sync-on-push live (~5s each way)"
session_id: 0fb571d0-d903-483b-9e8b-1198b51d571f
status: open
---
# Set up ADO MCP on the remote shell, sync orient between machines

## Outcome
ado-local-mcp was already synced to harry@hjf.shell.platform.ilg.software but failed: Arch's nodejs ships without npx, and pacman -S npm fails on a stale sync DB (full -Syu deferred, live sessions running). Remote entry now runs `mise exec node@24 -- npx -y @azure-devops/mcp ...`; connected, PAT returns 200. Backup at ~/.claude.json.bak-ado-*. Sync keeps the remote-divergent entry (KEPT). ado-remote-mcp still fails on both machines (no dynamic client registration).

orient: VM had unpushed 567df31 (usage by machine); cherry-picked onto laptop master as 1b8ffbf, tests green, pushed; VM rebased onto it. Both machines redeployed (web, index; VM orient-mcp rebuilt).
Vault (VM): sync failing since 5 Nov 16:04 — handover vault copy dropped laptop recordings into a sparse-excluded path. Moved them to ~/.local/state/orient/quarantined-recordings-20261106 on the VM (one audio.ogg is the only remaining copy), reapplied sparse rules. 2026-11-09: merged VM history (399 ahead / 319 behind) as e37445d — 59 conflicts: 40 path-only (laptop kept), 17 VM-newer (taken, paths normalised), People notes + this record from laptop. Both vault syncs green. Root cause (vault copied by sync-claude-config --folder) removed from session-handover ship step and from ~/.config/systemd/user/sync-claude-config.service (timer was already disabled). Quarantined recordings remain on the VM.

2026-11-09: orient moved to the VM as the main instance. Laptop runs `orient-tunnel.service` (ssh -L 3000, 3011 to the VM; terminal verified against VM tmux); laptop orient-pty disabled; laptop orient-web moved to :3001 by drop-in `orient-web.service.d/recordings-only-port.conf`, for Recordings only. desk/scribe hit :3000 (the VM) unchanged. No reverse forward for scribe: the remote-compute image sets `AllowTcpForwarding local` (ilg-platform/images, smoke-tested). Missing GitHub fuse repos cloned to the VM for headless runs; 13 ADO repos not (no ADO SSH on the VM). Vault keeps backing up through orient-vault-sync on both sides.
2026-11-09: planned scribe on the VM — [[scribe-on-the-vm-capture-on-the-laptop-everythin]] (draft, 6 increments, opus/high; 5 UNRESOLVED questions for Harry). Interim: desk pointed at laptop :3001 via `orient-desk.service.d/recordings-interim.conf` (the VM orient has no scribe).

2026-11-09 (later): scribe plan incs 1–5 done — VM scribe server (`-adopt laptop`), upload ingest, handoff, laptop recorder (delete on receipt), relay (VM page starts/stops laptop recordings, ~1 s). Inc 6 (retire :3001, desk → VM) gated on 3 real meetings via the VM page. Vault sync-on-push plan done (laptop→VM 6.6 s, VM→laptop 4.6 s); sign-off blocked only by Harry's uncommitted desk/gnome-extension files. Fixed an inc-4 regression: pre-switch laptop recordings were uneditable; VM now adopts `laptop/`, audio copied (13, sha-verified), laptop audio deleted.
