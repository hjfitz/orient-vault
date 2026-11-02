---
tags: [adhoc-task]
date: 2026-10-19
tldr: "Copies taken off the shared Firestore stats docs (tracking-service#16, prod): PURDYFIGG burst commits 0.8 s → 16-51 ms; 6x load test says the genuine-order path (~40/s cap) needs a counter fix before PURDYFIGG's full move"
session_id: 169298a2-e5d1-4de6-8c1a-7cc6d35e3a74
status: open
---
# Investigate tracking-service sales_order push latency

## Outcome
- **Shipped:** tracking-service#15 (dev-only Manual Deploy) and #16 (republished copies no longer write the shared stats docs), both in prod. fuse-ui#339 (duplicates week tile retired) is also in prod.
- **Prod after #16:** PURDYFIGG burst commits went from 0.79 s to 16–51 ms from 12:01 UTC onwards. The 11:56 burst, right after the rollout, was still slow and is unexplained.
- **6× load test** (throwaway dev Firestore, real `core.Ingestor`): copies drain at 167/s, about 44 s for a 7,344-message burst. Genuine (non-copy) ingest caps at about 40/s on the shared businesses/stats docs; the prod peak is about 8/s.
- **Owed:** inc 4, removing the shared-counter hot spot (sharded counters or `_all_` on read). Do it before PURDYFIGG's full move, after a design review.
