---
tags: [meeting]
series: Bifrost SteerCo
title: Bifrost SteerCo
---
# Bifrost SteerCo

## 2026-08-03
_13:30–14:00 · organizer Steve Greenwood · Teams · GFS + ILG steering committee_

### Context

**Attendees**
- GFS/Bifrost: Steve Greenwood, [[Jack Bailey]] (listed, but **OOO through 8 Aug** — no decline found for this specific event, unconfirmed whether he'll join), Harry
- ILG: [[Lee Simmons]], others per standing list

**Agenda (from invite)** — truncated in event body, same numbered items as recent occurrences (Pilot Migration & Process Refinement / Customer Value / Discovery & Configuration Auditing / Strategic Roadmap / Operational Readiness / Standardised Integration Framework)

**Live context to land**
- Item 5 (Operational Readiness) — prod is clean today: no incidents, no Alert/Warn monitors, 100% Fuse API availability. Worth flagging the new fleet-wide secops-dep-node checkout regression (see [[Meetings/Bifrost Leadership Catchup]] today) if platform reliability comes up — it's CI-side, not prod-facing, but it's fresh and cross-repo.
- Deploy skew: normal backlog only, nothing past the 7-day alert threshold this week.
- Jack's absence may leave items 1/3 (his usual items) without a GFS-side owner in the room — worth flagging if they come up.

### Carried from last time
- [ ] [[Keith Rigg]] extraction-project doc review — still open
- [ ] [[Fulfil]] webhook questions owed to [[Lee Simmons]]

### Notes
- ✍️ 

## 2026-07-27
_14:30–15:00 · organizer Steve Greenwood · Teams · GFS + ILG steering committee_

### Context

**Attendees**
- GFS/Bifrost: Steve Greenwood, Tom Ashley, Peter Liu, [[Jack Bailey]] (VIP), Harry (optional, accepted)
- ILG: [[Lee Simmons]] (VIP), Sam Taylor-Rowlinson, [[Ryan Ellis]], Darren Cobby, Simon Clifford, Glenn Woodhams

**Agenda (from invite — same 6 items as 07-20)**
1. Pilot Migration & Process Refinement — [[Lee Simmons]]
2. Customer Value and Transition Engagement Plan — Sam
3. Discovery and Configuration Auditing — [[Lee Simmons]]
4. Strategic Roadmap and Commercial Exposure Assessment — Darren
5. Ensure Operational Readiness of Integrations and Support functions — [[Ryan Ellis]]
6. Standardised Integration & Partner Framework (Non-Native Migration) — Pete

**Shape**
- 30 minutes for 6 items — expect it to overrun or skim
- I'm optional, so this is a listen-in unless items 1, 3 or 5 need Fuse input

**Live context to land**
- Item 3 (Discovery and Configuration Auditing) is the hook for [[Keith Rigg]]'s extraction project — updated docs for **all 9 test customers** are uploaded and waiting on my review feedback, and [[Lee Simmons]] committed to reviewing over the weekend or today, so my half is the open one
- Item 1 (Pilot Migration) — [[Lee Simmons]] processed SPS TEST3 and asked SPS to confirm the file carries the right shipment, noting a previous test picked up a **different wholesale order**; that's a Fuse-side selection question likely landing on me
- Item 5 (Operational Readiness) — two things I can speak to factually: prod is clean (no incidents, 100% API availability, failures down 91%), but Fuse UI served **100% 5xx for 39 minutes** unacknowledged on Saturday, and fuse-ui + shopify-app are both 7 days behind on prod deploys at the approval gate
- Dock & Bay / [[Fulfil]]: SKU now visible in SNAP under DOCKBAY and credentials confirmed working; I **missed Friday's Fulfil call**, so I owe myself a catch-up on what was agreed before speaking to it
- Wednesday's Charlotte Tilbury / Accenture session has **no invite out** — Patricia has asked for discussion topics and [[Lee Simmons]] has said it isn't in his calendar; a good thing to settle in the room since both are here
- [[Lee Simmons]]'s annual leave, fresh off his signature: 6 Aug, 17–21 Aug, 14–28 Sep

### Carried from last time
- [ ] [[Keith Rigg]] extraction-project doc review — now chased twice, docs complete for all 9 customers
- [ ] [[Fulfil]] webhook questions owed to [[Lee Simmons]]

### Notes
- ✍️ 

## 2026-07-20
_13:30–14:00 · organizer Steve Greenwood · Teams · GFS + ILG steering committee_

### Context

**Attendees**
- GFS/Bifrost: Steve Greenwood, Tom Ashley (gfsdeliver, no response), Peter Liu, [[Jack Bailey]] (VIP), Harry (optional)
- ILG: Tom Ashley (ilguk, optional), [[Lee Simmons]] (VIP), Sam Taylor-Rowlinson, Ryan Ellis, Darren Cobby, Simon Clifford, Glenn Woodhams

**Agenda (from invite — full, 6 items this time)**
1. Pilot Migration & Process Refinement — [[Lee Simmons]]
2. Customer Value and Transition Engagement Plan — Sam
3. Discovery and Configuration Auditing — [[Lee Simmons]]
4. Strategic Roadmap and Commercial Exposure Assessment — Darren
5. Ensure Operational Readiness of Integrations and Support functions — Ryan
6. Standardised Integration & Partner Framework (Non-Native Migration) — Pete

**Gotcha**: invite body's forwarded header text still says "14:30–15:00 8 June 2026" (stale copy-forward) — trust the structured 13:30–14:00 today, same pattern flagged last time.

**Live context to land**
- [[Lee Simmons]] still owed by me: [[Fulfil]] webhook questions (Dhairya chasing again), [[Keith Rigg]]'s extraction-project review (second chase sent 07-17), [[Ashley Quick]]'s confirmation-CSV field-order mismatch — item 3 (Discovery and Configuration Auditing) is the natural hook for the Keith Rigg doc-review thread
- [[Jack Bailey]] on this invite too — his PO Ingest Schema ask (Fri, re: Thomas Dunn/ILG) could surface under item 5 (integrations/support readiness)
- [[Tom Dunn]]'s new custom-outbound-mapping/Scribe ask (Fri) — GADG/Zedonk goods-out CSV config won't save — may be worth a mention under item 6 if it turns into a pattern issue

### Carried from last time
- (none unchecked from 2026-07-13)

### Notes
- ✍️ 

## 2026-07-13
_13:30–14:00 · organizer Steve Greenwood · Teams · GFS + ILG steering committee_

### Context

**Attendees**
- GFS/Bifrost: Steve Greenwood, Peter Liu, [[Jack Bailey]], Harry
- ILG: Tom Ashley (CEO), [[Lee Simmons]], Sam Taylor, Ryan E, Darren C, Tom (ilguk), Simon Clifford, Glenn W

**Agenda (from invite — stale recurring text, dated 8 Jun)**
- Pilot Migration & Process Refinement ([[Lee Simmons]])
- Customer Value and Transition Engagement Plan

**Live context to land**
- SPS/Manucurist retest — Lee asked Ashley Quick (SPS) to confirm the TEST2 confirmation file landed correctly; still awaiting her reply
- Extraction project — [[Keith Rigg]] (Inovize) uploaded updated docs for 9 customers to the shared OneDrive; Lee's review still outstanding
- Fulfil.IO (Dock & Bay) ERP integration — vendor ticket #87630 explicitly asking to "keep us posted on the fix"
- Tom Ashley personally praised the duplicate-shipments PIR (07-11 email) — worth a nod if it comes up

### Carried from last time
- (none unchecked from 2026-07-06)

### Notes
- ✍️ 

## 2026-07-06
_14:30–15:00 · organizer Steve Greenwood · Teams · GFS + ILG steering committee_

### Context

**Agenda (from invite)**
- Pilot Migration & Process Refinement ([[Lee Simmons]])
- Customer Value & Transition Engagement Plan

**Live context to land**
- [[Lee Simmons]] circulated the FUSE Migration swim-lane (happy-path) diagram; Keith wants explicit ILG sign-off before disabling DEV agents — fits the migration-refinement item
- Pilot docs: Lee asked the group to review functional + technical docs for the 9 pilot clients and feed back to Keith; [[Jack Bailey]] posted an exec summary
- [[Manucurist]] pilot still surfacing (currency `GB`≠`GBP` + SKU) — likely under Lee's pilot-migration item
- Fulfil.IO (Dock & Bay) ERP integration — vendor checking in on status (To: Lee + me)

### Carried from last time
- (none unchecked from 2026-06-29)

### Notes
- ✍️ 

## 2026-06-29
_14:30–15:00 · organizer Steve Greenwood · Teams · GFS + ILG steering committee_

### Context

**Attendees**
- GFS/Bifrost: Steve Greenwood, Tom Ashley, Peter Liu, [[Jack Bailey]]
- ILG: [[Lee Simmons]], Sam Taylor, Ryan E, Darren C, Tom, Simon Clifford

**Agenda (from invite)**
- Pilot Migration & Process Refinement ([[Lee Simmons]])
- Customer Value & Transition Engagement Plan

**Live context to land**
- [[Manucurist]] pilot orders failing (currency `GB`≠`GBP` + SKU mismatch) — likely surfaces under Lee's pilot-migration item; have the Fuse-side diagnosis ready
- CSL putwall — agreed (Lee + [[Jack Bailey]]) to build inside Fuse; transition/engagement angle
- Fulfil ERP (Dock & Bay) integration in flight with [[Lee Simmons]]

### Carried from last time
- (none — first tracked occurrence)

### Notes
- ✍️ 
