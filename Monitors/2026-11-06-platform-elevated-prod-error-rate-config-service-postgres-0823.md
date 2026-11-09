---
tags: [datadog-triage]
date: 2026-11-06
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: config-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793953483806379"
opened_at: "2026-11-06T08:23:37Z"
severity_assessed: P4
flapping: true
outcome: real_minor
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# 08:23Z firing: 3 config-service Postgres connection-check errors again (third recurrence of the 23:29Z / 01:46Z pattern)

## Fired
More than 2 error-level domain:fuse logs in 2m (monitor 180072217, alert post 08:24:43Z). Shortened re-check of known patterns, run as a read-only subagent (watcher posts the reply).

## Investigation
- Matching errors since 08:10Z (analyze_datadog_logs, the monitor's exact query): config-service "Dependency connection failed" x3, nothing else. search_datadog_logs rows: 08:22:22Z and 08:22:26Z `read ECONNRESET`, 08:23:20Z `Postgres ping took longer than 2000ms`; `dependency: postgres`, revision config-service-prod-00071-czr, version 6b73684 (same revision and shapes as 23:29Z and 01:46Z).
- Not any of the other patterns: no tracking-service "store failed", no snap_adapter slot_timeout or "SNAP request failed", no replay-service "Error unhandled" in the matching set.
- Postgres gauge: `min:fuse.postgres.up` over 08:20-08:26Z = 0 (scalar); `fuse.postgres.latency` returned null for the window. Cloud SQL (config-service-prod) over the last 45 min: avg CPU 0.13, avg num_backends 2.1 (scalar avg, so not a peak).
- config-service logs since 08:00Z (status error or warn): 3 errors above plus 9 warn "Entity not found"; no other errors.
- 5xx: prod logs since 08:00Z with http.status_code / response.status / statusCode / status_code 500-599: 0 rows. `status:error` prod logs since 08:00Z by service: gfs-coll8-integration 92, gfs-fedex-integration 10, config-service 3 (the first two are not domain:fuse matches of this monitor; not examined).
- Backlog: `max:gcp.pubsub.subscription.oldest_unacked_message_age{subscription_id:*prod*}` max over 45 min = 24s.
- Held records: replay-list-failures (production, createdAt 2026-11-06) total 21, all PURDYFIGG goods_out_confirmation created 07:06:40Z and earlier (top 5 shown all 07:06:40Z), same count as the 07:29Z triage; none new, none from this alert.
- Recurrence: config-service "Dependency connection failed" by hour over 24h: 12Z 2, 15Z 1, 20Z 3, 23Z 6, 01Z 3, 07Z 2, 08Z 3 (20 in 24h). Postgres hits so far: 23:29Z, 01:46Z, 08:23Z firings.
- Channel read (slack_read_channel from 07:03Z): alert posts since 07:25Z are 07:26:45Z (1793950005.536019, has the 07:29Z reply) and the new 08:24:43Z post (1793953483.806379, no reply). No other unreplied alert thread since 07:25Z.

## Not established
Why the Postgres connection checks fail (Cloud SQL maintenance or restart, network, pool config); no Cloud SQL logs or events were read. Whether any caller saw config-service failures (no 5xx logged, but request-level success was not measured). Peak Cloud SQL CPU or connections (only averages taken). Whether the 07Z config-service errors (2) were part of this pattern was not checked in detail.

## Outcome
Real minor, P4. Same config-service Postgres connection-check pattern as 23:29Z and 01:46Z: three error-level lines, `fuse.postgres.up` 0 in the window, no 5xx, no backlog, nothing new held. Chronic (20 such logs in 24h); the monitor counts the check's error line so three trips it. Earlier lead stands: log the dependency check at warn until repeated failure, and look at Cloud SQL connectivity. No ticket filed here.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793953483806379
- Monitor: https://app.datadoghq.com/monitors/180072217
- Prior records: Monitors/2026-11-05-platform-elevated-prod-error-rate-config-service-postgres-2329.md, Monitors/2026-11-06-platform-elevated-prod-error-rate-config-service-postgres-0146.md
