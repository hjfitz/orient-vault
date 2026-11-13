---
tags:
- waypoint
- remote-compute
- decision
decided: '2026-10-29'
status: accepted
---
# remote-compute workstations take SSH on public tcp/22

## Context
<!-- What forced a choice. -->
Each workstation needed a plain hostname an engineer can `ssh` to, like a laptop. Every other VM in
`ilg-platform-ec02` is reachable over IAP only. Dropping OS Login for Arch the same day left
SSH keys in tfvars, served from `rc-users` metadata, as the only login path.

## Options considered
<!-- Chosen first, then each rejected one, each with its because. -->
- **Chosen: public tcp/22 from `0.0.0.0/0` to tag `remote-compute`, key only.** It gives every VM a
  hostname with no client tooling. sshd refuses passwords and root, and fail2ban bans after 6
  failures in 10 minutes.
- **Rejected: IAP only.** Every login would need `gcloud` as a `ProxyCommand`, with no plain hostname.
  IAP stays as the fallback path.
- **Rejected: no external IP behind Cloud NAT.** It contradicts the per-VM hostname.
- **Deferred: a source allowlist.** `ssh_source_ranges` is a variable, so it can narrow later with no
  module change.

## Consequences
<!-- Good, and the cost accepted. -->
- Engineers connect with `ssh <user>@<key>.shell.platform.ilg.software`.
- The VMs are open to internet SSH scanning. Key-only auth and fail2ban carry that risk.
- An internet-facing VM must not reach the VPC: `remote-compute-deny-private-egress` (priority 900)
  overrides the VPC's allow-internal rule.
- Trivy GCP-0031 (public IP) is suppressed for `modules/workstation/main.tf` only.
- Agents that offer many keys get banned, so clients need `IdentitiesOnly yes`.

## Confirmation
<!-- The signal in prod that would show this was wrong. -->
**UNKNOWN** Nobody recorded a signal when this was decided.
