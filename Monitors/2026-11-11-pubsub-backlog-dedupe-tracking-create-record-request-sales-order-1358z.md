---
tags: [datadog-triage]
date: 2026-11-11
monitor: "[FUSE][Platform] Pub/Sub backlog building (any subscription) x2 (dedupe, tracking) + [FUSE][Dedupe Service] Pub/Sub backlog (undelivered messages)"
service: dedupe-service
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794405565519209"
opened_at: "2026-11-11T13:58:10Z"
severity_assessed: P4
flapping: true
outcome: self_resolved
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# Backlog Warn (247 undelivered) on the dedupe and tracking-service create_record_request sales_order subs: one-minute sample after a 294-record PURDYFIGG-led wave, 0 by 13:58

## Fired
Three Warn posts, none replied to when read at about 14:00Z. Monitor 302536090 (Platform, warn 200 / critical 1000, `max(last_15m)`, count only, P2, Terraform-managed) on the dedupe sub (thread 1794405565.519209, 13:58:10Z) and the tracking-service sub (1794405567.412889, 13:58:10Z), both value 247. Monitor 302511458 (Dedupe Service, warning 200 / critical 1000 via `getMonitor`, P3, Terraform-managed) on the dedupe sub (1794405589.575639, 13:58:38Z), value 247.

