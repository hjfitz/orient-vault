---
title: "orient Notes — Overview"
status: active
verdict: go
owner: "hjf"
services: ["orient"]
created: "2026-11-11"
updated: "2026-11-11"
tags: [bifrost]
---
# orient Notes — Overview

## Deliverables
- [[orient Notes/Migration State|Migration State]] — the live source of truth for progress
- [[orient Notes/Design|Design]] — the model, the two registries, the units, the defaults taken

## Verdict
**Go.** Harry asked for it on 2026-11-11 ("turn this in to a clone of confluence", extensible for soaks and incidents, Diagrams merged or trashed). The scope, the typed-page approach and the Diagrams decision are his answers recorded in the Migration State decision log. It rides on one gate: G1 (attachment policy) before the upload unit N9, which also needs an opus-tier session.

## Why this needs a programme
Notes is small today (a folder tree, a CodeMirror editor, rename and trash; two generated C4 notes in the vault) but the target touches the renderer, the index's notion of a page type, the write path, git, and an upload surface, and the vault is shared with `wp`, skills and agents that write fixed paths. Twelve units, three of them (the block registry, history, uploads) carry real risk, so the order and the gates matter more than the code.

## Strategy
Build the two registries first, because everything else plugs into them: **N1** the block registry (behaviour-preserving, proven by a golden render corpus) and **N3** the page-type registry. **N2** then deletes the Diagrams builder (it needs N1 so that `STARTERS` and `diagram-lint` have a new home). The workspace follows (**N4** tree, breadcrumbs, folder view; **N5** templates; **N6** labels and properties; **N7** the editor's insert menu), then history (**N8**) and, behind a gate, attachments (**N9**). Soaks and incidents become typed spaces (**N10**); live in-body macros (**N11**) are deferred. Each unit is built by a sonnet builder, reviewed with review-panel, and deployed by named sha, as with the Svelte UI programme. Writes are tested on a side-port core against a scratch vault, never the real vault.

## Scar tissue
The vault belongs to other tools (`wp`, skills, agents): the app only writes under `Notes/`, never moves an existing file, never re-serialises YAML. The write guard stays as it is. A document's type is folder-derived and Notes/ is always `note`. Registries are static imports. Full list in the Migration State.

## Next
**N1** (block registry) and **N3** (page-type registry) are unblocked and independent; they touch different files, so they can run side by side. Driven by `waypoint-programme`.
