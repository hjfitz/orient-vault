---
tags: [datadog-triage]
date: 2026-09-24
monitor: "[FUSE][Platform] Elevated production error rate (2m window)"
service: snap-adapter
business_id:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790243559989879"
opened_at: "2026-09-24T09:51:37Z"
resolved_at: "2026-09-24T09:52:37Z"
minutes_spent: 12
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
escalated_to:
ticket:
session_id: a5533af9-6c8f-4c08-aab9-53c76f9fbfce
status: resolved
---
# Elevated production error rate monitor flapping on scattered snap-adapter create failures

## Fired
Monitor id `180072217` (`logs("@domain:fuse status:error @environment:prod AND NOT(...) AND NOT(...)").rollup("count").last("2m") > 2`) triggered at 09:51:37 UTC, recovered at 09:52:37 UTC — 1 minute later, before this triage even started.

## Investigation
- Pulled the 4 log lines that tripped the window: 2x `snap_adapter` "Entity creation in SNAP failed" for `BYOMA` (sales_order), 2x for `LISAUK` (sales_order), one of the LISAUK pair carrying `error.message: Request failed with status code 401`.
- Checked the monitor's own event history over the last 24h via `search_datadog_events`: 9 full trigger/recover cycles since 2026-09-23T14:44Z, every one self-recovering within 1–4 minutes — this monitor is a chronic flapper, not a one-off.
- Pulled all `snap_adapter` `@domain:fuse` error logs over the same 24h window: 19 lines total, scattered across 5 different businesses (BYOMA, LISAUK, SAIRA, DISCOVERED, STUBBLE), never more than a handful clustered within any single 2-minute window. The SAIRA cluster (6 failures, 15:30–15:55 Sep 23) and the LISAUK 401 cluster (3 failures, 16:40–16:59 Sep 23, plus this morning's) were each self-contained and non-growing.
- Confirmed via Fuse MCP `lookup-service` that `snap-adapter` publishes `entity_error`/`create_data_failure` on this exact failure path — these are handled failures that flow into the normal replay/failure pipeline, not silently dropped records.
- Monitor's own query already carries two prior hand-added exclusions (`NOT(service:snap-polling-service AND @error.status:401)`, `NOT(service:shopify-connector AND @businessId:SAIRA)`) — visible in the event history as the query text changed partway through 2026-09-23, evidence this monitor has already been patched twice for exactly this "known noisy source" pattern.

## Outcome
No real incident — self-resolved before triage started, low and non-growing volume, spread across unrelated businesses, and the failures are already captured by the standard create-failure/replay path. The monitor itself is over-sensitive: a `>2 errors/2min` platform-wide threshold is trivially crossed by ordinary, unrelated `snap_adapter` create failures from different businesses. Posted the verdict + recommendation (consider a third exclusion for `snap_adapter` create failures, or widen the threshold/window) to the thread; left the actual retune for Harry to confirm before touching the `managed-by:terraform` monitor. No ticket filed — asked Harry first rather than filing unprompted, since this is the third occurrence of the same "needs another exclusion" pattern on one monitor and might warrant a more structural fix (e.g. excluding all known `entity_error`/`create_data_failure`-path logs) rather than a fourth one-off patch.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790243559989879
- Monitor: id 180072217
