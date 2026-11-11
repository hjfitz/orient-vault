---
title: "orient Notes — Design"
status: planning
owner: "hjf"
services: ["orient"]
created: "2026-11-11"
updated: "2026-11-11"
tags: [bifrost, design]
---
# orient Notes — Design

Progress is in [[orient Notes/Migration State|Migration State]]; the why is in [[orient Notes/Overview|Overview]]. This doc is the shape: what exists, the model, the two registries, the units. Every claim about the code cites `file:line` from the 2026-11-11 research (three read-only passes over `~/projects/orient` at `6445727`, plus the vault's git).

## 1. Goal and non-goals

**Goal.** Turn Notes into a Confluence-style workspace over the vault: a page tree with breadcrumbs and child lists, templates, labels and page properties, page history with diff and restore, attachments, and two registries that make it extensible: a **block registry** (renderer) and a **page-type registry** (soaks, incidents and the rest). The Diagrams page is deleted: its builder goes, the renderer's diagram blocks stay, because they are the embed format a future C4 whiteboard writes.

**Non-goals (v1).** Comments, WYSIWYG, per-page permissions, moving any existing vault file, the whiteboard itself, and folding the other page kinds (decisions, plans, systems…) into the workspace. The registry is the vehicle for that later.

## 2. What exists (the facts the design stands on)

| Area | Fact | Where |
| --- | --- | --- |
| Hierarchy | The tree is built from path segments, nothing else. `listNotes()` returns only `{id, path, title}`. | `src/lib/note-tree.ts:16-37`, `src/domain/notes.ts:9-27` |
| Writes | The app writes `Notes/<segments>/<name>.md` only. Dot-prefixed or empty segments, a non-`.md` name, `..` and symlink escapes are refused. `atomicWrite` takes strings only. | `src/edit/notes.ts:55-99`, `src/edit/pathSafety.ts:54-124`, `src/edit/atomicWrite.ts:9-34`, `src/config.ts:138` |
| Create | A new note is `# <title>\n\n`: no frontmatter, no id (ids come from the manifest, not the file). The body is hard-coded where a template would plug in. | `src/edit/notes.ts:132-163`, `src/content/manifest.ts:103-106` |
| Templates | `TEMPLATES = ['decision','inbox','tool']` with `{{title}} {{date}} {{slug}} {{service}} {{ticket}}` filling; only tests call `createDocument`. None is for Notes. | `src/edit/save.ts:84,195-241,446-454` |
| Types | A document's `type` comes from its folder (30 path rules); **Notes/ is always `note`, whatever its frontmatter says**. Incidents, Soaks, Support, Monitors, Tasks, Maintenance map from their folders. 22 types, closed enum. | `src/content/classify.ts:264-443,322-323`, `src/domain/types.ts:10-33` |
| Tags | Frontmatter `tags:` is indexed (`tags` table) and queryable (`DocumentQuery.tags`), but no op or UI uses the filter. `NoteDto` and `DocHeaderDto` carry no tags or frontmatter. | `src/index/schema.sql:85`, `src/domain/types.ts:649`, `src/api/types/notes.ts:19-28`, `src/api/types/doc.ts` |
| Readers | No registry. A typed header means a new `Reader` DTO variant, a builder, a branch in `readerFor`, and a branch in the page. Incident, soak, decision and system use the generic reader plus a bespoke list page. | `src/ops/doc.ts:122-131`, `ui/src/routes/doc/[id=docId]/+page.svelte:63-77`, `src/domain/incident.ts:73-86`, `src/domain/soak-tests.ts:133-140` |
| Search | FTS over documents and entries; the only scope is `notes`. The domain layer already accepts type, area, container, tags, status and a path-LIKE filter; ops and UI expose only `area`. | `src/ops/search.ts:67-125`, `src/domain/search.ts:63` |
| Blocks | Dispatch is an if-chain on the fence language; adding a block touches about ten places (parse, schema, lint, render, four hand-written regexes, tests, the external lint mirror, `RENDERER_VERSION`). `source-hash.ts` follows **static** imports only. | `src/render/html/blocks.ts:195-236`, `src/render/md/explainer-blocks.ts:207-210`, `src/render/md/orient-blocks.ts`, `src/content/entries.ts:1014`, `src/ops/doc-readers.ts:31`, `src/domain/health.ts:210`, `src/domain/today.ts:124`, `src/render/html/source-hash.ts:27-45` |
| Images | `![](url)` renders as `<img>`; `![[file]]` becomes an embed wikilink drawn only as a link; `safeHref` allows http(s), mailto, obsidian, relative; there is **no route that serves a vault file**, no `img-src` policy, no `nosniff`. | `src/render/md/pipeline.ts:62`, `src/render/md/plugins/wikilink.ts:6-46`, `src/render/html/blocks.ts:60-66`, `src/lib/safe-href.ts:9-15`, `src/core/kernel/guards.ts:90-94` |
| Write guard | Every non-safe request needs loopback Origin, `X-Orient: 1` and `application/json`; a multipart or binary POST gets 415. No route takes `formData` or bytes. | `src/core/kernel/guards.ts:54-84` |
| Vault git | The vault is its own repo, a **partial clone** (`blob:none`): 349 blobs are missing locally and `git log --follow -p` can die fetching one. Sync commits (`sync: vm <ts>`) arrive about every 90 s, so history granularity is seconds-to-minutes. `git log --follow` on the busiest file takes 0.08 s. Any file under `Notes/` is committed and pushed with no size limit; no LFS. | `scripts/vault-sync.sh:74-106`, `systemd/orient-vault-sync.timer:4-5`, `.git/config` |
| Editor | CodeMirror with a `[[` completion `override`; the toolbar is plain Svelte; preview posts to `/api/v1/editor/note/preview`. | `ui/src/lib/editor/Editor.svelte:136-200`, `src/ops/note-edit.ts:145-153` |
| Diff UI | `SplitDiffFile.svelte` takes `{filename, status, additions, deletions, patch}`; the parsers are `src/lib/unified-diff.ts` and `split-diff.ts`. | `ui/src/lib/delivery/tickets/SplitDiffFile.svelte`, `src/lib/unified-diff.ts:24,163` |
| Diagrams | The builder is `ui/src/routes/diagrams`, `DiagramEditor.svelte`, `knowledge/diagrams.ts`, `ops/diagrams.ts`, DTOs, a query, a nav entry in four places, tests; the renderer needs `diagram-presets.ts`, `explainer-blocks.ts`, `flow-layout.ts`, `html/diagrams.ts`. | see N2 |

## 3. The model

- **Spaces.** `Notes` is the authored space (editable). Typed spaces (`Incidents`, `Soaks`, later Decisions, Systems…) are read-only windows onto vault folders that skills and `wp` write; their files never move.
- **Pages and folders.** A page is a markdown file; the folder is the hierarchy. A folder's own page is `<folder>/<folder>.md` (the Obsidian folder-note convention), so `[[Architecture]]` resolves naturally; a folder with no folder note shows an automatic child list. Folders whose name starts with `_` (`_templates`, `_attachments`) are structural: hidden from the tree, search and labels. (`.`-prefixed folders cannot be written by the app at all.)
- **Labels and properties.** Labels are frontmatter `tags:`. Properties are the rest of the frontmatter, shown as a table. Editing a label edits the raw frontmatter text (never re-serialise YAML: unknown keys must survive byte for byte).
- **Typed pages.** The classifier decides `document.type` from the folder and is not touched. The page-type registry sits above it: it maps `document.type` (and, for pages under `Notes/`, a frontmatter `kind:` key) to a header (`fields`), a list view, and what may be created or edited.
- **Version history.** The vault's git, read-only: the sync commits that touched the path.
- **Embeds.** Fenced `orient-*` blocks and image attachments. The whiteboard will write the same fences.

## 4. The two registries

**Block registry** (`src/render/blocks/`, static imports only):

```ts
type BlockSpec<T> = {
  name: `orient-${string}`                        // the fence language
  label: string                                   // the editor's insert menu entry
  parse(text: string): { ok: true; data: T } | { ok: false; error: string }
  lint?(data: T): Finding[]                       // flow and sequence adopt diagram-lint.ts
  render(data: T, ctx: RenderCtx): Hast | null    // null drops the node (action lists)
  starter(): string                               // what the insert menu pastes
}
type DocumentLint = (blocks: ParsedBlock[]) => Finding[]   // BLUF at most one, evidence ids cited
```
The six blocks (bluf, evidence, flow, sequence, data, action) move behind it with **byte-identical output**; the four hand-written regexes become `BLOCK_NAMES`; `blocks.ts:195-236` becomes one lookup. Non-HTML consumers (`today.ts`, `health.ts`) import `parse` without the HTML side.

**Page-type registry** (`src/domain/page-types.ts`, plus an SPA map for optional bespoke headers):

```ts
type PageType = {
  id: string                                  // 'note' | 'incident' | 'soak-test' | …
  documentTypes: DocumentType[]               // what the classifier calls it
  notesKind?: string                          // frontmatter kind: under Notes/
  label: string; folder?: string; listHref?: string
  editable: boolean                           // only 'note' in v1
  fields(doc): HeaderField[]                  // chips: status, severity, dates, links
  templates?: TemplateRef[]
}
```
Registered statically. v1 registers `note`, `incident` (reference, severity, is_us, declared/resolved times, minutes to resolve, incident.io and Slack links) and `soak-test` (status, programme, unit, started, next checkpoint, verdict, subject and monitor counts). Fields come from the index's typed `meta`, not raw frontmatter. Adding a type later = one file + one line in the registry + (if it has a folder) a space entry.

## 5. API and URLs

URLs are a durable contract (vault links point at them): `/notes?path=` stays, for pages **and folders**; the rest is additive and lives in the URL (CLAUDE.md: every view state lives in the URL): `?view=history|diff`, `&from=&to=` (shas), `?label=`, `?space=`, `?template=`. `/diagrams` answers 308 to `/notes`.

Core (loopback, write guard unchanged): `GET /api/v1/pages/tree?space=`, `GET /api/v1/pages/page?path=` (header fields, labels, properties, html, children, breadcrumbs, backlinks, attachments), `GET /api/v1/pages/versions|version|diff`, `POST /api/v1/pages/create` (with `template`), `POST /api/v1/pages/labels`, `POST /api/v1/pages/restore`, `POST /api/v1/attachments` (JSON + base64), `GET /api/v1/attachments/<name>`. The existing `/api/v1/notes/*` and `/editor/*` routes keep working until the SPA has moved over.

## 6. The units

**N1 Block registry** (behaviour-preserving). Before touching anything, a golden-corpus harness: `scripts/render-golden.ts` renders every document of a scratch vault clone with `renderHtml` and records sha256s (snapshot kept outside the repo); after the refactor the snapshot must match exactly, `RENDERER_VERSION` stays, `rendererSourceHash` is allowed to change. Touch: `blocks.ts:195-236`, `explainer-blocks.ts:189-210` and `orient-blocks.ts:63-85` (the duplicated `parse` helper becomes one), `block-schemas.ts`, `explainer.ts`, `diagrams.ts`, `actions.ts`, the four regexes, tests. `diagram-lint.ts` becomes the flow/sequence `lint`. The external mirror `orient-writers/skills/explain/lint-explainer.mjs` is Harry's repo: it already drifts (its `NODE_KINDS` lacks `person`; `diagram-rules.mjs` is not tracked there). N1 exports a block manifest (names, schema keys) so that mirror can be generated later; adopting it is Harry's call.

**N2 Delete the Diagrams builder.** Delete: `ui/src/routes/diagrams/+page.svelte`, `ui/src/lib/knowledge/DiagramEditor.svelte`, `src/core/modules/knowledge/diagrams.ts` (mounted in `waves/w-d2.ts:2,17`), `src/ops/diagrams.ts`, `Diagram*Dto` (`src/api/types/knowledge.ts:182-212`), `diagramsQuery`, `'diagrams'` in `src/api/migrated/w-d2.ts:10`, `diagramHref` and the "draw a diagram" link (`notes/+page.svelte:54`), `appendToNote(Op)` if nothing else calls it, the nav entry in `navigation.ts:414-421`, `config.ts:164`, `nav.generated.ts` (regenerate with `pnpm ui:nav`), and the tests (`core-knowledge.test.ts:318-420`, `ui/tests/knowledge.test.ts`, `routing.test.ts:155-158`, `entity-href.test.ts:114-128`). Keep: `diagram-presets.ts` (minus the builder-only exports; `STARTERS` becomes the registry starters), `explainer-blocks.ts`, `flow-layout.ts`, `html/diagrams.ts`. `/diagrams` redirects to `/notes`. The `diagrams` slug in the vault's `.knowledge/config.yaml:31` is Harry's config: left alone (a stale slug must be harmless: N2 adds a test for that).

**N3 Page-type registry and typed chrome.** `src/domain/page-types.ts` as in §4; `DocHeaderDto` and `NoteDto` gain `fields`, `labels`, `properties`; `GenericReader.svelte`'s chip line renders `fields`; `readerFor` (`ops/doc.ts:122-131`) is untouched except to pass the fields. Incident and soak-test are the first two registrations (they keep their dashboards as list views).

**N4 Workspace shell.** Tree with folders and pages (collapse state in the URL), breadcrumbs (each segment links to the folder page or the folder view), folder view (folder note above an automatic child list), space switcher (Notes + typed spaces linking to their lists), a search box scoped to the space (`ops/search.ts` takes `scope` today only for `notes`; widen it to folder and label using the filters the domain already has). Touch: `ui/src/routes/notes/+page.svelte`, `NoteTree.svelte`, `src/lib/note-tree.ts`, `src/core/modules/notes.ts` (tree route), a new `pathPrefix` filter in `src/query/builder.ts` (the only place SQL may live).

**N5 Templates.** Built-in templates in `src/edit/templates/notes/*.md` (blank, meeting notes, decision, runbook, how-to) plus user templates in `Notes/_templates/`; create-from-template picker in the workspace; `createNote` takes `template` (`src/edit/notes.ts:160`), filling with the existing `fill()` (`save.ts:446-454`). Template files never appear in the tree or search.

**N6 Labels and properties.** A raw-text editor for the `tags:` key (`src/edit/frontmatter-tags.ts`) that handles flow lists, block lists, quoting, comments, CRLF and a missing key, and **refuses** (422) what it cannot round-trip. Label chips on pages, `?label=` browse (uses `DocumentQuery.tags`), and a read-only properties table. Page-level sections only (children, labels, properties, backlinks); in-body live macros are N11.

**N7 Editor insert menu and toolbar.** A slash source in the completion `override` (`Editor.svelte:149`, matching `^\s*\/\w*$`), a toolbar button row at `:189-200`; entries come from the block registry (`label`, `starter()`) plus headings, table, callout and wikilink. Hand-writing fences stays easy after the builder is gone.

**N8 Page history.** `execFile('git', [...])` with an args array on the vault root, `GIT_NO_LAZY_FETCH=1`, a timeout, and tolerance for missing blobs (the VM clone is partial): `log --follow --format=… --name-status -n 200 -- <path>`; a version is `show <sha>:<path>`; a diff is `diff <a> <b> -- <path>` parsed by `unified-diff.ts` and drawn by `SplitDiffFile.svelte`. Path is validated with the same rules as a note path; shas must match `^[0-9a-f]{7,40}$`. **Restore** is a normal user-initiated save of the old content against the current hash (`saveNote`, `edit/save.ts`), so conflicts and the Notes/ guard behave as for any save. Typed pages get history read-only.

**N9 Attachments** (opus tier). Upload as JSON + base64 (the write guard stays as it is: no new content type); per-route `bodyLimit`; allowlist by **magic bytes** (png, jpeg, gif, webp, pdf; never svg or html); stored hash-named at `Notes/_attachments/<sha256-12>-<slug>.<ext>`; `atomicWrite` gains a bytes path and `pathSafety` an attachment rule (the `.md`-only rule is hard-coded at `edit/notes.ts:78` and `config.ts:138`). Serving: `GET /api/v1/attachments/<name>` validates the name, maps extension to a fixed content type, sends `X-Content-Type-Options: nosniff`, `Content-Disposition` (inline for images, attachment for pdf), `Content-Security-Policy: sandbox; default-src 'none'`, and an immutable cache (the name is a content hash). Renderer: `![[x.png]]` and `![](…)` to an attachment draw `<img src="/api/v1/attachments/…">` (`blocks.ts:60-66`, `wikilink.ts`). Editor: paste and drop. The vault commits and pushes attachments with no size check, so the cap is the guard (G1).

**N10 Typed spaces.** Incidents and Soaks appear as spaces in the switcher, their pages open with the registry's typed header, history works read-only, and a short "how to add a page type" is written (docs, N12).

**N11 Live blocks** (deferred). `orient-children` and `orient-properties-report`. Output that depends on the index must be in the render-cache key (`link-gen.ts` shows how a dependency joins it); the safe route is a placeholder block hydrated by the SPA from the core, so the cached HTML never goes stale.

**N12 Records.** CLAUDE.md invariants (the registries, attachments, history, the Notes/ boundary), a `docs/notes/README.md`, the programme's close-out.

## 7. Verification

Each unit: `pnpm typecheck`, `pnpm ui:check`, `pnpm ui:build`, lint at baseline, `pnpm test` **on a quiet host** (load under ~3: at load above ~15 timing tests flake), a review-panel (at most 4 lenses; the lead verifies each high finding by reading the code), then a deploy by named sha and a browser tour with every non-GET aborted. Writes are exercised on a side-port core against a scratch vault clone (`git clone --no-hardlinks ~/Documents/obsidian <dir>`, origin removed) and never on the real vault. Tests never write the real vault or call scribe `:3013`.

## 8. Defaults taken (Harry can veto any)

1. A folder's own page is `<folder>/<folder>.md`.
2. `_`-prefixed folders under `Notes/` are structural and hidden.
3. Typed Notes use frontmatter `kind:`; the classifier is untouched.
4. Typed spaces are read-only in v1.
5. History is the vault's sync commits (about 90 s granularity), per path, with `GIT_NO_LAZY_FETCH=1`; a version whose blob is missing says so.
6. Attachments: 5 MB per file, png/jpeg/gif/webp/pdf, hash-named under `Notes/_attachments/` (G1).
7. Uploads are JSON + base64.
8. In-body live macros wait (N11); v1 shows children, labels, properties and backlinks as page sections.
9. An insert menu, not WYSIWYG.
10. `/notes?path=` keeps working.
11. No change to the vault's `.knowledge/config.yaml`.

## 9. Open questions (none blocks N1 to N8)

- Should the explain skill's lint mirror (Harry's `orient-writers`) be generated from the block manifest? (Harry's repo.)
- After N10, which page kind folds in next (decisions, systems, plans)? The registry is built for it; the order is Harry's call.
