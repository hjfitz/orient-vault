---
tags: [support-triage]
date: 2026-09-30
business_id: PURDYFIGG
customer: "Purdy and Figg"
connector: shopify
reporter: "Harry Humby"
channel: C099WKQTE8G
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790768033804159"
opened_at: "2026-09-30T11:33:53Z"
outcome: defect
session_id: 4a861a53-2095-4349-8531-596a63f68552
status: open
---
# Purdy and Figg shipped orders can't be marked fulfilled in Shopify ("Line item has no fulfillment ID")

## Reported
Harry Humby saw a Datadog alert for shopify-connector confirmations failing with `Unable to confirm order: Line item has no fulfillment ID` on PURDYFIGG. Orders had shipped from SNAP but Fuse couldn't mark them fulfilled in Shopify. He suspected the 09-29 evening SNAP slowdown, muted that one error on the alert, and asked whether to backfill the line attachments in SNAP. Harry Fitzgerald asked for the logs to show whether Fuse omitted the reference or the orders were hand-created/edited.

## Root cause
Not manual. Affected shipments are Fuse-created (deterministic `PURD…` ids, `MaintInd W`). Traced PURD12ADC65267F (Shopify order 14499411067260, ref #6458777): snap-adapter's first create attempt hit SNAP 599 timeouts twice (19:47/19:49Z, 09-29) and returned 503. The shipment had landed in SNAP anyway (created 19:45Z). Pub/Sub redelivery at 19:49:28Z found it at stage 10 via the read-before-write precheck, acknowledged it as already created and skipped the post-PUT attachment step. The ordered line has `AttachmentInd 0`; a healthy order created earlier that day has `AttachmentInd 1`. With no SHL attachment the poller sends no fulfillment id and shopify-connector throws on every retry.
The underlying trigger is SNAP's database timing out during Purdy & Figg's bulk order drops (Harry; known to ILG ops). The Fuse-side weakness is that Shopify line data is only written after the create, keyed by SNAP's post-create line id, so a create acked as `already_in_wms` never gets it.
Outbound queue at 13:00Z held 71 PURDYFIGG despatches: 33 (all created 09-29 19:10–22:20) had no SHL rows and matched their collected canonical orders on SKU/qty/line count; 1 more (PURD3A30EE1FF32, #6397751, 09-19) has the same gap but no collector record in range; 37 already had attachments (31 confirmed to Shopify ~21:30Z 09-29 but never cleared from the queue, clear-down failing in the same SNAP window; 1 loops on "no fulfillable line items"; 5 unclassified). STUBBLE (47) and WILDSMITH (1) hit the same create path but are SFTP-only.

## Fix / Resolution
Backfilled via `repair-shopify-confirmation`: 41 SHL rows across 33 shipments, fulfillment ids from the collector, new `BF…` LineIds (distinct from Fuse's deterministic ids). Pilot PURD12ADC65267F confirmed 13:18Z; the other 32 written 13:21–13:22Z, and all 33 queue records had cleared by 13:35Z. Posted to Ryan Ellis and Denis Tomolea in #bifrost-general (list in thread). Second pass (13:48–14:05Z): swept all 287 PURDYFIGG shipments acked `already_in_wms` on redelivery since 09-27, found 76 more missing a Shopify link (9 shipped, 67 not yet), backfilled 97 rows across 77 shipments incl. PURD3A30EE1FF32 (19 Sep address-segment interface error — pipe in Line1 — fulfillment id from replay-service's stored failure). `markProcessed` on 31 queue records Fuse had already confirmed on 09-29 but whose clear-down failed in the SNAP timeouts (PURDC7CD9346418 cleared itself). By 14:17Z: zero "no fulfillment ID" failures since the second pass, 29 successful confirmations. Still open: PURDC5EB6A337E2 / PURD8041A2FE1DE / PURDD85217B3733 / PURD50AF816638C (links intact, silently skipped by shopify-connector — Shopify order no longer open+unfulfilled; needs someone with store access) and PURD61FDB229170 (SNAP kit parent line QtyShipped 0 despite despatch — ILG ops). Security finding raised separately: snap-adapter's create-failure log includes the axios `_header` string with the SNAP Basic auth credential. Durable fix planned in `Engineering/snap-adapter/plans/persist-fuse-line-metadata-to-firestore-before-s.md` (write line metadata to Firestore before the create, keyed by SOLineId). No defect filed yet.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790768033804159
- Ops update: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1790775377461209
