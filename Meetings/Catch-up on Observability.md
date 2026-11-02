---
tags: [meeting]
series: Catch-up on Observability
---
# Catch-up on Observability

## 2026-09-29
_12:30–13:00 BST · Teams / Epsilon House Boardroom · organiser: you · [event](https://outlook.office365.com/owa/?itemid=AAkALgAAAAAAHYQDEapmEc2byACqAC%2FEWg0AAS7IEKRXT02slzmU1a62iwABrmG76AAA&exvsurl=1&path=/calendar/item)_

### Context

**Attendees**
- Sean De Fraine (accepted)
- [[Matt Shaw]] (accepted)
- [[Oli Denton]] (not responded)
- John Clarke (not responded)

**Other context**
- ⚠️ Clashes with the Manager Briefing (12:00–13:00 BST). You haven't responded to the briefing, and its invite asks you to pick one of several sessions
- Agenda (yours): follow-up to Matt's talk, where observability is heading (SigNoz), who owns a provider decision and on what criteria, and what the dev teams actually use
- [[Darren Cobby]] asked for a Datadog training session and a "one monitoring platform" session with Ryan, James and Denis — [email](https://outlook.office365.com/owa/?ItemID=AAMkADVhYjUxODIyLWM5NTktNGJmOC1hN2FjLWFjMjllNWUzYmY4MwBGAAAAAAAEXHdKGOMeRLfpaU7ff8ChBwABLsgQpFdPTayXOZTVrraLAAAAAAEMAAABLsgQpFdPTayXOZTVrraLAAHBMDI3AAA%3D&exvsurl=1&viewmodel=ReadMessageItem)
- [[Jack Bailey]]'s fortnightly update lists "supportability before peak" as a top risk
- Live examples of monitor ownership gaps: the 9 Dock & Bay watch monitors have no recipients, and Shopify confirmation delivery (303425509) flapped about 73× in 24h unacknowledged
- `dedupe_service.event.handled` returned no data over the last 48h, so the "records ingested" headline metric may have stopped being emitted

### To raise
- What criteria would settle the SigNoz question, and who owns that call?
- Fold in Darren's Datadog-training ask. Is it this group's job, or Support's?

### Carried from last time
- [ ] What decision criteria would settle the Signoz question, and who owns it — never answered in the first occurrence

### Notes
- ✍️

## 2026-09-22
_11:30–12:00 · location not captured this run_

### Context

**Attendees**
- [[Oli Denton]], John Clarke, Sean Defraine, [[Matt Shaw]]

**Other context**
- Agenda unchanged from the first occurrence: follow-up from Matt's talk, revisiting Signoz as an observability platform option
- No linked doc found; no related email thread surfaced this window either
- Worth having in mind going in: this week's Datadog flapping-monitor findings (the `[FUSE][Platform] Elevated production error rate` monitor cycling 8x overnight, unretuned since at least 18 Sep) and the MongoDB Atlas Query Targeting alert on collector-prod (likely already fixed by collector#98, pending verification) — both are live observability-tooling gaps this conversation might touch

### To raise
- Same open question as last time, still unresolved: what decision criteria would actually settle the Signoz question, and who owns making that call
- The recurring, never-retuned `Elevated production error rate` monitor is a concrete example of the "capabilities used across dev teams" gap — a monitor nobody owns enough to fix

### Carried from last time
- [ ] What decision criteria would settle the Signoz question, and who owns it — never answered in the first occurrence

### Notes
- ✍️ 

## 2026-09-08
_11:30–12:00 · Epsilon House Boardroom_

### Context

**Attendees**
- Sean De Fraine & Matt Shaw accepted
- [[Oli Denton]] and John Clarke have not responded

**Other context**
- Agenda: follow-up on Matt Shaw's talk — where observability is headed, revisiting Signoz (floated then stalled), who owns the decision/criteria, capturing what capabilities are actually used across dev teams
- No linked doc found; ties to a prior Signoz discussion with no thread surfaced in the last 3 days
- First tracked note for this series — no prior occurrence to carry from

### To raise
- What decision criteria would actually settle the Signoz question, and who owns making that call
- Matt Shaw's FUSE-999 work (fuse.* metric instrumentation) is the concrete thing already shipping — worth anchoring the "capabilities used across dev teams" discussion to what's real today rather than staying abstract

### Carried from last time
- (none — first occurrence)

### Notes
- ✍️ 
