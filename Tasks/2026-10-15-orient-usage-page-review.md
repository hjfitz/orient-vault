---
tags: [adhoc-task]
date: 2026-10-15
tldr: "orient: epic colours on the sprint board, Haiku 5.5 priced, /usage reviewed — every figure was ~2.2x too high (duplicate transcript lines); fixed, and Spend section rebuilt as daily cost + biggest sessions, deployed"
session_id: f3774182-f4eb-491b-ab56-a37bd4b01a7e
status: open
---
# Review orient's /usage page and fix what it found

## Outcome
Sprint board colours cards by epic; Haiku 5.5 priced (incl. >100K tier). /usage review: Claude Code writes one transcript line per content block of a request and orient charged each, so all spend/token figures were ~2.2x high (checked against Claude Code's own statusline cost: deduped 0.97x, old 2.22x). Fix + non-destructive manifest migration committed in `~/projects/orient` (9cee81c), deployed 2026-10-15 — dropped lifetime from ~$30k to ~$13k and flags days before 2026-09-14 as scaled estimates.
My Haiku manifest bump had wiped history older than transcript retention; restored from the v9 archive (backup: `~/.local/state/orient/token-usage-cache.pre-restore-*.json`).
Spend section rebuilt (9a3bb78, deployed): daily cost by reads/writes/output + biggest-sessions table; design doc updated and re-anchored.
Owed: time-windowed ticket/work attribution (needs hourly per-session buckets) and skill record changes (`started_at`).
