---
tags: [adhoc-task]
date: 2026-11-11
tldr: "Took over the orient Svelte UI programme on the VM and finished it (Next, React and orient-web retired, live at 6445727, tag next-ui-final); then opened and planned the orient Notes programme (a Confluence-style workspace; 16 units, reviewed twice) and started on N0; cleanup of the old build, a real review draft and G1 are owed"
session_id: 8584435d-36a9-464d-bc60-e21c842cfe59
status: open
---
# Finish the orient Svelte UI waves on the VM and retire Next

## Outcome
Fixed the W-G and rail review findings, got every gate green, deployed the five waves and the rail, drove every page in a browser, landed the two Retire-prep changes (core `/api/reindex` rebuilding in a child process, after I found and fixed my own 35 s core freeze; the review draft through `headless.ts`), then, with Harry's go, retired the UI: Next, React, `orient-web` and the proxy are gone (20 commits, live at `6445727`, pushed; the last tree that has them is the tag `next-ui-final`). Programme complete.
Owed (status open): a day after 2026-11-11 15:05Z delete `.next-prod`, `.next-prod.bak`, `.next-bench` on the VM; run one real PR review draft; send the note to Darren (drafted in Harry's Slack); decisions and dead-code cleanup in [[Handovers/2026-11-11-orient-svelte-ui]] (Waiting on Harry) and the programme's decision log.

## Next programme
Harry then asked for the Notes section to become a Confluence clone (the usual renderer, extensible for soaks and incidents, Diagrams merged or trashed ahead of a C4 whiteboard). Answers: core wiki scope, typed pages in place, **trash Diagrams now**, plan then build. Programme `Bifrost/orient Notes/` (Overview, Design revision 2, Migration State): 16 units, two adversarial plan reviews folded in (see its decision log). Status: N0 (golden harness for the renderer) in progress; N9a (uploads) needs an opus-tier session and gate G1 (attachment policy, Harry's call). Plan: [[Bifrost/orient Notes/Design]].
