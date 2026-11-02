# Kit Confirmations & Short-Ship (FUSE-785)

Shopify-connector handling for **kit orders** (SnapFulfil BOM-exploded kits). Ticket [FUSE-785](https://globalfreight.atlassian.net/browse/FUSE-785); the consumer cutover was FUSE-1057.

## Context
- A kit (e.g. `XTTRS` = 2× `TTRS`) is one sellable line on Shopify, but SNAP explodes it into component lines on despatch. The **master** line carries the Shopify reference; components carry `role: kit_component`.
- shopify-connector filters out `kit_component` lines and fulfils the master line — kits fulfil as the ordered item; components never hit the Shopify fulfilment.

## The two SIT edge cases (Thomas Dunn, 2026-08-10)
**Case 1 — partial / short-shipped kit → was a real bug, now fixed.**
- `XTTRS` (=2× `TTRS`), only 1 `TTRS` picked → SNAP master line `QtyShipped 0`. After the component filter the only surviving line nets qty 0 → tripped the "no valid fulfillment line items" throw → `confirmations.failure`, no Shopify update, one-shot (not looping).
- Correct outcome is to leave the order **unfulfilled** (can't ship half a kit) — but it isn't a *failure*. Now: ack cleanly + support warn + `confirmations.nothing_to_fulfill` metric + an `ILG_SUBSTITUTED` order tag for CS.

**Case 2 — kit amended in SNAP → working as designed.**
- CS swaps a component (`XTTRS` → 1× `TTRS` + 1× `TTRS2`); master ships 1 → Shopify fulfils the ordered `XTTRS` line. Correct.
- Concern: a downstream 3rd-party inventory app decrementing components off the *Shopify-side* BOM could imbalance stock. That's **BOM divergence** between SNAP and Shopify — a business / T&Cs matter, not a connector defect.

## Key Shopify limitation (the crux)
Partial fulfilment already works wherever Shopify can represent it:
- **Multi-kit** order → ship 1 of 2 kits → *partially fulfilled*.
- **Mixed** order (kit + standalone SKUs) → standalone lines fulfil, incomplete kit stays unfulfilled.

The **only** unrepresentable case is a **solo single kit that's incompletely picked**: the order line is one *atomic* kit unit and Shopify fulfilment quantities are whole integers — there's no "half a kit". That solo case is the short-ship path we tag rather than fulfil.

## The tag
- `ILG_SUBSTITUTED` — product-preferred CS-facing label (renamed from the initial `ILG_SHORT_SHIPPED` after Jack Bailey's steer, 2026-08-11).
- Additive annotation on the order-tag state machine — coexists with `ILG_RECEIVED` / `ILG_ERRORED` / `ILG_FULFILLED`, and is cleared by a later fulfilment. Opt-in per connector via `outboundTagsEnabled`.
- Internal signals keep the technical short-ship naming (`confirmations.nothing_to_fulfill`, warn) — only the CS-facing tag uses the business term.

## State (2026-09-07)
- **Both sides are now merged.** [FUSE-785](https://globalfreight.atlassian.net/browse/FUSE-785) landed as shopify-connector [#214](https://github.com/gfs-bifrost/shopify-connector/pull/214) (`c00b8d1`), and the consumer cutover [FUSE-1057](https://globalfreight.atlassian.net/browse/FUSE-1057) as [#254](https://github.com/gfs-bifrost/shopify-connector/pull/254) (`f9ffaaf`). Both tickets are Ready for QA.
- **Not live yet.** Two `shopify-connector` Deploy runs are parked at the `terraform-prod` approval gate, one per merge. Prod is still on the pre-merge build until the `f9ffaaf` run is approved — and approving an older parked run would deploy older code.
- Producer side was already merged before this: types 9.0.0 (`CanonicalLineRole`) + snap-adapter #169 (poller stamps `role`).
- Prior state (2026-08-11): PR #198 open and CI-green, deployed to dev (`d69aa53`) for SIT, shared to #bifrost-forge with a SIT note to Jack + Tom.

## Owed
- Approve the `f9ffaaf` `terraform-prod` run so QA is testing the merged code rather than the old build.
- SIT partial-kit run → capture the `ILG_SUBSTITUTED` tag landing on a real order (last PR evidence).
- Confluence changelog row + the first #bifrost-forge post still say `ILG_SHORT_SHIPPED` — **now due**, since the merge has happened.
- Rewrite the FUSE-785 ACs — they assume a Snap `/v2/kits` BOM roll-up; we shipped the on-wire `role` discriminator instead.

## Low-hanging connector cleanups spotted (deferred — see [[Shopify Connector Rearchitecture]])
- **Logger drops metadata** on the 3-arg `logger.error(msg, stack, meta)` form (Winston, no `splat` format). Fixed one site (`Confirmation failed`); still live in `confirmation-processing.filter.ts` — the error path silently loses the payload + reason. Fix at the logger class, not per-call.
- **Dead colliding metric** — `METRIC.LATENCY.PROCESS_CONFIRMATIONS` = `request.poll` (same string as `EXECUTE_POLL`), and unused.
- **Layering** — `core/` imports NestJS throughout; couldn't find the `dependency-cruiser` guardrail that PR #181's changelog claims it added in `main` — worth checking whether that S0 landed.
