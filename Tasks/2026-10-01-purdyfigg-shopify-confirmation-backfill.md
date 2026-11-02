---
tags: [adhoc-task]
date: 2026-10-01
tldr: "PURDYFIGG Shopify confirmations looping 'Line item has no fulfillment ID': backfilled SHL attachments for 13 orders (pilot then 12), all confirmed and cleared; 2 other batches + root cause still open"
session_id: 0c3952e2-0c45-4eb7-bb5d-181d471265e1
status: done
---
# Fix failing PURDYFIGG Shopify confirmations

## Outcome
13 orders (14 SHL rows, BF-prefixed LineIds, ids from collector) backfilled in SNAP prod; all 13 confirmed in Shopify and their outbound-queue records cleared on the next poll. Second burst in two days (30 Sep was the first), so the cause is still live: shipments land in SNAP without attachments (3 of 13 had collector status failed).
Owed: order 14424845353340 / PURD91B0BF21CC3 (short despatch, support decision), order 14476640387452 / PURD61FDB229170 (soft-ack loop, confirm fulfilled then markProcessed), new order 14503238697340 / PURDFAF7C22BC46 failing the same way, ~23 other unclassified queue records, and the root cause in snap-adapter.
2026-10-02: the owed items moved to [[2026-10-02-purdyfigg-routing-store-repair]]. PURDFAF7C22BC46 and the ~23 unclassified rows were repaired via the routing store. snap-adapter#275 fixed the root cause. PURD91B0BF21CC3 and PURD61FDB229170 are still owed there.
