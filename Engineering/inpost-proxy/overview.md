---
tags: [waypoint, inpost-proxy]
title: inpost-proxy — overview
thesis: "inpost-proxy is GFS's proxy between CSS and InPost, on Cloud Run. It creates labels and return labels. Client4 doesn't use it: Client4 calls InPost's old API directly."
confidence: high
verified: 2026-11-06
---
# inpost-proxy — overview

```orient-bluf
{ "v": 1, "bluf": "inpost-proxy is GFS's proxy between CSS and InPost, on Cloud Run. It creates labels and return labels. Client4 doesn't use it: Client4 calls InPost's old API directly.", "confidence": "high", "action": "none" }
```

## Responsibility
- Create label and return label; no cancel [1].
- Looks up InPost OAuth credentials in MongoDB by `CustomerId` from the ApiKy profile [1].

## In prod (snapshot 2026-11-06, 15 days to 5 Nov)
- **Traffic:** 44 calls; no return labels.
- **Credentials:** MongoDB, per customer.
- **Runs on:** Cloud Run, from GitHub.

**Quirks.** `log_carrier_payload` is marked TEMPORARY and logs carrier payloads (class-level; on the security list).

## Where the reference lives
- The system view, with every proxy side by side: `Systems/carrier-integrations/`.
- MPK *Carrier Ingress Services* (353697822) and *Carrier Proxies: Estate and Use Cases* (352059403) [2].

## What deliberately isn't here
- **Choosing the carrier.** Selector decides, from the site's contracts.
- **Tracking.** That's carrier egress: the connectors and webhooks.

## Neighbours

```orient-flow
{ "v": 1, "title": "inpost-proxy in context",
  "nodes": [
    { "id": "sel", "label": "Selector", "sub": "CSS or Client4", "kind": "external" },
    { "id": "p", "label": "inpost-proxy", "kind": "service", "tone": "accent" },
    { "id": "ak", "label": "ApiKy", "sub": "key to profile", "kind": "external" },
    { "id": "cr", "label": "MongoDB", "kind": "store" },
    { "id": "car", "label": "InPost API", "kind": "external" }
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
  { "id": 1, "kind": "code", "ref": "code/src/integrations/inpost-integration.ts@64656dc" },
  { "id": 2, "kind": "doc", "ref": "Confluence MPK 353697822 Carrier Ingress Services" }
] }
```
