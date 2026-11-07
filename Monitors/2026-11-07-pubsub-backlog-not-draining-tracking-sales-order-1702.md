---
tags: [datadog-triage]
date: 2026-11-07
monitor: "[FUSE][Platform] Pub/Sub backlog not draining (any subscription)"
service: tracking-service
business_id:
snap_instance:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794070968241819"
opened_at: "2026-11-07T17:01:38Z"
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: 7f84afae-380e-4959-8dc8-c8b0cbe9f19d
status: resolved
---
# Backlog not draining Triggered/Warn on tracking-service create_record_request sales_order sub (monitor 323648858), plus collector and dedupe backlog Warns

## Fired
323648858 (change(avg(last_15m), last_1h) of num_undelivered_messages > 200, per subscription) fired Triggered at 17:02:48Z and Warn at 17:04:50Z on the tracking-service sub. Siblings: 302536090 (max(last_15m) > 200 warn, 1000 critical) on collector and dedupe subs at 16:59:28-30Z, and 302511458 (dedupe, warn at 246) at 16:59:45Z.

## Investigation
- Undelivered on the tracking sub per minute from 16:45Z: 0, 242, 242, 0, 0, 0, 405, 409, 0, 0, 0, 390, 390, 0, 0, 0, 90, 90, 0 ... 155, 155 at 17:06-17:07. A burst arrives about every 5 minutes and is back to 0 within 2 minutes.
- Oldest unacked on tracking and dedupe subs stayed at or under 2s in the same window. Collector peak 300 at 16:56, 0 by 16:57.
- Tracking push responses: 1504, 1556, 1646, 1713 acks per burst minute; no non-ack response class appeared in the window.
- No deadline_exceeded on tracking, dedupe or collector create_record_request sub in 24h except collector (446 of 201,937 requests).
- Replay failures since 16:50Z: no sales_order, purchase_order, master_data, pick or pack entries (newest sales_order hold is DOCKBAY 13:03Z).

## Outcome
Normal 5-minute burst traffic that drains in seconds. The trend monitor compares a 15m average with the average an hour earlier, so it trips on burst timing rather than on a backlog that is not draining. The static monitors warn at 200 and see 246-300.

## Links
- Slack threads: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1794070968241819 , p1794071090972359 , p1794070768684279 , p1794070770611729 , p1794070785736059
