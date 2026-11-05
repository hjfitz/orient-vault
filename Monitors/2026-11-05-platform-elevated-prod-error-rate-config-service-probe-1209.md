---
tags: [datadog-triage]
date: 2026-11-05
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: config-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793880641852199"
opened_at: "2026-11-05T12:09:37Z"
severity_assessed: P4
flapping: true
outcome: real_minor
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# 12:09Z firing: 5 config-service "Error unhandled" from one external IP POSTing malformed-JSON exploit probes; not the slot-timeout pattern

## Fired
More than 2 error-level domain:fuse logs in 2m. Different cause from the 2 and 3 Nov firings (snap_adapter slot_timeout): zero slot-timeout logs today.

## Investigation
- Monitor query, alert window 12:07:37-12:09:37Z (Datadog log aggregation by service): 5 matches, all config-service. 00:00-13:45Z today the monitor query matches only config-service 5 (all 12:09:04-05Z) and replay_service 1 (11:43:24Z "Failed to decode param '%C0'", a malformed URL). Nothing matched after 12:10Z. Monitor recovered 12:11:37Z (search_datadog_events).
- The 5 errors: "Error unhandled", error.type entity.parse.failed (status 400), body a malformed JSON string containing `import os;os.system(...)` that downloads a payload from badmonner.s.gy and starts an xmrig-style miner. Paths: POST /run, /code/blocks/exec/start, /code/blocks/exec/code, /api/v1/code/blocks/exec/start, /api/v1/code/blocks/exec/code. correlationIds 082ec998..., 0fbc0d50..., 3bad7faa..., 1a175f12..., a31ed46b....
- Request-side logs (config-service, 12:09:04.431-12:09:05.109Z): one client IP 82.165.94.38 (behind the Google LB 34.117.76.219), 8 requests: those 5 POSTs returned 500, plus POST / 401, PUT /shell_b5a9e26c7a79585e.jsp 401, PUT /sb5a9e26c7a79585e.aspx 401. 0 responses 2xx. All 8 are that IP's only config-service write-method requests in the 7 days 29 Oct-5 Nov (572 write-method requests in total; other external IPs, e.g. 45.148.10.15 with 128, were all 401).
- Fuse MCP lookup-endpoints config-service: no /run or /code/... route exists. The malformed bodies were rejected by the body parser (entity.parse.failed) but returned 500, not 400.
- Service healthy in the same minute: GET /api/v1/business/PURDYFIGG, /api/v1/connectors, /api/v1/business/EPARFUM from dedupe_service and sftp-host returned 200 at 12:10:06-12:10:15Z.
- Slot-timeout check: snap_adapter "waiting for a concurrency slot" error logs 00:00-13:30Z today: 0. snap_adapter errors today: 1 (below).
- Held record, not this alert's cause: snap_adapter "Entity creation in SNAP failed" 12:00:06Z, ESCENTRIC sales_order #139825, failureMode snap_api_error, transient false (the monitor excludes snap_adapter transient:false). replay-list-failures (production, 5 Nov, sales_order/purchase_order/master_data): 1 record, the same #139825, "LastName - MANDATORY on line SH8MW3H4BT", attempts 0. The other 19 PURDYFIGG goods_out_confirmation failures seen today (07:24Z, Shopify fulfillment order CLOSED) are confirmation delivery, not Snap submission, and were not examined further. No prior vault record mentions #139825.
- Flapping: 3 trigger/recover pairs for monitor 180072217 in 48h (3 Nov 14:08Z, 3 Nov 16:56Z, 5 Nov 12:09Z). The 3 Nov 16:56Z cause is in the 3 Nov record (slot timeouts).

## Not established
Whether anything executed on the service or reached the network (no host or egress logs checked; the payload was unparseable JSON and no 2xx was returned, which is the evidence for no execution, not proof). Whether config-service is meant to be reachable from the internet (client IPs show external callers through the LB; ingress/Cloud Armor config not read). The cause of the 3 Nov 14:08Z firing (not queried). Whether #139825 has since been fixed or replayed (replay list read at about 13:50Z). Why the parse failure returns 500 instead of 400 (observed, mechanism not read in code).

## Outcome
Real minor, P4. Hostile external probe of config-service, no 2xx, no customer impact seen; the monitor tripped because the app logs a malformed-JSON 500 at error level. Leads, not findings: return 400 for body-parse failures (or log them at warn), and consider whether the monitor should count unauthenticated-client errors. Separate from the alert: ESCENTRIC #139825 is held in replay-service for a Snap MANDATORY LastName rejection, support to fix the data and replay. Not ticketed here.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793880641852199
- Monitor: https://app.datadoghq.com/monitors/180072217
- Prior firing: Monitors/2026-11-03-platform-elevated-prod-error-rate-purdyfigg-1656.md
