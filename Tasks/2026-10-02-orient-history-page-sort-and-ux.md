---
tags: [adhoc-task]
date: 2026-10-02
tldr: "Redeployed orient so /history showed, made its table sortable, then a ux-review pass: fixed 0-tool-calls parser bug, layout at every width, and the missing nav group."
session_id: 0788cadb-ae79-416c-bc1c-db1dc03dee13
status: done
---
# Make orient's History page visible, sortable and correct

## Outcome
orient-web was serving a build older than the History commit; redeployed, and `CLAUDE.md` now says to run `pnpm deploy:web` after app changes (also a nav-view note). Sortable columns via `?sort=&dir=` (f6b3515). ux-review of `/history` (ae82825): Tools read 0 on every row because the parser looked for `"type":"assistant"` in the first 320 chars and it sits at the end of the line (04cbd7b, cache bumped to v2); right-aligned numerics, sticky header, 1400px cap, phone stats line, empty-state recovery. Added `history` to the vault `.knowledge/config.yaml` nav group; design.md has a `/history` section and is re-anchored.
Owed: no second pane on the ultrawide and no "hide empty sessions" filter (both left as your call); transcript view (`/history/<id>`) not yet reviewed.
