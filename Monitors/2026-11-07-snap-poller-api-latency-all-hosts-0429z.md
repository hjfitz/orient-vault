---
tags: [datadog-triage]
date: 2026-11-07
monitor: "[FUSE][Snap Queue Polling Service] API latency threshold breached"
service: snap-polling-service
business_id:
snap_instance: ilg001-ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794025827436579"
opened_at: "2026-11-07T04:29:08Z"
severity_assessed: P3
flapping: false
outcome: unresolved
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Snap poller request latency stepped from about 0.1s to a flat 4.1s on all five prod Snap hosts at about 04:25Z

## Fired
Monitor 179927768 (warn > 2000 ms, alert > 5000 ms, avg over 20m, by snap_host) went Warn for ilg002 at 04:29:08Z and for ilg001, ilg003, ilg004 and ilg005 at 04:31:08Z. Five alert posts in #bifrost-notifications, none with a reply when checked at about 04:34Z. Parent ts: ilg002 1794025827.436579, ilg004 1794025944.234109, ilg003 1794025946.142099, ilg001 1794025947.863029, ilg005 1794025949.372809.

## Investigation
- `snap.poll.request.latency.avg` by snap_host, 2-minute buckets: 04:20 to 04:24 was 54-99 ms on ilg001-004 and 86-91 ms on ilg005; from 04:26 every host reads 4123-4198 ms, and at 04:32 ilg001 4123, ilg002 4131, ilg003 4136, ilg004 4126, ilg005 4156. For ilg002 the median, p95 and max in those buckets are all 4151-4198 ms, so every request is about 4.15s rather than a tail. The six hours before were 58-160 ms (ilg005 around 90 ms avg).
- snap-adapter (`snap.request.latency.avg`, only ilg005 traffic in the window, a handful of requests per bucket) went 409 ms at 04:15 to 4551 ms at 04:25 and 6074 ms at 04:30 (max 6600).
- Nothing failing: `snap.poll.request.failure` and `snap.request.failure` return no series, `snap.breaker.opened` none, `snap.slot_queue_depth` 0, snap-adapter error/warn logs in the last 12m none, no timeout/ETIMEDOUT logs in the last 30m. Poller polls continue every 5 minutes (`fuse.tick.poll` at 04:10/15/20/25/30) and `snap.poll.request.success` is steady.
- No backlog or held records: all prod snap_adapter create_record_* subscriptions 0 undelivered and 0 oldest-unacked-age for 04:18-04:31; `bifrost.prod.snap_poll_customer.v1.sub` oldest unacked age 4s from 04:28. `replay-list-failures` (production, created 2026-11-07) total 0.
- Poller warn logs (Consignment StU not found, stock movement direction, connector not enabled for confirmations) run at the same rate in the last 12m as in the last hour (270 vs 1350 / 60m), so unrelated to the step.
- No Snap maintenance window today: no `Maintenance/` record covers 2026-11-07; the latest are 11-02 API update (11-03 10:00-10:30Z) and 11-04 emergency patch (11-05 10:00Z). #bifrost-general and #snap-wms had no Snap notice since 11-05 in the last day of messages read.
- Deploys: GitHub deployments for snap-adapter, last terraform-prod 2026-11-06T18:00:52Z. The snap-queue-polling-service deployments list ends 2026-07-07 (looks incomplete, not relied on). No Datadog change event for a snap service found.
- Probe: one `snap-lookup` RECSTATUS against ilg005 (credentials from get-snap-connection for PURDYFIGG) returned 200 with rows at about 04:33Z. The tool reports no timing.
- Precedent: 2026-10-21 all five hosts slowed together (record 2026-10-21-snap-adapter-api-latency-multi-host-1116), triaged P3 vendor, nothing held.
- Not established: whether the 4.1s is added on the Snap side or on our path to Snap; per-business impact (lookup-snap-instance includeBusinesses returned 0 businesses for ilg002 and ilg005, so the host to business mapping could not be read that way); poller deploy history.

## Outcome
Unresolved, P3 provisionally. Fleet-wide latency step with no failures, backlog or held records at 04:33Z. Re-check for failures, slot waits, or the 5000 ms alert threshold.

## Links
- Slack thread (ilg002): https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794025827436579
- Monitor: https://app.datadoghq.com/monitors/179927768
