---
tags: [datadog-triage]
date: 2026-10-21
monitor: "[FUSE][Platform] Pub/Sub ack-deadline headroom eroding (standard subscriptions)"
service: snap-adapter
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792582988189009"
opened_at: "2026-10-21T11:41:39Z"
resolved_at: "2026-10-21T11:45:20Z"
minutes_spent: 4
severity_assessed: P3
flapping: true
outcome: vendor
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# snap_adapter sales_order sub unacked 242s while ilg005 circuit open (Snap HTTP 500 outage)

## Fired
Monitor 323648859, group snap_adapter.prod.create_record_sales_order.v1.sub, oldest unacked 242s at 11:41:39Z.

## Investigation
- snap_adapter "Entity creation in SNAP failed" 11:33–11:44Z, by record: PURDYFIGG #6570350 (2x snap_api_error 500, then circuit_open, exhausted at delivery 10, held 11:40:24Z `create.snap_unavailable`), #6570355 and #6570356 (circuit_open, delivery 9 by 11:44Z), #6565591 (circuit_open delivery 9; underlying data error Email MANDATORY).
- replay-service prod holds created since 11:35Z: #6570350 (outage) and #6565591 at 11:35:12Z (data).
- Direct snaplookups probe 11:45Z: 500 on ilg005 (PURDYFIGG) and ilg001 (DOCKBAY).

## Outcome
Vendor knock-on of the Snap ilg001/ilg005 outage; consumer not stuck. Outage holds tracked in the 11:36Z error-rate thread record.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792582988189009
- Verdict: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792583120417979
