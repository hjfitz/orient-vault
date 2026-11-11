---
tags: [meeting]
series: Fuse/Bifrost Weekly Sync
title: Fuse/Bifrost Weekly Sync
---
# Fuse/Bifrost Weekly Sync

## 2026-11-11
_13:00–13:45 GMT · calendar title "Weekly Bi-Frost/FUSE Update" · [[Darren Cobby]] (organizer), [[Jack Bailey]], [[Lee Simmons]], [[Tom Dunn]], [[James Godsell]], [[Ryan Ellis]], [[Denis Tomolea]], Danny Williams, you · Teams_
_Agenda on the invite: Fuse update and roadmap (Jack), customer update (Darren Cobby), QA update (Tom), integrations update (James), AOB. You have no named item_

### Context

**Open loops to raise**
- [[James Godsell]]'s ask for `identifiers.solLineId` in the pick and pack confirmation line mappings is unanswered, and no ticket exists
- [[Tom Dunn]]'s work-order and finished-good-receipt QA gaps are FUSE-1352 and FUSE-1353
- FUSE-1352 and FUSE-1353 are unassigned Sev 3 bugs in Ready for Development
- Indu go-live is Monday 16 Nov at 10:00 (JBMQ to Fuse middleware migration, rollback to JBMQ possible)
- CT PRICAT SFTP folders: [[Jack Bailey]] advised [[Darren Cobby]] that CT should log in and create its own
- CT EDIFACT stress-test action from the 9 Nov leadership catch-up: the team quietly tests CT's EDIFACT and Edicom sample files
- [[Jack Bailey]]'s 9 Nov Fuse Product Update (Purdy & Figg peak ramp-up runs clean)
- BAT SAP migration early notice, forwarded by [[Jack Bailey]]: a top-3 customer moving onto Fuse

### To raise
- [ ] Reply to [[James Godsell]] on `solLineId` and agree the ticket
- [ ] Confirm FUSE-1352 and FUSE-1353 owners and sizing with [[Tom Dunn]]
- [ ] Confirm engineering watches the Indu go-live on Monday 16 Nov at 10:00
- [ ] Tell [[Darren Cobby]] and [[Jack Bailey]] how the CT SFTP folders get created
- [ ] Ask [[Jack Bailey]] for the BAT SAP migration timeline

### Carried from last time
- [ ] [[SPS Commerce]]↔[[Manucurist]] `/to_ilg` subfolder (open with Ashley / [[Lee Simmons]]) — no update logged since 08-19

### Notes
- ✍️ 

## 2026-10-21
_13:00–13:45 BST · calendar title "Weekly Bi-Frost/FUSE Update" · [[Darren Cobby]] (organizer), [[Jack Bailey]], [[Lee Simmons]], [[Tom Dunn]], [[James Godsell]], [[Ryan Ellis]], [[Denis Tomolea]], [[Hayley Prior]], Danny Williams, Alexander Saunders, you · Teams_
_Agenda on the invite: Fuse update and roadmap (Jack), Bi-Frost customer update (Darren), QA update (Tom), integrations update (James), AOB. You have no named item and only you have responded. Jack is away today_

### Context

