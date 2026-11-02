---
tags: [waypoint, ledger]
---
# api-host-framework — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-10-06 — Fix failing dependency audit via lockfile update

Fix failing dependency audit via lockfile update

Updated the lockfile to patched axios, express, body-parser, qs, proxy-addr and fast-uri so the nightly dependency audit (red on master since 2 October: one high, one critical) passes again. No source or package.json change.

PR: gfs-hybrid-services/api-host-framework#13

## 2026-10-06 — Rename AGENTS.md to CLAUDE.md

Rename AGENTS.md to CLAUDE.md

Renamed the framework's agent instructions from AGENTS.md to CLAUDE.md so Claude Code loads them, and updated the package files entry and the CONSUMER.md link. No source or version change.

PR: gfs-hybrid-services/api-host-framework#12
