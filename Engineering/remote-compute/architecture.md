---
tags:
- waypoint
- remote-compute
title: remote-compute — architecture
thesis: One Terragrunt project calls a local workstation module once per prod.tfvars
  entry. Each VM's home disk, IPs and host identity outlive the instance, guest behaviour
  is driven only by rc-* instance metadata, and a merge to main applies behind the
  terraform-prod Environment.
confidence: high
verified_paths:
- README.md
- iac
- .github/workflows
- scripts/sync-claude-config
verified: '2026-11-13'
verified_sha: 8498e18
---
# remote-compute — architecture

```orient-bluf
{ "v": 1, "bluf": "One Terragrunt project calls a local workstation module once per prod.tfvars entry. Each VM's home disk, IPs and host identity outlive the instance, guest behaviour is driven only by rc-* instance metadata, and a merge to main applies behind the terraform-prod Environment.", "confidence": "high", "action": "Removing or renaming an entry fails the plan by design: follow the README's state-rm route, never drop prevent_destroy." }
```

## Guardrails

- [policy:G1] Never delete or rename a `prod.tfvars` entry in one PR. The home disk and external IP carry `prevent_destroy`, which guards every VM at once. Use the README route: `state rm` both, then merge the deleting PR straight away with no apply pending.
  — paths: iac/env/prod.tfvars, iac/modules/workstation/disk.tf, iac/modules/workstation/address.tf
- [technical:G2] Move a VM to a new image only by pinning `default_image` by name and bumping that entry's `image_generation`. The instance ignores image changes, and the variable refuses an image family.
  — paths: iac/env/prod.tfvars, iac/modules/workstation/main.tf, iac/projects/remote-compute/variables.tf
- [contract:G3] The `rc-*` metadata keys are the whole contract with `ilg-platform/images` (`packer/remote-compute`). Renaming or reshaping one breaks the guest silently, so change both repos together.
  — paths: iac/modules/workstation/main.tf
- [policy:G4] SSH access changes only by reviewed PR. Approve an `ssh_keys` change only when its author owns the entry or the owner has confirmed. Never give owners `compute.instances.setMetadata`.
  — paths: iac/env/prod.tfvars, iac/projects/remote-compute/iam.tf
- [policy:G5] Keep `remote-compute-deny-private-egress` at priority 900. The VPC's allow-internal rule admits every port from 10.0.0.0/8, and these VMs face the internet.
  — paths: iac/projects/remote-compute/network.tf
- [technical:G6] Keep the owners' IAP grant project-level, conditioned on the reserved internal IP and port 22. An instance-level grant is lost on a same-name replace.
  — paths: iac/modules/workstation/iam.tf, iac/modules/workstation/address.tf

## Structure

```orient-flow
{ "v": 1, "title": "From a tfvars entry to a workstation",
  "nodes": [
    { "id": "tfv", "label": "iac/env/prod.tfvars", "sub": "workstations map, default_image", "kind": "step", "ev": [1] },
    { "id": "stack", "label": "remote-compute project", "sub": "validation, subnet, firewall, custom roles", "kind": "service", "service": "remote-compute", "tone": "accent", "ev": [2, 3] },
    { "id": "mod", "label": "module.workstation[key]", "sub": "for_each over workstations", "kind": "step", "ev": [4] },
    { "id": "inst", "label": "rc-<key> instance", "sub": "replaced only by image_generation", "kind": "service", "ev": [4] },
    { "id": "disk", "label": "rc-<key>-home disk", "sub": "prevent_destroy", "kind": "store", "tone": "alert", "ev": [5] },
    { "id": "eip", "label": "rc-<key> external IP", "sub": "prevent_destroy", "kind": "store", "tone": "alert", "ev": [6] },
    { "id": "iip", "label": "rc-<key>-internal IP", "sub": "IAP grant keys on it", "kind": "store", "ev": [6] },
    { "id": "dns", "label": "<key>.shell.platform.ilg.software", "sub": "A record, TTL 300", "kind": "external", "ev": [7] },
    { "id": "iam", "label": "owner IAM", "sub": "instance role + conditional IAP", "kind": "step", "ev": [8] }
  ],
  "edges": [
    { "from": "tfv", "to": "stack" },
    { "from": "stack", "to": "mod" },
    { "from": "mod", "to": "inst" },
    { "from": "mod", "to": "disk" },
    { "from": "mod", "to": "eip" },
    { "from": "mod", "to": "iip" },
    { "from": "eip", "to": "dns" },
    { "from": "mod", "to": "iam" }
  ] }
```

```
iac/env/prod.tfvars              the workstations + default_image (the only file most PRs touch)
iac/env/global.tfvars            project_id
iac/projects/root.hcl            tfvars wiring, pinned state bucket, generated GCS backend
iac/projects/remote-compute/
  variables.tf                   tiers map and ~20 validations on the workstations map
  main.tf                        DNS zone lookup + module.workstation for_each
  network.tf                     subnet, ssh allow, private-egress deny
  iam.tf                         remoteComputeOwner / remoteComputeUser custom roles
  imports.tf                     one-off import of rc-hjf's internal IP; a no-op now, deletable
iac/modules/workstation/         instance, disk, addresses, A record, owner IAM
.claude/skills/                  create-workstation, add-laptop, sync-claude-to-workstation
scripts/sync-claude-config       Python engine behind the sync skill
```

