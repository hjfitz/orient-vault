---
tags: [adhoc-task]
date: 2026-10-14
tldr: "Traced Tom's GADG dev work-order API tests and sent him the causes plus a corrected sample payload on Slack"
session_id: 5435f8c8-87b7-4684-b341-95b8cfbff109
status: open
---
# Investigate Tom's work-order API testing and send an update

## Outcome
Tom's last send (eb730d33) landed in GADG dev Snap as GADGCB720D5E931, but with Site and Warehouse swapped (2SP/0006 instead of 0006/2SP) and no ShippingLane. That's the likely reason it isn't in the works-orders screen. His 7 earlier sends all got a 202 from fapi and then failed in snap-adapter. They're in replay: missing UoM, component QtyOrdered missing, Currency and DateShipment mandatory, class KIT. Every one of those comes from fapi's documented work-order example. Sent Tom the causes, a corrected payload (not sent end to end), and a warning that the deduper keys work orders on `identifiers.id` (his "AUTO" is now held).
Docs example fixed in gfs-bifrost/fapi#175 (verified end to end in dev as GADG074F3BC7C95), merged 2026-10-15 as f5881e9 and live on developers.fuse.ilg.software (portal revision 00007, run 38689730051). Harry agreed to ship master's portal, which also published the GET /stock docs (FUSE-1035, not yet QA'd; prod fapi still returns 501 there). 18 older parked portal runs were cancelled. 35964432406 is stuck (cancel 409, review 422). The fapi Confluence changelog row is still to add. Still owed: decide on the ILG-mandatory work-order badges. Optionally default component QtyOrdered and finished-good QtyRequired to 0 in snap-adapter. Fix `recordId: unknown` on work-order failures.
