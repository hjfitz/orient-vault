---
tags: [waypoint, remote-compute]
verified: '2026-11-13'
verified_paths: []
title: remote-compute — known context
---

# remote-compute — known context

`known-context.md` is exempt from staleness checks. It holds interview and investigation truth, not
claims about current source. Re-verify against code before trusting an implementation detail here.

## Who it's for and who owns it

Open to any ILG engineer (Harry, 2026-11-13). The self-serve route is the `create-workstation` skill
plus the Confluence how-to (PLTE 348356619). Platform engineering owns it, and Harry built it. The
`terraform-prod` reviewers are Harry and Kyle Chandler, mirroring core-infra.

Adoption so far: one workstation, `rc-hjf` (Harry, tier `s`). Harry runs Claude Code sessions on it,
including vault and orient work, handed over from the laptop with the `session-handover` skill.
(snapshot 2026-11-13)

## Decisions that would surprise someone reading only the source

- **Arch Linux, not Ubuntu.** It was switched before the first VM went live (2026-10-29), so OS Login went:
  it isn't maintained on Arch. Owners are `{email, username, uid, ssh_keys}` in tfvars, served from
  `rc-users` metadata. The images repo plan is still named `...-packer-ubuntu-24-04`, a leftover.
- **Public tcp/22 is deliberate.** Every other VM in `ilg-platform-ec02` is IAP-only. Workstations take
  key-only SSH from anywhere, with fail2ban, so each engineer gets a plain hostname. IAP stays as the
  fallback, and `ssh_source_ranges` can become an allowlist later. Durable record:
  [[2026-10-29-remote-compute-workstations-take-ssh-on-public-tcp-22]].
- **Access ends by PR, not by Workspace.** Disabling a leaver's Google account does not cut their SSH.
  Removing their owner entry or keys does. A scheduled active-account check was considered and left out
  because it needs Admin SDK access.
- **Idle and nightly shutdown are opt-in** (2026-11-02). Owners often leave work running overnight.
- **A standalone module is being rejected.** PR #15 (Wolf, Lead SRE) adds `iac/modules/standalone-workstation`
  so another repo's Terraform could create a workstation for an always-on agent VM. Harry said on
  2026-11-13 it will be rejected. Every workstation stays an entry in `prod.tfvars`, where the stack's
  uniqueness checks on subdomain, keys and uids hold. (snapshot 2026-11-13: PR still open)
- **The module is local, not from terraform-modules.** `terraform-modules//compute/vm` needs Terraform
  1.14 or later (the fleet runs 1.9.0) and lacks `attached_disk`. The plan intended to upstream
  `workstation` to the catalog once stable.
- **No `removed {}` block for offboarding.** Terraform 1.9 refuses a module instance key in
  `removed.from`, so the route is `terragrunt state rm` of the disk and IP, then the deleting PR. The
  day-2 plan's older `removed {}` idea is superseded by the README.

## Failure modes seen in practice

Harry confirmed these three are the only ones so far (2026-11-13):

1. **IAP access lost after a rebuild.** The instance-level `iap.tunnelResourceAccessor` write landed
   before IAP had initialised the new instance's policy, which then came up empty. It happened in two
   prod rebuilds (#4, #8). It was fixed in #11 with a reserved internal IP and a project-level grant
   conditioned on it. A throwaway probe reached sshd 23–30 s after each of three replaces.
2. **fail2ban bans an agent that offers many keys.** Each refused key counts as a failure, and 6 in
   10 minutes bans the address for 15 minutes. The fix is client-side: `IdentitiesOnly yes` and the
   right `IdentityFile`. The IAP range is never banned, so IAP still works during a ban.
3. **`rc-home` fails, and then there is no SSH at all.** If the `google-home` disk doesn't appear,
   or isn't blank and has no filesystem, `rc-users`, `rc-hostkeys` and sshd don't start. This is
   deliberate, so the VM never runs on the boot disk. Diagnose with
   `gcloud compute instances get-serial-port-output`, which owners can do.

## Constraints and fragility

- **Custom roles race their first binding.** Each has a 60 s `time_sleep`, and a first apply may
  still need a re-run.
- **terraform-runner needed `compute.instances.setIamPolicy`.** gcp-config granted
  `roles/compute.instanceAdmin.v1` for it. The same class of gap has bitten gcp-config and core-infra.
- **Repo and Environment governance is loose.** Every `ilg-platform` org member is a repo admin, and
  `terraform-prod` allows self-review. Any member could edit reviewers or bypass rules, and PR plans
  run as the owner-equivalent terraform-runner. This is the same exposure core-infra has, so it is
  treated as a fleet-level fix.
- **Owners are root on their VM.** Removing someone from a shared VM doesn't remove what they left in
  `/home`. A leaver on a shared VM means a replace plus an audit of `/home`.
- **Prices are unverified.** The Billing Catalog API returned 403 from every available quota project.

## In flight (snapshot 2026-11-13)

- **#14 `open_ports`** (Harry, opened 2026-11-03): per-entry extra inbound ports, scoped to the VM's
  own `rc-<key>` tag. Checks are green, but nobody has reviewed it.
- **#15 standalone module + `startup_script`** (Wolf, opened 2026-11-12): the module part is to be
  rejected (above).
- **Day-2 operations plan** (draft, nothing ticked): it would prove tier change, disk growth, two-owner
  VMs, offboarding, Claude Code self-update, and a second team onboarding unaided.

## Unknowns

- Is the `startup_script` half of #15 also rejected, or wanted on the stack's own module? It lets
  metadata run root code on every boot, which the image's cloud-init config avoids on purpose.
- Who will be the second user or team, and when? The day-2 plan's acceptance criterion 6 depends on it.
- The disk side of offboarding: who deletes a departed engineer's disk and snapshot, and when. The
  plan's draft posture copies sftp-host Plan C (warm two weeks, snapshot kept 30 days), but nobody has
  decided it.
- Is there a cost gate for tiers `m` and `l` beyond `terraform-prod` approval?
- Will `workstation` be upstreamed to `terraform-modules`, and on what trigger?
