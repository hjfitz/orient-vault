---
tags: [adhoc-task]
date: 2026-10-05
tldr: "Taught wp signoff to accept squash-merged PRs; signed off 19 merged plans (active 20 -> 8)"
session_id: 1588119a-fe0c-49ef-9820-89354e05366d
status: open
---
# Make wp signoff work after a squash merge, then close the finished plans

## Outcome
- `~/.claude/waypoint/wp.py` sign-off, two changes:
  - a done sha already on base counts as reachable;
  - when the PR is merged, an empty branch diff and a pre-squash or rebuilt sha are notes, not blockers.
  - Criteria, evidence and placeholders still gate. Backup is in the session scratchpad.
- Signed off and completed: config-service useCases; E1 in fapi, sftp-connector and shopify-connector; E8 in pkg-node, fapi and shopify-connector.
- Learnings promoted into the fapi, sftp-connector, config-service and shopify-connector `known-context.md` and `architecture.md`, with SUPERSEDED markers on stale sections.
- Then three agents worked the other merged plans. 12 more completed: collector, fapi FUSE-1056, shopify FUSE-1057, pkg-node FUSE-1034/1088/1258, sftp FUSE-1088, and five snap-adapter plans. Active plans went from 20 to 8.
- Still open, genuinely unfinished:
  - config-service OpenAPI increment 6. fuse-ui codegen hits `/api/v1/docs/openapi.yaml`, which returns 401; `docs-json` returns 200.
  - fuse-ui EDIFACT: a cancelled preview check needs a decision.
  - sftp EDIFACT increment 8 and AC 7, which needs a decision on batch.
  - snap-adapter FUSE-1078 increments 4 and 5; AC 1 and AC 3 need re-wording.
  - The two wms-gateway plans and the fuse-ui client regen.
- Zombie parked poller Deploy run 35326280351 (`121c514`, older than prod) can be neither cancelled nor rejected. Never approve it.
- 2026-10-07: orient gained a **Soaks** section (`/soaks`, `g q`, under Operations; orient `73faa8a`). Records live in `Soaks/` (type `soak-test`: status, programme, unit, started, next_checkpoint, subjects, queued, monitors, verdict), with live Datadog monitor state. First record: `Soaks/poller-clear-down-d1.md`.
