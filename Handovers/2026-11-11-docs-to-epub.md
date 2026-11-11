---
tags: [handover]
status: resumed
workstream: Build the reusable `docs-to-epub` skill (technical documentation to an illustrated EPUB with a custom cover). Tooling is built and tested; SKILL.md and the references are not written yet
programme: none
repo: hjfitz/orient-writers (local clone ~/projects/orient-writers, path skills/docs-to-epub, untracked)
from: laptop (freightops)
to: rc-hjf (the workstation, harry@hjf.shell.platform.ilg.software). Harry chose this on 2026-11-11. The tooling is installed there and the skill folder has been copied across from the laptop
session_id: 4ff6c302-4da3-4b14-bf3c-fc976c0ec75b
resumed_by: 9e1daa5f-c28e-44cb-b0dd-e5b4bfb5878c
updated: 2026-11-11T12:51Z
---
# Handover: the docs-to-epub skill

Harry asked for a reusable skill that turns a set of technical documentation (Confluence, orient, a repo, exported files, anything the agent can read) into a well-structured, illustrated EPUB with a custom cover. The session ended while the example book was being tested. The interrupted step was a rebuild after three small fixes.

## Requirements (Harry's brief, condensed so nothing is lost)
The skill must do all of this. Anything missing from `SKILL.md` when you finish is a defect.
1. **Read the sources and propose the book.** Inventory the material, infer the likely reader, prerequisites and learning goals. Propose a working title and chapter sequence. Per chapter: purpose, the source material it draws on, one promising example or reader question, proposed diagrams, gaps. Explain why the chapters are in that order. Decide what is main narrative and what is a reference appendix.
2. **Use `/grill-me` where the answers would change the book** (audience, scope, learning goals, competing interpretations). If it is not available, ask the same focused questions directly. Read what is available first. **Show the plan early** so Harry can steer it and flag sections he wants to rewrite or expand himself.
3. **Resolve substantive gaps before drafting the affected sections.** Look in the supplied sources, linked pages, related repos, decision records and other accessible material in scope. When sources disagree, check which version or context each describes. If still missing, state the exact question, where you looked, and what source or person could resolve it. Continue with chapters that have enough evidence. Keep technical claims traceable. Label hypothetical teaching examples.
4. **Write it as a book.** Reorganise and rewrite so understanding builds. Use a worked example across chapters. Introduce terms when needed. Tables for comparisons, walkthroughs for procedures, diagrams for relationships and behaviour.
5. **Voice.** Engaging and direct. From Julia Evans: start from a concrete question or surprising behaviour and build a predictive mental model. From Kleppmann and Riccomini: explain design choices through constraints, trade-offs and failure modes. From David Agans: troubleshooting as an investigation (observed, checked, narrowed). From Kernighan and Pike: compact code examples, each with one job, with the expected result shown.
6. **Plan diagrams alongside the chapters.** For each: the question it answers and what it must show. Pick the format that fits (sequence for interaction, state for lifecycle, component for boundaries). Check labels, arrows and behaviour against the sources. Captions and text alternatives. Legible on a small e-reader.
7. **Produce and check the EPUB.** Reflowable, custom cover, linked table of contents, consistent chapter and figure formatting, readable code blocks, source notes. Validate it. Preview representative pages at e-reader size. Check the cover, navigation, diagrams and long code blocks in the rendered book.

## Where things stand
The tooling exists and works end to end on a fictional example. The prose half is now written too: `SKILL.md` and seven reference documents, and the skill is linked into `~/.claude/skills` on rc-hjf. Nothing is committed. The tooling and the documents are tested. The workflow in `SKILL.md` has not been run by an agent on a real document set yet.

All paths below are under `~/projects/orient-writers/skills/docs-to-epub/`.

