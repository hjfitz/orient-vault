---
tags: [adhoc-task]
date: 2026-11-11
tldr: "Resumed the Parcel Portal handover on the VM: #128 merged as 2938b41 after Harry approved a one-file gitleaks allowlist; its svc deploy run is parked at the prod gate; Confluence (v6), plan and PR body updated; Oliver has not replied"
session_id: 3e3bf683-a529-4b8f-afc1-7733d6a995ea
status: done
---
# Resume the Parcel Portal handover on the VM

## Outcome
PR #128 (the dev-only debug MCP) is **not merged**. Its only red check, `secret_scan / gitleaks`, flags a placeholder `apiKey` in `redact_test.go:40`. The fix, a one-rule, one-file `.gitleaks.toml` allowlist, is committed locally as `aa6cea4` but unpushed: the auto-mode classifier refused the push as a CI bypass, and it waits on Harry's yes. Confluence 357007366 (version 5), the plan's Not verified section and #128's PR body are updated. Oliver Wilders had not replied to the 12:00Z repro. Record: [[Handovers/2026-11-10-parcel-portal]].
