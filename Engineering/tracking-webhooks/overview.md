---
tags: [waypoint, tracking-webhooks]
title: tracking-webhooks — overview
thesis: "tracking-webhooks is the monorepo for GFS's carrier tracking webhooks: carriers push events, and a shared core matches them to GFS shipments and publishes to raw_tracking.v1. Evri deploys from it in shadow, with publishing off. InPost and the Royal Mail import are open PRs."
confidence: high
verified: 2026-11-06
---
# tracking-webhooks — overview

```orient-bluf
{ "v": 1, "bluf": "tracking-webhooks is the monorepo for GFS's carrier tracking webhooks: carriers push events, and a shared core matches them to GFS shipments and publishes to raw_tracking.v1. Evri deploys from it in shadow, with publishing off. InPost and the Royal Mail import are open PRs.", "confidence": "high", "action": "Turning publish on doesn't backfill what shadow mode already recorded, and the matching connector must be switched off within hours." }
```

## Responsibility
- **One app per carrier** under `apps/`, built on `packages/tracking-webhook-core` [1].
- **The core** authenticates per carrier, acknowledges fast, and processes through an interim topic [1].
- **Processing** matches each event to a GFS shipment, then publishes to `raw_tracking.v1` when publishing is on.
- **Shared Terraform:** one module (`iac/modules/tracking-webhook`) and one project per carrier, named to keep each carrier's state key [2].

## Why it exists separately
Webhooks replace polling for carriers that push. Each carrier differs only in auth and mapping, so one core with thin adapters replaces a repo per carrier.

## Neighbours

```orient-flow
{ "v": 1, "title": "tracking-webhooks in context",
  "nodes": [
    { "id": "car", "label": "Carrier", "sub": "Evri today", "kind": "external" },
    { "id": "wh", "label": "tracking-webhooks", "sub": "Cloud Run, one service per carrier", "kind": "service", "tone": "accent" },
    { "id": "sid", "label": "shipments.v2.identified", "kind": "topic" },
    { "id": "mg", "label": "Mongo", "sub": "shipments, retries", "kind": "store" },
    { "id": "rt", "label": "raw_tracking.v1", "kind": "topic" },
    { "id": "con", "label": "connectors-hermes", "sub": "still polling Evri", "kind": "service" }
  ],
  "edges": [
    { "from": "car", "to": "wh", "label": "POST /tracking" },
    { "from": "sid", "to": "wh", "label": "shipments" },
    { "from": "wh", "to": "mg" },
    { "from": "wh", "to": "rt", "label": "when publish is on" },
    { "from": "con", "to": "rt", "label": "today's Evri feed" }
  ] }
```

## Where the reference lives
- [[architecture]] and [[known-context]] here; the repo's `monorepoplan.md`, `README.md` and `AGENTS.md`.
- MPK *Tracking Webhook Services* (353533985).

## What deliberately isn't here
- **Royal Mail, for now.** It runs from [[tracking-webhook-royal-mail-sapient]] until PR #3 merges.
- **Status derivation.** ECM's deriver consumes `raw_tracking.v1`.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "packages/tracking-webhook-core/src@9777dd4" },
  { "id": 2, "kind": "code", "ref": "iac/modules/tracking-webhook@9777dd4" }
] }
```
