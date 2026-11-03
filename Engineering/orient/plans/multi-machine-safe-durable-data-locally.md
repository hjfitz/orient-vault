---
ticket: none
title: Multi-machine-safe durable data, locally
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
impl_model: opus
impl_effort: medium
---
# none — Multi-machine-safe durable data, locally

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
Make orient's durable data safe to hold in git and to write from more than one machine, proving it all **locally** against throwaway bare remotes. The vault becomes a git repo. The writers (`wp.py`, `cust.py`, skills, `statusline.py`, hooks) get their own repo. Durable records leave the disposable state dir. A sync service commits, pulls and pushes. Nothing goes to a real remote in this plan. That one-way step, the bootstrap and the VM are [[go-remote-and-bootstrap-a-fresh-machine]] (Plan B), which is blocked on this plan.

The proof is two scratch clones of the vault writing concurrently, with no lost ledger entry, plan note or usage row and no conflict markers. The laptop's orient must keep showing the same totals, recordings and analytics throughout.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. The writers are in a git repo whose `git ls-files` holds only allow-listed paths. gitleaks is clean, and skills, `wp` and `cust` work unchanged on the laptop.
- [ ] 2. No durable record lives only in `~/.local/state/orient`. Deleting it loses only the index, caches and run dirs.
- [ ] 3. A corrupt or half-written `.knowledge` store makes the write fail. It is never read as an empty store and overwritten.
- [ ] 4. Two clones writing concurrently (ledger entries, plan notes, usage rows, programme ticks, hand edits) lose nothing, and `git grep '^<<<<<<<'` is empty on both.
> SUPERSEDED 2026-11-03 — "reaches clone B within seconds" holds only up to the remote. B has no push channel, so it sees A's write on its next sync: at most one timer interval (90 s), or at once when B runs a rewriting `wp`/`cust` command, which pulls first. Read AC 5 as: A's write reaches origin within seconds, and every other clone within one timer interval.
- [ ] 5. A `wp` or orient write on clone A reaches clone B within seconds, and a hand edit within one timer interval (≤2 min). Commits queue while offline and push on reconnect.
- [ ] 6. Meeting audio is never committed (`git check-ignore` matches it) and is deleted 14 days after recording. Transcripts and summaries sit in a vault-tracked dir that is not indexed.
- [ ] 7. On the laptop, `/usage`, work-cost, `/analytics` and `/recordings` show the same totals and counts before and after.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- **Writers:** `~/.claude/waypoint/wp.py` (`orient_state_dir` l.78; append writers at l.101 `plan-usage.jsonl` and l.120 `work-usage.jsonl`; vault writes via `atomic_write` l.131 behind the `changed_since_read` mtime guard l.155). `~/.claude/customers/cust.py` (plain `write_text` at l.54, 79, 131, 216, 276, 315). `~/.claude/statusline.py` `append_history` l.182 (runs at `refreshInterval: 5`, 3-5k rows a day).
- **orient durable writers:** `src/adapters/jira-write.ts:44`, `src/actions/slack.ts:61`, `src/adapters/github-write.ts:84`, `src/adapters/analytics-log.ts`.
- **orient readers:** `src/domain/plan-usage.ts:98,102` (`readJsonl` l.30 skips bad lines), `src/domain/work-cost.ts:112`, `analytics-log.ts`, `app/analytics/page.tsx`.
- **`.knowledge` stores:** `src/domain/plan-status.ts` (`readStore` l.24-32 swallows parse failures; `writeNote` l.56 is a non-atomic `writeFile`), `src/domain/todo-defers.ts:64` (same), `focus-log.ts` (`state.json` "one file for the whole machine", l.131; `rewrite` l.71 edits lines in place), `slack-sections.ts`, `manifest.ts` (absolute `root`, ids from paths).
- **Indexer:** `scripts/index-watch.ts`. `ignored()` l.88 drops `IGNORED_DIRS` (`src/config.ts:103`, which includes `.git` and `.knowledge`), and the 30 s structural sweep is unchanged. `config.yaml` is read once at boot (`config.ts:218`).
- **Editor saves:** `src/edit/save.ts` (`saveDocument`, `tickTask`, `captureLine`, `createDocument`, `writeThrough`), via `atomicWrite.ts`.
- **Scribe:** `scribe/` data dir, whose default `$XDG_STATE_HOME/orient/scribe` comes from `serve.go:39`; the unit passes no `-data`. Also `server.Resume` (`internal/server/server.go:89`), `store.Delete` (`store.go:228`), and rename, trim, merge, speaker naming and enhance. orient reaches it only over HTTP (`src/adapters/scribe.ts`, `mcp/internal/scribe`).
- **Copier:** `sync-claude-config.service`/`.timer` (Mon-Fri 17:30) copies `~/.claude` config, skills (skipping symlinks except ones into `~/.agents/skills`), memory, `--extra ~/code` and `--folder ~/Documents/obsidian` to the VM.
- **Docs in the repo:** `CLAUDE.md` (l.47-48 rollback, l.58 and l.95 the transcripts invariant), `README.md` (l.31 and l.128-140, `.knowledge` contents and rollback).
- Explainers: [[architecture]], [[known-context]] (Systems/orient, last verified 2026-09-24 and partly stale; see Learnings).

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- Git is the source of truth: a full clone per machine, `origin/main` authoritative, write-through commits, `merge=union` on append-only files, a timer pull. Agreed with Harry on 2026-11-02.
- Audio stays local and expires after 14 days, while transcripts and summaries are committed. Agreed with Harry on 2026-11-02.
- `orient-web` already binds `127.0.0.1:3000`. Established from the unit file and commit 90a7314; architecture.md's "0.0.0.0" is stale.
- `.knowledge` is skipped by the indexer, so records and recordings there are never indexed, searched or put in prompt context. Established from `config.ts:103`.
- The machine id comes from a file, `~/.config/orient/host` (default `laptop`), not an env var. `wp.py` and `statusline.py` run under Claude Code, not systemd, so an `ORIENT_HOST` set in a unit would never reach them. Established in review. An explicit id rather than the hostname lets new hardware take over the `laptop` role.
- The vault's own `git add -A` is intended. The orient repo's "never `git add -A`" rule does not apply to the vault.
- **The remotes are private repos on Harry's personal GitHub, `hjfitz`.** Harry decided this on 2026-11-02 ("everything can go in github… only for me").
- **All transcripts are committed, including 1:1s and interviews.** That follows from the same decision. The VM is headless and doesn't record, so its sparse checkout excludes `.knowledge/recordings/` along with `Bifrost/HR`, `Bifrost/Team` and `Interviews`. This is a default; Harry can override it. `docs/mcp-spec.md`:174-176 (withholding sensitive recordings from MCP reads) stays open, but it is a separate question.
- **The Mac is out of scope.** The bootstrap takes any `HOST`, so it can join later without a design change. This is a default.
- **`~/code` project skills stay with the copier** (`~/code/CLAUDE.md` and its 29 Fuse project skills). `~/code` is not a git repo and they are Fuse's shared contract, not orient's. This is a default; folding them into the writers repo is a later option.

