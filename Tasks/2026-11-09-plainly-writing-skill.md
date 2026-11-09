---
tags: [adhoc-task]
date: 2026-11-09
tldr: "Rebuilt the draft wiki-page-editor skill as plainly (write or rewrite any doc, high-signal, no fluff) with a lint.py that catches fluff and facts a rewrite dropped"
session_id: 8396ad15-6d38-46ca-9051-5d6124817a77
status: open
---
# Rebuild wiki-page-editor as the plainly writing skill

## Outcome
New skill at `orient-writers/skills/plainly/` (SKILL.md + lint.py), linked into `~/.claude/skills/plainly`. Adds a write-from-notes mode, `[??]` gap marking, a doc-type shape table and a concrete cut list. `lint.py --source` flags dropped numbers, IDs, URLs, code and obligation-word changes. Uncommitted: owed Harry's sign-off on the name and a commit.
