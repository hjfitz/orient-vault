---
tags:
- waypoint
- audit-service
title: audit-service — architecture
verified_paths:
- code/internal
- code/cmd
- code/tools/auditschema
- iac/projects/audit-service
- .github/workflows
- code/dockerfile
- code/Makefile
- code/go.mod
- code/openapi.yaml
- CLAUDE.md
- README.md
- iac/env
- mise.toml
verified: '2026-10-27'
verified_sha: 8b86c70
thesis: A private Go service on Cloud Run takes OIDC-pushed AuditMessages into one
  idempotent MongoDB collection keyed by eventId, and reads them back only through
  system-scoped routes that admit an allow-list of Google identities.
confidence: high
---
# audit-service — architecture

```orient-bluf
{ "v": 1, "bluf": "A private Go service on Cloud Run takes OIDC-pushed AuditMessages into one idempotent MongoDB collection keyed by eventId, and reads them back only through system-scoped routes that admit an allow-list of Google identities.", "confidence": "high", "action": "Never add an index or query that does not lead with system, and never log a message payload: details can hold credentials." }
```

## Guardrails

- [contract:G1] Every Mongo index and every query leads with `system`; never add one that scans across systems.
  — paths: code/internal/repositories, code/internal/core/query
- [technical:G2] DogStatsD metrics must flush within the request. Cloud Run throttles CPU after the response, so the client's background flush never runs and metrics silently never arrive.
  — paths: code/internal/observability
- [policy:G3] Data is kept forever: no TTL index, no delete path. Atlas prod has backups, PIT and termination protection.
  — paths: code/internal/repositories, iac/projects/audit-service/mongo.tf
- [contract:G4] The Go envelope is generated from `@gfs-bifrost/audit`'s Zod (`make gen`); never hand-edit `internal/models/audit`, and the envelope must stay a plain `z.object` or codegen emits an empty file.
  — paths: code/internal/models/audit, code/tools/auditschema
- [operational:G5] Only a store failure returns non-2xx on ingest. Invalid or system-mismatched messages are acked (204) and counted; returning 5xx for them would only dead-letter poison.
  — paths: code/internal/core/ingest, code/internal/http/controllers/ingest.go
- [policy:G6] Never public, never log a payload. Callers are the push SA and `api_readers`; `details` snapshots can contain credentials.
  — paths: iac/projects/audit-service/iam.tf, code/internal/http

## Structure

The service is one chi router over thin controllers, two small use cases and one Mongo repository. The ingest rules and the full event path are in [[audit-event-flow]]; this page covers the shape around them.

```orient-flow
{ "v": 1, "title": "Layers and callers",
  "nodes": [
    { "id": "push", "label": "Pub/Sub push SA", "sub": "POST /events/v1", "kind": "external", "ev": [2] },
    { "id": "rd", "label": "Allow-listed readers", "sub": "GET /api/v1/systems", "kind": "external", "ev": [2] },
    { "id": "mw", "label": "RequireCaller", "sub": "ID token, email allow-list", "kind": "step", "ev": [3, 4] },
    { "id": "ctl", "label": "Controllers", "sub": "ingest, read, health", "kind": "step", "ev": [2] },
    { "id": "ing", "label": "core/ingest", "sub": "one message, one Outcome", "kind": "service", "service": "audit-service", "tone": "accent", "ev": [5] },
    { "id": "qry", "label": "core/query", "sub": "filter, cursor, limits", "kind": "step", "ev": [6] },
    { "id": "repo", "label": "repositories", "sub": "events, read, legacy", "kind": "step", "ev": [7, 8] },
    { "id": "db", "label": "MongoDB Atlas", "sub": "events collection", "kind": "store", "ev": [7] }
  ],
  "edges": [
    { "from": "push", "to": "mw" },
    { "from": "rd", "to": "mw" },
    { "from": "mw", "to": "ctl", "label": "admitted" },
    { "from": "ctl", "to": "ing" },
    { "from": "ctl", "to": "qry" },
    { "from": "ing", "to": "repo", "label": "insert" },
    { "from": "qry", "to": "repo", "label": "find, count" },
    { "from": "repo", "to": "db" }
  ] }
```

```
code/cmd/api            HTTP server
code/cmd/import-legacy  fuse-ui audit_log → AuditMessage importer (human-run)
code/internal/
  config/               env, validated once (MONGODB_*, PUSH_INVOKER_EMAIL, READ_CALLERS, …)
  bootstrap/            wiring + routes.go
  http/                 controllers, middleware (Recover, Correlation, Logger, RequireCaller), respond
  core/ingest           one pushed message → one stored event, with an Outcome
  core/query            Filter, cursor encoding, limits (25 default, 100 max, total capped at 1000)
  core/legacy           legacy row → AuditMessage mapping and the import/verify walk
  repositories/         Mongo: events (insert, indexes), read, legacy source
  adapters/idtoken      Google ID token verification
  models/audit          generated AuditMessageJson
  observability/        slog, DogStatsD, correlation context
code/tools/auditschema  Node: imports @gfs-bifrost/audit, writes JSON Schema for go-jsonschema
code/openapi.yaml       read API spec
iac/projects/audit-service  Cloud Run, IAM, Atlas, subscriptions; env in iac/env/*.tfvars
```

