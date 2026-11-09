---
tags: [datadog-triage]
date: 2026-11-04
monitor: "[FUSE][Fuse API] Request latency p95 high"
service: fapi
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793814507743309"
opened_at: "2026-11-04T17:47:01Z"
resolved_at: "2026-11-04T17:50:00Z"
minutes_spent: 3
severity_assessed: P4
flapping: false
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# Fuse API p95 latency alert: one 680-record PURDYFIGG master-data upload took 18.5s

## Fired
Monitor 302685721 (`avg(last_15m):default_zero(avg:fuse.request.latency.95percentile{service:api-gateway,environment:prod}) > 2000`, P3, Terraform-managed) fired at 17:47:01Z with metric value 2198.1. Datadog tags the Fuse API as `service:api-gateway` (metric) and `rest_connector` (logs); Fuse MCP name is fapi.

## Investigation
- The metric has one data point above 1s in the last 3h: `businessid:purdyfigg` at 17:45, p95 18530ms, request count 1 (`queryTimeseriesData` per businessid, 1-min interval). The other businesses' points in that window were 107ms (phlur 17:36), 272ms (dockbay 17:22).
- That point is one request: `POST /api/v2/master-data` for PURDYFIGG, correlationId `b2d26a97-65c7-4092-b32b-c97ccf2682a2`. Log "Received 680 master-data records" at 17:45:01.465Z, the 202 response logged at 17:45:19.994Z (about 18.5s). It succeeded with 202.
- rest_connector logged 3 API request lines in 17:20-17:55Z in total (this one and two PHLUR sales-orders at 17:36), so a single request is the whole p95 sample.
- Per-record "Record published to topic" (680) ran from 17:45:01.691Z to 17:45:19.991Z, i.e. the response waited on the batch.
- Downstream for that correlationId: 535 "Entity created in SNAP" (snap_adapter, last at 17:46:37.58Z), 145 "Record dropped" (dedupe_service), 535 + 145 = 680; 680 "Record stored" (collector). No failure messages were in that correlationId's log summary.
- Flapping: 4 firing episodes in 30 days (alert events 2026-10-07 07:00Z, 10-20 09:19Z, 10-28 16:56Z, 11-04 17:47Z), each a single episode that recovered (recoveries seen 10-07 07:15Z, 10-20 09:39Z, 10-28 17:08Z). Not repeated firing within a day.
- Volume context: 6635 requests in 14 days on the metric (about 470/day), and only 3 API requests logged in the 35 min around the alert.
- Monitor still Alert at 17:50Z (last check). The firing point leaves the 15m window on its own.
- The 17:20Z api-gateway prod deploy (commit 09ac2c3) preceded the alert; requests after it at 17:22 and 17:36 were 272ms and 107ms.

## Not established
- Why the 680-record batch took 18.5s (the logs show the publishes spread across the 18s, not what bounds that).
- What caused the earlier episodes on 10-07, 10-20 and 10-28 (their latency sources were not queried; a dockbay point of 5178ms at 10-28 16:50 sits next to the 10-28 firing but I did not look into it).
- Whether the 17:20Z deploy has any effect on bulk-upload latency (only two later single-record requests, both fast, were seen).
- Monitor recovery, not yet observed at time of writing.

## Outcome
P4, monitor_mistuned: a single bulk upload, accepted with 202 and fully processed downstream, was enough to trip a p95 monitor on a metric that carries very few requests. No customer impact seen. A retune is worth considering (a minimum request count, or a longer window), but no change was made and no ticket filed.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793814507743309
- Monitor: https://app.datadoghq.com/monitors/302685721
