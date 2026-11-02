---
tags: [explain]
date: 2026-10-12
thesis: "SAIRA dispatch confirmations fail because the warehouse ships a free extra item that Shopify never saw. shopify-connector rejects the whole fulfilment over that line. It already skips kit components and could skip these too."
confidence: moderate
---
# SAIRA dispatches fail in Shopify because the warehouse adds a line Shopify has never seen

```orient-bluf
{ "v": 1, "bluf": "SAIRA dispatch confirmations fail because the warehouse ships a free extra item that Shopify never saw. shopify-connector rejects the whole fulfilment over that line. It already skips kit components and could skip these too.", "confidence": "moderate", "action": "Decide whether shopify-connector skips lines with no Shopify ID, then retry the 9 SAIRA orders from replay." }
```

## Situation
- **CONFIRMED** The weekend review of the Poller Clear-Down D1 soak found the failures. Harry Humby's #bifrost-general thread counted 1,455 "Line item has no fulfillment ID" errors for SAIRA over 9 shipments. PURDYFIGG had 3,407 over 110. [1] [2]
- **CONFIRMED** Seven SAIRA orders failed from 2026-10-05 to 2026-10-09. Three retried every ~12 minutes, about 460 times each, until cleared by hand on 2026-10-09. [3]
- **CONFIRMED** SAIRA joined clear-after-publish (D1) at 2026-10-09 12:41Z. The poller now clears a confirmation's SNAP queue row once it publishes it. [1]
- **CONFIRMED** Two more orders failed at 2026-10-09 15:38Z (`14510735327607`, `14507353145719`). Replay holds one record for each, with no loop. [4]
- **CONFIRMED** Over the weekend 57 SAIRA goods-out confirmations published and cleared. The two orders above are the only failures. [5]

## Assessment
- **CONFIRMED** Every fulfilment line needs the Shopify line ID of the order line it fulfils. The 10-09 `repair-shopify-confirmation` pass confirmed this for the 7 earlier orders. [3]
- **CONFIRMED** Each failing shipment carries one price-0 extra item that SNAP holds and Shopify never had. Full checks of three orders found MC1 on two and HFO10 on one. Fuse has no Shopify ID for it. [3]
- **UNKNOWN** Whether the 2 newest orders carry the same extra item. They fail with the same error, but nobody checked their lines.
- **CONFIRMED** `getLineItemsFromMappings` throws on the first line without an ID. That aborts the fulfilment for every line, including those Shopify knows. [6]
- **CONFIRMED** The same function already drops `CanonicalLineRole.KIT_COMPONENT` lines and logs `KitComponentsExcluded`. The warehouse's free extras are the same class of line but carry no tag, so they reach the throw. [6]
- **CONFIRMED** The counts differ because of D1. Before D1, a failed confirmation stayed on the SNAP queue and was re-announced every ~10 minutes. PURDYFIGG, not on D1, keeps climbing. [1] [5]
- **ASSESSED** Under D1 replay records a failure once, so the confirmation now exists only in replay and will not return on its own. This follows from the clear-after-publish design.

```orient-flow
{
  "v": 1,
  "title": "Per-line handling in shopify-connector",
  "nodes": [
    { "id": "l", "label": "Each despatched line", "kind": "step" },
    { "id": "k", "label": "Kit component?", "kind": "step", "ev": [6] },
    { "id": "x", "label": "Skipped and logged", "kind": "step" },
    { "id": "r", "label": "Has Shopify line ID?", "kind": "step", "ev": [6] },
    { "id": "f", "label": "Added to fulfilment", "kind": "step" },
    { "id": "t", "label": "Throw: no fulfillment ID", "kind": "step", "tone": "alert", "ev": [6] },
    { "id": "w", "label": "Whole confirmation fails", "sub": "order stays unfulfilled", "kind": "step", "tone": "alert" }
  ],
  "edges": [
    { "from": "l", "to": "k" },
    { "from": "k", "to": "x", "label": "yes" },
    { "from": "k", "to": "r", "label": "no" },
    { "from": "r", "to": "f", "label": "yes" },
    { "from": "r", "to": "t", "label": "no" },
    { "from": "t", "to": "w" }
  ]
}
```

## Open items
- **ASSESSED** Proposed, not decided: skip lines with no Shopify ID and log them, as kit components are. The safer version skips only lines whose SKU is absent from the Shopify order. It keeps failing loudly when the SKU is present but its ID is missing, the FUSE-1118 data-bug case. [7]
- **UNKNOWN** Whether `resolveLineItemFulfillmentOrders` returns SKUs or only IDs. The safer version needs SKUs.
- **UNKNOWN** Whether a goods-out replay retry goes back through shopify-connector. Confirm this before retrying the 9 orders.

| Item | Owner | By |
|---|---|---|
| Decide the skip rule in shopify-connector | unassigned | undecided |
| Retry the 9 SAIRA orders from replay after the fix ships | unassigned | after fix |
| Send the less-technical cause comms (drafted, held) | Harry | after decision |

## Evidence
```orient-evidence
{
  "v": 1,
  "items": [
    { "id": 1, "kind": "doc", "ref": "Soaks/poller-clear-down-d1", "note": "D1 soak; Poller Clear-Down Migration State" },
    { "id": 2, "kind": "doc", "ref": "#bifrost-general thread, Harry Humby, 2026-10-12", "note": "SAIRA 1,455 over 9 shipments; PURDYFIGG 3,407 over 110" },
    { "id": 3, "kind": "doc", "ref": "Monitors/2026-10-09-shopify-confirmation-delivery-failing-saira" },
    { "id": 4, "kind": "doc", "ref": "Monitors/2026-10-09-shopify-confirmation-delivery-failing-saira-refire", "note": "replay prod, SAIRA, search fulfillment: 1,455 total, latest 2026-10-09T15:38:10Z" },
    { "id": 5, "kind": "log", "ref": "Datadog 2026-10-09 13:09Z to 2026-10-12: SAIRA fuse.confirmation.published 406 = snap.outbound.cleared 57 + clear_skipped{reason:stock_adjustment} 349; clear_failed 0" },
    { "id": 6, "kind": "code", "ref": "apps/shopify-connector/src/core/confirmations/sales-order-confirmation.handler.ts@6680461:L404-439", "note": "origin/main at time of writing" },
    { "id": 7, "kind": "ticket", "ref": "FUSE-1118", "note": "Backlog; a line's Shopify reference is never saved at order creation" }
  ]
}
```
