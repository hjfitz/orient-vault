---
tags:
- waypoint
- selector2
title: selector2 — architecture
thesis: One pnpm workspace with a layered NestJS api (http to use-cases to core, adapters
  and repositories behind small interfaces) and a SvelteKit ui that only calls the
  api. Every query takes a TenantScope, both services are public at the Cloud Run
  layer so each route carries its own guard, and a carrier create is never retried
  once the proxy may have received it.
confidence: moderate
verified: '2026-11-12'
verified_sha: unknown
verified_paths:
- apps/selector2-api/src
- apps/selector2-api/openapi
- apps/selector2-api/drizzle
- apps/selector2-ui/src
- iac/projects
---
# selector2 — architecture

```orient-bluf
{ "v": 1, "bluf": "One pnpm workspace with a layered NestJS api (http to use-cases to core, adapters and repositories behind small interfaces) and a SvelteKit ui that only calls the api. Every query takes a TenantScope, both services are public at the Cloud Run layer so each route carries its own guard, and a carrier create is never retried once the proxy may have received it.", "confidence": "moderate", "action": "Add a new route only with a guard (ApiKeyGuard, BasicAuthGuard or a body check): nothing denies by default." }
```

## Guardrails
- [contract:G1] Every row carries `tenant_id` and every query goes through a `TenantScope` and `inScope`. There is no unscoped query method, and a child row points at its parent by `(parent_id, tenant_id)`. The only unscoped stores are the two sign-in lookups and the migration job's god account.
  — paths: apps/selector2-api/src/repositories, apps/selector2-api/src/models/tenant-scope.ts
- [policy:G2] Both Cloud Run services have `allUsers` as invoker, and nothing denies by default: each controller names its own guards. A new route needs `ApiKeyGuard` (REST), `BasicAuthGuard` plus `TenantScopeGuard` (admin) or the body credential check (SOAP), or it is open to the internet.
  — paths: apps/selector2-api/src/http/controllers, apps/selector2-api/src/http/middleware, iac/projects/selector2-api/iam.tf
- [contract:G3] SOAP credentials are the body element `AuthenticationDetails`, never a header. `UserID` is the account username and `UserPassword` is an API key, not the account password. `AuthConnDetails` is a C# parameter name and does not appear on the wire.
  — paths: apps/selector2-api/src/http/soap, docs/soap.md
- [technical:G4] A carrier create is never retried after the proxy may have received it (timeout, dropped connection, 429, 5xx), by the client or by a use-case. Such a booking keeps its reference in `booking`; a repeat within the stale limit is `in_progress`. The stale limit must exceed the longest carrier call.
  — paths: apps/selector2-api/src/adapters/carriers/carrier-http-client.ts, apps/selector2-api/src/use-cases/process-shipments.use-case.ts, apps/selector2-api/src/config/env/carrier-config.ts
- [policy:G5] Never log or put in an error message a request or response body, a label, an address, an API key or a credential. Log identifiers. Carrier failure messages are returned to the caller and never logged.
  — paths: apps/selector2-api/src/observability, apps/selector2-api/src/adapters/carriers, apps/selector2-ui/src/lib/server
- [technical:G6] The validation chain is pure: it takes a `ValidationContext` and never queries. It keeps CSS's codes and wording (`0002`, `0003`, `0030`) because SOAP and REST v1 echo them, and each rule has a slug that REST v2 returns.
  — paths: apps/selector2-api/src/core/validation, apps/selector2-api/src/core/shipments/outcomes.ts

## Structure
`apps/selector2-api/src` follows the org layer contract: `bootstrap` wires everything, `http` calls one use-case per route, `use-cases` hold what the service does, `core` has the rules with no framework or driver, and `adapters` and `repositories` hold the carrier client and Postgres access. Nest modules live only in `bootstrap/containers/`, and every injection is an explicit `@Inject(token)` from `models/tokens.ts` [1].

```orient-flow
{ "v": 1, "preset": "c4-container", "title": "Inbound request path in selector2-api",
  "nodes": [
    { "id": "soap", "label": "SOAP controller", "sub": "ClientShipService.asmx", "kind": "service" },
    { "id": "v1", "label": "REST v1 controller", "sub": "x-api-key", "kind": "service" },
    { "id": "v2", "label": "REST v2 controller", "sub": "x-api-key", "kind": "service" },
    { "id": "adm", "label": "Admin controllers", "sub": "basic auth + tenantId", "kind": "service" },
    { "id": "res", "label": "resolvePrincipal", "sub": "keys, argon2id, throttle", "kind": "service", "tone": "accent" },
    { "id": "uc", "label": "Shipment use-cases", "sub": "process, validate, delete, commit", "kind": "service" },
    { "id": "core", "label": "core", "sub": "validation chain, booking plan, outcomes", "kind": "service" },
    { "id": "db", "label": "Postgres", "sub": "repositories via TenantScope", "kind": "store" }
  ],
  "edges": [
    { "from": "soap", "to": "res", "label": "AuthenticationDetails" },
    { "from": "v1", "to": "res", "label": "x-api-key" },
    { "from": "v2", "to": "res", "label": "x-api-key" },
    { "from": "adm", "to": "res", "label": "Basic header" },
    { "from": "res", "to": "uc", "label": "Principal then TenantScope" },
    { "from": "uc", "to": "core", "label": "validate, plan" },
    { "from": "uc", "to": "db", "label": "claim, record" }
  ] }
```
SOAP, REST v1, REST v2 and the admin shipment routes all call the same use-cases and share the status mapping in `core/shipments/outcomes.ts`, so the transports cannot drift. REST v2 and `/admin/shipments` share one set of operation functions, so they answer byte for byte alike [2].

