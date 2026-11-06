---
tags: [waypoint, royal-mail-proxy]
title: royal-mail-proxy — architecture
thesis: "An Express app routed by openapi-backend against api/royalmail-integration-api.yaml. Each call resolves the ApiKy profile, maps the GFS service code to a Royal Mail product through MongoDB, gets a cached Sapient token, and calls Sapient. Four operations, four error classes."
confidence: high
verified: 2026-11-06
---
# royal-mail-proxy — architecture

```orient-bluf
{ "v": 1, "bluf": "An Express app routed by openapi-backend against api/royalmail-integration-api.yaml. Each call resolves the ApiKy profile, maps the GFS service code to a Royal Mail product through MongoDB, gets a cached Sapient token, and calls Sapient. Four operations, four error classes.", "confidence": "high", "action": "The configured ApiKy URL is ignored because of a typo; fix that before moving ApiKy hosts." }
```

## Guardrails
- [technical:G1] `apiky-integration.js` reads `process.sourceMapsEnabled.APIKY_AUTH_URI`, a typo, so it always falls back to the default ApiKy host.
  — paths: src/integrations/apiky-integration.js
- [policy:G2] Never log Sapient request or response bodies: they hold recipient personal data, and labels.
  — paths: src/integrations, src/observability
- [technical:G3] Creates are not idempotent and there are no retries. A timed-out create that Royal Mail completed leaves an orphan if Selector re-books.
  — paths: src/integrations/royalmail-integration.js

## Structure

```orient-flow
{ "v": 1, "title": "Create label",
  "nodes": [
    { "id": "in", "label": "POST /shipping/createLabel", "kind": "step" },
    { "id": "ak", "label": "ApiKy profile", "sub": "royalmailCustomerId", "kind": "external" },
    { "id": "map", "label": "Service-code mapping", "sub": "MongoDB", "kind": "step", "ev": [2] },
    { "id": "tok", "label": "Sapient token", "sub": "5-minute cache", "kind": "step" },
    { "id": "sap", "label": "Sapient create shipment", "kind": "external" },
    { "id": "doc", "label": "CN23 and invoice", "sub": "dutiable only", "kind": "step" },
    { "id": "out", "label": "201, base64 label", "kind": "step" }
  ],
  "edges": [
    { "from": "in", "to": "ak" },
    { "from": "ak", "to": "map" },
    { "from": "map", "to": "tok" },
    { "from": "tok", "to": "sap" },
    { "from": "sap", "to": "doc" },
    { "from": "doc", "to": "out" }
  ] }
```

| Route | What it does |
| --- | --- |
| `POST /shipping/createLabel` | Label, plus CN23 and commercial invoice for dutiable shipments [1] |
| `POST /shipping/manifestShipments` | Marks the shipments Picked (errors ignored), then manifests |
| `POST /shipping/updateShipmentStatus` | Hold, cancel, release or picked, in batches of 99 sent in parallel |
| `GET /shipping/getServiceCodes` | The customer's enabled Royal Mail products |
| `GET /` | Health check; writes no log |

Errors: authentication (403), validation (400 with metadata), carrier (Royal Mail's own status passed through) and internal (500).

## Runtime
- GKE `prod-uk1-primary-cluster`, at `royalmail.gfsdeliver.com`. Source is Azure DevOps (*GFS Royal Mail Intergration*). The GitHub copy (`gfs-hybrid-services/royal-mail-proxy`) is behind, with auto-deploy off.
- Traffic, 21 Oct–5 Nov: about 29.6k labels, 347 manifests, 1.9k service-code lookups, 145 status changes (snapshot 2026-11-06).
- About 6k "path not found" logs in the same window are internet scanners.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "src/integrations/royalmail-integration.js@361de96:L29-L275" },
  { "id": 2, "kind": "code", "ref": "src/services/servicecode-mapping-service.js@361de96" }
] }
```