State is `gs://ilg-platform-tfstate-prod/remote-compute`. `root.hcl` pins the bucket rather than deriving it from `TF_VAR_env`, so a stray env can't point `init` at another bucket [9].

## The workstation module

| Resource | Survives an instance replace | Notes |
|---|---|---|
| `google_compute_instance.this` | — | tags `remote-compute`, `ssh-iap`; no service account; Secure Boot off (Arch kernel unsigned), vTPM and integrity on |
| `google_compute_disk.home` | yes, `prevent_destroy` | pd-balanced, attached as `device_name = "home"`; grows in place, can't shrink |
| `google_compute_address.this` (external) | yes, `prevent_destroy` | owners pin its host key in `known_hosts` |
| `google_compute_address.internal` | yes | the IAP condition matches on it |
| `google_dns_record_set.this` | yes | A record in `core-infra-prod-zone` |
| `google_compute_instance_iam_member.owner` | re-created | `replace_triggered_by` the instance id, since instance IAM dies with the instance |
| `google_iap_tunnel_iam_member.owner` | yes | project-level, `destination.ip == <internal IP> && destination.port == 22` |

**What changes in place and what replaces** [4]:

| Change | Effect |
|---|---|
| keys, owners, `idle_minutes`, `nightly_stop`, `workspace_repo` | metadata update in place, no restart |
| `tier` | `machine_type` update; `allow_stopping_for_update` stops and starts the VM |
| `home_disk_gb` up | disk resized in place; the image grows the filesystem at boot |
| `default_image` alone | nothing: the instance ignores `boot_disk.initialize_params.image` |
| `image_generation` bump | instance replaced onto `default_image`; `/home`, both IPs and host keys kept |
| entry removed or key renamed | plan fails on `prevent_destroy` (G1) |

A tier change should pin `home_disk_gb`. The default home size follows the tier, so s→m without a pin grows the disk for good, and m→s fails on `prevent_destroy` [10].

## Metadata: the contract with the image

The module writes these keys; the image reads them. There is no startup script and no guest agent [4][11].

| Key | Guest reader |
|---|---|
| `rc-users` (JSON `{username, uid, ssh_keys}`) | `rc-users.service` at boot; `rc-authorized-keys` on every login |
| `rc-idle-minutes`, `rc-nightly-stop` | `rc-idle-check` timer; `rc-nightly-stop.service` |
| `rc-team`, `rc-tier`, `rc-subdomain`, `rc-workspace-repo`, `rc-shell-domain` | `rc-vmenv.service` → `/etc/remote-compute/vm.env` |
| `enable-oslogin=FALSE`, `block-project-ssh-keys=TRUE` | nothing in the guest; they stop GCP-managed keys |

Keys are served live, so removing one refuses the next login with no reboot [11].

## Access

| Path | How |
|---|---|
| Public SSH | `remote-compute-ssh` allows tcp/22 from `ssh_source_ranges` (`0.0.0.0/0`) to tag `remote-compute`. Key only, with fail2ban in the guest [3][11]. |
| IAP SSH (fallback) | gcp-config's `ilg-platform-allow-iap-ssh` rule on tag `ssh-iap`, plus the conditional grant. Use `gcloud compute start-iap-tunnel` as a `ProxyCommand`, not `gcloud compute ssh`, which tries to write metadata [8][10]. |
| Start, stop, reset, serial log | `remoteComputeOwner` on the owner's own instance [8]. |
| gcloud project reads | `remoteComputeUser` at project level for every owner email [12]. |
| sudo | `wheel`, passwordless, from `rc-users` in the guest [11]. |

Owners must be `gfsdeliver.com` accounts, because IAM grants go to `user:<email>` [2]. Both custom roles get a 60 s `time_sleep` before their first binding, because a new role races it [12].

## Validation

`variables.tf` refuses a bad entry at plan time rather than at boot [2]:

- keys are DNS labels of 3–32 characters; `tier` is in the map;
- usernames match the Linux pattern and aren't an Arch system name;
- a uid is in 2000–59999, and one username keeps one uid across every workstation;
- SSH keys are single-line public keys, not repeated per owner, and never listed under two emails;
- `idle_minutes` is 0 or at least 5; `nightly_stop` is `off` or `HH:MM`.

Error messages name the owner and entry, never the key value, in case a private key was pasted [2].

## Interfaces

| Direction | Interface |
|---|---|
| In | PRs to `prod.tfvars`, opened by the skills or by hand |
| In | SSH from engineers' laptops (public or IAP) |
| Out | GCE, Cloud DNS and IAP APIs, as `terraform-runner@ilg-platform-ec02` |
| Out | `rc-*` instance metadata, read by the image |
| Depends on | gcp-config: VPC, IAP firewall rule, state bucket, terraform-runner and who may impersonate it |
| Depends on | ilg-platform/core-infra: `core-infra-prod-zone` |
| Depends on | ilg-platform/images: the `remote-compute-arch-<date>-<sha>` image |

