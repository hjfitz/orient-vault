---
tags: [datadog-triage]
date: 2026-10-20
monitor: "[FUSE][Fuse API] Request latency p95 high"
service: fapi
business_id: DOCKBAY
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792488025842869"
opened_at: "2026-10-20T09:19:01Z"
resolved_at: "2026-10-20T09:30:00Z"
minutes_spent: 11
severity_assessed: P2
flapping: false
outcome: self_resolved
escalated_to:
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# [FUSE][Fuse API] Request latency p95 high

## Fired
Avg of fuse.request.latency.95percentile{service:api-gateway} read 102,739 ms (threshold 2000).

## Investigation
- Metric tags: PURDYFIGG purchase_order p95 6,496,967 ms; DOCKBAY sales_order 828,641 ms. Interceptor (logging.interceptor.ts @ b8870c5) times the HTTP handler.
- Logs: after the 07:02Z restart every connector resolution logged "No cached connector IDs ... fetching from API" and stalled; all released 09:18:15-09:18:17Z ("Confirmation forwarded to connector" / "Auth accepted"). 15 DOCKBAY ingest calls (first 07:02:13Z), 27 DOCKBAY SO pushes / 5 confirmations (from 08:50Z), 25 PURDYFIGG PO pushes / 4 confirmations (from 07:24Z).
- config-service answered GET /api/v1/connectors and GET conn_1a2ffda... 200 at 07:24:48.2Z, ~80 ms after fapi's 07:24:48.143Z log: not config-service/Mongo.
- Code: fapi RemoteConfig uses full cache (Redis+LRU); init timed out ("Dependency degraded"). @gfs-bifrost/cache 0.3.0 gates reads on connected state but updateNetworkCacheAsync_ -> redis.set has no gate and no timeout, so the write queues on the reconnecting client.
- gcp.redis metrics for api-gateway-prod-redis absent ~06:08Z to 09:19Z, resumed 09:19Z.
- Cloud Run: 55 504s since 07:00Z. Webhooks delivered (no failure logs) but duplicated: 27 POSTs for 5 DOCKBAY, 25 for 4 PURDYFIGG.
- After 09:18: ingest 09:23:48Z and confirmations 09:20/09:24Z complete in <0.3 s; confirmation_ready.so/.po subs oldest-unacked back to 0 (po peaked 6,733 s).

Not established: whether DOCKBAY resent 504'd orders; whether Redis returned through zone recovery or failover.

## Outcome
Real, covered by INC-40; recovered 09:18:15Z when Redis came back. Latent bug: Redis writes with no connected-check/timeout hang requests while Redis is reconnecting. Recurs if api-gateway-prod-redis drops again. Linked to INC-40 (https://gfsdeliver-eng.slack.com/archives/C0CAEGABJBF). Read-only; nothing restarted or replayed.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792488025842869
- Incident: https://gfsdeliver-eng.slack.com/archives/C0CAEGABJBF
