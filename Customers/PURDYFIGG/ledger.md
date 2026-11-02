---
tags: [customer, ledger]
title: PURDYFIGG — customer ledger
---
# PURDYFIGG — customer ledger

Agent-facing. Newest first. Incidents, config decisions, and the reasoning
behind them. Not a diary, not a support log — what a future agent needs before
touching this customer's config again.

## 2026-09-24 — FUSE-1238: redriven orders' confirmations black-holed; 118 routing docs repaired

118 PURDYFIGG routing docs (Firestore fuse-wms-routing) carried source "snap-adapter" from the 2026-09-21 redrive batch, so their confirmations matched no delivery subscription. 4 despatches were stuck on the SNAP outbound queue. The fix was deployed and all docs repaired on 2026-09-24 at about 10:43Z. Shopify confirmations then flowed: 137 processed and 138 SNAP clear-downs over the following hour. At 11:20Z Shopify rejected 3 fulfilments with 'Invalid fulfillment order line item quantity requested' (fulfilment orders 14468702994812, 14468753097084, 14468619436412). That error class predates the fix: 17 times between 17 and 23 Sep.

PR: gfs-bifrost/snap-adapter#253

## 2026-09-01 — Retrieval-window/tag-lag stranding at go-live

Go-live day incident: Skio subscription orders (and some Online Store orders) stuck paid+tagged+unfulfilled
but never reaching SNAP. Root cause: the bulk tick's 90-minute created_at window equalled P&F's own
~90-minute tag-release delay, leaving near-zero overlap. Not a Shopify channel/publication filter issue
(verified no such filter exists in the connector).

Fix: temporary 8h sweep recovered 1,035 stranded orders, then standing window set to 3h (10,800,000ms).
A ~65-minute gap existed between the temporary revert to 90min and the 3h decision landing (19:50-20:55
BST) — mostly covered by the 3h resweep reaching back to 17:55 BST, but not with certainty for orders
created before that point. See known-context.md for the full timeline and residual-risk detail.

2h post-fix monitor (21:20-23:21 BST): stable. +121 orders, zero failures. Confirmations quiet
22:00-23:21 — verified against SNAP's OBQ 3x, genuinely empty (warehouse lull, not a stall).

Compounding fact from Harry: Skio's subscription-order creation is a once-daily batch, not continuous
— narrows the exposure window for this race considerably. This was that one daily shot; caught in time.
