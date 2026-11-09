---
tags: [datadog-triage]
date: 2026-11-08
monitor: "[FUSE][Fuse UI] 5xx rate high (portal availability)"
service: fuse-ui
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794145268795189"
opened_at: "2026-11-08T13:39:55Z"
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# fuse-ui 5xx 26.7% = 4 scanner websocket timeouts in a 15-request window (no operator traffic)

## Fired
Monitor 303464815 (`sum(last_15m)` 5xx / all `gcp.run.request_count{service_name:fuse-ui-app-prod}` x100 > 5, priority 2, Terraform-managed, no minimum-volume guard) Triggered 13:39:55Z at 26.667. Slack alert ts 1794145268.795189 in C099WKQTE8G, no replies when read. Monitor status was still Alert on the re-check after the Cloud Run query (it only clears once the burst leaves the 15m window).

## Investigation
- Counts: 1-min `gcp.run.request_count` by class and code, 13:13-13:40Z: 8x 200 and 3x 307 in the 13:33 bucket, 4x 504 in the 13:38 bucket, nothing else. 4 / 15 = 26.667%, matching the monitor value. Last 20m re-check: 5xx 4, total 15, zero requests or 5xx after the 13:38 bucket.
- Cloud Run request log (`gcloud logging read`, project bifrost-prod-global1, fuse-ui-app-prod, 13:20-13:45Z): the 4 504s are all 13:32:10-13:32:16Z, latency 299.99-300.00s, from one IP 165.154.206.35, user agent `rawgrab`, to the raw LB IP 34.120.121.214 (not fuse.ilg.software), paths `/`, `/raw`, `/ws`, `/socket.io/?EIO=4&transport=websocket`, severity ERROR. The metric lands at request end (13:37-13:38).
- The 11 non-5xx requests in the window match the same pattern: 3x 307 and 8x 200 (`/login`, favicon, 6 `_next/static` chunks), all from 165.154.206.35 (NTRIP GNSSInternetRadio UA, old Chrome/49 and Chrome/106 UAs), plus a later 307 and 200 at 13:41:50Z from 172.104.11.34 (Mac Chrome/108 UA). No request carried an operator user agent or the fuse.ilg.software host.
- Same source and pattern as the 2026-11-03 01:54Z firing (rawgrab, 165.154.206.35, 4x 504 at 300s; see Monitors/2026-11-03-fuse-ui-5xx-rate-high-portal-availability.md).
- 7d totals: 13 5xx of 21,786 requests (0.06%). `search_datadog_events` source:alert for this monitor over 30d: 7 Triggered, 6 Recovered, 1 Warn (this firing still open).
- p99 `gcp.run.request_latencies` for fuse-ui-app-prod peaked at 324,644 ms in the 13:36 minute (the 300s-timeout requests); 12:43-13:40Z otherwise 9.9-126.7 ms. `gcp.run.container.instance_count`: 1 active/idle each minute, no scale event.
- fuse-ui app logs (Datadog `service:fuse-ui`, 13:25-13:45Z): 7 info lines (GET /, /raw, /ws), no error-status lines; `(service:fuse-ui* OR service:fuse_ui*) status:error` over 3h: 0 hits.
- Deploys: latest prod deployment of gfs-bifrost/fuse-ui is 2026-11-05T15:52:57Z (sha 89bf136d, matches the version tag in the logs), about 2 days 22h before the alert. `get_change_stories` for fuse-ui 2026-11-01 to 11-08: 0 stories.
- Other services: `gcp.run.request_count` 5xx by service_name, 13:00-14:00Z: fuse-ui-app-prod 4, mock-coll8-cp-dev (dev) 1, the other 8 services returned 0. Datadog error logs for `@domain:fuse @environment:prod` 13:25-13:45Z: 1 line total (config-service), not examined.
- Direct probe (read-only GET https://fuse.ilg.software/) x3 at about 13:45Z: 307 in 22-46 ms each.

## Outcome
Not a portal outage: no request to the portal hostname failed. The monitor has no minimum-volume guard, so one scanner holding four websocket-style requests to the 300s Cloud Run timeout reads as 26.7% of a 15-request window. Flaps on the same cause (7 triggers in 30d). Retune candidate: a minimum request count or absolute 5xx floor, or excluding the raw LB IP. No ticket filed here.

Not established: whether any real operator used the portal in the window (logs carry no user identity; none seen); why fuse-ui holds websocket upgrade requests open to 300s; whether the monitor recovers on its own at the end of the 15m window (status was still Alert when checked); the one config-service error log at 13:25-13:45Z was not examined; the 8-service 5xx list is the set the metric query returned, not every Fuse service.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794145268795189
- Monitor: https://app.datadoghq.com/monitors/303464815
