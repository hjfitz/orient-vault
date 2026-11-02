---
tags:
- system
- fuse
verified: '2026-09-24'
title: fuse — architecture
thesis: "Fuse is a loop, not a pipeline: every inbound dialect becomes a canonical record at the boundary, and Pub/Sub carries it asynchronously to the WMS and back as confirmations. Failures become records an operator can list and redrive."
confidence: moderate
---
# fuse — architecture

```orient-bluf
{ "v": 1, "bluf": "Fuse is a loop, not a pipeline: every inbound dialect becomes a canonical record at the boundary, and Pub/Sub carries it asynchronously to the WMS and back as confirmations. Failures become records an operator can list and redrive.", "confidence": "moderate", "action": "Convert to a canonical type at the boundary. Never publish a raw or connector-shaped payload, and never assume the WMS answers synchronously." }
```

The **narrative** layer: why Fuse is shaped this way, and the constraints that produced it.

> **Current state lives in the Fuse MCP, not here.** `fuse://services`, `fuse://architecture`,
> `fuse://pubsub-topology`, `fuse://canonical-types`, `fuse://api-endpoints`,
> `fuse://config-domain` are maintained and queryable. This doc must never become a second,
> staler service catalog — if a fact is "what exists and how it's shaped", query the MCP and
> link it. What belongs here is "why", which the MCP does not carry.

## The one idea

Fuse is a **canonical-first integration platform**. Every customer system speaks its own
dialect; Fuse converts at the boundary and everything downstream operates on canonical
records only. That single rule is what makes a connector addable without touching the core.

It is a **loop**, not a pipeline — that is the thing to hold onto:

```orient-flow
{ "v": 1, "title": "The loop: customer to WMS and back",
  "nodes": [
    { "id": "cust", "label": "Customer", "kind": "external" },
    { "id": "ing", "label": "Ingress", "sub": "sftp-connector, shopify-connector, fapi", "kind": "external", "ev": [1] },
    { "id": "ded", "label": "dedupe-service", "kind": "service", "service": "dedupe-service", "ev": [1] },
    { "id": "adp", "label": "snap-adapter", "kind": "service", "service": "snap-adapter", "ev": [1, 2] },
    { "id": "wms", "label": "SnapFulfil WMS", "kind": "external" },
    { "id": "pol", "label": "snap-queue-polling-service", "kind": "service", "service": "snap-queue-polling-service", "ev": [2] },
    { "id": "egr", "label": "Egress", "sub": "fapi, sftp-connector, shopify-connector", "kind": "external", "ev": [1] },
    { "id": "rpl", "label": "replay-service", "sub": "failure inbox", "kind": "service", "service": "replay-service", "tone": "alert", "ev": [1, 3] }
  ],
  "edges": [
    { "from": "cust", "to": "ing", "label": "file, webhook, API" },
    { "from": "ing", "to": "ded", "label": "create_record_request" },
    { "from": "ded", "to": "adp", "label": "create_record" },
    { "from": "adp", "to": "wms", "label": "create" },
    { "from": "wms", "to": "pol", "label": "outbound queue" },
    { "from": "pol", "to": "egr", "label": "confirmation_ready" },
    { "from": "egr", "to": "cust", "label": "webhook, file" },
    { "from": "adp", "to": "rpl", "label": "create_data_failure", "style": "dashed" },
    { "from": "egr", "to": "rpl", "label": "confirmation_data_failure", "style": "dashed" }
  ] }
```

Two things the diagram deliberately leaves out, because drawing them buries the shape:

- **config-service feeds the hops that resolve per-customer config.** Which connector, which mapping, which WMS credentials. It publishes `config_revision` to fapi, sftp-connector, shopify-connector, snap-adapter, dedupe-service, collector and wms-gateway [1]. The poller reads backends from it through remote-config [4]. replay-service has no config subscription [1]. It is ambient, not a step in the flow.
- **collector observes without participating.** It records what happened for Transaction History and never sits in the path.

The dashed edges are the interesting ones: a failure becomes a **queryable record**, not a lost message. snap-adapter publishes `create_data_failure` and the egress connectors publish `confirmation_data_failure`. replay-service stores both [1][3]. A replay re-enters the loop at `create_record_request` or `confirmation_ready`, so it passes through dedupe-service again [3].

## A record's journey

The thing newcomers get wrong is assuming ingress→WMS is synchronous. It is not: every hop is
Pub/Sub, and the WMS answers on its own schedule via a polled queue. The poller, not snap-adapter, clears the queue row, once its publish resolves [4].

```orient-sequence
{ "v": 1, "title": "One record, create to confirmation",
  "actors": [
    { "id": "c", "label": "Customer" },
    { "id": "i", "label": "Ingress connector" },
    { "id": "d", "label": "dedupe-service", "service": "dedupe-service" },
    { "id": "a", "label": "snap-adapter", "service": "snap-adapter" },
    { "id": "w", "label": "SnapFulfil" },
    { "id": "p", "label": "snap-queue-polling-service", "service": "snap-queue-polling-service" },
    { "id": "e", "label": "Egress connector" }
  ],
  "steps": [
    { "from": "c", "to": "i", "label": "file, webhook or API call", "kind": "call", "note": "The connector converts to canonical at the boundary." },
    { "from": "i", "to": "d", "label": "create_record_request", "kind": "async", "ev": [1] },
    { "from": "d", "to": "a", "label": "create_record, new records only", "kind": "async", "note": "A repeat is held, not dropped. Nothing goes back to the connector.", "ev": [1] },
    { "from": "a", "to": "w", "label": "keyed create over HTTP", "kind": "call", "ev": [2] },
    { "from": "w", "to": "a", "label": "accepted", "kind": "return" },
    { "from": "p", "to": "w", "label": "poll outbound queue, every 2 minutes", "kind": "call", "note": "The warehouse progresses the order on its own schedule.", "ev": [4] },
    { "from": "w", "to": "p", "label": "queue rows", "kind": "return" },
    { "from": "p", "to": "e", "label": "confirmation_ready", "kind": "async", "ev": [1] },
    { "from": "p", "to": "w", "label": "clear the row after the publish resolves", "kind": "call", "ev": [4] },
    { "from": "e", "to": "c", "label": "webhook, file or Shopify fulfilment", "kind": "call" }
  ] }
```

