---
tags: [waypoint, coll8-proxy]
title: coll8-proxy — overview
thesis: "coll8-proxy is GFS's proxy between Selector and Coll8. It creates labels, cancels shipments and sends the end-of-day manifest, using one GFS Coll8 account for every customer."
confidence: high
verified: 2026-11-06
---
# coll8-proxy — overview

```orient-bluf
{ "v": 1, "bluf": "coll8-proxy is GFS's proxy between Selector and Coll8. It creates labels, cancels shipments and sends the end-of-day manifest, using one GFS Coll8 account for every customer.", "confidence": "high", "action": "none" }
```

## Responsibility
- Create label: maps Selector's request to a Coll8 shipment, then fetches each package's label (PDF, ZPL, or PNG through GFS's converter) [1].
- Cancel and end-of-day manifest [1].
- Reads the customer's Coll8 account code from the ApiKy profile (`accountCode`).

## In prod (snapshot 2026-11-06, 15 days to 5 Nov)
- **Traffic:** 734 labels, 14 manifests.
- **Credentials:** One GFS account, plus the account code in ApiKy.
- **Runs on:** GKE (prod-uk1-primary-cluster).

**Quirks.** Echoes upstream error detail back to the caller, which can include credentials (class-level; on the security list). Client4's cancel sends a JSON body that fails parsing, so Client4 cancels return 500.

## Where the reference lives
- The system view, with every proxy side by side: `Systems/carrier-integrations/`.
- MPK *Carrier Ingress Services* (353697822) and *Carrier Proxies: Estate and Use Cases* (352059403) [2].

## What deliberately isn't here
- **Choosing the carrier.** Selector decides, from the site's contracts.
- **Tracking.** That's carrier egress: the connectors and webhooks.

## Neighbours

```orient-flow
{ "v": 1, "title": "coll8-proxy in context",
  "nodes": [
    { "id": "sel", "label": "Selector", "sub": "CSS or Client4", "kind": "external" },
    { "id": "p", "label": "coll8-proxy", "kind": "service", "tone": "accent" },
    { "id": "ak", "label": "ApiKy", "sub": "key to profile", "kind": "external" },
    { "id": "cr", "label": "One GFS account", "kind": "store" },
    { "id": "car", "label": "Coll8 API", "kind": "external" }
  ],
  "edges": [
    { "from": "sel", "to": "p", "label": "x-api-key" },
    { "from": "p", "to": "ak" },
    { "from": "p", "to": "cr", "label": "credentials" },
    { "from": "p", "to": "car", "label": "REST" }
  ] }
```

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "src/startup.js@479b3db" },
  { "id": 2, "kind": "doc", "ref": "Confluence MPK 353697822 Carrier Ingress Services" }
] }
```
