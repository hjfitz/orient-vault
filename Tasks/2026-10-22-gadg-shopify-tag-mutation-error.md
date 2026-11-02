---
tags: [adhoc-task]
date: 2026-10-22
tldr: "GADG tag errors and doubled stock were config: two connectors on one store with overlapping conditions and both flags on. Fix shipped in shopify-connector#349 makes Shopify's userErrors visible. Owed: tell Alex to fix the AlexP-Temp-Shopify connector."
session_id: 583835f3-1784-4578-afaf-b26ec1991695
status: open
---
# Follow up GADG Shopify tag write rejections

## Outcome
The code fix shipped (gfs-bifrost/shopify-connector#349, prod on `4103025d`). Everything else is config. GADG has `ILG Test Store` and `AlexP-Temp-Shopify` on the same store (`quickstart-501d0f59`) with identical retrieval conditions and both `outboundTagsEnabled` and `stockAdjustmentsEnabled` on. The results:
- every order is ingested twice and both copies are re-sent to Snap each poll;
- tags are written twice, so one write gets `Order tags is invalid`;
- every stock adjustment is applied twice (e.g. TTRS +3 became +6).

One store with several connectors is handled entirely by config:
- give the connectors retrieval conditions that don't overlap (as ESCENTRIC/ESCENTRICPL do with a UK/EU tag);
- turn on tags, stock adjustments and stock sync on one connector per store;
- confirmations are already routed per connector.

No prod store is shared.

Owed:
- Tell Alex to deactivate `AlexP-Temp-Shopify`, or give it conditions that don't overlap and turn its flags off. Its mapping also sets owner `ACADEMIC`, which is why its copies fail in Snap and the orders get ILG_ERRORED.
- Tell Alex the quickstart store's stock has been double-adjusted since 2026-10-20, so it no longer matches Snap.
- Optional: a fuse-ui warning when a second connector targets a store that's already in use.
