---
tags:
- waypoint
- tracking-service
title: tracking-service — known context
verified: '2026-10-15'
verified_paths: []
---
# tracking-service — known context

Exempt from staleness checks: investigation and decision truth, not a claim about current
source. Re-verify a specific implementation detail against code before relying on it. The
programme record is `Bifrost/Tracking Service/` (Overview, Migration State with its decision log).

## History
- Built as a skunkworks `fuse-tracker` on 2026-10-05/06 (Go API, standalone Next.js UI on
  esm.fuse.*, stdio MCP), live in prod within days; L2 support (Jack) gave the first feedback on day three.
- Productionised as `tracking-service` (agreed 2026-10-07): new stack and Firestore database kept forever
  (the old one had a 90-day TTL), Datadog, dead letters, CI emulator job. Not done by decision: a load
  test, a server cache, PII work (later, in a fuse-ui BFF), folding the MCP into the hosted Fuse MCP.
- The standalone UI and stdio MCP were retired in #1 (2026-10-09); fuse-ui `/order-tracker` and
  fuse-mcp's `tracking-*` tools replaced them.
- Cutover: dev and prod on 2026-10-14 (held apply, Firestore export/import of 131,001 prod docs, hold
  released, dead-lettering on, parity checked against the legacy API), fuse-ui and fuse-mcp repointed
  and the legacy stack, its databases, files and migration buckets removed on 2026-10-15. There is no
  copy of the legacy database any more.

## Decisions a reader would not guess from source
- **Identity is business + customer reference** (returns: RGA number). Support searches by it, and it
  rides unchanged from the create record through Snap onto every confirmation. The Snap ShipmentId is
  derived and display-only.
- **Despatch is two-step** (`none` → `reported` → `confirmed` / `confirmation_failed`). `delivered` is
  reserved for carrier proof of delivery, which doesn't exist; the stats still remap stored `delivered`
  until that compat path is retired (programme unit B9).
- **Overdue despatch is the end of the next London working day after the WMS took the order.** `dueOut`
  plays no part: ops don't work to it, and producers send it already past (Shopify the creation day at
  17:30Z, SPORTLUX the previous midnight). Jack's call.
- **One definition per number:** a record counts once, on its first failure of each kind.
- **Goods-out `confirmation_made` is `goods_out_confirmation` from every producer** (decided 2026-10-06;
  the old `sales_order` route is dead). The fuse-mcp topology note on `confirmation_made` still says the
  made side keeps `sales_order` — one of the two is stale.
- **The tracker is the L2 work queue:** failed records link to replay's retry queue and Transaction
  History; a link is omitted, never faked, when the lookup fails.

## Fragility and scar tissue
- Counting each flip of a derived flag once turned one Saira order into 57 failures (headline 76 vs 15).
- `recompute-stats` once skipped a day whose totals matched, leaving stale per-business reason codes; it
  must diff every counter, reason code and duration bucket (`0585898`).
- Lane-filtered attention pages must read on until full: the lane filter ran after each oldest-first page
  and Running late came back empty (`e17d9b9`).
- Pushing to `main` while a Deploy run is in flight cancelled the image jobs, both times.
- The rule "a human runs backfills against prod" was broken on 2026-10-07 and lifted explicitly by Harry
  for the 2026-10-14 cutover only; it stands otherwise.
- Datadog logs carry `env:serverless`, not the environment: filter on `project_id` or
  `configuration_name`. Metrics use `environment:`.

- **2026-11-06 burst errors were Firestore index-write throttling.** 536 commits (and 486 more at 11:20Z) failed `RESOURCE_EXHAUSTED` during PURDYFIGG reap bursts, surfacing as `InvalidArgument: transaction has expired` because the gapic Commit retry reuses the dead transaction id and `RunTransaction` retries only `Aborted`. Exempting the 9 unqueried, copy-rewritten fields from indexing (D1, #18) fixed it: 0 in 48 h of heavier bursts (peak 2,859 pushes/min).
- A record remembers only its last 64 counted copy ids (`dedupe.go:22`, ~1.5–2 h of PURDYFIGG resends); an older redelivered copy counts again.
- Prod Firestore has point-in-time recovery off (`firestore.tf:9`); nothing backs up the `tracking-service` database.
- `api-emulator` is one of the required checks on `main`.

## Surprises
- PURDYFIGG's bulk reap resends every open order with new messageIds: counted as duplicates, and
  old orders arrive this way first (preexisting). It is not just nightly: on 2026-10-18 it sent about 1,200 orders every
  5 minutes, ~98% unchanged. This is by design (Harry, 2026-10-19). Shopify tags are added to an order well after it is
  created, so the connector needs a large lookback window and will always resend. tracking-service has to absorb
  identical resends cheaply; they were 78% of all ingest from 15 to 18 Oct.
- A held backlog replayed out of order picks a different Shopify duplicate as the representative
  `received` event; counts are equal (seen in the prod parity check, benign).
- A shopify-connector ingest failure embeds the raw Shopify order; `rawPayload` is never stored.

## Unknowns
- The 429s on 2026-10-09 15:00–16:00 UTC (legacy revision 00019) were never investigated. (snapshot 2026-10-15)
- Whether the fuse-mcp topology's "made keeps `sales_order`" note or this repo's decision is current for
  every goods-out producer today.
- Real failure modes on the new stack: it has run only since 2026-10-14. (snapshot 2026-10-15)
