---
tags: [datadog-triage]
date: 2026-10-20
monitor: "[FUSE][Tracking Service] Message held in a dead-letter subscription"
service: tracking-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792488447436509"
opened_at: "2026-10-20T09:26:05Z"
resolved_at: "2026-10-20T12:37:00Z"
minutes_spent: 191
severity_assessed: P4
flapping: false
outcome: self_resolved
escalated_to:
ticket:
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# Tracking DLT monitor still Alert after INC-40 redrive; DLT now 0

## Fired
Monitor 332917925 (P2 tag) triggered once at 09:26Z on `tracking-service.prod.confirmation_data_failure.goods_out_confirmation.v1.dlt.sub` (8 held). There was no re-notify. It was still Alert at 12:36Z.

## Investigation
- The DLT metric read 0 until 09:23Z, then 8 until about 11:59Z, then rose to 203 and held there until 12:21Z. It has read 0 on every 1-minute point from 12:22Z to 12:31Z (the latest point). So the `cmd/redrive` cleared all 203, the earlier 8 included.
- The other 19 `tracking-service.prod.*dlt*` subscriptions read 0 on every point for the last 3h.
- Monitor events over 7 days show only that one trigger, so it is not flapping. It is still Alert because the `max(last_15m)` window holds the pre-redrive points of 203.
- There has been one tracking-service error since the redrive. At 12:35:07Z, `store failed; nacking for redelivery` was logged on create_record_request/sales_order with Firestore `Unauthenticated` (a credential token minted too late). That is one nack, and a message is only dead-lettered after 5 failed pushes.
- Not established: whether event 22062681442639849 has since been applied. A log search for that id found nothing.

## Outcome
The DLT was cleared by the manual redrive, and the monitor should recover once the 15m window rolls past 12:22Z. No further redrive is needed and no ticket was filed.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792488447436509
- Verdict reply: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792499820471039
- Incident: INC-40 https://gfsdeliver-eng.slack.com/archives/C0CAEGABJBF
