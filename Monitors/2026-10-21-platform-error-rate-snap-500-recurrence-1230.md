---
tags: [datadog-triage]
date: 2026-10-21
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: snap-queue-polling-service
business_id:
snap_instance: ilg001, ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792585909121499"
opened_at: "2026-10-21T12:30:37Z"
resolved_at: "2026-10-21T12:43:00Z"
minutes_spent: 13
severity_assessed: P3
flapping: false
outcome: vendor
escalated_to:
ticket:
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# Second Snap 500 burst on ilg001 and ilg005 at 12:30–12:35Z, during INC-42

## Fired
Monitor 180072217 fired at 12:30:37Z, recovered at 12:34:37Z and re-fired at 12:35:37Z. It counts error logs tagged `domain:fuse`. These errors were the second short SnapFulfil HTTP 500 burst inside the open P1 INC-42. Folded into this triage:
- Monitor 334832256, "Entity creation failing for many records", went to Alert at 12:35:36Z.
- Monitor 179927768, "API latency" on ilg001, went to Alert at 12:36:08Z, in thread p1792586243862369.

## Investigation
- **Poller 500s.** snap-polling-service logged 35 error lines carrying HTTP 500 between 12:30:18Z and 12:34:58Z, all on `GET /v2/snapoutbound`. Grouped by `@snapHost`:
  - ilg001: MANUCURIST, DOCKBAY
  - ilg005: PHLUR (`get-snap-connection` confirms PHLUR is on ilg005), PURDYFIGG, STUBBLE, WILDSMITH, EPARFUM
- **Order creates.** The ilg005 circuit opened at 12:34–12:35Z: `circuit_open` 31 and `slot_timeout` 3, all with `transient:true`.
  - 13 new orders were rejected: STUBBLE SCPR34xx ×8, and PURDYFIGG #6570358, #6570365, #6570427, #6570432 and #6570434.
  - All 13 logged "Entity created in SNAP" on redelivery by 12:35:53Z.
  - replay-service (`createdAt` 2026-10-21) has no new holds since 12:25Z apart from the #6565591 email loop.
- **DOCKBAY "Confirmation mapping failed".** Two rows, TPOB005123 and TPOB005124, at 12:30:19Z with `scope:entry`.
  - Code read on snap-adapter `origin/master` 65fb606, `apps/snap-queue-polling-service`. In `map-entries-in-isolation.ts:37-51` a failed entry returns null. `confirmations.service.ts:319-342` and `outbound-queue.clearer.ts:62-65` clear only the rows that were published. There is no per-row retry budget, so a failed row is retried on every poll.
  - At 12:37Z, Snap's OBQ for DOCKBAY had no unprocessed DESPATCH rows, and an XDoc search for both ids returned nothing.
  - At 12:36:54Z DOCKBAY logged a good_out "claim skipped duplicates" with `skippedCount` 2.
- **Probes,** all read-only `snaplookups`:
  - ~12:35Z: ilg001 with DOCKBAY credentials timed out, ilg005 with PHLUR credentials timed out, ilg005 with PURDYFIGG credentials succeeded.
  - 12:36–12:40Z: every probe succeeded (ilg001 with MANUCURIST and DOCKBAY credentials, ilg005 with PURDYFIGG and PHLUR credentials). OBQ reads on both hosts succeeded.
- **Watch.** No `domain:fuse` errors between 12:35:34Z and 12:42Z apart from #6565591 at 12:40:09Z. The poller and adapter were active and succeeding over the same window.
- **Latency.** `snap.poll.request.latency.avg` 2-minute averages:
  - ilg001: 14.6s at 12:34Z, then 2.6–3.4s 12:38–12:42Z
  - ilg005: 7.8s at 12:34Z, then about 300ms
  - ilg001 daily averages: 95–131ms 15–18 Oct, then 1.80s, 1.15s and 2.16s for 19–21 Oct. This is chronic degradation since 19 Oct.
- **Flapping.** 23 alert events for 180072217 in 24h, all during today's Snap incidents. Not mistuned.

Not established:
- A per-row publish log for TPOB005123/5124. The poller doesn't log `queueId` on publish.
- Whether the burst will recur.

## Outcome
A vendor burst that recovered on its own, inside INC-42. Nothing was lost or held, and @fuse-support was not pinged. Monitor 334832256 stays in Alert until its 15-minute cardinality window rolls past 12:35Z. ilg001's latency degradation since 19 Oct is worth raising with SnapFulfil.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792585909121499 (reply p1792586574188169)
- Latency thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792586243862369 (reply p1792586575635339)
- Incident room update: https://gfsdeliver-eng.slack.com/archives/C0CASJJEVKM/p1792586583510359
- Incident: https://app.incident.io/gfsdeliver-eng/incidents/01M5F4QXDC80YW1B177YAEM8Y0
