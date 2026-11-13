---
tags:
- waypoint
- parcel-portal
title: parcel-portal — overview
thesis: "parcel-portal is Native Dispatch, known as the Parcel Portal until 13 Nov 2026 (the repo, service and system ids stay parcel-portal): a Go service, a Next.js UI, an SFTP host, a customer-API gateway and two browser packages. It takes a customer's order CSVs by SFTP, browser upload or API, validates them row by row, books them with the carrier through Selector, prints labels at the pack bench and exports a day-end CSV. It is deliberately outside Fuse, and as of 13 Nov 2026 runs in dev only: prod is held."
confidence: high
verified: '2026-10-29'
verified_sha: 696cbd4
verified_paths:
- apps/svc/README.md
- apps/svc/openapi.yaml
- apps/ui/README.md
- iac/projects
---
# parcel-portal — overview

```orient-bluf
{ "v": 1, "bluf": "parcel-portal is Native Dispatch, known as the Parcel Portal until 13 Nov 2026 (the repo, service and system ids stay parcel-portal): a Go service, a Next.js UI, an SFTP host, a customer-API gateway and two browser packages. It takes a customer's order CSVs by SFTP, browser upload or API, validates them row by row, books them with the carrier through Selector, prints labels at the pack bench and exports a day-end CSV. It is deliberately outside Fuse, and as of 13 Nov 2026 runs in dev only: prod is held.", "confidence": "high", "action": "none" }
```

## Responsibility
- **Intake:** three ways in. A customer's WMS drops order CSVs on the portal's own SFTP host, staff upload a CSV in the browser, and the customer's systems send CSV or JSON through the customer API (`/v1`, via the gateway). svc imports each into the tenant whose slug names its folder, or whose API key sent it [1].
- **Validation and fix-up:** a bad row never sinks the file. svc keeps invalid orders with plain reasons, and staff fix them on the Orders screen [1].
- **Booking:** at-most-once dispatch through the tenant's Selector account, labels stored in GCS, void and manifest at Selector. In dev a customer can book with a fake carrier instead [1].
- **Printing:** print-to-screen everywhere, with a preview first, and silent WebUSB printing from a paired bench browser (`packages/label-print`) [2].
- **Export:** the day-end CSV in Despatch Cloud's 17-column layout, for the customer's WMS, for one day or up to 31 [1].
- **Customer setup:** GFS admins set each customer up in the ui (Settings → Customers): users, SFTP users and keys, file layout, shipping methods, the Selector account and its services, packaging, bench printers, export settings, and soft-delete. A `gfs_admin` can act for a customer [1][3].

## Why it exists separately
Harry's agents built it for one US customer (TCA, at a Yusen US site), as a parallel route to Despatch Cloud. Fuse is the platform's ingestion point. It has no labelling, packing or bench UI. So the portal **copies** Fuse's building blocks instead of depending on them. These are the rules-engine DSL ported to Go, the CONNECTOR_MAPPING shape, sftp-connector's Go SFTP host and selector-adapter's Selector client. Whether intake should move back into Fuse is an open question (see [[known-context]]).

## Neighbours
```orient-flow
{ "v": 1, "title": "parcel-portal in context",
  "nodes": [
    { "id": "wms", "label": "Customer systems", "sub": "WMS (Manhattan SCALE for TCA)", "kind": "external" },
    { "id": "sftp", "label": "sftp (Go)", "sub": "MIG + TCP LB, static IP", "kind": "service" },
    { "id": "gcs", "label": "Inbound bucket", "sub": "<slug>/inbound/", "kind": "store" },
    { "id": "gw", "label": "gateway (Go)", "sub": "Cloud Run, public, API key", "kind": "service" },
    { "id": "svc", "label": "svc (Go)", "sub": "Cloud Run", "kind": "service", "tone": "accent" },
    { "id": "db", "label": "Cloud SQL Postgres", "sub": "IAM auth only", "kind": "store" },
    { "id": "labels", "label": "Labels bucket", "kind": "store" },
    { "id": "ui", "label": "ui (Next.js)", "sub": "Cloud Run", "kind": "service" },
    { "id": "sel", "label": "Selector", "sub": "ClientShipService.asmx", "kind": "external" },
    { "id": "bench", "label": "Bench browser", "sub": "WebUSB to ZPL/EPL printer", "kind": "external" }
  ],
  "edges": [
    { "from": "wms", "to": "sftp", "label": "CSV over SFTP" },
    { "from": "wms", "to": "gw", "label": "customer API" },
    { "from": "sftp", "to": "gcs", "label": "write on close" },
    { "from": "gcs", "to": "svc", "label": "Pub/Sub push" },
    { "from": "gw", "to": "svc", "label": "declared /v1 routes, ID token" },
    { "from": "svc", "to": "db" },
    { "from": "svc", "to": "labels" },
    { "from": "svc", "to": "sel", "label": "validate, book, void, commit, query" },
    { "from": "ui", "to": "svc", "label": "HTTP, ID token + session" },
    { "from": "bench", "to": "ui", "label": "browser" }
  ] }
```
Only the UI's, the gateway's and the import push service accounts may invoke svc. The browser never talks to svc directly, and a customer's systems reach it only through the gateway, with an API key [1][3].

## Where the reference lives
- `apps/svc/README.md` is the deep reference for svc: routes, tenancy, import, the customer API and gateway, dispatch, shipments, printing, SFTP users. `docs/runbook.md` is the ops path. `docs/printing.md` covers bench printers.
- **Don't trust the root `README.md` and `AGENTS.md`'s *This repo* section:** they still describe svc-template.
- **Stale lines in the reference (checked against the code):** `docs/runbook.md` says the SFTP host has one account, one tenant has a carrier account, there is no list-tenants call and no void; all four are untrue. `apps/svc/README.md`'s `carrier-services` row says nothing enforces the list, but dispatch refuses a blocked or unlisted service.
- Structure and guardrails: [[architecture]]. History, fragility and open questions: [[known-context]]. Running it, and what has reached prod: [[operations]].
- Programme state, gates and decisions: `Bifrost/Parcel Portal/Migration State.md` (foundations, the customer screens and the held prod launch D1) and `Bifrost/Native Dispatch/` (planning: the 13 Nov customer feedback as 30 units, 4 shipped on 12 Nov). System framing: `Systems/parcel-portal/`.

## What deliberately isn't here
- **Canonical Fuse records and the event bus.** The portal publishes nothing to Fuse topics; orders live only in its Postgres.
- **Carrier integrations.** Selector does the carrier work; the portal only calls it.
- **Self-signup and self-serve.** GFS creates every tenant and user, and only a `gfs_admin` manages users, SFTP users, layouts and carrier accounts.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "apps/svc/README.md@621357e" },
  { "id": 2, "kind": "code", "ref": "packages/label-print/README.md@621357e" },
  { "id": 3, "kind": "code", "ref": "apps/ui/README.md@621357e" }
] }
```
