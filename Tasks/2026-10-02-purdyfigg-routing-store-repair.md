---
tags: [adhoc-task]
date: 2026-10-02
tldr: "PURDYFIGG 'Line item has no fulfillment ID' loop: wrote collector fulfillment ids into the routing store for 23 shipments (pilot, then 22); all 23 confirmed in Shopify and cleared from SNAP's queue within one cycle. 6 rows still owed to support"
session_id: 6cd66a26-c1fd-44fb-928d-fd9154c75173
status: open
---
# Repair PURDYFIGG's looping Shopify confirmations

## Outcome
- **Repaired:** 23 Case A shipments, all from the 09-30 bulk-drop cohort that predates snap-adapter#275. Each Firestore `routing-metadata` doc got `lines[SOLineId].extensions.shopify.fulfillmentId`, using ids from the collector matched by SKU. PURD5AC786581D9 has a duplicate SKU, so it was mapped by hand.
- **Results:**
  - The pilot, PURD89A4D902A78, cleared at 12:50Z.
  - The other 22 were written at 12:51Z and confirmed between 12:54 and 13:02Z: 22/22 `Confirmation dispatched successfully`, 22/22 queue rows processed.
- **Owed to support:**
  - PURD91B0BF21CC3 / 14424845353340 is a short despatch: is partial fulfilment OK? It's still looping.
  - 5 Case C rows are stuck silently: PURDC5EB6A337E2, PURD8041A2FE1DE, PURDD85217B3733, PURD61FDB229170, PURD50AF816638C. For each, confirm the order is fulfilled, then markProcessed.
- The prior record, [[2026-10-01-purdyfigg-shopify-confirmation-backfill]], is closed into this one.
