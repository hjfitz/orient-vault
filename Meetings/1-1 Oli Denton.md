---
tags: [meeting]
series: 1-1 Oli Denton
counterpart: "[[Oli Denton]]"
title: 1-1 Oli Denton
---
# 1-1 Oli Denton


## 2026-11-05
_10:00–10:30 GMT · Epsilon House (Slack huddle) · moved to Thursdays_

### Context

**Other context**
- Lee Simmons mailed that the temporary Iconic customer is deleted from FUSE Dev and Prod; Oli's two follow-ups (a roadmap route for exceptional order re-injection, and why the master data was wrong) are still open
- [Peak volume support and escalation procedures](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAHaGM34AAA%3D&exvsurl=1&viewmodel=ReadMessageItem) from [[Ryan Ellis]] names you Fuse On Call on Sat 7 and Sun 8 Nov
- ⚠️ overlaps the 10:00 Bifrost Team Standup, and Epsilon House at 10:00 sits against Schuster's 10:30 at Regus Southampton

### To raise
- [ ] Ryan's email names me Fuse On Call for 24 hours on both 7 and 8 Nov, but yesterday's call had Fuse on-call developers at level three and me at level four: is that the plan you agreed?
- [ ] SNAP is down from 10:00 today for the emergency patch: anything you want covered at standup?
- [ ] Spectrum IT's CV thread (Ruby Calver): the candidate is named Matthew Shaw, so is it a mix-up?
- [ ] Peak on-call: who covers 7–8 Nov, the hours, and the escalation route to give Ryan Ellis (carried ×2)
- [ ] Recruitment: next step after Peter Langley's first round with [[Matt Shaw]], and whether to see Peter Russell (carried ×2)
- [ ] The prod deploy backlog and who approves: config-service is 3 approvals and 7 days behind (carried ×2)
- [ ] Snap reliability after INC-42: ILG is logging each outage and challenging Snap before Peak (carried ×1)

### Carried from last time
- [ ] (nothing recorded)

### Notes
- ✍️ 

## 2026-10-22
_10:00–10:30 BST · Epsilon House + Slack huddle · "Moving to Thursdays", no agenda. Overlaps the 10:00 Bifrost Team Standup_

### Context

**Owed by you**
- Agree the Peak on-call route with him, then answer [[Ryan Ellis]] (the small meeting with Ryan and Dennis has no invite yet)
- Answer olliama (his agent) via haude: the four asks in the 24 Sep thread are still open
- Finish your own start-of-year PDR, which goes to him
- Weigh in on [[Schuster Efigenio]]'s Snap UI Automation proposal to him
- Forward the prior support-model email to him and [[Jack Bailey]]

