---
tags: [datadog-triage]
date: 2026-11-04
monitor: "[FUSE][Platform] Pub/Sub backlog building (any subscription)"
service: snap-adapter
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793814862755209"
opened_at: "2026-11-04T17:53:10Z"
resolved_at: "2026-11-04T17:56:00Z"
minutes_spent: 3
severity_assessed: P4
flapping: false
outcome: self_resolved
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# Pub/Sub backlog warn on snap_adapter.prod.create_record_master_data.v1.sub: one 680-record PURDYFIGG upload, drained in about 3 minutes

## Fired
Monitor 302536090 (`max(last_15m):max:gcp.pubsub.subscription.num_undelivered_messages{project_id:bifrost-prod-global1} by {subscription_id} > 1000`, thresholds warning 200 / critical 1000, P2, Terraform-managed) went Warn for group `subscription_id:snap_adapter.prod.create_record_master_data.v1.sub` at 17:53:10Z with metric value 306. Datadog posted the Slack alert at 17:54:22Z.

## Investigation
- Per-minute `num_undelivered_messages` / `oldest_unacked_message_age` for the subscription (`queryTimeseriesData`, 1 min): 17:47 60 / 0s, 17:48 306 / 23s, 17:49 7 / 78s, 17:50 and 17:51 and 17:52 0 / 0s. Zero for the preceding 3h (14:56-17:44 binned max 0). Peak age of the oldest unacked message was 78s. The monitor stays Warn because the peak is still inside its 15m window.
- Ack count on the subscription (`ack_message_count`): 293 at 17:46, 218 at 17:47, 24 at 17:48. Expired ack deadlines and dead-lettered counts: no non-zero points 17:30-17:55.
- Source: a single `POST /api/v2/master-data` batch for PURDYFIGG. dedupe_service logged 680 "Incoming record received" and 680 `POST /events/v1/record/request/master_data - 204` for correlationId `b2d26a97-65c7-4092-b32b-c97ccf2682a2`, between 17:45:02Z and 17:45:20Z (`@correlationId` log aggregation).
- Outcome for that correlationId: snap_adapter logged 535 "Entity created in SNAP", 535 `POST /events/v1/record/create/master_data - 204` and 190 "Alternatives created". dedupe_service logged 145 "Record dropped" (warn). Statuses across all services for the correlationId were only info, debug and warn: no error-level logs. The one other warn was rest_connector "Raw request body not captured" (x1).
- snap_adapter, 17:30-17:56Z: 1926 logs, all `info`; zero error/warn status and zero logs matching failed / rejected / timeout (`aggregateLogs`).
- Other subscriptions: the avg of `num_undelivered_messages` per subscription over 17:40-17:56Z (scalar query) was 1 or less everywhere except snap_adapter create_record_master_data (avg 28.7 over the window, from this burst). No other subscription showed a backlog.
- Flapping: the monitor's alert events 2026-10-28 to 2026-11-04 show this subscription fired once (today). The other firings were 10-29 for snap_adapter create_record_sales_order (17:06Z-17:20Z) and dedupe_service create_record_request_sales_order (16:36Z-16:52Z), both recovered.
- Related alert for the same upload: [FUSE][Fuse API] Request latency p95 high at 17:47Z (separate monitor, own Monitors record).
- Maintenance: no `Maintenance/` record covers 2026-11-04 (latest records are 10-20, 10-28, 11-02; the 11-02 window was 11-03 10:00-10:30Z). No Snap errors or timeouts were present, so no Snap instance check (Step 2b) was needed.

## Not established
- Why snap_adapter's draining took about 2 minutes for 535 creates (concurrency/slot limits not queried).
- Whether the monitor's Warn at 200 should tolerate short bulk-upload bursts: only this one firing for this subscription was seen in the last 7 days, so there is no evidence of repeat noise.

## Outcome
Self-resolved, P4, no action. Backlog drained by 17:50Z with no failures or held records for the upload. No ticket.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793814862755209
- Monitor: https://app.datadoghq.com/monitors/302536090
