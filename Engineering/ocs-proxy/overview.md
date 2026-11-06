---
tags: [waypoint, ocs-proxy]
title: ocs-proxy — overview
thesis: "ocs-proxy is GFS's proxy between Selector and OCS. It creates labels only, using one GFS OCS account. In prod only a test client calls it."
confidence: high
verified: 2026-11-06
---
# ocs-proxy — overview

```orient-bluf
{ "v": 1, "bluf": "ocs-proxy is GFS's proxy between Selector and OCS. It creates labels only, using one GFS OCS account. In prod only a test client calls it.", "confidence": "high", "action": "none" }
```

## Responsibility
- Create label only; no cancel or manifest [1].

## In prod (snapshot 2026-11-06, 15 days to 5 Nov)
- **Traffic:** 103 calls, all from the Test2 client.
- **Credentials:** One GFS account.
- **Runs on:** GKE (prod-uk1-primary-cluster).

**Quirks.** A dev rewrite exists in carrier-proxies/apps/ocs-proxy.

## Where the reference lives
- The system view, with every proxy side by side: `Systems/carrier-integrations/`.
- MPK *Carrier Ingress Services* (353697822) and *Carrier Proxies: Estate and Use Cases* (352059403) [2].

## What deliberately isn't here
- **Choosing the carrier.** Selector decides, from the site's contracts.
- **Tracking.** That's carrier egress: the connectors and webhooks.

## Neighbours

```orient-flow
{ "v": 1, "title": "ocs-proxy in context",
  "nodes": [
    { "id": "sel", "label": "Selector", "sub": "CSS or Client4", "kind": "external" },
    { "id": "p", "label": "ocs-proxy", "kind": "service", "tone": "accent" },
    { "id": "ak", "label": "ApiKy", "sub": "key to profile", "kind": "external" },
    { "id": "cr", "label": "One GFS account", "kind": "store" },
    { "id": "car", "label": "OCS API", "kind": "external" }
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
  { "id": 1, "kind": "code", "ref": "README.md@29eeaa6" },
  { "id": 2, "kind": "doc", "ref": "Confluence MPK 353697822 Carrier Ingress Services" }
] }
```
