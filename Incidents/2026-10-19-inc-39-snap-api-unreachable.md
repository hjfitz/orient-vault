---
tags: [incident]
reference: INC-39
date: 2026-10-19
service: snap-adapter
business_id:
severity: P2
is_us: false
declared_by: agent
declared_at: "2026-10-19T15:24:17Z"
resolved_at: "2026-10-19T15:59:03Z"
minutes_to_resolve: 34
incident_url: "https://app.incident.io/gfsdeliver-eng/incidents/01M5AC6WSFP4TWVHAVBQB80D47"
slack_channel_url: "https://gfsdeliver-eng.slack.com/archives/C0CABCGT9M4"
follow_up_count: 7
ticket:
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# Snap API unreachable (ilg005 and ilg001): order creates and polling failing

## Impact
From about 15:00Z (outbound polling from about 14:58Z) the Snap API host 209.143.134.157:443 was unreachable from snap_adapter and from an external host. Creates and polling failed across multiple businesses and the circuit breaker opened for ilg005. Orders that failed (PURDYFIGG 166, DOCKBAY 11, STUBBLE 3, EPARFUM 1) recovered via Pub/Sub redelivery and shopify-connector re-poll; one WILDSMITH master_data record was replayed manually. No data loss confirmed.

## Root cause
The Snap endpoint was unreachable (EHOSTUNREACH / timeouts), vendor-hosted. Cause on Snap's side not established; an ILG colleague reported Snap closed their incident. On our side, circuit-open refusals were stored as non-retryable held failures after 10 delivery attempts.

## Resolution
Self-recovered at the vendor: host reachable 15:21:39Z, last snap_adapter error 15:22:07Z, poller breaker closed 15:19:33Z. 42 stale held PURDYFIGG rows deleted via the replay-service API after checking each was in Snap. Declared at the Lead's call for a comms room, after triage judged Snap-down not incident-worthy on its own.

## Follow-ups
- Move the replay-service API key into Secret Manager
- Ask ILG/SnapFulfil for an RCA and whether a maintenance window applied
- Add a 'Snap API unreachable' monitor and group the knock-on Pub/Sub monitors
- Investigate making circuit-open refusals recoverable
- Add bulk delete/dismiss for held failures (fuse-ui Retry Queue) and a delete tool to the Fuse MCP
- Consider auto-clearing replay-service rows whose record is already in the WMS
- Investigate the rising PURDYFIGG goods_out_confirmation holds

## Links
- Incident: https://app.incident.io/gfsdeliver-eng/incidents/01M5AC6WSFP4TWVHAVBQB80D47
- Slack channel: https://gfsdeliver-eng.slack.com/archives/C0CABCGT9M4
- Postmortem (draft): https://globalfreight.atlassian.net/wiki/spaces/Bifrost/pages/335020090/Postmortem+INC-39+Snap+API+unreachable+ilg005+and+ilg001
