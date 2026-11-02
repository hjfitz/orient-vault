---
ticket: none
title: 'Harden the SFTP VM: SFTP-only, per-user isolation, no root path'
service: sftp-connector
status: abandoned
created: '2026-10-20'
updated: '2026-10-20'
repo: /home/hjf/code/fuse/sftp-connector
worktree: /home/hjf/code/fuse/sftp-connector/.claude/worktrees/sftp-vm-hardening
branch: hjf/sftp-vm-hardening
base: origin/master
base_sha: c9f3f0e04
pr: null
tags:
- waypoint
- plan
impl_model: opus
impl_effort: high
reason: 'Harry 2026-10-20: VM hardening skipped for now (GCP incident, VM down); the
  host migration (Plans A-C) closes the exposure at cutover. Findings kept here for
  reference.'
---
# none — Harden the SFTP VM: SFTP-only, per-user isolation, no root path

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
Customers on the SFTP VM get full `/bin/bash` shells, and the single whole-bucket gcsfuse mount (#140, 2026-04-02) is `root:sftpgroup 770/660`, writable by every customer. So any customer can read and write every other customer's files and `users.json`. The root-run `sync_users.sh` then `eval`s each `users.json` username (`startup.sh.tpl:87`), which gives root at the next boot. A shell also reaches the metadata server for the VM SA's `cloud-platform` token. All of this is established from source and unverified on the live VMs.

Make the VM SFTP-only and per-user isolated **without** going back to per-user gcsfuse mounts, which exhausted the VM before #140. Keep absolute paths (`/home/<user>/to_ilg`, `from_ilg`) exactly as customers were given them. Remove every root path from `users.json`. This plan comes first and on its own: the container migration ([[sftp-host-a-monorepo-host-image-and-dev-infrastr|Plan A]] → B → C) is weeks away, and its drop-in baseline is the hardened VM, not today's.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. Every customer login gets SFTP only. An `ssh <user>` shell, an exec command, scp, `-L`/`-R` forwarding, X11, agent forwarding and tunnels are all refused (sshd's "This service allows sftp connections only" or channel refusal).
- [ ] 2. A customer's view is a chroot that holds only `/home/<user>/{to_ilg,from_ilg}`. The session starts in `/home/<user>`. `/mnt/gcs_root`, `users.json`, `/home/<other>` and other users' prefixes can't be reached by any path.
- [ ] 3. Existing absolute and relative paths still work. Every prod username from the pre-change baseline logs in and transfers within 24 h, and uploads still get archived by Cloud Run.
- [ ] 4. Effective `sshd -T` on both VMs shows `permitrootlogin no` and `passwordauthentication no`. No `users.json` content can run as root: no `eval`, and usernames that fail `^[A-Za-z0-9_.-]+$` are skipped and logged.
- [ ] 5. Provisioning still works: a new dev SFTP connector goes PENDING → ACTIVE through Cloud Run's SSH-as-`sftpuser` path, and the new user lands chrooted. The `sftp-partner-key` and `sftp-key-access-audit` skills' IAP admin path still works.
- [ ] 6. The hardening survives a reboot: a dev reboot reaches "Sync Run Complete" with AC 1-2 still true.
- [ ] 7. There's a written answer to whether the exposure was used (shell sessions per customer, `users.json` version history), and it went to Harry before any prod change.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `iac/projects/bifrost-sftp-connector/scripts/startup.sh.tpl`. Behaviour changes only on boot. The script's `rm -f /etc/ssh/sshd_config.d/*` (line 19) wipes any hand-applied override, so the drop-in must be written **after** it.
- `code/src/core/sftp-user-builder/sftp-user.builder.ts`: `useradd -s /bin/bash` (`:77`), `echo "${publicKey}" | sudo tee` (`:95`), `/home/<user>` binds (`:113-140`), and the unawaited `users.json` upload (`:196`).
- The admin user `sftpuser` (`keys.tf`; key comes from metadata `ssh-keys` through the guest agent). VMs that ran the pre-#140 script probably put it in `sftpgroup`, so any `Match Group sftpgroup` must exclude it.
- The live VMs `bifrost-sftp-connector-{dev,prod}-sftp` (names from `compute.tf:14`; confirm). Prod changes need a reboot or a hand-applied reload.
- Audit programme gate **G7** ("SFTP VM owner and recovery runbook exist"; `Bifrost/Audit Service/Migration State.md`), which applies to any sshd_config, mount or reboot change.
- Skills `/home/hjf/code/.claude/skills/{sftp-partner-key,sftp-key-access-audit}`, plus the `~/.codex/skills/sftp-partner-key` copy.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- Customers have interactive shells and can write the whole bucket. Source read of `startup.sh.tpl:18-21,79-82,87,93`, `iam.tf:12-16` and `compute.tf:34-37` by two independent reviewers. Debian 12's stock config has `#PermitRootLogin prohibit-password` and `#PasswordAuthentication yes` commented, so the `sed`s at `:20-21` are no-ops. **Not checked on the live VMs**; inc 1 does that.
- The exposure came in with #140. Before it, FUSE-241 (#49, 2025-09-24) used per-user `--only-dir` 700 mounts that isolated users. Established from git history (`32f8d1c^:startup.sh.tpl`).
- A chroot was tried on the FUSE-241 branch (`35e72b7`…`a44e7f4`) and backed out in `b2efea0` with no recorded reason. Inc 1 finds out why before retrying.
- Isolation through a chroot of bind mounts keeps the single gcsfuse process from #140. `/mnt/gcs_root` sits outside every chroot, so isolation doesn't depend on mount permissions. That's the design premise; inc 2's dev reboot proves it.
- `ChrootDirectory` requires every path component to be root-owned and not group/other-writable. So the chroot is `/srv/sftp/<user>/` (root 755) with `home/<user>/` (root 755) holding the `to_ilg`/`from_ilg` binds. The bind targets themselves are owned `<user>:sftpgroup`, as today.
- Customer pollers fall back to password after a key attempt (`sftp-key-access-audit` skill evidence). Users have no passwords, so making `PasswordAuthentication no` effective changes nothing for them.
- UNRESOLVED: on 2026-10-15 Harry chose not to raise a ticket for the shared-shell exposure (UJ plan). Gate G7 still blocks sshd, mount and reboot changes on the VM. With the new evidence (cross-tenant write and a root path), does that decision stand? This plan needs a named VM owner and a recovery runbook, or an explicit G7 waiver for this change.
- UNRESOLVED: if inc 1 finds a customer actually used a shell, read another prefix, or wrote `users.json`, is that handled as a data incident (`incident-response`) with customer notification? That's Harry's call.

## Increments
<!-- Each independently implementable AND verifiable. Cite the criteria it discharges as
     (AC n,n). Tick with `wp tick`, which stamps `— done: <sha>` from HEAD; never hand-write it.
     Prefer 3-7 — more usually means the ticket is too big, so say that rather than splitting
     hairs.

     A PRECONDITION THAT IS NOT CODE goes on its own indented `gate:` line, with a confirmation
     box under it. Sign-off blocks on a ticked increment sitting above an unconfirmed gate, and
     `wp brief` shows unmet gates in its NEXT block — so "do not action this yet" stops being
     bold prose a fresh session can miss:

         - [ ] 6. Widen the subscription filter (AC 6) — verify: filter matches in dev
               gate: FUSE-1052 AND FUSE-1053 confirmed in prod
                     [ ] confirmed
-->
- [ ] 1. Baseline and exposure check, read-only over IAP on both VMs (AC 7). Capture:
      - `sudo sshd -T`, `sudo sshd -T -C user=sftpuser,host=x,addr=127.0.0.1` and `id sftpuser`;
      - four weeks of `auth.log*` per username: `Starting session: shell|command|subsystem 'sftp'`, plus client KEX and host-key algorithms;
      - the `users.json` generation history (`gsutil ls -a`) diffed version to version against the provisioning ledger;
      - the reason the FUSE-241 chroot was backed out (`git show b2efea0`, PR #49 discussion);
      - whether `/srv` exists or is used.
      — verify: findings written to `### Evidence`. A per-user table of session types decides whether `ForceCommand` breaks anyone. The result is reported to Harry before inc 2 merges.
- [ ] 2. Harden the script and the builder in dev; one PR, applied by a dev reboot (AC 1,2,4,5,6).
      - **`startup.sh.tpl`:** write `/etc/ssh/sshd_config.d/10-fuse.conf` **after** the `rm` at `:19`. Set:
        - globally: `PermitRootLogin no`, `PasswordAuthentication no`, `KbdInteractiveAuthentication no`, `X11Forwarding no`;
        - in a `Match Group sftpgroup User !sftpuser` block: `ChrootDirectory /srv/sftp/%u`, `ForceCommand internal-sftp -d /home/%u`, `AllowTcpForwarding no`, `AllowAgentForwarding no`, `PermitTunnel no`, `PermitOpen none`.
      - **Validate and reload:** run `sshd -t` before `systemctl reload ssh`, and abort the reload on failure.
      - **Sync script:**
        - replace `eval echo "~$username"` with `getent passwd`;
        - skip and log usernames that fail the regex, or that are `root`, `sftpuser` or any system user;
        - create users with `/usr/sbin/nologin`, and `usermod -s` existing ones;
        - bind `<gcs>/<user>/{to_ilg,from_ilg}` into `/srv/sftp/<user>/home/<user>/` and drop the `/home/<user>/` binds.
      - **Builder, same semantics as the script:**
        - `nologin` shell;
        - the key goes over stdin, not shell interpolation;
        - the chroot binds, with a `mountpoint -q` guard;
        - await `upsertFile`.

      gate: G7 owner and runbook in place, or an explicit G7 waiver for this change (Harry)
            [ ] confirmed
      gate: inc 1 shows no customer depends on shell or exec, or Harry accepts breaking them with notice
            [ ] confirmed

      — verify, in dev after reboot:
      - serial log "Sync Run Complete";
      - `FUSE_EC11DE9F4F` (DAZZA "sftpfive") logs in, `pwd` = `/home/FUSE_EC11DE9F4F`, `ls` = `to_ilg from_ilg`, and both absolute and relative `put` work;
      - `cd /mnt/gcs_root`, `get /users.json` and `cd /home/<other>` fail;
      - `ssh FUSE_EC11DE9F4F` and `ssh … ls` are refused, `ssh -L` is refused, and root key login is refused;
      - a new dev SFTP connector in fuse-ui goes PENDING → ACTIVE and its user is chrooted;
      - `sftp-partner-key` dry-run IAP access works;
      - the `sshd -T` diff matches AC 4.
- [ ] 3. Prod rollout in a window: apply the metadata change (in place, no stop), then a prod reboot (AC 1-4,6).
      gate: customer notice sent if inc 1 found shell/exec users or the reboot needs one (Harry)
            [ ] confirmed

      — verify:
      - prod `sshd -T` matches AC 4;
      - for 24 h after the reboot, `auth.log` shows every baseline username with `subsystem request for sftp` and no `Starting session: shell`;
      - Datadog `new_file` processing and archive/error routing are at baseline (`service:sftp_connector`, underscore);
      - zero `Failed to create a SFTP user` alerts.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- <YYYY-MM-DD> [inc <n>] <what was run, against what, and the observable result>

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- <what remains unproven, and what would prove it>

## Rollout & rollback
<!-- Added on demand. Written at plan time; amend in place as it changes.
     `Shared state touched:` is the single home for the five classes git does not own — a dev
     deploy, a prod config write, a Datadog monitor, a CI var or secret, cross-repo IaC. Reverting
     the branch undoes none of them, so if they are not written here they are not written down. -->
- **Order:** 1 → 2 (dev) → 3 (prod). Inc 2 changes `code/`, so it merges before Plan A inc 1 moves `code/` to `apps/connector` (that's a gate in Plan A).
- **Flags/config:** none. The behaviour lives in the startup script and only takes effect on reboot, or on a hand-applied `sshd_config.d` drop-in plus reload, which a reboot then reproduces.
- **One-way doors:** none. Every step reverts by reverting the script and rebooting.
- **Rollback:**
  - Inc 2/3: `rm /etc/ssh/sshd_config.d/10-fuse.conf && systemctl reload ssh` on the VM restores today's access immediately. Revert the PR for the next boot.
  - The chroot binds are additive, so `/home/<user>` binds can be recreated by the old `sync_users.sh`.
- **Shared state touched:**
  - dev and prod VM instance metadata (`startup-script`), applied in place by the connector Deploy;
  - dev and prod VM reboots;
  - users' login shells (`usermod`), changed on the live VMs.
- **Proof in prod:**
  - `auth.log` shows no `Starting session: shell` for any customer after the change, against the inc 1 baseline counts;
  - every baseline username has an sftp subsystem session in 24 h.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
- #140 (2026-04-02) undid FUSE-241's per-user isolation. Per-user 700 mounts became one `sftpgroup` 770 mount, so every customer can read and write the whole bucket, `users.json` included. Not yet recorded anywhere in the vault.
- A chroot (`Match Group sftpgroup` / `ChrootDirectory`) was tried on the FUSE-241 branch (2025-09-19 to 22) and backed out without a recorded reason. The startup script's `rm -f /etc/ssh/sshd_config.d/*` wipes any sshd override on every boot.
- The admin user `sftpuser` was added to `sftpgroup` on VMs that ran the pre-#140 script. Any `Match Group sftpgroup` restriction also hits Cloud Run's provisioning SSH unless it excludes that user.
- The `support` SFTP user has never had `support/logs/` under its home. Only the shared `/mnt/gcs_root` mount reaches it, and this plan closes that.
- `sftp-user.builder.ts:169-171` replaces only the first matching `users.json` record. A multi-key user's first key is overwritten permanently, not until the next sync.

