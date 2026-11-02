---
tags:
- system
- orient
verified: '2026-09-24'
title: orient — overview
thesis: "orient is Harry's personal engineering-knowledge system: an Obsidian vault that tools fill as a side effect of real work, and a local app that reads it. The vault is the source of truth. The app and its index are disposable."
confidence: moderate
---
# orient — overview

```orient-bluf
{ "v": 1, "bluf": "orient is Harry's personal engineering-knowledge system: an Obsidian vault that tools fill as a side effect of real work, and a local app that reads it. The vault is the source of truth. The app and its index are disposable.", "confidence": "moderate", "action": "Keep the vault plain Markdown that Obsidian and grep can read with the app deleted." }
```

**What it is.** Harry's personal engineering-knowledge system: an Obsidian vault of durable
context, the tooling that writes it all day, and a local web app that makes it readable.

**Who it serves.** One expert reader, plus the Claude Code sessions that work alongside him.
That single-reader assumption is why the app is dense, keyboard-first and dark-only — and why
it must never be judged against an operator tool like [[fuse-ui]].

**Why it exists.** Engineering context decays between sessions. Jira says what was asked,
git says what changed, neither says *why it is shaped this way* or *what is in flight*. The
vault carries that, and only survives because tools write to it as a side effect of real work
rather than as documentation homework.

## Components

| Component | Where | Onboarded |
| --- | --- | --- |
| orient (Next.js app) | `~/projects/orient` | yes — [[orient]] service |
| `wp.py` / `cust.py` | `~/.claude/waypoint`, `~/.claude/customers` | no — not a git repo |
| ~30 Claude Code skills | `~/.claude/skills` | no — not a git repo [2] |
| orient-mcp (Go, read-only) | `~/projects/orient/mcp` | part of the [[orient]] repo [1] |
| The vault | `~/Documents/obsidian` | n/a — it is the artefact |

## Relationship to the work

This system is *about* [[fuse]] and [[ilg-platform]] but is not part of them: it is personal
tooling that happens to have those as its subject. Nothing here ships to a customer, there is
no CI, no remote, and commits go straight to a local `master` [3].

## Boundaries

**In scope:** capturing and surfacing engineering context; the read/write contract over the
vault; the skills that produce records as a by-product of doing the work.

**Out of scope:** anything that would make the vault depend on the app. The vault must stay
plain Markdown that Obsidian and `grep` can read with the app deleted.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "docs/mcp-spec.md@27cc8db", "note": "orient repo: read-only Go MCP server over the SQLite index" },
  { "id": 2, "kind": "doc", "ref": "~/.claude/skills", "note": "31 skill directories, 2026-10-13; not a git repo" },
  { "id": 3, "kind": "code", "ref": "CLAUDE.md@27cc8db", "note": "orient repo: vault rule, no remote, commits straight to master" }
] }
```
