---
tags: [datadog-triage]
date: 2026-10-28
monitor: "[FUSE][Snap Adapter] API latency threshold breached"
service: snap-adapter
business_id:
snap_instance: ilg003
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793110049123889?thread_ts=1793110049.123889&cid=C099WKQTE8G"
opened_at: "2026-10-28T10:31:08Z"
severity_assessed: P3
flapping: true
outcome: vendor
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: open
---
# ilg003 Snap API latency >5s, continuing slowdown (ilg001/ilg004 same)

## Fired
Monitor 179927768 (`avg(last_20m):avg:snap.poll.request.latency.avg{environment:prod} by {snap_host} > 5000`) in Alert for ilg003 from 2026-10-28T10:31:08Z. No Datadog post was made: downtimes on ilg001/ilg003/ilg004 (events 2026-10-27 14:38Z/15:32Z/19:28Z) mute it until 14:38Z, 15:32Z and 19:28Z today. No thread existed, so the reply went into yesterday's ilg003 thread with broadcast.

## Investigation
- 20-min avg latency 09:20-12:20Z: ilg003 4.5-9.9s, ilg001 4.3-9.7s, ilg004 4.3-8.4s, moving together; ilg002 0.2-1.5s, ilg005 0.25-0.77s. Possible shared Snap-side cause; the three slow hosts are all already on 2.20.26076 (correlation only).
- ilg003 4h averages <0.85s until the 27 Oct 08:00Z bucket, 7.3s then, 9.9s in the 08:00-12:00Z bucket today.
- `snap.poll.request` equals `.success` on all hosts in every hourly bucket 09:20-12:20Z.
- Oldest unacked age on snap_adapter create_record_* subs: max 37s (sales_order), 0 elsewhere. `snap.slot_queue_depth` ilg003 0; max 12.3 ilg005, 12 ilg001.
- snap_adapter `Entity creation in SNAP failed` last 6h: 29 (21 transient, 8 non-transient, 10:35-10:59Z mostly); causes of the 8 not examined.
- No maintenance window covers it (DB2 is 10:00Z today, ilg002 stayed <1.5s). Continuation of Monitors/2026-10-27-snap-adapter-api-latency-ilg001-ilg003-ilg004.md.
- Not established: why Snap is slow; direct Snap probe (Fuse MCP 401); the 8 non-transient failures' errors; whether the single-DB-update timing is causal.

## Outcome
Vendor P3: sustained Snap-side slowness, no failures or backlog. Monitor is chronic and its 5s threshold sits inside these hosts' current normal; retune or a Snap ticket is Harry's call (not filed).

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793110049123889?thread_ts=1793110049.123889&cid=C099WKQTE8G (reply ts 1793189318.213169)

## Re-fire 13:10:08Z (Warn)
- Latency 20-min avg 09:20-13:20Z: ilg003 4.5-9.7s (last buckets 5.5s, 4.8s), ilg001/ilg004 same shape, ilg002/005 0.2-1.8s. Unchanged from the earlier range.
- `snap.poll.request` equals `.success` on all hosts hourly; ilg003 `snap.slot_queue_depth` 0 over 90 min.
- New, unrelated to latency: PURDYFIGG sales order `#6521935` fails creation every 5 min from 12:50Z (5 failures to 13:10Z), `schema_validation`, non-transient, `ShipAddress.0.Name` too big; no created log for it. @fuse-support pinged in the reply. No slot_timeout since DOCKBAY 12:05Z.
- Verdict unchanged: vendor P3. Reply (no broadcast): ts 1793193126.559519 in the same thread.
- Not established: why Snap is slow; direct Snap probe (Fuse MCP 401); why the logged address name is empty yet fails the length check.

## Re-fire 14:11:08Z (Warn)
- Latency: ilg003 20-min avg 8.5s at 11:20Z, 9.7s peak, 2.5s at 13:20Z; 5-min buckets 13:30-14:10Z 1.5-3.4s. ilg001/ilg004 same curve; ilg002/005 ~0.2s. Easing, now under the 5s alert line.
- `snap.poll.request` equals `.success` on all hosts 12:00-14:12Z (ilg003 187/194/42); ilg003 `snap.slot_queue_depth` 0 since 13:30Z.
- All 14 `Entity creation in SNAP failed` logs 13:10-14:10Z are PURDYFIGG; 0 for other businesses.
- PURDYFIGG `#6521935` still failing: every 5 min since 12:50Z, latest 14:10:08Z, `schema_validation` non-transient, `ShipAddress.0.Name` over 50 chars. No success log found for it in 6h. @fuse-support pinged again.
- Verdict unchanged: vendor P3 for latency. Reply (no broadcast): ts 1793196813.987279 in the same thread.
- Not established: why Snap is slow; direct Snap probe (Fuse MCP 401); why logged name is empty yet fails length check; monitor Warn threshold value and why Warn fired at 14:11Z with 20-min avg ~2.5s.