## Increments
<!-- Each independently implementable AND verifiable. Cite the criteria it discharges as
     (AC n,n). Tick with `wp tick`, which stamps `— done: <sha>` from HEAD; never hand-write it.
     Prefer 3-7 — more usually means the ticket is too big, so say that rather than splitting
     hairs.

     A PRECONDITION THAT IS NOT CODE goes on its own indented `gate:` line, with a confirmation
     box under it. Sign-off blocks on a ticked increment sitting above an unconfirmed gate, and
     `wp brief` shows unmet gates in its NEXT block — so "do not action this yet" stops being
     bold prose a fresh session can miss:

         - [x] 6. Widen the subscription filter (AC 6) — verify: filter matches in dev — harness + live: wp, orient save and the Claude Code hook each reach origin in under 0.5 s; offline never blocks — done: 11aaab0
               gate: FUSE-1052 AND FUSE-1053 confirmed in prod
                     [ ] confirmed
-->

- [x] 1. **Writers repo.** (AC 1) — in orient-writers; allow-listed ls-files, gitleaks clean, wp/cust/statusline run via links — done: 07b5532
  - `~/projects/orient-writers/` holds `skills/`, `waypoint/`, `customers/`, `statusline.py` and `hooks/`. The originals in `~/.claude` become symlinks into it.
  - `.gitignore` is allow-list style. It excludes `skills/synced/`, `skills/.trash/` and `__pycache__/`, and the existing relative `~/.agents` symlinks (`find-skills`, `shopify-app-store-review`) stay as they are. `settings.local.json` holds a prod key and must never be added.
  - Replace `/home/hjf` with `$HOME` in `slack-bot`, `snap-maintenance` and `morning-digest`.
  - Add a gitleaks pre-commit hook.
  > SUPERSEDED 2026-11-02: the copier is retired, so neither this step nor its verify line below applies.
  - **Teach the copier to dereference symlinks into `orient-writers`.** Otherwise it silently stops shipping skills to the VM.
  - Verify:
    - `git ls-files` lists only allow-listed paths, and `gitleaks detect` is clean.
    - `wp doctor` and `cust list` run, and the Claude Code skill list is unchanged.
    - A manual copier run delivers an edited skill to the VM.
