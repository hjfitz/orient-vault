---
tags:
- waypoint
- selector-rest-proxy
title: selector-rest-proxy — architecture
thesis: 'One Express app: openapi-backend validates the body and resolves x-api-key
  through ApiKy, then a per-operation handler builds a SOAP client for the tenant''s
  Selector WSDL, calls it once, and maps the per-shipment results to 200, 207 or 400.'
confidence: high
verified_paths:
- src/app.ts
- src/controllers
- src/handlers
- src/selector.ts
- src/retrier.ts
- src/exceptions
- src/middleware
- src/observability
- src/schemas/openapi.yaml
- Dockerfile
- .github/workflows
- iac
- .env.production
verified: '2026-10-27'
verified_sha: 05c2bea
---
# selector-rest-proxy — architecture

```orient-bluf
{ "v": 1, "bluf": "One Express app: openapi-backend validates the body and resolves x-api-key through ApiKy, then a per-operation handler builds a SOAP client for the tenant's Selector WSDL, calls it once, and maps the per-shipment results to 200, 207 or 400.", "confidence": "high", "action": "A master merge auto-applies to prod; never approve the terraform-destroy job that waits on every run." }
```

## Guardrails

- [operational:G1] A push to `master` builds and runs `terraform apply -auto-approve` against prod, with no approval gate. The `terraform-destroy-prod` job waits for approval on every run; approving it tears prod down.
  — paths: .github/workflows, iac
- [contract:G2] `openapi.yaml` is the runtime validator, not documentation. Changing a schema changes what tenants' live requests are accepted or rejected.
  — paths: src/schemas/openapi.yaml
- [contract:G3] The 200 / 207 / 400 mapping in `handleResponse` is what tenant integrations branch on. A 207 still returns the full Selector body, and a 400 replaces it with a problem+json list.
  — paths: src/handlers/selector/util.ts
- [technical:G4] A request with no ApiKy profile (static key, or auth off) falls back to the env WSDL and credentials, which are the Selector sandbox with user `TEST` in prod too. A missing `upstream` on a real profile silently does the same.
  — paths: src/selector.ts, src/handlers/auth, .env.production
- [policy:G5] The access log writes full request and response bodies to Datadog, including recipient names and addresses and label data.
  — paths: src/middleware/logger.middleware.ts

## Request path

```orient-flow
{ "v": 1, "title": "One operation request",
  "nodes": [
    { "id": "mw", "label": "middleware", "sub": "requestId (cls), container-id echo, access log", "kind": "step", "ev": [1] },
    { "id": "oab", "label": "openapi-backend", "sub": "route by operationId, AJV body validation", "kind": "step", "ev": [2] },
    { "id": "sec", "label": "API_KEY handler", "sub": "BASICAUTH_KEY or ApiKy lookup", "kind": "step", "ev": [3] },
    { "id": "apiky", "label": "ApiKy", "sub": "GET /api/profile?token=", "kind": "service", "service": "apiky" },
    { "id": "h", "label": "operation handler", "sub": "build SOAP args, auth details, print spec", "kind": "step", "ev": [4] },
    { "id": "wsdl", "label": "soap.createClientAsync", "sub": "fetches WSDL every request; retried", "kind": "step", "ev": [5] },
    { "id": "sel", "label": "Selector ClientShipService", "sub": "<Op>Async, not retried", "kind": "external" },
    { "id": "map", "label": "handleResponse", "sub": "200 / 207 / 400", "kind": "step", "ev": [6] }
  ],
  "edges": [
    { "from": "mw", "to": "oab" },
    { "from": "oab", "to": "sec" },
    { "from": "sec", "to": "apiky", "style": "dashed" },
    { "from": "sec", "to": "h", "label": "profile in ctx.security.API_KEY" },
    { "from": "h", "to": "wsdl" },
    { "from": "wsdl", "to": "sel" },
    { "from": "sel", "to": "map" }
  ] }
```

`src/app.ts` mounts the request-id, container-id and logger middleware, JSON body parsing, the `/health` router, and one `openAPIController` that handles everything else [1]. The controller builds an `OpenAPIBackend` from `config.openapi.schemaFilename` at import time, with a top-level `await api.init()`. A missing or invalid spec therefore stops the process at startup [2]. It also serves `/docs` (Redoc) and `/openapi.yaml` [2].

### Operations

