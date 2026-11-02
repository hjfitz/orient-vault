---
tags: [datadog-triage]
date: 2026-10-21
monitor: "[FUSE][Platform] create_data_failure spike"
service: snap-adapter
business_id: PURDYFIGG
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792583846893069"
opened_at: "2026-10-21T11:56:07Z"
resolved_at: "2026-10-21T12:02:33Z"
minutes_spent: 6
severity_assessed: P3
flapping: false
outcome: escalated
escalated_to: INC-42
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# create_data_failure spike (10 in 15m) = INC-42 Snap outage holds + #6565591 loop

## Fired
Monitor 302536087, Warn, send_request_count on bifrost.prod.create_data_failure.v1 = 10 over 15m.

## Investigation
- replay-service prod holds 11:45–11:55Z: PURDYFIGG #6570355, #6570356, #6570364, #6570266, #6570350, #6570366, #6570368 (create.snap_unavailable, circuit open after 10 deliveries) plus #6565591 (circuit-held and Email MANDATORY data error).
- Snap ilg005 creating again from 11:51:35Z; no outage errors after 11:51:23Z.

## Outcome
Knock-on of the INC-42 Snap outage; pointed at INC-42, no ping.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792583846893069
- Verdict: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792584153681939
- Incident: https://app.incident.io/gfsdeliver-eng/incidents/01M5F4QXDC80YW1B177YAEM8Y0
