---
tags: [meeting]
series: Purdy and Figg Go-Live War Room
title: Purdy and Figg Go-Live War Room
---
# Purdy and Figg Go-Live War Room

## 2026-09-01

### Context

**Attendees**
- [[Matt Shaw]], [[Nylah Klasson]], [[Harry Humby]], [[Schuster Efigenio]] (Southampton/remote)
- [[Tom Dunn]], [[James Godsell]], Darren Rielly, [[Peter Liu]], [[Lee Simmons]], Ryan Ellis (Northampton, on-site with the customer)
- Milosz Fialkowski, Denis Tomolea (ILG)

**Other context**
- Coordinated live in #purdy-and-figg-go-live-01-09 (Slack), 09:00–11:35 BST so far
- Datadog log query for orders failing into Snap for this business: [link](https://app.datadoghq.com/logs?query=%40domain%3Afuse%20status%3Aerror%20%40environment%3Aprod%20%40businessId%3APURDYFIGG&agg_m=count&agg_m_source=base&agg_q=%40canonicalRecord.order.customerRef&agg_t=count&analyticsOptions=%5B%22bars%22%2C%22dog_classic%22%2Cnull%2Cnull%2C%22value%22%5D&clustering_pattern_field_path=message&cols=host%2Cservice&messageDisplay=inline&refresh_mode=sliding&storage=hot&stream_sort=desc&viz=toplist&live=true)

### Notes
- ✍️ 09:34 — Shopify connector switched live (James, with Darren's go-ahead)
- ✍️ 09:40–09:44 — first reap: 0 orders, then 298 orders retrieved on the next pass
- ✍️ 09:46 — first failures surfaced: city field >30 chars on a few orders, missing SKUs on others
- ✍️ 09:55 — agreed to tighten the `created_at` retrieval condition to avoid backdating a large backlog into Snap
- ✍️ 10:09 — shared a Datadog log link so ILG can self-serve the current failing-orders list
- ✍️ 10:34 — status check-in: all green on the Fuse side; Northampton reports WMS release running slow (BGP-related, "Snap being Snap") but orders processing operationally
- ✍️ ~10:47 — James working `ILG_OTHER` tag mapping into the size-tag logic for warehouse visibility (not causing failures, cosmetic gap)
- ✍️ 11:08–11:17 — a genuinely un-replayable order surfaced (#6270193): already processed in the warehouse but re-appeared due to wide retrieval conditions — Fuse can't confirm it now. Flagged to Milosz. Captured as a piece of work to investigate (repeated-order-on-wide-retrieval-window).
- ✍️ 11:14 — Matt: internal monitors green end-to-end (ingest → canonicalisation → Snap → confirmations)
- ✍️ 11:17 — a retry-queue update attempt hit a secondary issue: 12 other fields then failed, and the retry silently amended site ID `'0010'` → `'10'`
- ✍️ 11:21–11:24 — UI promoted to prod to support the go-live
- ✍️ 11:34 — James replayed the 3 city-too-long orders (customer-side fix applied) and lowered the retrieval window to 90 minutes

### Carried forward (open, not yet resolved as of 11:35)
- [ ] Investigate repeated/un-replayable orders caused by wide retrieval-window backdating (order #6270193 and similar) — captured as a piece of work, no ticket yet
- [ ] The retry-queue's field-12-failure + silent site-ID amendment (`'0010'` → `'10'`) James hit at 11:17 — needs a real look, not just a retry
- [ ] Peter Liu's broader point: "a standardised approach to retrieval days for the go-live process" — worth a process decision beyond this one customer
