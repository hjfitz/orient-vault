---
tags: [datadog-triage]
date: 2026-10-21
monitor: "[FUSE][Snap Adapter] API latency threshold breached"
service: snap-queue-polling-service
business_id: 
snap_instance: ilg001
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792573769566529"
opened_at: "2026-10-21T09:08:08Z"
resolved_at: "2026-10-21T09:11:00Z"
minutes_spent: 3
severity_assessed: P3
flapping: true
outcome: vendor
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: open
---
# ilg001 latency was 54s after the 404 window and is settling toward about 2s

## Fired
Monitor 179927768 went to Warn for the ilg001 group (avg over 20m > 2000ms, value 3871).

## Investigation
- Error-rate window 08:40–08:50Z: 24 errors, all snap-polling-service `Outbound queue fetch failed`/`SNAP request failed`. HTTP 404 on GET /v2/snapoutbound at ilg001liveapi.snapfulfil.net.
- Every poll from 08:46:03 to 09:06:04Z failed: 60 fetch failures across DESPATCH/RECEIPT/STOCK_MOVE for DOCKBAY and MANUCURIST, the only businesses on ilg001 (get-snap-connection). PHLUR is on ilg005 and INDU on ilg002.
- The 404 body is an IIS HTTP.sys HTML "Not Found" (server Microsoft-HTTPAPI/2.0), not Snap's JSON. Neither service has deployed since 10-20 (poller 1b834b8, adapter dbed308). The 7-day log history has no earlier 404s.
- snap_adapter, 09:03:59–09:04:00Z: 8 distinct DOCKBAY sales orders failed (failureMode snap_api_error, transient:false, 404 on /v2/shipments). All 8 are held in replay-service prod with attempts 0: UK-909425, 909430, 909431, 909432, 909434, 909435, 909436 and 206-7860177-0345162. UK-909436 (DOCK986817590CD) checked in Snap: "No matching entity". The last DOCKBAY create succeeded at 08:14:47Z.
- create_data_failure: send_request_count was 6 at 09:04Z, carrying those 8 records. UK-909420 at 03:03Z is unrelated (City over 30 chars).
- Latency (snap.poll.request.latency.avg): ilg001 was about 20–35ms from 08:56 to 09:06 (fast 404s), then 54.3s at about 09:08, 9.9s, 2.1s and 1.9s. Baseline is about 70ms. ilg002–005 stayed at 70–250ms. The 07:10–07:20Z maintenance hit every host (15–107s).
- Direct probes at about 09:08 (DOCKBAY creds, read-only): snaplookups, snapoutbound (including the poller's exact filter/$top) and shipments returned 200 in 1.3–14s. DNS: every ilg host resolves to 209.143.134.157 (host-header routing).
- Not established: why Cloud Run got HTTP.sys 404s while the workstation got 200s, and whether this is left over from the cluster change. The 404 classed non-transient is a possible our-side classification gap (not verified in code).

## Re-fire 10:22Z (Warn, 2120ms; 2 further firings folded in)
- ilg001 `snap.poll.request.latency.avg` has held at 1.3–2.5s since 09:15Z, and the last point is 1.6s. Yesterday's 08–11Z window was mostly 70–300ms. ilg002–005 are at 50–250ms. There was a brief spike on all hosts at about 10:28Z: ilg001 6.9s, ilg003 1.8s, ilg005 1.5s.
- Direct probe at about 10:25Z: 5 ilg001 `snaplookups` calls returned 200 in 1.55–2.04s. ilg002 round trips took about 60ms.
- No `HTTP Error 404` or `status code 404` logs, and no DOCKBAY or MANUCURIST errors, in snap-polling-service or snap_adapter since 09:06:30Z. The 96 `SNAP request failed` logs in that window are BYOMA, EPARFUM, WILDSMITH, STUBBLE and CHAMPO, all on other hosts.
- DOCKBAY created 13 sales orders in Snap at 10:06:54–10:07:04Z (UK-909433 to UK-909456). MANUCURIST has had no snap_adapter traffic in 7 days.
- In replay-service prod, the 8 DOCKBAY records are still held at attempts 0, and there are no new DOCKBAY or MANUCURIST failures. The other failures today are PURDYFIGG (Email MANDATORY) and WILDSMITH (data), which are unrelated. None of the 8 refs has an `Entity created in SNAP` log.
- Not established: why ilg001 is about 20x slower than the other hosts, or when it will recover.

## Escalated to Alert 11:01Z (value 5116ms, over the 5000ms alert threshold)
- Cause of the Alert: one short ilg001 spike to 15.3s and 26.3s just before 11:00Z. Either side of it, `snap.poll.request.latency.avg` sat at 1.5–4s from 10:00Z, and the last points are 1.7s and 2.2s, so it is not trending worse. Other prod hosts also rose at about 11:00Z (ilg005 5.4s, ilg002 1.4s, ilg003 1.3s).
- Direct probe at 11:04Z: 5 ilg001 `snaplookups/RECSTATUS` calls with DOCKBAY creds all returned 200, in 1.30–2.45s.
- From 10:20Z, snap-polling-service and snap_adapter logged no 404, Not Found, fetch-failed, timeout or 5xx for ilg001, DOCKBAY or MANUCURIST. The only matches were PURDYFIGG `Consignment StU not found` warns.
- DOCKBAY created 15 sales orders in Snap between 10:51:30 and 11:02:25Z (UK-909338, 909437–909469, 205-8748194-4742705).
- The 8 orders held at 09:04Z are still at attempts 0 in replay-service prod. None of them has any snap_adapter log since 09:05Z, so they have not been replayed.
- New DOCKBAY hold UK-909462 at 11:01:56Z: `create.wms_precheck`, ShipAddress.City over 30 characters. This is a data issue unrelated to ilg001, the same class as UK-909420.
- Seen while investigating but outside ilg001: PURDYFIGG (site 0010, ilg005) had four 599 retries at 11:02:14–16Z. Its 13 `Email MANDATORY` holds for #6565591 repeat about every 5 minutes.
- The PURDYFIGG retries timed out on ilg005, and Pub/Sub redelivered them as `Entity already exists`. That is covered in its own record, Monitors/2026-10-21-platform-error-rate-ilg005-purdyfigg.md. By 11:03:25Z the ilg001 monitor had gone back to Warn at 4992ms.
- Not established: why ilg001 is slow.

## Outcome
Vendor (SnapFulfil ilg001), P3. At 11:04Z, the escalation to Alert was answered in the thread with @fuse-support pinged: replaying the 8 is still safe and they are still unreplayed, and UK-909462 needs its City fixed (https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792580670056189). At 09:11Z @fuse-support was told to replay the 8 held DOCKBAY sales orders once ilg001 was stable. At 10:25Z the advice changed: ilg001 is slow but error-free and accepting writes, so they should replay now. @fuse-support was re-pinged. The record stays open until the 8 are replayed. No ticket.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792573769566529
- Re-fire thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792578203835849
- Verdict reply: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792578302634929?thread_ts=1792578203.835849
