---
tags: [sprint-digest]
sprint_closed: Sprint 14
sprint_closed_window: 2026-07-27 → 2026-09-16 (nominal end 2026-08-10; stayed open ~5 extra weeks before being closed)
sprint_started: Sprint 15
sprint_started_window: 2026-09-16 → 2026-10-07
posted: '2026-09-16'
channel: bifrost-general (C098LD5PS95)
title: Sprint 14 → Sprint 15 boundary digest
---

# Sprint 14 → Sprint 15 boundary digest

Sprint 14 ran far past its nominal 2026-08-10 end before Harry closed it on 2026-09-16 and started
Sprint 15 fresh (overflowing incomplete Sprint 14 work into it). All Sprint 14 delivery figures below
use the real ~7-week open window (2026-07-27 → 2026-09-16), not the nominal 2-week one.

- Retro post: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1789555932736149
- Look-ahead post: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1789555939728339

---

## Post 1 — Sprint 14 retro (2,777 chars)

**Sprint 14 wrapped** (27 Jul → 16 Sep — stayed open longer than usual before being closed today).

### 📊 At a glance
- 430 PRs merged — plus 113 automated dependency updates
- 87 tickets delivered this window
- 5 epics delivered — Work Order Flow, Shopify Bulk Order Ingest, Smart Routing of Confirmations, Mapping Template Library, Customer Transaction History
- 4 production incidents this window (1 high, 1 medium, 2 low) — one still under investigation
- fuse.* operational metrics now instrumented fleet-wide
- 3 new customers onboarded — Escentric Molecules, Purdy & Figg, Manucurist

### 📈 Reliability in production
- Outbound warehouse calls: 23,125 successful Snap submissions against 47 failures (99.8%)
- Warehouse polling: 310,138 successful reads against 327 failures (99.9%)
- API gateway (api-gateway/rest_connector only): 41,378 successful requests against 1,137 failures (~2.7%)
- New confirmation routing forwarded 14,618 confirmations successfully against 66 failures (99.5%)
- 4 incidents: a SnapFulfil vendor upgrade with no advance warning, a dropped-adjustment issue affecting two customers' stock accuracy, a stuck confirmation retry loop, and an ongoing latency investigation

### 🚀 What went out
Work Orders join sales and purchase orders as a full Fuse capability (create + WOC + FGR, SFTP/API) · Confirmations route only to the originating channel instead of broadcasting, with a manual-origin broadcast opt-in · Shopify bulk order ingest rebuilt for scale (FSM/reap lane, Mongo ledger+watermark+lease) · ILG-managed, copy-on-apply mapping templates replace the old code-managed ones.

### ⚙️ Engineering nuggets
- Slot-timeout misclassified as permanent → deduper released and re-PUT live shipments every 5 min, duplicating kit lines (FUSE-1147)
- SNAP 500 misclassified as retryable → infinite Pub/Sub redelivery loop (FUSE-1085)
- Dedupe acked create-request messages before processing — a downstream failure could silently lose the record (FUSE-1104)
- Confirmation-claim Redis key omitted businessId — cross-tenant collision risk (FUSE-1176)
- Work Order create pipeline: shipped, broke, reverted, fixed, relanded (FUSE-857)
- fuse-mcp Go rewrite shipped live behind a 0%-traffic weighted LB split

---

## Post 2 — Sprint 15 look-ahead (1,438 chars)

**Sprint 15 is underway** (16 Sep → 7 Oct).

### 🚀 What Fuse gains this sprint
**Shopify stock sync, scheduled and on demand** _(18 tickets, epic FUSE-658)_ — Jitterbit-parity scheduled/on-demand full stock republish per SKU, recovering from the gaps event-driven Stock Adjustments alone can't close (cancellations, failed deliveries, part-shipments, outages).

**A native Get Stock API** _(9 tickets, epic FUSE-792)_ — Jitterbit-parity read-only stock endpoint (products + kits) via a new standalone WMS read-gateway service that fapi proxies to.

### ⚙️ Engineering nuggets
- Get Stock API gets a dedicated standalone read-gateway rather than living in fapi — keeps live SNAP creds + concurrency protection off the public edge
- Kit availability is a derived quantity (assemblable from component stock), not stored
- Stock sync ships a brand-new NestJS egress service + a Shopify workspace/package unification (ShopToken extraction) riding alongside

---

## Evidence

