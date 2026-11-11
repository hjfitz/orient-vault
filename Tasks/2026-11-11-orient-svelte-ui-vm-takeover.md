---
tags: [adhoc-task]
date: 2026-11-11
tldr: "Took over the orient Svelte UI programme on the VM, deployed every wave and the rail, then retired Next, React and orient-web (live at 6445727, pushed, tag next-ui-final keeps the old UI); cleanup of the old build and a real review draft are owed"
session_id: 8584435d-36a9-464d-bc60-e21c842cfe59
status: open
---
# Finish the orient Svelte UI waves on the VM and retire Next

## Outcome
Fixed the W-G and rail review findings, got every gate green, deployed the five waves and the rail, drove every page in a browser, landed the two Retire-prep changes (core `/api/reindex` rebuilding in a child process, after I found and fixed my own 35 s core freeze; the review draft through `headless.ts`), then, with Harry's go, retired the UI: Next, React, `orient-web` and the proxy are gone (20 commits, live at `6445727`, pushed; the last tree that has them is the tag `next-ui-final`). Programme complete.
Owed (status open): a day after 2026-11-11 15:05Z delete `.next-prod`, `.next-prod.bak`, `.next-bench` on the VM; run one real PR review draft; send the note to Darren (drafted in Harry's Slack); decisions and dead-code cleanup in [[Handovers/2026-11-11-orient-svelte-ui]] (Waiting on Harry) and the programme's decision log.
