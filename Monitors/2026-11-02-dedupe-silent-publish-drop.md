---
tags: [datadog-triage]
date: 2026-11-02
monitor: "[FUSE][Dedupe Service] Silent publish drop (handled minus outcomes)"
service: dedupe-service
business_id:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793644906458469"
opened_at: "2026-11-02T18:40:36Z"
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: open
---
# Dedupe "silent publish drop" fired: no records lost, metrics do not reconcile with requests

## Fired
Monitor 302511456: sum(last_1h) of fuse.dedupe.event.handled minus (fresh + duplicate + sku.blacklisted + event.invalid + record.invalid + default_zero(dropped_config_unavailable)) > 50 (warn 20), evaluation_delay 300s. Rolling 1h net from 10-min buckets: 56 at 18:30, 95 at 18:40, 91 at 18:50 (reconstruction, not the monitor's own value).

## Investigation
- Logs (service:dedupe_service, @environment:prod): 18:00-18:45Z "Incoming record received" 15,247 = "Record dropped" (reason duplicate) 15,142 + "Record published to topic" 105. Equal in every 10-min bucket 15:30-18:50. No "Dedupe gate held". Only warns other than drops: 2x LISAUK CSTEST "Record failed validation" (15:52, 16:24).
- Per-recordId reconciliation (key businessId|recordId|correlationId), windows 18:10-18:12 and 18:30-18:32 (+3 min for outcomes): 1,701 and 1,714 incoming, 0 without a drop/publish log. PURDYFIGG = 1,667 and 1,683 of them (reap, ~98% duplicate).
- All 105 records published 18:00-18:45 (PURDYFIGG 76, DOCKBAY 16, STUBBLE 6, ESCENTRIC 3, SAIRA 2, WILDSMITH 2) have "Entity created in SNAP" in snap_adapter (by @recordId).
- Metric vs requests: Cloud Run request_count (10-min) matches handled until 15:30 (209/188/197/253 vs 209/190/195/189), then requests climb to ~3,400 per 10 min while handled stays 150-770. Daily handled/requests is ~25-45% since 10-20. Instances went 2 -> 5 at 15:30 and stayed 5; revision dedupe-service-prod-00051-q85 unchanged all afternoon (no deploy/restart).
- Net by bucket (sales_order): 17:10 -353 and 17:20 -369 (duplicate metric exceeded handled), 18:10 +56, 18:30 +27, 18:40 +29.
- 14d: rolling 1h net > 50 only at 1 Nov 19:10Z (60) and 2 Nov 18:30-18:50Z. Hourly net is chronically negative. Monitor events API returned none.
- Code: handled and duplicate both increment once per request (event.controller.ts), so the metric gap is not logic in the controller.

## Outcome
No record lost. Alert is an accounting artefact of the metrics, not a drop. Why handled/duplicate counts are ~10x lower than requests and skewed bucket to bucket is not established. Monitor needs retuning or a log-based/ledger-based reconciliation; fixing the metric emission is the real fix.

## Not established
Cause of the metric undercount (timing coincides with instances 2 -> 5, not proven). The monitor's exact tripping value. Whether 1 Nov 19:10 lost any record (only the metric was checked).

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793644906458469
- Monitor: https://app.datadoghq.com/monitors/302511456
