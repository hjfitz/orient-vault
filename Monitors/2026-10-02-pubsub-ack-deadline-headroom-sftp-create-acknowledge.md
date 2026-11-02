---
tags: [datadog-triage]
date: 2026-10-02
monitor: "[FUSE][Platform] Pub/Sub ack-deadline headroom eroding (standard subscriptions)"
service: sftp-connector
business_id:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790929663896889"
opened_at: "2026-10-02T08:27:43Z"
resolved_at: "2026-10-02T08:29:06Z"
minutes_spent: 2
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 75e611a9-f198-41c4-8b6b-5c3a45fbe972
status: resolved
---
# sftp-connector create_acknowledge sub hit 35s oldest-unacked at deploy time

## Fired
Warn on `sftp-connector.prod.create_acknowledge.v1.sub`: oldest unacked message aged 35s, at the minute of the sftp-connector prod deploy (`79dbd5e`, 09:26 BST).

## Investigation
- Confirmed: spike was one minute (08:22Z, 35s, 2 undelivered), sub at 0s for 3h before and after. Not tied to the 08:26Z deploy: the running version at the time was `8d2d270`, the pre-deploy build.
- Confirmed cause: at 08:19:47Z a burst of 31 acknowledgements arrived; 4 hit the by-design guard "Acknowledge routing already in flight for this file; redeliver" and returned HTTP 500 (warn-level log). Pub/Sub retried after the sub's 30s `minimumBackoff`, so oldest-unacked reached ~35s. All 4 were acked on retry.
- Confirmed: the 4 flapping subs are all push subs to Cloud Run. sftp and shopify have a 20s ack deadline and 30s min backoff; both snap_adapter subs have a 300s ack deadline and 10s min backoff.
- Confirmed: monitor warn is 30s and critical 60s, in `observability/iac/projects/bifrost-observability/monitors.tf`, and its message assumes a ~20s deadline for every sub.
- Not verified: the cause of the other 12 firings (shopify/snap_adapter), including a 2h Warn on snap_adapter sales_order on Sep 30 (247s peak).

## Outcome
Benign, by-design redelivery. The warn threshold (30s) equalled the sftp/shopify retry backoff (30s). Retuned to warn 90s / critical 180s and fixed the message (observability#59, applied and verified live). Also codified a console-added PURDYFIGG filter on the error-rate monitor so the apply didn't revert it (#58). Correction to the first "deploy rollover" reply posted in the thread.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790929663896889
- Monitor: https://app.datadoghq.com/monitors/323648859
- PRs: https://github.com/gfs-bifrost/observability/pull/59 , https://github.com/gfs-bifrost/observability/pull/58