## Re-fire 16:22Z (Alert, fresh thread)
- Thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793204638854189 (Datadog post 16:23:58Z, reply ts 1793205326.724429, broadcast, @fuse-support pinged). Downtimes had expired.
- Monitor value (alert text): ilg003 5700.9ms, ilg001 5056.3ms, 20m avg. Re-rose from ~2.5s at 13:20Z. Datadog metric queries timed out all run, so no per-host series or backlog metric.
- `Entity creation in SNAP failed` last 3h: PURDYFIGG 29, ESCENTRIC 27, none else. All data errors, not latency.
- New: ESCENTRIC `#138864` fails every 5 min from ~14:15Z, latest 16:30:03Z, `schema_validation` non-transient, `ShipAddress.0.Line1` >50 chars.
- PURDYFIGG `#6521935`: 26 failures 13:35-15:45:05Z, none since.
- One slot_timeout: PURDYFIGG `#6611181` 16:15:53Z (create 503). Co-timed with Pub/Sub ack-deadline Warn on create_record_sales_order (118s, 16:26Z); link not tested.
- Verdict unchanged: vendor P3.
- Not established: why Snap is slow; current per-host latency series; unacked backlog; direct Snap probe (Fuse MCP 401); why #6521935 stopped.

## Re-fire 17:57:08Z (Alert to Warn, ilg001/003/004; checked ~18:00Z)
- Monitor Warn = avg(20m) > 2000ms, Alert > 5000ms. Values in alert text: ilg001 4535ms, ilg003 4758ms; stepped down from Alert but ~2x Warn, not recovered.
- 10-min latency (s) 17:00-17:50Z: ilg001 4.5/7.3/6.2/6.8/4.3/4.9; ilg003 2.4/7.5/6.7/8.4/4.1/5.7; ilg004 4.4/6.1/6.3/6.6/4.4/5.5; ilg002 0.1-1.1, ilg005 0.3-1.5. Last 5-min bucket: ilg001 4.2, ilg003 5.3, ilg004 5.2.
- snap.poll.request = .success on all hosts 17:00-17:59Z. Since 17:25Z: 0 `Entity creation in SNAP failed`, 0 error-status snap_adapter logs.
- ESCENTRIC #138864 still not created (last attempt 17:10:03Z, nothing after). PURDYFIGG #6521935: no logs since 17:00Z, no created log. PURDYFIGG creates continue (17:55:25Z).
- One reply for all three hosts in ilg003's Alert thread (ts 1793210321.982649), reply ts 1793210405.995859, no broadcast. Verdict unchanged: vendor P3.
- Not established: why Snap is slow; whether #6521935 is in Snap; host probe (Fuse MCP 401).

## Re-fire 23:31Z (ilg003 Alert, group muted; checked ~23:35Z)
- 10-min avg latency (s) 22:00-23:30Z (last partial): ilg001 2.7/3.4/4.6/3.1/3.5/3.5/3.3/3.2/4.6/5.4; ilg003 2.8/3.5/4.5/3.1/3.3/4.2/3.1/2.9/5.9/6.6; ilg004 2.9/3.8/5.1/3.5/3.4/4.0/3.1/3.5/4.2/5.0. ilg002 0.10-0.34, ilg005 0.16-0.27. Same plateau flapping at the 5s line, peaks inside the earlier range.
- snap.poll.request = .success on all hosts every bucket 22:00-23:33Z. 0 error/warn snap_adapter logs and 0 `Entity creation in SNAP failed` since 21:55Z. Creates continue: 68 (22:00h), 19 (23:00h to 23:35Z).
- Verdict unchanged: vendor P3. Reply (no broadcast) in the ilg001 Alert thread 1793217756.199449, ts 1793230399.793669.
- Not established: why Snap is slow; direct Snap probe (Fuse MCP 401); ESCENTRIC #138864 / PURDYFIGG #6521935 state in Snap (not re-checked).

