---
ticket: none
title: 'Scribe on the VM: capture on the laptop, everything else on the VM'
service: orient
status: active
created: '2026-11-09'
updated: '2026-11-09'
repo: /home/hjf/projects/orient
worktree: /home/hjf/projects/orient
branch: master
base: origin/master
base_sha: 1b8ffbf28
pr: null
tags:
- waypoint
- plan
impl_model: opus
impl_effort: high
---
# none — Scribe on the VM: capture on the laptop, everything else on the VM

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
Since 2026-11-09 the VM (`rc-hjf`) is orient's home. The laptop reaches it through `orient-tunnel` (`:3000` web, `:3011` terminal). The exception is Recordings: scribe captures on the laptop, and a laptop-only orient on `:3001` stays up to serve them. This plan makes the VM the single home for recordings. The laptop only captures, because it needs PipeWire to tap both sides of a call. It hands each finished capture to the VM's scribe over a forward the laptop opens. The VM transcribes, enhances, stores and serves the recordings, and relays start/stop/pause back to the laptop. Then `:3001` is retired. Done means a call recorded on the laptop appears transcribed, enhanced and playable at `localhost:3000/recordings` (the VM), with no audio left on the laptop and no orient-web running there. A phone recorder is a follow-up plan; the upload ingest built here must work for it.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. The VM runs `orient-scribe` in a server role: it transcribes, compresses, enhances and summarises, never records, and serves the Recordings page at `localhost:3000`. Its vault checkout includes `.knowledge/recordings/`. `Bifrost/HR`, `Bifrost/Team` and `Interviews` stay excluded.
- [ ] 2. A finished laptop capture reaches the VM intact, confirmed by sha256, through a resumable upload. A dropped tunnel delays the upload but loses nothing, and the recording ends `done` and enhanced on the VM with playable audio.
- [ ] 3. The laptop writes no new recordings into the vault and never transcribes. Its local copy is deleted as soon as the VM confirms receipt (sha256 matched, file synced to disk). While the VM is unreachable, captures queue on the laptop and you get a notification.
- [ ] 4. From `localhost:3000/recordings` on the laptop: start, pause, resume, stop and ignore act on the laptop's capture within about 2 s. With the recorder disconnected, Start is refused and the page says why.
- [ ] 5. The laptop runs no orient-web. The top-bar widget, the reminders and the laptop's orient MCP all show and control recordings through the VM. Re-running `install-units.sh` on the laptop doesn't bring orient-web back.
- [ ] 6. The upload ingest accepts a recording whose total size isn't known until the end, appended from a reported offset. This is what the phone recorder needs.
- [ ] 7. Audio is pruned after 14 days unless the recording is marked **keep**. A kept recording's audio survives the prune, and the mark can be set and cleared from its page.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- **scribe:**
  - `scribe/internal/server/server.go`: routes L500–517, `owned()` L520, `start()` L335, `process()` L173, `Resume()` L89.
  - `scribe/internal/store/store.go`: status values L21–26, `Save` L216–220, `Load` takes the host from the directory (L252), `PruneAudio` L300.
  - `scribe/cmd/orient-scribe/serve.go`: `-threads` L70, orient URL L76, `-remind-lead` L77, prune and backfill at start L143/L151, the music warning only when `playerctl` is present L169.
  - `scribe/cmd/orient-scribe/main.go`: `load()` L187, which maps mono to "Them" and needs 16 kHz.
  - New files: `upload.go`, `agents.go`, `internal/handoff`.
- **Units and bootstrap:**
  - `systemd/orient-scribe.service` uses `%h`. The duplicate `scribe/orient-scribe.service` hard-codes `/home/hjf` and is installed by `make -C scribe install`.
  - `scripts/install-units.sh`: HEADLESS at L15/L25.
  - `scripts/bootstrap.sh`: the sparse list at L113–114, scribe and models gated by HEADLESS at L172–174.
  - New `systemd/orient-tunnel.service`.
- **orient (TS):**
  - `src/adapters/scribe.ts`: `RecordingSchema.status` is a strict `z.enum` at L48. An unknown status fails the whole list.
  - `src/lib/recordings.ts`: the `RecordingStatus` union L6–12, label/colour maps L14–31, `PROCESSING` L361, `recordingNavStatus` L364.
  - `src/domain/recordings.ts` (`startRequest`), `src/actions/recordings.ts`, `RecordPanel`, `RecordingNav`, `app/recordings/[id]/page.tsx` (read-only and "recorded on" display), `app/api/desk/act/route.ts` (loopback check plus write token).
  - `mcp/internal/config/config.go:20` (`ORIENT_SCRIBE_URL`).
