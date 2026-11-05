---
tags: [adhoc-task]
date: 2026-11-05
tldr: "Recovered the 5 Nov 13:29 recording (Go modcache clean broke sherpa-onnx); scribe now bundles its libs, warns when music plays into a recording, and can ignore apps live"
session_id: ab13787f-5144-413b-9c70-a0a24e1c1cd5
status: done
---
# Recover a failed scribe recording, and keep music out of recordings

## Outcome
- 20261105-132921-2bf2 failed with exit 127: `libsherpa-onnx-c-api.so` was missing because the Go module cache had been cleaned. Restored the module, requeued the recording, and it is now done (transcript, summary, enhanced).
- orient `31b46cc`: `make build` copies the sherpa-onnx libraries to `bin/lib`, with `$ORIGIN/lib` as a fallback RUNPATH.
- orient `ad04890`: an MPRIS warning (Pause it / Keep) when a player plays during a recording; `POST /ignore` plus ignore/include toggles on the live panel. Both checked live. The music on 5 Nov flagged that recording as a call; not investigated.
