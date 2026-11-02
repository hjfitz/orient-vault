---
tags: [datadog-triage]
date: 2026-10-14
monitor: "[FUSE][Platform] Pub/Sub ack-deadline headroom eroding (standard subscriptions)"
service: tracking-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url:
opened_at: "2026-10-14T19:51:39Z"
severity_assessed: P4
flapping: false
outcome: false_positive
escalated_to:
ticket:
session_id: 4fc06c6b-d424-4da8-b551-fb874e9c6e96
status: open
---
# Five tracking-service prod subs in Alert: the cutover's intentional ingest hold (503), downtime already set, no Slack thread

## Fired
Monitor 323648859 (`max(last_10m)` of `gcp.pubsub.subscription.oldest_unacked_message_age` by subscription, prod, `> 180` alert; P3; Terraform-managed) went Alert on `tracking-service.prod.create_record.sales_order.v1.sub` at 19:51:39Z. Enumerated every group: five `tracking-service.prod.*` subscriptions, no others. There is no #bifrost-notifications thread for this monitor: a scheduled downtime (id `12967c01-85c8-4064-a8d7-7a2f54885d03`, scope `subscription_id:tracking-service.prod.*`, started 19:06:04Z by Harry, until 2026-10-15 14:00Z, note "tracking-service prod cutover: ingest is held, so a backlog is expected") suppresses its notifications.

## Investigation
- What it measures: age in seconds of the oldest unacknowledged message on a subscription (monitor query above), not a direct ack-deadline reading. These subs have `ackDeadlineSeconds: 30`, retry backoff 10s-600s, 7-day retention, no deadLetterPolicy (`gcloud pubsub subscriptions describe`).
- Which groups, and how far (max oldest-unacked age since 19:30Z, `top()` scalar query): `confirmation_ready.goods_out_confirmation` 466s, `confirmation_made.goods_out_confirmation` 435s, `create_record_request.sales_order` 291s, `create_record.sales_order` 272s, `create_acknowledge.sales_order` 259s. Every other subscription in the monitor's scope was 0 over the same window (the full list of 154 groups was read; the other tracking-service subs and all fuse-tracker, snap_adapter, dedupe, collector, sftp-connector, shopify subs showed 0).
- Trend on the named sub (1-min series): age 0, 32, 92, 152, 212, 272s at 19:46-19:51Z; undelivered messages steady at 2. Age rises 60s per minute, so nothing is being acked.
- Cause: all push responses to `tracking-service.prod.*` over 19:40-19:55Z are `remote_server_5xx` (no other response class). Cloud Run `tracking-service-api-prod` request_count is 503 only: 24, 997, 395 per 5 min from 19:40Z; latency about 1.4-1.6 ms; 1 instance. Its logs carry "ingest held; answering pushes with 503 so Pub/Sub keeps them" (12 logs, 19:42:05Z to 19:53:15Z). Live service config has `INGEST_HOLD=true` on revision `tracking-service-api-prod-00001-h9w` (Ready 19:40:33Z). origin/main `iac/env/tracking-service/prod.tfvars` has `ingest_hold = true` and `dead_letter_enabled = false`, and `docs/cutover.md` step 1 describes exactly this: new stack applied held, 503 on `/events/v1/*`, backlog grows.
- Redelivered, not lost or dead-lettered: Pub/Sub retries a 5xx push with backoff; undelivered stays 2 on the named sub (not falling); no deadLetterPolicy on the sub, and the `dlt.sub` subscriptions read 0 age.
- Consumer health: nothing unhealthy; the 503s are the hold working. The Cloud Run service was first created at 19:40Z (no tracking-service data before then); the prod Deploy run 38620865453 (started 19:06:32Z) was still `in_progress` at triage.
- Shared cause: all five groups sit behind the same held API. Other consumers of the same topics are not affected: the fuse-tracker (legacy, authoritative until cutover step 7) subs, snap_adapter, dedupe and collector sales_order subs all read 0 since 19:30Z.
- Flapping: this group has no earlier firing (the subs did not exist before 19:40Z). The monitor itself had 46 events since 2026-10-07 (other subs: sftp-connector 10-13, snap_adapter 10-12, fuse-tracker 10-07).
- Related, not the same monitor: `[FUSE][Egress] Confirmation delivery lagging` (303425507) posted to #bifrost-notifications at 19:52Z for the two goods_out tracking-service subs (messages 1792007571.949379 and 1792007574.058379). The 19:06Z downtimes cover monitors 302536093, 323648859, 323648858 and 302536090 only, so 303425507 is not muted. Same cause by the group names; its own thread was not triaged.

