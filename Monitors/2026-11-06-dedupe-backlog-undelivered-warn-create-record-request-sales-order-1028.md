---
tags: [datadog-triage]
date: 2026-11-06
monitor: "[FUSE][Dedupe Service] Pub/Sub backlog (undelivered messages)"
service: dedupe-service
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793960987411109"
opened_at: "2026-11-06T10:28:38Z"
severity_assessed: P4
flapping: true
outcome: self_resolved
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Dedupe sales_order subscription Warn (undelivered above 200) twice in 25 minutes: 5-minute PURDYFIGG duplicate batches, consumer acks everything

## Fired
Monitor 302511458 (`max(last_15m)` of `gcp.pubsub.subscription.num_undelivered_messages{subscription_id:dedupe_service.prod.*}` by subscription, warning 200 / critical 1000, P3, Terraform-managed; `getMonitor`) went Warn for `dedupe_service.prod.create_record_request_sales_order.v1.sub` at 10:03:38Z (alert value 385, Recovered 10:17:38Z) and again at 10:28:38Z (value 329). Slack parents in C099WKQTE8G: 10:04:50Z `1793959490.644929` and 10:29:47Z `1793960987.411109`, neither with a reply at 10:36Z. The Warn is the 200 line, not the 1000 critical; the monitor message itself says "Tune threshold to normal volume".

## Investigation
Pub/Sub metrics lag about 4 minutes (newest undelivered sample read at 10:36Z was 10:32Z, newest oldest-unacked 10:33Z).
- Why it fired (reproduced): per-minute max undelivered on the sub, 09:30-10:32Z: 385 at 10:01 and 10:02, 100 at 10:11 and 10:12, 77 at 10:17, 329 at 10:27, 581 at 10:32 (new peak); 0 in the minutes between. 385 and 329 exceed 200 inside the 15-minute window at 10:03:38Z and 10:28:38Z, so the Warn is the monitor doing what it says. The 581 at 10:32 is below 1000; critical was not reached.
- Drain: oldest-unacked max over 10:00-10:33Z was 6s on dedupe (5s at 10:32, 0 at 10:33; 3s collector, 5s tracking-service). Undelivered returned to 0 in the minutes after each earlier peak (0 at 10:03, 0 at 10:13). The undelivered series for 10:33 and later was not yet published, so the 10:32 batch drain rests on oldest-unacked 0 at 10:33.
- Consumer: push responses to this sub 10:00-10:35Z, all 16,738 were `ack_204` (no nack or error code series). dedupe-service-prod Cloud Run: 2xx only 16,756, instances 5 flat, pending queue 0, p99 concurrency 41.96 at 10:32. dedupe_service logs: warn only, no error lines since 09:30Z; 30,831 warn since 09:30Z and 3,906 of the 3,906 warn lines since 10:28Z are "Record dropped". Drop reason: all 7,045 drops since 10:25Z are `reason:duplicate`.
- Cause of the batches: shopify-connector logged 11,274 "Record published to topic" for PURDYFIGG 10:15-10:36Z; per poll (correlationId) counts 2,310 to 2,431 over six polls since 10:10Z. In dedupe, the top PURDYFIGG recordIds each arrived 13 times between 09:35 and 10:36Z (#6662637, #6662646, #6662648, #6662665, #6662666). Dedupe published 110 PURDYFIGG records (new, not dropped) since 10:25Z.
- Same batch hits collector and tracking-service subs (320 and 573 at 10:32; the same two monitors posted for them, see monitor 302536090 and 323648858 records).
- Held: `replay-list-failures` (production): newest overall 2026-11-06T09:30:42Z PURDYFIGG goods_out_confirmation (Shopify fulfilment order CLOSED, delivery, not a Snap submission); newest sales_order 2026-11-05T17:20:05Z (WILDSMITH, ShipContacts.Phone too long). Nothing from this window. No `dead_letter_message_count` series for the sub.
- Flapping: 2 Warn and 1 Recovered for this group in 25 minutes (alert events, `search_datadog_events`), earlier Warn/Recovered at 09:47Z for the sibling monitor 323648858.

## Not established
- Why shopify-connector republishes the same PURDYFIGG orders every 5 minutes in batches of about 2,300 (publisher logic not read).
- Whether the 10:32 batch drained on the undelivered series (10:33 not yet published).
- Whether peaks keep rising (385 at 10:01, 329 at 10:27, 581 at 10:32 are single-minute samples that depend on where the minute falls in the batch drain); critical is 1000.
- dedupe-service Cloud Run concurrency cap.

## Outcome
Self-resolved, P4. Each 5-minute batch lifts the sub above 200 for one or two 1-minute samples, dedupe acks every push and returns to oldest-unacked 0, nothing errors, dead-letters or is held. Warn stays latched until 15 minutes after the last sample above 200. The cause is the PURDYFIGG duplicate republish, which is worth passing to the shopify-connector owner; 581 is the highest peak so far against a 1000 critical.

## Links
- Slack threads: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793959490644929, https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793960987411109
- Monitor: https://app.datadoghq.com/monitors/302511458
- Related: Monitors/2026-11-06-pubsub-backlog-not-draining-dedupe-create-record-request-sales-order.md, Monitors/2026-11-06-pubsub-backlog-building-collector-tracking-dedupe-create-record-request-sales-order-1028.md
