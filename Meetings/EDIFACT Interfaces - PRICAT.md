---
tags: [meeting]
series: ILG — EDIFACT Interfaces (PRICAT)
title: ILG — EDIFACT Interfaces (PRICAT)
---
# ILG — EDIFACT Interfaces (PRICAT)

## 2026-06-23

### Context

**Attendees**
- Accenture — Rafael Peñuela Tristán (organizer)
- Accenture — Patricia Navarro, Miguel Fernández
- Puig — Manel Sibils, David Baños, Neus Bock
- [[Charlotte Tilbury]] — Sham Ahmad, Karolina Semeniuk
- ILG — Harry, [[Jack Bailey]], [[Lee Simmons]], Sam Taylor-Rowlinson

**Where we are on PRICAT**
- PRICAT maps to **master_data** in Fuse, handled by `@gfs-bifrost/edi` (v0.2.0)
- v0.2.0 reads primary/alternative identifier by **PIA code-list** + **IMD component index** from the per-business `EDI_PROFILE` config fragment — envelope, charset and qualifier maps vary per customer without forking handler code
- EDI parsing is **near-bespoke for [[Charlotte Tilbury]]** (the high-value driver); ORDERS is parked

**Reference**
- Gap analysis / EDIFACT field-coverage — Confluence 215678985
- [open event](https://outlook.office365.com/owa/?itemid=AAkALgAAAAAAHYQDEapmEc2byACqAC%2FEWg0AAS7IEKRXT02slzmU1a62iwABe7KFwwAA&exvsurl=1&path=/calendar/item)

### Notes
- ✍️ 
