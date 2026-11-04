---
tags: [adhoc-task]
date: 2026-11-04
tldr: "cloud-sql-iam not ready to promote to terraform-modules yet: G6/E3 soak runs to ~11-10, plus a latent disk_size replace hazard and 3 cheap validations to add first"
session_id: 144409d0-1b73-440a-a6f4-da083941e6aa
status: open
---
# Assess cloud-sql-iam for promotion to ilg-platform/terraform-modules

## Outcome
Review panel (platform, security, contract) plus my own checks. Blocking: no `ignore_changes` on `settings[0].disk_size` (latent instance replacement in config-service prod once autoresize fires). Before publishing: validations for REGIONAL+shared-core tier, a user-managed migrator, and impersonators that exclude app accounts. Doc rewrite, and the target repo's 5-file/no-tests rule needs a call. M3 needs the GitHub App token wired into config-service's terragrunt calls. Owed: a fix PR if Harry says go.
