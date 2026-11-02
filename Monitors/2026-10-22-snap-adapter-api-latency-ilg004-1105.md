---
tags: [datadog-triage]
date: 2026-10-22
monitor: "[FUSE][Snap Adapter] API latency threshold breached"
service: snap-queue-polling-service
business_id:
snap_instance: ilg004
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792667182649709"
opened_at: "2026-10-22T11:05:08Z"
resolved_at: "2026-10-22T11:07:58Z"
minutes_spent: 3
severity_assessed: P4
flapping: true
outcome: vendor
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# ilg004 latency Alert again: still slow after the DB4 update, still no errors

## Fired
Monitor 179927768 (`avg(last_20m) snap.poll.request.latency.avg by snap_host > 5000`, managed-by:terraform). The ilg004 group went to Alert at 11:05:08Z at 5084ms. This repeats the 10:01Z firing (record `2026-10-22-snap-adapter-api-latency-ilg001-ilg004-1001`). One more firing with the same cause is folded in here.

## Investigation
- **Latency:** `snap.poll.request.latency.avg` for ilg004 in 10-min buckets from 09:30Z was 2.9–6.4s. Across the 30h before the 08:30Z DB4 update, most buckets averaged about 75–280ms.
- **Poll metrics since 10:00Z:**
  - `snap.poll.request.success` for ilg004 was 510.
  - `snap.poll.request.failure` for ilg004 had no data.
  - `snap.circuit_opened`, `snap.poll.skipped_circuit_open` and `snap.request.failure` (prod) had no data.
- **Error and warning logs since 10:00Z:**
  - In the snap services, the only items were PURDYFIGG schema_validation (13: ShipAddress.0.Name over 50 chars, BRACKMILLS2) and "Consignment StU not found" warnings for PURDYFIGG, EPARFUM, WILDSMITH and DOCKBAY. None of these businesses is on ilg004.
  - A fleet-wide search for timeout, 5xx, 404, circuit and EHOSTUNREACH found nothing from Snap hosts.
  - The ilg004 businesses showed only SAIRA shopify "DDP rules unavailable" (42) and dedupe "Record dropped" (42). Both messages also appeared yesterday in the same window (17 each), and neither involves Snap.
- **Replay holds (prod, created 2026-10-22):** KAPPAHL, BABYMORI, SAMMCK and SAIRA have 0. SPORTLUX has 58 in total, and the newest is from 08:41:43Z, so none is new.
- **Maintenance:** `Maintenance/2026-10-19-snap-version-update-and-patch.md` has a DB4 window starting at 2026-10-22T08:30Z with an estimate of about 60 min. The slowness is still going after that.

## Outcome
Vendor P4, the same as the 10:01Z triage. Snap is slow but nothing fails, and nothing new is held. Reply posted (broadcast). No ticket. Escalate if errors or holds appear.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792667182649709
