---
tags: [datadog-triage]
date: 2026-11-09
monitor: "[FUSE][Platform] Pub/Sub backlog building (any subscription)"
service: dedupe-service
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://slack.com/archives/C099WKQTE8G/p1794245363332169"
opened_at: "2026-11-09T17:28:10Z"
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# Pub/Sub backlog Warn on dedupe_service.prod.create_record_request_sales_order.v1.sub (268 undelivered)

## Fired
Second Warn today (first 16:18:10Z, thread 1794241172.331659) on `max(last_15m)` of `num_undelivered_messages` > 200 for the dedupe_service sales_order subscription. Value 268. The monitor's Terraform-managed query carries a 1,000 critical threshold and no age condition.

## Investigation
- Per-minute `num_undelivered_messages` (this subscription), 17:00-17:27Z: 0 except 1 at 17:01, 9 at 17:02, 130 at 17:06, 48 at 17:11, 54 at 17:21, 268 at 17:26; 0 at 17:27. Every peak is a single minute and drains the next minute. 16:00-17:00Z peaks, same pattern: 91 (16:11), 205 (16:16), 315 (16:21), 273 (16:26), 38 (16:31), 161 (16:36), 17 (16:41), 90 (16:51).
- `oldest_unacked_message_age`, this subscription, 17:00-17:27Z: max 6 s (at 17:26), 0 s in every other minute apart from 2-3 s at the other peaks. ack_message_count totals per wave match the wave size (e.g. 511+1079+59 across 17:05-17:07 vs 1,647 received).
- dedupe_service `Incoming record received` per minute, sales_order, 5-minute waves: 15:55=646, 16:00=751, 16:05=854, 16:10=933, 16:15=1032, 16:20=1046, 16:25=1055, 16:30=1094, 16:35=1194, 16:40=1228, 16:45=1283, 16:50=1403, 16:55=1513, 17:05=1647, 17:10=1656, 17:15=1672, 17:20=1676, 17:25=1688, 17:30=1696. The 17:00 wave was 649+969 across two minutes. Waves grew steadily through 16:xx and have been near-flat (1.65k-1.70k) since 17:05.
- Peak wave 17:25: 1,688 received (1,669 `Record dropped` + 19 `Record published to topic`), 98.9% dropped. Arrival was concentrated in about 25 s (17:25:03-17:25:27Z), busiest second 294 records. A dedupe_service instance logged Dependency connected / Cache service initialized / Server listening at 17:25:29-30Z; no causal link established.
- Business split 17:00-17:32Z (dedupe logs): PURDYFIGG 9,972 received / 9,758 dropped / 221 published; ESCENTRIC 70 received, 70 dropped; SAIRA 24 / 23 dropped / 1 published; ESCENTRICPL 21 / 21 dropped; DOCKBAY 20 published; STUBBLE 2, WILDSMITH 1 published; EPARFUM 1 dropped.
- dedupe_service status in 17:00-now: only `Record dropped` at warn; 7 debug lines; no error status.
- Downstream: snap_adapter `Incoming record received` 261 sales_order + 1 master_data and `Entity created in SNAP` 245 sales_order + 1 master_data at 17:00-17:31Z. Per-minute created matches dedupe published through the 17:25 wave. The 17:30 wave: 1,696 received, 17 published, snap_adapter received 17 and created 2 (17:30) + 15 (17:31). snap_adapter has no error/warn lines, no slot_timeout or 429 text in 17:00-now. Fuse-wide error/warn (excluding Record dropped) in the window: snap-polling-service warns (Consignment StU not found, stock movement direction, confirmation withheld), shopify-connector warns, replay_service 404 warns on probes; none on the create path.
- snap_adapter subscription (downstream): undelivered peaked 69 at 17:03, oldest unacked max 112 s at 17:05 (2 messages), 0 at 17:06; 14-29 s at 17:07, 17:12, 17:17-17:18, 17:22-17:23; 0 since 17:24.
- replay-service (production), failures created 2026-11-09: newest is 16:50:42Z, so none created since 17:00. Newest 14 are PURDYFIGG goods_out_confirmation (Shopify fulfillment order CLOSED, confirmation delivery, not a Snap submission). Older today: DOCKBAY PO 16:38, ESCENTRIC SO 15:03, AYMSTUDIO PO 14:15, SAIRA SO 13:40, all `wms_submission` failures from before this window and not PURDYFIGG sales orders.
- dedupe-summary (production): 239,791 gate entries (sales_order 208,036, duplicatesBlocked 4,385,983). dedupe-list PURDYFIGG sales_order since 17:00: 238 entries, newest storedAt 17:30:18Z, dedupeCount 0. These are gate entries, not shown to be failed submissions.
- Maintenance/ vault: no record with a window on 2026-11-09 (latest windows 05 Nov and earlier).
- Flapping: monitor events for this subscription in the last 24 h: Warn 16:18:10Z, Recovered 16:41:10Z, Warn 17:28:10Z. Hourly max over 24 h: 315 (16:00Z hour), 268 (17:00Z hour), 178 (18:00Z 08 Nov hour), 176 (23:00Z 08 Nov hour), under 150 otherwise. The same monitor also fired today on collector (16:08Z), snap_adapter (08:23Z) and tracking-service (08 Nov 18:38Z) subscriptions.

## Outcome
P4, monitor_mistuned. The signal is a one-minute spike after each 5-minute PURDYFIGG wave that drains within a minute (oldest unacked 6 s at the worst point), and every record dedupe published reached snap_adapter and was created. The count-only threshold of 200 on a bursty subscription is what fires. Wave size has grown from 646 to about 1,690 records over 1.5 h, which is why peaks now cross 200; why PURDYFIGG sends that many, mostly duplicate, records every 5 minutes is not established. A ticket for retuning (add an age condition or raise the warn) is worth raising. The Warn stays until the 15-minute window ages out (about 17:41Z) unless another wave exceeds 200 (the 17:30 wave's metric effect was not yet visible).

## Not established
- Backlog after 17:27Z (metric lag), including the 17:30 wave.
- Why PURDYFIGG sends 1.6-1.7k records per wave, 98.9% duplicates, or why it grows.
- Whether the dedupe instance start at 17:25:29Z relates to the 268 peak.
- Why the downstream snap_adapter subscription reached 112 s oldest unacked at 17:05.
- #bifrost-general pin and ILG mail not checked.

## Links
- Slack thread: https://slack.com/archives/C099WKQTE8G/p1794245363332169
- Earlier Warn today: Monitors/2026-11-09-pubsub-backlog-dedupe-service-sales-order.md
