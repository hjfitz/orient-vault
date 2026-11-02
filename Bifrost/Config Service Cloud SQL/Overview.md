---
title: "Config Service Cloud SQL — Overview"
status: planning
verdict: go
owner: "Harry"
services: ["config-service", "terraform-modules", "fuse-mcp-server"]
created: "2026-10-28"
updated: "2026-10-28"
tags: [bifrost]
---
# Config Service Cloud SQL — Overview

<!-- The narrative and the verdict. PROGRESS lives in the Migration State doc, not here — link it,
     never duplicate its ledger. This doc changes rarely; the state doc changes every session. -->

## Deliverables
- [[Config Service Cloud SQL/Migration State|Migration State]] — the live source of truth for progress.
- `docs/migrations.md` in the config-service repo: how schema migrations are written, reviewed, run and rolled back (B3).
> SUPERSEDED 2026-10-28 — connector-only public IP through our own module; see the next two lines.
- A Cloud SQL for PostgreSQL instance per environment, private IP, IAM auth, owned by `iac/projects/config-service/` (B2).
- A Cloud SQL for PostgreSQL instance per environment, built from the module below: public IP with no authorised networks, connectors only, IAM database users only, no passwords anywhere (B2).
- **An IAM-centric Cloud SQL module for the platform** (group M): built and proven in config-service under `iac/modules/cloud-sql-iam`, then published to `ilg-platform/terraform-modules` as `database/cloud-sql-iam`. Its job is to make the secure path the easy one: callers name service accounts, not users, and get a connection name and env back.
- A migration job pattern (Cloud Run Job inside the terragrunt apply) that a second service can lift into `terraform-modules` once one exists (B3).
- A backfill tool and a parity oracle that compare the two backends route by route (D1, D2).
- The Fuse MCP catalogue and the config-service Waypoint docs updated for the new persistence (F3).

## Verdict
**Go for dev.** Everything up to the dev cutover (D3) is additive behind `PERSISTENCE_BACKEND=mongo`, so the fleet sees no change. The prod cutover (E2) waits on the parity oracle green against prod data (E1) and an agreed write-freeze window (G2). Decommissioning Atlas (F2) waits on a week's clean soak (G3) and a proven restore of the final snapshot (G4).

> SUPERSEDED 2026-10-28 — Harry confirmed the motivation; see the next paragraph.
**Motivation, to confirm with Harry:** the drivers named so far are consolidation onto GCP and relational integrity for the business → storefront → connector chain. If Atlas cost is also a driver, say so here; it changes how long the overlap (both databases live) is allowed to run.

**Motivation (Harry, 2026-10-28): this is prep for Merak.** The [[Delivery Backends/Overview|Delivery Backends]] programme puts a second product (the Merak delivery portal) on the same config model, and the data is already lightly relational (business → storefront → connector, backends per business and type). Keeping that integrity in application code on Mongo gets harder to track with every Merak change, so the relationships move into the database. Atlas cost is not a stated driver, so the overlap is bounded by the soak (G3), not by spend. No Jira ticket: out-of-ticket, like Delivery Backends.

## Why this needs a programme
- **It is the fleet's config source of truth.** Every service reads config-service on a cache miss, and `config_revision` drives every cache refresh. A wrong response shape or a lost write reaches fapi, snap-adapter, sftp-connector, shopify-connector, dedupe-service and wms-gateway at once.
> SUPERSEDED 2026-10-28 — A0's inventory: 8 core services hold 14 collection injections, 6 core files hand-write pipelines, and one caller (the cascading business delete) uses a transaction. See `architecture.md#persistence-surface`.
- **The persistence layer isn't behind a seam today.** 11 core services inject `Collection<T>` directly, 6 sites hand-write aggregation pipelines, and a Mongo `ClientSession` is threaded through core methods for the cascading business delete. A Postgres implementation has nothing to plug into until that seam exists.
- **The infrastructure pattern doesn't exist in the fleet yet, and this is where it gets made.** The Cloud SQL module built here is meant for every team, so its DX matters as much as config-service's migration. config-service has no VPC, no service in Bifrost runs Cloud SQL, and nothing runs schema migrations automatically: apiky has no migrate step and sandbox runs them from a laptop. This programme sets the pattern.
- **Two one-way doors.** The prod flip after the first Postgres write, and the Atlas teardown.

