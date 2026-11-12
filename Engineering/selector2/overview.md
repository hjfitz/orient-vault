---
tags:
- waypoint
- selector2
title: selector2 — overview
thesis: 'selector2 is a multi-tenant TypeScript replacement for Selector''s label-getting:
  a NestJS api that keeps CSS''s SOAP and selector-rest-proxy''s REST wire contracts,
  adds a terse REST v2, books labels through carrier-playground''s twelve mock proxies,
  and a SvelteKit UI over it. It is a dev-only, synthetic-data build with no prod
  and no cutover.'
confidence: high
verified: '2026-11-12'
verified_sha: '6442634'
verified_paths:
- README.md
- AGENTS.md
- apps/selector2-api/openapi
- apps/selector2-ui/src/hooks.server.ts
- iac/projects
---
# selector2 — overview

```orient-bluf
{ "v": 1, "bluf": "selector2 is a multi-tenant TypeScript replacement for Selector's label-getting: a NestJS api that keeps CSS's SOAP and selector-rest-proxy's REST wire contracts, adds a terse REST v2, books labels through carrier-playground's twelve mock proxies, and a SvelteKit UI over it. It is a dev-only, synthetic-data build with no prod and no cutover.", "confidence": "high", "action": "none" }
```

## Responsibility
- **The five label operations:** ProcessShipments, ValidateShipments, DeleteShipments, CommitShipGroup and CommitShipments, over SOAP (`/ClientShipService.asmx`), REST v1 (selector-rest-proxy's routes) and REST v2 (`/v2/shipments`) [1][2].
- **Tenancy and callers:** accounts, hashed API keys and a seeded `god` account. One Postgres holds every tenant, and every row carries `tenant_id` [3].
- **Egress:** one adapter per carrier proxy, each reached with a Cloud Run ID token and an `x-api-key`. The proxies are the mocks in `ilg-merak/carrier-playground` [4].
- **UI:** `selector2-ui` sits behind HTTP basic auth and validates every sign-in against the api, and calls only the basic-auth `/admin` routes. It manages accounts and API keys; its playground composes a v2 shipment and validates, processes, commits and deletes it with the carrier call trace and the label (PNG, PDF, ZPL) streamed through the UI server; `/shipments` lists and shows them; `/export` streams a CSV; `/scenarios` runs 74 preset shipments (one happy path and the mocks' failure values per carrier) and compares each with what it expects [5]. On dev no tenant has carrier contracts yet, so nothing books there until contracts can be provisioned.

## Why it exists separately
Harry asked for a clean replacement, not a port. The wire contracts stay, so a caller changes its URL and credentials and nothing else. The inside is a Drizzle/Postgres model with no Firebird and no C#. It lives in `ilg-merak` because it is Merak's build, outside Fuse. It uploads nothing to GFS: CSV export from the UI is the only way data leaves [6].

## Neighbours
```orient-flow
{ "v": 1, "preset": "c4-container", "title": "selector2 in context",
  "nodes": [
    { "id": "soap", "label": "SOAP clients", "sub": "Parcel Portal, selector-adapter", "kind": "external" },
    { "id": "rest", "label": "REST callers", "sub": "x-api-key, v1 and v2", "kind": "external" },
    { "id": "person", "label": "A person", "sub": "browser", "kind": "external" },
    { "id": "ui", "label": "selector2-ui", "sub": "SvelteKit, basic auth", "kind": "service" },
    { "id": "api", "label": "selector2-api", "sub": "NestJS, Cloud Run", "kind": "service", "tone": "accent" },
    { "id": "db", "label": "Cloud SQL Postgres 17", "sub": "IAM logins only", "kind": "store" },
    { "id": "mocks", "label": "carrier-playground mocks", "sub": "12 proxies", "kind": "external" },
    { "id": "sm", "label": "Secret Manager", "sub": "god password, migrator only", "kind": "store" }
  ],
  "edges": [
    { "from": "soap", "to": "api", "label": "AuthenticationDetails body" },
    { "from": "rest", "to": "api", "label": "x-api-key" },
    { "from": "person", "to": "ui", "label": "basic auth" },
    { "from": "ui", "to": "api", "label": "caller's own Basic header" },
    { "from": "api", "to": "db", "label": "tenant-scoped" },
    { "from": "api", "to": "mocks", "label": "ID token + x-api-key" },
    { "from": "sm", "to": "db", "label": "migrate job syncs god hash" }
  ] }
```
The ui holds no account store and no database access. The api is the only service that reaches Postgres or a carrier proxy [5].

## Where the reference lives
- `docs/` in the repo is the deep reference: `data-model`, `auth`, `admin-api`, `ui`, `soap`, `rest-v1`, `rest-v2`, `shipment-use-cases`, `carrier-egress` and `validation-scope`. `AGENTS.md` carries the programme invariants and the recorded departures from the org contract.
- The programme record is `Bifrost/Selector2/` in the vault: `Migration State.md` (decision log, gates, risks) and the carrier and SOAP evidence digests.
- Structure and guardrails: [[architecture]]. History, decisions and open questions: [[known-context]]. Running it: [[operations]]. The test strategy: [[testing]].

## What deliberately isn't here
- **Firebird events, upload to GFS and billing.** Commit marks a shipment committed and goes no further.
- **Real data.** Every tenant, address, key and label is synthetic.
- **A prod environment.** There is no prod tfvars and no cutover; nothing in production moves to it.
- **Carriers beyond the twelve proxy carriers.** No template-drawn labels and no direct-API carriers.
- **Number-range allocation.** Selector takes consignment numbers from the proxy; the `number_range` table exists but no code allocates from it (Harry's programme dropped unit B4).

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "README.md@6442634" },
  { "id": 2, "kind": "code", "ref": "apps/selector2-api/openapi@6442634" },
  { "id": 3, "kind": "code", "ref": "docs/data-model.md@6442634" },
  { "id": 4, "kind": "code", "ref": "docs/carrier-egress.md@6442634" },
  { "id": 5, "kind": "code", "ref": "docs/ui.md@ee122ca" },
  { "id": 6, "kind": "doc", "ref": "Bifrost/Selector2/Overview.md" }
] }
```
