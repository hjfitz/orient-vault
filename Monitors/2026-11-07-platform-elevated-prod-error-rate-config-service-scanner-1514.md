---
tags: [datadog-triage]
date: 2026-11-07
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: config-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794064548358519"
opened_at: "2026-11-07T15:14:37Z"
resolved_at: "2026-11-07T15:19:00Z"
minutes_spent: 5
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# Error-rate monitor tripped by 5 malformed-JSON scanner probes on config-service (one-second burst at 15:14:15Z)

## Fired
Monitor 180072217 (log alert, more than 2 matching error lines in 2m). Triggered 15:14:37Z, post 15:15:48Z (parent ts 1794064548.358519), no reply when checked at about 15:17Z. Status read OK again at 15:18Z.

## Investigation
- 1 Monitor query run for 15:05-15:20Z, grouped by service and message: 5 lines, all config-service "Error unhandled", all stamped 15:14:15Z. Per-minute count since 14:48Z: 5 in the 15:14 minute, none before, none 15:15-15:19 (query to now).
- 2 The 5 lines are POSTs to /run, /code/blocks/exec/start, /api/v1/code/blocks/exec/start, /code/blocks/exec/code and /api/v1/code/blocks/exec/code. Each body is a JSON-shaped string carrying a shell command (crypto-miner download and start), and the error is `entity.parse.failed` (underlying status 400). It failed at body parsing, before any handler.
- 3 The info logs of the same second show those five requests answered "500 Internal Server Error" and a set of other probes (GET /, POST /, /foo.jsp, /crumbIssuer/api/json, PUT *.aspx and *.jsp) answered "401 Unauthorized". So this is internet scanner traffic against config-service. Revision config-service-prod-00071-czr, version 6b73684.
- 4 Same scanner family elsewhere today (text search for the probe paths and strings, 00:00-15:25Z): replay_service 15 warn lines (404 for /.git/config and /cdn-cgi/trace among them), fuse-ui 17, config-service 10, others info. Matches the 6 Nov replay-service scan record.
- 5 Only 5xx logged by any prod service 14:48-15:20Z: those 5 (query on "500 Internal Server Error" / 5xx attribute by service).
- 6 Pub/Sub oldest-unacked, max per subscription 14:48-15:20Z (top 6): snap_poll_customer 60 s, shopify goods_out_confirmation 26 s, snap_adapter create_record_sales_order 22 s, tracking create_record_request sales_order 1 s, rest 0. No backlog. Metrics lag about 4 min.
- 7 Snap, 14:48-15:20Z: snap.poll.request.failure, snap.request.failure and snap.breaker.opened return no series; snap.slot_queue_depth max 9; snap.request.latency.avg max 6381 ms. snap_adapter and snap-polling-service logs for error/warn/"SNAP request failed"/slot_timeout/timeout/ETIMEDOUT/circuit: only snap-polling-service warns "Consignment StU not found" (4,585), "Stock movement dropped — could not determine adjustment direction" (96), "Withholding confirmation: connector not enabled for confirmations" (16). No error lines. The Snap delay has not turned into failures in this window.
- 8 Held records (replay-list-failures, production, createdAt 2026-11-07, paged to 14:37Z): since 14:48Z every new hold is goods_out_confirmation, business PURDYFIGG, failurePoint confirmation.delivery_shopify, reason "Fulfillment order ... is CLOSED in Shopify": 157 by 15:16:44Z (first 15:04:41Z, in bursts every 1-3 min), 0 replayed, 157 distinct recordIds; day total 1,412 at 15:11, 1,434 at 15:18; latest hold 15:18:41Z, so ongoing. sales_order, purchase_order, master_data, pick, pack holds today: 1 (sales_order, DOCKBAY, 13:03Z, before 14:48), none new.
- 9 Those PURDYFIGG holds are the CLOSED family in [[2026-11-06-egress-shopify-confirmation-delivery-failing-purdyfigg-redelivery-race-2121]] (finding 7 there: 1,557 on 6 Nov). Check this session: all 157 held recordIds have exactly one shopify-connector "Confirmation dispatched successfully" log today (157 distinct, 157 lines). For 4 sampled records the success precedes the hold by about 10 s (e.g. 14653732127100 success 15:16:35.6Z, hold 15:16:44.5Z). Shopify-connector error-level lines 14:48-15:20Z: none. These holds do not match the monitor query, which is why they did not trip it.
- 10 Slack since 15:10Z: 1 Triggered post for this monitor (no reply); 5 Warn posts for monitor 179927768 (ilg001-005), each with a Bifrost Support Bot reply; 5 Recovered posts ignored. No post after 15:15:48Z up to 15:19Z.

## Not established
- Source IPs or whether any probe got a 2xx: the logs carry no client address.
- That nothing executed: shown only to have failed at JSON parsing (entity.parse.failed) and been answered 500; no log of a spawned process was looked for.
- Why a malformed body is logged at error level and answered 500 rather than 400 (code not read).
- Whether every one of the 157 holds is a second attempt after a success: success log existence confirmed for all 157, ordering confirmed for 4; the redelivery mechanism itself not observed.
- Whether any of the 157 orders is genuinely unfulfilled in Shopify (no Shopify read tool).
- Whether the earlier 2 firings folded into this alert were the same burst; the per-minute query shows a single burst minute since 14:48Z.

## Outcome
P4 monitor_mistuned: scanner probes with unparseable bodies produce error-level "Error unhandled" lines that the monitor counts, 5 in one second. Over, nothing customer-facing. Separate and ongoing: PURDYFIGG CLOSED holds continue (known pattern, support should not replay or retry). Nothing retried, released or replayed.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794064548358519
- Monitor: https://app.datadoghq.com/monitors/180072217
- Earlier same-day: [[2026-11-07-snap-poller-api-latency-all-hosts-0429z]]
