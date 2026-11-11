---
title: "orient Notes — Design"
status: active
owner: "hjf"
services: ["orient"]
created: "2026-11-11"
updated: "2026-11-11"
tags: [bifrost, design]
---
# orient Notes — Design

Progress is in [[orient Notes/Migration State|Migration State]]; the why is in [[orient Notes/Overview|Overview]]. This doc is the shape: what exists, the model, the two registries, the units. Claims about the code cite `file:line` from three read-only research passes over `~/projects/orient` at `6445727` and the vault's git. **Revision 2 (2026-11-11):** two adversarial reviews (factual grounding; sequencing, vault ownership and security) found no unit un-buildable but changed the plan: a standalone golden-harness unit (N0), attachments split in three behind a kernel header fix and cut to images only, hardened history, a structural-path allowlist instead of a blanket `_` rule, and serial sequencing for units that share files. What changed is listed in §9.

## 1. Goal and non-goals

**Goal.** Turn Notes into a Confluence-style workspace over the vault: a page tree with breadcrumbs and child lists, templates, labels and page properties, page history with diff and restore, image attachments, and two registries that make it extensible: a **block registry** (renderer) and a **page-type registry** (soaks, incidents and the rest). The Diagrams page is deleted: its builder goes, the renderer's diagram blocks stay, because they are the embed format a future C4 whiteboard writes.

**Non-goals (v1).** Comments, WYSIWYG, per-page permissions, non-image attachments (PDF, SVG, office files), moving any existing vault file, the whiteboard itself, and folding the other page kinds (decisions, plans, systems…) into the workspace. The registry is the vehicle for that later.

## 2. What exists (the facts the design stands on)

> SUPERSEDED 2026-11-11 — the Tags row below says body `#hashtags` count as tags. They do not reach the index: `parse.ts:159` and `writer.ts:209` write only frontmatter `tags:` (the `tags.source` column exists but no `body` row is written). Found building N3; N6's source option is unnecessary unless body tags are added.