| Unit | What it delivered | State |
| --- | --- | --- |
| `scripts/book.py` | CLI: `init`, `figures`, `cover`, `check`, `build`, `validate`, `preview`, `all`. Pure Python (markdown-it-py, lxml, PyYAML, Pillow). Own Markdown dialect: `[^source-id:locator]` citations, `::: kind` callouts (hypothetical, gap, note, warning, tip, example, investigation), `{{figure:id}}`. Builds EPUB 3 with a nav document, NCX, accessibility metadata, per-chapter source notes, a Sources page, an Open questions page (from `gaps.yaml`) and a List of figures | Works. 20-odd checks (placeholders, uncited chapters, long code lines, wide tables, missing alt text, unreferenced figures, open gaps not shown) |
| `scripts/figures.py` | Diagram specs in YAML to SVG and PNG. `sequence` is drawn by its own renderer. `state` and `graph` (aliases `component`, `flow`) go through Graphviz `dot`, trying left-to-right and top-to-bottom and keeping the more legible. Reports text size at 600 px wide and flags anything under 11 px | Works. Fixed three defects found by looking at the images |
| `scripts/cover.py` | Generated 1600 x 2560 JPEG cover from the title (motifs `network`, `arcs`, `grid`; palettes `ink`, `paper`, `signal`), or a supplied image | Works. Looked good at thumbnail size |
| `scripts/preview.py` | Unzips the EPUB, renders every page in headless Chrome at 600 x 800 (`eink`) or 390 x 844 (`phone`), measures sideways overflow and figure text size, writes representative page images and a contact sheet | Works. The three fixes were re-run and checked on rc-hjf (see Closed since handover) |
| `assets/book.css` | E-ink-first stylesheet: relative units, wrapping code blocks, callouts that rely on text labels and border styles, not colour | Done |
| `examples/lantern-queue/` | A fictional worked example ("Reading a Retry Queue", about an invented job queue called Lantern): 6 chapters, 3 figures (sequence, state, component), `sources.yaml`, `gaps.yaml` with one open question, a `PLAN.md` showing the plan format, and `source-material/` it cites | Built. Rebuilt and re-validated on rc-hjf after the fixes (see Closed since handover): **EPUBCheck 5.4.0 VALID, no messages**, 13 preview pages, 0 mechanical problems |
| `SKILL.md` and `references/` | The workflow, plan template, voice guide, chapter template, diagram guide, gaps-and-sources guide, format reference and QA checklist | Written on rc-hjf at about 13:00Z. `plainly`'s linter passes all eight files. The format claims were checked against `book.py` and `figures.py`, and a second book exercised the features the example does not use |
| `~/.claude/skills/docs-to-epub` symlink | Makes the skill invocable | Created on rc-hjf at 13:03Z, the same way as `plainly`. A running session's skill list is fixed at start-up, so it shows in new sessions only. Not created on the laptop |

The example is fictional on purpose: nothing from the unannounced Merak research may go into a reusable skill that could be pushed.

## In flight
Nothing is running. No agents or workflows were started for this workstream.

| Work | Where | State | To close it |
| --- | --- | --- | --- |
| Uncommitted edits to the skill: `scripts/figures.py`, `scripts/book.py`, `assets/book.css` | `~/projects/orient-writers/skills/docs-to-epub/` on rc-hjf, untracked | Made at about 12:48Z and tested (see Closed since handover). The laptop's copy does not have them | Commit only when Harry asks, with explicit paths (see Next up 6) |

## Next up
1. ~~Re-run the example and read the page images at full size.~~ Done on rc-hjf, see Closed since handover.
2. **Write `SKILL.md`.** Frontmatter `name: docs-to-epub`, with a `description` that triggers on turning technical documentation (Confluence, orient, a repo, files) into an EPUB or book. Follow the conventions of the `plainly` and `c4-diagrams` skills. The workflow, in order:
   - Intake. Ask for the reader and goal only if they cannot be inferred. Read first.
   - Inventory the sources into `sources.yaml` with versions and dates. Note disagreements.
   - Infer the reader, prerequisites and outcomes.
   - Write `PLAN.md` from `references/plan-template.md` and **show it before drafting**. Mark chapters the reader wants to write themselves (`owner: author` in the chapter front matter; the checker treats these as outline-only).
   - Run `/grill-me` (it batches one-click questions and then hands off) only on questions that would change the book. Fall back to `AskUserQuestion` directly if it is unavailable.
   - Resolve gaps (the ladder in requirement 3), record the rest in `gaps.yaml`, show each with `::: gap G1`.
   - Draft chapters to the voice guide. Plan each figure alongside its chapter in `figures/*.yaml` (question, sources, alt, caption, description).
   - `book.py all`, then read the preview images, then fix and repeat.
   - Deliver the EPUB, the project folder, the validation result and the open-questions list. Ask before distributing: an EPUB carries its sources' content. If the user says the material is confidential, set `confidential:` in `book.yaml`.
