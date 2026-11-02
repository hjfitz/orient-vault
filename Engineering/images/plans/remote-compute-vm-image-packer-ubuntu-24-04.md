---
ticket: none
title: remote-compute VM image (Packer, Arch Linux)
service: images
status: active
created: '2026-10-29'
updated: '2026-10-29'
repo: /home/hjf/code/fuse/images
worktree: /home/hjf/code/fuse/images/.claude/worktrees/remote-compute-vm-image
branch: hjf/remote-compute-vm-image
base: origin/main
base_sha: unknown
pr: '14'
tags:
- waypoint
- plan
impl_model: opus
impl_effort: medium
---
# none — remote-compute VM image (Packer, Arch Linux)

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
Out-of-ticket, platform work. `ilg-platform/images` builds its first **VM** image: an **Arch Linux** Compute Engine image, for [[first-workstation-stack-module-and-one-engineer-|remote-compute workstations]].
- It starts from Arch's own cloud image (`Arch-Linux-x86_64-cloudimg.qcow2`, built by arch-boxes, signature-checked).
- Packer's `qemu` builder customises it on the CI runner, and the `googlecompute-import` post-processor uploads it into family `remote-compute-arch` in `ilg-platform-ec02`.
- It bakes the toolchain, hardened sshd with keys served live from instance metadata, the `/home` disk mount, the idle and nightly shutdown timers, and a first-login script.

Done means a VM booted from the image, with a blank disk attached as `home` and an owner in its metadata, mounts the disk before sshd. The owner logs in with their key, and the VM shuts down when idle and walks the user through `rc-setup` to a working `claude`.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. `gcloud compute images describe-from-family remote-compute-arch --project ilg-platform-ec02` returns `remote-compute-arch-<yyyymmdd>-<sha7>`, built by the `main` workflow through Workload Identity.
- [ ] 2. A PR touching `packer/**` runs `packer fmt -check`, `packer validate` and shellcheck as a check. It is not a required check, because path-filtered required checks would block every non-Packer PR in this repo.
- [ ] 3. Build-time smoke inside the qemu VM checks:
  - the tool versions;
  - the `sshd -T` posture: `passwordauthentication no`, `authorizedkeysfile none`, `authorizedkeyscommand` set;
  - the enabled units and `fail2ban-client -t`;
  - that both `OnCalendar` expressions parse in Europe/London;
  - that no package came from the AUR (`pacman -Qm` is empty).
- [ ] 4. On a VM booted from the image with a blank disk attached as `home`:
  - `/dev/disk/by-id/google-home` exists;
  - `rc-home` formats and mounts `/home` before `ssh.service`;
  - on reboot it mounts with no `mkfs`.
- [ ] 5. An owner listed in the `rc-users` metadata logs in with their key, as their configured UID, with sudo. Removing the key from metadata refuses the next login with no reboot. Password and keyboard-interactive auth are refused.
- [ ] 6. `rc-idle-minutes=N` powers the VM off within N + 5 minutes of the last disconnect (one timer tick of slack), and a running `claude -p` job keeps it up past the threshold.
- [ ] 7. Interactive SSH lands in tmux `main`, and the MOTD names `rc-setup`. A second `rc-setup` run is a no-op. Four failed SSH attempts produce a ban in `fail2ban-client status sshd`.
- [ ] 9. `rc-upgrade` shows the Arch news since the last upgrade before running `pacman -Syu`, and stamps the upgrade time. With the stamp backdated 15 days, the MOTD shows the upgrade warning; with a fresh stamp it doesn't. No timer or unit runs pacman.
- [ ] 8. Pruning never removes the image name remote-compute's `prod.tfvars` pins, and keeps at least 30 days of images.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- **New `packer/remote-compute/`**:
  - `arch.pkr.hcl`: a `qemu` source from the downloaded cloud image (`disk_image = true`, `accelerator = "kvm"`, `format = "raw"`), SSH key injected through a cloud-init seed ISO, and the `googlecompute-import` post-processor with `bucket` = the staging bucket and `image_family = "remote-compute-arch"`, `image_guest_os_features = ["UEFI_COMPATIBLE"]` (UEFI boot proven in inc 1).
  - `scripts/fetch-base.sh`: downloads the latest cloud image and verifies its `.sig` against the pinned Arch release signing key before Packer sees it.
  - `provisioners/{00-base,10-toolchain,20-claude,30-sshd-users,40-systemd,50-first-login,90-smoke}.sh` and `files/`.
