---
tags: [datadog-triage]
date: 2026-10-22
monitor: "[FUSE][Snap Adapter] API latency threshold breached"
service: snap-adapter
business_id:
snap_instance: ilg004
channel: bifrost-notifications
thread_url: "https://slack.com/archives/C099WKQTE8G/p1792669106101649"
opened_at: "2026-10-22T11:37:08Z"
resolved_at: "2026-10-22T11:39:18Z"
minutes_spent: 2
severity_assessed: P4
flapping: true
outcome: vendor
session_id: 7b50d12c-31a0-425c-913d-8c963cd91233
status: resolved
---
# ilg004 Snap API latency Warn (third repeat today)

## Fired
Monitor 179927768 Warn on snap_host ilg004liveapi: snap.poll.request.latency.avg 4813.842ms > 2000ms over 20m, at 11:37:08Z. Two further firings folded in. Same signal as the 11:05Z triage (slow since Snap's planned DB4 update ended 08:54Z).

## Investigation
- Errors in snap_adapter / snap-polling-service / snap-queue-polling-service since 11:00Z (log patterns): 1, at 11:00:10Z, PURDYFIGG "Entity creation in SNAP failed" (Unable to parse data). Not ilg004 related.
- Timeouts / circuit / 503 / 504 / 404 / ilg004liveapi warn+error since 11:00Z: none from Snap services (only shopify-connector DDP warnings, replay_service and fuse-mcp route 404s).
- Prod replay holds created 2026-10-22: newest is 11:00:10Z PURDYFIGG #6572814 (ShipAddress.Name >50 chars, wms_precheck). None for KAPPAHL, BABYMORI, SAMMCK, SAIRA or SPORTLUX after the known 08:41:43Z.

Not established: the free-text `ilg004liveapi` log query matched 0 rows, so per-host coverage rests on the service-scoped error search.

## Outcome
P4 vendor, unchanged since 11:05Z. No action. Verdict posted to the thread (reply ts 1792669158.068869).

## Links
- Slack thread: https://slack.com/archives/C099WKQTE8G/p1792669106101649