## Re-fire 06:01:08Z 29 Oct (ilg001, ilg003, ilg004 Alert; checked ~06:05Z)
- Thread: Datadog post 06:02:29Z ts 1793253749.135479 (ilg001 group, value 6611.7ms). One reply for all three hosts, no broadcast, reply ts 1793253853.699789.
- 5-min avg latency (s) 05:00-06:00Z (06:00 partial, 06:03Z): ilg001 5.3/2.1/2.9/2.8/2.9/2.3/2.7/3.1/3.1/2.7/3.9/3.5/11.7; ilg003 6.5/2.3/3.1/3.0/3.5/2.3/2.5/3.6/3.3/2.9/5.2/3.6/11.5; ilg004 4.7/2.5/3.0/3.0/3.2/2.9/3.1/3.6/3.6/3.3/3.7/3.9/8.3. ilg002 0.08-0.43, ilg005 0.10-0.41. Spike is the 06:00 bucket (slowest single polls ~16.6s ilg001/003, 11.1s ilg004); 04:00-05:55 mostly 2-4s.
- snap.poll.request = .success on all hosts 04:00-06:10Z. 0 `Entity creation in SNAP failed`, 0 error/warn snap_adapter logs, 0 slot_timeout since 23:35Z. Oldest unacked 0 on all snap_adapter prod create_record subs; slot_queue_depth 0.
- Creates per hour: 29 (23Z), 19, 3, 14, 3, 4, 4 (05Z), 1 (06Z). Not ramping yet; latency not load-driven.
- No log mentions of ESCENTRIC #138864 / PURDYFIGG #6521935 since 17:10Z yesterday (id search returned nothing).
- Verdict: vendor P3, same plateau, no change of shape. Not established: why Snap is slow / the 06:00 spike; behaviour under UK daytime load; whether the two orders exist in Snap; host probe (Fuse MCP 401).

## Re-fire 09:07Z 29 Oct (ilg003 group, Alert; checked ~09:10Z): first fresh measurement since 07:10Z
- 10-min avg latency (s) 07:00-09:00Z (09:00 partial): ilg001 4.6/5.2/6.1/6.9/4.4/3.2/3.4/3.1/3.6/2.5/6.5/4.2/5.2; ilg003 4.3/4.3/4.9/7.9/4.1/3.0/3.4/3.2/4.1/2.6/5.1/4.2/5.2; ilg004 6.0/4.4/6.0/6.1/4.1/3.3/3.6/3.7/4.1/2.9/5.3/4.4/5.7; ilg002 0.1-0.6, ilg005 0.2-0.6. Same plateau (peak 7.9s, inside the earlier 7.3s-12s range); ilg002/005 unaffected.
- `snap.poll.request` equals `.success` on all five hosts in every 10-min bucket 07:00-09:09Z.
- Creates (`Entity created in SNAP`) per hour: 11 (06Z), 334 (07Z), 173 (08Z), 27 (09Z to 09:09Z). Volume ramped about 30x by 07Z, and latency did not move with it (06:00-07:10Z means were already 2.8-7.3s).
- snap_adapter error logs since 06:50Z: 91, all "Timed out after 30000ms waiting for a concurrency slot", all SPORTLUX, 07:06:26-07:12:06Z. Zero error/warn logs 07:13Z-09:10Z. 0 `Entity creation in SNAP failed` after 07:12:06Z. SPORTLUX has 217 created logs since 07:10Z.
- Oldest unacked age on snap_adapter prod create_record subs: max 12.2s sales_order (07:00Z bucket), 0-1.8s after; purchase_order/master_data/rga/work_order 0. `snap.slot_queue_depth` peaked 20.3 (ilg004, 07:10Z bucket) and 16.2 (ilg005, 08:40Z bucket), 0 otherwise.
- Verdict: vendor P3, same plateau, no change of shape. Not established: why Snap is slow; whether the SPORTLUX burst records were all created (the 07:10Z note said so; not re-counted per record); which host SPORTLUX is on; direct Snap probe (Fuse MCP 401).

