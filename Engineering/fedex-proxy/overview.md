---
tags:
- waypoint
- fedex-proxy
title: fedex-proxy — overview
thesis: 'fedex-proxy is GFS''s proxy between CSS and FedEx, on Cloud Run. It creates
  shipments with customs and cancels them. Client4 doesn''t use it: Client4 calls
  FedEx''s old API directly.'
confidence: high
verified: '2026-11-06'
verified_paths:
- code/src
verified_sha: 1d246f8
---
# fedex-proxy — overview

```orient-bluf
{ "v": 1, "bluf": "fedex-proxy is GFS's proxy between CSS and FedEx, on Cloud Run. It creates shipments with customs and cancels them. Client4 doesn't use it: Client4 calls FedEx's old API directly.", "confidence": "high", "action": "none" }
```

## Responsibility
- Create shipment with customs, and cancel [1].
- Looks up the FedEx account in MongoDB by `fedexCustomerId` from the ApiKy profile [1].

## In prod (snapshot 2026-11-06, 15 days to 5 Nov)
- **Traffic:** 71 creates, 29 cancels.
- **Credentials:** MongoDB, per customer.
- **Runs on:** Cloud Run, from GitHub.

**Quirks.** FedEx truncates centimetres to inches on labels (TCA). A blank FEDEX_URL sends Client4 to FedEx's test gateway.

## Where the reference lives
- The system view, with every proxy side by side: `Systems/carrier-integrations/`.
- MPK *Carrier Ingress Services* (353697822) and *Carrier Proxies: Estate and Use Cases* (352059403) [2].

## What deliberately isn't here
- **Choosing the carrier.** Selector decides, from the site's contracts.
- **Tracking.** That's carrier egress: the connectors and webhooks.

## Neighbours

```orient-flow
{ "v": 1, "title": "fedex-proxy in context",
  "nodes": [
    { "id": "sel", "label": "Selector", "sub": "CSS or Client4", "kind": "external" },
    { "id": "p", "label": "fedex-proxy", "kind": "service", "tone": "accent" },
    { "id": "ak", "label": "ApiKy", "sub": "key to profile", "kind": "external" },
    { "id": "cr", "label": "MongoDB", "kind": "store" },
    { "id": "car", "label": "FedEx API", "kind": "external" }
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
  { "id": 1, "kind": "code", "ref": "code/src/integrations/fedex-integration.ts@1d246f8" },
  { "id": 2, "kind": "doc", "ref": "Confluence MPK 353697822 Carrier Ingress Services" }
] }
```
