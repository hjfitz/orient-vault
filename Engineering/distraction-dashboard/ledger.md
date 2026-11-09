---
tags: [waypoint, ledger]
title: distraction-dashboard — work ledger
---
# distraction-dashboard — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-05 — Run distraction-dashboard on the golden runtime image

Run distraction-dashboard on the golden runtime image

Runtime moves from node:22-alpine to ilg-platform's node24-runtime:0.1-affogato (Node 24, glibc build stages), so Datadog's agent runs in the app container. The service had no Datadog before: it now gets dedupe's DD_* set with GFS + ILG dual-ship, and memory goes from 512Mi to 1Gi (dev p99 0.67 of 512Mi, plus about 100MiB for the agent). The runtime image also stops inheriting GITHUB_TOKEN from the build stage. Verified on dev as revision 00070-nt4.

PR: gfs-bifrost/distraction-dashboard#39
