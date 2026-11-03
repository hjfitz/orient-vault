---
tags: [adhoc-task]
date: 2026-11-03
tldr: "Re-baselined the Confirmation Enrichment Pipeline programme against snap-adapter master 7f4e10d: claim deleted, clearing universal and paged, run budgets added, mapper/call counts moved; U0 not started."
session_id: 7b94e574-82eb-45c6-8407-685699118d76
status: open
---
# Re-baseline the Confirmation Enrichment Pipeline programme

## Outcome
Checked the programme (written 2026-09-18) against ~50 commits on `apps/snap-queue-polling-service` and annotated `Bifrost/Confirmation Enrichment Pipeline/` (Migration State + Target Design) with dated SUPERSEDED markers and a Decision log entry. The programme stands (nothing landed, type set unchanged), but the claim stage, R2, the 56/21/40/11 counts and the C2 allow-list notes are void.
Owed: Harry to read the re-baselined Target Design before U0; `waypoint-refresh` on snap-queue-polling-service `architecture.md` / `overview.md` (no anchor, so `wp stale` can't flag them); `snap-adapter` is now cloned at `~/code/fuse/snap-adapter`.
