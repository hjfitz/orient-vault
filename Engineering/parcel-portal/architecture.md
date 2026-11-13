---
tags:
- waypoint
- parcel-portal
title: parcel-portal — architecture
thesis: One Go module with five binaries (svc and the customer-API gateway on Cloud
  Run, sftp on a MIG, a canary job, a dev-only debug MCP) plus a Next.js UI and two
  browser packages. svc is contract-first and layered (http → core → adapters/repositories),
  every customer table is tenant-scoped through the request context, and dispatch
  is at-most-once per order.
confidence: high
verified: '2026-10-29'
verified_sha: 696cbd4
verified_paths:
- apps/svc/internal
- apps/svc/cmd
- apps/svc/openapi.yaml
- apps/ui/src
- packages/label-print/src
- iac/projects
---
# parcel-portal — architecture

```orient-bluf
{ "v": 1, "bluf": "One Go module with five binaries (svc and the customer-API gateway on Cloud Run, sftp on a MIG, a canary job, a dev-only debug MCP) plus a Next.js UI and two browser packages. svc is contract-first and layered (http → core → adapters/repositories), every customer table is tenant-scoped through the request context, and dispatch is at-most-once per order.", "confidence": "high", "action": "Never add a query that doesn't name tenant_id outside the four exempt files (auth.sql, tenant.sql, sftp_auth.sql, api_key_auth.sql); the static test will fail it, and it should." }
```

## Guardrails
- [contract:G1] Every customer-data query is tenant-scoped from the request context, never from a parameter. Only `queries/auth.sql`, `tenant.sql`, `sftp_auth.sql` (the SFTP users snapshot) and `api_key_auth.sql` are exempt, and a static test enforces it. The context's tenant is the user's own, an admin route's `{tenantId}`, or the customer a `gfs_admin` acts for (`X-Acting-Tenant`, session routes only) [6].
  — paths: apps/svc/internal/repositories/postgres, apps/svc/internal/http/middleware
- [technical:G2] Dispatch is at-most-once: claim with a lease, reconcile with `DailyShipQuery`, then book. Never retry `ProcessShipment` blindly or adopt a lost booking; void it.
  — paths: apps/svc/internal/core/dispatch
