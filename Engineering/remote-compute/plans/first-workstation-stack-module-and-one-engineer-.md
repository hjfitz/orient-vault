---
ticket: none
title: 'First workstation: stack, module and one engineer on a VM'
service: remote-compute
status: active
created: '2026-10-29'
updated: '2026-11-02'
repo: /home/hjf/code/fuse/remote-compute
worktree: /home/hjf/code/fuse/remote-compute/.claude/worktrees/skeleton
branch: hjf/remote-compute-skeleton
base: origin/main
base_sha: 115fcd4
pr: '1'
tags:
- waypoint
- plan
impl_model: opus
impl_effort: medium
---
# none — First workstation: stack, module and one engineer on a VM

<!-- Guidance in this file is written as HTML comments: Obsidian hides them, agents read them,
     and `wp signoff` ignores them. Only <angle spans> are treated as unfilled placeholders, so
     they mark the places a human or agent must actually type something. Leave the comments in
     place — deleting them costs the next reader the guidance and gains nothing at the gate.

     SUPERSEDING A STATEMENT. This file is edited by several sessions over days. When something
     here stops being true, do NOT strike it through, delete it, or bury a correction inside it.
     Put one blockquote immediately ABOVE the stale text and leave the text alone:

         > SUPERSEDED 2026-09-04 — the monitor now lives in `gfs-bifrost/observability`.
         > Everything below is kept as the record of how it was first built here.

     One marker, always above, never inside. `wp decide` writes the dated entry in
     `## Decisions & deviations` that explains why. -->

## Intent
<!-- What we are changing and why. Link the ticket. -->
Out-of-ticket, platform work. A new repo, `ilg-platform/remote-compute`, lets an engineer get a GCP VM at least as capable as an engineering laptop to run Claude Code on, by adding one entry to a tfvars map in a PR. One Terragrunt stack, prod only, instantiates a local `iac/modules/workstation` module per entry, the way `gfs-bifrost/github-config` instantiates `iac/modules/repository`. Each VM gets a static IP and lands at `<subdomain>.shell.platform.ilg.software`, runs Arch Linux, takes SSH by public key only (keys declared per owner in tfvars, served live from instance metadata), and keeps `/home` on its own persistent disk.

Done means one engineer runs `ssh <user>@<sub>.shell.platform.ilg.software`, lands in tmux, runs `rc-setup`, and has `claude` working inside their team workspace clone. Sibling plans: [[remote-compute-vm-image-packer-ubuntu-24-04|images: the Arch VM image]] and [[day-2-operations-tier-disk-owners-offboarding|day-2 operations]].

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. From a laptop, `ssh <username>@<sub>.shell.platform.ilg.software` with a key listed for that owner in tfvars, and no password, lands in tmux `main`. `rc-setup` ends with `claude` running inside the team workspace clone.
- [ ] 2. A team's only edit is one `workstations` entry in `iac/env/prod.tfvars`. Its PR gets a prod plan comment, and merging applies it behind the `terraform-prod` Environment.
- [ ] 3. An owner can stop and start their own VM and reach it through an IAP tunnel, and gets a 403 describing or tunnelling to any other instance.
- [ ] 4. Bumping an entry's `image_generation` replaces the instance only. The home disk and static IP are untouched, a file written before the replace keeps its owner UID, and `rc-home` logs no `mkfs`.
- [ ] 5. Changing `default_image` alone plans no change to any existing instance.
- [ ] 6. A VM with `idle_minutes = 5` is TERMINATED within ~10 min of its last disconnect, while a running `claude -p` job keeps it up. A VM with `nightly_stop = "20:00"` logs a guest-initiated stop at 20:00 Europe/London.
- [ ] 7. Subnet `remote-compute` (europe-west2, 10.20.0.0/24, Private Google Access on) and firewall `remote-compute-ssh` exist. IAP SSH still works through `ilg-platform-allow-iap-ssh`.
- [ ] 8. On the live VM after first boot, `sshd -T` reports `passwordauthentication no`, `kbdinteractiveauthentication no`, `permitrootlogin no` and `authorizedkeysfile none`.
- [ ] 9. Removing a key from an owner's `ssh_keys` plans an in-place `metadata` update, and the next login with that key is refused with no reboot.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- **New repo `ilg-platform/remote-compute`**, created empty with `gh repo create` and laid out like `ilg-platform/core-infra`. Not from `ilg-platform/repo-template`, which is a NestJS Cloud Run scaffold wired to the Bifrost WIF pool.
  - `iac/projects/root.hcl`: copied from **gcp-config's** (default env `prod`), not core-infra's (default `dev`, `<env>/<stack>` prefix). Bucket `ilg-platform-tfstate-prod`, prefix `remote-compute`, `generate "backend"` (never `remote_state`).
  - `iac/projects/remote-compute/`: `versions.tf` (TF `>= 1.9`, google `~> 7.45`, as core-infra), `providers.tf`, `variables.tf`, `network.tf`, `iam.tf`, `main.tf`, `outputs.tf`, committed `.terraform.lock.hcl`.
  - `iac/modules/workstation/`: `main.tf` (instance), `disk.tf`, `address.tf`, `dns.tf`, `iam.tf`, `variables.tf`, `outputs.tf`, `versions.tf`, `files/startup.sh.tftpl`.
  - `iac/env/global.tfvars`, `iac/env/prod.tfvars` (`default_image`, `ssh_source_ranges`, `workstations`).
  - `.github/workflows/{deploy,manual-deploy,tf-plan-pr,secops}.yaml`: core-infra's, prod only, `@0.1-affogato`, `tf_version 1.9.0`. `tf-plan-pr` plans prod, keeps `**.tfvars` in `paths` and `pull-requests: write`. `manual-deploy` gets the ancestor check from sftp-connector. `secops-*` pinned `@0.2-bonbon`, not `@main`. Prod apply sets `notify_on_failure` + `slack_webhook`.
  - `mise.toml` (terraform 1.9.0, terragrunt 0.50.8), `README.md`.
