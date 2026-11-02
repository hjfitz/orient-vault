---
tags: [datadog-triage]
date: 2026-10-22
monitor: "[FUSE][Snap Adapter] API latency threshold breached"
service: snap-queue-polling-service
business_id:
snap_instance: ilg001
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792666405144839"
opened_at: "2026-10-22T10:52:08Z"
resolved_at: "2026-10-22T10:55:33Z"
minutes_spent: 3
severity_assessed: P4
flapping: true
outcome: vendor
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# ilg001 latency Alert repeat at 10:52Z: still slow, no errors, nothing held

## Fired
Monitor 179927768 put the ilg001 group into Alert at 10:52:08Z (avg(last_20m) = 5105ms > 5000). One further firing of the same cause was folded in. This repeats the 10:01Z firing, which was triaged P4 vendor (2026-10-22-snap-adapter-api-latency-ilg001-ilg004-1001).

## Investigation
- `snap.poll.request.latency.avg` on ilg001 from 10:00 to 10:53Z ranged from 1478ms to 15514ms, with an average of 4871ms. The peaks were 15.5s at about 10:48Z and 14.9s at about 10:51Z.
- `snap.poll.request.success`: 387 since 10:00Z.
- `snap.poll.request.failure` (ilg001) and `snap.poll.skipped_circuit_open` returned no series since 10:00Z.
- Logs since 10:00Z mentioning ilg001 together with timeout, ETIMEDOUT, ECONNABORTED, 5xx, 404 or circuit: 0.
- snap_adapter/poller error and warn logs since 10:00Z, excluding the "Consignment StU not found" baseline: only 11 "Entity creation in SNAP failed" errors. All are PURDYFIGG, schema_validation, ShipAddress.0.Name over 50 characters, site 0010 BRACKMILLS2. They are unrelated to ilg001 and are the same known reject retrying every 5 minutes.
- replay-service (prod) holds 0 records created today for DOCKBAY and 0 for MANUCURIST.
- Maintenance: no DB1 window on 22 Oct. DB1's window was 21 Oct (2026-10-19-snap-version-update-and-patch).
- Flapping: 53 "API latency threshold breached" alert events in 24h.

Not established:
- Why ilg001 has been slow since 19 Oct.
- `lookup-snap-instance ilg001 includeBusinesses` (prod) returned businessCount 0. That conflicts with DOCKBAY and MANUCURIST being on ilg001, so their hosts were not re-verified this run.

## Outcome
Vendor, P4. Nothing has changed since the 10:01Z triage: ilg001 is slow, with no failures and nothing held. The monitor still needs retuning, and no ticket has been filed.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792666405144839
- Prior triage: 2026-10-22-snap-adapter-api-latency-ilg001-ilg004-1001
