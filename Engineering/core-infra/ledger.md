---
tags: [waypoint, ledger]
title: core-infra — work ledger
---
# core-infra — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-09-21 — FUSE-1194

Provision the GCS bucket for stock sync export files

New private stock_sync_export bucket (dev + prod), uniform_bucket_level_access +
public_access_prevention=enforced (mirrors ilg-secure-notes' precedent, not the
public media bucket). Writer IAM is roles/storage.objectCreator scoped only to
snap-queue-polling-service's Cloud Run SA, via a new stock_sync_export_writer_sas
tfvar mirroring cross_env_tfstate_reader_sas' shape. No lifecycle rule yet --
deferred until FUSE-1195/consumer work has real file-size data (agreed with
Harry). Exposes a stock_sync_export_bucket_name output so the paired
snap-adapter change resolves it via terraform_remote_state rather than a
hard-coded string. Verified with a real terragrunt plan against dev and prod
state -- both come back as exactly 2 to add, 0 to change, 0 to destroy.
Storage-only half of stage-2 stock sync; FUSE-1195 is the code that writes to
this bucket and publishes the confirmation_ready backlink.

PR: gfs-bifrost/core-infra#14

## 2026-09-16 — DNS zone decommissioned in place (code not yet removed)

This repo's entire DNS responsibility moved to `ilg-platform/core-infra` (project
`ilg-platform-ec02`) via the `ilg-platform DNS Migration` programme
(`Bifrost/ilg-platform DNS Migration/` in the vault, signed off 2026-09-16). No PR
against this repo — the move was: stand up equivalent zones + records in the new
project, cut registrar delegation over, repoint every consuming service's
Terraform at the new stack. `dns.tf` here is unchanged code but dead — its zone is
no longer delegated to. Removal (deleting `dns.tf` + the `dns_zone_name`/
`dns_name_servers` outputs) is the programme's D1 unit, gated on a 7-day
quiet-period check, earliest 2026-09-22, plus confirming `ilg-tech-services`
(a consumer of these zones the migration's own survey initially missed —
`route-check`, `tools-api`) is fully off this zone too. See `architecture.md`'s
DNS section for the present-tense detail.
## 2025-10-15 — FUSE-339

Add secrets for config service and update Terraform and Terragrunt versions

Added secrets for config service and updated Terraform and Terragrunt versions.

PR: gfs-bifrost/core-infra#1

