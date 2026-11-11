---
title: orient Notes — Migration State
programme: orient-notes
status: active
owner: hjf
services:
- orient
created: '2026-11-11'
updated: '2026-11-11'
tags:
- bifrost
- migration-state
---
# orient Notes — Migration State

<!-- The single source of truth for PROGRESS. The Overview carries the narrative and the verdict;
     this doc is the live ledger a session reads to know what is done and what is next.
     `wp programme status/next/tick` read and write the unit tables below, so keep the table
     shape intact. The shape of the work: [[orient Notes/Design|Design]]. -->

orient has no PRs or CI: a unit ships as commits on `master`, pushed, then deployed (`pnpm deploy:all`, a named sha). The `PR` column holds the commit range. Builders are sonnet, at most 3 at once in the shared checkout, no worktrees; every unit is reviewed with review-panel before it deploys.

## Unit status
Legend: ⬜ not started · 🟨 in progress · ✅ merged · ⛔ blocked · ⏸ deferred · ❌ dropped · 🔄 rescoped

Sequencing (Design §7): strictly in series N0 → N1 → (N2, N3: either order, never together) → N4a → N4b → N5 → N6 → N7; N8 may run beside N7 only after the lead checks the file lists are disjoint; N9a → N9b → N9c in series. Units share hot files and `git commit -- <paths>` only protects whole files.

### Foundations
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **N0** | ✅ | Golden harness for the renderer and its other consumers | | med | sonnet/high | 73bd0e7..c85ecdc | `scripts/render-golden.ts`: per-doc sha256 of `renderHtml`, `prepareDocument()` entries and findings, `parseNeeds`, health parse, `isWideSource`; counts per fence kind asserted; synthetic fixtures for all six blocks incl. every invalid-block message, `drift`, `serviceHrefs`, `renderInlineHtml`, `.mdx`; deterministic across two runs; baseline from a committed sha via `git archive`, never the live checkout; test that `rendererSourceFiles()` covers every `src/render/blocks/*` file. |
| **N1** | ✅ | Block registry, behaviour-preserving | N0 | med | sonnet/high | 9a43c4f..3eae2c5 | One `BlockSpec` per block (`parse` keeps `{ok, block}`; `starters` is a list) replaces the if-chain at `html/blocks.ts:195-236`, the duplicated `parse` helper and the five regexes (incl. `validate-blocks.mjs:92`, `evidenceRef.ts:16`); static imports only. N0's goldens must match; `RENDERER_VERSION` unchanged; exports a block manifest. |
| **N2** | ✅ | Delete the Diagrams builder | N1 | low | sonnet/medium | e42d19a..8c93c87 | Page, `DiagramEditor`, `knowledge/diagrams.ts`, `ops/diagrams.ts`, DTOs, query, `appendToNote(Op)` and its two tests, nav entry (4 places), tests (exact ranges in Design N2). `/diagrams` answers 308 to `/notes`. Extract `ui-nav.ts` grouping into a function so a stale slug in the vault's nav config is pinned harmless. Presets, `diagram-lint`, `explainer-blocks`, `flow-layout`, `html/diagrams` stay. |
| **N3** | ✅ | Page-type registry and typed chrome | N1 | med | sonnet/high | 742e2d8..8cf2712 | `src/domain/page-types.ts` (`note` matches only `area notes`; `kind:` for Notes); `fields`, `labels`, `properties` on `NoteViewDto` and `DocHeaderDto`; incident and soak-test first (fields from typed `meta`); `GenericReader` draws them. Do not touch `entity-href.ts` or the renderer's import graph. |

