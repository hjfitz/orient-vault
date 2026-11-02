---
tags: [meeting]
series: ILG — EDIFACT Interfaces (DESADV / RECADV)
title: ILG — EDIFACT Interfaces (DESADV / RECADV)
---
# ILG — EDIFACT Interfaces (DESADV / RECADV)

## 2026-06-24
_16:00–17:30 · MS Teams · Accenture-led_

### Context

**Attendees**
- Accenture — Rafael Peñuela Tristán (organizer)
- ILG — Harry, [[Jack Bailey]]

**What DESADV / RECADV map to in Fuse**
- **DESADV** (Despatch Advice) → outbound shipment / goods-out confirmation
- **RECADV** (Receiving Advice) → inbound goods-in / receiving confirmation
- `@gfs-bifrost/edi` already ships **outbound handlers for goods-in / goods-out confirmation** — these are the canonical shapes DESADV/RECADV serialise from
- Config-driven per business via the `EDI_PROFILE` fragment (envelope, charset, qualifier maps); the mapping shape stays canonical and in code
- Companion to yesterday's PRICAT (master_data) session — see [[EDIFACT Interfaces - PRICAT]]

**Reference**
- Gap analysis / EDIFACT field-coverage — Confluence 215678985
- [open event](https://outlook.office365.com/owa/?itemid=AAkALgAAAAAAHYQDEapmEc2byACqAC%2FEWg0AAS7IEKRXT02slzmU1a62iwABe7KF2gAA&exvsurl=1&path=/calendar/item)

### Notes
- ✍️ 