3. **Write `references/`.** `plan-template.md` (needed: `book.py init` copies it into `PLAN.md`; the example `PLAN.md` is a good start), `voice.md` (the four writers' techniques with short before and after examples, house-style note: British English and no em dashes if the user's setup says so, `plainly` lint available), `chapter-template.md` (opening question, mental model, build-up, walkthrough, failure modes, check yourself), `diagrams.md` (type choice, a per-figure spec, legibility rules, evidence table of arrows to sources, grayscale-safe), `gaps-and-sources.md` (the ladder, version and context check, the exact-question format), `book-format.md` (every field of `book.yaml`, `sources.yaml`, `gaps.yaml`, chapter front matter, the directives and figure specs), `qa-checklist.md` (what to look at in the previews).
4. **Create the symlink:** `ln -s ~/projects/orient-writers/skills/docs-to-epub ~/.claude/skills/docs-to-epub`.
5. **Smoke test a fresh project:** `book.py init /tmp/x`, then `check`. Fix whatever the scaffold gets wrong.
6. **Commit only when Harry asks.** The repo's `.gitignore` is an allow-list (nothing is tracked unless named), so check it, and do not commit `examples/lantern-queue/build/`, `__pycache__/` or `*.epubcheck.json`. Add explicit paths. End the commit message with the attribution line from the harness. Then push only on his yes.
7. **Make the figures robust to a missing DejaVu Sans.** Give `FONT_DOT` in `scripts/figures.py` a fallback list (for example `DejaVu Sans, Liberation Sans, Arial, sans-serif`) so Graphviz and Chromium agree, or have `book.py figures` warn when `fc-match "DejaVu Sans"` does not return DejaVu. Neither is written or tested.
8. **Check how a real e-reader treats the figure text description.** It is `<details class="figure-text">` with no `open` attribute, so Chromium shows it collapsed. Reading systems differ on `<details>`. Test one before `SKILL.md` claims the text alternatives are accessible, and say in `references/diagrams.md` what was found.

