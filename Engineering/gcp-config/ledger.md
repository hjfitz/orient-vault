---
tags: [waypoint, ledger]
---
# gcp-config — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-05 — Datadog GCP integration account for ilg-merak dev and prod

Datadog GCP integration account for ilg-merak dev and prod

Adds a datadog-integration SA per project: monitoring, compute and cloud asset viewer, plus browser. The GFS Datadog org's STS principal (ddgci-a9b25524d9a688f3633c@datadog-gci-sts-us1-prod) gets serviceAccountTokenCreator on that account only. Same shape as ilg-cx/cx-core-infra and gfs-bifrost/datadog-integration. parcel-portal registers it with Datadog (datadog_integration_gcp_sts). Plans: 6 to add in dev and in prod.

PR: ilg-merak/gcp-config#9

## 2026-10-29 — Admit remote-compute: WIF, state prefix, runner instance IAM, logging APIs

Admit remote-compute: WIF, state prefix, runner instance IAM, logging APIs

Prerequisites for ilg-platform/remote-compute (per-engineer Claude Code VMs). terraform-runner gains roles/compute.instanceAdmin.v1 (editor lacks compute.instances.setIamPolicy, which instance-level IAM needs). ilg_pool_repositories admits ilg-platform/remote-compute; state_stacks gives it the remote-compute/ prefix in ilg-platform-tfstate-prod; logging + monitoring APIs enabled project-wide. Prod apply: 4 added, 1 changed (tfstate-prod bucket policy, in place), 0 destroyed.

PR: ilg-platform/gcp-config#11

## 2026-10-28 — MKP-19

Grant terraform-runner compute.instanceAdmin.v1

Needed for parcel-portal's SFTP MIG. Plan 1 to add per env.

PR: ilg-merak/gcp-config#7

## 2026-10-25 — Ship per-env Terraform state buckets to prod

Ship per-env Terraform state buckets to prod

Ship: SHIP-1025-tfstate-env-buckets. Merged as cc2e4b0; Deploy run 40192325891 applied 6 added / 0 changed / 0 destroyed. ilg-platform-tfstate-dev and -prod live in ilg-platform-ec02 with authoritative IAM (no default projectViewer read). Stack runners get objectUser on their own <stack>/ prefix plus legacyBucketReader; ilg-merak registered first. Live probes as the Merak runners: own prefix allowed, another stack's prefix denied, the other env's bucket denied; a real GCS backend init/apply/plan round-trip worked. Follow-ups: move Merak's state across; ilg-platform-tfstate still grants projectViewer read; no lifecycle rule for old versions.

PR: ilg-platform/gcp-config#10

## 2026-10-25 — Add per-env Terraform state buckets for new stacks

Add per-env Terraform state buckets for new stacks

ilg-platform-tfstate-dev and -prod in ilg-platform-ec02, so new stacks keep state off SRE's gfs-terraform-core-tfstate. Per-stack prefix-scoped access via state_stacks; ilg-merak registered first (grants only). Plan: 8 add, 0 change, 0 destroy. Awaiting plan agreement.

PR: ilg-platform/gcp-config#10
