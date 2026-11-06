---
tags:
- waypoint
- tracking-webhooks
title: tracking-webhooks — architecture
thesis: A carrier POSTs to a Cloud Run service behind a load balancer. A per-carrier
  adapter authenticates it, the core publishes it to an interim topic and acknowledges,
  then a push handler matches it to a stored GFS shipment and publishes to raw_tracking.v1.
  Unmatched events wait in Mongo for up to 90 days.
confidence: high
verified: '2026-11-06'
verified_paths:
- packages/tracking-webhook-core
- iac
verified_sha: 9777dd4
---
# tracking-webhooks — architecture

```orient-bluf
{ "v": 1, "bluf": "A carrier POSTs to a Cloud Run service behind a load balancer. A per-carrier adapter authenticates it, the core publishes it to an interim topic and acknowledges, then a push handler matches it to a stored GFS shipment and publishes to raw_tracking.v1. Unmatched events wait in Mongo for up to 90 days.", "confidence": "high", "action": "Before turning a carrier's publish flag on, plan the connector switch-off: dedupe is per service, so both feeds reach raw_tracking.v1 while both run." }
```

## Guardrails
- [operational:G1] Shadow mode records events as seen. Turning `PUBSUB_TRACKING_PUBLISH_ENABLED` on won't backfill anything already received.
  — paths: packages/tracking-webhook-core, iac/projects
- [operational:G2] Dedupe is local to each service. While a carrier's connector and webhook both run, both feed `raw_tracking.v1`. Evri's terms also forbid running both for long.
  — paths: packages/tracking-webhook-core
- [contract:G3] A carrier must only move in from a standalone repo when the plan shows only moved resources, and only one repo may deploy a carrier's project at a time.
  — paths: iac/projects, iac/modules/tracking-webhook

## Structure

```orient-flow
{ "v": 1, "title": "One webhook event",
  "nodes": [
    { "id": "car", "label": "Carrier", "kind": "external" },
    { "id": "cr", "label": "POST /tracking", "sub": "auth adapter", "kind": "service" },
    { "id": "it", "label": "interim topic", "sub": "5 attempts, then DLQ", "kind": "topic" },
    { "id": "pr", "label": "Process event", "sub": "match to shipment", "kind": "step", "ev": [1] },
    { "id": "sh", "label": "Mongo shipments", "sub": "this carrier only", "kind": "store" },
    { "id": "re", "label": "Mongo retries", "sub": "up to 90 days", "kind": "store" },
    { "id": "rt", "label": "raw_tracking.v1", "kind": "topic" },
    { "id": "sid", "label": "shipments.v2.identified", "kind": "topic" }
  ],
  "edges": [
    { "from": "car", "to": "cr" },
    { "from": "cr", "to": "it", "label": "publish, then 200" },
    { "from": "it", "to": "pr", "label": "push" },
    { "from": "pr", "to": "sh", "label": "lookup" },
    { "from": "pr", "to": "rt", "label": "matched" },
    { "from": "pr", "to": "re", "label": "unmatched" },
    { "from": "sid", "to": "sh", "label": "push, filtered by carrier" },
    { "from": "sh", "to": "re", "label": "release held events" }
  ] }
```

| Part | What it is |
| --- | --- |
| Endpoints | `POST /tracking`, an optional carrier verification `GET`, `/health/liveness`, and two OIDC-protected Pub/Sub push endpoints. Cloud Run takes traffic only from the load balancer |
| Auth | Per carrier: Evri sends an API key header; InPost signs the body (HMAC); Royal Mail uses an OAuth client-credentials token checked as a JWT |
| Matching | Carrier plus consignment number, then parcel. `parcel.auto_created` adds a parcel when its number equals the consignment number |
| Output | The connectors' `raw_tracking.v1` shape, with `rawData` empty and a `carrierIdV2` attribute |
| Flags | `PUBSUB_TRACKING_PUBLISH_ENABLED`, `PUBSUB_INTERIM_TRACKING_ENABLED` and the shipment-subscription flag, per environment in tfvars [2] |

## Runtime
- Cloud Run in `gfs-selector-rest-prod-uk1`, `europe-west2`. No dev environment: CI creates and destroys a stack per end-to-end run.
- **Evri** (`tracking-webhook-evri-prod-cr`): 561k events in 15 days, 0 published (snapshot 2026-11-06).
- `apps/acme` is a fictional template carrier, never deployed. New carriers are added by copying it.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "packages/tracking-webhook-core/src/process.ts@9777dd4" },
  { "id": 2, "kind": "code", "ref": "iac/projects/tracking-webhook-evri/variables.tf@9777dd4" }
] }
```
