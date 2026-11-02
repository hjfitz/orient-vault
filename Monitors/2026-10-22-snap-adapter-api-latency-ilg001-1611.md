---
tags: [datadog-triage]
date: 2026-10-22
monitor: "[FUSE][Snap Adapter] API latency threshold breached"
service: snap-adapter
business_id:
snap_instance: ilg001
channel: bifrost-notifications
thread_url: "https://gfsdeliver.slack.com/archives/C099WKQTE8G/p1792685544779179"
opened_at: "2026-10-22T16:11:08Z"
resolved_at: "2026-10-22T16:13:54Z"
minutes_spent: 3
severity_assessed: P4
flapping: true
outcome: vendor
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# ilg001 Snap API latency warn (repeat of 15:21Z triage)

## Fired
Monitor 179927768 warned for snap_host ilg001liveapi at 16:11:08Z: 20-min avg `snap.poll.request.latency.avg` 3575ms (warn 2000, alert 5000).

## Investigation
- Latency 15:22Z–16:12Z: avg 5.2s, peak 18.2s (~15:50Z), min 1.6s.
- `snap.poll.request.success` ilg001 since 15:21Z: 202; `failure`: none.
- Snap service error/warn logs (snap_adapter, snap-polling-service, snap-queue-polling-service, @environment:prod) since 15:21Z: none mention ilg001. 22 snap_adapter errors all PURDYFIGG `Entity creation in SNAP failed`; DOCKBAY 3 `Consignment StU not found` warnings.
- replay_service `Failure stored` since 15:21Z: 20, all PURDYFIGG; none DOCKBAY/MANUCURIST.
- Not established: Snap-side cause of the slowness; Snap host probe not run (Fuse MCP disconnected).

## Outcome
Vendor P4, unchanged since 15:21Z. Monitor has fired repeatedly on ilg001 all day.

## Links
- Slack thread: https://gfsdeliver.slack.com/archives/C099WKQTE8G/p1792685544779179
