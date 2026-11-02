---
tags: [datadog-triage]
date: 2026-10-22
monitor: "[FUSE][Snap Adapter] API latency threshold breached"
service: snap-adapter
business_id:
snap_instance: ilg001, ilg004
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792678349489129"
opened_at: "2026-10-22T14:11:08Z"
resolved_at: "2026-10-22T14:14:26Z"
minutes_spent: 3
severity_assessed: P4
flapping: true
outcome: vendor
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# ilg001 + ilg004 Snap API latency, warn after >5s alert (repeat)

## Fired
At 14:11:08Z, monitor 179927768 moved both groups from Alert (>5s) down to Warn (>2s). The 20m averages were ilg001 at 3943.9ms and ilg004 at 4271.9ms. Only these two groups fired at or after 14:11Z; the alert events checked ran from 13:30Z to now.

## Investigation
- 5-min `snap.poll.request.latency.avg` from 13:00Z: ilg001 2.1–7.4s and ilg004 2.8–7.5s. Neither shows an upward trend.
- Polls since 13:30Z: `snap.poll.request.success` was 139 on ilg001 and 330 on ilg004. `snap.poll.request.failure` returned no data on any host.
- Error logs since 13:30Z (`@environment:prod`, snap_adapter / snap-polling-service / snap-queue-polling-service):
  - Nothing mentions ilg001 or ilg004.
  - Fleet-wide there were 2 `Entity creation in SNAP failed` errors, both data rejections: PURDYFIGG PO-U-00002210 (invalid unit / no product) and STUBBLE SCPR3468 (LastName mandatory).
  - The 368 `Consignment StU not found` warnings are baseline: the same window yesterday had 600.
- Prod replay holds created today total 113. The two created since 13:30Z are the PURDYFIGG and STUBBLE ones above. None belong to DOCKBAY, MANUCURIST, KAPPAHL, BABYMORI, SAMMCK, SAIRA or SPORTLUX; the newest SPORTLUX hold is still 08:41:43Z.
- No maintenance window covers 14:11Z: the DB4 update window started 08:30Z, and its end was 08:54Z per the prior triage.

## Outcome
P4 vendor. Nothing has changed since the 13:31Z and 13:37Z triages. Replies were posted in both threads (ilg001 p1792678349489129, ilg004 p1792678351209939). The monitor is flapping all day and the retune is still owed.

Not established: the Snap hosts for PURDYFIGG and STUBBLE, because the prod `lookup-snap-instance` business list came back empty. Neither business is on the ilg001/ilg004 lists, and both errors are data rejections, not timeouts.

## Links
- Slack thread (ilg001): https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792678349489129
- Slack thread (ilg004): https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792678351209939
