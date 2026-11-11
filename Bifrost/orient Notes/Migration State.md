---
title: "orient Notes — Migration State"
programme: "orient-notes"
status: active
owner: "hjf"
services: ["orient"]
created: "2026-11-11"
updated: "2026-11-11"
tags: [bifrost, migration-state]
---
# orient Notes — Migration State

<!-- The single source of truth for PROGRESS. The Overview carries the narrative and the verdict;
     this doc is the live ledger a session reads to know what is done and what is next.
     `wp programme status/next/tick` read and write the `## Unit status` tables below, so keep the
     table shape intact. The shape of the work: [[orient Notes/Design|Design]]. -->

orient has no PRs or CI: a unit ships as commits on `master`, pushed, then deployed (`pnpm deploy:all`, a named sha). The `PR` column holds the commit range. Builders are sonnet, at most 3 at once in the shared checkout, no worktrees; every unit is reviewed with review-panel before it deploys.

## Unit status
Legend: ⬜ not started · 🟨 in progress · ✅ merged · ⛔ blocked · ⏸ deferred · ❌ dropped · 🔄 rescoped

### Foundations
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **N1** | ⬜ | Block registry, behaviour-preserving | | med | sonnet/high | | One `BlockSpec` per fenced block (bluf, evidence, flow, sequence, data, action) replaces the if-chain at `html/blocks.ts:195-236`, the duplicated `parse` helper and four hand-written regexes; `diagram-lint` becomes flow/sequence `lint`. **Gate: a golden corpus.** `scripts/render-golden.ts` renders every doc of a scratch vault clone before and after; sha256 of every HTML must match, `RENDERER_VERSION` unchanged. Exports a block manifest. |
| **N2** | ⬜ | Delete the Diagrams builder | N1 | low | sonnet/medium | | Page, `DiagramEditor`, `knowledge/diagrams.ts`, `ops/diagrams.ts`, DTOs, query, nav entry (4 places), tests go; presets, `explainer-blocks`, `flow-layout`, `html/diagrams` stay; `STARTERS` become registry starters. `/diagrams` answers 308 to `/notes`. A stale `diagrams` slug in the vault's nav config must be harmless (test). |
| **N3** | ⬜ | Page-type registry and typed chrome | | med | sonnet/high | | `src/domain/page-types.ts`; `DocHeaderDto` and `NoteDto` gain `fields`, `labels`, `properties`; incident and soak-test registered first; `GenericReader` draws `fields`. The classifier is not touched. |

### Workspace
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **N4** | ⬜ | Tree, breadcrumbs, folder view, spaces, scoped search | N3 | med | sonnet/high | | Folder pages are `<folder>/<folder>.md`; `/notes?path=` keeps working for pages and folders; new `pathPrefix` filter in `query/builder.ts`; search scope widens beyond `notes`. |
| **N5** | ⬜ | Templates | N4 | low | sonnet/medium | | Built-ins in `src/edit/templates/notes/`, user templates in `Notes/_templates/` (hidden); `createNote(template)`, existing `fill()`. |
| **N6** | ⬜ | Labels and page properties | N3, N4 | med | sonnet/high | | Raw-text `tags:` editor that refuses what it cannot round-trip; label chips, `?label=` browse, read-only properties table; page sections for children, labels, properties, backlinks. |
| **N7** | ⬜ | Editor insert menu and toolbar | N1 | low | sonnet/medium | | Slash source in the `[[` completion `override`, toolbar row; entries from the block registry. |

### History and attachments
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **N8** | ⬜ | Page history: versions, diff, restore | N4 | med | sonnet/high | | `git` via `execFile` args array, `GIT_NO_LAZY_FETCH=1`, timeouts, missing blobs tolerated (the VM clone is partial); validated path and sha; diff through `unified-diff.ts` + `SplitDiffFile`; restore is a normal user-initiated save. Security lens in review. |
| **N9** | ⬜ | Attachments: upload, serve, embed | N4, N7, G1 | **high** | opus/high | | JSON+base64 upload (write guard unchanged), magic-byte allowlist (png, jpeg, gif, webp, pdf), hash-named under `Notes/_attachments/`, serve route with fixed content types, `nosniff`, CSP `sandbox`, `![[x.png]]` renders an image, paste and drop. **Opus tier: the session halts here if it is not opus.** |

### Typed spaces and records
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **N10** | ⬜ | Typed spaces: Incidents and Soaks | N3, N4, N8 | low | sonnet/medium | | Spaces in the switcher, typed headers, read-only history, lists stay on their dashboards. |
| **N11** | ⏸ | Live blocks: children and properties report | N1, N6 | med | sonnet/high | | Deferred: index-dependent output must be in the render-cache key; the plan is placeholder blocks hydrated by the SPA. Revisit after N10. |
| **N12** | ⬜ | Records: CLAUDE.md, docs, close-out | N1, N2, N3, N4, N5, N6, N7, N8, N10 | low | sonnet/low | | CLAUDE.md invariants (registries, attachments, history, the Notes/ boundary), `docs/notes/README.md`, programme close-out. |

