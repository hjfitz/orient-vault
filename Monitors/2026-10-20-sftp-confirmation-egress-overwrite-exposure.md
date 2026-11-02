---
tags: [datadog-triage]
date: 2026-10-20
monitor: "[FUSE][SFTP Connector] Confirmation egress overwrite exposure (possible lost update)"
service: sftp-connector
business_id: STUBBLE
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792488147112429?thread_ts=1792487045.152229&cid=C099WKQTE8G"
opened_at: "2026-10-20T09:16:35Z"
resolved_at: "2026-10-20T09:22:27Z"
minutes_spent: 6
severity_assessed: P3
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# SFTP egress overwrite-exposure Warn on prod: a duplicate re-announcement burst, no lost update

## Fired
Monitor 306134015 went to Warn on `@env:prod` at 09:16:35Z, its first prod firing in 30 days. The query counts `@appendedToExisting:true` egress window upserts in 1h, with warn above 10 and critical above 50. Datadog posted no Slack message for this Warn, so the verdict went in the INC-40-linked thread (parent 1792487045.152229), which already had the open "duplicate SFTP files?" question.

## Investigation
- **Prod build `7071412` already guards against lost updates.** `storage.service.ts` `upsertWindowFile` saves with `ifGenerationMatch`, retries up to 5 times on a 412, and dedupes rows within the window. The monitor text, which says the read-append-save is non-atomic, is out of date.
- **Appends:** 20 today against 1 in the previous 7 days (2026-10-15). 17 of today's were at 09:15. In both 09:15 files, each write's `existingBytes` equals the previous write's `resultBytes`, so no write started from a stale copy. A read-only `gcloud storage ls` gives final sizes of STUBBLE 0915 = 4146 bytes and EPARFUM 0915 = 2893 bytes, the last logged `resultBytes` for each.
- **Burst size:** between 09:15:35 and 09:15:46Z, STUBBLE received 49 messages covering 71 order refs, and EPARFUM received 4.
- **The burst was all duplicates.** All 71 STUBBLE refs were already in earlier window files today (06:08–08:28Z). The 4 EPARFUM refs were already in the 08:50 file.
- **Comparison with yesterday:** today 71 of 89 STUBBLE refs and 4 of 4 EPARFUM refs went to more than one file. On 10-19 the count was 0, apart from 1 EPARFUM PO.
- **Same-minute duplicates were already dropped:** the row dedupe removed them at STUBBLE 06:09 (5 rows) and 08:06 (4), and EPARFUM 08:50 (7, two writes).
- **Write contention:** there were 174 "Egress window write raced" retries (171 STUBBLE, 3 EPARFUM). 36 STUBBLE messages ran out of retries with a 412 (`Confirmation write failed irrecoverably`). Their 52 records were published to confirmation_data_failure: replay-service holds 52 STUBBLE `goods_out_confirmation` failures created at 09:15Z, all with 0 attempts.
- **Earlier write failures:** none in the previous 8 days.
- **After the burst:** no egress writes, retries or failures after 09:16Z.

### Not established
- **What re-sent the 09:15 burst.** Sample correlation `b3c6038e`: collector_service stored it again at 09:15:34. snap-polling-service has no log for that correlation after 08:22, and there was no STUBBLE "failing open" log in the 09:00 hour. So the burst is not proven to be the poller fail-open, and a Pub/Sub redelivery is possible but unchecked.
- **Effect on snap-adapter:** whether the 52 failure records stop it clearing those outbound-queue rows.

## Outcome
Real but minor, P3, a knock-on of INC-40. No data was lost or overwritten.
- **Duplicate rows:** STUBBLE and EPARFUM have 09:15 window files that contain only duplicate rows. Customers will collect them once the SFTP VM is back.
- **Do not replay:** the 52 held STUBBLE failures are duplicates, and replaying them would add more duplicate rows.
- **Follow-up (owed):** retune and reword the monitor so it tracks 412 retries running out instead of appends.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792488147112429?thread_ts=1792487045.152229&cid=C099WKQTE8G
- Monitor: https://app.datadoghq.com/monitors/306134015
- Incident: INC-40 (https://gfsdeliver-eng.slack.com/archives/C0CAEGABJBF)
