---
tags: [datadog-triage]
date: 2026-10-20
monitor: "[FUSE][Egress] Confirmation delivery lagging (303425507) + [FUSE][Platform] Pub/Sub backlog building (302536090)"
service: tracking-service
business_id:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792499285311009"
opened_at: "2026-10-20T09:26:47Z"
resolved_at: "2026-10-20T12:38:17Z"
minutes_spent: 192
severity_assessed: P4
flapping: false
outcome: self_resolved
escalated_to:
ticket:
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# Confirmation-lag and Pub/Sub backlog monitors: INC-40 knock-on, cleared

## Fired
The monitors were still showing Alert (303425507) and Warn (302536090) after INC-40, the GCP zone-b outage, was resolved. Both read OK at about 12:40Z.

## Investigation
- A scalar query over the last 30m (146 subs) showed every `*confirmation*` sub, and every prod sub, at 0 on the last point.
- A 3h max query picked out the groups that had fired:
  - `tracking-service…goods_out_confirmation.v1.dlt.sub`: 203 undelivered, age 10,750s.
  - `api-gateway.prod.confirmation_ready.so.v1.sub`: age 2,624s.
  - `api-gateway.prod.confirmation_ready.po.v1.sub`: age 2,264s.
  - `bifrost.prod.snap_poll_customer.v1.sub`: 443.
  - `tracking-service…goods_out_confirmation.v1.sub`: 371.
- **DLT sub (tracking-only, a false-positive class).** It held 8 from about 09:18Z and rose to 203 around 12:05Z. After the redrive it read 0 on every 1-min point from 12:22Z. The 15m max window held the alert until it cleared (302536090 at 12:36:10Z, 303425507 OK by 12:40Z).
- **fapi so/po subs (customer-facing).** They stalled from 09:45Z to 10:30Z and recovered at 10:41Z and 10:45Z (alert events).
  - In the `rest_connector` logs, revision `b8870c5` started at 09:43Z with `Cache service initialization failed`.
  - From 09:43Z to 10:22Z it logged `Confirmation push accepted` but no `forwarded`, `processed` or `acknowledged`. Across that revision: 74 accepted, 54 forwarded, and all 54 forwarded were before 09:26Z.
  - fapi#179 (`1d7217351819`, "Start fapi on a cache-less remote config when Redis is unreachable") was deployed via Deploy run 39407058629 and went live at 10:23Z.
  - On the new revision, 85 confirmations were accepted and all 85 were forwarded, processed and acknowledged (10:24Z to 12:06Z).
  - About 6 messages (peak undelivered: 5 so, 1 po) were delayed by up to about 45 min. Both subs drained to 0.
- Not established: the exact call inside the old revision that hung after `No cached connector IDs for business, fetching from API`. The logs show where it stopped but not why.

## Outcome
Self-resolved, P4, no action. The customer-facing fapi stall was already fixed by fapi#179 during INC-40. The DLT groups are the known `*dlt*` false-positive class, and excluding them from these generic monitors is the follow-up already proposed.

## Links
- Slack thread (303425507): https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792499285311009 (reply ts 1792499896.492509)
- Slack thread (302536090): https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792499848065179 (reply ts 1792499897.986269)
- Incident: INC-40
