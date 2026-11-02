---
tags: [datadog-triage]
date: 2026-10-22
monitor: "[FUSE][Snap Adapter] API latency threshold breached"
service: snap-adapter
business_id:
snap_instance: ilg004
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792685487800789"
opened_at: "2026-10-22T16:10:08Z"
resolved_at: "2026-10-22T16:13:20Z"
minutes_spent: 3
severity_assessed: P4
flapping: true
outcome: vendor
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# ilg004 Snap API latency warn (repeat, post DB4 update)

## Fired
Monitor 179927768 went to Warn for snap_host ilg004liveapi at 16:10:08Z, on a 20-minute average of 4954.553 ms (warn above 2000, alert above 5000). Two further firings were folded in. This repeats the 15:21Z triage, which found ilg004 slow since the planned DB4 update ended at 08:54Z.

## Investigation
Every check below covers 15:21Z to about 16:12Z and used `@environment:prod`.
- **Latency:** `avg:snap.poll.request.latency.avg{environment:prod,snap_host:ilg004liveapi}` averaged 5.3s from 15:20Z. It peaked at 16.5s around 16:14Z, and the last point was 2.4s.
- **Polls:** `snap.poll.request.success` on ilg004liveapi was 411, and `snap.poll.request.failure` was 0.
- **Errors:** the snap_adapter, snap-polling-service and snap-queue-polling-service logs had no timeout, 5xx, 404 or circuit errors.
  - snap_adapter had 22 errors, all PURDYFIGG: 20 `schema_validation` (ShipContacts.0.LastName over 30 characters, #6506667 and #6575295) and 2 `slot_timeout`.
  - snap-polling-service logged 801 `Consignment StU not found` warnings, the same as the 801 in the same window on 21 Oct.
- **Holds:** replay_service logged `Failure stored` 20 times, all PURDYFIGG. There were none for KAPPAHL, BABYMORI, SAMMCK, SAIRA or SPORTLUX.

## Outcome
Vendor, P4, with no change since the 15:21Z triage. The host is slow, but polls are succeeding and nothing is held. The monitor has been flapping all day on ilg001 and ilg004 (see the other records from today).

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792685487800789
