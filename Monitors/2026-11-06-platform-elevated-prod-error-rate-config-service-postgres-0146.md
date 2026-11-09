---
tags: [datadog-triage]
date: 2026-11-06
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: config-service
business_id:
snap_instance: ilg001
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793929665748739"
opened_at: "2026-11-06T01:46:37Z"
severity_assessed: P4
flapping: true
outcome: real_minor
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# 01:46Z firing: 3 config-service Postgres connection-check errors again (same pattern as 23:29Z); a folded 01:05Z firing was a different cause (DOCKBAY Snap slot timeouts, self-resolved)

## Fired
More than 2 error-level domain:fuse logs in 2m. Shortened re-check of a known pattern, run as a read-only subagent (watcher posts the reply).

## Investigation
- Monitor-matching errors since 00:56Z (analyze_datadog_logs, the monitor's exact query): config-service "Dependency connection failed" x3 (01:45:33Z and 01:45:34Z `read ECONNRESET`, 01:46:00Z `Postgres ping took longer than 2000ms`, `dependency: postgres`, revision config-service-prod-00071-czr, version 6b73684, same revision and shapes as 23:29Z) and snap_adapter "Entity creation in SNAP failed" x6 (01:04:45Z to 01:05:28Z). Nothing else matched. So the 01:46Z trigger is the config-service Postgres pattern; the tracking-service store pattern did not recur (search_datadog_logs "store failed" from 00:30Z: still only the 4 at 00:50-00:55Z).
- Postgres health: `min:fuse.postgres.up` over 01:44:00-01:46:00Z = 0 (scalar), and the 10s series shows 4 to 5 consecutive 0 samples then back to 1 (series start times returned by the tool were inconsistent between calls, so the dip is placed only as within 01:44-01:46Z). `fuse.postgres.latency.max` peak 599ms since 01:40Z.
- config-service: 0 error-level logs other than the 3 above and no 5xx (status filter over `status:error` or http status 5xx, 00:56Z onwards).
- Other 5xx since 01:30Z (all prod): 5 log lines, all gfs-coll8-integration (WordPress POST 500s, no `domain:fuse` match, not counted by this monitor) and 1 ccp-api "proxy returned non-ok status"; none from config-service or any service the monitor matched. Not examined further.
- Backlog: max `oldest_unacked_message_age` across all prod subscriptions since 01:40Z = 2s (scalar max).
- Held records: `replay-list-failures` (production, createdAt 2026-11-06) total 0.
- Recurrence/flapping: config-service "Dependency connection failed" by hour over 24h: 12Z 2, 15Z 1, 20Z 3, 23Z 6, 01Z 3 (15 in 24h). Monitor alert posts in #bifrost-notifications: 00:56:45Z, 01:06:44Z, 01:47:45Z today (plus 23:29Z yesterday). `search_datadog_events monitor_id:180072217` returned 0, so the earlier count of 8 triggers since 2 Nov was not re-queried.
- Folded 01:05Z firing (thread 1793927204.412889, no reply in it): not the same cause. snap_adapter, businessId DOCKBAY (instance ilg001, site 0001, warehouse SPACE), `failureMode: slot_timeout`, `Timed out after 30000ms waiting for a concurrency slot`, `transient: true`, `exhausted: false`, version e2974c0. Three orders (UK-913152, UK-913153, UK-913160): attempt 1 at 01:04:45Z, attempt 2 at 01:05:27-28Z, each returned 503 to the push (6 logged `POST /events/v1/record/create/sales_order - 503`), then "Entity created in SNAP" x3 (204) at 01:06:02Z (analyze_datadog_logs on those recordIds). snap_adapter.prod.create_record_sales_order.v1.sub peak oldest unacked 75s since 00:30Z. Entity-creation failures in the prior 24h: DOCKBAY 6 (this burst), ESCENTRIC 1 (snap_api_error), PURDYFIGG 1 and WILDSMITH 1 (schema_validation); no other slot timeouts. No Snap maintenance window covers 01:05Z on 6 Nov (records in Maintenance/ are 3 Nov 10:00 and 5 Nov 10:00). One read-only `snap-lookup RECSTATUS` against the ilg001 host returned data (no timing measured).
- tracking-service 00:50-00:55Z nacked events (the lead from the last triage): the 4 event ids are shopify-connector Pub/Sub messageIds from "Record published to topic" (SAIRA #37859, ESCENTRICPL #139892, PURDYFIGG #6662383 and #6662458, all sales_order, create_record_request). Shopify-connector re-publishes each open order about every 5 min: publish counts 24h for #37859 48 (21:55Z to 01:50Z), #139892 27, #6662383 36, #6662458 21. tracking-search-shipments shows a shipment for each customerRef, status in_wms, updatedAt before the nack (21:55Z, 23:40Z, 22:45Z on 5 Nov; 00:10Z on 6 Nov). tracking-service logged no further "store failed" after 00:55:07Z. tracking-service logs only errors in 00:49-01:10Z (a status/message grouping returned only the 4 store failed rows), so no success log exists to look for.

## Not established
Why the Postgres connection checks fail (Cloud SQL maintenance or restart, network, pool config; no Cloud SQL logs or events read). Whether the 4 nacked create_record_request messages were themselves redelivered and stored or dead-lettered: no log mentions their ids after the nack and tracking-service logs no success lines. What is shown is that the same orders were republished later, tracking holds all 4 shipments, and no later store failure was logged. Whether the 2 Nov and 3 Nov firings were the Postgres pattern. Whether DOCKBAY slot timeouts recur (not seen in 24h before 01:04Z); whether the host was slow or our concurrency cap queued (no Snap latency metric or probe timing taken).

## Outcome
Real minor, P4. Config-service Postgres connection checks failed for about a minute (fuse.postgres.up 0) with no 5xx, no backlog, nothing held. Chronic: 15 such logs in 24h and the same cause as 23:29Z; the monitor counts the check's error-level line so a handful trips it. The folded 01:05Z firing was a self-resolved DOCKBAY Snap slot-timeout burst, all 3 orders created at 01:06Z, nothing held. Not ticketed here; the earlier lead (log the dependency check at warn until repeated failure, look at Cloud SQL) stands.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793929665748739
- Folded 01:05Z thread (unreplied): https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793927204412889
- Monitor: https://app.datadoghq.com/monitors/180072217
- Prior records: Monitors/2026-11-05-platform-elevated-prod-error-rate-config-service-postgres-2329.md, Monitors/2026-11-06-platform-elevated-prod-error-rate-tracking-service-store-0055.md