### Workspace
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **N4a** | ⬜ | Pages read model | N3 | med | sonnet/high | | `isStructuralPath()` allowlist (`Notes/_templates`, `Notes/_attachments`) used by the indexer (new skip reason), `listNotes`, link resolver, `suggestLinks`, `backlinksOf`, search; known image embeds resolve as assets (no LINK-UNRESOLVED); sensitivity exclusion; path-range helper; tree, children, breadcrumb DTOs in `api/types/pages.ts`; `core/modules/pages/{tree,page}.ts`; ambiguity fixture for folder notes. |
| **N4b** | ⬜ | Workspace shell (SPA) | N2, N4a | med | sonnet/high | | `ui/src/lib/workspace/` with slot components (`PageSections`, `NewPageMenu`, `HistoryTab`); rewrites `notes/+page.svelte` once; tree, breadcrumbs, folder view, space switcher, scoped search; `/notes?path=` keeps working for pages and folders. |
| **N5** | ⬜ | Templates | N4b | low | sonnet/medium | | `src/edit/note-templates.ts`: built-ins + `Notes/_templates/` via `pathSafety` (symlink refusal, size cap), template = validated slug; `fill()` exported and quotes YAML scalars; core `Create` schema widened; test against manifest rename inheritance. |
| **N6** | ⬜ | Labels and page properties | N5 | med | sonnet/high | | Raw-text `tags:` editor (first `\n---\n` split, missing block and missing key, flow/block/scalar forms, refuses what it cannot round-trip, `Notes/` only, through `saveNote` with a base hash); `DocumentQuery.tags` source option; chips, `?label=`, properties table. |
| **N7** | ⬜ | Editor insert menu, toolbar, preview lint | N1, N6 | low | sonnet/medium | | Slash source in the `[[` completion `override`, toolbar row; entries from the registry's `starters`; the preview shows the registry's `lint` findings (raw JSON, so mistakes the schema rejects are still reported). **Carry-over from N1 review:** the data and action starters use `kind: "table"` and `"tasks"`, which are not registered, so a saved starter raises a BLOCK-INVALID info finding and indexes sample `data-row` entries; register them (`DISPLAY_ONLY_KINDS`, `ACTION_KINDS` in `block-schemas.ts`) with a golden run first, and add a test that every data and action starter has a registered kind. Editing lint or starter files changes `rendererSourceHash` (the registry imports them): one cold render-cache miss per deploy. |

### History and attachments
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **N8** | ⬜ | Page history: versions, diff, restore | N4b | med | sonnet/high | | `GIT_LITERAL_PATHSPECS=1`, `GIT_OPTIONAL_LOCKS=0`, `GIT_NO_LAZY_FETCH=1` with a version check, `--` before paths, no `--follow`, rev-parse every sha and require it in the path's log, commits only, plain `execFile` (no `runJson` cache), read-only path validator, sensitive excluded; diff cut at the first `@@`, `--numstat` counts, `SplitDiffFile`; restore is a normal `saveNote`. Security lens in review. |
| **N9a** | ⬜ | Attachment store and serve route | N4b, N7, G1 | **high** | opus/high | | `frameGuard` stops clobbering CSP (test through `createCore().app.request`); `resolveAttachmentPath`, `atomicWriteBytes` that never replaces; serve route: strict name, `lstat`, magic bytes and size re-checked each read, fixed type map (png, jpeg, gif, webp), `nosniff`, CORP, CSP `sandbox`, ETag + `no-cache`, never `serveStatic`. **Opus tier: the session halts here unless it is opus.** |
| **N9b** | ⬜ | Upload route | N9a | **high** | opus/high | | JSON + strict base64 through the unchanged write guard, per-route `bodyLimit`, decoded-length cap, extension from magic bytes, 64-hex sha256 name, total quota, no auto-delete. |
| **N9c** | ⬜ | Embed, paste and drop | N9b | med | sonnet/high | | `![[<stored name>]]` only; renderer maps only strictly matching names, never reads disk; `RENDERER_VERSION` bump; paste and drop; attachments section; CLAUDE.md attachment invariants. |