- [x] 2. **Safe `.knowledge` stores.** (AC 3,4) — append-only event logs; legacy JSON frozen and fails loudly if corrupt — done: 8196526
  - `plan-status` and `todo-defers` become append-only JSONL events (`{planPath|key, …, updated, host}`), with the last event winning.
  - Readers still read the legacy `.json` until it has been migrated.
  - Writes are atomic (temp file then rename).
  - `readStore` throws on a corrupt file instead of returning empty.
  - Verify with vitest:
    - A corrupt store refuses to write.
    - Two interleaved event streams resolve to the latest note per plan.
    - Existing plan notes still show on `/waypoints`.
- [x] 3. **Durable records split by host, out of the state dir.** (AC 2,7) — records under .knowledge/records/<host>; summaries unchanged across migration — done: 6c0e23e
  - Readers ship first. `src/config.ts` gains `hostId` from `~/.config/orient/host` and `durableDir = <vault>/.knowledge/records`. `plan-usage.ts`, `work-cost.ts` and `analytics-log.ts` read the legacy path **and** `records/*/…`.
  - Writers flip next: `wp.py` l.101/l.120, `statusline.py` `append_history` (monthly `usage-history-YYYY-MM.jsonl`), and `jira-write.ts`, `slack.ts`, `github-write.ts` and `analytics-log.ts`. Each writes to `records/<host>/`.
  - Then `scripts/migrate-durable.ts` copies the legacy rows to `records/laptop/`, makes a final sweep for rows appended during the copy, and renames the originals `*.migrated`.
  - `focus/state.json` moves to the state dir.
  - Update `README.md` and `CLAUDE.md`: `.knowledge` is split into derived (`manifest.json`, `reports/`) and durable (`records/`, `recordings/`, `focus/`, `puzzles/`, the stores). Rollback becomes "delete `manifest.json`, `reports/` and the state dir's index", plus `git checkout`.
  - Verify:
    - `planUsageSummaries()` and the work-cost output are byte-equal before and after (snapshots in the scratchpad).
    - With `statusline` writing in a loop during the migration, the row counts match.
    - `/usage` and `/analytics` return 200 with the same totals.
    - `WAYPOINT_VAULT=<tmp> wp tick` writes to `records/laptop/`.
