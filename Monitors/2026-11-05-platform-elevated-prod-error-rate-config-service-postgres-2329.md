---
tags: [datadog-triage]
date: 2026-11-05
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: config-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793921445626419"
opened_at: "2026-11-05T23:29:37Z"
severity_assessed: P4
flapping: true
outcome: real_minor
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# 23:29Z firing: 3 config-service Postgres connection-check errors (ECONNRESET, ping >2000ms); no failed requests seen; neither the slot-timeout nor the probe pattern

## Fired
More than 2 error-level domain:fuse logs in 2m. A third distinct cause for this monitor in 3 days: not the 3 Nov snap_adapter slot timeouts, not the 5 Nov 12:09Z malformed-JSON probe.

## Investigation
- Monitor query, 23:20Z onwards, by service: 3 matches, all config-service (analyze_datadog_logs). They are "Dependency connection failed" with `dependency: postgres`: 23:28:44Z and 23:28:46Z `read ECONNRESET`, 23:28:55Z `Postgres ping took longer than 2000ms` (stack in postgres.connection.ts checkOnce). Revision config-service-prod-00071-czr, version 6b73684. No business or correlationId on two of them (one carries correlationId b7f6842f-52a4-459f-b398-202f3ad3c077).
- Nothing else matched. All prod error-level domain:fuse logs since 23:00Z: config-service 6 only (23:04:50Z ping timeout, 23:08:25Z 2x ECONNRESET, plus the 3 above). 0 config-service error logs after 23:31Z at query time (about 23:33Z).
- Customer impact: config-service responses with a 4xx or 5xx since 23:00Z are only 97 `GET /api/v1/business/<id>/ddp/rules - 404`; 0 5xx. `GET /api/v1/business/PURDYFIGG` returned 200 at 23:30:07Z (many). Query fuse.postgres.up (min, environment:prod, service:config-service, last 6h, 20 bins): below 1 in 19:55, 20:13, 22:54 and 23:12 bins (min 0.33 in the last). fuse.postgres.latency.max: 2277ms in the 19:55 bin, 758ms in 22:54, 397ms in 23:12, typically under 300ms. Cloud SQL num_backends 2 to 4 over the same 6h, so no connection exhaustion visible.
- Recurrence: 14 "Dependency connection failed" logs from config-service in 7 days, 12 of them on 5 Nov (12:54Z x2 ECONNRESET, 15:22Z, 20:01Z, 20:22Z, 20:25Z, 23:04Z, 23:08Z x2, 23:28Z x3) and 2 on 3 Nov 14:32Z. Versions: 9627e7b (3 Nov), 5db1f87 (12:54Z), 6b73684 (the other 10; first logged 15:20:28Z). So the failures are not tied to one version, but the rate rose after 6b73684 began serving (lead, not a finding).
- Probe pattern: since 12:11Z config-service has 11 POST/PUT request logs, all info-level: 6x `POST / 401`, 1x `POST /api/v1/setting/captcha 401`, 4x 201 (VITALITY, COLLAGEN business and storefront at 17:15 and 17:24Z). 0 `Error unhandled`, 0 `/run` or `/code/blocks` paths, 0 500s. The client IP was not shown in these logs' fields, so whether 82.165.94.38 returned is not established; the exploit-route traffic has not returned.
- Slot-timeout pattern: not what fired (the 3 matches are all config-service). Not re-queried for snap_adapter slot timeouts beyond the all-service count above, which shows none matching the monitor.
- Held records (replay-service production, created 5 Nov, sales_order/purchase_order/master_data): 3, none caused by this alert: WILDSMITH SO-29606 (ShipContacts.Phone >20 chars, 17:20Z), PURDYFIGG #6661692 (CustomerName/ShipAddress.Name >50 chars, 16:50Z), ESCENTRIC #139825 (LastName MANDATORY, 12:00Z, already in the 12:09Z record). The first two are in no earlier vault record. Also 647 total failures held in replay (PURDYFIGG goods_out_confirmation Shopify CLOSED fulfilment orders seen at 21:40Z), delivery not Snap submission, not examined.
- Flapping: monitor events show 7 triggers between 2 Nov 16:36Z and 5 Nov 23:29Z (first 13 of 39 events read: 2 Nov 16:36, 16:51, 17:01; 3 Nov 14:08, 16:56; 5 Nov 12:09, 23:29), 3 distinct causes among the ones investigated.

## Not established
Why the Postgres connection checks fail (Cloud SQL maintenance or restart, network, pool config, or load not checked; no GCP/Cloud SQL logs or events read). Whether the 3 Nov 14:08Z and 2 Nov firings were this cause (only the 14:32Z Postgres errors on 3 Nov were seen, 24 minutes after the 14:08Z trigger). Whether the client IP 82.165.94.38 has returned (IP not a queryable field here). Whether the `ddp/rules` 404s and the 41 shopify-connector "DDP rules unavailable for business" warns in 23:20Z onwards relate to this (404s, warn level, not counted by this monitor; not examined). Whether the three held Snap-submission records have been fixed or replayed since the lists were read (about 23:32Z).

## Outcome
Real minor, P4. Intermittent config-service to Cloud SQL connection-check errors; no failed config-service request and no other service's error logs in the window. The monitor counts the check's error-level log line, so a few failed checks trip it. Leads, not findings: the postgres dependency check could log at warn until it fails repeatedly, and the 12 failures on 5 Nov warrant a look at Cloud SQL logs and the 15:20Z revision. Not ticketed here. Separate from the alert: WILDSMITH SO-29606 and PURDYFIGG #6661692 are held for Snap field-length rejections; support to fix the data and replay.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793921445626419
- Monitor: https://app.datadoghq.com/monitors/180072217
- Prior firings: Monitors/2026-11-03-platform-elevated-prod-error-rate-purdyfigg-1656.md, Monitors/2026-11-05-platform-elevated-prod-error-rate-config-service-probe-1209.md
