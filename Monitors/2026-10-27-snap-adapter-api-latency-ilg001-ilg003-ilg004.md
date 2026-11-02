---
tags: [datadog-triage]
date: 2026-10-27
monitor: "[FUSE][Snap Adapter] API latency threshold breached"
service: snap-adapter
business_id:
snap_instance: ilg001, ilg003, ilg004
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793103810018819"
opened_at: "2026-10-27T10:21:08Z"
severity_assessed: P3
flapping: true
outcome: vendor
session_id: 6735df5f-a090-45cd-991d-d7f9cfef0ba8
status: open
---
# ilg001 + ilg003 + ilg004 Snap API latency >5s, sustained (ilg003 newly affected after its DB3 update)

## Fired
Monitor 179927768 (`avg(last_20m):avg:snap.poll.request.latency.avg{environment:prod} by {snap_host} > 5000`, managed-by:terraform) in Alert for ilg001/ilg003 (10:22:08Z) and ilg004 (10:21:08Z). The 11:22Z and 12:22Z posts are re-notifications. I replied in the 12:22–12:23Z re-trigger posts.

## Investigation
- Still elevated at 13:08Z (20-min buckets): ilg001 17.3s, ilg003 10.9s, ilg004 10.2s; ilg002 0.54s, ilg005 0.66s.
- Polls: `snap.poll.request` equal to `.success` on every host over 3h (0 failures).
- Creates over 3h: 317 created, 49 already-exists, 55 errors. 51 were `slot_timeout` (ICONICL 43, DOCKBAY 8), all transient, none exhausted, returned 503 to Pub/Sub. All 35 distinct slot-timeout recordIds have a created/already-exists log in the window. The remaining 4 were DOCKBAY `snap_api_error` data rejections (No Product Found: D27537-4, D27538-5, GAP25313-3; Invalid Text: UK-910557), unrelated to latency.
- Create path, `snap.request.latency.avg` 30-min windows: ilg001 up to 27.6s (max 53.9s), ilg003 up to 31.6s, ilg004 up to 23.7s. `snap.slot_queue_depth` max 24 on ilg001.
- The 13:05Z entity-creation (334832256) and error-rate (180072217) monitors line up with the slot-timeout burst: 25 slot_timeouts in the 13:00Z bucket.
- Timing against the Snap version update 2.20.26076 (Maintenance/2026-10-19-snap-version-update-and-patch.md): ilg003 was 0.2–0.45s to 09:40Z and 18.3s at 09:50Z (DB3 window 09:30Z, est 60 min, now >3h). ilg004 was 92–143ms at 05–07Z on 22 Oct, then 2.4s at 08Z and 4.5s at 09Z (DB4 window 08:30Z). ilg001 has been slow since 19 Oct per earlier triages. Daily avg: ilg001 2.9–6.1s (21–27 Oct), ilg004 3.2–5.6s (22–27 Oct), ilg003 0.17–0.42s (21–26 Oct), then 4.6s today.
- DB2 (ilg002) is scheduled for 28 Oct 10:00Z and DB5 (ilg005, ~2.6k polls/h, the busiest host) for 29 Oct 10:00Z.
- Flapping: 25 prior Monitors/ records for this monitor on 22 Oct alone; 23 of them vendor.
- Already raised with Snap in the INC-42 channel (Matt Shaw, 26 Oct, pre/post-upgrade comparison).
- Not established: whether the update causes the slowdown (timing correlation only); which Snap host ICONICL creates against; a direct Snap probe (Fuse MCP 401, no credentials).

## Outcome
Vendor P3: a sustained Snap-side slowdown, not an outage. No data lost; orders are delayed by retries. Recommend adding ilg003 to the Snap ticket and watching ilg002/ilg005 through their 28/29 Oct windows. Ticket not filed: needs Harry's go-ahead, and it is already being pursued with Snap.

