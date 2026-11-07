---
tags: [datadog-triage]
date: 2026-11-07
monitor: "[FUSE][SFTP Host] Audit events not published (sftp_login)"
service: sftp-host
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794026127045779"
opened_at: "2026-11-07T04:34:01Z"
resolved_at: "2026-11-07T04:38:00Z"
minutes_spent: 4
severity_assessed: P4
flapping: false
outcome: self_resolved
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# Two sftp_login audit events timed out at publish at 04:30:03Z; both are in the audit log, nothing since

## Fired
Monitor 335786581 (`sum(last_15m) of fuse.sftp_host.audit.publish_failed{environment:prod} by {kind,reason} > 0`, P2, Terraform-managed, published from draft on 2026-11-02) alerted for group `kind:sftp_login,reason:timeout`. Alert post: parent ts 1794026127.045779, no reply when checked at about 04:37Z. The monitor text says a failed publish means the event is lost and nothing retries it.

## Investigation
- Failures: `fuse.sftp_host.audit.publish_failed` for `kind:sftp_login,reason:timeout` is 2 in the 04:30 minute and 0 in every other minute from 03:30 to 04:36. The log `service:sftp_host @environment:prod "audit event not published"` has exactly 2 lines in 15 days (flex + indexed), both 04:30:03Z on host sftp-host-prod-782n, `error: context deadline exceeded`, event ids c32d7ac0-d42e-50ae-872b-71faa2927acd and 45c00d31-599c-5dc3-a825-7a37bb33067b. Not a flapper; first time this monitor has alerted.
- Not lost: `audit-search` kind sftp_login 04:20-04:40Z returns both event ids, tenant EPARFUM, occurredAt 04:30:00.210Z / 04:30:00.205Z, receivedAt 04:30:10.319Z / 04:30:10.315Z (about 10s after the login; the host gave up at 3s). Every other sftp_login event in 04:19-04:35Z, 58 + 86 events across the two searches, is stored with receivedAt 50-110 ms after occurredAt, apart from the slow ones below.
- Slow-but-delivered publishes (receivedAt minus occurredAt) before and after: 04:06-04:09 all 50-110 ms; 04:20:26 about 480 ms; 04:22:00 and 04:22:27 about 800-830 ms; 04:27:00 two at about 550 ms; 04:30:00 two at 10.1s; 04:31:00 two at about 710 ms; 04:32:00 to 04:35:35 all 50-130 ms. So audit publish/ingest latency was intermittently slow from about 04:20 to 04:31 and normal for at least 4 minutes since. Slow events at 04:27 and 04:31 were on host g1b9 and the failed pair on 782n (host mapping from sftp_host login logs); the 04:20-04:22 events were not mapped to a host.
- Logins are succeeding: `sftp login failed` has one line in 6h (03:57:14Z, user `support`, `closed_before_auth`, host lt79, before the alert window). 247 `sftp login` info lines 03:50-04:35Z, and accepted logins continue at 04:30-04:35 (audit events outcome accepted for EPARFUM, WILDSMITH, STUBBLE, MANUCURIST).
- File ingestion: sftp_connector logged `File routed` at 04:35:06Z and `POST /events/v1/create_acknowledge - 204` at 04:35:26Z; 19 create_acknowledge calls 03:30-04:35. Only 2 `File routed` lines in the hour (03:34:25 and 04:35:06) so this is a low-volume check.
- Held records: `replay-list-failures` production createdAt 2026-11-07 returns total 0.
- Dependencies: audit publish goes to Pub/Sub topic `audit.prod.fuse.v1` (monitor text), consumed by audit-service (`lookup-service audit-service`: OIDC push, stores once under _id = eventId). `gcp.pubsub.topic.send_request_count` for audit.prod.fuse.v1 shows 3-12 requests per minute across 03:30-04:35 with no gap. The only topic with a send-latency series in the window (sftp-parcel-inbound-files, 5-min buckets) reads 21-29 ms avg 04:11-04:35.

### Link to the Snap poller latency step (record 2026-11-07-snap-poller-api-latency-all-hosts-0429z.md)
- Timing: Snap poller latency stepped at 04:25-04:26Z and is still 4.1-4.2s per request on all five hosts in the 04:32-04:36 buckets (ilg005 3.9-4.0s in the last two). Audit publish slowness began about 04:20 (before the step), peaked at 04:30, and is back to normal since 04:32 while Snap is still slow. The two series do not move together.
- Error text: sftp_host `context deadline exceeded` on a Pub/Sub publish; the Snap side has no failures and no error text at all.
- Other outbound calls: a search for timeout/deadline text in `@error`, `@err` and `@error.message` on all prod logs since 04:00Z returns only these two sftp_host lines. `fuse.mongo.latency.avg` (dedupe 9-21 ms, shopify-connector 7-21 ms) and `fuse.postgres.latency.avg` (config-service 3.7-156 ms, no step at 04:25) show no step in 5-minute buckets; replay mongo (132 ms) has no earlier points to compare. Warn/error log volume per minute shows only a repeating 5-minute pattern, no new messages from 04:25.
- Conclusion: contradicted as a single shared cause on the evidence above; a brief shared network or platform blip around 04:30 is not excluded.

## Outcome
P4, self-resolved. The monitor's claim that the event is lost did not hold for these two: both were stored once, about 10s late. No customer impact seen: logins accepted, a file routed after the alert, nothing held. The monitor will clear when its 15-minute window empties (about 04:45Z). Reply drafted for the watching session to post with broadcast; no ticket, since there is no defect found and a single occurrence.

Not established:
- Which hop was slow for the failed pair and the 0.5-0.8s ones: the host's publish call to Pub/Sub or Pub/Sub push delivery to audit-service. `receivedAt` only shows when audit-service stored it; the sftp_host and audit-service logs for the publish call were not queried for retries.
- Why the host's context deadline fired at 3s yet the message arrived 10s after login (whether the client kept sending after giving up).
- Cause of the 04:20-04:31 latency; sftp-host is not in the Fuse MCP catalog (`lookup-service sftp_host` not found), so its code and publisher settings were not read.
- Whether other prod Pub/Sub publishers were slow at the same time: GCP topic latency metrics have only one topic series in the window, at 5-minute resolution.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794026127045779
- Monitor: https://app.datadoghq.com/monitors/335786581
- Related record: 2026-11-07-snap-poller-api-latency-all-hosts-0429z.md