## Investigation
- **Per-minute `num_undelivered_messages`, 13:25-14:02Z.** Dedupe sub: 0 except 3 (13:37), 5 (13:47), 247 (13:57), then 0 at 13:58, 13:59, 14:00, then 10 at 14:01 and 14:02. Tracking sub: 0 except 5 (13:47), 247 (13:57), 0 at 13:58-14:01, 10 at 14:02. snap_adapter sub (`snap_adapter.prod.create_record_sales_order.v1.sub`): 0 except 4 (13:42) and 3 (13:52); 0 at 13:54-14:02. Last points available at about 14:05Z were 14:02.
- **`oldest_unacked_message_age`.** 0 s at every minute 13:54-14:03 on all three subs; in 13:25-now the peaks were 1 s (dedupe and tracking at 13:47) and 5 s / 6 s (snap_adapter at 13:42 / 13:52). 24 h max (10 Nov 14:00Z-now, aggregator max): dedupe 1 s, tracking 3 s, snap_adapter 52 s. 24 h max undelivered: dedupe 247, tracking 247, snap_adapter 64. Since the 11:36Z snap-adapter deploy: snap_adapter sub max 14 undelivered, 6 s oldest.
- **The wave (dedupe_service logs, `Incoming record received`, sales_order).** 13:55 minute = 294 (284 `Record dropped` + 10 `Record published to topic`), all between 13:55:03 and 13:55:10Z. By business 13:55-13:57: PURDYFIGG 269 (one correlationId 41bcf4a7-a0dd-4a48-ac79-7fb26e2509d5), ESCENTRICPL 9, SAIRA 9, ESCENTRIC 7. Waves every 5 minutes: 13:30 = 280, 13:35 = 278, 13:40 = 281, 13:45 = 279, 13:50 = 290, 13:55 = 294, 14:00 = 292 (283 dropped + 9 published). Totals 13:30-14:00:52Z: 2,017 received, 1,931 dropped, 85 published. The one received record with no dropped/published log is the WILDSMITH SO-29746 failure-release event at 13:38:40Z (`Dedupe gate held on permanent failure`). PURDYFIGG was 1,829 of the received count over 13:30-14:02Z.
- **Wave size vs peak, last 24 h.** Largest 5-minute sales_order wave was 1,633 (10 Nov 16:50Z); 5-minute maxima per hour 1,507-1,633 for 16:00-18:59Z on 10 Nov. Hourly max undelivered over 16:00-19:59Z on 10 Nov: dedupe 0, tracking 116 (17:00) and 33 (18:00). Today's 294-record wave sampled 247 on both subs, the 24 h maximum for each.
- **Pushes, nacks, dead letters.** `push_request_count` (13:30-now, 5-minute bins) on dedupe and tracking subs: only `ack_204`, 281, 288, 281, 279, 298, 294 each; snap_adapter sub only `ack_204` (7, 16, 11, 5, 24, 10). `nack_requests`, `expired_ack_deadlines_count` and `dead_letter_message_count` for the three subs returned no series. All `*dlt*` subscriptions: undelivered and oldest age avg 0 over 13:00-now. Cloud Run `gcp.run.request_count` for dedupe-service-prod, tracking-service-api-prod and snap-adapter-prod since 13:30: 2xx series only.
- **Consumer logs.** dedupe_service 13:30-now: info 4,120, warn 1,931 (all `Record dropped`), debug 3; 0 non-drop warn/error. tracking-service: 0 error/warn lines since 13:30; 0 `store failed` lines since 10 Nov 14:00Z. The tracking filter reproduces the 24 `store failed; nacking for redelivery` lines at 10 Nov 01:35Z, so 0 is meaningful.
- **Firestore (database tracking-service), `gcp.firestore.api.request_count` by response_code, 13:25-13:58 bins.** `ok` 11,531, `aborted` 6 (1 each at 13:31, 13:47, 13:51, 13:55; 2 at 13:56); no `resource_exhausted`, no `invalid_argument`. The same query returns `resource_exhausted` 2 (01:35) and 22 (01:36) with matching `invalid_argument` on 10 Nov, so those codes would appear if present.
- **Downstream (snap_adapter).** 13:30-14:00Z (5-minute buckets): 85 received, 84 created; the difference is WILDSMITH SO-29746, which failed pre-check at 13:38:39Z (the only snap_adapter error in 13:30-now and since 11:00Z; version 841717e). `snap_adapter` log search since 11:00Z for 429, slot_timeout and circuit text: 0. `snap.request.failure`: no data on any snap_host since 11:30Z (`snap.request.success` present, e.g. ilg005liveapi 1,211). `snap.breaker.state`: avg 0 on every snap_host series since 11:30Z (both `/api` and bare-origin spellings present); `snap.breaker.rejected` and `snap.circuit_opened`: no data.
- **Held / held records.** replay-list-failures (production), sales_order, createdAt 2026-11-11: newest is WILDSMITH SO-29746 13:38:40Z (`ShipContacts.Phone` over 20 characters, create.wms_precheck, source sftp, attempts 0, id 528cfbd3-79c4-4819-b625-c44c58c9c748); nothing for PURDYFIGG sales_order from this window (newest PURDYFIGG sales_order hold is 08:15Z, `ShipAddress.Name` over 50). dedupe-list (production, read-only): SO-29746 gate entry still held (storedAt 13:38:39Z, dedupeCount 0); 115 sales_order gate entries stored since 13:30Z (newest 14:05:08Z), the five newest listed all dedupeCount 0. dedupe-summary (production): 247,402 entries, sales_order 215,604, duplicatesBlocked 4,601,900. No dedupe-release, replay-retry or write called.
- **Deploys, last 24 h (GitHub deployments, environment terraform-prod, all harry-fitzgerald_gfsdev).** snap-adapter repo: 692d432 (snap-queue-polling-service request timeout / single probe, created 11:01Z, success 11:04Z), 841717e (snap-adapter SNAP_CB_TRIP_ON_429 on by default, 11:36Z / success 11:39Z), 5f4773e (snap-queue-polling-service SNAP_NORMALISE_HOST_KEY on by default, 12:56Z / success 12:58Z). tracking-service: 2387f18 (11:02Z / 11:05Z), 2c86cd6 (11:29Z / 11:31Z), b4b9e49 (12:45Z / 12:46Z), 01ea2e9 (12:51Z / 12:53Z); commit subjects are MongoDB store work (open the MongoDB store from every binary; pass the MongoDB connection and a store switch to the API service; freeze notes under the hold and add the Firestore to MongoDB import; hold dev ingest for the MongoDB cut). sftp-connector 91d70de created 10 Nov 14:00:01Z. dedupe-service, shopify-connector, collector, fapi, replay-service, config-service: no deployment newer than 10 Nov 14:00Z. snap_adapter logs carry version 841717e at 13:38Z; dedupe_service logs carry 1eeac6f.
- **Topic relation.** lookup-topic create_record_request: subscribers dedupe-service, collector, tracking-service; tracking-service has one recordType-filtered push sub per type.
- **Maintenance/.** Newest windows are 4-5 Nov (test DB patch, emergency patch); no record with a window on 9-12 Nov. Not Snap-related in any case.
- **Flapping / history.** Events API, 24 h from 10 Nov 14:00Z: only these three alert events for monitors 302536090 and 302511458 (13:58:10Z x2, 13:58:38Z). Events API 4-day pull (read to 7 Nov 17:42Z only, size-capped): monitor 302536090 Warned on both subs on 7 Nov at 15:38:10Z, 16:33:10Z and 17:28:10Z, plus tracking at 16:48:10Z and dedupe at 16:58:10Z. Earlier records in this folder cover the dedupe sub on 9 Nov (16:18Z, 17:28Z) and the tracking sub on 6 and 7 Nov, so the tracking sub is not new to this monitor.
- **Sibling alerts seen in the channel.** Monitor 323648858 (Platform "backlog not draining", trend) posted Warn for the tracking sub (ts 1794405763.254949, 14:02:43Z) and dedupe sub (1794405765.453159, 14:02:45Z), and Recovered posts at 14:04:46Z and 14:04:48Z (1794405886.194809, 1794405888.230419). Not part of this triage.
- **Jira.** FUSE search (created from 1 Nov; summary backlog / undelivered / monitor / Pub/Sub): only FUSE-1341 (unrelated, Done). FUSE search for a tracking-service Firestore / store failed ticket since 25 Oct: none. No ticket filed here.

