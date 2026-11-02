---
tags: [datadog-triage]
date: 2026-10-22
monitor: "[FUSE][Snap Adapter] API latency threshold breached"
service: snap-adapter
business_id:
snap_instance: ilg001
channel: bifrost-notifications
thread_url: "https://gfsdeliver.slack.com/archives/C099WKQTE8G/p1792692146672599"
opened_at: "2026-10-22T18:01:08Z"
resolved_at: "2026-10-22T18:03:19Z"
minutes_spent: 2
severity_assessed: P4
flapping: true
outcome: vendor
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# ilg001 Snap API latency repeat (18:01Z), unchanged since 17:31Z triage

## Fired
Monitor 179927768 on `snap_host:https_//ilg001liveapi.snapfulfil.net/api`: `snap.poll.request.latency.avg` 5045ms > 5000ms over 20m. One further firing folded in. Repeat of the day's ilg001 latency firings.

## Investigation
- Poll outcome since 17:31Z (`snap.poll.request.success/failure` by snap_host, sum): 96 success, 0 failure.
- Errors since 17:31Z in snap_adapter / snap-polling-service / snap-queue-polling-service, @environment:prod, status error/warn: none besides `Consignment StU not found` (407 warns), which pre-dates the window (5000+ between 11:00Z and 17:31Z). No 5xx/404/timeout/circuit-open patterns.
- replay_service `Failure stored` for DOCKBAY/MANUCURIST since 17:31Z: 0.

## Outcome
P4 vendor: ilg001 slow on Snap's side, no errors, nothing held. No action. Monitor is flapping on a sustained vendor slowness.

## Links
- Slack thread: https://gfsdeliver.slack.com/archives/C099WKQTE8G/p1792692146672599
