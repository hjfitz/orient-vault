---
tags: [datadog-triage]
date: 2026-11-05
monitor: "[FUSE][Config Service] config-service 5xx rate high (control-plane availability)"
service: config-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793880988205249"
opened_at: "2026-11-05T12:15:01Z"
severity_assessed: P4
flapping: false
outcome: real_minor
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# 12:15Z Warn: 5 of 216 config-service requests were 500s, all from the same external probe as the 12:09Z platform alert

## Fired
Monitor 302797201 (Warn, warning threshold 2, critical 5): `sum(last_15m)` of gcp.run.request_count 5xx / total for config-service-prod. Value at trigger 2.315, which is 5 / 216 over 12:00-12:15Z (metric query, 1-minute buckets).

## Investigation
- Counts: Datadog metrics `gcp.run.request_count{service_name:config-service-prod}`, 12:00-12:15Z: 216 total, 5 5xx (all response_code:500, all in the 12:10 bucket). 5/216 = 2.315, matching the notified value. 11:55-12:17Z by class: 2xx 197, 4xx 54, 5xx 5. 5xx after 12:11Z: 0.
- Same 500s as the 12:09Z platform alert: request logs `service:config-service @res.statusCode:[500 TO 599]` since 11:45Z grouped by client IP: 5 results, all `82.165.94.38` (behind the LB 34.117.76.219). Paths: /run, /code/blocks/exec/start, /code/blocks/exec/code, /api/v1/code/blocks/exec/start, /api/v1/code/blocks/exec/code. Same 5 "Error unhandled" logs (error.type entity.parse.failed, statusCode 500) at 12:09:04-05Z, bodies a script that downloads and runs a payload from badmonner.s.gy.
- That IP, full list (log search, 29 Oct to now): 12 requests, all 12:09:04.369-12:09:05.109Z: 6 POST (5 x 500, POST / 401), 2 PUT (shell_*.jsp, s*.aspx, 401), 4 GET (/, /, /foo.jsp, /crumbIssuer/api/json, all 401). 0 2xx. (The sibling record's "8 requests" counted write-method requests only; the GETs are extra and also 401.)
- Nothing since: write-method requests (POST/PUT/PATCH/DELETE) from any IP after 12:10Z: 0 (log aggregate to 12:17:38Z). config-service error-status logs after 12:10Z: 0. 5xx metric after 12:11Z: 0. The probe IP made no request after 12:09:05Z.
- Control-plane callers: the only 5xx by client IP is 82.165.94.38. Internal callers (34.34.246.x, 34.89.118.145) have 2xx on every route they hit. Their only non-2xx are 404s on GET /api/v1/business/{ESCENTRIC,SAIRA,PURDYFIGG,STUBBLE,EPARFUM}/ddp/rules (80 requests, 34.34.246.215 mostly; 5 sampled all 404, axios user agent). Not 5xx, so not counted by this monitor.
- Monitor history: only one Warn event in 7 days (this one; events search `source:alert`). Monitor was edited 3 Nov 14:33Z (message text, Mongo to Cloud SQL wording). No change_tracking events for config-service in the last 6h. 5xx metric over 7 days: 2 on 3 Nov 13:58Z, 5 on 5 Nov 12:10Z.
- Volume context: config-service takes about 216 requests per 15 minutes, so 5 failures is 2.3%; 11 would reach the 5% critical threshold.

## Not established
Whether anything ran on the service or reached the network (no host or egress logs checked). Whether config-service is meant to be internet-reachable (ingress config not read). Why a body-parse failure returns 500 and not 400 (mechanism not read in code). Whether the ddp/rules 404s are expected (only 5 sampled, response bodies not read). The cause of the 2 5xx on 3 Nov 13:58Z (not queried). When the monitor recovers (depends on the 5 failures leaving the 15m window; not observed).

## Outcome
Real minor, P4. Same 12:09Z hostile probe, no 2xx, no failure seen by an internal caller. The 5xx rate is a hostile client producing 500s on unparseable bodies at a low request volume, not control-plane unavailability. Leads, not findings: return 400 for body-parse failures, and consider a minimum request count or excluding unauthenticated-client 5xx on this monitor. Not ticketed here.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793880988205249
- Monitor: https://app.datadoghq.com/monitors/302797201
- Related: Monitors/2026-11-05-platform-elevated-prod-error-rate-config-service-probe-1209.md
