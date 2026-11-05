---
tags: [waypoint, ledger]
---
# wms-gateway — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-05 — Run wms-gateway on the golden runtime image

Run wms-gateway on the golden runtime image

Moved the gateway image from distroless/static to ilg-platform's go-runtime:0.1-affogato (Datadog serverless-init as entrypoint) and dropped the Datadog sidecar, shared volume and the held-file log sink; DD_* env moved onto the app container with the same values, logs stdout-only, boot metrics emitted immediately. Fleet golden-image migration, following audit-service#16 / dedupe-service#167. Draft; branch deployed to dev and verified (one container, dd.datadog_init_version logs, coldstart/request metrics, stock reads 200).

PR: gfs-bifrost/wms-gateway#42

## 2026-10-09 — FUSE-1036

Return kits beside products with a derived potentialKitQty, and drop the kits-only route

Kits are canonical type kit stock positions in the same snapshot-backed list and /sku/{sku} as products. A kit is a product with Group2 MASTERSKU; its BOM lines come from /v2/kits read by naming the business's own kit SKUs, 25 per request (the shared host keeps other businesses' kits there). potentialKitQty is derived in core/stock/kits.go, not from /v2/stocktotalskit (its list route 500s on GADG): min over components of floor(sum of max(Qty - QtyDueOut, 0) over State W, Status 00, non-UNLINK stock / BOM Qty), nested kits included, closed lines ignored, a zero-quantity line, cycle or no open lines gives 0 and is logged; a kit failing the ILG filter is absent, a zero-availability kit is still listed. A kit SKU in sku= or /sku/{sku} returns the kit entry only. GET /stock/{businessId}/kits is removed. Also: CanonicalStockPosition arm types generated (#9), derivation (#10), simulator parity in fuse-mocker. Paths: apps/gateway/internal/core/stock/{kits,kitpositions}.go, internal/adapters/snap/stock.go, apps/gateway/openapi.yaml. [[architecture]] [[known-context]]

PR: gfs-bifrost/wms-gateway#32

## 2026-10-09 — FUSE-1188

Serve a business's stock list and one SKU's position from a per-business snapshot

Stock read for the Get Stock API, shipped as a stack: paged SNAP stock-total and product reads with a pager that dedupes on SKU+Site+Facility+OwnerId+Status+State and never uses the response cache (#16), rows to canonical product positions with the ILG filters, catalogue-only positions and zero-quantity SKUs (#17), per-business snapshot store (#15) wired into ForBusiness (#19), the paged list contract {total, offset, count, data} with offset/count/sku/site and Last-Modified in openapi.yaml (#20), and GET /stock/{businessId}/sku/{sku} from the same snapshot (#28). Also Request.NoCache (#14), generated SNAP stock-total and kit types with gen-check covering openapi.yaml (#13), and simulator parity in fuse-mocker. Max age 270 s, build timeout 50 s: a build timeout is 504, SNAP failure or open circuit is 502, an empty business is a 200 with data []. Paths: apps/gateway/internal/core/stock, internal/adapters/snap/stock.go, internal/http/controllers/api/v1/stock.go, apps/gateway/openapi.yaml. [[architecture]] [[known-context]]

PR: gfs-bifrost/wms-gateway#28

## 2026-10-05 — FUSE-1036

Remove the kits-only stock route

GET /api/v1/stock/{businessId}/kits, its controller method, the UseCase stub and the openapi entry are removed (404). Rests on the plan gate that Harry agrees; called out on the PR.

PR: gfs-bifrost/wms-gateway#32

## 2026-10-05 — FUSE-1036

List kits beside products and serve a kit by its SKU

stockData.positions merges product and kit positions sorted by SKU, so the list, total, sku filter, site scope and /sku/{sku} treat both alike; a kit is one entry even with its own stock. New log event Stock kit availability forced to zero (recorder branches on potentialKitQty). Live: GADG kits equal SNAP stocktotalskit, HJF fixtures equal the simulator.

PR: gfs-bifrost/wms-gateway#31

## 2026-10-05 — FUSE-1036

Map kits to canonical kit positions with a derived availability

kitPositions (core/stock/kitpositions.go) builds one kit position per MASTERSKU product the ILG filter keeps from its BOM lines and W/00 stock via the nested-aware potentialKitQty; unit from the BOM lines then the product ItemUnit (else skipped); DateClosed set = closed; components always []; reasons other than computed are returned as Issues. Position gains a kit arm.

PR: gfs-bifrost/wms-gateway#30

## 2026-10-05 — FUSE-1036

Read the business's kit BOM lines in the stock snapshot

The snapshot build also reads the BOM lines of the business's MASTERSKU kits via Adapter.KitLines (adapters/snap/kits.go), naming the kit SKUs (25 per request, ProductKitId eq X or ...) because /v2/kits has no business field and a shared host keeps other businesses' kits. A failing kit read fails the build; no kits means no read. Nothing served yet.

PR: gfs-bifrost/wms-gateway#29

## 2026-10-05 — FUSE-1188

Serve one SKU's stock position from the same snapshot

UseCase.ForSKU (core/stock/list.go) returns the business's one position for the SKU, summed across sites, from the snapshot ForBusiness uses (shared lookup), plus the snapshot start for Last-Modified; binary search over the SKU-sorted positions; unknown SKU, UNLINK product or a SKU outside the catalogue is exceptions.NotFound -> 404. GET /api/v1/stock/{businessId}/sku/{sku} is a bare canonical record; openapi.yaml, README and CLAUDE.md updated. Path-only: for one site use the list with sku and site. Live on GADG and HJF. Top of the FUSE-1188 part of the stack; the FUSE-1036 kit PRs sit on it.

PR: gfs-bifrost/wms-gateway#28

## 2026-10-05 — FUSE-1188

Publish the stock list contract and its query parameters

GET /api/v1/stock/{businessId} takes offset (default 0), count (1-100, default 20), a repeated sku (max 100) and an optional site, and returns {total, offset, count, data} with bare canonical stock positions, Last-Modified = the snapshot's start. Bad parameters are a 400 naming the parameter (exceptions.InvalidQuery). openapi.yaml declares the parameters, StockPage, the 400/504 responses and the header; README and CLAUDE.md no longer call the list a stub. The contract is a one-way door once fapi consumes it. Top of the #16 -> #17 -> #19 -> #20 stack (GitHub stack 21).

PR: gfs-bifrost/wms-gateway#20

## 2026-10-05 — FUSE-1188

Serve a business's stock list from a per-business snapshot

stock.UseCase.ForBusiness (core/stock/list.go) resolves the backend, then pages a per-business snapshot of SNAP's products and W/00 stock totals (SnapshotStore from #15, rebuilt past STOCK_SNAPSHOT_MAX_AGE_SECONDS). Positions are memoised per snapshot and site; Page carries total/offset/count/data and AsOf. Skipped or trimmed products are reported once per build through observability.StockPositionRecorder (log + wms_gateway.stock.position.skipped). A build past its deadline is a 504 (ErrUpstreamTimeout), no stock is an empty page. Live on GADG real dev SNAP and HJF: 102 positions matching an independent read. Same live run exposed a cross-business leak in the rows-to-positions mapping (other businesses' products on stock rows with BizId GADG), fixed in #17: the business-filtered catalogue is the only source of positions. Stacked on #16 and #17; serves the default page until #20.

PR: gfs-bifrost/wms-gateway#19

## 2026-10-05 — FUSE-1188

Map SNAP stock rows and products to canonical product positions

Pure core mapping in core/stock (products.go, position.go): productPositions(catalogue, stock rows, site) returns one Position per catalogue product sorted by SKU, quantities summed across sites or taken from one (onHand=Qty, allocated reported not subtracted, orderOut=QtyOrderOut, dueIn=QtyDueIn). A product with no stock is listed at 0; MASTERSKU kits and Group1 UNLINK are not positions; a null Group1 passes. An invalid optional attribute (fractional boxQty or life) is dropped and the position kept; a missing required field skips it; both are returned as Issues for the caller to log. Only attributes with a documented canonical counterpart are mapped (not nmfcCode, values, dateHeld). Real GADG data: 106 rows + 71 products -> 97 positions, 0 issues, totals match an independent oracle. Increment 8's HJF live check corrected: a Q-only SKU is at 0, not absent.

PR: gfs-bifrost/wms-gateway#17

## 2026-10-05 — FUSE-1188

Read a business's stock totals and products from SNAP, paged

Adapter.StockTotals (Status 00, State W, BizId) and Adapter.Products read SNAP sequentially and uncached, $orderby SKUId,Site,Facility,OwnerId, stop on an empty page. $skip advances by rows received, not rows asked for, so a SNAP page cap below 500 loses nothing. Any failing page fails the read (one breaker fault per read); passing the 200-page ceiling is an error, never a partial result; a row repeated across pages counts once (SKU+Site+Facility+OwnerId+Status+State). Group1 is left to core so a null Group1 passes. decodeResults[T] now shared with GetShipment, pinned first. Live on GADG dev: 106 rows / 82 SKUs, matching an independent read. Open: successive failed snapshot rebuilds can still accumulate breaker faults. Paths: apps/gateway/internal/adapters/snap/{stock,request}.go.

PR: gfs-bifrost/wms-gateway#16

## 2026-10-02 — FUSE-1188

Keep a per-business stock snapshot never older than its max age

Increment 6 of the FUSE-1188 plan. core/stock/snapshot.go: a generic per-business SnapshotStore, rebuilt on demand once older than STOCK_SNAPSHOT_MAX_AGE_SECONDS (270) counting from the build's start; one shared detached build per business under STOCK_SNAPSHOT_BUILD_TIMEOUT_SECONDS (50) that also covers the wait for one of STOCK_SNAPSHOT_MAX_CONCURRENT_BUILDS (1) slots; failed builds never cached, expired snapshots never served, a timeout is exceptions.ErrUpstreamTimeout. Reported through an observer the observability layer implements, keeping core free of observability. One snapshot per instance, so pages can skew by up to the max age. Not called yet. [[architecture]]

PR: gfs-bifrost/wms-gateway#15

## 2026-10-02 — FUSE-1188

Let a request skip the SNAP response cache

Increment 3 of the FUSE-1188 plan. adapterclient.Request.NoCache (context-carried so get keeps its signature): not served from or written to the LRU, not a CacheLookup, still takes a limiter slot and goes through the breaker, own singleflight key so it never joins a cached flight. No caller yet; the stock read is the first. [[operations]]

PR: gfs-bifrost/wms-gateway#14

## 2026-10-02 — FUSE-1188

Generate SNAP stock-total and kit types; gen-check covers openapi.yaml

Increment 2 of the FUSE-1188 plan. canonschema reads @gfs-bifrost/snap/types after @gfs-bifrost/types (both export a different SnapProductSchema) and generates SnapStockTotalJson and SnapKitJson with optional-nullable fields as pointers, via a NULLABLE_AS_POINTER set limited to those roots (widening it breaks SnapShipment.CustomerOrder through ptr.FromAny). openapi.yaml gains the CanonicalStockPosition schema; make gen now runs the embed and gen-check diffs openapi.yaml, whose path was missing from gen-check.yaml's filter. SnapStockTotal's embedded product requires DateHeld, which real rows lack: harmless while the adapter decodes weakly, a trap if anyone json.Unmarshals into it. [[architecture]]

PR: gfs-bifrost/wms-gateway#13

## 2026-10-02 — FUSE-1036

Derive potentialKitQty in core, including nested kits

Increment 3 of the FUSE-1036 plan. internal/core/stock/kits.go: usableBySKU (Qty minus QtyDueOut clamped per row on W / 00 / non-UNLINK rows, matching SNAP) and potentialKitQty, a binary search over total leaf demand so a component shared by two paths is counted once; sub-kit assembled stock is spent first, the kit's own stock is never added, and a cycle, depth over 8, a zero-quantity line or no open lines gives 0 with a reason. Seven GADG kits recorded from dev SNAP reproduce SNAP's own number. Not yet called: the adapter reads and use-case come next, blocked on agreeing the shared /v2/stocktotals read with FUSE-1188. The fuse-mocker simulator implements the same rules with a different algorithm (d9e1b14), which agrees on HJF's N36- fixtures.

PR: gfs-bifrost/wms-gateway#10

## 2026-10-01 — FUSE-1036

Generate CanonicalStockPosition product and kit arm types

Increment 2 of the FUSE-1036 plan (kits with derived potentialKitQty). go-jsonschema writes an empty file with no error for a root oneOf, so canonschema now splits a root union into one schema per arm (UNION_ROOTS in tools/canonschema/src/index.ts). Adds CanonicalStockPositionProductJson and CanonicalStockPositionKitJson. components has no omitempty, so a nil slice marshals to null and still validates; emit a non-nil []. Live check on GADG found that stocktotalskit's list route 500s and PotentialKitQty is reproducible from /v2/kits + /v2/stocktotals, so the kit read will derive in core; see the plan's Verification. [[architecture]]

PR: gfs-bifrost/wms-gateway#9
