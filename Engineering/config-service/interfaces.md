---
tags:
- waypoint
- config-service
verified: '2026-10-09'
verified_sha: 6f0b36b
verified_paths:
- code/src/http/api/v1
- code/openapi.yaml
- code/src/core/storefront/constants.ts
- code/src/core/business-information/constants.ts
title: config-service — interfaces
---
# config-service — interfaces

Full HTTP surface, grouped by resource. All under `/api/v1` unless noted. Auth:
`x-api-key` header when `AUTH_ENABLED && AUTH_API_KEY` are both set; otherwise open.

> SUPERSEDED 2026-10-05 — there is no `/api/v1/docs*` wildcard. The allowlist holds exact paths (`/api/v1/docs`,
> `/api/v1/docs-json`); Swagger's asset files are open only because they are mounted before auth. Any other path
> under `/api/v1/docs/` (e.g. the old `/api/v1/docs/openapi.yaml`) returns 401. See [[architecture]].

`/health`, `/api/v1/docs*`, and `POST /events/customer-creation` are always open.

## Business / storefront / backend

| Base | Routes |
| ---- | ------ |
| `/business` | `GET` (list); `GET/PUT/DELETE :businessId`; `POST :businessId` (create under caller-supplied id) |
| `/business/:businessId/storefront` | `GET` (list); `POST` (create) |
| `/business/:businessId/backend` | `GET/POST/PATCH/DELETE` (SnapFulfil backend config) |
| `/backend` | `GET` (list all) |
| `/backend/:businessId` | `GET/POST/PUT/DELETE` |

## Storefronts / connectors / mappings

| Base | Routes |
| ---- | ------ |
| `/storefronts/:storefrontId` | `GET/PATCH/DELETE` |
| `/storefronts/:storefrontId/connectors` | `GET` (list); `POST` (create) |
| `/storefronts/:storefrontId/connectors/:connectorId` | `GET/PATCH/DELETE` |
| `/storefronts/:storefrontId/connectors/:connectorId/mappings/:useCase` | `GET/POST/PUT/DELETE` — `:useCase` is legacy naming, see [[known-context#legacy-usecase]] |
| `/storefronts/:storefrontId/connectors/:connectorId/credentials/cycle` | `POST` — rate-limited by `CREDENTIAL_CYCLE_LOCKOUT_SECONDS` |
| `/connectors` | `GET` (list, **read-only** global lookup, joins storefront → businessId) |
| `/connectors/:connectorId` | `GET` |

`confirmationsEnabled` (boolean) is writable on the connector `POST` (create,
defaults `false`) and `PATCH` (update — no default, omit to leave the stored
value untouched) request bodies, and is returned per connector by
`GET /storefronts/:storefrontId` and by the connector list on `GET /business` and
`GET /business/:businessId`. Each of those connector refs also carries `useCases`: the
list of use cases whose per-use-case key is set on the connector, derived in the Mongo
projection (`useCasesProjection`, `core/storefront/constants.ts`) — connector documents
store no `useCases` array, only the per-use-case mapping keys.

The backend routes no longer return a business-level `confirmations` flag (the
per-connector toggle replaced it); `broadcastConfirmations` is still returned. A stored
document may still carry the old field, it is just not served.

## Per-business config resources

| Base | Routes |
| ---- | ------ |
| `/business/:businessId/warehouses/routing` | `GET/POST/PUT/DELETE` — lives on `business_information`, no dedicated collection |
| `/business/:businessId/skus/blacklist` | `GET/POST/PUT/DELETE` — same, no dedicated collection |
| `/business/:businessId/ddp/rules` | `GET/POST/PUT/DELETE` — persisted on `ddp_config` |
| `/shipment_methods/:businessId` | `GET/POST/PUT/DELETE` — note the snake_case path segment |

## Docs

| Route | Notes |
| ----- | ----- |
| `GET /docs` | Swagger UI over the Nest-generated document |
| `GET /docs-json` | The generated OpenAPI document (JSON); error responses carry the problem+json envelope |

## Outside `/api` — unprefixed

| Route | Trigger | Notes |
| ----- | ------- | ----- |
| `GET /health` | Cloud Run startup probe | includes Mongo status |
| `POST /events/customer-creation` | Pub/Sub push (`customer_creation` topic) | **misnamed** — actually the SFTP-provisioning auth-status callback; see [[architecture]]. Bad payloads are 204-dropped, not retried. |

## Known surface drift

> SUPERSEDED 2026-10-05 — the file no longer reaches fuse-ui. fuse-ui's `gen-config-service-client` fetches
> `https://config.fuse.freightops.dev/api/v1/docs/openapi.yaml`, which returns 401, so a yaml edit changes nothing
> until fuse-ui is repointed at `/api/v1/docs-json` ([[regenerate-the-config-service-client-from-the-ge]]). fuse-ui's
> checked-in client is frozen at its last generation from the yaml.

- The hand-written `code/openapi.yaml` (~106 KB) is **no longer served**: the
  `/docs/openapi.yaml` route and the Scalar page are gone. It is still the input to
  fuse-ui's generated client, so connector-level fields are still edited there too.
- It still documents `/api/v1/default_mappings`, which **no longer exists** — verify
  routes against `http/api/v1/**/*.controller.ts`, not either spec.
- The drift is wider than `default_mappings`: the yaml documents 8 operations that 404
  (`GET/POST/PUT /default_mappings`, `GET/POST/PUT/DELETE /ingress/{businessId}`,
  `GET /connectors/{connectorId}/mappings`) and omits the real `POST /events/customer-creation`
  (checked against staging 2026-09-17).
- The two documents share no schema names (96 hand-written schemas vs 31 generated `*Dto`
  components, with nested types inlined). Moving a consumer from one to the other means
  re-deriving its types, not renaming them.
- The generated document is built from the controllers' Zod-derived DTOs, so a field
  missing from the Zod schemas is missing from it; `openapi.yaml` is a separate file
  with no codegen link and can disagree in either direction.
