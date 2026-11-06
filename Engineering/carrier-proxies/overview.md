---
tags:
- waypoint
- carrier-proxies
title: carrier-proxies — overview
thesis: 'carrier-proxies is the GitHub monorepo that rewrites GFS''s UPS, OCS, Coll8
  and Exelot proxies onto the shared api-host-framework, keeping success responses
  byte for byte. It runs in dev only: production still runs the Azure DevOps originals.'
confidence: high
verified: '2026-11-06'
verified_paths:
- apps
verified_sha: a996061
---
# carrier-proxies — overview

```orient-bluf
{ "v": 1, "bluf": "carrier-proxies is the GitHub monorepo that rewrites GFS's UPS, OCS, Coll8 and Exelot proxies onto the shared api-host-framework, keeping success responses byte for byte. It runs in dev only: production still runs the Azure DevOps originals.", "confidence": "high", "action": "Reconcile the UPS route casing with Selector before any prod cutover: the rewrite's camelCase routes would 404 Selector's PascalCase calls." }
```

## Responsibility
- `apps/ups-proxy`, `apps/ocs-proxy`, `apps/coll8-proxy` and `apps/exelot-proxy`, each on api-host-framework [1]. A Veho stub returning spec examples also exists in later clones.
- Golden fixtures from the originals pin the success shapes. Retries are 0, because creates aren't idempotent.

## Cutover risks
- **UPS route casing:** Selector sends `ShipConfirm`; the rewrite routes `shipConfirm`.
- **UPS errors become JSON** (`problem+json`), which Selector's XML parsing may not handle.
- **Exelot keys** each need an ApiKy profile with `exelotPartnerId`.

## Neighbours

```orient-flow
{ "v": 1, "title": "carrier-proxies in context",
  "nodes": [
    { "id": "cp", "label": "carrier-proxies", "sub": "dev only", "kind": "service", "tone": "accent" },
    { "id": "ups", "label": "ups-proxy", "sub": "prod original", "kind": "service" },
    { "id": "c8", "label": "coll8-proxy", "sub": "prod original", "kind": "service" },
    { "id": "ahf", "label": "api-host-framework", "kind": "service" }
  ],
  "edges": [
    { "from": "cp", "to": "ahf", "label": "built on" },
    { "from": "cp", "to": "ups", "label": "replaces, later" },
    { "from": "cp", "to": "c8", "label": "replaces, later" }
  ] }
```

## Where the reference lives
- The ledger here (CID-334, the UPS migration). The prod originals: [[ups-proxy]], [[coll8-proxy]], [[ocs-proxy]], [[exelot-proxy]].

## What deliberately isn't here
- **Production traffic.** It all goes to the originals.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "apps@8c25fc2" }
] }
```
