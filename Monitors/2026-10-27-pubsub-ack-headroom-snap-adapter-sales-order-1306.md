---
tags: [datadog-triage]
date: 2026-10-27
monitor: "[FUSE][Platform] Pub/Sub ack-deadline headroom eroding (standard subscriptions)"
service: snap-adapter
business_id:
snap_instance: ilg001
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793106484946419"
opened_at: "2026-10-27T13:06:39Z"
resolved_at: "2026-10-27T13:11:18Z"
minutes_spent: 5
severity_assessed: P3
flapping: true
outcome: vendor
session_id: 6735df5f-a090-45cd-991d-d7f9cfef0ba8
status: resolved
---
# snap_adapter sales_order sub unacked for 182s while snap-adapter's calls to Snap ilg001 were slow

## Fired
Monitor 323648859 went to Alert on group `snap_adapter.prod.create_record_sales_order.v1.sub` at 13:06:39Z, with oldest unacked at 182s. One more firing of the same cause was folded into this one.

## Investigation
- **The sub:** `gcp.pubsub.subscription.oldest_unacked_message_age` went 1s at 13:01Z, 62s, 122s, 182s at 13:04Z, then 0 at 13:05Z. `num_undelivered_messages` peaked at 14.
- **Failures:** `service:snap_adapter @environment:prod "Entity creation in SNAP failed"` logged 26 between 13:00:32Z and 13:05:58Z: ICONICL 17 and DOCKBAY 9. 25 were `slot_timeout` ("Timed out after 30000ms waiting for a concurrency slot", `transient:true`, then a 503) and 1 was `snap_api_error` (DOCKBAY UK-910557).
  - None since 13:06:30Z (checked to 13:10:48Z).
  - None with `@exhausted:true` since 10:00Z.
- **Recovery:** all 17 distinct sales_order recordIds that failed since 12:45Z later logged "Entity created in SNAP". For example, UK-910590, UK-910595 and UK-910596 failed at 13:05:38–58Z and were created at 13:06:52–56Z with 204s. Nothing is held.
- **Snap side:**
  - snap-adapter `snap.request.latency.avg{snap_host:ilg001liveapi}` was 14–53s from 12:59Z to 13:06Z.
  - `snap.slot_queue_depth` reached up to 9 on ilg001liveapi, against 0 on ilg003 and ≤5 on ilg005.
  - Poller `snap.poll.request.latency.avg` on ilg001 averaged about 16s in the 12:58Z bin. ilg003 and ilg004 were also at 7–13s through the morning, and ilg002 and ilg005 stayed under 1.1s on average.
- **Hosts:** DOCKBAY's host is ilg001liveapi per `Customers/DOCKBAY/config.snapshot.yaml` (synced 2026-10-22).
- **Maintenance:** the only window today is DB3 Poland at 09:30Z for an estimated 60 min (`Maintenance/2026-10-19-snap-version-update-and-patch.md`). It doesn't cover 13:00Z or DB1.
- **Flapping:** Datadog alert events for this monitor and group over 7 days show 5 Triggered (10-21 ×3, 10-26 16:16Z, 10-27 13:06Z) and 9 Warn.
- **Not established:**
  - ICONICL's Snap host. It has no Customers folder, and the Fuse MCP got a 401.
  - A direct read probe of ilg001, because Snap credentials come from the Fuse MCP.
  - Dead-letter count on the sub. The metric query returned no series.

## Outcome
Vendor-driven: Snap ilg001 was slow, and this is a knock-on of the same latency the snap-adapter API-latency monitor (179927768) is alerting on. The consumer wasn't stuck. Every failed create succeeded on redelivery about a minute later, and nothing is held. No Fuse action is needed and no ticket was filed. The 13:05Z P2 "Entity creation failing for many records" monitor (334832256) counts these same records and is being triaged separately.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793106484946419
- Reply: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793106678019999?thread_ts=1793106484.946419&cid=C099WKQTE8G
