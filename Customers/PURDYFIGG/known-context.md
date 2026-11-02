---
tags: [customer, PURDYFIGG]
verified: '2026-09-02'
title: Purdy & Figg — known context
---

# Purdy & Figg — known context

Exempt from staleness anchoring (no git to diff against) — trust the dates on each entry, and
re-verify the `## Captured Config` block via `customer-sync` rather than assuming it still holds.

## Incident: retrieval-window / tag-release race at go-live (2026-09-01)

**Symptom**: James Godsell reported a batch of Skio subscription orders — paid, tagged
`ILG_RELEASED`, unfulfilled — visibly sitting in Shopify but never reaching SNAP. First read was
a suspected Shopify sales-channel filter (Skio vs Online Store). That was a red herring: the
Shopify connector has **no channel/publication filter anywhere in its codebase** — verified by
grep. Two Online Store orders in James's own screenshot were stuck identically.

**Real root cause**: the bulk tick's `retrievalConditions.salesOrder` hard-ANDs `created_at >=
now - interval` with `financial_status:paid`, `fulfillment_status:unfulfilled`, and
`tag:ILG_RELEASED`. At go-live the interval was **90 minutes (5,400,000ms)** — and P&F's own
process releases (tags) an order roughly **90 minutes after creation**. Tag-lag and window length
being equal meant near-zero real overlap: an order became eligible at almost the exact instant it
aged out of the window. Confirmed directly from Shopify's own `currentBulkOperation` responses —
every tick from ~11:46 BST returned `objectCount:"0", url:null` for over 7 hours straight.

**Compounding factor (Harry, 2026-09-02)**: Skio's subscription-order creation is a **once-daily
batch run**, not a continuous drip. This is a scheduling fact worth remembering — the exposure
window for this specific race isn't "any time," it's narrow and roughly predictable (shortly after
that daily run), and this go-live incident *was* that one daily shot. We happened to catch and fix
it before the next day's run would have repeated it. If this recurs, check the timing against
Skio's daily run first before re-deriving root cause from scratch.

**Fix sequence** (all times BST, 2026-09-01):
1. ~19:33 — temporarily widened the interval to 8h to sweep the backlog.
2. ~19:45 — swept: dedupe held count 482 → 1,517 sales orders in one bulk op.
3. ~19:50 — reverted to 90 min per explicit instruction ("watch 20 min, revert in any case").
4. **19:50–20:55 — a ~65-minute gap where the 90-minute window was back in effect** (12
   consecutive `objectCount:0` ticks, confirmed from raw logs). Same failure mode as the original
   incident, just much shorter.
5. ~20:55 — standing window set to **3 hours (10,800,000ms)**, which reaches back to 17:55 BST —
   retroactively re-sweeping anything created after that point which had become eligible during
   the gap (that tick jumped to `objectCount:10421`).

**Residual risk from the gap**: an order created *before* ~17:55 BST that (a) wasn't yet tag-eligible
by the 19:45 BST 8h sweep, and (b) became eligible specifically during the 19:50–20:55 gap, would
have fallen outside the 3h window's reach once it activated — structurally the same silent-drop,
just needing an unusually long tag delay to land in that exact slot. Not ruled out; a silently
dropped order leaves no trace by design. Cheap check if ever needed: ask ILG whether anything
created ~17:00–17:55 BST on 2026-09-01 is still stuck.

**2-hour post-fix monitor (21:20–23:21 BST)**: stable throughout. +121 orders processed cleanly,
zero bulk-tick or SNAP-create failures, no new failure-inbox entries. Confirmations went quiet
~22:00–23:21 (verified 3× directly against SNAP's outbound queue — genuinely empty, not a stuck
backlog; just a warehouse dispatch lull).

**Platform gap surfaced, not yet fixed**: a `COMPLETED` bulk op with `objectCount:"0"` emits
**no warning and no metric** (`core/bulk/tick/bulk-ingest-tick.ts` only warns on
FAILED/CANCELED/EXPIRED). This is why the original stranding ran 7+ hours before anyone noticed —
worth a ticket. See [[reference_shopify_retrieval_conditions_traps]] (Claude memory) for the
platform-wide version of this gotcha.

## Captured Config

_Reflects live config-service state as of the `verified` date above — re-check via
`customer-sync` before trusting if this looks old._

| Field | Value |
| --- | --- |
| `retrievalConditions.salesOrder[created_at]` | `>= now - 10,800,000ms` (3h) |
| `retrievalConditions.salesOrder[financial_status]` | `== paid` |
| `retrievalConditions.salesOrder[fulfillment_status]` | `== unfulfilled` |
| `retrievalConditions.salesOrder[tag]` | `== ILG_RELEASED` |
| `confirmationsEnabled` | `false` |
| `outboundTagsEnabled` | `false` |
| `stockAdjustmentsEnabled` | `false` |
| Ingest path | bulk (not metered poll) |

## Unknowns

- P&F's actual worst-case order-creation-to-tag-eligible delay hasn't been confirmed with James —
  the 3h window is a reasoned buffer over the observed ~90min-by-design delay plus Skio's upload
  lag, not a number ILG has committed to. If their delay can exceed 3h under any circumstance,
  this recurs.
- Whether `confirmationsEnabled: false` is intentional-for-now or an oversight — worth confirming
  before P&F asks why they aren't seeing dispatch confirmations back.
- Skio's exact daily run time isn't recorded — would sharpen "when is the exposure window" if
  this ever needs re-diagnosing quickly.
- **Unleashed's role isn't confirmed.** ILG's team referenced it as an upstream system for the
  subscription flow (Matt Shaw: "how long does it take for the subs to get from Unleashed into
  Shopify?"), but whether it's inventory sync, order creation, or something Skio itself calls
  is unclear. Left off [[architecture|architecture.md]]'s diagram rather than guessed — worth
  asking James/Matt directly.
