---
title: orient Whiteboard — Migration State
programme: orient-whiteboard
status: active
owner: hjf
services:
- orient
created: '2026-11-12'
updated: '2026-11-13'
tags:
- bifrost
- migration-state
---
# orient Whiteboard — Migration State

<!-- The single source of truth for PROGRESS. The Overview carries the narrative, the verified facts and the board format; this doc is the live ledger. `wp programme status/next/tick` read and write the `## Unit status` tables below, so keep the table shape intact. -->

orient has no PRs or CI: a unit ships as commits on `master` in the main checkout (`CLAUDE.md:22`: no git worktrees on this machine), staged by explicit path, pushed, then deployed (`pnpm deploy:all`, a named sha). The `PR` column holds the commit range. Builders are one at a time across the Notes, Sync and Whiteboard programmes, because the full-suite gates run on the working tree and need it clean. Each unit: build, `review-panel`, one consolidated fix round, gates on a quiet host (`typecheck`, lint count, `ui:check`, `ui:build`, `pnpm test`), deploy by sha, live check with writes blocked, tick, decision log, push.

## Unit status
Legend: ⬜ not started · 🟨 in progress · ✅ merged · ⛔ blocked · ⏸ deferred · ❌ dropped · 🔄 rescoped

Sequencing: B0 → B1 → B2 → B3 in series is the minimum Harry asked for. B4 follows; B5 to B7 are deferred behind their own conditions. Freehand pen strokes are not in any unit yet.

