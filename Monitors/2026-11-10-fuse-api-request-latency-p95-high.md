---
tags: [datadog-triage]
date: 2026-11-10
monitor: "[FUSE][Fuse API] Request latency p95 high"
service: fapi
business_id: DOCKBAY
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794317310721809"
opened_at: "2026-11-10T13:27:01Z"
resolved_at: "2026-11-10T13:36:06Z"
minutes_spent: 9
severity_assessed: P4
flapping: false
outcome: self_resolved
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# Fuse API p95 latency warn: three DOCKBAY confirmation pushes spent 1.1-2.4s publishing to Pub/Sub, back to normal by 13:28Z

## Fired
Monitor 302685721 (`avg(last_15m):default_zero(avg:fuse.request.latency.95percentile{service:api-gateway,environment:prod}) > 2000`, P3, Terraform-managed, last modified 2026-09-15) went to Warn at 13:27:01Z with value 1012.769. Its thresholds are warning 1000 and critical 2000 (`getMonitor` options), so this was the warning line, not the 2s the message text names. `service:api-gateway` is Cloud Run `api-gateway-prod`, which is fapi (logs carry `service:rest_connector`); Fuse MCP has no `rest_connector` service, `fapi` is the REST API.

## Investigation
- Which route and customer: the metric by `businessid,flow,recordtype,channel` over 12:45-13:30Z has one slow series, `dockbay / rest / confirmation / sales_order` (5-min buckets: 13:00 959, 13:05 380, 13:10 453, 13:15 322, 13:20 1185, 13:25 1562 ms; count 2-3 per bucket). That is `POST /events/v1/confirmation/ready/sales_order`, a Pub/Sub push into fapi (rest_connector logs, user agent APIs-Google). The other two series in the window (dockbay create sales_order max 135 ms, a master_data create at 1 ms) were fast.
- Same 6h window, every business/flow/recordtype (`fuse.request.latency.*`, scalar by group, today vs each of the previous 7 days): only DOCKBAY confirmation sales_order was above 1s (avg p95 391, max 2563, n=139; yesterday 348/1117/146; d-4 345/872/98; d-5 331/820/57; d-6 398/800/48; d-7 336/715/102; no data on 7 and 8 Nov). The next highest max today was PHLUR confirmation sales_order 923 ms, n=1 (07:50Z).
- Per-request timing from rest_connector logs (DOCKBAY `@flow:confirmation`, `custom.timestamp` in ms, first log to the POST line): last 6h n=139, p50 325, p95 662, p99 2348, max 2557, 5 requests over 1s (11:50:06 1018, 13:02:04 2348, 13:20:05 1345, 13:24:05 1927, 13:26:05 2557) and 2 over 2s. Yesterday same window n=146, p50 310, p95 568, p99 673, max 1113. Seven days ago (3 Nov, same window) n=102, p50 301, p95 601, p99 662, max 707.
- The metric per 5-min bucket equals the mean of these request durations (13:20 bucket: mean of 1345, 266, 1927 = 1179 vs metric 1185; 13:25 bucket: mean of 2557, 555 = 1556 vs 1562). So the alert is a mean over 2-3 requests, not a p95 over a population. All-route Cloud Run view (`gcp.run.request_latencies.p95/.p99`, `samplecount`): 13:20 p95 568 ms n=4, 13:25 p95 1040 ms n=1, other 5-min buckets in 6h n=1-9 except 20-34 at the top of each hour.
- Where the time goes (log gaps for the three slow pushes 13:20:05 / 13:24:05 / 13:26:05): "Confirmation processed" to "Record published to topic" took 1138 / 1774 / 2397 ms. In fapi source at deployed sha 007ad5c that gap is `emitConfirmationMade`, i.e. `await topic.publishMessage(...)` to the confirmation_made topic. Same gap over the 6h: p50 149, p95 325; max yesterday 429, d-7 367. The webhook leg ("forwarded to connector" to "processed") was 200 / 145 / 152 ms (p50 156). Connector lookup was cache (3-4 ms) or a config API fetch (about 70 ms). The 13:02:04 outlier was a different step: webhook leg 2294 ms, publish 49 ms.
- Pub/Sub side: `gcp.pubsub.topic.send_request_latencies.avg` (microseconds per metric metadata) for `bifrost.prod.confirmation_made.v1`, 5-min max: 12.5-19.2 ms until 13:00; 137 ms 13:05; 310 ms 13:10; 143 ms 13:15; 135 ms 13:20; 99 ms 13:25; 20 ms 13:30. Publish requests 24-57 per 5 min. `confirmation_ready.v1` and `confirmation_data_failure.v1` stayed near 15 ms.
- Traces: none. `aggregate_spans` for api-gateway / rest_connector / fapi returned 0 spans in 6h, and none of the Fuse Cloud Run services appear in the span service list for the last hour. Timing above is from logs.
- Errors and codes: all rest_connector request lines in 6h were 2xx (204 on the push endpoints, 202 on `/api/v2/*`); log status counts 2580 info / 11 warn (yesterday 2496 / 12), zero error. The 11 warns (07:39-08:46Z redis "Dependency degraded"; 11:03 and 12:02 "Record batch rejected"; 11:26 and 11:44 WILDSMITH "could not be routed/delivered") are all before the spike and none is DOCKBAY confirmation. Each slow push logged "Confirmation made event emitted" and a 204.
- Duplicates: 150 push lines in 6h; the six repeated correlationIds each pair two different businesses 1-2s apart (shared run id), none is the same business twice. DOCKBAY confirmation correlationIds 12:50-13:34 are each unique (one 8-log group per request).
- Cloud Run `api-gateway-prod` (6h): instances about 1 (active+idle 0.3-1.4), CPU util p95 at most 0.04 (0.02 at 13:20-13:30), memory util 0.44-0.47, pending requests 0, one cold start at 08:40Z (startup p95 15.3s) and none after. Logs show only version 007ad5c over the last 30h.
- Deploys, last 24h: GitHub deployments for fapi, config-service, collector, dedupe-service, snap-adapter, sftp-connector, shopify-connector, bifrost-pubsub, core-infra, observability, audit-service, tracking-service, wms-gateway, replay-service. Only fapi af857f8 (13:08:41Z, status waiting, not applied, running version unchanged) and snap-adapter afdb226 (success 12:03:45Z, matches the 12:04:48Z post) and dd86e1a (waiting since 13:14:26Z). fapi 007ad5c last went live 6 Nov 09:56:58Z. `get_change_stories` api-gateway 9 Nov 13:00Z to 10 Nov 13:31Z: none.
- Snap link tested, not found: the push request has no Snap call (steps: payload received, connector resolve, forward to webhook, processed, publish, made-event, ack, POST line). DOCKBAY confirmation latency between snap-adapter going live (12:03:45Z) and 13:15Z stayed 171-603 ms per 5-min bucket (603 is the 13:00 hourly burst). p50/p95 today 325/662, 9 Nov 310/568, 3 Nov 301/601: no step since the 7 Nov Snap stall. There is no DOCKBAY confirmation data for 9 Nov 19:30-20:40Z or 7 Nov 04:00-05:30Z, so the ilg005 hang and the 4.07s stall cannot be compared against this route.
- Flapping and history: monitor alert events (7d) show episodes 4 Nov 17:47Z, 5 Nov 10:37Z and today 13:27Z; one Warn so far today. Earlier records 2026-11-04 and 2026-11-05 were single bulk master-data uploads (PURDYFIGG, DOCKBAY), a different cause; both suggested a retune and the monitor is unchanged since 15 Sep.
- Maintenance and chat: no Maintenance/ record with a window on 9 or 10 Nov; #bifrost-general since 9 Nov 17:00Z has the 9 Nov 22:20Z ilg005 note and nothing about Pub/Sub or the REST API. The Google Cloud status incidents feed (first 100k of 292k chars read via WebFetch) showed none on 10 Nov; latest seen was 20 Oct.
- Now: 1-min metric 13:28 562, 13:30 581, 13:32 456, 13:34 416, 13:35 228 ms; DOCKBAY pushes at 13:30:06 / 13:32:05 / 13:34:05 took 572 / 448 / 409 ms (publish gap 251 / 249 / 223 ms). `getMonitor` overallState was OK at 13:36:06Z (it was still Warn when polled at about 13:35, trailing 15m average 1016).

