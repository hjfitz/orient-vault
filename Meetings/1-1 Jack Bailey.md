---
tags: [meeting]
series: Harry/Jack 1:1
counterpart: "[[Jack Bailey]]"
title: 'Harry/Jack 1:1'
---
# Harry/Jack 1:1


## 2026-11-09
_13:30–14:15 GMT · Teams · weekly Fuse catch-up (recurring, optional, no formal agenda on the invite)_

### Context

**Owed by you**
- Reply-all with call-outs on [[Darren Cobby]]'s Q1 migration timeline, which asks him and [[Tom Dunn]] to write up the customer-facing technical changes
- Refine and sequence [FUSE-1335](https://globalfreight.atlassian.net/browse/FUSE-1335) (Escentric shared UK/PL store, still Backlog and unassigned) with the November Shopify parity work
- Confirm owners and dates on his Integrations Path Forward actions, or say they stand
- Agree the Peak on-call route for engineering cover
- Grant his "Fuse EDI Evidence" and "Use-Case Readiness" artifact access requests

**Other context**
- Snap's software release was applied to staging on Friday and he is cc'd on the thread — [Fuse\Snap call thread](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAHaYrD0AAA%3D&exvsurl=1&viewmodel=ReadMessageItem)
- Black Friday and Cyber Monday volumes from ILG: Escentric, Stubble and Wildsmith run promotions, Purdy and Figg are live from Friday and now run about 33k orders a day
- Over the weekend 74 Purdy and Figg sales-order creations failed in SNAP in three short bursts and the Support Bot counted 542 held goods-out confirmations on Friday evening

### To raise
- [ ] CT PRICAT GLN: ILG has no trading-partner ID yet. Who owns getting it into the connector config in Fuse UI? (carried ×3)
- [ ] Purdy & Figg API onboarding: what changes when they move WS shipments to sales orders by API? (carried ×3)
- [ ] Workshop actions: who owns what, and by when (carried ×4)
- [ ] Dock and Bay go-live watch monitors D2, D3, D7 and D8 are still Alert (muted): does the despatch plan explain it? (carried ×4)
- [ ] Snap staging release is applied: who runs the performance testing and when?
- [ ] Black Friday cover: Purdy and Figg at about 33k orders a day plus three customers' promotions, so what is the on-call route?

### Carried from last time
- [ ] [[SPS Commerce]]↔[[Manucurist]] work split (from 06-17) — still live
- [ ] Putwall — takeaways + where FUSE fits (now agreed to build in Fuse)

### Notes
- ✍️

## 2026-11-02
_13:30–14:15 GMT · Teams · weekly Fuse catch-up (recurring, optional, no formal agenda on the invite)_

### Context

**Owed by you**
- Reply-all with call-outs on Darren Cobby's Q1 migration timeline, which asks him and [[Tom Dunn]] to write up the customer-facing technical changes
- Refine and sequence FUSE-1335 (Escentric shared UK/PL store) with the November Shopify parity work
- Confirm owners and dates on his Integrations Path Forward actions, or say they stand (he sent an updated list on Fri 30 Oct)
- Agree the Peak on-call route for engineering cover
- Grant his "Fuse EDI Evidence" and "Use-Case Readiness" artifact access requests

**Other context**
- Sistaco zero-fulfillable virtual SKUs: he replied to [[James Godsell]] on 30 Oct suggesting the SKU blacklist, which now drops only the blacklisted lines — [thread](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAHWswZAAAA%3D&exvsurl=1&viewmodel=ReadMessageItem)
- The [Fuse\Snap call thread](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAHWswZCAAA%3D&exvsurl=1&viewmodel=ReadMessageItem): Jake Smith chased on 30 Oct for a test date against Snap's ready staging environment
- [Friday's workshop update](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAHWswZGAAA%3D&exvsurl=1&viewmodel=ReadMessageItem): S9 first dev face-to-face pushed back
- CT DESADV: Fuse is not rebuilt to split returns by content for now; he is to check whether work orders (kitting) share the returns message type and send Ingrid the Fuse folder structure — [recording](http://localhost:3000/recordings/20261029-153138-d1e2)

### To raise
- [ ] CT PRICAT GLN: ILG has no trading-partner ID yet. Who owns getting it into the connector config in Fuse UI? (carried ×2)
- [ ] Purdy & Figg API onboarding: what changes when they move WS shipments to sales orders by API? (carried ×2)
- [ ] Workshop actions: who owns what, and by when (carried ×3)
- [ ] Dock and Bay go-live watch monitors D2, D3, D7, D8 and D9 are still Alert (muted): does the despatch plan explain it? (carried ×3)

### Carried from last time
- [ ] [[SPS Commerce]]↔[[Manucurist]] work split (from 06-17) — still live
- [ ] Putwall — takeaways + where FUSE fits (now agreed to build in Fuse)

### Notes
- ✍️

## 2026-10-26
_13:30–14:15 GMT · Teams · weekly Fuse catch-up (recurring, optional, no formal agenda on the invite); you are out today_

### Context

**Owed by you**
- Confirm owners and dates on his Integrations Path Forward actions, or say they stand
- Agree the Peak on-call route for engineering cover
- Approve his access request to the "Use-Case Readiness" artifact and grant "Fuse EDI Evidence"

**Other context**
- His Friday decisions on the pick/pack thread: picked quantity from stock records, fill lines in line order, each order line reported separately (FUSE-1332), delivery address and contacts left off the confirmation for now
- Escentric UK and PL go-live is Tue 27 at about 09:30, the same hour as the Poland Snap upgrade; he asked Friday whether to push it and Tom said he would raise it
- Phlur goes live this afternoon with a slow ramp expected

### To raise
- [ ] CT PRICAT GLN: ILG has no trading-partner ID yet. Who owns getting it into the connector config in Fuse UI? (carried ×1)
- [ ] Purdy & Figg API onboarding: what changes when they move WS shipments to sales orders by API? (carried ×1)
- [ ] Workshop actions: who owns what, and by when (carried ×2)
- [ ] Dock and Bay go-live watch monitors D2, D3, D7 and D8 are still Alert (muted): does the despatch plan explain it? (carried ×2)

### Carried from last time
- [ ] [[SPS Commerce]]↔[[Manucurist]] work split (from 06-17) — still live
- [ ] Putwall — takeaways + where FUSE fits (now agreed to build in Fuse)

### Notes
- ✍️

## 2026-10-19
_13:30–14:15 BST · Teams · weekly Fuse catch-up (recurring, optional, no formal agenda on the invite)_

### Context

**Owed by you**
- Confirm owners and dates on his Integrations Path Forward actions, or say they stand (you are named on S18 hourly ingest monitoring, and L3)
- Agree the Peak on-call route for engineering cover
- Approve his access request to the "Use-Case Readiness" artifact
- Grant his "Fuse EDI Evidence" access request from 10-01
- Answer his Transaction History question in `#real-agent-only`

**Other context**
- CT PRICAT GLN thread: he [answered on your behalf Fri](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAHMCWGPAAA%3D&exvsurl=1&viewmodel=ReadMessageItem) and offered Fuse UI help once someone has the value
- [Purdy & Figg sample payloads thread](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAHMCWGLAAA%3D&exvsurl=1&viewmodel=ReadMessageItem): Tom Dunn says Purdy will start sending sales orders by API for WS shipments
- His workshop check-in: S2 who's-who card done (fill in yours), S8 comms audit session this week, S7 moved to 8 Nov

### To raise
- [ ] CT PRICAT GLN: ILG has no trading-partner ID yet. Who owns getting it into the connector config in Fuse UI?
- [ ] Purdy & Figg API onboarding: what changes when they move WS shipments to sales orders by API?
- [ ] Workshop actions: who owns what, and by when (carried ×1)
- [ ] Dock and Bay go-live watch monitors D2, D3, D7, D8, D10 and D11 are red: does the despatch plan explain it? (carried ×1)

### Carried from last time
- [ ] [[SPS Commerce]]↔[[Manucurist]] work split (from 06-17) — still live
- [ ] Putwall — takeaways + where FUSE fits (now agreed to build in Fuse)

### Notes
- ✍️

## 2026-10-12
_13:30–14:15 BST · Teams · weekly Fuse catch-up (recurring, optional, no formal agenda on the invite)_

### Context

**Owed by you**
- Confirm owners and dates on his Integrations Path Forward workshop actions by Tue 13 Oct, or say they stand
- Approve his access request for the "Use-Case Readiness" artifact
- Grant the "Fuse EDI Evidence" access request from 10-01 (granting happens in claude.ai)

**Other context**
- He is on [Harrison Beckley's OOO 14 to 16 Oct](https://outlook.office365.com/owa/?itemid=AAkALgAAAAAAHYQDEapmEc2byACqAC%2FEWg0AAS7IEKRXT02slzmU1a62iwABx4rE3AAA&exvsurl=1&path=/calendar/item) invite
- Transaction History question on `#real-agent-only`: the haude reply is still a draft waiting on you

### To raise
- Workshop actions: who owns what, and by when
- Dock and Bay go-live watch monitors D2, D3, D7 and D8 are in Alert: does the despatch plan explain it?

### Carried from last time
- [ ] [[SPS Commerce]]↔[[Manucurist]] work split (from 06-17) — still live
- [ ] Putwall — takeaways + where FUSE fits (now agreed to build in Fuse)

### Notes
- ✍️

## 2026-10-05
_13:30–14:15 BST · Teams · weekly Fuse catch-up (recurring, no formal agenda on the invite)_

### Context

**Open asks from Jack**
- Access request for my "Fuse EDI Evidence" artifact, sent 10-01
- No further mail since
- Granting it happens in claude.ai, not by email
- [Access request email](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAHCN1rEAAA%3D&exvsurl=1&viewmodel=ReadMessageItem)

**Transaction History question (`#real-agent-only`)**
- Open since 09-24
- Asks whether reference search is live in prod
- Asks why manual-origin broadcast BM2P089199 (PURDYFIGG) shows Failed while Retry Queue search finds nothing
- He is holding the announcement until it is answered
- The haude reply is still a draft waiting on me
- [Thread](https://gfsdeliver-eng.slack.com/archives/C0C0PFXTNAF/p1790189485468989)

**Where search stands (from my todo)**
- Reference search is back in prod, on fuse-ui `ae14bc5`
- FUSE-1240 is Ready for QA
- One logged-in prod search is still to run: an order reference and a correlation ID, then check the payload download has no `correlationId`

**Earlier today**
- 11:15 Fuse Leadership Catchup with Jack and Oli → [[Meetings/Bifrost Leadership Catchup]]

### To raise
- Transaction History: answer the search-live and BM2P089199 questions in person, and agree when he can make the announcement
- "Fuse EDI Evidence": confirm which account and access level he needs, then grant it from claude.ai
- CT/Puig build-timeline steer: confirm it really is settled (he said on 09-18 he no longer needed it; on my todo, carried ×9)

### Carried from last time
- [ ] [[SPS Commerce]]↔[[Manucurist]] work split (from 06-17) — still live
- [ ] Putwall — takeaways + where FUSE fits (now agreed to build in Fuse)

### Notes
- ✍️

## 2026-09-21
_12:30–13:15 · Teams · "Optional weekly slot to catch up on anything Fuse" (recurring, no formal agenda on the invite)_

**Context**
- Earlier today: [[Meetings/Bifrost Leadership Catchup]] (10:45, w/ Oli) — same room, some overlap expected
- Sportslux escalation call (10:00) — Jack not on it, Harry/Tom Dunn/Indre attending

**Jack's active FUSE work** (assignee, not Done — capped to 3, most recently updated)
- [FUSE-1235](https://globalfreight.atlassian.net/browse/FUSE-1235) Define Fuse's Role Model — Backlog — **new to top-3**
- [FUSE-924](https://globalfreight.atlassian.net/browse/FUSE-924) [UI] Add Viewer Role — Ready for Refinement — **new to top-3**
- [FUSE-930](https://globalfreight.atlassian.net/browse/FUSE-930) External SFTP Connectivity — Backlog — **new to top-3**

**To raise**
- CT/Puig EDIFACT build-timeline steer he asked for Thu (18 Sep) — he said afterwards he didn't need it after all; worth confirming that's still true
- Dock & Bay / Fulfil ERP escalation — Alex Saunders (ilguk) asked to be kept in the loop, 29/09 go-live, Tom Dunn's SO-response-code question to Fulfil looks unanswered
- olliama's 8 unpicked-up `#real-agent-only` threads (SNAP 401s, dropped confirmations, a lost STUBBLE sales order) — worth Jack knowing given the customer-facing surface
- FUSE-1004 template feedback — still owed, longest-running item on my own todo list

**Owed by you**
- (none carried from last time)

**Carried from last time**
- [ ] [[SPS Commerce]]↔[[Manucurist]] work split (from 06-17) — still live
- [ ] Putwall — takeaways + where FUSE fits (now agreed to build in Fuse)

**Notes**
- ✍️

## 2026-09-14
_12:30–13:15 · Teams · "Optional weekly slot to catch up on anything Fuse" (recurring, no formal agenda on the invite)_

**Context**
- Jack back from OOO (was out 2026-09-01 → 2026-09-12)
- Earlier today: [[Meetings/Bifrost Leadership Catchup]] (10:15, w/ Oli) — same room, some overlap expected

**Jack's active FUSE work** (assignee, not Done — capped to 3, most recently updated)
- [FUSE-955](https://globalfreight.atlassian.net/browse/FUSE-955) Fallback Values / Mapping Defaults Reframe — Backlog — unchanged since 08-24
- [FUSE-922](https://globalfreight.atlassian.net/browse/FUSE-922) [UI] Add Ability to Upload Shipment Method via CSV — Backlog — unchanged since 08-24
- [FUSE-877](https://globalfreight.atlassian.net/browse/FUSE-877) [UI] Add Length and Truncate Functions into DSL — Ready for Refinement — **new to top-3**

**To raise**
- Purdy & Figg "Duplicate Lines" thread (ILG ticket 48482577955) — Darren asked [[Lee Simmons]] to share it with SNAP; Jack's on it too
- CT SAP biweekly-call attendance — the client asked who's dialling in from ILG since no one showed this week
- olliama's `#real-agent-only` ask (unpicked-up) — 61 Purdy & Figg Shopify confirmations failed Sunday on a mapping fault; worth Jack knowing given P&F's history
- FUSE-1004 template feedback — still owed, longest-running item on my own todo list

**Owed by you**
- (none carried from last time)

**Carried from last time**
- [ ] [[SPS Commerce]]↔[[Manucurist]] work split (from 06-17) — still live
- [ ] Putwall — takeaways + where FUSE fits (now agreed to build in Fuse)

**Notes**
- ✍️

## 2026-08-24
_13:30–14:15 · Teams · weekly Fuse catch-up (recurring, no formal agenda on the invite)_

**Context**
- Jack still has no open GitHub PRs (PM)
- Earlier today: [[Meetings/Bifrost Leadership Catchup]] (11:15, w/ Oli) — same room, some overlap expected

**Jack's active FUSE work** (assignee, not Done — capped to 3, most recently updated)
- [FUSE-1110](https://globalfreight.atlassian.net/browse/FUSE-1110) [Migration] Saira Skin — In Progress — unchanged since last 1:1
- [FUSE-955](https://globalfreight.atlassian.net/browse/FUSE-955) Fallback Values / Mapping Defaults Reframe — Backlog — **new to top-3** (was untouched for weeks, now re-surfaced)
- [FUSE-922](https://globalfreight.atlassian.net/browse/FUSE-922) [UI] Add Ability to Upload Shipment Method via CSV — Backlog — **new to top-3**

**To raise**
- His Yusen Logistics EU intro email — closing thread said no action needed, but worth confirming whether "leadership session next Tue" is on my calendar too
- FUSE-1004 template feedback — still owed, longest-running item on my own todo list
- FUSE-1079 (Byoma) and FUSE-1065 (Escentric Molecules) dropped off his top-3 most-recently-updated — worth a quick "still alive?" check
- SPS/Manucurist order-number-missing regression — still unresolved per 08-17, ask if TEST3 landed clean

**Carried from last time**
- [ ] [[SPS Commerce]]↔[[Manucurist]] work split (from 06-17) — still live
- [ ] Putwall — takeaways + where FUSE fits (now agreed to build in Fuse)

**Notes**
- ✍️

## 2026-08-17
_12:30–13:15 · Teams · weekly Fuse catch-up (recurring, "optional slot to catch up on anything Fuse", no formal agenda on the invite)_

**Context**
- Jack still has no open GitHub PRs (PM)
- Separate today: Jack's own **15:15 API Documentation - Mandatory Use Cases** session (rescheduled) — not this 1:1, see → [[Meetings/API Documentation - Mandatory Use Cases]]

**Jack's active FUSE work** (assignee, not Done — capped to 3, most recently updated)
- [FUSE-1110](https://globalfreight.atlassian.net/browse/FUSE-1110) [Migration] Saira Skin — In Progress — **new since last 1:1**, Go Live "This Week (TBC)"
- [FUSE-1079](https://globalfreight.atlassian.net/browse/FUSE-1079) [Migration] Byoma — Backlog
- [FUSE-1065](https://globalfreight.atlassian.net/browse/FUSE-1065) [Onboarding/Migration] Escentric Molecules — In Progress

**To raise**
- Purdy & Figg support incident — Jack's SOW-review interim process update (using the Phlur SOW as reference); Peter Liu agreed to keep the review with Jack's team short-term rather than handing to [[Lee Simmons]]'s team — worth confirming that's still the plan
- FUSE-1004 template feedback — still owed, check the carried-marker below before repeating it again
- SPS/Manucurist order-number-missing regression — still unresolved per last 1:1, ask Jack if TEST3 landed clean

**Carried from last time**
- [ ] [[SPS Commerce]]↔[[Manucurist]] work split (from 06-17) — still live
- [ ] Putwall — takeaways + where FUSE fits (now agreed to build in Fuse)

**Notes**
- ✍️ 

## 2026-08-10
_13:30–14:15 · Teams · weekly Fuse catch-up (recurring, no formal agenda on the invite)_

**Context**
- Jack still has no open GitHub PRs (PM)
- Sprint 14 ends today (2026-08-10) — no sign yet of a Sprint 15 kickoff

**Jack's active FUSE work** (assignee, not Done — capped to 3, most recently updated)
- [FUSE-1079](https://globalfreight.atlassian.net/browse/FUSE-1079) [Migration] Byoma — Backlog — **new since last 1:1**
- [FUSE-963](https://globalfreight.atlassian.net/browse/FUSE-963) [Onboarding] Purdy & Figg — In Progress
- [FUSE-850](https://globalfreight.atlassian.net/browse/FUSE-850) [Onboarding] Manucurist — In Progress

**To raise**
- SPS Commerce's amquick is asking to move the Manucurist connection to **production** and wants production credentials — Jack and [[Lee Simmons]] are both on the email thread, needs a joint answer on readiness
- [[Lee Simmons]] separately proposed a regroup next week to retest Shopify CSV order-upload performance — worth flagging in case it affects Jack's onboarding timelines
- FUSE-1004 template feedback — still owed, check the carried-×7 marker from last time before repeating it here
- SPS/Manucurist order-number-missing regression — still unresolved per last 1:1, ask Jack if TEST3 landed clean

**Carried from last time**
- [ ] [[SPS Commerce]]↔[[Manucurist]] work split (from 06-17) — still live
- [ ] Putwall — takeaways + where FUSE fits (now agreed to build in Fuse)

**Notes**
- ✍️ 

## 2026-07-27
_13:30–14:15 · Teams · weekly Fuse catch-up_

**Context**
- Jack still has no open GitHub PRs (PM)
- Sprint 13 is **7 days overdue** — it ended 2026-07-20 and was never closed; Sprint 14 exists but sits in `future` state
- Sprint 13 is verification-heavy for me: 4 tickets in QA/Ready-for-QA, 2 in Code Review, only Distraction Duty actively In Progress

**Jack's active FUSE work** (assignee, not Done — 20 open, 4 In Progress)
- [FUSE-1065](https://globalfreight.atlassian.net/browse/FUSE-1065) [Onboarding/Migration] Escentric Molecules — In Progress — **new since last 1:1**
- [FUSE-963](https://globalfreight.atlassian.net/browse/FUSE-963) [Onboarding] Purdy & Figg — In Progress — **moved up from Backlog**
- [FUSE-850](https://globalfreight.atlassian.net/browse/FUSE-850) [Onboarding] Manucurist — In Progress
- [FUSE-964](https://globalfreight.atlassian.net/browse/FUSE-964) [Migration] Saira Skin — **dropped In Progress → Backlog** since 07-13, worth asking why
- [FUSE-955](https://globalfreight.atlassian.net/browse/FUSE-955) Fallback Values / Mapping Defaults Reframe — Backlog
- [FUSE-979](https://globalfreight.atlassian.net/browse/FUSE-979) Spike: assess estate for fallbacks-as-constants (gates 955) — Backlog

**To raise**
- Sprint 13 close-out / Sprint 14 start — it's a PM call and it's now a week late; my own PR window is being measured against a stale sprint boundary
- Wednesday's Charlotte Tilbury / Accenture session has **no calendar invite** — Patricia asked for discussion topics, Lee has flagged it isn't in his calendar either; Jack is on both threads
- FUSE-1004 template feedback — I still owe this, carried ×7 since 07-15; either give it today or drop it explicitly
- PO Ingest Schema help ask for Tom Dunn / ILG — carried ×4, needs a yes/no on bandwidth
- Southampton Tuesday — still owe a yes/no
- SPS/Manucurist order-number-missing regression — still unresolved; Jack cc'd on Lee's TEST3 thread where a previous test picked up a different wholesale order
- Harry Humby has 5 open drafts all blocked on the same missing evidence (screenshots / dev e2e) — flagging as a coaching thread, not 5 PR comments

**Carried from last time**
- [ ] [[SPS Commerce]]↔[[Manucurist]] work split (from 06-17) — still live
- [ ] Putwall — takeaways + where FUSE fits (now agreed to build in Fuse)

**Notes**
- ✍️ 

## 2026-07-13
_12:30–13:15 · Teams · weekly Fuse catch-up_

**Context**
- Jack still has no open GitHub PRs (PM)
- Sprint 13 is active (started 07-06, ends 07-20) — "Distraction Duty" tracking ticket [FUSE-1000](https://globalfreight.atlassian.net/browse/FUSE-1000) shows steady ad-hoc load this sprint

**Jack's active FUSE work** (assignee, not Done — carried from last 1:1, re-confirm)
- [FUSE-850](https://globalfreight.atlassian.net/browse/FUSE-850) [Onboarding] Manucurist — In Progress
- [FUSE-964](https://globalfreight.atlassian.net/browse/FUSE-964) [Migration] Saira Skin — In Progress
- [FUSE-963](https://globalfreight.atlassian.net/browse/FUSE-963) [Onboarding] Purdy & Figg — Backlog
- [FUSE-955](https://globalfreight.atlassian.net/browse/FUSE-955) Fallback Values / Mapping Defaults Reframe (Epic) — Ready for Refinement
- [FUSE-979](https://globalfreight.atlassian.net/browse/FUSE-979) Spike: assess estate for fallbacks-as-constants (gates 955) — Backlog

**To raise**
- Tom Dunn's Nuzest SFTP report — all SOs landing in SNAP as "TBC" across every ship method despite clean files; Jack's cc'd, needs Fuse-side diagnosis
- SPS/Manucurist retest — Lee asked Ashley Quick to confirm the TEST2 confirmation file arrived correctly; Jack cc'd on the thread
- API Swagger vs CSV-guide mandatory-field mismatch — still open (carried ×3 in the daily todo)
- CSL putwall — who scopes it, is there a ticket/epic yet, timeline (2027 project)

**Carried from last time**
- [ ] [[SPS Commerce]]↔[[Manucurist]] work split (from 06-17) — still live
- [ ] Putwall — takeaways + where FUSE fits (now agreed to build in Fuse)

**Notes**
- ✍️ 

## 2026-07-06
_13:30–14:15 · Teams · weekly Fuse catch-up_

**Context**
- Jack has no open GitHub PRs (PM). Recent activity: updated the INC-30 postmortem (07-03) + "Jitterbit Customer Export Template" (07-04) Confluence pages
- Sprint 12 is still the only *active* sprint but its end date (2026-06-29) has passed — it hasn't been closed

**Jack's active FUSE work** (assignee, not Done — from last 1:1, re-confirm)
- [FUSE-850](https://globalfreight.atlassian.net/browse/FUSE-850) [Onboarding] Manucurist — In Progress
- [FUSE-964](https://globalfreight.atlassian.net/browse/FUSE-964) [Migration] Saira Skin — In Progress
- [FUSE-963](https://globalfreight.atlassian.net/browse/FUSE-963) [Onboarding] Purdy & Figg — Backlog
- [FUSE-955](https://globalfreight.atlassian.net/browse/FUSE-955) Fallback Values / Mapping Defaults Reframe (Epic) — Ready for Refinement
- [FUSE-979](https://globalfreight.atlassian.net/browse/FUSE-979) Spike: assess estate for fallbacks-as-constants (gates 955) — Backlog

**To raise**
- Stubble & Co / Charlotte Tilbury dedup file — [[Tom Dunn]] asked us to prep + land it; state + owner
- Jitterbit Customer Export Template — fold in the huddle's per-customer doc fields (functional/technical); I own the Confluence page
- New ILG L1 starter Steve Thompson — Fuse UI + Datadog access ([[Tom Dunn]] asked; needs sign-off)
- API Swagger vs CSV-guide mandatory-field mismatch (Darren/James) — fix before sharing with more customers
- Shopify retrieval-conditions UX → feeds [FUSE-955](https://globalfreight.atlassian.net/browse/FUSE-955) fallback reframe

**Carried from last time**
- [ ] [[SPS Commerce]]↔[[Manucurist]] work split (from 06-17) — still live
- [ ] Putwall — takeaways + where FUSE fits (now agreed to build in Fuse)

**Notes**
- ✍️ 

## 2026-06-29
_13:30–14:15 · ⚠️ no agenda on invite (normal) · sits before 14:30 [[Bifrost SteerCo]]_

**Context**

**Decided over the weekend**
- CSL Automation x ILG BM2 putwall — [[Jack Bailey]] **and** [[Lee Simmons]] both confirmed (email) to build the requirement **inside Fuse** on cost-opportunity grounds; Lee notifying his team — moves from "assess feasibility" to scope/own

**Jack's active FUSE work** (assignee, not Done)
- [FUSE-850](https://globalfreight.atlassian.net/browse/FUSE-850) [Onboarding] Manucurist — In Progress (the currency `GB`→`GBP` + SKU failures still open with [[Lee Simmons]] / Ashley)
- [FUSE-964](https://globalfreight.atlassian.net/browse/FUSE-964) [Migration] Saira Skin — In Progress
- [FUSE-963](https://globalfreight.atlassian.net/browse/FUSE-963) [Onboarding] Purdy & Figg — Backlog
- [FUSE-955](https://globalfreight.atlassian.net/browse/FUSE-955) Fallback Values — Mapping Defaults Reframe (Epic) — Ready for Refinement (NEW since last 1:1)
- [FUSE-979](https://globalfreight.atlassian.net/browse/FUSE-979) Assess the estate for fallbacks used as constants (Spike, gates FUSE-955) — Backlog (NEW)

**To raise**
- CSL putwall — agreed to build in Fuse; who scopes it, is there a ticket/epic, what's the timeline (2027 project)
- [[Manucurist]] — currency `GB`≠`GBP` + SKU mismatch; diagnosis + confirm the [[SPS Commerce]] `/to_ilg` work split
- [FUSE-955](https://globalfreight.atlassian.net/browse/FUSE-955) Fallback/Fixed Values reframe — the spike (FUSE-979) needs sizing/owner before the conversion work
- JB Project Documentation — Keith (Inovize) doc packs flagged ASAP; Jack looped me into all future chains

**Carried from last time**
- [ ] [[SPS Commerce]]↔[[Manucurist]] work split (from 06-17) — still live
- [ ] Putwall — takeaways + where FUSE fits (now agreed to build in Fuse)

**Notes**
- ✍️ 

## 2026-06-24
_11:30–12:15 · debrief of the 11:00 [[Lee Simmons]] putwall meeting (per the invite)_

**Context**
- Sits right after the 11:00 FUSE → Putwall scoping with [[Lee Simmons]] — this 1:1 is the debrief
- 🎉 FUSE-794 metadata/traceability stack shipped 06-23 (17 PRs merged)
- New P2: [FUSE-976](https://globalfreight.atlassian.net/browse/FUSE-976) [SFTP] user-creation failed (Built For Athletes) — SFTP provisioning again
- [[Jack Bailey]]'s active FUSE work (no open PRs): [[FUSE-850]] Manucurist, [[FUSE-964]] Saira Skin migration, [[FUSE-963]] Purdy & Fig

**To raise**
- Putwall — takeaways + where FUSE fits (2027 project)
- [[SPS Commerce]]↔[[Manucurist]] — `/to_ilg` subfolder still open with Ashley / [[Lee Simmons]]; confirm the split
- [[FUSE-976]] P2 SFTP provisioning failure — who picks it up

**Carried from last time**
- [ ] SPS↔Manucurist work split (from 06-17) — still live
- [x] EPERFUM SSH key — resolved 06-23

**Notes**
- ✍️ 

## 2026-06-17
_13:00–14:00 · ⚠️ no agenda on invite · likely SPS/Manucurist + EPERFUM_

**Context**
- [[Jack Bailey]]'s active FUSE work (assignee, not Done):
  - [[FUSE-850]] [↗](https://globalfreight.atlassian.net/browse/FUSE-850) [Onboarding] Manucurist — **In Progress** (ties to the [[SPS Commerce]]↔[[Manucurist]] connection [[Lee Simmons]] handed you)
  - [[FUSE-964]] [↗](https://globalfreight.atlassian.net/browse/FUSE-964) [Migration] Saira Skin — Backlog (also your 15:00 call)
  - [[FUSE-962]] [↗](https://globalfreight.atlassian.net/browse/FUSE-962) BYOK for SFTP Customers (Epic) + [[FUSE-930]] [↗](https://globalfreight.atlassian.net/browse/FUSE-930) External SFTP Connectivity (Epic) — context for the [[EPERFUM]] SSH-key thread
  - [[FUSE-963]] [↗](https://globalfreight.atlassian.net/browse/FUSE-963) [Onboarding] Purdy & Fig — Backlog
- GitHub PRs: handle not resolvable via API search — pull manually if needed.
- Related threads: Lee's [SPS–ILG–Manucurist recap](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAF9ZPYqAAA%3D&exvsurl=1&viewmodel=ReadMessageItem); [[Ankit Kansal]]'s [EPERFUM PublicKey](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAF7slBvAAA%3D&exvsurl=1&viewmodel=ReadMessageItem) ("confirm new ssh key added your side?")

**To raise**
- [[SPS Commerce]]↔[[Manucurist]] — confirm split of work picking it up from [[Lee Simmons]]
- [[EPERFUM]] SSH key — are we adding it our side; who replies to [[Ankit Kansal]]
- [[FUSE-953]] sidecar stack status (replay-service `main` CI keystone)

**Notes**
- ✍️ 
