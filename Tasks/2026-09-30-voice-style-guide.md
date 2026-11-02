---
tags: [adhoc-task]
date: 2026-09-30
tldr: "Built and validated an evidence-backed Slack voice style guide from 3,941 of Harry's own messages; with substance supplied drafts pass at chance (6/15); the `voice` skill is built"
session_id: 10181f4a-e6e7-4706-a6bb-3e49707e7bc1
status: done
---
# Build a style guide so a skill can draft Slack replies in Harry's voice

## Outcome
Sampled 52 random weekdays (Aug 2025 to Sep 2026), filtered out machine-written posts (em dashes are the tell),
profiled six audience clusters, and wrote the guide to `Voice/` in the vault (`Voice.md`, `Audiences.md`,
`Method.md`, `Validation.md`, five files under `Registers/`). Held-out tests: without facts Harry picked his real
reply in 14-15 of 16 (drafts lacked substance), so the guide gained a "Substance first" section; with the
substance supplied he picked it in 6 of 15 (40%, chance 33%). The guide beat a no-guide control mechanically
(emoji, "in to", length) but not in his preference.
Built the `voice` skill (`~/.claude/skills/voice/`): substance first, read the thread, pick the register, lint with
`check.py` (0 errors on 32 real replies once the channels full-stop case was a warning), show in chat, never send. Refresh kit
in `refresh/` (scripts and prompts, no corpus). Smoke-tested on a live DM: it correctly refused to force a reply when the
supplied point did not fit the thread. Next iteration is real use: note heavy edits and add rules only with counts.
Raw DM corpus deliberately not stored; answer keys are in the session scratch dir only.