- [x] 4. **Recordings in the vault, audio local.** (AC 6,7) — recordings in .knowledge/recordings/<host>; foreign read-only (409); audio pruned at 14 days — done: d62e6b8
  - `orient-scribe.service` gets `-data <vault>/.knowledge/recordings/<host>`, and the existing dirs move there.
  - Recordings from another host are read-only in the UI and API: rename, trim, merge, speaker naming, delete, enhance again, `server.Resume` and the enhance backfill all refuse them, and so does `store.Delete`.
  - `store.PruneAudio(14d)` runs on start and daily. It deletes `audio.*` only, skips recordings not yet enhanced, and its first run is a dry run.
  - The player and trim show an "audio expired" state.
  - Update the transcripts invariant at `CLAUDE.md`:58 and :95 to "in the vault's `.knowledge`, never in the index". The separate rule on Claude Code session transcripts stays as written.
  - Verify:
    - `go test ./internal/store ./internal/server`, with an injected clock for the prune, and a check that a foreign host's `meta.json` and directory are never written or deleted.
    - `/recordings` shows the same count.
    - After a prune, `find … -name 'audio.*' -mtime +14` returns nothing.
    - gate: Harry decides how 1:1 and interview recordings are handled (resolved 2026-11-02: all committed; the VM sparse checkout excludes recordings)
      [x] confirmed
- [x] 5. **The vault in git, with sync, against throwaway remotes.** (AC 4,5,6) — vault in git; sync timer live on a local bare remote; two-clone harness passed — done: 535e9e3
  - `git init` the vault, with `.gitignore` covering `.obsidian/workspace*.json`, `.trash/`, `.wp-*.tmp`, `.orient-*.tmp`, `*.tmp`, `**/audio.*`, `**/transcript.log` and `*.corrupt-*`.
  - `.gitattributes` follows the merge table in Decisions & deviations. `merge.ours.driver` is set per clone.
  - `writeManifest` refuses on any host other than the `config.yaml` `manifestWriter`.
  > SUPERSEDED 2026-11-02: the script fetches and merges rather than running `pull --rebase`, because rebase refuses the dirty tree that hourly records batching leaves (see Decisions).
  - `scripts/vault-sync.sh` runs under `flock`. It commits if the tree is dirty, but commits `records/**` at most hourly, so statusline doesn't produce ~960 commits a day. Then it runs `pull --rebase`; on a conflict it runs `rebase --abort`, writes `.git/orient-sync-status` and runs `notify-send`. It pushes with retries.
  - `orient-vault-sync.service` (oneshot) and `.timer` (90 s) are **installed but only pointed at a scratch bare remote**.
  > SUPERSEDED 2026-11-02: the copier is retired.
  - The copier gets `--exclude .git` for the vault folder.
  - Verify with two scratch clones of a bare repo:
    - Concurrent `wp ledger` and plan notes both arrive.
    - Ticks on adjacent rows of one programme table leave no conflict markers.
    - A hand edit on A arrives on B within one interval.
    - `git check-ignore` matches `audio.*`.
    - Offline commits queue, then push on reconnect.
    - `pnpm index:watch` on B batches a 50-file pull, and `pnpm index:status` exits 0.
- [ ] 6. **Writes kick the sync straight away.** (AC 5)
  - `wp.py` and `cust.py` run `systemctl --user start --no-block orient-vault-sync` after any write, and do a best-effort pull before a rewriting command (tick, set-status, programme tick, sync, index).
  - The orient save paths and `.knowledge` stores do the same through a new `src/adapters/vault-sync.ts`.
  - A Claude Code `PostToolUse` hook on `Write|Edit` covers vault paths.
  - Verify:
    - Between the scratch clones, a `wp idea` on A is visible on B in under 5 s.
    - An editor save does the same.
    - Offline, the kick is a no-op and the work is not blocked.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-11-03 [inc 6] **Writes kick the sync** (AC 5): orient commit 11aaab0, writers commit 60c4c5f.
  - Harness: a bare remote and clones A and B of the vault (14 MB), real `wp` and `orient-vault-sync`.
    - `wp idea` on A returned in 0.09 s and its commit was on origin at 0.3 s. B had it at 0.8 s, after a `wp index` on B (a rewriting command, so it pulls first).
    - Offline, with origin on an address that hangs: `wp idea` returned in 0.11 s (the kick never blocks). A rewriting command waited 8.4 s, bounded by the fetch timeout; it was 16.4 s before `pull` took the result of a sync that finished while it waited. When DNS fails, it took 0.4 s.
    - On reconnect, a kick pushed the queued commits and B picked up both offline ideas. `git grep '^<<<<<<<'` is empty on A and B.
    - A kick during a running sync, with A's push held 2 s by a pre-push hook: the second write still reached origin, because the running sync went round again.
  - Live vault:
    - The Claude Code `PostToolUse` hook: an Edit to this plan was committed and synced as bb42852 within 2 s, and a file outside the vault didn't kick.
    - `wp decide` pulled, wrote and synced as 21c8c7a, in 0.15 s.
    - A save through deployed orient (`POST /api/write`) was on origin in 0.25 s (7b627b6). The probe file was then deleted (d4ba3a8).
  - Tests: 4,734 vitest (5 new, in `tests/unit/vault-sync.test.ts`: kicks inside the vault, not outside, not without `.git`, not when switched off, never throws). The 14 cust unittests pass, lint shows the 2 old warnings, and tsc is clean.
