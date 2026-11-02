---
tags: [explain]
date: 2026-10-28
thesis: "config-service uses Drizzle, not Prisma, because its data is mostly JSON typed by @gfs-bifrost/types and Drizzle keeps migration tooling out of the production image; migrations run as a Cloud Run Job inside the Terraform apply."
confidence: high
---
# Drizzle over Prisma for config-service's move to Cloud SQL

```orient-bluf
{ "v": 1, "bluf": "config-service uses Drizzle, not Prisma, because its data is mostly JSON typed by @gfs-bifrost/types and Drizzle keeps migration tooling out of the production image; migrations run as a Cloud Run Job inside the Terraform apply.", "confidence": "high", "action": "Wrap the Drizzle migrator in a Postgres advisory lock, because Drizzle does not take one and Prisma does." }
```

## Situation
- **CONFIRMED** config-service is moving from MongoDB Atlas to Cloud SQL Postgres, as prep for Merak. Harry chose Drizzle on 2026-10-28 [1].
- **CONFIRMED** Both tools already exist in the estate. apiky runs Prisma 7.8 with `@prisma/adapter-pg` [2]. sandbox runs `drizzle-orm` 0.45 and `drizzle-kit` 0.31 [3].

## Assessment

### Why Drizzle fits this data
- **ASSESSED** Most of config-service's volume is JSON: connector config, mappings, dictionaries, the EDI envelope. Only business → storefront → connector is relational. Its types already live in `@gfs-bifrost/types`.
- **CONFIRMED** Drizzle declares a `jsonb` column with `.$type<T>()`, so `@gfs-bifrost/types` stays the one definition. It also declares generated columns (`generatedAlwaysAs`) and partial indexes (`.where()`) in the schema [8].
- **ASSESSED** Prisma would model the relational spine in `schema.prisma` and type each JSON column as `JsonValue`. Every read would then need a cast or a Zod parse.

### Why the migration tooling matters
- **CONFIRMED** Drizzle's runtime migrator ships in `drizzle-orm`. sandbox's runner imports it directly, so `drizzle-kit` stays a dev dependency [3][4].
- **ASSESSED** `prisma migrate deploy` needs the `prisma` CLI where migrations run. apiky keeps it in devDependencies and runs no migrate step [2]. Our job runs on the service image, so Prisma would put the CLI in the production tree. `audit-ci --prod` and the container scan both read that tree [9].

### What Prisma does better
- **CONFIRMED** Prisma's migrate engine takes `pg_advisory_lock` before running [6]. Drizzle's migrator runs the migrations in one transaction and takes no advisory lock [5].
- **CONFIRMED** Prisma supports partial indexes behind its `partialIndexes` preview flag [7]. That corrects an earlier claim in the programme discussion that it needed hand-written SQL.
- **ASSESSED** Prisma is the estate's existing ORM (apiky), and Drizzle is pre-1.0. Pin exact versions and read every generated SQL file.

### How migrations run
- **CONFIRMED** config-service deploys with one terragrunt apply per environment [10]. The migration runs inside it.

```orient-flow
{ "v": 1, "title": "Migrations inside the apply",
  "nodes": [
    { "id": "pr", "label": "PR", "sub": "schema + generated SQL", "kind": "step" },
    { "id": "apply", "label": "terragrunt apply", "sub": "prod gate", "kind": "step", "ev": [10] },
    { "id": "job", "label": "Migration job", "sub": "service image, migrator SA", "kind": "step", "service": "config-service", "tone": "accent" },
    { "id": "db", "label": "Cloud SQL", "sub": "IAM users only", "kind": "store" },
    { "id": "svc", "label": "New revision", "sub": "rolls after the job", "kind": "service", "service": "config-service" }
  ],
  "edges": [
    { "from": "pr", "to": "apply", "label": "merge" },
    { "from": "apply", "to": "job", "label": "execute --wait" },
    { "from": "job", "to": "db", "label": "advisory lock, migrate" },
    { "from": "job", "to": "svc", "label": "only on success" }
  ] }
```

- **ASSESSED** A failed migration stops the apply, so the old revision keeps serving. The prod gate approval therefore covers the migration.
- **CONFIRMED** Every migration is expand/contract. Cloud Run overlaps revisions, and a rollback redeploys the old image without rolling the schema back [1].

## Open items
| Item | Owner | By |
|---|---|---|
| Advisory lock around the Drizzle migrator, in `docs/migrations.md` (B3) | Harry / programme | B3 |
| Exact Drizzle pins, plus a PR check that schema and migrations agree (B4) | Harry / programme | B4 |

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "doc", "ref": "Bifrost/Config Service Cloud SQL/Migration State.md", "note": "Decision log and Scar tissue, 2026-10-28" },
  { "id": 2, "kind": "code", "ref": "api/package.json@86c63dc", "note": "apiky: prisma, @prisma/client, @prisma/adapter-pg ^7.8.0; prisma in devDependencies" },
  { "id": 3, "kind": "code", "ref": "code/package.json@70ae9c9", "note": "sandbox: drizzle-orm ^0.45.2, drizzle-kit ^0.31.10 (dev)" },
  { "id": 4, "kind": "code", "ref": "code/scripts/run-migrations.cjs@70ae9c9", "note": "sandbox: runtime migrator from drizzle-orm/postgres-js/migrator" },
  { "id": 5, "kind": "url", "ref": "https://github.com/drizzle-team/drizzle-orm/blob/eab8bed/drizzle-orm/src/pg-core/dialect.ts#L73-L100", "note": "migrate(): creates __drizzle_migrations, runs in session.transaction; no advisory lock" },
  { "id": 6, "kind": "url", "ref": "https://github.com/prisma/prisma-engines/blob/d1b3f37/schema-engine/connectors/sql-schema-connector/src/flavour/postgres.rs#L377", "note": "SELECT pg_advisory_lock(72707369)" },
  { "id": 7, "kind": "url", "ref": "https://github.com/prisma/prisma-engines/blob/d1b3f37/psl/psl-core/src/common/preview_features.rs#L159-L161", "note": "PartialIndexes in the active preview features" },
  { "id": 8, "kind": "url", "ref": "https://github.com/drizzle-team/drizzle-orm/blob/eab8bed/drizzle-orm/src/pg-core/columns/common.ts#L86", "note": "generatedAlwaysAs; partial index .where() in pg-core/indexes.ts" },
  { "id": 9, "kind": "code", "ref": ".github/workflows/secops.yaml@2465c74", "note": "config-service: secops-dependency-audit and secops-image-scan" },
  { "id": 10, "kind": "code", "ref": ".github/workflows/on-push.yaml@2465c74", "note": "config-service: one terragrunt apply per environment" }
] }
```
