---
tags: [waypoint, ledger]
---
# ilg-platform-core-infra — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-10-29 — Let ilg-merak write DNS records under delivery.<domain>

Let ilg-merak write DNS records under delivery.<domain>

ilg-merak claims the delivery namespace: each env's merak terraform-runner gets dnsRecordWriter on the central zones (freightops.dev, ilg.software), zone hardcoded so no state read. First records: parcel.delivery.<domain> (UI behind the serverless LB) and sftp.parcel.delivery.<domain>. Also: tf-plan-pr now plans tfvars-only PRs. Applied in both envs (1 added each; merged and prod-approved by Harry).

PR: ilg-platform/core-infra#16

## 2026-10-29 — VM image staging bucket and main-only build grant for ilg-platform/images

VM image staging bucket and main-only build grant for ilg-platform/images

For the remote-compute Arch VM image (Packer qemu build + googlecompute-import). New vm-images.tf, prod state path only: bucket ilg-platform-vm-image-staging (europe-west2, uniform access, public access prevented, 7-day delete), and for principal subject repo:ilg-platform/images:ref:refs/heads/main: roles/storage.objectAdmin on the bucket and roles/compute.storageAdmin on the project. Branches and PRs of images get nothing. Dev plan no-op; prod 3 added, 0 changed, 0 destroyed.

PR: ilg-platform/core-infra#17

## 2026-10-27 — Add the golden-images Artifact Registry

Add the golden-images Artifact Registry

Public-read Docker registry europe-west2-docker.pkg.dev/ilg-platform-ec02/images for golden base images, created from the prod state path only; ilg-platform/images pushes by direct WIF. Also enables the AR API and grants terraform-runner artifactregistry.admin (editor can't set repo IAM). Draft, prod plan 6/0/0 pending Harry's review.

PR: ilg-platform/core-infra#15