- **Sprint boundary**: openSprints() returned only Sprint 14 (still `active`, ~7 weeks past its nominal 2026-08-10 end) until Harry closed it and started Sprint 15 today. Confirmed via re-query after closure: Sprint 14 now `closed`, Sprint 15 `active` (2026-09-16 → 2026-10-07, id 2162).
- **Sprint 15 board**: 82 issues — 36 To Do (24 Ready for Refinement + 12 Ready for Development; 2 more sat in bare Backlog, not investigated), 20 in-flight/QA, 22 Won't do (breakdown not investigated), 2 Done. All 36 To Do items were in a sprint for the first time except FUSE-1186 (sprint count 2, carried Collector businessId-scoping fix).
- **Look-ahead scope note**: the "dictionaries"/lookup() DSL batch (FUSE-1215/1216/1217/1220/1221/1222, 6 tickets) was originally in Sprint 15's To Do but Harry moved it to a new **"Sprint 15 Stretch"** sprint (state: future) mid-session — confirmed live via JQL before excluding it from the look-ahead. Not published as committed work.
- **Sprint 14 delivery** (real window 2026-07-27 → 2026-09-16): 89 tickets changed to Done/QA — 66 Done, 21 reached QA; published as one merged "87 tickets delivered" figure at Harry's request (dropped the Done/QA split), which nets to 87 after reconciling against the epic-level rollup used for the "5 epics delivered" line. 2 tickets kicked back to Rework Required (FUSE-1050 RGA mapping — supersedes the prior "In QA" status in memory; FUSE-1010 multi-parcel tracking) — excluded from delivered count, not published.
- **PRs**: 543 merged in the 7-week window (430 human / 113 bot), vs ~120-190 human per normal 2-week sprint — expected given the elongated window. By repo: shopify-connector 66, fuse-ui 53, snap-adapter 48, dedupe-service 46, observability 38, pkg-node 29, sftp-connector 28, fapi 23, fuse-mcp 23, replay-service 20, collector 19, config-service 13, others <10. By author: harry-fitzgerald 248, harry-humby 80, matt-shaw 59, nylah-klasson 21, schuster-efigenio 20, kyle-chandler 2.
- **Incidents**: 5 total org-wide in window, 4 Fuse (team tag Bifrost) — INC-36 (P1, SnapFulfil unannounced prod upgrade), INC-35 (P3, SPORTLUX ingest + audit degraded collector latency, still open/undocumented as of posting), INC-34 (P2, Shopify rejected stock-adjustment requests, SAIRA/PURDYFIGG), INC-33 (P3, shopify-connector confirmation retry loop, SAIRA). INC-32 (cert expiry) excluded — ECM/SRE, not Bifrost.
- **Datadog** (`environment:prod`, 2026-07-27→2026-09-16): `fuse.request` 185,084 (component breakdown doesn't fully reconcile, see withheld) · `fuse.request.success` 41,378 · `fuse.request.failure` 1,137 (dev 1,120, both nonzero) · `fuse.request.rejected` 60,781 (dev 73,479) · `snap_adapter.snap.request` 23,125 ok / 47 fail (dev 2,379/1,015) · `snap_polling_service.snap.request` 310,138 ok / 327 fail (dev 524,019 ok / no dev failure series) · confirmation routing: published 34,489, forward.success 14,618, forward.failure 66, manual_origin_broadcast 403, unroutable 23,239 (reason breakdown not available, not published).

## Withheld figures — reported to Harry, deliberately not published

1. **`fuse.request.rejected` still exceeds accepted volume** (60,781 rejected vs 41,378 success) — the same anomaly flagged in the Sprint 13→14 digest, still unresolved two sprints later. **Open action: actually investigate this, not just re-flag it.**
2. **Confirmation-routing `unroutable` count (23,239)** — large relative to `published` (34,489), but a mixed bucket including legitimate non-error states (e.g. webhook-less connectors); no reason-code breakdown available. Publishing the raw count would misleadingly read as a failure rate.
3. **`fuse.request` total (185,084) doesn't reconcile** against success+failure+rejected (103,296) — ~82K unaccounted for, likely retries or an uncounted request phase. Not published as a clean total for this reason.
4. **`dedupe_service.event.handled`** — skipped entirely per the standing gotcha (unexplained step-change 30 Jun + no `environment` tag); still unusable for any comparison.
5. **Two tickets kicked back to Rework Required this window**: FUSE-1050 (RGA confirmation mapping — memory said "In QA", now stale, needs updating) and FUSE-1010 (multi-parcel tracking).
6. **INC-35** (SPORTLUX/collector latency) still open and undocumented as of posting — the retro only gestures at it as "an ongoing investigation."
7. Didn't dig into the 22 "Won't do" items this sprint or the 2 Sprint-15 tickets sitting in bare "Backlog" status — flagged as unresearched, not as a finding.
