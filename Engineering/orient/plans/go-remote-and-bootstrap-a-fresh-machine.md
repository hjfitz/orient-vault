---
ticket: none
title: Go remote and bootstrap a fresh machine
service: orient
status: active
created: '2026-11-02'
updated: '2026-11-03'
repo: /home/hjf/projects/orient
worktree: /home/hjf/projects/orient
branch: master
base: master
base_sha: 0f9f52ecc
pr: null
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: medium
---
# none — Go remote and bootstrap a fresh machine

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
Take the git setup built in [[multi-machine-safe-durable-data-locally]] (Plan A, which must be done first) to real remotes. orient goes to `hjfitz/orient`, the vault and writers to their chosen remote. The VM becomes a sparse clone that writes back, and its 17:30 copier is retired. Then make a fresh machine standable from the repos alone: units in the repo, `bootstrap.sh` and `docs/INSTALL.md`, proven first in a scratch `$HOME` and then on the new hardware.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. orient's history is on `git@github.com:hjfitz/orient.git`, pushed through a per-repo `core.sshCommand "ssh -F ~/.ssh/config-self"`. The global `~/.ssh/config` stays on work, and `gitswitch` is never used.
- [ ] 2. No live secret in the history of orient, the vault or the writers reaches GitHub. Every gitleaks finding is either fixed or allowlisted with a note.
- [ ] 3. All six orient units live in the repo, use `%h`, and install with an identical diff. `orient-web` answers on `127.0.0.1` only (`ss -ltn` shows no `0.0.0.0:3000`).
- [ ] 4. `scripts/bootstrap.sh` plus `docs/INSTALL.md` stand up orient from nothing, and a round-trip write works.
- [ ] 5. The VM is a sparse clone without `Bifrost/HR`, `Bifrost/Team` or `Interviews`. A `wp idea` written on either machine shows on the other within 2 min, and the 17:30 copier no longer touches the vault.
- [ ] 6. The repo's docs no longer say "no remote / never push".

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- **orient repo:** 386 commits authored as `harry.fitzgerald@globalfreightsolutions.com`.
  - gitleaks finds 11 findings across its history: `src/components/focus/FocusTimer.tsx:30,35`, `tests/unit/redact.test.ts` (6), `history-parse.test.ts` (2) and `pty-ticket.test.ts` (1).
  - Real `@gfsdeliver.com` addresses appear in 6 test files and as defaults at `src/config.ts:158,163`.
  - `gfs-bifrost` is named in 26 test files.
- **Units:** `desk/orient-desk.service` and `scribe/orient-scribe.service` are tracked in the repo (`make install`). `orient-web`, `orient-index` and `orient-pty` are hand-written in `~/.config/systemd/user`, and all of them hard-code `/home/hjf`; the VM user is `harry`.
- **Builds:** the mcp Makefile has `build` but no `install`. desk needs GNOME and scribe needs PipeWire plus 1.7 GB of models (`scripts/fetch-models.sh`), so the VM skips both.
- **Bootstrap inputs:**
  - `~/.secrets` holds `GITHUB_TOKEN`, read by `config.ts:256-273` and by the sprint-digest, week-roundup and morning-digest skills.
  - `gh` auth, `pnpm install`, and the `~/.claude.json` MCP registration of `mcp/bin/orient-mcp`.
  - `~/.config/orient/host`.
  - `~/.ssh/config-self` has no `IdentitiesOnly yes`.
