---
tags: [adhoc-task]
date: 2026-11-09
tldr: "Built ~/code/fuse/tv-dashboard: Pi-hosted office wall (availability, traffic in/out, backlogs) with red takeover on P1/P2, traffic flatline or backlog over limit. Tested live against Datadog; not yet deployed to a Pi."
session_id: ba5a56e8-fcae-4d15-8064-c802762e6fed
status: open
---
# Build the office TV wall dashboard

## Outcome
New zero-dependency Node app at `~/code/fuse/tv-dashboard` (not a git repo yet, nothing pushed). 31 unit tests pass and it runs against live Datadog. The traffic rule was calibrated by replaying 7 days of real data: week-on-week ratio alone cried wolf 6-10% of the time, so critical is flatline or collapse gated on last week's baseline.
Owed: create a scoped Datadog app key (monitors_read, timeseries_query), set up the Pi (see README), and decide whether to `git init` and push. Real businessIds are shown on the wall, by choice.