## Waiting on Harry
- **Done: carry on on rc-hjf** (Harry's decision, 2026-11-11). Harry ran the copy from the laptop and 22 files arrived. The skill folder is untracked on both machines and the two copies have now diverged: the laptop's is stale, and the edits of 12:48Z exist only on rc-hjf. Do not edit the laptop copy. The command used was: `rsync -a --exclude '__pycache__' --exclude 'examples/*/build/' ~/projects/orient-writers/skills/docs-to-epub/ harry@hjf.shell.platform.ilg.software:projects/orient-writers/skills/docs-to-epub/`. A branch commit also works, but that needs his go-ahead.
- None for the build. Two small calls the next session can make and report: whether the voice guide should default to British English with no em dashes (recommendation: yes, as the default, switchable in `book.yaml` via `style.no_em_dash` and `language`), and whether the example should stay fictional (recommendation: yes).
- Commit and push of the skill: wait for his go-ahead.

## How work is done here
- Skills live in `~/projects/orient-writers/skills/<name>/` and are symlinked from `~/.claude/skills/`. Look at `plainly` and `c4-diagrams` for the shape.
- Commit and push only when Harry asks. Verify before committing. Never put a secret or real customer data in a skill.
- Report faithfully: say what ran and what did not. Open the rendered images, because the validators passed a diagram with literal `\n` in its labels.
- Global rules in `~/.claude/CLAUDE.md` apply (British English, no em dashes, `Tasks/` record, no Slack or Jira posting by agents).

## On the target
Checked on the laptop at 2026-11-11T12:26Z, not on the workstation. The laptop has Google Chrome 156 (headless works for screenshots), Graphviz 2.43, Java 21, ImageMagick 6, Python 3.12 with markdown-it-py, lxml, PyYAML and Pillow. It has no pandoc, calibre or EPUBCheck: `book.py validate` downloads EPUBCheck 5.4.0 to `~/.cache/docs-to-epub/` on first use and needs network and Java. `mdit_py_plugins`, `cairosvg` and `ebooklib` are not installed and are not needed. `~/.claude/skills/docs-to-epub` is meant to be a symlink into `~/projects/orient-writers`, which only exists where that repo is cloned.

**Checked on rc-hjf (the workstation) at 2026-11-11T12:32Z, from session `9e1daa5f-c28e-44cb-b0dd-e5b4bfb5878c`. The tooling was installed at 2026-11-11T12:40Z and the skill folder had arrived by 12:44Z (22 files, matching this record).**
- **The skill folder is not on rc-hjf.** `~/projects/orient-writers` is cloned there (branch `main`, level with `origin/main`) but has no `skills/docs-to-epub/`. A search of the filesystem for `docs-to-epub` found only this record. `~/.claude/skills/docs-to-epub` does not exist either.
- **Installed on rc-hjf at 2026-11-11T12:40Z, with Harry's go-ahead (all were missing).** Each was tested, not just installed:
  - Chromium 156.0.8078.79, by pacman. Google Chrome is AUR-only, and this is the same major version as the laptop's Chrome 156. `chromium --headless=new --screenshot` rendered a page with real fonts, no `--no-sandbox` needed. **Check which binary name `preview.py` looks for**: if it hardcodes `google-chrome`, point it at `chromium`.
  - Graphviz 16.1.1 (`dot` rendered a labelled graph). The laptop has 2.43, so layouts and label metrics may differ: re-read every figure image after the first build here.
  - OpenJDK JRE 27 headless (`java` is on `PATH` at `/usr/bin/java`). The laptop has Java 21. EPUBCheck 5.4.0 under Java 27 is untested.
  - rsync 3.5.1-3 (see the pacman gotcha below). Your laptop's `rsync` flags with `--exclude` were tested locally and work.
  - Python: markdown-it-py 4.3.0, lxml 6.1.3, PyYAML 6.0.3 and Pillow 13.0.0, installed with `pip --only-binary=:all:` into mise's Python 3.15.2, in the user site `~/.local/lib/python3.15/site-packages`. Plain `python3` sees them. `python3 -I` does not, because isolated mode skips the user site.
  - `ttf-dejavu` (DejaVu Sans, Serif and Sans Mono), installed at about 12:47Z. The figures and `book.css` name DejaVu, so this restores the intended look. It also changed the machine's default serif and monospace fonts (see Gotchas).
  - Not installed: ImageMagick (`convert`). No script calls it (Pillow does the image work), so it is not needed. `uv` is absent too. `preview.py` finds `chromium` as its second choice, so no change was needed there.
- **Present on rc-hjf:** Python 3, Node, `pacman`, `mise`, `pip`, `npm`. `sudo -n true` printed no error. `https://github.com` answered 200, so the EPUBCheck download would work once Java is installed.
- **Skills the record points at:** `plainly` is present on rc-hjf. `c4-diagrams` is not.
- The skill folder is on rc-hjf. The `~/.claude/skills/docs-to-epub` symlink is not created yet: it waits until `SKILL.md` exists (a skill folder with no `SKILL.md` is not a skill). `book.py validate` downloaded EPUBCheck 5.4.0 to `~/.cache/docs-to-epub/` on first use. It asks GitHub for `releases/latest`, so the version is not pinned: `latest` happened to be 5.4.0, the same as on the laptop.

## Gotchas
- **The skill folder is not in git or the vault.** It is untracked in the laptop's clone of `hjfitz/orient-writers`, and the vault sync carries notes only. A session on another machine finds this record and none of the code. Copy the folder across, or commit it to a branch on Harry's go-ahead, before handing over to another machine. (Found from rc-hjf at 2026-11-11T12:32Z.)
- **rc-hjf's pacman sync database is stale (2 Nov) and the mirror has dropped those versions.** Do not run `pacman -Sy` on its own: that is a partial upgrade. A full `-Syu` is 42 packages, including kernel 7.2.15, openssl 3.6.5 to 4.1.0, systemd, docker and openssh, so it needs a planned reboot. The 139 new packages above went in with `pacman -U` from the current mirror URLs, which left the system database alone and upgraded nothing already installed.
- **A mirror package can need a newer OpenSSL than rc-hjf has, and pacman does not object.** rsync 3.5.2 died with `libcrypto.so.4: cannot open shared object file`. The fix was 3.5.1-3 from archive.archlinux.org. After any `pacman -U` of new packages, run `ldd` over the new files and look for `not found`. The only other hits were optional (Graphviz's Perl, Lua and R bindings and `gvedit`, Chromium's Qt shim, audio and image viewers), and `libjvm.so`, which `ldd` cannot see because the `java` launcher loads it.
- **The figures need DejaVu Sans installed, and nothing warns when it is missing.** `FONT_DOT` is "DejaVu Sans". Without it, Graphviz measured text in one fallback font and Chromium drew another, so the two Graphviz figures came out in serif (unlike the sequence diagram, which has a CSS fallback chain). Fixed on rc-hjf by installing `ttf-dejavu`. A code fix is Next up 7.
- **Installing a font changes the previews.** `book.css` sets no body font on purpose (the reader's font wins) and only code names DejaVu Sans Mono, so the preview's body text is the machine's default serif. On rc-hjf that went from Nimbus Roman to DejaVu Serif when `ttf-dejavu` went in. It is wider, so line breaks are indicative only (the Sources ID column now wraps `lantern-` / `readme`). Judge wrapping and legibility, not exact line breaks.
- **`dot` ignores the width of a label on an edge inside a cluster.** The label can run through the cluster border even with the right font: "last attempt (not" in `queue-parts` crossed the Postgres box. Fixed with `margin=40` for any group that holds a labelled internal edge. Look at every figure that has a group.
- **Two copies of the skill folder exist.** The laptop's is stale from 12:48Z. Do not edit it. If work ever moves back, copy the rc-hjf folder over it first.
- **Validators miss layout.** EPUBCheck passed while the images were wrong. Three defects were only visible by opening the PNGs: literal `\n` in Graphviz labels (an escaping bug, fixed with `dlab()`), note text sitting on the box edge in the sequence renderer, and a forced left-to-right layout that shrank the text to 7.7 px. Always read the figure images.
- **YAML flow mappings need quotes.** A string containing a colon or a comma, such as `{text: returns, no error}`, silently splits or fails. Quote it.
- **EPUBCheck rules that bit:** `<figcaption>` must be the first or last child of `<figure>`, so the text description (`<details>`) goes after the figure. A source cited twice in one chapter needs unique back-reference ids.
- **Graphviz legends:** only worth the space with three or more node kinds. Group labels go at the bottom (`labelloc=b`) so incoming arrows do not cross them.
- **Preview tiles are not real pages.** Reflowable text has no fixed pages. The preview starts a tile at each feature (figure, table, longest code block, callout) so it can be judged whole.
- **`book.py` regenerates `build/`.** Figures and the cover are rebuilt only when their spec or `book.yaml` is newer than the output. Use `book.py figures` or `book.py cover` to force it.
- **A rejected tool call can still have run.** Harry interrupted a Bash call that edited files and rebuilt. Check the files before assuming either way.

## Closed since handover
| When (UTC) | Work | Result |
| --- | --- | --- |
| 2026-11-11T12:50Z | Fix what the full-size previews showed, rebuild, re-validate | Two defects fixed in `scripts/figures.py`, `scripts/book.py` and `assets/book.css`. A Graphviz label ran through its cluster border (groups with a labelled internal edge now get `margin=40`). The Sources table broke slugs and dates across lines ("Cited in" now lists chapter titles in book order, one per line, and dates do not break). Rebuilt: 0 errors, 0 warnings. EPUBCheck 5.4.0 VALID, no messages, under Java 27. 13 preview pages, 0 mechanical problems. All five images read again at full size |
| 2026-11-11T12:47Z | Install `ttf-dejavu` on rc-hjf | The Graphviz figures were rendering in serif because DejaVu Sans was missing (see Gotchas). After the install both Graphviz figures render in DejaVu Sans. `job-states` is clean |
| 2026-11-11T12:44Z | Re-run the example after the three earlier fixes, and judge the preview images | The rebuild ran clean on rc-hjf and EPUBCheck 5.4.0 reported VALID. Read at full size: the sequence figure (legible, but its 12 px text at 600 px is the smallest in the book), the long code page (wraps, and the hyphen in `attempt - 1` is ASCII, not a minus sign), the cover thumbnail (the title reads), the Sources table (widths work). The contents tile ends at "Open questions" only because the tile is 800 px high: the nav also lists Sources and List of figures |
| 2026-11-11T12:44Z | Copy the skill folder from the laptop | Harry ran the rsync. 22 files arrived and match this record: four scripts, `book.css` and the example. `references/` is empty and there is no `SKILL.md`, as expected |
