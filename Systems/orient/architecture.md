---
tags:
- system
- orient
verified: '2026-11-09'
title: orient — architecture
thesis: "orient is four components around one artefact, the Obsidian vault, which stays authoritative and is a git repo synced between machines. The writers own exact vault paths. The app adopts the vault in place and reads it through a disposable SQLite index."
confidence: high
---
# orient — architecture

```orient-bluf
{ "v": 1, "bluf": "orient is four components around one artefact, the Obsidian vault, which stays authoritative and is a git repo synced between machines. The writers own exact vault paths. The app adopts the vault in place and reads it through a disposable SQLite index.", "confidence": "high", "action": "Never add an app feature that needs vault files rewritten. Change a doc-kind list or frontmatter rule in wp.py and orient together. Put durable data in the vault, never the state dir." }
```

Four components around one shared artefact: **the Obsidian vault**. Everything here exists to
write to it or to read from it, and the vault, not any program, is the source of truth.

**CONFIRMED** The app repo also holds a read-only Go MCP server (`mcp/`) and the meeting recorder (`scribe/`) [5]. Six systemd user units run on the machine: `orient-web`, `orient-index`, `orient-pty`, `orient-desk`, `orient-scribe` and `orient-vault-sync` (a 90 s timer) [6].

```orient-flow
{ "v": 1, "title": "Who writes the vault, who reads it",
  "nodes": [
    { "id": "hjf", "label": "Harry", "sub": "edits in Obsidian, reads in the app", "kind": "external" },
    { "id": "agents", "label": "Claude Code sessions", "sub": "run skills all day", "kind": "external" },
    { "id": "skills", "label": "~30 Claude Code skills", "sub": "digests, triage, tickets, reviews", "kind": "external", "ev": [2] },
    { "id": "wp", "label": "wp.py and cust.py", "sub": "plans, ledgers, programmes, systems", "kind": "external", "ev": [2] },
    { "id": "vault", "label": "Obsidian vault", "sub": "~/Documents/obsidian, a git repo", "kind": "store", "tone": "accent", "ev": [1] },
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

**CONFIRMED** **The vault is authoritative and belongs to the writers.** `wp.py` (22 subcommands), `cust.py` and the skills own exact paths and write them every weekday. The app **adopts the vault in place**. It never moves, renames or rewrites an existing file except through a user-initiated editor save. It adds `<vault>/.knowledge/`, and new documents only under `Prompts/`, `Engineering/<svc>/decisions/`, `_heap/`, `Digests/Orientation/` and `People/`. Every write passes `resolveWritablePath` [1][7].

That asymmetry is the whole design. The app can be deleted and rebuilt with no data loss. A schema idea that needs vault files rewritten is out of bounds.

## Read path

```orient-flow
{ "v": 1, "title": "Read path",
  "nodes": [
    { "id": "v", "label": "Vault", "sub": "~1,060 Markdown files", "kind": "store", "ev": [8] },
    { "id": "w", "label": "orient-index.service", "sub": "systemd user unit, vault watcher", "kind": "step", "ev": [6] },
    { "id": "db", "label": "SQLite and FTS5", "sub": "~/.local/state/orient", "kind": "store", "ev": [1] },
    { "id": "app", "label": "orient-web.service", "sub": "127.0.0.1:3000", "kind": "service", "service": "orient", "tone": "accent", "ev": [6] },
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

**CONFIRMED** **The index is disposable.** Updates go in place, never by rename: renaming a new file over the live one strands every open reader on a deleted inode [1].

**CONFIRMED** Costs, measured: one save takes about 25 ms, a full rebuild about 8.7 s, and staleness stamping about 7 s, so it runs every 15 min [1]. A structural change schedules a full sweep after 30 s quiet, with a 6-hour backstop. It changes how *other* documents' links resolve.

**CONFIRMED** `orient-web` binds `127.0.0.1:3000` only [6]. Reach it from another machine over an SSH tunnel. The app serves the whole vault, sensitive globs included, and accepts editor saves.

## What lives where

**CONFIRMED** `.knowledge/` holds two kinds of data [1][9]:

- **Derived, regenerable:** `manifest.json` and `reports/`. Rollback is deleting them and the state dir.
- **Durable, synced:** `records/<host>/` (usage, plan-usage, work-usage, analytics and write logs), `recordings/<host>/`, and the append-only `plan-status.jsonl` and `todo-defers.jsonl`.

**CONFIRMED** `~/.local/state/orient` holds only the index, caches, run dirs and secrets it can mint again. Nothing durable may live only there [10].

**CONFIRMED** Each machine names itself in `~/.config/orient/host` (default `laptop`). It appends only under its own `<host>/` directory, so no record file has two writers [10]. Readers merge every host.

**CONFIRMED** The VM (`rc-hjf`, host `vm`) is orient's home. The laptop is a window onto it through `orient-tunnel` (`:3000` web, `:3011` terminal, `:3014` the VM's scribe) and runs no web or terminal of its own; with `~/.config/orient/sync-peer` set, `scripts/install-units.sh` installs it that way. The VM's sshd allows local forwards only, so every connection between the two starts on the laptop.

**CONFIRMED** Recordings live on the VM [11]. The laptop's scribe (`-role recorder`) only captures. It hands each finished recording to the VM's (`-role server`) over `:3014` with a hub token, and deletes its copy once the VM's receipt matches its sha256. The laptop polls the VM every second, so the VM's page can start, stop, pause, resume and ignore a laptop recording through the relay. The VM writes `recordings/vm/` and, adopted in place (`-adopt laptop`), the laptop's older `recordings/laptop/`. Transcripts and summaries sync. Audio never syncs; it lives on the VM and is deleted 14 days after a recording is enhanced, unless the recording is marked keep. Recordings of a host neither its own nor adopted are read-only: edits return 409.

**CONFIRMED** The manifest has one writer, the host named `manifestWriter` in `config.yaml` [10]. Other hosts skip writing it.

## Sync between machines

```orient-flow
{ "v": 1, "title": "How a write reaches the other machines",
  "nodes": [
    { "id": "w", "label": "A write", "sub": "wp, cust, orient save, Claude Code edit", "kind": "step" },
    { "id": "s", "label": "orient-vault-sync", "sub": "commit, fetch, merge, push", "kind": "service", "service": "orient", "tone": "accent", "ev": [9] },
    { "id": "o", "label": "origin", "sub": "the authoritative copy", "kind": "store" },
    { "id": "b", "label": "Another machine", "sub": "its timer or its next rewrite pulls", "kind": "external" }
  ],
  "edges": [
    { "from": "w", "to": "s", "label": "kick" },
    { "from": "s", "to": "o", "label": "push" },
    { "from": "o", "to": "b", "label": "kicked at once; else its timer, ≤90 s" }
  ] }
```

- **CONFIRMED** `scripts/vault-sync.sh` commits everything, fetches, **merges (never rebases)** and pushes [9]. A timer runs it every 90 s.
- **CONFIRMED** Each writer kicks a sync after a write, so the write reaches origin in under 1 s [9][12]. A kick during a running sync makes it go round again.
- **CONFIRMED** A `wp`/`cust` command that rewrites a file pulls first [12]. Offline, the kick is a no-op and commits queue.
- **CONFIRMED** A push that sent this machine's commits is announced, so the other machine pulls at once (about 5 s each way, measured 2026-11-09). It's appended to `.git/orient-pushed`. The laptop, whose `sync-peer` names the VM, kicks the VM's sync over ssh. The VM can't reach the laptop, so the laptop's `orient-vault-follow` runs `tail -F` on the VM's `orient-pushed` over ssh and kicks its own. A push that only fast-forwarded announces nothing, so the two never set each other off. If the peer is down, each machine falls back to its timer.
- **CONFIRMED** Records commit at most hourly: the statusline appends 3,000 to 5,000 rows a day [9].
- **CONFIRMED** `.gitattributes` unions append-only logs and ledgers and keeps "ours" for generated indexes [13]. A conflict aborts the merge, writes `.git/orient-sync-status` and notifies once.

## Layering inside the app

- React components never import `better-sqlite3`, `node:fs` or `child_process`. All data flows through `src/domain/*` (`server-only`).
- No SQL outside `src/query/builder.ts`.
- One render boundary: `src/render/renderDocument.tsx`. `.md` renders as Markdown; `.mdx` as MDX **only** under a trusted folder (`Prompts/`), with ESM rejected.
- Sensitive globs (`Bifrost/HR`, `Bifrost/Team`, `Interviews`) are indexed and searchable but never enter Today or prompt context.
- **No LLM calls.** The app emits a prompt; Claude Code executes it.

## The writers

**CONFIRMED** `wp.py`, `cust.py`, the hooks, the statusline and Harry's own skills live in the `orient-writers` repo (`~/projects/orient-writers`) [2]. Each is linked into `~/.claude` at the directory level. A gitleaks pre-commit hook guards it.

**ASSESSED** They are versioned but not an onboarded `Engineering/` service, so docs cannot sha-anchor them yet. Their contracts are documented where they bind: this doc and `known-context.md`.

## Coupling that must hold

**CONFIRMED** The app hand-mirrors constants the writers own. Frontmatter parsing must agree with `wp.py`'s splitter and key lists. orient's `WAYPOINT_DOC_KINDS` mirrors `wp.py`'s `DEFAULT_DOCS` [1]. **Add a doc kind in one and not the other and it silently renders as "other".** The host-id pattern and records path are mirrored the same way between `config.ts` and `wp.py` [10].

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": "README.md@11aaab0", "note": "orient repo: write rules, watcher costs, state and .knowledge locations" },
  { "id": 2, "kind": "doc", "ref": "~/projects/orient-writers@01dbcf2", "note": "wp.py has 22 top-level subcommands; 32 skills" },
  { "id": 3, "kind": "code", "ref": "CLAUDE.md@11aaab0", "note": "orient repo: architecture invariants" },
  { "id": 4, "kind": "code", "ref": "src/adapters/github.ts@11aaab0", "note": "the app's own fetches go to Jira, GitHub, Datadog and incident.io adapters" },
  { "id": 5, "kind": "code", "ref": "docs/mcp-spec.md@11aaab0" },
  { "id": 6, "kind": "doc", "ref": "~/.config/systemd/user/orient-*.service", "note": "orient-web ExecStart: next start -H 127.0.0.1 -p 3000; six units plus orient-vault-sync.timer, 2026-11-03" },
  { "id": 7, "kind": "code", "ref": "src/edit/pathSafety.ts@11aaab0" },
  { "id": 8, "kind": "log", "ref": "find ~/Documents/obsidian -name '*.md' -not -path '*/.*': 1,062 files, 2026-11-03" },
  { "id": 9, "kind": "code", "ref": "scripts/vault-sync.sh@11aaab0" },
  { "id": 10, "kind": "code", "ref": "src/config.ts@11aaab0", "note": "hostId, recordsDir, manifestWriter, vaultSyncBin" },
  { "id": 11, "kind": "code", "ref": "scribe/internal/store/store.go@11aaab0" },
  { "id": 12, "kind": "code", "ref": "src/adapters/vault-sync.ts@11aaab0" },
  { "id": 13, "kind": "doc", "ref": "~/Documents/obsidian/.gitattributes" }
] }
```
