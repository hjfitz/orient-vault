---
tags:
- waypoint
- gfs-pod-service
title: gfs-pod-service — architecture
thesis: 'One Node image runs as two Deployments: a subscriber that copies shipments
  into Mongo, and an API that answers POD requests by calling the carrier live, caching
  the normalised result in Redis. v2, keyed on shipmentId, is the only API anything
  calls; it has no auth and stays in-cluster. The public v1 needs a pod:read token.'
confidence: high
verified: '2026-11-06'
verified_paths:
- src/api-v2/router.js
- src/api-v1/router.js
- src/pod-service
- src/config.js
verified_sha: 811007e
---
# gfs-pod-service — architecture

```orient-bluf
{ "v": 1, "bluf": "One Node image runs as two Deployments: a subscriber that copies shipments into Mongo, and an API that answers POD requests by calling the carrier live, caching the normalised result in Redis. v2, keyed on shipmentId, is the only API anything calls; it has no auth and stays in-cluster. The public v1 needs a pod:read token.", "confidence": "high", "action": "Never route the v2 port through an ingress: it checks no token." }
```

## Guardrails
- [policy:G1] The v2 API (port 30002) has no token check. It must stay cluster-internal. Only the v1 port sits behind the public `pod.gfsdeliver.com` ingress, and v1 requires a `pod:read` JWT.
  — paths: src/api-v2/router.js, src/api-v1/router.js
- [technical:G2] Carrier credentials come from the legacy `gfs-carrier-credentials` service (`CCS_URL`), not `carrier-credentials-manager`.
  — paths: src/pod-service/credentials-service.js
- [technical:G3] Image ids are minted per cached POD entry, so an image link from an older POD can stop resolving once the cache entry changes.
  — paths: src/pod-service/pod-cache.js
- [contract:G4] On v2 requests the POD address is GFS's shipment address, on purpose, geocoded for its coordinates; a failed geocode falls back to 0,0. v1 passes no shipment, so it keeps the carrier's address. DPD, DPD Local and BJS supply none; Hermes and Yodel derive one from the carrier's GPS point. v1 and v2 share the cache key `carrier:consNo`, so a POD first cached by v1 reaches v2 callers without the GFS address.
  — paths: src/pod-service

## Structure

```orient-flow
{ "v": 1, "title": "A v2 POD request",
  "nodes": [
    { "id": "caller", "label": "Caller", "sub": "public-gateway, Connect, Nexus", "kind": "external" },
    { "id": "route", "label": "v2 router", "sub": "GET /pod/:shipmentId", "kind": "step", "ev": [1] },
    { "id": "mongo", "label": "Mongo shipment doc", "sub": "carrier, consNo, parcels", "kind": "store" },
    { "id": "cache", "label": "pod-cache", "sub": "Redis", "kind": "step", "ev": [2] },
    { "id": "svc", "label": "Carrier service", "sub": "one module per carrier", "kind": "step" },
    { "id": "creds", "label": "gfs-carrier-credentials", "kind": "external" },
    { "id": "car", "label": "Carrier API", "kind": "external" }
  ],
  "edges": [
    { "from": "caller", "to": "route" },
    { "from": "route", "to": "mongo" },
    { "from": "route", "to": "cache" },
    { "from": "cache", "to": "svc", "label": "on miss" },
    { "from": "svc", "to": "creds" },
    { "from": "svc", "to": "car", "label": "POD, images" }
  ] }
```

**Deployments.** Both run the image `gfs-pod-service`, 3 replicas each:
- `gfs-pod-service-deployment`: API v1 and v2 on, subscriber off.
- `gfs-pod-service-deployment-subscriber`: subscriber on, APIs off.

## Interfaces in

| Interface | Detail |
| --- | --- |
| v2 HTTP (in-cluster) | `GET /pod/:shipmentId`, `/type`, `/image/:imageId`; `POST /request`, `/email`; parcel variants under `/parcels/:parcelNo`. Called by public-gateway (customer portal), connect-gateway (Connect API) and Nexus |
| v1 HTTP (public) | `GET /pod/:carrier/:consNo[...]`, `/pod-image/...`. Requires a `pod:read` JWT. No active caller found |
| Pub/Sub | `shipments.v2.identified`, which upserts the shipment doc; `raw_tracking.v1`, BJS only, for detail links. The subscriber handled about 7.8M messages in 15 days |

## Interfaces out
- **Carrier APIs, one module per carrier** in `src/pod-service/`:
  - Amazon Logistics, through the GFS Amazon proxy;
  - BJS, by page scrape;
  - DHL eCommerce UK (UK Mail), DPD, DPD Local, Evri (Hermes), FedEx, Panther, Tuffnells, UPS, Yodel;
  - a DHL Express module exists but isn't loaded (no prod URL), and the test carrier `MOCKCARRIER` is.

  Parcel-level POD applies to DPD, Evri, DPD Local and UPS; the rest are consignment-level. The per-carrier table (API used, requests) is in known-context, under Carriers.
- **Credentials:** `gfs-carrier-credentials` (`getCredential`), with OAuth tokens cached until expiry. There are also per-carrier secrets for UPS, DHL eCommerce UK, FedEx and the Amazon proxy key.
- **Other services:** SendGrid for POD emails, a geocode service, and Google Maps static maps.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "src/api-v2/router.js@811007e" },
  { "id": 2, "kind": "code", "ref": "src/pod-service/pod-cache.js@811007e" },
  { "id": 3, "kind": "doc", "ref": "gfs-ecm/ecm-development docs/data-journeys.md (POD journey)" },
  { "id": 4, "kind": "doc", "ref": "prod-uk1-primary-cluster deploy/k8s/pod-server/pod-service.yaml" }
] }
```

Ingress and Deployment facts are from the prod manifest [4], and the step-by-step journey is in ECM's data journeys [3].
