---
tags: [datadog-triage]
date: 2026-11-09
monitor: "[FUSE][Platform] Pub/Sub backlog building (any subscription)"
service: snap-adapter
business_id: SPORTLUX
snap_instance: ilg004
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794212668614199"
opened_at: "2026-11-09T08:23:10Z"
severity_assessed: P3
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# Backlog Warn on snap_adapter sales-order subscription: a 246-order SPORTLUX burst, all created within 172 s, nothing held

## Fired
Monitor 302536090 (priority 2, `max(last_15m)` of gcp.pubsub.subscription.num_undelivered_messages by subscription, Warn at 200, Critical at 1,000) went Warn on `snap_adapter.prod.create_record_sales_order.v1.sub` at 08:23:10Z with value 228. Datadog's post is C099WKQTE8G 1794212668.614199 (08:24:28Z, no replies when read). The ack-deadline monitor 323648859 fired for the same subscription at 08:23:39Z (oldest unacked 111 s; its own post is 1794212685.394339). First backlog firing on this subscription seen in the monitor's events (the two previous events read, 8 Nov 18:38Z and 19:01Z, are the tracking-service subscription; 41 events in 48h, only the newest 3 read).

## Investigation
All numbers read between 08:25Z and 08:29Z, so 08:29-08:40Z was not observable.
- Subscription metrics (max per minute): num_undelivered_messages 0 through 08:19, 228 at 08:20, 191 at 08:21, 65 at 08:22 (no later point returned yet, Pub/Sub metric lag). oldest_unacked_message_age 0 until 08:19, 28 s at 08:20, 88 s at 08:21, 111 s at 08:22 (equals the 111.0 s in the ack-deadline alert), 0 at 08:23. Peak 228 and 111 s, shape: one spike of about 3 minutes.
- Source of the burst: dedupe-service logged "Record published to topic" for 246 SPORTLUX sales_order recordIds between 08:18:11.565Z and 08:18:13.651Z (collector POST record/request/sales_order, one correlationId 38cc6495-53ab-4e0e-b322-ea3740b9e9d7, 246 x 201). Topic bifrost.prod.create_record.v1 send_message_operation_count: 1 at 08:18, 237 at 08:19, 8 at 08:20 (all record types). SPORTLUX hourly sales_order publishes since 2 Nov: 246 in the 08Z hour today, next largest 182 (2 Nov 08Z), then 65, 62, 48. PURDYFIGG also had 87 published and 1,435 dropped as duplicates since 07:50Z (dedupe "Record dropped", reason duplicate), not part of the spike.
- Received vs created (snap_adapter, sales_order, 08:00Z to 08:28Z): "Incoming record received" 330 (262 at deliveryAttempt 1, 67 at attempt 2, 1 at attempt 3); "Entity created in SNAP" 330 (split of the first 320 at 08:25Z: SPORTLUX 246, PURDYFIGG 60, STUBBLE 8, DOCKBAY 5, WILDSMITH 1), 330 distinct recordIds, 0 duplicates. dedupe published 330 distinct sales_order recordIds in the same window; 0 of them lack an "Entity created in SNAP". Per minute received/created: 08:18 120/30, 08:19 101/101, 08:20 42/126, 08:21 0/6; other minutes 1-15 each, equal.
- Delay per recordId (dedupe publish to Entity created): median 70 s, p90 154 s, max 172 s across all 330; SPORTLUX 246: median 106 s, max 172 s, created 08:18:43Z to 08:21:05Z.
- Failures: no snap_adapter log with @failureMode in 08:00-08:28Z (the same query returns 74 slot_timeout lines for 8 Nov 15:30-17:00Z, so it would have caught them); no error/warn status and no "failed" message from snap_adapter today. Cloud Run snap-adapter-prod request_count at 08:20: 429 x35, 500 x32, 503 x0 (204: 29 at 08:19, 102 at 08:20, 126 at 08:21). Pub/Sub push_request_count for the subscription at 08:20: remote_server_5xx 32, unreachable 21 (+14 at 08:21). Those pushes were redelivered (67 attempt-2 incoming logs) and every one ended up created.
- Cloud Run: active instance_count 1 until 08:18, 2 at 08:19, 3 from 08:20 to 08:24; p99 max concurrent requests per instance about 32 from 08:19; CPU p99 0.11-0.27, memory p99 0.31-0.36. Two "App build started" logs (two new instances). All 1,664 snap_adapter logs since 02:00Z are revision snap-adapter-prod-00099-b4z.
- Snap per host (environment:prod): ilg004 latency avg 4,623 ms (08:18), 4,745 (08:19), 4,850 (08:20), 5,049 (08:21 and the 08:25 point), max 6,116 ms at 08:19; slot_queue_depth 24 at 08:18-08:20 and 08:25; 49/62/61/6 requests at 08:18-08:21. ilg005 avg 1,352-2,876 ms around 08:15-08:21, 4,361 ms avg and 8,425 ms max at 08:25 (33 requests); queue depth 3 at 08:25. ilg001 only 08:03-08:07. ilg004 averages over the last 24h are mostly 0 (no traffic) with isolated hours of 2,603-4,924 ms. SPORTLUX is on ilg004 (get-snap-connection); one read-only snap-lookup RECSTATUS against it returned 200 with 6 rows (response time not measured). Latency monitor 179927768 (snap.poll.request.latency, polling service) went Warn for ilg002 07:45, ilg005 07:50, ilg001 07:55, ilg004 08:01 (recovered 08:03) and 08:04, ilg003 08:05.
- Held: replay-list-failures (production, sales_order): newest held failure is DOCKBAY UK-914139 (ShipAddress.City over 30 characters), created 8 Nov 22:04Z; none created 9 Nov.
- Changes: get_change_stories for snap-adapter and dedupe-service, 02:00-08:35Z, prod: none. change_tracking events in the last 7h are Kubernetes CronJob updates (newest page read only). Vault Maintenance/ has no record naming 8-10 Nov.
- Cap context (Fuse MCP lookup-service snap-adapter, June 2026 note, not re-read from live config): Cloud Run max 3 instances x concurrency 30, per-host semaphore 5 per instance.

## Outcome
real_minor, P3. A 246-order SPORTLUX burst (largest hour since 2 Nov) arrived in 2 s; ilg004 was slow (about 4.6-5.0 s average, 6.1 s max); Cloud Run scaled 1 to 3 and rejected 67 pushes (429 x35, 500 x32) that Pub/Sub redelivered; the backlog peaked at 228 and oldest age 111 s, and all 330 sales orders in the window were created, slowest 172 s after publish. Nothing held, no slot_timeout, no duplicates. Different from the 8 Nov episodes: different business and host (SPORTLUX on ilg004, not PURDYFIGG on ilg005), zero slot_timeout, first backlog-monitor firing on this subscription in the events read.

Not established: what produced the Cloud Run 500s and 429s (no app log; Cloud Run config not read live); whether Snap ilg004 latency or the adapter's concurrency cap was the bottleneck; the ilg004 probe's response time; undelivered samples after 08:22Z and anything 08:29-08:40Z; the #bifrost-general maintenance pin and ILG mail; the monitor's firing history for this subscription beyond the newest 3 of 41 events.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794212668614199
- Monitor: https://app.datadoghq.com/monitors/302536090
- Related: [[2026-11-08-pubsub-ack-deadline-headroom-snap-adapter-sales-order-1627z]]