## Re-fire 14:49Z 29 Oct (ilg004 14:49:08Z, ilg001 14:51:08Z, Alert; checked ~15:00Z): first fresh measurement since 09:10Z, covers both groups
- 30-min avg latency (s) 09:00-14:30Z (12 buckets): ilg001 4.5/5.0/5.0/4.8/5.6/6.8/8.9/7.0/6.2/8.1/6.7/5.8; ilg003 3.8/5.3/4.7/5.6/6.1/6.1/9.7/8.7/8.1/8.2/8.7/6.5; ilg004 4.1/5.3/5.2/5.6/6.1/5.5/8.6/7.5/6.5/7.0/7.6/5.7; ilg002 0.2-1.1, ilg005 0.3-0.8.
- 10-min avg 14:00-14:50Z: ilg003 10.6/9.6/5.7/5.9/5.0/8.7; ilg004 8.1/8.3/6.4/4.9/4.7/7.3; ilg001 6.6/8.1/5.4/5.3/4.8/7.5; ilg002 0.2-0.7, ilg005 0.25-1.1. Higher than the morning's 10-min peak (7.9s) at 12:00-14:10Z, but yesterday's 20-min avg peaked 9.9s and 5-min 11.7s. ilg002/ilg005 unaffected. Flapping, not a sustained rise.
- snap.poll.request = .success on all five hosts in every 30-min bucket 09:00-14:59Z except ilg005 10:00-10:30Z (340 vs 130, the DB5 window).
- snap_adapter / snap-polling-service error+warn logs 10:30-15:00Z: 1 snap_adapter error (MANUCURIST purchase_order WHSL16074^16152, 11:17:19Z, 400, snap_api_error, non-transient, held in replay-service), plus snap-polling-service warns "Consignment StU not found" (4916; also 1.0-2.1k/h through yesterday 12:00Z) and "Stock movement dropped" (540). 0 slot_timeout, 0 404s, no ilg005 recurrence.
- `Entity created in SNAP` per hour: 81 (09Z), 72, 94, 80, 72, 61 (14Z).
- Oldest unacked, prod create_record_sales_order sub, 30-min max (s): 0/8/40/0/4/3/59/34/33/64/93/33; other prod create_record subs 0 (purchase_order 7 once).
- 20 held DB5-window sales_orders (STUBBLE SC17418701-704/706/707/709/711/713/715 + SCPR3581, WILDSMITH SO-29414..29419, PHLUR SO399422/425/428): no `Entity created in SNAP` and no log of any kind for any of the 20 recordIds after the last failure at 10:20:21Z. Other STUBBLE/WILDSMITH/PHLUR orders were created in the same period. Still held in replay-service as far as logs show.
- ESCENTRIC #138864 (last log 28 Oct 17:10:03Z) and PURDYFIGG #6521935 (last log 28 Oct 15:45:05Z): no created log in either.
- Verdict: vendor P3 for latency, no change of shape. @fuse-support ping owed for the held records.
- Not established: why Snap is slow; whether held records exist in Snap by another route (Fuse MCP 401, no probe); cause of the MANUCURIST 400; whether the stock-movement/StU warns relate to anything.

## Re-fire 17:43-19:10Z 29 Oct (ilg001, ilg004 Warn, ilg003 Warn; checked ~20:23Z): fresh status, covers all three groups
- Monitor state at 20:22Z (monitors API, group states): ilg001 Warn (last triggered 17:43:08Z), ilg004 Warn (17:44:08Z), ilg003 Warn (19:10:08Z), ilg002 OK (16:13:08Z), ilg005 OK (16:12:08Z). None at Alert.
- Latency, 30-min avg (s), live hosts, 16:30 / 17:00 / 17:30 / 18:00 / 18:30 / 19:00 / 19:30 / 20:00Z: ilg001 9.3 / 5.1 / 4.3 / 3.2 / 2.4 / 3.6 / 3.1 / 3.8; ilg003 9.6 / 4.9 / 4.3 / 3.6 / 2.5 / 2.9 / 2.7 / 3.3; ilg004 9.7 / 5.0 / 4.4 / 3.2 / 2.4 / 3.1 / 2.7 / 3.5; ilg002 1.5 / 0.3 / 0.2 / 0.1 / 0.1 / 0.1 / 0.1 / 0.2; ilg005 1.5 / 0.3 / 0.3 / 0.2 / 0.1 / 0.2 / 0.2 / 0.2. Last hour, 10-min avg 19:20-20:20Z: ilg001/003/004 1.9-5.0s (peak 20:10Z: 5.0 / 4.4 / 4.3), ilg002/005 0.1-0.3s. Max single poll per 30-min since 17:00Z: ilg001/003/004 5.6-22.3s, ilg002/005 0.3-6.8s.
- No spike recurrence on ilg002/005 after 16:38Z; the 16:36Z all-host spike did not recur. No latency data gap.
- `snap.poll.request` equals `.success` on all five live hosts in every 30-min bucket 16:30-20:30Z: no failed polls.
- snap_adapter and snap-polling-service error/warn since 16:38Z: snap-polling-service warns only "Consignment StU not found" (414/1306/783/1449/594 per hour) and "Stock movement dropped" (52-120 per hour), the known ones. 0 slot_timeout after 16:37:20Z (last one 16:37:20.852Z). snap_adapter `Entity creation in SNAP failed` 62 since 16:38Z, all schema_validation, transient:false, three records: PURDYFIGG #6617071 (ShipAddress.0.Name over 50 chars, 16:40-18:50:08Z), ESCENTRICPL #139010 (ShipAddress.0.Line1 over 50, from 18:00Z, still every 5 min at 20:20Z), SAIRA #37526 (ShipAddress.0.Line1 over 50, from 20:05Z, still failing 20:20Z). None has an "Entity created"/"already exists" log (28 Oct onward).
- The 60 distinct PURDYFIGG recordIds with slot_timeout 16:35-16:37Z (SQL join on recordId): 60 of 60 have "Entity created in SNAP" or "already exists" from 16:38:15Z. (The earlier 61 count was not reproduced; 71 slot_timeout errors, 60 distinct recordIds, 16:30-now.)
- PURDYFIGG reap: "Bulk reap completed" published every 5 min still; peak 1832 (17:xx), 1593-1819 in 18:xx, then falling 1437 (19:05Z) to 244 (20:20Z), skipped 0, errored 0. snap_adapter PURDYFIGG created+already-exists logs: 1-2 per minute-bucket 19:50-20:10Z; "Entity created" per hour 447 (16:30+), 722, 52, 19, 5 (20:00-20:10Z).
- Held records, searched @recordId across all prod services 10:00Z-now: 20 DB5-window sales_orders, ESCENTRIC #138864, PURDYFIGG #6521935 and MANUCURIST WHSL16074^16152: no log of any kind since 15:00Z (last logs 10:20:21Z and 11:17:20Z, all "Record marked failed"/"Failure stored"); none created, none replayed. replay_service has no activity naming them since 15:00Z.
- Not established: why Snap is slow; direct Snap probe (Fuse MCP 401); whether the held records are still stored in replay-service (not queried); why #6617071 stopped logging at 18:50:08Z (not created); the ShipAddress field values (logged empty); why the reap set is shrinking.

