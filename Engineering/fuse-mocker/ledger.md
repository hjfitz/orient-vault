---
tags: [waypoint, ledger]
title: fuse-mocker — work ledger
---
# fuse-mocker — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-10-02 — FUSE-1188

snap-api simulator: stock reads behave like real SNAP

Stock totals split by facility and state (SetLevel takes facility, orderIn, orderOut, dueIn); every read reports 'Successes: n/n' including empty ones; $orderby on an unknown stock-total field is a 400 with SNAP's wording; embedded Product carries the product's own Group1 and a fallback Description; products seed with group1/group2 (MASTERSKU kit products). Direct to main (dev-only), commit f9e349e, deployed. Needed so the wms-gateway paged stock read can be exercised through HJF.

Commit: gfs-bifrost/fuse-mocker f9e349e (direct to main, no PR)

## 2026-10-01 — FUSE-1036

snap-api kits and stock totals read like real SNAP, nested kits included

For the wms-gateway's kit availability work, the snap-api simulator now behaves like real SNAP on three routes: /v2/stocktotals embeds the Product (carrying Group1) and always has QtyDueOut, and $filter takes ne and Product/Group1 paths; /v2/kits serves one row per component line (it used to serve the stored BOM doc); /v2/stocktotalskit uses SNAP's own formula (Qty minus QtyDueOut, clamped per row, State W / Status 00 / non-UNLINK, allocated not subtracted) and resolves nested kits (sub-kit stock first, shared components spent once, cycle/depth/zero-line/no-open-lines give 0), with a 404 for an unknown kit. Control plane: kit unit, explicit qty 0, closed lines; stock state and dueOut. SellableStock removed (no other caller). Verified live on HJF with N36- fixtures. No fleet service read /v2/kits or /v2/stocktotalskit from the simulator before this, so the shape fix broke nobody; the poller's coming stock sync (FUSE-1195) reads /v2/stocktotals and the change there is additive.

Commit: gfs-bifrost/fuse-mocker@d9e1b14 (direct to main, no PR flow)

## 2026-09-30 — snap-api simulator serves the poller's new Snap reads (per-line moves, pick moves, Stock Detail batch/expiry, R10↔S10)

snap-api simulator serves the poller's new Snap reads (per-line moves, pick moves, Stock Detail batch/expiry, R10↔S10)

Direct to main: 9d15612 (per-line /v2/stockmovements/{site}/{type}/{moveId}/{line}; filtered stockmovements list ToAssignType/ToAssignRef; pick moves on first shipment advance; multi-line stock adjustments with batch/expiry; R10 minted once with Prime = S10 ShipmentId and only the finished good expected; IC consignment rows with BatchId; openapi lines/batch/expiry/batches), 642efa6 (Stock Detail rows carry every SnapStockDetailSchema column — without it the poller's Stock Detail read failed), 9ec3dd2 (receipt/shipment completion dates — without them FGR had no documentDate). Proved FUSE-1088 / FUSE-1258 / FUSE-1253 inc 6 end to end for HJF through the real poller + sftp EDIFACT. Gotcha: mocker-created records carry source mock/mock-sftp, which sftp's FGR/WOC subscriptions (source=sftp or broadcast) never match — set the backend broadcastConfirmations for a mock-driven run.
