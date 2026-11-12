---
tags: [waypoint, ideas]
---
# tracking-service — ideas log

Every idea waypoint-ideate has surfaced, kept or discarded, newest first.
Read in full before generating new ideas — don't resurface a discarded idea
without new evidence that changed the picture.

## 2026-11-12 — kept — Move apps/api to code/
source: techdebt
plan: move-apps-api-to-code

The fleet keeps service code under `code/`; tracking-service still has its one app at `apps/api`, a leftover from the monorepo era that B11/B13 deferred.

## 2026-11-12 — kept — Bring stats and insights latency back down on MongoDB
source: techdebt
plan: bring-stats-and-insights-latency-back-down-on-mo

Measured after the 2026-11-11 cut, the read endpoints the order tracker loads first are 4-6x slower than on Firestore; Harry called it fine for now, so it's parked, not dropped.

## 2026-11-12 — kept — Turn the migration buckets off once the final export expires
source: techdebt
plan: turn-the-migration-buckets-off-once-the-final-ex

The final Firestore export is only kept until the bucket's 30-day lifecycle empties it, about 2026-12-11; after that the bucket and its IAM are dead weight.
