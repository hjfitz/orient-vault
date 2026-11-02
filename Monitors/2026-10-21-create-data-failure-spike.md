---
tags: [datadog-triage]
date: 2026-10-21
monitor: "[FUSE][Platform] create_data_failure spike"
service: snap-adapter
business_id: DOCKBAY
snap_instance: ilg001
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792573644460409"
opened_at: "2026-10-21T09:06:07Z"
resolved_at: "2026-10-21T09:11:00Z"
minutes_spent: 5
severity_assessed: P3
flapping: false
outcome: vendor
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: open
---
# 6 publishes, 8 DOCKBAY records, all from ilg001 404s

## Fired
Monitor 302536087 went to Warn at send_request_count 6 over 15m.

## Investigation
- Error-rate window 08:40–08:50Z: 24 errors, all snap-polling-service `Outbound queue fetch failed`/`SNAP request failed`. HTTP 404 on GET /v2/snapoutbound at ilg001liveapi.snapfulfil.net.
- Every poll from 08:46:03 to 09:06:04Z failed: 60 fetch failures across DESPATCH/RECEIPT/STOCK_MOVE for DOCKBAY and MANUCURIST, the only businesses on ilg001 (get-snap-connection). PHLUR is on ilg005 and INDU on ilg002.
- The 404 body is an IIS HTTP.sys HTML "Not Found" (server Microsoft-HTTPAPI/2.0), not Snap's JSON. Neither service has deployed since 10-20 (poller 1b834b8, adapter dbed308). The 7-day log history has no earlier 404s.
- snap_adapter, 09:03:59–09:04:00Z: 8 distinct DOCKBAY sales orders failed (failureMode snap_api_error, transient:false, 404 on /v2/shipments). All 8 are held in replay-service prod with attempts 0: UK-909425, 909430, 909431, 909432, 909434, 909435, 909436 and 206-7860177-0345162. UK-909436 (DOCK986817590CD) checked in Snap: "No matching entity". The last DOCKBAY create succeeded at 08:14:47Z.
- create_data_failure: send_request_count was 6 at 09:04Z, carrying those 8 records. UK-909420 at 03:03Z is unrelated (City over 30 chars).
- Latency (snap.poll.request.latency.avg): ilg001 was about 20–35ms from 08:56 to 09:06 (fast 404s), then 54.3s at about 09:08, 9.9s, 2.1s and 1.9s. Baseline is about 70ms. ilg002–005 stayed at 70–250ms. The 07:10–07:20Z maintenance hit every host (15–107s).
- Direct probes at about 09:08 (DOCKBAY creds, read-only): snaplookups, snapoutbound (including the poller's exact filter/$top) and shipments returned 200 in 1.3–14s. DNS: every ilg host resolves to 209.143.134.157 (host-header routing).
- Not established: why Cloud Run got HTTP.sys 404s while the workstation got 200s, and whether this is left over from the cluster change. The 404 classed non-transient is a possible our-side classification gap (not verified in code).

## Outcome
Vendor (SnapFulfil ilg001), P3. @fuse-support was pinged to replay the 8 held DOCKBAY sales orders once ilg001 is stable. The record stays open until they are replayed. No ticket.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792573644460409
