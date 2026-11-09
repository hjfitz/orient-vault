---
tags: [datadog-triage]
date: 2026-11-08
monitor: "[FUSE][Platform] Pub/Sub ack-deadline headroom eroding (standard subscriptions)"
service: snap-adapter
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794153244711689"
opened_at: "2026-11-08T15:52:39Z"
resolved_at: "2026-11-08T16:00:39Z"
minutes_spent: 8
severity_assessed: P3
flapping: true
outcome: self_resolved
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# snap_adapter sales_order sub unacked 139s (second firing in 10 min): tail of the 15:45 burst, later bursts clean

## Fired
Monitor 323648859 (warn 90, critical 180; query `max(last_10m)` of oldest_unacked_message_age by subscription_id), group snap_adapter.prod.create_record_sales_order.v1.sub, Warn 15:52:39Z at 139s, Recovered 16:00:39Z (19s). Second Warn in ~10 min: the first (110s, 15:43:39Z, recovered 15:49:39Z) is in [[2026-11-08-pubsub-ack-deadline-headroom-snap-adapter-sales-order-1543z]]. Third Warn episode on this group in 24h: also 07 Nov 17:03:39Z (events, 6 monitor events in 24h = 3 Warn/Recovered pairs).

## Investigation
- oldest_unacked_message_age (60s samples): 123 at 15:49, 139 at 15:50, 0 at 15:51, 19 at 15:52 and 15:53, 0 at 15:54-56, 11 at 15:57, 19 at 15:58, 0 at 15:59-16:01, 18 at 16:02 and 16:03. num_undelivered: 84,84,65,5 at 15:47-15:50 samples, 0 at 15:51, 26 at 15:52, 24 at 15:53, 55 at 15:57, 32 at 15:58, 69 at 16:02. Inside 15:51-16:03 the max age was 19s; 139s was the 15:50 sample, not repeated.
- snap_adapter logs (prod), 15:50:00-16:03:30Z: 357 "Incoming record received", 357 "Entity created in SNAP" (357 distinct recordIds, all sales_order), 357 x 204. Zero warn/error logs in the service from 15:47:40Z to 16:05:12Z; zero "Entity creation in SNAP failed", zero slot_timeout/"concurrency slot". Created per minute: 15:50 128, 15:51 4, 15:55 94, 16:00 112, 16:02 19. By business: PURDYFIGG 332, DOCKBAY 19, STUBBLE 3, ESCENTRIC 1, SAIRA 1, WILDSMITH 1. Incoming logs carry no recordId, so incoming-to-created is matched on count only.
- The 139s tail: 33 PURDYFIGG creates failed slot_timeout 15:45:40.6-15:46:13.5Z (33 distinct recordIds, 33 failure logs); each was created later, last at 15:47:39.7Z; fail-to-create gaps 75-105s. First "Incoming record received" in that burst 15:45:09.9Z, so the last of those 33 was ~150s after burst start, which brackets 139s.
- Cloud Run snap-adapter-prod (60s buckets 15:50-16:04): response_code 429 = 0 and 503 = 0 in every bucket; 204 = 128 (15:51 label), 4, 94 (15:56), 112 (16:01), 18, 1; instance_count active 3 and idle 0 for 15:50-15:59; pending_queue 10 at 15:51, 0 otherwise. Pub/Sub push response classes: ack only (remote_server_5xx 0 for 15:50-15:54). nack_requests 33 flat 15:50-15:55, then 23 (15:56), 1 (15:57): the 33 nacks of the 15:45 burst rolling off.
- Publishes onto bifrost.prod.create_record.v1 (gcp.pubsub.topic.send_message_operation_count): 128 (15:51 label), 4, 0, 0, 93 (15:56), 1, 0 (15:58). The 16:00 burst is not in the topic metric yet (the series ends at 15:58) but subscription sent_message_count shows 98 at 16:01 and logs show 112 created in the 16:00 minute. So there were further ~100-130 message bursts at 15:50, 15:55 and 16:00, on the same ~5-minute cadence as 15:36 and 15:45 (earlier record).
- snap.request.latency.avg, per-minute max of the metric, ilg005: 738 ms (15:50), 817 (15:51), 1134 (15:55), 1572 (16:00 and 16:02); latency.max 1912, 1991, 2308, 3874 ms. Other hosts: ilg004 808 ms avg / 1194 max at 16:00 and 16:02; ilg001 2037 avg / 4859 max at 16:02 only. snap.slot_queue_depth max: ilg005 24 at every ilg005 sample (15:50, 15:51, 15:55, 16:00, 16:02), ilg004 0, ilg001 6. snap.breaker.state 0 throughout. For contrast, same query at the 15:45 burst: ilg005 avg 9409 (15:45), 11879 (15:46), 5281 (15:47) ms, max 10794, 12571, 7113 ms, slot_queue_depth 24. So bursts of 94-128 with slot depth 24 and ilg005 at 0.7-1.6 s avg finished with no failures; the burst at 5-12 s avg latency had 33 slot timeouts.
- Held: replay-list-failures production sales_order newest entry is still DOCKBAY UK-913950 (15:02:45Z, ShipAddress.City over 30 chars, wms_precheck), before the window and unrelated. Nothing from 15:45-16:03 is held.
- Third episode: as of 16:05:12Z no warn/error logs, last age samples 18s (16:02/16:03), no creates after 16:03:30Z yet. The next on-cadence burst (about 16:05) was not yet in the data.

## Outcome
Self-resolved, P3. The 139s peak was the tail of the 15:45 burst (33 slot_timeout creates, all created by 15:47:39Z, already covered in the first thread); the monitor stayed Warn until 16:00:39Z because of its 10 minute max window. The three later bursts (15:50, 15:55, 16:00) were each fully created within the same minute with no failures, 429 or 503, while ilg005 answered in 0.7-1.6 s average. Nothing is stuck or held. Chronic pattern: ~5-minute bursts of ~94-130 sales orders (mostly PURDYFIGG) and ilg005 latency decide whether the 30s slot wait expires; third Warn episode on this group in 24h.

Not established: why ilg005 was 5-12 s at 15:45 and 15:40 but under 1.6 s after 15:50; the exact alignment of the 123/139s samples to the log timeline (Cloud Run and topic metric buckets appear labelled one minute after the log minute; the age metric's offset was not measured); the sub ack deadline and live snap-adapter concurrency/max-instance settings (not read); what drives the 5-minute publish cadence upstream; whether the 16:05 burst behaved like the previous three.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794153244711689
- First firing: [[2026-11-08-pubsub-ack-deadline-headroom-snap-adapter-sales-order-1543z]]
- Monitor: https://app.datadoghq.com/monitors/323648859