Not established: how long the hold lasts (cutover plan owner decides; the downtime ends 15 Oct 14:00Z); whether prod export/import (docs/cutover.md step 2-3) has run (not checked); why `ack_message_count` is non-zero on eight tracking-service subs (confirmation_made pick/pack, RGA) while only 5xx push responses are recorded (possibly filter auto-acks, not checked); metric lag means the last point is about 19:51Z.

## Outcome
Expected behaviour of the planned prod cutover hold, P4, no customer-visible impact established (legacy fuse-tracker stack still carries the flow). Nothing changed, no ticket. No Slack reply posted: the monitor has no thread (muted by the downtime and no `source:alert` events today). Left status open because the monitor stays in Alert until the hold is released or the downtime lapses. If the hold is not meant to outlive 15 Oct 14:00Z, the downtime needs extending, and monitor 303425507 needs one too or it keeps posting.

## Links
- Monitor: https://app.datadoghq.com/monitors/323648859
- Downtime: https://app.datadoghq.com/monitors/downtimes?id=12967c01-85c8-4064-a8d7-7a2f54885d03
- Related Egress alert thread: #bifrost-notifications ts 1792007574.058379
- Runbook: tracking-service `docs/cutover.md`
- Prior record: 2026-10-13-pubsub-ack-deadline-headroom-sftp-connector-create-acknowledge.md

## Update 2026-10-14 20:15Z: sixth group, `create_data_failure.sales_order`, same cause

Monitor 323648859 group `subscription_id:tracking-service.prod.create_data_failure.sales_order.v1.sub` went Alert at 20:11:39Z (group state `lastTriggeredTs` 1792008699). Verdict unchanged: false_positive, P4, the intentional `INGEST_HOLD=true`.

- Push responses: the sub's `push_request_count` by response class over 19:44-20:12Z is only `remote_server_5xx` / `unreachable_5xx_error_503` (4, 2, 1, 1, 2 per minute from about 20:07Z), no other class. Oldest unacked age 0 until 20:07Z, then 134, 194, 254, 314, 367s; undelivered steady at 1. The sub was idle until one message arrived at about 20:06Z, and the hold is 503ing its retries (not a consumer fault). Message content not read.
- Hold still in effect: `gcloud run services describe tracking-service-api-prod` at 20:14Z gives `INGEST_HOLD=true`, latest ready = latest created = `tracking-service-api-prod-00001-h9w`, 100% traffic, Ready since 19:40:33Z. Datadog logs (`service:tracking-service*`, "ingest held") show 32 lines, 19:42:05Z to 20:13:46Z, so it is still emitting.
- Downtime did mute it: no notification was sent. All six alerting groups of 323648859 have `lastNotifiedTs` null, there are no `source:alert` events for monitors 323648859, 302536093, 302536090 or 323648858 since 19:00Z, and #bifrost-notifications has no Datadog post after the 19:52Z ones. The downtime scope is `subscription_id:tracking-service.prod.*` (audit event 19:06:04Z) and `create_data_failure` shares the `tracking-service.prod.` prefix, so topic family is irrelevant. The monitor reads Alert in the UI and API because muting silences notifications, not state.
- Other monitors from the same cause: `303425507` Egress confirmation lagging is the only one that is posting (two groups, goods_out ready/made, events 19:51:47Z, threads already exist). `302536093` oldest unacked >600s is Alert on five tracking-service groups (Warn on create_data_failure at 367s) and `302536090` backlog is Warn on create_record_request; both silent. `323648858` is OK. Ages now: goods_out ready 1666s, made 1636s, create_record_request 1492s, create_record 1472s, create_acknowledge 1460s. Every other prod subscription (164 groups read) is 0, including `audit-service.prod.*`, whose group entries came back redacted by the tool but whose ages read 0. Other prod monitors in Alert (Dock and Bay go-live D2/D3/D7-D11, PF go-live T3, CCP stranded actions) have queries on `fuse.*`/`snap.*`/CCP metrics, nothing on tracking-service or Pub/Sub age.

Not established: the downtime's own definition via API (v2 downtimes are not readable with the available SDK; the scope comes from the audit event); how long the hold lasts; content of the create_data_failure message.