**Stack:** Go 1.26.9, chi v5, mongo-driver v2, datadog-go v5, `google.golang.org/api` for ID-token validation. The image is a static, CGO-off binary on distroless `nonroot` [9][10].

## Interfaces

### Inbound

| Route | Caller check | Behaviour |
| --- | --- | --- |
| `POST /events/v1/audit/{system}` | `PUSH_INVOKER_EMAIL` only | Pub/Sub push. 204 for every outcome but a store failure, which is 500 [2][11] |
| `GET /api/v1/systems/{system}/events` | `READ_CALLERS` | Filters `tenantId`, `targetType`, `targetId`, `actorId`, `kind`, `action`, `from`, `to`. Cursor paging on `(occurredAt, _id)`, newest first. A bad `limit`, time or cursor is a 400 [2][6] |
| `GET /api/v1/systems/{system}/events/{id}` | `READ_CALLERS` | One event, 404 when absent in that system |
| `GET /api/v1/systems/{system}/filter-options` | `READ_CALLERS` | Distinct actors, and tenants when `tenantId` is not given |
| `GET /api/v1/health` | none in the app | Returns `{status: ok}`; Cloud Run IAM still gates it |

`cmd/import-legacy -source-uri -target-uri [-dry-run|-verify]` copies fuse-ui's `audit_log` rows through the same insert. It prints counts and error samples, never payloads. `code/openapi.yaml` documents the read routes [12].

### Outbound and Pub/Sub

- MongoDB Atlas, database `audit-service`, collection `events`, `_id = eventId`. Flex cluster in dev. In prod, an M10 replica set that autoscales to M20, with backups, point-in-time recovery and termination protection [20].
- Topics belong to bifrost-pubsub, and this stack reads their ids from its remote state. Subscriptions belong here [13].
- `audit-service.<env>.<system>.v1.sub` is a push subscription with an OIDC token (audience is the service URL), a 30 s ack deadline, 10 to 600 s backoff, and a dead letter after 5 attempts [14].
- `audit-service.<env>.<system>.v1.dlt.sub` is a pull hold with a 7-day retention for manual re-publish. Neither subscription expires [14].

## Authentication and exposure

Two layers guard each route. Cloud Run IAM is the coarse gate, and `RequireCaller` pins each route group to the identities that group is for [3].

- **Cloud Run IAM.** `run.invoker` goes to the push service account and each address in `api_readers`. No `allUsers` member exists, and a comment in `iam.tf` says there never will be. Ingress is `INGRESS_TRAFFIC_ALL`, so the `run.app` URL is reachable from the internet but answers only a caller with a granted identity [1][11].
- **App check.** `idtoken.Validate` checks signature, issuer and expiry. It skips the audience, because Cloud Run already rejected a token minted for another service. A token needs a verified email. Emails compare case-insensitively against the allow-list. Missing or invalid is 401 and not listed is 403 [3][4].
- **Reader list.** `READ_CALLERS` is the joined `api_readers`. An empty list admits no one. Dev lists `fuse-ui-dev` and prod lists `fuse-ui-prod` [1][15].

**ASSESSED** No unauthenticated route is exposed publicly. Source: [1][3][4]. A project-level or organisation-level IAM binding outside this repo could still widen access, and this repo cannot show it.

## Persistence

`events` holds the raw message as relaxed Extended JSON, so open `details` and fields from a newer producer survive. `eventId` becomes `_id`, `occurredAt` becomes a date, and `receivedAt` is stamped on insert. Reads rename `_id` back to `eventId` and flatten BSON types to plain JSON [7][8].

Six indexes exist, and every one leads with `system`: `occurredAt` plus `_id`, then `tenantId`, `target.type` plus `target.id`, `actor.id`, `kind` and `action`, each followed by `occurredAt`. Boot creates them and fails if Mongo is unreachable [7][16].

The list counts with a limit of 1001, so `total` stops at 1000 and `totalCapped` says so. Query values are typed strings, so a filter cannot inject a Mongo operator [6][8].

## Secrets and leakage

- **CONFIRMED** The code never logs a message payload. Ingest logs the `eventId`, Pub/Sub `messageId`, outcome and reason, and the access log records method, path, status and duration. The invalid-message reason is Go's JSON error text, and a system mismatch logs the two system names [5][17][24].
- **CONFIRMED** The service stores `details` exactly as sent and returns it unmasked from the read routes. It does no masking. A reader must mask secrets before anything reaches a browser.
- **ASSESSED** A producer snapshot that carries a credential therefore sits in Atlas and in the Pub/Sub topic and dead-letter hold for up to 7 days, and any allow-listed reader can fetch it. Source: [14][8].
- **CONFIRMED** `MONGODB_CONNECTION_STRING`, with the Atlas password, and both Datadog API keys are plain Cloud Run env values. They also sit in Terraform state. No Secret Manager is used [1][20].
- **UNKNOWN** The Atlas IP access list. It is configured at project level, outside this stack.

