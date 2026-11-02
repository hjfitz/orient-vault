---
tags: [datadog-triage]
date: 2026-10-14
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: shopify-connector
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791977199550639"
opened_at: "2026-10-14T11:25:37Z"
resolved_at: "2026-10-14T11:29:00Z"
minutes_spent: 4
severity_assessed: P4
flapping: true
outcome: real_minor
escalated_to:
ticket:
session_id: 4fc06c6b-d424-4da8-b551-fb874e9c6e96
status: resolved
---
# Platform error-rate monitor tripped by 3 PURDYFIGG Shopify fulfilment rejections

## Fired
Monitor is `>2` matching `domain:fuse` error log lines in 2m (id 180072217, terraform-managed). It tripped at 11:25:37Z on 6 log lines.

## Investigation
- DDSQL per-minute count (monitor filter, 10:55Z to now): only 2026-10-14T11:24Z, shopify-connector, PURDYFIGG, 6 lines. Nothing else in the window, including with the monitor exclusions removed.
- The 6 lines are 3 pairs ("Shopify fulfillment creation returned errors" + "Confirmation dispatch failed") at 11:24:45, :47, :51Z, one run correlationId `94244d57-e32e-4cbe-afb0-8e873a9d113e`. userError "Invalid fulfillment order line item quantity requested." on 3 distinct FulfillmentOrders (14556083093884, 14556092367228, 14556141420924). 15 other PURDYFIGG confirmations dispatched OK in the same minute.
- Current: no `status:error` after 11:24:51Z (checked to ~11:27Z, logs flowing). Hourly error volume 6 vs ~15/h typical over 7d.
- `fuse.confirmation.forward.failure` = 3 in the 11:20Z bucket, matching the Shopify monitor 303425509 (fired 11:24:49Z, triaged separately).
- Deploys: get_change_stories empty for shopify-connector 08:00-11:30Z; current version e9aef9e first logged 2026-10-12T14:11Z, so not a lead.
- Flapping: 26 Triggered / 25 Recovered events in 7d.
- Not established: why Shopify rejected the quantities (WMS vs FulfillmentOrder mismatch is a hypothesis only); whether the 3 confirmations are retried and clear on the next poll.

## Outcome
Real but minor: one business, 3 orders, Shopify API rejection, not repeating after 11:24:51Z. P4, no incident, no ticket. Reply posted in thread with broadcast.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791977199550639
- Monitor: https://app.datadoghq.com/monitors/180072217
