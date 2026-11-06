---
tags: [waypoint, bjs-proxy]
title: bjs-proxy — overview
thesis: "bjs-proxy is GFS's proxy between Selector and BJS. It creates labels and cancels shipments, taking BJS's carrier secret straight from the caller's ApiKy profile."
confidence: high
verified: 2026-11-06
---
# bjs-proxy — overview

```orient-bluf
{ "v": 1, "bluf": "bjs-proxy is GFS's proxy between Selector and BJS. It creates labels and cancels shipments, taking BJS's carrier secret straight from the caller's ApiKy profile.", "confidence": "high", "action": "none" }
```

## Responsibility
- Create label and cancel [1].
- Reads `bjsSecret` from the ApiKy profile and sends it to BJS as the API key [1].

## In prod (snapshot 2026-11-06, 15 days to 5 Nov)
- **Traffic:** 664 labels, 22 cancels, 6–7 clients.
- **Credentials:** BJS secret in the ApiKy profile.
- **Runs on:** GKE (prod-uk1-primary-cluster).

**Quirks.** The GitHub copy (gfs-hybrid-services/bjs-proxy) is behind this one and serves a hostname Selector doesn't use.

## Where the reference lives
- The system view, with every proxy side by side: `Systems/carrier-integrations/`.
- MPK *Carrier Ingress Services* (353697822) and *Carrier Proxies: Estate and Use Cases* (352059403) [2].

## What deliberately isn't here
- **Choosing the carrier.** Selector decides, from the site's contracts.
- **Tracking.** That's carrier egress: the connectors and webhooks.

## Neighbours

```orient-flow
{ "v": 1, "title": "bjs-proxy in context",
  "nodes": [
    { "id": "sel", "label": "Selector", "sub": "CSS or Client4", "kind": "external" },
    { "id": "p", "label": "bjs-proxy", "kind": "service", "tone": "accent" },
    { "id": "ak", "label": "ApiKy", "sub": "key to profile", "kind": "external" },
    { "id": "cr", "label": "BJS secret in the ApiKy profile", "kind": "store" },
    { "id": "car", "label": "BJS API", "kind": "external" }
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
  { "id": 1, "kind": "code", "ref": "src/integrations/bjs-integration.js@ed56a53" },
  { "id": 2, "kind": "doc", "ref": "Confluence MPK 353697822 Carrier Ingress Services" }
] }
```
