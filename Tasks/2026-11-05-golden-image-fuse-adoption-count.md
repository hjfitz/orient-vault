---
tags: [adhoc-task]
date: 2026-11-05
tldr: "Counted Fuse golden-image adoption from the default branches: 3 images migrated, 18 repos (26 deployable images) still on node:*-alpine or distroless static-debian12"
session_id: df20a2e1-7faa-4363-a264-b18e9200b3d7
status: done
---
# Count Fuse services not on golden images

## Outcome
Scanned the FROM lines of every dockerfile on the default branch of the non-archived gfs-bifrost repos, using local checkouts because the GitHub REST API was rate-limited. Only dedupe-service, audit-service and fuse-devtools/pr-sitrep are on golden images. 18 repos (26 images) are not, and the Go ones are still on the deprecated distroless static-debian12 base. snap-test-automation wasn't checked because there's no local clone.
