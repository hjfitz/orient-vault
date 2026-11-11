---
tags: [adhoc-task]
date: 2026-11-11
tldr: "Finished the docs-to-epub skill on rc-hjf: set up and tested the build tooling, fixed four tooling defects, wrote SKILL.md and seven references, and linked the skill. Uncommitted; the workflow has not yet run on a real document set."
session_id: 9e1daa5f-c28e-44cb-b0dd-e5b4bfb5878c
status: open
---
# Check the docs-to-epub handover on the workstation

## Outcome
Ran `session-handover` for the "epub skill" on rc-hjf. The record [[Handovers/2026-11-11-docs-to-epub]] was written on the laptop. The skill folder (`skills/docs-to-epub/`) is untracked there, so it never reached rc-hjf. Harry chose to continue on rc-hjf and approved the installs. Installed 139 packages by `pacman -U` (Chromium, Graphviz, a JRE, rsync and their dependencies) and four Python libraries by `pip`, and tested each. The system pacman database is stale, so the sync database was left alone. rsync 3.5.2 needed OpenSSL 4 and failed, so rsync is the 3.5.1-3 build from the Arch archive. Harry then ran the rsync and 22 files arrived. I resumed the record (`status: resumed`), rebuilt the example (EPUBCheck 5.4.0 VALID, 13 preview pages, 0 mechanical problems) and read the previews at full size. That found DejaVu Sans missing (installed `ttf-dejavu`), a Graphviz label running through its cluster border, and a Sources table that broke slugs and dates. The last two are fixed in `figures.py`, `book.py` and `book.css`, uncommitted. The laptop's copy of the folder is now stale.
Then wrote `SKILL.md` and seven references from the code, and linked the skill at `~/.claude/skills/docs-to-epub`. Testing the documented features in a second book found two more tooling defects: `chapter:` and `fig:` links were checked but never rewritten, and any book with no open gaps built an INVALID EPUB. Both are fixed. In total four defects fixed (cluster label overlap, Sources table wrapping, link rewriting, the no-gap about page) and one environment gap closed (DejaVu fonts).
Owed: Harry's go-ahead to commit. Add `skills/docs-to-epub/examples/*/build/` and `*.epubcheck.json` to `.gitignore` first, or `git add` stages about 31 generated files. Next up in the record: a font fallback in `FONT_DOT`, a real e-reader test of the figure text description, a kept feature-complete test book, and a first run of the skill on a real, non-confidential document set. Nothing is committed.