## Update 2026-10-27 13:53Z: ilg001 Alert to Warn
- The ilg001 group transitioned to Warn at 13:51:08Z. No separate Datadog post for this transition in bifrost-notifications (13:48Z onward has only a deploy message), so I replied in the existing ilg001 thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793109224375099
- `snap.poll.request.latency.avg`, 20-min scalar avg to 13:52Z: ilg001 4.06s, ilg003 5.24s, ilg004 5.36s, ilg002 0.34s, ilg005 0.58s. Over 60 min on ilg001 it peaked at 35.1s (12:59Z bucket) and was 2.5s by 13:49Z.
- Create path, `snap.request.latency.avg{snap_host:https_//ilg001liveapi.snapfulfil.net}`: 36.3s avg in the 13:00Z bucket and 13.5s at 13:09Z. No points between 13:10Z and 13:47Z, then 3.35s at 13:47Z.
- Polls over the last 60 min: ilg001 had 568 requests and 569 successes; ilg004 474/476; all other hosts equal. So 0 failures.
- snap_adapter since 13:10Z: 0 `Entity creation in SNAP failed` (the same query matched 26 between 12:00Z and 13:10Z). 29 `Incoming record received` and 29 `Entity created in SNAP`. Nothing is held.
- Verdict unchanged: vendor, P3. Easing on ilg001, but ilg003 and ilg004 are still above the 5s threshold.

## Links
- Slack thread (ilg001, full reply): https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793106678424299
- ilg003 thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793103808047009
- ilg004 thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793103746025289

## Update 2026-10-27 14:10Z: ilg004 and ilg003 Alert to Warn
- ilg004 transitioned to Warn at 14:05:08Z (20-min avg 4.95s per the monitor post). 5-min buckets 13:10-14:05Z ranged 2.4-9.0s, latest 2.4s. Poll request equals success in every bucket (0 failures). 0 `Entity creation in SNAP failed` in snap_adapter since 13:50Z. Verdict unchanged: vendor, P3. Replied in the Datadog post: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793109983122569
- ilg003 transitioned to Warn at 14:06:08Z (20-min avg 4.88s per its monitor post; 5-min buckets 13:10-14:05Z 2.2-9.8s, latest 2.8s; poll request equals success in every bucket). Same 0 failures in snap_adapter since 13:50Z covers both hosts. Verdict unchanged: vendor, P3. Replied in the ilg003 Datadog post: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793110049123889

## Update 2026-10-27 14:37Z: ilg001 and ilg003 relapse to Alert
- ilg001 went back to Alert at 14:35:08Z (20-min avg 5179ms per the monitor post) and returned to Warn at 14:36:08Z (4923ms). ilg003 went back to Alert at 14:31:08Z (5611ms) and is still Alert. ilg004 has been Warn since 14:05:08Z. Source: monitor 179927768 group states.
- `snap.poll.request.latency.avg`, 20-min scalar avg to ~14:37Z: ilg001 4.82s, ilg003 5.29s, ilg004 4.32s, ilg002 0.27s, ilg005 0.27s. ilg001 5-min buckets 13:40-14:35Z ranged 1.9-8.0s (8.0s in the 14:30Z bucket).
- Create path, `snap.request.latency.avg` on ilg001: only two points in 60 min (3.35s at 13:45Z, 2.04s at 14:00Z). `snap.slot_queue_depth` max 3 on ilg001, 0 elsewhere.
- Polls over 60 min, `snap.poll.request` vs `.success` (sum): ilg001 524/524, ilg003 180/180, ilg004 623/623, ilg002 90/90, ilg005 1451/1451. 0 failures.
- snap_adapter since 14:00Z: 0 `Entity creation in SNAP failed` (the same query matches 26 in 12:00-13:10Z, so it works). 39 `Incoming record received`, 39 `Entity created in SNAP`. Nothing exhausted or held.
- `snap_adapter.prod.create_record_*` subscriptions (master_data, purchase_order, rga, sales_order, work_order): max backlog 0 and max oldest unacked age 0 over 60 min.
- Verdict unchanged: vendor, P3. Replied in the 14:36Z Datadog post: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793111786064839?thread_ts=1793111786.064839 (reply ts 1793111879.574919)
- Not established: why latency rebounded at 14:30Z (no Snap-side visibility; no direct probe, Fuse MCP 401).

## Update 2026-10-27 14:50Z: ilg004 re-trigger to Alert
- ilg004 back in Alert at 14:47Z (20-min avg 5.2s per monitor post; 5.4s scalar). Polls 30 min: complete 5-min buckets 455 requests / 455 successes. 0 `Entity creation in SNAP failed` since 14:37Z (8 `Entity created in SNAP`). Max oldest_unacked_message_age 0 on all five `snap_adapter.prod.create_record_*` subs. No impact; vendor, P3 unchanged. Replied in https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793112503645869
