---
tags: [datadog-triage]
date: 2026-10-22
monitor: "[FUSE][Snap Adapter] API latency threshold breached"
service: snap-queue-polling-service
business_id:
snap_instance: ilg001, ilg004
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792663348243679"
opened_at: "2026-10-22T10:01:08Z"
resolved_at: "2026-10-22T10:05:23Z"
minutes_spent: 4
severity_assessed: P4
flapping: true
outcome: vendor
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# ilg001 + ilg004 latency Alert: slow but no errors; ilg004 slow since DB4 update

## Fired
Monitor 179927768 (`avg(last_20m) snap.poll.request.latency.avg by snap_host > 5000`): two groups went to Alert at 10:01:08Z. ilg001 was at 5144ms and ilg004 at 5469ms. The ilg002, ilg003 and ilg005 groups did not fire.

## Investigation
- `snap.poll.request.latency.avg` by snap_host, 5m buckets, 07:05–10:00Z:
  - ilg004 ran at 46–271ms until 08:50, hit 19.1s at 08:55, then held at 2.3–7.6s.
  - ilg001 ran at 1.6–9.3s and finished at 7.8s and 9.0s.
  - The other hosts stayed mostly under 1s, with one ilg005 bucket at 2.5s at 09:35.
- 7d at 12h buckets:
  - ilg004 ran at 77–152ms before today.
  - ilg001 ran at 93–166ms until 19 Oct 12:00Z, then at 0.6–3.7s.
- Maintenance record 2026-10-19-snap-version-update-and-patch puts DB4 at 2026-10-22T08:30Z for about 60 minutes. Poller "Outbound queue fetch failed" errors ran 08:34–08:54Z (165 of them), which matches the window. No window covers ilg001 today.
- Errors since 08:55Z (snap_adapter + snap-polling-service): only 14 "Entity creation in SNAP failed" (schema_validation, PURDYFIGG, ShipAddress.0.Name over 50 characters). None were Snap 5xx, 404s or timeouts. Warn level held only the usual "Consignment StU not found" baseline.
- `snap.poll.request.success` / `.failure`, 10m buckets since 08:00Z:
  - ilg004 failed only in 08:30–09:00. Since then it has shown 75 successes every 10 minutes and 0 failures.
  - ilg001 had no failures, with 25–94 successes every 10 minutes.
  - `snap.poll.skipped_circuit_open` was empty.
- Direct snaplookups RECSTATUS probes at about 10:04Z: ilg004 (KAPPAHL) and ilg001 (DOCKBAY) both returned data. Wall-clock time was about 3s each, including tooling.
- The monitor has 51 alert events in 24h, so it is flapping.
- snap-queue-polling-service was deployed to prod at 09:47Z. ilg004 was already elevated from 08:55Z, so the deploy didn't cause it.

Not established:
- Why ilg004 stays slow after the update.
- Why ilg001 has been slow since 19 Oct.
- The cause of the 09:50–10:00Z peaks.
- Precise probe latency.

## Outcome
Vendor, P4, for both hosts: latency only, with nothing held and no errors. Raise ilg004's slowness after the update with ILG if it persists. The monitor needs retuning, and no ticket has been filed.

## Links
- Slack thread (ilg004): https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792663348243679
- Slack thread (ilg001): https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792663346019659
