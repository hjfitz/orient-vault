---
tags: [waypoint, ledger]
---
# cx — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-10-12 — Move cx to Terragrunt and the ilg-platform reusable workflows

Move cx to Terragrunt and the ilg-platform reusable workflows

Moved gfs-ecm/cx off the gfs-sre/terraform-framework hand-rolled CI and onto the platform stack. Terragrunt layout uses a generated backend at stacks/cx/<env>, so the state is unchanged. Module now comes from ilg-platform/terraform-modules project/factory@0.1-affogato; its .tf files are identical. CI runs github-actions@0.2-bonbon: dev then prod deploy, PR plans, manual deploy, and secops with Checkov kept. Local plans as each env's runner show No changes for both. CI needs PLATFORM_CI_APP_ID and PLATFORM_CI_APP_PRIVATE_KEY set on the repo first. Not routed to Wolf.

PR: gfs-ecm/cx#7