- **Shared network `ilg-platform`** (owned by gcp-config): the stack adds a subnet and one firewall rule to it via `data "google_compute_network"`. The existing `ilg-platform-allow-iap-ssh` (tag `ssh-iap`) and `ilg-platform-allow-internal` (RFC1918, covers 10.20.0.0/24) already apply.
- **DNS zone `core-infra-prod-zone`** (`ilg.software.`, owned by `ilg-platform/core-infra`): A records under `shell.platform.ilg.software`, via `data "google_dns_managed_zone"` by name. `platform` is already claimed in core-infra's README. terraform-runner's `roles/editor` carries the record-set permissions, so no `dns_record_writer_sas` entry.
- **gcp-config** (where terraform-runner's roles and the WIF admission list live): one PR, a gate below.
- **The VM image** comes from [[remote-compute-vm-image-packer-ubuntu-24-04]] (Arch, family `remote-compute-arch`), pinned by image **name** in `prod.tfvars`, never by family. Its contract: metadata keys `rc-users`, `rc-idle-minutes` and `rc-nightly-stop`; disk `device_name = "home"`; `/etc/remote-compute/vm.env`; the `rc-setup` command.
- No Fuse MCP topic, type or service is touched.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **Module shape: standalone, raw `google_compute_*` resources.** `terraform-modules//compute/vm` needs Terraform `>= 1.14` against the fleet's 1.9.0, has no `attached_disk` or `allow_stopping_for_update`, and uses the ForceNew `metadata_startup_script`. Read on its `origin/main`. Upstream `workstation` to the catalog once it is stable.
- **Per-VM declaration is a map**, `workstations = map(object({...}))` keyed by subdomain, with one `for_each` module block. Each owner is `{ email, username, uid, ssh_keys }`:
  - `email` drives IAM and the `owner` label;
  - `username` and `uid` drive the Linux account; `uid` is explicit, in 2000–59999;
  - stack-level `validation` keeps each username→uid pair consistent across VMs and unique per uid.

  The key is immutable: renaming recreates.
- **Access is public key only, without OS Login (Arch).** The module writes `rc-users` metadata as JSON and sets `block-project-ssh-keys = "TRUE"` and `enable-oslogin = "FALSE"`. The image creates the users every boot and serves keys live through `AuthorizedKeysCommand`. Public keys aren't secrets, so tfvars is a fine home. Every key change is a reviewed PR and an in-place metadata update.
- **Offboarding is by PR (decided 2026-10-29, Harry).** Disabling someone's Workspace account no longer cuts their SSH; removing their owner entry, or their keys, does. That PR is part of leaver handling. A scheduled check that every owner email is still an active Workspace account was considered and left out; it would need Admin SDK access, and is a possible follow-up.
- **terraform-runner cannot set instance-level IAM today.** `compute.instances.setIamPolicy` is not in `roles/editor` or any of its other roles. Checked with `gcloud iam roles describe` and the live policy. The fix is `roles/compute.instanceAdmin.v1` in gcp-config, with the repo's `time_sleep` settle. The same gap class bit gcp-config (`iap.admin`) and core-infra (`artifactregistry.admin`).
- **Custom roles race their first binding.** `remoteComputeOwner` and `remoteComputeUser` each get a `time_sleep` before any binding, per gcp-config's `dns-roles.tf`. A first apply may still need a re-run.
- **Owner IAM is instance-level, apart from one read permission.**
  - Instance: custom `remoteComputeOwner` (`compute.instances.{get,start,stop,reset,getSerialPortOutput}`, deliberately no `setMetadata`), and `roles/iap.tunnelResourceAccessor` (`google_iap_tunnel_instance_iam_member`).
  - Project: custom `remoteComputeUser` (`compute.projects.get`, `compute.zones.{get,list}`, `compute.zoneOperations.get`) for gcloud.
  - The IAP path is `ssh -o ProxyCommand='gcloud compute start-iap-tunnel %h 22 --listen-on-stdin --zone europe-west2-a' <user>@<instance>`. `gcloud compute ssh` would try to push keys into metadata, which owners can't do.
  - Sudo comes from `rc-users`: `wheel`, NOPASSWD, since nobody has a password.
- **No service account on the VMs.** The project's default compute SA is disabled, and an omitted `service_account` block gives no SA (provider source).
- **Stateful by construction.**
  - The home disk and the static IP carry `prevent_destroy`; the disk is attached with `attached_disk`, which is not ForceNew.
  - `boot_disk.initialize_params.image` is ForceNew, so the instance carries `ignore_changes` on it plus `replace_triggered_by = [terraform_data.image_generation]`, from the first apply.
  - `metadata` is an in-place map, and `metadata_startup_script` is never used.
  - The UID is explicit, so ownership survives a replace by construction.
- **Shielded VM: Secure Boot off.** Arch's kernel is unsigned; vTPM and integrity monitoring stay on.
- **Nightly stop and idle shutdown run in the guest**, from the image's timers reading metadata. A compute instance-schedule policy was rejected because changing `resource_policies` recreates the instance.
- **The first VM runs with `nightly_stop = "off"` until owner self-service (inc 3) lands.**
- **Bootstrap applies are local until CI is admitted** (gcp-config's documented route for a new stack; Harry is a token creator on terraform-runner).
- **Prices are unverified.** The Billing Catalog API returned 403 from every quota project available.
- **Tier shapes.** `n2-custom-22-32768` exists in europe-west2-a (22 vCPU, 32 GiB), checked live, which matches the laptop. `n2d-standard-*` and `c3-standard-22` exist in all three London zones. `c3d-standard-*` does not exist in London. Disks are pd-balanced.
- **Tiers (decided 2026-10-29, Harry):** `s = n2-custom-22-32768` (22 vCPU / 32 GiB, laptop parity), `m = n2-standard-32` (32 / 128 GiB), `l = n2-standard-64` (64 / 256 GiB). Home disks default to 500 GB, 1 TB and 2 TB.
- **Repo access and approvers mirror core-infra (decided 2026-10-29).**
  - `terraform-prod` required reviewers: `harry-fitzgerald_gfsdev` and `kyle-chandler_gfsdev`, as on core-infra (read via the environments API).
  - Write access is the org default, which in `ilg-platform` is **admin** for every member; core-infra has no extra teams and no branch protection.
  - Risk carried: any org member can edit the Environment's reviewers or bypass rules, and every PR plan runs as the owner-equivalent terraform-runner. That is the same exposure core-infra already has, so it is a fleet-level fix, not this repo's.
- **Public tcp/22 is accepted (decided 2026-10-29, Harry), with a durable record.** It is key-only with fail2ban and `ssh_source_ranges = ["0.0.0.0/0"]`, flippable to an allowlist later. Every other VM here is IAP-only, and the IAP path stays as the fallback. With OS Login gone, Wolf's project-level `roles/compute.osLogin` no longer reaches these VMs.
- **Logging and Monitoring get enabled (decided 2026-10-29, Harry).** The gcp-config PR adds `logging.googleapis.com` and `monitoring.googleapis.com` to `activate_apis`, project-wide. The image needs no agent for the audit trail of instance and IAM changes. sshd's own login lines stay on the VM's journal unless the Ops Agent is added later.

## Increments
<!-- Each independently implementable AND verifiable. Cite the criteria it discharges as
     (AC n,n). Tick with `wp tick`, which stamps `— done: <sha>` from HEAD; never hand-write it.
     Prefer 3-7 — more usually means the ticket is too big, so say that rather than splitting
     hairs.

     A PRECONDITION THAT IS NOT CODE goes on its own indented `gate:` line, with a confirmation
     box under it. Sign-off blocks on a ticked increment sitting above an unconfirmed gate, and
     `wp brief` shows unmet gates in its NEXT block — so "do not action this yet" stops being
     bold prose a fresh session can miss:

         - [x] 6. Widen the subscription filter (AC 6) — verify: filter matches in dev — done: 8e62c5a
               gate: FUSE-1052 AND FUSE-1053 confirmed in prod
                     [ ] confirmed
-->

- [x] 1. **Repo skeleton and network.** Create the repo, add `root.hcl`, versions, providers, variables, workflows (not yet runnable), `mise.toml`, and `network.tf` (subnet + `remote-compute-ssh` firewall, `source_ranges = var.ssh_source_ranges`, target tag `remote-compute`). Local apply. (AC 7) — verify: `terragrunt init` creates the state object under `gs://ilg-platform-tfstate-prod/remote-compute/`; plan is exactly subnet + firewall; `subnets describe` and `firewall-rules describe` match after apply. — done: 28a12d9
      gate: `ilg-platform/remote-compute` exists (`gh repo view ilg-platform/remote-compute`)
            [x] confirmed
- [x] 2. **Workstation module and the first VM on Arch's unmodified cloud image.** This adds: — done: 530bc1d
  - the instance: `rc-users`, `block-project-ssh-keys`, `enable-oslogin=FALSE`, every `rc-*` key and `startup-script` in metadata; labels; tags `remote-compute` and `ssh-iap`; `allow_stopping_for_update`; the `ignore_changes`/`replace_triggered_by` pair; Shielded VM with Secure Boot off;
  - the home disk, the static IP, and the owner's IAP tunnel member;
  - `default_image` = the images plan's `arch-cloudimg-<date>` base;
  - Harry's entry with `nightly_stop = "off"`, plus his key in `ssh-keys` metadata for cloud-init's default `arch` user (stock image only).

  Local apply. — verify: plan is instance + disk + address + IAM member; `ssh arch@<ip>` works; `ls /dev/disk/by-id/` shows the home disk; `/etc/remote-compute/vm.env` matches tfvars; editing `idle_minutes` plans an in-place `metadata` update.
      gate: gcp-config PR applied: terraform-runner holds `roles/compute.instanceAdmin.v1` (`gcloud projects get-iam-policy ilg-platform-ec02 --flatten=bindings[].members --filter=bindings.members:terraform-runner@` lists it)
            [x] confirmed
      gate: the images plan's inc 1 base image exists (`gcloud compute images list --filter=name~^arch-cloudimg- --project ilg-platform-ec02`)
            [x] confirmed
- [x] 3. **Owner self-service roles.** `remoteComputeOwner` (instance) and `remoteComputeUser` (project), each behind a `time_sleep`. Local apply. (AC 3) — verify: as the owner, `gcloud compute instances stop` then `start` succeeds; the IAP ProxyCommand ssh lands; `describe example-vm` is a 403. — done: 530bc1d
- [x] 4. **DNS and hostname.** `dns.tf` in the module, `data "google_dns_managed_zone"` by name, TTL 300. Local apply. — verify: `dig +short <sub>.shell.platform.ilg.software` returns the static IP; `ssh arch@<sub>.shell.platform.ilg.software` lands. — done: 530bc1d
- [x] 5. **CI proven.** A trivial tfvars change through a PR. All applies go through CI from here. (AC 2) — verify: a prod plan comment on the PR; secops green; merge runs plan-prod, then `terraform-prod` approval, then apply; the run URL in Evidence. — done: 5b24418
      gate: gcp-config PR applied: terraform-runner's SA policy lists `principalSet://…/attribute.repository/ilg-platform/remote-compute` under `roles/iam.workloadIdentityUser`
            [x] confirmed
      gate: repo variables `WORKLOAD_IDENTITY_PROVIDER` / `WORKLOAD_IDENTITY_SERVICE_ACCOUNT` copied from core-infra, not gcp-config
            [x] confirmed
      gate: `terraform-prod` Environment exists with required reviewers `harry-fitzgerald_gfsdev` and `kyle-chandler_gfsdev`; branch protection requires the plan check, set after its first run
            [x] confirmed
- [ ] 6. **Switch to the Packer image: no-roll, then stateful replace.** Two applies: first `default_image` alone moves to the pinned `remote-compute-arch-*` name, then Harry's `image_generation` goes 1 → 2. The stock-image `ssh-keys` entry is removed in the same change. (AC 4,5,8,9) — verify:
  - the first plan shows no instance change;
  - the second replaces the instance only, disk and address untouched;
  - Harry logs in as his `rc-users` username, a marker file keeps its UID, and `rc-home` shows no `mkfs`;
  - `sshd -T` matches AC 8;
  - a tfvars key removal is refused at the next login (AC 9).
      gate: the images plan's first `remote-compute-arch` image exists
            [x] confirmed
- [ ] 7. **Acceptance run: first login and lifecycle on the real VM.** Set `idle_minutes = 5` and `nightly_stop = "20:00"` through CI. (AC 1,6) — verify: AC 1 end to end from a laptop, by an engineer other than the author if one is available; TERMINATED within ~10 min of disconnecting; a `claude -p` loop keeps it up; next morning the 20:00 guest stop is in `gcloud compute operations list` and the owner starts it themselves.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-11-02 [AC 3 restored] Manual prod apply from `main` (`9e41313`, run 41453736044), agreed by Harry after a local plan of exactly `1 to add` (the hjf IAP tunnel member). Applied `1 added, 0 changed, 0 destroyed`; the live IAP policy shows `tunnelResourceAccessor` for Harry. The IAP ProxyCommand ssh returned `IAP_OK` after ~45 s of propagation. The root cause (the binding lost after an `image_generation` replace) is still open: day-2.
- 2026-11-02 [inc 6] Two applies. First, ilg-platform/remote-compute#3 (`84596c6`), which moved `default_image` to `remote-compute-arch-20261102-fcbcd58`, made idle and nightly shutdown opt-in, and added `rc-shell-domain`. Prod plan `0 to add, 1 to change, 0 to destroy`: an in-place metadata update on `rc-hjf`, so the new default image touched no instance (AC 5). Then #4 (`8e62c5a`), `image_generation` 1→2, prod plan `3 to add, 1 to change, 3 to destroy`: the instance and its two owner IAM members replaced; disk, IP and A record untouched. Apply: instance created in 27 s, no stockout.
- 2026-11-02 [inc 6, as Harry] `ssh harry@hjf.shell.platform.ilg.software` worked within ~5 s:
  - `id`: uid=2001(harry), groups wheel and docker.
  - `/home` is `/dev/sdb` ext4, 492 GB.
  - `vm.env` correct, including `RC_SHELL_DOMAIN`; 4 host keys saved to `/home/.rc/ssh`.
  - `sshd -T`: PermitRootLogin no, PasswordAuthentication no, AuthorizedKeysCommand `rc-authorized-keys %u`.
  - Lateral to example-vm blocked; `is-system-running` = running.
  - The interactive login landed in tmux `main` with the banner (OPERATOR harry, TERMINAL hjf.shell.platform.ilg.software) and the `rc-setup` notice.
- 2026-10-29 [inc 2,3,4] ilg-platform/remote-compute#2 merged (530bc1d). Two self-review rounds (rollout/conventions + correctness/security, then a review-panel delta of platform + security, then an inline review of the 30-line round-2 delta). Fixed: owner IAM re-bound on instance replace (simulated), startup-script dropped, Arch reserved usernames, key/idle/disk/image/email validation, `trivy.yaml` so CI evaluates the module (CI log: `Loaded trivy.yaml`, 6 config files), lock timeouts on plan and apply. Deploy run 40906946030: prod plan 13 to add, 0 to change, 0 to destroy; shared with Harry, he agreed; `Apply complete! Resources: 13 added`.
- 2026-10-29 [inc 2] `rc-hjf` RUNNING, `n2-custom-22-32768`, NAT IP 34.89.115.64, tags `remote-compute,ssh-iap`, disks `persistent-disk-0,home`, labels team/tier/owner/stack. `ssh arch@hjf.shell.platform.ilg.software` logged in on the 2nd attempt (Arch 7.2.9). `Google_PersistentDisk_home` is present. A connection to example-vm 10.10.0.2:22 is **blocked** by the egress deny; `https://github.com` returns 200. Editing `idle_minutes` 60→90 plans `0 to add, 1 to change` (in-place `rc-idle-minutes`). `main` plans `No changes` after the apply (no metadata drift).
- 2026-10-29 [inc 3] As Harry (own identity): `gcloud compute instances stop rc-hjf` → TERMINATED, `start` → RUNNING. Instance policy has `remoteComputeOwner` for Harry; the IAP tunnel policy has `tunnelResourceAccessor` for Harry. The IAP ProxyCommand ssh returned `IAP_OK` on the second minute; the first try was 4033 while the new binding propagated.
- 2026-10-29 [inc 4] `dig +short hjf.shell.platform.ilg.software` → 34.89.115.64, from the zone's nameserver and the public resolver.
- 2026-10-29 [inc 5] ilg-platform/remote-compute#1 merged (5b24418). PR CI: `plan / terragrunt` prod plan "No changes" against the real backend (refreshed both resources), gitleaks and Trivy (scan-ref `iac/projects/remote-compute`, 2 config files) green. Deploy run 40902519000: plan-prod No changes → `terraform-prod` approved (`/ship SHIP-1029-remote-compute-workstations`) → apply-prod `0 added, 0 changed, 0 destroyed`. Repo vars set; `terraform-prod` reviewers harry-fitzgerald_gfsdev + kyle-chandler_gfsdev; `main` protected (PR required, strict checks: plan, gitleaks, Trivy; no force-push/delete; admins not enforced because the org default is admin).
- 2026-10-29 [gates inc 2, inc 5] ilg-platform/gcp-config#11 applied (run 40897729452: 4 added, 1 changed, 0 destroyed). terraform-runner holds `roles/compute.instanceAdmin.v1`; its SA policy lists `principalSet://…/attribute.repository/ilg-platform/remote-compute` as `workloadIdentityUser`; `ilg-platform-tfstate-prod` grants it `objectUser` on `remote-compute/`; logging + monitoring APIs enabled.
- 2026-10-29 [inc 1] Local `terraform apply` of the saved plan as terraform-runner (impersonation), branch `hjf/remote-compute-skeleton` @ `28a12d9`: 2 added, 0 changed, 0 destroyed. `subnets describe remote-compute` → 10.20.0.0/24, europe-west2, privateIpGoogleAccess True; `firewall-rules describe remote-compute-ssh` → INGRESS tcp:22 from 0.0.0.0/0 to tag `remote-compute`. State at `gs://ilg-platform-tfstate-prod/remote-compute/default.tfstate`. Gate confirmed: repo `ilg-platform/remote-compute` exists (internal).
- <YYYY-MM-DD> [inc <n>] <what was run, against what, and the observable result>

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- **AC 3 regressed after the inc 6 replace (found 2026-11-02, ~13:00).** rc-hjf's IAP tunnel policy is empty (`etag ACAB`) although the apply log shows the old binding destroyed at 11:17:29 and the new one created at 11:18:08. Every plan since shows `module.workstation["hjf"].google_iap_tunnel_instance_iam_member.owner` to create. The compute instance IAM binding survived. The likely cause, unproven, is asynchronous cleanup of the deleted same-named instance's IAP policy wiping the new binding. Consequence: every `image_generation` bump loses the owner's IAP fallback until a later apply recreates it. Normal SSH is unaffected.
- AC 4's "a file keeps its owner UID across a replace" on rc-hjf itself. This replace moved off the stock image, which never formatted the home disk, so there was no prior file. The same image proved it on throwaway VMs (images plan, evidence (f) and r3). The next `image_generation` bump on rc-hjf will show it.
- AC 1's last step (`rc-setup` through to `claude` running) needs Harry's own gh and Claude browser logins.
- AC 6 (idle and nightly stop on a real workstation). Both are now opt-in and off on rc-hjf; the behaviour is proven on the image's throwaway VMs.
- AC 3's negative case (an owner gets 403 on other instances): Harry holds project `roles/viewer` through platform-engineering@, so describing example-vm succeeds for him. It needs an owner outside that group; proven in the day-2 plan's second-team increment.
- AC 8 (`sshd -T` hardening) and AC 9 (live key revocation): stock image only so far. Stock sshd allows password auth (no account has a password). Proven at inc 6 on the Packer image.
- <what remains unproven, and what would prove it>

## Rollout & rollback
<!-- Added on demand. Written at plan time; amend in place as it changes.
     `Shared state touched:` is the single home for the five classes git does not own — a dev
     deploy, a prod config write, a Datadog monitor, a CI var or secret, cross-repo IaC. Reverting
     the branch undoes none of them, so if they are not written here they are not written down. -->

- **Order:**
  1. gcp-config PR first, one PR: `ilg_pool_repositories` += `ilg-platform/remote-compute`; `state_stacks` += `remote-compute = { prod = "terraform-runner@ilg-platform-ec02.iam.gserviceaccount.com" }`; terraform-runner += `roles/compute.instanceAdmin.v1` with a `time_sleep`; `activate_apis` += `logging.googleapis.com`, `monitoring.googleapis.com`. It blocks inc 2 (instance IAM) and inc 5 (CI), nothing else.
  2. Incs 1–4 run by local apply. Inc 1 runs in parallel with everything; inc 2 needs only the images plan's inc 1, a local import of Arch's cloud image. Everything after that runs in parallel with the images plan.
  3. Inc 5 moves applies to CI. Inc 6 waits for the images plan's first image. Inc 7 is the acceptance run.
- **Flags/config:** per-VM `owners` (email, username, uid, ssh_keys), `idle_minutes`, `nightly_stop`, `image_generation`, `tier`, `home_disk_gb` in `prod.tfvars`; stack-wide `default_image` and `ssh_source_ranges` (default `["0.0.0.0/0"]`).
- **One-way doors:** the static IP and its A record. Once an engineer has the hostname in `known_hosts`, changing the IP or host key breaks them. Both resources carry `prevent_destroy`.
- **Rollback:**
  - Incs 1–5: `git revert` and apply, except the home disk and IP, which `prevent_destroy` refuses to destroy. That is intended; removal is the day-2 plan's offboarding route.
  - Inc 6: set `default_image` back and bump `image_generation` again; the home disk survives.
  - A `manual-deploy` from a stale branch would drop a teammate's entry. `prevent_destroy` turns that into a plan error, but tier, disk-size and metadata changes would revert silently. The ancestor check in `manual-deploy.yaml` prevents it. The README rule: approve prod runs in merge order and cancel superseded ones.
- **Shared state touched:**
  - **Cross-repo IaC:** gcp-config (WIF admission, state_stacks, runner role, project APIs).
  - **A prod config write:** new A records in `core-infra-prod-zone`, under `shell.platform.ilg.software` only.
  - **The shared VPC `ilg-platform`:** one subnet and one firewall rule.
  - **CI vars:** `WORKLOAD_IDENTITY_PROVIDER`, `WORKLOAD_IDENTITY_SERVICE_ACCOUNT` and the `terraform-prod` Environment on the new repo.
  - **Project IAM:** two custom roles.
  - **Instance metadata `rc-users`:** whoever holds `compute.instances.setMetadata` can add a login key outside a PR. Today that is project editors only (terraform-runner and the disabled default compute SA); the owner role deliberately leaves it out.
- **Proof in prod:** AC 1 run by an engineer other than the author; `gcloud compute instances list --filter=labels.stack=remote-compute` shows the VM with its `team` label.

## Options considered
<!-- Added on demand. Why this approach and not the others — the thing the planning agent is
     asked for and the plan has otherwise had nowhere to put. Promote to a durable record with
     `wp decide --record` when it is worth defending in a review six months out. -->

- **Chosen: own VMs from a local Terraform module.** It gives a plain SSH hostname, a Packer image the platform controls, and nothing new to run.
- **Rejected: Google Cloud Workstations.** It brings managed images, idle timeout and a browser IDE. But access goes through its own gateway rather than `ssh <host>`, images are containers rather than the Packer VM image, and there is a per-cluster control-plane fee (unverified) plus a new API and cluster to run. Revisit if the hostname requirement goes.
- **Rejected: wrapping `terraform-modules//compute/vm`.** It needs Terraform `>= 1.14` and five additive features, plus a CI app token for the git source.
- **Rejected: OS Login** (2026-10-29, with the switch to Arch). Google's guest agent and OS Login modules aren't packaged for Arch, and the AUR copies are stale. Keys in tfvars, served by `AuthorizedKeysCommand` from metadata, keep login key-only and make every key change a reviewed PR. What's lost: IAM-backed revocation (disabling a Workspace account no longer cuts SSH; the key must be removed) and Google-assigned UIDs (set explicitly instead).
- **Rejected: Ubuntu 24.04** (the first draft). It has Google's guest agent, OS Login and unattended security upgrades, but Harry chose Arch.
- **Rejected: project-level `roles/compute.osLogin`** (the `compute/vm` way). It grants SSH to every OS Login VM in the project.
- **Rejected: a compute instance-schedule resource policy.** Changing `resource_policies` recreates stateful VMs.
- **Rejected: an image-family reference in the stack.** Every image rebuild would plan a replace of every VM.
- **Rejected: Cloud NAT with no external IP.** It contradicts the per-VM hostname.
- **Rejected: a GitHub App token at first boot to clone the workspace.** It needs an SA on the VM and a long-lived app key every VM can read, and pushes still need the engineer's own identity.
- **Tiers.** On-demand estimates only, unverified. `n2-custom` carries a premium per unit. Home disks are pd-balanced, boot disks 100 GB.

  | tier | machine type | vCPU / RAM | home default | est. $/h |
  |---|---|---|---|---|
  | s | `n2-custom-22-32768` | 22 / 32 GiB | 500 GB | ~0.9 |
  | m | `n2-standard-32` | 32 / 128 GiB | 1 TB | ~1.6 |
  | l | `n2-standard-64` | 64 / 256 GiB | 2 TB | ~3.2 |

  A stopped VM still costs its disks and its static IP: roughly $70 a month for a tier-s VM, mostly the 500 GB home disk.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-11-02 (Harry Fitzgerald)** — Idle and nightly shutdown are opt-in (defaults idle_minutes=0, nightly_stop=off). Owners often leave software running overnight.

- **2026-10-29** — vm.env cannot appear on the stock-image VM: Arch has no guest agent, so nothing runs startup-script until the Packer image adds a runner. Inc 2's vm.env check moves to inc 6.

- **2026-10-29** — Trivy GCP-0031 (instance has a public IP, HIGH) is suppressed in .trivyignore.yaml for **/modules/workstation/main.tf only. It follows from the accepted per-VM hostname and public SSH decision. Inline #trivy:ignore doesn't work because Trivy reports the finding through the module call. The old AVD-GCP-0027 entry was dead (Trivy 0.70 uses GCP-* ids, and the rule didn't fire).

- **2026-10-29** — Increments 2-4 ship as one PR (module + first VM + owner roles + DNS), verified per increment after its apply. It also carries PR #1's review fixes: an EGRESS deny to RFC1918 for tag remote-compute (priority 900, so allow-internal can't be used for lateral movement), deploy concurrency groups, a prod-only env validation, apply-only ancestor check, import/refresh var files, and the Trivy scan widened to iac/.

- **2026-10-29 (Harry Fitzgerald)** — Tiers s=n2-custom-22-32768, m=n2-standard-32, l=n2-standard-64; Logging+Monitoring enabled project-wide via gcp-config; repo access and terraform-prod reviewers (Harry, Kyle Chandler) mirror core-infra.

- **2026-10-29 (Harry Fitzgerald)** — Offboarding cuts SSH by PR (remove the owner entry or keys); no Workspace active-account check for now, a possible follow-up.

- **2026-10-29 (Harry Fitzgerald)** — 2026-10-29: VM OS switched to Arch Linux before activation. OS Login dropped (not maintained on Arch); owners are {email, username, uid, ssh_keys} in tfvars, served from rc-users metadata via AuthorizedKeysCommand; Secure Boot off; first VM boots Arch's unmodified cloud image.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
- **N2 stockouts in europe-west2-a** (2026-11-02): n2-standard-2 and n2-standard-4 creates failed with STOCKOUT. A workstation replace (`image_generation` bump) or a start can fail there until capacity returns. The zone is fixed in the stack (`var.zone`); per-entry zones are a follow-up if this recurs.
- **OpenSSH sends only the first `-o SetEnv`.** Several variables go in one, space-separated: `ssh -o SetEnv="RC_NO_TMUX=1 NO_COLOR=1"`.
- **tmux `-t main` matches by prefix**, so `maintenance` counts. Use `=main` for session targets and `=main:` where a pane target is expected (`set-hook`, `show-hooks`, `display-message`).
- terraform-runner on `ilg-platform-ec02` cannot set **instance-level** compute IAM: `compute.instances.setIamPolicy` is in `compute.instanceAdmin.v1`, `compute.admin` and `owner` only. This is the third resource-level IAM gap after `iap.admin` and `artifactregistry.admin`.
- **Cloud Logging and Monitoring are not enabled on `ilg-platform-ec02`**, so nothing in that project has an audit or metrics trail.
- `Engineering/gcp-config/ledger.md`'s newest entry (2026-10-28, MKP-19, "Grant terraform-runner compute.instanceAdmin.v1") is `ilg-merak/gcp-config#7`, a different repo and project. It reads as if ilg-platform's runner already has that role. It does not; the entry needs moving.
- `ilg-platform/repo-template` is a NestJS Cloud Run scaffold wired to the Bifrost pool (`661226359806`, `github-integration@bifrost-dev-global1`). It is the wrong seed for an IaC-only ilg-platform repo.
- On Arch there is no OS Login, so these VMs are the first in `ilg-platform-ec02` whose SSH access isn't IAM-backed. Login keys live in instance metadata, and `compute.instances.setMetadata` is now an access-granting permission there.
- **Deferred with permissions (2026-10-29):** the images repo's main-branch principal holds `roles/compute.storageAdmin` project-wide, which includes creating disk snapshots, so it could snapshot `rc-*-home` disks that hold Claude and gh credentials. `prevent_destroy` guards only Terraform. Scope it down with the CI-identity hardening.
- `Engineering/github-actions` `architecture.md` and `overview.md` are STALE: tag positions moved (`0.1-affogato` 2e47b65, `0.2-bonbon` 8cb1511), Datadog keys are optional, and `secrets_hub_url` is missing. Needs `waypoint-refresh`.