- **desk:** `desk/cmd/orient-desk/main.go` (`-orient`, `-token`).
- **Hand-written laptop units that this plan replaces:** `~/.config/systemd/user/orient-tunnel.service`, `orient-web.service.d/recordings-only-port.conf`, `orient-desk.service.d/recordings-interim.conf`.
- **Vault:** `.gitignore` (`audio.*`, `transcript.log`, `*.tmp`) is the only thing keeping audio out of git.
- **Related plans:** [[go-remote-and-bootstrap-a-fresh-machine]] (its AC 5, the VM's sparse list, is partly overridden here) and [[multi-machine-safe-durable-data-locally]] (one writer per host directory).

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **The VM can never connect to the laptop.** The image sets `AllowTcpForwarding local` (ilg-platform/images `packer/remote-compute/files/ssh/10-remote-compute.conf`, checked by its smoke test). Anything that goes VM → laptop has to be pulled by the laptop. Established from the sshd config on the VM and the image repo.
- **The VM has gcc, Go (mise), `~/.local/bin/claude`, 22 cores, 31 GB RAM and 432 GB free, and `~/.config/orient/host` reads `vm`.** It lacks ffmpeg, `pw-link`, `playerctl` and `notify-send`. Established by a read-only check on the VM.
- **The laptop has no `~/.config/orient/host`;** it is `laptop` only by `hostID()`'s default (serve.go L50–60). Established by reading source and the laptop.
- **Code is committed on the laptop and pulled on the VM,** because the VM's deploy key for `hjfitz/orient` is read-only. No git worktrees on the laptop (CLAUDE.md L15). The VM is deployed by hand, never by a timer, because a timer redeploy would kill `/sprint` runs. Established from [[go-remote-and-bootstrap-a-fresh-machine]] and known-context.
- **scribe prunes audio and backfills enhancements when it starts** (serve.go L143/L151), and that has lost audio before (2026-10-19). Every first start in a new role, and every new delete-on-receipt job, gets a dry run first. Established from known-context.
- **A 4.7 s stub, `20261105-143224-c1da`, is `done` with an empty transcript;** a backfill would re-run Claude on it. Established by the fact-check.
- **Answered 2026-11-09: recordings may live on the VM,** sensitive ones (1:1s, interviews) included. `orient-recordings` is unchanged; nothing is withheld.
- **Answered 2026-11-09: 14-day retention stays,** with a per-recording **keep** mark that exempts a recording's audio from the prune (AC 7).
- **Answered 2026-11-09: the laptop copy is deleted once the VM has it,** meaning on receipt. No `handed-off/` buffer.
- **Answered 2026-11-09: all transcription is on the VM.** No local fallback; captures queue and notify.
- **Answered 2026-11-09: the morning digest and the other recording-reading skills keep running on the laptop.** So the laptop MCP must read the VM's scribe (inc 4). Getting the laptop's vault *writes* onto the VM is a separate concern and a separate plan (see Follow-up plans).

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

- [x] 1. **The VM runs scribe as a server and lists the synced transcripts read-only. The laptop is unchanged.** (AC 1) — VM scribe -role server: 17 read-only, POST 409, no reminders, RTF 0.21; laptop both-role recorded fine — done: 66511dc
  - Code:
    - `serve -role recorder|server|both`. The default is `both`, today's behaviour. `server` never records: `POST /api/recordings` answers 409 "this machine does not record".
    - `systemd/orient-scribe.service` gains `EnvironmentFile=-%h/.config/orient/scribe.env` and `ExecStart=… serve $SCRIBE_ARGS`.
    - `install-units.sh` and `bootstrap.sh` take `SCRIBE=server`: install the scribe unit, build scribe and fetch models even when HEADLESS is set.
    - Drop `'!/.knowledge/recordings/'` from bootstrap's sparse list.
    - Delete `scribe/orient-scribe.service`, and have the Makefile's `install` use `../systemd/`.
    - Write `~/.config/orient/host` explicitly on the laptop.
  - VM:
    - Install ffmpeg.
    - `git sparse-checkout set --no-cone '/*' '!/Bifrost/HR/' '!/Bifrost/Team/' '!/Interviews/'`.
    - `make -C scribe build models`.
    - `scribe.env` is `SCRIBE_ARGS=-role server -threads 8 -remind-lead 0`.
    - `orient-scribe prune -dry-run` before the first start.
    - `SCRIBE=server HEADLESS=1 scripts/install-units.sh`.
  - Verify:
    - `go test ./...` in `scribe/`.
    - On the VM: the list holds ≥17 recordings, all `host: laptop`, all read-only. A POST answers 409. `journalctl` shows no reminder or music-warning start.
    - `eval/fetch-ami.sh`, then `process` on `ES2004a.stereo-me0.wav`, has a real-time factor of 0.5 or less.
    - On the laptop after pulling the unit change: `systemctl --user cat orient-scribe` shows the new unit, a 30 s recording still works there, and `localhost:3000/recordings` lists the read-only history.
      gate: on the VM, ffmpeg is installed and `claude -p` answers when signed in. On the laptop, `~/.config/orient/host` reads `laptop`.
          [x] confirmed
- [x] 2. **Upload ingest on the VM, behind a token.** (AC 2,6) — VM upload ingest live: 401 without token, 403 foreign Host, both orient pages 200; Go protocol tests green under -race — done: 6898741
  - `scribe/internal/server/upload.go`:
    - `POST /api/uploads` takes `{id, meta, format, layout}` and answers `{offset}`. It is idempotent and reports the current offset when called again.
    - `PATCH /api/uploads/{id}` appends at `Upload-Offset`. A wrong offset gets 409 with the true offset.
    - `POST /api/uploads/{id}/complete` takes `{size, sha256}`. It checks both, converts with ffmpeg to 16 kHz `audio.wav`, writes `vm/<id>/` (fsync, then rename) with status `queued`, and queues it. It answers 200 with the recording and the checksum. That answer is the receipt, and the call is idempotent.
  - Parts are staged in `~/.local/state/orient/scribe-uploads/`, outside the vault.
  - The total size isn't known until `complete`, so a recording still in progress can be appended (the phone needs this).
  - No per-chunk checksums yet; the phone plan adds them if WebCrypto needs them.
  - A bearer token (generated on the VM, file mode 0600) on the upload and agent routes, and a Host check on every route. The check accepts `127.0.0.1`/`localhost` with any port, because orient sends `Host: 127.0.0.1:3013`.
  - Verify:
    - Go tests, one behaviour each: resumes after a cut; a wrong offset gives 409 with the true offset; `complete` before every byte arrives is refused; `complete` again gives the same answer; an id reused with different content is refused; no token gives 401.
    - After `make` and a restart on the VM, `localhost:3000/recordings` and `localhost:3001/recordings` both still load.
      > SUPERSEDED 2026-11-09 — the laptop's copy is `~/.config/orient/scribe-hub-client-token`, not `scribe-hub-token`. scribe reads `scribe-hub-token` to switch uploads *on*, so a laptop copy at that path would make the laptop accept uploads too.
      gate: hub token generated on the VM and copied to the laptop (`~/.config/orient/scribe-hub-token`, mode 0600)
          [x] confirmed
- [x] 3. **A manual `handoff` on the laptop, the tunnel unit in the repo, `capturedOn`, the keep mark, and a status schema that tolerates unknown values.** (AC 2,6,7) — live handoff + resume across tunnel restart; FLAC WER 20.7% = raw; keep mark renders; tolerant status — done: 0dae982
  - orient first, deployed on the VM and on `:3001`: unknown statuses show as "unknown" instead of failing the list. Add `uploading` to the `RecordingStatus` union, the label and colour maps (an in-flight accent, not red) and `PROCESSING`. Show an optional `capturedOn` beside "recorded on".
  - scribe:
    - `internal/handoff`: convert to 16-bit FLAC, hash it, resume from the server's offset, back off on errors.
    - `orient-scribe handoff -i x.wav -title … -hub URL -hub-token-file F`.
    - `store.Recording.CapturedOn`.
    - A `Keep` field: `PATCH /api/recordings/{id}` sets it, and `PruneAudio` skips kept recordings. On the recording page in orient, a Keep toggle with a chip in the list (AC 7).
  - `systemd/orient-tunnel.service` goes into the repo. It's for the laptop only (`install-units.sh` installs it only for `SCRIBE=recorder`, from inc 4).
    - It adds `-L 127.0.0.1:3014:127.0.0.1:3013`.
    - It pins its own ssh config with `-F ~/.ssh/orient-tunnel.conf`, so a `gitswitch` swap of `~/.ssh/config` can't break it.
    - Check :3014 is free first: with `ExitOnForwardFailure` set, one taken port takes down the whole tunnel, terminal included.
  - Verify:
    - Decode a recent `audio.ogg` to WAV, then `orient-scribe handoff … -hub http://127.0.0.1:3014`, with `systemctl --user restart orient-tunnel` partway through. This also drops the terminal, which is expected. The upload resumes, and the recording reaches `done` and is enhanced on `localhost:3000/recordings`, with `capturedOn: laptop`. `curl -sI localhost:3000/api/recordings/<id>/audio` returns 200 `audio/ogg`.
    - Run `eval/wer.py` on ES2004a raw and on a FLAC round-trip; the word error rates match within noise.
    - A Go test: `PruneAudio` removes an unkept recording older than 14 days and leaves a kept one. A `prune -dry-run` on the VM lists the kept recording as skipped. Toggling Keep on the page persists across a reload.
- [x] 4. **The laptop becomes a recorder only and hands each call off automatically.** (AC 2,3,5) — recorder live: dry run then real delete-on-receipt; outage holds uploading+lastError, drains 2s after; laptop MCP reads VM — done: ffb44e4
  - In recorder role, the store lives in a spool outside the vault, `~/.local/state/orient/scribe-spool/laptop/<id>/`.
    - A `Handoff` step replaces Transcribe, Summarise and Enhance in `process()`.
    - `Resume()` drains the spool at start.
    - Progress is kept in the meta: `{offset, sha256, attempts, lastError}`.
    - `notify-send` warns when a handoff has waited more than an hour.
  - On receipt (`complete` answered 200 with a matching sha256), the spool entry is deleted. Run a dry-run mode of that delete before it is enabled for real.
  - Laptop `scribe.env`: `-role recorder -hub http://127.0.0.1:3014 -hub-token-file …`.
  - The laptop MCP gets `ORIENT_SCRIBE_URL=http://127.0.0.1:3014`, because the morning digest and the other recording-reading skills run on the laptop.
  - From here `:3001` shows only live and uploading recordings; history is at `localhost:3000`.
  - While the VM is unreachable, captures queue in the spool and `notify-send` warns after an hour. Nothing is transcribed locally.
  - Rollback: the `both` role never reads the spool. Drain it first, or run `orient-scribe handoff` on each leftover, then remove `-role recorder`.
  - Verify:
    - Record two minutes of a video from `:3001` and from a reminder's Record button. Each ends with the spool empty, `done` and enhanced on the VM with `capturedOn: laptop`, and `find ~/Documents/obsidian/.knowledge/recordings/laptop -newer <marker>` empty.
    - `systemctl --user stop orient-tunnel`, record and stop: the recording sits at `uploading` with `lastError`. Restart the tunnel and it drains within a minute.
    - The laptop's `orient-recordings` MCP tool returns the new recording.
      gate: inc 3's handoff has worked on at least one real recording
          [x] confirmed
- [x] 5. **The VM relays start, stop, pause, resume and ignore to the laptop's recorder. `:3001` stays up alongside.** (AC 4) — relay live: start/pause/resume/stop via VM in <1.1s; disconnected start 409 with reason; restart hands off — done: 39e7fb8
  - `scribe/internal/server/agents.go`:
    - The recorder short-polls `POST /api/agents/laptop/poll` every 1–2 s. Each poll carries a snapshot (the live recording, pending uploads, the answer to the last command) and gets back the next command, if any. The recorder counts as disconnected after about 10 s of silence.
    - The VM's list merges in the snapshot's live and `uploading` items; its own copy wins once it has received one.
    - Controls for the live recording are queued for the recorder, and the route waits up to about 5 s for the answer.
    - `POST /api/recordings` is sent on to the recorder, or answers 409 "the laptop's recorder is not connected".
    - `GET /api/recordings/{id}` serves the snapshot while the recording is live.
  - orient: `recorder: {connected, lastSeen}` on the list, so the rail can say why Start is disabled.
  - Renaming during a call: only after handoff. That's the default; relaying titles waits for a need.
  - Verify:
    - At `localhost:3000/recordings`, Start. The laptop's scribe shows it live, and `pw-link -l | grep 'orient scribe'` shows the links.
    - Pause, resume, stop and ignore each show on the page within about 2 s, and sending the same stop twice is harmless.
    - With the laptop's scribe stopped, Start gives 409 and the rail shows the reason.
    > SUPERSEDED 2026-11-09 — a restart stops a recording by design (CLAUDE.md, Scribe); what it captured is handed off and appears on the VM. That's what was verified.
    - `systemctl --user restart orient-scribe` on the laptop mid-recording keeps it live on the VM page.
- [ ] 6. **Retire `:3001` and move every laptop client onto the VM.** (AC 5)
  - Remove the `orient-web` and `orient-desk` drop-ins.
  - The desk uses `-orient http://127.0.0.1:3000` and `-token` from a copy of the VM's write token. If the VM ever mints a new one, the desk gets 401; document that.
  - `systemctl --user disable --now orient-web`.
  - `install-units.sh` and `bootstrap.sh` gain a laptop recorder role, `SCRIBE=recorder`: desk, scribe, index, vault-sync and tunnel, with no web or pty. Reconcile Plan B's unfinished inc 5 (`bootstrap.sh HOST=laptop`) and INSTALL.md with it.
  - Update the repo docs: the Scribe and security sections of `CLAUDE.md`, `scribe/README.md`, `docs/INSTALL.md` (L64/L66/L81/L88), `desk/README.md`, and the vault `.gitignore` comment.
  - Verify:
    - `ss -ltn | grep -c ':3001 '` gives 0.
    - The top bar shows a live recording and Pause from its menu works.
    - Re-running `SCRIBE=recorder HEADLESS=1 scripts/install-units.sh` leaves orient-web disabled.
      gate: at least 3 real meetings recorded and controlled from the VM page after inc 5
          [ ] confirmed

Follow-up plans, not in this one:
- **Laptop vault writes land on the VM promptly.** The laptop's skills (digest, ledger, Tasks, People) keep writing markdown locally. Proposed: an event-driven sync, not rsync. A systemd path unit runs `vault-sync.sh` a few seconds after a change instead of waiting for the 90 s timer, then asks the VM to sync (`ssh … systemctl --user start orient-vault-sync`, started from the laptop). Git stays the only transport.
> SUPERSEDED 2026-11-09 — done in place instead: the VM adopts `laptop/` (`-adopt laptop`), and the audio was copied with checksums. See Decisions.
- **Move the 17 laptop recordings.** rsync their audio, then `orient-scribe adopt -from laptop` to move `laptop/<id>` to `vm/<id>`. Gate it on: the laptop confirmed recorder-only and synced, so `laptop/` has one writer; the retention answer; a prune dry run on the VM; and every sha256 matching before the laptop deletes anything.
- **Phone recorder.** A browser MediaRecorder, chunks buffered in IndexedDB, uploaded through orient route handlers to inc 2's ingest. The `room-mono` layout maps to the mic channel, not to "Them".

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-11-09 [inc 5] **The relay is live** (`39e7fb8`). The VM was deployed first, then the laptop's recorder, which polls `127.0.0.1:3014` every second. The VM's list reads `"recorders":[{"name":"laptop","connected":true}]`.
- 2026-11-09 [inc 5] **Every control through the VM's API, as orient calls it** (AC 4). Timed with curl against `127.0.0.1:3014`:
  - Start: 201 in 795 ms. The laptop went live with the same id, and `localhost:3000/recordings` showed it.
  - Pause: 200 in 752 ms (`pausedAt` set). Resume: 200 in 1,039 ms (`pausedAt` null).
  - Stop: 200 in 1,046 ms, `uploading`. A second stop: 409 "that recording is not running", which is harmless.
  - The VM then had it `done`, with sources me = JLAB mic and them = Nightly, `pausedSeconds` 3.05, length 7 s.
  - Ignore wasn't driven live (no app on the call side at the moment of the call); it's the same relay path, and `Relayable` covers it.
- 2026-11-09 [inc 5] **Disconnected** (AC 4): with the laptop's scribe stopped, after 12 s `recorders` read `connected:false`, and a start got 409 `this machine does not record, and no recorder is connected`. orient shows that text as the Start error.
- 2026-11-09 [inc 5] **Laptop scribe restarted mid-recording** (started from the VM): the restart stopped the recording by design and the captured audio was handed off. The VM had it `transcribing` moments later and the laptop spool was empty.
- 2026-11-09 [inc 5] **Go tests** (`-race -count=2`): starting on the server starts the recorder; the recorder's live recording is listed on the server; stopping on the server stops the recorder; no recorder gives a reason; only start, stop, pause, resume and ignore are relayable (DELETE, PATCH, trim, uploads and a `..` path refused); the recorder refuses a non-relayable command (403).
- 2026-11-09 [inc 5] **Cleanup:** both test recordings deleted on the VM; `vm/` is empty.
- 2026-11-09 **Regression from inc 4 fixed: the laptop's own recordings had become uneditable.** Harry couldn't name speakers on "Fuse Leadership Catchup" (`20261109-111949-d4b5`, recorded before the switch). The VM served `recordings/laptop/` read-only (another machine's; PATCH 409), and the laptop's recorder no longer reads the vault (GET 404).
  - Fix (`f7b7299`): `serve -adopt laptop` (and `prune -adopt`) makes the VM write `laptop/` in place, so nothing moves and ids and links are unchanged.
  - The laptop's 13 remaining `audio.ogg` (128 MB) were copied with `tar` over ssh (the VM has no rsync); all 13 sha256 match, and git sees no change.
  - `prune -dry-run -adopt laptop`: would delete 0.
  - The VM's `scribe.env` is `-role server -threads 8 -adopt laptop`; the log reads "writing the recordings of laptop as well as this machine's".
  - Every laptop recording is now `readOnly: false`; 13 have audio, a no-op PATCH answers 200, and the audio route answers 206 `audio/ogg`.
  - The laptop's audio copies were then deleted, after a re-check (13 removed, 0 left).
- 2026-11-09 [inc 4] **The laptop is a recorder** (`ffb44e4`, live since 12:11). The switch waited until a live meeting ("Fuse Leadership Catchup", 42 min) had finished processing the old way.
  - The log reads `serving on 127.0.0.1:3013 as recorder, recordings in ~/.local/state/orient/scribe-spool` and `handing recordings off to http://127.0.0.1:3014`.
- 2026-11-09 [inc 4] **Dry run first** (`-handoff-dry-run`). A 15 s capture went `uploading` at stop, then "handed off; dry run, so …/scribe-spool/laptop/20261109-121107-596a is kept". The spool held `audio.wav`, `audio.flac` and `meta.json`; the VM had it with `host=vm`, `capturedOn=laptop` and length 15 s. The music warning still fired on a Firefox mix, so recorders keep it.
- 2026-11-09 [inc 4] **Real handoff deletes the laptop copy** (AC 3). With `SCRIBE_ARGS=-role recorder`, a 15 s capture logged "handed off, local copy deleted" 16 s after stop. The spool was empty, the VM had it with length 15 s, and nothing new appeared under the vault's `recordings/laptop/`.
- 2026-11-09 [inc 4] **Server unreachable** (AC 2, 3). The VM's scribe was stopped, then a 10 s capture was taken.
  - The client retried at 1 s, 2 s, … up to 1 min within its 2-minute bound, then the recorder recorded `attempts=1` and `lastError=context deadline exceeded (… read tcp …3014 …)` and kept it `uploading`.
  - VM scribe restarted: drained 2 s later ("handed off, local copy deleted"). The VM had it at 10 s.
- 2026-11-09 [inc 4] **The laptop orient MCP reads the VM's scribe** (AC 5). `~/.claude.json` `mcpServers.orient.env.ORIENT_SCRIBE_URL=http://127.0.0.1:3014` (backup `~/.claude.json.bak-orient-mcp-*`). Driving `orient-mcp` over stdio with that env, `orient-recordings` answered "10 recordings of 21", including "Fuse Leadership Catchup" and the handed-off tests. Running sessions pick it up on `/mcp` reconnect.
- 2026-11-09 [inc 4] **Cleanup:** the three test recordings were deleted on the VM (204 each). `recordings/vm/`, `scribe-uploads/` and the laptop spool are all empty. Two had empty transcripts (music only), so their summary and enhancement reported "the transcript is empty"; that's expected.
- 2026-11-09 [inc 4] **Gate: the handoff works on a real laptop recording.** A copy of `20261029-153138-d1e2` ("SFTP Folder Discussion", 443 s, 48 kHz stereo Opus from the laptop recorder) was handed off as `20261109-120000-3e14`.
  - 17,459,949 bytes; the sha256 matched.
  - On the VM: `done`, enhanced, `call=true`, 45 transcript lines (the original has 41), and the same tl;dr gist.
  - The copy was deleted (204).
  - It exposed a bug, now fixed in `a325b35`: the manual handoff sent no `endedAt`, so the length came out at −2331 s. `handoff` now ends the recording at start plus the audio's `ffprobe` duration.
- 2026-11-09 [inc 3] **Live handoff over the tunnel** (`0dae982`, `-chunk` in `eb626ea`; AC 2, 6).
  - The full meeting: `orient-scribe handoff -i ES2004a.stereo-me0.wav` (public AMI audio, not a real meeting) sent 16,811,508 bytes of FLAC through `127.0.0.1:3014`. The receipt sha256 `786665a8…` matched.
  - The VM stored it as `vm/20261109-113000-5f55` with `capturedOn: laptop` and `received.bytes` 16811508. It went `queued`, then `transcribing`, then `done`, and was enhanced, with a summary.
  - `curl -H 'Range: bytes=0-1023' localhost:3000/api/recordings/<id>/audio` answered 206 `audio/ogg`, so audio plays through the VM's orient.
- 2026-11-09 [inc 3] **Resume across a real tunnel drop.** A 5-minute clip at `-chunk 8192`; `systemctl --user restart orient-tunnel` once the VM's staged part held 425,984 bytes.
  - The client logged `attempt 1 failed, retrying in 1s: … EOF`, resumed from the VM's offset, and finished at 11:13:19 with sha256 `6245f78b…`. That's identical to an uninterrupted run of the same clip, so the FLAC encode is deterministic.
- 2026-11-09 [inc 3] **FLAC costs no accuracy:** `eval/wer.py` against the AMI words for ES2004a.
  - Raw WAV transcribed on the VM (inc 1): WER 20.7% (S 139, D 334, I 49).
  - The FLAC handoff copy: WER 20.7% (S 139, D 334, I 49). Identical.
- 2026-11-09 [inc 3] **Keep mark (AC 7).**
  - PATCH `{"keep":true}`: the VM page reads "Audio kept: it is not deleted after 14 days" with "let it expire", and the list shows a `kept` chip.
  - PATCH `{"keep":false}`: back to "Audio is deleted 14 days after recording" with "keep audio".
  - The page shows "captured on laptop".
  - Go tests: `TestPruningSparesAKeptRecording`, `TestARecordingCanBeMarkedToKeepItsAudio`.
- 2026-11-09 [inc 3] **orient tolerates new statuses:** `toRecordingStatus` maps unknown values to `unknown` (no "unexpected shape"); `uploading` is in-flight and `unknown` isn't (`tests/unit/recording-status.test.ts`). Typecheck clean, lint has only the 2 existing `globals.css` warnings, 4,767 tests pass.
- 2026-11-09 [inc 3] **Deploy order held.** orient was deployed on the VM and on the laptop's `:3001` before either scribe. The repo `orient-tunnel.service` replaced the hand-written one (backup `orient-tunnel.service.bak-handwritten`); `:3000`, `:3001`, `:3011`, `:3013` and `:3014` are all listening, and `:3014` reaches the VM's scribe (200). The tunnel uses its own `~/.ssh/orient-tunnel.conf` (Host `orient-vm`, `IdentitiesOnly`).
- 2026-11-09 [inc 3] **Cleanup:** the three test recordings were deleted (204 each); the VM's `recordings/vm/` and `scribe-uploads/` are empty.
- 2026-11-09 [inc 2] **Upload ingest live on the VM** (`6898741`). `serve` turns uploads on only when `~/.config/orient/scribe-hub-token` is non-empty; the log reads `accepting uploads, staged in ~/.local/state/orient/scribe-uploads`.
  - No token: 401 `missing or wrong hub token`.
  - `Host: evil.example`: 403.
  - The list is still 17.
  - The laptop's scribe (rebuilt) serves as `both` with uploads off, since it has no server token file.
  - `localhost:3000/recordings` (VM) and `localhost:3001/recordings` (laptop) both answer 200, with no "unexpected shape" or "not running".
- 2026-11-09 [inc 2] **Gate:** a 32-byte random hub token generated on the VM (mode 600, never printed) and copied to the laptop as `~/.config/orient/scribe-hub-client-token` (600). The sha256 of both copies matches.
- 2026-11-09 [inc 2] **Go tests** (`go test -race -count=3`), one behaviour each:
  - Refused without the token (401), and off without a token (404).
  - A completed upload is stored with its receipt and `capturedOn`, and is processed to `done`.
  - Starting again reports the resume offset; a wrong offset gets 409 with the true offset.
  - Complete before every byte arrives is 409; a damaged upload (sha mismatch) is 422 and its part is dropped.
  - Complete again gives the same receipt; an id received with other content is 409.
  - Appending without the total size until complete works (AC 6).
  - A non-loopback Host is 403.
  - Store: `Ingest` moves the audio in, and an unfinished `.incoming-<id>` isn't listed.
- 2026-11-09 [inc 1] **The VM's scribe runs as a server** (AC 1). It was installed with `SCRIBE=server HEADLESS=1 scripts/install-units.sh`, which wrote `scribe.env` as `SCRIBE_ARGS=-role server -threads 8` and enabled the unit without starting it.
  - `prune -dry-run` before the first start: "would delete 0 audio file(s)".
  - Started: the log reads `serving on 127.0.0.1:3013 as server`.
  - `GET /api/recordings`: 17 recordings, hosts `["laptop"]`, readOnly `[true]`.
  - `POST /api/recordings`: 409 `{"error":"this machine does not record"}`.
  - No reminder, nudge or playerctl lines in the journal.
  - `localhost:3000/recordings` on the laptop (the VM's orient, through the tunnel) answers 200 and lists them, with no "not running" or "unexpected shape" error.
- 2026-11-09 [inc 1] **VM transcription speed:** `nice -n 10 orient-scribe process -threads 8` on `ES2004a.stereo-me0.wav` (1049 s) took 3m39s, a real-time factor of 0.21 against the ≤0.5 bar. Per channel: me RTF 0.088, them RTF 0.119; diarisation is most of the time (about 1m10s per channel).
- 2026-11-09 [inc 1] **Gate confirmed.** VM: static ffmpeg n9.0.2 (BtbN `ffmpeg-n9.0-latest-linux64-gpl-9.0`, sha256 verified against the release's `checksums.sha256`, libopus encoder present) in `~/.local/bin`, so no pacman change on a box whose package DB is stale. `claude -p` on the VM answered (signed in). Laptop: `~/.config/orient/host` written as `laptop`.
- 2026-11-09 [inc 1] **Laptop unchanged in the `both` role** (`66511dc`): rebuilt scribe and installed `systemd/orient-scribe.service` (now with `EnvironmentFile` and `$SCRIBE_ARGS`). The log reads `serving on 127.0.0.1:3013 as both`. An 8 s recording went started, then `queued` after stop, then `done`, then deleted (204), leaving nothing in the vault.
- 2026-11-09 [inc 1] **`go test ./...`** in `scribe/` green, including the new `TestAMachineWithNoRecorderRefusesToStart` (409 "does not record", nothing live). `make fmt-check vet` clean.
- 2026-11-09 [inc 1] **VM sparse list lifted for recordings only:** `git sparse-checkout list` reads `/*`, `!/Bifrost/HR/`, `!/Bifrost/Team/`, `!/Interviews/`. 17 recordings are on disk under `recordings/laptop/`, and HR and Interviews are still absent.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- [inc 4] **A recording started from a reminder's Record button** wasn't driven live; the reminder calls the same `s.Start` as `POST /api/recordings`, which was. Prove it at the next reminded meeting.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->
- **2026-11-09 — The VM adopts `recordings/laptop/` in place** (`-adopt laptop`), replacing the planned follow-up that would `adopt`-move each recording to `vm/<id>`. One writer still holds, because the laptop's recorder never touches `laptop/`. The laptop can no longer go back to the `both` role without handing `laptop/` back first, which Harry accepts. His direction: "the laptop should just be a window in to orient, and write files to the server", with the phone as the next capture device.
- **2026-11-09 — The receipt is made atomic by `Store.Ingest`.** The recording is built in `<host>/.incoming-<id>/` (audio, then `meta.json.tmp`, both gitignored), synced, and renamed into place. The receipt goes out only after that, so the laptop can't delete audio the VM doesn't durably have.
- **2026-11-09 — All of scribe's routes now refuse a non-loopback Host,** not just the upload routes, guarding against DNS rebinding from a browser. The port is ignored because the `:3014` forward keeps its own.
- **2026-11-09 — Harry's answers to the open questions.** Recordings, sensitive ones included, may live on the VM. Retention stays at 14 days, plus a keep mark (AC 7). The laptop copy is deleted on receipt. All transcription is on the VM, with no local fallback. Recording-reading skills stay on the laptop, so the laptop MCP reads the VM's scribe. This drops the review's 7-day `handed-off/` buffer: the VM's sha256-checked, synced-to-disk receipt is the safety net.
- **2026-11-09 — Knowingly overrides "audio stays on the machine that recorded it".** That rule was agreed 2026-11-02 and is stated in CLAUDE.md L103, scribe/README L25, Systems/orient architecture.md, the vault `.gitignore` comment and INSTALL.md L88. It also overrides [[go-remote-and-bootstrap-a-fresh-machine]] AC 5's exclusion of recordings from the VM. That exclusion rested on "the VM is headless and doesn't record". Harry's call on 2026-11-09: the VM becomes the home for recordings, and the sensitivity exclusions for HR, Team and Interviews stay. Record it durably with `wp decide --record` at sign-off.
- **2026-11-09 — The laptop pulls controls from the VM; the browser doesn't call the laptop's scribe directly.**
  - A direct call would need CORS on scribe and a ticket the VM issues but the laptop checks.
  - The server-rendered rail, the desk and the MCP would never see a live recording.
  - Polling keeps orient on the VM as the only brain, and the phone gets the same path.
  - The cost: up to 2 s of control latency, and two tokens copied to the laptop (hub, write).
- **2026-11-09 — New recordings live under `vm/<id>`, with `capturedOn` set.** The directory is what keeps git sync to one writer. If the laptop rolls back to `both`, it writes `laptop/` and the VM writes `vm/`, so they never collide. The "another machine's recordings are read-only" rule stays as it is.
- **2026-11-09 — Upload protocol kept small:** offset resume and a whole-file sha256 at `complete`. Per-chunk checksums and `HEAD` wait for the phone plan. The traffic is laptop-only, over an ssh tunnel that already protects it.
- **2026-11-09 — Handoff goes over a separate forward (`:3014` to the VM's `:3013`), not through orient on `:3000`.** A `pnpm deploy:web` would cut uploads and polls mid-way, and the laptop would need orient's write token just to upload.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
- **Workstation SSH only allows forwards started from the laptop** (`AllowTcpForwarding local`, set in ilg-platform/images and checked by its smoke test). No orient feature can rely on the VM opening a connection to the laptop.
- **`RecordingSchema.status` is a strict enum.** One status orient doesn't know fails the whole Recordings list ("unexpected shape"), so scribe must never send a new status before orient accepts it.
- **`make -C scribe install` installs a unit hard-coded to `/home/hjf`.** It breaks any machine with a different user, such as the VM's `harry`. `systemd/orient-scribe.service` uses `%h`.
- **design.md's Fixtures bullet still says `~/.local/state/orient/scribe/`,** but recordings moved into the vault in d62e6b8.
- **`next build` (the laptop's `pnpm deploy:web`) once hung for 10+ min in static generation,** with a worker idle in `epoll` and no network wait. orient-web stays stopped meanwhile. Killing the process group and rerunning built normally in about 3 min. If it recurs, look at the prerender workers before assuming a code fault.
- **The desk reads `:3000` by default,** so the tunnel sends it to the VM. It has to be pointed elsewhere for as long as recordings live on the laptop (interim drop-in, 2026-11-09).
