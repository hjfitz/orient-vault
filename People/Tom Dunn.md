---
tags: [person]
role: Migration Analyst
org: ILG (ilguk.com)
relationship: internal-partner
reports_to: "[[Lee Simmons]]"
team: Migration
title: Tom Dunn
---
# Tom Dunn
> ILG senior tester; my main contact on SNAP/WMS behaviour + NMFC mapping.

## Coordinates
- Slack: <@U0ALBJ70GDB>
- Email: thomasdunn@ilguk.com

## Open loops
**I owe**
- [ ] Reply to his "Works Orders SFTP QA Issues" email (to you and [[Matt Shaw]], 14:51 UTC on 9 Nov, unread): work-order confirmations lack line-level production and expiry dates, and FGR line numbers map to a backend value where he wants the `identifiers.solineId` equivalent. [FUSE-1329](https://globalfreight.atlassian.net/browse/FUSE-1329) (Ready for QA) may cover the first gap and [FUSE-866](https://globalfreight.atlassian.net/browse/FUSE-866) is the same thread — [email](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAHc35JoAAA%3D&exvsurl=1&viewmodel=ReadMessageItem)
- [x] Reply to his 5 Nov DM: Indu wants to go live next week or the week after pending testing, a channel is being set up, and he is picking up from [[Lee Simmons]]; his "Morning bud" of 6 Nov is also unanswered — replied on Indu on 9 Nov, with no objection to a Monday or Tuesday go-live if testing signs off by Wednesday — [DM](https://gfsdeliver-eng.slack.com/archives/D0AM9957WTS/p1793896444420819)
- [ ] Review his works-order test (he asks for 2 minutes): his POST to the dev Works Order Ingest API returns 204 and shows in the SNAP host interface but not the Works Orders GUI. He also asks what CT's behaviour has to do with Fuse's API (DM `D0AM9957WTS`) — [Tom's email](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAFcAAABLsgQpFdPTayXOZTVrraLAAHMCW1PAAA%3D&exvsurl=1&viewmodel=ReadMessageItem)
- [x] Be free this morning to talk through the work-order testing with him — [Slack DM](https://gfsdeliver-eng.slack.com/archives/D0AM9957WTS/p1791999406308939)
- [x] Reply on works-order SFTP testing: the header-level default is `identifiers.carrierId`, which shipped in [FUSE-1238](https://globalfreight.atlassian.net/browse/FUSE-1238). Still open: the confirmation line number and FGR `WorksOrderRef` from his DM. Slack shows my reply last, and his Goods-in email thread is unread — [Tom's email](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAHLFMPeAAA%3D&exvsurl=1&viewmodel=ReadMessageItem)
- [x] Decide who owns customer outreach on the goods-in confirmations change: he and [[Lee Simmons]] do not know who holds recent comms with two of the listed customers, and ILG must flag concerns by Thu 15 Oct or it ships Mon 19 Oct — [Tom's email](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAHLFMPeAAA%3D&exvsurl=1&viewmodel=ReadMessageItem) — resolved 10-16: [[Darren Cobby]] is sending the customer messages and the aim moved to Thu 22 Oct
- [ ] Hold the 30 minutes with him on Wed 14 Oct after fuse/bifrost, which we both agreed — [digest](../Digests/2026-10/2026-10-13.md)
- [ ] Answer his Escentric Molecules DM: can one Shopify store serve UK and PL Fuse customers, routed by country? [[James Godsell]]'s "worth testing it" likely covers it — [DM](https://gfsdeliver-eng.slack.com/archives/D0AM9957WTS/p1791456498692529)
- [ ] Read his 10-07 17:33 DM on works-order CSV test feedback — [DM](https://gfsdeliver-eng.slack.com/archives/D0AM9957WTS/p1791390803079849)
- [ ] Reply to his 10-05 13:08 follow-up on Engraving: he wants line-level properties configured against Gadgets (the Shopify dev store) even if that is not the client's mechanism; James Godsell has only mapped such fields, never set them up in Shopify. Then tell [[Darren Cobby]] the outcome — [thread](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAHExRLsAAA%3D&exvsurl=1&viewmodel=ReadMessageItem)
- [x] Take the 10:30 call with him on the Escentric engraving / "VAS via Shopify, line level" idea, then tell [[Darren Cobby]] the outcome — [engraving thread](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAHEQeBuAAA%3D&exvsurl=1&viewmodel=ReadMessageItem)
- [ ] Order FUSE-1273, FUSE-1274 and FUSE-1276 (his QA defects) with [[Matt Shaw]] at the 10:00 standup — [group DM](https://gfsdeliver-eng.slack.com/archives/C0BC33H8QMT/p1790783612714759)
- [ ] Answer his unanswered Fulfil SO-response-code question for the Dock & Bay escalation (carried ×9 on my todo)
- [x] Catch up on the Platform Testing defects thread now I'm back (he @-mentioned me). QA is re-testing Pick/Pack this week and starting Work Orders — [email](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAHBMDI9AAA%3D&exvsurl=1&viewmodel=ReadMessageItem)
- [ ] Follow up on his SSL/500 errors report across SNAP instances (DM, 2026-09-16 19:21) — asked whether scheduled reporting should pause; got a "Tomorrow problem" deferral from me last night, now due
- [ ] Confirm/decline his call ask (DM 2026-08-19 15:56) to use Datadog to validate deprecated `GOODS_IN_CONFIRMATION` field payloads — asked for "tomorrow" (today, 2026-08-20); conversation drifted into filing FUSE-1120 instead but the call itself was never confirmed or declined
- [ ] Raise the **dedupe bulk-release cap** ticket — his DM: the summary UI only bulk-releases 100 records, can it do more? I said I'd raise something (07-29) — [DM](https://gfsdeliver-eng.slack.com/archives/D0AM9957WTS/p1785337625749129)
- [x] Counter/decide on his "Gisou Split Middleware - Returns RGA Only" pushback — replied; his 07-24 email thanks me for the input and agrees tandem JBMQ/ILG SFTP isn't viable
- [ ] Reply on his prod **JBMQ P1** heads-up (Slack, 07-22 21:12) — he'll be on it 9am, no reply yet
- [ ] Give cross-middleware solutioning input on Escentric Molecules JBMQ "Engraving CR VAS" line-level flow (email 07-24, + [[Matt Shaw]]) — chased again 2026-08-03, now asking directly whether it's "more of a Jack question" (Jack OOO 3–10 Aug, cc'd to Harry/[[Matt Shaw]]/Darren C)
- [ ] Review his weekend FUSE Testing pass/fail summary — sent To me alone, "As per Slack for your review please" — [email](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAGbYfi8AAA%3D&exvsurl=1&viewmodel=ReadMessageItem)
- [ ] Give him a yes/no on whether "Stock Updates via JSONL missing movement ref + attribute/StU data" becomes a properly raised ask rather than a nice-to-have
- [ ] Answer what record type the ~16 hanging Purdy & Figg dev confirmations are — he guessed stock adjustment — [Slack](https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1785771891175859?thread_ts=1785768353.172359&cid=C098LD5PS95)
- [ ] Act on his CSV/JSON ingest test files for Alex (attached to email, 07-22; a follow-up 07-24 email says "as per Slack" — check what was actually agreed)
- [x] Close out his JSON-over-SFTP test-file question ("is that what we're expecting?") — resolved: [[Harry Humby]] shipped [sftp-connector#232](https://github.com/gfs-bifrost/sftp-connector/pull/232) for it
- [ ] Stand up the agreed **10k sales-order CSV ingest load test** in dev (proposed 07-27 14:57) — I offered dev, he's prepping the file; no further movement since my acknowledgement, and the "not against GADG" caveat doesn't appear explicitly in the DM itself (may have been said elsewhere) — confirm before running
- [ ] Reply on the Custom Outbound Mapping / Scribe UAT thread — [[James Godsell]] can't save the GADG/Zedonk goods-out CSV mapping config in Scribe ("missing required fields": client reference, ship date, tracking number); Tom @'d me directly, [[Jack Bailey]] cc'd (07-17)
- [ ] Diagnose + reply to Nuzest SFTP SO test — all sales orders landing in SNAP as "TBC" across every configured ship method despite clean-looking files (attachments supplied, 07-13)
- [ ] His consolidated RGA Ingress/Egress Issue List (07-14) supersedes the individual RGA threads below — Matt Shaw confirmed working it, but Tom's direct 07-15 07:57 ask names both of us for support
- [x] Reply to his Purdy SKU Similarities question — closed 07-16/17: decision = `PAF-` prefix (SNAP 30-char limit fine); thread ended with thanks
- [ ] Configure the `PAF-` SKU prefix add/strip for Purdy & Figg (LISAUK) in the integration — Fuse-side follow-on from the closed SKU thread (Danny attached the SNAP schema)
- [ ] Answer the SNAP-doesn't-like-postman-calls issue (DM 07-14 16:00) — only reacted 🤔, never actually answered
- [ ] Send the promised follow-up info on the CSV→JSONL API-conversion question (DM 07-15, said "I'll drop some info in a follow-up")
- [ ] Diagnose + reply to the RGA ingest failure cluster: JSON SFTP RGA "Invalid JSON Lines input" (correlationId supplied), CSV RGA Zod errors (Gadgets), RGA confirmation CSV 2SPR000134 missing data, + API feedback ("two items need engineering")
- [x] Grant new ILG L1 starter Steve Thompson Fuse UI + Datadog access — access granted, confirmed closed (Steve T email 07-08) — [email](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAGJd643AAA%3D&exvsurl=1&viewmodel=ReadMessageItem) (asked 04/07, flagged for Mon AM)
- [ ] Prep + land a file with the Stubble & Co / Charlotte Tilbury duplicate SOs removed — [email](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAGG9cXMAAA%3D&exvsurl=1&viewmodel=ReadMessageItem) (asked 02/07)
- [ ] Respond on the FUSE UI ingest rule creating an extra attachment for the header PRODDETAIL CSV — [email](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAGG9cXCAAA%3D&exvsurl=1&viewmodel=ReadMessageItem) (reported 02/07, shared a SNAP trend query)
- [ ] Walk him through composing a Confluence doc from a template + body of text with AI (promised "Monday" 29/06) — [DM](https://gfsdeliver-eng.slack.com/archives/C0ANTUQM1H8/p1782566674749179)
- [ ] Reply on the SNAP 500s DM — ICONIC is the known SKU-query 500; the new ones since 15:45 (29/06) need a status answer — [DM](https://gfsdeliver-eng.slack.com/archives/D0AM9957WTS/p1782750172989939)

**Owed to me**
- [ ] Confirm the Fulfil webhook secret for Dock and Bay (dev). Fulfil rejects the webhook with 401 "Invalid x-webhook-secret-key"; waiting on him or Dock and Bay, then I update the Fulfil.io Testing connector

## Standing context
- Off 07–14 Sep 2026
- Handed the FUSE Migration testing SharePoint and his open project items to the group for that week
- SNAP / WMS behaviour + NMFC code mapping; coordinates BM2 deployments
- Load/volume tests must avoid **GADG** — it's the shared test business and he doesn't want it polluted
- Raised [FUSE-1086](https://globalfreight.atlassian.net/browse/FUSE-1086) at [[Matt Shaw]]'s direction for the custom-egress column-ordering gap that failed QA
- [FUSE-1077](https://globalfreight.atlassian.net/browse/FUSE-1077) (one SKU split across two batches under one Snap ConsignmentId) is parked pending a product decision, routed to [[Lee Simmons]] to raise with [[Jack Bailey]]
- That FUSE-1077 decision is blocked until [[Jack Bailey]] is back on 10 Aug
- ✍️ 

## Together (newest first)
- 2026-11-10 — new "Works Orders SFTP QA Issues" email to you and [[Matt Shaw]] with CSVs attached → [[Meetings/1-1 Matt Shaw]]
- 2026-11-06 — heads-up that Indu wants to go live next week or the week after → [[Digests/2026-11/2026-11-06]]
- 2026-11-02 — Forwarded Darren Cobby's Q1 Fuse migration timeline to you alone at 09:17 ("FYI mate"); he and Jack are asked to write up the customer-facing technical changes
- 2026-10-23 — Escentric UK and PL go-live set for Tue 27 at about 09:30, the same slot as the Poland Snap upgrade; Phlur smoke orders shipped on 23 Oct and he added you and Matt to the thread for visibility
- 2026-10-19 — replied "please proceed" on the Fuse\Snap call thread, clearing the Purdy & Figg load test on ILGSTG
- 2026-10-16 — his 10-15 14:14 DM says the work order tested via API is "mostly working", asks for a 2-minute review, then asks what CT's behaviour has to do with Fuse's API, and no reply has gone back
- 2026-10-15 — works-order API testing: his POST to the dev Works Order Ingest API returned 204 but is not visible in the Works Orders GUI; he asked to borrow you this morning, you said yes
- 2026-10-13 — Goods-in Confirmations email thread (09:09, unread): nobody knows who holds comms with two of the listed customers, so outreach ownership is open ahead of the Thu 15 Oct flag deadline
- 2026-10-09 — works-order SFTP testing: the "Works Orders via SFTP - Gadgets Testing" email thread was resolved by [[Matt Shaw]] and [[Lee Simmons]] (CT works orders carry no carrier or ship method), but his DM on carrier default "OWN", WOC line number and FGR `WorksOrderRef` is still unanswered. He also asked about one Shopify store for UK and PL customers (Escentric Molecules) and sent WO API schema / Bruno unit-of-measure errors, which I answered ("poke matt on this one"). Fulfil sent another transfer order on ticket 87630 for his new test order request (I am cc'd)
- 2026-10-05 — the 10:30 Engraving call happened; he followed up by email at 13:08 and it is unanswered
- 2026-10-05 — back from leave; 10:30 1:1 booked from my bookings page ("VAS via Shopify, line level") → [[Meetings/Escentric Engraving - Solution Design]]
- 2026-09-30 — his QA defects (FUSE-1272 to 1276) are still unassigned; his 09-28 reply says QA re-tests PICK/PACK this week and starts WO on a new thread, and that I'll catch up with him. Also in today's 13:00 Fuse/Bifrost Weekly Sync → [[Meetings/Fuse-Bifrost Weekly Sync]]
- 2026-09-29 — sent 5 dev QA defects (batch/expiry repeated per line, PO stock status, SO line number, RMA Description), now FUSE-1272 to FUSE-1276. Confirmed the Dock & Bay prod test products ingested
- 2026-09-16 — DM (19:21 BST): Inovize seeing more SSL/500 errors across SNAP instances, asked whether scheduled reporting should pause — Harry's reply deferred it to today rather than answering there and then
- 2026-09-07 — emailed "TD Handover 7th > 14th September" handing over the FUSE Migration testing SharePoint and his open project items while he is off all week 07–14 Sep, and declined today's standup
- 2026-09-04 — organising today's 08:30 [[Meetings/Escentric Engraving - Solution Design]] with Escentric + Karmoon on [INOVIZE-966](https://globalfreight.atlassian.net/browse/INOVIZE-966) Line Level Engraving; sent an FYI note ahead of it
- 2026-09-01 — on-site in Northampton for the Purdy & Figg go-live; reported WMS release running slow (BGP-related "Snap being Snap") but orders processing operationally, first shipment out (PURD018ABAA0A02)
- 2026-08-19 — DM asking for a call "tomorrow" to validate deprecated `GOODS_IN_CONFIRMATION` field payloads in Datadog; thread drifted into filing FUSE-1120 instead, call still unconfirmed
- 2026-08-12 — DM 08-11 17:32 (unreplied) about a busy day tomorrow; the kit short-ship fix (order #1273) is confirmed on dev + verified, matches [FUSE-785](https://globalfreight.atlassian.net/browse/FUSE-785) now Ready for QA — the "regroup this morning" from the huddle looks resolved by that dev-verify update rather than a separate meeting
- 2026-08-10 — DM asked to catch up today on the Kit work, embedded in a longer banter thread — the scheduling ask itself was never confirmed, conversation moved on
- 2026-08-06 — his weekend FUSE Testing summary review has shifted: the RGA gaps in it match [[FUSE-1050]] (already In QA), and [[Lee Simmons]] is picking it up with [[Jack Bailey]] on his return — likely off my plate now, worth confirming; the ~16 hanging Purdy & Figg confirmations question is still unanswered by anyone
- 2026-08-03 — forwarded a weekend FUSE Testing pass/fail summary "for your review please"; re-chased the Escentric Molecules JBMQ Engraving CR VAS ask, now openly asking whether it's a Jack question instead (Jack's OOO this week)
- 2026-07-29 — two new asks by DM: the dedupe summary UI's 100-record bulk-release cap (I'll raise a ticket), and a new Purdy Shopify order (#1086) not reaching SNAP — parked overnight for the SPORTLUX incident, he's nudging [[Matt Shaw]] on it this morning
- 2026-07-29 — no further movement on the 10k sales-order CSV load test since his 07-27 proposal and my grateful acknowledgement; separately, the dB1-4 SNAP test-env patch window he coordinated with Danny Williams resolved cleanly and I acknowledged it this morning
- 2026-07-28 — agreed a 10k sales-order CSV ingest load test: I offered dev, he's prepping the file, and he asked that it not run against GADG; his JSON-over-SFTP test-file question is now closed off the back of [[Harry Humby]] shipping [sftp-connector#232](https://github.com/gfs-bifrost/sftp-connector/pull/232)
- 2026-07-24 — new direct ask: Escentric Molecules JBMQ "Engraving CR VAS" line-level VAS flow (+ [[Matt Shaw]] for cross-middleware input); thanked me for input on Gisou RGA-only and agrees tandem isn't viable — that counter is now closed; sent CSV/JSON ingest files again "as per Slack" — check what was agreed
- 2026-07-23 — flagged (Slack, group DM w/ Jack Bailey) a prod **P1 on JBMQ** he'll be on at 9am — no reply from me yet; Gisou RGA-only counter still owed
- 2026-07-22 — Gisou RGA-only pushback received (tandem JBMQ/ILG SFTP "probably not viable"); delivered CSV/JSON ingest test files for Alex; heads-up on this morning's SNAP BM2 dB5/0010 test patch downtime; his FUSE-920 QA / SKU blacklist / JSON ingest / ticket-status DM questions all answered yesterday
- 2026-07-21 — new direct ask: "Gisou Split Middleware - Returns RGA Only" — proposes Fuse solely owning the RGA piece for Gisou
- 2026-07-20 — new direct ask (Fri email, cc [[Jack Bailey]]): Custom Outbound Mapping / Scribe UAT — GADG/Zedonk goods-out CSV config won't save in Scribe, missing-required-fields error; on today's 09:00 Bifrost Standup attendee list
- 2026-07-17 — Catch-up — RGA SFTP ingress (10:30, w/ [[Matt Shaw]] + [[Jack Bailey]]) → [[Meetings/RGA SFTP Ingress Catch-up]] — covers his consolidated RGA list + the SFTP-format "iron out" session promised for today; Purdy SKU thread closed (`PAF-` prefix decision — Fuse now owns add/strip config); his jsonl/ticket/dedupe-bypass Slack questions all answered this week
- 2026-07-16 — RGA CSV/JSON/API feedback + Purdy SKU pre-fix threads still open (direct To, ++[[Matt Shaw]]); heads-up that STUBBLE SO CSV confirmations process but client says the file never lands in SFTP ("will come your way shortly"); HEADER_POST vs HEADER_UPDATE prod-SO group DM awaiting his answer on Danny's query cadence
- 2026-07-15 — consolidated RGA Ingress/Egress Issue List thread still live (direct ask naming me + Matt Shaw); two short ad-hoc huddles yesterday (CSV/JSONL question, resolved "they're the same"); Purdy SKU pre-fix question; SNAP postman-call issue still unanswered
- 2026-07-13 — reported Nuzest SFTP SO test failure — all orders reaching SNAP as "TBC" across every ship method; [[Jack Bailey]] cc'd, attachments supplied; also on today's 09:00 Bifrost Standup attendee list
- 2026-07-10 — Tom raised RGA JSON/CSV/API ingest failures for triage: JSON SFTP RGA "Invalid JSON Lines input" (correlationId supplied), CSV RGA Zod errors (Gadgets, file attached), RGA confirmation CSV 2SPR000134 missing data, API feedback ("two items need engineering"); also flagged Nuzest SO ship-methods all reaching Snap as "TBC" (I'm letting support escalate first); [[Lee Simmons]] + [[Jack Bailey]] cc'd
- 2026-07-09 — RGA via CSV + API confirmation threads: CSV ingest validation error (Gadgets), confirmation missing-data (2SPR000134 — mappings?), and API feedback ("engineering to look at the other two"); [[Lee Simmons]] + [[Jack Bailey]] cc'd
- 2026-07-06 — emailed to grant new ILG starter Steve Thompson Fuse UI + Datadog access; plus a "Product Master Data Update" reprocess-status note (possible small reprocess for Ajay/Kavusalya)
- 2026-07-02 — reported a FUSE UI ingest rule creating an extra attachment for a header PRODDETAIL CSV (Stubble Co), with a SNAP query showing the trend
- 2026-07-02 — "Product Master Data Update" email thread (INC-30 SportLux duplicate-dispatch cleanup); ILG (Tom/Ryan) handling the data re-fresh, I'm the technical owner — track that the replay lands
- 2026-07-01 — Bruno Scripting working session (10:30, Teams) → [[Meetings/Bruno Scripting]]
- 2026-06-29 — DM: SNAP 500s status — ICONIC known SKU-query 500, new ones since 15:45 (tail of the BM2/inovize-503 outage)
- 2026-06-29 — asked (group DM) if AI can compose a Confluence doc from a template; I offered to walk him through it today
- 2026-06-23 — NMFC code-mapping thread (class = first 2 digits; wary of an eng change driven by bad SNAP data)
- SNAP dB5 Site 0010 BM2 deployment updates

## Links
- (ILG — no Fuse Jira / GitHub)
