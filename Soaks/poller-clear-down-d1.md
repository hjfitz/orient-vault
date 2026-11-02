---
tags: [soak-test]
status: running
programme: Poller Clear-Down
unit: D1
started: "2026-10-05T13:02:00Z"
next_checkpoint: "2026-10-14T09:00:00Z"
subjects: [BYOMA, WILDSMITH, EPARFUM, SPORTLUX, DOCKBAY, SAIRA, STUBBLE]
queued: []
monitors: [327518496]
verdict: "Closed 2026-10-12: D1 complete (all polled, live businesses clear after publish; allow-list removed) and D2 shipped. First reconciliation clean, zero clear_failed. Owed: redrive 9 SAIRA confirmations; first prod broadcast clear unseen"
---
# Poller clears routed confirmations after publish (D1)

The SNAP poller clears a routed outbound-queue row as soon as it has published the confirmation, rather than waiting for snap-adapter's clear-down on `confirmation_made`. It is on per business through Terraform `clear_after_publish_business_ids` (snap-adapter `iac/projects/snap-queue-polling-service/variables.tf`). Programme: [[Bifrost/Poller Clear-Down/Migration State|Poller Clear-Down]].

## In the soak

| Business | Live from | Change | Notes |
|---|---|---|---|
| BYOMA | 2026-10-05 13:02Z | snap-adapter#281 (`f441460`) | One SFTP connector; also real SNAP's repeat-PATCH check (G2) |
| WILDSMITH | 2026-10-05 13:02Z | snap-adapter#281 | One SFTP connector |
| EPARFUM | 2026-10-05 13:02Z | snap-adapter#281 | One SFTP connector (goods-in and goods-out) |
| SPORTLUX | 2026-10-07 19:28Z | snap-adapter#282 (`b7859ab`) | Released alongside FUSE-1195 before its QA (Harry's call); poller revision `00090-cwr` |
| DOCKBAY | 2026-10-07 19:28Z | snap-adapter#282 (`b7859ab`) | First REST (fapi) business |
| SAIRA | 2026-10-09 12:41Z | snap-adapter#287 (`0392b2b`) | One Shopify connector (sales_order, goods_out_confirmation). Only goods-out is cleared; every other routed type skips as `no_subscription`. Poller revision `00091-ldp` also carried the types `^10.12.0` Renovate bumps |
| STUBBLE | 2026-10-09 13:09Z | snap-adapter#288 (`b48b0c1`) | One SFTP connector. Highest volume, on ilg005 (clear timeouts). Hold lifted: the "157 poisoned docs" were fleet-wide and repaired 09-24; STUBBLE has 6,488 `source=sftp` docs, 28 with no `source` (resolved from the connector) and none stamped `snap-adapter`. Poller revision `00092-x8j` |

## What passing looks like

- Per business: `snap.outbound.cleared` equals the routed records published (`snap.outbound.clear_skipped` only for expected reasons).
- `snap.outbound.clear_failed` stays at zero; monitor `327518496` stays No Data/OK.
- No duplicate claims (`confirmation-claim` collisions), so no row re-announced after clear.
- Downstream consumers processed the pushes; replay holds no new confirmation failures for these businesses; snap-adapter logs no `Confirmation clear-down failed` for them.

## Rollback

Remove the business from `clear_after_publish_business_ids` and release the poller. snap-adapter's clear-down still clears made rows, so nothing is stranded.

## Checkpoints

