---
tags: [datadog-triage]
date: 2026-10-21
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: snap-adapter
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://slack.com/archives/C099WKQTE8G/p1792582603807499"
opened_at: "2026-10-21T11:35:37Z"
resolved_at: "2026-10-21T12:02:54Z"
minutes_spent: 27
severity_assessed: P3
flapping: true
outcome: escalated
escalated_to: INC-42
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# Snap ilg001 + ilg005 returning HTTP 500 on every call; PURDYFIGG #6570350 at 9/10 deliveries

## Fired
Error-rate monitor 180072217 fired at 11:35:37Z, its third firing today after 11:13 and 11:18Z. Folded in: 334832256 (entity creation failing for many records, draft), Warn at 11:37:36Z.

## Investigation
- 11:35–11:38Z errors: snap_adapter PURDYFIGG #6570350 got a Snap `500 Runtime Error` (ASP.NET error page) at 11:35:18 and 11:35:30Z, then `circuit_open` on ilg005 from delivery 3 onwards. snap-polling-service got 500s on outbound-queue fetches for ilg001 and ilg005 at 11:36:03Z (26 lines) and 11:38:03Z, across every business group on those hosts.
- Direct read-only `snaplookups/RECSTATUS` probes at 11:38:52–11:39:19Z returned 500 every time, in about 50ms: ilg005 7/7 (PURDYFIGG and STUBBLE users), ilg001 5/5 (DOCKBAY).
- `snap.poll.request.latency.avg` (5-minute buckets) had been improving before the 500s: at 11:30–11:35Z ilg004 0.42s, ilg002/003/005 0.34–0.51s, ilg001 6.2s.
- #6570350 (messageId 21733824111503523) reached delivery 9 of 10 at 11:39:13Z. The sub dead-letters after 10.
- `dead_letter_message_count`: no series on any sub between 11:00Z and about 11:39Z.
- replay-service prod today: new holds #6570234 and #6570334 (11:27:34Z, Snap DB `session is in the kill state`). Both got `already exists` at 11:30:09Z, so they're in Snap and don't need replaying. Other holds are unchanged: #6565591 (Email), UK-909462 (City), the 8 DOCKBAY 404s, and WILDSMITH SO-29273 (09:27Z, CustomerId/OrderClass).
- 334832256's records: #6570317/320/325/327/329/330/332/234/334 and SC17414852-1 all got `already exists`, DC127878086 was created, #6565591 is the known data hold, and #6570350 is pending.
- Not established: the cause on Snap's side, and the state of ilg002/003/004 (not probed; no Fuse errors logged for them).

## Outcome
Vendor, P3. Pinged @fuse-support: #6570350 is about to dead-letter and needs replaying once Snap recovers. Status is open until it is confirmed in Snap or replayed.

## Links
- Slack thread: https://slack.com/archives/C099WKQTE8G/p1792582603807499
- Incident: https://app.incident.io/gfsdeliver-eng/incidents/01M5F4QXDC80YW1B177YAEM8Y0 (INC-42, declared P1 by Harry ~11:50Z)

## Follow-up tracking 11:44–12:02Z
- Snap still 500 on probes 11:45, 11:49Z (ilg005 + ilg001); 200 on both at ~11:54Z and 12:02Z.
- Recovery: first snap_adapter `Entity created in SNAP` 11:51:35Z; last outage error (circuit_open) 11:51:23Z; last poller `Outbound queue fetch failed` 11:50:04Z. Error-free >10 min at 12:02Z (only #6565591 Email data errors after).
- Outage holds (create.snap_unavailable): #6570350 (11:40:24, 11:50:23), #6570355 (11:45:11), #6570356 (11:45:14), #6570364 (11:49:57), #6570266 (11:50:13), #6570366 (11:50:25), #6570368 (11:50:45); #6565591 also circuit-held 11:45:01, 11:49:55 (underlying data error).
- Created in Snap 11:51:35–11:51:56Z: STUBBLE SC17417301/302/303, SC17394980-1; PURDYFIGG TX-00001378, #6570274, #6570355, #6570356, #6570364, #6570371, #6570376.
- Snap search by CustomerRef: #6570350 IS in Snap (PURD767D7C81805, created 11:35:12Z, i.e. the 500 came after commit). #6570266/#6570366/#6570368 not in Snap. DOCKBAY 8 (09:04Z 404s) not in Snap.
- Final replay list posted in INC-42 room (as Harry, @fuse-support): https://gfsdeliver-eng.slack.com/archives/C0CASJJEVKM/p1792584174528399
