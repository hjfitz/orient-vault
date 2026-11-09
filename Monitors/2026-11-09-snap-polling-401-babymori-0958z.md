---
tags: [datadog-triage]
date: 2026-11-09
monitor: "[FUSE][Snap Queue Polling Service] SnapFulfil rejecting credentials (401)"
service: snap-polling-service
business_id: BABYMORI
snap_instance: ilg004
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794218387403659"
opened_at: "2026-11-09T09:58:23Z"
severity_assessed: P3
flapping: false
outcome: escalated
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# SnapFulfil answers 401 to the BABYMORI outbound-queue fetch (ilg004), ongoing

## Fired
Monitor 326299823 (log alert, more than 5 "Outbound queue fetch failed" "status code 401" per business in 15m) fired for `@businessId:BABYMORI` at 09:58:23Z. The monitor is new in the watch (created 2026-09-29, last edited 2026-11-05) and has no earlier alert events in the last 7 days.

## Investigation
- 401 onset and rate: first line 09:56:05.129Z; the poller logs 3 "Outbound queue fetch failed" lines per ~2 min poll, at 09:56, 09:58 and 10:00 (9 in total as of 10:00:07Z). No such line for BABYMORI in the previous 7 days (hourly count, analyze_datadog_logs). The 09:54 poll logged only the info heartbeat, with no error.
- Still failing at 10:00:46Z: the newest 401 is 10:00:07.655Z.
- Same window, other businesses (names only, not investigated): KAPPAHL first 401 at 09:56:05.133Z (9 lines), SAMMCK first at 09:58:02.923Z (6 lines). No other business has 401s from the poller in 3h.
- Host and instance: Fuse MCP get-snap-connection (production) gives host ilg004liveapi.snapfulfil.net, on Snap DB 4 (sites EGA 0007, EG25 0008, LGW 0009, BH 0011), per lookup-snap-instance. The username on the stored connection is FUSEBABYMORI. get-business-config shows the same host and username as the connection.
- Direct read-only probe: snap-get-outbound-queue (top 100) with the stored connection returned "Request failed with status code 401". So config-service's credential is rejected by the host right now.
- Config change: audit-search with tenantId BABYMORI since 2026-11-02 returned 0 events. audit-search across all tenants since 2026-11-08 (sftp_login excluded) returned 0 events, and config_change and credential_access since 2026-11-09 returned 0 events each.
- Deploys: get_change_stories for snap-polling-service and config-service (prod, 2026-11-08 09:00Z to 2026-11-09 10:05Z) returned no stories. GitHub deployments: config-service last prod deploy 2026-11-05 15:34Z. The snap-queue-polling-service repo lists no deployment after 2026-07-07 (terraform-prod environment only, so app image deploys may not appear there).
- Maintenance: no Maintenance/ record is dated 2026-11-09; the latest (2026-11-04) is an emergency patch window on 2026-11-05. #bifrost-general pin and ILG mail not checked.
- Other services: no 401 error or warn lines for any business from other services (snap-adapter etc.) in the last 3h.
- Impact: the BABYMORI backend is a SNAP backend with one prod SFTP connector (Baby Mori SFTP; master_data, sales_order, purchase_order; confirmationsEnabled true), so confirmations return as CSV over SFTP. Customer vault page is generated from config only, with no narrative and no known-context. BABYMORI shows no fuse.confirmation.published data in 14 days, and only 5 dedupe_service log lines on each of 11-05 and 11-06 outside the poller. Poll heartbeat only (about 720 lines/day) since 2026-10-26.
- Queue backlog and time since last successful poll: the outbound queue cannot be read (401), so the backlog is unknown. The last poll without a 401 started 09:54Z, so at most the polls from 09:56Z on have failed (about 5 minutes at 10:00:46Z).

## Outcome
Escalated, not declared. The credential the poller holds for BABYMORI is rejected by ilg004 now, nothing in Fuse changed it (no audit event, no deploy), so it will not self-resolve without someone fixing the credential at Snap or in config-service. Severity P3 is provisional: BABYMORI shows no confirmation traffic in 14 days, so customer impact is unquantified. Raise to P2 if live traffic or a backlog is found, or if KAPPAHL and SAMMCK show the same cause.

Not established: who rotated or reset the credential on ilg004 and when; whether KAPPAHL and SAMMCK share the host (not checked); backlog size; whether BABYMORI has live confirmations; whether a Snap-side change (not Fuse) caused all three.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794218387403659
- Monitor: https://app.datadoghq.com/monitors/326299823
