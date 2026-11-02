---
tags: [waypoint, ideas]
---
# snap-queue-polling-service — ideas log

Every idea waypoint-ideate has surfaced, kept or discarded, newest first.
Read in full before generating new ideas — don't resurface a discarded idea
without new evidence that changed the picture.

## 2026-09-22 — kept — Update the SNAP dashboard with a new tab
source: user
plan: add-a-log-volume-stu-unmatched-tab-to-the-snap-w

User-suggested during keep/discard: surface the new StU-unmatched metric and log-volume monitor on the existing SNAP WMS Operations dashboard.

## 2026-09-22 — kept — Emit a metric for unmatched StU
source: evolution
plan: replace-the-per-item-stu-not-found-warn-with-a-m

User modified scope: replace the per-item warn log entirely with a metric, rather than aggregating/keeping the log.

## 2026-09-22 — kept — Add a log-volume monitor
source: evolution
plan: add-a-datadog-log-volume-monitor-for-snap-pollin

No Datadog monitor exists for this service's log volume today.

## 2026-09-22 — kept — Extend the DROPPED_CONFIRMATION tag convention
source: techdebt
plan: extend-the-dropped-confirmation-tag-convention-t

Cover degraded-but-non-fatal per-item warnings under the existing grep-able vocabulary; closes the stale TODO at confirmation-failure.ts:10.

## 2026-09-22 — kept — Aggregate the two working-as-intended info logs
source: techdebt
plan: aggregate-claim-skip-and-already-claimed-info-lo

'Confirmation claim skipped duplicates' and 'Skipping already-claimed queue items' log the idempotency mechanism succeeding, once per occurrence.

## 2026-09-22 — kept — Migrate remaining raw logger calls onto FUSE-995 event-catalogue seam
source: techdebt
plan: migrate-remaining-raw-logger-calls-onto-the-fuse

FUSE-995 (PR #236) migrated the sibling warning but missed this handler family and the SNAP-failure logging.

## 2026-09-22 — kept — Find why debug logs leak into prod
source: techdebt
plan: investigate-debug-level-logs-leaking-into-prod

8,850 debug logs/day despite LOG_LEVEL=info in iac/env/prod.tfvars.

## 2026-09-22 — kept — Per-business backoff for chronic SNAP failures
source: techdebt
plan: per-business-backoff-for-chronically-failing-sna

No breaker trips on a single business's 4xx; a permanently-broken business retries at full poll frequency forever.

## 2026-09-22 — kept — Stop double-logging raw Axios error on SNAP request failures
source: techdebt
plan: stop-double-logging-the-raw-axios-error-on-snap-

12,431 error logs/day, each carrying a duplicated massive raw Axios error payload (>20k tokens for one sample).

## 2026-09-22 — discarded — Root-cause why SNAP never returns these StUs
source: evolution

Already covered elsewhere.

## 2026-09-22 — discarded — Aggregate StU-not-found warn
source: techdebt

User directive: ignore the StU-not-found condition as a per-item log line entirely, superseded by the kept 'replace with metric' idea instead of dedup/aggregation.
