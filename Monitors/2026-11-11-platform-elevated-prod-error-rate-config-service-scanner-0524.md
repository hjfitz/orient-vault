---
tags: [datadog-triage]
date: 2026-11-11
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: config-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794374746926179"
opened_at: "2026-11-11T05:24:37Z"
resolved_at: "2026-11-11T05:31:00Z"
minutes_spent: 6
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# Error-rate monitor tripped by the same 5 malformed-JSON scanner probes on config-service (third time: 5, 7, 11 Nov); not snap_adapter

## Fired
Monitor 180072217 (log alert, more than 2 matching error lines in 2m). Triggered 05:24:37Z, Datadog Recovered event 05:26:37Z, monitor status OK when re-read at about 05:30Z. Alert thread C099WKQTE8G / 1794374746.926179, no replies when read.

## Investigation
- 1 Monitor query run for 05:22:37-05:24:38Z (search_datadog_logs, extra_fields all): 5 lines, all config-service "Error unhandled", all 05:24:04.333-.475Z. Same query grouped by service and status over 04:30-07:00Z: 5 lines, config-service only. No snap_adapter, snap-polling-service, shopify-connector, tracking-service or any other service line matched.
- 2 The 5 lines: error.type `entity.parse.failed` (status 400), POST to /api/v1/code/blocks/exec/code, /code/blocks/exec/code, /api/v1/code/blocks/exec/start, /code/blocks/exec/start and /run. Each body is a JSON-shaped string carrying a shell command that downloads and starts a crypto-miner. Fuse MCP lookup-endpoints (5 Nov record) found no such routes on config-service.
- 3 Request logs of the same second (config-service info lines, 05:24:03.8-05:24:04.6Z): one client IP 82.165.94.38 (behind Google LB 34.117.76.219). 12 requests: 5 x 500 (the POSTs above) and 7 x 401 (GET /, GET / with a Shellshock-style user agent, POST /, GET /foo.jsp, GET /crumbIssuer/api/json, PUT /shell_*.jsp, PUT /s*.aspx). Query on `@request.client.ip` for that IP, 4-11 Nov: exactly 12 requests on each of 5, 7 and 11 Nov (7 x 401, 5 x 500), none on other days, 0 responses 2xx.
- 4 Same signature on the earlier firings: parse-error burst at 5 Nov 12:09:05Z and 7 Nov 15:14:15Z; monitor Triggered events at 12:09:37Z and 15:14:37Z (search_datadog_events). See [[2026-11-05-platform-elevated-prod-error-rate-config-service-probe-1209]] and [[2026-11-07-platform-elevated-prod-error-rate-config-service-scanner-1514]]. Monitor event count 5-11 Nov (alert + recovery): 67.
- 5 Mechanism, config-service at the running commit 6b73684 (git show): `bodyParser.json` is mounted before `buildAuthMiddleware()` in bootstrap/app.ts, so a malformed body fails before auth. `errorMiddleware` maps only the service's own exception classes to 4xx; body-parser's error falls through to the generic branch, which `logError` logs as `ErrorEvent.UnhandledError` (error level) and the response was 500 (info log lines "POST ... - 500 Internal Server Error").
- 6 No customer impact seen: config-service info logs 05:24:05-05:34Z by status: 200 x39, 404 x2, no 5xx. Cloud Run 4xx count 1-6 per 5 min over 04:45-05:45Z.
- 7 Deploy / change: config-service has been on 6b73684 (all 26,675 prod log lines 10 Nov 04:00Z - 11 Nov 05:25Z carry that version); latest GitHub terraform-prod deployments are 6b73684 (5 Nov 15:06Z) and 25a4943 (5 Nov 15:34Z, status waiting). get_change_stories for config-service 10 Nov 04:00Z - 11 Nov 06:00Z: none. So no config-service change in 24 h.
- 8 Snap, since the SNAP_TRANSPORT_GUARD=adapter deploy (snap_adapter afdb226, serving from 10 Nov 12:04:31Z, still the only version on 11 Nov 05:25Z): snap_adapter and snap-polling-service error/warn logs 10 Nov 11:00Z - 11 Nov 07:30Z (excluding three known snap-polling warn messages): 11 snap_adapter error lines, every one transient=false (cancelled_in_wms 1, schema_validation 5, snap_api_error 4... see query), last at 11 Nov 00:00Z. No slot_timeout, circuit_open or transient=true lines. snap.breaker.state hourly max 0 in all 18 hourly points 10 Nov 12:00Z - 11 Nov 06:00Z; snap.breaker.rejected and snap.circuit_opened returned no series; snap.slot_queue_depth hourly values 0-13.5; snap.request.latency.max per 5 min 04:45-05:45Z: 800-1,974 ms (two empty buckets); prod snap_adapter subscriptions oldest-unacked max 0.6 s (create_record_sales_order), others 0, 04:45-05:45Z. The guard did not fire in this window, so the half-open probe was not exercised and not assessed.
- 9 snap_adapter dd86e1a: GitHub deployment 10 Nov 13:14:24Z has one status, `waiting` (no success), and Datadog shows only afdb226 serving. sftp-connector 91d70de: GitHub terraform-prod deployments 10 Nov 13:55:50Z and 14:00:01Z both `success`, but sftp_connector prod logs carry version e17c9ca up to 05:25Z on 11 Nov (mismatch not explained).
- 10 Maintenance vault: no record with a window on 10 or 11 Nov (latest window_starts: 4 Nov 09:00Z test DBs, 5 Nov 10:00Z emergency patch). #bifrost-general since 10 Nov 00:00Z: no ILG/Snap notice. #snap-wms: last message 10 Nov 12:41Z (ILG asking about the 9 Nov 20:02-22:30Z DB5 slowness), nothing since.
- 11 Held in replay-service (replay-list-failures production, sales_order/purchase_order/master_data): 11 Nov, 1: DOCKBAY UK-914809, 00:02:49Z, `ShipAddress.City - Too big: expected string to have <=30 characters`, create.wms_precheck, attempts 0, replayed false. 10 Nov, 13: DOCKBAY 5, ESCENTRIC 4, SAIRA 1, PURDYFIGG 1, SPORTLUX 1, STUBBLE 1 (counts by reading the list), all attempts 0, all data-validation rejections (City or Name too long, SKU/Carrier/Unit not found, Line1 mandatory, SupplierRef length). None transient, none are retries-exhausted. Not related to this alert (the monitor excludes snap_adapter transient=false).
- 12 No transient snap_adapter failure in the window, so no PRODDETAIL attachment check was due and none was run. No Snap host was implicated, so no timed probe was run.
- 13 Jira: FUSE text search since 1 Oct for config-service with malformed/parse/scanner/probe/400 returned 7 unrelated tickets; orient-search found nothing. No ticket exists for the 500-on-malformed-body behaviour.

