---
tags: [waypoint, evri-auth-facade]
title: evri-auth-facade — overview
thesis: "evri-auth-facade holds one Evri OAuth token and hands it to the Evri polling connectors, so they don't each log in to Evri. It's a small Express service with an in-memory and Redis cache, called at /token about 1,350 times in 15 days."
confidence: high
verified: 2026-11-06
---
# evri-auth-facade — overview

```orient-bluf
{ "v": 1, "bluf": "evri-auth-facade holds one Evri OAuth token and hands it to the Evri polling connectors, so they don't each log in to Evri. It's a small Express service with an in-memory and Redis cache, called at /token about 1,350 times in 15 days.", "confidence": "high", "action": "Retire it with connectors-hermes and connectors-hermesps when the Evri webhook goes live (CID-315)." }
```

## Responsibility
- **`GET /token`** returns the current Evri access token (client-credentials, audience `client-tracking-api`). It fetches a new token from Evri's OAuth endpoint only when the cached one has expired [1].
- **Cache:** first in memory, then in Redis (Upstash), with a TTL of 3,500 seconds. Over 15 days it served 1,347 token requests: 1,346 from memory, 1 from Redis, and 15 refreshes from Evri.
- **A general proxy route** to Evri's API also exists, but is switched off in prod (`FEATURE_FLAG_EVRI_PROXY=false`).

## Neighbours

```orient-flow
{ "v": 1, "title": "evri-auth-facade in context",
  "nodes": [
    { "id": "h", "label": "connectors-hermes", "kind": "service" },
    { "id": "hps", "label": "connectors-hermesps", "kind": "service" },
    { "id": "f", "label": "evri-auth-facade", "sub": "GET /token", "kind": "service", "tone": "accent" },
    { "id": "c", "label": "Memory and Redis cache", "kind": "store" },
    { "id": "e", "label": "Evri OAuth", "kind": "external" }
  ],
  "edges": [
    { "from": "h", "to": "f", "label": "http://evri-auth-facade:3000/token", "ev": [2] },
    { "from": "hps", "to": "f" },
    { "from": "f", "to": "c" },
    { "from": "f", "to": "e", "label": "on expiry" }
  ] }
```

## Where the reference lives
The repo README describes configuration and the caching design. Evri's tracking path as a whole is in system [[carrier-integrations]].

## What deliberately isn't here
- **The Evri webhook's signature lookup.** `tracking-webhooks` calls Evri itself.
- **Exposure:** the facade is cluster-internal: a NodePort Service with no ingress. Its caller key is a placeholder, and auth only applies when a flag enables it. That's acceptable only while it stays internal.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "src/adaptors/evri.adaptor.js@7bc8861" },
  { "id": 2, "kind": "doc", "ref": "prod-uk1-primary-cluster deploy/k8s/fenghuang/tracking/connectors/connectors-hermes.yaml:82" }
] }
```
