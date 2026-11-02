---
tags: [datadog-triage]
date: 2026-10-20
monitor: "[FUSE][Snap Adapter] Entity creation failed"
service: snap-adapter
business_id: PURDYFIGG
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792498642951699"
opened_at: "2026-10-20T11:32:51Z"
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: open
---
# Snap Adapter "Entity creation failed" (274521171) in Alert, notifying a dead Slack handle

## Fired
`sum(last_5m):max:snap.entity_not_created{environment:prod}.as_count() > 0`. It triggered at 11:32:51Z, recovered at 12:00:51Z and re-triggered at 12:02:51Z, then stayed in Alert. It also triggered on 19 Oct at 12:17, 14:03, 14:32 and 15:00Z. The notification goes to `@slack-bifrost-alerts`, which is not a real channel, so no Slack thread exists for it. The verdict was posted in the related create_data_failure thread in #bifrost-notifications.

## Investigation
- Failures by record, last 3h (log SQL on `"Entity creation in SNAP failed"`):
  - PURDYFIGG `#6531052`: 27
  - PURDYFIGG `#6565591`: 16
  - DOCKBAY `026-8515917-5357958`: 5
  - DOCKBAY `204-2446765-1345901`: 3
  - STUBBLE `SCB2B584889`: 1
- Every failure after 11:35:52Z is one of the two PURDYFIGG orders (`CONTACT_UPDATE Email MANDATORY`, empty value). Support was already pinged about them in the thread.
- STUBBLE `SCB2B584889` is new. It failed with `City MANDATORY` and is held in replay-service (id 9682b186…, 0 attempts). Support was pinged.
- DOCKBAY: both orders logged `Entity created in SNAP` at 11:31:51Z. Their redeliveries 1–2s later were rejected with `XDoc Invalid Syntax`, which left 8 held replay rows (0 attempts). Support was told not to replay them. This happened during the INC-40 recovery.
- Re-fire cadence:
  - PURDYFIGG rejections arrive about every 5 minutes, and there was a 7-minute gap from 11:55 to 12:02Z.
  - Terraform `monitors.snap-adapter.tf` sets `renotify_interval = 60`, `draft_status = "draft"` and `require_full_window = false`.
  - So while the re-polls keep coming the monitor stays in Alert and re-notifies hourly. Any gap of more than 5 minutes recovers it, and the next re-poll re-triggers it.
- Routing:
  - Slack channel search (public, private and archived) found no `#bifrost-alerts`, and no Slack message for this monitor was found.
  - On observability `origin/main`, `@slack-bifrost-alerts` is hardcoded in 5 snap-adapter, 4 shopify-connector and 1 sftp-connector monitor messages.
  - `global.tfvars` `alert_handles` = `@slack-bifrost-notifications`.
- Not established:
  - whether `draft_status = "draft"` suppresses notifications;
  - why the DOCKBAY redeliveries returned `XDoc Invalid Syntax` rather than a duplicate rejection;
  - the Snap-side existence of the DOCKBAY orders, which was not checked directly.

## Outcome
P4. The verdict is monitor_mistuned: the monitor routes to a dead Slack handle and flaps on re-polls of customer data errors. Support was pinged once for the new STUBBLE hold, and the DOCKBAY "do not replay" note went in the same reply. Still owed: repoint the 10 hardcoded `@slack-bifrost-alerts` monitors to `alert_handles`, and consider per-record dedupe or a higher threshold so one stuck order doesn't keep this P2 in Alert.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792498642951699 (reply ts 1792499882.395409)
- Monitor: https://app.datadoghq.com/monitors/274521171
