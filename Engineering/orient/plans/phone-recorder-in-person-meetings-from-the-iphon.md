---
ticket: none
title: 'Phone recorder: in-person meetings from the iPhone, offline-first'
service: orient
status: active
created: '2026-11-09'
updated: '2026-11-09'
repo: /home/hjf/projects/orient
worktree: /home/hjf/projects/orient
branch: master
base: origin/master
base_sha: 41c98708f
pr: null
tags:
- waypoint
- plan
impl_model: opus
impl_effort: high
---
# none — Phone recorder: in-person meetings from the iPhone, offline-first

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
Record in-person meetings on Harry's iPhone. Safari on the phone opens orient through a Termius forward (`localhost:3000` on the phone goes to the VM), records the room with `MediaRecorder`, and the recording reaches the VM's scribe like any other: transcribed with "Harry" or "Room N" labels, summarised, enhanced, listed and playable. iOS may suspend Termius, and with it the tunnel, while Safari has the screen, so the recorder is offline-first. Every chunk is kept on the phone (IndexedDB) and sent whenever the tunnel answers, and nothing is lost if the tunnel was down for the whole meeting, the tab reloaded, or Safari was killed. Calls (phone or Teams audio) are out of scope; a browser can't capture another app's audio. This follows [[scribe-on-the-vm-capture-on-the-laptop-everythin]], whose upload ingest it reuses.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. A meeting recorded on the iPhone with the tunnel up appears on `localhost:3000/recordings`, processed as in-person ("Harry" or "Room N" labels, no call setting), with `capturedOn: phone`.
- [ ] 2. A meeting recorded with the tunnel down throughout is sent once the tunnel is back, and the VM's receipt (size and sha256) equals what the phone held.
- [ ] 3. A reload or kill of Safari mid-recording loses at most the last chunk (≤5 s). The recording reappears as interrupted and can be sent or discarded; discarding also removes any partial upload on the VM.
- [ ] 4. A recording live in one tab is never shown as interrupted in another.
- [ ] 5. The phone never holds the hub token. Only loopback same-origin requests carrying the recorder header reach the upload routes, and the layout and meeting context are decided server-side.
- [ ] 6. The Recordings page names the device on each button: "record on laptop" (disabled with a reason when the laptop isn't connected) and "record on this device".

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- **scribe:**
  - `internal/server/upload.go`: the layout check (l.142), `Convert` (l.278) under `uploadMu`; the meta is fixed at start (l.155-165).
  - `cmd/orient-scribe/serve.go`: `convertUpload`.
  - `cmd/orient-scribe/handoff.go`: `Layout` is hard-coded to `stereo` (l.78, l.120).
- **orient:**
  - `src/config.ts`: a new `scribeHubToken()`, read from the VM's `~/.config/orient/scribe-hub-token` and never minted.
  - `src/adapters/scribe.ts`: `call()` hard-codes JSON and drops the 409 `{offset}`, so append needs its own fetch path.
  - `src/domain/recordings.ts`: `startRequest` is async.
  - New routes `app/api/recordings/uploads/…` (a static segment beside `[id]`, like `glossary`); the guard is `src/lib/allowed-host.ts` `hostAllowed` (Origin-based).
  - New page `app/recordings/here/`.
  - `src/components/recordings/RecordPanel.tsx` (copy at l.281) and the desk labels in `src/lib/desk.ts`.
  - `app/api/desk/act/route.ts:25`, a stale comment.
  - The root `app/layout.tsx` mounts `FocusEffects` (`router.refresh` at l.81), `CommandPalette`, `Chords`, `QuickView` and `TerminalPanel`, any of which can navigate or fetch on every page.
- **Next 16:** an RSC fetch that fails offline falls back to a full page load unless `experimental.useOffline` (`fetch-server-response.js` l.209-243), so the recorder page must never trigger one. A failed server action rejects rather than reloading (`server-action-reducer.js` l.85-98), but actions are capped at 1 MB and run one at a time, so uploads use route handlers.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **In-person needs no pipeline change.** A room-mono upload converted to stereo [mono, silence] gets the in-person path: `engine.Process` skips the silent channel, `speakerNames` gives "Harry"/"Room N", `IsCall(nil)` is false, and the in-person prompts and room VAD 0.35 apply. It's the shape of the `ES2004a.room-array.wav` eval fixture. The ffmpeg filter `[0:a]aformat=channel_layouts=mono,aresample=16000[m];anullsrc=r=16000:cl=mono[z];[m][z]join=inputs=2:channel_layout=stereo[a]` with `-shortest` was run on a 3 s mono sine: it exited 0 and gave 3.000 s at 16 kHz, 2 channels, right channel silent. (Source read and fact-check, 2026-11-09.)
- **The VM is single-user** (`getent passwd`: only `harry`, uid 2001), so loopback-only routes plus the ssh tunnel are real protection. No new browser credential. (Checked 2026-11-09.)
- **The IndexedDB origin is `http://localhost:3000`.** Unsent recordings are tied to the Termius forward staying on local port 3000.
- **Unknown until measured on the phone (inc 1):**
  - the MediaRecorder type (`audio/mp4` AAC expected);
  - whether `timeslice` chunks join into a decodable file, including one cut at a chunk boundary;
  - how capture behaves on Control Centre, Siri, a call or a screen lock;
  - whether Termius keeps the forward alive in the background (with and without its location keep-alive);
  - whether a wake lock is available;
  - whether `persist()` and the quota hold;
  - how long hashing 60 MB takes;
  - whether Safari plays `audio.ogg`.
> SUPERSEDED 2026-11-09 — Harry: "use context wherever possible, I think that's important. I'm happy to pause processing notes until then." Context is resolved when the recording is sent, and the prompts are worded for it (see Decisions).
- UNRESOLVED: **Meeting context for a recording made entirely offline.** It's resolved at the first successful send, which is after the meeting, so it includes notes written during it. The summary and enhance prompts label it "What Harry's notes said before the meeting". Use it anyway (fixing the label), or send no context when the start wasn't online?
- UNRESOLVED (after the spike): **if capture dies mid-meeting** (Siri, a call, a reload), should the result be one recording made of segments (a scribe and client change, a follow-up plan) or two recordings (no scribe change)?

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
- [ ] 1. **The iPhone spike probe.**
  - `scribe/eval/phone-probe.html` plus `scribe/eval/phone-probe-server.py`: binds 127.0.0.1:3020, run with `python3 -I`, and saves PUTs to `~/.cache/orient-scribe/phone-probe/`, outside the vault.
  - The probe records format support, chunks in IndexedDB as ArrayBuffers, a reload mid-recording, interruption events, wake lock, `storage.estimate`/`persist`, a tunnel heartbeat every 5 s, a 60 MB digest timing, and ogg playback.
  - verify: desktop Chromium with `--use-fake-device-for-media-stream` (webm) against the VM's probe. The receiver saves the full and the cut file, and `ffmpeg -v error -i <f> -f null -` decodes both.
      gate: Harry ran the probe on the iPhone (a Termius forward of 3020; one 45-minute heartbeat session with keep-alive on, one with it off, one with the screen locked), and the results table is in this plan
            [ ] confirmed
      gate: the iPhone's timeslice chunks and the chunk-boundary cut both decode. If not, stop and re-plan (segments)
            [ ] confirmed
- [ ] 2. **scribe accepts `room-mono`.** (AC 1)
  - `Layout` accepts `stereo` (the default) and `room-mono`; anything else stays 422.
  - `Converter` takes the layout, and `convertUpload` applies the room-mono filter above.
  - Conversion runs under `context.WithoutCancel` with a timeout, so a dropped phone doesn't kill ffmpeg.
  - `UploadMeta` and `store.Recording` gain `contextAt`, the time the meeting context was looked up. When it's after `endedAt`, the summary and enhance prompts (`summary.go`, `enhance.go`, where they now say "What Harry's notes said before the meeting") read "Harry's notes for this meeting, including any written during or after it". Recordings without `contextAt`, including every laptop one, keep today's wording.
  - `handoff -layout`, which only sets the layout field; FLAC keeps the channel count.
  - verify:
    - Go tests: a `contextAt` after the end gives the during-or-after wording; none keeps the before-the-meeting wording; room-mono accepted; an unknown layout is 422; the converter is told the layout; a conversion outlives its request; room-mono becomes stereo with a silent right (ffmpeg, skipped without it).
    - On the VM: AAC 64 kbps mono fMP4 made from `ES2004a.Array1-01.wav`, then `orient-scribe handoff -i x.m4a -layout room-mono -hub http://127.0.0.1:3013 -hub-token-file ~/.config/orient/scribe-hub-token -captured-on phone`. It shows "Room N" labels and the in-person setting; record DER (`der -channel me`) against the room-array baseline, then delete the recording.
      gate: on the VM, `orient-scribe prune -dry-run -adopt laptop` is clean and no laptop recording is live, before scribe restarts
            [ ] confirmed
- [ ] 3. **orient's upload proxy, server only.** (AC 5)
  - `scribeHubToken()`; adapter functions `uploadStart` and `uploadComplete` (with a 150 s timeout and no client abort signal) and `uploadAppend` (its own fetch: octet-stream, and the 409 `{offset}` passed through).
  - `src/lib/recorder-guard.ts`: `hostAllowed` against localhost/127.0.0.1 plus a required `X-Orient-Recorder: 1` header, which forces a CORS preflight that Next's automatic OPTIONS never satisfies.
  - The routes:
    - `POST /api/recordings/uploads`: `{id, title, docId?, startedAt, endedAt, pausedSeconds, mime}`, then `await startRequest` at send time (so the newest notes are included), stamped `contextAt: now`, then layout `room-mono`, `capturedOn: phone`, `sources.me: ['phone mic']`.
    - `PATCH /api/recordings/uploads/[id]`: at most 8 MB.
    - `POST …/[id]/complete` with `{size, sha256}`.
    - `DELETE …/[id]`, proxied to a new scribe `DELETE /api/uploads/{id}` that drops the `.part` and `.json` (a small Go change with its test).
  - No token gives 503. Fix the stale `desk/act` comment.
  - verify:
    - vitest, one behaviour each: a foreign Origin is refused; a missing header is refused; a body over 8 MB is refused before scribe; the layout is always room-mono; a 409 keeps its offset; complete doesn't forward the abort; no token gives 503; a meeting docId carries its context.
    - Go test for the DELETE.
    - On the VM after `pnpm deploy:web` (check `/sprint` first): curl start, two PATCHes with one deliberately at a stale offset (409), complete; it processes. A DELETE on a second partial leaves no staged files. Delete the test recording.
      gate: answer the context question above, which changes what start sends
            [x] confirmed
- [ ] 4. **The recorder page: local capture, recovery and export.** (AC 3, 4, 6)
  - `app/recordings/here/` has a tab title and no Sidebar or AutoRefresh, and the root layout's navigators (`FocusEffects`, `CommandPalette`, `Chords`, `QuickView`, `TerminalPanel`) render nothing on this path. If a pathname check turns out leaky, move to a route group with its own root layout.
  - `PhoneRecorder`:
    - An IndexedDB row is written before capture; each chunk is appended in one transaction across both stores; the schema is versioned from day one.
    - Pause and resume; a wake lock taken on start and re-taken when the page is visible again; background gaps recorded and shown on return.
    - The recording tab holds `navigator.locks.request('rec-'+id)`, so a row counts as interrupted only when its lock is free.
    - Interrupted rows can be sent later, exported ("save file", through the share sheet), or discarded with a confirm.
  - UI: a live recording is amber, never red; "waiting" and "interrupted" are amber or `fg-2`; buttons are `h-10`.
  - `RecordPanel`: "record on laptop" (disabled with "laptop not connected" when the scribe list's `recorders` says so; this was promised in the last plan's inc 5 and never built) and "record on this device →". The copy is fixed and the desk labels match.
  - verify:
    - vitest: the id matches the scribe regex; chunk bookkeeping is right; liveness follows the lock; RecordPanel names both devices and disables the laptop one when it's disconnected.
    - Chromium with a fake mic: a reload mid-recording gives an interrupted row; a second tab doesn't show the live one as interrupted; an exported file decodes.
      gate: Harry exported an iPhone recording, sent it with `handoff -layout room-mono`, and it appeared processed in orient
            [ ] confirmed
- [ ] 5. **The uploader and the backlog banner.** (AC 1, 2, 3)
  - `uploader.ts`, single-flight per tab:
    - start (with the final `endedAt` and `pausedSeconds`, known by then), then PATCH from the server's offset in batches of up to 1 MB built from the stored chunks (a 409 adopts the server's offset), then the sha256 (computed once and stored on the row), then complete.
    - A receipt whose sha matches the row deletes the chunks; the small sent row is kept.
    - A 422 restarts from 0. Timeouts are 20 s, or 180 s for complete. Back-off is 2 s doubling to 60 s, reset by `online`/`pageshow`/visible/"send now".
  - `PhoneBacklog` on `/recordings`: "N recordings on this device not yet sent". It warns that Safari clears script-written storage after 7 days without a visit.
  - verify:
    - vitest: `sliceFrom` and `nextStep` on an ffmpeg fMP4 fixture split at arbitrary offsets.
    - Chromium against the VM: offline, then stop, then back online, and it sends with receipt bytes and sha equal to the row's and the chunks deleted. A page killed mid-upload resumes from the server's offset.
      gate: on the iPhone: (1) 5 minutes with the tunnel up; (2) Termius quit before stop, then sent later; (3) a reload mid-recording, sent as interrupted; (4) airplane mode for 20 minutes, then sent, receipt equal; (5) Safari quit after stop, resumed from the server's offset. Each recording deleted afterwards
            [ ] confirmed

