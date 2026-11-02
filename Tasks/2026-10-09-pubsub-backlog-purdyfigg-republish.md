---
tags: [adhoc-task]
date: 2026-10-09
tldr: "Explained 08-Oct evening Pub/Sub backlog alerts (PURDYFIGG Shopify 3h window re-publish, not a stuck consumer), posted exec summary to bifrost-notifications, built alert-watch skill (Monitor + poll script that dispatches datadog-triage)"
session_id: 4683e989-1dd8-45cf-b386-565cac9bbffb
status: open
---
# Investigate 08-Oct evening Pub/Sub backlog alerts, build alert-watch

## Outcome
Backlog: three alerts (16:06/16:26/16:40 UTC) all on `fuse-tracker.prod.create_record_request.sales_order.v1.sub`; oldest-unacked age never above ~10s, no nacks. Cause: PURDYFIGG shopify connector (3h created_at/updated_at window, 5 min poll, stateless) re-publishes every in-window order each poll; dedupe holds them (1.77M duplicates lifetime). Peaks of 1.1-2.2k/5min are routine for two weeks. Exec summary posted to bifrost-notifications via the support bot.
alert-watch: new skill at `~/code/.claude/skills/alert-watch/` (`alert-poll.sh` polls Datadog monitor search for monitors notifying slack-bifrost-notifications, dedupes by cause, one line per poll; SKILL.md dispatches `datadog-triage` in a subagent, escalation returns to main for `incident-response`). Poller tested (baseline, repeat, window suppression, cause key) and the Monitor transport smoke-tested; no end-to-end triage run yet, since that would post to the live channel.
Owed: decide on the monitor change (alert on oldest-unacked age) and PF window; first supervised alert-watch shift, then check /usage for idle cost.
