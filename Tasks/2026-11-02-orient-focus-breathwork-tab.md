---
tags: [adhoc-task]
date: 2026-11-02
tldr: "orient: Focus breathe tab, trim-start/end for recordings, then a custom mono audio player and an Ask-Claude section on a recording; all deployed."
session_id: 7377f74d-d886-4354-8e27-fa180441d42e
status: open
---
# orient: Focus breathe tab, recording trim, player and Ask

## Outcome
**Focus breathe tab** (5422210): `/focus?tab=breathe`, a client-only pacer (box, 4-7-8, coherent, sigh; 1/3/5 min in whole breaths; optional tones). Not logged. `PageTabs` counts are optional.
**Recording trim** (d62629e): `POST /api/recordings/{id}/trim` in orient-scribe cuts `audio.ogg` (stream copy for an end-only cut, re-encode when the start moves), moves transcript and enhanced lines onto the new timeline without re-transcribing, drops the old-timeline `channels`/`echo`, and re-runs the summary. The transcript player gets `cut before` / `cut after` at the playhead, with a confirm. Verified on copies of a real recording (since deleted); scribe service reinstalled.
**Player and Ask** (3d96bd6): the browser audio control is replaced by `AudioBar` (play, hairline scrubber, times, ±10, speed) with the trim row under it; fixed a hydration race that left the length at 0 and hid the trim bar. An `Ask` section on a finished recording runs a tool-less Claude over notes + transcript (`askRecording`, nothing saved); cited `[mm:ss]` times play the audio. Reviewed with /ux-review on desktop and 390px (tap targets, menu-button overlap, chip layout fixed); design doc updated and re-anchored.
**Transcript export + Ask on top** (0f9f52e): `copy` and `export` (.txt named title-day-enhanced|raw) in the Transcript header, for whichever tab is showing; Ask moved above Summary.
Owed, if wanted: seek-to-line highlight from a cited time; log breathwork sessions to the vault and a break-phase "breathe" action; a separate re-transcribe action (clustering/speaker-count options) was discussed and not built.
