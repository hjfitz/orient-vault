---
tags: [datadog-triage]
date: 2026-11-06
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: shopify-connector
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793996329016919"
opened_at: "2026-11-06T20:17:37Z"
severity_assessed: P3
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Error-rate monitor tripped by the same PURDYFIGG Shopify fulfilment rejection

## Fired
Monitor 180072217: more than 2 error lines (monitor query, domain:fuse, prod, with its exclusions) in 2 minutes.

## Investigation
- Monitor query run via aggregateLogs 20:12-20:22Z: 5 matches. 4 are shopify-connector ("Confirmation dispatch failed" x2, "Shopify fulfillment creation returned errors" x2, PURDYFIGG order 14648314036604, 20:16:26 and 20:16:43Z). 1 is config-service "Dependency connection failed | Postgres ping took longer than 2000ms" at 20:13:56Z, outside the 2m window.
- Same cause as the Shopify egress alert (303425509); not config-service, tracking-service, dedupe, snap_adapter or replay. Last 3h of matches: config-service 6, dedupe_service 3, shopify-connector 4, nothing else.

## Not established
- Cause of the config-service Postgres ping timeout at 20:13:56Z (not investigated; it matches today's known config-service Postgres pattern but did not trigger this alert).

## Outcome
Real but minor and shared with the Shopify egress alert; see that record.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793996329016919
- Monitor: https://app.datadoghq.com/monitors/180072217
