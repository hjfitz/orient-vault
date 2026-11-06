---
tags:
- system
- carrier-integrations
verified: '2026-11-06'
title: carrier-integrations — architecture
thesis: "Ingress proxies are small Node services: ApiKy key to profile, profile to carrier credentials, carrier token, call, label back. Egress has three paths into raw_tracking.v1: polling connectors on tracking-core, webhook services that match pushed events to shipments, and SFTP files. Polling carries 87% of events."
confidence: high
---
# carrier-integrations — architecture

```orient-bluf
{ "v": 1, "bluf": "Ingress proxies are small Node services: ApiKy key to profile, profile to carrier credentials, carrier token, call, label back. Egress has three paths into raw_tracking.v1: polling connectors on tracking-core, webhook services that match pushed events to shipments, and SFTP files. Polling carries 87% of events.", "confidence": "high", "action": "Never log carrier payloads or keys: several proxies still do, and their logs reach Datadog." }
```

## Guardrails
- [policy:G1] Never log carrier request or response bodies, labels, ApiKy keys or carrier tokens. Payloads hold recipient personal data.
  — paths: src/api/routes/stepping-stone.js, src/integrations
- [technical:G2] Creates are not idempotent, and no proxy retries. A timed-out create that the carrier completed leaves an orphan shipment if the caller re-books.
  — paths: src/integrations
- [operational:G3] Webhook shadow mode records events as seen, so turning publish on doesn't backfill. Dedupe is per service, so a carrier's connector and webhook both feed `raw_tracking.v1` while both run.
  — paths: packages/tracking-webhook-core
- [contract:G4] Selector calls proxy routes in PascalCase (UPS `ShipConfirm`). A proxy that matches routes case-sensitively 404s Selector.
  — paths: src/api/routes, apps/ups-proxy
- [contract:G5] `raw_tracking.v1` is shared by all three tracking paths and has no formal schema. A field change hits every downstream consumer.
  — paths: schema, packages/tracking-webhook-core

## Ingress: what a proxy does

```orient-flow
{ "v": 1, "title": "One proxied label",
  "nodes": [
    { "id": "sel", "label": "Selector", "sub": "CUST_SITES URL + CARR_KEY", "kind": "external" },
    { "id": "ak", "label": "1 Auth", "sub": "ApiKy key to profile", "kind": "step" },
    { "id": "cr", "label": "2 Credentials", "sub": "profile to carrier account", "kind": "step" },
    { "id": "tk", "label": "3 Carrier token", "sub": "OAuth, cached", "kind": "step" },
    { "id": "call", "label": "4 Map and call", "kind": "step" },
    { "id": "car", "label": "Carrier API", "kind": "external" },
    { "id": "back", "label": "5 Map back", "sub": "base64 label, tracking, errors", "kind": "step" }
  ],
  "edges": [
    { "from": "sel", "to": "ak", "label": "x-api-key" },
    { "from": "ak", "to": "cr" },
    { "from": "cr", "to": "tk" },
    { "from": "tk", "to": "call" },
    { "from": "call", "to": "car" },
    { "from": "car", "to": "back" },
    { "from": "back", "to": "sel" }
  ] }
```

| Proxy | Prod home | Traffic, 15 days | Credentials |
| --- | --- | --- | --- |
| Royal Mail | Azure DevOps, GKE | about 29.6k labels, 347 manifests | MongoDB, per customer |
| UPS | Azure DevOps, GKE | about 6.1k label pairs | One GFS OAuth client |
| Coll8 | Azure DevOps, GKE | 734 labels | One GFS account |
| BJS | Azure DevOps, GKE | 664 labels | In the ApiKy profile |
| Amazon | Azure DevOps, GKE (source not located) | about 2.3k requests a week | Not checked |
| FedEx, InPost | GitHub, Cloud Run | 71 and 44 | MongoDB, per customer |
| OCS, DPD Europe, Exelot | Azure DevOps, GKE | test only, all failing, none | GFS account; MongoDB with KMS; MongoDB |