| Area | Fact | Where |
| --- | --- | --- |
| Hierarchy | The tree is built from path segments only. `listNotes()` returns `{id, path, title}` and is not filtered. | `src/lib/note-tree.ts:16-37`, `src/domain/notes.ts:9-27` |
| Writes | The app writes `Notes/<segments>/<name>.md` only; dot-prefixed or empty segments, a non-`.md` name, `..` and symlink escapes are refused (`checkNotePath`). Trash writes `Notes/.trash/` through `ensureDirs`. `atomicWrite` takes strings and **replaces** the target (`rename`). `WRITABLE_EXTENSIONS` also gates the generic `saveDocument`, so an image extension must never be added there. | `src/edit/notes.ts:55-99,204-234`, `src/edit/pathSafety.ts:54-124`, `src/edit/atomicWrite.ts:12-35`, `src/config.ts:138`, `src/edit/save.ts:251,293` |
| Create | A new note is `# <title>\n\n` (no frontmatter, no id: ids come from the manifest). The body is hard-coded where a template plugs in; the core's `Create` zod schema is non-strict, so a new field is silently stripped until widened. | `src/edit/notes.ts:132-163`, `src/content/manifest.ts:103-106`, `src/core/modules/notes.ts:22` |
| Templates | `TEMPLATES = ['decision','inbox','tool']`; `fill()` (module-private) substitutes `{{title}} {{date}} {{slug}} {{service}} {{ticket}}` raw, and unknown placeholders stay literal; `readTemplate` is typed to those three names and reads `process.cwd()/src/edit/templates`. Only tests call `createDocument`. | `src/edit/save.ts:84,195-241,430-454` |
| Types | A document's `type` comes from its folder (30 path rules); **Notes/ is always `note`**, but `note` is also the catch-all (Engineering depth 2, the final fall-through). 22 types, closed enum. `_heap` is a real content folder (area `inbox`). | `src/content/classify.ts:264-443,323`, `src/domain/types.ts:10-33`, `classify.ts:92` |
| Tags | Frontmatter `tags:` is indexed in `tags(doc_id, tag, source 'fm'\|'body')`; `DocumentQuery.tags` does not filter by source, so body `#hashtags` count. `stringList` accepts a scalar `tags: a, b`. No op or UI uses the filter. | `src/index/schema.sql:85`, `src/domain/types.ts:649`, `src/index/writer.ts:125-132` |
| DTOs | `NoteDto` is `{path, note: NoteViewDto \| null}`; the view DTO and `DocHeaderDto` carry no tags, frontmatter or fields. | `src/api/types/notes.ts:16-28`, `src/api/types/doc.ts` |
| Readers | No registry: a typed header means a new `Reader` variant, a builder, a branch in `readerFor` and one in the page. Incident and soak use the generic reader plus a bespoke list page. `saveSourceOp` saves **any** document by id (so `/doc/<id>/edit` already edits every type, as user-initiated saves). | `src/ops/doc.ts:20-32,122-131`, `ui/src/routes/doc/[id=docId]/+page.svelte:63-77`, `src/domain/incident.ts:73-86`, `src/domain/soak-tests.ts:133-140` |
| Meta | `meta` for incident and soak-test carries the header fields (reference, severity, isUs, declaredAt, resolvedAt, minutesToResolve, incidentUrl, slackChannelUrl / status, programme, unit, started, nextCheckpoint, verdict, subjects, queued, monitors); `meta` for Notes is always plain `note`. `kind:` is readable from the indexed `frontmatter` JSON (`fm.kind`). | `src/domain/types.ts:304-350`, `src/content/classify.ts:699-760` |
| Search | FTS over documents and entries; the only scope is `notes`; the domain layer already accepts type, area, container, tags, status and a `where` on path. A path **range** (`{gte:'Notes/A/', lt:'Notes/A0'}`) expresses a prefix with no builder change (`contains` is an infix LIKE; `_` is a LIKE wildcard). | `src/ops/search.ts:67-120`, `src/domain/types.ts:643-665`, `src/query/builder.ts:79-81,598-601,729-753` |
| Blocks | Dispatch is an if-chain on the fence language; adding a block touches about ten places: parse, schema, lint, render, **five** hand-written fence regexes (`entries.ts:1014`, `ops/doc-readers.ts:31`, `domain/health.ts:210`, `domain/today.ts:124`, and the standalone mirror `scripts/validate-blocks.mjs:92`) plus a literal in `evidenceRef.ts:16`, tests, the external lint mirror and `RENDERER_VERSION`. `parse` returns `{ok, block}` today. `source-hash.ts` follows **static** imports only. | `src/render/html/blocks.ts:195-236`, `src/render/md/explainer-blocks.ts:189-210`, `src/render/md/orient-blocks.ts:61-85`, `src/render/html/source-hash.ts:27-45` |
| Images | `![](url)` renders `<img>`; `![[file]]` is an embed wikilink drawn only as a link (and, unresolved, a LINK-UNRESOLVED finding); `safeHref` allows http(s), mailto, obsidian, relative. **No route serves a vault file**; no `img-src`; no `nosniff`. | `src/render/md/pipeline.ts:62`, `src/render/md/plugins/wikilink.ts:6-46`, `src/render/html/blocks.ts:60-66`, `src/lib/safe-href.ts:9-15` |
| Headers | `frameGuard` runs on every route and **replaces** `Content-Security-Policy` after the route has run, so a route-level CSP is silently lost. | `src/core/kernel/guards.ts:90-94`, `src/core/kernel/server.ts:153` |
| Write guard | Non-safe requests need loopback Origin, `X-Orient: 1` and `application/json`; a multipart or binary POST gets 415; no route takes bytes. `bodyLimit` is per route (notes 16 KiB, editor/doc save 2 MiB). | `src/core/kernel/guards.ts:54-84` |
| Vault git | The vault is a **partial clone** (`blob:none`): 349 blobs are missing locally; `git log --follow -p` can die fetching one. Sync commits (`sync: vm\|laptop <ts>`, about every 90 s, plus merges) batch many files. `git log --follow` on the busiest file takes 0.08 s. Local git is 2.56 (`GIT_NO_LAZY_FETCH` needs 2.44). Anything under `Notes/` is committed and pushed with no size check; no LFS. | `scripts/vault-sync.sh:74-106`, `systemd/orient-vault-sync.timer:5-6` |
| Editor | CodeMirror with a `[[` completion `override`; the toolbar is plain Svelte; preview posts to `/api/v1/editor/note/preview`. | `ui/src/lib/editor/Editor.svelte:136-200`, `src/core/modules/editor.ts:67`, `src/ops/note-edit.ts:32-40` |
| Diff UI | `SplitDiffFile.svelte` takes one prop `file: DiffFileDto` and renders with `splitPatch` (no pre-hunk skip: git's `---`/`+++` lines would draw as rows); fixed `max-h-96` and a binary fallback. `parsePatch` skips the header but the component does not use it. | `ui/src/lib/delivery/tickets/SplitDiffFile.svelte:7`, `src/api/types/tickets.ts:124-130`, `src/lib/split-diff.ts:32-47`, `src/lib/unified-diff.ts:39-40` |
| Diagrams | The builder: `ui/src/routes/diagrams`, `DiagramEditor.svelte`, `knowledge/diagrams.ts`, `ops/diagrams.ts`, DTOs, a query, a nav entry in four places, tests; the renderer needs `diagram-presets.ts`, `explainer-blocks.ts`, `flow-layout.ts`, `html/diagrams.ts`. | see N2 |

## 3. The model

- **Spaces.** `Notes` is the authored space. Typed spaces (`Incidents`, `Soaks`, later more) are windows onto vault folders that skills and `wp` write; their files never move. The workspace adds no editing for them (the existing `/doc/<id>/edit`, a user-initiated save, is unchanged).
- **Pages and folders.** A page is a markdown file; the folder is the hierarchy. A folder's own page is `<folder>/<folder>.md` (the folder-note convention). `[[Architecture]]` does **not** resolve reliably (the vault has 39 `architecture.md` and 67 `overview.md`, and the resolver ranks `waypoint` above `note`), so the app emits path-qualified links (`/notes?path=…`) for folder pages and an ambiguity fixture pins it. A folder with no folder note shows an automatic child list.
- **Structural folders.** `Notes/_templates` and `Notes/_attachments` (a fixed allowlist, `isStructuralPath()`) are infrastructure: skipped by the indexer, so they never appear in the tree, search, backlinks, link completion, labels or the manifest. Other `_` folders (`_heap`) are content and untouched. (`.`-prefixed folders cannot be written by the app, apart from the existing `.trash`.)
- **Labels and properties.** Labels are frontmatter `tags:` (source `fm` only). Properties are the rest of the frontmatter as a table. Editing a label edits the raw frontmatter text (never re-serialise YAML: unknown keys survive byte for byte) and goes through `saveNote` with a base hash.
- **Typed pages.** The classifier is untouched. The page-type registry sits above it and maps a document to a header (`fields`) and the workspace's offerings. Under `Notes/` a frontmatter `kind:` selects the type; elsewhere `document.type` does.
- **Sensitive documents.** `Bifrost/HR`, `Bifrost/Team` and `Interviews` (`sensitive`) are excluded from the tree, labels, search and history by the shared read model, so no future space or label browse can surface them.
- **Version history.** The vault's git, read-only: the sync commits that touched the path.
- **Embeds.** Fenced `orient-*` blocks and image attachments (`![[<stored name>]]`). The whiteboard will write the same fences.

## 4. The two registries

**Block registry** (`src/render/blocks/`, static imports only; `source-hash.ts` must list every file, a test pins it):

```ts
type BlockSpec<T> = {
  name: `orient-${string}`                          // the fence language
  parse(text: string): { ok: true; block: T } | { ok: false; error: string }   // today's shape
  lint?(raw: unknown): Finding[]                    // takes the RAW JSON (the schema rejects what several rules target); flow and sequence adopt diagram-lint.ts; N7's preview shows them
  render(block: T, ctx: RenderCtx): Hast | null     // null drops the node (action lists)
  starters: { label: string; text: string }[]       // the editor's insert menu; flow has several (C4 and data-flow variants)
}
type DocumentLint = (blocks: ParsedBlock[]) => Finding[]   // BLUF at most one, evidence ids cited
```
Six blocks (bluf, evidence, flow, sequence, data, action) move behind it with **byte-identical output**; the five regexes become one `BLOCK_NAMES` (the standalone `validate-blocks.mjs` mirror gets a test that it agrees); `blocks.ts:195-236` becomes one lookup; `today.ts` and `health.ts` keep importing `parse` without the HTML side.

**Page-type registry** (`src/domain/page-types.ts`, static, plus an SPA map for optional bespoke headers):

```ts
type PageType = {
  id: string                                  // 'note' | 'incident' | 'soak-test' | …
  documentTypes: DocumentType[]               // what the classifier calls it
  match?(doc): boolean                        // 'note' requires area 'notes' (the type is also a catch-all)
  notesKind?: string                          // frontmatter `kind:` for pages under Notes/
  frontmatterFields?: string[]                // header keys for a `kind:` page (its meta is plain `note`)
  label: string; folder?: string; listHref?: string
  workspaceEditable: boolean                  // what the workspace offers; only 'note' in v1
  fields(doc): HeaderField[]                  // chips: status, severity, dates, links
}
```
v1 registers `note`, `incident` and `soak-test` (fields from typed `meta`). Adding a type later = one file + one line + (if it has a folder) a space entry.

## 5. API and URLs

URLs are a durable contract: `/notes?path=` stays, for pages **and folders**; the rest is additive and in the URL: `?view=history|diff`, `&from=&to=` (shas), `?label=`, `?space=`, `?template=`. `/diagrams` answers 308 to `/notes` (the `/tools` precedent in `core/modules/knowledge/redirects.ts`).

Core (loopback, write guard unchanged), one module file per unit under `src/core/modules/pages/` and DTOs in a new `src/api/types/pages.ts` (so units do not edit the same file): `tree`, `page`, `versions|version|diff`, `create` (with `template`), `labels`, `restore`, `attachments` (`POST` JSON+base64, `GET /api/v1/attachments/<name>`). The existing `/api/v1/notes/*` and `/editor/*` routes keep working until the SPA has moved over.

## 6. The units

**N0 Golden harness.** Before any renderer change. `scripts/render-golden.ts` takes a scratch vault path and writes JSON of per-document sha256 for: `renderHtml` output; `prepareDocument()` entries and findings (`entries.ts:1014`); `parseNeeds` (`today.ts`), the health parse (`health.ts`) and `isWideSource` (`doc-readers.ts`) for documents with blocks. It asserts corpus counts per fence kind (the vault has 194 bluf, 181 flow, 146 data, 40 action and only 3 sequence), ships synthetic fixtures (`tests/fixtures/blocks/`) for all six blocks, every invalid-block error message, `drift`, `serviceHrefs`, `renderInlineHtml` and `.mdx`, and must be deterministic across two runs. The baseline comes from a committed sha via `git archive` into a temp dir (never the live, shared checkout); the "after" run is N1's commit alone. A test asserts `rendererSourceFiles()` covers every `src/render/blocks/*` file. Reuse the shape of `scripts/render-parity.ts` at tag `next-ui-final`.

**N1 Block registry.** As §4. Touch: `blocks.ts:195-236`, `explainer-blocks.ts:189-210` and `orient-blocks.ts:61-85` (one `parse` helper), `block-schemas.ts`, `explainer.ts`, `diagrams.ts`, `actions.ts`, the five regexes, `evidenceRef.ts:16`, tests. `RENDERER_VERSION` unchanged; N0's two goldens must match. Exports a block manifest; the external lint mirror (`orient-writers/skills/explain/lint-explainer.mjs`, Harry's repo, already drifting: no `person` kind, `diagram-rules.mjs` untracked) is Harry's to adopt.

