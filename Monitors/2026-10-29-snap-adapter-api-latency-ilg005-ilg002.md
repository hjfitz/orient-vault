---
tags: [datadog-triage]
date: 2026-10-29
monitor: "[FUSE][Snap Adapter] API latency threshold breached"
service: snap-adapter
business_id:
snap_instance: ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793290406079019"
opened_at: "2026-10-29T16:12:08Z"
severity_assessed: P3
flapping: true
outcome: real_minor
session_id: 7198be0e-f4de-4cae-8e32-ef4ac0c4cdb9
status: open
---
# ilg005 and ilg002 Warn at 16:12Z/16:13Z: a 4-minute spike on all five Snap hosts, ilg002/005 back under 1s by 16:16Z

## Fired
Monitor 179927768 Warn (avg 20m > 2000ms): ilg005 2225.6ms (16:12:08Z), ilg002 2148.0ms (16:13:08Z). First firing of either host today; ilg001/003/004 flap daily.

## Investigation
- 10-min avg latency 10:00-16:00Z: ilg005 0.10-1.68s (max 1.68s at 10:20, the DB5 recovery bucket), ilg002 0.14-1.02s except 2.15s at 12:50. No step up after the 10:22Z recovery. The first sustained rise on either host is 16:10Z.
- 2-min avg 16:10-16:12Z: ilg005 8.2/8.2s, ilg002 5.3/3.2s, ilg001 12.0/11.5, ilg003 14.0/12.6, ilg004 11.7/10.6. All five hosts rose in the same buckets (also 16:06Z: ilg001/003/004 7.7-12.2s, ilg002 1.9s, ilg005 1.5s). 16:14Z: ilg002 0.27s, ilg005 0.78s (1.6s in the 2-min bucket), others 4.1-4.8s. 16:16Z: ilg002 0.13s, ilg005 0.20s, ilg001/003/004 2.9-3.6s.
- Shared shape, so not "ilg005 catching the post-update slowdown". ilg002's DB2 window was 28 Oct 10:00Z (Maintenance/2026-10-19 note); its poll success dropped to 0 at 10:10-10:20Z yesterday with 60 snap-polling 404 error logs against ilg002. No window is pending; DB5 (29 Oct 10:00Z) was the last.
- snap.poll.request minus .success = 0 on all five hosts every minute 16:04-16:16Z. snap-polling-service error logs since 10:30Z: 0.
- snap_adapter error logs 15:55-16:17Z: 132, all PURDYFIGG: 126 slot_timeout (transient), 6 schema_validation. Slot timeouts 16:10:41-16:12:33Z. PURDYFIGG creates per 2 min: ~75-93 to 16:05Z, 5 (16:06Z), 1 (16:10Z), 82 and 109 (16:12/16:14Z). A PURDYFIGG snap_adapter log from the DB5 window carries ilg005liveapi, so PURDYFIGG calls ilg005.
- 78 distinct slot-timeout records 16:00-16:17Z: 55 had a later created log at my check; the posted triage reply says all 78 are created (not re-verified by me).
- snap_adapter errors since 10:30Z: 133 total, PURDYFIGG 131 (126 slot_timeout, rest schema_validation), DOCKBAY 1, MANUCURIST 1. No 404s, no ilg005 recurrence.
- Businesses calling ilg005: from the DB5-window 404 logs (Monitors/2026-10-29-platform-elevated-prod-error-rate-1003.md): ABBOTT, EPARFUM, ESCENTRIC, PHLUR, PURDYFIGG, STUBBLE, WILDSMITH.
- 20 held DB5-window sales_orders (STUBBLE 11, WILDSMITH 6, PHLUR 3): not re-checked in this run beyond the 14:49Z note (no created log as of then).

## Not established
Why all five hosts spiked together (Snap platform, shared network, or our egress; Cloud Run/egress metrics not checked); whether Snap slowness or our 30s slot cap caused the slot timeouts; the 20 held orders' current state; direct probe (Fuse MCP 401).

## Outcome
Real minor P3: brief all-host latency spike, ilg002/005 recovered within ~4 min, no failed polls, transient PURDYFIGG create stall. Escalate if the all-host spike recurs or ilg002/005 stay above 2s.

## Links
- ilg005 Warn thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793290406079019
- ilg002 Warn thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1793290463294799
- Continuation of Monitors/2026-10-28-snap-adapter-api-latency-ilg003.md