- **New `.github/workflows/remote-compute-vm.yaml`.** On PRs: validate. On `main`, `workflow_dispatch` and a weekly schedule: `auth@v3` with the provider only, then fetch-base, `packer build`, prune. `golden-image.yaml` is container-only and stays untouched.
- **README.md / CLAUDE.md** get a "VM images" section. The container fleet contract is scoped to container images. The VM image states its own rules: consumers pin it by name, never by family; it is rebuilt weekly; it uses official repos and vendor tarballs only, never the AUR.
- **core-infra** (a gate below), one change set in `vm-images.tf`, prod state path only. Builds create no VM in GCP, so the grant is narrower than an instance-admin role. It adds:
  - a staging bucket `ilg-platform-vm-image-staging` (uniform access, 7-day delete lifecycle);
  - `roles/storage.objectAdmin` on that bucket and `roles/compute.storageAdmin` on the project, both for the subject-pinned principal;
  - a row in core-infra's README Access table.
- **The image's contract with remote-compute**, which is API surface:
  - metadata keys `rc-users` (JSON: username, uid, ssh_keys), `rc-idle-minutes`, `rc-nightly-stop`, `rc-team`, `rc-tier`, `rc-subdomain` and `rc-workspace-repo`. There is no `startup-script`: the image builds `/etc/remote-compute/vm.env` itself from the `rc-*` keys, in a unit ordered before ssh;
  - disk `device_name = "home"`, surfaced as `google-home` by the image's own udev rule;
  - `/etc/remote-compute/vm.env`;
  - the `rc-setup` command.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **Google publishes no Arch image.** `gcloud compute images list` shows no Arch family in the public image projects, and the old `arch-linux-gce` project isn't listable. So the base is Arch's own cloud image, refreshed upstream every ~2 weeks (the latest was modified 2026-10-15) and shipping cloud-init from `extra` (26.2).
- **No OS Login on Arch.** Google's guest agent and OS Login NSS/PAM modules aren't in Arch's repos. The AUR copies are from 2022–2023, and `google-compute-engine-oslogin` has been flagged out of date since 2026-09-08. Instead:
  - `rc-users.service` creates and updates local users from the `rc-users` metadata on every boot, before sshd;
  - sshd's `AuthorizedKeysCommand /usr/local/bin/rc-authorized-keys %u` (run as `nobody`, `AuthorizedKeysFile none`) reads that user's keys live from the metadata server, so a key change takes effect at the next login with no reboot;
  - cloud-init keeps network, hostname and growpart only, and its `users-groups` and `ssh` modules are disabled so it can't add a default user.
