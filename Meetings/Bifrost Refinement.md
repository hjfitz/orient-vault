---
tags: [meeting]
series: Bifrost Refinement
title: Bifrost Refinement
---
# Bifrost Refinement

## 2026-10-08
_13:00–13:30 BST · no location, no Teams link · no agenda_

### Context

**Active Jira**
- [FUSE-1273](https://globalfreight.atlassian.net/browse/FUSE-1273) [Snap] [Sev 3] Attribute per-batch expiry and production date on goods-in confirmation lines (Ready for Refinement, assigned to [[Schuster Efigenio]] in Jira although the digest listed it unassigned)
- [FUSE-1274](https://globalfreight.atlassian.net/browse/FUSE-1274) [Snap] [Sev 3] Split goods-in confirmation lines by stock status on a single PO line (Ready for Refinement, unassigned)
- [FUSE-1276](https://globalfreight.atlassian.net/browse/FUSE-1276) [Snap] [Sev 3] Populate Description on returns confirmations from the product record (Ready for Refinement, unassigned)
- [FUSE-1202](https://globalfreight.atlassian.net/browse/FUSE-1202) [Egress] Publish confirmation_data_failure for stock sync failures (Ready for Development, unassigned)
- [FUSE-1203](https://globalfreight.atlassian.net/browse/FUSE-1203) [Collector] Mark stock sync runs failed (Ready for Development, unassigned)
- [FUSE-1204](https://globalfreight.atlassian.net/browse/FUSE-1204) [Replay] Hold and redrive stock sync failures (Ready for Development, unassigned)
- [FUSE-1205](https://globalfreight.atlassian.net/browse/FUSE-1205) [UI] Surface stock sync runs in Transaction History (Ready for Development, unassigned)
- [FUSE-1209](https://globalfreight.atlassian.net/browse/FUSE-1209) [Egress] Handle single-SKU stock sync redrive as a synchronous set (Ready for Development, unassigned)
- [FUSE-1292](https://globalfreight.atlassian.net/browse/FUSE-1292) [Snap] Spike: load-test how Snap responds to Shopify stock sync (Backlog, unassigned)
- [FUSE-1035](https://globalfreight.atlassian.net/browse/FUSE-1035) [API] Serve customer GET /stock by proxying to the WMS gateway (Ready for Refinement, unassigned)

**Owed by you**
- Order FUSE-1273, FUSE-1274 and FUSE-1276 (carried ×8, due at the 10:00 Standup)
- Place the unassigned stock-sync tickets, FUSE-1292 and FUSE-1035 while Sprint 15 is still active
- Sort out the Agentic Delivery Day clashes with the Standup and this meeting

**Other context**
- ⚠️ Double-booked with Agentic Delivery Day (you organise, 10:00–17:00, Epsilon House Boardroom)
- ⚠️ No agenda, no location, no Teams link
- Snap maintenance 15:00–16:30 may slow Snap-facing checks this afternoon

### To raise
- Which of the Standup and this meeting moves or shortens around Agentic Delivery Day
- Owners for FUSE-1202, FUSE-1203, FUSE-1204, FUSE-1205 and FUSE-1209
- Who takes FUSE-1292 and FUSE-1035
- Order for FUSE-1273, FUSE-1274 and FUSE-1276 if it was not settled at the Standup

### Notes
- ✍️

## 2026-07-23
_09:00–10:30 UTC · Epsilon House Boardroom + Southampton Boardroom (Teams) · organiser Harry · no agenda on invite_

### Context

**Attendees**
- [[Matt Shaw]], [[Harry Humby]], [[Schuster Efigenio]]

**Other context**
- ⚠️ Double-books the 1:1 w/ [[Schuster Efigenio]] (09:30–10:00) — sort which one moves.
- Carried from standup: SKU-blacklisting ownership confusion, deferred here by [[Jack Bailey]] (07-22).
- Sprint 13 ended 07-20 and is still open in Jira 3 days later — this session is likely Sprint 14 intake / close-out.
- Fleet DevSecOps trip continues: 2 new HIGH `fast-uri` advisories (transitive via `ajv > fast-uri`) failing `dependency_audit`/`image_scan` across 8 repos overnight — allowlist sweep still outstanding.
- Harry is on 0.5-day leave this afternoon and tomorrow afternoon (approved by [[Oli Denton]]) — worth flagging end time if it affects handoffs.

### Carried from last time
- (none carried — 07-21 items were informational, not action items)

### Notes
- ✍️ 

## 2026-07-21
_12:00–13:30 · Southampton Boardroom + Epsilon House Boardroom · organiser Harry · no agenda on invite_

### Context

**Attendees**
- [[Matt Shaw]], [[Harry Humby]], [[Schuster Efigenio]] (accepted), Oliver Wilders (optional, accepted)

**Other context**
- Sprint 13 ended yesterday (2026-07-20) — still showing `active` in Jira (not yet closed out), so this session is likely Sprint 14 intake. The "Ready for Refinement" backlog is large — 20+ tickets, oldest going back to FUSE-633/635/642 (Work Order use-cases). Worth triaging down to a shortlist rather than working the whole queue live.
- The fleet-wide DevSecOps trip from last night (axios CVE family + a shared container base-image Trivy CVE, 13 repos) is today's operational headline — may be worth a mention if it isn't already ticketed, since it's the kind of cross-cutting item that tends to eat sprint capacity unplanned.
- [[Schuster Efigenio]]'s probation Final Review (ends 26/07, 5 days out) still isn't booked — HR chased directly again this morning.

### Carried from last time
- (none carried — last occurrence's items were informational, not action items)

### Notes
- ✍️ 

## 2026-07-14
_10:00–11:00 · Epsilon House Boardroom + Southampton Boardroom · organiser Harry · no agenda on invite_

### Context

**Attendees**
- [[Harry Humby]], [[Schuster Efigenio]], [[Matt Shaw]]

**Tickets currently in "Ready for Refinement"** (candidates for today)
- [FUSE-999](https://globalfreight.atlassian.net/browse/FUSE-999) — [Observability] Instrument fuse.* operational metrics across Fuse services (agentic umbrella)
- [FUSE-998](https://globalfreight.atlassian.net/browse/FUSE-998) — [SFTP] Route RGA confirmation egress to the confirmation mapping, not the ingress mapping
- [FUSE-995](https://globalfreight.atlassian.net/browse/FUSE-995) — [Observability] Adopt canonical structured-logging field spec across Fuse services
- [FUSE-992](https://globalfreight.atlassian.net/browse/FUSE-992) — [Snap] Propagate ingest capture onto create_acknowledge and create_data_failure

**Other context**
- Sprint 13 (Distraction Duty) is tracking steady ad-hoc load this sprint — worth a temperature check on capacity for new refinement intake
- fapi's `Code Quality` nightly went red overnight (`Matrix (test)` — pre-existing master breakage from a merge-order conflict between #77/#79, now fixed via fapi#81)
- secops `DevSecOps Scans` gitleaks failure is on its 5th consecutive night unresolved — may be worth a refinement slot if it isn't already ticketed

### Carried from last time
- (none — first tracked occurrence)

### Notes
- ✍️ 
