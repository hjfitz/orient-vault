---
ticket: FUSE-1239
title: multi-field reference search on the v1 records API
service: collector
status: complete
created: '2026-09-23'
updated: '2026-09-23'
repo: /home/hjf/code/fuse/collector
worktree: /home/hjf/code/fuse/collector/.claude/worktrees/fuse-1239-reference-search
branch: hjf/fuse-1239-serve-confirmations
base: origin/master
base_sha: 096e55e
pr: '110'
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: high
---
# FUSE-1239 — multi-field reference search on the v1 records API

<!-- Guidance in this file is written as HTML comments: Obsidian hides them, agents read them,
     and `wp signoff` ignores them. Only <angle spans> are treated as unfilled placeholders, so
     they mark the places a human or agent must actually type something. Leave the comments in
     place — deleting them costs the next reader the guidance and gains nothing at the gate.

     SUPERSEDING A STATEMENT. This file is edited by several sessions over days. When something
     here stops being true, do NOT strike it through, delete it, or bury a correction inside it.
     Put one blockquote immediately ABOVE the stale text and leave the text alone:

         > SUPERSEDED 2026-09-04 — the monitor now lives in `gfs-bifrost/observability`.
         > Everything below is kept as the record of how it was first built here.

     One marker, always above, never inside. `wp decide` writes the dated entry in
     `## Decisions & deviations` that explains why. -->