Follow-ups, not in this plan:
- Live upload during recording, plus `endedAt` at complete: only if the spike shows the tunnel survives in the background.
- Multi-segment recordings, if the second spike gate fails or by the answer to the interruption question.
- A service worker or Home Screen install, if a reload mid-meeting with the tunnel down proves common.
- Staged phone uploads shown in the list, deduplicated against the laptop's `uploading` snapshot.
- AAC playback on the phone, if Safari can't play ogg.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-11-09 [inc 1] **The probe works end to end in desktop Chrome with a fake mic** (`4504f06`, report fix `3b…` on master). Headless Chrome (`--use-fake-device-for-media-stream`, `?auto=12`) ran against the VM's receiver (`127.0.0.1:3020`, `--sample` a real `audio.ogg`) through a temporary forward.
  - It recorded, reloaded at 12 s, found the session `interrupted`, sent the full and cut files, hashed 60 MB in 57 ms, and sent the report with every stored event (including those before the reload) and each chunk's time and size.
  - On the VM, `ffmpeg -v error -i <f> -f null -` decodes both: full 10.10 s (the last ≤5 s lost to the reload, as designed) and cut (1 of 2 chunks) 0.105 s.
  - **Chrome's `audio/mp4` holds Opus, not AAC**, and its first 5 s chunk was only 641 bytes (0.1 s of audio): chunk boundaries don't track the timeslice. The cut file still decodes. Whether Safari does the same is the second gate.
  - Wake lock was granted, and `pagehide`/`visibilitychange` fire on reload.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- <what remains unproven, and what would prove it>

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->
- **2026-11-09 — Meeting context is used wherever possible** (Harry). It's resolved when the recording is sent and so includes notes written during or after the meeting, and processing waits until then, which the upload-after-stop design does anyway. `contextAt` lets the prompts say what the notes are, rather than claiming they predate the meeting.
- **2026-11-09 — Phone uploads go through orient on `:3000`, knowingly reversing** the scribe-on-the-VM decision that handoff goes over `:3014` and not through orient. A phone talking to `:3014` would need the hub token in the browser and CORS on scribe. Cost: a `pnpm deploy:web` (about 70 s, once 10+ min) interrupts phone sends; they resume from the server's offset.
- **2026-11-09 — No new browser credential.** This matches every existing recording action and the `:3014` reasoning ("an ssh tunnel that already protects it"). The VM is single-user (checked), and the custom header plus the Origin check stop cross-site requests and DNS rebinding.
- **2026-11-09 — Defaults taken rather than asked:**
  - The device label is `phone`, since `capturedOn` already holds device names.
  - Audio is raw (echo cancellation, noise suppression and auto gain off; scribe normalises gain), checked against DER on one real meeting, as CLAUDE.md says to tune against `scribe/eval/`.
  - "Record on this device" shows on every browser, clearly labelled.
  - Per-chunk checksums are rejected: a whole-file sha at complete is enough.
  - Partial uploads are cleaned up by an explicit DELETE, not a new prune job, because destructive jobs that run on start have lost audio before.
  - Sent rows are kept; only the chunks are deleted.
- **2026-11-09 — Planning reviews:** the draft's 7 increments became 5. The spike gates the iPhone-dependent work; increment 4 is split; live upload, segments and the service worker are follow-ups.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
- **orient's root layout mounts `FocusEffects`, `CommandPalette`, `Chords`, `QuickView` and `TerminalPanel` on every page,** and some of them call `router.refresh`, `push` or `replace`. Combined with Next 16's offline fallback to a full page load (unless `experimental.useOffline`), any page that has to survive a dead connection must keep them out.
- **Server actions are open to any loopback page.** Only `/api/desk/act` and `/api/write` take a token, and `hostAllowed` "does not authenticate anyone". The `desk/act` comment claiming a browser can't start or stop a recording is wrong.
- **`scribe/eval/fetch-ami.sh`'s `room-array` fixture is the in-person shape** (mono plus a silent `anullsrc` channel). Anything that sends in-person audio to scribe should match it.
