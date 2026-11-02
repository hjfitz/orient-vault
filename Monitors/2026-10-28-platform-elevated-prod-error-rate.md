---
tags: [datadog-triage]
date: 2026-10-28
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: snap-adapter
business_id: DOCKBAY
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793189209323259"
opened_at: "2026-10-28T12:05:37Z"
resolved_at: "2026-10-28T16:58:00Z"
minutes_spent: 10
severity_assessed: P3
flapping: true
outcome: real_minor
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: resolved
---
# 6 DOCKBAY sales-order creates hit snap_adapter slot_timeout

## Fired
More than 2 domain:fuse error logs in 2m; all 6 were snap_adapter `slot_timeout` (30s wait for a concurrency slot, transient:true) for DOCKBAY, 12:05:30-12:05:38Z, each returning 503.

## Investigation
- Log aggregation 11:55-12:20Z: only service snap_adapter, only DOCKBAY, 6 errors, none after 12:08. DOCKBAY had 17 successful creates in the same window.
- Monitor fired 09:01, 10:10, 12:05 today (events 19 in 24h). 09:01 burst was 15 slot timeouts, all SPORTLUX.
- snap.poll.request.latency.avg by snap_host 09:00-12:30Z: ilg001/003/004 4-13s, ilg002/005 under 1s.
- Maintenance record 2026-10-19: DB2 (ilg002) 10:00Z only; not applicable.
## Not established
DOCKBAY's Snap host (Fuse MCP 401, no probe); whether the 6 orders were redelivered successfully.

## Outcome
Real minor, P3. Likely knock-on of Snap latency on ilg001/003/004 but unproven. Reply posted, fuse-support pinged.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793189209323259

## Firing 4 at 16:51Z (re-triage, real_minor P3)
Thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793206363217339
### Fired
More than 2 domain:fuse error logs in 2m. Fourth firing today (09:01, 10:10, 12:05, 16:51Z).

### Investigation
- Monitor-equivalent count 16:20-17:10Z (per minute, per service): snap_adapter only; 1 at 16:46 (PURDYFIGG sales_order slot_timeout), 5 at 16:51 (DOCKBAY master_data slot_timeout, 16:51:17-25Z, transient:true).
- Monitor query excludes snap_adapter transient:false, so ESCENTRIC #138864 schema_validation (11 errors since 16:00Z) does not count toward it.
- DOCKBAY master_data creates/min: 22 (16:50), 34 (16:51), 71 (16:52); 127 created since 16:50Z. PURDYFIGG sales_order creates/min: 118 (16:41), 107 (16:46), 60 (16:50); 286 since 16:40Z.
- Failed recordIds TOWLB-DES-LG-PCHBCH and TEATWL-MD-WTSHELL show "Entity created in SNAP" at 16:52Z (redelivered).
- Errors since 16:00Z by business/mode: ESCENTRIC schema_validation 11, DOCKBAY slot_timeout 5, PURDYFIGG slot_timeout 2.

### Not established
Whether the DOCKBAY load keeps ramping; the other 3 failed recordIds; current Snap latency/Pub/Sub backlog (metrics queries failed); DOCKBAY's Snap host (Fuse MCP 401, no probe).

### Outcome
Real minor, P3. Slot cap exceeded by concurrent DOCKBAY master_data and PURDYFIGG sales_order bursts while Snap is slow; transient, redelivered. Reply posted.


## Firing 5 at 17:21Z (re-triage, real_minor P3)
Thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793208164798889
### Fired
More than 2 domain:fuse error logs in 2m. Fifth firing today; largest burst so far.

### Investigation
- Monitor query, logs 17:10-17:30Z by minute/service/business/failureMode/recordType: only snap_adapter, PURDYFIGG, sales_order, slot_timeout, transient:true. 4 at 17:20, 57 at 17:21, 12 at 17:22 (last 17:22:13Z). No other Fuse service errored 17:15-17:23Z. Earlier firings today were 5-15 errors.
- PURDYFIGG sales_order creates in bursts: 94 (17:01), 124 (17:10), 100 (17:16); 53 at 17:22 and 32 at 17:23 after the burst.
- From 17:19Z: 62 distinct recordIds failed, 87 distinct recordIds "Entity created in SNAP" (overlap not computed here).
- snap.poll.request.latency.avg 17:00-17:07Z: ilg001 5-13s, ilg003 6-14s, ilg004 5-11s late; ilg002 and ilg005 rose to 3-5s at the end.

### Not established
PURDYFIGG's Snap host (Fuse MCP 401); whether all 62 failed records were recreated (left to the 334832256 triage); slot cap vs Snap latency as the cause.

### Outcome
Real minor, P3. Reply posted (broadcast). Severity moves up if 334832256 finds records not recreated.
