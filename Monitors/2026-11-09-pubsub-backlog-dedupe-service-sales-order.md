---
tags: [datadog-triage]
date: 2026-11-09
monitor: "[FUSE][Platform] Pub/Sub backlog building (any subscription)"
service: dedupe-service
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://slack.com/archives/C099WKQTE8G/p1794241172331659"
opened_at: "2026-11-09T16:18:10Z"
severity_assessed: P4
flapping: true
outcome: self_resolved
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# Pub/Sub backlog Warn on dedupe_service.prod.create_record_request_sales_order.v1.sub (205 undelivered)

## Fired
Warn (200) on `max(last_15m)` of `num_undelivered_messages` for the dedupe_service sales_order subscription, value 205. Follow-on from the 16:08Z Warn on the collector subscription (thread 1794240569.068789), one hop later.

## Investigation
- Metric per minute (gcp.pubsub.subscription.num_undelivered_messages, this subscription): 0 through 16:10, 91 at 16:11, 0 at 16:12-16:15, 205 at 16:16, 0 at 16:17. Last point available was 16:17 (16:18 not yet ingested).
- oldest_unacked_message_age: 0 s everywhere except 1 s at 16:16. ack_message_count: 878 at 16:11, 982 at 16:16.
- dedupe_service logs (POST /events/v1/record/request/sales_order, `Incoming record received`): 16:05 = 854, 16:10 = 933, 16:15 = 1032. Each equals `Record dropped` + `Record published to topic` (735+119, 839+94, 925+107). The 16:15 wave is one correlationId (117242ab-b859-47c6-bdb7-5c4adaaf36fb, 1013 POSTs, 204 each). Metric peaks follow each wave by about 1 min (16:11, 16:16).
- dedupe_service logs in last 6 h: no `error` status; the only warn is `Record dropped` (the duplicate-drop path). Nothing else outside info/debug found with the drop/publish messages excluded (top rows are info request lines).
- A 16:20 wave has started (184 `Incoming record received` in the 16:20 minute by 16:20:xxZ); its metric effect not yet visible.
- dedupe-summary (production): 238,969 records in the store (sales_order 207,217, duplicatesBlocked 4,365,300; return_goods_authorization and work_order 0). dedupe-list sales_order since 00:00Z: 2,702, newest storedAt 16:15:14Z, PURDYFIGG, dedupeCount 0. These are gate entries, not shown to be failed submissions.
- replay-list-failures (production), PURDYFIGG sales_order, createdAt 2026-11-09: 0. Newest failures overall are unrelated and earlier: ESCENTRIC sales_order 15:03Z (ShipContacts.Phone over 20 chars, wms_precheck), AYMSTUDIO PO 14:15Z, SAIRA sales_order 13:40Z, PURDYFIGG goods_out_confirmation 13:25Z (Shopify fulfilment order closed).
- 7 d hourly max of this subscription (rollup max 3600): 11 of 168 hourly buckets at or above 200 including the current one (peaks 581, 623, 723, 407, ...), none at or above 1000.
- Maintenance/: newest record covering a window is 2026-11-05 (emergency patch); none covers 2026-11-09.

## Outcome
Self-resolved, P4. A one-minute spike from the PURDYFIGG 5-minute burst; consumer acked 982 that minute and oldest unacked age peaked at 1 s. Monitor is chronically noisy at the 200 warn line; a count-only threshold on a bursty subscription is worth a retune (age condition) ticket.

## Not established
- Backlog after 16:17Z (metric lag), including the effect of the 16:20 wave.
- What drives the 5-minute PURDYFIGG bursts.
- Monitor Warn/Recover history for this specific group (events search for the monitor returned nothing); only hourly peaks were checked.
- When the monitor recovers; it holds Warn for 15 m after the last >200 point (16:16Z) unless another wave exceeds 200.
- #bifrost-general pin and ILG mail not checked.

## Links
- Slack thread: https://slack.com/archives/C099WKQTE8G/p1794241172331659
