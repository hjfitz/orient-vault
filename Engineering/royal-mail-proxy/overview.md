---
tags: [waypoint, royal-mail-proxy]
title: royal-mail-proxy — overview
thesis: "royal-mail-proxy is GFS's busiest carrier proxy: Selector calls it to create Royal Mail labels through Royal Mail's Sapient API, about 29.6k in 15 days for 19 accounts. It also manifests, changes shipment status, returns customs documents and serves service codes."
confidence: high
verified: 2026-11-06
---
# royal-mail-proxy — overview

```orient-bluf
{ "v": 1, "bluf": "royal-mail-proxy is GFS's busiest carrier proxy: Selector calls it to create Royal Mail labels through Royal Mail's Sapient API, about 29.6k in 15 days for 19 accounts. It also manifests, changes shipment status, returns customs documents and serves service codes.", "confidence": "high", "action": "Search its logs by handler, not message: the create-label and manifest log lines name each other." }
```

## Responsibility
- **Create label** with CN23 and commercial invoice for dutiable shipments [1].
- **Manifest:** marks the shipments Picked first, ignoring errors from that step, then manifests [1].
- **Status changes** (hold, cancel, release, picked) in batches of 99, and **service-code lookup** [1].
- **Per-customer credentials:** the ApiKy profile's `royalmailCustomerId` is the Sapient shipping account. The proxy looks up that customer's Sapient credentials in MongoDB, falling back to service-wide ones [2].

## Why it exists separately
Royal Mail moved to Sapient behind OAuth. The proxy holds each customer's Sapient credentials and the token cache, so Selector sites only hold an ApiKy key.

## Neighbours

```orient-flow
{ "v": 1, "title": "royal-mail-proxy in context",
  "nodes": [
    { "id": "sel", "label": "Selector", "sub": "CSS or Client4", "kind": "external" },
    { "id": "p", "label": "royal-mail-proxy", "sub": "royalmail.gfsdeliver.com", "kind": "service", "tone": "accent" },
    { "id": "ak", "label": "ApiKy", "kind": "external" },
    { "id": "mg", "label": "MongoDB", "sub": "customers, services", "kind": "store" },
    { "id": "sap", "label": "Royal Mail Sapient", "kind": "external" },
    { "id": "cron", "label": "gfs-royal-mail-cron", "sub": "nightly service sync", "kind": "service" }
  ],
  "edges": [
    { "from": "sel", "to": "p", "label": "x-api-key" },
    { "from": "p", "to": "ak" },
    { "from": "p", "to": "mg" },
    { "from": "p", "to": "sap", "label": "OAuth, REST" },
    { "from": "cron", "to": "mg" }
  ] }
```

Tracking for Royal Mail comes back separately, by webhook: [[tracking-webhook-royal-mail-sapient]].

## Where the reference lives
- [[architecture]] and [[known-context]] here. The OpenAPI contract is `api/royalmail-integration-api.yaml`.
- Mock copy for testing: `ilg-merak/carrier-playground` `apps/royal-mail-proxy`.

## What deliberately isn't here
- **Tracking.** Royal Mail pushes it to the Sapient webhook service.
- **Service catalogue sync.** `gfs-royal-mail-cron` runs nightly into the same MongoDB.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "src/integrations/royalmail-integration.js@361de96" },
  { "id": 2, "kind": "code", "ref": "src/stores/royalmail-mongo.js@361de96" }
] }
```
