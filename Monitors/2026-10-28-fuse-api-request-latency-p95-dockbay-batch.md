---
tags: [datadog-triage]
date: 2026-10-28
monitor: "[FUSE][Fuse API] Request latency p95 high"
service: fapi
business_id: DOCKBAY
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793206661747479"
opened_at: "2026-10-28T16:56:01Z"
resolved_at: "2026-10-28T17:02:44Z"
minutes_spent: 7
severity_assessed: P4
flapping: false
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: resolved
---
# Fuse API p95 latency Warn: a single DOCKBAY bulk master-data POST

## Fired
Monitor 302685721 (avg 15m of fuse.request.latency.95percentile, service:api-gateway) Warn, value 1783 ms against the 2000 threshold.

## Investigation
- Logs (service:rest_connector, Cloud Run api-gateway-prod): the only fapi request since 16:02:34Z was POST /api/v2/master-data at 16:50:05Z, DOCKBAY, 127 records in one batch, python-httpx, 202. 260 log lines in 16:45-16:58Z, all from that batch.
- 127 "Incoming record received" lines span 16:50:00.195Z-16:50:05.346Z, so about 5.2s for the call.
- 0 error-status logs and 0 4xx/5xx request lines from fapi in 3h; 129 POSTs in 6h all 202 (94 sales-orders, 35 master-data). 4xx reasons are debug-logged, so a 4xx would not show.
- The request path in logs is receive then publish to create_record_request per record; no Snap call, so independent of the Snap latency.
- Prior firings from vault: 2026-09-29 (DOCKBAY go-live bulk load, monitor_mistuned, retune still open), 2026-10-20 (real, Redis hang, INC-40). No monitor events in Datadog for the last 3d.

Not established: the metric by route/business (all metric queries timed out, 1783 is the alert's value); whether the 5.2s was payload size or another cause (no APM spans for this service); Fuse MCP was down (401), so service resolved from the vault record, not lookup-service.

## Outcome
Low-volume mistuned monitor: one bulk request in the window sets the p95. No customer impact seen. The retune (minimum request count or longer window) is still open from 2026-09-29, not ticketed.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793206661747479
- Earlier: [[2026-09-29-fuse-api-latency-p95-and-availability-flap]], [[2026-10-20-fuse-api-request-latency-p95]]