- [contract:G3] `openapi.yaml` (the ui's contract) and `public-openapi.yaml` (the customer API, versioned separately) are the contracts. Edit the spec first, bump its `info.version`, run `make gen`; never hand-edit `internal/http/api`, `internal/http/publicapi`, `client/` or `repositories/postgres/db`.
  — paths: apps/svc/openapi.yaml, apps/svc/public-openapi.yaml, apps/svc/internal/http/api, apps/svc/internal/http/publicapi
- [operational:G4] Never call CommitShipments, PrintManifest or ProcessCarrierDispatch against the shared Selector sandbox; it closes out everyone's TEST account. Tests use the fake Selector.
  — paths: apps/svc/internal/adapters/selector, apps/svc/internal/core/shipments
- [operational:G5] Never regenerate or destroy the SFTP host keys (customers pin their fingerprints) or the carrier key `svc-parcel-carrier-key` (it seals every stored carrier password). Both carry `prevent_destroy`.
  — paths: iac/projects/parcel-portal-sftp, iac/projects/parcel-portal-svc/secrets.tf
- [technical:G6] Nothing about an order is defaulted: dims, weight and a mapped carrier service must be present before dispatch.
  — paths: apps/svc/internal/core/imports, apps/svc/internal/core/dispatch

## Structure
```orient-flow
{ "v": 1, "title": "Inside svc",
  "nodes": [
    { "id": "http", "label": "http", "sub": "generated api, controllers, middleware, respond", "kind": "service" },
    { "id": "core", "label": "core/<capability>", "sub": "auth, tenants, users, mapping, imports, orders, dispatch, shipments, printers, exports, carriers", "kind": "service", "tone": "accent" },
    { "id": "adapters", "label": "adapters", "sub": "selector, gcs, secretmanager, pdf, password, pushauth", "kind": "service" },
    { "id": "repos", "label": "repositories", "sub": "postgres (sqlc + tern), memory", "kind": "store" },
    { "id": "boot", "label": "bootstrap", "sub": "the only wiring", "kind": "service" }
  ],
  "edges": [
    { "from": "http", "to": "core", "label": "one use-case per handler" },
    { "from": "core", "to": "adapters", "label": "consumer-declared interfaces" },
    { "from": "core", "to": "repos" },
    { "from": "boot", "to": "http", "style": "dashed" }
  ] }
```
- `apps/svc/cmd/svc` is the API, `cmd/sftp` the SFTP host and `cmd/canary` the SFTP canary job, all in one Go module [1].
- `apps/ui` is Next.js on `@ilg-platform/ui-toolkit`. Server components and actions call svc from the server with the session as a bearer token and a Google ID token for Cloud Run; the browser never calls svc [2].
- `packages/label-print` (`@ilg-merak/label-print`, private) rasterises PDF labels to ZPL `^GFA` or EPL `GW` and sends them over WebUSB. The ui installs it from `file:` as TypeScript source, so **the ui image builds from the repo root** [2][3].

## Interfaces in
| Surface | Who | Notes |
| --- | --- | --- |
| HTTP (svc) | ui's runtime SA only | `security`: public, `session`, `adminSession` (`gfs_admin`) per operation; `Authorize` middleware enforces it [1] |
| `POST /events/inbound-files` | `svc-parcel-<env>-push` SA | GCS `OBJECT_FINALIZE` via Pub/Sub push; 10 attempts then dead letter [1] |
| SFTP :22 | the customer's key | single user, public-key only, static IP, writes to GCS on close [1] |
| Browser | customer and GFS staff | sign-in sets the `pp_session` cookie (HTTP-only, 12h) [2] |

## Interfaces out
| Target | How |
| --- | --- |
| Selector | SOAP `ClientShipService.asmx`: ValidateShipment, ProcessShipment, DeleteShipments, CommitShipments, DailyShipQuery [1] |
| Cloud SQL Postgres 17 | IAM auth only; migrations run at startup under tern [1] |
| GCS | inbound bucket (read by generation), labels bucket (`<tenant>/labels/<shipment>/<parcel>`) [1] |
| Secret Manager | the carrier key, one pinned version read once at startup (passwords themselves are encrypted on `carrier_connection`); bootstrap admin password via secret env [1] |

## Persistence
Migrations `001`–`007` in `apps/svc/internal/repositories/postgres/migrations`. Every table but `tenant` carries `tenant_id`, and children reference parents by `(id, tenant_id)`, so no row can point into another tenant. Main tables: `app_user`, `session`, `import_file`, `import_mapping`, `orders` (+ `order_line`, `parcel`, `parcel_item`), `carrier_connection`, `dispatch_attempt`, `shipment` (+ `shipment_parcel`), `packaging_preset`, `bench_printer` [1].

## Runtime
- `us-central1`, projects `ilg-merak-dev-b5e3` and `ilg-merak-prod-1be0`. Cloud Run services `svc-parcel-<env>` and `ui-parcel-<env>` on the ilg-platform golden images and `terraform-modules` `compute/cloud-run` [4].
- The SFTP host runs on a MIG behind a TCP load balancer with a static IP; its health check is the container's HTTP `/healthz` on 8080 [4].
- Each app deploys from `<app>-on-push.yaml`: dev automatically, prod after the `terraform-prod` approval [4].

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "apps/svc/README.md@696cbd4" },
  { "id": 2, "kind": "code", "ref": "apps/ui/README.md@696cbd4" },
  { "id": 3, "kind": "code", "ref": "apps/ui/next.config.ts@696cbd4" },
  { "id": 4, "kind": "code", "ref": "iac/projects@696cbd4" }
] }
```
