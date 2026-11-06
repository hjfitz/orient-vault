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
