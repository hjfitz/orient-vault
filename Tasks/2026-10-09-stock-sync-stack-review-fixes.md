---
tags: [adhoc-task]
date: 2026-10-09
tldr: "Linked shopify-connector FUSE-1198 stock-sync stack (#305–#317) as GitHub stack #327, fixed review comments and CI across it; apiky UI stack un-drafted and greened"
session_id: 85d0cbd2-3fe2-46cc-b863-34dbe95f62e1
status: open
---
# Get the FUSE-1198 stock-sync stack and the apiky UI stack ready to merge

## Outcome
- shopify-connector #305 ← #311 ← #312 ← #315 ← #316 ← #314 ← #317 (Matt's) linked as GitHub stack #327. Merged main into #305 (lockfile conflict), then merged up through the stack. #311: GCS adapter made a generic `GcsObjectStore`, with export parsing and the result copy store moved to core. #312/#314: GraphQL ops on gql-query-builder; pushed back on the two raw bulk strings (`@idempotent`, String args). #316: gitleaks allowlist for run-key fixtures. All 7 PRs green and CLEAN.
- Merged atomically as `f53f083` (9 Oct) and applied to dev. FUSE-1198 → Ready for QA, with a summary comment. Prod (egress, app, connector) is held at the `terraform-prod` gates until next week.
- Owed: prod approval next week. FUSE-1202's #318 conflicts after the merge and needs retargeting to `main` (heads-up posted on the ticket).
- apiky #5–#10 un-drafted; merged #12's audit fix up the stack so api-audit is green. #12 still draft and unmerged.
