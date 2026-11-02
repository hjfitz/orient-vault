---
tags: [support-triage]
date: 2026-09-21
business_id: BYOMA
customer: "Byoma"
connector: sftp
reporter: "James Godsell"
channel: bifrost-general
thread_url: "https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1789999974819089"
opened_at: "2026-09-21T14:12:54Z"
resolved_at: "2026-09-21T14:24:49Z"
minutes_spent: 12
outcome: config-issue
session_id: 1cf35a9e-e41e-4456-9905-3e341fc2cfc5
status: open
---
# Byoma "transfers" (Goods In) failing in Snap with "Invalid Consignment" / "Invalid Receipt"

## Reported
James Godsell reported Byoma's goods-in ingest failing for "transfers" (TRF-prefixed purchase orders) in prod for 25 days, with Snap returning a 400 on create: `XDoc - Invalid Consignment on line SEK9LXVPVF; ReceiptId - Invalid Receipt on line SEK9LXWLB5`. He said the payload looked fine and asked us to investigate. Harry's first-glance reply floated a field-length/generated-key hypothesis.

## Root cause
Not a code defect. BYOMA's `purchase_order` connector mapping (config-service, friendlyName "Goods In") carries a header default `identifiers.consignmentId → "AUTO"`. `snap-adapter`'s `PurchaseOrderService` maps this straight through to Snap's `ConsignmentId` field with no special-casing (pure canonical→Snap passthrough, by design). Snap doesn't recognise the literal string `"AUTO"` as a real consignment value on this creation path (that convention only applies to Snap-minted ids on a different flow), so it rejects the whole receipt — the "Invalid Consignment" error on the header segment cascades into "Invalid Receipt" on the same write (segmented-write partial-failure behaviour, consistent with snap-adapter's documented Snap-API gotchas).

Verified directly against replay-service failure `ca52b2c5-5835-44da-94a4-b5017b3007af` (record TRF04291, correlationId `5f85da7c-1edb-4d76-a483-c6ce959165bb`) — the stored canonical record carries `identifiers.consignmentId: "AUTO"` — and against config-service's live `purchase_order` mapping for BYOMA's connector, which shows the exact `"AUTO"` default. `identifiers.consignmentId` is optional on `CanonicalPurchaseOrder`, so nothing downstream requires it.

All ~15 queue entries with this exact reason (TRF04206 through TRF04291, oldest 25d) are affected; BYOMA appears to only send transfer-type purchase orders, so this has been failing every one of them since the mapping was set up.

## Fix / Resolution
Not yet applied — this is James's/ILG's own config to own (he configures BYOMA's connector mappings directly, same as the 2026-08-05 outbound-use-cases fix). Replied in-thread via Bifrost Support Bot with the exact fix: drop the `identifiers.consignmentId → "AUTO"` header default from BYOMA's `purchase_order` mapping (leave everything else as-is). Offered to replay the ~15 stuck transfers via replay-service once he's made the change. Deliberately did not touch prod config ourselves — Harry's call.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1789999974819089
- Reply: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1790000689069769