```orient-flow
{ "v": 1, "preset": "c4-container", "title": "Egress to a carrier proxy",
  "nodes": [
    { "id": "uc", "label": "processShipments", "sub": "claim, book, record", "kind": "service", "tone": "accent" },
    { "id": "reg", "label": "CarrierRegistry", "sub": "checkBookable first", "kind": "service" },
    { "id": "ad", "label": "Carrier adapter", "sub": "one per proxy, 12", "kind": "service" },
    { "id": "http", "label": "CarrierHttpClient", "sub": "ID token, timeout, retry rules", "kind": "service" },
    { "id": "mock", "label": "Mock proxy", "sub": "carrier-playground", "kind": "external" },
    { "id": "trace", "label": "carrier_call", "sub": "identifiers and timings only", "kind": "store" }
  ],
  "edges": [
    { "from": "uc", "to": "reg", "label": "BookingRequest" },
    { "from": "reg", "to": "ad", "label": "resolve by carrier" },
    { "from": "ad", "to": "http", "label": "proxy request" },
    { "from": "http", "to": "mock", "label": "x-api-key + X-Serverless-Authorization" },
    { "from": "http", "to": "trace", "label": "one row per attempt" }
  ] }
```
`CarrierAdapter` has one required operation, `create`; `cancel`, `commit` and `validate` are optional, because not every proxy has them. Each adapter classifies its own proxy's replies (a 500 is a refusal on BJS and InPost, and UPS and Amazon report failures inside a 200), so the client never classifies a response itself [3].

## Interfaces
| Surface | Auth | Contract |
| --- | --- | --- |
| `POST /ClientShipService.asmx` | body `AuthenticationDetails` (username, API key) | CSS's WSDL; eight operations; HTTP 200 with a status in the body |
| REST v1 (`/ProcessShipments` and four more) | `x-api-key` | `openapi/rest-v1.yaml`; selector-rest-proxy's 200/207/400 rule, read at runtime |
| REST v2 (`/v2/shipments`, `GET /v2/services`) | `x-api-key` | `openapi/rest-v2.yaml`; idempotent create by reference |
| `/admin/...` | HTTP basic, JSON-only POST | `openapi/admin.yaml`; accounts, API keys, the UI's shipment routes, CSV export |
| `GET /health/liveness`, `/health/readiness` | none | liveness is always 200; readiness is 503 until Postgres answers |

A `god` account acts on its own tenant for REST and SOAP. On the admin routes it names a tenant with `?tenantId=`, and no route gives it an all-tenants scope [4].

## Persistence
Postgres 17 on Cloud SQL, IAM logins only, with 12 tables and four migrations (`apps/selector2-api/drizzle/`). Migrations run as a Cloud Run job inside the Terraform apply, as the migrator service account; the app login (`app_rw`) cannot change the schema. A repeated `(tenant, reference)` is claimed with one `INSERT ... ON CONFLICT DO UPDATE ... RETURNING`, and a booked or committed holder is returned without calling the carrier. Labels are stored as `bytea` [5].

## Runtime
Two Cloud Run services on the platform's golden `node24-runtime` image (`selector2-api-dev`, `selector2-ui-dev`), min instances 0. The platform module exposes no max-instance cap, so the pool (default 2 connections) is the only bound on a 25-connection `db-f1-micro`. **ASSESSED:** Cloud Run probes only liveness, so a service that never reaches its database stays "ready" and returns 503 from `/health/readiness` [6].

The ui is reached by the browser directly and gates every route except `GET /health/liveness` through `hooks.server.ts`. It remembers a successful sign-in for 60 seconds, so a revoked account can still pass in the ui for up to a minute on an instance that has seen it [7]. Labels and the CSV export reach the browser only through the ui server, streamed under a type the ui chose (`no-store`, `nosniff`); a PDF label shows in an iframe without `sandbox`, because Chromium's PDF viewer refuses a sandboxed frame [7].

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "AGENTS.md@6442634" },
  { "id": 2, "kind": "code", "ref": "apps/selector2-api/src/core/shipments/outcomes.ts@6442634" },
  { "id": 3, "kind": "code", "ref": "docs/carrier-egress.md@6442634" },
  { "id": 4, "kind": "code", "ref": "apps/selector2-api/src/http/controllers/admin-shipments.controller.ts@6442634" },
  { "id": 5, "kind": "code", "ref": "docs/data-model.md@6442634" },
  { "id": 6, "kind": "code", "ref": "iac/projects/selector2-api/cloud-run.tf@6442634" },
  { "id": 7, "kind": "code", "ref": "docs/ui.md@ee122ca" }
] }
```
