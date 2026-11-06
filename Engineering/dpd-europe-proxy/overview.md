---
tags: [waypoint, dpd-europe-proxy]
title: dpd-europe-proxy — overview
thesis: "dpd-europe-proxy is GFS's proxy between Selector and DPD in the Netherlands and Germany. It speaks REST to Selector and SOAP to DPD. Every prod call in 15 days failed validation."
confidence: high
verified: 2026-11-06
---
# dpd-europe-proxy — overview

```orient-bluf
{ "v": 1, "bluf": "dpd-europe-proxy is GFS's proxy between Selector and DPD in the Netherlands and Germany. It speaks REST to Selector and SOAP to DPD. Every prod call in 15 days failed validation.", "confidence": "high", "action": "Find out why every call fails validation before anyone relies on it." }
```

## Responsibility
- Create label only, for DPD NL and DPD DE [1].
- Per-customer credentials in MongoDB, encrypted with KMS, looked up by `company` from the ApiKy profile [1].

## In prod (snapshot 2026-11-06, 15 days to 5 Nov)
- **Traffic:** 21 calls, all failing validation.
- **Credentials:** MongoDB with KMS, per customer.
- **Runs on:** GKE (prod-uk1-primary-cluster).

**Quirks.** Logs a 60-character token and personal data (class-level; on the security list).

## Where the reference lives
- The system view, with every proxy side by side: `Systems/carrier-integrations/`.
- MPK *Carrier Ingress Services* (353697822) and *Carrier Proxies: Estate and Use Cases* (352059403) [2].

## What deliberately isn't here
- **Choosing the carrier.** Selector decides, from the site's contracts.
- **Tracking.** That's carrier egress: the connectors and webhooks.

## Neighbours

```orient-flow
{ "v": 1, "title": "dpd-europe-proxy in context",
  "nodes": [
    { "id": "sel", "label": "Selector", "sub": "CSS or Client4", "kind": "external" },
    { "id": "p", "label": "dpd-europe-proxy", "kind": "service", "tone": "accent" },
    { "id": "ak", "label": "ApiKy", "sub": "key to profile", "kind": "external" },
    { "id": "cr", "label": "MongoDB with KMS", "kind": "store" },
    { "id": "car", "label": "DPD NL / DE (SOAP)", "kind": "external" }
  ],
  "edges": [
    { "from": "sel", "to": "p", "label": "x-api-key" },
    { "from": "p", "to": "ak" },
    { "from": "p", "to": "cr", "label": "credentials" },
    { "from": "p", "to": "car", "label": "SOAP" }
  ] }
```

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "src/controllers/Labelling.js@67ad24f" },
  { "id": 2, "kind": "doc", "ref": "Confluence MPK 353697822 Carrier Ingress Services" }
] }
```
