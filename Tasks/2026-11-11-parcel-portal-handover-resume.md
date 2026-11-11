---
tags: [adhoc-task]
date: 2026-11-11
tldr: "Resumed the Parcel Portal handover on the VM: #128 merged as 2938b41 after Harry approved a one-file gitleaks allowlist; its svc deploy run is parked at the prod gate; Confluence (v6), plan and PR body updated; Oliver has not replied"
session_id: 3e3bf683-a529-4b8f-afc1-7733d6a995ea
status: done
---
# Resume the Parcel Portal handover on the VM

## Outcome
PR #128 (the dev-only debug MCP) is **merged** as `2938b41`. Its only red check, `secret_scan / gitleaks`, flagged a placeholder `apiKey` in `redact_test.go:40`. The auto-mode classifier refused my push of the fix, a one-rule, one-file `.gitleaks.toml` allowlist, as a CI bypass. Harry said yes, so `aa6cea4` was pushed, all 32 checks passed, and #128 merged. The `svc deploy` run for it is parked at `docker-push-prod`, not approved. Confluence 357007366 (version 6), the plan's Not verified section and #128's PR body are updated. Oliver Wilders had not replied to the 12:00Z repro. Record: [[Handovers/2026-11-10-parcel-portal]].