## Strategy
1. **Seam first (A).** A repository interface per aggregate and a backend-neutral unit of work, with the Mongo implementation wrapping today's code. No behaviour change; the existing suites prove it.
> SUPERSEDED 2026-10-28 — no VPC; the instance comes from our module (M). See 2a.
2. **Infrastructure, dev then prod (B).** VPC and direct VPC egress, then the Cloud SQL instance with IAM auth and two service accounts, then the migration job wired into the apply with an empty baseline migration and `docs/migrations.md`.
2a. **Module, then infrastructure (M, B).** Bump config-service's google provider so `database_roles` exists (M0). Build the IAM-centric module locally (M1) and instantiate it for config-service (B2): IAM users for the app and migrator SAs, the migrator holding `cloudsqlsuperuser`, no password anywhere. Then the migration job (B3), whose first migration grants the app its role. Once config-service has run on it in prod (G6), publish the module (M2), repoint config-service at the published tag (M3, a no-op plan) and announce it (M4).
3. **Postgres behind a flag (C).** Drizzle schema, Postgres repositories proven by the same integration suite as Mongo, and the `PERSISTENCE_BACKEND` switch plus a `PERSISTENCE_READ_ONLY` freeze.
4. **Backfill and parity (D).** An idempotent Mongo → Postgres backfill and an oracle that diffs every route and every write's side effects, with Mongo as the expected side. Dev flips first and soaks.
5. **Prod cutover (E).** Rehearse against a no-traffic tagged revision, then flip under a short write freeze. Readers serve from cache throughout.
6. **Decommission (F).** Delete the Mongo code, export and restore-test the final Atlas snapshot, tear Atlas down, update the catalogue.

**The cutover mechanism** is one env var on the Cloud Run service, `PERSISTENCE_BACKEND`. Rollback is the same var set back to `mongo`. After the first prod write on Postgres, a rollback also needs those writes re-applied; audit-service's config-change log is the record of what they were.

**How migrations ship.** A `google_cloud_run_v2_job` on the service's own image runs `drizzle-orm`'s migrator under an advisory lock. A `terraform_data` keyed on the image name executes it with `--wait`, and the Cloud Run service depends on that, so the apply orders job → revision and a failed migration stops the apply with the old revision still serving. The `terraform-prod` approval therefore covers the migration too. Every migration is expand/contract: nothing is dropped that the previous revision still reads.

## Scar tissue
- **No passwords, anywhere.** IAM users through connectors only; the instance refuses anything else.
- **The module is ours.** It doesn't wrap or depend on SRE's `database/cloud-sql`; we build for the caller's DX.
- **Expand/contract, always.** Cloud Run overlaps revisions and a rollback never rolls the schema back.
- **The migration job runs the service's own image.** Never a separate build, never a laptop against prod.
- **`drizzle-kit` never enters the production image.** The runtime migrator is `drizzle-orm`'s.
- **The app SA owns no DDL.**
- **`metadata.version` never resets.** `X-Resource-Version` must not go backwards across the backfill.
- **Core never imports a driver type.**
- **Do not copy apiky's Cloud SQL wiring.** Public IP, a password in the connection string and `sslmode=disbale` are not the precedent.

## Next
> SUPERSEDED 2026-10-28 — A0 and A5 are merged.
**A0, the contract snapshot and persistence inventory.** Drive it with `waypoint-programme`. G5 (runner permissions for Cloud Run Jobs) can be checked in parallel, since it may need an admin outside the repo.

**M0 (google provider bump) and A1 (repository interfaces), in parallel.** M0 unblocks the module; A1 starts the seam. Drive both with `waypoint-programme`.
