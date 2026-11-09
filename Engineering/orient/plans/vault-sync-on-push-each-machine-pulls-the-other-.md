---
ticket: none
title: 'Vault sync on push: each machine pulls the other''s changes at once'
service: orient
status: active
created: '2026-11-09'
updated: '2026-11-09'
repo: /home/hjf/projects/orient
worktree: /home/hjf/projects/orient
branch: master
base: origin/master
base_sha: ffb44e47f
pr: null
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: medium
---
# none — Vault sync on push: each machine pulls the other's changes at once

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
Laptop writes reach GitHub within seconds already: the `vault-sync-kick.sh` PostToolUse hook, `wp` and `cust` all run `orient-vault-sync kick`. The lag is on the receiving side, because each machine pulls only on its 90 s timer. This makes a push that moved `origin` announce itself, so the other machine pulls at once. Laptop → VM: the laptop runs the VM's sync over ssh, which the laptop is allowed to start. VM → laptop: the VM can't connect to the laptop (its sshd allows local forwards only), so the laptop follows a push log on the VM over an ssh session the laptop opens. Done means a vault write on either machine is on the other within about 10 s, so the VM's orient (the one Harry reads) and handovers between the machines are current. Follow-up to [[scribe-on-the-vm-capture-on-the-laptop-everythin]].

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. A vault write on the laptop is in the VM's checkout within about 10 s.
- [ ] 2. A vault write on the VM is in the laptop's checkout within about 10 s.
- [ ] 3. Only a push that moved `origin` announces itself, so the two machines never ping-pong. A quiet vault produces no announcements.
- [ ] 4. Peer down (VM off, tunnel down) costs nothing but speed: each machine falls back to its 90 s timer, and nothing blocks or alerts.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `scripts/vault-sync.sh`: `sync_once`, a new announcement after a push that moved `origin`.
- New: `scripts/vault-follow.sh` and `systemd/orient-vault-follow.service`, laptop only.
- `~/.config/orient/sync-peer`, laptop only: the peer's ssh host alias in `~/.ssh/orient-tunnel.conf` (`orient-vm`).
- `scripts/install-units.sh`, `docs/INSTALL.md`.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **Both machines have `~/.local/bin/orient-vault-sync`** (a symlink to the repo script) **and the Write|Edit kick hook.** Checked on both, 2026-11-09.
- **No `inotifywait` on the VM** (and pacman's DB there is stale), so the VM → laptop channel uses `tail -F` over ssh, which needs only coreutils. Checked.
- **Edits that bypass the hook** (a human in Obsidian, a script writing into the vault) still wait for the source machine's 90 s timer; only the receiving side gets faster. Accepted.

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
- [ ] 1. **Announce a push that moved `origin`, and kick a configured peer.** In `sync_once`, note `origin/<branch>` after the merge. If HEAD differs from it after `push_local`, append `<time> <host> <sha>` to `.git/orient-pushed`. When `~/.config/orient/sync-peer` exists, also run `ssh -F ~/.ssh/orient-tunnel.conf <peer> .local/bin/orient-vault-sync kick` in the background with a timeout. (AC 1,3,4)
  - verify: on the laptop, write a file under `Tasks/`, kick, and time its arrival on the VM (≤10 s). A sync with nothing new appends no line. With the peer unreachable, the sync still finishes `ok synced`.
- [ ] 2. **The laptop follows the VM's pushes.** `scripts/vault-follow.sh` runs `ssh … 'tail -n0 -F ~/Documents/obsidian/.git/orient-pushed'` and kicks a local sync for each line; `systemd/orient-vault-follow.service` restarts it. (AC 2,3,4)
  - verify: write a file on the VM, kick, and time its arrival on the laptop (≤10 s). Each machine's `orient-pushed` gains one line per real change and stops there. `systemctl --user restart orient-tunnel` leaves the follower running, since it uses its own connection.
- [ ] 3. **Install it and document it.** `install-units.sh` installs the follower when `sync-peer` exists. Add `docs/INSTALL.md` steps for a laptop that reaches orient on the VM: the tunnel, `sync-peer`, the follower. (AC 1,2)
  - verify: `systemctl --user is-enabled orient-vault-follow` on the laptop; `bash -n` on both scripts.

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
- **2026-11-09 — Planned without the three-reviewer pass.** Harry wanted it quickly to hand work between the machines, and the change is small: one script edit and one follower. The verifications are live round-trip timings.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
(none)
