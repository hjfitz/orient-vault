---
tags: [datadog-triage]
date: 2026-10-28
monitor: "[FUSE][Snap Adapter] API latency threshold breached"
service: snap-adapter
business_id:
snap_instance: ilg004
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793112503645869?thread_ts=1793112503.645869&cid=C099WKQTE8G"
opened_at: "2026-10-28T12:02:08Z"
severity_assessed: P3
flapping: true
outcome: real_minor
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: open
---
# ilg004 Snap API latency >5s (chronic, ilg001/003/004 together)

## Fired
Group ilg004 went to Alert at 12:02:08Z (avg(last_20m) snap.poll.request.latency.avg > 5000). No Slack post for this firing was found; reply went to the latest ilg004 thread.

## Investigation
- 10-min buckets, last 6h: ilg001/003/004 4-13s in lockstep; ilg002/005 0.1-1s.
- 14-day daily avg: ilg001 steps up from 21 Oct (2.9-5.9s), ilg004 from 22 Oct (3.2-5.6s), ilg003 on 27 Oct (5.3s), each matching its maintenance date in Maintenance/2026-10-19-snap-version-update-and-patch.md. Timing correlation only.
- Monitor events: 28 in 24h, flapping.
- Today's window is DB2 (ilg002, 10:00Z); ilg002 not degraded (one 2.9s bucket at 10:30Z).
- snap_adapter errors last hour: 6, DOCKBAY slot timeouts (transient) at 12:05Z. 24h by hour 1-25.
- Not established: cause of post-patch slowness (no Snap probe, Fuse MCP unreachable); DOCKBAY host; ilg002 after patch; why no Slack post for this firing (monitor muted_until 19:28Z, reason unknown).

## Re-fire 13:05Z (1793192708)
- ilg004 latency 4.4-11.2s in 10-min buckets 10:10-13:00Z (last 5.3s); ilg001/003 in step, ilg002/005 0.1-2.8s.
- Polls: request minus success 0 hourly 11:00-13:00Z (514/707/60). Oldest unacked max 2s sales_order, 15s master_data; slot_queue_depth ilg004 0.
- No new transient/slot_timeout failures after 12:09Z. New: PURDYFIGG #6521935 non-transient schema_validation (ShipAddress.0.Name >50 chars) every 5 min 12:50-13:05Z; fuse-support pinged in thread (not broadcast).
- Not established: cause of slowness; PURDYFIGG's Snap host; whether #6521935 failed before 12:50Z.
- Reply: thread ts 1793192851.881279.

## Re-fire 17:19Z (1793207948), Warn to Alert
- ilg004 10-min avg latency (s): 16:10 5.2; 16:20-16:50 3.0/3.3/2.9/4.4; 17:00 6.1; 17:10 5.3 (partial). 14:30-16:00 range 2.6-4.1. Risen over ~20 min, within the day's range; crossed 5s, no new step.
- snap-polling-service error logs last 30m: 0. snap.poll.request.success ilg004 75-88 per 10m 16:30-17:10Z.
- `Entity created in SNAP` 102 in 10m (fleet-wide, not per host).
- Not established: cause of slowness; request-count vs success (count query returned nothing); per-host creates; host probe (Fuse MCP 401).
- Reply: ilg001 alert thread ts 1793207919.536849 (no ilg004 post in channel), reply ts 1793208088.393769, not broadcast. Verdict vendor P3.

## Outcome
Real, minor, chronic. Recommend retune and raising with ILG; ticket worth filing, not filed.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793112503645869
- Monitor: https://app.datadoghq.com/monitors/179927768

## Re-fire 17:57:08Z (Alert to Warn, ilg001/003/004; checked ~18:00Z)
- Monitor Warn = avg(20m) > 2000ms, Alert > 5000ms. Values in alert text: ilg001 4535ms, ilg003 4758ms; stepped down from Alert but ~2x Warn, not recovered.
- 10-min latency (s) 17:00-17:50Z: ilg001 4.5/7.3/6.2/6.8/4.3/4.9; ilg003 2.4/7.5/6.7/8.4/4.1/5.7; ilg004 4.4/6.1/6.3/6.6/4.4/5.5; ilg002 0.1-1.1, ilg005 0.3-1.5. Last 5-min bucket: ilg001 4.2, ilg003 5.3, ilg004 5.2.
- snap.poll.request = .success on all hosts 17:00-17:59Z. Since 17:25Z: 0 `Entity creation in SNAP failed`, 0 error-status snap_adapter logs.
- ESCENTRIC #138864 still not created (last attempt 17:10:03Z, nothing after). PURDYFIGG #6521935: no logs since 17:00Z, no created log. PURDYFIGG creates continue (17:55:25Z).
- One reply for all three hosts in ilg003's Alert thread (ts 1793210321.982649), reply ts 1793210405.995859, no broadcast. Verdict unchanged: vendor P3.
- Not established: why Snap is slow; whether #6521935 is in Snap; host probe (Fuse MCP 401).

## Re-fire 21:51Z (1793224268, ilg004; checked ~21:56Z)
- 10-min avg latency 20:00-21:50Z (s): ilg004 4.4/3.8/3.0/2.9/2.9/2.8/3.0/3.7/3.8/3.8/4.8/5.6; ilg001 4.7/3.5/2.8/2.7/3.4/2.8/2.8/3.7/3.5/3.7/5.0/5.0; ilg003 4.3/3.7/2.7/2.7/2.7/2.5/3.0/3.8/3.7/3.5/4.8/4.7. Below the earlier 5-13s range. ilg002 0.1-0.2, ilg005 0.2-0.4.
- snap.poll.request = .success on all five live hosts 20:00-21:55Z. 0 error-status Snap logs and 0 `Entity creation in SNAP failed` since 20:10Z (last failure 17:22Z). `Entity created in SNAP`: 29 in 20Z hour, 58 in 21:00-21:55Z.
- ESCENTRIC #138864 and PURDYFIGG #6521935: no logs since 17:10Z.
- Same plateau, no change in shape. Verdict vendor P3. Reply in ilg001 thread ts 1793217756.199449, reply ts 1793224386.262129, not broadcast. No Slack post existed for this firing (monitor muted until ~19:30Z 29 Oct).
- Not established: cause of Snap slowness; whether #138864 / #6521935 exist in Snap (Fuse MCP 401, no probe).

## Re-fire 06:01:08Z 29 Oct
Checked with the ilg003 record (one reply for all three hosts, thread 1793253749.135479): vendor P3, same plateau. ilg001 alert value 6611.7ms. Detail in 2026-10-28-snap-adapter-api-latency-ilg003.md.