| Route | operationId | SOAP op | Request wrapper sent | Per-shipment detail read from |
| --- | --- | --- | --- | --- |
| `POST /ProcessShipments` | processShipments | ProcessShipments | `ShipRequests{Shipments.RequestedShipment, PrintSpec}` | `ProcessShipmentsResult.Shipments.ProcessedShipment[].ShipmentStatus` |
| `POST /ValidateShipments` | validateShipments | ValidateShipments | `ShipRequests{…}` | `ValidateShipmentsResult.ValidatedShips.ValidatedShipment[].Status.ResponseDetails` |
| `DELETE /DeleteShipments` | deleteShipments | DeleteShipments | `Shipments{RequestedShipments}` | `DeleteShipmentsResult.Shipments[].Status` |
| `POST /CommitShipGroup` | commitShipGroup | CommitShipGroup | `ShipGroupRequest{ShipGroups}` | `CommitShipGroupResult.ErrorShipGroups[].ResponseDetails` |
| `POST /CommitShipments` | commitShipments | CommitShipments | `CarrierShipments{…, CarrierServiceGroups}` | `CommitShipmentsResult.CarrierDocuments[].ResponseDetails` |

Every handler spreads `AuthenticationDetails` (version 5.0.0, `UserID`, `UserPassword`) into the wrapper [4][5]. Process and Validate merge the caller's `PrintSpecification` over `DefaultPrintSpec` (203 dpi, ZPLII, `PAPER_4X6`, `BOTTOM_EDGE_OF_TEXT_FIRST`, `PrintDocs: false`) [7].

`DeleteShipments` is a `DELETE` with a JSON body. Some HTTP clients and proxies drop a DELETE body.

### Status mapping

`handleResponse(res, upstream, details, requestSize)` counts the `details` entries whose `Status` is `ERROR` or `FAILURE` (warnings pass) [6]:

- none → **200**, with the raw Selector result as JSON
- some, but fewer than `requestSize` → **207**, with the raw Selector result
- equal to `requestSize` → it throws `BadRequestException`, giving a **400** `application/problem+json` whose `errors[]` is `{field: "Request Body: [i]", problem: StatusDescription}`

`requestSize` is the number of shipments the caller sent. For CommitShipGroup it is the total consignments across groups, and for CommitShipments the `CarrierServiceGroups` length [4]. **ASSESSED** CommitShipGroup compares error groups to consignments, so a whole-request failure there can still come back as 207.

The code marks one gap with a todo: a Selector `FAILURE`/`ERROR` with no per-shipment detail reads as success [6]. CommitShipGroup alone guards one shape of it [4].

### EU commodity validation

`eu-commodity-validation.ts` holds a pre-flight check for Process and Validate. For a recipient country in the EU-27 it requires `SKU`, `ManufacturerProductID` and `StandardisedProductID` on every commodity. Failing shipments are withheld from Selector and spliced back into the response as `FAILURE` / `0030` entries in request order, and a 400 follows if every shipment fails [8]. **It is disabled**: `findMissingEuFields` returns `[]` before its logic, and the matching tests are switched off with a `TEMPORARY` marker [8]. The handlers still call it, so re-enabling it means deleting the early return.

## Auth and tenancy

`securityHandlers.API_KEY` is `apiKyHandler` [2][3]. In order:

1. `AUTH_ENABLED` false → `{}` (no profile).
2. No `x-api-key` → reject (401 problem+json).
3. Key equals `BASICAUTH_KEY` → `true` (no profile). In prod that key is a Terraform `random_password` [9].
4. Otherwise `GET {APIKY_BASE_URL}?token=<key>` with the service's own `APIKY_KEY`, timed as the `apiky.request.latency` histogram. A status of 400 or more → reject. A 2xx returns `{upstream, username, password}` from `data.profile` [3].
5. A thrown error → 500 `Unable to authorize`.

Handlers read the profile from `ctx.security.API_KEY`. `getClient(profile?.upstream)` and `getAuthenticationDetails(profile)` fall back field by field to `REMOTE_SELECTOR_WSDL`, `SELECTOR_USERNAME` and `SELECTOR_PASSWORD` [5]. A profile with credentials but no `upstream` only logs a warning, then sends that tenant's credentials to the sandbox WSDL [3][5].

The ApiKy profile is the tenant record. Adding a tenant means adding an ApiKy token whose profile names its Selector instance. Nothing in this repo lists tenants.

## Resilience

`ExponentialBackoffRetrier` races the call against a `RESILIENCE_TIMEOUT_MS` timer (default 2 s) and retries up to `RESILIENCE_MAX_RETRIES` times (default 3) with jittered quadratic backoff [10]. **Only the WSDL fetch (`soap.createClientAsync`) is wrapped.** The SOAP operation itself has no retry and no timeout of its own, so it is bounded only by the LB backend timeout (30 s) and Cloud Run's request timeout (300 s) [9]. The client is not cached: every request downloads and parses the tenant's WSDL again [5].

## Errors

`ErrorHandler` sends a `GFSException` subclass as its own problem+json, and anything else as a 500 with a fixed body. It increments a failure counter and logs at error level either way [11]. The subclasses are BadRequest (400, `client.request.failed`), Authorization (401), NotFound (404) and InternalServerError. A failed SOAP call logs the request args with `client.lastRequest` and `client.lastResponse` (the raw XML) before it rethrows.

