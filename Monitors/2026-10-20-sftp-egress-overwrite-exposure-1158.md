---
tags: [datadog-triage]
date: 2026-10-20
monitor: "[FUSE][SFTP Connector] Confirmation egress overwrite exposure (possible lost update)"
service: sftp-connector
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792487045152229"
opened_at: "2026-10-20T11:59:35Z"
resolved_at: "2026-10-20T12:40:55Z"
minutes_spent: 41
severity_assessed: P3
flapping: false
outcome: real_minor
escalated_to:
ticket:
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# SFTP egress overwrite-exposure Warn on prod at 11:59Z: second INC-40 burst, no clobber

## Fired
Monitor 306134015 went to Warn on `@env:prod` at 11:59:35Z with 20 appends to existing window files since 11:00Z. All were between 11:58:36 and 11:58:40Z in the EPARFUM, SPORTLUX and BYOMA `2026-10-20-1158` files, during the second INC-40 duplicate-confirmation burst. This is the second Warn today; the first was at 09:16Z and recovered at 10:16Z. Datadog posted neither Warn into the channel, so the verdict went into the thread that holds the 09:16 verdict.

## Investigation
- Lost-update recipe over all prod `Egress window upsert` logs today: 115 writes (STUBBLE 65, EPARFUM 30, SPORTLUX 17, BYOMA 3), 40 of them appends.
  - 0 cases of two real saves (`resultBytes > existingBytes`) from the same `@existingBytes` on one `@filePath`.
  - 7 same-base pairs exist. Each pairs one no-op (`resultBytes = existingBytes`) with one real save. At sha 7071412, `storage.service.ts` returns before `file.save` when every incoming row is already present, and real saves use `ifGenerationMatch`.
- Chain check: all 40 appends start from a `resultBytes` that an earlier real save on the same file logged.
- Final GCS sizes match the last logged size:
  - SPORTLUX `FUSE_DD2AF79592/.../2026-10-20-1158-confirmation.csv` is 11,132 bytes.
  - EPARFUM `FUSE_C062E5C41B/.../.archive/2026-10-20-1158-confirmation.csv` is 8,762 bytes, archived at 11:59:24Z.
- Contention: 44 "write raced" retries (EPARFUM 25, SPORTLUX 19) and 13 `Confirmation write failed irrecoverably` 412 errors (EPARFUM 11, SPORTLUX 2), between 11:58:37 and 11:58:40Z.
- Refs on the failed attempts:
  - EPARFUM: 17 distinct refs. All 17 appear in "Confirmation file write started" logs earlier today, in the 10:24, 10:30, 10:34, 10:36, 11:06 and 11:08 files.
  - SPORTLUX: the refs on the failed attempts appear in the 11:42, 11:52 and 11:54 files.
  - Before 11:58:35Z, write-started and upsert counts match 1:1 (EPARFUM 19/19, SPORTLUX 7/7), with 0 errors for EPARFUM, SPORTLUX and BYOMA.
- No egress upserts, retries or failures since 11:58:40Z.

Not established:
- BYOMA's 1158 object was not found by name in `sftp-connector-prod-storage`. It had one real save (0 to 4,478 bytes) and one no-op, so it had no clobber exposure.
- What re-sent the confirmations at 11:58Z.

## Outcome
Real but minor. No clobber and no lost order. The failed writes duplicate orders already delivered, so their replay-service failure records must not be replayed. Follow-up, already raised at 09:16: retune the monitor to track 412 retries running out rather than appends, because the monitor text still describes a non-atomic write that this build no longer has.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792487045152229
- Verdict reply: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792500055383639?thread_ts=1792487045.152229&cid=C099WKQTE8G
- Incident: INC-40
