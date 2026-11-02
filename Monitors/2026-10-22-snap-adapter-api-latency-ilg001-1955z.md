---
tags: [datadog-triage]
date: 2026-10-22
monitor: "[FUSE][Snap Adapter] API latency threshold breached"
service: snap-adapter
business_id:
snap_instance: ilg001
channel: bifrost-notifications
thread_url: "https://gfsdeliver.slack.com/archives/C099WKQTE8G/p1792692146672599"
opened_at: "2026-10-22T19:55:08Z"
resolved_at: "2026-10-22T19:57:32Z"
minutes_spent: 2
severity_assessed: P4
flapping: true
outcome: vendor
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# ilg001 Snap API latency repeat (19:55Z), unchanged since 18:36Z triage

## Fired
Monitor 179927768 on `snap_host:https_//ilg001liveapi.snapfulfil.net/api`, status Alert at 19:55Z; one further firing folded in. No new Datadog Slack post for this firing, so the reply went in the open 18:01Z ilg001 thread.

## Investigation
- `snap.poll.request.latency.avg` on ilg001 since 18:36Z (2-min avgs): 1.5s to 13.3s, spikes 13.3s and 11.0s.
- Poll outcome since 18:36Z (`snap.poll.request.success/failure` by snap_host): 246 success, failure series empty (0).
- snap_adapter / snap-polling-service / snap-queue-polling-service, @environment:prod, error/warn matching ilg001, timeouts, circuit, 5xx/404 since 18:36Z: 0.
- replay_service `Failure stored` for DOCKBAY/MANUCURIST since 18:36Z (free text and @businessId): 0.
- No Maintenance/ record covers ilg001 (DB1) at 19:55Z.

## Outcome
P4 vendor: ilg001 still slow on Snap's side, no errors, nothing held. No action.

## Links
- Slack thread: https://gfsdeliver.slack.com/archives/C099WKQTE8G/p1792692146672599
- Reply: https://gfsdeliver.slack.com/archives/C099WKQTE8G/p1792699052444879?thread_ts=1792692146.672599
