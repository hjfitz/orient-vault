---
tags: [datadog-triage]
date: 2026-09-21
monitor: "[FUSE][Platform] Pub/Sub ack-deadline headroom eroding (standard subscriptions)"
service: collector
business_id:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790004943642539"
opened_at: "2026-09-21T15:25:41Z"
resolved_at: "2026-09-21T15:40:35Z"
minutes_spent: 15
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 26786e07-db97-44ac-aff4-911f6cd52eca
status: resolved
---
# Pub/Sub ack-deadline headroom monitor fired twice within an hour of creation, both self-resolved

## Fired
New monitor (id `323648859`, created by Harry at 15:19 UTC same day) alerts when a subscription's oldest-unacked-message age exceeds 15s against its ~20s ack deadline. Fired on `sftp-connector.prod.create_acknowledge.v1.sub` (26.0s, 16:25:41 BST, recovered 16:34:42) and then on `collector.prod.create_record_request_sales_order.v1.sub` (21.0s, 16:35:43 BST). Harry flagged "needs tuning" in-thread within a minute of the first firing.

## Root cause
Not a real backlog. At investigation time every subscription across the fleet (including both that fired) sat at 0s oldest-unacked age and 0 undelivered messages. `collector_service` prod logs showed zero errors in the window; `sftp_connector` prod logs showed only normal info-level traffic (~106 ack-processing lines over 11 minutes), no slow/stuck-consumer pattern. The 15s threshold sits close enough to the ~20s ack deadline that ordinary processing jitter under normal load crosses it — this is a mistuned monitor, not a pipeline problem.

## Fix / Resolution
No platform fix needed. Recommended in-thread that the monitor require a sustained breach (e.g. over a few minutes) or use a slightly looser threshold, rather than firing on a single evaluation. Monitor itself not edited as part of this triage (Terraform-managed) — retuning is a follow-up for whoever owns that monitor definition.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790004943642539