## Re-fire 2 Nov: ilg004 Warn 05:34:08Z, ilg001 08:57:08Z, ilg003 08:58:08Z (checked ~09:30Z): first fresh measurement since 29 Oct 20:23Z, covers all three groups
- Channel: no latency alert post or reply in #bifrost-notifications after 30 Oct 20:11Z (ilg004 Recovered). On 30 Oct 12:16-12:18Z Nylah Klasson muted ilg001/003/004 ("known issue"). Monitor now: ilg001 silenced until 2026-11-05T17:56Z (the other two groups unsilenced); ilg001/003/004 Warn, none Alert; ilg002/005 not in alert/warn. Reply goes in the 29 Oct thread 1793253749.135479 (no newer latency thread exists).
- Latency avg per 6h bucket (s), 29 Oct 18:00Z to 2 Nov 06:00Z (partial, to ~09:30Z), ilg001: 2.9/2.6/3.8/4.7/3.3/2.9/2.5/2.9/2.8/2.6/2.6/2.6/2.7/2.7/3.7; ilg003 2.9/2.7/3.6/4.6/3.0/2.8/2.6/2.8/2.5/2.6/2.4/2.6/2.5/2.7/3.7; ilg004 same shape (2.4-4.7); ilg002 0.12-0.36, ilg005 0.10-0.40 (all buckets under 1s). Peak was 30 Oct 12:00Z bucket (4.6-4.7s); weekend 2.4-3.0s. Last-week 20-min averages reached 9.9s, so no worse; the plateau is unchanged and 2-5s.
- 10-min avg 06:30-09:20Z (09:20 partial) ilg003: 2.0/2.7/2.5/2.8/2.6/2.3/5.2/3.7/3.0/4.6/4.1/4.0/4.2/5.4/4.2/3.7/4.7/2.8; ilg001 and ilg004 same band (2.0-5.3); ilg002 0.12-1.09, ilg005 0.16-0.99.
- Polls: `snap.poll.request` vs `.success` per 6h bucket equal on all five hosts except ilg004 2695/2700, ilg001 1078/1080, ilg003 1092/1094 (30 Oct 18:00-24:00Z bucket); nothing failing now.
- snap_adapter / snap-polling-service error+warn last 12h: snap-polling-service 8478, all "Consignment StU not found" (sampled; top-message aggregate returned empty, so the split of the 8478 is not established); snap_adapter 22: 21 SPORTLUX `slot_timeout` 08:15-08:16Z (19 distinct records, all later created, 182 SPORTLUX created since 08:10Z) and 1 DOCKBAY schema_validation 09:21Z.
- slot_timeout per day: 29 Oct 288 (whole day; the hourly series from 20:23Z shows none until 30 Oct 10:00Z), 30 Oct 331 (10:00-16:00Z), 31 Oct 0, 1 Nov 0, 2 Nov 21. Since 29 Oct 20:23Z by business: SPORTLUX 197, ICONICL 114, DOCKBAY 26, PURDYFIGG 15. The 2 Nov ones are the SPORTLUX burst 08:15Z, co-timed with Platform error-rate trigger 08:16Z and ack-deadline Warn 08:18Z, recovered 08:29Z). ICONICL 103 failed ids and PURDYFIGG 15: all later created. ICONICL also had 103 `snap_api_error` (OrderType "No Check Code Found") on 30 Oct 12:34Z, all later created.
- PURDYFIGG reap: "Bulk reap completed" every 5 min. Published per run: 69 (29 Oct 21:00Z), 8 (30 Oct 06:00Z), 1638 (30 Oct 18:00Z), 80-120 (31 Oct), 484 (1 Nov 00:00Z), 227 (2 Nov 00:00Z), 174 (08:50Z) to 193 (09:25Z). Not a large growing set; slow rise this morning.
- Held records (searched @recordId across prod, since 29 Oct 20:23Z; Fuse MCP replay tools unavailable, 401):
  - Created since: STUBBLE SC17418701-704/707/709/711/713/715 on 30 Oct 09:51-09:52Z (consistent with a replay, not confirmed), SCPR3581 on 2 Nov 07:04Z, all six WILDSMITH SO-29414..29419 on 30 Oct 15:03-15:15Z.
  - Not created, no log: STUBBLE SC17418706; PHLUR SO399422/425/428; PURDYFIGG #6521935 and #6617071; ESCENTRIC #138864; MANUCURIST WHSL16074^16152. ESCENTRICPL #139010 last failed 29 Oct 20:55Z (7 attempts), SAIRA #37526 last failed 30 Oct 00:45Z (33 attempts), neither created; SAIRA has a dedupe "Dedupe gate held on permanent failure" log.
  - replay_service logged "Failure stored" for the schema_validation failures.