## Observability

`slog` JSON goes to stdout only. The image is built on ilg-platform's `go-runtime` golden image, whose entrypoint is Datadog's `datadog-init`: the agent runs in the app container, reads stdout directly and dual-ships to the GFS and ILG accounts (`DD_ADDITIONAL_ENDPOINTS` / `DD_LOGS_CONFIG_ADDITIONAL_ENDPOINTS`). There is no sidecar. Logs carry `source:go` and `dd.datadog_init_version`. `x-request-id` is the correlation id, minted when absent and echoed back [17][1].

The metric is `fuse.audit.ingest`, tagged `system`, `outcome` and, when present, `kind`. The client flushes after every increment, per G2, to the in-container agent on `localhost:8125`. `datadog-go` also adds `env`/`service`/`version` tags from `DD_ENV`/`DD_SERVICE`/`DD_VERSION` on the container [18]. **ASSESSED** The monitors live in `gfs-bifrost/observability`, per [[operations]]; this repo does not define them.

## Runtime and deploy

- **Cloud Run v2.** One container. It declares no CPU or memory limit, so it runs on Cloud Run defaults, shared with the in-container Datadog agent. The Dockerfile sets `CMD` only (an `ENTRYPOINT` would bypass the agent) and restates `USER nonroot:nonroot` for Semgrep. Scaling is 0 or 1 minimum (prod sets 1) and 5 maximum [1].
- **Server.** `ReadHeaderTimeout` is 10 s. Shutdown drains for 8 s, under Cloud Run's 10 s window. Config validation reports every bad variable at once [16][19].
- **Deploy.** A push to `main` builds and applies dev with `-auto-approve`, builds the prod image, plans prod, and applies prod behind the `terraform-prod` environment. `manual-deploy.yaml` deploys any ref to dev only [21].
- **CI.** `code-quality.yaml` runs gofmt, build, vet, race tests and golangci-lint, plus a job that runs the repository tests on a real Mongo. It runs on pull requests and nightly. `gen-check.yaml` regenerates the envelope on pull requests, `tf-plan.yaml` posts a dev plan, and `secops.yaml` runs secret, Go dependency, code, container and Terraform scans [21].
- **Codegen.** `make gen` runs `tools/auditschema` to turn the Zod envelope into JSON Schema, then `go-jsonschema` v0.24.1 writes `gen_audit_message.go`. `make gen-check` fails when the committed file is stale [22][23].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "iac/projects/audit-service/cloud-run.tf@ddefd56" },
  { "id": 2, "kind": "code", "ref": "code/internal/bootstrap/routes.go@ddefd56" },
  { "id": 3, "kind": "code", "ref": "code/internal/http/middleware/caller.go@ddefd56" },
  { "id": 4, "kind": "code", "ref": "code/internal/adapters/idtoken/verifier.go@ddefd56" },
  { "id": 5, "kind": "code", "ref": "code/internal/core/ingest/ingest.go@ddefd56" },
  { "id": 6, "kind": "code", "ref": "code/internal/http/controllers/read.go@ddefd56" },
  { "id": 7, "kind": "code", "ref": "code/internal/repositories/events.go@ddefd56" },
  { "id": 8, "kind": "code", "ref": "code/internal/repositories/read.go@ddefd56" },
  { "id": 9, "kind": "code", "ref": "code/go.mod@ddefd56" },
  { "id": 10, "kind": "code", "ref": "code/dockerfile@ddefd56" },
  { "id": 11, "kind": "code", "ref": "iac/projects/audit-service/iam.tf@ddefd56" },
  { "id": 12, "kind": "code", "ref": "code/openapi.yaml@ddefd56" },
  { "id": 13, "kind": "code", "ref": "iac/projects/audit-service/remotes.tf@ddefd56" },
  { "id": 14, "kind": "code", "ref": "iac/projects/audit-service/pubsub.tf@ddefd56" },
  { "id": 15, "kind": "code", "ref": "iac/env/prod.tfvars@ddefd56" },
  { "id": 16, "kind": "code", "ref": "code/cmd/api/main.go@ddefd56" },
  { "id": 17, "kind": "code", "ref": "code/internal/http/controllers/ingest.go@ddefd56" },
  { "id": 18, "kind": "code", "ref": "code/internal/observability/metrics.go@ddefd56" },
  { "id": 19, "kind": "code", "ref": "code/internal/config/config.go@ddefd56" },
  { "id": 20, "kind": "code", "ref": "iac/projects/audit-service/mongo.tf@ddefd56" },
  { "id": 21, "kind": "code", "ref": ".github/workflows/deploy.yaml@ddefd56" },
  { "id": 22, "kind": "code", "ref": "code/Makefile@ddefd56" },
  { "id": 23, "kind": "code", "ref": "code/tools/auditschema/src/index.ts@ddefd56" },
  { "id": 24, "kind": "code", "ref": "code/internal/http/middleware/middleware.go@ddefd56" }
] }
```