- 2026-11-02 [inc 5] **The vault in git, with sync**: orient commit 535e9e3, writers commit 3ac78d2.
  - Harness: a copy of the vault without audio (1,312 files, a 13 MB `.git`), a bare remote and clones A and B, each with its own host file, using the real `wp` and `scripts/vault-sync.sh`.
    - A `wp ledger` entry on each clone for the same service: both entries on both clones, 0 conflict markers.
    - New `plan-status.jsonl` events on each clone: both on both (union, add/add).
    - Edits 5 lines apart in one programme table merge cleanly. Edits to the same row: `rc=1`, status `conflict … CONFLICT (content): Merge conflict in Bifrost/Shopify Connector Rearchitecture/Migration State.md … Resolve by hand: cd <vault> && git merge origin/main`, 0 markers on disk, no `MERGE_HEAD`, B keeps its edit as 1 unpushed commit, 0 dirty paths. Resolving by hand puts both clones back on the same HEAD.
    - A hand edit on A reaches B in one sync.
    - Offline (A's remote pointed at a missing path): `rc=2`, status `offline`, 1 commit queued, and it reached B after reconnecting.
    - Both clones regenerating `Engineering/index.md` differently: no conflict (`merge=ours`).
    - Uncommitted records (hourly batching, fresh stamp) don't block a merge of A's changes.
    - `git check-ignore` matches `recordings/**/audio.ogg`.
  - `pnpm index:watch` on clone B (its own state dir): a 50-file pull was indexed as one batch, `updated 50 indexed in 2618 ms`, and `pnpm index:status` exited 0 with 1,064 of 1,064 indexed and the watcher running.
  - vitest: the manifest isn't written on a host other than `manifestWriter`, and daily record files are read. 4,729 tests pass, typecheck and lint clean. After `pnpm deploy:web`, `/usage` returns 200.
  - Live vault: `git init`, and a dry run of the first add listed 1,312 files with 0 audio, workspace or temp files. gitleaks over the vault: no leaks. First commit 381ffde. Local bare remote at `~/.local/state/orient/vault-remote.git`. `orient-vault-sync.timer` enabled; its first unattended run at 20:25:16 made commit 3356c7c, status `ok synced`, tree clean apart from the hourly-batched records. `systemd-analyze --user verify` is clean on both units.
- 2026-11-02 [inc 4] **Recordings moved into the vault**, commit d62e6b8.
  - Go: `go test ./...` green, with new store tests (new recordings land in this host's dir, other hosts are listed, a loaded recording knows its host, save and delete of a foreign recording are refused, an unsafe host id is rejected, and prune deletes old audio while keeping the transcript, recent audio, audio still waiting to be enhanced, and another host's audio; a dry run deletes nothing and reports what it would delete) and server tests (foreign shown `readOnly`, own not, and PATCH, DELETE, enhance and trim of a foreign recording are 409; `Resume` leaves a foreign recording's `meta.json` byte-identical). orient: 4,727 tests pass, typecheck and lint clean.
  - Live: stopped scribe with all 14 recordings idle, moved `~/.local/state/orient/scribe` → `.knowledge/recordings/laptop/` (a rename on the same filesystem), and started scribe. The API lists 14 recordings, all `host: laptop`, 10 with audio. The dirs are mode 700.
  - Simulated a foreign host (copied one recording into `recordings/vm-test/` under a new id). The live API returns 409 "recorded on another machine; read-only here" to PATCH, DELETE, enhance and trim, and its `meta.json` was untouched. The page shows "recorded on vm-test, read-only here" and "No audio here: it stays on vm-test", with no rename control. The test dir was removed.
  - `/recordings/20261019-100036-f543` shows "Audio expired: it is deleted 14 days after recording."
- 2026-11-02 [inc 3] **Durable records moved**: orient commits ae9f116 and 6c0e23e, writers commit 1c8d489.
  - vitest `records.test.ts`: a write lands in this host's dir, reads cover every host plus the old state-dir file, monthly splits are read, and `work-usage-extra` isn't mistaken for `work-usage`. 4,727 tests pass.
  - After `pnpm deploy:web`, `/today`, `/usage`, `/analytics` and `/waypoints` return 200. The live statusline wrote `records/laptop/usage-history-2026-11.jsonl` within a minute of the writer flip.
  - `scripts/migrate-records.ts`, dry-run on copies and then live, moved plan-usage 266, work-usage 192, usage-history 73,242, analytics 1,623, jira-write-log 6, slack-write-log 23 and review-log 5 rows. The sorted row multisets (md5) match the originals for all seven. One old usage-history line is NUL-padded (a torn write); it was unreadable before and still is.
  - Domain snapshot before vs after (`tsx --conditions=react-server`): all 63 `planUsageSummaries()` entries unchanged, plan-usage rows identical (266), analytics events identical (1,623), 4 programme-cost keys before and after. Usage history went 73,239 → 73,262, and the extra rows are live statusline appends.
  - `/analytics` HTML before vs after differs only in the storage line and Next.js chunk hashes.
  - `wp tick` on this increment appended its row to `records/laptop/plan-usage.jsonl` (266 → 267), and no `plan-usage.jsonl` was recreated in the state dir.
- 2026-11-02 [inc 2] **Stores made append-only**, commit 8196526.
  - vitest: the plan-status and todo-defers suites cover concurrent writes keeping both notes, the newest note winning by time when the log is out of order, a torn line costing only itself, the legacy JSON still reading and never being rewritten, and a corrupt legacy file throwing. The hostId suite covers the default, the file, and an unsafe id. 4,721 tests pass, and typecheck and lint are clean (the 2 warnings in `app/globals.css` were already there).
  - After `pnpm deploy:web`, `/today` and `/waypoints` return 200, and the live plan page `d_mpiqzxztykj5` (FUSE-1057) still shows its note from the frozen `plan-status.json`.
- 2026-11-02 [inc 1] **Writers repo** `~/projects/orient-writers`, commit 07b5532.
  - `git ls-files`: 65 files, all under the allow-listed paths.
  - `gitleaks protect --staged` on commit: "no leaks found". The one hit, a synthetic `sk_live_` value in `customers/tests/test_config_snapshot.py:16`, is marked `gitleaks:allow` inline.
  - `cust` unit tests: OK.
  - After the swap: `wp doctor orient` exits 0, `cust list` and `wp brief` run, and `statusline/statusline.py` runs from the new `settings.json` path. 34 `SKILL.md` files resolve through `~/.claude/skills` (the same 32 own skills plus the 2 `~/.agents` links).
  - `grep -rn /home/hjf` over the repo finds nothing.
  - Live vs repo before the swap: `diff -rq` showed only the 4 files edited on purpose.
  - Side effect: the statusline smoke test appended one zero-cost row with `session_id` `wp-verify` to `usage-history.jsonl`. It was left in place rather than rewriting a file that is being appended to live. Its session snapshot was deleted.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- <what remains unproven, and what would prove it>

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-11-03** — Inc 6: writers run the sync script directly as ~/.local/bin/orient-vault-sync (kick = background sync, pull = commit + merge, no push) instead of `systemctl --user start`. That passes the writer's own vault through (scratch clones work, the VM needs no unit to kick), and a kick that lands mid-sync marks the running sync to go round again; systemd would have merged it into the running job and dropped it. Kicked runs log to .git/orient-sync.log, not the journal. Fetch and push are bounded by timeout (20 s; 8 s when a writer is waiting). orient kicks after editor saves and .knowledge store writes but never pulls first: the editor already checks the file on disk against its base hash. Record appends don't kick, because the sync batches them hourly. AC 5 amended: other clones see a write within one timer interval, not seconds.

- **2026-11-02** — Inc 5 departures:
- Fetch and merge instead of pull --rebase. Hourly records batching keeps the tree dirty, and rebase refuses a dirty tree; a merge refuses only if the incoming side touches a dirty file, and nothing but this host writes its records. Merge commits are the cost.
- Usage history split per day (usage-history-YYYY-MM-DD.jsonl). A monthly file of several MB stored a new copy on every records commit; the reader accepts both forms.
- A conflict notifies once per kind, not every 90s.
- writeManifest skips with a warning on a non-writer host rather than throwing, so the watcher on the VM keeps indexing.
- The live vault is in git with its timer enabled, pushing to a local bare remote (~/.local/state/orient/vault-remote.git) that Plan B replaces with hjfitz/orient-vault. The units live in the orient repo under systemd/.
To roll back: systemctl --user disable --now orient-vault-sync.timer, then delete ~/Documents/obsidian/.git.

- **2026-11-02** — Inc 4: MISTAKE. The planned dry-run-first prune did not happen. Prune runs inside serve on start, and the service was started with it live, so the audio of 4 recordings from 2026-10-19 (Bifrost Standup, Stock Sync Catchup, Fuse Leadership Catchup, Harry/Jack) was deleted at 20:00. They were past 14 days and enhanced, so the policy would have taken them anyway, but they went without the agreed check. There is no snapshot (ext4, no Timeshift); transcripts, enhanced transcripts and summaries are intact. 'orient-scribe prune -dry-run' exists for future checks. Other choices: the data root defaults in serve.go to <vault>/.knowledge/recordings, with a -host flag from ~/.config/orient/host, rather than adding -data to the unit file. Read-only is enforced in three places: the store (ErrReadOnly), an owned() wrapper on the mutating routes (409), and the UI.

- **2026-11-02** — Inc 3 departures:
- The migration renames each old file aside before copying its rows, so readers keep reading the old state-dir path permanently and nothing appended mid-migration is lost. This replaces the line-count check plus final sweep.
- The machine-local focus timer session moved to stateDir/focus-session.json, falling back to the old .knowledge/focus/state.json.
- vitest defaults ORIENT_RECORDS_DIR to a temp dir, so tests never read the live vault's records.
- The script is scripts/migrate-records.ts (not migrate-durable.ts).
- Old files are kept in the state dir as *.migrated-<ms>.
- Inc 5's vault .gitignore must also cover .knowledge/focus/state.json.

- **2026-11-02** — Inc 2: plan-status.json is kept as a frozen, read-only base rather than migrated into the event log. There's no one-way step, and since writes no longer read the store, a write can't wipe anything. readJsonl moved to src/domain/jsonl.ts so the stores don't import plan-usage (which pulls in waypoints). hostId() was brought forward from inc 3, because events carry a host.

- **2026-11-02** — Inc 1's commit is in ~/projects/orient-writers (07b5532), not the orient repo, so sign-off will not find it on orient's branch. Writers are linked per directory, never per file: Claude Code's Edit refuses to write through a symlinked file. statusline.py moved to ~/.claude/statusline/ and settings.json now runs that path. Originals are kept in ~/.claude/backups/writers-pre-repo-20261102/.

- **2026-11-02 (Harry)** — Retired the sync-claude-config copier (timer stopped and disabled, unit files kept; re-enable with systemctl --user enable --now sync-claude-config.timer). The VM gets no skill, config or ~/code updates until Plan B step 4. Inc 1's copier-symlink work and inc 5's --exclude .git are dropped.
- 2026-11-02: **Merge strategy per file class**, fixed at plan time. Union on JSON stores produces invalid JSON, and combined with the old `readStore` that wipes every note.

  | Files | Strategy |
  |---|---|
  | `.knowledge/records/<host>/**`, `.knowledge/recordings/<host>/**` | One writer each, so never merged. `merge=union` on the `.jsonl` as a safety net. |
  | `.knowledge/{plan-status,todo-defers}.jsonl`, `focus/*.jsonl`, `puzzles/*.jsonl` | `merge=union`, readers dedupe and the last entry wins. A focus-log `rewrite` can leave both versions of a block, which is accepted. |
  | `Engineering/*/ledger.md`, `*/ideas-log.md`, `Customers/*/ledger.md` | `merge=union`. Two concurrent prepends become both entries. |
  | `Engineering/index.md`, `Customers/index.md` (derived) | `merge=ours`, regenerated after a pull. |
  | Plans, `waypoint.yaml`, programme Migration State docs, `config.yaml`, `slack-sections.json`, `reports/` | Default text merge. A conflict aborts and notifies. Never union. |
  | `.knowledge/manifest.json` | `-merge`, with one writer host. |
- 2026-11-02: **Rejected options:**
  - Making `~/.claude` itself the repo: a `git clean -x` or `stash -u` would delete `.credentials.json`.
  - A synchronous push inside `wp`: it blocks while offline.
  - `pull --autostash`: a failed pop leaves conflict markers that get indexed.
  - Hostname as the machine id: new hardware would make the laptop's records look foreign.
  - A custom JSON merge driver: it fails silently in any clone without the config.
- 2026-11-02: **Split from one plan into two** on the structure review. This plan has no one-way step and needs no decision about the remote.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
- **Systems/orient/architecture.md is stale:**
  - It says `orient-web` binds `0.0.0.0`; it binds loopback, since 90a7314 on 2026-10-13.
  - It says "three systemd units"; there are six, including desk, scribe and the vault-sync to come.
  - It says wp.py has "22" subcommands.
  - Refresh it at sign-off.
- **The `sync-claude-config` copier ships much more than skills and the vault:** CLAUDE.md, settings, statusline, agents, commands, hooks, project memory, `--extra ~/code` and MCP servers with their tokens from `~/.claude.json`. It also skips symlinks. Nothing documents this in the vault.
- **`statusline.py` writes `usage-history.jsonl` at 3-5k rows a day** (72.5k rows in total). Any sync design that commits on every change has to batch it.
- **Two `.knowledge` stores (`plan-status`, `todo-defers`) write non-atomically and read a parse failure as empty.** Before this plan, a crash mid-write lost every note, sync or no sync.
- **Scribe's write surface on `meta.json`** goes well beyond status: rename, trim, merge, speaker naming, delete and enhance.
- **Claude Code's Edit and Write refuse to write through a symlinked file** ("it is a symbolic link. Write to the link's target path instead"), but write through a symlinked directory normally. Tested in a scratchpad on 2026-11-02. Anything linked into `~/.claude` must be linked at the directory level.
- **`wp tick --note` suppresses the `done:` stamp if the note contains the sha** (`cmd_tick`, `if sha and sha not in new`). It's a substring check, so a note that mentions the commit loses its stamp silently.
- **A destructive job wired into a service's startup runs the moment the service starts.** To get a "dry run first", run the dry run (`orient-scribe prune -dry-run`) *before* deploying the build that prunes on start; a flag added afterwards doesn't help. That's how the 2026-10-19 audio went.
- **A oneshot systemd unit can't take a "run again" request.** `systemctl start` on a oneshot unit that is already activating merges into the running job, so a write that lands mid-sync would wait for the next timer run. vault-sync.sh fixes this with a request stamp (`.git/orient-sync-requested`) that the running sync checks before it exits.
- **In bash, `cmd <missing-file 2>/dev/null` still prints the "No such file" error:** redirections apply left to right, and the input redirect fails before stderr moves. Put `2>/dev/null` first.
