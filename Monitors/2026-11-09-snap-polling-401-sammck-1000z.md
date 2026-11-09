---
tags: [datadog-triage]
date: 2026-11-09
monitor: "Snap Queue Polling Service SnapFulfil rejecting credentials (401)"
service: snap-polling-service
business_id: SAMMCK
snap_instance: ilg004
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794218507614999"
opened_at: "2026-11-09T10:00:23Z"
severity_assessed: P2
flapping: false
outcome: escalated
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# SAMMCK: ilg004 rejects the poller's credential (third business, same host)

## Fired
Monitor 326299823 (log alert, more than 5 in 15m by businessId) fired for SAMMCK at 10:00:23Z (Datadog post 10:01:47Z). BABYMORI and KAPPAHL fired on the same monitor at 09:58:23Z and are triaged separately.

## Investigation
- Blast radius, 401s: aggregateLogs `@environment:prod "Outbound queue fetch failed" "status code 401"` over 3h and over 7d, grouped by @businessId, returned exactly BABYMORI 12, KAPPAHL 12, SAMMCK 9, all service snap-polling-service. Grouping by @error.request.baseURL puts all 33 on https://ilg004liveapi.snapfulfil.net/api. The 7d result equals the 3h result, so none before today. All `status:error` lines from snap-polling-service in 3h are status 401 (66 = 33 fetch lines + 33 "SNAP request failed" lines, same three businesses).
- First seen (listLogs, ascending): BABYMORI 09:56:05.129Z, KAPPAHL 09:56:05.133Z, SAMMCK 09:58:02.923Z. Each business fails 3 fetches (DESPATCH, RECEIPT, STOCK_MOVE) per 2-minute poll.
- SAMMCK timeline: polls at 09:50, 09:52, 09:54 and 09:56 have no error line; 09:58, 10:00 and 10:02 each have 3 failed fetches. Latest 401 in the index at 10:02:03Z; the 10:04 poll was not yet indexed when last checked (10:04:13Z).
- Polled businesses: 17 businesses log "Confirmation poll event received" (30 each in 1h). get-snap-connection (production) for all 17: ilg004 hosts SAMMCK, SAIRA and SPORTLUX (plus BABYMORI and KAPPAHL per the sibling record); ABBOTT, EPARFUM, ESCENTRIC, PHLUR, PURDYFIGG, STUBBLE, WILDSMITH on ilg005; BYOMA and ESCENTRICPL on ilg003; DOCKBAY and MANUCURIST on ilg001; INDU on ilg002. No 401 for any business outside the three. lookup-snap-instance includeBusinesses returned empty business lists, so the host map came from get-snap-connection.
- Control probe: snap-lookup RECSTATUS on ilg004 with the stored SPORTLUX credential returned the 6 rows at about 10:03Z. The host is up and accepting another business's credential. SAIRA and SPORTLUX have no 401 or error lines.
- SAMMCK probes with its stored credential (get-snap-connection, host ilg004, username SAMMCKAPI): snap-get-outbound-queue (top 100) and snap-lookup RECSTATUS both returned HTTP 401 at about 10:03Z. The stored config-service credential is rejected now.
- Config change: audit-search tenantId SAMMCK from 2026-10-26 returned 0 events. audit-search for all tenants from 2026-11-09T00:00Z (excluding sftp_login) returned 0. The backend id on get-business-config is be_400d7c92...; no revision information is exposed, so a change made outside audit-service is not ruled out.
- Deploys: snap-polling-service has one version tag (9af85287ca23) over 6h and over 24h (85,404 log lines); get_change_stories for snap-polling-service and config-service (04:00Z to 10:05Z, prod) returned no stories; config-service logs show one version tag (6b736842c4d4) over 6h. The deploy posts in the channel from 09:22Z to 09:42Z are shopify-connector, shopify-egress-service and sftp-connector; none is snap-polling-service or config-service.
- Maintenance: no Maintenance/ record names a window for 9 Nov (latest records 2 and 4 Nov). The sibling KAPPAHL run found no #bifrost-general post today.
- Monitor history: 3 trigger events in 24h (BABYMORI, KAPPAHL, SAMMCK), no recoveries, so not flapping.
- SAMMCK throughput: fuse.confirmation.published and fuse.confirmation.retrieved {businessid:sammck} over 7d each total 6, all in the 09:00Z hourly bucket today. SAMMCK was receiving confirmations until about the time the credential failed. Connector conn_9413... is active, confirmationsEnabled true, goods_in and goods_out confirmation use cases, SFTP csv egress.

## Outcome
Escalated as P2. Three live businesses on ilg004 have their stored credential rejected by Snap since 09:56 to 09:58Z, while ilg004 accepts another business's credential. Confirmations for those businesses are not being collected and will not resume until the credentials are fixed. No Fuse-side cause found. incident-response not invoked by this run.

## Not established
- Outbound queue depth and age for SAMMCK: the queue cannot be read with the rejected credential. Accumulation can only have begun at 09:58Z or a little earlier (last clean poll 09:56:04Z); the log does not record a successful fetch, so the exact last good fetch is unknown.
- Who or what invalidated the three credentials, and whether one event caused all three (shared host and a 2-minute window are established; the mechanism is not). Whether the SAMMCK username SAMMCKAPI was changed, locked or expired on the Snap side.
- Whether SAIRA is healthy beyond having no error lines (no direct probe was made).
- Customer impact in orders: how many confirmations SAMMCK has waiting.
- One probe in this run used a placeholder username against ilg004 (returned 401, meaningless); it is not evidence for anything.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794218507614999
- Monitor: https://app.datadoghq.com/monitors/326299823
- Siblings: Monitors/2026-11-09-snap-poller-401-kappahl.md, Monitors/2026-11-09-snap-polling-401-babymori-0958z.md
