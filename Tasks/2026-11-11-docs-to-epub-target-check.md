---
tags: [adhoc-task]
date: 2026-11-11
tldr: "Resumed the docs-to-epub skill on rc-hjf: installed and tested the build tooling, verified the copied folder, rebuilt and validated the example, and fixed two defects found in the previews. SKILL.md and the references are still to write."
session_id: 9e1daa5f-c28e-44cb-b0dd-e5b4bfb5878c
status: open
---
# Check the docs-to-epub handover on the workstation

## Outcome
Ran `session-handover` for the "epub skill" on rc-hjf. The record [[Handovers/2026-11-11-docs-to-epub]] was written on the laptop. The skill folder (`skills/docs-to-epub/`) is untracked there, so it never reached rc-hjf. Harry chose to continue on rc-hjf and approved the installs. Installed 139 packages by `pacman -U` (Chromium, Graphviz, a JRE, rsync and their dependencies) and four Python libraries by `pip`, and tested each. The system pacman database is stale, so the sync database was left alone. rsync 3.5.2 needed OpenSSL 4 and failed, so rsync is the 3.5.1-3 build from the Arch archive. Harry then ran the rsync and 22 files arrived. I resumed the record (`status: resumed`), rebuilt the example (EPUBCheck 5.4.0 VALID, 13 preview pages, 0 mechanical problems) and read the previews at full size. That found DejaVu Sans missing (installed `ttf-dejavu`), a Graphviz label running through its cluster border, and a Sources table that broke slugs and dates. The last two are fixed in `figures.py`, `book.py` and `book.css`, uncommitted. The laptop's copy of the folder is now stale.
Owed: write `SKILL.md` and the seven reference documents, then create the `~/.claude/skills/docs-to-epub` symlink. Two robustness items are in the record's Next up (a font fallback in `FONT_DOT`, and a real e-reader test of the figure text description). Nothing is committed: wait for Harry's go-ahead.
