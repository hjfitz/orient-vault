---
tags: [datadog-triage]
date: 2026-10-02
monitor: "[FUSE][Egress] Shopify confirmation delivery failing (fulfilment / order-tag)"
service: shopify-connector
business_id: PURDYFIGG
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790954156715699"
opened_at: "2026-10-02T15:14:49Z"
resolved_at: "2026-10-02T15:21:13Z"
minutes_spent: 6
severity_assessed: P3
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket: "https://globalfreight.atlassian.net/browse/FUSE-1118"
session_id: ad15503c-4ba6-425f-8c6f-38c909d12b97
status: resolved
---
# Shopify confirmation delivery warn re-fired on one PURDYFIGG order looping

## Fired
Monitor 303425509 warned at 15:14:49Z (value 2.0) and recovered at 15:17:49Z (value 1.0). 144 alert events in the last 3 days. Warn threshold is 1.0, critical 5.0, over a 15m window.

## Investigation
- Confirmed: the warn is PURDYFIGG `Confirmation dispatch failed: Unable to confirm order: Line item has no fulfillment ID` (shopify-connector prod, `92b81ec`). Shopify GraphQL responding normally; no vendor issue.
- Confirmed: order `14424845353340` / shipment `PURD91B0BF21CC3` has failed every ~12 min (one poll cycle) since its despatch, first failure 2026-09-30 21:16Z, ~210 times. (The Slack verdict said "since 10-01 15:26Z": that was the edge of a 24h query window, not the start.)
- Confirmed: a batch of ~15 other orders (`145032…`–`145034…`) failed ~110 times each in the 24h window and stopped at 12:42-12:50Z today. That was the 23-shipment routing-store repair ([[2026-10-02-purdyfigg-routing-store-repair]]).
- Follow-up, same session: `PURD91B0BF21CC3` is not repairable by writing ids. SNAP shipped 0 of both ordered kit lines (only component FG1229 ×1 went out), and the mapping fulfils `quantities.shipped`. Writing ids would land on NOTHING_TO_FULFIL, which publishes no `confirmation_made`, so the row would keep looping silently. Needs a P&F/support decision: it's on Matt Shaw's 10-01 #bifrost-general list as "Category 1, goods shipped", which SNAP contradicts, and that thread has no reply. One checked (`14503238697340`) shows `Confirmation dispatched successfully` at 12:58Z. Failures dropped from ~100+/hr to ~5/hr around 13:00Z.
- Not verified: what cleared the batch (shopify-connector deployed at 11:07Z, so not obviously the deploy). Not verified: the root cause for the remaining order; hypothesis is the same missing-fulfillment-ID gap as 09-29/09-30 (line Shopify ref never written at create time).
- Why it flaps: one order failing every 12 min leaves 1-2 events in the 15m window, straddling the warn threshold. The throw is swallowed by `Promise.allSettled` and never reaches `confirmation_data_failure`, so nothing clears it.

## Outcome
P3, real-but-minor, PURDYFIGG only, not escalated. Verdict posted in-thread with broadcast. No fix applied and no monitor change. Owed: repair or clear order `14424845353340`, FUSE-1118 (still Backlog, no new comment added this time), and a retune of the warn threshold in `observability` (monitors.tf, needs plan-then-proceed before any change).

## Follow-up sweep (same session)
Read-only sweep of every open SNAP shipment, plus queued stage-90 despatches, for the two businesses that confirm to Shopify (PURDYFIGG, SAIRA). Each Level 00 line was resolved the way the poller does it (store `lines[SOLineId]`, then `lineExtensions[Line]`, then SHL attachment).
- PURDYFIGG: 1,227 shipments, 1,226 resolve. The 16 pre-cutover ones resolve via `lineExtensions`. The only gap is `PURD91B0BF21CC3` (short despatch, above).
- SAIRA: 48 shipments, 46 resolve. The gaps are `E250188264` and `E250188441`: SNAP-native ids, no CustomerOrder, no routing doc, so they were keyed directly into SNAP and are not Shopify orders. Nothing to backfill. From reading the code, they will likely be silently undeliverable (no `confirmation_made`) when they despatch. Not observed.
- Result: no backfill needed. Only checks that an id is present, not that it's correct.

## The five "silent" queue rows (same session)
They do reach shopify-connector every ~12 min. None is a missing-id case.
- **`PURDC5EB6A337E2`, `PURD8041A2FE1DE`, `PURDD85217B3733`, `PURD50AF816638C`** (orders `14414769455484`, `14401006272892`, `14465437172092`, `14414184710524`) are `CLOSED` in Shopify. Shopify has no `FULFILLED` fulfillment-order status: a fully fulfilled FO is `CLOSED` (Admin GraphQL `FulfillmentOrderStatus` docs). shopify-connector (`sales-order-confirmation.handler.ts`, `fulfillmentOrderState`, prod `e1ad1bb`) only treats `FULFILLED` as "already done" and buckets `CLOSED` with ON_HOLD/CANCELLED as not deliverable. The result: no `confirmation_made`, the SNAP row never clears, a debug-only log, and one replay failure per cycle. Replay holds 903 "is CLOSED in Shopify" failures, 146 for `14401006272892` alone.
  - Not verified: who closed them in Shopify. Likely a manual fulfil, possibly during the FUSE-1238 black-hole window (09-21 to 09-24).
- **`PURD61FDB229170`** (`14476640387452`) is `OPEN` in Shopify. SNAP: kit `FG1233D_V2` shipped 0, with one component (`FG1197X_V4`) shipped, which is the same shape as `PURD91B0BF21CC3`. So it lands on NOTHING_TO_FULFIL at warn level, with no `confirmation_made`.
- Open question for ILG ops: is `FG1233D_V2` really short-shipped twice, or does the warehouse ship it pre-built as one unit, so that SNAP's per-component quantities are misleading? `PURD91B0BF21CC3`'s 1.026kg actual weight fits a whole kit.
- **Correction:** earlier advice that "a manual fulfil in Shopify clears the queue row on the next poll" is wrong. A manual fulfil makes the FO `CLOSED`, which is exactly how these four got stuck.

## Actions taken (on Harry's go-ahead)
- Marked processed (snapOutbound `markProcessed`, ~16:03Z): `SPLU023707` (PURDC5EB6A337E2), `SPLU026937` (PURD8041A2FE1DE), `SPLU028168` (PURDD85217B3733), `SPLU034592` (PURD50AF816638C), `SPLU033277` (PURD61FDB229170), `SPLU041624` (PURD91B0BF21CC3). Queue re-read afterwards: only 2 new despatches from 17:02 BST remain.
- Asked @fuse-support in #bifrost-general (bot post, 17:03 BST) whether the two `FG1233D_V2` orders (#6371398, #6433739) shipped in full. Told them the other four are already fulfilled in Shopify.
- Still owed: a shopify-connector fix to treat `CLOSED` as already fulfilled (or equivalent), and cleanup of ~900 duplicate replay failures.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790954156715699
- Earlier triage of the same monitor: [[2026-09-29-shopify-confirmation-delivery-failing-purdyfigg]]
- Ticket: https://globalfreight.atlassian.net/browse/FUSE-1118
