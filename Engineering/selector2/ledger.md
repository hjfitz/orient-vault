---
tags: [waypoint, ledger]
---
# selector2 — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-11-11 — Scaffold selector2-api and selector2-ui, IaC and CI

Scaffold selector2-api and selector2-ui, IaC and CI

New repo ilg-merak/selector2: NestJS selector2-api and SvelteKit selector2-ui in one pnpm workspace, Biome, Vitest, Terragrunt projects and four workflows. Merged to main; deploy dev applied 2 resources per app (Cloud Run service plus service account), 0 destroyed. Services are IAM-only (no allUsers), so an unauthenticated call returns 403 and no invoker is granted yet. Names carry the project name, never svc/ui.

PR: ilg-merak/selector2#1
