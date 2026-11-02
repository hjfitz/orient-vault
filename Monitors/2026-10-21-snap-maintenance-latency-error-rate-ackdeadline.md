---
tags: [datadog-triage]
date: 2026-10-21
monitor: "[FUSE][Snap Adapter] API latency threshold breached (+ Elevated production error rate 2m, + Pub/Sub ack-deadline headroom eroding)"
service: snap-adapter
business_id:
snap_instance: ilg001, ilg002, ilg003, ilg004, ilg005
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792566987084759"
opened_at: "2026-10-21T07:15:08Z"
resolved_at: "2026-10-21T08:10:19Z"
minutes_spent: 55
severity_assessed: P4
flapping: false
outcome: vendor
escalated_to:
ticket:
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# Snap planned cluster maintenance: latency, error-rate and ack-deadline alerts, all recovered

## Fired
- Monitor 179927768 (Snap API latency) fired at 07:15:08Z. ilg001, ilg002, ilg004 and ilg005 went to Alert. ilg003 went to Warn, then Alert at 07:16:08Z.
- Monitor 180072217 (prod error rate, 2m window) fired at 07:15:37Z.
- Monitor 323648859 (Pub/Sub ack-deadline headroom) fired at 07:21:39Z on `snap_adapter.prod.create_record_sales_order.v1.sub`.
- All of these fell inside ILG's planned Snap cluster modification, 07:00–07:30Z, which is pinned in #bifrost-general.

## Investigation
- **Latency** (`snap.poll.request.latency.avg` by snap_host, 5m buckets):
  - Baseline from 06:00 to 07:10Z was 60–270ms on every host.
  - Peaks:

    | Host | Peak | Bucket |
    | --- | --- | --- |
    | ilg001 | 11.7s | 07:10Z |
    | ilg002 | 11.9s | 07:10Z |
    | ilg003 | 18.2s | 07:15Z |
    | ilg004 | 30.6s | 07:15Z |
    | ilg005 | 21.8s | 07:15Z |

  - Every host was back under 300ms from the 07:20Z bucket through 08:05Z.
  - All three monitors were OK by 07:39Z. ilg001 and ilg004 briefly showed Warn at 07:38Z because the 20m average was still trailing the spike.
- **Errors**:
  - There were 0 matching error logs from 06:30 to 07:14Z.
  - There were 122 from 07:14 to 07:18Z, and 0 after that up to 08:05Z.
  - 99 came from snap-polling-service: `SNAP request failed` and `Outbound queue fetch failed` reads of `/v2/snapoutbound`. Snap returned HTTP 500 with an IIS runtime-error page, on all hosts and across 17 businesses. These are reads that retry on the next poll.
  - 23 came from snap_adapter. All were `transient:true` and `exhausted:false`, with failureMode `snap_api_error` or `circuit_open` on ilg005.
  - None were the known PURDYFIGG "no fulfillment ID" errors (the monitor excludes those).
- **Creates**:
  - 4 PURDYFIGG sales orders failed: #6569925, #6569929, #6569931 and #6569932.
  - Pub/Sub redelivered them (503 nack) and all 4 logged `Entity created in SNAP` / 204 between 07:18:41 and 07:18:43Z.
  - Snap creates per hour were 66 (06:00), 30 (07:00) and 17 (08:00 so far).
- **Terminal failures**:
  - replay-service prod holds 1 failure for today. It is DOCKBAY UK-909420 from 03:03Z, a City longer than 30 characters caught by the WMS precheck. It is unrelated and predates the window.
- **Dead letters**:
  - `gcp.pubsub.subscription.dead_letter_message_count` reports normally: there are series for 4 subscriptions over 14 days.
  - None of them has any datapoint today.
  - The snap_adapter sales_order subscription last dead-lettered 12 messages on 2026-10-20 between 10:50 and 11:40Z. That is outside this window.
- **Ack-deadline**:
  - Oldest-unacked on that subscription was 55s at 07:17, 55s at 07:18, 151s at 07:19 and 211s at 07:20Z, then 0 from 07:21Z.
  - Undelivered messages peaked at about 2–3.
  - The monitor recovered at 07:31:47Z.
- **Flapping (7 days)**:
  - The latency monitor fired on 10-14, 10-19 (the 19 Oct Snap outage), 10-20 and today. Each firing matches a Snap event, so it isn't a tuning problem.
  - The error-rate monitor fired 13 times on 10-20. That is a separate matter, not triaged here.
- **Not established**:
  - The vendor-side cause of the HTTP 500s: we only see an IIS error page.
  - No direct snap-MCP probe was run. Recovery is shown by the metric and logs instead.

## Outcome
Vendor: Snap's planned maintenance caused a short burst of latency and 500s. It recovered without intervention at about 07:20Z. No data was lost, there were no dead letters, nothing is held, and no action or ticket is needed. Verdicts were posted in all 8 alert threads. The ilg004 latency, error-rate and ack-deadline replies were broadcast to the channel; the other per-host replies were thread-only.

## Links
- Slack thread (ilg004, broadcast): https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792566987084759
- Error-rate thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792567004928569
- Ack-deadline thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1792567367434279
- Maintenance notice: https://gfsdeliver-eng.slack.com/archives/C098LD5PS95/p1792525805816669
