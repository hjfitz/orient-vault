---
tags: [datadog-triage]
date: 2026-10-20
monitor: "[FUSE][Egress] Shopify confirmation delivery failing (fulfilment / order-tag)"
service: shopify-connector
business_id: PURDYFIGG
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792487045152229"
opened_at: "2026-10-20T09:02:49Z"
resolved_at: "2026-10-20T09:06:43Z"
minutes_spent: 4
severity_assessed: P4
flapping: false
outcome: real_minor
escalated_to:
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# Shopify confirmation delivery failing: duplicate PURDYFIGG announcements from the poller's fail-open Redis claim (INC-40 knock-on)

## Fired
Monitor 303425509 (forward.failure + order-tag failure, sum over 15m > 5) hit 9, then 18. All failures were PURDYFIGG goods_out_confirmation, between 09:02:38 and 09:03:00Z.

## Investigation
- Metric: `fuse.confirmation.forward.failure` had 18 failures, all `businessid:purdyfigg`, at 09:02-09:03Z. The week before had 3 (14 Oct) and 1 (16 Oct). There were no order-tag failures.
- Logs: all 18 failures were `Shopify fulfillment creation returned errors` with userError `Invalid fulfillment order line item quantity requested.` The same error class appeared on 14 Oct and 16 Oct under the older images e9aef9e and ad3ee5c.
- The failures came from two correlationIds, 06f9cc97 and 1e1355fb, which carried the **same 18 fulfilment orders**. For each recordId there was one success and one failure, split across the two correlationIds.
- snap-polling-service logged `Confirmation claim unavailable, failing open` for both correlationIds (09:02:15-09:02:37Z). That claim is the Redis SET NX confirmation dedupe.
- That fail-open message has appeared 178 times since 06:00Z (PURDYFIGG, STUBBLE, SAIRA, DOCKBAY, EPARFUM), and 0 times in the prior 7 days. It began before the 08:17Z shopify-connector deploy.
- shopify-connector at 8f35a129 uses Redis only for remote-config, and has no confirmation dedupe of its own (git grep). Since 08:17Z it has logged no config/timeout/429 failures. The only one is `DDP rules unavailable` (404), which appeared 1,252 times in the 30h before the outage.
- config-service has logged no errors since 08:17Z, and its warn counts match 19 Oct.
- "Confirmation dispatched successfully": 383 in the 08:00Z hour (backlog drain), against 119 on 19 Oct 08:00Z.
- replay-service stored failure records for both correlationIds (34 + 20 `Failure stored`).

## Not established
- Whether duplicate announcements also produced duplicate SFTP confirmation files for STUBBLE, SAIRA, DOCKBAY or EPARFUM.
- config-service latency: the trace metric returned no data.

## Outcome
This was not caused by the cache-less shopify-connector deploy. It is a knock-on of INC-40: the poller's Redis claim is failing open, so the same confirmations are announced twice, and the second Shopify fulfilment is rejected because the order is already fulfilled. No customer impact on Shopify. The resulting replay-service failure records must not be replayed. Posted the verdict in the thread, linked to INC-40.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792487045152229
- Incident: INC-40 https://gfsdeliver-eng.slack.com/archives/C0CAEGABJBF
