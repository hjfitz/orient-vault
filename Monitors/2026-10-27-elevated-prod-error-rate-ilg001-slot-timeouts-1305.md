---
tags: [datadog-triage]
date: 2026-10-27
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: snap-adapter
business_id:
snap_instance: ilg001
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793106404340169"
opened_at: "2026-10-27T13:05:37Z"
resolved_at: "2026-10-27T13:16:00Z"
minutes_spent: 11
severity_assessed: P4
flapping: true
outcome: vendor
escalated_to:
ticket:
session_id: 6735df5f-a090-45cd-991d-d7f9cfef0ba8
status: resolved
---
# Platform error-rate monitor tripped by snap-adapter slot timeouts while Snap ilg001 was slow

## Fired
Monitor 180072217 (a log count over 2m, threshold > 2) triggered at 13:05:37Z, for the second time in five minutes (the first trigger was 13:00:37Z, recovering at 13:04:37Z). It is back to OK.

## Investigation
- **Every error the monitor counted came from snap-adapter.** Monitor query, 12:30Z to now, grouped by service: snap_adapter is the only service, with 25 error lines at 13:00–13:05Z. All are `Entity creation in SNAP failed`, `failureMode: slot_timeout`, `transient: true` ("Timed out after 30000ms waiting for a concurrency slot").
- **Two businesses were affected.** In the 13:00 hour, ICONICL had 17 lines (deliveryAttempt 1–3) and DOCKBAY had 8. All were sales orders, `identifiers.warehouse = SPACE`.
- **Nothing is held.**
  - All 17 distinct recordIds from the burst logged `Entity created in SNAP` on redelivery: ICKM5xx_1 by 13:03:41Z, and UK-9105xx by 13:06:56Z.
  - Across today (09:00Z onwards), 44 records hit a slot timeout. Zero lack a later `Entity created in SNAP`; that count is checked against a positive control query returning 44.
- **Snap was slow; our cap was not the problem.**
  - In code, `snap.request.latency` starts timing after the slot is acquired. `requestMetricsInterceptor` is registered before `withConcurrencyLimit`, and axios runs request interceptors in reverse order (snap-adapter master: `customer.http-router.ts`, `axios.builder.ts`).
  - On ilg001 that latency averaged 14.4–52.9s per bucket from 12:59 to 13:06Z. The 13:00 hourly rollup was 27.6s, while most hourly points over 48h sit at about 2–3s.
  - `snap.slot_queue_depth` on ilg001 hit max 8 at 12:59–13:01 and max 9 at 13:04–13:05. No other host reported a non-zero queue at 13:04–13:06.
- **Poller latency (`snap.poll.request.latency.avg`) is chronically high on ilg001 and ilg004.** ilg001 ran about 12s average at 12:32–13:08 today, against 11.3s and 8.7s in the same buckets yesterday. ilg003 jumped from about 0.2–0.5s to 5–12s at about 09:51Z today, but no ilg003 business shows in this alert.
- **No maintenance window covers this.** The `Maintenance/2026-10-19-snap-version-update-and-patch.md` window today was DB3 Poland at 09:30Z (est. 60 min). Nothing covers DB1/ilg001 at 13:05Z.
- **Flapping.** 33 trigger events over 7 days (4, 8, 4, 6, 1, 0, 6, 4 by day), 4 of them today (09:41, 11:20, 13:01, 13:06 Slack posts).
- **Shared cause with sibling monitors.**
  - 334832256 counts the same `Entity creation in SNAP failed` lines: 17 distinct recordIds in 13:00–13:06, over its threshold of 10.
  - 179927768 is the poller-side ilg001/ilg004/ilg003 latency.

Not established:
- No direct read probe of ilg001. The Fuse MCP returned 401, so there was no `get-snap-connection` for credentials.
- The business-to-host mapping for ICONICL and DOCKBAY was not checked against config. The ilg001 attribution rests on warehouse SPACE (DB1) and on ilg001 being the only host with a slot queue.
- Whether the 09:41 and 11:20 firings today had the same cause was not individually checked.

## Outcome
Vendor-side slowness on Snap ilg001 made snap-adapter time out waiting for its concurrency slot. Every affected record was created on redelivery, nothing is held, and the monitor recovered. P4, no incident. The monitor is a chronic flapper because transient slot timeouts that redeliver cleanly count towards it, so it needs a retune. No ticket filed in this run.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793106404340169
- Monitor: https://app.datadoghq.com/monitors/180072217
