---
tags: [datadog-triage]
date: 2026-11-02
monitor: "[FUSE][Fuse API] Ingress validation-error spike"
service: fapi
business_id: DOCKBAY
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793631805960609"
opened_at: "2026-11-02T15:01:59Z"
severity_assessed: P3
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: open
---
# Ingress validation-error spike: 26 DOCKBAY sales-order POSTs rejected with 400 at 15:01Z

## Fired
Monitor 302685719 (priority 3): `sum(last_15m):default_zero(sum:fuse.ingest.validation_errors{service:rest_connector,environment:prod}.as_count()) > 50`. Warn at metric value 30 (the 15:03:25Z thread post; event ts 15:01:59Z). Not a flapper: no 2h bucket in the prior 14 days above 11.

## Investigation
- **What the metric counts:** one per record rejected by canonical validation at fapi (rest_connector). It carries no businessid tag (businessid:N/A), so attribution is from logs.
- **Tripping value reproduced:** 26 `Record batch rejected` (warn) log lines at 15:01:11-15:01:15Z plus 4 at 14:51:20, 14:51:50, 14:51:54 and 14:52:30Z = 30 in the 15 min window. A fifth earlier today, 14:37:36Z. All 31 carry connectorId conn_068adb8146774f9199ad1168316d056d, which the same-connector logs show is DOCKBAY (businessId DOCKBAY on 3015 of 3517 lines in 24h), `correlationId: fulfil`, channel rest, recordType sales_order. No other connector or record type today.
- **Reason:** every rejection is `expected string, received null` on optional-looking customer fields: 15:01Z burst `order.class` and `shipContacts.0.contact.email`; 14:37 and 14:51-14:52Z `shipContacts.0.contact.email` and `.contact.phone`. Each line is one record (count 1, failedCount 1).
- **Shape of the 15:01Z burst:** about 37 single-order POSTs /api/v2/sales-orders in ~7s: 26 rejected, 11 accepted (202, "Record batch emitted"). No rejection after 15:01:15Z up to the last check at ~15:05Z.
- **Same customer, same errors, not new:** 34 rejection logs in the 14 days before today, all the same connector: sales_order `shipContacts...email/phone` and `order.class` null from 19 Oct (1 on 20 Oct, 7 on 21 Oct, 3 on 26 Oct, 12 on 27 Oct, 2 on 28 Oct, 1 on 31 Oct), plus master_data `countryOfOrigin`/`nmfcCode` null (28 and 30 Oct) and one purchase_order (22 Oct). Today's 31 is the largest day.
- **No platform change:** every log since 20 Oct carries fapi version 1d72173 (commit "Start fapi on a cache-less remote config...", #179, 2026-10-20T10:18Z); the only earlier rejections (19 Oct, version b8870c5) show the same email-null error. The last merged fapi PR is #179 (20 Oct). No other customer's connector appears.
- **Loss:** a 400 is returned to the caller and nothing is held in replay-service. The 26 rejected POSTs are only in Fuse if DOCKBAY's Fulfil.io resends them. No order reference is logged for a rejected record, so whether they were resent, and whether they are 26 distinct orders or retries of fewer, is not established.
- Context: this is the same DOCKBAY resumed burst seen earlier (110 orders accepted at 14:37Z); records_emitted for dockbay sales_order shows 110 at 14:37Z and 11 at 15:01Z.

## Not established
- Distinct order references behind the 26 rejections and whether DOCKBAY has resent them (no order id in the log; rejected requests are not stored).
- Whether the monitor has fired before (monitor event search returned nothing) and its Warn threshold (only the >50 critical threshold is in the returned query).
- What Fulfil.io populates for guest/no-contact orders (why email/phone/class are null).
- The Fuse MCP was down (401): no business config or audit lookup.

## Outcome
Real_minor, P3. Not a platform fault or rule change: DOCKBAY's Fulfil.io is sending sales orders with null `shipContacts.0.contact.email`/`phone` and `order.class`, which fapi's canonical schema rejects (400), a pattern since 19 Oct. 26 POSTs rejected at 15:01Z; they are lost to Fuse unless DOCKBAY resends. Support/DOCKBAY should be asked to resend the rejected orders and fix or default those fields (or the schema should accept nulls). Re-check if rejections continue or DOCKBAY confirms the orders were not resent (then raise).

## Update 2026-11-03 (Alert, metric 51.0 at 13:03:59Z)
Thread: C099WKQTE8G / 1793711124.580619. Thresholds (monitor 302685719, Terraform-managed): critical 50, warning 10. Tripping value 51.0 vs >50.
- **All 51 are DOCKBAY again:** 51 `Record batch rejected` warns in the last 75m, every one connector conn_068adb81..., recordType sales_order, service rest_connector; no other connector or record type.
- **One 7-second burst:** 13:03:18-13:03:25Z (per-minute counts over 26h: 14:37 1, 14:51 3, 14:52 1, 15:01 26 on 2 Nov, 17:01 1, then 13:03 51 today). Nothing before or after on 3 Nov.
- **Same fault:** all 51 are `order.class` AND `shipContacts.0.contact.email` `expected string, received null` (one pair per record).
- **Accepted in the same burst:** 18 `Record batch emitted` at 13:03Z (DOCKBAY posts hourly at about :01-:03; accepted 11:03 26, 12:03 14, no rejections at those). So about 51 of 69 orders (74%) rejected at 13:03.
- **Volume since 2 Nov 14:00Z:** 83 rejected vs 468 accepted batches (hourly counts, all 1 record each); 14:00 hour 2 Nov was 139 accepted.
- **No Fuse-side change:** single fapi version 1d72173 across all rest_connector logs in 48h; last merged fapi PR #179 (20 Oct).
- **Resend:** a 400 is not stored; no order id in rejection logs. Rejections did not recur at the hourly runs after 2 Nov 15:01 (1 at 17:01), so the 2 Nov rejected orders were not re-posted unchanged, but whether they arrived corrected is NOT established.
- Not established: distinct orders rejected, whether any were resent; snap-adapter DOCKBAY order refs (Fuse MCP down, 401); what Fulfil sends for these orders.
Agent assessed a P2 candidate and returned ESCALATE. Harry judged it P3 (one customer, recurring since 19 Oct, no Fuse change) and chose a @fuse-support request to contact Dock and Bay instead of declaring an incident (2026-11-03). Still open: whether DOCKBAY resent the rejected orders, and whether the canonical schema should accept null.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793631805960609
- Monitor: https://app.datadoghq.com/monitors/302685719
- Related: [[2026-11-02-new-orders-stopped-dockbay]], [[2026-09-29-fuse-api-availability-below-target]]
