---
tags:
- waypoint
- tracking-webhook-royal-mail-sapient
title: tracking-webhook-royal-mail-sapient — overview
thesis: 'tracking-webhook-royal-mail-sapient receives Royal Mail''s tracking events
  pushed through Sapient and publishes them to raw_tracking.v1. It is the only live
  publishing webhook and Royal Mail''s only tracking source: about 340.6k events in,
  215.9k published in 15 days.'
confidence: high
verified: '2026-11-06'
verified_paths:
- handler
verified_sha: 3c880bf
---
# tracking-webhook-royal-mail-sapient — overview

```orient-bluf
{ "v": 1, "bluf": "tracking-webhook-royal-mail-sapient receives Royal Mail's tracking events pushed through Sapient and publishes them to raw_tracking.v1. It is the only live publishing webhook and Royal Mail's only tracking source: about 340.6k events in, 215.9k published in 15 days.", "confidence": "high", "action": "Moving it into tracking-webhooks (PR #3 there) needs a reviewed plan and a quiet-time merge: Royal Mail has no polling fallback." }
```

## Responsibility
- `POST /tracking` on `royalmail-tracking.gfsdeliver.com`. Royal Mail authenticates with an OAuth client-credentials token the service issues and checks as a JWT [1].
- Holds events in Mongo until the shipment arrives on `shipments.v2.identified`, then publishes to `raw_tracking.v1` [1].
- Processes synchronously: it predates the shared core's interim topic.

## In prod (snapshot 2026-11-06)
- Cloud Run in `gfs-selector-rest-prod-uk1`, revision 00052, deployed 21 May 2026, publish on.
- 15 days: about 340.6k events in, 215.9k published, about 145k held for retry, about 21k dropped unmatched.
- Its metrics carry `env:serverless`, not `env:prod`.

## Neighbours

```orient-flow
{ "v": 1, "title": "tracking-webhook-royal-mail-sapient in context",
  "nodes": [
    { "id": "rm", "label": "Royal Mail Sapient", "kind": "external" },
    { "id": "w", "label": "tracking-webhook-royal-mail-sapient", "kind": "service", "tone": "accent" },
    { "id": "sid", "label": "shipments.v2.identified", "kind": "topic" },
    { "id": "mg", "label": "Mongo", "sub": "held events", "kind": "store" },
    { "id": "rt", "label": "raw_tracking.v1", "kind": "topic" }
  ],
  "edges": [
    { "from": "rm", "to": "w", "label": "POST /tracking" },
    { "from": "sid", "to": "w" },
    { "from": "w", "to": "mg" },
    { "from": "w", "to": "rt" }
  ] }
```

## Where the reference lives
- The shared design it is moving onto: [[tracking-webhooks]]. MPK *Tracking Webhook Services* (353533985).

## What deliberately isn't here
- **Royal Mail labels.** Those go through [[royal-mail-proxy]].

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "handler@3c880bf" }
] }
```
