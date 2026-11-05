---
tags: [person]
role: Solutions / Integration lead
org: ILG (ilguk.com)
relationship: leadership
team: Projects
reports_to: "[[Peter Liu]]"
title: Lee Simmons
---
# Lee Simmons
> ILG solutions/integration lead; funnels customer + integration asks to me; currently overloaded.

## Coordinates
- Slack: `@Lee Simmons` (not in the eng workspace)
- Email: lee@ilguk.com

## Open loops
**I owe**
- [ ] Answer him: does the blank SFTP status-mapping fix apply to all SFTP customers or only Byoma? [[Matt Shaw]] traced the blank status column, and the goods-in confirmation change ships Mon 19 Oct — [Lee's reply](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAHLFMPYAAA%3D&exvsurl=1&viewmodel=ReadMessageItem) — 10-16: still open in the digest (carried ×2), tick if Jack's reply covered it
- [x] Weigh in on the "Purdy & Figg — Duplicate Lines" thread (ILG ticket 48482577955) — Darren asked him to share it with SNAP; Jack Bailey also on it
- [x] Investigate the HERMES→EVRI broken tracking-link mismatch he raised (forwarded by [[Chris Cumings]]) — [digest](../Digests/2026-10/2026-10-09.md)
- [ ] Sign off the Dock & Bay/Fulfil carrier-field mapping question — Lee answered on-thread but it may still need Harry's sign-off
- [ ] Confirm coverage of FUSE-build mapping questions while he's away again — named Harry as the contact on the Dock & Bay/Fulfil thread ([email](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAG0S3wQAAA%3D&exvsurl=1&viewmodel=ReadMessageItem))
- [ ] Weigh in on his despatch-interface filter proposal — wants to change a filter (stus=0) to stop items hitting the SNAP queue, cc [[Jack Bailey]] — [email](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAG34WxLAAA%3D&exvsurl=1&viewmodel=ReadMessageItem)
- [ ] Answer which SFTP egress formats Fuse actually supports — [[Tom Dunn]] asked whether plain JSON rather than JSONL confirmations are a Fuse requirement, and Lee can't tell which JBMQ clients are on it — email "Re: FUSE JSON to SFTP Confirmations" (09-07)
- [ ] Install the SPS Commerce public key for [[Manucurist]] prod — Lee committed me to it "over the next few days" (key attached 08-10), not yet actioned
- [ ] Diagnose why Saira Skin's ship-method mapping is still broken in DEV after copying the Gadgets template
- [x] Give Lee a time for the [[Fulfil]] (Dock & Bay) ERP call — invite sent 07-22: Fri 24/07 11:00–11:45 BST "Lee/Harry - fulfil.io catch up"
- [x] Resolve which Fulfil slot is live — both are: 11:00 is our internal prep, 16:30 is the external vendor call (Zoom + agenda) with Dhairya Goel + Sarah — → [[Meetings/ILG - Fulfil Dock and Bay Integration]]
- [x] Decide whether to attend the 16:30 external Fulfil call given my approved half-day leave — didn't attend
- [ ] Catch up on what was agreed on Friday's Fulfil (Dock & Bay) call — I missed it and owe myself the readout before speaking to it
- [ ] Feed back on [[Keith Rigg]]'s extraction-project docs — now complete for all 9 test customers, and Lee's own review lands today, so my half is the open one
- [x] Resolve the missing invite for the Charlotte Tilbury / Accenture session — resolved without me: the session ran Wed 07-29 10:00 with Lee handling it, Accenture circulated minutes (I'm cc)
- [ ] Validate the Fulfil goods-in table he posted in Slack — gates his "payloads to Fulfil by end of this week" promise; the technical-team review he promised the vendor is me
- [ ] Deliver the documented **Postman collection** for Dhairya (fulfil.io shipment + SO integration) — I committed to end of week in #bifrost-general — **today is EOW** — [thread](https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1785313047263639)
- [ ] Answer Dhairya's outstanding Dock & Bay API questions Lee forwarded (kit/FBA/B2B flags, lot-tracking/FEFO) plus a Postman-collection discrepancy list — acked "I'll take a look" Friday evening, substantive answer still owed — [DM](https://gfsdeliver-eng.slack.com/archives/D0BLE6QQD4Z/p1786114647973339)
- [ ] Joint answer (w/ [[Jack Bailey]]) to SPS Commerce's amquick — asking to move [[Manucurist]] to production and requesting production credentials — Lee is cc'd on the same thread
- [ ] Answer two technical questions in the Dock & Bay/ILG Fulfil ERP integration email thread that @-mention me directly, still unanswered — [thread](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAGklci5AAA%3D&exvsurl=1&viewmodel=ReadMessageItem)
- [ ] Reposition the **Stage column** (between TotalWeight/StockPool) in the SPS confirmation CSV — [[Ashley Quick]] replied 07-29 "otherwise all good for Next Beauty" and Lee handed the reorder to me on-thread
- [ ] Fix the SPS/[[Manucurist]] order-number-missing regression Ashley Quick reported (07-24) — likely related to the field-order mismatch below and/or [FUSE-954](https://globalfreight.atlassian.net/browse/FUSE-954)
- [ ] Diagnose the [[Manucurist]] / SPS test-order **field-order mismatch** — Ashley Quick reports the confirmation CSV's field order doesn't match the user guide (07-13 18:38, attachment supplied)
- [ ] Loop in Sarah Davenport (+ make Darren optional) on the next Fulfil call, per Darren's ask
- [x] Reply on [[Fulfil]] ERP SKUs — Lee resolved with new SFTP credentials (02/07 16:59); thread reads closed
- [ ] CSL putwall — agreed (Lee + [[Jack Bailey]]) to build in Fuse; scope it + confirm next step

**Owed to me**
- [ ] A firm [[Charlotte Tilbury]] / Accenture integration timeline — re-committed on 09-04 to push the integration team, still nothing back (carried since 2026-09-02)
- [ ] Send Inovize the detailed response [[Peter Liu]] has committed he will send
- [ ] Confirm he's paused sharing further Fulfil / Dock & Bay payload detail until dev has validated what's already been shared — asked him to hold on the 9-message thread (07-26 to 07-28)
- [ ] The scoping-requirements cross-reference ILG is finalising this week (his 07-27 email) — until it lands, ILG's CT discussion points aren't ready
- [ ] Nothing on the [[Fulfil]] / Dock & Bay thread — he's driving it himself and confirmed nothing is pending on me

## Standing context
- On leave as of this week (2026-08-19) — Darren Cobby and Peter Liu are fielding the Dock & Bay/Fulfil.io ERP integration thread in his absence
- Off 2026-08-06 — Sarah (Dock & Bay) had to ask #bifrost-general who covers Dhairya while he's out
- Overloaded (24/06 huddle flagged it); Steve retiring adds load → BA/TA hire proposed
- Owns the customer-facing ILG integration relationships ([[SPS Commerce]], [[Manucurist]], [[Fulfil]], putwall)
- Annual leave off his signature (07-27): 6 Aug, 17–21 Aug, 14–28 Sep
- Dock & Bay is live in SNAP under business DOCKBAY with credentials confirmed working
- He drives the [[Fulfil]] / Dock & Bay thread directly with the vendor (Dhairya Goel) — sample payloads and clarifying questions go through him, not me
- Fixed the [[Manucurist]] credentials so they only receive confirmations for orders they genuinely send
- Has stated a priority pivot: CSV egress plus Pick/Pack Confirmations are the focus because they unlock the most use cases, Zedonk included
- The JSON work is deferred behind CSV egress and Pick/Pack Confirmations
- ✍️ 

## Together (newest first)
- 2026-11-04 — Test DB patch went onto DB2 only and the fix tested OK; emergency all-DB SNAP patch announced for 10:00 GMT on 5 Nov (45 to 60 minutes) → [email](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAHaGM3zAAA%3D&exvsurl=1&viewmodel=ReadMessageItem)
- 2026-11-03 — emailed that customer IconicL is deleted from Fuse dev and prod (Ionic short-ship closure)
- 2026-10-16 — "Migration thread: hypercare ownership": his L2 Projects team owns hypercare for FUSE migrations and new business, and the thread reads as closed with Ryan and Darren agreed
- 2026-10-13 — goods-in confirmations thread: he is happy for James (ILG) to fix the blank SFTP status mapping and asks whether it applies to all SFTP customers or only Byoma
- 2026-10-09 — he and [[Matt Shaw]] resolved the "Works Orders via SFTP - Gadgets Testing" email thread: CT works orders carry no carrier or ship method, so no carrier field is needed
- 2026-09-17 — emailed "Re: Shipping Errors - Fuse Logs" proposing a despatch-interface filter change (stus=0) to stop items hitting the SNAP queue, wants Fuse-side input, cc [[Jack Bailey]]
- 2026-09-14 — new Purdy & Figg "Duplicate Lines" thread (ticket 48482577955) — Darren asked him to share with SNAP, Jack Bailey also on it; Fulfil.IO Dock & Bay carrier-field mapping answered on-thread but may still need Harry's sign-off; CT SAP timeline reply landed (testing early/mid-Nov) but the client asked who's attending the biweekly calls since no one from ILG showed this week
- 2026-09-11 — going away again: Dock & Bay/Fulfil thread now names Harry as the mapping-question contact for the FUSE build while he's out; CT SAP thread continues, Accenture pressing for an EDI dev timeline
- 2026-09-10 — two VIP threads: (1) CT SAP — will share a projected timeline + "further questions for you and the dev team" this week, and Accenture (Rafa) is now flagging the **EDI dev timeline as a delivery risk** in-thread (raise at the Oli 1:1); (2) Fulfil Dock & Bay — carrier/ship-method mapping question (CARRIER is always NETCOURIER), I'm on the To line, still owe a reply. Also [[Chris Cumings]] forwarded Lee's HERMES→EVRI broken-tracking-links report (Shopify/FUSE)
- 2026-09-09 — new "[Fulfil.IO] Re: Dock & Bay / ILG - Fulfil ERP Integration" email from Dhairya Goel with Lee cc'd (direct To me) — integration update on the active Dock & Bay thread, needs a read/reply; the firm CT/Accenture integration timeline he re-committed to chasing on 09-04 is still not back
- 2026-09-07 — emailed "Re: FUSE JSON to SFTP Confirmations" (VIP, direct To) relaying [[Tom Dunn]]'s question on whether plain JSON rather than JSONL SFTP confirmations are a Fuse requirement, which he can't answer himself because he can't tell which JBMQ clients are on it
- 2026-09-04 — happy with the Jitterbit plan on [INOVIZE-966](https://globalfreight.atlassian.net/browse/INOVIZE-966) (Escentric Line Level Engraving) — Tom Dunn to update the Inovize ticket once he's clarified with the customer; sent Fulfil.io the Dock & Bay onboarding pack + shipping-route answers, thread still open; committed (again) to chasing the integration team for CT/Accenture timelines ahead of today's 14:00
- 2026-09-03 — email: confirms he's already sent Sarah (Dock & Bay) the item she'd requested — FYI, no action needed; on the invite for today's 14:00 [[Meetings/Charlotte Tilbury SAP - ILG Integration Catch Up]] alongside [[Jack Bailey]] (who's OOO) and ~10 Accenture/Puig/CT contacts
- 2026-09-02 — Dock & Bay/Fulfil thread: sent answers + onboarding pack to Fulfil.io, I'm cc'd throughout (worth confirming nothing further needed); CT SAP thread: Sham Ahmad chasing "ASAP" (09-01), Lee replied (08-31), other 3PLs reportedly ahead — [[Jack Bailey]] (who'd normally own the CT room) is OOO through 14 Sep, so today's [[Meetings/Fuse-Bifrost Weekly Sync]] is a good venue to move both along
- 2026-08-28 — shared the Charlotte Tilbury SAP/ILG integration pack (email), for discussion in September — no immediate action, just context ahead of that
- 2026-08-19 — [[Meetings/Fuse-Bifrost Weekly Sync]] (13:00): SPS Commerce↔[[Manucurist]] `/to_ilg` subfolder item still open, no update this week; on leave this week, with Darren Cobby + Peter Liu fielding the Dock & Bay/Fulfil ERP integration thread in his absence — that thread has two technical questions @-mentioning me directly, still unanswered
- 2026-08-13 — SPS Commerce/[[Manucurist]] thread now shows production SFTP connectivity confirmed both sides (amquick reply) — go-live thread closing out, worth a glance for any final ack needed; Saira Skin ship-method mapping still unresolved, and the SPS key install he committed me to on 08-10 still not actioned
- 2026-08-12 — new unread thread: Saira Skin ship-method mapping still broken in DEV after copying the Gadgets template — a live ILG-flagged gap; the SPS public-key install he committed me to "over the next few days" (attached 08-10) still hasn't been actioned; on leave next week, flagged as a risk to the Shopify load test if it slips
- 2026-08-10 — sent (DM) Dhairya's outstanding Dock & Bay API questions + a Postman-collection discrepancy list, still owed a substantive reply; separately proposed (email) a regroup next week to retest Shopify CSV order-upload performance; cc'd with [[Jack Bailey]] on SPS Commerce's amquick asking to move [[Manucurist]] to production
- 2026-08-06 — off today; his SPS Commerce/[[Manucurist]] mapping-change PROD sign-off request is resolved on my side, now waiting on customer retest; Sarah (Dock & Bay) asked who covers Dhairya in his absence — worth a reply since I have the technical history
- 2026-07-31 — organising today's [[Meetings/FUSE Shopify Load Test Call]] (13:00, rescheduled from Thursday) — plan to load-test the Shopify connector with 5,000+ shipments on the Gadgets account; SPS Stage-column reorder and the Fulfil goods-in-table validation both still sitting on me, and today's the EOW deadline I gave for the Dhairya Postman collection
- 2026-07-29 — the CT/Accenture session finally ran (10:00, he handled it, minutes circulated); [[Ashley Quick]] came back on the SPS thread — all good for Next Beauty bar the Stage-column position, which Lee handed to me; on Fulfil he promised the vendor payloads "by end of this week" pending my validation of his goods-in table, and I committed to the Dhairya Postman collection by EOW
- 2026-07-29 — his CT/Accenture invite commitment to [[Patricia Navarro Vaquero]] (confirmed 07-28 07:50) still hasn't reached my calendar and has now visibly slipped; his SPS TEST3 follow-up to [[Ashley Quick]] (07-28 11:10) remains unanswered; on the 9-message Fulfil/Dock & Bay thread since 07-26 I've asked him to pause sharing further payload detail until dev validates it; attends today's [[Meetings/Fuse-Bifrost Weekly Sync]] and [[Meetings/Fuse Support & Operational Ownership]] — a busy day for him and me together
- 2026-07-28 — chased the CT/Accenture invite question with no answer back from Accenture, and says ILG is still cross-referencing scoping-session requirements against current capability so tomorrow's discussion points aren't ready; on [[Fulfil]] / Dock & Bay he moved 5 messages yesterday — sample Goods In and product payloads sent, Dhairya Goel back with further clarifying questions on Goods In, and he's driving it with nothing pending on me
- 2026-07-27 — together in [[Meetings/Bifrost SteerCo]] (14:30) where items 1 and 3 are his, off the back of three fresh emails needing me — the missing Wednesday CT/Accenture invite, his weekend review of [[Keith Rigg]]'s extraction docs landing today, and SPS TEST3 possibly carrying the wrong shipment
- 2026-07-24 — both Fulfil sessions confirmed live today (11:00 prep + 16:30 external vendor call) → [[Meetings/ILG - Fulfil Dock and Bay Integration]]; her SPS/Manucurist thread now carries a real order-number-missing bug report from Ashley Quick; Keith Rigg uploaded revised extraction docs
- 2026-07-23 — a SECOND Fulfil/Dock & Bay Zoom now shows booked Fri 24/07 16:30–17:00 BST — reconcile against the 11:00 invite before accepting either; Darren wants Sarah Davenport added to the next call
- 2026-07-22 — pressing [[Keith Rigg]] hard on the extraction-doc slippage ("today or not?"); Fulfil call booked for Fri 24/07; told [[Ashley Quick]] the new Manucurist file goes out first thing this morning (I should verify it went)
- 2026-07-21 — confirmed he's free for the [[Fulfil]] (Dock & Bay) call, waiting on me for a time; separately pushing [[Keith Rigg]] again for the extraction docs date (Jack Bailey cc'd)
- 2026-07-20 — together in [[Meetings/Bifrost SteerCo]] (13:30, 6-item agenda — his items: Pilot Migration & Process Refinement, Discovery and Configuration Auditing); cc'd on [[Tom Dunn]]'s new Custom Outbound Mapping/Scribe ask; Fulfil webhook + Keith Rigg + Ashley Quick field-order loops all still open
- 2026-07-16 — closing "thanks, appreciate it" on the SPS/[[Manucurist]] field-order thread; Fulfil (Dock & Bay) vendor Dhairya Goel chasing the webhook/API docs again (To: Lee + me; Lee OOO til Fri → likely lands on me); Lee OOO until Friday
- 2026-07-13 (evening) — thanked me on the SPS/[[Manucurist]] TEST2 thread as it closed out; Ashley Quick separately flagged a confirmation-CSV field-order mismatch on the same thread (18:38); chasing [[Keith Rigg]] again for the extraction-project doc (14:06)
- 2026-07-13 — together in [[Meetings/Bifrost SteerCo]] (13:30); thread live: asked Ashley Quick to confirm the SPS/[[Manucurist]] TEST2 confirmation file landed correctly, still awaiting her reply; [[Keith Rigg]]'s 9-customer doc pack uploaded to OneDrive, Lee's review still outstanding; Fulfil.IO (Dock & Bay) support ticket #87630 chasing a status update (To: Lee + me)
- 2026-07-10 — Lee gave RGA API feedback (two items need engineering); leaning to pivot the Shopify pilot to another customer if no [[Saira Skin]] reply today; chasing [[Keith Rigg]]'s active-only extraction docs
- 2026-07-09 — extraction-project / CT SAP migration live ([[Keith Rigg]] 1pm call, I gave the priority stack-rank); [[Saira Skin]] Shopify migration may pivot first-customer if no dev-store reply; SPS ([[Ashley Quick]]) resent [[Manucurist]] test orders for a confirmation retry
- 2026-07-07 — [[Meetings/Fuse-Bifrost Weekly Sync]] (13:00); live threads: [[Fulfil]] webhook Qs (@'d me), [[Keith Rigg]] extraction-project call today, SPS/[[Manucurist]] test orders re-requested
- 2026-07-02 — [[SPS Commerce]] / [[Manucurist]] onboarding thread (email): ship-method NEXTDAY/SAMEDAY + confirmation-pickup decisions; I'm on the To: line
- 2026-06-30 — tagged me (email) on the [[Fulfil]] ERP SKU-casing thread (uppercase round-trip)
- 2026-06-29 — confirmed (email) to build the CSL putwall requirement inside Fuse; in [[Bifrost SteerCo]] (his pilot-migration agenda item)
- 2026-06-25 — SPS / [[Manucurist]] thread escalated (test orders failing)
- 2026-06-24 — putwall project scoping
- 2026-06-23 — fixed his [[SPS Commerce]] SFTP permission-denied (`/home/FUSE_521239C5D7`)

## Links
- (ILG business side — no Fuse Jira / GitHub)
