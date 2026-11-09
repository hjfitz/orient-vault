---
tags: [datadog-triage]
date: 2026-11-09
monitor: "Platform elevated error rate + Snap Adapter entity creation failing + Snap host circuit breaker opened + Pub/Sub ack-deadline headroom (ilg005, one investigation)"
service: snap-adapter
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794254563681399"
opened_at: "2026-11-09T20:01:37Z"
severity_assessed: P3
flapping: true
outcome: real_minor
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# ilg005 slow writes: 4 monitors in 8 minutes, every order reached Snap, 34 lost their customisation attachment

## Fired
- 180072217 error rate (Alert, 20:01:37Z), 334832256 entity creation (Warn, 20:01:36Z, warn 5 / critical 10 distinct @recordId in 15m), 337501612 breaker opened (Alert, 20:04:52Z, thread 1794254764.872089), 323648859 ack-deadline (Alert, ~20:08:39Z, oldest unacked 277 s, thread 1794255008.231039). Error-rate thread 1794254563.681399.

## Investigation
- Monitor 1 window 19:59:37-20:01:37Z matched 7 logs, all snap_adapter, PURDYFIGG, slot_timeout, transient true, exhausted false, deliveryAttempt 1. Monitor 2 counted 7 distinct refs in its 15m window (warn 5), 12 by about 20:06Z (critical 10).
- Wave was 23 distinct refs by 20:11Z (18 PURDYFIGG, 5 STUBBLE; 28 sales_order messages received 20:06-20:10). Max deliveryAttempt 6, none exhausted, every failure transient true; replay-service newest sales_order failure is 15:03Z ESCENTRIC (unrelated).
- New today: PUT /v2/attachments hung 120 s (snap_api_error "timeout of 120000ms exceeded", 8 refs), first breaker open (20:04, 22 circuit_open logs over 12 refs, closed 20:06 onward), ilg005 adapter latency avg 70 s (20:02), 120 s (20:04), 41-60 s (20:07-20:10), max 80 s at 20:10. Earlier waves peaked at 11 s avg / 14.6 s max.
- Cheap read probes: 6 GETs 20:04:33Z four at 0.07 s and two at 4.1 s; 6 GETs 20:06:53Z all 0.05-0.07 s. Attachment GETs ~0.1 s or ~4.1 s.
- All 23 refs have a shipment in Snap (read-only CustomerRef search). 34 of 130 PURDYFIGG orders that failed today (16 from the 16Z wave, 18 from this wave) have no attachment row; the 96 others have the "Cleaning Products" PRODDETAIL row. All 130 carry one customisation. Retry hits "Entity already exists in SNAP", and createInSnap (sales-order.service.ts) throws before event.controller.ts calls handleAttachments, so retries do not add it.
- Breaker source: snap-host-breaker.ts (5xx/no response trips, 429 optional), config.ts defaults 5 consecutive failures, 30 s half-open; prod env not read. Open circuit is classified transient circuit_open (classify-snap-failure.ts), nacked and redelivered.
- Other hosts: breaker 0 on ilg001-004, ilg001 avg 0.56 s max 2.5 s. DOCKBAY (ilg001) 20 created, no failures. SPORTLUX (ilg004) no failures. EPARFUM (ilg005) 2 created, no failures.
- Maintenance/ has no record for 2026-11-09. #bifrost-general has no ILG post after 10:05Z today.

## Outcome
Real, minor on delivery (orders arrive minutes late), but ilg005 write latency is not recovered and 34 orders silently lack their attachment. Support needs to add them in Snap; engineering needs the attachment gap on the "already exists" path fixed. Not escalated: breaker closed since 20:06Z, backlog sawtooth (peak 277 s at 20:06Z, 39 s at 20:07Z), no order held or exhausted.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794254563681399
- Breaker thread: ts 1794254764.872089; ack-deadline thread: ts 1794255008.231039
