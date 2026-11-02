---
tags: [adhoc-task]
date: 2026-10-24
tldr: "ilg-merak groundwork: org AGENTS.md (agents#1, merged), Go+UI service template (svc-template#1), app platform in gcp-config (#4, plan pending review)"
session_id: f95db3f3-7a06-4c33-b451-20dbcef41931
status: open
---
# Lay the ilg-merak engineering groundwork

## Outcome
- ilg-merak/agents#1 (merged 2026-10-25, 846ea0c): org AGENTS.md. It covers backend structure and composition drawn from the Fuse Go and Node services, plus the technology standards (OpenAPI published, JSON on Pub/Sub, PostgreSQL on Cloud SQL or AlloyDB, Atlas, Firestore, slog). Frontend is a TODO for Darren.
- ilg-merak/svc-template#1: monorepo template with apps/{svc (Go), ui (empty, ui-toolkit)} and the full 0.2-bonbon CI/CD and secops. Its AGENTS.md carries a short form of the backend principles plus a frontend placeholder for Darren.
- ilg-merak/gcp-config#4: APIs, `services` registry, app state bucket, runner actAs. Plans are 7 add / 0 change / 0 destroy per env. Owed: plan review, then merge and apply, then a first template deploy.
- svc-template CI: secops, Go checks, integration and ui (cross-org ui-toolkit install) are all green. The TF plans need org-level `PLATFORM_CI_APP_ID` and `PLATFORM_CI_APP_PRIVATE_KEY`, set by an ilg-merak admin. WIF to terraform-runner works.
- Fleet follow-up: ui-toolkit's `next-navigation-guard` peer blocks Next 16, so consumers override postcss for GHSA-6g55/r28c.
- Not in the wp ledger: neither repo is onboarded, and `wp ledger` can't create folders because `~/.local/bin/templates/waypoint.yaml` is missing from the wp install.
