---
tags: [datadog-triage]
date: 2026-10-09
monitor: "[FUSE][Platform] create_data_failure spike"
service: snap-adapter
business_id: SAIRA
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791558732660639"
opened_at: "2026-10-09T15:11:07Z"
resolved_at: "2026-10-09T15:14:00Z"
minutes_spent: 3
severity_assessed: P3
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: 0a6fab47-9201-4b91-aea7-e306bf321ad2
status: open
---
# create_data_failure topic spike is the echo of the SAIRA snap create loop

## Fired
Monitor 302536087 (Terraform-managed, `gcp.pubsub.topic.send_request_count` on `bifrost.prod.create_data_failure.v1`, warn at 5 per 15m) read 6 at 15:11:07Z.

## Investigation
- Confirmed: every create_data_failure publish in the last hour is SAIRA `sales_order` (13 publishes, 6 correlationIds, 14:50Z-15:10Z, a burst every ~5 min). These are the failure side of the SAIRA orders #37125/#37126/#37127 that Snap rejects for an empty `skuId` on a price-0 line and snap_adapter resubmits every ~5 min. Same cause as the Elevated production error rate firing at 15:00Z (see the linked record).
- Confirmed: baseline over 24h is ~0-1 sends per 35m bucket; no other business or record type is publishing failures; not vendor.
- Hypothesis, not verified: SKU-less Shopify line item (customer data).
- Flapping: first firing of this monitor in 3 days.

## Outcome
P3, real-but-minor, one customer, three orders; verdict posted in-thread with broadcast. No ticket. Owed: ask SAIRA about the SKU-less line; the loop keeps both monitors firing until fixed.

## Update 2026-10-09T15:52Z
Re-fired 15:51Z (re-trigger, no new thread post); verified unchanged: topic send_request_count is 3 per ~5 min burst (one per order) over 14:46Z-15:52Z with no growth, replay shows only SAIRA #37125/#37126/#37127 sales_order create failures (latest 15:50Z, same "SKUId - MANDATORY" error), no other business, recordType or order on create_data_failure. Still P3; loop continues until the SKU-less line is fixed at source.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791558732660639
- Monitor: https://app.datadoghq.com/monitors/302536087
- Related record: [[2026-10-09-fuse-platform-elevated-error-rate-saira-snap-create]]
