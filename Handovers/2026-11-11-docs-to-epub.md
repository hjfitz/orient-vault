---
tags: [handover]
status: open
workstream: Build the reusable `docs-to-epub` skill (technical documentation to an illustrated EPUB with a custom cover). Tooling is built and tested; SKILL.md and the references are not written yet
programme: none
repo: hjfitz/orient-writers (local clone ~/projects/orient-writers, path skills/docs-to-epub, untracked)
from: laptop (freightops)
to: next session, any machine with the laptop's ~/projects/orient-writers
session_id: 4ff6c302-4da3-4b14-bf3c-fc976c0ec75b
resumed_by: ""
updated: 2026-11-11T12:30Z
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
The tooling exists and works end to end on a fictional example. The prose half of the skill (the workflow in `SKILL.md` and the reference documents) is not written. Nothing is committed and the skill is not yet linked into `~/.claude/skills`.

All paths below are under `~/projects/orient-writers/skills/docs-to-epub/`.

| Unit | What it delivered | State |
| --- | --- | --- |
| `scripts/book.py` | CLI: `init`, `figures`, `cover`, `check`, `build`, `validate`, `preview`, `all`. Pure Python (markdown-it-py, lxml, PyYAML, Pillow). Own Markdown dialect: `[^source-id:locator]` citations, `::: kind` callouts (hypothetical, gap, note, warning, tip, example, investigation), `{{figure:id}}`. Builds EPUB 3 with a nav document, NCX, accessibility metadata, per-chapter source notes, a Sources page, an Open questions page (from `gaps.yaml`) and a List of figures | Works. 20-odd checks (placeholders, uncited chapters, long code lines, wide tables, missing alt text, unreferenced figures, open gaps not shown) |
| `scripts/figures.py` | Diagram specs in YAML to SVG and PNG. `sequence` is drawn by its own renderer. `state` and `graph` (aliases `component`, `flow`) go through Graphviz `dot`, trying left-to-right and top-to-bottom and keeping the more legible. Reports text size at 600 px wide and flags anything under 11 px | Works. Fixed three defects found by looking at the images |
| `scripts/cover.py` | Generated 1600 x 2560 JPEG cover from the title (motifs `network`, `arcs`, `grid`; palettes `ink`, `paper`, `signal`), or a supplied image | Works. Looked good at thumbnail size |
| `scripts/preview.py` | Unzips the EPUB, renders every page in headless Chrome at 600 x 800 (`eink`) or 390 x 844 (`phone`), measures sideways overflow and figure text size, writes representative page images and a contact sheet | Works. Three fixes applied but not re-run (see In flight) |
| `assets/book.css` | E-ink-first stylesheet: relative units, wrapping code blocks, callouts that rely on text labels and border styles, not colour | Done |
| `examples/lantern-queue/` | A fictional worked example ("Reading a Retry Queue", about an invented job queue called Lantern): 6 chapters, 3 figures (sequence, state, component), `sources.yaml`, `gaps.yaml` with one open question, a `PLAN.md` showing the plan format, and `source-material/` it cites | Built, **EPUBCheck 5.4.0 reported VALID with no messages** before the last three fixes |
| `SKILL.md` and `references/` | The workflow, the voice guide, the diagram guide, the plan template, the format spec | **Not written** |
| `~/.claude/skills/docs-to-epub` symlink | Makes the skill invocable | **Not created** |

The example is fictional on purpose: nothing from the unannounced Merak research may go into a reusable skill that could be pushed.

## In flight
Nothing is running. No agents or workflows were started for this workstream.

| Work | Where | State | To close it |
| --- | --- | --- | --- |
| Re-run the example after three fixes | `scripts/preview.py` (metrics box now hidden; each tile starts at the feature, not a fixed 800 px boundary), `scripts/book.py` (Sources table gets column widths) | The edits are on disk. Whether the rebuild that followed them ran is unknown: Harry interrupted that command | `cd ~/code && B=~/projects/orient-writers/skills/docs-to-epub/scripts/book.py; E=<scratch>/lantern.epub; python3 $B build ~/projects/orient-writers/skills/docs-to-epub/examples/lantern-queue -o $E && python3 $B validate $E && python3 $B preview $E --out <scratch>/lantern-preview` |
| Judge the preview images one by one | `<scratch>/lantern-preview/` | Only the contact sheet has been read. It showed the cover, contents, callouts, a table and wrapped code all behaving. Still to read at full size: the figure pages (is the sequence diagram's 12 px text legible?), the long code page, the cover thumbnail, the Sources table | Open each PNG with Read. The checks cannot judge legibility or taste |

## Next up
1. **Re-run the example** (command above) and read the page images at full size. Fix anything real.
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

## Waiting on Harry
- None for the build. Two small calls the next session can make and report: whether the voice guide should default to British English with no em dashes (recommendation: yes, as the default, switchable in `book.yaml` via `style.no_em_dash` and `language`), and whether the example should stay fictional (recommendation: yes).
- Commit and push of the skill: wait for his go-ahead.

## How work is done here
- Skills live in `~/projects/orient-writers/skills/<name>/` and are symlinked from `~/.claude/skills/`. Look at `plainly` and `c4-diagrams` for the shape.
- Commit and push only when Harry asks. Verify before committing. Never put a secret or real customer data in a skill.
- Report faithfully: say what ran and what did not. Open the rendered images, because the validators passed a diagram with literal `\n` in its labels.
- Global rules in `~/.claude/CLAUDE.md` apply (British English, no em dashes, `Tasks/` record, no Slack or Jira posting by agents).

## On the target
Checked on the laptop at 2026-11-11T12:26Z, not on the workstation. The laptop has Google Chrome 156 (headless works for screenshots), Graphviz 2.43, Java 21, ImageMagick 6, Python 3.12 with markdown-it-py, lxml, PyYAML and Pillow. It has no pandoc, calibre or EPUBCheck: `book.py validate` downloads EPUBCheck 5.4.0 to `~/.cache/docs-to-epub/` on first use and needs network and Java. `mdit_py_plugins`, `cairosvg` and `ebooklib` are not installed and are not needed. The workstation was not checked: confirm Chrome, Graphviz and Java there before moving the work, and note that `~/.claude/skills/docs-to-epub` is a symlink into `~/projects/orient-writers`, which only exists where that repo is cloned.

## Gotchas
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
