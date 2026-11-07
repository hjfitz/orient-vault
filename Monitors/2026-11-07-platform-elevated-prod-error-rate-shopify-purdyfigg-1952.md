---
tags: [datadog-triage]
date: 2026-11-07
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: shopify-connector
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794081228903219"
opened_at: "2026-11-07T19:52:37Z"
resolved_at: "2026-11-07T19:57:00Z"
minutes_spent: 5
severity_assessed: P3
flapping: true
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# Error-rate monitor tripped by 12 shopify-connector error lines: 6 PURDYFIGG goods-out confirmations failed Shopify fulfilment in a 5 s burst

## Fired
Monitor 180072217 (log alert, more than 2 matching error lines in 2m). Triggered 19:52:37Z, Slack post 19:53:48Z (parent ts 1794081228.903219), no replies when read at about 19:55Z. Monitor status read OK again at about 19:56Z. Different cause from the 15:14Z firing today (config-service scanner probes, see Links).

## Investigation
- 1 Monitor query run for 19:45Z to now, grouped by service and message: 12 lines, all shopify-connector, 6 "Confirmation dispatch failed" and 6 "Shopify fulfillment creation returned errors", 19:51:37.998Z to 19:51:42.881Z. No other service matched.
- 2 All 12 are businessId PURDYFIGG, connector conn_7ce8402090194b67b0f8a1de03019397, shop purdy-figg.myshopify.com, recordType goods_out_confirmation, one correlationId (cd93357d-4e4f-4a18-9f0a-ae8cbea0600f), 6 distinct recordIds (14654536712572, 14654442504572, 14654305206652, 14654453743996, 14654266835324, 14654543266172). Shopify userErrors "Invalid fulfillment order line item quantity requested." (field fulfillment); connector error "Unable to confirm order: One or more fulfillment orders could not be fulfilled in Shopify." This is not the "Line item has no fulfillment ID" message the monitor excludes, and not the "is CLOSED in Shopify" message of the long-running hold family.
- 3 Same correlationId, 19:30Z to now: one batch from 19:51:00 to 19:51:42Z with 33 "Confirmation dispatched successfully", 33 "Confirmation processed", 33 "Record published to topic", 6 "dispatch failed". Each of the 6 failing recordIds has exactly one "dispatched successfully" and one "dispatch failed" line, the failure 25 ms to 0.5 s after the success. None of the 6 recordIds has any shopify-connector log earlier today (00:00Z to now).
- 4 Per-minute shopify-connector PURDYFIGG error/warn since 19:00Z: errors only in the 19:51 minute (12); warns 7-8 per 5 minutes throughout. Monitor status OK at about 19:56Z.
- 5 Sibling monitor 303425509 (metric 6.0 at 19:51:49Z): `fuse.confirmation.forward.failure` for businessid purdyfigg is 3 and 3 in the 10 s buckets starting 19:51:30Z, then 0 to 19:55Z. Same 6 failures, same business, same seconds: shared cause with 303425509. Not investigated beyond that, per instruction.
- 6 replay-list-failures (production, PURDYFIGG, search recordId 14654536712572): 1 held record, created 19:51:38.043Z, goods_out_confirmation, confirmation.delivery_shopify, attempts 0, reason as in 2. The other 5 were not individually looked up.
- 7 Separate and ongoing: newest PURDYFIGG holds at 19:54:45-46Z are "Fulfillment order ... is CLOSED in Shopify" (10 listed, the known CLOSED family from the 6 Nov and earlier 7 Nov records). They are not in the monitor query and not part of the 12 lines.
- 8 Other prod services, error/warn 19:47Z to now: only warns (snap-polling-service 1,425, dedupe_service 539, shopify-connector 18, config-service 14, replay_service 2); no errors other than the 12.

## Not established
- Why each failing record logged both a success and a failure (two deliveries of one record, two fulfilment orders on one order, or something else). The logs show both lines per record; the mechanism was not observed.
- Whether any of the 6 Shopify orders is actually unfulfilled in Shopify (no Shopify read tool); the success log for each may mean it is fulfilled.
- Whether the other 5 failing records are held in replay-service (checked for 1 of 6).
- Whether more such bursts will follow (one burst seen; no repeat by about 19:56Z).

## Outcome
P3 real_minor: one customer, 6 confirmations, a 5-second burst that has not repeated, monitor back to OK. Shares its cause with the Shopify confirmation delivery monitor 303425509. Nothing retried, released or replayed. No ticket filed.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794081228903219
- Monitor: https://app.datadoghq.com/monitors/180072217
- Sibling monitor (other agent): https://app.datadoghq.com/monitors/303425509
- Earlier same-day, different cause: [[2026-11-07-platform-elevated-prod-error-rate-config-service-scanner-1514]]