**N2 Delete the Diagrams builder.** Delete: `ui/src/routes/diagrams/+page.svelte`, `ui/src/lib/knowledge/DiagramEditor.svelte`, `src/core/modules/knowledge/diagrams.ts` (mounted at `waves/w-d2.ts:2,17`), `src/ops/diagrams.ts`, `Diagram*Dto` (`api/types/knowledge.ts:182-212`), `diagramsQuery`, `'diagrams'` in `src/api/migrated/w-d2.ts:10`, `diagramHref` and the "draw a diagram" link (`notes/+page.svelte:54`), `appendToNote` and `appendToNoteOp` (their callers are `ops/diagrams.ts:82` and two tests, `tests/unit/notes.test.ts:197-210`), the nav entry (`navigation.ts:414-421`, `config.ts:164`, regenerate `nav.generated.ts`; `config.test.ts:157` forces the first two together). Tests, exact: `core-knowledge.test.ts:318-422` (a whole describe); in `ui/tests/knowledge.test.ts` only the diagrams describe (`:812-958`), the insert-gate describe (`:1231-1297`) and the lazy import and DTO import at `:5,:33`; in `entity-href.test.ts` only `:127-129`; the diagrams case in `routing.test.ts:154-159`. Keep: `diagram-presets.ts` (`DIAGRAM_PRESET_IDS`, `STARTERS` stay: tests and the registry use them), `diagram-lint.ts` (its consumer becomes N7's preview), `explainer-blocks.ts`, `flow-layout.ts`, `html/diagrams.ts`. `/diagrams` redirects. The `diagrams` slug in the vault's `.knowledge/config.yaml:31` is Harry's config and stays: `scripts/ui-nav.ts` filters group slugs against `NAV` (the vault config already carries a retired slug, `tools`); N2 extracts the grouping from that script (it writes a file on import) into a function so a test can pin it.

**N3 Page-type registry and typed chrome.** As §4; depends on N1 (both touch `src/ops/doc-readers.ts`, and `src/lib/entity-href.ts` is in the renderer's import graph: N3 must not change it before N1's golden has passed). `fields`, `labels`, `properties` go on `NoteViewDto` and `DocHeaderDto`; `GenericReader.svelte`'s chip line draws `fields`; `readerFor` only passes them. Incident and soak-test are the first registrations (their dashboards remain the list views).

**N4a Pages read model.** `isStructuralPath()` allowlist used by the indexer (a new skip reason), `listNotes`, the link resolver (`resolverFor`/`buildResolverIndex`), `suggestLinks`, `backlinksOf` and search; an image embed of a known extension resolves as an asset with no LINK-UNRESOLVED finding (`links.ts`); sensitivity exclusion; a path-range helper (no new operator; any `contains` fallback uses the builder's `escapeLike`); tree, children and breadcrumb DTOs in `api/types/pages.ts`; `core/modules/pages/tree.ts` and `page.ts`. The old `/api/v1/notes/*` stay. Tests include an ambiguity fixture for folder notes.

**N4b Workspace shell (SPA).** New components under `ui/src/lib/workspace/` with **slot components** (`PageSections`, `NewPageMenu`, `HistoryTab`) so later units add files rather than edit one hot page; `ui/src/routes/notes/+page.svelte` is rewritten once, here (depends on N2, which removes the link at `:54`). Tree with folders and pages (collapse state in the URL), breadcrumbs, folder view (folder note above the child list), space switcher (Notes, Incidents, Soaks linking to their lists), a search box scoped to the space (widen `ops/search.ts` scope beyond `notes` using the filters the domain already has).

**N5 Templates.** `src/edit/note-templates.ts`: built-ins (`src/edit/templates/notes/*.md`: blank, meeting notes, decision, runbook, how-to) plus user templates under `Notes/_templates/`, read through `pathSafety` with symlink refusal and a size cap; the template name is a validated slug taken from the listing, never a path. `fill()` is exported and quotes values in frontmatter positions as JSON scalars (`title: {{title}}` with the title `Q4: plan #2` must stay valid YAML). Widen the core `Create` schema. A test pins that two near-identical template-derived notes do not trigger the manifest's rename inheritance (`findRenameSource`, similarity 0.9 within 5 minutes). Template files are skipped by the indexer (N4a), so their bare `{{placeholders}}` are never parsed.

**N6 Labels and properties.** The `tags:` editor splits frontmatter exactly as `WP_FM_RE` does (first `\n---\n`), handles a missing block as well as a missing key (app-created notes have none), covers flow lists, block lists, quoting, comments, CRLF and the scalar form, **refuses** (422) what it cannot round-trip, only for `Notes/` paths, and writes through `saveNote` with a base hash. `DocumentQuery.tags` gains a source option so `?label=` means frontmatter labels only. Label chips, `?label=` browse and a read-only properties table.

**N7 Editor insert menu, toolbar and lint.** A slash source in the completion `override` (`Editor.svelte:149`, matching `^\s*\/\w*$`), a toolbar row at `:189-200`; entries come from the block registry's `starters` plus headings, table, callout and wikilink. The preview pane shows the registry's `lint` findings: this is what the builder's lint becomes.

**N8 Page history (hardened).** `execFile('git', args)` on the vault root with `GIT_LITERAL_PATHSPECS=1` (a note named `*` would otherwise match many files), `GIT_OPTIONAL_LOCKS=0`, `GIT_NO_LAZY_FETCH=1` (check `git --version` at startup: older than 2.44 means history is unavailable, not a silent GitHub fetch), `--` before every path, a timeout, `maxBuffer`, a concurrency cap and **no cache** (not `adapters/exec.ts`'s `runJson`: it caches stdout in memory and on disk outside the vault). Commits only (never a worktree or index diff: those refresh `.git/index` and race `vault-sync.sh`'s `git add -A`). No `--follow` in v1: it matches by content similarity across sync batches and can reach files outside the page's scope; a rename shows as add and delete. Every sha is resolved with `rev-parse --verify <sha>^{commit}` and must appear in that path's log. A read-only path validator separate from `checkNotePath` (which refuses everything outside `Notes/`): an indexed document path in an allowlisted space, no glob characters, never a `sensitive` one. Log: `log --format=… -n 200 -- <path>`; version: `show <sha>:<path>`; diff: `diff <a> <b> -- <path>` cut at the first `@@`, with additions and deletions from `--numstat`, drawn by `SplitDiffFile.svelte` (mind its `max-h-96` and binary fallback). A missing blob says "version not available locally". **Restore** is a normal user-initiated `saveNote` of the old content against the current hash, `Notes/` only.

**N9a Attachment store and serve route** (opus tier, behind G1). First `frameGuard` stops clobbering: set the header only when the route did not, and a test through `createCore().app.request` pins the full header set for every allowed type. Storage: `resolveAttachmentPath` (only `Notes/_attachments/<64-hex>.<ext>`), an `atomicWriteBytes` that never replaces (`wx`/link; same bytes are a no-op, different bytes are refused); `WRITABLE_EXTENSIONS` is not touched. Serve `GET /api/v1/attachments/<name>`: strict name regex, `lstat` not a symlink (files also arrive through git from other machines), magic bytes and size cap re-checked on every read, a fixed extension-to-type map (png, jpeg, gif, webp), `X-Content-Type-Options: nosniff`, `Cross-Origin-Resource-Policy: same-origin`, `Content-Security-Policy: sandbox; default-src 'none'; frame-ancestors 'self'`, `Content-Disposition: inline`, `ETag` from the content hash and `Cache-Control: private, no-cache` (not `immutable`: a file replaced in place by git or Obsidian would stay stale for a year). Never `serveStatic` (its mime map serves svg and html). Mounted through the kernel, so the Host guard covers it.

**N9b Upload route** (opus tier). `POST /api/v1/attachments`, JSON `{data: <base64>}` through the unchanged write guard; strict base64; a per-route `bodyLimit` sized for the cap with the real check on the decoded length; the extension comes from the **detected magic bytes**, never the client's name; the stored name is the full 64-hex sha256; a total quota under `Notes/_attachments` (G1) refuses over it; nothing is ever auto-deleted (at most a list of unused attachments); `kickVaultSync` as for any write.

**N9c Embed, paste and drop.** The editor inserts one stable form, `![[<stored name>]]` (location-independent; `renameNote` ignores it, whereas a relative `![](…)` would be rebased by `retargetRelativeLinks`). The renderer maps only names matching the strict regex to `/api/v1/attachments/<name>`, never looks a name up on disk (the render-cache key must hold every input the output depends on), and `RENDERER_VERSION` is bumped. Paste and drop in `Editor.svelte`; an attachments section on the page; CLAUDE.md invariants for attachments land here.

**N10 Typed spaces.** Incidents and Soaks as spaces in the switcher, typed headers from the registry, read-only history, an explicit space allowlist (Notes, Incidents, Soaks), sensitivity excluded in the shared read model.

**N11 Live blocks** (deferred). `orient-children`, `orient-properties-report`. Index-dependent output must be in the render-cache key (`link-gen.ts` shows how a dependency joins it); the safe route is a placeholder block hydrated by the SPA.

**N12 Records.** CLAUDE.md (the registries, history, the Notes/ boundary; attachments were done in N9c), `docs/notes/README.md` ("how to add a block", "how to add a page type"), the programme's close-out.

## 7. Sequencing and the shared checkout

The research found units that collide on hot files (`notes/+page.svelte`, `core/modules/notes.ts`, `ops/notes.ts`, `api/types/notes.ts`, `edit/notes.ts`, `tests/unit/core-*`), and `git commit -- <paths>` only protects whole files. So: N0 → N1 → (N2, N3 in either order, **not** together) → N4a → N4b → N5 → N6 → N7, strictly in series; N8 needs only N4b and may run beside N7 if the lead has checked the file lists are disjoint (it lives under `core/modules/pages/versions.ts` and its own components); N9a → N9b → N9c in series; N10 and N12 last. At most 3 builders at once, and normally 1 to 2.

## 8. Verification

Each unit: `pnpm typecheck`, `pnpm ui:check`, `pnpm ui:build`, lint at baseline, `pnpm test` **on a quiet host** (load under ~3: above ~15 timing tests flake), a review-panel (at most 4 lenses; the lead verifies each high finding by reading the code), a deploy by named sha, and a browser tour with every non-GET aborted. Writes are exercised on a side-port core against a scratch vault clone (`git clone --no-hardlinks ~/Documents/obsidian <dir>`, origin removed), never on the real vault; tests never write the real vault or call scribe `:3013`.

## 9. What review changed (revision 2)

1. N0 became its own unit with a deterministic, broader golden (it proves only `renderHtml` otherwise: not the index rows, `today`/`health` parses, invalid-block messages, the render cache hash).
2. N9 split into three and images only (PDF has no renderer and the most active-content risk); a kernel fix first because `frameGuard` overwrote the CSP; no `serveStatic`, no `immutable`, never-replace writes, extension from magic bytes, a quota.
3. Structural paths are a fixed allowlist the indexer skips (templates and attachments were otherwise indexed as notes, adding ghost pages, backlinks and link findings); `_heap` stays content.
4. N8: `GIT_LITERAL_PATHSPECS`, no `--follow`, rev-parse every sha, commits only, no cache, git version check, a read-only path validator, sensitivity excluded.
5. N4 split in two; a `core/modules/pages/` and `api/types/pages.ts` layout and slot components so units add files; N5 to N7 in series; N3 after N1.
6. Smaller: the folder-note link claim corrected; `NoteViewDto` (not `NoteDto`) carries the fields; `note` needs an area guard; a prefix filter is a path range; `?label=` filters source `fm`; the tags editor handles a missing frontmatter block; `fill()` quotes YAML scalars; `SplitDiffFile` needs a trimmed patch; N2's test ranges and the `appendToNote` tests corrected; `BlockSpec.parse` keeps `{ok, block}`; five regexes, not four.

## 10. Defaults taken (Harry can veto any)

1. A folder's own page is `<folder>/<folder>.md`; links to it are path-qualified.
2. Only `Notes/_templates` and `Notes/_attachments` are structural.
3. Typed Notes use frontmatter `kind:`; the classifier is untouched.
4. The workspace offers no editing for typed spaces.
5. History is the vault's sync commits, per path, no rename-following, missing blobs say so.
6. Attachments: 5 MB per file, png/jpeg/gif/webp only (no svg, html or pdf), 64-hex hash names under `Notes/_attachments/`, a 200 MB total quota, no auto-delete (G1).
7. Uploads are JSON + base64.
8. In-body live macros wait (N11); v1 shows children, labels, properties and backlinks as page sections.
9. An insert menu and preview lint, not WYSIWYG.
10. `/notes?path=` keeps working.
11. The vault's `.knowledge/config.yaml` is not edited. Images already in the vault (three `Pasted image*.png` at its root, from Obsidian's default attachment folder) stay as they are and will not render; pointing Obsidian's attachment folder at `Notes/_attachments` is Harry's config.

## 11. Open questions (none blocks N0 to N8)

- Should the explain skill's lint mirror (Harry's `orient-writers`) be generated from the block manifest?
- After N10, which page kind folds in next (decisions, systems, plans)? The order is Harry's call.
