---
tags: [datadog-triage]
date: 2026-10-22
monitor: "[FUSE][Platform] Pub/Sub backlog building (any subscription)"
service: tracking-service
business_id:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792697243899439"
opened_at: "2026-10-22T19:26:10Z"
resolved_at: "2026-10-22T19:28:46Z"
minutes_spent: 3
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# Pub/Sub backlog warn on tracking-service create_record_request sales_order sub: a one-sample publish burst

## Fired
Monitor 302536090 went to Warn (>200 on `max(last_15m)` of `num_undelivered_messages`) for `tracking-service.prod.create_record_request.sales_order.v1.sub`, at a value of 225, at 19:26:10Z.

## Investigation
- The minute series shows one 225 sample at 19:22Z, with 0 before and after it. `oldest_unacked_message_age` was 0s across the last 90 minutes.
- At 19:21Z the topic `bifrost.prod.create_record_request.v1` had 344 `send_message_operation_count`. The sibling subscriptions spiked in the same minute and were at 0 the next: `collector...sales_order` 180 and `dedupe_service...sales_order` 172.
- Acks on the tracking sub follow the ~5-minute publish cadence (for example 1265 at 18:01Z and 344 at 19:22Z). The consumer is keeping up.
- tracking-service logs with `@environment:prod` and status error/warn over the last 6h: only 18 errors, all in the 16:00Z hour (the earlier Firestore blip). There were none around the alert.
- The last prod `Deploy` run for tracking-service was on 2026-10-19 (gh run list).
- Flapping: 27 `source:alert` events for this monitor in 7d, spread over several subscription groups.

## Outcome
No impact and nothing stuck. The threshold trips on transient publish bursts. A retune is recommended (gate on oldest_unacked_message_age or a sustained window). No ticket was filed.

Not established: the alert group's auto-recovery had not happened yet at the time of the reply.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792697243899439