- **`sync-claude-config` copier:** remove its `--folder ~/Documents/obsidian`.
- **Docs in the repo:** `CLAUDE.md`:19 and :21-32 (no remote, the deploy loop), `waypoint.yaml` `deploy: none`.
- Explainers: [[known-context]] ("No remote… do not attempt a push"), [[overview]].

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- The orient app goes to `hjfitz/orient` (personal account). Harry's decision on 2026-11-02. The repo exists and is empty, and `ssh -F ~/.ssh/config-self` authenticates as `hjfitz` (checked on 2026-11-02).
- orient's history is **not rewritten**. A filter-repo would orphan every `verified_sha` and `@sha` anchor in the vault (the `wp doctor` ORPHAN-ANCHOR check). Findings are scrubbed going forward or allowlisted with notes. Established in review.
- The VM gets a read-only deploy key on `hjfitz/orient` and never a copy of the personal key.
- **The vault and writers also go to `hjfitz`,** as private repos only Harry can access: `hjfitz/orient-vault` and `hjfitz/orient-writers`. All three share one SSH setup, which keeps the sync simple. Harry decided this on 2026-11-02, having seen the concern about HR, interview and customer data. The repo names are a default; rename them if wanted. Harry creates the empty repos, since `gh` here is authenticated as the work account.
- **The work email on orient's commits stays as it is,** with no `.mailmap`. The repo is private and only Harry can access it. This is a default that follows from the same decision.
- **The VM's orient is deployed by hand** (`pnpm deploy:web` after a pull). A timer-driven redeploy would kill `/sprint` runs that share the web unit's cgroup. This is a default; Harry can override it.

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

- [x] 1. **First push of orient.** (AC 1,2,6) — gitleaks clean with reviewed allowlist; ls-remote master equals HEAD; global git and ~/.ssh/config unchanged — done: 078c0fc
  - Review the 11 gitleaks hits and the `gfsdeliver` fixtures and defaults. Scrub them going forward (synthetic addresses, config defaults moved to `~/.secrets` or `config.yaml`), or allowlist them with notes.
  - Add `IdentitiesOnly yes` to `~/.ssh/config-self`.
  - `git remote add origin git@github.com:hjfitz/orient.git`, then `git config core.sshCommand "ssh -F ~/.ssh/config-self"`, then push `master`.
  - Update `CLAUDE.md`:19/:21-32 and `waypoint.yaml` `deploy:` to describe the remote and the push rule.
  - Verify:
    - `gitleaks detect` over the working tree is clean, or has notes for every finding.
    - `git ls-remote` shows `master` at the local HEAD.
    - `git config --global` and `~/.ssh/config` are unchanged (`diff` against `config-gfs`).
    - gate: Plan A complete
      [x] confirmed (2026-11-03, multi-machine-safe-durable-data-locally signed off)
    - gate: Harry decides on the commit author email (resolved 2026-11-02: kept as is, private repo)
      [x] confirmed
- [x] 2. **Units in the repo.** (AC 3) — systemd-analyze verify clean; all 7 units active from repo copies; :3000 on 127.0.0.1 only; /today, /recordings 200; scribe and desk up — done: e14885b
  - Add `systemd/` with all six units plus `orient-vault-sync.{service,timer}`, written with `%h` and `-H 127.0.0.1`, and a `make install-units` target.
  - Swap them in for the laptop's hand-written units.
  - Verify:
    - `systemd-analyze --user verify systemd/*`.
    - After a restart, `curl -sf 127.0.0.1:3000/today` and `ss -ltn | grep ':3000'` show loopback only.
    - `/recordings` and the desk still work.
- [x] 3. **Bootstrap and INSTALL, proven in a scratch home.** (AC 4) — throwaway VM user, deploy keys, SPARSE+HEADLESS: rerun rc=0 in 84s; index:status ok; /today /recordings /usage 200 on loopback; HR/Team/Interviews absent from disk and index; wp idea round-tripped to a second clone — done: 4f5b12e
  - `scripts/bootstrap.sh` takes `ORIENT_REMOTE`, `VAULT_REMOTE`, `WRITERS_REMOTE`, `HOST` and `SPARSE`, plus `HEADLESS` to skip desk, scribe and models.
  - It does:
    - The toolchain: mise, pnpm, Go, PyYAML.
    - `~/.ssh/config-self` (the key is copied by hand), and a `~/.secrets` template.
    - The clones with per-repo `core.sshCommand`, sparse checkout when `SPARSE` is set, and `merge.ours.driver`.
    - The writer symlinks and `~/.local/bin/{wp,cust}`, plus `~/.config/orient/host`.
    - `pnpm install`, `make build` for desk, scribe and mcp, and `claude mcp add orient`.
    - The units, then `pnpm index:build` and `pnpm deploy:web`.
  - Add `docs/INSTALL.md` for the manual steps: keys, `gh auth login`, `~/.secrets` values.
  - Verify: in a container or a throwaway user, against local bare remotes, the script runs end to end, `pnpm index:status` exits 0, `/today` returns 200, and a `wp idea` round-trips to a second scratch clone.
