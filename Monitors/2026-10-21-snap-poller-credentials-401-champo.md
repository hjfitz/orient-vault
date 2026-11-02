---
tags: [datadog-triage]
date: 2026-10-21
monitor: "[FUSE][Snap Queue Polling Service] SnapFulfil rejecting credentials (401)"
service: snap-polling-service
business_id: CHAMPO
snap_instance: ilg003
channel: bifrost-notifications
thread_url: "https://gfs-engineering.slack.com/archives/C099WKQTE8G/p1792573662407479"
opened_at: "2026-10-21T09:06:23Z"
severity_assessed: P4
flapping: false
outcome: real_minor
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: open
---
# CHAMPO prod Snap API credential rejected (401) on first confirmation poll

## Fired
Monitor 326299823 (log alert, >5 "Outbound queue fetch failed" 401s per business in 15m) triggered for @businessId:CHAMPO at 09:06:23Z.

## Investigation
- 7d: all 24 poller `status code 401` logs are CHAMPO, 09:04:03Z–09:10:04Z, at every 2-min poll, and still occurring at the time of triage. No other business has any.
- Poll set: the "Skipping businesses with no confirmation-enabled connector" log listed CHAMPO through 09:02:03. CHAMPO was dropped from that list at 09:04:03, after the connector PATCH in Fuse UI at 09:02:48Z. The 06:58Z cust snapshot had confirmationsEnabled false, and it is true now. This was CHAMPO's first-ever poll, so there was no prior working state.
- Backend PUT /api/v1/backend/CHAMPO happened twice via Fuse UI (09:04:34Z, 09:04:41Z), and the 401s continued afterwards.
- Host is https://ilg003liveapi.snapfulfil.net/api (Snap DB 3, Poland), user FUSECHAMPO. A direct read-only probe of the outbound queue (top 1) returned 401.
- Not related to the 07:00–07:30Z Snap cluster change: the onset coincides with the business first entering the poll set.
- Impact: no CHAMPO record traffic in 14d (no sftp-connector, snap-adapter or dedupe record logs). It is pre-live, so nothing is blocked yet.

Not established:
- Whether the user doesn't exist on live or the password is wrong.
- The stored password contains a non-ASCII character (£), which could be an encoding mismatch in Basic auth. This is unverified.
- lookup-snap-instance reports 0 prod businesses on ilg003 despite CHAMPO being there, which suggests stale data in that tool.

## Outcome
Real-minor onboarding misconfig. @fuse-support pinged to get the correct FUSECHAMPO live credential from ILG/Snap and update the backend, or to disable confirmations until go-live. No config changed.

## Links
- Slack thread: https://gfs-engineering.slack.com/archives/C099WKQTE8G/p1792573662407479
- Verdict reply ts: 1792573891.816159
