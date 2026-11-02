---
tags: [adhoc-task]
date: 2026-10-19
tldr: "Shipped 'where it failed' to the Retry Queue (SHIP-1019), re-attributed 540 no-business prod rows, and shipped FUSE-1319 (Snap outages retryable + labelled) to prod"
session_id: f9b4bd94-d9a5-4bf5-a512-fdd463fe7e1e
status: done
---
# Check whether replay-service records where a failure happened

## Outcome
SHIP-1019 put `failurePoint` and the Where It Failed column/filter/grouping live (replay `66ca610`, fuse-ui `cc1d50e`). Then 540 prod failures with no business were re-attributed to their envelope customer. FUSE-1319 is live: snap-adapter `dbed308` (#303), replay `1fe4c16` (#125), fuse-ui `e09675e` (#345). That unblocks dedupe-service#160. Defects split out: FUSE-1318, 1320, 1321, 1322. Gap found: a successfully replayed create-side failure stays "Failed Again" until dismissed, and no ticket covers it yet. See the ledger entries in all three repos.