**Other context**
- INC-42 (Snap ilg005 and ilg001 returning 500s, P1, you were Lead) closed at 19:22 on 21 Oct with no data lost; the postmortem draft is on [Confluence](https://globalfreight.atlassian.net/wiki/spaces/Bifrost/pages/337674242)
- INC-40 and INC-41 are both closed
- Prod is AMBER: Snap API latency has been in Warn since 04:10Z, and ILG is chasing Snap on ilg001
- config-service prod is 7 days behind dev with 3 approvals pending

### To raise
- [ ] Peak on-call: who covers 7–8 Nov, the hours, and the escalation route to give Ryan Ellis (carried ×1)
- [ ] Recruitment: next step after Peter Langley's first round with [[Matt Shaw]], and whether to see Peter Russell (carried ×1)
- [ ] The prod deploy backlog and who approves: config-service is 3 approvals and 7 days behind (carried ×1)
- [ ] Snap reliability after INC-42: ILG is logging each outage and challenging Snap before Peak

### Notes
- ✍️

## 2026-10-15
_12:30–14:00 BST · 90 minutes · no location, no agenda_

### Context

**Owed by you**
- Agree the Peak on-call hours and escalation route with him, then answer [[Ryan Ellis]]
- Answer olliama (his agent) via haude; its 4 asks in the 24 Sep thread are unanswered
- Finish your own start-of-year PDR, which goes to him
- Weigh in on [[Schuster Efigenio]]'s Snap UI Automation proposal to him
- Recruitment: he has delegated vetting and interview scheduling for the Senior Software Engineer role to you

**Other context**
- Chris Lynes (SpectrumIT) has offered Peter Russell as another candidate and mentioned an Android developer
- Peter Langley's first-round interview with [[Matt Shaw]] was 14:00 yesterday
- The Purdy & Figg sale is 7–8 Nov
- Prod is GREEN this morning, with no incidents
- Prod deploy skew: shopify-app 21d, dedupe-service 16d, fapi and collector 12d behind

### To raise
- Peak on-call: who covers 7–8 Nov, the hours, and the escalation route to give Ryan Ellis
- Recruitment: next step after Peter Langley, and whether to see Peter Russell
- Who covers Distraction Duty: FUSE-1238 is still assigned to Nylah Klasson and four nightlies are red
- The prod deploy backlog, and who approves

### Notes
- ✍️

## 2026-10-08
_09:30–10:00 BST · Epsilon House + Slack huddle · no agenda beyond "Moving to Thursdays"_

### Context

**Owed by you**
- Agree the Peak on-call hours and escalation route with him, then answer [[Ryan Ellis]]
- Answer olliama (his agent) via haude; its 09-24 thread ends "one line per item is enough" and about a dozen older asks are unanswered
- Finish your own start-of-year PDR, which goes to him
- Weigh in on [[Schuster Efigenio]]'s Snap UI Automation proposal to him (carried ×8)

**Other context**
- [[Ryan Ellis]] is waiting on Peak coverage hours and the escalation route
- The Purdy & Figg sale is 7–8 Nov with about 60k orders projected
- He forwarded your "Meet: Orient" invite to more people
- Jack Bailey, Stefan Aspin and Peter Liu accepted, Thomas Lam declined
- Agentic Delivery Day is today 10:00–17:00 and he is an optional attendee with no response
- [[Darren Rielly]] is off until Mon 12 Oct, so you are the SRE contact meanwhile

### To raise
- Peak on-call: who covers 7–8 Nov, the hours, and the escalation route to give Ryan Ellis
- Is he joining Agentic Delivery Day, given it starts at 10:00
- Who the "Meet: Orient" invite was forwarded to, and why
- What being SRE contact for Darren Rielly's absence covers until 12 Oct

### Notes
- ✍️

## 2026-09-24
_13:00–13:30 UTC · Epsilon House + Slack huddle · note "Moving to Thursdays"_

### Context

**Other context**
- Prod is GREEN — no incidents, no Alert/Warn monitors; overnight was self-resolving Snap flapping (SAIRA-driven entity-creation blips, a latency episode)
- His agent (`olliama`) flagged two open SnapFulfil issues in `#real-agent-only` this week with no Fuse agent picking them up yet — PURDYFIGG (+6 others) shipment-create rejections, and intermittent entity-creation failures 18–21 Sep — worth surfacing that these are being actioned, not ignored
- Sprint 15 (started 2026-09-16) — 18 tickets in flight fleet-wide, 10 pre-merge / 8 in QA
- Deploy approval backlog: dedupe-service (7d, 11 pending) and ilg-secure-notes (8d, 6 pending) both need a click-through

### To raise
- Whether the CT/Accenture EDI timeline risk from 09-10 got resolved
- Nylah's FUSE-1187 has sat 5 days with no PR — flag as a possible handover-scope gap given her resignation is still in progress

### Notes
- ✍️

## 2026-09-10
_09:00–09:30 · Slack huddle · note "Moving to Thursdays"_

### Context

**Other context**
- [[Nylah Klasson]] resigned this morning (letter to me + HR) — Oli DM'd about the leaver / team backfill, so this is the live topic
- [[Lee Simmons]] + Accenture (Rafa) flagging the CT/Accenture **EDI dev timeline** as a delivery risk in-thread
- [[Darren Cobby]] @-mentioned me + [[Jack Bailey]] on "FUSE Migrations/Bi-Frost" asking where things are

### To raise
- Nylah's resignation — backfill plan, and how to cover her open work (observability#28, collector#89/FUSE-1058) over her notice
- The CT/Accenture EDI timeline risk — do we need to formally push back on the date

### Carried from last time
- [ ] Build a test suite for the [[Charlotte Tilbury]] EDI samples + review the extracts
- [ ] Shell scripts to push Jitterbit extracts through the Fuse CLI for verification
- [ ] Debrief [[Ryan Dennis]] on the purpose of the Slack support channel

### Notes
- ✍️ 

## 2026-08-27
_09:00–09:30 · Epsilon House / Slack huddle_

### Context

**Carried from last time**
- [ ] Build a test suite for the [[Charlotte Tilbury]] EDI samples + review the extracts
- [ ] Shell scripts to push Jitterbit extracts through the Fuse CLI for verification
- [ ] Debrief [[Ryan Dennis]] on the purpose of the Slack support channel

### Notes
- ✍️ 

## 2026-08-13
_09:00–09:30 · Epsilon House + Slack huddle · invite body just notes "Moving to Thursdays" — no agenda_

### Context

**Open PRs / Jira**
- None — still no open PRs or active Jira assigned to him, consistent with every prior occurrence (decision-maker/reviewer, not authoring)

**Owed by you**
- Skim [[Jack Bailey]]'s **Proposed Bifrost Restructure** whiteboard — still unopened, carried since 2026-07-30 (now ~2 weeks)
- Clear pending annual-leave approvals in PHR/Access — carried ×22 since 2026-07-09, the longest-running item on the list
- Confirm [[Matt Shaw]]'s holiday request actually got approved — carried since 2026-07-23

**Other context**
- FUSE-1104 (silent-loss hardening) has 3 of your own PRs (dedupe-service#118/#120/#121/#122) awaiting review, CI green — worth flagging for review bandwidth
- collector#80 (FUSE-1104 backoff) and shopify-connector#214 (FUSE-785) are both CI-red and needed judgement rather than a mechanical fix this morning — see today's digest GitHub section

### Carried from last time
- [ ] Build a test suite for the [[Charlotte Tilbury]] EDI samples + review the extracts
- [ ] Shell scripts to push Jitterbit extracts through the Fuse CLI for verification
- [ ] Debrief [[Ryan Dennis]] on the purpose of the Slack support channel

### Notes
- ✍️ 

## 2026-08-04

### Context

**Open PRs**
- None — `oliver-denton_gfsdev` has no open PRs in `gfs-bifrost`
- Consistent with every prior occurrence: he is a reviewer and decision-maker, not authoring

**Active Jira**
- None — no non-Done issue is assigned to him anywhere on the site, not just in FUSE

**Owed by you**
- Skim [[Jack Bailey]]'s **Proposed Bifrost Restructure** whiteboard — the invite is still unopened, and yesterday's digest explicitly deferred this to "tuesday pm", which is this slot
- Clear pending annual-leave approvals in PHR/Access — carried ×17 since 2026-07-09, the longest-running item on the list
- Confirm [[Matt Shaw]]'s holiday request actually got approved — carried ×7 since 2026-07-23
- Establish guardrails against dev-to-prod SFTP credential misuse — his action on you from the 07-13 huddle, now roughly three weeks carried and re-flagged at yesterday's Leadership Catchup

**Owed to you** (from the 07-13 huddle, still open)
- Reaffirm the Granola recording-without-declaring policy company-wide
- Forward the Amazon SFTP incident-management requirements
- Initiate Nya's OH/return-to-work assessment

**Other context**
- Agenda: the invite body is one line — "Chat new org?"
- That almost certainly means the Bifrost restructure / pod structure work, so the whiteboard skim above is the real prep for this call
- The pod-structure pack (structure + Jira board + runbook templates) was delivered to [[Jack Bailey]] in the office yesterday, so you have something concrete to bring
- Pete wanted that pack live by Monday, which has now passed — worth confirming with Oli that it landed where Pete expected
- ⚠️ No location or dial-in is set on a 90-minute slot — decide whether this is Epsilon House in person, Teams, or a Slack huddle, and put it on the invite
- ⚠️ Oli has not responded to the invite, and he also missed responding to the Bifrost Leadership Catchup invite on its last three occurrences — a nudge is reasonable
- You organised this one, so the 90 minutes are yours to shape; it is triple the usual 30-minute slot
- You are on approved annual leave tomorrow, 5 Aug — flag anything that needs a decision before you go
- [[Jack Bailey]] is OOO 3–10 Aug with you named as the Fuse escalation contact, so cover is a live topic, and any product decision parked on Jack is parked until next week
- [[Schuster Efigenio]]'s 6-Month Probation Review Meeting Form is still not completed or sent — carried ×7 since 2026-07-23, and [[Laura Bockling]]'s HR chase is well past due

### Carried from last time
- [ ] Build a test suite for the [[Charlotte Tilbury]] EDI samples + review the extracts
- [ ] Shell scripts to push Jitterbit extracts through the Fuse CLI for verification
- [ ] Debrief [[Ryan Dennis]] on the purpose of the Slack support channel

### Notes
- ✍️ 

## 2026-07-30
_10:00–10:30 · Epsilon House + Slack huddle · invite body only says "Moving to Thursdays" — no agenda_

### Context

**Open PRs / Jira**
- Nothing open assigned (decision-maker / reviewer, not authoring)

**To raise**
- His [Future of Capitalisation email](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAGYfh9wAAA%3D&exvsurl=1&viewmodel=ReadMessageItem) — new ongoing capitalisation-report habits expected of leads; confirm what changes for Bifrost
- [[Jack Bailey]]'s **Proposed Bifrost Restructure** whiteboard (shared via Confluence yesterday) — skim before this slot; natural topic with Oli
- Samuel Pryce interview is **today 14:00** (Oli organizer, with [[John Clarke]]) — align on interview angles; Oli's own note says "probably a little thin on the technical skills for a mid level"
- [[Schuster Efigenio]]'s probation review is **overdue** (HR high-importance chase, end date passed) — being closed out at the 10:30 1:1 right after this

**Other context**
- ⚠️ **Slot likely moved**: Oli DM'd yesterday evening — his 10:00 got "Pete'd over"; he's WFH with the lergy and wants another slot today to discuss "new plans". You offered "even lunch" — **nothing booked yet**, book it this morning
- No agenda on the invite (normal for this 1:1; series just moved to Thursdays)

### Carried from last time
- [ ] Build a test suite for the [[Charlotte Tilbury]] EDI samples + review the extracts
- [ ] Shell scripts to push Jitterbit extracts through the Fuse CLI for verification
- [ ] Debrief [[Ryan Dennis]] on the purpose of the Slack support channel

### Notes
- ✍️ 

## 2026-07-14
_12:45–13:15 · Teams · no agenda on invite (normal)_

### Context

**Open PRs / Jira**
- Nothing open assigned (decision-maker / reviewer, not authoring)

**Owed by you (carried from 15/06 huddle, still open — now a month unresolved)**
- Build a test suite for the [[Charlotte Tilbury]] EDI samples + review the extracts
- Write shell scripts to push Jitterbit extracts through the Fuse CLI for verification
- Debrief [[Ryan Dennis]] on the purpose of the Slack support channel

**From yesterday's huddle (2026-07-13, 11:06 group DM w/ Jack Bailey)**
- Harry action: establish guardrails against dev-to-prod SFTP credential misuse (staff bypassing audit trails with prod creds) — report progress
- Oli owes: reaffirm the Granola recording-without-declaring policy company-wide
- Oli owes: meet Alex P to clarify QA/dev/onboarding deployment
- Oli owes: forward the Amazon SFTP incident-management requirements to Harry
- Oli owes: divvy work packages this week with team leads
- Oli owes: initiate Nya's OH/return-to-work assessment if no response by next week
- **Project Northstar** — board-approved global platform expansion, up to $100M budget; 3-week US-opco assessment starting; scope could pull in WMS/OMS/Fuse
- Charlotte Tilbury scope drift flagged by Simon Clifford; reorg by workstream; final discovery session planned pre-design

**To raise**
- Data-extraction / CT SAP migration — still live; check in on the still-owed CT EDI test-suite work

### Carried from last time
- [ ] Build a test suite for the [[Charlotte Tilbury]] EDI samples + review the extracts
- [ ] Shell scripts to push Jitterbit extracts through the Fuse CLI for verification
- [ ] Debrief [[Ryan Dennis]] on the purpose of the Slack support channel

### Notes
- ✍️ 

## 2026-07-09
_11:30–12:00 · Teams ("Hot girl walk" — informal chinwag + steps) · no agenda_

### Context

**Open PRs / Jira**
- Nothing open assigned (decision-maker / reviewer, not authoring)

**Owed by you (carried from 15/06 huddle, still open)**
- Build a test suite for the [[Charlotte Tilbury]] EDI samples + review the extracts
- Write shell scripts to push Jitterbit extracts through the Fuse CLI for verification
- Debrief [[Ryan Dennis]] on the purpose of the Slack support channel

**To raise**
- ⚠️ 11:30 double-books my [[Harry Humby]] 1:1 — decide which moves
- Data-extraction / CT SAP migration is live this week ([[Lee Simmons]]/[[Keith Rigg]] 1pm calls, I gave the priority stack-rank) — flag progress + the still-owed CT EDI test-suite work

### Carried from last time
- [ ] Build a test suite for the [[Charlotte Tilbury]] EDI samples + review the extracts
- [ ] Shell scripts to push Jitterbit extracts through the Fuse CLI for verification
- [ ] Debrief [[Ryan Dennis]] on the purpose of the Slack support channel

### Notes
- ✍️ 

## 2026-06-30

### Context

**Open PRs / Jira**
- Nothing open assigned (he's a decision-maker / reviewer, not authoring)

**Owed by you (still open from the 15/06 huddle)**
- Build a test suite for the [[Charlotte Tilbury]] EDI samples + review the extracts
- Write shell scripts to push Jitterbit extracts through the Fuse CLI for verification
- Debrief [[Ryan Dennis]] on the purpose of the Slack support channel

**Other context**
- 29 Jun evening prod flap — SNAP/BM2 inovize-503 outage hit STUBBLE + EPARFUM SOs; I tracked + closed it in the Oli/Jack group DM ("snap is happy" 19:55, redeploy 20:14). Worth a one-line "drained, root cause = upstream 503s" close-out
- FUSE-984 Snap SO-create idempotency surfaced again (Alex Topea: SO-26839 imported twice) — Kaizen ticket already raised
- Today 16:00 EDIFACT INSDES + OSTRPT session w/ Accenture continues the CT EDI work he sponsored
- No agenda on the invite (normal for a 1:1)

### Carried from last time
- [ ] Build a test suite for the [[Charlotte Tilbury]] EDI samples + review the extracts
- [ ] Shell scripts to push Jitterbit extracts through the Fuse CLI for verification
- [ ] Debrief [[Ryan Dennis]] on the purpose of the Slack support channel

### Notes
- ✍️ 

## 2026-06-18

### Context

**Open PRs / Jira**
- Nothing open assigned (he's a decision-maker / reviewer, not authoring this sprint)

**Owed by you (from the 15/06 huddle)**
- Build a test suite for the [[Charlotte Tilbury]] EDI samples + review the extracts
- Write shell scripts to push Jitterbit extracts through the Fuse CLI for verification
- Debrief [[Ryan Dennis]] on the purpose of the Slack support channel

**Other context (15/06 huddle topics)**
- Agentic-tooling cost sign-off (~£30/mo per power user, premium approved)
- Sprint 12 chunk scheduling
- Cyruskin first Shopify migration
- Return-goods (plumbing done, Snap wiring remains)
- No agenda on the invite (normal for a 1:1)

### Notes
- ✍️ 
