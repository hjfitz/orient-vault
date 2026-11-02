---
tags: [incident]
reference: INC-40
date: 2026-10-20
service: shopify-connector
business_id:
severity: P2
is_us: false
declared_by: agent
declared_at: "2026-10-20T07:08:56Z"
resolved_at: "2026-10-20T12:32:12Z"
minutes_to_resolve: 323
incident_url: "https://app.incident.io/gfsdeliver-eng/incidents/01M5C28JVNS08THJMDHGX5A1P9"
slack_channel_url: "https://gfsdeliver-eng.slack.com/archives/C0CAEGABJBF"
follow_up_count: 4
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# GCP europe-west2-b power event: Fuse services hung on unreachable Redis

## Impact
06:03–12:02 UTC. Shopify order collection and fulfilment stopped 06:03–08:17 (shopify-connector crash-looping). The Fuse API hung on connector lookups 07:02–09:18 and 09:43–10:23 (DOCKBAY, PURDYFIGG POs). The SFTP server was unreachable ~06:00–11:06 (STUBBLE, EPARFUM, WILDSMITH could not upload). snap-adapter returned 504s 10:00–11:31, and snap-polling-service sent bursts of duplicate confirmations (09:15, 11:58).

**Fuse dropped nothing.** We reconciled end to end for 06:00–12:20, excluding requests that failed back to the sender:
- Records in, 0 lost: Shopify 185 orders, API 99 records and SFTP 105 files reached the bus. 325 records reached Snap, and 3 were rejected for missing data.
- Confirmations out, 0 lost: none was cleared from Snap without being published. All 1,435 distinct confirmations were delivered: Shopify 1,169, API webhooks 118, SFTP 148.
- Side effects: duplicate confirmations reached customers (safe to ignore), and PURDYFIGG #6565457 was created in Snap with duplicate lines.

## Root cause
A Google Cloud power event in europe-west2-b took out the zone's BASIC (single-zone) Memorystore Redis instances, about 06:03–09:19 and again 09:40–~11:40. The trigger was the vendor, but our own code turned it into an outage:
- `@gfs-bifrost/cache` 0.3.0 checks the connection before reads but not before writes, and node-redis queues commands forever, so cache writes hung.
- Startup Redis init had no time limit.
- remote-config's memory mode and `dispose()` are broken, so neither was a fallback.

## Resolution
- shopify-connector#345 (live 08:17) and fapi#179 (live 10:23): Redis init now times out and the service carries on without a cache.
- snap-adapter and snap-polling-service recovered on their own once Redis returned (11:31–12:02).
- The SFTP VM became reachable again at 11:06.
- Tracking-service's dead-letter queue was redriven: 203 messages, 0 errors.

## Follow-ups
- Let every Redis-using service run when Redis is unreachable. The library fix belongs in `@gfs-bifrost/cache` and `@gfs-bifrost/remote-config`.
- Re-evaluate the SFTP server architecture: a single VM in zone b, zone hard-coded, SSH host keys not persisted.
- Move plain-text keys in Cloud Run env vars to Secret Manager.
- Correct PURDYFIGG #6565457 duplicate lines in Snap.

## Links
- Incident: https://app.incident.io/gfsdeliver-eng/incidents/01M5C28JVNS08THJMDHGX5A1P9
- Slack channel: https://gfsdeliver-eng.slack.com/archives/C0CAEGABJBF
- Postmortem (complete, closed 2026-10-20T12:38Z): https://globalfreight.atlassian.net/wiki/spaces/Bifrost/pages/335314954
