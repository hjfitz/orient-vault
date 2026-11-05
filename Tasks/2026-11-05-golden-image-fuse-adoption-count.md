---
tags: [adhoc-task]
date: 2026-11-05
tldr: "Rolled every Fuse Cloud Run service onto ILG golden images (Datadog in-container, no sidecars): 17 PRs + 2 direct pushes, all live and verified in prod/dev"
session_id: df20a2e1-7faa-4363-a264-b18e9200b3d7
status: open
---
# Roll Fuse services onto golden images

## Outcome
Counted 18 repos / 26 images off golden images, then migrated all deployable ones (Prism sandbox and sftp-host VM excluded) across three waves; each PR has its own wp ledger entry. Memory limits raised where the in-container agent left <25% headroom. Owed (Harry's call): rotate the GH_TOKEN PAT baked into old Next.js image configs, delete orphan distraction-dashboard-prod; fuse-mcp master parity red (pre-existing).
