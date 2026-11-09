---
tags: [datadog-triage]
date: 2026-11-06
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: snap-adapter
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793950005536019"
opened_at: "2026-11-06T07:25:37Z"
resolved_at: "2026-11-06T07:26:29Z"
minutes_spent: 1
severity_assessed: P4
flapping: true
outcome: self_resolved
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# 5 snap_adapter "SNAP request failed" (status 599) for PURDYFIGG sales orders, all retried and created in Snap

## Fired
Monitor 180072217 (>2 error logs in 2m) fired at 07:25:37Z. Matching errors in 07:15-07:27Z: 5 x snap_adapter "SNAP request failed", all PURDYFIGG sales_order, response status 599 (no request details logged), version e2974c0. This is not any of the five earlier patterns on this monitor (config-service Postgres, tracking-service store failed, slot_timeout, replay-service scanner 400s).

## Investigation
- Matching-error count (analyze_datadog_logs, monitor query, from 07:15Z): 5 rows, one service/message. Zero matching errors from 07:27Z onward.
- Each failed record (#6662650, #6662660, #6662677, #6662693 at 07:25:27Z; #6662675 at 07:26:26Z) logged "Retry attempted after transient failure" (attempt 1) and then "Entity created in SNAP" + 204 within 3-5s (07:25:30-32Z, 07:26:29Z).
- Same 161 PURDYFIGG creates (204) in 07:10-07:26Z; 5 "SNAP request failed" is the only occurrence in the last 24h; 7-day count of failed/retry/slot_timeout lines: 10 on 6 Nov (5 failed + 5 retry warns), 3 on 30 Oct, none other days.
- Host: PURDYFIGG -> https://ilg005liveapi.snapfulfil.net/api (DB5, site 0010 Brackmills 2). Five read-only GETs of snaplookups/RECSTATUS via curl at ~07:29Z: all 200, 55-140 ms total.
- Snap error/warn lines 24h, excluding "Consignment StU not found" warns: snap_adapter error 14, warn 5; snap-polling-service none (excluding StU warns).
- Load: all-business creates in 07:20-07:30Z buckets were 51 and 102, so a burst of creates ran alongside the failures; whether that caused them is not established.
- 5xx in prod fuse logs since 07:10Z (http.status_code / response.status / statusCode / status_code 500-599): only these 5 (response.status 599).
- Pub/Sub max oldest_unacked_message_age over all prod subscriptions, 45 min to ~07:30Z: 23s max.
- Maintenance: no Maintenance/ record covers 07:25Z on 6 Nov (latest window was 5 Nov 10:00Z emergency patch, all DBs).
- Held records: replay-list-failures (production) createdAt 2026-11-06: 21 held, all PURDYFIGG goods_out_confirmation, created 07:06:38-07:06:40Z, reason "Fulfillment order ... is CLOSED in Shopify, so it cannot be fulfilled", failurePoint confirmation.delivery_shopify. Different record type, service and time from the alerted errors. Same reason on 5 Nov (647 held that day, latest 21:40Z); PURDYFIGG holds 17,711 failures in total.
- Monitor flapping: 6 firings from 5 Nov 23:29Z to 6 Nov 07:25Z, each a different cause.

## Not established
- Why snap_adapter got status 599 (request/path/baseUrl logged as unknown), and whether Snap slowness or our own concurrency under the create burst caused it.
- Other businesses on ilg005: lookup-snap-instance returned businessCount 0, so the per-instance comparison was not possible; the errors carried PURDYFIGG only.
- Why 21 goods_out_confirmations for closed Shopify fulfillment orders were held at 07:06Z, and whether they need action; not part of this alert.

## Outcome
Self-resolved, P4. No Snap outage, nothing from this alert held. The 07:06Z PURDYFIGG held confirmations are a separate, recurring Shopify-closed pattern worth a look. No ticket filed.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793950005536019
- Monitor: https://app.datadoghq.com/monitors/180072217
