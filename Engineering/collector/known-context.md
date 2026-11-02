---
tags: [waypoint, collector]
verified: '2026-09-23'
verified_paths: []
title: collector — known context
---

# collector — known context

## Forked from dedupe-service, and the seams show

The service does **no deduplication** — it's a pure read-model/observer —
but it was forked from dedupe-service and several names never got cleaned
up: `code/package.json`'s `name` is still `@dedupe/core`; the metrics module
still carries a `// dedupe specifics` block with names like
`collector_service.dedupe.new_record_added` (which actually fires on every
upsert — nothing to do with dedup), `…event.duplicate`, `…event.fresh`,
`…dedupe.skipped`. Most of these are dead — never incremented. Don't infer
behaviour, and don't build alerts, from the dedupe-shaped names; check
`observability/metrics.ts` for what's actually wired.

## The root README is inert boilerplate

`README.md` is the untouched "Repository Template" scaffold — `.nvmrc`,
`on-pr.yaml`, `pnpm run dev`, `PROJECT_ID` placeholders, none of which exist
in this repo. `CLAUDE.md` is the trustworthy doc here; it's held to a
standing "update in the same PR" discipline and is (mostly — see below)
current.

## CLAUDE.md is current but for one imprecise claim

`CLAUDE.md` is held to a same-PR update rule and, checked against `master`
(2026-09-23), lists every ingest route, all six confirmation types and the
reference search. Its earlier pick/pack drift is fixed. One claim is still
imprecise: it says `Collection.save`'s `$set` "overwrites the whole document",
but it replaces top-level keys only (see [[architecture]] → Persistence). Still
grep-verify any single "only resolves for X/Y" claim before relying on it for
something that matters.

## Work orders, WOC and FGR are collected now

Once a known gap. Work orders arrive off `create_record_request`, and WOC/FGR
off `confirmation_ready` / `confirmation_made` / `confirmation_data_failure`.
All three are readable on `api/v1/records` along with pick/pack. What remains
untapped is work-order lifecycle past `pending` (no ack, failure or release
subscription); [[architecture]] → "Still not tapped" is the current list.

## "Order Ref 1/2/3" come from the ILG CSV confirmation spec

When support quotes "Order Ref 1/2/3", the names come from the ILG CSV
confirmation spec, not any Confluence doc:
- goods-out: OrdRef1 = `customerRef`, OrdRef2 = `salesOrder`, OrdRef3 = `customerOrder`;
- goods-in: OrdRef1 = `supplierRef`, OrdRef2 = `purchaseOrder`.

That's the mapping behind each type's reference-search fields.

## A correlation id only finds a record's latest ingest

Every document stores `metadata.correlationId`, but a re-ingest overwrites it
(latest write wins). On 2026-09-23 a GADG Shopify order kept one `_id` while
carrying three correlation ids in about an hour. So a correlation id copied
from an older log line can find nothing through reference search, even though
the record exists. Search by the order reference instead.

## RGA's asymmetric topic sourcing is deliberate, not an inconsistency

RGA is the one record type collected off the **post-dedupe**, cross-entity
`create_record` topic (filtered on `attributes.recordType`) rather than a
pre-dedupe `create_<type>_request` topic like PO/SO/MD. This follows the
org's cross-entity-topic convention (subscription-level filter, never
app-side) — RGA didn't get its own dedicated ingress-request topic the way
PO/SO/MD did. Don't try to add a `create_return_goods_authorization_request`
topic to "fix" this; the asymmetry is the platform's cross-entity pattern
working as intended.

## The 204-ACK-drop is intentional, but easy to mistake for a bug

A malformed or undecodable Pub/Sub event returns HTTP 204 (an ACK, not a
NACK) and is silently dropped — no retry, no dead-letter. This is a
deliberate "don't wedge the pipeline on bad input" choice, but it means a
real ingestion bug can look like nothing happened rather than throwing
loudly. If a record you expect to see in collector is missing, check for a
`decode-error` log line or an `errors.zod_validation` spike before assuming
the publisher never sent it.

## Ownership

Owned by the Bifrost/Fuse team — same team, same on-call model as the rest
of the Fuse platform (no separate ownership split for collector
specifically). No standout production incidents or fragility reported
beyond what's already documented in [[architecture]] (the malformed `push:`
trigger on the black-box CI workflow; the legacy in-memory pagination is gone).

## Unknowns

- Index headroom on the prod M10 as data grows. Reference search added about 50
  indexes across the 12 served collections. Size wasn't measured at rollout
  (snapshot 2026-09-23).