- New non-transient failures since 29 Oct 20:23Z, one attempt each, not created: DOCKBAY UK-911119 (City >30, 30 Oct 00:05Z) and "WAIT12005-7-DISPATCH / PO573058" (CustomerRef >20, 2 Nov 09:21Z; trips Dock and Bay D9 Alert 09:22Z); ESCENTRIC #139353 (FirstName >30, 1 Nov 11:40Z); ESCENTRICPL #139159 (City >30, 30 Oct 18:45Z); PHLUR SO400621 (Line1, 30 Oct 15:05Z), SO400737 (City, 30 Oct 17:07Z); BFA00112 (Invalid Unit EA, 30 Oct 08:26Z); DISCOVERED 143764, 143783 (Email MANDATORY on the latter; 30 Oct 15:54-16:02Z); PURDYFIGG #6603947 cancelled_in_wms. ESCENTRIC #139088 and PURDYFIGG #6629289 were created after failing.
- Monitors in Alert/Warn in prod: latency (Warn x3). Alert but no Slack recipients: Dock and Bay go-live D2/D3/D7/D8 (go-live watch, by design) and D9 (SNAP rejections, 09:22Z, the CustomerRef failure), CCP request-volume floor. Weekend/overnight posts in the channel (29 Oct 22:00Z-2 Nov): Platform error-rate (many, to 08:16Z today), Pub/Sub ack-deadline on snap_adapter create_record_sales_order (30 Oct, 2 Nov 08:18-08:29Z), create_data_failure spike 30 Oct 12:39Z, SFTP canonical validation 30 Oct 18:08Z, SFTP file upload failure 30 Oct 11:43Z, Tracking push 5xx 1 Nov 01:01-01:08Z, Dedupe silent publish drop flapping 1 Nov 19:11-21:01Z (10-min net values -39 to +25, cause not established), Shopify confirmation delivery 2 Nov 07:50-08:05Z. None triaged here except as they touch the Snap create path above.
- Verdict: vendor P3 for latency, unchanged; records held (new and old) need support. Not established: why Snap is slow; direct Snap probe (Fuse MCP 401); whether held records are still stored in replay-service; whether the 20 STUBBLE/WILDSMITH creates were a replay; SC17418706 and the 3 PHLUR orders in Snap by another route; the causes of the weekend monitor posts other than the above.

