---
tags: [datadog-triage]
date: 2026-10-27
monitor: "[FUSE][Snap Adapter] Entity creation failing for many records"
service: snap-adapter
business_id:
snap_instance: ilg001
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793106654089609"
opened_at: "2026-10-27T13:05:36Z"
resolved_at: "2026-10-27T13:10:54Z"
minutes_spent: 5
severity_assessed: P3
flapping: true
outcome: vendor
session_id: 6735df5f-a090-45cd-991d-d7f9cfef0ba8
status: resolved
---
# 17 slot_timeout orders on ilg001 (ICONICL, DOCKBAY) all landed in Snap; ilg001 latency is rising all week

## Fired
Monitor 334832256 went to Warn at 13:01:36Z and to Alert at 13:05:36Z. It counts distinct `@recordId` on "Entity creation in SNAP failed" over 15m, with a threshold of >10. It also fired today at about 09:54Z and 11:19Z (Triggered), recovering at 10:09Z and 11:35Z: 32 alert events over 7d. Datadog did not post the 13:05 firing (or the 11:19 one) to #bifrost-notifications, so the verdict went out as a top-level bot message.

## Investigation
- **Failures:** 25 failure logs for 17 records between 13:00:32 and 13:05:58Z. All were `@failureMode:slot_timeout` with `@transient:true`: ICONICL 9 and DOCKBAY 8. All were sales orders with `@snapPayload.Warehouse:SPACE` (DB1, ilg001).
- **No loss:** all 17 have a later `Entity created in SNAP` log. Over 24h, all 153 transient-failed recordIds have a later created or already-exists log. The `dead_letter_message_count` for snap_adapter subs has no data.
- **Backlog:** the oldest unacked message on `snap_adapter.prod.create_record_sales_order.v1.sub` was 62s at 13:02, 122s at 13:03 and 182s at 13:04, then 0 at 13:05 and 18s at 13:06. No failures since 13:06:30.
- **ilg001 latency:** `snap.request.latency.avg` on ilg001 was 31.2s at 13:00 and 28.3s at 13:05 (5-min avg). The daily average was 1.1s on 20 Oct, 3.9s, 2.7s, 4.7s, 3.0s, 2.3s, 7.3s on 26 Oct, and 17.2s today. `snap.slot_queue_depth` max was 9 on ilg001 at 13:00.
- **Poll latency** (`snap.poll.request.latency.avg`, 30-min) at 13:00: ilg001 16.5s, ilg003 9.6s, ilg004 9.1s, ilg002 0.45s, ilg005 0.58s. ilg003 went from about 0.3s to 7.7s at 09:30Z, in line with its DB3 maintenance window, and has stayed at 9.6–12s since.
- **Self-saturation:** ilg001 poll counts (`snap.poll.request.latency.count`) were 331–375 per hour today, against 380–661 yesterday. The adapter count was 71 in the 13:00 hour against 26 in the 12:00 hour. Slot timeouts while Snap itself answers slowly (28–31s) mean Snap is the bottleneck, with the 5-slot per-instance cap.
- **Shared cause:** the platform error-rate monitor (180072217) window at 13:03:30–13:05:40 held only 6 snap_adapter slot_timeout errors. The ilg001 group of API latency monitor 179927768 is the same host. Schuster's 11:49 reply on the latency thread describes this as the ongoing South-region degradation.
- **Deploys:** the prod revision is snap-adapter-prod-00092-9nm, version e60ef06 (merged 23 Oct). There was no deploy today.
- **Maintenance:** the only window today was DB3 (Poland) from 09:30Z, so DB1/ilg001 is not covered.
- **Not established:**
  - No direct probe of ilg001, because the Fuse MCP returned 401, leaving no Snap credentials.
  - Why ilg001 is slow on Snap's side.
  - Why Datadog did not post this monitor's firings to Slack today.
  - The hourly slot_timeout histogram came back empty.

## Outcome
Vendor-side latency on ilg001. No data was held, and every failed record landed on redelivery. P3. Recommended, not filed:
1. Raise ilg001's week-long latency rise with SnapFulfil.
2. Add `@transient:false` (or exclude slot_timeout) to the monitor query in the observability repo. This was first recommended on 2026-10-21.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793106654089609
- Monitor: https://app.datadoghq.com/monitors/334832256