## Gates
<!-- A precondition that is NOT a unit. -->
- [ ] **G1 — Attachment policy confirmed** — blocks N9. Harry confirms the cap (default 5 MB per file), the allowed types (default png, jpeg, gif, webp, pdf; never svg or html), hash-named storage under `Notes/_attachments/`, and that the vault's git (a 207 MB repo, pushed with no size check) may grow with images.

## Risks
- **R1 ★ The block refactor changes how existing documents render** — the golden corpus (every doc of a scratch vault clone, before and after, sha256 equal) gates N1; `RENDERER_VERSION` is not bumped; static imports only (`source-hash.ts:27-45`) — open.
- **R2 ★ Uploads** — traversal, type confusion and script via svg/html, vault growth. Mitigations: JSON+base64 so the write guard is unchanged, magic-byte allowlist, fixed extension-to-type map, `nosniff`, CSP `sandbox`, hash-named files, size cap (G1), security lens in review, opus tier — open.
- **R3 ★ Vault ownership** — the app writes only `Notes/<…>.md` (and, from N9, attachments under `Notes/_attachments/`); typed spaces are read-only; `.knowledge/config.yaml` is not edited; no existing vault file is moved. Tests use scratch clones, never the real vault — standing.
- **R4 Git history on a partial clone** — 349 blobs are missing locally; commits are machine syncs; renames are only found by content similarity. Mitigation: `GIT_NO_LAZY_FETCH=1`, timeouts, "version not available locally", args array and validated path and sha — open.
- **R5 Render-cache correctness** — output that depends on the index must be part of the cache key. v1 keeps such data in SPA page sections, not in the cached HTML; N11 is deferred for this — standing.
- **R6 Raw YAML editing** — a label edit could corrupt frontmatter. The editor edits text only, round-trip tests cover the forms in the vault, and it refuses what it cannot round-trip — open.
- **R7 Classification is by folder** — Notes pages cannot be typed by frontmatter through the classifier; the registry reads `kind:` for Notes — standing.
- **R8 External lint mirror drifts** — `orient-writers/skills/explain/lint-explainer.mjs` already lacks `person`, and `diagram-rules.mjs` is untracked there. Harry's repo; N1 exports a manifest — open.
- **R9 Scope creep** — comments, WYSIWYG and permissions are out; each would be its own programme — standing.

## Decision log
<!-- Dated, newest first. -->
- **2026-11-11** — **Programme opened.** Harry: turn Notes into a Confluence clone that handles the usual renderer and is extensible for soaks, incidents and the like; merge or trash Diagrams because he wants a C4 whiteboard with embeddable components later. Answers: scope **core wiki** (tree, breadcrumbs, child lists, templates, labels and properties, history from the vault's git, attachments; no comments, WYSIWYG or permissions); soaks and incidents **typed pages in place** (a page-type registry; their files stay where the skills write them); Diagrams **trash it now** (the builder UI and API go, the renderer's diagram blocks and presets stay because they draw existing explainers and C4 notes and are the whiteboard's future embed format); approach **plan, then build** (units are built, reviewed and deployed in turn, as with Retire). Research: three read-only passes (document model, write path and attachments, git history and the renderer's blocks) are cited in [[orient Notes/Design|Design]]. Planning tier is sonnet/high; N9 (uploads) rates opus/high, so the session stops there unless it is opus.

## Scar tissue
<!-- Do not change, and why. -->
- Vault ownership (orient `CLAUDE.md`, "The one rule"): never move, rename or rewrite an existing vault file except through a user-initiated editor save; never re-serialise YAML; never create `.md` at `Engineering/<svc>/` root. The Notes workspace only widens what `Notes/` can hold.
- The write guard (loopback Origin, `X-Orient: 1`, JSON) is not relaxed for uploads: attachments travel as JSON with base64.
- `checkNotePath` refuses dot-prefixed and empty segments (`src/edit/notes.ts:55-82`): structural folders are underscore-prefixed (`_templates`, `_attachments`).
- A document's type is folder-derived and Notes/ is always `note` (`classify.ts:322-323`): do not make the classifier read frontmatter for it.
- `source-hash.ts:27-45` follows static imports: registries are static, never `import.meta.glob` or dynamic imports.
- Anything a rendering reads besides its own text belongs in the render-cache key.
- The renderer's diagram presets, `explainer-blocks` and `flow-layout` are not builder code: they draw existing documents.
- Gates run on a quiet host (load under ~3); at load above ~15 UI timing tests flake. Browser UI tests on the VM need `PLAYWRIGHT_BROWSERS_PATH=$HOME/.cache/orient-pw`.
- `wp programme new` needs `python3 ~/.claude/waypoint/wp.py` (the `~/.local/bin/wp` symlink looks for its templates next to itself).
