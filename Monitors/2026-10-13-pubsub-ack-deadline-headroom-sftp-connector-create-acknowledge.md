---
tags: [datadog-triage]
date: 2026-10-13
monitor: "[FUSE][Platform] Pub/Sub ack-deadline headroom eroding (standard subscriptions)"
service: sftp-connector
business_id: STUBBLE
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791884564362559"
opened_at: "2026-10-13T09:41:39Z"
resolved_at: "2026-10-13T09:46:30Z"
minutes_spent: 5
severity_assessed: P4
flapping: false
outcome: self_resolved
escalated_to:
ticket:
session_id: 4fc06c6b-d424-4da8-b551-fb874e9c6e96
status: resolved
---
# create_acknowledge sub hit 99s unacked: the same STUBBLE move failure, redelivered three times then acked

## Fired
Monitor 323648859 (`max(last_10m)` of `gcp.pubsub.subscription.oldest_unacked_message_age` by subscription, prod; warn 90, critical 180, P3) went Warn at 09:41:39Z on `sftp-connector.prod.create_acknowledge.v1.sub` with value 99s. Terraform-managed (`managed-by:terraform`); no change made.

## Investigation
- What it measures: GCP metric description, "age (in seconds) of the oldest unacknowledged message". Seconds since publish, not a direct ack-deadline measure. The sub has `ack_deadline_seconds = 20` and `retry_policy.minimum_backoff = "30s"`, no dead-letter block (`iac/projects/bifrost-sftp-connector/pubsub.tf` at deployed sha 28c514e, read via `gh api`), so one failed delivery reads about 30-60s.
- How far: 1-min series for the sub 08:30-10:15Z is 0 except 39 then 99, then 0. Hourly max over the previous 7d never exceeded 39s; 99s is the 7d high. 0 age and 0 undelivered at the last two points (09:40, 09:41Z). Highest 7d max across the monitor's other subscriptions is not comparable to this one (fuse-tracker subs reach 369-499s, snap_adapter sales_order 189s); not investigated.
- Redelivered, not lost: sftp_connector logs for correlationId `9bab3e37-46dc-442e-9baa-a858919ca2a0` show first receipt 09:35:04Z; `POST /events/v1/create_acknowledge` 500 at 09:35:09 (`Failed to move object in cloud storage`), 500 at 09:35:47 and 09:36:38 (`File routing deferred to an in-flight claim`), then 204 and `File routed` at 09:37:22Z, 138s after first receipt. `push_request_count` for the sub 09:25-09:50Z: 3 responses of 500 (1 + 2 across two 1-min buckets), 204 acks otherwise; `nack_requests` 1.
- Link to the 09:35Z alert: same correlationId as the STUBBLE record `2026-10-13-sftp-connector-file-routing-move-failed-stubble.md`. The 39 then 99 reading at 60s spacing is consistent with one message published about 09:35:04.
- Mechanism, from code at sha 28c514e (`core/file-routing/file-routing.service.ts`, `constants.ts`): `claim()` does SET-NX of a pending claim with `PENDING_CLAIM_TTL_MS` = 120_000. When the move throws, `markDone` is not reached; redeliveries get `lost_pending` and throw a retryable exception (HTTP 500) until the claim expires. One transient GCS failure therefore costs about 2 minutes of unacked time.
- Flapping check: monitor events in the last 3d are 5, all this monitor: `snap_adapter.prod.create_record_sales_order.v1.sub` on 10-12 (Warn 112s at 09:11Z, recovered 09:19Z, Triggered 189s at 09:26Z, recovered 09:36Z), then today's sftp-connector Warn. Different subscription each day.
- sftp_connector prod warn/error log patterns 09:00Z-now: `Record dropped` (51, 09:29Z), `Records failed CSV validation` (1), `File routing deferred...` (14, 09:29-09:36Z), plus the single `File routing failed` / `Error unhandled` at 09:35:09Z. Not examined beyond the pattern list.

- Re-check (later session, ~16:09Z): the correlationId `9bab3e37…` log chain matches the bot's reply exactly (three 500s at 09:35:09/09:35:47/09:36:38, 204 at 09:37:22Z). Sub age from 09:26Z to now, 2-min max: 19.5, 49.5 at 09:36-09:38Z, then 0 apart from isolated 0.5/21/14/1s points, all under the 90s warn. Zero sftp_connector prod `status:error` logs from 09:36Z to now. No reply posted; the bot's verdict stands.

Not established: whether Google Cloud Storage had a wider incident at 09:35Z; why the 10-12 snap_adapter sales_order firings occurred (not investigated); whether other 09:29-09:36Z deferred-claim deliveries also reached the monitor window (only the 9bab3e37 chain was traced).

## Outcome
Self-resolved, P4. Message acked 09:37:22Z, sub empty. Nothing moved, resent or edited. Suggestion for the sftp-connector owner, untested: release the pending claim when the move throws so the first 30s-backoff retry can proceed instead of waiting out the 120s TTL. No ticket filed.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1791884564362559
- Monitor: https://app.datadoghq.com/monitors/323648859
- Related record: 2026-10-13-sftp-connector-file-routing-move-failed-stubble.md
