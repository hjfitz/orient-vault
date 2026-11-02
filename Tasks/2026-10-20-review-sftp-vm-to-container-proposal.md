---
tags: [adhoc-task]
date: 2026-10-20
tldr: "Planned replacing the SFTP VM with a multi-zone, portable Go SFTP host (own server on x/crypto/ssh + pkg/sftp) behind a load balancer with a gradual traffic split; Plan A active, B/C draft, VM hardening and UJ login audit superseded."
session_id: c483ad99-3b6e-42ca-94f7-5ad17f5f895d
status: open
---
# Review SFTP VM → container proposal

## Outcome
Plans in `Engineering/sftp-connector/plans/`: `sftp-host-a-…` (active: monorepo, connector prep, Go host, dev infra), `sftp-host-b-…` and `sftp-host-c-…` (draft). Plan H (VM hardening) and UJ (Ops Agent login audit) abandoned at Harry's call; Audit Migration State updated (UJ halted, G7 covered by the plans).
Open: password-auth connector count (Plan A inc 3 gate); host-key lift once the VM is back up.
