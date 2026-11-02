---
tags: [datadog-triage]
date: 2026-10-21
monitor: "[FUSE][Snap Adapter] API latency threshold breached"
service: snap-adapter
business_id:
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792581567709479"
opened_at: "2026-10-21T11:18:08Z"
severity_assessed: P3
flapping: false
outcome: vendor
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: open
---
# All five Snap hosts slowed down together at about 11:16Z (ilg002/004/005 Warn)

## Fired
Monitor 179927768 went to Warn for ilg002 and ilg005 at 11:18:08Z and for ilg004 at 11:20:08Z. ilg001 was already at Alert.

## Investigation
- `snap.poll.request.latency.avg` by snap_host, 2-minute peaks: ilg001 32s, ilg002 10.4s, ilg003 5.2s, ilg004 17.4s, ilg005 11.8s. The baseline was 0.1–0.3s, and 07:10Z peaked at 35–80s. In the latest bucket ilg002, ilg003 and ilg005 were 0.1–0.15s, while ilg001 and ilg004 were about 6.9s.
- snap_adapter create failures from 11:14:30Z were only on ilg005 (PURDYFIGG timeouts and STUBBLE/EPARFUM/PURDYFIGG slot waits), and every one is in Snap. snap-polling-service logged a few retried failures at 11:17–11:21Z.
- A direct ilg005 read returned 200 at about 11:20Z. ILG support (Ryan) has raised a ticket for BM2 / ilg005, per Schuster in thread 1792581618.529099.
- Not established: the cause on Snap's side. Maintenance notices weren't checked.

## Outcome
Vendor, P3, nothing held. ilg001 and ilg004 were still elevated at hand-off.

## Links
- ilg005 reply: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792581874356239
- ilg002 reply: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792581882829949
- ilg004 reply: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792581884289529