## Intent
<!-- What we are changing and why. Link the ticket. -->
[FUSE-1239](https://globalfreight.atlassian.net/browse/FUSE-1239) — backend half of multi-field
Transaction History search (UI half: FUSE-1240, planned separately in `fuse-ui`). ILG support can't
find a record by the reference a customer quotes — the most frequent support ask in
`#bifrost-general` over 2026-09-09..23. Add one `?reference=` param to
`GET /api/v1/records/:recordType/:businessId` that exact-matches a value against every reference
field held for that record type — Record ID, Correlation ID, Reference, Customer Order, SO number —
without reintroducing the Atlas Query Targeting alert that #95/#98 fixed. Proven when a real
reference finds its record on dev and the find and count query plans are index-only for both a
unique and a bulk-shared value.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. Given a value, the route returns the records of the requested type for that business that
      match on **any** of that type's declared reference fields.
- [x] 2. A value matching more than one field (on one record or across records) returns every match,
      each record once — no field takes silent precedence.
- [x] 3. No match returns HTTP 200 with `{ total: 0, count: 0, data: [] }`, not an error.
- [x] 4. Invalid input (non-string, repeated, blank, over 256 chars) is rejected with 400 before it
      reaches Mongo — `?reference[$ne]=x` in particular never becomes a Mongo operator.
- [x] 5. Both halves of the paginated query stay index-only: find resolves by sorted merge with no
      `COLLSCAN` and no blocking sort, and count examines 0 documents, for a unique and a bulk-shared
      value, on Mongo 7.0 and 8.0.
- [x] 6. Paging a search whose matches share a `lifecycle.createdAt` returns every match exactly once.
- [x] 7. A leading `#` is ignored in both directions: `11435` finds a record holding `#11435`, and
      `#11435` finds one holding `11435`.
- [x] 8. Every record the v1 list and single-record routes return carries its `correlationId`.
- [x] 9. Pick, pack, work-order confirmations and finished-good receipts are listed (index-covered,
      newest-first) and fetched by `_id` on the v1 records API, scoped to the business, with lifecycle,
      and searchable like every other type.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `code/src/http/controllers/records.controller.ts` — new `reference` query param + Swagger decl.
  Contract consumed by fuse-ui's generated collector client (codegen reads dev `/api-json`).
- `code/src/http/pipes/` — new `ReferenceSearchPipe` (pattern: `MaxCountPipe`, `ObjectIdPipe`).
- `code/src/core/use-cases.service.ts` — `listRecordsWithLifecycle` / `resolveRecordType()` (from #104).
- `code/src/core/reference-search.ts` (new) — per-type field → index derivation and branch builder.
- `code/src/models/use-case-registry.ts` — optional `referenceSearchFields` on `UseCaseDefinition`.
- `code/src/core/use-case-registry.service.ts`, `code/src/core/confirmation-registry.service.ts` —
  per-type field declarations; the `new Collection(db, name, [indexes])` arg is the single index source.
- `code/src/repositories/collection.ts` — a read path for pre-scoped branch queries that does not
  wrap them in `withNotDeleted`'s `$and`.
- `code/src/scripts/` — `ensure-indexes` (pattern: `backfill-lifecycle`).
- Collections (8 served by the records API): `sales_orders`, `purchase_orders`, `master_data`,
  `stock_adjustments`, `return_goods_authorizations`, `work_orders`,
  `purchase_order_confirmations`, `sales_order_confirmations` — ~20-25 new indexes total; increment 5
  adds `pick_confirmations`, `pack_confirmations`, `work_order_confirmations`,
  `finished_good_receipts` (list index + search family each).
- `CLAUDE.md` (repo root, not `code/`) — index family, pre-build step, where the list lives.
- Fuse MCP: `fuse-mcp-server/data/api-endpoints.json` (collector v1 records list entry).
- See [[architecture]] "Persistence & upsert semantics" / "Query API gotchas" and
  [[fix-unpaginated-list-routes-causing-atlas-query-]] (the #98 index-coverage fix this must not regress).

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- Support's "Order Ref 1/2/3" come from the ILG CSV confirmation spec (sftp-connector
  `sales-order.transformer.ts:27-30`, `purchase-order.transformer.ts:12-13`) — traced; no Confluence
  doc defines them (Denis's 12 Aug notes not found).
- Per-type business fields (Reference / Customer Order / SO number), paths verified against
  `@gfs-bifrost/types` 10.2.0 and sampled data:
  - sales_order: `order.customerRef` / `customer.order` / `identifiers.salesOrder`
  - goods_out_confirmation: `order.customerRef` / `order.customerOrder` + `customer.order` (both
    from `shipment.CustomerOrder`) / `order.salesOrder`
  - work_order: `workOrder.customerRef` / — / `identifiers.salesOrder`
  - purchase_order: `supplier.reference`, `identifiers.purchaseOrder` (equal in 43/43 prod POs —
    indexed anyway as the OrdRef2 equivalent)
  - goods_in_confirmation: `order.supplierRef`, `order.purchaseOrder`
  - return_goods_authorization: `identifiers.businessRgaNumber`; stock_adjustment: `identifiers.reference`
  - master_data: none beyond Record ID
- Multi-field matters in prod: STUBBLE `customerRef` ≠ `salesOrder` in 100/100 newest SOs;
  PURDYFIGG/SAIRA carry three distinct values in 100/100 — Fuse MCP prod sample, 2026-09-23.
- Stored refs carry no leading/trailing whitespace (0/400 prod SOs) — so trim the input, match exact.
- Correlation ID is already persisted as `metadata.correlationId` (`Collection.save` `$set`s the
  envelope, `collection.ts:110`), latest-write-wins, stripped by both read surfaces — source read.
  Resubmissions overwrite it; original ids are unrecoverable. Latest-only needs no backfill.
- One fapi bulk request shares one correlation id across every record (`bulk-ingest.service.ts:144`),
  and `confirmation_ready`/`stock_adjustment_ready` are bulk — so high-fanout correlation matches are
  normal on every collection, not an edge case.
- Query shape: top-level `$or` with `bizKey` and `deletedAt: null` inside every branch is index-only
  for find (SORT_MERGE) and count (0 docs) including a 1,500-record shared value; the nested
  `$and:[{bizKey, $or}, {deletedAt:null}]` form fetches the whole business on the bulk count, and
  `withNotDeleted`'s `$and` wrapper around the top-level form causes a blocking sort on 7.0 —
  throwaway mongodb-memory-server experiment on 7.0.24 and 8.2.6 (scratchpad `sortmerge-exp.js`).
  **Not yet run on 8.0.x**, which is what prod Atlas runs (`mongo.tf`) — increment 1 closes this.
- The `_id` branch forces a blocking sort (no sorted merge across it). Acceptable because it's only
  added when the value is 24-hex and matches at most one record; fapi correlation ids are UUIDs, so a
  24-hex value is not expected to also be a bulk correlation id — inferred, not measured.
- Express 4.21.2's extended query parser turns `?reference[$ne]=x` into `{ $ne: "x" }` and a repeated
  param into an array — tested against the app.
- Scale: largest prod business PURDYFIGG 29,164 SOs (STUBBLE 26,172); staging GADG 81,577 — Fuse MCP.
- Prod Atlas is 8.0 LTS on M10 (2 GB RAM, autoscale to M20, 10 GB disk) — `mongo.tf`; index-size
  headroom unmeasured.
- `ensureIndexes()` runs in `onModuleInit`, inside `app.listen()` before the port binds; the startup
  probe is `/health/liveness` on default timings (~30s, `cloud-run.tf:97`) — so a slow build fails the
  deploy rather than serving unindexed queries.
- Indexes are never dropped by the app, so prod holds superseded indexes a fresh memory-server lacks
  (old 2-field list indexes, pre-FUSE-1165 `identifiers.id`-keyed ones) — the CI planner test can't see
  them; only a live explain can.
- The upsert-key indexes (`{businessId, order.customerRef}` SO, `{businessId, supplier.reference}` PO,
  `{businessId, businessRgaNumber}` RGA) stay — ingest depends on them (`CLAUDE.md` L147-176).
- RESOLVED 2026-09-23 (Harry) — **Record ID scope:** match the fields fuse-ui's Record ID column can
  actually display — its per-type `refPaths` chain up to and including the first required field — plus
  Mongo `_id` (FUSE-1238 deep links). Grounded in the fuse-ui FUSE-967 ledger ("the customer's own
  business reference"). SO and goods-in chains stop at fields already listed; PO adds
  `identifiers.businessOrderNumber`, master_data adds `product.identifiers.skuId`, goods-out's chain
  ends at SNAP `identifiers.shipmentId` (so goods-out alone becomes searchable by SNAP ShipmentId).
  Read the exact chains from fuse-ui `transaction-history.const.ts` at implementation time (incs 3-4).
- RESOLVED 2026-09-23 (Harry) — `11435` finds `#11435` and vice versa: each field branch matches the
  trimmed value and its `#`-toggled twin (`$in` of two) — same indexes. Increment 2.
- RESOLVED 2026-09-23 (Harry) — the v1 list and single-record responses expose
  `metadata.correlationId` as a top-level `correlationId` (additive; lets support see why a
  correlation search matched). Increment 2.
- RESOLVED 2026-09-23 (Harry) — prod indexes are built in code: boot-time `ensureIndexes()`, as #98
  and #103 did. No manual pre-build and no live-Atlas access needed for rollout; `ensure:indexes`
  stays as an optional tool. (Dev evidence: the boot build added ~30s and still passed the probe.)
- Scope added 2026-09-23 (Harry: "surface every transaction type") — collector also serves
  pick/pack/WOC/FGR on the v1 records API (increment 5), which FUSE-1207 assumed already existed:
  #104 left them out because their collections have no `lifecycle.createdAt` list index.

## Increments
<!-- Each independently implementable AND verifiable. Cite the criteria it discharges as
     (AC n,n). Tick with `wp tick`, which stamps `— done: <sha>` from HEAD; never hand-write it.
     Prefer 3-7 — more usually means the ticket is too big, so say that rather than splitting
     hairs.

     A PRECONDITION THAT IS NOT CODE goes on its own indented `gate:` line, with a confirmation
     box under it. Sign-off blocks on a ticked increment sitting above an unconfirmed gate, and
     `wp brief` shows unmet gates in its NEXT block — so "do not action this yet" stops being
     bold prose a fresh session can miss:

         - [ ] 6. Widen the subscription filter (AC 6) — verify: filter matches in dev
               gate: FUSE-1052 AND FUSE-1053 confirmed in prod
                     [ ] confirmed
-->

- [x] 1. Search index family + covered branch query, no route change (AC 5) — `reference-search.ts` — explain spec 23/23 on Mongo 7.0.24 and 8.0.32: SORT_MERGE find, 0-doc count for unique + 1,500-shared correlation id; no-index control fails; ensure-indexes rerun creates nothing; full suite 178 pass — done: 009c9f2
      derives `{bizKey:1, field:1, deletedAt:1, "lifecycle.createdAt":-1, _id:-1}` per declared field
      plus `metadata.correlationId` on all 8 served collections, and builds the top-level `$or`
      (bizKey + `deletedAt: null` in every branch); a `Collection` read path that takes it without the
      `withNotDeleted` wrapper, sorted `{lifecycle.createdAt:-1, _id:-1}`; `referenceSearchFields`
      declared for sales_order only; `ensure-indexes` script — verify: new integration spec running
      `explain()` through that real Collection path, index set from the real registry `onModuleInit()`
      in `beforeAll` (avoids the static `indexesEnsured` trap), on 7.0.24 **and** 8.0.x: find is
      SORT_MERGE with no COLLSCAN/blocking SORT, count examines 0 docs, for a unique value and a
      1,500-record shared correlation id, other-business and soft-deleted seeds present; negative
      control fails with the new indexes removed; a second script run creates nothing.
- [x] 2. `?reference=` on the v1 list route (AC 1,2,3,4,6,7,8) — `ReferenceSearchPipe`, `@ApiQuery` + — 24 e2e cases (400s incl. [$ne] + repeated, per-field, cross-field, once-only, no match, # both ways, _id, other business, soft-deleted, tie paging, correlationId on list/detail, legacy unchanged, Swagger); explain spec 27/27 on 7.0.24 + 8.0.32 incl. # twin — separate branches per variant ($in broke the merge); suite 206 pass — done: bc692b8
      400 `@ApiResponse`, `listRecordsWithLifecycle(…, reference?)`; universal branches on every served
      type (correlation id; `_id` when `/^[0-9a-f]{24}$/i`) plus sales_order's fields; each branch
      matches the value and its `#`-toggled twin; `correlationId` surfaced on v1 responses and the
      Swagger DTOs; `CLAUDE.md` updated — verify: e2e for each 400 case incl. `reference[$ne]=x` and a
      repeated param; each SO field alone matches; value in A's `customerRef` and B's `customer.order`
      → total 2, a record holding it in two fields → once; no match → `{total:0,count:0,data:[]}`;
      `11435` ↔ `#11435` both directions; other business and soft-deleted excluded; 15 same-`createdAt`
      matches paged by 5 → 15 distinct; correlation-id match on a non-SO type; list and single-record
      responses carry `correlationId`; Swagger document has optional `reference` with `maxLength`, and
      the explain spec re-run with the `$in` twin still shows SORT_MERGE and a 0-doc count. Dev: branch deploy,
      `/api-json` shows the param, GADG `sales_order` found by customerRef, salesOrder and
      correlationId; dev Atlas `explain("executionStats")` for a bulk correlation id if access exists.
- [x] 3. Goods-in/out confirmation fields (AC 1,2) — declarations in `confirmation-registry.service.ts` — goods-in/out fields + indexes (goods-out incl. both Customer Order paths + SNAP shipmentId as Record ID); per-field e2e + cross-field AC2 on goods_out; explain sorted-merge/0-doc count on 7.0.24 + 8.0.32 — done: a678953
      (bizId key), both goods-out Customer Order paths — verify: per-field e2e generated from the served
      record types (`RECORDS_API_RECORD_TYPES` filtered to what `resolveRecordType` resolves, not
      `getAll()`), a cross-field AC2 case on `goods_out_confirmation`, explain spec extended to both
      confirmation collections with a bulk-correlation seed.
      gate: per-type field mapping (incl. Record ID scope) confirmed with Harry
            [x] confirmed
- [x] 4. Purchase order, work order, RGA, stock adjustment, master data fields (AC 1) — remaining — PO/WO/RGA/SA/MD fields + Record ID additions (PO businessOrderNumber+id, SA id, MD skuId); guard proven (fails on removed WO declaration); 17 new indexes; suite 287 pass — done: a678953
      declarations; guard test that every served type declares a list — verify: generated per-field e2e,
      explain spec per collection with a bulk-correlation seed, guard fails when a declaration is removed.
      gate: per-type field mapping (incl. Record ID scope) confirmed with Harry
            [x] confirmed
- [x] 5. Serve pick, pack, work-order confirmation and finished-good receipt on the v1 records API (AC 1,9) — 4 types served (list newest-first, single by _id, cross-tenant 404, correlationId); list index + search family (21 indexes); guard/per-field cover 12 types; explain 149/149 on 7.0.24 + 8.0.32 (list sort control fails without the list index); suite 363 pass; all docs already carry lifecycle.createdAt — done: ac6edfb
      searchable (AC 1,9) — `{identifiers.businessId:1, deletedAt:1, "lifecycle.createdAt":-1}` list
      index plus the search family (correlation id + each type's fields) on `pick_confirmations`,
      `pack_confirmations`, `work_order_confirmations`, `finished_good_receipts`; `resolveRecordType`
      resolves `pick_confirmation` / `pack_confirmation` / `work_order_confirmation` /
      `finished_good_receipt` from the confirmation registry scoped by `identifiers.businessId`; field
      lists read from the canonical types (pick/pack carry `order.customerRef` / `order.customerOrder` /
      `order.salesOrder`; WOC/FGR read from source) plus a Record ID field per type by the same
      first-required-identifier rule — fuse-ui's `refPaths` for these types must mirror it — verify: e2e
      list + single-record + cross-tenant 404 for each of the 4 types; the generated per-field e2e,
      explain spec and served-types guard now cover 12 types; dev: each of the 4 lists 200 for GADG with
      `_id` + `lifecycle`, and a record is found by each of its declared fields.
- [x] 6. Prod rollout, per PR (AC 1,5,9 in prod) — indexes build at boot via `ensureIndexes()`; — three runs approved by sha after reading each prod plan (image-only): #106 d1fe749 (rev 00031, listening 53s), #108+#109 bc46ca8 (rev 00032, 51s), #110 4a5c235 (listening 15:44Z); no prod errors; v1 responses carry correlationId; pick_confirmation 200 (was 404); 0 Query Targeting alerts at +15min — 24-48h window still open — done: 2fa7a24
      approve each PR's Deploy run by sha — verify: the revision goes Ready and logs `Server listening`
      with the PR's sha; prod curl finds a known record by each field type; Query Targeting for
      `collector-prod` stays near 1:1 for 24-48h after each PR.
      gate: #104 + #105 live in prod (via #105's Deploy run 35857642789, `096e55e`), and no older parked run approved after it
            [x] confirmed
      gate: before PR B's prod approval — fuse-ui FUSE-1240 increment 1 (correlationId kept out of the payload panel) live in prod
            [x] confirmed
      gate: #98's AC3 closed — Query Targeting clean since #103's prod deploy (2026-09-21), so a new alert is attributable
            [x] confirmed
- [x] 7. Fuse MCP data — `api-endpoints.json` collector v1 records entry documents `?reference=` and — gfs-bifrost/fuse-mcp 216da57 on master (2-line description change, 90/90 tests), Deploy success; hosted lookup-endpoints collector returns the new ?reference= / correlationId / 12-type descriptions (commit lives in fuse-mcp, so no collector sha)
      the 4 newly served record types, committed from a `fuse-mcp-server` worktree (its main checkout
      has unrelated edits to the same file) straight to `master` — verify: hosted
      `lookup-endpoints collector` returns both.
      gate: increment 6 live in prod
            [x] confirmed

PRs: A = inc 1 (indexes only, no contract change — can reach prod first), B = inc 2, C = inc 3+4,
D = inc 5. Stacked, each a branch in this worktree: A = #106 `hjf/fuse-1239-reference-search` →
B = #108 `hjf/fuse-1239-reference-param` → C = #109 `hjf/fuse-1239-reference-fields` → D
`hjf/fuse-1239-serve-confirmations` (frontmatter `pr:` tracks the stack base, #106).
Each stacks on the previous only while it is unmerged.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-09-23 [inc 6, prod soak] Atlas Admin API re-check at 18:27Z (all 229 alerts, OPEN + CLOSED,
  paged): `collector-prod` has 0 open Query Targeting alerts and its last is still 2026-09-21 12:29Z
  (119 historic). Clean since #110 reached prod at 15:44Z and since fuse-ui's FUSE-1240 search went
  live in prod at 17:34Z (`fuse-ui-app-prod-00052-hsg`). No Query Targeting alert on any cluster
  since 15:00Z.
- 2026-09-23 [inc 5, AC 9, dev] Stack merged up with master `78e31c2` (#107) — clean except a
  two-script `package.json` conflict (kept both); tip suite 370 pass. PR D tip `f7a23cd` on collector-dev
  (run 35865928637, announced; reverted to master afterwards, run 35866411184, announced). GADG:
  pick_confirmation 146, pack_confirmation 107, work_order_confirmation 19, finished_good_receipt 19 —
  each lists 200 newest-first with `_id` + `lifecycle` + `correlationId` and no `metadata`, fetches a
  single record by `_id` (200) and 404s it cross-tenant; every declared field present in the newest 20
  finds its record (pick 4/4, pack 4/4, WOC 2/2, FGR 2/2 — FGR `identifiers.businessReceiptId` absent
  on dev, e2e only). Regression re-run of the PR C per-type script after the #107 merge: all green.
- 2026-09-23 [incs 3-4, AC 1,2, dev] PR C branch `a678953` on collector-dev (run 35863512611; the 17
  new indexes built at boot, revision served normally), dev reverted to master afterwards (run
  35864000558, announced). For each served type, a real GADG record was found by every declared field
  present in the newest 20: sales_order 3/3, purchase_order 4/4 (incl. Record ID `businessOrderNumber`
  and `identifiers.id`), goods_in 2/2, goods_out 5/5 (incl. both Customer Order paths and SNAP
  `identifiers.shipmentId`), work_order 1/1 present (`identifiers.salesOrder` absent on all 20 newest
  — covered by e2e only), RGA 1/1, stock_adjustment 2/2 (`identifiers.reference` total 3 — one
  reference shared by the adjustment's lines, as expected), master_data 1/1. Each search 50-80ms.
- 2026-09-23 [inc 2, AC 1-4,7,8, dev] PR B branch `bc692b8` on collector-dev (manual-deploy run
  35863091443, announced; waited for another session's branch deploy to finish first rather than
  overwrite it). `/api-json` declares optional `reference` (minLength 1, maxLength 256). Against real
  GADG data (81,577 SOs): the newest SO `6ab299a37ef54de54dc50c06` is found — alone, total 1 — by its
  customerRef `TESTREF51`, salesOrder `TESTMYSHOPIFY`, `#TESTREF51` (twin), its `_id`, and its
  correlation id; a nonsense value → 200 total 0; another business → total 0; blank / `[$ne]=x` /
  repeated / 257 chars → 400 with a clear `detail`; purchase_order found by correlation id (non-SO
  type, total 3 sharing it); v1 list, goods_out_confirmation list and single-record responses all
  carry `correlationId`; legacy `/GADG/sales_order` unchanged (no `correlationId`, no `_id`, same
  total). Every search 50-120ms.
- 2026-09-23 [inc 6 gate — baseline] Atlas Admin API alert history (project `bifrost`, read-only):
  `collector-prod` had 105 Query Targeting alerts from 2026-09-14 to its last at 2026-09-21 12:29Z
  (resolved 12:56Z), and **none since** #103's prod deploy finished (13:03Z) — ~47h clean as of
  12:35Z 09-23. Every Query Targeting alert since is another cluster's (replay-prod 3, replay-dev 2,
  dedupe-service-prod 2 — not this service). So a collector-prod alert after this plan's rollouts is
  attributable to it.
- 2026-09-23 [inc 1, dev] Branch `009c9f2` deployed to collector-dev (manual-deploy run 35859305485,
  announced in `#bifrost-general`), dev reverted to master afterwards (run 35859834112). Boot built the 11
  new indexes with no pre-build: revision `collector-dev-00141` created 12:17:34Z → `Server listening`
  12:18:40Z (66s) → Ready 12:18:52Z, vs 35s for master's `00140` (12:00:54 → 12:01:29) — the builds on
  dev's data (GADG 81,577 SOs) added ~30s and still passed the startup probe. No regression, identical
  to the master baseline taken minutes earlier: GADG `sales_order` total 81,577 with the same first two
  `_id`s, `purchase_order` total 111 same first `_id`, single-record `sales_order/6ab299a37ef54de54dc50c06`
  identical body. Not checked: `getIndexes()` on dev Atlas (no data-plane access — the successful boot is
  the indirect proof, since a failing `createIndex` would crash the revision before it went Ready).
- 2026-09-23 [inc 1, AC 5] `reference-search-index-coverage.spec.ts` (23 tests) through the real
  `Collection.findAnyPaginatedWithLifecycle` with the registry's real index set, on 7.0.24 and 8.0.32
  (re-run independently on 8.0.32): unique value — SORT_MERGE over 8 (7.0) / 4 (8.0) IXSCANs, 6 docs
  examined, count 0 docs; 1,500-shared correlation id — SORT_MERGE, 10 docs examined per page, count
  0 docs, paging by 100 returns all 1,500 once; no-index control — blocking SORT over ~3,505 docs and a
  ~3,505-doc count fetch (the spec discriminates). 7.0 doubles the scans because it splits
  `deletedAt: null` into null + undefined ranges. `ensure-indexes` against a scratch 8.0.32 mongod:
  second run logged `created: []` everywhere. Full suite 178 pass / 11 skipped; `build:check` and
  `lint` clean (pre-existing warnings only). Indexes added: sales_orders 4, the other 7 collections 1
  (correlation id) — 11 total so far.
- 2026-09-23 [planning, AC 5] Throwaway mongodb-memory-server experiment (7.0.24 and 8.2.6; 2,000
  non-matching SOs, one REF-X per field, 1,500 sharing CID-BULK, another business, soft-deleted
  matches): nested `$and` form — find SORT_MERGE (6 docs examined), unique count 0 docs, bulk count
  ~3,505 docs (whole business, FAIL); top-level `$or` form — SORT_MERGE find and 0-doc count in every
  case; top-level form wrapped by `withNotDeleted` — blocking sort over 3,507 docs on 7.0 (FAIL).

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
> SUPERSEDED 2026-09-23 — verified: increment 1's explain spec runs on 8.0.32 and passes (SORT_MERGE, 0-doc count).
- The query-shape result on Mongo 8.0.x (prod's version) — increment 1 runs it.
- Planner behaviour against prod's real index set, which includes superseded indexes CI can't see —
  only a live Atlas explain proves it (increments 2 and 5, access permitting).
- M10 index-size headroom for ~20-25 new indexes.
- The 24-48h Query Targeting soak on real search load. Atlas stayed clean for ~2h45m after #110
  reached prod (15:44Z → 18:27Z), but Harry released FUSE-1240's UI search at 17:34Z ("ship them
  all") before the window closed. The traffic the soak was guarding against only starts now. Re-check
  `collector-prod` Query Targeting over the next 24-48h; any new alert is attributable to this search,
  since there have been none since 2026-09-21.

## Rollout & rollback
<!-- Added on demand. Written at plan time; amend in place as it changes.
     `Shared state touched:` is the single home for the five classes git does not own — a dev
     deploy, a prod config write, a Datadog monitor, a CI var or secret, cross-repo IaC. Reverting
     the branch undoes none of them, so if they are not written here they are not written down. -->

- **Order:** PR A (indexes) → prod, then PR B (param) → prod, then PR C (remaining types) → prod.
  **Cross-plan:** PR B's prod approval waits for fuse-ui's FUSE-1240 increment 1 in prod — PR B adds a
  top-level `correlationId` to every v1 record, and fuse-ui's `toDisplayRow` rest-spread would otherwise
  leak it into the Canonical Payload panel and download.
  FUSE-1240's prod release waits for PR C in prod plus 24-48h of clean Query Targeting. Reversed, a
  collector revision without PR B silently ignores `?reference` and returns the unfiltered list, which
  the UI would render as search results.
- **Flags/config:** none.
- **One-way doors:** none. Prod index builds are reversible only by a manual drop, by key spec copied
  from a live `getIndexes()` (indexes are unnamed).
- **Rollback:** `git revert` per PR. New indexes survive a revert (the app never drops) — harmless
  beyond write cost; drop by hand only if the feature is abandoned. Reverting PR B while FUSE-1240 is
  live must be paired with a UI rollback, for the reason under Order.
- **Shared state touched:** dev branch deploys (announce in `#bifrost-general`, revert dev to master
  after); prod and dev index builds via `ensure-indexes`; collector's parked Deploy runs — 14 were
  `waiting` on 2026-09-23; the 13 whose sha was an ancestor of prod's `7a7b71b` were cancelled that day
  (Harry's go-ahead), leaving only #104's run 35851892780. Still approve by sha only, since every merge
  parks a new run; `fuse-mcp-server` data push to `master`.
- **Proof in prod:** Atlas Query Targeting for `collector-prod` stays near 1:1 for 24-48h after each
  PR (baseline: the window since #103, 2026-09-21); a prod `?reference=` call returns the expected
  record for a known customerRef, salesOrder and correlation id.

## Options considered
<!-- Added on demand. Why this approach and not the others — the thing the planning agent is
     asked for and the plan has otherwise had nowhere to put. Promote to a durable record with
     `wp decide --record` when it is worth defending in a review six months out. -->

- **Chosen — one compound index per searchable field, top-level `$or`** — exact bounds per branch,
  index-ordered rows so a sorted merge works, index-only count; no backfill, no write-path change;
  a list change is just a new index. Cost: ~2× index writes per SO insert, more cache, one-off builds.
- **Rejected — nested `$and:[{bizKey, $or}, {deletedAt:null}]`** — whole-business fetch on a bulk count
  (measured). The draft's original shape.
- **Rejected — denormalised `searchKeys` multikey array** — backfill of every doc before AC 1 holds and
  again on every list change; a multikey index can't cover the count on the array field (the #98
  failure mode for bulk correlation ids).
- **Rejected (fallback) — compound wildcard `{bizKey:1, "$**":1}` + `wildcardProjection`** — index-only
  count and index-ordered sort with `deletedAt`/`createdAt` not established; list change = full rebuild.
- **Rejected — Atlas Search** — out-of-band, eventually consistent, Terraform-managed, not testable in
  mongodb-memory-server; right tool for the out-of-scope fuzzy follow-up.
- **Rejected — per-field queries unioned in app** — loses DB pagination and count.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-09-23** — Sign-off: Learnings promoted — architecture.md Guardrails G1-G3 (top-level $or shape; plain-string query params; Record ID fields mirror fuse-ui refPaths — G3 touched by this diff, not breached: FUSE-1240 inc 6/7 verified refPaths against these fields 53/53 on dev), Persistence (top-level $set, latest correlationId), Query API gotchas (createdAt-only sort ties; reference search mechanism; stale in-memory-pagination and metadata.customer-fallback claims corrected), prod Atlas M10 snapshot; known-context.md (Order Ref 1/2/3, latest-correlation-id caveat, work-order/confirmation/CLAUDE.md sections rewritten against origin/master 0599b6b). New system explainer explainers/reference-search.md.

- **2026-09-23** — Refuted learning (tried at sign-off): giving known-context.md verified_paths so wp stale catches drift. wp refuses by design — that doc is exempt from staleness anchors, and its dated mutable claims carry (snapshot <date>) markers instead, which wp doctor ages. The stale facts it flagged (work orders, confirmation types) were fixed against origin/master instead.

- **2026-09-23** — Sign-off: increment 6 restamped 4a5c235 → 2fa7a24. The prod-deployed #110 squash isn't on the plan branch, and 2fa7a24 (the branch tip, merged up with master) has an identical tree (git diff 2fa7a24 4a5c235 empty). The worktree had been left detached on master; switched back to hjf/fuse-1239-serve-confirmations so sign-off diffs the real branch. Increment 7's commit lives in fuse-mcp (216da57), so it carries no collector sha.

- **2026-09-23** — Master moved again to 67563b9 (#111, fuse-1b: Terraform-only snap-adapter exclusion on the WOC/FGR confirmation_data_failure subs) — merged up the stack bottom-up, no conflicts, pushed. Only the stack base (#106) runs CI; stacked PRs targeting branches get none until they rebase onto master, so each was checked locally (tip suite 370 pass after #107).

- **2026-09-23** — #104+#105 reached prod via #107's Deploy run 35863751662 (78e31c2, terraform-apply-prod success ~13:00Z), not via #105's own run — that parked run (35857642789, 096e55e, an ancestor of prod) was cancelled as a rollback hazard and fuse-1b told not to approve it. Rollout gate 1 ticked on that basis. Master moved to 78e31c2 (#107, stock-adjustment lifecycle) — merged into the stack bottom-up before the next dev deploy.

- **2026-09-23** — Inc 5 as built — source corrects the plan: pick/pack carry customerRef and salesOrder under identifiers.* (poller maps shipment.CustomerRef → identifiers.customerRef, shipment.SalesOrder → identifiers.salesOrder), only CustomerOrder under order.*. Fields: pick/pack identifiers.customerRef, order.customerOrder, identifiers.salesOrder, identifiers.shipmentId (RID, SNAP); WOC workOrder.customerRef, identifiers.id (RID = SNAP shipment id); FGR customer.reference (SupplierRef), identifiers.businessReceiptId (BizPurchaseOrder), identifiers.id (RID, SNAP receipt id). Deliberately left out as duplicates of CustomerRef: pick/pack customer.reference, WOC businessWorkOrderId. No lifecycle backfill needed — all four collections post-date lifecycle (added 07-10 / 08-19 vs 06-23).

- **2026-09-23** — Incs 3-4 as built: Record ID for work_order and RGA leads with their required customer reference (workOrder.customerRef / identifiers.businessRgaNumber), matching how fuse-ui's existing chains lead — already business fields, so nothing extra; newly searchable via the Record ID rule: PO identifiers.businessOrderNumber + identifiers.id, stock_adjustment identifiers.id, master_data product.identifiers.skuId, goods-out SNAP identifiers.shipmentId. Served-type guard detects 'served' by a 200 from the list route (resolveRecordType is private). Per-type e2e loops fields and asserts one list of misses so a failure names the field.

- **2026-09-23** — Harry: prod indexes are handled in code (boot-time ensureIndexes, as #98/#103) — dropped the manual prod pre-build and the live-Atlas-access gate from rollout; ensure:indexes kept as an optional tool. Harry: surface every transaction type — added increment 5 (serve pick/pack/WOC/FGR on v1, with list + search indexes; FUSE-1207's UI assumed they were already served) and renumbered rollout/MCP to 6/7. PR #106 body and its Confluence row still say to pre-build — correct both when #106 is marked ready.

- **2026-09-23** — Inc 1 as built: the branch read path is Collection.findAnyPaginatedWithLifecycle(branches, …), which adds deletedAt: null to each branch itself (keeps the not-deleted rule inside Collection next to withNotDeleted); find+count body shared via a private paginateWithLifecycle, findPaginatedWithLifecycle unchanged. referenceSearchFields is a plain path list (no labels — nothing reads one). CLAUDE.md updated in inc 1 rather than inc 2, since PR A is inc 1 alone and docs ship with the code.
- 2026-09-23 — Base moved again, `0b25bdd` → `096e55e` (#105, lifecycle failure marking for goods-in/out
  confirmations, merged 12:58). It touches confirmation services, `event.controller.ts` and `pubsub.tf`
  only — nothing this plan edits. Its Deploy run 35857642789 supersedes #104's 35851892780.
- 2026-09-23 — Harry accepted the defaults: Record ID = displayable `refPaths` chain + `_id`; leading
  `#` ignored both ways; `correlationId` exposed on v1 responses. AC 7-8 added for the latter two.
- 2026-09-23 — Cancelled the 13 stale parked collector Deploy runs (all ancestors of prod `7a7b71b`) on
  Harry's go-ahead, removing the approve-the-wrong-run rollback hazard before this plan's prod rollouts.
- 2026-09-23 — Base moved from stacked-on-FUSE-1238 (`2df8818`) to `origin/master` (`0b25bdd`): #104
  squash-merged at 10:59Z while this plan was drafted. Branch had no commits of its own.
- 2026-09-23 — "SO number" = the customer's own sales-order number, `identifiers.salesOrder` (Harry),
  not the ticket's assumed `shipmentId`: canonical SO `identifiers.shipmentId` holds `""`/`"AUTO"`
  placeholders, and SNAP's real ShipmentId is a hash snap-adapter never writes back
  (`apps/snap-adapter/src/core/sales-order/sales-order.service.ts`). SNAP ShipmentId search out of scope.
- 2026-09-23 — The draft proposed dropping the SO `{businessId, customerRef}` index as a redundant
  prefix; reversed — it and the PO/RGA equivalents are upsert-key indexes ingest depends on.
- 2026-09-23 — Sort tiebreaker `_id` applied to the search path only. The unfiltered list has the same
  tie problem today (`createdAt` stored to the second — 24 tie groups in PURDYFIGG's newest 100 SOs),
  but fixing it rebuilds every existing list index — separate follow-up, not this plan.
- 2026-09-23 — Keeping every correlation id a record has carried (`$push`/`$slice` history) split out
  to a future plan: it changes the write path and reintroduces a multikey count.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->

(none)
