---
tags: [datadog-triage]
date: 2026-11-11
monitor: "[FUSE][Fuse API] Request latency p95 high"
service: fapi
business_id: DOCKBAY
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794381567643379"
opened_at: "2026-11-11T07:18:01Z"
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Fuse API p95 latency Warn then Alert: one DOCKBAY confirmation push spent 19.8 s in the fapi to connector webhook POST

## Fired
Monitor 302685721 (`avg(last_15m):default_zero(avg:fuse.request.latency.95percentile{service:api-gateway,environment:prod}) > 2000`, P3, `managed-by:terraform`, last modified 2026-09-15T04:58:48Z, thresholds warning 1000 and critical 2000 unchanged) went Warn at 07:18:01Z (value 1505.439; Slack post 07:19:27Z, thread parent ts 1794381567.643379) and Triggered at 07:19:01Z (value 2809.207; second Slack post 07:20:26Z, its own thread, ts 1794381626.664599). `getMonitor` overallState was still Alert at 07:28:30Z with no Recovered event. The message text says ">2s", the Warn line is 1000. `service:api-gateway` is Cloud Run `api-gateway-prod`, which is fapi (logs carry `service:rest_connector`).

## Investigation
- Value and route (`fuse.request.latency.*{service:api-gateway,environment:prod} by {businessid,flow,recordtype}`, 5-min buckets 06:00 to 07:25Z, p95 avg / true max / count): only `dockbay|confirmation|sales_order` was above 600 ms: 07:10 332 / 342 / n=2, 07:15 10,104 / 19,911 / n=2, 07:20 294 / 318 / n=3, 07:25 297 / 297 / n=1. Every other series: dockbay create sales_order 592 / 592 / n=7 (07:00), purdyfigg confirmation stock_adjustment 272 (n=1, 07:05), phlur create sales_order 105 (n=1, 06:05), master_data 1-4 ms, one N/A route 2 ms. Total requests per 5-min bucket: 06:00 3, 06:05 1, 06:35 1, 07:00 10, 07:05 1, 07:10 2, 07:15 2, 07:20 3, 07:25 1 (other buckets no data). The 10 s points behind the 07:15 bucket are 07:16:00 = 296.3 and 07:18:20 = 19,910.9; 10,104 is their mean. The metric has statsdInterval 10 s.
- The slow request (rest_connector logs, one correlationId = one request): `3ecdc409-d9b9-446b-a3f5-78d99939fde0`, DOCKBAY `POST /events/v1/confirmation/ready/sales_order`, 07:18:06.435 to 07:18:26.339 = 19,904 ms, returned 204, info logs only. Gaps: "Confirmation forwarded to connector" 07:18:06.441 to "Confirmation processed" 07:18:26.218 = 19,777 ms; processed to "Record published to topic" 120 ms. Other DOCKBAY pushes today (07:12, 07:14, 07:16, 07:20, 07:22, 07:24, 07:26): 314, 311, 290, 277, 276, 315, 291 ms (forward leg 135-159, publish gap 83-170). No DOCKBAY confirmation push in the logs between 06:00 and 07:12. The correlationId is a run id shared with collector_service, sftp_connector (STUBBLE) and PURDYFIGG made events, so it was not unique to this push.
- What the slow leg is (fapi source at deployed sha 007ad5c, `confirmation.service.ts`): `forwardToConnector` logs "forwarded to connector", then `axiosInstance.post(webhookUrl, ...)` (axios timeout 30000 ms, up to 3 attempts with 1 s / 2 s backoff, a failed attempt logs a warn event), and `deliverConfirmation` logs "processed" on success. `fuse.confirmation.forward.attempt` by attempt had only `attempt:1` (07:05 1, 07:10 2, 07:15 2, 07:20 1) and `fuse.confirmation.forward.failure` returned no series since 06:00, and the only warn logs 06:00-07:23Z are the 5 "Dependency degraded" lines (no "Confirmation forward attempt failed"), so the 19.8 s was a single successful attempt. The 10 Nov episode was a different step (publish gap 1.1-2.4 s).
- Pub/Sub: `gcp.pubsub.topic.send_request_latencies.avg` (microsecond per metric metadata), 5-min avg for `bifrost.prod.confirmation_made.v1`: 13.2 to 20.6 ms from 06:00, 15.2 ms at 07:15 (19-61 publish requests per full 5-min bucket from 06:05); confirmation_ready 17.0 ms at 07:15; no prod topic above 52 ms in any bucket 06:00-07:20 (max `snap_poll_customer.v1` 51.2 ms at 06:20).
- Cloud Run `api-gateway-prod` 06:30-07:20: instances active 0-0.6 plus idle 0.4-1.0 (about one), CPU util p95 0.010-0.026 apart from 0.167 at 06:35, memory util p95 0.41-0.47, pending requests 0, `fuse.coldstart.count` 1 at 06:35 and 0 after. `gcp.run.request_latencies.p95` 07:15 = 7,012 ms (n tiny, the same request).
- Errors, codes, duplicates: rest_connector logs 06:00 to 07:23: 219 info, 5 warn ("Dependency degraded, continuing in reduced capacity", 06:39-07:00, no businessId), 0 error; status 202 x14, 204 x8, 200 x1. Zero `@res.statusCode:[400 TO 599]` rest_connector logs in the last 24 h. Cloud Run request_count by class: 2xx at 07:00-07:20, 4xx 7 in total 06:35-06:55 (1, 3, 2, 1), none after 06:55, no 5xx series. DOCKBAY confirmation `Confirmation payload received` per correlationId since 06:00: 7 ids, each once (no redelivery or duplicate).
- Deploys: GitHub deployments since 2026-11-10T07:20Z. fapi af857f8 (created 13:08:39Z) and snap-adapter dd86e1a (13:14:24Z) are still `waiting`, never applied; fapi logs carry only version 007ad5c over the last 24 h (6,169 lines). snap-adapter afdb226 success 12:03:45Z; sftp-connector 91d70de success 14:00:01Z and 14:01:38Z (two deployments). No deployment since 10 Nov 07:20Z in config-service, collector, dedupe-service, shopify-connector, replay-service, wms-gateway, tracking-service, audit-service, core-infra, observability, bifrost-pubsub, snap-queue-polling-service. Newest deploy finished 17 h before the firing. Maintenance/: no record with a window on 10 or 11 Nov (latest window_start 2026-11-05T10:00Z). #bifrost-general since 10 Nov 13:15Z: only an Indu go-live note (16 Nov), nothing on the REST API, Pub/Sub or Snap.
- Still firing and trend: Alert at 07:28:30Z, no Recovered event. The last 4 DOCKBAY pushes (07:20-07:26Z) took 276-315 ms. A replay of the monitor (below) read 4,219 at 07:19 and 2,749 at 07:26; the 19.9 s sample stays in the 15-min window until about 07:33 (replay estimate, not observed).
- Flapping: monitor events (9 d): 4 Nov 17:47 Triggered, 18:04 Warn, 18:05 Recovered; 5 Nov 10:37 Warn, 10:39 Triggered, 10:52 Warn, 10:54 Recovered; 10 Nov 13:27 Warn, 13:35 Recovered; 11 Nov 07:18 Warn, 07:19 Triggered. Four episodes in 6.5 days, three reached critical. What set each off (true max per 5-min bucket and count): 4 Nov purdyfigg create master_data 18,530 ms n=1; 5 Nov dockbay create master_data 6,056 ms n=1; 10 Nov dockbay confirmation sales_order 1,934 ms n=3 and 2,563 ms n=2; 11 Nov dockbay confirmation sales_order 19,911 ms n=2. DOCKBAY confirmation, 4 Nov 07:20Z to now: 789 requests over 369 buckets with data, 9 buckets with max > 1 s (all on 9-11 Nov), 1 above 5 s and 1 above 10 s (today's). Nothing fired on 7 or 9 Nov (the Snap stall and the ilg005 hang).
- Monitor replay, 4 Nov 07:00Z to 11 Nov 07:24Z, 10,105 one-minute evaluations of `moving_rollup(default_zero(avg:fuse.request.latency.95percentile{service:api-gateway,environment:prod}), 900, 'avg')` as a proxy for the monitor (peaks 1,013 on 10 Nov and 2,802 today against real 1,012.8 and 2,809.2, and the same 4 warn episodes / 3 critical as the real events, but its minute timestamps differ by up to 5 min). 15-min request count (`sum:fuse.request.latency.count`): p50 2, p75 9, p90 22, max 72; at the peak of the four episodes it was 3, 2, 8 and 12. Results as episodes (minutes) at warn 1000 / critical 2000: current rule 4 (50) / 3 (39); `!flow:confirmation` 2 (40) / 2 (32); count >= 10 gate 2 (3) / 1 (2); count >= 20 gate 0 / 0; 1 h window 1 (61) / 0; `!flow:confirmation` plus count >= 10 gate 1 (1, 4 Nov 18:05Z) / 0.

## Not established
- Where DOCKBAY's webhook points and why it took 19.8 s: the `redirectUri` log attribute is a 65-char string that does not parse as an absolute URL and was not read further; the customer endpoint was not looked at.
- What the 7 Cloud Run 4xx responses at 06:35-06:55Z were (not in rest_connector logs).
- Whether Google Cloud had an incident (status feed not read this run).
- When the monitor recovers (not observed before this record was written); the exact monitor evaluation maths (the replay is a proxy).
- Recall of the proposed rule: no broad latency event occurred in the window to test it against.
- Config changes for DOCKBAY or config-service in the last 24 h (audit-service not queried).

## Outcome
P4, monitor_mistuned: one DOCKBAY confirmation push took 19.9 s (19.8 s of it the fapi to connector webhook POST, one attempt, 204, no retry, no errors) and pulled a 15-min average over 2 to 12 requests above both thresholds. Pub/Sub publish latency, Cloud Run and deploys are normal. Fourth episode in 6.5 days; recommendation (no change made): scope the monitor with `!flow:confirmation` and require at least 10 requests in the 15-min window, which would have fired 1 warn window (1 min) and 0 critical in the replay against 4 warn / 3 critical now. No ticket filed.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794381567643379
- Second post (Triggered 07:20:26Z): https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794381626664599
- Monitor: https://app.datadoghq.com/monitors/302685721
- Earlier records: 2026-11-04-fuse-api-request-latency-p95-high.md, 2026-11-05-fuse-api-request-latency-p95-high.md, 2026-11-10-fuse-api-request-latency-p95-high.md