- **Google's udev disk-naming rules aren't packaged for Arch**, so without them a disk appears only as `scsi-0Google_PersistentDisk_home`. The image ships `65-gce-disk-naming.rules`, copied from Google's `guest-configs` (Apache-2.0), so `google-home` exists as remote-compute expects.
- **Time comes from systemd-timesyncd**, which already syncs from the metadata server (169.254.169.254), handed out by DHCP (inc 1). No chrony and no guest agent.
- **First boot takes ~153 s on the stock image.** `cloud-init-local` retries `metadata.google.internal` for ~130 s before the network is up. The baked image limits `datasource_list` to `[ GCE ]` and stops the local-stage lookup; inc 7 measures time to login.
- **The source image's disk is 2 GB.** Every VM sets an explicit boot disk size (remote-compute uses 100 GB), and cloud-init's growpart grows the btrfs root.
- **No Cloud NAT in the project.** A smoke VM without an external IP can't reach pacman mirrors, GitHub or Anthropic. Inc 7's throwaway VM gets an ephemeral external IP, and IAP isn't needed.
- **Nobody can IAP-tunnel into project VMs today.** terraform-runner has `iap.admin` but not `iap.tunnelResourceAccessor`, and neither has Harry. Workstation owners get it per instance from the module. Image smoke tests use the external IP instead.
- **The build runs in qemu on the GitHub runner**, which needs `/dev/kvm`. Standard `ubuntu-latest` runners expose it after a udev permission tweak, but that is **inferred**; inc 3 proves it. If KVM isn't available, the fallback is a two-stage build: import the base once, then a `googlecompute` build from it, which brings back IAP and the build-VM grants.
- **Boot mode** is assumed: the arch-boxes cloud image boots under UEFI on GCE with `UEFI_COMPATIBLE`; inc 1 proves it. Shielded VM runs with **Secure Boot off** (Arch's kernel is unsigned), and vTPM plus integrity monitoring on.
- **Build auth is the same subject pin as before:** `principal://…/subject/repo:ilg-platform/images:ref:refs/heads/main`. The `sub` format is inferred from GitHub's OIDC docs, and inc 3 proves a branch dispatch is refused. Local builds impersonate terraform-runner.
- **Claude Code comes from the native installer**, per user in `rc-setup` (`curl -fsSL https://claude.ai/install.sh | bash`): Anthropic's supported path, self-updating, into `~/.local/bin` on the home disk. The AUR `claude-code` is not Anthropic's packaging and is excluded. Managed settings in `/etc/claude-code/managed-settings.json` deny reads of `~/.claude/.credentials.json` and `~/.config/gh/hosts.yml`, and leave auto-update on.
- **Packages:** mise, github-cli, docker, tmux, git, base-devel, fail2ban, chrony and cloud-init all come from `core`/`extra`. gcloud is Google's tarball in `/opt/google-cloud-sdk`, not the AUR `google-cloud-cli`.
- **The arch-boxes signing subkey expires 2027-05-28.** `fetch-base.sh` will fail on the first build after that. Re-pin the subkey from the arch-boxes README before then.
- **SSH host keys persist across replaces.** Otherwise every `image_generation` bump changes them, and owners get `REMOTE HOST IDENTIFICATION HAS CHANGED`. A unit ordered after `rc-home` and before `sshd` keeps them under `/home/.rc/ssh/` on the home disk: on first boot it copies the generated keys there, and on every later boot it restores them to `/etc/ssh/`. (Found in the module PR's self-review, 2026-10-29.)
- **`rc-users` refuses to touch any existing account** whose uid differs from the declared one or falls outside 2000–59999. Terraform also denylists Arch's system user and group names.
- **sshd must not wait for `pacman-init`.** Arch's cloud image orders the first-boot keyring setup before sshd. On an e2 it blocked SSH for more than 10 minutes. The image edits that unit's `Before=`, since the unit lives in `/etc` and no package owns it.
- **Prune by age, never by count.** Keep 30 days, and never delete the name remote-compute pins.
- **Patching (decided 2026-10-29, Harry).** pacman never runs unattended: an unattended `pacman -Syu` on a rolling release occasionally needs a manual intervention, and a broken boot on a stateful VM costs more than a late patch. Three parts:
  - the image is rebuilt weekly on a schedule, so a new VM or an `image_generation` bump starts current;
  - `rc-upgrade` prints the archlinux.org news items since the last upgrade (from the RSS feed), asks for confirmation, runs `pacman -Syu`, and stamps `/var/lib/remote-compute/last-upgrade`;
  - the MOTD warns when that stamp, or the image build date if there is none, is more than 14 days old.
- UNRESOLVED: managed-settings content beyond the minimum, and who owns it.

## Increments
<!-- Each independently implementable AND verifiable. Cite the criteria it discharges as
     (AC n,n). Tick with `wp tick`, which stamps `— done: <sha>` from HEAD; never hand-write it.
     Prefer 3-7 — more usually means the ticket is too big, so say that rather than splitting
     hairs.

     A PRECONDITION THAT IS NOT CODE goes on its own indented `gate:` line, with a confirmation
     box under it. Sign-off blocks on a ticked increment sitting above an unconfirmed gate, and
     `wp brief` shows unmet gates in its NEXT block — so "do not action this yet" stops being
     bold prose a fresh session can miss:

         - [x] 6. Widen the subscription filter (AC 6) — verify: filter matches in dev — done: a24ca35
               gate: FUSE-1052 AND FUSE-1053 confirmed in prod
                     [ ] confirmed
-->

- [x] 1. **Base import, unmodified.** `fetch-base.sh` verifies the signature, then the cloud image is converted to raw, uploaded, and created as image `arch-cloudimg-<date>` (UEFI_COMPATIBLE). Done locally. This gives remote-compute an Arch image to start on straight away. (AC 4 in part) — verify: a throwaway N2 VM boots it (serial console shows login); `ssh arch@<ip>` works with a key in `ssh-keys` metadata through cloud-init's GCE datasource; `ls /dev/disk/by-id/` shows the `scsi-0Google_PersistentDisk_*` names, which proves the udev rule is needed. — done: 96ee174
- [x] 2. **Packer qemu template, PR check, base + sshd/users + `rc-home` + udev rule.** Built locally with `googlecompute-import`, impersonating terraform-runner. (AC 2,3,4,5 in part) — verify: an image appears in the family; the PR check is green; smoke asserts the `sshd -T` posture and `pacman -Qm` empty; a throwaway VM with an `rc-users` entry and a blank `home` disk accepts the owner's key, refuses a password, and refuses again once the key is removed from metadata. — done: a24ca35
- [x] 3. **CI build on `main` and the prune rule.** (AC 1,8) — verify: a `main` run is green with the full toolchain; the image name carries that run's sha7; a branch dispatch fails auth; prune dry-run output excludes the pinned name. — done: f8a7311
      gate: core-infra applied: the staging bucket exists and `gcloud projects get-iam-policy ilg-platform-ec02 --flatten=bindings[].members --filter="bindings.members:subject/repo:ilg-platform/images"` lists `roles/compute.storageAdmin`
            [x] confirmed
- [x] 4. **Toolchain.** mise system config, gh, docker, tmux, base-devel, fail2ban, the gcloud tarball, managed settings. (AC 3) — verify: smoke asserts every version and `pacman -Qm` empty. — done: a24ca35
- [x] 5. **Lifecycle timers and `rc-idle-check`.** (AC 3) — verify: units enabled; `systemd-analyze calendar` on both expressions; shellcheck. — done: a24ca35
- [x] 6. **First login and upgrades.** `rc-setup` (docker group, `mise install`, `gh auth login --web`, workspace clone, native Claude install, `claude auth login`), MOTD with the 14-day upgrade warning, tmux auto-attach, `rc-upgrade`, and the weekly `schedule:` trigger on the workflow. (AC 7,9 in part) — verify: shellcheck, `bash -n`, `rc-setup --check` in smoke; `systemctl list-timers --all` and `grep -r pacman /etc/systemd` show nothing that runs pacman. — done: f8a7311
- [x] 7. **Runtime acceptance on a throwaway VM.** Created from the family with a blank 10 GB `home` disk, an `rc-users` entry and `rc-idle-minutes=1`; deleted after. (AC 4,5,6,7,9) — verify: critical-chain, a reboot with no `mkfs`, a live key revoke, the idle stop and its negative case, the tmux landing, the `rc-setup` no-op, the fail2ban ban, and an `rc-upgrade` run with the MOTD warning before and after, each in Evidence. — done: a24ca35

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
- 2026-11-02 [inc 3,6] CI build (images#17, #18). PR run: KVM on the GitHub runner (`/dev/kvm` crw-rw-rw-), base `Arch-Linux-x86_64-cloudimg-20261101.620452` signature OK, `SMOKE: all checks passed`, build 2m20s, no import. Main run 41471233479 imported `remote-compute-arch-20261102-f8a7311` through the WIF grant, prune: 4 images, 0 deleted. Branch dispatch: before the preflight, auth passed and the upload got a 403 on the staging bucket (run 41473602963); after it, the job fails at "Check the import grant" with a message naming the ref (run 41474586266). Prune dry-run with zero thresholds keeps the image rc-hjf runs on and would delete the older two. Monday 05:00 UTC schedule in the workflow; nothing runs pacman on the VM (unchanged smoke check). Prune rule deviates from "never delete the name remote-compute pins": CI can't read that private repo, so it keeps anything no older than the newest in-use image instead.
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-11-02 [merge] ilg-platform/images#13 (base; merged by Harry at 09:30, before its review fixes) and #15 (fixes, tools, banner; `a24ca35`). `packer/remote-compute` on main is byte-identical to `fcbcd58`, the commit image `remote-compute-arch-20261102-fcbcd58` was built from, so that image is the merged code. On an e2-standard-2 the fixed image gave `LOGIN-OK` 57 s after create, with `pacman-init` still `activating`. Superseded images `-f44bf0d` and `-fffd513` were deleted.
- 2026-11-02 [banner, round-2 fixes] Image `remote-compute-arch-20261102-f44bf0d`, all smoke checks passed. Throwaway n2-standard-2 in europe-west2-b (n2 was out of stock in -a), over real SSH from a laptop:
  - Silent cases: `ssh host 'echo CMD-OK'` printed `CMD-OK` and no banner. scp printed 0 bytes and the file arrived; sftp showed no banner.
  - An interactive login with `RC_NO_TMUX=1` showed the coloured banner (256-colour SGR, a reset on every line) with `OPERATOR smoke` and `TERMINAL smoke.shell.platform.ilg.software` from metadata.
  - `NO_COLOR=1` and `TERM=dumb` showed the banner with 0 SGR codes. `RC_NO_BANNER=1` showed nothing.
  - A new tmux session showed the banner in window 0 and not in window 1, and the flag was consumed.
  - On reattach, the client's status line showed `APPLIED COMPUTING · OPERATOR smoke · smoke.shell.platform.ilg.software`. The hook removed itself, and window 0 wasn't redrawn.
- 2026-11-02 [defect found and fixed] On an e2-standard-2, Arch's `pacman-init` (`Before=sshd.service`, not owned by any package) ran for more than 10 minutes on first boot. sshd never started, and port 22 refused connections; on n2 it took 7.7 s. Fixed in `fcbcd58` by taking sshd off pacman-init's `Before=`, plus a smoke check. The root cause on e2 is unproven: a likely slow entropy or keyring path.
- 2026-10-29 [inc 2,4,5,6] Local build (`e22e373`, `9e42c7c`, `aef875d`, `ed6d309`), qemu/KVM + `googlecompute-import` impersonating terraform-runner (no SA key). Image `remote-compute-arch-20261029-ed6d309` (READY, 10 GB, UEFI_COMPATIBLE). qemu stage ~4m20s, end to end 7m51s–17m15s (upload varies). A throwaway n2-standard-4 with a blank `home` disk, all deleted after. Results:
  - (a) `google-home -> sdb`, `/home` ext4; first-boot `rc-home` mkfs; userspace in 21.6 s, sshd up at 21.5 s (was ~153 s); cloud-init local stage 0.2 s.
  - (b) `uid=2500(smoke) … wheel, docker`; `sudo -n true` works; `vm.env` correct.
  - (c) `sshd -T`: PermitRootLogin no, PasswordAuthentication no, KbdInteractiveAuthentication no, AuthorizedKeysCommand `rc-authorized-keys %u` as `rc-keys`. A password-only attempt is offered `publickey` only.
  - (d) Removing the key from metadata refused the next login, and restoring it allowed login, with `uptime -s` unchanged.
  - (e) Reboot: no mkfs, `restored 4 host keys`, identical RSA/ECDSA/ED25519 fingerprints, marker uid 2500 survives.
  - (f) Delete with `--keep-disks=data` and recreate (twice): `StrictHostKeyChecking=yes` login against the original known_hosts entry on a new IP; marker and uid survive; no mkfs.
  - (g) Lands in tmux `main` with the `rc-setup` message; `rc-setup --check` correct; scp/sftp unaffected; the 14-day upgrade warning appears with a stale stamp and not a fresh one.
  - (h) Four bad-key logins produced a ban (Total failed 4, banned 1).
  - (i) `rc-idle-minutes=5` gave guestTerminate 7.6 min after the last disconnect; a busy `claude` process kept it up for 16 min.
- 2026-10-29 Split for review into stacked ilg-platform/images#13 (base, incs 1–2) and #14 (incs 4–6, plus fail2ban tuned to 6 failures in 10 min, a 15-min ban and the IAP range exempt). Superseded local images `-1cf9095` and `-2793a26` deleted.
- 2026-10-29 [inc 1] `fetch-base.sh` (`96ee174`) downloaded Arch cloudimg `20261015.611680`, verified the `.SHA256` and the signature against arch-boxes key `1B9A16984A4E8CB448712D2AE0B78BF4326C6F8F` (signing subkey `656E4C5A…9174`, **expires 2027-05-28**; fetched from keyserver.ubuntu.com, matching the arch-boxes README key block). A truncated copy gave `BAD signature`, exit 1. Imported as `arch-cloudimg-20261015` (UEFI_COMPATIBLE, 2 GB). A throwaway n2-standard-2 booted it under UEFI with Secure Boot off and TPM2 present. `cloud-init` finished (DataSourceGCE, degraded: `metadata.google.internal` unresolvable in the local stage); `is-system-running` = running; timesyncd synced from 169.254.169.254 via DHCP. `/dev/disk/by-id` shows only `scsi-0Google_PersistentDisk_home`, no `google-home`. Stock sshd: `passwordauthentication yes`, `permitrootlogin prohibit-password`. Key login as `arch` was proven from a second VM over the internal network; IAP was denied (`4033`) for terraform-runner and Harry. Both VMs and their disks are deleted.
- 2026-10-29 [gate inc 3] ilg-platform/core-infra#17 applied (run 40898099727: 3 added, 0 changed, 0 destroyed). Bucket `ilg-platform-vm-image-staging` (EUROPE-WEST2, uniform access, PAP enforced, 7-day delete); `principal://…/subject/repo:ilg-platform/images:ref:refs/heads/main` holds `roles/storage.objectAdmin` on it and `roles/compute.storageAdmin` on the project. Caveat: a workflow job with `environment:` changes the sub claim and would not match.

- <YYYY-MM-DD> [inc <n>] <what was run, against what, and the observable result>

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- <what remains unproven, and what would prove it>

## Rollout & rollback
<!-- Added on demand. Written at plan time; amend in place as it changes.
     `Shared state touched:` is the single home for the five classes git does not own — a dev
     deploy, a prod config write, a Datadog monitor, a CI var or secret, cross-repo IaC. Reverting
     the branch undoes none of them, so if they are not written here they are not written down. -->

- **Order:** inc 1 is local and unblocks remote-compute at once. The core-infra grant gates only inc 3, the CI build. The remote-compute plan's image switch needs inc 2 or later, built locally or in CI.
- **Flags/config:** none. Consumers pick an image by name.
- **One-way doors:** none. A bad image never rolls to running VMs.
- **Rollback:** revert the PR. Delete a bad image unless a consumer pins it.
- **Shared state touched:**
  - **Cross-repo IaC:** core-infra `vm-images.tf` (the staging bucket and the subject-pinned grants).
  - **Images in `ilg-platform-ec02`:** family `remote-compute-arch` and the `arch-cloudimg-*` base images.
  - **Throwaway test VMs.**
- **Proof in prod:** remote-compute's image-switch increment boots this image with the home disk and the owner's UID intact.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-29** — Agent findings folded in: the sshd drop-in is 10-remote-compute.conf (sshd keeps the first value, and systemd's 20-systemd-userdb.conf sets its own AuthorizedKeysCommand); OpenSSH 10.6 prints no AuthorizedKeysFile line for none; cloud-init reads 169.254.169.254 in its local stage instead of skipping it; fail2ban needs mode=aggressive to count key refusals, tuned to 6/10m with a 15m ban and IAP exempt; CI needs xorriso; the unit is sshd.service on Arch; the key command runs as rc-keys.

- **2026-10-29** — From remote-compute's module self-review: no startup-script; the image derives vm.env from rc-* metadata (rc-subdomain added); SSH host keys persist on the home disk so a replace keeps them; rc-users refuses existing accounts outside the declared uid range.

- **2026-10-29 (Harry Fitzgerald)** — Patching: no unattended pacman; weekly image rebuild, rc-upgrade (Arch news then pacman -Syu, stamped), and a MOTD warning past 14 days.

- **2026-10-29 (Harry Fitzgerald)** — 2026-10-29: base OS switched from Ubuntu 24.04 to Arch Linux before activation. Consequences: Arch's own cloud image + qemu build + import instead of a GCE source image; no OS Login (stale on Arch), users and keys from instance metadata via AuthorizedKeysCommand; own udev rule for google-<name> disk links; native Claude installer instead of apt; narrower build grant (no build VM in GCP).

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
- Google publishes no Arch Linux image, and the AUR's OS Login and guest-agent packages are stale (2022–2023, flagged out of date). An Arch VM on GCE has to manage its own users and keys.
- Without Google's `guest-configs` udev rules, persistent disks appear only as `scsi-0Google_PersistentDisk_<device-name>`. The `google-<device-name>` links come from those rules.
- cloud-init's GCE datasource reads `ssh-keys` and `block-project-ssh-keys` from metadata, so a stock Arch cloud image is reachable on GCE with no Google guest software.
- `google-startup-scripts` (on Google's images) is not ordered against ssh. Anything a login depends on must be a unit with `Before=ssh.service`.
