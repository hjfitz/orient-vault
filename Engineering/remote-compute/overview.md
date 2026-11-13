---
tags:
- waypoint
- remote-compute
title: remote-compute — overview
thesis: remote-compute is the prod-only Terragrunt stack that gives an ILG engineer
  a persistent Arch Linux VM in GCP for running Claude Code. One prod.tfvars entry
  per workstation; it owns the VM's infrastructure and access, and the images repo
  owns everything inside the guest.
confidence: high
verified_paths:
- README.md
- iac/env
- iac/projects/remote-compute
- iac/modules/workstation
verified: '2026-11-13'
verified_sha: 8498e18
---
# remote-compute — overview

```orient-bluf
{ "v": 1, "bluf": "remote-compute is the prod-only Terragrunt stack that gives an ILG engineer a persistent Arch Linux VM in GCP for running Claude Code. One prod.tfvars entry per workstation; it owns the VM's infrastructure and access, and the images repo owns everything inside the guest.", "confidence": "high", "action": "Change a workstation only through its prod.tfvars entry. Never remove or rename an entry without the state-rm route in the README." }
```

## Responsibility

- **One workstation per entry** in `iac/env/prod.tfvars`, keyed by subdomain. Each entry gets a VM at `<key>.shell.platform.ilg.software` [1][2].
- **The infrastructure around each VM:** instance, a separate `/home` disk, a static external IP, a reserved internal IP, an A record and owner IAM [3].
- **The shared network edge:** the `remote-compute` subnet on the `ilg-platform` VPC, public tcp/22, and a deny on egress to private ranges [4].
- **Who may log in:** owners and their SSH public keys, written to the `rc-users` metadata key [3].
- **The self-serve path:** three Claude Code skills that open the PRs for an engineer [1].

## Why it exists separately

Workstations are long-lived, stateful and personal, unlike anything else in `ilg-platform-ec02`. The stack is built around keeping state: home disks and IPs survive every rebuild, and removal fails the plan on purpose [3].

It sits in `ilg-platform` because it is a shared engineering surface, open to any ILG engineer. It is not a contract other repos consume. Its consumers are people, through PRs and SSH.

The image is a separate repo because it has its own build cadence: weekly rebuilds, pinned by name [5]. The two meet only at instance metadata.

## Neighbours

```orient-flow
{ "v": 1, "title": "remote-compute in context",
  "nodes": [
    { "id": "eng", "label": "Engineer", "sub": "Claude Code skills in this repo", "kind": "external", "ev": [1] },
    { "id": "gha", "label": "github-actions", "sub": "terragrunt.yaml@0.1-affogato", "kind": "service", "service": "github-actions", "ev": [6] },
    { "id": "rc", "label": "remote-compute", "sub": "prod.tfvars → workstation module", "kind": "service", "service": "remote-compute", "tone": "accent", "ev": [2] },
    { "id": "gcpc", "label": "gcp-config", "sub": "VPC, state bucket, terraform-runner", "kind": "service", "service": "gcp-config", "ev": [4] },
    { "id": "core", "label": "ilg-platform-core-infra", "sub": "core-infra-prod-zone (DNS)", "kind": "service", "service": "ilg-platform-core-infra", "ev": [3] },
    { "id": "img", "label": "images", "sub": "remote-compute-arch-* image", "kind": "service", "service": "images", "ev": [5] },
    { "id": "vm", "label": "rc-<key> VM", "sub": "Arch, /home disk, static IP", "kind": "store", "ev": [3] }
  ],
  "edges": [
    { "from": "eng", "to": "rc", "label": "PR to prod.tfvars" },
    { "from": "gha", "to": "rc", "label": "plan on PR, apply behind terraform-prod" },
    { "from": "gcpc", "to": "rc", "label": "network, state, runner" },
    { "from": "core", "to": "rc", "label": "DNS zone" },
    { "from": "rc", "to": "vm", "label": "creates; rc-* metadata" },
    { "from": "img", "to": "vm", "label": "boot image, pinned by name" },
    { "from": "eng", "to": "vm", "label": "SSH: public :22, or IAP" }
  ] }
```

The arrow that matters is `rc → vm`. Every change to a running workstation is a metadata update or a planned replace from this stack.

## Where the reference lives

- **[[architecture]]**: the module, statefulness, access model, CI and guardrails.
- **[[known-context]]**: decisions, failure modes, what's in flight and the open questions.
- **The guest:** `packer/remote-compute/README.md` in `ilg-platform/images` covers boot order, accounts, idle stop and the toolchain [5].
- **User how-to:** Confluence, *Remote Compute Workstations (Claude Code)* in PLTE [7]. The repo README is the maintainer reference.

## What deliberately isn't here

- **Anything inside the VM.** Accounts, sshd, shutdown timers and packages are the image's job [5].
- **The VPC, state bucket and terraform-runner.** gcp-config owns them [4].
- **The DNS zone.** ilg-platform/core-infra owns it; this stack only writes A records [3].
- **Workstations defined in other repos.** A standalone module for that (PR #15) is being rejected [8].
- **Non-prod environments.** `env` must be `prod` [2].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "README.md@8498e18", "note": "skills table, maintainer reference, removal route" },
  { "id": 2, "kind": "code", "ref": "iac/projects/remote-compute/variables.tf@8498e18", "note": "workstations map, prod-only env validation" },
  { "id": 3, "kind": "code", "ref": "iac/modules/workstation/main.tf@8498e18", "note": "instance, metadata, lifecycle; disk/address/dns/iam.tf alongside" },
  { "id": 4, "kind": "code", "ref": "iac/projects/remote-compute/network.tf@8498e18", "note": "subnet on gcp-config's VPC, ssh allow, private egress deny" },
  { "id": 5, "kind": "code", "ref": "packer/remote-compute/README.md@3e289e8", "note": "ilg-platform/images: build cadence, metadata contract, boot order" },
  { "id": 6, "kind": "code", "ref": ".github/workflows/deploy.yaml@8498e18" },
  { "id": 7, "kind": "url", "ref": "https://globalfreight.atlassian.net/wiki/spaces/PLTE/pages/348356619" },
  { "id": 8, "kind": "pr", "ref": "ilg-platform/remote-compute#15", "note": "Harry, 2026-11-13: the standalone module is going to be rejected" }
] }
```
