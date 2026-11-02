---
tags: [datadog-triage]
date: 2026-10-22
monitor: "[FUSE][Snap Adapter] API latency threshold breached"
service: snap-adapter
business_id:
snap_instance: ilg004
channel: bifrost-notifications
thread_url: "https://gfsdeliver.slack.com/archives/C099WKQTE8G/p1792671029454489"
opened_at: "2026-10-22T12:09:08Z"
resolved_at: "2026-10-22T12:11:33Z"
minutes_spent: 2
severity_assessed: P4
flapping: true
outcome: vendor
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# ilg004 Snap API latency Warn (repeat, 4 firings folded)

## Fired
snap.poll.request.latency.avg on ilg004liveapi > 2000ms over 20m (value 4975ms), Warn. Repeat of the 11:37Z triage.

## Investigation
- Since 11:37Z: snap.poll.request.failure 0 vs success 255 on ilg004live.
- Prod logs for snap_adapter / snap-polling-service / snap-queue-polling-service since 11:37Z: 0 error-level; 0 matching timeout/ETIMEDOUT/ECONNABORTED/502-504/404/circuit + ilg004. Only warn pattern: "Consignment StU not found" (703).
- Latency 10:00Z onward: 1.7–13.0s, no clear worsening.
- Prod replay holds created today: newest 11:00:10Z (PURDYFIGG); none since 11:37Z for any business.
- ilg001 fired the same monitor at the same time (separate thread, not triaged here).

## Outcome
P4 vendor, unchanged: post-DB4-update slowness, no errors, no holds. No action.

## Links
- Slack thread: https://gfsdeliver.slack.com/archives/C099WKQTE8G/p1792671029454489
