---
tags: [adhoc-task]
date: 2026-10-09
tldr: "Reviewed prod Snap failures/timeouts since 9 Sep for Ryan's email: bad days 11-12 Sep, 29-30 Sep (ilg005), none since 1 Oct bar a 12-record slot-timeout blip on 5 Oct; post-change load is lower than before, so not a like-for-like peak test."
session_id: 5dc5ab1c-f5dc-4b12-b10c-4e432f77b05e
status: open
---
# Review prod Snap failures and timeouts, 9 Sep to 9 Oct

## Outcome
Datadog metrics (snap.request.failure/latency, snap.circuit_opened) plus snap_adapter logs (retained from 24 Sep only). ilg005 timed out at 120s on 11, 12, 22, 29, 30 Sep; 29-30 Sep hit PURDYFIGG hardest (14 retries exhausted into replay-service). Clean from 1 Oct bar 12 DOCKBAY slot timeouts on 5 Oct 00:04 UTC.
Owed: ~75 prod replay failures reasoning "concurrency slot" (newest 30 all attempts 0) not confirmed redriven; reply to Ryan.
