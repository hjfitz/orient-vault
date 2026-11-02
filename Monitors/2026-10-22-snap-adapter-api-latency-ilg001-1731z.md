---
tags: [datadog-triage]
date: 2026-10-22
monitor: "[FUSE][Snap Adapter] API latency threshold breached"
service: snap-adapter
business_id:
snap_instance: ilg001
channel: bifrost-notifications
thread_url: "https://gfsdeliver.slack.com/archives/C099WKQTE8G/p1792690345875759"
opened_at: "2026-10-22T17:31:08Z"
resolved_at: "2026-10-22T17:33:25Z"
minutes_spent: 2
severity_assessed: P4
flapping: true
outcome: vendor
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# ilg001 Snap poll latency over 5s (repeat)

## Fired
Monitor 179927768, group snap_host ilg001 live, 20-minute average of 5494ms against a 5000ms alert threshold. Repeat of the 15:21Z and 16:11Z triages.

## Investigation
- `snap.poll.request.latency.avg` for ilg001 from 16:11Z to 17:32Z averaged 3.8s, with one 17.7s point around 17:28Z.
- `snap.poll.request.success` 247 and `failure` 0 for ilg001 since 16:11Z.
- No error/warn logs mentioning ilg001 in snap_adapter, snap-polling-service or snap-queue-polling-service since 16:11Z. All 29 snap_adapter errors were PURDYFIGG `Entity creation in SNAP failed`.
- replay_service `Failure stored`: 52 since 16:11Z, all PURDYFIGG. None for DOCKBAY or MANUCURIST.
- Not established: replay-service API check (Fuse MCP auth rejected), so holds were checked through Datadog logs only.

## Outcome
Vendor-side slowness on ilg001, P4, with no errors and no impact. Thread reply posted.

## Links
- Slack thread: https://gfsdeliver.slack.com/archives/C099WKQTE8G/p1792690345875759
