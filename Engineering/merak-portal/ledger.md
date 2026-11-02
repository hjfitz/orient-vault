---
tags: [waypoint, ledger]
---
# merak-portal — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-10-28 — Run the ui on the node24-runtime golden image and 0.1-affogato cloud-run

Run the ui on the node24-runtime golden image and 0.1-affogato cloud-run

Direct push to main (6489a0a). node24-runtime, node:24 build stages, module ref 0.1-affogato, DD keys mapped; dev applied, prod parked at terraform-prod gate.

Commit: ilg-merak/merak-portal@6489a0a

## 2026-10-28 — Sign in with Basic auth and render plain semantic HTML

Sign in with Basic auth and render plain semantic HTML

Folded into C1's PR before merge: HTTP Basic auth middleware (one shared account, generated password in Secret Manager), public run.app invoker accepted for the PoC, ui-toolkit and Tailwind removed.

PR: ilg-merak/merak-portal#3

## 2026-10-28 — Manage each business's Selector backend from the portal

Manage each business's Selector backend from the portal

Delivery Backends C2. Business list + per-business Selector backend create/edit/delete via config-service ?type=SELECTOR, server-side only; passwords never rendered; config-service key secret named in Terraform, dev copy made. Verified locally end to end (15/15) against config-service main with A3; dev wiring verified, full dev check waits for A3 on config-service dev.

PR: ilg-merak/merak-portal#6

## 2026-10-28 — Scaffold the delivery portal from svc-template, keeping only the ui app

Scaffold the delivery portal from svc-template, keeping only the ui app

Delivery Backends C1. New repo ilg-merak/merak-portal seeded from svc-template; ui only (ui-portal-<env>, system portal); terraform-prod environment with Harry as reviewer. Found and fixed the template's shared state prefix (basename(get_repo_root()) is 'workspace' in CI): the repo is named explicitly. Deployed to dev; startup probe passes.

PR: ilg-merak/merak-portal#3
