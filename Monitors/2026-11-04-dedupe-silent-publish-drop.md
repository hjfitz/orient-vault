---
tags: [datadog-triage]
date: 2026-11-04
monitor: "[FUSE][Dedupe Service] Silent publish drop (handled minus outcomes)"
service: dedupe-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793817707283879"
opened_at: "2026-11-04T18:40:36Z"
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Dedupe "silent publish drop" Warn: no record lost, metric does not reconcile with logs

## Fired
Monitor 302511456 (P2, managed-by:terraform, warning 20 / critical 50, evaluation_delay 300s) went Warn at 18:40:36Z. Metric 1h sums at ~18:44Z: handled 2297, fresh 149, duplicate 2104 (other outcome series have no data), net 44. Net over 3h -127, 6h -143, 24h -321, previous 24h -450.

## Investigation
- Per-record accounting from dedupe-service logs (@environment:prod), 00:00-18:30Z 4 Nov: "Incoming record received" 54,802 = "Record dropped" (reason duplicate) 51,667 + "Record published to topic" 3,128 + "Dedupe gate held on permanent failure" 7; unaccounted 0. Same 0 for 17:00-18:00Z (19,254 = 18,614 + 640 + 0) and 15:00-18:00Z. 3 of 73,610 unaccounted on 3 Nov (not investigated).
- No error-level dedupe-service logs in 24h; only warns are the duplicate drops.
- Downstream: 17:00-18:00Z dedupe published 640; snap_adapter "Incoming record received" 640 = "Entity created in SNAP" 637 + "Entity already exists in SNAP" 3. Whole day: snap_adapter incoming 3,128 = created/exists 3,121 + "Entity creation in SNAP failed" 7.
- create_record Pub/Sub subscriptions (snap_adapter, tracking, collector) drained over 3h: avg undelivered ~0-3, oldest unacked age ~0-2s.
- The 7 Snap failures are held in replay-service (production, created 4 Nov, attempts 0): WILDSMITH SO-29578 (CustomerId/OrderClass MANDATORY, Invalid Shipment), STUBBLE SC17419784 (City/Line1/LastName MANDATORY), ESCENTRIC 41126 (OrderClass/OrderType No Check Code Found), PURDYFIGG PO-U-00002315 (Invalid Unit, No Product Found), AYMSTUDIO PO-051126 (No Product Found), DOCKBAY DSBJJG5HAK (City >30 chars, wms_precheck), DOCKBAY PO-57UKLX3A (Invalid Unit, No Product Found). These are visible, accounted-for failures, not silent drops.
- Metric vs logs: last 1h metric handled 2,297 vs log "Incoming record received" 18,334 (PURDYFIGG 18,143 of them, all POST /events/v1/record/request/sales_order 204).
- Flapping: 19 alert events for this monitor in 7 days (30 Oct, 1 Nov x4 triggers, 2 Nov, 4 Nov). Prior records 2026-09-23 and 2026-11-02 reached the same monitor_mistuned reading; used as leads only.

## Outcome
No record dropped in the checked windows. Alert is the metric not reconciling with request volume (handled is ~8x below log-counted requests, and hourly net is chronically negative), so the monitor cannot detect a real drop. Seven records rejected by Snap on data validation are held for support to fix and replay.

## Not established
Why the handled/duplicate metrics undercount the requests. The monitor's exact tripping value at 18:40:36Z. The 3 unaccounted records on 3 Nov.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793817707283879
- Monitor: https://app.datadoghq.com/monitors/302511456
