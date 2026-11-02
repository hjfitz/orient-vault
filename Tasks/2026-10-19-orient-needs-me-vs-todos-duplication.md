---
tags: [adhoc-task]
date: 2026-10-19
tldr: "Investigated why orient's Needs me today and Todos duplicate: morning-digest Step 4 copies every Needs-me item into Todo, then the two lists live independently. Fixed in morning-digest Step 4; today's Todo pruned."
session_id: 42f7cd29-59f8-40b5-9fff-b4d234284f1d
status: done
---
# Explain orient Needs-me vs Todos duplication

## Outcome
Read-only. Cause is morning-digest Step 4 ("new todos derived from Needs me today"): no shared id, ticks and text drift apart. 2026-10-19 digest: 21 Needs-me items, 128 open Todos (108 carried 5+ days), 15 Needs-me items share a wikilink with a Todo.
Changed: morning-digest SKILL.md Step 4 (one item one list, no Needs-me to Todo copy, evidence-only closes, re-triage at x10) plus template and pre-save check.
Pruned 2026-10-19 Todos 128 -> 103 open: 22 ticked on the digest's own evidence (drop tomorrow), 3 duplicate-of-Needs-me lines removed. Nothing owed.
