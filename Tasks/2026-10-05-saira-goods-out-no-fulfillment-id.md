---
tags: [adhoc-task]
date: 2026-10-05
tldr: "SAIRA goods-out loop ('Line item has no fulfillment ID') is not the lost-line-metadata bug: SNAP added gift lines (HFO10/NCO10) after Fuse created the orders, shopify-connector throws on any non-kit line without a Shopify id. 4 orders stuck; fix choice owed."
session_id: fb23636e-90c2-4e96-9436-ed5bfb83ed89
status: open
---
# Investigate why SAIRA goods-out confirmations fail with "Line item has no fulfillment ID"

## Outcome
4 SAIRA shipments (SAIR61D1865C26A, SAIR3B2C8C5A5FE, SAIR4A131F97936, SAIR2286ED85FF6) loop every ~6-12 min since 2026-10-05 11:24 UTC. Cause: SNAP holds 1-2 extra Level 00 zero-price lines (HFO10/NCO10, line ids SFHL...) that were never in the Shopify order Fuse collected, so no Shopify id exists; getLineItemsFromMappings (shopify-connector sales-order-confirmation.handler.ts:433) throws and the whole order fails. Not repairable by id backfill (no ids exist); the last-week line-metadata fix is working (46 of 50 recent SAIRA confirmations carry every id).
Owed: decide the fix (poller marks SNAP-only lines vs connector skips them); customers on the 4 orders have no Shopify fulfilment/tracking yet. Separate and unexplained: 290 PURDYFIGG goods-out rows "fulfillment order is CLOSED" over 10-04/10-05.
Update 13:58 BST: with Harry's go-ahead, marked the four SAIRA outbound rows processed (SIOB000895, 896, 907, 911). Queue is empty and the last retry row was 12:58:05 UTC, 23s before the clear. Support asked in #bifrost-general whether the warehouse added the HFO10/NCO10 lines and to fulfil the four by hand with the Royal Mail tracking. The four replay records are still held and will fail the same way if redriven.
