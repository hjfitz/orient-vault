---
tags: [waypoint, ups-proxy]
title: ups-proxy — architecture
thesis: "An Express app with two routers: /api/stepping-stone passes Selector's UPS XML through with a bearer token, and /api/v2 maps JSON requests onto UPS's JSON APIs through seven ordered transformers. Both sit behind ApiKy key validation."
confidence: high
verified: 2026-11-06
---
# ups-proxy — architecture

```orient-bluf
{ "v": 1, "bluf": "An Express app with two routers: /api/stepping-stone passes Selector's UPS XML through with a bearer token, and /api/v2 maps JSON requests onto UPS's JSON APIs through seven ordered transformers. Both sit behind ApiKy key validation.", "confidence": "high", "action": "Remove the request and response body logging in stepping-stone.js before anything else: it writes full UPS XML, with personal data, to Datadog." }
```

## Guardrails
- [contract:G1] Selector sends PascalCase paths (`ShipConfirm`). Route matching must stay case-insensitive; the dev rewrite's camelCase routes would 404.
  — paths: src/api/routes
- [policy:G2] `stepping-stone.js` logs full request and response bodies. Don't extend it; remove it.
  — paths: src/api/routes/stepping-stone.js
- [technical:G3] ShipConfirm and createLabel aren't idempotent. Don't add retries.
  — paths: src/api

## Structure

```orient-flow
{ "v": 1, "title": "ups-proxy routes",
  "nodes": [
    { "id": "ak", "label": "ApiKy middleware", "sub": "401 no key, 403 bad key", "kind": "step" },
    { "id": "ss", "label": "/api/stepping-stone", "sub": "XML passthrough", "kind": "service", "ev": [1] },
    { "id": "v2", "label": "/api/v2", "sub": "JSON, transformers", "kind": "service" },
    { "id": "auth", "label": "OAuth token", "sub": "cached", "kind": "step", "ev": [2] },
    { "id": "ux", "label": "UPS XML API", "kind": "external" },
    { "id": "uj", "label": "UPS JSON APIs", "kind": "external" }
  ],
  "edges": [
    { "from": "ak", "to": "ss" },
    { "from": "ak", "to": "v2" },
    { "from": "ss", "to": "auth" },
    { "from": "v2", "to": "auth" },
    { "from": "ss", "to": "ux", "label": "body unchanged" },
    { "from": "v2", "to": "uj" }
  ] }
```

- **Stepping stone** forwards the body unchanged and returns UPS's status and body as `application/xml` [1].
- **V2** applies the transformers in order: canary-islands, china, domestic, eu-to-gb, gb-to-eu, gb-to-rest, norway. Known source bugs: `ShipmentServiceOptions` sits outside `Shipment`, so two transformers never fire; access-point search sends the misspelt `AdressLine`.
- **Health:** lightship probes on a separate port (9001).

## Runtime
- GKE `prod-uk1-primary-cluster`, at `ups.gfsdeliver.com`. Source is Azure DevOps (*GFS UPS Integration*), last changed June 2025.
- Traffic, 21 Oct–5 Nov: about 6.1k ShipConfirm/ShipAccept pairs and about 40 voids; no Locator, LabelRecovery or V2 calls (snapshot 2026-11-06).
- CSS sends about 6,100 of those confirms for about 35 companies; Client4 sends 228 for 8. The XML declaration tells them apart.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "src/api/routes/stepping-stone.js@bacc881" },
  { "id": 2, "kind": "code", "ref": "src/auth.js@bacc881" }
] }
```