## Re-fire 2 Nov: ilg001 Alert 11:03:08Z, ilg004 11:06:08Z, ilg003 11:06:08Z (checked ~11:09Z): all three at Alert, covers all three groups
- Thread: 29 Oct thread 1793253749.135479 (last full measurement reply ts 1793611777.350539, then one-line acks for the Warn and the ilg001 Alert). Not posted by this run (draft returned to the watcher).
- 10-min avg latency (s) 09:00-11:00Z (last bucket 11:00-11:10 partial): ilg001 4.0/5.3/2.7/5.3/6.6/1.7/4.3/5.9/4.8/4.8/4.2/4.5/11.1; ilg003 3.7/4.7/3.2/5.2/6.2/2.7/3.6/2.9/4.6/4.1/5.5/3.7/11.3; ilg004 3.5/4.6/2.9/4.8/6.5/2.2/3.5/4.6/4.3/4.0/3.9/4.4/9.8; ilg002 0.14-0.41 then 2.0; ilg005 0.12-0.60 then 2.9. So 09:00-10:50Z is the known 2-6.6s plateau; the change is 11:00Z onward.
- 1-min avg 10:56-11:06Z: slow hosts 1.7-4.8s to 10:59, then 10-12s at 11:00-11:01, 6-8s, then 11.7-13.3s, peak 14.4-16.7s (ilg001 14.4, ilg003 16.7, ilg004 15.2), 5.7-6.4s at 11:06. ilg002 and ilg005 also rose for about 3 min (3.2-4.6s and 4.2-5.7s peak) and were back at 0.5/0.8s by 11:06. Max single poll 22.0s ilg001 (11:00 bucket), 18.8s ilg004, 16.7s ilg003; ilg005 10.4s, ilg002 5.6s. 20-min avg (rollup, partial) ilg001 10.6, ilg003 10.0, ilg004 9.1, ilg002 1.8, ilg005 2.6. Slightly above last week's 9.9s 20-min / 10.6s 10-min peaks for ilg001; 2-min peak 16.7s vs 14s last week. Earlier all-host spikes: 29 Oct 06:00Z and 16:36Z, each did not recur.
- `snap.poll.request` equals `.success` on all five hosts in every 30-min bucket 09:00-11:08Z (ilg001 162/123/344/300/154, ilg004 293/333/336/280/60, ilg003 90/145/138/125/24, ilg002 45x4/12, ilg005 1827/877/397/1152/385). No failed polls.
- snap_adapter error/warn since 09:30Z: 1 error, ESCENTRIC sales_order 15309 `Entity creation in SNAP failed` 10:57:25Z, snap_api_error "City - MANDATORY", retryable false, one attempt, no created log by 11:08Z. 0 slot_timeout. snap-polling-service warns: "Consignment StU not found" 1959, "Stock movement dropped" 196 (known ones). 0 404s, 0 schema_validation.
- Creates since 09:30Z (`Entity created in SNAP`): PURDYFIGG 71, STUBBLE 33, EPARFUM 12, ESCENTRIC 10, SAIRA 8, WILDSMITH 6, DOCKBAY 2, ESCENTRICPL 2, LISAUK 2, PHLUR 1 (about 147 in 1h40, no bulk wave; SPORTLUX, ICONICL 0).
- Oldest unacked on prod snap_adapter create_record subs, 20-min max 09:00-11:08Z: 0.6s (sales_order), 0 others. `snap.slot_queue_depth` max 8 (ilg005, 10:20Z bucket), else 0-1.5.
- Held records (@recordId, prod, since 29 Oct 20:00Z): no log of any kind for #6521935, #138864, SC17418706, SO399422/425/428, WHSL16074^16152. Not created. Fuse MCP unavailable (401).
- Maintenance: Maintenance/ has no record covering 2 Nov (latest is the 29/31 Oct firewall one, ended 31 Oct 07:00Z, unpinned 09:26Z today).
- Verdict: P3, same plateau underneath plus a new sharp burst from 11:00Z (about 6 min, peaks above last week's, briefly touching ilg002/ilg005) with no failed polls, no backlog, no timeouts. Burst cause not established. @fuse-support ping owed: held records plus new ESCENTRIC 15309.
- Not established: why Snap is slow; cause of the 11:00-11:06Z burst, including why ilg002/005 rose too (Snap-wide vs Fuse-side path); whether burst is over (last point 11:06Z easing, data may lag); direct Snap probe (Fuse MCP 401); whether held records exist in Snap or replay-service; whether a newer Snap notice exists outside Maintenance/.

## Re-fire 2 Nov 18:27Z (ilg001/ilg004 Alert, ilg003 Warn 18:47Z; checked ~18:58Z)
- Window 16:50-18:55Z. 10-min avg latency (s), ilg001 10.7/8.2/2.8/5.9/5.6/10.3/2.3/3.6/3.5/6.3/9.8/3.9/5.6; ilg003 8.3/9.2/4.2/4.9/5.8/8.8/2.0/2.2/3.5/5.7/6.8/3.5/2.2; ilg004 9.1/6.7/3.4/5.3/5.4/8.2/2.5/2.4/3.3/6.3/7.5/3.2/2.6. ilg002 0.09-0.99, ilg005 0.13-1.47. Not worse than the 16:15-16:46Z peak: 5-min max since 16:50 ilg003 13.2s (17:05), ilg001 12.1s (17:45), ilg004 9.3s (17:45); 1-min max ilg001 18.3s (17:06), ilg003 16.2s (17:06), ilg004 15.3s (16:50). ilg002/005 5-min max 1.9s/2.0s.
- `snap.poll.request` equals `.success` on all five hosts in every 5-min bucket 16:50-18:58Z. snap-polling-service: 0 error logs, 0 snap_api_error/404; 2305 warns, all "Consignment StU not found" (2057) or "Stock movement dropped" (248). snap_adapter warn: 0.
- New slot_timeout wave 17:00:47-17:01:36Z: 58 errors, 43 PURDYFIGG records, all transient, max deliveryAttempt 2. All 43 created by 17:02:59Z (first error to created: median 111s, max 132s). No other slot_timeout 16:52-18:57Z.
- Oldest unacked, snap_adapter prod create_record_sales_order: peak 133s at 17:04Z (vs 248s earlier, 300s deadline per iac); other prod create_record subs 0.
- PURDYFIGG reap total per 5 min: 1117 (16:50), 1264 (17:00), 1543 (17:25), peak 1683 (18:30), then 1641/1597/1544/1474 (18:35-18:50). Errored 0 throughout. Falling since 18:30.
- ilg005 `snap.slot_queue_depth` 10-min max: 20.5 (16:50), 22 (17:00), 12.3 (17:50), 5.4 (18:00), 0 (18:50); 0-1.5 at 2-min points 18:30-18:50.
- Four first-attempt rejections, not slot: ESCENTRIC #139527 (16:55, Name Invalid Text) and #139531 (17:00, LastName MANDATORY) snap_api_error; DOCKBAY UK-912102 (17:01) and SAIRA #37747 (17:40) schema_validation City over 30. Whether they were later created was not established (id search returned no logs).
- No maintenance record covers 2 Nov (newest Maintenance/ file is 2026-10-28). Email/pin not checked.
- Verdict unchanged: vendor P3, same plateau; one more self-healed PURDYFIGG wave, headroom better than 16:42Z. Reply: draft returned to watcher.
- Not established: why Snap is slow; direct Snap probe (Fuse MCP 401); which host PURDYFIGG uses; the four rejected records' fate; email/pinned maintenance notice.

## Re-fire 3 Nov 06:37:08Z (ilg004 and ilg001 Alert; checked ~06:40Z)
- Thread: 29 Oct thread 1793253749.135479 (C099WKQTE8G), about 15 one-line acks since the 18:58Z full measurement. Draft returned to the watcher, not posted by this run.
- 30-min avg latency 19:00Z 2 Nov to 06:30Z 3 Nov (s), range over the 24 buckets: ilg001 2.0-5.3, ilg003 2.0-4.4, ilg004 2.1-5.2; ilg002 0.11-0.27, ilg005 0.10-0.36. Last bucket (06:00-06:30Z): ilg001 5.33, ilg004 5.24, ilg003 4.36, ilg002 0.25, ilg005 0.36. 10-min buckets 04:40-06:30Z: ilg001 2.3-5.3, ilg004 2.3-5.2, ilg003 2.3-5.0. No step change; ilg002/005 not affected.
- Same overnight window a week earlier (26 Oct 19:00Z to 27 Oct 07:00Z, hourly): ilg001 3.1-5.3s, ilg004 3.1-4.9s, ilg002 0.19-0.34s, ilg005 0.18-0.34s, but ilg003 0.15-0.25s (now 2.0-4.4s).
- Failed polls: `snap.poll.request` minus `.success` is 0 on all five hosts over 19:00Z-now.
- snap_adapter: 0 error or warn logs since 19:00Z (1406 info; 452 "Entity created in SNAP"); 236 errors 16:00Z-now, all earlier. 0 slot_timeout and 0 snap_api_error anywhere in prod since 19:00Z. snap-polling-service: 0 error logs; warns are only "Consignment StU not found" (5494) and "Stock movement dropped" (1400).
- Oldest unacked since 19:00Z, max per snap_adapter prod sub: create_record_sales_order 26s, all others 0. No other prod sub above 31s (bifrost snap_poll_customer).
- PURDYFIGG reap total per hour (sum of @total): 12237 (19Z), 4270, 2316, 1429, 754, 522, 342, 151, 54, 9, 16, 18 (06Z). Errored 0 on the latest samples.
- Other monitor events since 20:00Z: Fuse UI 5xx rate high (P2) Triggered 01:54:55Z, Recovered 02:08:55Z; PF go-live T3 Triggered 21:26Z, Recovered 01:26Z; PF go-live T6 No data 22:11Z to 06:09Z recovered. All OK now. Monitors in Alert/Warn that notify bifrost-notifications now: only 179927768.
- Held records (17 ids): no "Entity created in SNAP" log for any since 27 Oct (7-day query; query validated against #6647100). Latest log per id: replay_service create-failure for #139010, #6521935, 15309, SC17418706, SO399422/428, UK-911960/912082/912102, WHSL16074^16152; collector failure for SO399425; dedupe 204 for #139527 (20:50Z), #139531 (20:55Z), #37747 (22:20Z), #37526 (30 Oct); shopify publish for #6617071 (29 Oct); no log in 14 days for PO573058.
- Maintenance/: no record covers 3 Nov (newest 2026-10-28).
- Verdict: vendor, P3, same plateau, slightly below the evening's 10-min peaks, no errors, no backlog, no failed polls. Flapping across the 5s line continues.
- Not established: why Snap is slow; direct Snap probe (Fuse MCP 401); whether the 17 records exist in Snap or are still in replay-service (no replay-list-failures); Snap maintenance email/pin; whether the monitor's muted_until_ts (2026-11-05) is a scoped mute.
