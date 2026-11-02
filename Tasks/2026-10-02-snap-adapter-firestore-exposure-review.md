---
tags: [adhoc-task]
date: 2026-10-02
tldr: "Reviewed snap-adapter Firestore (routing-metadata) exposure in dev+prod: not open to the internet; two over-broad IAM paths found, no changes made"
session_id: fc99c833-e6c5-4e47-a6bc-f3ee75ad3a6b
status: open
---
# Review snap-adapter Firestore exposure

## Outcome
No Security Rules released and anonymous REST read returns 403 in both bifrost-dev-global1 and bifrost-prod-global1; no API keys, no Identity Platform. Findings: datastore.user/viewer granted project-wide with no condition (covers dedupe-service-dev-db in dev), and shopify-app runs as the default compute SA (project editor) so can write routing-metadata. Owed: decision on scoping IAM to the fuse-wms-routing database. Read-only, nothing changed.
