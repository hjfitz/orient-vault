---
tags: [datadog-triage]
date: 2026-11-11
monitor: "[FUSE][Config Service] config-service 5xx rate high (control-plane availability)"
service: config-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794375084742799"
opened_at: "2026-11-11T05:30:01Z"
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: done
---
# config-service 5xx monitor (P2) tripped by 5 hostile-client 500s at overnight volume: 5 of 63 responses, same scanner burst as the Platform alert

## Fired
Monitor 302797201 (priority 2, Terraform-managed, critical 5, warning 2, notify_no_data false): `sum(last_15m)` of gcp.run.request_count 5xx / total for service_name:config-service-prod, times 100, over 5. Triggered 05:30:01Z, Slack post 05:31:24Z (parent ts 1794375084.742799), value 7.937. The message blames "Cloud SQL unreachable"; that lead was tested and refuted below. The monitor counts every route and caller and has no minimum request count.

## Investigation
- 1 Value: gcp.run.request_count by response_code_class (queryTimeseriesData, 1 min), 05:15-05:30Z buckets: 47 2xx + 11 4xx + 5 5xx = 63; 5/63 = 7.937, equal to the notified value.
- 2 Counts per minute 04:30-05:31Z: 231 requests (about 4/min) and 5 5xx, all in the 05:25 bucket. Same window yesterday (10 Nov 04:30-05:32Z): 207 requests, no 5xx series. 14-day hourly 5xx: 3 Nov 13Z 2, 5 Nov 12Z 5, 6 Nov 10Z 1, 6 Nov 19Z 2, 7 Nov 15Z 5, 11 Nov 05Z 5. Daily totals 16k-33k requests, so the same 5 failures are far below 5% in the daytime.
- 3 The 5 failures: config-service error logs 04:30-now: 5, all `Error unhandled`, error.type entity.parse.failed (underlying status 400), logged statusCode 500, 05:24:04Z; POST /run, /code/blocks/exec/start, /code/blocks/exec/code, /api/v1/code/blocks/exec/start, /api/v1/code/blocks/exec/code. Bodies are JSON-shaped strings carrying a shell command (download and run a payload). 5 error logs = 5 5xx in the metric.
- 4 Client: request logs `@res.statusCode:[500 TO 599]` since 05:15Z: 5, all `@request.client.ip` "82.165.94.38, 34.117.76.219". That minute (05:24) held 12 logged requests, all from that chain. Same prefix over 15 days: 36 requests = 21 x 401 + 15 x 500, 0 x 2xx, 12 on each of 5, 7 and 11 Nov (hourly buckets 5 Nov 12Z, 7 Nov 15Z, 11 Nov 05Z). Only 5xx source in the last 24 h.
- 5 Mechanism (git show origin/main; `git diff 6b73684 origin/main -- code/src` is empty, 6b73684 is the version on every log line): bootstrap/app.ts mounts `bodyParser.json` before `buildAuthMiddleware()`; exceptions/http/logger.ts `getStatusCode` returns 500 for anything that is not one of the service's own exception classes, so body-parser's 400 falls to the `UnhandledError` branch and a 500. It failed at parsing, before auth and any handler.
- 6 Reachability: iac/projects/config-service/cloud-run.tf `ingress = "INGRESS_TRAFFIC_ALL"`, iam.tf run.invoker includes `allUsers`; app-level auth answered 401 to the scanner's other probes (GET /, /foo.jsp, /crumbIssuer/api/json).
- 7 Cloud SQL (the monitor's suggested cause): fuse.postgres.up avg/min/max 1 over 64 points 04:30-05:36Z; gcp.cloudsql.database.up min 1 (hourly, 24 h) and 1 over 60 points; instance config-service-prod CPU max 0.143, memory max 0.305, num_backends max 3.98 over 24 h; fuse.postgres.latency.95percentile max 342.7 ms in 5-min buckets since 04:30Z (393 ms over 24 h, `.max` 398 ms). "Dependency connection failed" logs: none since 04:30Z, last 01:32:05Z. Over 15 days 62 (45 "Postgres ping took longer than 2000ms", 17 "read ECONNRESET"), none at 05:2x. These were already triaged 5-6 Nov (see Links), so the brief's "once, 9 Nov, never investigated" is wrong.
- 8 Cloud Run: one revision, config-service-prod-00071-czr, for 24 h (max instance_count by revision, hourly 0.57-1.17); request_latencies.avg 5.6-22.0 in the window; container CPU p99 max 0.025, memory p99 max 0.54 over 24 h.
- 9 Blast radius: `@domain:fuse status:error` 04:30-05:37Z: config-service 5, no other service. config-service request logs since 05:15Z by @res.statusCode: 200 x80, 401 x9, 404 x6, 500 x5. The 404s are GET /business/{id}/ddp/rules; shopify-connector logs them as warn "DDP rules unavailable" (14 PURDYFIGG + 3 SAIRA, all 404). Pub/Sub oldest-unacked, top 5 subscriptions, max over 90 min: 3.6 s (sftp-connector create_acknowledge), 0.6 s snap_adapter create_record_sales_order. replay-list-failures (production, createdAt 2026-11-11): 1, DOCKBAY sales_order UK-914809, 00:02:49Z, ShipAddress.City over 30 chars, attempts 0, snap-adapter wms_precheck; unrelated and before the alert.
- 10 Changes in 24 h: config-service GitHub deployments last are 6b73684 (5 Nov 15:06:16Z) and 25a4943 (5 Nov 15:34:56Z, status `waiting`); no config-service push or apply run since (only scheduled runs). Prod deployments in the last 24 h across 22 Fuse repos queried: fapi 10 Nov 13:08Z, sftp-connector 13:55Z and 14:00Z, snap-adapter 12:01Z and 13:14Z, fuse-ui 13:07Z. get_change_stories config-service 10 Nov 04:00Z-11 Nov 05:40Z: none. Datadog resource_changes: "gcp_sql_database_instance config-service-prod was updated" 10 Nov 22:32:59Z (settings, settings_version) and the dev instance 22:38:40Z; cause not found. Maintenance/ vault: no record with a window on 10-11 Nov and none naming Cloud SQL or config-service.
- 11 Google Cloud status: https://status.cloud.google.com/incidents.json fetched 05:35Z: 8 incidents in the feed, newest began 2026-10-20, none open.
- 12 Flapping: monitor events (source:alert, 30 d): Warn 5 Nov 12:15:01Z, Warn 7 Nov 15:22:01Z, Triggered 11 Nov 05:30:01Z. Same 5-log burst each time (parse-failure logs 15 in 15 days, 5 each in the 5 Nov 12Z, 7 Nov 15Z, 11 Nov 05Z hours). 5 of about 216 requests in daytime reached Warn only; 5 of 63 overnight reaches critical. Prior records for the same monitor and scan: [[2026-11-05-config-service-5xx-rate-high-probe-1215]].
- 13 Relationship to the Platform alert (monitor 180072217, thread 1794374746.926179, handled separately, not replied to here): same 5 log lines (05:24:04Z) matched that monitor's 2-minute query; `@domain:fuse status:error` 05:20-05:30Z by service: config-service 5 only. Record read: [[2026-11-11-platform-elevated-prod-error-rate-config-service-scanner-0524]].
- 14 Waypoint: `wp stale config-service`: architecture.md 16 commits behind, interfaces.md 21, operations.md 38, overview.md 34; known-context.md exempt but verified 2026-08-24 (pre-Cloud SQL). Programme `Config Service Cloud SQL`: E2 prod cutover to Postgres about 2026-11-03T14:04Z, E3 soak not started, R11 monitors live. Relied on code and live data, not those docs.
- 15 Recovery: last read of monitor 302797201 at 05:41:41Z (getMonitor, groupStates all): overall Alert, group `*` lastTriggeredTs 1794375001 (05:30:01Z), lastResolvedTs 1794065101 (7 Nov 15:25:01Z, from the state field, not a Slack post). Trailing 15 minutes from the same read (gcp.run.request_count, 05:26:41-05:41:41Z): 38 2xx, 6 4xx, 0 5xx, so the 05:25 bucket had left the window by my own count while the monitor had not yet re-evaluated. Earlier reads, same state: 05:36:50Z Alert (window 5 5xx), 05:38:37Z Alert (43 2xx, 9 4xx, 5 5xx = 8.8%). No 5xx bucket after 05:25 up to 05:41Z. Recovery itself not observed; record left `status: open` for that reason.

## Not established
- That nothing executed on config-service or reached the network: the bodies failed JSON parsing and no request from the IP got a 2xx, but no host or egress logs were read.
- Whether config-service is meant to be internet-reachable (ingress and invoker are open in iac; intent, Cloud Armor and LB rules not read) or whether the IP is blocked anywhere.
- Cause of the Cloud SQL instance "updated" resource-change events of 10 Nov 22:32:59Z (prod) and 22:38:40Z (dev). Not tied to the 05:24 requests (Cloud SQL up stayed 1), but unexplained.
- Why the 62 chronic Postgres connection errors (15 days) happen. Not part of this alert; triaged 5-6 Nov without a cause.
- Causes of the 5xx on 3 Nov 13Z, 6 Nov 10Z and 6 Nov 19Z (not queried).
- GitHub deployments for fuse-mcp-server, carrier-proxies, terraform-modules and ilg-platform-core-infra (API returned 404).
- Per-consumer counts of config reads served from cache versus the API: not queried. No consumer logged a config-fetch error other than the DDP-rules 404s.
- Whether the Waypoint config-service explainers still match the code (stale).

## Outcome
P4 monitor_mistuned. Five 500s from one scanner IP, on malformed JSON, tripped a 5% ratio that has no minimum volume, at a quiet hour. Control plane kept serving (200 x80, no 5xx from any real caller), Cloud SQL healthy, nothing held or lost. It will re-trip on any overnight repeat of the scan (3 bursts so far). Leads, not applied: return 400 and log at warn for `entity.parse.failed` in config-service; add a request-count floor or exclude the parse failure in the monitor (observability repo, `managed-by:terraform`); decide whether the Cloud Run ingress should be open. No ticket filed, nothing written, replayed, retried or restarted.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794375084742799
- Monitor: https://app.datadoghq.com/monitors/302797201
- Prior: [[2026-11-05-config-service-5xx-rate-high-probe-1215]], [[2026-11-07-platform-elevated-prod-error-rate-config-service-scanner-1514]], [[2026-11-06-platform-elevated-prod-error-rate-config-service-postgres-0823]]
