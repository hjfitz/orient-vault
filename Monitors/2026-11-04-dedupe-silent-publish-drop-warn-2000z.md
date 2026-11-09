---
tags: [datadog-triage]
date: 2026-11-04
monitor: "[FUSE][Dedupe Service] Silent publish drop (handled minus outcomes)"
service: dedupe-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793822503614479"
opened_at: "2026-11-04T20:00:36Z"
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Dedupe "silent publish drop" back to Warn at 20:00Z: shortened re-check, nothing unaccounted since 19:27Z

## Fired
Monitor 302511456 (P2, managed-by:terraform, warn 20 / critical 50, `sum(last_1h)` handled minus outcomes) went Warn at 20:00:36Z. Fifth transition today: Warn 18:40Z, Alert 18:50Z, Warn 19:05Z, Alert 19:25Z, Warn 20:00Z (`search_datadog_events`, source:alert, last 6h). Shortened re-check of a cause already triaged twice today; scope was the window since 19:27:49Z only.

## Investigation
- dedupe_service logs (@environment:prod), 19:27:49Z to 20:02:30Z: "Incoming record received" 2,254 = "Record dropped" 2,216 + "Record published to topic" 38 + "Dedupe gate held" 0. Unaccounted 0. Every drop has reason `duplicate` (2,216).
- The same holds in every 5-minute log bucket 19:00Z to 20:00Z (incoming = dropped + published, held 0 in all 13 buckets), including 19:20Z: 715 = 711 + 4.
- Error-level logs (status error/critical/alert/emergency) in dedupe_service, snap_adapter and replay_service, same window: 0.
- snap_adapter, same window: "Incoming record received" 38 = "Entity created in SNAP" 38; "Entity already exists" 0; "Entity creation in SNAP failed" 0. The 38 equals the 38 dedupe published.
- replay-service (`replay-list-failures`, production, createdAt 2026-11-04, 150 total, newest first): the newest entry is 18:40:44Z (goods_out_confirmation, PURDYFIGG, Shopify fulfillment order CLOSED). Nothing created since 19:27Z, so no new held record.
- Metric view (`fuse.dedupe.event.*`, environment:prod, 5-minute buckets 19:00Z to 20:00Z): handled 2,094, fresh + duplicate 2,046, net 48. The 19:20Z bucket alone is handled 145 vs fresh 2 + duplicate 50 (net +93); the other 12 buckets net -45 together. dropped_config_unavailable, default_zero: 0 throughout. All other outcome metrics (blacklisted, invalid) returned no series.
- Metrics vs logs for 19:30Z to 20:00Z buckets: `fuse.dedupe.event.handled` sums 729 against 2,254 incoming logs, so the counters again run well below log volume, as in the earlier records.
- Monitor status read at triage: Warn (`search_datadog_monitors` id:302511456).

## Outcome
No incoming record since 19:27Z lacks an outcome, every published record reached snap_adapter with no failure, and nothing new is held in replay-service. The monitor's net is again carried by the single 19:20Z metric bucket (+93), where handled and the outcome counters disagree while logs reconcile exactly. Same conclusion as the earlier two records: the monitor cannot distinguish this from a real drop and needs retuning or replacing with a log-based or per-record reconciliation. P4, no escalation.

## Not established
Why the 19:20Z bucket's duplicate counter is short, and why the metrics sit below log volume (no code or instrumentation check). The monitor's exact evaluated value at 20:00:36Z (I summed 19:00Z to 20:00Z buckets myself; the monitor's window and evaluation delay differ). When it recovers (by my arithmetic the 19:20Z bucket leaves the 1h window around 20:20 to 20:30Z, not observed). Per-record rather than per-batch matching of incoming to outcome (counts only). Whether support has replayed the 7 held records from the earlier record.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793822503614479
- Monitor: https://app.datadoghq.com/monitors/302511456
- Earlier records: Monitors/2026-11-04-dedupe-silent-publish-drop.md, Monitors/2026-11-04-dedupe-silent-publish-drop-alert-1925z.md
