---
tags:
- system
- parcel-portal
verified: '2026-10-29'
title: parcel-portal — architecture
thesis: "One repo, four runtimes: a Go API on Cloud Run that owns a tenant-scoped Postgres, a Go SFTP host on a MIG that writes to GCS, a Next.js UI that is svc's only caller, and a browser package that prints over WebUSB. Selector does every carrier call."
confidence: high
---
# parcel-portal — architecture

```orient-bluf
{ "v": 1, "bluf": "One repo, four runtimes: a Go API on Cloud Run that owns a tenant-scoped Postgres, a Go SFTP host on a MIG that writes to GCS, a Next.js UI that is svc's only caller, and a browser package that prints over WebUSB. Selector does every carrier call.", "confidence": "high", "action": "Keep tenant scoping in the request context; it is the one thing a multi-customer future depends on." }
```

The system narrative. The service-level structure, guardrails and interfaces are in `Engineering/parcel-portal/architecture.md`.

## The day, end to end
```orient-flow
{ "v": 1, "title": "A shipping day",
  "nodes": [
    { "id": "drop", "label": "WMS drops CSV", "kind": "external" },
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
- **A monolith:** one Go binary holds the API, import, mapping, Selector client, export and auth. SFTP is a second command in the same module only because Cloud Run serves HTTP only.
- **Postgres, IAM only:** orders, queues, search and date ranges are relational, and there are no database passwords to leak.
- **Tenancy from day one:** every customer row carries `tenant_id`, enforced in the repositories and by a static test, so a second customer is a data change, not a rewrite.
- **Printing in the browser:** no print agent to install. The browser rasterises PDF labels to ZPL or EPL and talks to the USB printer directly; anything that fails falls back to the print dialog.

## What is single-customer today
- The SFTP host serves one user with one key, fixed to one tenant.
- The carrier account is going to environment variables (snapshot 2026-10-29).
- Tenant, user and mapping setup is API only.
- One site per tenant: the timezone sits on the tenant.

`Bifrost/Parcel Portal/Multi-customer.md` covers what changes for more customers.
