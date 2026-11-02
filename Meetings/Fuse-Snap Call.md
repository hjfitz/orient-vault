---
tags: [meeting]
series: Fuse-Snap Call
title: Fuse-Snap Call
---
# Fuse-Snap Call

## 2026-10-14
_11:30–12:00 BST · Teams · organiser [[Ryan Ellis]] (ILG IT Ops Manager) · w/ Jake Smith (Snap technical team leader), Chloe Warren-Ross (Snap), [[Lee Simmons]], [[Peter Liu]] · ⚠️ no formal agenda, Snap attendees are external_

### Context

**Topics from the thread**
- Peak readiness, scaling requirements and forecast order volumes for Purdy & Figg (sale 7–8 Nov, about 60k orders)
- Snap says Fuse's connection to Snap looks fine; Ryan set the call up after your 10-05 DB5 / Stock Sync load note
- Snap throughput ahead of stock sync: your earlier reply raised about a 10h backlog into Snap at 2M records a day in testing

**Other context**
- Stock sync runs are being built (FUSE-1203 and the other stock-sync tickets) and the Fuse snap-api simulator is the relevant test background
- Snap entity creation has been failing for Purdy & Figg and SAIRA sales orders (FUSE-1311), so expect timeouts to come up

### To raise
- Does Snap still see timeouts after its own changes?
- What does Snap need from Fuse before the 7–8 Nov peak, and who on the Snap side is on call?

### Notes
- ✍️