## Not established
- Why the confirmation_made publish was slow for those three pushes, and why the topic-level latency rose from 13:05Z. The topic metric aggregates every publisher (fapi, sftp-connector, shopify-connector and others); which of them contributed was not queried, and Google status was only partly read.
- Whether the 13:02:04 DOCKBAY webhook leg (2294 ms) was the customer's endpoint; the destination was not looked at.
- Config changes for DOCKBAY or config-service in the last 24h (Fuse audit-search not used; config reads can return secrets). Only deploys and Datadog change stories were checked.
- Whether DOCKBAY's Snap host (ilg00x) matters: not looked up, as the request path has no Snap call.
- Whether fapi 007ad5c behaves differently from earlier versions on publish latency (only 30h of version tags checked).

## Outcome
P4, self_resolved: three of 139 DOCKBAY confirmation pushes in 6h spent 1.1-2.4s in the Pub/Sub publish to confirmation_made, all returned 204 and emitted their made-event, no 4xx/5xx and no duplicates; the route was back to 250 ms publish gaps from 13:28Z and the monitor read OK at 13:36Z. The Warn is the mean of 2-3 requests per 5-min bucket crossing the 1000 ms warning line (the message text says 2s). Third episode of this monitor in 7 days on a different cause; the retune suggested on 4 and 5 Nov (minimum request count or longer window) still applies. No change made, no ticket filed. No link to the snap-adapter 12:03Z deploy or the 7 and 9 Nov Snap host problems found.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794317310721809
- Monitor: https://app.datadoghq.com/monitors/302685721
- Earlier records: 2026-11-04-fuse-api-request-latency-p95-high.md, 2026-11-05-fuse-api-request-latency-p95-high.md
