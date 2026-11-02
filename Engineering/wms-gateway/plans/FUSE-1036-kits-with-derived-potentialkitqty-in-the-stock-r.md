---
ticket: FUSE-1036
title: kits with derived potentialKitQty in the stock read
service: wms-gateway
status: complete
created: '2026-10-01'
updated: '2026-10-09'
repo: /home/hjf/code/fuse/wms-gateway
worktree: /home/hjf/code/fuse/wms-gateway/.claude/worktrees/fuse-1036-drop-kits-route
branch: hjf/fuse-1036-drop-kits-route
base: origin/hjf/fuse-1036-kits-in-list
base_sha: beeca76
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: medium
pr: '32'
---
# FUSE-1036 — kits with derived potentialKitQty in the stock read

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
[FUSE-1036](https://globalfreight.atlassian.net/browse/FUSE-1036), under epic FUSE-792. Extend the gateway's stock read to return product kits as canonical kit stock positions (`type: "kit"`) carrying a `potentialKitQty`, applying the ILG filters (`Status 00`, `State W`, `Group1 != UNLINK`) to the kit and to every component feeding the number. A zero-availability kit is still returned with `0`, and a kit SKU in the SKU lookup returns the kit entry, never its components. Proof: a dev business with a kit returns it from the gateway matching SNAP's own stock screen, and zeroing a component drops it to `0` while it stays listed. Formally blocked by FUSE-1188 (the products read, not started); see `## Rollout` for how this plan sequences around it.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. Kits are returned alongside regular products, each identified as a kit with `potentialKitQty`. — met 2026-10-09 in code and tests, QA not yet passed: on origin/main (1a1f48d) `go test ./...` is green and TestTheListCarriesProductsAndKitsInOneBody, TestTheStockListCarriesAKitBesideProducts, TestAKitPositionMarshalsAsTheKitArm, TestKitPositionCarriesDerivedQuantity and TestGADGKitsMatchSNAPsOwnNumber pass; PR #31 Evidence: one GADG body of 102 products and 10 kits, each kit's `potentialKitQty` equal to SNAP's own `stocktotalskit` figure read before and after
- [x] 2. ILG filters are applied at both the kit-SKU level and the component level. — met 2026-10-09 in gateway behaviour, not proved on real SNAP: TestKitFailingFilterIsAbsent (kit SKU level) and TestStockOutsideTheILGFilterDoesNotFeedAKit, TestComponentWithNoUsableStockMakesKitZero (component level) pass on origin/main; PR #31 Evidence on HJF: UNLINK component 0, non-W component 0. GADG has no UNLINK or non-W rows, so SNAP's own handling of those is still unseen (see Not verified)
- [x] 3. A kit with zero availability is still returned with `potentialKitQty = 0`. — met 2026-10-09: TestAStocklessKitIsStillListed, TestKitWithNoAvailabilityIsZero, TestADerivationThatForcesZeroIsReportedWithItsReason and TestAKitWithoutBOMLinesTakesItsProductUnitAndIsListedAtZero pass on origin/main; PR #31 Evidence: GADG's three BOM-less kits listed at 0, and zeroing a component on HJF made the kit read 0 after 3.3 s while it stayed listed
- [x] 4. A kit SKU in the SKU filter returns the kit entry, not its components. — met 2026-10-09: TestAKitSKUInTheFilterReturnsTheKitEntry, TestKitSKUReturnsExactlyOneEntry, TestKitSKUEntryIsKitTyped, TestAKitSKUIsServedAsItsKitEntry and TestAKitWithItsOwnStockIsListedOnceAsAKit pass on origin/main; PR #31 Evidence: `/sku/LEGOKIT` returned a kit entry (537, `components` [])

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `apps/gateway/tools/canonschema` (`src/index.ts` `WANTED`, `src/embed-openapi.ts` `SCHEMAS`, `package.json`) → generated `internal/models/canonical/canonical.gen.go`. See guardrail G2 in [[architecture]].
- `internal/adapters/snap/request.go`: `SnapResponse.Results` is typed `[]canonical.SnapShipmentJson` and `get`/`GetShipment` are the only code, so the envelope decode must be generalised, not just extended. Weak decode stays (G4).
- `internal/core/stock` (new `kits.go`), `internal/http/controllers/api/v1/stock.go`.
- `apps/gateway/openapi.yaml`: the contract other teams may consume (G1). Today the three stock 200s are bare `type: object`.
- `CanonicalStockPosition` in `@gfs-bifrost/types` (10.9.0): consumed, not changed, unless UNRESOLVED 3 forces a pkg-node change.
- SNAP `/v2/stocktotalskit` (`@gfs-bifrost/snap` 0.4.0 `SnapStockTotalKitSchema`), `/v2/stocktotals`, `/v2/kits`.
- In-flight overlap: draft PR #7 (backend resolution) edits `core/stock/stock.go`, `snap/request.go`, `snap/provider.go` and `openapi.yaml`; Renovate PR #8 bumps types to `^10.9.0` and regenerates `canonical.gen.go`.
- Fuse MCP: `wms-gateway` has no entry in `services.json` yet, so `api-endpoints.json` and friends have nothing to update until that exists (sign-off will prompt).

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
> SUPERSEDED 2026-10-01 — increment 1 settled it: the `stocktotalskit` list route 500s on GADG and State/Group1 filtering is unproven there, so `potentialKitQty` is derived in core from `/v2/kits` + a filtered `/v2/stocktotals` read, not passed through. See `## Verification` and `## Decisions & deviations`.
- Kit availability may be a pass-through of `PotentialKitQty` from `/v2/stocktotalskit` rather than derived — ticket hint only; not verified. Increment 1 settles it, and the decision rule is in that increment.
- `SnapStockTotalKit` has never been live-verified (0.3.0 verified 15 entities and this was not one) — `/home/hjf/code/CLAUDE.md` `@gfs-bifrost/snap` 0.3.0 note. Expect nullable/casing gaps (`LineID` here vs `LineId` on stock totals; owner/business are `OwnerId`/`BizId`, not `Owner`/`Biz`).
- The `fuse-mocker` snap-api simulator cannot settle filter semantics: it derives `PotentialKitQty` itself as `min(floor(sellable/qtyPerKit))`, hardcodes `Status 00`/`State W`, lacks real OData `ne`, and omits `Unit`/`OwnerId` on kit rows. Use a real dev tenant (GADG has kits; TTRS is a component of three) — source read plus known-context.
- go-jsonschema v0.24.1 given `z.toJSONSchema(CanonicalStockPositionSchema)` (a root `oneOf` with no `type`) emits an **empty file, no error**, so `go build` and `make gen-check` pass vacuously. The canonschema README's "dangling subtypes" description is wrong for this case. Splitting `oneOf[i]` into one schema file per arm in `index.ts` generates and compiles, with no pkg-node change (reviewer experiment in scratch, 2026-10-01).
- Snap-package schemas are all `.optional().nullable()`, so go-jsonschema emits `interface{}` for every field (plus dangling `X_0` aliases); types' own `SnapProduct` is `.optional()` only and yields `*string`. A `SnapStockTotal` also drags a second ~600-line Product tree with `Group1` as `interface{}`. Verified by generating all three in scratch.
- `CanonicalKit` requires `kitId`, `unit` and `components[]` (all min-length 1 / non-empty strings), the kit arm has no other identifier, and `SnapStockTotalKit.Unit` is nullable. A kit with no `Unit` fails canonical validation and the gateway returns 502 (G4, `respond.DomainError`).
- `CanonicalKit.components` has no `omitempty` in the generated Go, so a nil slice marshals as `null`; always emit a non-nil `[]`.
- The adapterclient cache cannot be disabled or bypassed per request: a TTL of 0 falls back to 15 min, the default is 30 (`SNAP_CACHED_CONTENT_MINUTES`), and `iac/` does not set it. Kit reads inherit that unless changed.
- Zero-availability handling must clamp at 0: the simulator's stock is unclamped (oversold reads negative) — memory note on the simulator; real SNAP unverified.
> SUPERSEDED 2026-10-01 — the derivation needs only `/v2/kits` plus ONE filtered `/v2/stocktotals` read, the same read FUSE-1188's products snapshot needs, so the extra SNAP cost is the kits read alone. The concurrency concern below still applies to the combined reads.
- Deriving would cost three paged SNAP reads per cache miss against a service-wide cap of 20 concurrent SNAP calls (4 per instance), and SNAP degrades past 10–20 fleet-wide — snap-adapter known-context. This is why pass-through is the default.
> SUPERSEDED 2026-10-02 — Harry's team now owns FUSE-1188 as well (Nylah, 10:54: "I don't hold any stock tickets"). The two tickets deliver together: 1188 owns the stock read, snapshot and list contract ([[plans/FUSE-1188-products-stock-read-with-a-paged-filtered-snapsh|FUSE-1188 plan]]); this plan's kit work stacks on it as K0–K2 below. The ticket still closes only once kits are in the same response as products.
- UNRESOLVED 1: **Done-state vs the FUSE-1188 link.** 1188 formally blocks this ticket (Jira link) and has no code. AC 1 says kits "alongside regular products", which only exists once 1188's products read does. This plan builds kits on the existing `/kits` route ahead of 1188 (increments 2–6) and leaves the merge as increment 7, gated on 1188. Is kits-only on `/kits` an acceptable interim, and may the ticket stay open until 7?
> SUPERSEDED 2026-10-01 — Harry decided: a component failing the ILG filter counts as zero availability, so the kit reads 0 and is still returned; a kit whose own SKU fails the filter is excluded.
- UNRESOLVED 2: **A kit whose rows are all filtered out** (or whose components all drop out): excluded from the response, or returned with `0`? AC 2 and AC 3 pull opposite ways. Kit parents may also hold no stock rows at all, so "StockStatus/State at kit-SKU level" only means something on `stocktotalskit` rows, and `Group1` needs a product lookup.
> SUPERSEDED 2026-10-01 — `unit` can't come from `stocktotalskit`: `Unit` is null on kit rows with no stock line (BIRDBATH, BATHELLTD). Working default is now `/v2/kits` `Unit`.
- UNRESOLVED 3: **`kit.unit` and `kit.components`.** Required by `CanonicalKit` but the breakdown is out of scope. Source `unit` from `stocktotalskit.Unit` or from `/v2/kits`? Is `components: []` acceptable (it can read as "no components"), or should pkg-node loosen `components` to optional (a types minor, no fapi impact since fapi is on `^9.5`)?
> SUPERSEDED 2026-10-02 — moved to [[plans/FUSE-1188-products-stock-read-with-a-paged-filtered-snapsh|FUSE-1188 plan]] UNRESOLVED 4, which owns the list contract.
- UNRESOLVED 4: **List response shape.** FUSE-1188 requires pagination, so a bare array can't carry paging metadata, while G3 says bare canonical record with no envelope. The `openapi.yaml` shape is a one-way door for other-team consumers. Needs agreeing with the 1188 owner before increment 5 merges.
> SUPERSEDED 2026-10-02 — settled in the [[plans/FUSE-1188-products-stock-read-with-a-paged-filtered-snapsh|FUSE-1188 plan]]: a per-request cache opt-out (its increment 3) and a per-business snapshot with a max age counted from the start of the build (its increment 6). Kits use the same snapshot.
- UNRESOLVED 5: **Freshness.** FUSE-792 and FUSE-1188 want ≤ ~5 min, and this ticket's QA step 3 zeroes a component and re-checks. With the 30-min cache that step fails on dev as built. Options: a short per-client TTL for kit reads (code), a lower service-wide `SNAP_CACHED_CONTENT_MINUTES` (Terraform, and it also shortens the cache on `salesorder` reads), or align with 1188's planned short-TTL per-business snapshot. Which?
> SUPERSEDED 2026-10-01 — decided by the agent, not Harry: extend `normalizeUnions` so `anyOf[T, null]` becomes `*T`.
> SUPERSEDED 2026-10-02 — narrowed: extending `normalizeUnions` globally would silently break `customer.order` on sales orders, so the [[plans/FUSE-1188-products-stock-read-with-a-paged-filtered-snapsh|FUSE-1188 plan]] (increment 2) collapses nullable fields to pointers only for the new SNAP roots.
- UNRESOLVED 6: **Codegen typing.** Accept `interface{}` fields from the snap-package schemas and map through a thin adapter-private struct, or extend `normalizeUnions` so `anyOf[T, null]` becomes `*T`? Recommendation: extend `normalizeUnions` once, since 1188 needs stock totals too and the same shape will recur.
> SUPERSEDED 2026-10-02 — moved to [[plans/FUSE-1188-products-stock-read-with-a-paged-filtered-snapsh|FUSE-1188 plan]] UNRESOLVED 4 (a repeated `?sku=`, recommended there).
- UNRESOLVED 7: **`?sku=` on `/stock/{businessId}`.** Today the SKU lookup is only the `/sku/{sku}` path param. If a query filter is intended, AC 4 isn't fully covered by increment 6.
> SUPERSEDED 2026-10-01 — Harry confirmed: match SNAP's own number.
- UNRESOLVED 9: **Which quantity counts as available.** SNAP's own `PotentialKitQty` reproduces exactly as `floor(Σ max(Qty − QtyDueOut, 0) over State W / Status 00 rows ÷ BOM Qty)`, min over components (no subtraction of `QtyAllocated`/`QtyAssigned`). The QA step compares against SNAP's screen, so I'd match SNAP. Confirm, or specify another definition?
> SUPERSEDED 2026-10-01 — Harry decided: closed lines are ignored and a kit with no open lines returns 0; a `Qty 0` line makes the kit 0; nested kits are handled fully (semantics in the increment 3 text), never 500.
- UNRESOLVED 10: **BOM edge cases SNAP handles inconsistently.** A BOM line with `DateClosed` set, `MaintInd = 'H'`, a `Qty 0` line, and a component that is itself a kit. On GADG: `08OTTPA4` (an open `Qty 0` line plus a closed line) reads 0, while `EJTEST` (one `Qty 0` line whose component is a kit) returns 500. What should the gateway do for each: skip the line, treat the kit as 0, or fail? Recommendation: ignore closed lines, treat a `Qty 0` line as invalid and return that kit as 0, never 500.
- UNRESOLVED 8: **Shared module intent.** An earlier decision wanted one shared stock-read / ILG / kit-derivation module for FUSE-658 (Shopify stock sync, TypeScript) and FUSE-792. The gateway is Go, so if derivation is forced the ILG constants and kit math live in two places. Still intended? If yes, the ILG policy needs one source and a parity test.

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

- [x] 1. **Live settle (merges nothing).** Against a real dev SNAP (GADG, connection via `get-snap-connection`; not the simulator) diff a real `/v2/stocktotalskit` payload against `SnapStockTotalKitSchema`, and settle: (a) `stocktotalskit/{sku}` vs hand-computed `min(floor(component sellable / qtyPerKit))` over `/v2/stocktotals` + `/v2/kits`; (b) whether `PotentialKitQty` moves when a component has `State != W` / `Status != 00` / `Group1 = UNLINK`; (c) whether `$filter` works on `stocktotalskit` (SNAP docs call it "named but not demonstrated") and on `stocktotals` (`$expand` is undocumented, so don't rely on it); (d) a zero-stock kit still has a row, and what a missing SKU returns; (e) how `OwnerId`/`BizId` relate to `businessId` (shipments filter `Owner eq '<businessID>'`). Verify: dated evidence bullets in `## Verification` and a `wp decide` entry naming the chosen source. Decision rule: honours component filters → pass-through; ignores them → derive in core from `/v2/kits` plus filtered `/v2/stocktotals` (clamp at 0); omits zero rows → enumerate via `/v2/kits` and synthesise `0`. Exit step: re-plan increments 3–5 from the recorded outcome (they are written for pass-through). Probing (b) needs a stock write on a real tenant — name the tenant and get a developer's go-ahead first. — live settle on GADG: formula matches SNAP on 6/8 kits; list route 500s; State/Group1 unprovable without a write — done: 9fc03c8
- [x] 2. **Canonical kit position type generated** — special-case `CanonicalStockPositionSchema` in `tools/canonschema/src/index.ts` by emitting each `oneOf` arm as its own schema file, then `make gen`. Verify: the generated package defines named product and kit arm types (an empty file passes `go build` and `gen-check`, so assert the names, not the build), and `TestKitPositionRoundTripsThroughSchema` in `shared/schema` round-trips a hand-built kit position (with a non-nil empty `components`) through `schema.Parse`. Own small PR: large generated diff, no behaviour. Needs Go 1.27 locally (the machine has 1.25.14; `gen-check` runs in CI regardless). Independent of increment 1, so it can run in parallel with it; rebase after Renovate #8 so the regenerated output isn't fought over. (no AC; enabler) — union arms generated; fmt/build/vet/test/race/lint/gen-check all green on the committed tree; 5 tests on the arm types — done: f58593b
- [x] 3. **Pure kit derivation in core, nested-aware** — `core/stock/kits.go`: `potentialKitQty(kitID, boms, usable)` on plain domain inputs (BOMs keyed by kit SKU; usable stock per leaf SKU, already reduced to `Σ max(Qty − QtyDueOut, 0)` over rows passing the ILG filters, so a filtered-out component is simply absent and reads 0). Rules, decided 2026-10-01: open BOM lines only; a `Qty ≤ 0` line or no open lines → 0; a component failing the filter → the kit reads 0; a component that is itself a kit is expanded, its assembled stock used first and the top-level kit's own stock never added; leaf demand is summed across every path; the result is the largest n whose total leaf demand fits the usable stock, found by binary search (monotone in n); a cycle or a BOM deeper than 8 → 0 with a distinct reason the caller can log. Returns `(qty, reason)` and never errors on data shape. Verify, one behaviour each: `TestKitAvailabilityIsLimitedByScarcestComponent`, `TestKitWithNoAvailabilityIsZero`, `TestAllocatedQuantityIsNotSubtracted`, `TestClosedBomLineIsIgnored`, `TestKitWithNoOpenLinesIsZero`, `TestZeroQuantityBomLineMakesKitZero`, `TestComponentWithNoUsableStockMakesKitZero`, `TestSubKitAssembledStockIsUsedFirst`, `TestSharedLeafDemandIsSummedAcrossPaths`, `TestTwoLevelNestingResolves`, `TestBomCycleIsZeroWithReason`, and a table-driven test over the six GADG kits with their recorded stock rows as fixtures (expected = SNAP's own `PotentialKitQty`). (AC 2 arithmetic, 3) — 17 tests incl. 7 GADG kits matching SNAP's own PotentialKitQty; fmt/build/vet/test/race/lint green; on branch hjf/fuse-1036-kit-derivation — done: 91c726a
- [x] 4. **Simulator brought up to SNAP's kit semantics** — fuse-mocker `apps/snap-api`, direct to its main (dev-only). OData `ne` and the `Product/Group1` path; a kit-specific availability using SNAP's formula (leave `SellableStock` alone, shipments use it); nested resolution per increment 3's rules; kit rows carrying `Unit`, `OwnerId`, `Site`, `Facility`, `LineID` with nulls where SNAP has them; STKS seed fixtures: a nested kit with a shared leaf, a sub-kit with assembled stock, a non-W row, an UNLINK kit product. Verify: simulator unit tests for the grammar and the nested fixture's number; after its deploy, live `GET /v2/stocktotalskit/{sku}` on crackle for the fixtures, and `$filter=State eq 'W' and Status eq '00' and Product/Group1 ne 'UNLINK'` on `/v2/stocktotals` returning only qualifying rows. Check `SEED_BUSINESSES` is set in dev first. The simulator and the gateway are two implementations of one written spec, so agreement proves the implementations match, not that SNAP would. (enabler for 7) — fuse-mocker main, deployed and verified on HJF — done: d9e1b14
      gate: Harry's go-ahead for simulator changes (given 2026-10-01)
            [x] confirmed
- [x] K0. **The business's kits and their BOMs, read in the same snapshot build.** Kits are the business's products with `Group2 = MASTERSKU` (from the FUSE-1188 products read; the SNAP host is shared, so never trust `/v2/kits` alone); their BOM rows come from `/v2/kits` through the 1188 pager, filtered to those kit SKUs; a kit's own product record carries the kit-level Group1, since a stockless kit has no stock row. Verify: `TestKitsFollowsPagesUntilExhausted`, `TestAKitIsAProductMarkedMasterSKU`, `TestBOMRowsForAnotherOwnersKitsAreIgnored`; live local run on GADG lists its 10 `MASTERSKU` kits and not `EJTEST`. (AC 1, 2 groundwork) — PR #29, filtered BOM read in the snapshot build; 11 tests, 7 mutations caught — done: eb18b48
      gate: FUSE-1188 increment 4 landed (the pager), and its UNRESOLVED 3 answered (if no products read, K0 adds one)
            [x] confirmed — 2026-10-09: FUSE-1188 #16 is on main (b4f17f5) with the pager, and Harry answered UNRESOLVED 3 on 10-02 (FUSE-1188 plan decisions); `TestKitLinesFollowsPagesUntilExhausted` and `TestProductsReturnsEveryProductOfTheBusiness` pass on main
- [x] K1a. **Kit positions (pure core).** `toKitPosition`: `kit.unit` from `/v2/kits`, `components` a non-nil `[]`, `potentialKitQty` from #10's derivation over the snapshot's usable rows (per site if FUSE-1188 UNRESOLVED 1 says so), a kit whose own product fails the ILG filter excluded, the derivation reason logged through the catalogue (G6), an invalid kit handled by FUSE-1188 UNRESOLVED 5's rule. Verify, one behaviour each: `TestKitFailingFilterIsAbsent`, `TestAStocklessKitIsStillListed` (the BIRDBATH case), `TestKitPositionCarriesDerivedQuantity`, `TestKitComponentsMarshalAsEmptyArray`, `TestAKitPositionMarshalsAsTheKitArm`, and the invalid-kit test once that rule is decided. (AC 1, 2, 3) — PR #30, kitPositions with the nested-aware derivation; 17 tests, 10 mutations caught — done: 83752ad
      gate: FUSE-1188 increment 5 landed (the `stock.Position` wrapper and the extended `stockRow`)
            [x] confirmed — 2026-10-09: #17 is on main (61d3cf3); `stock.Position` and `TestAProductPositionMarshalsAsTheProductArm` are in main's tests
- [x] K1b. **Kits in the list and in `ForSKU`.** The snapshot build also produces kit positions; the list includes them; a kit SKU in `sku=` or `/sku/{sku}` returns the kit entry, never its components; a kit SKU is never also a product. Verify: `TestAKitSKUInTheFilterReturnsTheKitEntry`, `TestKitSKUReturnsExactlyOneEntry`, `TestKitSKUEntryIsKitTyped`, `TestAKitWithItsOwnStockIsListedOnceAsAKit`. Live, a local run: HJF's N36 fixtures through the list give FLAT 4, NEST 5, SUBSTOCK 5, FILT 0, QSTATE 0, ZERO 0, CLOSED 8, CYC1/CYC2 0; GADG's six kits match `stocktotalskit/{sku}` read just before and after; QA step 3 on HJF (zero a component, the kit reads 0 and stays listed within the freshness bound); one body carrying both `type` values. (AC 1, 2, 3, 4) — PR #31, kits merged into the list and the SKU lookup; GADG kits match SNAP stocktotalskit exactly; HJF fixtures match — done: 5671812
      gate: FUSE-1188 increments 8 and 9 merged
            [x] confirmed — 2026-10-09: #19 (83a8c0d), #20 (4d0bab0) and #28 (41d51d4) are on main
- [x] K2. **Remove the `/kits` route.** Kits are in the list now; drop the route, its `openapi.yaml` entry, the controller method, #7's `reads` case, and the README/CLAUDE.md rows. Verify: routes_test green with the route gone; `GET /api/v1/stock/{biz}/kits` is a 404 locally. (no AC; cleanup) — PR #32, /kits route removed; rests on the plan gate that Harry agrees — done: 3ae5666
      gate: Harry agrees to remove it rather than keep a kits-only view
            [x] confirmed — 2026-10-09: #32's description said to close the PR if /kits should stay; Harry merged it himself at 07:41 UTC

## Superseded increments
> SUPERSEDED 2026-10-02 — increments 5–9 below were written before this team took FUSE-1188. Their shared parts (the stock read, the codegen, the cache opt-out, the snapshot, the list contract, `ForSKU`) moved into the [[plans/FUSE-1188-products-stock-read-with-a-paged-filtered-snapsh|FUSE-1188 plan]]; their kit parts are K0–K2 above. Kept verbatim as the record and deliberately outside `## Increments`, so they neither count as open work nor block sign-off.

- [ ] 5. **Kit BOM and filtered stock reads in the adapter** — add `@gfs-bifrost/snap` as a canonschema dependency (lockfile regenerated with pnpm 11.0.8, token in user `~/.npmrc`), generate `SnapKit` and `SnapStockTotal` with `normalizeUnions` extended so optional-nullable fields come out as pointers (not `SnapStockTotalKit`: its list route is broken and it is unverified), generalise `SnapResponse` so `Results` decodes into the caller's type, and add two paged reads: `Kits` (`/v2/kits`, `$top`/`$skip`) and `StockTotals` with `$filter=State eq 'W' and Status eq '00' and Product/Group1 ne 'UNLINK'`. The stock read is the same one FUSE-1188's products snapshot needs, so agree who lands it. Verify, one behaviour each via `httptest` over the real `adapterclient`: `TestKitsFollowsPagesUntilExhausted`, `TestStockTotalsDecodesStringQuantities`, `TestStockTotalsRequestsOnlyWorkingGoodStock` asserting on rows returned by a fake that honours `$filter`, not on the URL string. Live: against GADG, `Product/Group1 eq 'GADG'` returns the TTRS rows and `eq 'NEW'` returns none, which proves the path filter actually filters (increment 1 only showed 200s). (AC 2 groundwork)
      gate: who lands the shared stock read agreed with the FUSE-1188 owner
            [ ] confirmed
- [ ] 6. **Kit mapping and the `KitsForBusiness` use-case** — one `toKitPosition` mapper, the only place that reads SNAP fields (`kit.unit` from `/v2/kits`, `components` a non-nil `[]`); `KitsForBusiness` builds usable stock from the filtered read, runs increment 3's derivation per kit, excludes a kit whose own SKU fails the filter, logs the derivation reason through the existing catalogue (G6), and returns `[]CanonicalStockPosition` through `schema.Parse`. Verify, one behaviour each: `TestKitFailingFilterIsAbsent`, `TestKitWithoutUnitIsRejectedByValidation`, `TestKitPositionCarriesDerivedQuantity`, `TestKitComponentsMarshalAsEmptyArray`, and a use-case test over an `httptest`-backed adapter serving the STKS fixtures. (AC 2, 3)
      gate: increment 5 landed; UNRESOLVED 3 stands as the working default (unit from `/v2/kits`, `components: []`)
            [ ] confirmed
- [ ] 7. **Kits served on `/kits`** — wire the use-case into the existing route; `openapi.yaml`: add the `# >>> canonschema:CanonicalStockPosition ... >>>` marker pair and placeholder inside `components.schemas` first (the embed script throws without it), add to `SCHEMAS`, `make openapi`, `$ref` an array of positions on the `/kits` 200; update the README and CLAUDE.md stock rows; apply the freshness choice from UNRESOLVED 5. Verify: a controller test that the `/kits` body is an array whose every entry validates; `make openapi && git diff --exit-code apps/gateway/openapi.yaml` (`gen-check` does not diff the spec); all gates. Live, local run with a cold cache: `GET /kits` against HJF (its backend is the simulator) for the nested fixtures, and against GADG side by side with SNAP's `stocktotalskit/{sku}` for the six real kits, then change a component's stock in SNAP and see the number move within the bound (the ticket's QA step 3). (AC 1 for kits only, 3)
      gate: list response shape agreed with the FUSE-1188 owner (UNRESOLVED 4) and UNRESOLVED 5 decided
            [ ] confirmed
- [ ] 8. **`ForSKU` kit branch** — a kit SKU resolves to one kit entry, a non-kit SKU falls through to the products path (still 501 until 1188). Detection depends on increment 1(d). Update the SKU route's `openapi.yaml` response. Verify: `TestKitSKUReturnsExactlyOneEntry`, `TestKitSKUEntryIsKitTyped`; live call with a kit SKU. (AC 4)
      gate: `ForSKU` return type agreed with FUSE-1188 (it changes the same signature)
            [ ] confirmed
- [ ] 9. **Merge kits into the `ForBusiness` response** — concatenate products and kits in one canonical response. Verify: a live call showing both `type` values in one body. Blocked follow-up that completes AC 1; the ticket does not close before it. (AC 1)
      gate: FUSE-1188 merged and deployed to dev
            [ ] confirmed

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-09 [sign-off, AC 1-4] `go test ./...` green in a clean export of `origin/main` (1a1f48d), and each criterion's named tests pass individually (listed on the criteria). PR #32 has no failing checks, and `gen-check` and `quality` are green on main at e9aa1ce and 1a1f48d. The ticket is Ready for QA, so QA itself has not run; nothing here calls the deployed gateway (internal ingress, no invoker binding).
- 2026-10-05 [K0, K1a, K1b, K2] Live, with a local binary built from the top of the stack (`3ae5666`; the kit-zeroed log event in `beeca76` came after), a local config-service stand-in, GADG real dev SNAP and the HJF simulator.
  - **GADG, real SNAP:** the list is one body of both types (112 positions: 102 products, 10 kits). The 10 kits listed are exactly the catalogue's `MASTERSKU` products; `EJTEST` (another business's kit on the shared host) is absent. For the seven kits with a BOM, gateway `potentialKitQty` equals SNAP's own `stocktotalskit` figure read just before and just after: 08OTTPA4 0, BATHELLTD 6046, BIRDBATH 2015, LEGOKIT 537, TTRS35 44180, XTTRS 22090, XTTRS3 6046 (the 10-01 figures). The three kits with no BOM rows (IDRINKANDIKNOWTHINGSTOTE26, SKUFUSEKIT, TTRS4) are listed at 0 where SNAP answers 404.
  - **GADG `/sku`:** `LEGOKIT` a kit entry (537, `components` []), `TTRS` a bare product, `NOPE` 404; `/kits` is a 404.
  - **HJF, simulator:** seeded `N9-` fixtures through the control plane (the 10-01 `N36-` fixtures were gone, the simulator's data having been reset). Ten kits, each equal across the gateway, the simulator's own `stocktotalskit` and hand-derived rules: FLAT 4, SUB 8, NEST 6 (the sub-kit's 5 assembled units used first; my first hand figure of 4 forgot them), SUBSTOCK 13, FILT 0 (UNLINK component), QSTATE 0 (non-W component), ZERO 0 (zero-quantity line), CLOSED 10 (closed line ignored), CYC1 and CYC2 0 (cycle).
  - **QA step 3:** zeroing `N9-C2` behind a warm snapshot (max age 20 s) made `N9-FLAT` read 0 after 3.3 s, and it stayed listed. `N9-C2` restored afterwards.
  - **Logs:** no password in the gateway logs; derivation reasons `no_open_lines`, `zero_quantity_line` and `bom_cycle` logged. HJF `N9-` products deleted afterwards; the simulator has no kit-delete route, so the BOM rows may remain.
- 2026-10-05 [K0, K1a, K1b, K2] PRs #29 (+286/-6, 11 tests), #30 (+308/-6, 17), #31 (+317/-14, 19), #32 (+24/-104, 1). Mutations each caught: 7 on K0, 10 on K1a (one first survived because a regular product failed validation for lacking a unit, so the test now gives it one), 10 on K1b (five of the merge, five of the recorder). Gates green on each: `fmt-check`, `build`, `vet`, `test`, `test -race`, `golangci-lint` 2.14 (0 issues).
- 2026-10-01 [inc 4] fuse-mocker `d9e1b14` pushed to main, Deploy run 36885743021 green, running image confirmed as `fuse-mocker-snap-api:dev-d9e1b14` (revision 00053). Seeded `N36-` fixtures on HJF through the control plane and read them back over the SNAP wire with HJF's own credentials: `stocktotalskit` gave FLAT 4, NEST 5 (shared component), SUBSTOCK 5 (sub-kit stock first), FILT 0 (UNLINK component), QSTATE 0 (non-W component), ZERO 0, CLOSED 8, CYC1/CYC2 0, all as specified; an unknown kit is 404. `$filter=State eq 'W' and Status eq '00' and Product/Group1 ne 'UNLINK'` on `/v2/stocktotals` excluded N36-E (UNLINK) and N36-F (state Q). `/v2/kits` served 15 rows, one per component line, with DateClosed on N36-G. Script: scratchpad `n36-fixture.py` (re-runnable, upserts).
- 2026-10-01 [inc 3] `87bbbe0` on `hjf/fuse-1036-kit-derivation`: 17 tests pass, including the seven GADG kits matching SNAP's own PotentialKitQty; fmt/build/vet/test/race/lint green. The simulator's independent unit-by-unit algorithm agrees with the gateway's binary search on every hand-worked case.
- 2026-10-01 [inc 1, a] Against GADG's dev SNAP (read-only; connection from `get-snap-connection`), SNAP's own `PotentialKitQty` equals `min over open BOM lines of floor(Σ over component stock rows with State W and Status 00 of max(Qty − QtyDueOut, 0) ÷ BOM Qty)` on 6 of 8 kits: LEGOKIT 537, TTRS35 44180, XTTRS 22090, XTTRS3 6046, BATHELLTD 6046, BIRDBATH 2015. `QtyAllocated` and `QtyAssigned` are not subtracted, Status 13/01/04 rows are excluded, and rows with Qty 0 but a large due-out clamp to 0 (`@WAREHOUSE` row, due-out 224707). BATHELLTD read 6047 minutes earlier, so live stock was moving. Script: scratchpad `kitprobe.py`.
- 2026-10-01 [inc 1, b] Component-level **State and Group1 filtering could not be tested**: GADG has no stock rows with State other than W (`$filter=State ne 'W'` returned 0) and no product with Group1 `UNLINK` (values are CAIA, CODEPT1, GADG, NEW). Proving it needs a product or stock write on a real tenant, which I haven't done.
- 2026-10-01 [inc 1, c] The `stocktotalskit` list route returns **500 for any parameters, including none** (SNAP-side `DivideByZeroException` in `CalculatePotentialKitQtyByOwner`), so the owner-wide list and `$filter` on it are unusable on GADG. Per-SKU detail works for 7 of 8 kits; `EJTEST` (one BOM line, Qty 0, whose component is itself a kit) returns 500 on its own detail, while `08OTTPA4` (an open Qty 0 line plus a closed line) returns 0. `/v2/stocktotals` supports `$filter` on `SKUId`, `State`, `Status` and `Product/Group1` (200s; the Group1 filter is not yet shown to exclude anything). SNAP's front end returns 403 to Python's default user agent, while curl's passes.
- 2026-10-01 [inc 1, d] A kit with no availability still has a row (`08OTTPA4`, `PotentialKitQty` 0), a missing SKU returns 404, and kit rows for kits with no stock line of their own (BIRDBATH, BATHELLTD) return `State`, `Status`, `Site` and `Unit` all null, so row-level State/Status filters mean nothing for those and `kit.unit` must come from `/v2/kits`.
- 2026-10-01 [inc 1, e] `OwnerId` and `BizId` both equal the businessId (`GADG`).

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- Component-level State and Group1 exclusion (needs a write on a real tenant, increment 1(b)).
- Whether SNAP honours `DateClosed` and `MaintInd` on BOM lines, and what it does for nested kits (`08OTTPA4` and `EJTEST` behave differently).
- Whether the gateway-derived number tracks SNAP when those cases occur; only the six plain kits are proven.
> SUPERSEDED 2026-10-05 — K0 to K2 are built too (PRs #29 to #32); see Evidence. Increments 5 to 9 below stay superseded.
> SUPERSEDED 2026-10-02 — increments 2–4 are built; what remains unbuilt is K0–K2.
- All build increments (2–7): nothing is built.
- Whether `components` as an empty array reads as "no components" to consumers, and whether the unit fallback to the product's `ItemUnit` matches what they expect (both are the plan's working defaults, unconfirmed).
- Kit availability for a single site against SNAP: SNAP's `stocktotalskit` figure is not per site, so only the all-sites figure was compared with SNAP. The per-site figure follows the same derivation and is checked against the simulator and unit tests only.
- A BOM line closing on a future date (the gateway treats any `DateClosed` as closed), and a fractional BOM `Qty` (the generated SNAP type is a whole number): neither occurs in the data seen.
- Request count and build time for a tenant with many kits (25 kits per request, plus an empty page each), and memory for large catalogues.
> SUPERSEDED 2026-10-09 — Harry merged #32 with the removal called out in its description.
- That the maintainers want `/kits` removed (K2).

## Rollout & rollback
<!-- Added on demand. Written at plan time; amend in place as it changes.
     `Shared state touched:` is the single home for the five classes git does not own — a dev
     deploy, a prod config write, a Datadog monitor, a CI var or secret, cross-repo IaC. Reverting
     the branch undoes none of them, so if they are not written here they are not written down. -->

> SUPERSEDED 2026-10-02 — #9 merged; the order is now the [[plans/FUSE-1188-products-stock-read-with-a-paged-filtered-snapsh|FUSE-1188 plan]]'s, with K0–K2 after its increment 8.
- **Order:** increment 2 (codegen) merges first and alone, after Renovate #8 so the regenerated output isn't contested. Increments 3–6 stack behind it and behind draft PR #7 (backend resolution), which edits the same `core/stock`, `snap/request.go` and `openapi.yaml`: rebase on it or wait for it. The list shape (UNRESOLVED 4) and the `ForSKU` signature (increment 6) are agreed with the FUSE-1188 owner before either merges, because 1188 edits the same files and signatures. Increment 7 waits for 1188.
- **Flags/config:** none planned. If UNRESOLVED 5 chooses a service-wide `SNAP_CACHED_CONTENT_MINUTES` change it lives in `iac/projects/wms-gateway` and also shortens the cache on `salesorder` reads.
- **One-way doors:** the `/kits` and `/sku` response shape in `openapi.yaml`. The service is prod-deployed with no traffic, but other teams may query it, so freeze nothing until UNRESOLVED 4 is agreed. Merging a response-shape change after a consumer exists is a contract break.
- **Rollback:** increments 2–4, 6, 7 are git revert (no data, no state). Increment 5 is a revert, or a Terraform apply back if the config route is chosen. Nothing is called from prod today, so a bad route in prod affects no one.
- **Shared state touched:** the fuse-mocker snap-api simulator on dev (`crackle`), changed direct to its main and deployed by its own workflow, a cross-repo change this branch cannot revert; HJF's dev backend already points at it, so the gateway e2e needs no config write. Also a dev deploy of the gateway if verification goes through Cloud Run, plus a stock write on a real dev SNAP tenant for increment 1(b) and the QA step in increment 5. Cloud Run ingress is internal-only and `caller_service_account` is unset in both tfvars, so nothing can invoke a deployed gateway yet. Live evidence therefore comes from a local run of the real binary (`SERVICE_AUTH_DISABLED=true`, config-service dev, GADG's SNAP connection from `get-snap-connection`); binding fapi's runtime SA is separate Terraform and would need its own plan shared and agreed first.
- **Proof in prod:** none yet; no traffic. The signal once there is traffic is the `fuse.request` / `.request.failure` metrics tagged `route:/api/v1/stock/{businessId}/kits`, and `snap.response.invalid{reason}` for decode drift. Baseline is zero.

## Handback
<!-- Append-only, newest first. Written by `wp handback`, never by hand.
     Sign-off never clears this section — a refuted approach is exactly what a
     later session needs and what ## Learnings would have deleted. -->

### 2026-10-09 11:22
- **stopped:** Learnings promoted into known-context and architecture; gates confirmed against main; sign-off pending QA being a separate step
- **tried and abandoned:** Believed gen-check does not diff openapi.yaml, and that embedding a schema needs no spec edit beyond SCHEMAS. Refuted: gen-check now runs make gen (including embed-openapi) and diffs openapi.yaml, and embed-openapi.ts still throws unless the schema's marker pair is already in openapi.yaml. Also believed the adapterclient cache could not be bypassed per request (TTL 0 became 15 min); Request.NoCache now exists and stock reads use it.
- **turn:** me

### 2026-10-02 10:46
- **stopped:** #9 merged (Harry, 10-02). Increment 3 is draft PR #10 (rebased on e28042d, gates green). Increment 4 live on fuse-mocker. DM sent to Nylah 10-02 10:43 BST proposing: she owns the shared paged /v2/stocktotals read, list/paging shape and ForSKU type; we own kits on top. Increment 5 waits on her answer; don't start the shared read or touch snap/request.go (her #7 changes it) until she replies. Two prod Deploy runs (685afa6, e28042d) are parked at the terraform-prod gate; not ours to approve.
- **turn:** me

### 2026-10-01 16:42
- **stopped:** Increments 1-4 done. 3 (pure nested-aware derivation) is on hjf/fuse-1036-kit-derivation @87bbbe0, pushed, no PR yet. 4 (simulator) is live on fuse-mocker main @d9e1b14 and verified on HJF with N36- fixtures. #9 approved and green, unmerged. Increment 5 waits on Nylah: who lands the shared filtered /v2/stocktotals read; the voice-drafted DM to her is unsent.
- **turn:** me

### 2026-10-01 15:19
- **stopped:** Increments 1-2 done (PR #9 draft). Increments 3-5 are gated on human decisions: UNRESOLVED 2, 3, 4, 5, 6, 9, 10 (working defaults for 2, 3, 5, 6 were taken from recommendations, not confirmed), plus agreeing the shared stock read, list shape and ForSKU signature with the FUSE-1188 owner. Not verified: component State/Group1 exclusion in SNAP (needs a write on a real tenant). Next: answer the UNRESOLVED items, then build increment 3.
- **turn:** me

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-09** — Squash-merged shas on main: increment 2 f58593b is e28042d (#9), increment 3 91c726a is 58050ad (#10), K0 eb18b48 is 1a17f39 (#29), K1a 83752ad is d28cfc8 (#30), K1b 5671812 is e55ccb6 (#31), K2 3ae5666 is e9aa1ce (#32). Increment 4 d9e1b14 is a fuse-mocker commit on its main. The four K gates are confirmed: the parents are on main and Harry merged #32 after its description offered the choice to keep /kits.

- **2026-10-05** — K1b adds a distinct log event, Stock kit availability forced to zero, for a kit whose availability the data forces to zero (no_open_lines, zero_quantity_line, bom_cycle, bom_too_deep). The live run logged them as Stock attribute dropped, which is wrong; nothing is dropped. The event is not counted as a skipped position. One merged SKU-sorted list holds products and kits, so paging, total, the sku filter and the site scope treat both alike.

- **2026-10-05** — K0 reads kit BOM lines by naming the business's own MASTERSKU kit SKUs, 25 per request, because /v2/kits has no business field and a shared host keeps other businesses' kits in it (GADG dev host: EJTEST is not GADG's kit). Rejected: reading the host's whole kit list, and one request per kit. A failing kit read fails the snapshot build rather than serving a list without its kits.

- **2026-10-05** — K1a keeps the plan working defaults, still unconfirmed by Harry and flagged on #30: components is always an empty array (the breakdown is out of scope), and a kit unit comes from its BOM lines, falling back to its product ItemUnit, a kit with neither being skipped and reported. A BOM line is closed when its DateClosed is set, whatever the date. Availability counts the one site when a site is given, otherwise every site, using only stock that passes the ILG filter.

- **2026-10-05** — The kit work shipped as four stacked PRs on top of the FUSE-1188 stack (native GitHub stack 21; kits are #29 K0, #30 K1a, #31 K1b, #32 K2). The plan gates on FUSE-1188 increments 4, 5, 8 and 9 landing are met by those PRs being beneath these in the stack, not by their merging; confirm the gate boxes when the parents merge. K2 rests on the gate that Harry agrees to drop /kits, taken from the instruction to get everything out and called out on #32.

- **2026-10-02** — Re-planned 2026-10-02 with FUSE-1188 (now ours): increments 5-9 moved verbatim under ## Superseded increments and replaced by K0 (kits = MASTERSKU products, BOMs via the 1188 pager, filtered to this owner on the shared host), K1a (kit positions, pure), K1b (kits in the list and ForSKU, all live checks carried over: N36 fixtures, GADG six kits, QA step 3) and K2 (remove /kits, Harry's call). The Nylah gate on the shared stock read is gone. 91c726a lives only on #10's branch until it merges; after a squash merge it won't be reachable from main, which sign-off should treat as expected. When #10 merges, repoint this plan's branch and pr to K0's, or wp will read it as finished. UNRESOLVED 3 (unit from /v2/kits, components []) stays a working default Harry has not confirmed.

- **2026-10-02** — #9 merged by Harry 2026-10-02 08:57 (e28042d). The plan's branch, worktree and pr now point at increment 3's PR #10 (hjf/fuse-1036-kit-derivation), so wp no longer reads #9's merge as the plan being finished. Jira moved back to In Progress.

- **2026-10-02** — Increment 3 rebased onto main after #8 and #9 merged (Harry merged #9 2026-10-02 08:57); its commit is now 91c726a. wp tick appended the new stamp beside the old 87bbbe0 instead of replacing it, so the stale stamp was removed by hand.

- **2026-10-01** — Increment 4's sha d9e1b14 is a fuse-mocker commit on its main (no PR flow there), not a wms-gateway commit, so sign-off's sha-in-branch check will flag it; that is expected. The simulator gained more than planned: /v2/kits had the wrong shape (the stored BOM doc, not one row per component) and stock rows had no embedded Product, so both were fixed to match real SNAP. No fleet service reads either route today. STKS seeding was not needed; fixtures live on HJF.

- **2026-10-01** — Increment 3 built on its own branch hjf/fuse-1036-kit-derivation off origin/main (057d19e), not on #9's approved branch: it needs none of #9's types. TestAllocatedQuantityIsNotSubtracted moves to increment 6, because the core stock row carries no allocated field and the rule only exists in the SNAP-row mapping. Added TestTopLevelKitOwnStockIsNotAdded, TestSubKitWithNoOpenLinesCanOnlyUseAssembledStock and TestSharedSubKitStockIsSpentOnce. Real data supports the own-stock rule: GADG's 08OTTPA4 holds 1000 assembled and SNAP reports 0. Correction to my 'STKS for fixtures' advice: the gateway e2e reads whatever business its backend config names, so the nested fixtures must live on HJF, created through the simulator's /api/v1 control plane; STKS seeding is not needed.

- **2026-10-01** — Plan file rebuilt 2026-10-01: an earlier rollout edit spliced a second copy of the body in after the heading text inside the template comment; the stale copy is dropped and the Decisions and Handback sections re-homed. Increments renumbered: pure nested-aware derivation is 3 (no gate, in-repo), the fuse-mocker simulator uplift is 4, adapter reads 5, mapping and use-case 6, /kits 7, ForSKU 8, merge 9. Nine increments is over the preferred seven; the ticket is big and the plan says so rather than hiding it. UNRESOLVED 6 decided by me, not Harry: extend normalizeUnions so optional-nullable snap-package fields generate as pointers, since FUSE-1188 needs the same shape.

- **2026-10-01 (Harry)** — Harry confirmed 2026-10-01: nested-kit semantics as proposed (shared leaf demand summed across paths; assembled sub-kit stock used first, the top-level kit's own assembled stock not added; a cycle or a BOM deeper than the cap returns 0, is logged as its own event, and the kit is still returned). Closed BOM lines are ignored and a kit with no open lines returns 0 (UNRESOLVED 10 closed). A component failing the ILG filter counts as zero availability, so the kit reads 0; a kit whose own SKU fails the filter is excluded (UNRESOLVED 2 closed). The real-gateway e2e runs against HJF, whose backend points at the fuse-mocker snap-api simulator; fixtures live on the STKS seed business. Simulator changes go direct to fuse-mocker main (dev-only).

- **2026-10-01 (Harry)** — Nested kits are handled properly and fully, not zeroed (Harry, 2026-10-01). SNAP's own behaviour is unobservable (EJTEST 500s), so the semantics are ours to write down and the fuse-mocker snap-api simulator becomes the e2e oracle; Harry is happy for simulator changes to go to its main (dev-only). Semantics still to confirm: shared leaf demand summed across paths, assembled sub-kit stock used first, cycle or over-depth returns 0 and is logged.

- **2026-10-01 (Harry)** — Confirmed by Harry 2026-10-01: (UNRESOLVED 9) match SNAP's own PotentialKitQty, i.e. floor(sum of max(Qty - QtyDueOut, 0) over State W / Status 00 rows / BOM Qty), min across components, allocated and assigned not subtracted. (UNRESOLVED 10, part) a BOM line with Qty 0 makes the kit return 0, never 500. Still open: how closed BOM lines are read (ignore the line vs kit returns 0), nested kits, and what a fully filtered kit returns.

- **2026-10-01** — Increment 1 outcome: derive potentialKitQty in core from /v2/kits plus one filtered /v2/stocktotals read, NOT a pass-through of stocktotalskit. Why: its list route 500s on GADG, State/Group1 filtering is unprovable there, and the derivation reproduces SNAP's own number on 6/8 kits. Supersedes the pass-through default, the 'unit from stocktotalskit' default (Unit is null on stockless kits) and SnapStockTotalKit as a codegen target. Increments 3-5 rewritten in place; freshness folded into 5.

- **2026-10-01** — Activated on 'action the draft' without answers to UNRESOLVED 1-8. Working defaults taken from the plan's recommendations, NOT confirmed answers: 1 kits-only on /kits interim, 2 fully-filtered kit returned as 0 when the kit passes its own filters, 3 unit from stocktotalskit and components [], 5 align with 1188's snapshot, 6 extend normalizeUnions. 4, 7, 8 stay open and gate increments 4, 6 and the shared-module question. Starting with increments 1 (reads only) and 2.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
