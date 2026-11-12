---
tags: [waypoint, ledger]
---
# selector2 — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-12 — Add the carrier egress port, ID-token client and Royal Mail adapter

Add the carrier egress port, ID-token client and Royal Mail adapter

Unit B5: carrier port with optional capabilities, Cloud Run ID-token HTTP client, carrier_call tracing, Royal Mail adapter. Three-lens review fixed. Finding: no number ranges for the 12 proxy carriers, so B4 dropped.

Ship: SELECTOR2-1112-ship. PR: ilg-merak/selector2#4

## 2026-11-12 — Add the multi-tenant domain schema, its Selector mapping and a synthetic seed

Add the multi-tenant domain schema, its Selector mapping and a synthetic seed

Unit B1: Drizzle schema (12 tables, composite tenant FKs), migration 0001, docs/data-model.md (CSS mapping), dev-only fail-closed synthetic seed, integration tests against Postgres 17. Review panel (data, seed/security, tests) findings fixed. Draft; merge waits on Harry.

PR: ilg-merak/selector2#3

## 2026-11-11 — Cloud SQL, migrations, readiness and public access

Cloud SQL, migrations, readiness and public access

Cloud SQL (cloud-sql-iam, Postgres 17, db-f1-micro, ZONAL, deletion protection on), IAM-only logins, a Cloud Run migrate job run inside the apply, readiness that checks the database, and allUsers invokers on selector2-api and selector2-ui (auth is in the app, later units). Dev apply: api 17 added / 1 changed / 0 destroyed, ui 1 / 1 / 0. Migrate job logged migrations applied and exited 0; api readiness returns 200 publicly. The god-password secret exists (Terraform state; read with gcloud secrets versions access) but no job reads it yet: the seeding unit adds the env. Open: no instance cap on the platform module (R8), readiness not probed by Cloud Run (R9).

PR: ilg-merak/selector2#2

## 2026-11-11 — Scaffold selector2-api and selector2-ui, IaC and CI

Scaffold selector2-api and selector2-ui, IaC and CI

New repo ilg-merak/selector2: NestJS selector2-api and SvelteKit selector2-ui in one pnpm workspace, Biome, Vitest, Terragrunt projects and four workflows. Merged to main; deploy dev applied 2 resources per app (Cloud Run service plus service account), 0 destroyed. Services are IAM-only (no allUsers), so an unauthenticated call returns 403 and no invoker is granted yet. Names carry the project name, never svc/ui.

PR: ilg-merak/selector2#1
