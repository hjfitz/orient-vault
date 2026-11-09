---
tags: [datadog-triage]
date: 2026-11-09
monitor: "Snap Queue Polling Service SnapFulfil rejecting credentials (401)"
service: snap-polling-service
business_id: KAPPAHL
snap_instance: ilg004
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794218385924289"
opened_at: "2026-11-09T09:58:23Z"
severity_assessed: P2
flapping: false
outcome: escalated
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# KAPPAHL: SnapFulfil (ilg004) answers 401 to the poller's outbound-queue fetch

## Fired
Monitor 326299823 (log alert, >5 in 15m by businessId) fired for KAPPAHL at 09:58:23Z. Siblings BABYMORI (same second) and SAMMCK (10:01:47Z) fired on the same monitor.

## Investigation
- 401 start and rate: service:snap-polling-service @environment:prod "Outbound queue fetch failed" "status code 401" @businessId:KAPPAHL. First line 09:56:05.133Z. None in the 7 days before. 3 fetch-failed lines (each paired with a "SNAP request failed") per 2-minute poll at 09:56, 09:58 and 10:00, 9 in total at 10:00:07Z. Still failing at 10:01Z (error lines in the 10:00 bucket).
- Last clean poll: "Confirmation poll event received" logged every 2 min for 24h (720 lines), with no error line at the 09:54:03Z poll. The log does not record a successful fetch, so the last successful fetch time is not established.
- Host: get-snap-connection (production) gives https://ilg004liveapi.snapfulfil.net/api, username FUSEKAPPAHL. lookup-snap-instance: instance 004, Snap DB 4, sites EGA 0007, EG25 0008, LGW 0009, BH 0011. Its includeBusinesses list returned 0, so the businesses sharing the instance came from other queries below.
- Read-only probes with the stored credential: snap-get-outbound-queue (top 100) and snap-lookup RECSTATUS both returned HTTP 401 at about 10:01Z. The host rejects the credential Fuse holds now.
- Config change: audit-search tenantId KAPPAHL from 2026-11-01 returned 0 events. audit-search for all tenants from 2026-11-09T00:00Z (excluding sftp_login) returned 0. config_change events since 2026-11-08 returned 0.
- Deploys: Datadog version tag on snap-polling-service logs is a single value (9af85287ca23) for the whole 24h; get_change_stories returned nothing. The channel shows no snap-polling-service or config-service deploy in the hour before; the deploys there were shopify-connector, shopify-egress-service and sftp-connector.
- Same host, other businesses: the 401 query grouped by businessId over 24h returned BABYMORI (first 09:56:05.129Z), KAPPAHL (09:56:05.133Z) and SAMMCK (first 09:58:02.923Z). get-snap-connection shows all three on the ilg004 host with different usernames (FUSEBABYMORI, FUSEKAPPAHL, SAMMCKAPI).
- Maintenance: no record in Obsidian Maintenance/ covers 9 Nov or names a window for DB4 after 5 Nov, and #bifrost-general has no maintenance post today. The separate API latency monitor was at warning on ilg004, ilg001, ilg003 and ilg005 at 09:51-09:52Z (ilg004: 2372 ms avg).
- Customer scope: get-business-config shows one active connector with confirmationsEnabled true and goods_in_confirmation and goods_out_confirmation use cases, SFTP csv egress. Confirmations from the Snap outbound queue to the customer's SFTP are not being picked up.

## Outcome
Escalated as P2 (live customer confirmations stopped, credential rejected by the host, no Fuse-side change found, will not self-resolve). incident-response not invoked by this run; the watching session decides.

## Not established
- Outbound queue depth and age (the queue cannot be read with the rejected credential).
- Who or what invalidated the credential, and whether the three businesses share a cause (same host and start time is established; the mechanism is not).
- Whether other ilg004 businesses are failing (only the three above were seen).
- Whether KAPPAHL had any confirmations waiting (no fuse.confirmation.retrieved series for it in 24h).

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794218385924289
- Monitor: https://app.datadoghq.com/monitors/326299823
