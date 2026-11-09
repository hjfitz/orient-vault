---
tags: [datadog-triage]
date: 2026-11-09
monitor: "[FUSE][Platform] Pub/Sub oldest unacked message age (any subscription) - snap_adapter.prod.create_record_sales_order.v1.sub"
service: snap-adapter
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794255270894289"
opened_at: "2026-11-09T20:14:30Z"
severity_assessed: P3
flapping: false
outcome: real_minor
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Oldest-unacked Warn (360 s) on snap_adapter sales_order sub: real peak 430 s at 20:19Z, second ilg005 hang, all orders in Snap, 35 shipments lack the customisation attachment

## Fired
Monitor 302536093 (max over 10 m, Terraform-managed, critical line > 600 s, Warn post at 300 s) went Warn at 20:14:30Z (Slack ts 1794255270.894289) on 360 s and Recovered at 20:30:29Z (ts 1794256229.422049, value 4.0 s, both posts read). Its event history over 3 days holds only this Warn (20:13:13Z) and Recovered (20:29:13Z) pair, so not flapping. Ack-deadline monitor 323648859 recovered at 20:30:49Z (ts 1794256249.925019).

## Investigation
- Per-minute max oldest_unacked_message_age (s), sales_order sub, metric timestamps: 20:02 37, 20:03 89, 20:04 157, 20:05 215, 20:06 277, 20:07 39, 20:08 98, 20:09 140, 20:10 217, 20:11 260, 20:12 281, 20:13 360, 20:14 166, 20:15 226, 20:16 249, 20:17 310, 20:18 370, 20:19 430, then 0 from 20:20 (4 at 20:26) through 20:53. The 277 s in the ack-deadline reply was only the first peak. The real peak is 430 s at 20:19, still under the 600 s critical line.
- num_undelivered_messages: 12, 12, 8, 6, 6, 9, 11, 10, 10, 6, 11, 11, 7, 7, 3, 19, 19, 19 for 20:02-20:19, then 0 (2 at 20:21, 2 at 20:26, 2 at 20:31). Peak 19 at 20:17-20:19. config_revision, master_data, purchase_order, rga and work_order subs: 0 and 0 every minute 19:58-20:38.
- Logs (snap_adapter, @environment:prod): 128 "Entity creation in SNAP failed" 20:00-20:36, all exhausted:false, transient:true (slot_timeout 91, circuit_open 22, snap_api_error 15). 45 distinct refs failed: PURDYFIGG 39, STUBBLE 5 (SC17420678/679/681/682/683), PHLUR 1 (SO414812, a business not named in earlier replies). Every one was acked by 20:18:39Z (success log after its last failure); last failure log 20:17:42Z; no warn/error snap_adapter log after 20:20 through 20:52.
- Highest deliveryAttempt: 7 on PURDYFIGG #6705913 (message 23235390452496643), first delivered 20:00:10Z, 6 failed deliveries, 7th acked 20:05:28Z. Next highest 5 (several). Limits per source master (variables.tf default 30, dead-letter = +5 = 35; prod value not read): 23 attempts below the 30 self-report. No exhausted:true log, no create_data_failure publish log, dead_letter_message_count query returned no series. "Retries exhausted" (15) logs are HTTP-level (PUT /v2/attachments, maxAttempts 1), not Pub/Sub.
- Second hang 20:15-20:18: snap.request.latency avg 13 s (20:16), 32 s (20:17), 14 s (20:18), max 120 s at 20:16-20:18; slot queue depth up to 13 at 20:15-20:20. First hang: avg 90 s (20:02), 120 s (20:04), 33-65 s 20:07-20:14. After 20:20: avg 1.2-4.8 s, max 6.1 s to 20:37; 0.5-4.5 s avg, max 6.4 s 20:40-20:52.
- Breaker (ilg005): snap.breaker.state 1 only in the 20:04 and 20:05 datapoints, 0 on every point 20:06-20:52; snap.circuit_opened 1 at 20:04, no datapoint after; breaker.rejected 4 (20:04) + 12 + 6 (20:05) = 22, 0 after. The second hang did not open the breaker.
- Probes 20:54Z (read-only curl, HTTP 200): snaplookups 0.05-0.07 s x4 and 4.18/4.20 s x2; CustomerRef shipment search 0.83, 4.92, 0.82 s; attachments GET 4.15, 4.27, 0.11 s. Recurring ~4.1 s mode on cheap reads.
- Snap checks (read-only, CustomerRef then GET /v2/attachments/SHH/{ShipmentId}) for all 151 PURDYFIGG refs that failed today (from 15:20Z), the 5 STUBBLE and the 1 PHLUR ref: every ref has a shipment. Missing attachment: PURDYFIGG 32 of 151 (16 created 16:05-16:36Z, 16 created 20:00:11-20:12:17Z), STUBBLE 3 of 5 (SC17420681/682/683, created 20:07:37Z), PHLUR 0. Earlier thread said 34 (16 + 18); this wave now shows 16 for PURDYFIGG, difference not explained. No shipment created after 20:12:17Z lacks the attachment (11 PURDYFIGG created 20:18:13-20:18:33Z all have it). The 20:00-20:12 missing ones are Stage 10; of the 16Z-wave missing, 11 Stage 15, 4 Stage 30 with QtyPicked > 0 (#6703789, #6703573, #6703684, #6703713), 1 Stage 90 with one ShipmentDespatch row (#6703666).
- Replay-service (production, newest first): newest held failure createdAt 16:50:42Z (PURDYFIGG goods_out_confirmation, Shopify FulfillmentOrder CLOSED); none created since 20:00Z.
- Maintenance/ has no record for 2026-11-09 (latest windows 2026-11-03 and 2026-11-05). #bifrost-general: only post since 10:05Z is Jack Bailey's go-lives update at 10:05:55Z, no ILG notice.

## Outcome
real_minor, P3: delivery was delayed by two ilg005 write hangs, all 45 orders reached Snap and were acked by 20:18:39Z, nothing exhausted or held, 0 s backlog since 20:20. Not escalated. Follow-up owed: customisation attachment missing on 35 shipments (32 PURDYFIGG, 3 STUBBLE), 5 of them already picked or despatched; support must add in Snap, engineering needs the "already exists" path fixed. Root cause of the ilg005 hangs not established.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794255270894289
- Related threads: error rate 1794254563.681399, breaker 1794254764.872089, ack-deadline 1794255008.231039
- Earlier record: Monitors/2026-11-09-snap-ilg005-write-hang-2001z.md
