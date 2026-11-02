---
tags: [datadog-triage]
date: 2026-10-21
monitor: "[FUSE][Snap Adapter] Entity creation failing for many records"
service: snap-adapter
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792580736194369?thread_ts=1792580625.070129"
opened_at: "2026-10-21T11:04:36Z"
resolved_at: "2026-10-21T11:24:31Z"
minutes_spent: 20
severity_assessed: P4
flapping: false
outcome: self_resolved
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# 8 slot_timeout orders on ilg005 all landed in Snap; none dead-lettered

## Fired
Monitor 334832256 (draft) went to Warn at 11:04:36Z and then Alert, counting distinct recordIds with "Entity creation in SNAP failed" over 15m.

## Investigation
- Followed the 8 slot_timeout orders: PURDYFIGG #6570200 and #6570293 got already-exists at 11:07:16–17Z. STUBBLE SC17318799-1, SC17417295, SC17417296 and SC17417297 got it at 11:09:25–27Z, and PURDYFIGG #6570287 and #6570290 at 11:09:27–28Z. That took 3 to 6 deliveries against a dead-letter limit of 10 (`ack_event_delivery_attempts` default 10).
- Snap MCP on ilg005 shows all the PURDYFIGG orders created at 11:05:11–16Z, and SC17417295 at 11:07:23Z.
- slot_timeout means `SemaphoreAcquireTimeoutError`. The order waited 30s for one of 5 per-host slots (`SNAP_MAX_CONCURRENT_REQUESTS`=5, per instance) and never reached Snap. The slots were held by PURDYFIGG PUTs hitting the 120s timeout twice (#6570197/292/205/294/296). Snap had stored those orders at 11:05Z but answered late.
- `dead_letter_message_count`: no data on any prod sub since 10:30Z. Every transient failure since 10:50Z has a later success log. The exceptions are DOCKBAY UK-909462 (City over 30 characters, held) and PURDYFIGG #6565591 (Email, known).
- The pattern repeated at 11:14Z (#6570299/303/305/310) and 11:19–20Z (#6570311/316/317/320). All of those landed too.
- The monitor counts transient retries, which inflated it to Alert. It needs `@transient:false` or a mode exclusion before it goes live.

## Outcome
Self-resolved, no loss. Snap was degrading across hosts from about 11:16Z (see the latency record). Not established: why PURDYFIGG creates in particular are slow on ilg005.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792581871396789
