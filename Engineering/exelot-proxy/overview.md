---
tags: [waypoint, exelot-proxy]
title: exelot-proxy — overview
thesis: "exelot-proxy is GFS's proxy between Selector and Exelot. It creates labels with a generated commercial invoice. It had no prod traffic in 15 days."
confidence: high
verified: 2026-11-06
---
# exelot-proxy — overview

```orient-bluf
{ "v": 1, "bluf": "exelot-proxy is GFS's proxy between Selector and Exelot. It creates labels with a generated commercial invoice. It had no prod traffic in 15 days.", "confidence": "high", "action": "Fix the ApiKy URL typo before relying on its configuration." }
```

## Responsibility
- Create label with a commercial invoice PDF; keeps the invoice counter in MongoDB [1].
- Looks up per-customer credentials in MongoDB by `exelotPartnerId` from the ApiKy profile.

## In prod (snapshot 2026-11-06, 15 days to 5 Nov)
- **Traffic:** none.
- **Credentials:** MongoDB, per customer.
- **Runs on:** GKE (prod-uk1-primary-cluster).

**Quirks.** `process.sourceMapsEnabled.APIKY_AUTH_URI` is a typo, so the proxy ignores the configured ApiKy URL and always uses the default host [1]. Its spec names the GFS International Hub as a second caller; none seen.

## Where the reference lives
- The system view, with every proxy side by side: `Systems/carrier-integrations/`.
- MPK *Carrier Ingress Services* (353697822) and *Carrier Proxies: Estate and Use Cases* (352059403) [2].

## What deliberately isn't here
- **Choosing the carrier.** Selector decides, from the site's contracts.
- **Tracking.** That's carrier egress: the connectors and webhooks.

## Neighbours

```orient-flow
{ "v": 1, "title": "exelot-proxy in context",
  "nodes": [
    { "id": "sel", "label": "Selector", "sub": "CSS or Client4", "kind": "external" },
    { "id": "p", "label": "exelot-proxy", "kind": "service", "tone": "accent" },
    { "id": "ak", "label": "ApiKy", "sub": "key to profile", "kind": "external" },
    { "id": "cr", "label": "MongoDB", "kind": "store" },
    { "id": "car", "label": "Exelot API", "kind": "external" }
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
  { "id": 1, "kind": "code", "ref": "src/integrations/apiky-integration.js@b21a47d" },
  { "id": 2, "kind": "doc", "ref": "Confluence MPK 353697822 Carrier Ingress Services" }
] }
```
