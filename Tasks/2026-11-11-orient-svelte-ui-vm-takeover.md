---
tags: [adhoc-task]
date: 2026-11-11
tldr: "Took over the orient Svelte UI programme on the VM and deployed W-C, D1, D2, F, G, the rail and two Retire-prep changes (live at ef8d2c8), stopping at gate G8; 13 commits are unpushed until a write-enabled deploy key exists"
session_id: 8584435d-36a9-464d-bc60-e21c842cfe59
status: open
---
# Finish the orient Svelte UI waves on the VM, up to gate G8

## Outcome
Fixed the five W-G review findings and the rail unit's review findings, got every gate green (three test fixes for running on the VM), deployed the five waves and the rail at fa069be, drove every moved page in a browser, ticked the five units done, and landed the two Retire-prep changes (core `/api/reindex` with the rebuild in a child process; the review draft's spawn through `headless.ts`). Live at `ef8d2c8`. Found and fixed my own regression on the way: the first in-core reindex froze the core for ~35 s (live from 13:36Z to 13:57Z).
Owed (status open): Harry adds a write-enabled deploy key so the 13 local commits can be pushed, runs one real PR review draft, and ticks G8 (earliest 2026-11-18) before Retire. Detail: [[Handovers/2026-11-11-orient-svelte-ui]] (Waiting on Harry) and the programme's decision log.
