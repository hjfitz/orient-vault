---
tags: [datadog-triage]
date: 2026-09-23
monitor: "[FUSE][Dedupe Service] Silent publish drop (handled minus outcomes)"
service: dedupe_service
business_id:
channel: bifrost-notifications
thread_url: "https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790168020512679"
opened_at: "2026-09-23T12:52:36Z"
resolved_at: "2026-09-23T12:55:36Z"
minutes_spent: 3
severity_assessed: P4
flapping: true
outcome: monitor_mistuned
ticket:
session_id: 335db79e-9fb1-423f-b0ea-f1e58dfe56ca
status: resolved
---
# Dedupe Service "Silent publish drop" monitor flapping on async window skew

## Fired
Monitor id `302511456` (P2, `managed-by:terraform`) fired Warn/Triggered at 12:52:36 UTC and
recovered at 12:55:36 UTC. Formula: `sum(last_1h): fuse.dedupe.event.handled` minus the sum of
every known outcome metric (`fresh`/`duplicate`/`sku.blacklisted`/`event.invalid`/
`record.invalid`/`dropped_config_unavailable`) `> 30` — the monitor's own message frames a
positive gap as records that were `handled` (push route already acked 204) but never accounted
for by any outcome, i.e. likely lost before reaching SNAP.

## Investigation
- Pulled the same six component metrics as 5-min buckets across the firing window
  (`get_datadog_metric`, `environment:prod`). `blacklisted`/`invalid`/`dropped_config_unavailable`
  were empty (true zero) throughout; `handled` vs `fresh + duplicate` reconciled to within ±4 in
  every bucket except one: the 11:55–12:00 UTC bucket showed `handled=94` against
  `fresh+duplicate=74`, a 20-record gap.
- The very next bucket (12:00–12:05 UTC) shows `fresh` spike to 39 against a ~2–7 baseline —
  consistent with those same ~20 records being counted as `fresh` one evaluation bucket later than
  `handled`, not lost. This matches the monitor's own caveat: "Threshold tolerates async/window
  skew — tune to baseline."
- Cross-checked raw `status:warn service:dedupe_service "Record dropped"` logs over the window:
  every drop carries `reason:duplicate` (business PURDYFIGG, `sales_order`, one poll's
  correlationId) — the expected/accounted-for duplicate path, nothing carrying an unexplained
  reason.
- Event history (`search_datadog_events`, 30d) shows this monitor fired/recovered **8 times in
  under 2 hours** on 2026-09-19 (16:30–18:20 UTC) before this occurrence — a repeat flapper, not a
  first-time signal.
- Slack: the alert posts as standalone (non-threaded) messages in #bifrost-notifications; a
  teammate (Jack Bailey) had already reacted 👀 and posted a "surprised cat" GIF to the Warn
  message before this triage, i.e. the team already treats these firings as noise.

## Outcome
False positive / self-resolved — a metric-timing artifact (handled counted before its outcome
metric lands, within the monitor's own 1h rolling window), not a real silent drop. Confirmed in
`dedupe-service`'s `event.controller.ts`: `event.handled` increments on receipt, the outcome
metrics only after the blacklist lookup, dedupe upsert and forward publish — so the fix is the
monitor, not the code.

Retuned at Harry's ask: added `evaluation_delay = 300` (the actual fix — lets log-to-metric
ingestion catch up before evaluating) plus thresholds 30→50 / 10→20 as a margin. `observability`
PR #47, plan reviewed (1 resource), merged, `terraform-prod` gate approved, verified live (`> 50`,
`OK`). A first CI run hit a one-off Datadog `503` on an unrelated catalog resource and passed on
rerun. No ticket — out-of-ticket tuning of Harry's own monitor.

## Links
- Slack thread: https://gfsdeliver-eng.slack.com/archives/C099WKQTE8G/p1790168020512679
- Monitor: https://app.datadoghq.com/monitors/302511456
- PR: https://github.com/gfs-bifrost/observability/pull/47
