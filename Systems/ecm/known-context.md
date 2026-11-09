---
tags:
- system
- ecm
verified: '2026-11-09'
title: ecm — known context
---
# ecm: known context

What the MPK research left standing on 2026-11-09: the canonical figures, Harry's decisions, and every claim still unconfirmed. Sources are the handover [[Handovers/2026-11-09-merak-replacement-pages]] [1] and the number reconciliation run that day [2]. No interview. Figures marked `(snapshot …)` age out.

## Standing decisions (Harry, 2026-11-09)
- **Merak replacing ECM and Selector is an unconfirmed hunch.** It cannot be confirmed with Jack and Stef yet. The MPK pages say "a replacement" and leave the choice to the Merak team. Keep new wording hypothetical.
- **Merak is unannounced.** Keep the content in MPK, with no Slack. Do not anchor Merak pages on the Parcel Portal or its MKP gates.
- **No further pages are wanted.** Four were proposed and stay unwritten. Any future page stays research level, comprehensive and simple.
- **No security ticket.** Harry: "not my domain". Do not draft or offer one. Class-level notes from the research agents stay in the handover record, not re-checked.
- **DHL Parcel UK hand-off (CID-317, blocked) is dropped.** Harry: "not an us issue for now". Nothing was sent and nothing is owed.
- **Lucid diagrams are linked, not embedded.** Harry draws the Confluence whiteboards by hand.
- **Verification of the five draft pages was declined.** Do not run it unless he asks.
- **Page 2 keeps its link to "Idea: Developer promise" (349110455).** That is a recommendation. The decisions on that page stay with Stef.

## Canonical figures
The window is the 15 days from 2026-10-23 00:00 to 2026-11-07 00:00 UTC, which is "15 days to the end of 6 Nov". The reconciliation chose it because it is complete days that anyone can reproduce. Every disputed figure had been true for a different window, and the metrics move by up to 1% with the hour the window ends. The hub's first figures (6.25M and 215,319) match a run that ended about 2026-11-05 20:00 UTC. Source is Datadog application metrics.

| Figure | Value |
| --- | --- |
| `raw_tracking.v1` total | about 6.29M (6,294,707) |
| Polling, Royal Mail webhook, files | about 6.01M, 218k, 62k |
| Royal Mail webhook: received, published, held for retry | about 343k, 218k, 146k |
| Evri webhook, in shadow: received, held for retry | about 563k, 59k. About 260k a week, none published |
| Unmapped codes published to BigQuery | about 11.6k, mostly Interlink (4,651), DPD (3,124) and UPS (2,412) |
| Customer webhooks sent | about 406k, which is 6.5% of events |
| New shipments (new IDs) | about 675k |
| Nine mocked carriers | about 587k events, 9.3% |
| Evri, DHL Parcel UK, DPD Local, DPD | about 5.59M events, 88.8% |
| Hosted Selector VMs | 278, backing 259 sites (snapshot 2026-08-06). About 1,000 sites are registered |
| Bill-on-scan contracts | 1,309 (Billing space) |

**Not re-run on this window, so the wording stands:**
- 5.44M new events and 142M carrier calls.
- The file processor's 54k, 12.4k errors and 7.0k retried.
- 24.6k Evri and 21.0k Royal Mail unmatched, and the Royal Mail 21k never matched.
- The per-carrier POD traffic figures.

About 24 calls per event still holds: 142M over 6.01M is 23.6.

## Unconfirmed
Each item has a source that says one thing and a source that says another, or no source at all.

**Figures that disagree**
- **306 against 278 VMs.** 278 is the 2026-08-06 Tech Services snapshot. About 306 is in the 4 Nov Deep Dives artifact. 306 less the 79 stopped VMs is 227, which matches neither. Needs `compute.instances.list` on `gfs-cloud-selector-prod-uk1`, which is denied.
- **142M carrier calls against about 114M polls.** The Polling Connectors table sums to about 114M, and the Journey page says 115M parcel polls. Nobody has reconciled them. They may be different measures.
- **DPD Europe proxy: dormant, or live.** Logs show 21 failures in 15 days. The proxy's own metric shows about 710 requests (about 330 a week) with 5% errors. Whether they are real labels is not confirmed. Logs older than 15 days are gone.
- **Royal Mail "about a third never matches".** The metrics give 21k of 343k unmatched and 146k held for retry. The claim is not reconciled with them.

**Claims with no evidence yet**
- **Which parcel callers ask for on the v2 POD route.** The service does not pick the delivered parcel for DPD Local. Who does is open.
- **The live billing timetable.** Each customer has its own schedule. Which run program is live, and whether split runs are on, is open.
- **Whether the `shipment-identity-service` repo matches the deployed service.** Only a legacy copy was read.
- **The "12 mocked carriers" row on How Carriers Feed ECM.** Its table has 12 rows. Amazon SFP is not resolved, and Veho and Exelot sent nothing.
- **The DHL Express POD module claim.** Page 5 says the module is not loaded and does not work. The cleanup pass did not re-check it.
- **Nightline.** The Selector Interface page says Nightline. Four pages name only Nightfreight. They are two carriers, so those pages cover only one.
- **Evri "keeps held events up to 90 days".** It is a read cutoff, and the TTL indexes are not confirmed. Recommended wording: "reads them for up to 90 days". Harry has not decided.

**Answers owed by others**
- **The production Firebird triggers** on `SHIPMENTS` and `SHIP_PIECES`. One read-only query by a DBA settles it.
- **Which carriers `patina-service-2` writes back,** and which carriers hold the 1,309 bill-on-scan contracts. The list is ADO variable group `gfs-patina-service.prod` (Library id 141), which the ADO MCP cannot read.
- **Who runs `CHECK_SHIP_STATUS`,** and which host runs the Scan Injector. Datadog shows `MEDC-APP-01-P`. SRE-126 confirmed `MEDC-APP-12-P`.
- **What the deployed mark-as-delivered code writes.** The default of 1003 is read from code, and legacy UPS loss reporting reads 1003 as lost. Nobody owns the write-back.
- **Whether DataBridge writes Slipway's masked billing export into Firebird in production.**
- **Evri code-mapping coverage before the CID-315 cutover.**
- **Whether any n8n workflow calls a carrier API.**
- **Live GCP state:** cross-project grants, the warehouse subscription and `tracking-dump@`.
- **Whether Client4's SOAP upload carries a file or shipment records.**

## Owed
- Harry deletes three Confluence pages by hand: Carrier Services (353468499), Day End and Billing Handoff (353566845) and a scratch draft (355565572).
- Harry's feedback on the five draft pages. Apply it to the live page first, then the vault copy.
- The `orient-writers` skills `plainly` and `c4-diagrams` are uncommitted.
- Retest the Lucid macro on Confluence once the admin installs the app.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "doc", "ref": "Handovers/2026-11-09-merak-replacement-pages.md" },
  { "id": 2, "kind": "doc", "ref": "Session scratchpad numbers-canonical.md, 2026-11-09 (Datadog metrics via execute_code; not in the vault)" }
] }
```