## Not established
- Whether anything executed on config-service or reached the network: the bodies failed JSON parsing and no request got a 2xx, but no host or egress logs were checked.
- Whether config-service is meant to be internet-reachable (ingress / Cloud Armor config not read).
- Whether support already knows about the held records in 11 (list read at about 05:30Z; attempts 0 on all; later holds and pick/pack/confirmation holds not examined).
- The sftp_connector deployed-version mismatch in 9.
- gcp.run.request_count 5xx returned no series although five 500 responses are logged, so that metric was not used.
- Whether the source IP is blocked anywhere (Cloud Armor / LB config not read).

## Outcome
P4 monitor_mistuned, third occurrence from one scanner IP and payload. The scan itself is harmless to customers (no 2xx, config-service kept serving 200s). The monitor counts the resulting error-level "Error unhandled" lines, five in under 200 ms, which exceeds the threshold of 2. snap_adapter and the new transport guard were not involved. Leads, not findings: return 400 and log at warn for body-parse errors in config-service, and/or exclude `entity.parse.failed` from the monitor query (monitor is Terraform-managed, `managed-by:terraform`, so the change goes in the observability repo). Nothing retried, released, replayed or written. No ticket filed here.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794374746926179
- Monitor: https://app.datadoghq.com/monitors/180072217
- Prior: [[2026-11-05-platform-elevated-prod-error-rate-config-service-probe-1209]], [[2026-11-07-platform-elevated-prod-error-rate-config-service-scanner-1514]]
