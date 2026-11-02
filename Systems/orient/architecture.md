---
tags:
- system
- orient
verified: '2026-09-24'
title: orient — architecture
thesis: "orient is four components around one artefact, the Obsidian vault, which stays authoritative. The writers own exact vault paths. The app adopts the vault in place and reads it through a disposable SQLite index."
confidence: moderate
---
# orient — architecture

```orient-bluf
{ "v": 1, "bluf": "orient is four components around one artefact, the Obsidian vault, which stays authoritative. The writers own exact vault paths. The app adopts the vault in place and reads it through a disposable SQLite index.", "confidence": "moderate", "action": "Never add an app feature that needs vault files rewritten. Change a doc-kind list or frontmatter rule in wp.py and orient together." }
```

Four components around one shared artefact: **the Obsidian vault**. Everything here exists to
write to it or to read from it, and the vault — not any program — is the source of truth.

The app repo also holds a read-only Go MCP server over the index (`mcp/`) [5]. Three systemd user units run beside it: `orient-web` (the app), `orient-index` (the watcher) and `orient-pty` (a terminal sidecar) [6].

```orient-flow
{ "v": 1, "title": "Who writes the vault, who reads it",
  "nodes": [
    { "id": "hjf", "label": "Harry", "sub": "edits in Obsidian, reads in the app", "kind": "external" },
    { "id": "agents", "label": "Claude Code sessions", "sub": "run skills all day", "kind": "external" },
    { "id": "skills", "label": "~30 Claude Code skills", "sub": "digests, triage, tickets, reviews", "kind": "external", "ev": [2] },
    { "id": "wp", "label": "wp.py and cust.py", "sub": "plans, ledgers, programmes, systems", "kind": "external", "ev": [2] },
    { "id": "vault", "label": "Obsidian vault", "sub": "~/Documents/obsidian, authoritative", "kind": "store", "tone": "accent", "ev": [1] },
    { "id": "app", "label": "orient", "sub": "Next.js app, reads the vault in place", "kind": "service", "service": "orient", "ev": [1, 3] },
    { "id": "src", "label": "External systems", "sub": "Jira, GitHub, Datadog, incident.io, Slack, email", "kind": "external", "ev": [4] }
  ],
  "edges": [
    { "from": "hjf", "to": "vault", "label": "edits" },
    { "from": "agents", "to": "skills", "label": "invoke" },
    { "from": "skills", "to": "wp", "label": "call" },
    { "from": "wp", "to": "vault", "label": "writes exact paths" },
    { "from": "skills", "to": "vault", "label": "write records" },
    { "from": "app", "to": "vault", "label": "reads in place" },
    { "from": "hjf", "to": "app", "label": "reads" },
    { "from": "skills", "to": "src", "label": "query" },
    { "from": "app", "to": "src", "label": "Jira, GitHub, Datadog, incident.io", "style": "dashed" }
  ] }
```

## The one rule

**The vault is authoritative and belongs to the writers.** `wp.py` (22 subcommands),
`cust.py` and the skills own exact paths and write them every weekday. The app **adopts the
vault in place**: it never moves, renames or rewrites an existing file except through a
user-initiated editor save. It adds `<vault>/.knowledge/`, and new documents only under `Prompts/`, `Engineering/<svc>/decisions/`, `_heap/`, `Digests/Orientation/` and `People/`. Every write passes `resolveWritablePath` [1][7].

That asymmetry is the whole design. It is why the app can be deleted and rebuilt with no data
loss, and why a schema idea that would require rewriting vault files is out of bounds.

## Read path

