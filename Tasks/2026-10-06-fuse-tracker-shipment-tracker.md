---
tags: [adhoc-task]
date: 2026-10-06
tldr: "Built fuse-tracker, now tracking-service: shipments and returns tracker, productionised, with the fuse-ui order tracker as an L2 work queue. Tracked as the Bifrost/Tracking Service programme"
session_id: b7f195f7-c12d-4677-87e4-6f4416a0869e
status: open
---
# Build the fuse-tracker shipment tracker

## Outcome
Started as a skunkworks tracker (2026-10-05) and is now the team service `gfs-bifrost/tracking-service`, backfilled into orient as the **Bifrost/Tracking Service** programme (26 units: 12 merged, 3 in progress; progress lives in its Migration State). Live in prod on the legacy stack: shipments and returns, support views, a read-only MCP, and the fuse-ui order tracker at `/order-tracker` (fuse-ui #287, #289, #290, #291, #292).
Still owed: Harry's sign-off on the cutover plan (the new `tracking-service` stack is planned, not applied), the per-connector confirmation status ship decision, the UX-review fixes, and date sorting (waits for the cutover).