**Why the deduper is a gate, not a filter.** A customer resending the same file is normal, not
an error. Holding the duplicate (rather than dropping it) keeps a release path: clearing the
held record lets a legitimate resend through. See `dedupe-*` in the MCP tooling.

After a successful create, snap-adapter publishes `create_acknowledge`. The sftp and shopify connectors and the collector consume it [1].

## Configuration is a hierarchy, not a bag

Nearly every "why is this customer behaving differently" question resolves here.

```orient-flow
{ "v": 1, "title": "The configuration hierarchy",
  "nodes": [
    { "id": "biz", "label": "Business", "sub": "businessId, caller-supplied", "kind": "store", "tone": "accent", "ev": [5] },
    { "id": "be", "label": "Backend", "sub": "WMS host and credentials, one per business", "kind": "store", "ev": [5] },
    { "id": "sf", "label": "Storefront", "sub": "one per sales channel or region", "kind": "store", "ev": [5] },
    { "id": "cn", "label": "Connector", "sub": "sftp, shopify or rest", "kind": "store", "ev": [5] },
    { "id": "mp", "label": "Mapping", "sub": "at most one per use case", "kind": "store", "ev": [5] },
    { "id": "dc", "label": "Dictionary", "sub": "lookup tables on the mapping", "kind": "store", "ev": [6] }
  ],
  "edges": [
    { "from": "biz", "to": "be", "label": "WMS credentials" },
    { "from": "biz", "to": "sf", "label": "has many" },
    { "from": "sf", "to": "cn", "label": "has many" },
    { "from": "cn", "to": "mp", "label": "per use case" },
    { "from": "mp", "to": "dc", "label": "has many" }
  ] }
```

Build order matters: business, then backend (nothing reaches the WMS without it), then storefront, connector and mapping. Shipment methods, warehouse routing, DDP rules and the SKU blacklist hang off the business and need no storefront [5]. `fuse://config-domain` and
`lookup-config` carry the live shape, fragments, cache keys and handler patterns.

## Failure has a front door

A failure the services classify is a record you can list, inspect and redrive:

- **dedupe-service** holds duplicates (`dedupe-list` / `dedupe-release`).
- **replay-service** holds pipeline failures (`replay-list-failures` / `replay-retry`), and can
  say whether a retry would pass the canonical gate before you try.

This is deliberate: a manual retry budget was chosen over Pub/Sub DLQs so that a human (or an
agent) can see *why* something failed and decide, rather than watching messages disappear.

The front door does not cover delivery that exhausts its retries. replay-service's three dead-letter topics have no consumer, though a monitor alerts a human [7]. The `create_record` dead-letter topic has no consumer either, and the team has confirmed that a bad enough snap-adapter outage can lose orders [8]. dedupe-service subscriptions have no dead-letter topic, so a nacked message loops until the 7-day retention expires [9].

## What has no home yet

- **No cancellation or amendment path.** An order, once created, cannot be withdrawn through
  Fuse. Customers ask; the answer today is out-of-band.
- **Stock is read-only and incomplete.** wms-gateway serves stock reads inside the platform. fapi's stock routes return 501 until a wms-gateway proxy lands [10].

## Member services

Derived from each service's own `waypoint.yaml`, never listed here — run `wp system status fuse`.
Grouped: 17 backend, 2 frontend ([[fuse-ui]], [[distraction-dashboard]]), 4 infra, 1 library
([[pkg-node]]) [11].

Shared UI and CI come from the **[[ilg-platform]]** system, not from Fuse — see its docs for
`@ilg-platform/ui-toolkit` and the reusable workflows every Fuse repo pins.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "data/pubsub-topology.json@d455b6e", "note": "fuse-mcp: topic publishers and subscribers" },
  { "id": 2, "kind": "doc", "ref": "Engineering/snap-adapter/overview.md", "note": "write side; publishes acknowledge, failure and release" },
  { "id": 3, "kind": "doc", "ref": "Engineering/replay-service/architecture.md", "note": "inbound failure topics and outbound redrive topics" },
  { "id": 4, "kind": "doc", "ref": "Engineering/snap-queue-polling-service/overview.md", "note": "polls every 2 minutes, clears each row after its publish" },
  { "id": 5, "kind": "code", "ref": "data/config-domain.json@d455b6e", "note": "customerSetup: hierarchy and setupOrder" },
  { "id": 6, "kind": "doc", "ref": "~/code/CLAUDE.md", "note": "types 10.3.0: dictionaries sit on the mapping config" },
  { "id": 7, "kind": "doc", "ref": "Engineering/replay-service/known-context.md", "note": "DLTs unconsumed but monitored" },
  { "id": 8, "kind": "doc", "ref": "Engineering/snap-adapter/known-context.md", "note": "no consumer on the create_record dead-letter topic" },
  { "id": 9, "kind": "doc", "ref": "Engineering/dedupe-service/architecture.md" },
  { "id": 10, "kind": "doc", "ref": "Engineering/fapi/overview.md", "note": "stock routes return 501" },
  { "id": 11, "kind": "doc", "ref": "Engineering/*/waypoint.yaml", "note": "services declaring system: fuse, scanned 2026-10-13" }
] }
```