- [x] 4. **Vault and writers go remote, the VM becomes a clone.** (AC 5) — VM bootstrapped from GitHub remotes (sparse, headless, deploy keys); writes round-trip both ways within one timer interval — done: f9bdc45
  - Push the vault and writers to their remote, then enable the laptop's sync timer against it.
  - Remove the copier's `--folder ~/Documents/obsidian`, and its writer files if the writers repo now covers them.
  - On the VM: move the existing `~/Documents/obsidian` aside, then run `bootstrap.sh` with `HOST=vm SPARSE=1 HEADLESS=1` and a read-only deploy key on `hjfitz/orient`.
  - Verify:
    - `git sparse-checkout list` on the VM, with `Bifrost/HR`, `Bifrost/Team`, `Interviews` and `.knowledge/recordings/` absent.
    - A `wp idea` on the VM shows on the laptop within 2 min, and the reverse.
    - `records/vm/` appears.
    - The next 17:30 copier run lists no vault files.
    - gate: private repos `hjfitz/orient-vault` and `hjfitz/orient-writers` created by Harry (remote chosen 2026-11-02)
      [x] confirmed (2026-11-03; both pushed from the laptop)
    - gate: the VM's write-enabled deploy keys added to `orient-vault` and `orient-writers` (keys in the VM's `~/.ssh/orient-deploy/`)
      [x] confirmed (2026-11-03; all three keys accepted, `orient` read-only)
    - gate: Obsidian Sync confirmed disconnected in the app (`core-plugins.json` has `sync: true` but there is no `sync.json`)
      [x] confirmed (2026-11-03: Harry hasn't used Obsidian since orient was built; no sync.json)
    - gate: `gitleaks detect` over the vault clean
      [x] confirmed (2026-11-03: 0 findings over history and tree)
- [ ] 5. **Fresh-hardware proof.** (AC 4)
  - Run `bootstrap.sh` on the new machine with `HOST=laptop`, timed.
  - Verify:
    - `pnpm index:status` exits 0, `/today` returns 200, `systemctl --user list-timers` shows vault-sync, and a round-trip write reaches the VM.
    - Every manual step it needed is in `INSTALL.md`.
    - gate: new hardware arrived and the old laptop's last sync has been pushed
      [ ] confirmed

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-11-03 [inc 4] **The VM is a clone of the GitHub remotes** (AC 5): orient f9bdc45, writers 01dbcf2.
  - Laptop: writers pushed to `hjfitz/orient-writers`, and the vault's origin moved from the local stand-in to `hjfitz/orient-vault` (first sync and push 4.6 s, ls-remote equals HEAD).
  - VM (`harry@hjf.shell.platform.ilg.software`): `HOST=vm SPARSE=1 HEADLESS=1 SSH_MODE=deploy scripts/bootstrap.sh`, rc 0 in 99 s on the second run. The first stopped on mise's python having no PyYAML, fixed in f9bdc45.
    - The copier's vault, `~/.claude/{waypoint,customers,hooks}` and 33 copied skills moved to `~/.orient-bootstrap-backup/20261103-102645/` (19 MB).
    - `git sparse-checkout list` excludes `Bifrost/HR`, `Bifrost/Team`, `Interviews` and `.knowledge/recordings`. None are on disk, and 0 of them are in the index. The partial-clone filter is `blob:none`.
    - `index:status` ok at 1,062 documents. orient-web, -index, -pty and the vault-sync timer are active, Linger=yes, and `/today`, `/recordings` and `/usage` return 200 on `127.0.0.1:3000` only. `claude mcp get orient` is connected, and `wp` and `cust` run.
  - Round trip, probe files in `_heap/` (removed after):
    - VM → laptop: on origin about 4 s after the write, and on the laptop at 101 s, on the laptop's own timer.
    - Laptop → VM: on the VM at about 25 s.
    - Both sync statuses read `ok synced`.
- <YYYY-MM-DD> [inc <n>] <what was run, against what, and the observable result>

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- **`records/vm/` hasn't appeared yet.** Nothing on the VM has appended a record so far. The first Claude Code session there writes `usage-history`, and the VM's first sync after that commits it, because records commit straight away on a machine's first sync.
- **The VM's `~/.secrets` is an empty template**, so its orient shows no Jira, GitHub, Datadog or incident.io data until Harry fills it in.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-11-03** — Three repos, not two: Harry kept orient-writers separate from orient so the app can be shared publicly one day without his skills. Should orient go public, its history first needs the work emails and Slack/incident.io workspace URLs scrubbed from test fixtures, and the gfsdeliver default in config.ts, by a history rewrite. That would orphan vault sha anchors, so plan it as its own piece of work. Laptop side of inc 4 done: writers pushed to hjfitz/orient-writers, and the vault's origin repointed from the local stand-in to hjfitz/orient-vault, first push in 4.6 s.

- **2026-11-03** — Inc 3 proven in a throwaway user (orienttest) on the VM itself, not a scratch HOME on the laptop. A throwaway user has its own systemd user manager, so units, lingering and deploy:web run for real, and the 22-core VM carries a second node_modules and build that the laptop can't spare. The first run found node-pty compiling from source with no node-gyp, now installed by the script. The user was removed afterwards (userdel -r).

- **2026-11-03** — Inc 2: scripts/install-units.sh (with HEADLESS=1) instead of a make install-units target; the repo has no root Makefile and its other entry points are scripts/. Units call /usr/bin/env mise, because mise is ~/.local/bin/mise on the laptop and /usr/bin/mise on the VM. The laptop's old hand-written units are in ~/.config/systemd/user/backup-pre-repo-units-20261103/.

- **2026-11-03** — Inc 1: the work-domain emails and Slack/incident.io workspace URLs in test fixtures and the people.internalDomains default stay as they are. History keeps them anyway (no rewrite), and the repo is private to Harry, per his 2026-11-02 call. All 11 gitleaks hits are fixtures or a key name, allowlisted by fingerprint in .gitleaksignore.

- **2026-11-03** — Amended at activation (2026-11-03), from a read-only look at the VM (harry@hjf.shell.platform.ilg.software: Arch, 22 cores, 31 GB; mise provides node 24, pnpm 10, Go; passwordless sudo; Linger=no). (1) The copier is already retired (Plan A), so inc 4's copier steps are moot. (2) orient-vault-sync.{service,timer} are already in systemd/; inc 2 adds the other five. (3) The VM gets three deploy keys, one per repo, since GitHub needs a key unique per repo: hjfitz/orient read-only, hjfitz/orient-vault and hjfitz/orient-writers write-enabled, because the VM writes both. Each clone pins its key with core.sshCommand. (4) bootstrap.sh must run loginctl enable-linger, or the VM's sync timer stops at logout. (5) The VM's copier-made vault (18 MB) already holds Bifrost/HR and Interviews. Inc 4 moves it aside and the sparse clone replaces it.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
- **`gitswitch` (`~/.zshrc`:121) swaps the whole `~/.ssh/config`**, so anything unattended that needs the personal account must use a per-repo `core.sshCommand`.
- **`config-self` has no `IdentitiesOnly yes`.** With an agent holding `id_ed25519`, `ssh -i ~/.ssh/id_rsa` authenticated as the work account (observed 2026-11-02).
- **Once Plan B lands, known-context's "No remote… do not attempt a push" and "`~/.claude` is not version-controlled" are false.** Rewrite both at sign-off. The writers may then become anchorable in Waypoint.
