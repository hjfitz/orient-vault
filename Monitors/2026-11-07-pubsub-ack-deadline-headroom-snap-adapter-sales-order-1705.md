---
tags: [datadog-triage]
date: 2026-11-07
monitor: "[FUSE][Platform] Pub/Sub ack-deadline headroom eroding (standard subscriptions)"
service: snap-adapter
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794071104218939"
opened_at: "2026-11-07T17:03:39Z"
severity_assessed: P4
flapping: false
outcome: self_resolved
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# ack-deadline headroom Warn on snap_adapter create_record_sales_order sub (monitor 323648859, first firing)

## Fired
Monitor 323648859 (Terraform-managed, created 2026-09-21) warned on subscription_id:snap_adapter.prod.create_record_sales_order.v1.sub with oldest unacked age 137s. Its query is max(last_10m) of gcp.pubsub.subscription.oldest_unacked_message_age by subscription_id, > 180 (the lookup returns only that threshold, not the warn threshold), excluding master_data, snap_poll_customer, new_file, token_revalidation, reap and stock_adjustment_ready subs. It measures message age, not handler processing time and not ack-deadline headroom.

## Investigation
- Oldest unacked on the sub: 64s at 16:58, 137s at 16:59, 0 at 17:00 (60s metric samples). Backlog 116, 116, 25, 0. It is the highest value on any monitored sub in the last 24h.
- Cloud Run snap-adapter-prod returned 26 HTTP 429 at 16:57 (gcp.run.request_count by response_code); Pub/Sub recorded 26 push responses of class unreachable on this sub at 16:57-16:58. Instances were 3 active; max request concurrency 30. 29 429s in 24h, 26 of them this minute.
- snap-adapter logs 16:56:47-16:57:51: 116 "Entity created in SNAP" and 116 "POST /events/v1/record/create/sales_order - 204". No warn/error logs from 16:50Z to 17:08Z.
- No deadline_exceeded push responses on this sub in 24h.
- Later bursts (17:02: 87, 17:07: 20) drained with no unreachable responses.

## Outcome
Self-resolved, P4. A burst of sales orders hit snap-adapter, 26 requests were rejected with 429, Pub/Sub retried them, and all 116 orders were created in SNAP with nothing held.

Not established: why Cloud Run returned 429 (instance and concurrency limits from the service config were not read); the monitor's warn threshold.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794071104218939
