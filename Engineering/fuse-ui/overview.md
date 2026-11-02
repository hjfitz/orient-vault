---
tags:
- waypoint
- fuse-ui
verified: '2026-10-14'
verified_sha: d610a91
verified_paths:
- code/package.json
- code/src/config.ts
- code/src/proxy.ts
- code/src/lib/db
- code/src/app
- iac/projects/fuse-ui
title: fuse-ui — overview
thesis: fuse-ui is the staff console for customer setup and failure triage. It owns
  only its users, audit log and mapping templates; all platform data comes from the
  owning services.
confidence: high
---
# fuse-ui — overview

```orient-bluf
{ "v": 1, "bluf": "fuse-ui is the staff console for customer setup and failure triage. It owns only its users, audit log and mapping templates; all platform data comes from the owning services.", "confidence": "high", "action": "Never add a Fuse platform collection to fuse-ui's own Mongo. Read platform data through the owning service's API." }
```

## Responsibility

fuse-ui is a Next.js 16 app that Fuse staff use to configure customers and clear pipeline failures. [1]

- **Customer setup.** Operators manage customers, storefronts, connectors and mappings. They also edit the central configuration: backend, DDP, shipping methods, SKU ignore list, VAS and warehouse routing [2].
- **Failure triage.** The Retry Queue lists failures that replay-service holds. Operators replay, dismiss or delete them. It lives at `/customer/{id}/exceptions` [3].
- **Pipeline views.** Dedupe Summary lists and releases records dedupe-service holds. Transaction History reads collector records. A flag-gated Order Tracker reads tracking-service [2].
- **Mapping templates.** A library of reusable mappings sits in fuse-ui's own Mongo. Applying one copies it into a connector [4].
- **Change History and users.** Admins read the audit trail and manage users [2].
- **ASSESSED** Only Fuse staff use it. Accounts are admin-created, nothing offers self-signup, and `/customer/{id}` routes name the customer, not the user. [[known-context]] records the interview.

## Why it exists separately

It is the one place a human works on the platform directly. Every other Fuse service is machine to machine.

Its own database stays small on purpose. It holds `users`, `audit_log` and `template_collections`, and nothing else [5]. Everything else is read live from the owning service. A copy of platform data would drift from its source.

Auth is app-level: a signed session cookie that `proxy.ts` checks. No load-balancer auth sits in front [6][13].

## Neighbours

```orient-flow
{ "v": 1, "title": "fuse-ui in context",
  "nodes": [
    { "id": "op", "label": "Fuse staff", "sub": "browser, session cookie", "kind": "external", "ev": [6] },
    { "id": "ui", "label": "fuse-ui", "sub": "Next.js BFF", "kind": "service", "service": "fuse-ui", "tone": "accent", "ev": [1] },
    { "id": "mongo", "label": "Own MongoDB", "sub": "users, audit_log, templates", "kind": "store", "ev": [5] },
    { "id": "cfg", "label": "config-service", "sub": "customer config", "kind": "service", "service": "config-service", "ev": [7] },
    { "id": "rep", "label": "replay-service", "sub": "Retry Queue", "kind": "service", "service": "replay-service", "ev": [7] },
    { "id": "col", "label": "collector", "sub": "Transaction History", "kind": "service", "service": "collector", "ev": [7] },
    { "id": "ded", "label": "dedupe-service", "sub": "held records", "kind": "service", "service": "dedupe-service", "ev": [7] },
    { "id": "trk", "label": "tracking-service", "sub": "Order Tracker, flag", "kind": "service", "service": "tracking-service", "ev": [7] },
    { "id": "aud", "label": "audit-service", "sub": "dual-publish, dev only", "kind": "service", "service": "audit-service", "ev": [8, 9] },
    { "id": "oth", "label": "shopify-connector, ilg-secure-notes", "sub": "preview, credential link", "kind": "external", "ev": [7] }
  ],
  "edges": [
    { "from": "op", "to": "ui" },
    { "from": "ui", "to": "mongo" },
    { "from": "ui", "to": "cfg" },
    { "from": "ui", "to": "rep" },
    { "from": "ui", "to": "col" },
    { "from": "ui", "to": "ded" },
    { "from": "ui", "to": "trk", "label": "ID token" },
    { "from": "ui", "to": "aud", "label": "audit events", "style": "dashed" },
    { "from": "ui", "to": "oth" }
  ] }
```

fuse-ui calls every neighbour over HTTP with an API key, except tracking-service (Google ID token) and audit-service (Pub/Sub). Dev publishes audit events to both Mongo and audit-service. Prod and previews write Mongo only [8][9].

## Where the reference lives

[[architecture]] carries the BFF layering, auth, audit pipeline, route table and flags. [[operations]] covers deploys and previews. [[design]] holds the UI language. [[known-context]] holds interview truth and incident history.

Do not trust these:

- `README.md` is boilerplate. It describes a `/api/random-cat` route the app does not have [10].
- The repo has no `CLAUDE.md` or `AGENTS.md`.
- The Fuse MCP catalog lists "BASIC auth" as a responsibility. No load balancer or IAP auth exists. The `BASIC_AUTH_*` env pair is the admin login [11].
- [[known-context]] test counts and its checkout note predate this anchor.
- Other people edit the local checkout, so it is often dirty. Read the default branch with `git show origin/main:<path>`.

## What deliberately isn't here

- **Platform data.** Canonical records, config, failures and dedupe state belong to their owning services.
- **Customer-facing pages.** No portal exists. See the audience note above.
- **Pipeline publishing.** fuse-ui publishes only audit events. Ingress, dedupe and WMS delivery belong to the pipeline services [12].
- **Load-balancer auth.** The app checks sessions itself.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "code/package.json@ca5962f" },
  { "id": 2, "kind": "code", "ref": "code/src/app/page-header.tsx@ca5962f" },
  { "id": 3, "kind": "code", "ref": "code/src/app/customer/[customerId]/exceptions/page.tsx@ca5962f" },
  { "id": 4, "kind": "doc", "ref": "Engineering/fuse-ui/plans/FUSE-1070-template-library-storage-browse-and-crud.md" },
  { "id": 5, "kind": "code", "ref": "code/src/instrumentation.ts@ca5962f" },
  { "id": 6, "kind": "code", "ref": "code/src/proxy.ts@ca5962f" },
  { "id": 7, "kind": "code", "ref": "code/src/lib/api-client/api-client.ts@ca5962f" },
  { "id": 8, "kind": "code", "ref": "iac/projects/fuse-ui/variables.tf@ca5962f" },
  { "id": 9, "kind": "code", "ref": "iac/env/dev.tfvars@ca5962f" },
  { "id": 10, "kind": "code", "ref": "README.md@ca5962f" },
  { "id": 11, "kind": "code", "ref": "code/src/app/api/auth/login/route.ts@ca5962f" },
  { "id": 12, "kind": "code", "ref": "code/src/lib/audit/audit-publisher.ts@ca5962f" },
  { "id": 13, "kind": "code", "ref": "iac/projects/fuse-ui/iam.tf@ca5962f" }
] }
```
