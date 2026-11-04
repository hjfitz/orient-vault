---
tags: [datadog-triage]
date: 2026-11-04
monitor: "[FUSE][Fuse UI] 5xx rate high (portal availability)"
service: fuse-ui
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793831167996869"
opened_at: "2026-11-04T22:24:55Z"
resolved_at: "2026-11-04T22:28:00Z"
minutes_spent: 3
severity_assessed: P4
flapping: true
outcome: self_resolved
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# fuse-ui portal 5xx ratio 26.7% on 4 requests (low-traffic night window)

## Fired
Monitor 303464815 (`sum(last_15m)` 5xx / total of `gcp.run.request_count{service_name:fuse-ui-app-prod}` x100 > 5) tripped at 22:24:55Z with 26.667. Slack alert ts 1793831167.996869, no replies in the thread.

## Investigation
- Real counts: `gcp.run.request_count` 5xx vs total, 5-min buckets from 21:30Z: 5xx = 4 in the 22:20-22:25 bucket and none in earlier buckets; totals 11 (22:15-22:20) and 4 (22:20-22:25). 4 / 15 requests in the 15m window = 26.667%, which matches the monitor value.
- Response codes per minute from 22:00Z: all 4 failures were HTTP 504, all in the single minute 22:22Z, and all 4 requests that minute were 504. Earlier in the window: 8x 200 and 3x 307 at 22:17Z. 0 requests in each minute 22:23-22:27Z, so there is no traffic proving recovery, only no further 5xx.
- Daily totals 29 Oct - 4 Nov: 1622, 2346, 3972, 2074, 1142, 2948, 2916 requests. 5xx: none recorded 29 Oct - 2 Nov, 5 on 3 Nov, 4 on 4 Nov. So 4 of 2916 on 4 Nov (about 0.14%). Hourly totals over 48h range from 3 to 725 requests.
- Flapping: `search_datadog_events` source:alert for this monitor over 7d shows 3 triggers (3 Nov 01:54Z, 3 Nov 07:39Z, 4 Nov 22:24Z) and 2 recoveries (3 Nov 02:08Z, 07:52Z). Hourly 5xx on 3 Nov: 4 in the 01:00 hour (24 total requests) and 1 in the 07:00 hour (15 total).
- Cloud Run `gcp.run.container.instance_count` for fuse-ui-app-prod was 1 active, 0 idle each minute 21:45-22:25Z.
- fuse-ui app logs (`service_name:fuse-ui-app-prod`) since 22:00Z hold only 6 request lines, all at 22:16Z from one client IP 152.32.216.159 (user agents `rawgrab`, `NTRIP GNSSInternetRadio`, old Chrome; paths `/`, `/raw`, `/ws`). There are no error-status logs and nothing at 22:22Z. The 504 requests have no app log line and no matching Cloud Run request log in Datadog (searched `@http.status_code:5*` and Cloud Run request log sources, 0 hits).
- No `source:change_tracking` events for fuse-ui in the last 24h (0 results). Running revision tag in the logs is `fuse-ui-app-prod-00094-dst`, version `ab9a3373`.
- Direct probe at 22:27Z: 3 x GET https://fuse.ilg.software/ returned 307 in 18-50 ms each (no 5xx).

## Outcome
Self-resolved, P4. No sustained user impact established: 4 failed requests in one minute, none since, portal answering normally on a direct probe. The monitor tripped on ratio over a very low-volume window and has flapped 3 times in 7 days at low-traffic hours. No ticket filed. A retune (add a minimum request count or absolute 5xx floor) would be worth considering but is not done here.

Not established: which routes the 4 requests hit, what caused the 504s (nothing logged by the app, no Cloud Run request logs in Datadog), and whether the 22:16Z scanner traffic is related (only timing proximity).

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793831167996869
- Monitor: https://app.datadoghq.com/monitors/303464815
