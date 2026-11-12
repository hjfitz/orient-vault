---
title: "orient Whiteboard — Overview"
status: active
verdict: go
owner: "hjf"
services: ["orient"]
created: "2026-11-12"
updated: "2026-11-12"
tags: [bifrost]
---
# orient Whiteboard — Overview

## Deliverables
- [[orient Whiteboard/Migration State|Migration State]] — the live source of truth for progress
- **The minimum Harry set (2026-11-12): a freeform whiteboard with premade symbols for context diagrams.** That is units B0 to B3: a board page you place, move, resize and connect symbols on, saved into the vault like any note, drawn the same way as the diagrams already in orient.
- After the minimum: insert a board into another note as a block, export, live embeds, symbols from the `c4-diagrams` guide, Lucid import.

## Verdict
**Go.** The whiteboard is a separate programme from [[orient Notes/Migration State|orient Notes]] (its Design lists "the whiteboard itself" as a non-goal), but it stands on that programme's registries and editor: the block registry (N1), the page-type registry (N3), history and restore (N8), and the create menu (N13, where Whiteboard is listed and disabled until B1 registers it).

## What Harry asked for (his words, 2026-11-12)
"a diagrams whiteboard. free-flowing. a page in our /notes can be a markdown page like we should have, or a whiteboard. components should be available following our design language in /c4-diagrams. google resource type in the top left. orient blocks. we created some in lucid - may need to check the merak confluence". Then: "are we able to plan whiteboards … Freeform with premade symbols for context diagrams is the minimum".

## What exists already (verified in the repo, 2026-11-12)
- **The symbols.** `src/render/md/diagram-presets.ts`: node kinds `service, topic, store, step, external, person`; eleven Google-resource glyphs `compute, storage, pubsub, run, memorystore, gke, sql, bigquery, functions, secret, scheduler` (the file says they are generic marks, not the official product art Lucid carries); presets `c4-context` (person, service, external; at most 10 nodes), `c4-container`, `c4-component`, `data-flow`, and the `c4-dynamic` sequence preset. This is "premade symbols for context diagrams", and the glyph is the "Google resource type in the top left": `src/render/html/diagrams.ts` draws it at the top-left of the card (`glyph(icon, p.x + 14 + swatch, p.y + 6 + drop)`).
- **The drawing code takes positions.** `diagrams.ts` draws a node from a spec of `kind, x, y, w, h, fill, stroke` (a store is a cylinder, a topic or person a pill, the rest a box; an external system is drawn on the lighter fill). Today `flow-layout.ts` computes those positions automatically for `orient-flow`. A board supplies them itself, so both look identical because they share one drawing path.
- **The block mechanism.** `orient-flow` and the rest are registered `BlockSpec`s with parse, lint (`lint(raw: unknown)`), starters and a renderer; the editor's Block menu and the preview's Block checks (N7) pick up a new block by registering it.
> SUPERSEDED 2026-11-12 — the `c4-diagrams` guide is now on the VM (`~/.claude/skills/c4-diagrams/`: `SKILL.md`, `lucid_style.py`, `example_carrier_proxy.py`, `reference/component-diagram.png`) and gate G1 is cleared; see "The house style" below. Only the Lucid half of the next bullet still stands: the Lucid connector needs Harry's authorisation, and the nine Confluence pages that mention Lucid were not opened.
- **Not found.** The `c4-diagrams` guide: a skill by that name exists only on Harry's laptop (uncommitted), not on this VM. Lucid content: a Confluence search for "Lucid" returned nine pages (in Merak Project, Product Management, Bifrost and Data Solutions Team spaces); none was opened, so whether any holds a reusable symbol library is unknown. The Lucid connector needs Harry to authorise it.