- **2026-10-07 — two-day review: clean.** EPARFUM 130 goods-out + 1 goods-in, WILDSMITH 51, BYOMA 7 cleared, each equal to published. Zero `clear_skipped`, zero `clear_failed`, monitor No Data. Zero prod duplicate claims, no breaker changes, no poll failures. sftp-connector processed 112 / 47 / 7 pushes (per push, not per record). No replay confirmation failures; no snap-adapter clear-down failures, so the repeat clear after `made` is harmless on real SNAP. Not checked: the live SNAP outbound queue (prod SNAP read blocked).
- **2026-10-07 19:28Z — SPORTLUX and DOCKBAY joined.** Poller `b7859ab` live in prod (revision `00090-cwr`), allow-list now five businesses. The same release shipped FUSE-1195 un-QA'd (Harry accepted), raising the poller's request timeout to 600s and `stock_sync_due`'s ack deadline to 600s. snap-adapter `9e09021` (proxy-addr fix, types ^10.9.0) went out earlier the same day.
- **2026-10-09 ~12:30Z — four-day review: clean.** Since 10-07 12:00Z, `snap.outbound.cleared` plus `broadcast` skips equals `fuse.confirmation.published` for every business. From 19:30Z on 10-07: SPORTLUX 71/71, DOCKBAY 373/373, EPARFUM 98+6, WILDSMITH 34 (+2 goods-in skipped as `broadcast`), BYOMA 8+2 (+1 `broadcast`). The three `broadcast` skips are by design and are the first skips seen. Zero `clear_failed`, no "Outbound queue clear failed" or snap-adapter "Confirmation clear-down failed" logs, monitor `327518496` still No Data. `fuse.confirmation.failure.emitted` is empty for all five; duplicate claims appear only for GADG and ACADEMIC (not allow-listed). Not checked: replay read directly, the live SNAP outbound queue, and whether the three `broadcast` rows reached `made`.
- **2026-10-09 12:41Z — SAIRA joined** (snap-adapter#287, poller revision `00091-ldp`, allow-list now six). Prod plan: 1 in-place change, shared and approved. SAIRA had a goods-out re-announce loop ("Line item has no fulfillment ID", three orders, ~375 publishes/day since 10-05, 2,073 replay failures), which I expected the clear to end. It had already stopped at ~12:26Z, before the deploy, for a cause I haven't found. So SAIRA's first real clear is still unseen. Watch for it on the next goods-out. A first watcher filtered on `businessId`, which is a comma-joined chunk in these logs; filter on `customers`.
- **2026-10-10 — next (proposed):** re-run the numbers, and look for SAIRA's first goods-out clear and any `no_subscription` skips.
- **2026-10-09 13:09Z — STUBBLE joined** (snap-adapter#288, poller revision `00092-x8j`, allow-list now seven). Plan: the same 1 in-place change as SAIRA, shared and approved. First evidence for SAIRA under D1: `stock_adjustment` rows skip (4 published, 3 skipped, nothing cleared), so its stuck stock move adds nothing to replay. No goods-out for SAIRA or STUBBLE had appeared by 13:16Z (a quiet Friday afternoon), so neither first clear is seen yet. Still to look for: their first goods-out clear, any `clear_failed` for STUBBLE (ilg005 timeouts), and SAIRA's `no_subscription` skips.
- **2026-10-09 ~15:00Z — the 15 stamped routing docs repaired.** `routing.source` deleted on BYOMA 13, EPARFUM 1 and MANUCURIST 1 (each kept its `connectorId`, so the poller resolves the channel from the connector); a re-query finds none stamped `snap-adapter`. Backup of the 15 docs: `Bifrost/Poller Clear-Down/Findings/routing-docs-source-repair-backup-2026-10-09.json`. Cause (BYOMA traced): failures stored before the FUSE-1238 fix carry `metadata.source=snap-adapter`; a redrive from fuse-ui re-sends it (09-29 14:07:37Z, 09-30 11:57Z) and snap-adapter stores it unguarded. **Still open:** held failures keep the stamp and a redrive will re-poison; snap-adapter `persistRoutingMetadata` (`event.controller.ts:435`) has no guard.
- **2026-10-12 — weekend review (10-09 13:09Z to 10-12 ~08:00Z): clean for all seven.** Published = cleared + skips, record for record: STUBBLE 435/435 (no ilg005 clear timeouts), DOCKBAY 363/363, EPARFUM 110 = 109 + 1 `broadcast`, WILDSMITH 24 = 23 + 1 `broadcast`, SPORTLUX 6/6, BYOMA 3/3, SAIRA 406 = 57 goods-out cleared + 349 `stock_adjustment` skips (the stuck stock move, re-announced as expected; no `no_subscription` skips seen). So both SAIRA's and STUBBLE's first real clears happened. Zero `clear_failed`; monitor `327518496` still No Data; no "Outbound queue clear failed" or "Confirmation clear-down failed" logs. **Owed:** SAIRA goods-out `14510735327607` and `14507353145719` failed at Shopify ("Line item has no fulfillment ID") at 10-09 15:38Z, one failure each and no loop. That is D1 working as designed, but the rows are now cleared, so those two confirmations sit only in replay and need a routing-doc repair plus a replay retry. SAIRA's replay growth since 10-09 (2,073 → 2,303) is mostly create-side order `#37149` (ShipAddress.Line1 > 50 chars, every 5 min), unrelated to D1. Not checked: the live SNAP outbound queue.

- **2026-10-12 ~15:15Z — soak closed: D1 complete, D2 shipped.** PURDYFIGG joined (#290), then the allow-list was removed and broadcast/channel-only groups are cleared too (#291, poller `00094-bcj` 14:50Z), then snap-adapter's `confirmation_made` clear-down was retired (#292). First ~25 min: published = cleared + `stock_adjustment` skips for every business (PURDYFIGG 34 = 23 + 11, WILDSMITH 6/6, STUBBLE 2/2, DOCKBAY 1/1, SAIRA 1 = 0 + 1), `clear_failed` 0. Monitor `327518496` still covers clear failures. Owed: the 9 SAIRA goods-out confirmations in replay (waiting on Harry's go to redrive now FUSE-1118 is in prod); first prod broadcast clear not yet seen.
- **2026-10-12 15:42Z — stock adjustments clear too** (#293, poller `00095-dcf`). First poll cleared PURDYFIGG's 11 open stock moves and SAIRA's 1; 0 skips, 0 `clear_failed`, 0 claim-blocked entries since. SAIRA's 9 goods-out redriven from replay at ~15:13Z: all 9 fulfilled in Shopify, 12 extra lines skipped (6 orders × 1, 3 × 2), failures resolved. D3 decision at the 10-14 checkpoint.