Snapshot 2026-11-06 [1].

## Egress: three paths into `raw_tracking.v1`

```orient-flow
{ "v": 1, "title": "Tracking into GFS",
  "nodes": [
    { "id": "sid", "label": "shipments.v2.identified", "kind": "topic" },
    { "id": "tc", "label": "tracking-core", "sub": "active-parcels, batches", "kind": "service" },
    { "id": "con", "label": "Polling connectors", "sub": "about 5.44M events", "kind": "service" },
    { "id": "wh", "label": "Webhook services", "sub": "about 215k events", "kind": "service" },
    { "id": "fi", "label": "SFTP files", "sub": "about 54k events", "kind": "service" },
    { "id": "car", "label": "Carriers", "kind": "external" },
    { "id": "rt", "label": "raw_tracking.v1", "kind": "topic", "tone": "accent" }
  ],
  "edges": [
    { "from": "sid", "to": "tc" },
    { "from": "sid", "to": "wh" },
    { "from": "tc", "to": "con", "label": "batches" },
    { "from": "con", "to": "car", "label": "poll" },
    { "from": "car", "to": "wh", "label": "push" },
    { "from": "car", "to": "fi", "label": "files" },
    { "from": "con", "to": "rt" },
    { "from": "wh", "to": "rt" },
    { "from": "fi", "to": "rt" }
  ] }
```

## On request: proof of delivery

POD sits outside the event stream. [[gfs-pod-service]] keeps a copy of each shipment from `shipments.v2.identified`. When a caller asks, it fetches the POD from the carrier live. It normalises the result and caches it in Redis.

```orient-flow
{ "v": 1, "title": "One POD request",
  "nodes": [
    { "id": "c", "label": "public-gateway, Connect, Nexus", "kind": "external" },
    { "id": "p", "label": "gfs-pod-service", "sub": "v2, in-cluster", "kind": "service", "tone": "accent" },
    { "id": "cr", "label": "gfs-carrier-credentials", "sub": "legacy", "kind": "external" },
    { "id": "car", "label": "Carrier POD API", "kind": "external" }
  ],
  "edges": [
    { "from": "c", "to": "p", "label": "GET /pod/:shipmentId" },
    { "from": "p", "to": "cr" },
    { "from": "p", "to": "car", "label": "signature, photo, GPS" }
  ] }
```

## Coverage by carrier (15 days to 6 Nov 2026)

| Carrier | Path | Events |
| --- | --- | --- |
| Evri | Polling (webhook in shadow) | 2,301,636 |
| DHL Parcel UK | Polling | 1,485,343 |
| DPD Local | Polling | 1,008,906 |
| DPD | Polling | 752,850 |
| Amazon Logistics | Polling, through the Amazon proxy | 226,991 |
| Royal Mail | Webhook | 215,319 |
| UPS | Polling | 105,720 |
| Evri ParcelShop | Polling | 44,712 |
| GFS International | Polling | 33,068 |
| DX Freight, BJS, DPD NL, Coll8, OCS | Files | 61,012 combined |
| DHL Express, InPost, FedEx | Polling | 10,919, 305, 21 |

No tracking source: Click & Collect, Parcelforce, Palletforce. Idle connectors: Yodel, Panther, Collect+ [2].

## Credential patterns (class-level)
- **Per customer, in MongoDB,** keyed by an ID in the ApiKy profile: Royal Mail, FedEx, InPost, Exelot, DPD Europe (KMS-encrypted).
- **Per customer, in the ApiKy profile itself:** BJS.
- **One GFS account for everyone:** UPS, OCS, Coll8.
- **Connectors:** a SealedSecret per connector; DPD, DPD Local, Panther and FedEx fetch per-contract credentials from `carrier-credentials-manager`.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "doc", "ref": "Confluence MPK 353697822 Carrier Ingress Services" },
  { "id": 2, "kind": "doc", "ref": "Confluence MPK 353206337 Carrier Egress Services" }
] }
```
