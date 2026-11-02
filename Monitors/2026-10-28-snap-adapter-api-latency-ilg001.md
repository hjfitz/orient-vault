---
tags: [datadog-triage]
date: 2026-10-28
monitor: "[FUSE][Snap Adapter] API latency threshold breached (ilg001 group)"
service: snap-adapter
business_id:
snap_instance: ilg001
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793111786064839"
opened_at: "2026-10-28T12:06:08Z"
severity_assessed: P3
flapping: true
outcome: vendor
escalated_to:
ticket:
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: resolved
---
# ilg001 Snap API latency Alert, same slowdown as ilg003/ilg004 since each host's version update

## Fired
Monitor 179927768 (avg 20m `snap.poll.request.latency.avg` > 5000ms) alerted for ilg001 at 12:06:08Z. The group is under a scheduled downtime until 14:38Z, so no new Slack post; reply went into the latest ilg001 thread. Sibling groups ilg003/ilg004 and platform error-rate monitor 180072217 fired together.

## Investigation
- 10-min buckets 08:10-12:00Z: ilg001 3.3-13.2s, ilg003 3.4-11.6s, ilg004 3.3-11.2s; ilg002 and ilg005 flat (~0.2-1.2s).
- 14d view: each of ilg001/003/004 stepped from ~0.1-0.3s to multi-second in the 4h bucket containing its Snap update window (21, 27, 22 Oct; Maintenance/2026-10-19-snap-version-update-and-patch.md). ilg002 window opened 10:00Z today, no step through 12:07Z.
- Poll requests minus successes over 6h: 0 on ilg001/003/004/005.
- snap_adapter: 6 `Entity creation in SNAP failed` in 12:00Z hour, all DOCKBAY, 30s concurrency-slot timeout, transient:true.
- Monitor has fired repeatedly 27 Oct (events 131 matches in 2d); downtimes set by Harry on ilg001/003/004.

## Re-fire 12:52:08Z (checked ~12:54Z)
- ilg001 10-min latency 12:10-12:50Z 4.2-9.8s, unchanged range; ilg003/004 move with it; ilg002/005 max 2.9s.
- ilg001 poll requests = successes in 30-min buckets 11:00-13:00Z (182/90/187/255).
- No transient creation failures since 12:06Z; oldest unacked on prod sales_order sub max 59s.
- New unrelated failure: PURDYFIGG #6521935 12:50:05Z, schema_validation, non-transient, ShipAddress.0.Name too big (<=50); not in Snap, @fuse-support pinged to fix and replay.
- Replied in same thread (no broadcast): ts 1793192063.107159.

## Re-fire 16:22:08Z (Alert, checked ~16:37Z)
- Monitor group states: ilg001 Alert, ilg003 Alert (both 16:22:08Z), ilg004 Warn, ilg002/005 OK. No ilg001 channel post for this Alert; replied in the 14:40 ilg001 thread (ts 1793205420.745919, no broadcast). ilg003 has its own Alert thread (another agent).
- Creates per 10 min 15:40-16:40Z: 123/132/129/172/246/229, PURDYFIGG wave (888 created in the last hour). 1 slot_timeout in the last hour (PURDYFIGG 16:15:53Z, transient). snap_adapter error logs 15 in last hour vs 23 before.
- Ack-deadline monitor 323648859 Warn on snap_adapter create_record_sales_order sub since 16:24:39Z.
- New: ESCENTRIC #138864 non-transient schema_validation (ShipAddress.0.Line1 >50), every ~5 min from 14:15:03Z, still failing 16:30Z; @fuse-support pinged.
- PURDYFIGG #6521935: 35 failures 12:50-15:45:05Z every ~5 min, none since, no created log for it.
- Datadog metrics API timed out on every query, so no latency values or backlog numbers this run.

## Not established
Current ilg001 latency value and backlog size on the sales order sub (metrics API timeouts); whether #6521935 is in Snap now; whether the update causes the slowdown; whether DOCK88BDDEA25C4 / DOCKEB452A001F6 were created after redelivery; which host DOCKBAY uses; direct host probe (Fuse MCP auth failing, no Snap credentials).

## Outcome
Vendor, P3, already raised with Snap (INC-42). No escalation. Monitor is chronic-flapping while the hosts stay slow.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793111786064839