## The house style (the `c4-diagrams` guide, read 2026-11-12)
The guide draws diagrams in Lucidchart; its rules apply to a board unchanged. The reference is `~/.claude/skills/c4-diagrams/reference/component-diagram.png` (the Fuse SFTP connector, a component diagram).
- **Every box has three things**: a name, a type or technology, a short description. orient's node schema already has them (`src/render/md/explainer-blocks.ts`: `label`, `tech`, `sub`), plus `kind`, `icon`, `group`, `unconfirmed`.
- **Anatomy**: about 225 by 120 px (`BOX_W, BOX_H = 225, 121`; small 180 by 55); the GCP icon top-left at about 30 px; a bold title centred, then `**Type:** description`; boxes with no product icon (an endpoint, a module) are plain. **Groups**: rounded rectangle, bold label top-left, about 40 px of padding, a product icon may sit beside the label. **Datastores** are cylinders with a `Store:` line. **Topics** are ordinary boxes with the Pub/Sub icon and a `Pubsub topic:` line. External things sit outside the groups.
- **Edges**: one direction, a label that says what happens (not "uses"), 1 px with open chevron arrowheads, right-angle bends (a gentle curve where a bend would cross something), the label sitting on the line filled with the colour of what it sits on.
- **Limits and marks**: 20 boxes or fewer, under about 2,600 px wide, a title over about 28 characters runs into the icon. An unverified element or arrow is dashed and labelled `Not confirmed`. No secret, key, internal hostname or customer data.
- **Colour** (sampled from the reference): canvas `#1f1f21` with a faint dot grid; surface `#303134`; a box inside a group `#242528` with a 1 px `#1f1f21` edge; border `#7e8188`; connector `#75787e`; text `#cecfd2`; GCP blues `#aecbfa`, `#669df6`, `#4285f4`. orient's renderer draws with theme tokens so it works in both themes; the board follows the tokens and the reference is the visual acceptance test, not a hex table to copy.
- **Icons.** The guide's library has 19 (`lucid_style.py`: ComputeEngine, CloudStorage, PubSub, CloudRun, Memorystore, GKE, CloudSQL, CloudFunctions, Dataflow, Firestore, BigQuery, LoadBalancing, DNS, Logging, Monitoring, PersistentDisk, VPC, KMS, IAM) and its prose also names Secret Manager and Cloud Scheduler. orient draws 11 (`ICON_KEYS`, including `secret` and `scheduler`). **Ten are missing in orient: Dataflow, Firestore, LoadBalancing, DNS, Logging, Monitoring, PersistentDisk, VPC, KMS, IAM.** The palette needs all 21; they go into `diagram-presets.ts`, so `orient-flow` gets them too, and the mirrored table in `orient-writers` (`diagram-rules.mjs`, checked by `tests/unit/diagram-presets.test.ts`) must change with it.
- **One difference to settle.** The guide draws a topic as an ordinary box; orient draws a topic as a pill (`diagrams.ts`: "a topic or person a pill"). Changing it moves every topic in every existing diagram, which the golden harness would show. B0 keeps orient's drawing (one path); B6 puts the choice to Harry with the reference side by side.
- **The text twin.** The guide says neither the Atlassian MCP nor orient can read a Lucid diagram, so a text twin of tables must sit beside it. A board is that twin and the diagram at once: plain text in the vault, searchable, diffable, readable by orient and the MCP. Confluence still shows Lucid through its macro (the guide's embedding notes), so a board that must appear there needs an export (B4).

## Strategy
- **One drawing path.** The board's renderer calls the same node and edge drawing as `orient-flow`; only layout differs (explicit coordinates). The renderer change is verified with the N0 golden harness: every existing document must render identically, and only new `orient-board` blocks may differ.
- **A board is a markdown page.** `Notes/<…>.md` with `kind: whiteboard` in the frontmatter and one `orient-board` fence. Obsidian opens it as markdown, history, diff and restore (N8) work on it as text, and the block embeds in other notes the same way `orient-flow` does. An Obsidian `.canvas` file was considered and set aside: it would be a second storage format with no renderer, no history view and no embedding.
- **A diff-friendly fence.** One JSON object, one element per line, stable key order and ids, so a moved box is a one-line diff. A board the editor has not touched is written back byte for byte.
- **The editor is a pure model plus a view.** A command reducer (add, move, resize, connect, delete, undo, redo) with no DOM, unit-tested; the Svelte canvas only turns pointer events into commands. Save goes through the editor's existing note save with the base hash, so conflicts behave as they do for notes.
- **Series, main checkout, one builder at a time across all programmes.** `CLAUDE.md:22` forbids worktrees. Each unit: build, `review-panel` (frontend and tests, plus backend on B0), one fix round, gates on a quiet host, deploy by sha, live check, tick.

## The board format (v1, B0 settles the details)
```
{
  "v": 1,
  "title": "Orders, in context",
  "preset": "c4-context",
  "nodes": [
    {"id":"customer","kind":"person","label":"Customer","x":80,"y":60},
    {"id":"shop","kind":"service","label":"Shop","icon":"run","x":320,"y":60},
    {"id":"carrier","kind":"external","label":"Carrier","x":560,"y":60}
  ],
  "edges": [
    {"from":"customer","to":"shop","label":"orders"}
  ],
  "groups": [],
  "notes": []
}
```
Nodes use the existing kinds and glyphs; `groups` are boundary boxes (geometric, not membership lists); `notes` are sticky text. Presets still apply as warnings in the editor ("a context diagram with 14 boxes"), never as blockers: it is a whiteboard.

## Scar tissue
See the State doc. The short form: one drawing path; a board is plain markdown; labels are text, never HTML; the golden harness must pass.

## Next
B0, driven by `waypoint-programme`, after the Notes unit N13 and the Sync unit in flight.
