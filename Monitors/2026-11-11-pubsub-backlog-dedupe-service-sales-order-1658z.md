---
tags: [datadog-triage]
date: 2026-11-11
monitor: "[FUSE][Dedupe Service] Pub/Sub backlog (undelivered messages)"
service: dedupe-service
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794416384173529"
opened_at: "2026-11-11T16:58:38Z"
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# Backlog Warn (710 undelivered) on the dedupe sales_order sub: one-minute sample after a 1,633-record PURDYFIGG wave, 0 the next minute, not coupled to the tracking-service release

## Fired
Monitor 302511458 (Dedupe Service, P3, Terraform-managed, `max(last_15m)` of `num_undelivered_messages` by subscription over `subscription_id:dedupe_service.prod.*`, warning 200 / critical 1000 from `getMonitor`, no age condition in the query) went Warn on `dedupe_service.prod.create_record_request_sales_order.v1.sub` at 16:58:38Z, value 710. Slack post 16:59:44Z, thread 1794416384.173529 (no replies when read at about 17:07Z, so nothing posted by the watcher). The Platform sibling 302536090 also went Warn at 16:58:10Z on this sub and on the tracking-service sub (events API); not triaged here.

## Investigation
- **Per-minute `num_undelivered_messages`, dedupe sub, labels 16:30-17:02 (latest available at 17:06Z; GCP lag about 4 min).** 0 except 1 (16:32), 171 (16:46), 710 (16:56), 644 (17:01). Reads 0 at 16:57-17:00 and 17:02. Peak 710 at 16:56. `oldest_unacked_message_age`: 6 s (16:32), 2 s (16:46), 8 s (16:56), 5 s (17:01), 0 s every other minute. 7-day hourly maxima (4 Nov 17:00Z-now): undelivered 723 (7 Nov 16:00Z hour; 710 is not a new high), oldest unacked 27 s (7 Nov 07:00Z hour).
- **Wave sizes (dedupe_service logs, `Incoming record received`, sales_order, per log minute).** 16:30 1,225; 16:35 1,303; 16:40 1,371; 16:45 1,478; 16:50 1,530; 16:55 1,633; 17:00 1,720 (singletons of 2 at 16:38 and 16:53). The 17:05 wave had 1,752 received by 17:05:36Z (5-minute bucket, partial). The 16:55 wave arrived within about 40 s (10 s bins from 16:55:00: 215, 708, 15, 695); the 16:45 wave within about 20 s (152, 1,325, 1). Business split of the 16:55 minute: PURDYFIGG 1,615, ESCENTRIC 10, ESCENTRICPL 7, SAIRA 1; 16:45: PURDYFIGG 1,461, ESCENTRIC 10, ESCENTRICPL 6, SAIRA 1. Totals 16:30-17:01:34Z: 10,264 received, 9,592 `Record dropped` (all reason `duplicate`), 671 `Record published to topic`. So 93.5% dropped (the 13:58Z record had 95.7% over 13:30-14:00Z, and the 9 Nov 17:25Z wave 98.9%, from those records). Only some waves sample high (171, 710, 644); the 16:30, 16:35, 16:40, 16:50 waves read 0.
- **Pushes, nacks, dead letters.** `push_request_count` for the dedupe sub, 16:30-17:03: only `response_code:ack_204`; per wave 1,190+35 (16:31/16:32), 1,286+17, 236+1,123+13+1, 1,441+36, 1,504+26, 1,470+163 (16:56/16:57) = 1,633, 1,623+97 (17:01/17:02) = 1,720. `nack_requests`, `expired_ack_deadlines_count`, `dead_letter_message_count`: no series. `num_undelivered_messages` max across all `*dlt*` subscriptions: 0 each minute 16:30-17:03 (the earlier per-subscription listing showed every `*dlt*` sub at 0). GCP minute labels trail the log minute by 1-2 minutes.
- **Dedupe itself.** `gcp.run.container.instance_count` dedupe-service-prod: 5 active every minute 16:30-16:59, 0 idle. Logs carry one revision, dedupe-service-prod-00053-m72, 16:00-17:04; last dedupe-service deployment is 1eeac6f on 5 Nov 16:37Z (GitHub deployments). Status counts 16:30-17:05:36Z: info 24,806, warn 11,307 (equals the `Record dropped` count), debug 37, no error; `status:(warn OR error) -"Record dropped"`: 0. `gcp.run.request_count` dedupe-service-prod: 2xx only, 16:56 = 1,628.
- **Downstream (snap_adapter), 5-minute buckets.** Received (sales_order) equals dedupe published in every bucket 16:30-17:05 (106, 86, 85, 110, 69, 120, 109, 37; the 17:05 bucket partial), so duplicates do not reach Snap. Created: 106, 86, 85, 109, 69, 120, 107, 37. Gaps: 16:45 bucket -1 (`Entity creation in SNAP failed`, PURDYFIGG #6719674, 16:45:22Z, replay-service failure fd964af2-d23b-4cb3-a4be-35accdd120a1, `create.snap_api`, "Line1 - Invalid Text on line SHLEM3KTFY", attempts 0; dedupe logged `Dedupe gate held on permanent failure` once at 16:45); 17:00 bucket -2 (DOCKBAY UK-914987 failed 17:04:12Z, replay-service failure 0da31742-16d1-4452-8180-d46a44c28a3a, `create.wms_precheck`, "ShipAddress.City ... <=30 characters", attempts 0; the other record has neither a created nor a failed log as of 17:06Z). 16:05-17:00 window: 1,017 received, 1,016 created, 1 failed. snap_adapter warn/error in 16:05-17:05: only those two failure lines.
- **Snap health.** `snap.breaker.state` max 0 on all 11 snap_host series each minute 16:05-17:05 (0 closed, 0.5 half-open, 1 open); `snap.breaker.rejected` and `snap.circuit_opened`: no data; `snap.request.failure`: 1 (ilg005liveapi, 16:45 bucket); `snap.request.success` ilg005liveapi 48-223 per 5 min. Log search over snap_adapter and the snap polling services for 429, slot_timeout, "Too Many Requests", circuit, 16:05-17:05: 0 lines. `snap.slot_wait.*` (count, avg, p95, max): no data. `snap.slot_queue_depth` (snap-adapter) per 5-min bucket avg 3.84-13.83, min 0, max 24; `snap.rate_queue_depth` max 0-20 (12 at 16:55, 20 at 17:00). `snap.request.latency.95percentile` ilg005liveapi 1,848-3,075 (units as returned). snap_adapter sub: undelivered max 53 (16:47), oldest unacked max 12 s (16:32, 16:42), 0 at every other minute through 17:03. Maintenance/ vault: newest record dated 4 Nov, none covering today.
- **Tracking-service test.**
  - tracking-service has its own sub, `tracking-service.prod.create_record_request.sales_order.v1.sub`. GitHub deployments (tracking-service, terraform-prod): fe6ef98 "Flip prod to MongoDB and turn dev dead-lettering back on (#41)" created 16:26:55Z, success 16:28:33Z (log revision 00022-xgx from 16:28); 83ffea4 "Turn prod dead-lettering back on after the MongoDB cut (#42)" created 16:44:35Z, success 16:46:23Z (revision 00023-xtp from 16:46).
  - Tracking sub: undelivered 8,975 at 16:29 (6,755-8,982 over 16:20-16:29), 414 at 16:30, 25, 22, 22, 12, 9, 3, 1, 1, then 0 from 16:39; oldest unacked 4,151 s (16:30) rising to 4,571 s (16:37-16:38); pushes at 16:30: 4,849 `ack_204` plus 469 answered 429 (`unreachable_5xx_error_429`); a `nack_requests` series 2,549 (16:30) down to 469 (16:39); one `store failed; nacking for redelivery` log in the 16:25 bucket.
  - Dedupe sub over the same minutes: 0, 0, 1 (oldest 6 s at 16:32), then 0; only `ack_204`; no nack series.
  - Tracking sub in the dedupe sub's spike minutes: 141 (16:46), 236 (16:56), 73 (17:01), with 1,477 / 1,633 acks at 16:46 / 16:56. Both subs receive the same waves.
  - The dedupe sub alerted before any of today's tracking-service prod deploys: 16 Warn and 15 Recovered events for monitor 302511458 on this sub since 4 Nov 17:00Z (6 Nov: 5 Warn; 7 Nov: 7; 9 Nov: 2; 11 Nov: 2, at 13:58 and 16:58).
- **Flapping.** Events API pull 4 Nov 17:00Z-now, this sub: Warn 6 Nov 10:03, 10:28, 19:18, 20:38, 22:53; 7 Nov 12:18, 15:38, 16:32, 16:58, 17:28, 18:42, 19:02; 9 Nov 16:18, 17:28; 11 Nov 13:58, 16:58. Earlier records: Monitors/2026-11-09-pubsub-backlog-dedupe-service-sales-order-1728z.md (monitor_mistuned), Monitors/2026-11-11-pubsub-backlog-dedupe-tracking-create-record-request-sales-order-1358z.md (self_resolved).

## Outcome
P4, monitor_mistuned. Not stuck: oldest unacked peaked at 8 s, undelivered read 0 the minute after each sample, every push was ack_204, no nack, expired deadline or dead letter, no dedupe error, and snap_adapter received exactly what dedupe published. The count-only Warn at 200 on `max(last_15m)` is tripping on one-minute samples of a 20-40 s burst, and waves are growing (1,225 to 1,720 over 16:30-17:00). The tracking-service release does not explain it: the same pattern fired on 6, 7, 9 and 11 Nov before it, and the dedupe sub read 0 while the tracking sub drained. Retune (add an age condition or raise the warn line) is the follow-up; no ticket filed (read-only run). The two Snap-side create failures above are separate from this alert and are not caused by the backlog.

## Not established
- Why only some waves sample high (171, 710, 644 against 0 for four others); sampling phase against a 20-40 s burst is a lead, untested.
- The sample for the 17:05 wave (label 17:06 not available at 17:06Z), and when the monitor returns to OK: not before the 17:01 point leaves the 15-minute window (about 17:16Z), later if a wave samples above 200.
- Why PURDYFIGG sends 1.2-1.7k records every 5 minutes and why the waves grow (shopify-connector not read; the "last 3 hours of open orders" mechanism is from the brief, unverified).
- Whether the 1,000 critical line will be reached by a sample (current maximum 710).
- The one record in the 17:00 bucket with neither a created nor a failed log at 17:06Z (in flight or other).
- Whether support already knows about PURDYFIGG #6719674 (reported in the channel at 16:59Z by the watcher) and DOCKBAY UK-914987; whether a replay of either is safe.
- Any mechanism linking the 83ffea4 deploy window (16:44:35-16:46:23Z) to the 16:46 sample of 171; none observed.
- #bifrost-general Snap pin and ILG mail; Jira for an existing retune ticket (not searched this run).

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794416384173529
- Monitors: https://app.datadoghq.com/monitors/302511458, https://app.datadoghq.com/monitors/302536090
- Earlier: Monitors/2026-11-09-pubsub-backlog-dedupe-service-sales-order-1728z.md, Monitors/2026-11-11-pubsub-backlog-dedupe-tracking-create-record-request-sales-order-1358z.md, Monitors/2026-11-11-tracking-service-hold-mode-on-prod-1518z.md
