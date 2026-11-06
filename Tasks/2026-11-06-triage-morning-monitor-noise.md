---
tags: [adhoc-task]
date: 2026-11-06
tldr: "Triaged overnight/morning Fuse monitor alerts: one real blip (tracking-service Spanner 'transaction expired' burst 09:10–09:16, self-recovered), rest noise/flapping"
session_id: c36659b6-edee-4035-ab29-ffd89416a0e8
status: open
---
# Triage morning monitor noise

## Outcome
Only real signal: tracking-service ~540 "store failed; nacking for redelivery" (Spanner InvalidArgument: referenced transaction expired) 09:10–09:16 UTC, ~10–13% 5xx; nacked so Pub/Sub redelivers. Same pattern 2026-11-01 00h (231), so it predates the golden-image deploy (#17). Rest of the Fuse alerts are noise: PF go-live watches, the [FUSE][Platform] 2m error-rate monitor (>2 errors) flapping on single-digit config-service/snap_adapter blips. Owed: decide on a fix for the recurring Spanner expiry, and retune the 2m platform monitor.

## Tracking-service dig
Underlying error is Firestore commit RESOURCE_EXHAUSTED (536 = 536 InvalidArgument): the gapic Commit retry (RE/Unavailable) reuses the dead txn id, so the surfaced error is "transaction has expired"; RunTransaction only retries Aborted. Not Cloud Run scaling (CPU p99 21%, mem 35%, commit latency ~20 ms) and not the #16 hot-doc contention. Bursts are the PURDYFIGG 5-min reap (~2k pushes/min, growing through the morning). Leading hypothesis, unconfirmed: index write hotspot on the monotonic `lastSeenAt` that every copy rewrites; it is never queried but carries default single-field indexes. Confirm in Firestore Key Visualizer. Nothing dead-lettered. Owed: exempt lastSeenAt from indexing, map RE to a throttle response, consider skipping identical-copy writes / spreading the reap.


## Programme
Harry chose MongoDB (2026-11-06), superseding the 10-19 "stay on Firestore" call. Group D (D1–D13) added to Bifrost/Tracking Service Migration State with gates G3–G11 and risks R7–R12; counters plan inc 4 superseded. D1 stopgap plan drafted (`exempt-unqueried-fields-from-firestore-indexing`, worktree `hjf/exempt-unqueried-firestore-fields`). Spare worktree `hjf/tracking-service-mongo` reserved for D2+.
