---
tags: [waypoint, ledger]
---
# svc-template — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-10-28 — Run svc and ui on the golden images and 0.1-affogato cloud-run

Run svc and ui on the golden images and 0.1-affogato cloud-run

Direct push to main (6420d29). go-runtime + node24-runtime, sidecar log file sink and LOG_DIR removed from svc, module ref 0.1-affogato; dev applied, prod parked at gate.

Commit: ilg-merak/svc-template@6420d29

## 2026-10-28 — Name the repo in the Terraform state prefix

Name the repo in the Terraform state prefix

basename(get_repo_root()) is 'workspace' in CI, so every repo made from the template shared svc-template's state (merak-portal's plans would have replaced ui-template). Repo now named in root.hcl; dev branch deploys announce failures only. Draft until svc-template's state is copied from workspace/ to svc-template/ in both buckets.

PR: ilg-merak/svc-template#7
