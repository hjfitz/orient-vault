---
tags: [adhoc-task]
date: 2026-10-15
tldr: "Added a channel mode to support-watch (poller script + Monitor, mirrors datadog-watch) for human questions in #bifrost-support; replies via support bot never admit our-side fault, console reports it."
session_id: 1d9d4e08-5fd6-456e-a688-ccf226d4b051
status: open
---
# Mirror datadog-watch into support-watch

## Outcome
`~/code/.claude/skills/support-watch/` gains `channel-poll.sh` and a Channel mode in SKILL.md (thread mode kept). Poller tested live read-only (new message, thread replies, bot filtering, idempotent rerun). Not started yet: owed a first supervised start, and a decision on whether bot posts (Datadog alerts) in #bifrost-support should ever be triaged.
