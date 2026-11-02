---
tags: [meeting]
series: Harry/Kyle 1:1 (Fuse internals)
counterpart: "[[Kyle Chandler]]"
title: 'Harry/Kyle 1:1 — Fuse internals'
---
# Harry/Kyle 1:1 — Fuse internals

## 2026-06-24
_15:00–15:45 · Slack huddle · walk [[Kyle Chandler]] through how Fuse works ahead of him contributing_

### Context
- New contributor onboarding — teaching session, no PRs/tickets yet
- Suggested walkthrough order:
  - The pipeline — connector ingress → canonical conversion at the boundary → Pub/Sub (canonical-only) → dedupe → collector / egress
  - Canonical-first, standard `BifrostMessage<T>` envelope, `recordType` Pub/Sub attribute
  - Layered architecture (http → use-cases → core; adapters / repositories / config) — `fuse://architecture` in the Fuse MCP
  - Shared packages `@gfs-bifrost/*` (types, pubsub, cache, edi, remote-config)
  - Point him at the Fuse MCP server for service / topic / type lookups

### Notes
- ✍️ 
