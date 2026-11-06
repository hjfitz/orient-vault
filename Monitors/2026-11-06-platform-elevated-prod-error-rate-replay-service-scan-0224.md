---
tags: [datadog-triage]
date: 2026-11-06
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: replay-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793931885436209"
opened_at: "2026-11-06T02:23:37Z"
resolved_at: "2026-11-06T02:28:00Z"
minutes_spent: 5
severity_assessed: P4
flapping: true
outcome: false_positive
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# 02:23Z firing: 5 replay-service "Error unhandled" (HTTP 400 malformed JSON) during an internet scanner burst; not the config-service Postgres or tracking-service patterns

## Fired
More than 2 error-level domain:fuse logs in 2m. Shortened re-check of known patterns, run as a read-only subagent (watcher posts the reply). The cause turned out to be new, so the check was widened.

## Investigation
- Monitor-matching errors since 02:00Z (analyze_datadog_logs, the monitor's exact query, which I read from the monitor definition): replay_service "Error unhandled" x5, all 02:22:42Z to 02:22:43Z, version 0db33e5, revision replay-prod-00038-nwm. Nothing else matched, so none of the three earlier patterns recurred: no config-service "Dependency connection failed", no tracking-service "store failed", no snap_adapter slot_timeout since 02:00Z (the same query, plus an all-services error-level count since 01:50Z: replay_service 5, gfs-fedex-integration 1, the latter not domain:fuse).
- The 5 errors are `BadRequestException` status 400, "Expected ',' or '}' after property value in JSON at position 30", raised by NestJS body parsing (RoutesResolver.mapExternalException). They carry no path.
- Same seconds, same service: 404 warn lines for GET /, POST /, GET /foo.jsp, GET /crumbIssuer/api/json, PUT /shell_e8ea0fc87cd9f008.jsp (02:22:39-44Z), and at 02:21Z GET /index.php, /whm, /wp-json/batch/v1. Per-minute timeline of all replay_service logs since 01:50Z shows only these. Which request produced which 400 is not recorded.
- Recurrence: replay_service 404 warn logs per day, 30 Oct to 5 Nov: 741, 444, 460, 281, 597, 1165, 1617 (25 so far today). Error-level "Error unhandled" in 7d: 1 on 5 Nov 11:43Z (`Failed to decode param '%C0'`, during a wp-config.* scan, 928 warn/error lines in 20 min) and these 5. So constant background scanning; two bursts reached error level.
- Impact checks: 5xx since 01:50Z across prod: 0 (analyze_datadog_logs on @http.status_code / @statusCode 5xx and "- 5xx" request text; no match); max oldest_unacked_message_age across prod subscriptions since 01:50Z = 2s (top-5 scalar, snap_poll_customer sub); replay-list-failures production, createdAt 2026-11-06: total 0.
- Cloud SQL (config-service-prod, database_id bifrost-prod-global1:config-service-prod), 1-minute metrics 22:30Z to 02:27Z: gcp.cloudsql.database.up = 1 every minute, instance_state = 1, available_for_failover = 1 (no failover signal), cpu.utilization max 21.8% (00:34Z), memory.utilization 29-30%, postgresql.num_backends 2 throughout, new_connection_count 8-10/min. fuse.postgres.up (environment:prod) dipped below 1 at 23:04Z (0), 23:08Z (0.5), 23:28Z (0), 01:45Z (0), 01:46Z (0.5), nothing since; max fuse.postgres.latency.max 1453ms (23:04Z). The 02:22Z dip to 0 and 20.8s latency are environment:dev, not prod. So Cloud SQL's own metrics show no restart, failover or CPU/memory saturation at those minutes. The failures are visible only from config-service's side.
- Datadog events (12h, cloudsql/config-service-prod, sources gcp/alert/change_tracking/resource_changes): only 2 Cloud Run changes for config-service-prod at 15:33Z on 5 Nov (service updated, revision 00070). No Cloud SQL events, and a Cloud SQL log search (source gcp.cloudsql_database, 24h) returned 0, so maintenance windows and instance logs are not in Datadog.
- Thread check: every earlier alert post since 23:29Z (1793921445.626419, 1793926605.353019, 1793927204.412889, 1793929665.748739) has a reply; the only post without a reply is this one (1793931885.436209).

## Not established
Where the scanner traffic comes from and whether replay-prod is meant to be reachable from the internet (ingress setting not visible via Datadog). Which of the 404 requests carried the malformed JSON. Why the config-service Postgres checks fail: Cloud SQL metrics look healthy but no Cloud SQL logs, operations or maintenance events were readable here (needs `gcloud sql operations list` / Cloud SQL logs in GCP).

## Outcome
False positive, P4. The monitor counted 5 error-level lines produced by unauthenticated-style scanner traffic on replay-service; no 5xx, no backlog, nothing held, and none of the customer-facing patterns recurred. Monitor mistuning lead: replay-service logs client 400s as error "Error unhandled", so a scan can trip a monitor that needs only 3 lines in 2 minutes. Not ticketed here; the Postgres lead (log the dependency check at warn until repeated failure; read Cloud SQL logs and operations in GCP) stands.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793931885436209
- Monitor: https://app.datadoghq.com/monitors/180072217
- Prior records: Monitors/2026-11-05-platform-elevated-prod-error-rate-config-service-postgres-2329.md, Monitors/2026-11-06-platform-elevated-prod-error-rate-tracking-service-store-0055.md, Monitors/2026-11-06-platform-elevated-prod-error-rate-config-service-postgres-0146.md
