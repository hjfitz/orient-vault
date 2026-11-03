---
tags: [datadog-triage]
date: 2026-11-03
monitor: "[FUSE][Fuse UI] 5xx rate high (portal availability)"
service: fuse-ui
business_id:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793670966494899"
opened_at: "2026-11-03T01:54:55Z"
severity_assessed: P4
flapping: false
outcome: monitor_mistuned
ticket:
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: open
---
# fuse-ui 5xx rate 25% = 4 scanner websocket timeouts out of 16 overnight requests

## Fired
Monitor 303464815 (`sum(last_15m)` 5xx / all requests * 100 > 5, no minimum-volume guard, Terraform-managed) tripped at 25.0 (4 / 16 requests).

## Investigation
- Metric `gcp.run.request_count{service_name:fuse-ui-app-prod}` by class, 1-min: 4x 5xx (all 504) in the 01:53 bucket; 9x 2xx and 3x 3xx in the 15m window. Nothing else 01:30-01:57.
- Cloud Run request log (bifrost-prod-global1): the 4 504s are 01:47:27-01:47:33Z, unauthenticated hits on the LB IP 34.120.121.214 (`/`, `/raw`, `/ws`, `/socket.io/?EIO=4&transport=websocket`), user agent `rawgrab`, source IP 165.154.206.35, 300s latency ("reached the maximum request timeout"). Metric lands at request end (01:52-01:53).
- Other traffic 01:30-01:57: same scanner IP browsing /login, zgrab from 20.42.90.131, ClaudeBot on fuse.ilg.software. No operator request seen.
- Identical pattern 7 days ago: 4x 504 from `rawgrab` at 2026-10-27T10:05Z. No other 5xx in the Cloud Run log since 2026-10-20.
- 1 active instance throughout, no idle/scale change. Last fuse-ui deploy 2026-11-02T16:12Z (about 10h before); 5xx are on revision 00092 only from the scanner.
- Last 5xx bucket 01:53; 01:54-01:57 zero 5xx. Window clears about 02:08Z.
- Datadog logs `status:error` for fuse-ui: 0 hits.

## Outcome
Not a portal outage. Monitor has no low-volume guard so a scanner's websocket probes trip it overnight. Retune candidate: min request count or exclude traffic to the raw LB IP.

Not established: whether real operators were affected 02:05Z+ (triage ran at 01:57Z); why fuse-ui keeps websocket probes open for 300s; monitor fire history over 14 days (event search returned 0, so only the 5xx log history above).

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793670966494899
- Monitor: https://app.datadoghq.com/monitors/303464815
