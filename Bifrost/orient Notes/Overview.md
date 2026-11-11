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
Notes is small today (a folder tree, a CodeMirror editor, rename and trash; two generated C4 notes in the vault) but the target touches the renderer, the index's notion of a page type, the write path, git, and an upload surface, and the vault is shared with `wp`, skills and agents that write fixed paths. Sixteen units, four of them (the block registry, history, uploads, and the structural-path exclusion in the index) carry real risk, so the order and the gates matter more than the code. Two adversarial reviews reshaped the first draft (see the Design's revision list).

## Strategy
Prove the renderer first: **N0** a golden harness, then **N1** the block registry (behaviour-preserving). **N2** then deletes the Diagrams builder (it needs N1 so that `STARTERS` and `diagram-lint` have a new home), and **N3** adds the page-type registry. The workspace follows, in series because the units share files (**N4a** read model, **N4b** shell, **N5** templates, **N6** labels and properties, **N7** the editor's insert menu), then history (**N8**) and, behind a gate and an opus-tier session, attachments (**N9a** store and serve, **N9b** upload, **N9c** embed). Soaks and incidents become typed spaces (**N10**); live in-body macros (**N11**) are deferred. Each unit is built by a sonnet builder, reviewed with review-panel, and deployed by named sha, as with the Svelte UI programme. Writes are tested on a side-port core against a scratch vault, never the real vault.

## Scar tissue
The vault belongs to other tools (`wp`, skills, agents): the app only writes under `Notes/`, never moves an existing file, never re-serialises YAML. The write guard stays as it is. A document's type is folder-derived and Notes/ is always `note`. Registries are static imports. Full list in the Migration State.

## Next
**N0** (the golden harness) is the only unblocked unit, and everything renderer-related waits on it. Driven by `waypoint-programme`.
