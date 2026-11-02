---
tags: [meeting]
series: ILG — EDIFACT Interfaces (INSDES / OSTRPT)
title: ILG — EDIFACT Interfaces (INSDES / OSTRPT)
---
# ILG — EDIFACT Interfaces (INSDES / OSTRPT)

## 2026-06-30
_16:00–17:30 · MS Teams · Accenture-led_

### Context

**Attendees**
- Accenture — Rafael Peñuela Tristán (organizer)
- ILG — Harry, [[Jack Bailey]]
- Wider invite — Puig / [[Charlotte Tilbury]] / Accenture

**What INSDES / OSTRPT map to in Fuse**
- **INSDES** (Despatch Instruction) → inbound **sales_order** — `@gfs-bifrost/edi` already ships a built-in INSDES → sales_order inbound handler
- **OSTRPT** (Order Status Report) → order/stock status reporting — **not** covered by a built-in edi handler yet; clarify direction + exact mapping before committing (likely a status/inventory report, candidate for a new handler or a stock-API surface)
- Config-driven per business via the `EDI_PROFILE` fragment (envelope, charset, qualifier maps); mapping shape stays canonical and in code
- Companion to the DESADV/RECADV + PRICAT sessions — see [[EDIFACT Interfaces - DESADV RECADV]] and [[EDIFACT Interfaces - PRICAT]]

**Reference**
- Gap analysis / EDIFACT field-coverage — Confluence 215678985
- [open event](https://outlook.office365.com/owa/?itemid=AAkALgAAAAAAHYQDEapmEc2byACqAC%2FEWg0AAS7IEKRXT02slzmU1a62iwABe7KF6AAA&exvsurl=1&path=/calendar/item)

### Notes
- ✍️ 