**Open loops to raise**
- GCP outage on 20 Oct: Shopify and API recovered, SFTP clients must resubmit files (Jack's follow-up), and ArtEssence reported the live SFTP down at 09:55 BST. INC-40 is closed; INC-41 is probably still open
- Snap: the 19 Oct outage, today's 08:00 cluster change and DB1 update at 09:30, and Ryan's line that ILG is logging every outage before Peak
- CT SAP (EDIFACT): files from 21 Oct, master data 22 Oct, DESADV 26 Oct, sales orders 28 Oct; ILG's single UK GLN is settled for UK and Poland
- Purdy & Figg load test on ILGSTG: Tom said "please proceed" on 19 Oct; Ryan and Jake still need a date and time from you
- Peak on-call hours and the support model: a small meeting with Ryan and Dennis, ideally Thursday
- [[Darren Cobby]]'s open ask on the Escentric dates and whether Sistaco can migrate before Peak, with the Eccentric Molecules go/no-go due today

### Carried from last time
- [ ] [[SPS Commerce]]↔[[Manucurist]] `/to_ilg` subfolder (open with Ashley / [[Lee Simmons]])

### Notes
- ✍️

## 2026-10-14
_13:00–13:45 BST · w/ [[Jack Bailey]] (organizer), [[Lee Simmons]], [[Tom Dunn]], [[James Godsell]], [[Ryan Ellis]], [[Darren Cobby]], [[Matt Shaw]], Alex, Hayley, Steve Greenwood, Denis Tomolea, Danny Williams, [[Peter Liu]] · Teams_
_⚠️ Generic agenda only. Topics go in the meeting chat, and the series is cancelled if nobody raises one_

### Context

**Open loops to raise**
- Goods-in confirmation change on Mon 19 Oct: Jack recommends updating the mapping for all active customers, with a Dev test that Schuster deploys. [[Lee Simmons]] wants Customer Support clear on what they ask customers, and [[Tom Dunn]] and Lee do not know who holds recent comms with two of the listed customers. ILG must flag concerns by Thu 15 Oct
- Integrations Path Forward workshop: hypercare action extended to 1 Nov; Jack is chasing action owners
- Fuse Product Update (12 Oct): Snap sees no issues with how Fuse connects, and a Peak scaling call with Snap is set up for 11:30 today
- Peak on-call hours and escalation route still owed to [[Ryan Ellis]]

### Carried from last time
- [ ] [[SPS Commerce]]↔[[Manucurist]] `/to_ilg` subfolder (open with Ashley / [[Lee Simmons]])

### Notes
- ✍️


## 2026-10-07
_12:00–12:45 BST · w/ [[Jack Bailey]] (organizer), [[Lee Simmons]], [[Ryan Ellis]], [[James Godsell]], [[Tom Dunn]], [[Darren Cobby]], [[Matt Shaw]], Alex, Hayley, Steve Greenwood, Denis Tomolea · Teams_
_⚠️ Generic agenda only. Jack's note says it is cancelled if nobody raises a topic. Lee, Ryan and Steve have accepted; Darren, Tom, James, Hayley, Matt and Denis have not responded_

### Context

**Open loops to raise**
- Peak on-call coverage. [[Ryan Ellis]] thanked you for the Peak info on 10-07. You owe him the on-call hours and escalation route once agreed with [[Oli Denton]] (Harry/Oli 1:1 is Thu 08:30). Purdy & Figg's sale is 7–8 Nov, about 60k orders projected — [email](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAHHiU5YAAA%3D&exvsurl=1&viewmodel=ReadMessageItem)
- Snap throughput ahead of stock sync. Your 10-06 reply raised about a 10h backlog into Snap at 2M records/day in testing; Ryan said he will answer the capacity thread himself. Snap maintenance Thu 8 Oct 15:00–16:30 (no ILG downtime expected, possible slowness) — [email](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAHExRLcAAA%3D&exvsurl=1&viewmodel=ReadMessageItem)
- Engraving / Gadgets test order. [[Tom Dunn]] wants line-level properties configured against Gadgets; [[James Godsell]] has only mapped such fields, never set them up in Shopify. The thread is stalled on James — [email](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAHExRLsAAA%3D&exvsurl=1&viewmodel=ReadMessageItem)
- Fulfil.IO / Dock & Bay. Fulfil sent transfer order IS147, is splitting addresses across lines 1–3 (50 characters each, 150 total) and will use "." as the fallback last name. IS145 is stuck and returning API responses is "on the roadmap". You are cc only; Tom owns it — [email](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAHExRL6AAA%3D&exvsurl=1&viewmodel=ReadMessageItem)
- [[Darren Cobby]]'s open ask for a target-customer and progress update (nothing sent since 09-28) — [email](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAHBMDI3AAA%3D&exvsurl=1&viewmodel=ReadMessageItem)

### Carried from last time
- [ ] [[SPS Commerce]]↔[[Manucurist]] `/to_ilg` subfolder (open with Ashley / [[Lee Simmons]]) — no update logged since 08-19

### Notes
- ✍️

## 2026-09-30
_13:00–13:45 BST · w/ [[Jack Bailey]] (organizer), [[Lee Simmons]], Alex Saunders, [[Tom Dunn]], Hayley Prior, James Godsell; optional: [[Matt Shaw]], Ryan Ellis, Denis Tomolea, Steve Greenwood · Teams_
_⚠️ [[Darren Cobby]] has declined. The invite says it's cancelled if nobody raises a topic; agenda items go in the meeting chat beforehand_

### Context

**Open loops to raise**
- [[Darren Cobby]]'s open asks (target-customer update, WO/WOC/FGR status over CSV/API/JSON, Datadog training for Ryan Ellis, James Godsell and Denis Tomolea). He said today's sync can carry the training ask
- Charlotte Tilbury plan and dates. [[Lee Simmons]] says the build runs to November; Accenture will date the 7 messages to code this week — [email](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAHCN1q6AAA%3D&exvsurl=1&viewmodel=ReadMessageItem)
- [[Tom Dunn]]'s QA defects [FUSE-1272](https://globalfreight.atlassian.net/browse/FUSE-1272) to [FUSE-1276](https://globalfreight.atlassian.net/browse/FUSE-1276): unassigned, allocation agreed at standup first
- Dock & Bay: Alex Saunders says stock upload is blocked until the full master-data catalogue is in SNAP. Our D2/D7 master-data watch monitors have been in Alert since 09-29 19:50Z

**Product context**
- [[Jack Bailey]]'s 09-28 Fuse Product Update: 14 customers trading, about 2,000 orders/day, Dock & Bay live 29 Sep, Stock Sync late October. Support model goes to Thursday's "Integration Looking Forwards" session (BM1)

### Carried from last time
- [ ] [[SPS Commerce]]↔[[Manucurist]] `/to_ilg` subfolder (open with Ashley / [[Lee Simmons]]) — no update logged since 08-19

### Notes
- ✍️

## 2026-09-23
_12:00–12:45 UTC · w/ [[Jack Bailey]] (organizer), [[Matt Shaw]], Steve Greenwood + ILG's Darren C, Alex, Thomas Dunn, Hayley P, James Godsell, Ryan Ellis, Denis Tomolea, [[Lee Simmons]] · Teams_
_⚠️ Lee Simmons has declined this occurrence_

**Likely to come up**
- **Dock & Bay ↔ Fulfil ERP webhook auth (401s)** — Alex Saunders (ILG) emailed Harry directly asking for help; Tom Dunn/James/Alex have been troubleshooting with Fulfil.IO support since Sunday (~16 messages), still unresolved as of Tuesday evening. Heavy attendee overlap with this call (Tom, James, Alex, Ryan Ellis all on both) — natural place to raise/resolve live rather than by email.
- **Robert's Datadog access** — Denis Tomolea chased Harry + Jack directly; credential reset/resend still pending after expiry.
- SPS Commerce↔[[Manucurist]] `/to_ilg` subfolder — carrying again, no fresh update gathered this run.

**Carried from last time**
- [ ] [[SPS Commerce]]↔[[Manucurist]] `/to_ilg` subfolder (open with Ashley / [[Lee Simmons]]) — no update logged since 08-19

**Notes**
- ✍️

## 2026-09-16
_12:00–12:45 UTC · w/ [[Jack Bailey]] (organizer), [[Lee Simmons]] (OOO until 28 Sep), Darren Cobby, Thomas Dunn, [[Matt Shaw]], Steve Greenwood, James, Alex, Hayley P, Ryan E, D Tomolea · Teams_

**Likely to come up**
- **[[Ryan Ellis|Ryan E]] asked (email, today) for 15 min on this call** re Purdy & Figg go-live support fallout + some outstanding Slack items — worth putting near the top of the agenda since he flagged it same-day.
- **09-14 huddle w/ [[Oli Denton]] + [[Jack Bailey]] surfaced several threads likely to resurface here**: Charlotte Tilbury EDI has slipped to mid-November (not the previously-cited 28 Sep master-data date); the support-model/escalation ownership gap (no playbook, apps team unresponsive) is still open; a peak-season on-call rota was proposed; a Bifrost programme intervention meeting is planned for the 28th. Harry owes: gauging team on-call appetite and forwarding the prior support-model context email to Oli/Jack — see [[People/Oli Denton]] / [[People/Jack Bailey]] open loops.
- SPS Commerce↔[[Manucurist]] `/to_ilg` subfolder — carrying again, no update logged since 08-19.

**Carried from last time**
- [ ] [[SPS Commerce]]↔[[Manucurist]] `/to_ilg` subfolder (open with Ashley / [[Lee Simmons]]) — no update logged since 08-19

**Notes**
- ✍️

## 2026-09-02
_12:00–12:45 UTC · w/ [[Jack Bailey]] (organizer), [[Lee Simmons]], Darren Cobby, Thomas Dunn, [[Matt Shaw]], Steve Greenwood, James, Alex, Hayley P, Ryan E, D Tomolea · Teams_
_⚠️ Jack is OOO through 14 Sep — confirm whether a delegate is running this or it's effectively cancelled today_

**Likely to come up**
- ✅ **[[Darren Cobby]]'s 09-01 escalation — resolved this morning.** Purdy & Figg SNAP order intake reportedly stopped ~12:00 UTC 09-01; Harry confirmed direct with [[Ryan Ellis]] on Teams that it's a non-issue. Datadog had shown real `snap_adapter`/`snap-polling-service`/`shopify-connector` errors clustered 10:05–17:00 UTC 09-01, nothing since — consistent with the resolution. Good news to share in the room. Separately, two deeper tech-debt findings from the go-live war room remain open and are NOT covered by this resolution: repeated/un-replayable orders from wide retrieval windows; retry-queue silently amending site ID `'0010'`→`'10'` — see [[Meetings/Purdy and Figg Go-Live War Room]].
- **shopify-connector#234 (fleet-wide tar-CVE allowlist) merged this morning** — the blocker noted here on 08-26 for #214/#215 is cleared; #215 (store-api Logger mock) also merged. #214 (FUSE-785, kit short-ship tagging) just needs a reviewer now.
- Sprint 14 nominally ended 2026-08-10 and is **still** the active sprint in Jira — now **5+ weeks** overrun (raised 08-12, 08-19, 08-26, still unresolved) — worth escalating past a fourth ask since Jack (who owns the sprint boundary) is out.
- SPS Commerce↔Manucurist `/to_ilg` subfolder — no fresh update gathered this run; carrying as still open.
- Charlotte Tilbury SAP integration — Sham Ahmad (CT) chasing Lee "ASAP" (08-31/09-01 thread), other 3PLs reportedly ahead in build; Jack (who'd normally own this) is OOO.

**Carried from last time**
- [ ] [[SPS Commerce]]↔[[Manucurist]] `/to_ilg` subfolder (open with Ashley / [[Lee Simmons]]) — no update logged since 08-19

**Notes**
- ✍️

## 2026-08-26
_12:00–12:45 UTC · w/ [[Jack Bailey]] (organizer), [[Lee Simmons]], Darren Cobby, Thomas Dunn, [[Matt Shaw]], Steve Greenwood, James, Alex, Hayley P, Ryan E, D Tomolea · Teams_

**Likely to come up**
- **Purdy & Figg go-live readiness** — Monday's (24/08) huddle with Jack + Matt flagged low confidence in James/Lee's tagging-logic effort; a Wednesday go/no-go call was agreed but **is not on today's calendar** — worth raising directly since this is that Wednesday. Harry's own follow-through (6K test-order soak, mock-order verification in Snap, escalating to Pete/Ollie) not independently confirmed done — see [[Bifrost/Purdy & Figg Testing/Overview]].
- Sprint 14 nominally ended 2026-08-10 and is **still** the active sprint in Jira — now 16 days overrun (raised 08-12, 08-19, still unresolved) — worth a third ask since Jack owns the sprint boundary.
- Dock & Bay / Fulfil ERP integration — Thomas Dunn's 08-25 note (#36189, manual SKU amendment) surfaces the known SAIRA-style gap (a manually-added SKU lacking the Shopify line-level ID Fuse relies on); not yet addressed to Harry directly but the same underlying gap as [[Darren Cobby]]'s still-open technical questions.
- SPS Commerce↔[[Manucurist]] `/to_ilg` subfolder — still open per Lee's tracker, no update logged since 08-19.
- shopify-connector#214/#215 (FUSE-785, kit short-ship tagging + a pre-existing test-mock fix) are both still blocked on sibling #234 shipping the fleet-wide tar-CVE allowlist fix first — #234 itself just needs a reviewer, unchanged since last week.

**Carried from last time**
- [ ] [[SPS Commerce]]↔[[Manucurist]] `/to_ilg` subfolder (open with Ashley / [[Lee Simmons]]) — no update logged since 08-19

**Notes**
- ✍️

## 2026-08-19
_13:00–13:45 · w/ [[Jack Bailey]] (organizer), [[Lee Simmons]], Darren Cobby, Thomas Dunn, [[Matt Shaw]], [[Steve Greenwood]], D Tomolea + 5 others · Teams — series was just renewed after expiring, no specific agenda sent_

**Likely to come up**
- SNAP prod outage 2026-08-18 ~14:20–20:38 UTC, now resolved — 49 sales orders exhausted retry budget (STUBBLE 25, EPARFUM 9, WILDSMITH 8 via SFTP + SAIRA 6 via Shopify + DISCOVERED 1 via SFTP), all captured in replay-service with dedupe gates released; Harry redriving the 43 SFTP orders today now SNAP is confirmed stable — good status line if asked, source: [Slack](https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1787080420212709)
- Sprint 14 nominally ended 2026-08-10 and is **still** showing as the active sprint in Jira 9 days later — same gap flagged on 08-12 and still unresolved; worth raising again since Jack owns the sprint boundary
- Dock & Bay / ILG Fulfil.io ERP integration thread has two technical questions @-mentioning Harry still unanswered while Lee Simmons is on leave (Darren/Peter fielding the rest) — [thread](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAGklci5AAA%3D&exvsurl=1&viewmodel=ReadMessageItem)
- Saira Skin go-live — Peter Liu sent a high-importance team thank-you; good news to share if it comes up
- shopify-connector#214 (FUSE-785, tag short-shipped orders by real Shopify order id) and #215 (store-api Logger mock fix) are chained — #214's CI failure is caused by the same pre-existing bug #215 fixes; #215 itself is stuck on the known fleet-wide `secops-dep-node` checkout regression, reran once today, failed identically — a platform-level fix, not a per-PR issue

**Carried from last time**
- [ ] [[SPS Commerce]]↔[[Manucurist]] `/to_ilg` subfolder (open with Ashley / [[Lee Simmons]]) — no update this week, Lee is on leave

**Notes**
- ✍️

## 2026-08-12
_14:00–14:45 · w/ [[Jack Bailey]] (organizer), [[Lee Simmons]], Tom Dunn, Darren Cobby, Alex, Hayley P, James Godsell, Ryan E (ILG), [[Matt Shaw]], [[Steve Greenwood]], D Tomolea · Teams — this week moved from its usual slot to fit around a CT internal catchup_

**Likely to come up**
- Sprint 14 ended 2026-08-10 with no Sprint 15 kickoff visible yet in Jira — Sprint 15 exists (board, future) but hasn't started; worth raising since Jack owns the sprint boundary
- FUSE-785 (Shopify kit order confirmations) moved to Ready for QA — the short-ship/`ILG_SHORT_SHIPPED` fix from Monday's huddle is verified on dev
- [shopify-connector#181](https://github.com/gfs-bifrost/shopify-connector/pull/181) (S0 rearchitecture baseline) unblocked this morning — was stuck on the fleet-wide dependency-audit platform bug + a merge conflict, both cleared, now just needs a reviewer
- SPS Commerce↔Manucurist production move still in flight — Lee committed Harry to installing SPS's public key "over the next few days" (key attached 08-10, not yet actioned)

**Carried from last time**
- [ ] [[SPS Commerce]]↔[[Manucurist]] `/to_ilg` subfolder (open with Ashley / [[Lee Simmons]])

**Notes**
- ✍️ 

## 2026-07-29
_13:00–13:45 · w/ [[Jack Bailey]] (organizer), [[Lee Simmons]], [[Tom Dunn]], Darren C, Alex, Hayley P, James Godsell, Ryan E, [[Matt Shaw]], Steve Greenwood, D Tomolea · Teams_
_⚠️ **post agenda items in chat before the meeting or it's cancelled**_

**Likely to come up**
- The Charlotte Tilbury / Accenture session (meant for 10:00 today) never appeared on the calendar and no discussion topics were ever sent, despite Lee confirming to Patricia yesterday that "I have the invite" — worth resolving out loud since half the attendees here are on that thread
- [[Schuster Efigenio]]'s probation review is overdue (ended 26 Jul) and HR is chasing at high importance — an internal item, not for this room, but a live deadline
- [[Keith Rigg]]'s extraction docs (all 9 test customers) — still awaiting Harry's review feedback since 07-24, Lee's own "over the weekend" estimate has slipped
- SPS/Manucurist TEST3 — Lee's 07-28 follow-up chase to Ashley Quick is still unanswered
- FUSE-633/FUSE-635 (work order create requests, dedupe + Snap Adapter) both moved to Ready for QA yesterday — good news to report if asked about the work-order flow
- Overnight nightly builds went fully green for the first time since the fleet-wide `brace-expansion` advisory broke 11 repos on 07-25 — the remediation held

**Carried from last time**
- [ ] [[SPS Commerce]]↔[[Manucurist]] `/to_ilg` subfolder (open with Ashley / [[Lee Simmons]])

**Notes**
- ✍️ 

## 2026-07-22
_13:00–13:45 · w/ [[Jack Bailey]] (organizer), [[Lee Simmons]], [[Tom Dunn]], Darren C, Alex, Hayley P, James Godsell, Ryan E, [[Matt Shaw]], Steve Greenwood, D Tomolea · Teams_
_⚠️ **post agenda items in chat before the meeting or it's cancelled**_

**Likely to come up**
- Extraction project slippage — [[Lee Simmons]] pressing [[Keith Rigg]] hard this morning ("today or not?") on the updated extraction documents — [thread](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAGURTCyAAA%3D&exvsurl=1&viewmodel=ReadMessageItem)
- [[Gisou]] Split Middleware — Returns RGA Only — [[Tom Dunn]] thinks tandem JBMQ/ILG SFTP is "probably not viable"; your counter/decision owed (re-verify the prod confirmation-mapping feature flag first)
- [[SPS Commerce]]↔[[Manucurist]] — Ashley Quick asked "has a new file been sent?"; [[Lee Simmons]] said it goes first thing this morning — verify it actually went before 13:00
- Snap prod health — Elevated Error Rate alert on `snap_adapter` creates (121 fails/12h) + 3 nights of unacked ANOMALOUS SNAP ACTIVITY — have a status line ready if asked
- SKU-blacklisting change — [[Jack Bailey]] raised Lee/Tom ownership confusion in DM yesterday; deferred to standup, may resurface here

**Carried from last time**
- [ ] [[SPS Commerce]]↔[[Manucurist]] `/to_ilg` subfolder (open with Ashley / [[Lee Simmons]])

**Notes**
- ✍️ 

## 2026-07-15
_12:00–12:45 · w/ [[Jack Bailey]] (organizer), [[Lee Simmons]], [[Tom Dunn]], Darren C, Alex, Hayley Prior, James Godsell, Ryan E, [[Matt Shaw]], Steve Greenwood, D Tomolea · Teams_
_⚠️ **post agenda items in chat before the meeting or it's cancelled**_

**Proposed agenda**
- [[Tom Dunn]]'s consolidated RGA Ingress/Egress Issue List (07-14) — [[Matt Shaw]] confirmed he's working through it; still a live direct ask this morning (07-15 07:57) for support from both of us
- James Godsell — Shopify dev app under review, Purdy & Figg may not be able to install it for testing; needs a call
- Ashley Quick (SPS) — confirmation CSV field order vs the GADGETS user guide, still open
- [[Lee Simmons]] chasing [[Keith Rigg]] on the extraction-project doc timing
- Hayley Prior's expired access link — resend

**Carried from last time**
- [ ] [[SPS Commerce]]↔[[Manucurist]] `/to_ilg` subfolder (open with Ashley / [[Lee Simmons]])

**Notes**
- ✍️ 

## 2026-07-07
_13:00–13:45 · w/ [[Jack Bailey]] (organizer), [[Lee Simmons]], [[Tom Dunn]], James + Fuse devs · Teams_
_⚠️ **post agenda items in chat before the meeting or it's cancelled**_
_(M365 date-offset: connector filed this under 07-08 — treat as today's sync, verify)_

**Proposed agenda**
- [[Fulfil]] ERP (Dock & Bay) — outstanding webhook questions; [[Lee Simmons]] @'d me, vendor (Dhairya) chasing — answer + status
- Extraction project — [[Keith Rigg]] / Peter Liu questions ahead of today's follow-up call ([[Lee Simmons]] arranging); stack-rank Keith's focus
- CT SAP migration — Integration Discovery Summary doc shared in the Oli/Jack huddle; where Fuse fits
- [[SPS Commerce]]↔[[Manucurist]] — Lee re-requesting test orders, trouble triggering confirmations
- FUSE-952 in flight: [sftp-connector#200](https://github.com/gfs-bifrost/sftp-connector/pull/200) JSON-Lines up for review; collector image-scan fix ([collector#56](https://github.com/gfs-bifrost/collector/pull/56)) pending merge

**Carried from last time**
- [ ] [[SPS Commerce]]↔[[Manucurist]] `/to_ilg` subfolder (open with Ashley / [[Lee Simmons]])

**Notes**
- ✍️ 

## 2026-07-01
_13:00–13:45 · w/ [[Jack Bailey]] (organizer), [[Lee Simmons]], [[Matt Shaw]], [[Steve Greenwood]], [[Tom Dunn]], Alex, Hayley, Ryan, James_
_⚠️ **post agenda items in chat before the meeting or it's cancelled**_

**Proposed agenda**
- [[SPS Commerce]]↔[[Manucurist]] onboarding — [[Ashley Quick]] sent an updated `create_sales_order` CSV; review + confirm next steps
- [[Fulfil]] ERP SKU-casing — outbound SKUs should round-trip UPPERCASE; Dhairya resent data, [[Lee Simmons]] awaiting my read
- SO-26839 duplicate import ([FUSE-984](https://globalfreight.atlassian.net/browse/FUSE-984)) — status for [[Alex Topea]]

**Carried from last time**
- [ ] [[SPS Commerce]]↔[[Manucurist]] `/to_ilg` subfolder (open with Ashley / [[Lee Simmons]])

**Notes**
- ✍️ 

## 2026-06-24
_13:00–13:45 · w/ [[Jack Bailey]], [[Lee Simmons]], [[Tom Dunn]], [[Steve Greenwood]], [[Matt Shaw]], Ryan E_
_⚠️ **post agenda items in chat before the meeting or it's cancelled**_

**Proposed agenda**
- 🎉 FUSE-794 metadata / traceability stack shipped (17 PRs merged 06-23)
- New P2 [FUSE-976](https://globalfreight.atlassian.net/browse/FUSE-976) [SFTP] user-creation failed (Built For Athletes)
- [[SPS Commerce]]↔[[Manucurist]] `/to_ilg` subfolder — open with Ashley / [[Lee Simmons]]

**Notes**
- ✍️ 

## 2026-06-17
_12:00–12:45 · w/ [[Jack Bailey]], [[Lee Simmons]], [[Tom Dunn]], [[Steve Greenwood]]_
_⚠️ **post agenda items in chat before noon or it's cancelled**_

**Context / proposed agenda**
- [[SPS Commerce]]↔[[Manucurist]] connection — picking up from [[Lee Simmons]] ([[FUSE-850]])
- [[EPERFUM]] SSH key — confirm added our side ([[Ankit Kansal]] awaiting reply)
- [[FUSE-953]] sidecar/cost-opt stack status — replay-service `main` CI keystone blocking the rest

**Notes**
- ✍️ 
