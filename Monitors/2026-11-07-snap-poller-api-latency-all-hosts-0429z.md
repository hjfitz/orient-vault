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
flapping: true
outcome: vendor
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: open
---
# Snap poller request latency: intermittent fixed ~4.1s delay on all five prod Snap hosts since 04:25Z, reproduced from outside our network

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

## Re-check 2026-11-07 05:45-05:53Z (monitor re-fired Warn 05:43:08Z ilg001/003/004/005 and 05:44:08Z ilg002; Slack posts 05:44:27-05:45:25Z, no Support Bot replies at read time)
Re-fire context: the monitor recovered 05:20-05:21Z (20m avg 1361-1987 ms) and went Warn again 05:43-05:44Z (20m avg 2119-2280 ms). Five new threads: ilg003 1794030267.176619, ilg004 1794030269.062819, ilg005 1794030270.651339, ilg001 1794030272.185749, ilg002 1794030325.716199.
- Correction to the earlier read: it was not a flat step. `snap.poll.request.latency.avg` by snap_host (2-min buckets, 04:00-05:50Z) is bimodal, each bucket either 45-300 ms or 4095-4250 ms (the odd ones 1.4-3.2s are partial buckets): high at 04:26-04:37, 04:44-04:49, 04:54-05:01, 05:04, 05:26 (partial), 05:36, 05:42-05:48; normal in between and from 05:50. All five hosts move in the same buckets. In high buckets median and max agree (e.g. ilg002 median 4137, max 4151 at 05:36) so every request in the bucket is about 4.1s; one 5.06s max on ilg003.
- Not our egress alone: unauthenticated GET to each host (`/api/v2/snaplookups`, returns 401) from this workstation, outside GCP, 05:48:10Z: dns/tcp/tls 0.02-0.03s, time to first byte 4.05-4.13s on ilg001/002/003 (3 of 3), ilg004 1 of 3, ilg005 2 of 3, the rest 0.02s. Repeat samples: ilg005 05:50:48-05:51:18 (6 requests) 2 slow at 4.08/4.06s, 4 fast at 0.017-0.019s; ilg002 30 requests 05:51:31-05:52:44 3 slow (4.061-4.088s), 27 fast (max 0.020s), nothing in between. So at request level it is a fixed ~4.07s extra on some requests, before any auth, on all hosts. The poller series went back to 84-138 ms at the 05:50 bucket, consistent with the probe going fast from about 05:48:40Z.
- All five hostnames resolve to one IP (209.143.134.157) from this workstation (getent hosts). Not checked from GCP.
- Nothing failing: `snap.poll.request.failure`, `snap.request.failure`, `snap.breaker.opened/rejected`, `snap.circuit_opened` return no series 04:00-05:46; `snap.slot_queue_depth` and `snap.rate_queue_depth` max 0; poll successes 395 per 10 min on every bucket except the partial last; log aggregation 03:30-05:46 for snap-adapter and snap-polling-service: 0 error-status logs, 0 matching timeout/ETIMEDOUT/ECONNABORTED/ECONNRESET/EAI_AGAIN/ENOTFOUND/slot_timeout; 3640 warn logs (poller, steady).
- Backlog: all prod subscriptions, max oldest unacked age 04:00-05:46: snap_poll_customer 14.2s, snap_adapter sales_order 1.2s, everything else 0; no prod subscription over 120s; undelivered max 1.8. `replay-list-failures` production createdAt 2026-11-07: total 0.
- Customer effect: `snap.messages.received` equals `snap.event_handled.success` in every 10-min bucket 03:00-05:46 (e.g. 5, 9 at 05:30, 05:40) and `snap.entity_not_created` has no series, so every message snap-adapter received was handled. snap-adapter sales_order create handling time (`fuse.request.latency.avg`, service snap-adapter, flow create) was 1.9-2.0s hourly average 00:00-04:00Z, 8.7s over 04:00 hour and 8.4s over 05:00 hour; 10-min peaks 24.3s at 04:30, 18.7s at 05:06, 19.7s at 05:14; yesterday 06:00-19:00Z hourly averages were 2.4-11.3s so the level is not unusual for a loaded day. Volume is 1-9 creates per 10 min. That is seconds to tens of seconds per create, not minutes.
- snap-adapter's own Snap call latency (`snap.request.latency.avg`, ilg005 only, 4 requests per bucket) was 4.5-6.1s at 04:24-04:34 and 4.5-4.9s at 05:04-05:14 and 05:24, but 399 and 397 ms at 04:44 and 04:50 when the poller was at 4.1s, and 4.5-4.9s at 05:06/05:14 when the poller was normal, so adapter and poller episodes do not line up bucket for bucket (sparse samples).
- Other dependencies, 04:00-05:46Z: config-service request latency avg 0.4-12 ms, config-service Postgres 3-447 ms (avg 112), dedupe-service 41-147 ms, dedupe Mongo 9-29 ms, shopify-connector Mongo 6-21 ms, collector http 13-52 ms, sftp-connector 1-274 ms, rest_connector 1-92 ms; none over 1s. shopify-connector poll avg (`fuse.request.poll.avg`) 550-2446 ms, over 1s at 04:00, 04:04, 04:54, 05:00. No other dependency shows a 4s step.
- Datadog events 03:00-05:46Z for the snap services: only the monitor's own alert events, no deploy or change event. GitHub deployments (earlier check): snap-adapter last terraform-prod 2026-11-06T18:00:52Z, which the adapter's revision `snap-adapter-prod-00099-b4z` was serving in the metric tags. No `Maintenance/` record covers 2026-11-07; #bifrost-general had no messages since 04:00Z; #snap-wms had only Datadog posts.
- Monitor behaviour: with a delay of about 4.1s the 20m average cannot reach the 5000 ms alert line (highest per-host 2-min bucket avg was 5362 ms at 05:00 on ilg005, a single bucket); the 20m average only crosses 2000 ms warn when more than about half the window is slow, which is why it recovered at 05:20 and re-fired at 05:43.
- Not established: why Snap adds ~4.07s to some requests (maintenance, load, a front-end or network step on their side); whether the slow requests on our own GCP path hit the same IP and the same fraction (probe was from a workstation); Cloud NAT / VPC connector / egress IP changes (no such metrics looked up in Datadog; not queried); per-business impact (hosts not mapped to businesses); poller deploy history; whether snap-adapter's 24s create handling is caused by the added 4s on each of several Snap calls (not tested).

## Re-check outcome
vendor, P3. The delay reproduces from outside our network on Snap's endpoint (401 response delayed), on all five hosts together, with nothing failed, held or backlogged; only effect seen is seconds-to-tens-of-seconds longer snap-adapter creates. Still intermittent at 05:51Z. Escalate if failures, backlog or held records appear, or if creates start taking minutes.
