---
ticket: none
title: 'Day-2 operations: tier, disk, owners, offboarding'
service: remote-compute
status: draft
created: '2026-10-29'
updated: '2026-10-29'
repo: /home/hjf/code/fuse/remote-compute
worktree: "unknown"
branch: "unknown"
base: origin/main
base_sha: unknown
pr: null
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: medium
---
# none — Day-2 operations: tier, disk, owners, offboarding

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
Out-of-ticket follow-up to [[first-workstation-stack-module-and-one-engineer-|the first-workstation plan]]. It proves the stateful promises that plan makes but doesn't exercise:
- a tier change and disk growth happen in place;
- a VM can have two owners;
- removing an entry never destroys a home disk;
- Claude Code updates itself on running VMs;
- removing an owner's keys cuts their access.

It also ends with a second team's VM going live from a tfvars-only PR, following the README unaided. Start only after the first plan's AC 1 holds.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. Changing an entry's `tier` plans a `machine_type` update with no replace, and `nproc` shows the new count after the stop/start.
- [ ] 2. Raising `home_disk_gb` plans an in-place `size` update, and `df -h /home` shows it after reboot.
- [ ] 3. On a two-owner VM, both owners can SSH and stop/start it. Removing one owner's entry refuses their next login, while the other owner is unaffected.
- [ ] 4. Removing an entry cannot destroy its home disk. The documented route leaves the disk in GCP, unmanaged, with a snapshot.
- [ ] 5. A new Claude Code release reaches a running VM through the native installer's self-update, with no image roll.
- [ ] 6. A member of a second team follows the README from PR to `claude` running, with no help.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- Same repo and module as [[first-workstation-stack-module-and-one-engineer-]]: `iac/modules/workstation` (lifecycle, disk, `removed` blocks), `iac/env/prod.tfvars`, `README.md`.
- The image's `rc-users` handling and the native Claude installer, from [[remote-compute-vm-image-packer-ubuntu-24-04]].

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **`prevent_destroy` is one literal for every VM.** It sits in the module's `lifecycle`, so it guards every home disk at once. "Remove `prevent_destroy`, then the entry" would drop the guard for the whole fleet for that apply. The offboarding route is instead a `removed { from = module.workstation["<sub>"].google_compute_disk.home  lifecycle { destroy = false } }` block (Terraform 1.7+), preceded by a snapshot. The static IP is handled the same way.
- **Offboarding removes the owner's keys first.** That cuts access at the next login; the IAM members go in the same PR.
- **Offboarding posture follows sftp-host Plan C**: snapshot first, keep the disk warm for two weeks, then delete it and keep the snapshot 30 days.
- **Offboarding from a shared VM is not just a PR.** Owners are root (wheel, NOPASSWD), so removing someone's keys doesn't remove anything they left in `/home` or other users' homes. A leaver on a shared VM means a replace plus an audit of `/home`. (Module self-review, 2026-10-29.)
- **A tier change must pin `home_disk_gb`.** The default home size follows the tier, and shrinking is impossible: going m→s without a pin fails the plan on `prevent_destroy`, and going s→m without one grows the disk for good. Inc 1 and inc 2 prove this.
- **RESOLVED 2026-11-02 (remote-compute#11): the owner's IAP binding is lost after an `image_generation` replace.** A throwaway Terraform probe proved the instance-level binding is unreliable after a same-name replace (read back empty once, lost for good once, in 3 replaces), so a sleep wouldn't fix it. Now: a reserved internal IP per workstation and a project-level IAP grant conditioned on `destination.ip` and port 22; the probe reached sshd 23-30 s after each of 3 replaces, and prod IAP SSH worked straight after the apply. Original note: The binding was created after the new instance, then found missing; the cause is unproven, likely asynchronous cleanup of the old same-named instance's IAP policy. To do: prove the cause, then make the grant survive a replace (e.g. a project-level grant with an IAM condition on the instance, or ordering after cleanup), and add a check after every replace.
  - **Second occurrence, caught in the act (2026-11-02, remote-compute#8, deploy run 41459536365):** the instance was created, the instance IAM binding succeeded, then `google_iap_tunnel_instance_iam_member` failed with *Provider produced inconsistent result after apply*. Straight afterwards the new instance's IAP policy was empty with etag `ACAB` (a fresh policy). Re-applying a minute later (manual-deploy run 41461285159, 1 to add) stuck, and SSH over IAP worked about 2 minutes after that. So the write lands before IAP has initialised the new instance's policy, which then starts empty. It isn't cleanup of the old instance. **Fix candidate:** a `time_sleep` of a few minutes between the instance and the IAP member, both replaced together, or a project-level IAP grant with an IAM condition on the instance name, which doesn't depend on the instance existing.
- UNRESOLVED: **which team gets the second VM, and who on it.**
- **Access ends by PR** (decided 2026-10-29 in the first-workstation plan): removing the leaver's owner entry or keys cuts their next login, with no IAM revocation behind it. Inc 3 proves it.
- UNRESOLVED: **the disk side of the offboarding policy**: who deletes a departed engineer's disk, and when.

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

- [ ] 1. **Tier change in place**, `s` → `m` on the test VM. (AC 1) — verify: the plan shows an `machine_type` update and no replace; `nproc`.
- [ ] 2. **Disk growth**, `home_disk_gb` +100. (AC 2) — verify: the plan shows a `size` update; `df -h /home`; `resize2fs` logged by `rc-home`.
- [ ] 3. **Offboarding route** on a scratch entry: snapshot, `removed` block, remove the entry. (AC 4) — verify: the plan shows "removed from state" with no destroy; the disk and snapshot still exist in `gcloud compute disks list`; the README documents the route.
- [ ] 4. **Claude Code self-update.** (AC 5) — verify: `claude --version` before and after a release, with no image change and no pacman involvement.
- [ ] 5. **A second team, two owners, README acceptance.** (AC 3,6) — verify: the second team's PR is tfvars-only; both owners pass AC 3 of the first plan; the engineer reaches `claude` unaided.
      gate: the second team and its engineers named
            [ ] confirmed

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
(none)
