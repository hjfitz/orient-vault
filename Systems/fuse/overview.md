---
tags:
- system
- fuse
verified: '2026-09-24'
title: fuse — overview
thesis: "Fuse converts every customer's orders, stock and master data into canonical records, routes them into the SnapFulfil WMS, and sends confirmations back in the customer's own shape. Onboarding customer N+1 is configuration, not code."
confidence: moderate
---
# fuse — overview

```orient-bluf
{ "v": 1, "bluf": "Fuse converts every customer's orders, stock and master data into canonical records, routes them into the SnapFulfil WMS, and sends confirmations back in the customer's own shape. Onboarding customer N+1 is configuration, not code.", "confidence": "moderate", "action": "Publish canonical shapes only. Never put a raw webhook, file row or vendor object on the event bus." }
```

**What it is.** The integration platform between ILG's customers and the SnapFulfil WMS.
A customer sends orders, stock and master data in whatever shape they already have; Fuse
normalises it, routes it into the warehouse, and sends confirmations back out in the shape
that customer expects.

**Who it serves.** Retail/e-commerce brands fulfilled by ILG. Day to day, the people in front
of it are ILG support and ops staff — which is why the UI is built for someone who did not
write it (see [[fuse-ui]]'s `design.md`).

**Why it exists.** Before Fuse, each customer integration was bespoke. The canonical-first
rule ([[fuse]] `architecture.md`) exists so that onboarding customer N+1 is configuration,
not code.

## The shape at a glance

```orient-flow
{ "v": 1, "title": "Fuse at a glance",
  "nodes": [
    { "id": "cust", "label": "Customers", "sub": "retail and e-commerce brands", "kind": "external", "ev": [5] },
    { "id": "ing", "label": "Ingress and egress", "sub": "sftp-connector, shopify-connector, fapi", "kind": "external", "ev": [1] },
    { "id": "core", "label": "Core", "sub": "dedupe-service, replay-service, collector, config-service", "kind": "external", "tone": "accent", "ev": [1] },
    { "id": "wms", "label": "WMS edge", "sub": "snap-adapter, snap-queue-polling-service", "kind": "external", "ev": [1, 6] },
    { "id": "snap", "label": "SnapFulfil", "sub": "vendor WMS", "kind": "external", "ev": [4] },
    { "id": "ui", "label": "Surfaces", "sub": "fuse-ui, distraction-dashboard", "kind": "external", "ev": [3] },
    { "id": "found", "label": "Foundations", "sub": "pkg-node, bifrost-pubsub, core-infra", "kind": "external", "ev": [2] }
  ],
  "edges": [
    { "from": "cust", "to": "ing", "label": "files, webhooks, API" },
    { "from": "ing", "to": "core", "label": "create_record_request" },
    { "from": "core", "to": "wms", "label": "create_record" },
    { "from": "wms", "to": "snap", "label": "create, poll queue" },
    { "from": "wms", "to": "ing", "label": "confirmation_ready" },
    { "from": "ing", "to": "cust", "label": "confirmations" },
    { "from": "ui", "to": "core", "label": "operate, configure" },
    { "from": "found", "to": "core", "label": "types, topics, infra", "style": "dashed" }
  ] }
```

Eight members sit outside these groups. `wms-gateway` serves stock reads. `audit-service` stores the audit trail. `fuse-mcp`, `fuse-mocker`, `snap-mcp` and `fuse-devtools` are agent and developer tooling. `observability` and `ilg-secure-notes` are standalone [2].

## Where to look for what

| Question | Go to |
| --- | --- |
| What exists, what shape is it, who publishes what | **Fuse MCP** — `fuse://services`, `fuse://pubsub-topology`, `fuse://canonical-types` |
| Why is it shaped this way | [[fuse]] `architecture.md` (this system) |
| How does *one* service work | `Engineering/<service>/` — overview, architecture, operations |
| Why is *this customer* different | `Customers/<BUSINESSID>/known-context.md` |
| What is in flight | `wp fleet`, `wp status`, orient `/work` |
| What shipped | orient `/ledger` |
| Shared UI / CI / IaC | the **[[ilg-platform]]** system |

## Boundaries

**In scope:** order, stock, master-data and confirmation flow between a customer and the WMS;
the config that makes one customer differ from another; the operational surfaces over it.

**Out of scope:** the WMS itself (SnapFulfil is a vendor product — we integrate, we do not
control its release schedule or its data model); shared platform surfaces, which belong to
[[ilg-platform]]; anything customer-commercial.

## Standing constraints

- **SnapFulfil is a vendor system.** Prod upgrades arrive with no advance notice, and its API
  has irregularities that are designed behaviour rather than bugs (a kit explodes into
  component lines on despatch; some write failures return HTTP 2xx with an error body).
- **One customer per invocation.** No cross-customer batching, anywhere.
- **The event bus carries canonical shapes only** — never a raw webhook or a vendor object.

Members: `wp system status fuse`.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "data/pubsub-topology.json@d455b6e", "note": "fuse-mcp: publishers and subscribers per topic" },
  { "id": 2, "kind": "doc", "ref": "Engineering/*/waypoint.yaml", "note": "services declaring system: fuse, scanned 2026-10-13" },
  { "id": 3, "kind": "doc", "ref": "Engineering/fuse-ui/design.md" },
  { "id": 4, "kind": "doc", "ref": "Systems/fuse/known-context.md" },
  { "id": 5, "kind": "doc", "ref": "~/code/CLAUDE.md", "note": "canonical-first, single-customer and event-bus rules" },
  { "id": 6, "kind": "doc", "ref": "Engineering/snap-queue-polling-service/overview.md" }
] }
```
