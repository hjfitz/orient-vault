---
tags: [datadog-triage]
date: 2026-10-29
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: snap-adapter
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793290364926679"
opened_at: "2026-10-29T16:11:37Z"
severity_assessed: P3
flapping: true
outcome: real_minor
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: resolved
---
# 16:11Z firing: 126 PURDYFIGG snap_adapter slot_timeout errors after a Shopify bulk order wave, all 78 records created

## Fired
More than 2 domain:fuse error logs in 2m at 16:11:37Z. Fourth firing today (07:06 SPORTLUX slot_timeout, 08:10 PURDYFIGG token refresh, 10:03 ilg005 maintenance 404s). Same failure mode as 07:06Z and 28 Oct; not a new service or mode. Larger: 126 errors vs 53 (07:06Z) and 73 (28 Oct 17:21Z).

## Investigation
- Monitor's own query (with all four exclusions), 15:45-16:15Z: 126 errors, all snap_adapter, PURDYFIGG, sales_order, slot_timeout (transient:true, "Timed out after 30000ms waiting for a concurrency slot"). Per minute 16:10 = 45, 16:11 = 48, 16:12 = 33; none at 16:13 or since (checked to ~16:14Z). No other service errored in 15:45-16:15Z; since 10:30Z the only other prod domain:fuse errors were 3 at 11:00Z and 2 at 15:00Z.
- Each failure returned 503 to the dedupe-forwarded POST /events/v1/record/create/sales_order (45/48/33 per minute), so Pub/Sub redelivers.
- 78 distinct recordIds failed with slot_timeout; all 78 later have "Entity created in SNAP" or "Entity already exists in SNAP" after 16:10Z (SQL join on recordId, 16:00-16:30Z). Recovery visible: 34 created at 16:12, 48 at 16:13.
- Trigger volume: shopify-connector "Bulk reap completed", PURDYFIGG. dedupe "Incoming record received" 1168 at 16:05 (682 published, 485 dropped) and 676 at 16:10 (107 published, 568 dropped). snap_adapter PURDYFIGG logged 216 and 366 "already exists" at 16:05/16:06, then nothing 16:07-16:09, then slot_timeouts from 16:10.
- Snap latency (snap.poll.request.latency.avg, prod): ilg005 about 0.4-0.6s until 16:04, 1.4s at 16:06, then 7.9-8.2s from 16:10Z (2m rollups). ilg001/003/004 also 3-17s (10s points 15:40-15:55). Active DB5 latency Warn 179927768 posted 16:13Z. Only ilg005 spikes align with the 16:10 burst, but PURDYFIGG's host for creates was not shown (polling logs carry no snapHost).
- No maintenance window covers 16:10Z (Maintenance records: DB5 10:00Z, firewall 08:00-09:00Z).
- Recurring "Entity creation in SNAP failed" schema_validation transient:false, 1 per 5 min for PURDYFIGG 15:55-16:10 (excluded from the monitor); not investigated.

## Not established
Whether ilg005 is PURDYFIGG's create host and whether Snap slowness or our own 30s slot cap drove the timeouts (get-snap-connection/lookup-snap-instance unavailable: Fuse MCP 401, no host probe). Why the 16:05 wave had a 3m gap. What the schema_validation record is.

## Outcome
Real minor, P3. Self-healing via redelivery, 0 of 78 records outstanding at 16:14Z. Chronic: slot_timeout bursts recur (07:06Z, 28 Oct), worth a ticket on slot cap vs Snap latency.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793290364926679