## Outcome
Self-resolved, P4. The 247 was a single 1-minute sample (13:57) after the 13:55 wave of 294 records that arrived in 7 seconds; both subs read 0 from 13:58, every push was acked (only ack_204), oldest unacked stayed at 0-1 s (24 h max 3 s), no dead letters, no nacks, no errors on dedupe or tracking-service, no Firestore RESOURCE_EXHAUSTED, and the snap_adapter sub and Snap breaker show no downstream pressure. Not stuck, so none of the P1/P2 triggers apply. The count-only 200 warn line keeps firing on sub-minute samples; a retune (add an age condition or raise the warn line) is still the follow-up, with no ticket found.

## Not established
- Why this 294-record wave sampled 247 on both subs while the 1.5-1.6k waves of 10 Nov 16:00-19:00Z sampled 0 on the dedupe sub (sampling phase against a 7 s burst is a lead, untested).
- Backlog after 14:02Z (metric lag), including the 14:00 wave (10 at 14:01-14:02).
- When 302536090 and 302511458 return to OK (15-minute window; no Recovered post read for these groups).
- Why PURDYFIGG sends a wave every 5 minutes, and the "last 3 hours of open orders" mechanism (shopify-connector not read).
- Whether the four tracking-service MongoDB-cut deploys, snap-adapter afdb226 / dd86e1a (10 Nov, before my 24 h list window) or the three 11 Nov snap deploys affect anything; nothing in the evidence points to them.
- Per-event completion on tracking-service (no success log) and why Firestore returned RESOURCE_EXHAUSTED on 10 Nov (no quota data read).
- #bifrost-general Snap pin and ILG mail.

## Links
- Slack threads: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794405565519209 (302536090 dedupe), p1794405567412889 (302536090 tracking), p1794405589575639 (302511458 dedupe)
- Monitors: https://app.datadoghq.com/monitors/302536090, https://app.datadoghq.com/monitors/302511458
- Earlier: Monitors/2026-11-09-pubsub-backlog-dedupe-service-sales-order.md, Monitors/2026-11-09-pubsub-backlog-dedupe-service-sales-order-1728z.md, Monitors/2026-11-10-platform-elevated-prod-error-rate-tracking-service-store-0135z.md
