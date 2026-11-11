---
tags: [adhoc-task]
date: 2026-11-11
tldr: "Resumed the docs-to-epub skill on rc-hjf: installed and tested the build tooling, verified the copied folder, rebuilt and validated the example, and fixed two defects found in the previews. SKILL.md and the references are still to write."
session_id: 9e1daa5f-c28e-44cb-b0dd-e5b4bfb5878c
status: open
---
# Check the docs-to-epub handover on the workstation

## Outcome
Ran `session-handover` for the "epub skill" on rc-hjf. The record [[Handovers/2026-11-11-docs-to-epub]] was written on the laptop. The skill folder (`skills/docs-to-epub/`) is untracked there, so it never reached rc-hjf. Harry chose to continue on rc-hjf and approved the installs. Installed 139 packages by `pacman -U` (Chromium, Graphviz, a JRE, rsync and their dependencies) and four Python libraries by `pip`, and tested each. The system pacman database is stale, so the sync database was left alone. rsync 3.5.2 needed OpenSSL 4 and failed, so rsync is the 3.5.1-3 build from the Arch archive. Record updated in place and left `open`.
Owed: Harry runs the `rsync` from the laptop (command in the record) to copy the skill folder across. Then a session on rc-hjf resumes the record, creates the `~/.claude/skills/docs-to-epub` symlink and re-runs the example build.
