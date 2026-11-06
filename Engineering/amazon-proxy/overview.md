---
tags: [waypoint, amazon-proxy]
title: amazon-proxy — overview
thesis: "amazon-proxy is GFS's Amazon Logistics proxy, used by Selector for labels and by ECM's Amazon connector for tracking. Prod runs an Azure DevOps copy that hasn't been located; this GitHub copy is deployed but gets no prod traffic."
confidence: high
verified: 2026-11-06
---
# amazon-proxy — overview

```orient-bluf
{ "v": 1, "bluf": "amazon-proxy is GFS's Amazon Logistics proxy, used by Selector for labels and by ECM's Amazon connector for tracking. Prod runs an Azure DevOps copy that hasn't been located; this GitHub copy is deployed but gets no prod traffic.", "confidence": "high", "action": "Locate the prod source (image gfs-amazon-logistics-proxy) before changing anything here." }
```

## Responsibility
- Create label and cancel for Selector [1].
- Tracking, called by connectors-amazon through an internal in-cluster copy, and by gfs-pod-service for Amazon PODs.
- Checks rates as part of creating a label.

## In prod (snapshot 2026-11-06, 15 days to 5 Nov)
- **Traffic:** about 2.3k requests a week; frequent Amazon 400s.
- **Credentials:** MongoDB per customer (in this copy).
- **Runs on:** GKE (prod-uk1-primary-cluster).

**Quirks.** The new tracking route takes the customer from the URL path, not the caller's key [1]. So any valid key can read any customer (class-level; on the security list). The internal in-cluster copy runs with IS_SECURED=false.

## Where the reference lives
- The system view, with every proxy side by side: `Systems/carrier-integrations/`.
- MPK *Carrier Ingress Services* (353697822) and *Carrier Proxies: Estate and Use Cases* (352059403) [2].

## What deliberately isn't here
- **Choosing the carrier.** Selector decides, from the site's contracts.
- **Tracking.** That's carrier egress: the connectors and webhooks.

## Neighbours

```orient-flow
{ "v": 1, "title": "amazon-proxy in context",
  "nodes": [
    { "id": "sel", "label": "Selector", "sub": "CSS or Client4", "kind": "external" },
    { "id": "p", "label": "amazon-proxy", "kind": "service", "tone": "accent" },
    { "id": "ak", "label": "ApiKy", "sub": "key to profile", "kind": "external" },
    { "id": "cr", "label": "MongoDB per customer (in this copy)", "kind": "store" },
    { "id": "car", "label": "Amazon Logistics API", "kind": "external" }
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
  { "id": 1, "kind": "code", "ref": "code/src/handlers/labelling.handler.ts@be40413" },
  { "id": 2, "kind": "doc", "ref": "Confluence MPK 353697822 Carrier Ingress Services" }
] }
```