The spec declares `GET /` and `GET /liveness` with no `operationId`. openapi-backend matches them and then throws `Unknown operation`, so those two paths answer 500. The real health routes are `/health` and `/health/liveness` on the Express router [1][12].

## Runtime and deploy

| Item | Value |
| --- | --- |
| Cloud Run | `gfs-selector-rest-proxy-prod`, project `gfs-selector-rest-prod-uk1`, `europe-west2` |
| Scaling | min 1 instance, concurrency 80, 1 vCPU / 512 Mi; startup probe `GET /health` on 3003 |
| Sidecar | `gcr.io/datadoghq/serverless-init:latest`, shared in-memory volume, `DD_SERVICE` = project name |
| Ingress | `run.invoker` for `allUsers`; global external HTTPS LB, Google-managed cert for `selector_hosted_domain` (`rest-preview.selector.freightops.dev`), HTTP→HTTPS redirect |
| DNS | the A record is a central record in core-infra, not in this repo |
| Env from Terraform | `NODE_ENV=prod`, `DD_API_KEY`, `BASICAUTH_KEY` (random), `APIKY_KEY`, `APIKY_BASE_URL` |
| Env from the image | `.env.production`, loaded by dotenv-flow (sandbox WSDL, `TEST` creds, `AUTH_ENABLED`, `BASICAUTH_ENABLED`) |
| State | GCS bucket `gfs-tfstate`, prefix `prod/gfs-selector-rest-proxy` |
| Image | `europe-west2-docker.pkg.dev/gfs-selector-rest-prod-uk1/selector/gfs-selector-rest-proxy:<sha>` |

The LB name and its HTTPS proxy carry a hash of the cert domains, so changing the domain replaces both [9]. `Dockerfile` copies `src/schemas/` into the runtime image because `tsc` does not emit yaml, and runs `node --enable-source-maps` [13].

CI is `on-pr.yaml` (unit + smoke tests, typecheck, lint, a terragrunt plan comment) and `on-push.yaml` (unit tests → image → plan → auto-apply, plus the gated destroy job) [14]. Terraform is 1.3.0 and terragrunt 0.50.8, through `gruntwork-io/terragrunt-action`. Module sources are fetched with `ORG_READ_ACCESS_TOKEN`.

## Observability

- Logs are winston JSON on stdout and stderr in production. The sidecar ships them to Datadog under service `gfs-selector-rest-proxy-prod` [15]. Inside each line, `service` is `selector-proxy`.
- Each line carries `requestor{requestId, username, isSandbox}` from the cls-hooked namespace. **ASSESSED** `isSandbox` reads `true` on error lines even for authenticated tenants, so do not filter on it.
- The access log skips bots (`isbot`) and two static paths, and records bodies and client IP [15].
- Metrics go through `dd-trace`'s dogstatsd: `apiky.request.latency` and the exception failure counters. No monitor or dashboard for this service was found.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "src/app.ts@05c2bea" },
  { "id": 2, "kind": "code", "ref": "src/controllers/openapi.controller.ts@05c2bea" },
  { "id": 3, "kind": "code", "ref": "src/handlers/auth/apiky.handler.ts@05c2bea" },
  { "id": 4, "kind": "code", "ref": "src/handlers/selector/commit-ship-group.handler.ts@05c2bea" },
  { "id": 5, "kind": "code", "ref": "src/selector.ts@05c2bea" },
  { "id": 6, "kind": "code", "ref": "src/handlers/selector/util.ts@05c2bea" },
  { "id": 7, "kind": "code", "ref": "src/handlers/selector/defaults.ts@05c2bea" },
  { "id": 8, "kind": "code", "ref": "src/handlers/selector/eu-commodity-validation.ts@05c2bea" },
  { "id": 9, "kind": "code", "ref": "iac/projects/gfs-selector-rest-proxy/main.tf@05c2bea" },
  { "id": 10, "kind": "code", "ref": "src/retrier.ts@05c2bea" },
  { "id": 11, "kind": "code", "ref": "src/exceptions/error.handler.ts@05c2bea" },
  { "id": 12, "kind": "log", "ref": "Datadog service:gfs-selector-rest-proxy-prod \"Unknown operation\", 2026-10-12..27", "note": "221 occurrences, stack from OpenAPIValidator.validateRequest" },
  { "id": 13, "kind": "code", "ref": "Dockerfile@05c2bea" },
  { "id": 14, "kind": "code", "ref": ".github/workflows/on-push.yaml@05c2bea" },
  { "id": 15, "kind": "code", "ref": "src/middleware/logger.middleware.ts@05c2bea" }
] }
```
