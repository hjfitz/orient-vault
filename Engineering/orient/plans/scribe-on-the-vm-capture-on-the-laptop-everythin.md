---
ticket: "none"
title: "Scribe on the VM: capture on the laptop, everything else on the VM"
service: "orient"
status: draft
created: "2026-11-09"
updated: "2026-11-09"
repo: "/home/hjf/projects/orient"
worktree: "/home/hjf/projects/orient"
branch: "master"
base: "origin/master"
base_sha: "1b8ffbf28"
pr:
tags: [waypoint, plan]
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
- [ ] 3. The laptop writes no new recordings into the vault. Its local copy is kept briefly after the VM confirms receipt, then removed.
- [ ] 4. From `localhost:3000/recordings` on the laptop: start, pause, resume, stop and ignore act on the laptop's capture within about 2 s. With the recorder disconnected, Start is refused and the page says why.
- [ ] 5. The laptop runs no orient-web. The top-bar widget, the reminders and the laptop's orient MCP all show and control recordings through the VM. Re-running `install-units.sh` on the laptop doesn't bring orient-web back.
- [ ] 6. The upload ingest accepts a recording whose total size isn't known until the end, appended from a reported offset. This is what the phone recorder needs.

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
- UNRESOLVED: Sensitive transcripts and their audio (1:1s, interviews) will live on a company-hosted VM with passwordless sudo, where project admins can snapshot the disk. `HR`, `Team` and `Interviews` are excluded from it for sensitivity. Is that acceptable for recordings? Linked: should `orient-recordings` withhold 1:1s and interviews (`docs/mcp-spec.md` L149/L184)?
- UNRESOLVED: Audio retention on the VM: keep 14 days, or longer now the VM is the home?
- UNRESOLVED: When the laptop copy goes: after the VM confirms receipt (the plan's default, with a 7-day `handed-off/` buffer), or only after the VM has transcribed it?
- UNRESOLVED: If the laptop is offline for a long time, should it ever fall back to transcribing locally, or only queue and notify?
- UNRESOLVED: Where do the morning digest and the other skills that read recordings run (laptop, VM, both)? This decides whether the laptop MCP points at the VM's scribe.

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

- [ ] 1. **The VM runs scribe as a server and lists the synced transcripts read-only. The laptop is unchanged.** (AC 1)
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
    - gate: on the VM, ffmpeg is installed and `claude -p` answers when signed in. On the laptop, `~/.config/orient/host` reads `laptop`.
          [ ] confirmed
- [ ] 2. **Upload ingest on the VM, behind a token.** (AC 2,6)
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
    - gate: hub token generated on the VM and copied to the laptop (`~/.config/orient/scribe-hub-token`, mode 0600)
          [ ] confirmed
- [ ] 3. **A manual `handoff` on the laptop, the tunnel unit in the repo, `capturedOn`, and a status schema that tolerates unknown values.** (AC 2,6)
  - orient first, deployed on the VM and on `:3001`: unknown statuses show as "unknown" instead of failing the list. Add `uploading` to the `RecordingStatus` union, the label and colour maps (an in-flight accent, not red) and `PROCESSING`. Show an optional `capturedOn` beside "recorded on".
  - scribe:
    - `internal/handoff`: convert to 16-bit FLAC, hash it, resume from the server's offset, back off on errors.
    - `orient-scribe handoff -i x.wav -title … -hub URL -hub-token-file F`.
    - `store.Recording.CapturedOn`.
  - `systemd/orient-tunnel.service` goes into the repo. It's for the laptop only (`install-units.sh` installs it only for `SCRIBE=recorder`, from inc 4).
    - It adds `-L 127.0.0.1:3014:127.0.0.1:3013`.
    - It pins its own ssh config with `-F ~/.ssh/orient-tunnel.conf`, so a `gitswitch` swap of `~/.ssh/config` can't break it.
    - Check :3014 is free first: with `ExitOnForwardFailure` set, one taken port takes down the whole tunnel, terminal included.
  - Verify:
    - Decode a recent `audio.ogg` to WAV, then `orient-scribe handoff … -hub http://127.0.0.1:3014`, with `systemctl --user restart orient-tunnel` partway through. This also drops the terminal, which is expected. The upload resumes, and the recording reaches `done` and is enhanced on `localhost:3000/recordings`, with `capturedOn: laptop`. `curl -sI localhost:3000/api/recordings/<id>/audio` returns 200 `audio/ogg`.
    - Run `eval/wer.py` on ES2004a raw and on a FLAC round-trip; the word error rates match within noise.
- [ ] 4. **The laptop becomes a recorder only and hands each call off automatically.** (AC 2,3,5)
  - In recorder role, the store lives in a spool outside the vault, `~/.local/state/orient/scribe-spool/laptop/<id>/`.
    - A `Handoff` step replaces Transcribe, Summarise and Enhance in `process()`.
    - `Resume()` drains the spool at start.
    - Progress is kept in the meta: `{offset, sha256, attempts, lastError}`.
    - `notify-send` warns when a handoff has waited more than an hour.
  - On receipt, the spool entry moves to `scribe-spool/handed-off/`, which is pruned after 7 days. Dry-run that prune before it is enabled.
  - Laptop `scribe.env`: `-role recorder -hub http://127.0.0.1:3014 -hub-token-file …`.
  - The laptop MCP gets `ORIENT_SCRIBE_URL=http://127.0.0.1:3014`, depending on the digest-location answer.
  - From here `:3001` shows only live and uploading recordings; history is at `localhost:3000`.
  - Rollback: the `both` role never reads the spool. Drain it first, or run `orient-scribe handoff` on each leftover, then remove `-role recorder`.
  - Verify:
    - Record two minutes of a video from `:3001` and from a reminder's Record button. Each ends with the spool empty and `handed-off/` holding it, `done` and enhanced on the VM with `capturedOn: laptop`, and `find ~/Documents/obsidian/.knowledge/recordings/laptop -newer <marker>` empty.
    - `systemctl --user stop orient-tunnel`, record and stop: the recording sits at `uploading` with `lastError`. Restart the tunnel and it drains within a minute.
    - The laptop's `orient-recordings` MCP tool returns the new recording.
    - gate: the retention, delete-timing and offline-fallback questions above are answered, and inc 3's handoff has worked on at least one real recording
          [ ] confirmed
- [ ] 5. **The VM relays start, stop, pause, resume and ignore to the laptop's recorder. `:3001` stays up alongside.** (AC 4)
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
    - gate: at least 3 real meetings recorded and controlled from the VM page after inc 5
          [ ] confirmed

Follow-up plans, not in this one:
- **Move the 17 laptop recordings.** rsync their audio, then `orient-scribe adopt -from laptop` to move `laptop/<id>` to `vm/<id>`. Gate it on: the laptop confirmed recorder-only and synced, so `laptop/` has one writer; the retention answer; a prune dry run on the VM; and every sha256 matching before the laptop deletes anything.
- **Phone recorder.** A browser MediaRecorder, chunks buffered in IndexedDB, uploaded through orient route handlers to inc 2's ingest. The `room-mono` layout maps to the mic channel, not to "Them".

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
- **The desk reads `:3000` by default,** so the tunnel sends it to the VM. It has to be pointed elsewhere for as long as recordings live on the laptop (interim drop-in, 2026-11-09).