```orient-flow
{ "v": 1, "title": "Read path",
  "nodes": [
    { "id": "v", "label": "Vault", "sub": "~700 Markdown files", "kind": "store", "ev": [8] },
    { "id": "w", "label": "orient-index.service", "sub": "systemd user unit, vault watcher", "kind": "step", "ev": [6] },
    { "id": "db", "label": "SQLite and FTS5", "sub": "~/.local/state/orient", "kind": "store", "ev": [1] },
    { "id": "app", "label": "orient-web.service", "sub": "Next.js server components, port 3000", "kind": "service", "service": "orient", "tone": "accent", "ev": [6] },
    { "id": "mcp", "label": "orient-mcp", "sub": "Go stdio server, read-only", "kind": "external", "ev": [5] }
  ],
  "edges": [
    { "from": "v", "to": "w", "label": "watch" },
    { "from": "w", "to": "db", "label": "incremental, in place" },
    { "from": "db", "to": "app" },
    { "from": "db", "to": "mcp", "label": "mode=ro" },
    { "from": "app", "to": "v", "label": "editor saves and new docs only", "style": "dashed" }
  ] }
```

**The index is disposable**; the manifest lives in `<vault>/.knowledge/`. Rollback is deleting
both. Updates are **in place, never a rename** — renaming a new file over the live one strands
every open reader on a deleted inode.

Costs, measured: one save ≈ 25 ms; full rebuild ≈ 8.7 s; staleness stamping ≈ 7 s (hence
every 15 min, not per save) [1]. A structural change schedules a full sweep after 30 s quiet (and every 6 hours as a backstop),
because it changes how *other* documents' links resolve.

`orient-web.service` runs `next start -H 0.0.0.0 -p 3000`, so it listens on every interface, not loopback [6]. **UNKNOWN** whether a host firewall limits it. The app serves the whole vault, sensitive globs included, and accepts editor saves.

## Layering inside the app

- React components never import `better-sqlite3`, `node:fs` or `child_process` — all data
  flows through `src/domain/*` (`server-only`).
- No SQL outside `src/query/builder.ts`.
- One render boundary: `src/render/renderDocument.tsx`. `.md` → Markdown; `.mdx` → MDX **only**
  under a trusted folder (`Prompts/`), ESM rejected.
- Sensitive globs (`Bifrost/HR`, `Bifrost/Team`, `Interviews`) are indexed and searchable but
  never enter Today or prompt context.
- **No LLM calls.** The app emits a prompt; Claude Code executes it.

## Components not separately onboarded

Only the app is an `Engineering/` service — it is the one component with a git repo.
`wp.py`/`cust.py` and the skills live under `~/.claude`, which is **not version-controlled**,
so they cannot be sha-anchored and have no `waypoint.yaml`. Their contracts are documented
where they bind: this doc, and `known-context.md`.

That is a real gap, not a deliberate choice — losing `~/.claude` would lose the writers.

## Coupling that must hold

The app hand-mirrors constants the writers own. Frontmatter parsing must agree with `wp.py`'s
splitter and key lists, and orient's `WAYPOINT_DOC_KINDS` mirrors `wp.py`'s `DEFAULT_DOCS` [1].
**Add a doc kind in one and not the other and it silently renders as "other".**

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "README.md@27cc8db", "note": "orient repo: write rules, watcher costs, state locations" },
  { "id": 2, "kind": "doc", "ref": "~/.claude/waypoint/wp.py", "note": "22 top-level subcommands; 31 skill directories under ~/.claude/skills; neither is a git repo" },
  { "id": 3, "kind": "code", "ref": "CLAUDE.md@27cc8db", "note": "orient repo: architecture invariants" },
  { "id": 4, "kind": "code", "ref": "src/adapters/github.ts@27cc8db", "note": "the app's own fetches go to Jira, GitHub, Datadog and incident.io adapters; no Slack adapter exists" },
  { "id": 5, "kind": "code", "ref": "docs/mcp-spec.md@27cc8db" },
  { "id": 6, "kind": "doc", "ref": "~/.config/systemd/user/orient-web.service", "note": "also orient-index.service and orient-pty.service" },
  { "id": 7, "kind": "code", "ref": "src/edit/pathSafety.ts@27cc8db" },
  { "id": 8, "kind": "log", "ref": "find ~/Documents/obsidian -name '*.md', excluding dot-directories: 700 files, 2026-10-13" }
] }
```