## Re-fire 17:17:08Z (Alert, 20m avg 5.50s; checked ~17:20Z)
- Own thread for this firing (ts 1793207919.536849); replied there without broadcast (ts 1793207992.910089).
- Metrics worked this run (timeseries by snap_host, 10-min). ilg001 s: 16:20 2.6, 16:30 3.8, 16:40 3.5, 16:50 2.9, 17:00 4.5, 17:10 7.3 (partial). ilg003 17:10 7.5, ilg004 6.1, ilg002 0.3, ilg005 0.7. 20m avg 5.06s at 16:24Z vs 5.50s now: held, newest buckets highest of 3h.
- Creates 226 in last 10 min (40 min: PURDYFIGG 770, DOCKBAY 138). Failures in 40 min: 13 (ESCENTRIC #138864 x7 non-transient, latest 17:10:03Z; DOCKBAY x5 + PURDYFIGG x1 transient, 16:46-16:51Z). No #6521935 failures. snap-polling-service error logs last hour: 0.
- Not verified this run: that the 6 transient records were created (taken from earlier thread posts, not re-queried).
- Not established: why Snap is slow; whether #6521935 exists in Snap; host probe (Fuse MCP 401).
- Verdict unchanged: vendor, P3.

## Re-fire 17:57:08Z (Alert to Warn, ilg001/003/004; checked ~18:00Z)
- Monitor Warn = avg(20m) > 2000ms, Alert > 5000ms. Values in alert text: ilg001 4535ms, ilg003 4758ms; stepped down from Alert but ~2x Warn, not recovered.
- 10-min latency (s) 17:00-17:50Z: ilg001 4.5/7.3/6.2/6.8/4.3/4.9; ilg003 2.4/7.5/6.7/8.4/4.1/5.7; ilg004 4.4/6.1/6.3/6.6/4.4/5.5; ilg002 0.1-1.1, ilg005 0.3-1.5. Last 5-min bucket: ilg001 4.2, ilg003 5.3, ilg004 5.2.
- snap.poll.request = .success on all hosts 17:00-17:59Z. Since 17:25Z: 0 `Entity creation in SNAP failed`, 0 error-status snap_adapter logs.
- ESCENTRIC #138864 still not created (last attempt 17:10:03Z, nothing after). PURDYFIGG #6521935: no logs since 17:00Z, no created log. PURDYFIGG creates continue (17:55:25Z).
- One reply for all three hosts in ilg003's Alert thread (ts 1793210321.982649), reply ts 1793210405.995859, no broadcast. Verdict unchanged: vendor P3.
- Not established: why Snap is slow; whether #6521935 is in Snap; host probe (Fuse MCP 401).

## Re-fire 20:01:08Z (Alert, ilg001; checked ~20:10Z)
- No channel post for this firing (monitor 179927768 carries muted_until_ts 1793302284). Replied in ilg003's Alert thread, reply ts 1793217804.395539, no broadcast.
- 10-min latency (s) 18:00-20:00Z (20:00 partial): ilg001 3.7/3.6/2.7/3.0/3.6/3.6/4.9/3.0/2.8/3.0/3.6/4.1/6.5; ilg003 3.9/3.7/2.4/3.1/3.6/3.3/4.3/3.2/2.7/2.7/5.0/3.6/5.8; ilg004 3.9/3.6/2.9/3.2/3.8/3.2/5.0/3.5/3.1/3.2/4.7/3.8/6.2. ilg002 0.1-0.4, ilg005 0.2-0.5. Same plateau recrossing 5000ms, lower than the 17:00-17:50Z peak (4.3-8.4).
- snap.poll.request = .success on ilg001/003/004 in all 30-min buckets 18:00-20:10Z.
- 0 `Entity creation in SNAP failed` and 0 error-status snap_adapter logs since 17:57Z. `Entity created in SNAP` per hour: 725 (17Z), 52, 34, 7 (20Z to 20:10). Volume low, PURDYFIGG wave over.
- ESCENTRIC #138864 / PURDYFIGG #6521935: no log mentions of either id since 17:10Z.
- Not established: why Snap is slow; whether either order exists in Snap (Fuse MCP 401, no probe); whether silence means created or just not retried.
- Verdict unchanged: vendor, P3.

## Re-fire 06:01:08Z 29 Oct
Checked with the ilg003 record (one reply for all three hosts, thread 1793253749.135479): vendor P3, same plateau. ilg001 alert value 6611.7ms. Detail in 2026-10-28-snap-adapter-api-latency-ilg003.md.
