---
tags: [datadog-triage]
date: 2026-11-06
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: shopify-connector
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793998243770429"
opened_at: "2026-11-06T20:49:37Z"
severity_assessed: P3
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Platform error-rate monitor fired on the 6 PURDYFIGG Shopify fulfilment rejection log lines

## Fired
Log alert 180072217 (more than 2 matching error lines in 2m, monitor 180072217 is Terraform-managed) went Alert at 20:49:37Z, 48s after the Shopify egress monitor 303425509.

## Investigation
- The monitor's own query (domain:fuse, error, prod, with its exclusions) for 20:45-20:52Z returns 6 lines, all service shopify-connector, all in the 20:48Z minute: "Shopify fulfillment creation returned errors" x3 and "Confirmation dispatch failed" x3 (analyze_datadog_logs). Nothing from any other service, per-minute counts since 20:40Z show only 20:48Z.
- Those lines are the 3 PURDYFIGG quantity rejections at 20:48:45-47Z (see the Shopify egress record, same file set, correlation 73dd2884-9243-46ae-aaf0-5e1365308281). No further matching errors after 20:48:47Z through ~20:51Z.

## Not established
- Whether the monitor will clear on its own (state was still Alert at 20:51Z; the 2m window had not yet rolled past 20:48:47Z).

## Outcome
Shared cause with monitor 303425509, no separate failure. Held records and support action are tracked in the Shopify egress record.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793998243770429
- Related: 2026-11-06-egress-shopify-confirmation-delivery-failing-purdyfigg-invalid-quantity-2016.md