## CI and deploy

| Workflow | Trigger | Does |
|---|---|---|
| `tf-plan-pr.yaml` | every PR to `main` | prod plan as a PR comment; a required check, so it has no path filter |
| `deploy.yaml` | push to `main` touching `iac/**` | plan, then apply behind `terraform-prod` |
| `manual-deploy.yaml` | `workflow_dispatch` | plan from any branch; apply only from a branch that contains `origin/main` |
| `secops.yaml` | PR and nightly | gitleaks and the Trivy IaC scan |

All call `ilg-platform/github-actions` `terragrunt.yaml@0.1-affogato` with `tf_version 1.9.0` and a 10-minute lock timeout [13]. Prod applies share one concurrency group, `remote-compute-prod-apply`, and a newer queued apply replaces an older pending one. Approve prod runs in merge order and cancel superseded ones, or an older run reverts a newer entry [1].

Trivy's GCP-0031 (instance has a public IP) is suppressed for `modules/workstation/main.tf` only, as a consequence of public SSH [14].

Local runs impersonate terraform-runner. Only principals in gcp-config's `terraform_runner_token_creator_members` can [1].

## Runtime

| Tier | Machine type | Default `/home` |
|---|---|---|
| `s` | `n2-custom-22-32768` (22 vCPU, 32 GiB) | 500 GB |
| `m` | `n2-standard-32` (32 vCPU, 128 GiB) | 1 TB |
| `l` | `n2-standard-64` (64 vCPU, 256 GiB) | 2 TB |

Every VM is in `europe-west2-a` with a 100 GB pd-balanced boot disk, on subnet 10.20.0.0/24 [2][3][4]. Idle and nightly shutdown are opt-in per entry and off by default [2].

## sync-claude-config

`scripts/sync-claude-config` copies a fixed set of a user's Claude Code setup to their workstation over SSH. It previews by default and copies with `--apply` [15]:

- **Copied:** `CLAUDE.md`, settings, skills, agents, commands, hooks, memory notes, and project roots' `CLAUDE.md`/`AGENTS.md`/skills.
- **Copied on request:** whole folders through `--folder`.
- **MCP servers:** merged into the workstation's `~/.claude.json` at mode 600, tokens included, and never printed.
- **Never copied:** secret-named files, credentials, history or Claude Code state.
- **Safety:** a gitleaks scan gates the copy, and every file is checked by sha256. A newer workstation copy is kept unless `--prefer-local` is passed.

The skill can install a weekday 17:30 systemd user timer. An unreachable workstation exits 75, a quiet skip [16].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "README.md@8498e18", "note": "maintainer reference: CI table, apply ordering, rebuild and removal routes" },
  { "id": 2, "kind": "code", "ref": "iac/projects/remote-compute/variables.tf@8498e18", "note": "tiers, workstations map and its validations, owner domains" },
  { "id": 3, "kind": "code", "ref": "iac/projects/remote-compute/network.tf@8498e18" },
  { "id": 4, "kind": "code", "ref": "iac/modules/workstation/main.tf@8498e18", "note": "metadata keys, ignore_changes on image, replace_triggered_by image_generation" },
  { "id": 5, "kind": "code", "ref": "iac/modules/workstation/disk.tf@8498e18" },
  { "id": 6, "kind": "code", "ref": "iac/modules/workstation/address.tf@8498e18" },
  { "id": 7, "kind": "code", "ref": "iac/modules/workstation/dns.tf@8498e18" },
  { "id": 8, "kind": "code", "ref": "iac/modules/workstation/iam.tf@8498e18", "note": "instance owner role, project-level conditional IAP grant" },
  { "id": 9, "kind": "code", "ref": "iac/projects/root.hcl@8498e18" },
  { "id": 10, "kind": "doc", "ref": "Engineering/remote-compute/plans/day-2-operations-tier-disk-owners-offboarding.md", "note": "tier/disk pinning, IAP replace root cause" },
  { "id": 11, "kind": "code", "ref": "packer/remote-compute/README.md@3e289e8", "note": "ilg-platform/images: metadata contract, accounts and keys, fail2ban" },
  { "id": 12, "kind": "code", "ref": "iac/projects/remote-compute/iam.tf@8498e18" },
  { "id": 13, "kind": "code", "ref": ".github/workflows/deploy.yaml@8498e18" },
  { "id": 14, "kind": "doc", "ref": "Engineering/remote-compute/plans/first-workstation-stack-module-and-one-engineer-.md", "note": "Decisions & deviations, 2026-10-29: Trivy GCP-0031 suppression" },
  { "id": 15, "kind": "code", "ref": "scripts/sync-claude-config@8498e18" },
  { "id": 16, "kind": "pr", "ref": "ilg-platform/remote-compute#10", "note": "weekday timer, exit 75 on unreachable" }
] }
```
