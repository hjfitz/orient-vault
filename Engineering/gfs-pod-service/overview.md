---
tags: [waypoint, gfs-pod-service]
title: gfs-pod-service — overview
thesis: "gfs-pod-service returns a proof of delivery on request: it looks up the shipment, calls the carrier's own POD or tracking API live, and returns one normalised POD with signature, safe-place photo and GPS. It serves the customer portal, Connect API and staff tools, about 21k requests in 15 days, mostly DHL Parcel UK."
confidence: high
verified: 2026-11-06
---
# gfs-pod-service — overview

```orient-bluf
{ "v": 1, "bluf": "gfs-pod-service returns a proof of delivery on request: it looks up the shipment, calls the carrier's own POD or tracking API live, and returns one normalised POD with signature, safe-place photo and GPS. It serves the customer portal, Connect API and staff tools, about 21k requests in 15 days, mostly DHL Parcel UK.", "confidence": "high", "action": "Change the repo in Azure DevOps project GFS POD, by PR; read its AGENTS.md first." }
```

## Responsibility
- Keeps its own copy of each shipment (carrier, consignment, parcels, address) from `shipments.v2.identified`, plus BJS tracking from `raw_tracking.v1` [1].
- On request, fetches the POD from the carrier's API and normalises it: signee, delivery time, GPS, images, comments [2].
- Serves POD images and emails a POD on request through SendGrid.

## Why it exists separately
POD isn't part of the tracking event stream. Most carriers only return signatures and photos from a separate API call, made when someone asks. This service owns those per-carrier calls and the image handling: base64 decoding, PDF and TIFF cropping.

## Neighbours

```orient-flow
{ "v": 1, "title": "gfs-pod-service in context",
  "nodes": [
    { "id": "sid", "label": "shipments.v2.identified", "kind": "topic" },
    { "id": "sub", "label": "Subscriber", "sub": "same image", "kind": "service" },
    { "id": "mongo", "label": "Mongo PODService", "kind": "store" },
    { "id": "gw", "label": "public-gateway, Connect, Nexus", "sub": "callers, v2", "kind": "external" },
    { "id": "api", "label": "POD API", "sub": "v2 in-cluster, v1 public", "kind": "service", "tone": "accent" },
    { "id": "redis", "label": "Redis", "sub": "POD cache", "kind": "store" },
    { "id": "ccs", "label": "gfs-carrier-credentials", "kind": "external" },
    { "id": "car", "label": "Carrier POD APIs", "kind": "external" }
  ],
  "edges": [
    { "from": "sid", "to": "sub" },
    { "from": "sub", "to": "mongo" },
    { "from": "gw", "to": "api", "label": "GET /pod/:shipmentId" },
    { "from": "api", "to": "mongo" },
    { "from": "api", "to": "redis" },
    { "from": "api", "to": "ccs", "label": "credentials" },
    { "from": "api", "to": "car", "label": "live fetch" }
  ] }
```

## Where the reference lives
- The repo's `AGENTS.md` is the most complete description. [[architecture]] covers the API and the carriers; [[known-context]] covers traffic and risks.
- ECM's `ecm-development` `docs/data-journeys.md` has the POD journey step by step.

## What deliberately isn't here
- **Tracking events.** Those come through connectors, webhooks and files into `raw_tracking.v1`; see system [[carrier-integrations]].
- **gfs-smart-pod-service.** Its repo is disabled and it's commented out of prod config.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "src/subscriber@811007e" },
  { "id": 2, "kind": "code", "ref": "src/pod-service/pod-cache.js@811007e" }
] }
```
