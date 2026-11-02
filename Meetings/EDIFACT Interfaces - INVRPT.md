---
tags: [meeting]
series: ILG — EDIFACT Interfaces (INVRPT)
title: ILG — EDIFACT Interfaces (INVRPT)
---
# ILG — EDIFACT Interfaces (INVRPT)

## 2026-07-13
_15:00–16:00 · MS Teams · Accenture-led_

### Context

**Attendees**
- Accenture — R. Peñuela Tristán (organizer), P. Navarro Vaquero, Miguel F. Fernández
- ILG — [[Lee Simmons]], Sam Taylor
- Puig — Manel Sibils, David Baños, Neus Bock
- Charlotte Tilbury — Sham Ahmad, Karolina Semeniuk, Beatrice Pauryte, Kushaal Dudhia
- GFS/Bifrost — [[Jack Bailey]], Harry

**Agenda (from invite)** — "setting up this slot to comment on the 3PL integration messages... feel free to distribute to any team member that should be present"
- Wider attendee list than the 07-01 session (now includes Puig and Charlotte Tilbury directly) — reads as the messages moving from an ILG-internal discussion to a live cross-customer EDI review
- Ties into the Charlotte Tilbury EDI work: `@gfs-bifrost/edi` is largely built config-driven per business via the `EDI_PROFILE` fragment; ORDERS is parked; gap analysis lives at Confluence 215678985

### Carried from last time
- [ ] INVRPT direction (inbound stock levels vs outbound report) + exact mapping still needs clarifying — candidate for a new `@gfs-bifrost/edi` handler or the Get Stock API surface ([FUSE-792](https://globalfreight.atlassian.net/browse/FUSE-792))

### Notes
- ✍️ 

## 2026-07-01
_16:00–17:00 · MS Teams · Accenture-led_

### Context

**Attendees**
- Accenture — Rafael Peñuela Tristán (organizer)
- ILG — Harry, [[Jack Bailey]]

**What INVRPT maps to in Fuse**
- **INVRPT** (Inventory Report) → stock/inventory reporting — **not** covered by a built-in `@gfs-bifrost/edi` handler yet; clarify direction (inbound stock levels vs outbound report) + exact mapping before committing (candidate for a new handler or the Get Stock API surface, [FUSE-792](https://globalfreight.atlassian.net/browse/FUSE-792))
- Config-driven per business via the `EDI_PROFILE` fragment (envelope, charset, qualifier maps); mapping shape stays canonical and in code
- Companion to the DESADV/RECADV, PRICAT + INSDES/OSTRPT sessions — see [[EDIFACT Interfaces - DESADV RECADV]], [[EDIFACT Interfaces - PRICAT]], [[EDIFACT Interfaces - INSDES OSTRPT]]

**Reference**
- Gap analysis / EDIFACT field-coverage — Confluence 215678985
- [open event](https://outlook.office365.com/owa/?itemid=AAkALgAAAAAAHYQDEapmEc2byACqAC%2FEWg0AAS7IEKRXT02slzmU1a62iwABe7KF9QAA&exvsurl=1&path=/calendar/item)

### Notes
- ✍️ 
