---
tags: [waypoint, ledger]
title: github-config — work ledger
---
# github-config — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-10-27 — Add selector-adapter repository

Add selector-adapter repository

Adds module "selector_adapter" (new gfs-bifrost/selector-adapter repo, disable_template, bifrost_admins) for the Selector adapter dev spike. Apply behind terraform-prod; check env reviewers non-empty after (#20 race).

PR: gfs-bifrost/github-config#21

## 2026-10-13 — Create repo environments after the admin team has access

Create repo environments after the admin team has access

Environments raced github_team_repository on repo creation; GitHub stored an empty reviewer list (secrets-hub couldn't approve deploys). depends_on fix; secrets-hub reviewers restored via API to the declared value.

PR: gfs-bifrost/github-config#20

## 2026-10-13 — Add secrets-hub repository

Add secrets-hub repository

Secrets Hub programme H0: bootstrap gfs-bifrost/secrets-hub (no template, bifrost_admins admin, terraform envs), mirroring audit-service #18. Draft.

PR: gfs-bifrost/github-config#19

## 2026-10-12 — Add the audit-service repository

Add the audit-service repository

Adds a module "audit_service" block that creates gfs-bifrost/audit-service with no template, bifrost_admins as admin, and terraform-dev/prod environments. Unit UB of the Audit Service programme (out-of-ticket).

PR: gfs-bifrost/github-config#18

## 2026-07-07 — FUSE-952

Archive snap-queue-polling-service — merged into snap-adapter monorepo

Archived snap-queue-polling-service — merged into snap-adapter monorepo.

PR: gfs-bifrost/github-config#10

## 2025-09-24 — FUSE-105

Add pkg-node repository for core Node/Bun packages

Added the pkg-node repository for core Node/Bun packages, and updated outputs for other repos.

PR: gfs-bifrost/github-config#2