### Typed spaces and records
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **N10** | ⬜ | Typed spaces: Incidents and Soaks | N3, N4b, N8 | low | sonnet/medium | | Explicit space allowlist (Notes, Incidents, Soaks), typed headers, read-only history, lists stay on their dashboards; sensitivity excluded in the shared read model. |
| **N11** | ⏸ | Live blocks: children and properties report | N1, N6 | med | sonnet/high | | Deferred: index-dependent output must be in the render-cache key; plan is placeholder blocks hydrated by the SPA. Revisit after N10. |
| **N12** | ⬜ | Records: CLAUDE.md, docs, close-out | N1, N2, N3, N4b, N5, N6, N7, N8, N9c, N10 | low | sonnet/low | | CLAUDE.md (registries, history, the Notes/ boundary), `docs/notes/README.md` (how to add a block, how to add a page type), programme close-out. |

## Gates
<!-- A precondition that is NOT a unit. -->
- [ ] **G1 — Attachment policy confirmed** — blocks N9a. Harry confirms: 5 MB per file; png, jpeg, gif, webp only (never svg, html or pdf); full 64-hex sha256 names under `Notes/_attachments/`; a 200 MB total quota; nothing auto-deleted; that the vault's git (207 MB, pushed with no size check) may grow with images; and that the three `Pasted image*.png` already at the vault root stay unrendered (Obsidian's attachment folder is Harry's config).

## Risks
- **R1 ★ The block refactor changes how existing documents render** — N0's goldens (render output, index entries and findings, `today`/`health` parses, invalid-block messages, the render-cache source hash) gate N1; `RENDERER_VERSION` is not bumped; static imports only — open.
- **R2 ★ Uploads and stored XSS** — a same-origin script on :3000 reaches the PR-approve and Slack-post routes. Mitigations: `frameGuard` stops overwriting route CSP (N9a, tested), images only, magic-byte allowlist and extension from detected type, fixed type map, `nosniff`, CORP, CSP `sandbox`, `lstat` and re-validation on every read (files also arrive via git), ETag not `immutable`, never `serveStatic`, JSON+base64 so the write guard is unchanged, quota, opus tier, security lens — open.
- **R3 ★ Vault ownership** — the app writes only `Notes/<…>.md` plus, from N9, hash-named images that are never replaced, under `Notes/_attachments/`; `WRITABLE_EXTENSIONS` is not widened; typed spaces get no workspace editing; `.knowledge/config.yaml` is not edited; no existing vault file is moved; tests use scratch clones — standing.
- **R4 ★ History reads the vault's git** — option and pathspec injection, scope escape through rename-following, a partial clone with 349 missing blobs, racing vault-sync's `git add -A`. Mitigations in N8 (literal pathspecs, `--`, rev-parse every sha, commits only, optional locks off, no lazy fetch with a version check, no `--follow`, no cache, validated read-only paths, sensitive excluded) — open.
- **R5 Render-cache correctness** — output that depends on the index must be part of the cache key; v1 keeps such data in SPA sections, N11 is deferred for this; the attachment embed depends only on text — standing.
- **R6 Raw YAML editing** — a label edit could corrupt frontmatter; text edit only, round-trip tests for the forms in the vault, refuses what it cannot round-trip — open.
- **R7 Classification is by folder** — Notes pages cannot be typed through the classifier; `note` is also a catch-all; the registry reads `kind:` and guards on area — standing.
- **R8 The external lint mirror drifts** — `orient-writers/skills/explain/lint-explainer.mjs` lacks `person`; `diagram-rules.mjs` is untracked there; `scripts/validate-blocks.mjs` mirrors the schemas inside this repo. N1 pins the in-repo mirror with a test and exports a manifest — open.
- **R9 Scope creep** — comments, WYSIWYG, permissions and non-image attachments are out; each would be its own programme — standing.
- **R10 Collisions in the shared checkout** — units share hot files and `git commit -- <paths>` only protects whole files. Serial sequencing, a `core/modules/pages/` and `api/types/pages.ts` layout, slot components, at most 3 builders and normally 1 to 2 — standing.
- **R11 Structural paths leak into the index** — templates and attachments indexed as notes would add ghost pages, backlinks and link findings. `isStructuralPath()` in the indexer plus tests in N4a; `_heap` and other `_` folders stay content — open.
- **R12 Sensitive documents surface through a new read model** — `Bifrost/HR`, `Bifrost/Team`, `Interviews` excluded in the shared read model (tree, labels, search, history), pinned by tests — open.
- **R13 Vault growth** — every attachment is committed and pushed. Size cap, quota, never auto-delete (G1) — open.

