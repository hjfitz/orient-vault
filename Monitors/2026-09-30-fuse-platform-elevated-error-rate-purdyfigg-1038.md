---
tags: [datadog-triage]
date: 2026-09-30
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: shopify-connector
business_id: PURDYFIGG
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790764784677229"
opened_at: "2026-09-30T10:38:37Z"
resolved_at: "2026-09-30T10:42:32Z"
minutes_spent: 4
severity_assessed: P3
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: c4ac81de-f591-4dc7-8eb3-b9abf31d4c3f
status: resolved
---
# Error-rate monitor re-fired on PURDYFIGG standing failure; monitor needs retune

## Fired
Monitor 180072217 (>2 `domain:fuse` error logs in 2m, prod) triggered at 10:32 and 10:38 UTC. 69 fire/recover events in the last 24h.

## Investigation
- Confirmed: both triggers were PURDYFIGG shopify-connector `Confirmation dispatch failed` on goods_out_confirmation (`Unable to confirm order: Line item has no fulfillment ID`). 24 in 45m, continuous since ~20:30 UTC on 09-29, still occurring at 10:40 UTC.
- Root cause (traced on order #6458859, shipment PURDE9646C9028D; follow-up investigation): the goods-out mapping reads each line's Shopify ref from `extensions.shopify.fulfillmentId`, which snap-adapter writes at create time (SHL attachment + routing store doc, keyed by SNAP line id). On 09-29 snap-adapter hit `Timed out after 30000ms waiting for a concurrency slot` (window ~18:50-21:30 UTC). For this order SNAP created the shipment (~20:30:11 UTC) but the follow-on attachment step timed out, 9 redeliveries failed the same way, and attempt 10 hit `already_in_wms` which only acks (`acknowledgeAlreadyInWms` in snap-adapter `event.controller.ts`) and never writes the attachments/store doc. The line ships later with no ref, so the goods-out confirmation fails permanently. The multi-fulfillment-order warning I first suspected is not the cause.
- Not verified: that the SHL attachment/store doc is actually absent for this shipment (inferred from the code path and logs); how many of the 118 `already exists` retries since 12:01 UTC 09-29 are damaged (upper bound).
- Confirmed, low volume and not the trigger: EPARFUM snap-adapter SNAP 400s. purchase_order `SDA13P-1660` (XDoc Invalid Syntax, then Invalid Order Stage on all 16 lines); sales_order `DC127862227` (SKU `INSIDEADVIB02` No Product Found, UoM Invalid Unit).
- SPORTLUX: single sftp-connector `Confirmation write failed irrecoverably` at 09:58 UTC, a GCS 503. Not verified whether it was retried or redriven, so a confirmation CSV may be missing.
- Not us vs vendor: ours (config/mapping), apart from the GCS 503 blip.

## Outcome
P3, real-but-minor. Verdict posted in-thread with broadcast. No fix applied. The monitor excludes only SAIRA and snap-polling 401s, so it re-fires on the PURDYFIGG standing set; it is Terraform-managed in `observability`. Owed: an owner for the PURDYFIGG fulfillment-ID failure (backfill line refs for orders created in the 09-29 saturation window, and make the `already_in_wms` path heal missing attachments), the monitor retune, and a check on SPORTLUX's 09:58 confirmation. The Slack verdict still names the multi-fulfillment-order hypothesis; correction not yet posted. No ticket filed yet.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790764784677229
- Earlier triage of the same monitor today: [[2026-09-30-fuse-platform-elevated-error-rate]]
