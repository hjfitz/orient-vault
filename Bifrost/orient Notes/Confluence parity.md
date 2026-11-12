---
title: "orient Notes — Confluence parity"
programme: "orient-notes"
status: active
created: "2026-11-12"
updated: "2026-11-12"
tags: [bifrost, orient-notes]
---
# orient Notes — Confluence parity

Harry, 2026-11-12: "the editor should look like notion or confluence more in that it renders as you type, rather than a side-by-side. the overall editing + navigation experience needs to be a near mirror of confluence."

This table is the target. The Confluence column is from general knowledge of Confluence Cloud, not checked against the Merak site; correct it where it is wrong. "Have" means live in orient today. Units are in [[orient Notes/Migration State|Migration State]].

## Navigation

| Confluence | orient today | Plan |
| --- | --- | --- |
| Space sidebar with a page tree, expand and collapse | Have (N4b) | |
| `+` beside a page to add a child | Have for folders (N13); a folder's own page is its folder note | |
| Collapse and resize the sidebar, remembered | No | **NV2** |
| Drag a page or folder in the tree to move it | No (a Move exists on the page: `NoteActions` rename with link rewriting) | **NV2** (drag, plus a keyboard "Move to…") |
| Manual order of pages in the tree | No: the tree is alphabetical | Not planned; needs an `order` field in frontmatter if Harry wants it |
| Breadcrumbs | Have (N4b) | |
| A global Create button in the top bar | No (the `+` is in the tree) | **NV2** |
| Search, scoped to the space | Have (N4b) | |
| Recently updated, starred pages | No | **NV3** |
| Space overview / folder page with its child list | Have (folder view, N4b) | |

## The page view

| Confluence | orient today | Plan |
| --- | --- | --- |
| Title, then a byline (who, when, read time) | Title and type chip | **NV1**. The vault's author is the same person on both machines, so the byline is "updated 3 hours ago" and the read time, not an author |
| Labels, page properties | Have (N6) | |
| A `…` menu: copy link, move, rename, delete, export, page information | Rename and delete exist; no copy link, move, export or information | **NV1** |
| Table of contents on the page ("on this page") | No | **NV3** (an outline panel with scroll-spy) |
| Version history, compare, restore | Have (N8) | |
| Inline and footer comments, reactions | No | Not planned (Design non-goal) |
| Watch, share, restrictions | No | Not planned (single user, no per-page permissions) |

## The editor

| Confluence | orient today | Plan |
| --- | --- | --- |
| **Renders as you type**, one surface | Markdown source beside a preview | **W1**: live preview on the markdown source, in place on the page |
| `Edit` turns the page itself into the editor; `Publish` and `Close` | A separate `/notes/edit` page with Save | **W1** (one surface) and **W4** (a draft kept in the browser, `Publish` writes it, `Close` asks about unsaved changes) |
| Title is a field at the top of the page | The title is the first heading and the file name | **W3** (a rename through the existing rename, with link rewriting) |
| Formatting toolbar on top | Have (N7: Heading, Table, Callout, Task, Link, Insert, Block) | **W3** restyles it |
| A bubble toolbar on selection (bold, italic, code, link, heading) | No | **W3** |
| `/` command menu | Have (N7) | **W3** (a Confluence-like look, with icons and groups) |
| `[[` page links with a picker | Have (N7) | |
| `@` mentions of people | No | Later (orient knows people entities); not in W1 to W4 |
| Tables with row and column controls | Insert only | **W2** |
| Panels (info, note, warning, success) | Callouts exist (N7 Callout) | W1 draws them as panels |
| Code blocks with a language | Fenced code | W1 draws them |
| Task lists with checkboxes | Have the syntax (N7) | W1 makes the checkbox clickable in place |
| Images and attachments by drag and drop or paste | No | N9a to N9c (gate G1 on the attachment policy) |
| Macros: table of contents, child pages, page properties report | No | N11 (deferred) |
| Page layouts and columns | No | Not planned: markdown cannot express them |
| Emoji with `:` | No | Optional, later |
| **Whiteboards** | Block and page type (Whiteboard programme B0, B1) | B2, B3 |

## What makes it "a near mirror" in practice
1. You never see raw markdown marks except on the line you are typing on (W1).
2. You never leave the page to edit (W1, W4).
3. The page looks like Confluence's: title, byline, `…` menu, labels, tree, breadcrumbs, `+` (NV1, NV2, N13).
4. Everything stays plain markdown in the vault, so Obsidian, git history and the renderer keep working.