## Decision log
<!-- Dated, newest first. -->
- **2026-11-11** — **N2 done and live at 8c93c87** (e42d19a, 0df8a4d, 8c93c87; 23 files, +104/−891 before the review fixes). The Diagrams builder is gone: route, `DiagramEditor`, `knowledge/diagrams.ts`, `ops/diagrams.ts`, the DTOs, `diagramsQuery`, `appendToNote`/`appendToNoteOp` and its `MAX_APPEND`, the nav entry, and the tests that only covered them. Nothing under `src/render/` changed; the diagram blocks, presets, lint and layout stay. `/diagrams`, `/diagrams/` and `/diagrams/<x>` answer 308 to `/notes` (added to the existing `legacyRoutes` list); `/api/v1/diagrams*` answers the core's JSON 404; the health module list no longer has `diagrams`. `railGroups(configured, views = NAV)` now holds the rail's grouping so a test can pin it; the vault's `diagrams` and `tools` slugs are dropped silently and Harry's config is untouched. Two reviewers (backend, frontend): the redirect missed a trailing slash and sub-paths (a fall-through to the not-found page; fixed, and the new tests fail with the route removed), and several `railGroups` tests held two behaviours (split). `/tools/<x>` and `/team/` have the same trailing-slash gap, left alone. Gates on 8c93c87: typecheck clean, lint 47 baseline, ui:check 0/0, 7,846 tests pass. Builder discrepancies, all benign: `entity-href.test.ts` lives under `tests/unit`; `config.test.ts` needed no edit; `pnpm ui:nav` writes unformatted JSON, so `biome format` ran on `nav.generated.ts`. Seen under load only, green alone ×3: `today.test.ts` and `usage.test.ts` (the suite ran beside two reviewers). Chord `D` is free.
- **2026-11-11** — **N1 done and live at 3eae2c5** (9a43c4f..3eae2c5, pushed). Final gates on that head: typecheck clean, lint at the 47 baseline, ui:check 0/0, ui:build clean, 7,861 tests pass (no flakes), both goldens identical to the pre-N1 baseline (27 fixtures, 1,398 real documents). Deployed with `pnpm deploy:all`; one cold render-cache miss expected because `rendererSourceHash` changed (`RENDERER_VERSION` did not). Browser tour (explainers, digests, health, decisions, systems, eight doc pages with tables and SVGs, writes aborted): no errors. Review fixes after the first panel: registry typing (`BlockSpec<T, N extends FenceName>`, no default, `satisfies`), `lint` takes raw JSON, five fence sites pinned to the registry by table-driven tests, a fences-in-context fixture, tests that could not fail removed. Open and not N1's: the Systems page links `carrier-integrations`, `ecm` and `selector` to `/service/<name>`, which answers "No service called …" (parcel-portal and connectors-dpd resolve); `serviceOverview` reads Engineering/ facts, not touched here.
- **2026-11-11** — **N0 done (73bd0e7..c85ecdc), N1 built and in review.** N0: `scripts/render-golden.ts` + `.sh` (a baseline or after state from a committed sha via `git archive`, per-document hashes of render, reader, inline render, index entries and findings, `today`/`health`/wide consumers; refuses the real vault; deterministic: two runs byte-identical over 1,398 documents), 26 fixture documents with a checked-in `golden.json`. N1 (9a43c4f, a66a503, bb90fa4): `src/render/blocks/` (registry, one shared `parseBlock`, starters, manifest) and `src/render/html/block-renderers.ts` (an exhaustive renderer table); the five fence sites derive their names from the registry. Both goldens identical to the pre-N1 baseline (26 fixtures, 1,398 real documents). Two reviewers found no behaviour change; fixes in flight: registry typing (a loosely typed seventh block would have silently dropped the exhaustiveness check), `lint` over raw JSON (the old builder's behaviour), the harness's fence list pinned to the registry, table-driven fence-site tests, a fences-in-context fixture. Known flakes seen on a quiet host: `ticket-run-cycle` and `headless-scope` (green alone).
- **2026-11-11** — **Plan revised after two adversarial reviews** (factual grounding; sequencing, vault ownership and security). No unit was un-buildable, but: N0 split out as a deterministic golden harness; N9 became N9a/b/c, images only, behind a kernel fix because `frameGuard` replaces any route-level CSP (verified at `guards.ts:90-94`); structural folders are a fixed allowlist the indexer skips (`_heap` is real content); N8 hardened; N4 split into a read model and a shell, with slot components and a `core/modules/pages/` layout; N5 to N7 and N2/N3 run in series; N3 follows N1. Eight smaller corrections to claims and citations. The Design (revision 2) lists them. G1 now covers the revised attachment policy.
- **2026-11-11** — **Programme opened.** Harry: turn Notes into a Confluence clone that handles the usual renderer and is extensible for soaks, incidents and the like; merge or trash Diagrams because he wants a C4 whiteboard with embeddable components later. Answers: scope **core wiki** (tree, breadcrumbs, child lists, templates, labels and properties, history from the vault's git, attachments; no comments, WYSIWYG or permissions); soaks and incidents **typed pages in place** (a page-type registry; their files stay where the skills write them); Diagrams **trash it now** (the builder UI and API go, the renderer's diagram blocks and presets stay because they draw existing explainers and C4 notes and are the whiteboard's future embed format); approach **plan, then build** (units are built, reviewed and deployed in turn, as with Retire). Research: three read-only passes cited in [[orient Notes/Design|Design]]. Planning tier is sonnet/high; N9 (uploads) rates opus/high, so the session stops there unless it is opus.

## Scar tissue
<!-- Do not change, and why. -->
- Vault ownership (orient `CLAUDE.md`, "The one rule"): never move, rename or rewrite an existing vault file except through a user-initiated editor save; never re-serialise YAML; never create `.md` at `Engineering/<svc>/` root. The workspace only widens what `Notes/` can hold.
- The write guard (loopback Origin, `X-Orient: 1`, JSON) is not relaxed for uploads: attachments travel as JSON with base64.
- `frameGuard` (`guards.ts:90-94`) sets `Content-Security-Policy` after the route, replacing any the route set: fix it before any route relies on its own CSP.
- `WRITABLE_EXTENSIONS` (`config.ts:138`) gates the generic `saveDocument` as well as notes: never add an image extension there. `atomicWrite` replaces its target: attachments use a never-replace writer.
- `checkNotePath` refuses dot-prefixed and empty segments (`edit/notes.ts:55-82`): structural folders are underscore-prefixed, and only the allowlisted two are structural (`_heap` is content).
- A document's type is folder-derived and Notes/ is always `note` (`classify.ts:323`); `note` is also the catch-all. Do not make the classifier read frontmatter for it.
- `source-hash.ts:27-45` follows static imports: registries are static, never `import.meta.glob` or dynamic imports.
- Anything a rendering reads besides its own text belongs in the render-cache key.
- `adapters/exec.ts`'s `runJson` caches stdout in memory and on disk: never use it to read vault content.
- Bare `[[Architecture]]` is ambiguous in this vault (39 `architecture.md`, 67 `overview.md`): the app writes path-qualified links to folder pages.
- The renderer's diagram presets, `explainer-blocks` and `flow-layout` are not builder code: they draw existing documents.
- Gates run on a quiet host (load under ~3). Browser UI tests on the VM need `PLAYWRIGHT_BROWSERS_PATH=$HOME/.cache/orient-pw`.
- `wp programme new` needs `python3 ~/.claude/waypoint/wp.py` (the `~/.local/bin/wp` symlink looks for its templates next to itself).
