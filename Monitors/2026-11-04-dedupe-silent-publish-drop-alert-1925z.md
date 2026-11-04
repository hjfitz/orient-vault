---
tags: [datadog-triage]
date: 2026-11-04
monitor: "[FUSE][Dedupe Service] Silent publish drop (handled minus outcomes)"
service: dedupe-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793820406901749"
opened_at: "2026-11-04T19:25:36Z"
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Dedupe "silent publish drop" went Warn to Alert: no record unaccounted for, the metric undercounts outcomes

## Fired
Monitor 302511456 (P2, managed-by:terraform, warn 20 / critical 50, `sum(last_1h)` handled minus outcomes) went Alert at 19:25:36Z. Same monitor was Warn 18:40Z, Alert 18:50Z, Warn 19:05Z, Alert 19:25Z. Two further firings were folded into this one.

## Investigation
- Per-record accounting from dedupe_service logs (@environment:prod), 18:30:00Z to 19:27:49Z 4 Nov: "Incoming record received" 13,019 = "Record dropped" (reason duplicate, the only reason seen) 12,963 + "Record published to topic" 56 + "Dedupe gate held on permanent failure" 0; unaccounted 0. 18:30-19:00Z 7,851 = 7,825 + 26 + 0. 19:00-19:27Z 5,168 = 5,138 + 30 + 0. Day to date 00:00-19:27Z: 67,821 = 64,630 + 3,184 + 7, unaccounted 0 (the 7 held are the ones in the earlier record, none new since 18:30Z).
- By business since 18:30Z (incoming logs): PURDYFIGG 12,852 of 13,019.
- Per-correlationId check for 19:20-19:25Z (715 incoming across 3 correlationIds) and 18:50-18:55Z (1,205 across 6): every incoming correlationId has an equal count of outcome logs, 0 missing. A correlationId spans many records, so this is a count check per request batch, not per record.
- dedupe_service error-level logs and non-duplicate warns since 18:30Z: 0.
- Downstream: 56 published since 18:30Z; snap_adapter "Incoming record received" 56 = "Entity created in SNAP" 55 + "Entity already exists in SNAP" 1; "Entity creation in SNAP failed" 0.
- Pub/Sub create_record* subscriptions, last 3h (first 12 series returned): max oldest-unacked age 4.7s (snap_adapter create_record_sales_order), max undelivered 37.3 (snap_adapter create_record_master_data), the rest at or near 0.
- Metric view (1-min points, `fuse.dedupe.event.*` environment:prod): the metric is emitted in 5-minute bursts, one revision (dedupe-service-prod-00051-q85, running since 2 Nov 20:00Z, unchanged). Rolling 1h net handled minus outcomes at 19:27Z: 2320 - 2217 = 103. The gap arrives in one bucket: 19:20Z handled 145 vs fresh 2 + duplicate 50 (net 93); 19:15Z, 19:25Z buckets net 0 and 9. Over the same 19:20-19:25Z the logs show 715 incoming = 711 dropped + 4 published. Over 17:30-19:28Z `fuse.dedupe.event.handled` sums 5,048 vs 31,785 incoming logs (sales_order 4,901 vs 31,078), so the counters run well below log volume.
- Monitor history: 22 alert-source events in 7 days (warn 11, ok 7, error 4); 4 firings today. Earlier records 2026-11-04 (Warn 18:40Z), 2026-11-02, 2026-09-23 reached the same reading, used as leads only.

## Outcome
No incoming record lacked an outcome and every record dedupe published reached snap_adapter. The 1h net crossing 50 comes from the duplicate and handled counters landing unevenly in the metric; the monitor cannot tell this from a real drop, and the Alert status change did not coincide with any log-side loss. Retune or replace the monitor with a log-based or per-record reconciliation.

## Not established
Why the duplicate counter is missing 95 increments in the 19:20Z bucket and why the metrics sit far below log volume (no code or instrumentation check done). Per-record (not per-batch) matching of incoming to outcome. Whether support has replayed the 7 earlier held records (not checked this run).

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793820406901749
- Earlier Warn thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793817707283879
- Monitor: https://app.datadoghq.com/monitors/302511456
- Earlier record: Monitors/2026-11-04-dedupe-silent-publish-drop.md
