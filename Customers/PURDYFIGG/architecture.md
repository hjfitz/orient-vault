---
tags: [customer, PURDYFIGG]
verified: '2026-09-02'
verified_against: mcp__fuse__trace-data-flow(sales_order)
title: Purdy & Figg — architecture
thesis: "Purdy & Figg orders reach Fuse through one Shopify connector on the bulk-ingest tick and land in a single SNAP warehouse. Dispatch comes back from the SNAP queue to the same connector, which fulfils the Shopify order."
confidence: moderate
---

# Purdy & Figg — architecture

```orient-bluf
{ "v": 1, "bluf": "Purdy & Figg orders reach Fuse through one Shopify connector on the bulk-ingest tick and land in a single SNAP warehouse. Dispatch comes back from the SNAP queue to the same connector, which fulfils the Shopify order.", "confidence": "moderate", "action": "Before tracing a missing order, check the connector's retrievalConditions window and the ILG_RELEASED tag. Do not look for a channel filter: none exists." }
```

Single order channel, single WMS. The Fuse core pipeline (collector, dedupe, snap-adapter) is
deliberately collapsed to one box below — it's the same for every Shopify customer and is
Waypoint's job to document (`Engineering/{shopify-connector,collector,dedupe-service,snap-adapter}`),
not this customer's. What's customer-specific here is the channel/connector shape and which WMS
it lands in — the thing that changes once we're multi-WMS.

```orient-flow
{ "v": 1, "title": "Purdy & Figg: order in, dispatch back",
  "nodes": [
    { "id": "skio", "label": "Skio", "sub": "subscription billing", "kind": "external" },
    { "id": "shop", "label": "Shopify", "sub": "purdy-figg.myshopify.com: Online Store and Skio Subscriptions channels", "kind": "external", "ev": [1] },
    { "id": "sc", "label": "shopify-connector", "sub": "bulk ingest, 5-minute tick", "kind": "service", "service": "shopify-connector", "tone": "accent", "ev": [2, 3] },
    { "id": "pipe", "label": "Fuse core pipeline", "sub": "collector, dedupe-service, snap-adapter", "kind": "external", "ev": [4] },
    { "id": "snap", "label": "SNAP", "sub": "warehouse BRACKMILLS2", "kind": "external", "ev": [1] },
    { "id": "poll", "label": "snap-queue-polling-service", "sub": "polls the outbound queue", "kind": "service", "service": "snap-queue-polling-service", "ev": [4, 5] }
  ],
  "edges": [
    { "from": "skio", "to": "shop", "label": "subscription orders" },
    { "from": "shop", "to": "sc", "label": "bulk operation" },
    { "from": "sc", "to": "pipe", "label": "create_record_request (sales_order)" },
    { "from": "pipe", "to": "snap", "label": "creates shipment" },
    { "from": "snap", "to": "poll", "label": "dispatch row" },
    { "from": "poll", "to": "sc", "label": "confirmation_ready (goods_out_confirmation)" },
    { "from": "sc", "to": "shop", "label": "marks fulfilled" }
  ] }
```

## Reading this

- **Ingress**: both Shopify channels feed the same `shopify-connector` bulk-ingest tick. The
  connector has no channel or publication filter [3], so "which channel" never
  affects delivery. Gating is entirely `retrievalConditions` (see
  [[known-context|known-context.md]]). The live conditions are paid, unfulfilled, tagged `ILG_RELEASED`, and created or updated within the last 3 hours [1].
- **Egress**: SNAP dispatch is polled by `snap-queue-polling-service` (a separate app in the
  snap-adapter monorepo, not `snap-adapter` itself), which publishes `confirmation_ready` with
  `recordType=goods_out_confirmation`. It does not pass back through the core pipeline. The
  legacy `sales_order_confirmation_ready` topic was deleted on 2026-09-16 [5]. Subscriptions now
  filter on `source` or `broadcast`, so the shopify-connector receives a Shopify-origin
  confirmation and the other connectors normally do not [3][5]. If you trace this in Datadog,
  `fapi` appears tagged `service:rest_connector`.
- **Other connectors**: production config also holds a `Main SFTP` connector and a REST `API`
  connector [1]. The SFTP connector maps `master_data`, `sales_order` and `purchase_order` and has
  `confirmationsEnabled: false`. The REST connector has no mappings and `confirmationsEnabled: true`
  with a webhook URL. **UNKNOWN** whether either carries live traffic. The diagram draws only the
  Shopify path, which is the one with sales-order and goods-out mappings.
- **WMS**: SNAP only, one warehouse (`BRACKMILLS2`). The sales-order mapping defaults the carrier to `GFS_EVRI` [6]. The multi-WMS case (a second WMS box, a
  connector or recordType routing to it) doesn't exist for any customer yet — this diagram's
  shape is the template to extend once it does.

## Open question

Unleashed is referenced by ILG's team as an upstream system for the subscription flow (Matt
Shaw asked how long subs take to reach Shopify *from* Unleashed) but its exact mechanism/role
isn't confirmed — left off the diagram rather than guessed. See `known-context.md`'s `## Unknowns`.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "log", "ref": "mcp__fuse__get-business-config(PURDYFIGG, production), 2026-10-13", "note": "three connectors, retrievalConditions, SNAP backend, confirmationsEnabled per connector" },
  { "id": 2, "kind": "doc", "ref": "Engineering/shopify-connector/architecture.md", "note": "bulk ingest tick on */5 Cloud Scheduler" },
  { "id": 3, "kind": "code", "ref": "apps/shopify-connector@e9aef9e0", "note": "grep for publication, sales channel and channel id finds nothing outside the generated GraphQL schema" },
  { "id": 4, "kind": "doc", "ref": "Engineering/snap-queue-polling-service/overview.md", "note": "polls the outbound queue and publishes confirmation_ready" },
  { "id": 5, "kind": "code", "ref": "data/pubsub-topology.json@d455b6e", "note": "fuse-mcp: legacy per-entity confirmation topics deleted 2026-09-16; confirmation_ready subscribers" },
  { "id": 6, "kind": "log", "ref": "mcp__fuse__config-read(.../connectors/conn_7ce8402090194b67b0f8a1de03019397/mappings/sales_order, production), 2026-10-13", "note": "defaults: warehouse BRACKMILLS2, carrierId GFS_EVRI, order class PURDYE" }
] }
```
