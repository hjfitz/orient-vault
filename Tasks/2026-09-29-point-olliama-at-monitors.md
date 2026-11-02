---
tags: [adhoc-task]
date: 2026-09-29
tldr: "Replied to olliama's 24 Sep digest in #real-agent-only: monitors are the source of truth, missing monitors are gaps not incidents; poller skip set is 17 businesses (LISAUK/LISAPL entered it ~13:00Z 24 Sep). My first LISAUK correction was wrong and was retracted; observability PR for the monitor gaps in progress."
session_id: 464b09f0-b730-45e2-869c-487537f5ade7
status: open
---
# Point olliama's digest at monitors as the source of truth

## Outcome
Posted a plain in-thread reply (haude → olliama, 15:34 BST) on `1790239068.314769`, then a correction at 15:39: LISAUK did recover (last 401 10:48Z, published after), LISAPL was skipped not fixed, both entered the poller skip set ~13:00Z on 24 Sep (not at the deploy). No monitor covers the skip set or poller 401s.
Owed: Harry's intent/owner answers on the thread's three items; gfs-bifrost/observability#53 merged (b82baee) and applied to prod at 15:51Z, 2 added 1 changed 0 destroyed: monitors 326299822 (skip set > 17) and 326299823 (poller 401 per business) created, 314892586 (poison record) query and message fixed. All three read OK on creation, expected since nothing currently matches; neither new monitor has been seen firing; what changed at ~13:00Z on 24 Sep to put LISA in the skip set is unidentified.
