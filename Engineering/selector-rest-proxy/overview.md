---
tags:
- waypoint
- selector-rest-proxy
title: selector-rest-proxy — overview
thesis: 'selector-rest-proxy is a stateless REST front for GFS Selector''s SOAP ClientShipService:
  it authenticates an x-api-key against ApiKy, takes that tenant''s Selector instance
  and credentials from the ApiKy profile, and relays five shipment operations as SOAP
  calls.'
confidence: high
verified_paths:
- src/app.ts
- src/controllers
- src/handlers
- src/selector.ts
- src/schemas/openapi.yaml
- src/config.ts
- .env.production
- iac/projects/gfs-selector-rest-proxy
verified: '2026-10-27'
verified_sha: 05c2bea
---
# selector-rest-proxy — overview

```orient-bluf
{ "v": 1, "bluf": "selector-rest-proxy is a stateless REST front for GFS Selector's SOAP ClientShipService: it authenticates an x-api-key against ApiKy, takes that tenant's Selector instance and credentials from the ApiKy profile, and relays five shipment operations as SOAP calls.", "confidence": "high", "action": "Onboard a tenant in ApiKy, not here. Treat every master merge as a prod deploy." }
```

## Responsibility

- It exposes five REST operations, `ProcessShipments`, `ValidateShipments`, `DeleteShipments`, `CommitShipGroup` and `CommitShipments`, plus health and docs routes. Each operation maps one to one onto a Selector SOAP operation of the same name [1][2].
- It validates the JSON body against `openapi.yaml` before any handler runs, and answers bad input with `application/problem+json` [2][3].
- It resolves the caller to a tenant. It looks the `x-api-key` up in ApiKy, and the profile supplies that tenant's Selector WSDL URL, user ID and password [4].
- It maps Selector's per-shipment `ResponseDetails` to a status: 200 if none failed, 207 if some did, 400 if all did [5].
- It fills in a ZPLII 4x6 print spec when the caller sends none [6].

It holds no state. There is no database, cache, queue or Pub/Sub [1].

## Why it exists separately

- **Selector is SOAP, and tenants want REST.** Each Selector customer runs its own instance (`<tenant>.gfsdeliver.com/ClientServer/ClientShipService.asmx`). This service gives them one REST endpoint and spec in front of all of them [4].
- **It is a stepping stone, due for retirement.** The intended replacement is a Fuse adapter that calls Selector directly, with tenants moving onto Fuse. See [[known-context]].
- It lives in the `gfs-hybrid-services` org and GCP project `gfs-selector-rest-prod-uk1`, outside the Fuse estate. It shares none of Fuse's canonical types, envelopes or pipeline [7].

## Neighbours

```orient-flow
{ "v": 1, "title": "selector-rest-proxy in context",
  "nodes": [
    { "id": "client", "label": "Tenant WMS / iPaaS", "sub": "YUSENCASIO, SMEGUK", "kind": "external" },
    { "id": "lb", "label": "Global HTTPS LB", "sub": "rest-preview.selector.freightops.dev", "kind": "step", "ev": [7] },
    { "id": "proxy", "label": "selector-rest-proxy", "sub": "Cloud Run, prod only", "kind": "service", "tone": "accent", "ev": [1, 7] },
    { "id": "apiky", "label": "ApiKy", "sub": "token -> profile", "kind": "service", "service": "apiky", "ev": [4] },
    { "id": "sel", "label": "Selector (SOAP)", "sub": "one instance per tenant", "kind": "external", "ev": [8] },
    { "id": "sandbox", "label": "Selector sandbox", "sub": "sandbox.gfsdeliver.com, user TEST", "kind": "external", "ev": [9] },
    { "id": "dd", "label": "Datadog", "sub": "logs via sidecar", "kind": "external", "ev": [7] }
  ],
  "edges": [
    { "from": "client", "to": "lb", "label": "x-api-key" },
    { "from": "lb", "to": "proxy" },
    { "from": "proxy", "to": "apiky", "label": "GET ?token=" },
    { "from": "proxy", "to": "sel", "label": "SOAP, profile creds" },
    { "from": "proxy", "to": "sandbox", "label": "no profile: env fallback", "style": "dashed" },
    { "from": "proxy", "to": "dd", "style": "dashed" }
  ] }
```

A request goes to the tenant's Selector only when ApiKy returns a profile. A static `BASICAUTH_KEY` match, or auth turned off, has no profile. The request then falls back to the env WSDL and credentials. Those point at the Selector **sandbox**, user `TEST`, in every environment including prod [4][9].

## Where the reference lives

- [[architecture]] covers the guardrails, request path, status mapping, auth resolution, runtime and deploy.
- [[known-context]] covers ownership, the retirement plan, tenants, and what is fragile.
- The API contract is `src/schemas/openapi.yaml`, served live at `/docs` (Redoc) and `/openapi.yaml`.

Do not trust:

- The spec's `servers` entry `https://customer.selector.gfsdeliver.com`. It does not resolve. The live host is `rest-preview.selector.freightops.dev` [7][10].
- The `CLIENT_CUSTOMER_NAME` env var. Config requires it, but no code reads it [11].

## What deliberately isn't here

- **Tenant configuration.** It is the ApiKy profile (`upstream`, `username`, `password`). Onboarding a tenant needs no change to this repo.
- **Shipment logic.** Rating, labels and carrier selection all happen in Selector. The proxy only reshapes and relays.
- **Any non-prod environment.** There is one stack, `prod`. A `dev` env existed briefly in February 2025 [12].
- **Fuse integration.** No Pub/Sub, canonical types or config-service.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "src/app.ts@05c2bea" },
  { "id": 2, "kind": "code", "ref": "src/controllers/openapi.controller.ts@05c2bea" },
  { "id": 3, "kind": "code", "ref": "src/handlers/errors/validation-fail.handler.ts@05c2bea" },
  { "id": 4, "kind": "code", "ref": "src/handlers/auth/apiky.handler.ts@05c2bea" },
  { "id": 5, "kind": "code", "ref": "src/handlers/selector/util.ts@05c2bea" },
  { "id": 6, "kind": "code", "ref": "src/handlers/selector/defaults.ts@05c2bea" },
  { "id": 7, "kind": "code", "ref": "iac/projects/gfs-selector-rest-proxy/main.tf@05c2bea" },
  { "id": 8, "kind": "log", "ref": "Datadog logs service:gfs-selector-rest-proxy-prod \"Authed successfully with apiky\" by @data.upstream, 2026-10-12..27", "note": "two upstreams: yusencasio.gfsdeliver.com (5,202), smegukltd.gfsdeliver.com (2,055)" },
  { "id": 9, "kind": "code", "ref": ".env.production@05c2bea" },
  { "id": 10, "kind": "code", "ref": "src/schemas/openapi.yaml@05c2bea" },
  { "id": 11, "kind": "code", "ref": "src/config.ts@05c2bea" },
  { "id": 12, "kind": "url", "ref": "https://github.com/gfs-hybrid-services/selector-rest-proxy/commit/cf15f7c" }
] }
```
