---
tags:
- system
- parcel-portal
verified: '2026-11-13'
title: parcel-portal — architecture
thesis: "One repo, five runtimes: a Go API on Cloud Run that owns a tenant-scoped Postgres, a Go SFTP host on a MIG that writes to GCS, a Next.js UI and a public customer-API gateway that are svc's only callers, and browser packages that print over WebUSB and make SSH keys. Selector does every carrier call."
confidence: high
---
# parcel-portal — architecture

```orient-bluf
{ "v": 1, "bluf": "One repo, five runtimes: a Go API on Cloud Run that owns a tenant-scoped Postgres, a Go SFTP host on a MIG that writes to GCS, a Next.js UI and a public customer-API gateway that are svc's only callers, and browser packages that print over WebUSB and make SSH keys. Selector does every carrier call.", "confidence": "high", "action": "Keep tenant scoping in the request context; it is the one thing a multi-customer future depends on." }
```

The system narrative. The service-level structure, guardrails and interfaces are in `Engineering/parcel-portal/architecture.md`.

## The day, end to end
```orient-flow
{ "v": 1, "title": "A shipping day",
  "nodes": [
    { "id": "drop", "label": "Order file arrives", "sub": "SFTP, browser upload or customer API", "kind": "external" },
    { "id": "import", "label": "Import", "sub": "format check, map, row checks", "kind": "service" },
    { "id": "fix", "label": "Orders screen", "sub": "fix, pack, dispatch", "kind": "service", "tone": "accent" },
    { "id": "book", "label": "Selector", "sub": "book, label", "kind": "external" },
    { "id": "print", "label": "Bench printer", "sub": "WebUSB or print dialog", "kind": "external" },
    { "id": "manifest", "label": "Manifest", "sub": "CommitShipments", "kind": "service" },
    { "id": "export", "label": "Day-end export", "sub": "DC 17 columns", "kind": "service" }
  ],
  "edges": [
    { "from": "drop", "to": "import" },
    { "from": "import", "to": "fix", "label": "invalid, needs packing, ready" },
    { "from": "fix", "to": "book", "label": "at most once" },
    { "from": "book", "to": "print" },
    { "from": "print", "to": "manifest" },
    { "from": "manifest", "to": "export", "label": "back to WMS" }
  ] }
```

## Why it is shaped this way
- **Partial import:** the failure it exists to fix is Selector's all-or-nothing CSV import. A file is rejected only when its format is wrong; otherwise each order stands or falls alone.
- **A monolith:** one Go binary, `svc`, holds the API, import, mapping, Selector client, export and auth. The other commands in the module are thin [1]:
  - SFTP, because Cloud Run serves HTTP only.
  - The canary, which logs in to the SFTP host as a customer would.
  - The gateway, the customer API's public front door, so svc itself stays private.
  - A debug MCP for dev.
- **Postgres, IAM only:** orders, queues, search and date ranges are relational, and there are no database passwords to leak.
- **Tenancy from day one:** every customer row carries `tenant_id`, enforced in the repositories and by a static test, so a second customer is a data change, not a rewrite.
- **Printing in the browser:** no print agent to install. The browser rasterises PDF labels to ZPL or EPL and talks to the USB printer directly; anything that fails falls back to the print dialog.

## What is still single-customer
GFS admins already set up each customer in the UI: users, SFTP logins, file layout, carrier account, packaging, printers and export settings. What remains:
- **One site per tenant:** the timezone sits on `tenant` [2].
- **One export layout:** Despatch Cloud's 17 columns. A customer sets only its time zone, tracking link and Excel flag [3].
- **One service per requested method:** a per-customer lookup turns the file's shipping method into a carrier service. No rules choose by destination or weight [1].
- **The tenant's meaning:** shipper or warehouse operator is undecided (gate G10).

`Bifrost/Parcel Portal/Multi-customer.md` covers what changes for more customers. It predates the SFTP, carrier-account and setup items above, which are done.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "apps/svc/README.md@621357e" },
  { "id": 2, "kind": "code", "ref": "apps/svc/internal/repositories/postgres/migrations/005_tenant_export_settings.sql@621357e" },
  { "id": 3, "kind": "code", "ref": "apps/svc/internal/core/exports/csv.go@621357e" }
] }
```
