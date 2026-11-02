---
tags: [waypoint, ledger]
---
# audit-service — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-10-27 — Build FROM the go-runtime rolling tag, not a digest pin

Build FROM the go-runtime rolling tag, not a digest pin

Drops the digest from the go-runtime FROM so base patches and Datadog agent updates arrive on the next build. Resolves to the same digest today (7e98f0e1), runtime unchanged.

PR: gfs-bifrost/audit-service#18

## 2026-10-27 — Re-pin the go-runtime base to 0.1-affogato on Debian 13

Re-pin the go-runtime base to 0.1-affogato on Debian 13

go-runtime:1@afa607 (Debian 12, deprecated upstream) → go-runtime:0.1-affogato@7e98f0e1 (Debian 13). Merged; dev rev 00017 verified (12 stored, source:go logs); prod at terraform-prod gate, plan 0/1/0.

PR: gfs-bifrost/audit-service#17

## 2026-10-27 — Run Datadog in the app container on the go-runtime golden image

Run Datadog in the app container on the go-runtime golden image

First consumer of ilg-platform go-runtime: FROM the golden image, logs to stdout only, Datadog sidecar + shared volume removed with its DD_* settings moved onto the app container unchanged (DD_ENV=serverless, ILG dual-ship). Dev rev 00015 verified in the GFS org (source:go, dd.datadog_init_version, fuse.audit.ingest intact); ILG org check pending. Draft.

PR: gfs-bifrost/audit-service#16

## 2026-10-22 — Let the Fuse MCP read the audit log in prod

Let the Fuse MCP read the audit log in prod

fuse-mcp-prod-sa added to prod api_readers (run.invoker + READ_CALLERS), the go-live for the MCP's audit-search/audit-get-event, which return only a per-kind allow-list projection. Grant spans every system, secrets included (accepted, decision log 2026-10-22). Ship: SHIP-1022-audit-mcp-tools.

PR: gfs-bifrost/audit-service#15

## 2026-10-22 — Unblock audit-service deploys and ship sftp_login retention to prod

Unblock audit-service deploys and ship sftp_login retention to prod

Ship: SHIP-1022-audit-retention-deploy. main was red because the runner image moved to a 6.19+ kernel, where mongo:8.0 refuses to start (SERVER-121912), and because the container scan flagged klauspost/compress 1.17.6 (CVE-2026-63209). #14 moves CI and make test-mongo to mongo:7.0 and bumps compress to 1.18.7. Deploys had been stuck since 10-14: deploy.yaml's single concurrency group (cancel-in-progress false) let Renovate run 38523356056 (254dfd9), parked at terraform-prod, block every later run, and each newer push cancelled the pending one. I cancelled it (it's an ancestor) and approved 8dec02b. Dev Atlas: a test sftp_login event got expireAt = occurredAt + 365d, and expireAt_ttl is partial on $exists. Prod is on 8dec02b (#12, #13, #10, #14). Not verified live: the read API excludeKind and list paths on the new revision, because only fuse-ui's SA is an allowed caller.

PR: gfs-bifrost/audit-service#14

## 2026-10-15 — Expire sftp_login audit events after a year and add an excludeKind read filter

Expire sftp_login audit events after a year and add an excludeKind read filter

A code-level retention policy (system -> kind -> duration) sets expireAt = occurredAt + 365d for fuse/sftp_login on ingest; Insert drops producer expireAt; a partial TTL index (expireAt_ttl, expireAfterSeconds 0, only rows with the field) deletes them. Every other kind is still kept forever.
GET /events and /filter-options gain a repeatable excludeKind (max 20, combines with kind) so fuse-ui can hide sftp_login by default; no new index.
Draft; dev is Atlas Flex, so the first dev deploy confirms the TTL index is accepted. Vault architecture/known-context/audit-event-flow still say 'forever / no TTL' and need amending on merge.

PR: gfs-bifrost/audit-service#12

## 2026-10-13 — Subscribe audit-service to the secrets audit system

Subscribe audit-service to the secrets audit system

Programme H2 part 2: local.systems.secrets -> push sub, dlt hold and DLT grants for audit.<env>.secrets.v1. Applied dev and prod (4 add).

PR: gfs-bifrost/audit-service#11

## 2026-10-12 — Build audit-service: per-system ingest, read API, legacy import

Build audit-service: per-system ingest, read API, legacy import

Audit Service unit UE (out-of-ticket). Go service at code/, private Cloud Run in dev and prod. Ingests AuditMessages by OIDC push from audit.<env>.<system>.v1, stores them once under _id=eventId in its own Atlas cluster (kept forever), and serves a system-scoped, cursor-paged read API to api_readers (fuse-ui SAs). cmd/import-legacy is human-run at the fuse-ui cutover; a dev dry run over the real audit_log mapped 702/702.
Gotchas: stacked PRs merge only via merge-async; DogStatsD must flush per request on throttled Cloud Run; gcloud user ID tokens fail the app verifier, so test with an SA token minted for the service URL.

PR: gfs-bifrost/audit-service#1
PR: gfs-bifrost/audit-service#2
PR: gfs-bifrost/audit-service#3
PR: gfs-bifrost/audit-service#4
PR: gfs-bifrost/audit-service#6
PR: gfs-bifrost/audit-service#7
PR: gfs-bifrost/audit-service#8
PR: gfs-bifrost/audit-service#9
