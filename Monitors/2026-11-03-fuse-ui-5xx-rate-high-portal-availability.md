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
# fuse-ui 5xx rate high = scanner websocket timeouts (01:54Z 25%, 07:40Z 10%)

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

## Second firing 07:39:55Z (metric value 10.0)
- Slack alert ts 1793691666.045939 in C099WKQTE8G (separate top-level post); tripped at 10.0 = 1 5xx / 10 requests in the 15m window.
- Metric `gcp.run.request_count{service_name:fuse-ui-app-prod}` by class, 1-min, 07:00-07:39Z: one 5xx (07:37 bucket), 2xx x4, 3xx x8, no 4xx. Nothing else in the window.
- The one 5xx is a 504 at 300.000s (request logged 07:31:49Z, started about 07:26:49Z): GET `https://production-ws.kriptosh.com/v1/ws?r=4alh91475ab7` from 87.199.203.96, UA generic Windows Chrome-style string. Same IP made two 307s in the same second (`production-api.kriptosh.com/api/v1`, `zzctl-u2wz0y3v5l58.example.com`): a Host-header probe, not an operator. Different scanner and IP from the 01:47Z `rawgrab` one, same pattern (websocket upgrade held to the 300s Cloud Run timeout).
- All requests 07:00-07:41Z (Cloud Run log, bifrost-prod-global1): ClaudeBot, fasthttp `/.git/HEAD`, python-requests, Mac-Chrome UA scanners on the LB IP 34.120.121.214, the probe above. No request carrying an operator path or user agent; no 4xx; no other 5xx.
- Cloud Run ERROR-severity logs 07:00Z+: one, the 07:31:49Z request-timeout line for that 504.
- Healthy now: 200s on `/login` at 07:38:17Z (ClaudeBot) and 07:31:39Z; requests after 07:32Z all 2xx/3xx.
- Prior mornings 06:30-08:30Z: 2 Nov 74 requests, 1 Nov 31, 31 Oct 55, 30 Oct 175, no 5xx on any. All 5xx since 27 Oct: 4x on 27 Oct 10:05Z (rawgrab), 4x on 3 Nov 01:47Z (rawgrab), this 1x.
- fuse-ui deploys: none since 2 Nov 16:12Z (GitHub deployments, gfs-bifrost/fuse-ui, newest entry).
- Outcome unchanged: monitor_mistuned, P4. Low volume (10 requests in 15m, almost all bots) makes one scanner timeout a 10% rate. Window clears about 07:52Z.
- Not established: instance count this morning; whether any authenticated operator session exists today (logs carry no user identity; none seen); dependency health (config-service, audit-service, Mongo, IdP) was not queried because no request failed other than the timed-out websocket probe.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793670966494899
- Monitor: https://app.datadoghq.com/monitors/303464815