### The minimum: a freeform board with premade symbols
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **B0** | ✅ | The `orient-board` block: model, lint, static render | | med | sonnet/high | 63d89b5..8053669 | A `BlockSpec` in `src/render/blocks/` (parse, `lint(raw: unknown)`, starters, renderer) with the v1 format in the Overview: nodes (existing kinds and glyphs, explicit `x`, `y`, optional `w`, `h`, `icon`, `unconfirmed`), edges (`from`, `to`, optional label), `groups` (boundary boxes), `notes` (sticky text). The renderer calls the SAME node and edge drawing as `orient-flow` (`src/render/html/diagrams.ts`) with the given positions and skips `flow-layout.ts`; edges are drawn as straight or elbow lines between the nearest sides. Size caps (at most 300 elements, coordinates and sizes bounded, strings capped), duplicate or dangling ids are lint findings not crashes, preset rules are warnings. A fixed serializer: one element per line, stable key order. The golden harness (`scripts/render-golden.sh`) must show every existing document identical; the renderer source hash changes. Tests: parse, lint with hostile input, round trip (parse then serialise is byte-identical for serializer output), render snapshot, the same node drawn by `orient-flow` and by a board is the same SVG. |
| **B1** | ✅ | Whiteboard page type, page view, create entry | B0 | low | sonnet/medium | 8053669..59e8a3c | Register `whiteboard` in `src/domain/page-types.ts` (`kind: whiteboard`, header chip, `creatable` entry, starter text with one board). The Notes page view draws the board full width with pan and zoom (wheel, drag, pinch; fit to screen; a reset button), no editor yet. Enables the disabled Whiteboard entry in the N13 `+` menu: it creates `Untitled` from the whiteboard template in that folder and opens it. History, diff and restore already work (N8). Needs Notes N13 (gate G3). |
| **B2** | ✅ | The canvas editor | B0, B1 | **high** | opus/high | d97d804..e850831 | **Harry, 2026-11-12: "the whiteboard should be drag-and-drop which generates the markdown code. happy for it to be snapping."** So drag and drop is the way a board is made, and the `orient-board` fence is its output, never something to type: **snapping is on by default** (a 20 px grid for position and size, with a toolbar toggle and a held modifier to bypass it; alignment guides to neighbouring nodes' edges and centres, and equal spacing, if cheap), the text stays one fence in the page and a hand edit still works. Edit in place on the board page. A pure command reducer (`src/lib/board/` or under `ui/`, no DOM): add, move, resize, delete, duplicate, connect, label, undo and redo, with a command log so undo is exact. A Svelte canvas turns pointer events into commands: pan and zoom, click and marquee select, drag to move, handles to resize, arrow keys to nudge, Delete, Esc, optional snap to a 20 px grid. Touch: pan, pinch, tap to select, drag to move; no hover-only controls. Save is the editor's note save with the base hash (conflict banner and reload as in the note editor), writing the fence through the B0 serializer and leaving the rest of the page untouched; a board it did not change is written back byte for byte. Unsaved-changes guard. Risk R1. |
| **B3** | ✅ | Palette, connectors, groups, notes | B2 | med | sonnet/high | 6a9e048..d959794 | A palette of the premade symbols: Person, System, External system (the `c4-context` kit), and Container, Component, Store, Topic, Step for deeper levels, each placed by click or drag, a new box carrying the guide's anatomy (name, `tech`, `sub`) at its default 225 by 120; a glyph picker for the Google resource type drawn top-left, **the full set of 21** (the 11 in `ICON_KEYS` plus Dataflow, Firestore, LoadBalancing, DNS, Logging, Monitoring, PersistentDisk, VPC, KMS and IAM, added to `diagram-presets.ts` so `orient-flow` gets them too, with the `orient-writers` `diagram-rules.mjs` mirror updated and `tests/unit/diagram-presets.test.ts` green); connectors dragged from a node's handle to another with an inline label; boundary groups; sticky notes; a Block-checks style panel for the lint and preset warnings. Keyboard and screen-reader paths for every action (the canvas is `role=application` with a list view of the elements). |

### After the minimum
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **B4** | 🔄 | Export | B0 | low | sonnet/medium | | **Rescoped 2026-11-13: "Copy to a page" is dropped** (Harry: link a board, don't "mash everything together"; B5 embeds by link). Left: SVG download of a board (and PNG if the Chromium-free route is cheap). |
| **B5** | ✅ | Embed a whiteboard by link | B1 | **high** | opus/high | 43d8561..033c00c | **Un-deferred and moved ahead of B2, 2026-11-13** (Harry: "if we have our whiteboards, we should also be able to embed one. ideally in edit mode we'd be able to link an existing one rather than mash everything together").<br>• **Syntax:** an Obsidian embed, `![[Notes/…/Board]]`, alone on its line. The page holds only the link and never the board's fence.<br>• **Reading:** the renderer turns an embed that resolves to a Notes page into a placeholder naming the resolved path. Resolution is already in the render-cache key, so this is cache-safe; it is N11's "placeholder blocks hydrated by the SPA". The SPA fills it with the board's current `svg[data-board]` from the page route, so a board edit shows everywhere at once.<br>• **Editing:** the live editor draws the same embed in place and reveals the `![[…]]` source on the caret line. Insert and `/` get "Whiteboard", a picker of existing boards that inserts the link.<br>• **Designed states:** loading, missing board, and a page that is not a whiteboard. |
| **B9** | ✅ | Make an inline diagram a whiteboard | B5 | med | sonnet/high | b12f868..130c298 | **Proposed 2026-11-13.** Pages written before B5 (the C4 notes) hold `orient-flow` diagrams inline, and the editor shows them as a wall of JSON. In the live editor, draw an inline `orient-flow`/`orient-board` fence (W2's block half) and offer **Make it a whiteboard**:<br>• a new board page beside the note, its nodes placed by the flow layout;<br>• the fence replaced by its `![[…]]` embed, as an unpublished edit that Publish writes. |
| **B6** | ⬜ | House-style conformance against the reference | B3 | low | sonnet/high | | Re-draw `~/.claude/skills/c4-diagrams/reference/component-diagram.png` (the Fuse SFTP connector) as a board and compare it with the PNG side by side in the browser: box anatomy and default sizes, group padding and label, cylinder datastores, open chevron arrowheads and right-angle bends, the edge label filled with the colour it sits on, the faint dot grid on the board canvas, dashed `Not confirmed`. Fix what differs in the shared drawing path, so `orient-flow` improves with it. **Put one decision to Harry with both renderings shown: topics as pills (orient today) or ordinary boxes (the guide).** The golden harness shows exactly which existing diagrams change. Check the 21 icons against `lucid_style.py`'s names. |
| **B7** | ⏸ | Lucid import | B3 | med | sonnet/high | | **Deferred behind G2.** Read a Lucid document through the connector Harry authorises and map its shapes onto the premade kinds. Read-only against Lucid. |
| **B8** | ⏸ | The `c4-diagrams` skill writes boards | B6 | low | sonnet/medium | | **Deferred.** The skill's two tables (elements, relationships) become an `orient-board` in the vault instead of, or as well as, a Lucid diagram: the text twin the guide asks for is then the diagram. The skill is Harry's (laptop, now also on the VM); change it only when he asks. A board that must show on Confluence uses the B4 export or the Lucid macro as before. |

## Gates
- [x] **G1 — The `c4-diagrams` design-language guide is readable on the VM** — blocks B6. Cleared 2026-11-12: Harry had his laptop agent upload the skill; it is at `~/.claude/skills/c4-diagrams/` (`SKILL.md`, `lucid_style.py`, `example_carrier_proxy.py`, `reference/component-diagram.png`).
- [ ] **G2 — Lucid authorised** — blocks B7. The Lucid connector needs Harry's OAuth; nothing is read from Lucid until he does it.
- [x] **G3 — orient Notes N13 merged** — blocks B1. N13 puts the `+` create menu in the tree, with Whiteboard listed and disabled. Cleared 2026-11-12: N13 is live at 63d89b5; B1 registers `PageType.creatable` for `whiteboard` to enable the entry.

## Risks
- **R1 ★ Pointer interaction is the hard part** — drag, resize, connect, marquee, undo and touch interact in ways unit tests on a DOM stub do not show. Mitigation: a pure reducer with exhaustive tests, the view thin, Chromium tests for every pointer path (mouse and touch emulation), opus for B2 — open.
- **R2 ★ One drawing path** — a second renderer would drift from `orient-flow`. Mitigation: B0 calls the existing node and edge drawing; a test proves identical SVG for the same node; the golden harness shows existing documents unchanged — open.
- **R3 Save format and merge noise** — Mitigation: one element per line, stable key order and ids, byte-identical write-back of an untouched board, base-hash conflicts as for notes, history diff already works on text — open.
- **R4 Size and cost** — a board with thousands of elements. Mitigation: caps in the lint and the parser (300 elements), coordinates and strings bounded, the page stays under the editor's 1 MiB text cap, viewport-only drawing if a view needs it — open.
- **R5 Untrusted text in SVG** — labels and notes are text nodes, never HTML or attributes; glyphs come from the fixed `ICON_KEYS`; no URL fields. Mitigation: tests with markup, bidi and control characters in every field — open.
> SUPERSEDED 2026-11-13: orient is desktop only (gate G7 of the Svelte UI programme), so B2 and B3 built for the mouse, the keyboard and the trackpad. The List view (B3) is the accessible path.
- **R6 Touch and mobile** — editing on a phone is possible but cramped. Mitigation: 36 px targets, pan and pinch first, a list view of the elements as the accessible and small-screen path — open.
- **R7 `layoutFlow` blows up on interleaved groups** — found by the B9 builder fuzzing the conversion.
  - **What happens:** in 112 of 200 random flows whose groups interleave, `src/render/md/flow-layout.ts` `layoutFlow` produces widths around 1e22. The reading view draws such a flow the same way. B9 refuses to convert it, with the reason, because the board would pass 10,000 units.
  - **Who is affected:** no vault flow does this today. `ups-proxy`, `connectors-dpd` and 8 other real flows lay out and convert cleanly.
  - **Status:** open, not fixed, as a renderer change of its own. The golden harness will show which documents move.

## Decision log
<!-- Dated, newest first. -->
- **2026-11-13** — **B9 done and live at 130c298** (b12f868..130c298: 10 commits, opus builder, plus one copy fix by the lead). **The JSON wall is gone.**
  - **In the live editor:** an inline `orient-flow` or `orient-board` (not on a whiteboard page) is drawn as its diagram, under a caption with its title, and shows its source when the caret is in it. One that does not parse, or has lint errors, stays text.
  - **Make it a whiteboard** is a quiet button on the caption. It opens a confirm, then makes **one** vault write: a whiteboard page beside the note, named from the flow title up to its first " (" (`ups-proxy`'s is "Component diagram: ups-proxy"), at the next free name if taken, never overwriting.
    - Only then is the fence swapped for `![[…]]`, as one undo step, an unpublished edit.
    - Byte-identical text links the existing board and says "Linked the existing …"; the core's create now answers `reused`.
    - No answer says "the board may have been made in … Check there".
  - **The conversion** (`ui/src/lib/board/from-flow.ts`) uses `layoutFlow` positions, rounded to the 20-unit grid and never under the board minimum. Every field is kept, and a group that shares a node's id is renamed. `ups-proxy` gives 20 boxes, 27 arrows and 1 group, with no lint findings at all.
    - Boards now draw `service` (the colour swatch and the name) and `ev` (evidence references) as the flow does (`board-layout.ts`).
    - The flow's own edge routes are not stored; boards draw straight or one-bend arrows, and the confirm says so.
  - **Review (create and swap; conversion and widget) found 10 issues, all fixed with tests failing first:**
    - stale offsets across the dynamic import could replace unrelated text, or orphan a board;
    - the "Made" notice outlived Publish;
    - "Nothing was made" was said when the page may exist;
    - a silent reuse of an identical board;
    - boxes under the board minimum, so a fresh board warned;
    - a valid flow with a shared group and node id was refused;
    - converted boards dropped the service colours and evidence;
    - a FIFO drawing cache and an unbounded heights map;
    - a raw caption title.
  - **Lead's fix:** the no-answer message said "orient-core did not answer (orient-core did not answer)", and now says it once (130c298).
  - **Gates:** typecheck 0, lint 44, `ui:check` 0, the touched files (about 3,400 tests). The golden is identical over 1,459 documents through the renderer change (no existing board uses `service` or `ev`).
  - **Live check** (`:3000`, the real `ups-proxy`, writes aborted):
    - the diagram is drawn (1 SVG, 0 JSON lines), with the caption and the action;
    - opening stays Published with 0 writes;
    - the confirm names the board and the folder, and says what is written when;
    - the create, aborted, says the board may have been made, and the page text is unchanged.
  - **Not converted:** nothing was converted. Harry chooses which diagrams to move.
  - **Next:** Notes NV2b (drag to reorganise the tree).
- **2026-11-13** — **B3 done and live at d959794** (6a9e048..d959794: 8 commits, opus builder). **The canvas is a C4 tool.**
  - **What was built:**
    - **Palette:** Context (Person, System, External system), Deeper (Container, Component, Store, Topic, Step) and Frame (Group, Note). Each is placed by a click at a free spot in view, or dropped where it is dragged, snapped; this replaces B2's Add box.
      - It maps onto the existing kinds, with no new node kinds: Person→person, System and Container→service, External→external, Component and Step→step, Store→store, Topic→topic with the pubsub glyph. `tech` tells the pairs apart.
      - Topics are still drawn as pills, which is B6's call.
    - **Glyph picker** (Glyph or `i`) with 21 glyphs. The ten new generic marks (dataflow, firestore, loadbalancing, dns, logging, monitoring, persistentdisk, vpc, kms, iam) are in `diagram-presets.ts`, so `orient-flow` draws them too.
    - **Connecting:** connectors drag from a box's side handles, with the target marked and the label opening for typing. Keyboard connect is `c`.
    - **Groups and notes:** Group (or `g`) wraps the selection and opens its name; Note opens a note for typing.
    - **Labels:** name, type and description are edited in place on the box.
    - **Panels:** the Board checks panel (lint and preset warnings; a click selects); the List view (every box, group, note and arrow, with Edit, Join and Delete and a checkbox for choosing by key).
    - **Keys:** Alt-arrow resizes; a run of arrow nudges is one undo step; Ctrl-C and Ctrl-V paste.
  - **Mirror:** `orient-writers` `diagram-rules.mjs` lives only on its `origin/main`. Local `main` has diverged (2 ahead, 2 behind) and has another session's uncommitted edits, so the builder committed the mirror update as 927a359 on a **local, unpushed** branch, `hjf/diagram-rules-icons`, off `origin/main`. It is left for Harry.
  - **Review (model and renderer; canvas interaction) found 7 issues, all fixed with tests failing first:**
    - a new group could land under a bigger group on a hand-ordered board;
    - pasted or duplicated groups covered smaller ones;
    - the board lint went quadratic (3,086 ms against 576 ms on a 100k board; `note-block-checks` runs it in the core's event loop on every preview);
    - connect-by-key stayed armed after other actions and hijacked the next Enter;
    - an Esc'd palette drag could still place a box on a late release;
    - the List and Checks panels lost focus to the canvas;
    - the glyph menu's Esc went to the toolbar.
  - **Gates:** typecheck 0, lint 44, `ui:check` 0, 1,521 board, lint and diagram tests (74 mirror tests skip locally). The golden is identical over 1,459 documents, and `rendererSourceHash` moved (the cache misses once).
  - **Live check** (`:3000`, real `test whiteboard`, writes aborted):
    - all 10 palette entries are there;
    - a Container lands at (320, −100), overlapping nothing;
    - a connector dragged from a handle (8 shown) to Customer makes `n1→customer:calls`;
    - `g` wraps Orders and Payments as "Payments platform";
    - typing `g` in a label does not group;
    - Ctrl-C then Ctrl-V adds a copy;
    - the checks panel shows a real warning;
    - the List shows 5 boxes, 1 group, 0 notes and 3 arrows;
    - Publish was tried, aborted, and the draft kept.
  - **Polish noted:** the glyph menu has no type-to-filter, and opens on "None" rather than the box's current glyph.
  - **Next:** B9 (turn the C4 notes' inline `orient-flow` JSON into boards plus embeds), then Notes NV2b (drag to reorganise the tree). B4 export and B6 (Harry's topic-shape call) when there is room.
- **2026-11-13** — **B2 done and live at e850831** (d97d804..e850831: 7 commits, opus builder). **The board is drag and drop now.**
  - **What was built:**
    - Edit on a whiteboard page opens a canvas (`ui/src/lib/board/`: `model.ts`, `snap.ts`, `fence.ts`, `hit.ts`, `draw.ts`, `BoardCanvas.svelte`, `BoardEditor.svelte`).
    - **Editing:** add, drag, resize, connect (Shift-click two boxes, then Connect), relabel (double-click), delete, duplicate, Esc, and undo and redo with the board before and after each command. Tab moves through boxes, and a live region announces each change.
    - **Snapping:** a 20-unit grid, on by default and remembered per browser, with Alt to bypass it, and alignment guides.
    - **Drawing:** the static render's own drawing functions (only the `noteBox` export changed). The golden is identical over 1,441 documents.
    - **Publishing:** a browser draft until Publish, which rewrites only the fence. A board that won't parse, has lint errors or has an unclosed fence opens as text, with the reason. "Edit as text" (`?as=text`) takes the draft with it.
    - **Speed:** a drag on a 300-element board takes 2.8 ms median per frame.
    - **Sensitive boards** open as text, because the core withholds their `pageType`.
  - **Review (write-back, model, canvas) found 10 issues, all fixed with 23 tests failing first.** The board editor's copy of the draft and Publish logic is patched to match `Editor.svelte`'s guards; extracting it to share is left for later. The serious ones:
    - switching editors after a Publish opened stale text, and Reload theirs then lost work;
    - Reload theirs with an unparseable board kept yours against their hash (an inv-7 breach);
    - a late Publish reply on a closed editor;
    - Esc or Ctrl-Z mid-drag committed the drag on top of an undone state;
    - per-box snapping broke group and selection offsets (two reviewers found it);
    - duplicating a group copied only its frame.
  - **Gates:** typecheck, lint 44 (the builder found and fixed a 45th error from its own 777c1e7), `ui:check` 0, the build, 592 board tests and 264 note-editor route tests. The full suite was not run.
  - **Live check** (`:3000`, real `test whiteboard`, writes aborted):
    - Edit opens the canvas;
    - Add box places `n1` at (320, 0);
    - a 73×41 px drag lands on (400, 40), on the grid, and Alt gives (407, 43);
    - double-click relabels;
    - Connect adds `n1→customer`;
    - undo and redo take the edges 3 → 2 → 3;
    - Publish was tried, aborted, and the draft kept;
    - Close shows the banner, and the reading view keeps the vault's board;
    - Edit as text carries the draft.
  - **Still not like Confluence, for B3:**
    - Add box can land on top of another box;
    - there is no connector dragged from a handle, and no keyboard connect;
    - only plain boxes, with no palette;
    - the label edits above the box, not in place;
    - repeated nudges are separate undo steps;
    - there is no copy and paste.
  - **Next:** B3.
- **2026-11-13** — **B5 done and live at 033c00c** (43d8561..033c00c: 9 commits, opus builder; a login error stopped it once mid-build, and it was resumed with its work intact).
  - **What was built:**
    - **Reading:** an embed of a Notes page, alone on its line or on lines ended by a hard break, renders as a `data-page-embed` placeholder with a fallback link. Every other embed, images included, is byte-identical. `RENDERER_VERSION` is `html-7`.
    - **Hydration:** the SPA fills the placeholder with the board's current SVG, cloned from the page route and scrubbed. There are designed states for loading, a missing page, another kind of page, and a failure with Retry.
    - **Editing:** the live editor draws the same embed, and shows the `![[…]]` source on the caret line.
    - **Picker:** Insert and `/whiteboard` open a picker that writes `![[path]]` in one undo step.
    - **Supporting changes:** the tree's page and folder nodes carry `pageType`, so a folder's own board is listed and drawn.
  - **Golden:** all 1,441 vault documents render identically to before B5.
  - **Review (backend, frontend and security lenses) found 9 issues, all fixed with tests failing first:**
    - a failed background reload replaced a drawn board;
    - every embed fetched and listened on its own (now one load and one subscription per path, at most 50 drawn per page, and a bounded memory);
    - the cloned SVG was not scrubbed (now script, foreignObject, iframe, object, embed, animate and set are dropped, along with `on*` and unsafe hrefs; today's renderer cannot emit any of them anyway);
    - widget teardown leaked when CodeMirror reused the DOM;
    - a board collapsed to source mid-drag;
    - the picker could apply a stale range after Tab-away;
    - board paths with `#|[]` broke the link (now listed but disabled);
    - an ambiguous `![[Name]]` drew an arbitrary candidate (now it stays a link, and the editor says "N pages are called …");
    - the editor and the reader disagreed on hard breaks.
  - **Security found no live exploit:** traversal and sensitive paths are refused by `isPagePath`, and attributes are escaped by `el()`.
  - **Gates:** typecheck, lint 44, `ui:check` 0, and the touched files (234 browser tests). The full suite was not run (Harry, after two reaps for low memory).
  - **Live check** (`:3000`, writes aborted; the reading view was served the core's own preview rendering of a page embedding the real `test whiteboard`):
    - the placeholder sits outside any `<p>` and carries none of the board's content;
    - reading and editing draw the board the same way;
    - Open goes to the board, and a 404 shows "No page at";
    - opening the editor stays Published;
    - the caret reveals the source;
    - the picker lists the board and inserts the link, and one undo removes it.
  - **Polish left:** the picker opens under the sticky bar, not at the caret.
  - **Next:** Notes NV2 (Harry's sidebar ask), then **B2**, then B3, then B9.
    > Reordered the same day after Harry asked where the drag-and-drop board was ("All I see is the JSON one"). B2 goes straight after NV2. B9 (turning inline JSON diagrams into boards) follows B2 and B3, because a converted board is only worth having once it can be dragged.
- **2026-11-13** — **Embeds come first: B5 is un-deferred and goes ahead of B2; B4 loses "Copy to a page"; B9 is proposed.**
  - **Harry, after the editor ux-review:** "Let's focus on the gap with diagrams. if we have our whiteboards, we should also be able to embed one. ideally in edit mode we'd be able to link an existing one rather than mash everything together".
  - **Why B5 can go now:** it was deferred for one reason, the render-cache key. N11's plan (placeholder blocks hydrated by the SPA) settles that.
    - `src/render/md/plugins/wikilink.ts` already parses `![[…]]` with an `embed` flag. The renderer ignores the flag today and draws a link (`src/render/html/blocks.ts` `wikilink`).
    - Link resolution is already part of the cache key, so a placeholder that depends only on the resolved path is cache-safe.
    - The board's drawing is fetched at view time, and a whiteboard page already carries one `svg[data-board]` from the core (B1), so there is no second drawing path.
  - **Syntax:** an Obsidian embed, not a new fence. It is native to the vault (three embeds exist today, all images), Obsidian shows it as a transclusion, and it is a link, so backlinks see it.
  - **Order now:** B5 → B9 (the inline JSON diagrams on existing C4 pages) → B2 → B3 → the rest as agreed.
  - **B4:** "Copy to a page" is the mash-together route Harry ruled out, so it is dropped; export stays.
  - **Also on 2026-11-13:** the editor ux-review fixes went live at 6c134aa (Notes decision log).
- **2026-11-12** — **B2 and B3 move up (Harry: "yes - makes sense. happy for you to just run with this autonomously").** The open question below is answered: one builder at a time, Notes W3 (in flight) → W4 → the editor `/ux-review` → **B2 → B3** → Notes NV1 → NV2 → Confluence C0 to C3 → the rest (see the Notes decision log). B4 and B6 follow B3 when there is room; B6 still stops for Harry's topic-shape call.
- **2026-11-12** — **Harry on the whiteboard: "the whiteboard should be drag-and-drop which generates the markdown code. happy for it to be snapping."** He had looked at B1's view, which only pans and zooms (a board is still made by editing its fence in the markdown editor until B2), so that is expected, and it is exactly B2 and B3. B2's snap changed from "optional" to **on by default** (with a toggle and a bypass), and the row carries his words. Open: whether to move B2 and B3 ahead of NV1, NV2 and the Confluence C0 to C3 (they currently follow C3); recommended, because the board's edit mode reuses the W3 and W4 edit-mode shell and Harry has now asked for it, but it is his call.
- **2026-11-12** — **B1 done and live at 59e8a3c** (8053669..59e8a3c, 3 commits). **A whiteboard is a page type with a view.** `src/domain/page-types/whiteboard.ts` (`notesKind: 'whiteboard'`, chip "page type: whiteboard") with a `creatable` entry `{id: 'whiteboard', flow: 'page', template: 'whiteboard'}` that takes over N13's disabled built-in; the template `src/edit/templates/notes/whiteboard.md` (frontmatter `title`, `date`, `kind: whiteboard`, a `# {{title}}` heading and the B0 starter board) is readable by slug and never listed, so it is not in the Page group and a vault `whiteboard.md` cannot shadow it. `NoteViewDto.pageType` (null for a sensitive page) tells the SPA. The board SVG carries `data-board`; `ui/src/lib/notes/board-view.ts` and `BoardView.svelte` enhance the first `svg[data-board]` on a whiteboard page by rewriting only its `viewBox` (nothing is parsed or redrawn: one drawing path): wheel zooms at the pointer, drag pans, pinch, keys (arrows, `+`, `-`, `0`), a toolbar (Zoom out, Zoom in, Fit, Reset, a percentage; 36 px under a coarse pointer and at `max-sm`); the `max-height` cap is lifted for the view (`max(20rem, 100dvh - 26rem)`) and kept on every other page. History, diff and restore work on a whiteboard page (a real-git test: a moved box is a one-line diff). **Evidence:** golden on 59e8a3c shows only the known Sportlux entry (the two board fixtures changed because their SVG now has `data-board`; every flow and sequence fixture is identical); gates on a quiet host (typecheck, lint 44, `ui:check` 0, `ui:build`, 11,537 tests; the suite now takes 150 s); deployed; live check on the real core with every write aborted: the registry lists Whiteboard enabled with its own template and `/templates` does not list it, an existing page reports `pageType: note`, the `+` menu shows Whiteboard enabled and Upload disabled "later", the Whiteboard popover opens on its title field with no template select, and, with the page response rewritten in the browser (there is no whiteboard page in the real vault and none was created) so the deployed SPA drew a board rendered by the deployed renderer: the toolbar and the lifted height cap appear, wheel zoom and drag change the `viewBox`, `0` restores it exactly, a normal page has no board toolbar, and at 390 px there is no horizontal overflow and the four controls are 36 px. **Process:** light lane, no review panel; the builder took about 25 minutes; the unit from brief to deploy took about 1 hour 15 minutes. **Known, left:** creating a whiteboard lands in the markdown editor, like every create (B2 flips it to the canvas); wheel and touch-drag over the board are captured, so the page scrolls only from outside it; the board-view enhancement is not applied to a sensitive whiteboard (its page type is withheld); `deploy-lib.sh` printed `line 42: /proc/<pid>/cmdline: No such file or directory` during `gate_no_runs` (a process exited between listing and reading; harmless; for Sync S6). **For B2:** `BoardView` owns the `viewBox`; the canvas editor can take over the same SVG or replace it in edit mode; creating a whiteboard should open edit mode then.
- **2026-11-12** — **Order changed: B2 and B3 wait for the writer.** Harry moved the editing experience to the front (see the Notes decision log, Revision 4). One builder at a time: B1 (in flight) → Notes W1 → W3 → W4 → NV1 → NV2 → B2 → B3 → Notes W2 → NV3 → Sync S1 to S5. B2's canvas editor shares the idea of edit-in-place and the Publish flow with W4, so building W1 and W4 first gives B2 a pattern to follow.
- **2026-11-12** — **B0 done and live at 8053669** (63d89b5..8053669, 3 commits: the drawing exports with no output change, the block, the review fixes). **The `orient-board` block** is registered and offered as "Block: whiteboard" in the editor's Block and slash menus; boards lint (`board-lint.ts`), draw with the shared `orient-flow` node, group and edge drawing (`board-diagram.ts`, `board-layout.ts`), and serialise one element per line (`serializeBoard`, browser-safe in `board.ts`). **Review fixes:** unknown fields are kept only if at most 8 levels deep, with no string over 2,000 characters and under 4 KB per object (anything else is an error finding and is dropped, never thrown on); a drawn extent over 4,000 units is a warning and every board SVG has `max-height: min(80vh, 900px)`; an edge with no visible length is a warning; node, note and group minimum sizes are clamped up (80 by 44, 60 by 30, 60 by 40); above 300 elements groups and notes keep a tenth of the cap each, nodes two thirds of the rest and edges the remainder, and the lint and notice say "past the cap". **Evidence:** golden on 8053669, mine and the builder's, shows only the known Sportlux entry (28 fixture documents and the 1,398-document corpus unchanged; `rendererSourceHash` changed, which changes the render-cache key on deploy); gates on a quiet host (typecheck, lint 44, `ui:check` 0, `ui:build`, 11,398 tests); deployed; live check on the real core through the preview route (stores nothing) and the editor, every write aborted: the block list has 10 entries, the starter renders 3 nodes with no findings, a malformed board is findings and not a 500, hostile label text stays inert text with no `<script` in the output, a 20,000-unit board gets the extent warning and the height limit, a 6,000-deep unknown field is reported and dropped while the page still renders, and inserting the block from the Block menu puts the fence in the text and the board in the preview. **Not live-tested:** the zero-length edge warning (my input left the boxes 44 apart; the unit tests cover it). **Process:** the builder took about 25 minutes (a shorter brief, mutation checks only on four invariants), one reviewer, one short fix round; the whole unit from brief to deploy took about 2 hours including the review and verification waits. **For B1:** register `whiteboard` in `src/domain/page-types.ts` (`notesKind: 'whiteboard'`, a `creatable` entry whose template holds the starter board) and draw the board full width with pan and zoom; the Notes page view already renders the block through the pipeline, so B1 can start from that. **For B2:** `parseOrientBoard`, `serializeBoard`, `BOARD_LIMITS` and `placeBoard` (hit-testing) are the model; a hostile unknown field can no longer make the serializer throw.
- **2026-11-12** — **B0 built (18f6656), in its fix round.** The `orient-board` block is registered with the node, edge and group drawing shared with `orient-flow` (`src/render/md/board{,-lint,-layout}.ts`, `src/render/html/board-diagram.ts`; the drawing functions in `diagrams.ts` and `flow-layout.ts` are exported, with no change to `orient-flow` output). Format v1 limits chosen by the builder: x and y within ±10,000, w and h 20 to 2,000 (the review raises the minimums), at most 300 elements, id 64 characters, label 200, tech 100, sub 500, note 2,000. Unknown fields are kept through parse and serialise (`.loose()`). The golden run on the final commit shows only the known Sportlux entry (builder's run and mine); `rendererSourceHash` changed, which also changes the render-cache key on deploy, so no `RENDERER_VERSION` bump is needed. One reviewer (renderer and security, heavy lane with the builder having mutation-checked the four invariants) found no SVG injection, no throw in lint or parse and no prototype pollution, and five smaller issues, being fixed: unbounded unknown fields (a 6,000-deep one made `serializeBoard` throw and 3,000 deep serialised to 18 MB, which B2's save would hit), no cap or scale on the drawn extent (a tall board drew 20,079 px high), zero-length edges, boxes smaller than their text, and a misleading notice when the 300-element cap drops edges. The builder took about 25 minutes against 38 to 47 for earlier builders, with a shorter brief and the mutation-check requirement narrowed to the invariants. **Choices to know:** the parser accepts duplicate ids, dangling edges and more than 300 elements and the lint reports them, so a hand-edited board never fails to open; control and bidi characters are dropped at render only, the data keeps them; `service`, `group` and `ev` survive as unknown fields; the block's label is "Whiteboard"; `scripts/validate-blocks.mjs` lists only the row blocks and is left alone. **For B1/B2:** import `board.ts` (browser-safe: schemas, `parseOrientBoard`, `serializeBoard`, `BOARD_LIMITS`) and `placeBoard` from `board-layout.ts` for hit-testing.
- **2026-11-12** — **G1 cleared; the `c4-diagrams` guide read.** Harry: "I've had my local agent upload the skill". It is at `~/.claude/skills/c4-diagrams/`. What it changes: (1) the symbols are not new work, orient's `label`, `tech` and `sub` are the guide's name, type and description, and the guide's rules (anatomy, groups, cylinders, labelled one-way edges, dashed `Not confirmed`, 20 boxes, 2,600 px) are the board's acceptance rules; (2) **ten GCP icons are missing in orient** (Dataflow, Firestore, LoadBalancing, DNS, Logging, Monitoring, PersistentDisk, VPC, KMS, IAM) and go into B3's palette work; (3) B6 is no longer deferred but becomes a conformance pass that re-draws the reference diagram as a board and settles the topic shape (pill versus box) with Harry; (4) B8 added, deferred: the skill writing boards. The Lucid half stays gated (G2): the connector needs Harry's authorisation and the nine Confluence pages that mention Lucid were not opened. The guide's colour hexes are Lucid's dark theme; orient draws with theme tokens, so the reference image is the acceptance test and the hexes are not copied.
- **2026-11-12** — **Order agreed (Harry: "yes").** One builder at a time across the three programmes: Sync S0 (fix round, then deploy) → Notes N13 (create from the tree; also takes the 25 px tab links and the 14 px `All versions` link at 390 px) → this programme's minimum B0 to B3 → Sync S1 to S5. G3 (N13 merged) therefore clears before B1.
- **2026-11-12** — **Programme opened.** Harry asked for a freeform whiteboard page type under Notes with the standard C4 components, the Google resource type at the top left, orient blocks, and Lucid material from the Merak Confluence; then "are we able to plan whiteboards … freeform with premade symbols for context diagrams is the minimum". Taken without asking again (the three open questions had defaults): **(1) badge** = the existing node `icon` glyph, already drawn top-left of every card; **(2) storage** = a markdown page with `kind: whiteboard` and one `orient-board` fence, one element per line (not an Obsidian `.canvas`); **(3) source of the symbols** = the six kinds and eleven glyphs already in `diagram-presets.ts`, with the `c4-diagrams` guide (laptop only) and Lucid left as gates G1 and G2 that block only B6 and B7, not the minimum. Checked first: the node drawing takes explicit positions, so a board reuses it; the glyph comment says they are generic marks, not Lucid's product art; a Confluence search for "Lucid" returned nine pages across four spaces, none opened. The minimum is B0 to B3. The whiteboard needs Notes N13 first (G3).

## Scar tissue
- **One drawing path for diagrams** — `orient-flow` and `orient-board` share the node and edge drawing in `src/render/html/diagrams.ts`; a second renderer would drift.
- **A board is plain markdown** — no second storage format; Obsidian must be able to open the file, and history, diff and restore must keep working on it as text.
- **Labels are text, never HTML.**
- **The golden harness gates every renderer change** (`scripts/render-golden.sh`): existing documents must render identically.
- **No git worktrees** (`CLAUDE.md:22`); one builder at a time across programmes.
