---
tags: [datadog-triage]
date: 2026-10-22
monitor: "[FUSE][Snap Adapter] API latency threshold breached"
service: snap-adapter
business_id:
snap_instance: ilg001
channel: bifrost-notifications
thread_url: "https://gfsdeliver.slack.com/archives/C099WKQTE8G/p1792692146672599"
opened_at: "2026-10-22T18:36:08Z"
resolved_at: "2026-10-22T18:39:24Z"
minutes_spent: 3
severity_assessed: P4
flapping: true
outcome: vendor
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# ilg001 Snap API latency repeat (18:36Z), unchanged since 18:01Z triage

## Fired
Monitor 179927768 on `snap_host:https_//ilg001liveapi.snapfulfil.net/api`, status Alert at 18:36Z; one further firing folded in. No new Slack post or Datadog alert event existed for 18:36Z, so the reply went in the 18:01Z trigger thread.

## Investigation
- `snap.poll.request.latency.avg` on ilg001 since 18:01Z: 1.7s to 19.9s, spikes 19.9s and 11.5s.
- Poll outcome since 18:01Z (`snap.poll.request.success/failure` by snap_host): 108 success, 0 failure.
- snap_adapter / snap-polling-service / snap-queue-polling-service, @environment:prod, error/warn matching ilg001, timeouts, circuit, 5xx/404 since 18:01Z: 0.
- replay_service `Failure stored` for DOCKBAY/MANUCURIST since 18:01Z: 0.
- No Maintenance/ record covers ilg001 at this time.

## Outcome
P4 vendor: ilg001 still slow on Snap's side, no errors, nothing held. No action.

## Links
- Slack thread: https://gfsdeliver.slack.com/archives/C099WKQTE8G/p1792692146672599
- Reply: https://gfsdeliver.slack.com/archives/C099WKQTE8G/p1792694364724869?thread_ts=1792692146.672599
