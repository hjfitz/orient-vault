---
tags: [datadog-triage]
date: 2026-11-05
monitor: "[FUSE][Fuse API] Request latency p95 high"
service: fapi
business_id: DOCKBAY
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793875104987379"
opened_at: "2026-11-05T10:37:01Z"
severity_assessed: P4
flapping: false
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Fuse API p95 latency warn: one 135-record DOCKBAY master-data upload took about 6s

## Fired
Monitor 302685721 (`avg(last_15m):default_zero(avg:fuse.request.latency.95percentile{service:api-gateway,environment:prod}) > 2000`, P3, Terraform-managed) went to Warn at 10:37:01Z with metric value 1250.751. Same monitor as the 4 Nov 17:47Z alert (see 2026-11-04-fuse-api-request-latency-p95-high.md). Fuse API is `service:api-gateway` in the metric and `rest_connector` in logs.

## Investigation
- Metric, 1-min points over the last 6h, by `businessid` (`queryTimeseriesData`, `fuse.request.latency.95percentile`, `.count`, `.max`): the only point above 1s is `businessid:dockbay` at 10:36, p95 6056.5ms, max 6056.5, count 1. The next highest is PURDYFIGG 859.4ms at 08:52 (count 1). Not broad slowness, and not PURDYFIGG.
- That point is one request: `POST /api/v2/master-data` for DOCKBAY (correlationId `fulfil`, the Fulfil.io connector's fixed id). rest_connector logged "Auth accepted" at 10:36:04.158Z and the 202 at 10:36:10.215Z, about 6.06s, matching the metric. Log "Received 135 master-data records" at 10:36:04Z.
- The 6s is the per-record publish loop: 135 "Record published to topic" logs ran 10:36:04.253Z to 10:36:10.214Z, and the 202 was logged right after "Record batch emitted" at 10:36:10.215Z.
- It completed downstream (logs on `@correlationId:fulfil @businessId:DOCKBAY`, 10:35:30-10:50Z): 135 dedupe_service "Incoming record received" and 135 "Record published to topic", 135 snap_adapter "Entity created in SNAP" (10:36:06.9Z to 10:36:49.3Z), 135 sftp_connector "Create acknowledgement received", plus 1 "Alternatives created". No warn or error status logs for `@correlationId:fulfil` from any service 10:36-10:50Z.
- Volume: rest_connector `POST /api/v2/` lines in the monitor window 10:22:00-10:37:01Z total 2, both DOCKBAY (10:31:55Z master-data with 1 record, 202; 10:36:10Z the slow one). So one slow request in a window of about two requests set the p95.
- Flapping: monitor alert events (`source:alert`, 30d) show episodes starting 2026-10-07 07:00Z, 10-20 09:19Z, 10-28 16:56Z, 11-04 17:47Z, and today 11-05 10:37Z (Warn). Each earlier one recovered within about 10-20 min. Two consecutive days now, not repeated within a day.
- Monitor status when checked at about 10:39Z: Warn.

## Not established
- Why publishing takes about 27-45ms per record (6s for 135 here, 18.5s for 680 on 4 Nov); the logs show the publishes spread across the duration, not what bounds it.
- Whether these 135 records are a resend of DOCKBAY's 10:21Z batch of 136 that fapi rejected on null nmfcCode (the counts differ by one; not queried).
- Causes of the 10-07, 10-20 and 10-28 episodes (not queried).
- Monitor recovery, not yet observed at time of writing.

## Outcome
P4, monitor_mistuned: a single 135-record bulk upload, accepted with 202 and fully processed downstream, tripped a p95 monitor on a metric that carries very few requests. Same shape as 4 Nov (one bulk request is the whole p95 sample), different business (DOCKBAY, not PURDYFIGG). No customer impact seen. The retune suggested on 4 Nov (a minimum request count or a longer window) applies again; no change made and no ticket filed.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793875104987379
- Monitor: https://app.datadoghq.com/monitors/302685721
