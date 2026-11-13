---
title: orient Confluence — Migration State
programme: orient-confluence
status: active
owner: hjf
services:
- orient
created: '2026-11-12'
updated: '2026-11-13'
tags:
- bifrost
- migration-state
---
# orient Confluence — Migration State

<!-- The single source of truth for PROGRESS. The Overview carries the narrative and the verified facts; this doc is the live ledger. `wp programme status/next/tick` read and write the `## Unit status` tables below, so keep the table shape intact. -->

orient has no PRs or CI: a unit ships as commits on `master` in the main checkout (`CLAUDE.md:22`: no git worktrees), staged by explicit path, pushed, then deployed (`pnpm deploy:all`, a named sha). The `PR` column holds the commit range. One builder at a time across the Notes, Sync, Whiteboard and Confluence programmes. Each unit: build, review by the lane its risk needs, gates on a quiet host, deploy by sha, live check with writes blocked, tick, decision log, push.

## Unit status
Legend: ⬜ not started · 🟨 in progress · ✅ merged · ⛔ blocked · ⏸ deferred · ❌ dropped · 🔄 rescoped

Sequencing: C0 → C1 → C2 → C3 → C4 in series. C3 reuses the sidebar and tree from Notes NV2, so the programme starts after NV2.

### The minimum: Fuse and Merak tabs, read-only
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **C0** | ✅ | Confluence client, config, cache | | med | sonnet/high | 85e2d50..512155a | `src/adapters/confluence.ts`: **GET only**, one allowlisted host (the site behind `jiraApiBase()`), no redirects off it, size and time caps, `Retry-After` and 429 honoured, the credential from `jiraCredentials()` and never logged. Reads: spaces, a space's top-level pages and a page's children (the tree), a page (`/wiki/api/v2/pages/{id}?body-format=atlas_doc_format`, plus ancestors, labels, `version` for the byline: real author and last-updated), attachments metadata, CQL search (`/wiki/rest/api/search`). Vault config `confluence.spaces` (a tab label, key and id each; defaults **Fuse → Bifrost (4587524)** and **Merak → MP (338526210)**), site derived from `external.jiraBase`, a `confluence` section validated like the rest of `loadVaultConfig`. Cached in the kernel `SwrCache` (tree 5 minutes, page 60 s, search 60 s) with a job-runner refresh of the tree for configured spaces; **page bodies are memory only** (R2). Routes under `/api/v1/confluence/…` returning DTOs, never raw responses. Tests use synthetic responses only. |
| **C1** | ✅ | ADF to HTML renderer | C0 | **high** | sonnet/high | fa8ee78..223e075 | `src/render/adf/`: ADF → hast → HTML with an **allowlist**, styled with the same tokens as `Prose` so a page reads like a Notes page. Nodes: paragraphs, headings, bold, italic, strike, code, links (https, mailto and Confluence-relative only, `rel="noopener noreferrer"`), bullet, ordered and task lists, blockquote, rule, code blocks (language label), tables (header rows, colspan and rowspan, column widths), panels (info, note, warning, success, error), status lozenges, dates, emoji, mentions (display name only), expand (as `<details>`), table of contents (an outline of the page), layout sections and columns (stacked on narrow screens), inline and block cards (a link card), Jira issue macros (an orient ticket link through `entity-href`), the Lucid macro (a card with the document title and **Open in Lucid**), media (through the C2 proxy). **Anything else is a visible placeholder** (\"Unsupported: <node type> — open in Confluence\"), never dropped silently and never raw HTML. Fixtures are **synthetic ADF written by hand** covering each node type (R2: no real Confluence content in the repo). Security review in the lane (R1). |
| **C1b** | ⬜ | Render off the event loop | C1 | med | sonnet/high | | **Proposed 2026-11-13 by the C1 review.** C1's renderer runs synchronously in orient-core's cache loader, the same process as `:3000`, PR-approve and Slack-post. Its output budget now keeps any page under about 100 ms and about 150 MB. As defence in depth against a future renderer bug, run `withHtml` in a long-lived `worker_threads` worker: `resourceLimits` (for example 256 MB), a time limit, request ids, respawn after a timeout or crash, and the page copied across (up to 8 MiB). That is about 120 lines plus tests. |
| **C2** | 🟨 | Media and attachments proxy | C0 | **high** | sonnet/high | | `GET /api/v1/confluence/media/<pageId>/<attachmentId>`: fetches with the credential, a content-type allowlist (png, jpeg, gif, webp; **no SVG, HTML or anything active**), a size cap, `X-Content-Type-Options: nosniff`, a restrictive `Content-Security-Policy: sandbox`, no cookies, `Cache-Control: private`; the same stored-XSS class as Notes N9a (a same-origin script on :3000 reaches the PR-approve and Slack-post routes), so mind `frameGuard` clobbering the CSP header (test through `createCore().app.request`). A page's image placeholder when the attachment is refused. Security review in the lane (R1). |
| **C3** | ⬜ | Space tabs, tree, page view, search | C0, C1, C2 | med | sonnet/high | | The workspace's space switcher lists the configured Confluence spaces as tabs after Notes, Incidents and Soaks (Fuse, Merak). Inside a tab: the page tree (lazy children, collapse state in the address, reusing the NV2 sidebar and tree), breadcrumbs from the page's ancestors, a page view with the title, a real byline (author and last updated from Confluence), labels, the rendered body, and **Open in Confluence** (and an \"Edit in Confluence\" link: no editing here), the space's home page, search scoped to the space (CQL: title and text) and a Recently updated list. Pages the user cannot see show a clear \"no access\", not an error. Addresses stay stable (`/notes?space=<tab>&page=<id>`, decide the exact form and keep it). 390 px, keyboard and touch like the rest of the workspace. |
| **C4** | ⬜ | Confluence links open in orient | C3 | low | sonnet/medium | | A Confluence page URL (`…/wiki/spaces/<key>/pages/<id>/<slug>`) found in a note, a ticket description, a Slack summary or the vault resolves to the in-orient page when its space is a configured tab, following the rule in `CLAUDE.md` that every mention of a named thing links to its address; a small \"↗ Confluence\" affordance keeps the original one click away. Pages in unconfigured spaces still link out. |

### Later, each behind a decision
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **C5** | ⏸ | Create and edit Confluence pages from orient | C3 | **high** | opus/high | | **Deferred behind G2.** Writing means ADF editing that preserves every node orient does not understand byte for byte (macros, extensions, layouts); the Atlassian MCP drops macros when a page goes through markdown, so markdown must never be the write path. A Confluence-flavoured use of the W-series editor would need an ADF ↔ editor model, which is a large unit of its own. Likely a link out to Confluence's own editor stays the answer. |
| **C6** | ⏸ | Confluence titles in global search and the MCP | C3 | med | sonnet/medium | | **Deferred.** Needs a decision on keeping Confluence titles (not bodies) in the local index, and on who may read them through the MCP. |

## Gates
- [x] **G1 — The credential orient holds reaches Confluence** — blocks C0. Cleared 2026-11-12: a read-only probe through `jiraCredentials()` and `jiraApiBase()` got HTTP 200 from the v2 spaces and pages endpoints (Bifrost and Merak) and the v1 CQL search. No new token or scope is needed.
- [ ] **G2 — Decision: may orient write to Confluence?** — blocks C5. Harry's call; the recommendation is no, and to link out to Confluence's editor.

## Risks
- **R1 ★ Third-party content rendered in orient** — page bodies and attachments are written by many people. A same-origin script on :3000 reaches the PR-approve and Slack-post routes. Mitigation: an allowlist ADF renderer with no raw HTML, hrefs restricted to https, mailto and Confluence-relative links, `rel="noopener noreferrer"`, images only through a proxy with a content-type allowlist, `nosniff`, a sandbox CSP and no SVG; security lens in the review of C1 and C2 — open.
- **R2 ★ Company documents in a personal repo, logs and snapshots** — the orient repo is on a personal GitHub account and the pages are Global Freight documents (some may hold customer data). Mitigation: fixtures are synthetic ADF; no page body, title or id in a log line, a test, a committed file, a Sync disk snapshot (S3) or the SQLite index; bodies live in the memory cache only; only the space tree (titles and ids) may be cached longer, and not on disk until a decision — open.
- **R3 ADF breadth** — Confluence has many macros and extensions. Mitigation: a coverage list, placeholders with an \"Open in Confluence\" link for the rest, never silent loss — open.
- **R4 Rate limits** — Confluence Cloud limits are cost-based. Mitigation: the SWR cache, a lazy tree (children on demand), `Retry-After` honoured, no bulk crawl, no per-page fan-out on load — open.
- **R5 Permissions** — the credential is Harry's, so orient shows what he can see; restricted pages answer 403/404. Mitigation: a \"no access\" state, never an error page; single-user behind the tunnel as today — standing.
- **R6 Staleness** — an edit in Confluence is not seen at once. Mitigation: page TTL 60 s, the `version.number` shown, a Refresh button — standing.

## Decision log
<!-- Dated, newest first. -->
- **2026-11-13** — **C1 done and live at 223e075** (fa8ee78..223e075: 12 commits, opus builder). **Confluence pages render as safe HTML.**
  - **What was built:** an allowlist renderer, ADF → hast → HTML, in `src/render/adf/`.
    - **Links:** hrefs limited to `https`, `mailto` (the address only) and the site, all `rel="noopener noreferrer"`.
    - **Enforcement:** an element, attribute and id allowlist is enforced on the final tree.
    - **Input handling:** only an object's own keys are read; control and bidi characters are stripped.
    - **Coverage:** text and marks (known colours become tokens), lists, code blocks (no copy button), tables (head and row headers, spans, up to 200 columns, row numbers), panels as Notes callouts, expands as `<details>`, layouts, status, date, emoji and mention as text, the three card kinds, Jira issue macros as orient ticket links, Lucid as a card, the table of contents. Anything else is a visible "Unsupported: <type>" placeholder; a bodied macro's body still renders.
    - **Media:** placeholders carrying checked file and collection ids, for C2.
    - **Where it renders:** `html` is rendered once per load in the core and held in the memory cache only. **`body` is no longer sent.**
  - **Review (security, R1; correctness and capacity) — the security lens found no script, `javascript:` navigation, CSS or URL load** across about 45 href-smuggling variants and hostile strings in every attribute position, run through jsdom.
  - **It did find denial of service in the core,** with working PoCs. Rendering is synchronous in orient-core, which serves `:3000`, PR-approve and Slack-post:
    - 1000 TOC × 1000 headings: 62 MB, 6.5 s, 1.6 GB; at 2000 × 2000 **orient-core died out of memory**;
    - 12k identical headings: about 11 s of quadratic id de-duplication;
    - a crafted table: a million `<col>`s, or a RangeError that blanked the page.
  - **Fixed with one page-wide output budget**: every emitted element, attribute and text node counts, with caps of 30k units and 1.5 MB, and the page ends with "too large to show here". Also: the TOC built once and capped at 500; an id counter per base; 200 columns per table; no spreads of data-sized arrays (a parser test bans them; there were 33); spacing inside containers; row headers styled; row numbers kept.
  - **After the fixes:** every PoC renders in 12–85 ms, and any page at the caps in under 100 ms. 33 tests failed first; 26 of 28 mutants are killed.
  - **Not built here:** a worker with `resourceLimits`, now **C1b**.
  - **Gates:** typecheck 0, lint 44, 676 tests across 7 files.
  - **Live check** (counts and type names only, per R2):
    - 10 real pages answer in 0.11–0.25 s cold, with HTML of 2.7–56 KB, no `body` and no `<script`;
    - across 50 pages in both spaces, the only placeholder is `extension:recently-updated`, once.
  - **Next:** C2, the media proxy, which maps ADF file ids to attachments through the page's attachments list.
- **2026-11-13** — **C0 done and live at 512155a** (85e2d50..512155a: 6 commits, sonnet builder). **orient reads Confluence, read-only.**
  - **What was built:**
    - **The adapter** (`src/adapters/confluence.ts`) makes GETs only, to the Jira site's own origin.
      - Every redirect is refused. A `next` link must keep its endpoint's path exactly.
      - An 8 MiB body cap (an oversize body is cancelled through its reader).
      - 15 s per request and 20 s per list, across retries. `Retry-After` is honoured in its seconds and date forms, capped.
      - Failures carry a kind and a fixed message, and never content.
    - **Config:** `confluence.spaces` in the vault config, defaulting to Fuse (Bifrost) and Merak (MP), with ids and keys validated. Invalid or repeated entries are dropped.
    - **Routes** under `/api/v1/confluence` return DTOs: spaces, space pages, space search (CQL escaped), page, children and attachments.
      - Everything is held in the kernel's memory cache (tree 5 min, page and search 60 s), with LRU-capped keys. A test pins that the three files import no fs, sqlite or child process.
      - A refusal never replaces good data. A first refusal is held 30 s.
      - A cold read answers "unavailable" at 15 s.
      - `/spaces` answers from config without waiting on Confluence.
    - **`webUrl`** is built from the site, the configured key and the numeric id, never from `webui`.
  - **Review (backend and security) found 8 issues, all fixed with tests failing first** (synthetic only; 41, 13 and 18 failed before, plus 9 foreign-page route tests):
    - **the page, children and attachments routes served any page id in the org** (Harry's token reaches every space), so a loopback caller or a same-origin script could sweep HR, legal or finance pages. They now answer not-found outside the configured spaces, after a body-less read of the page's space, and nothing of a foreign page is fetched or held;
    - **one bad config section reset the whole vault config** (`loadVaultConfig` fell back to `parse({})`), which drops the `sensitive` globs and `contextExcluded`, so sensitive documents could reach Today and prompt context. This existed for every section before C0; C0's strict section made it easier to trigger. **Each section now falls back on its own**;
    - a 401 or 403 overwrote good cached data for the full TTL;
    - there was no overall deadline (up to 176 s), and `/spaces` waited on Confluence;
    - the `Retry-After` date and negative forms were ignored;
    - a locked stream was never cancelled;
    - a `next` link could steer to another `/wiki/` endpoint;
    - `webUrl` was taken from the response.
  - **Gates:** typecheck 0, lint 44, 358 tests across the touched files. The live vault config loads every section as before (checked by section shape, values not printed).
  - **Live check** (`:3000`, counts and shapes only, nothing of content printed, per R2):
    - `/spaces` gives 2 spaces;
    - each tree has 1 top-level page;
    - each home page loads with `author`, `updatedBy`, `createdAt`, `version` and an ADF body (about 9.6 KB and 8.1 KB);
    - children: 11 and 5;
    - attachments answer;
    - search for a common word gives 25 hits;
    - an unknown page is not-found, and a traversal-shaped id gives 404.
  - **Next:** C1, the ADF renderer (R1 starred, opus).
- **2026-11-12** — **C0 to C3 move back by two units.** Harry asked for a drag-and-drop whiteboard and agreed to put the Whiteboard canvas (B2, B3) first: Notes W3 → W4 → editor `/ux-review` → Whiteboard B2 → B3 → Notes NV1 → NV2 → **Confluence C0 to C3** → Notes W2 → NV3 → Confluence C4 → Sync S1 to S5. The programmes now run autonomously (Harry: "happy for you to just run with this autonomously"); G2 still stops for him.
- **2026-11-12** — **Order agreed (Harry: "yeah - we can get the editing experience nailed prior to rendering confluence").** One builder at a time: Whiteboard B1 (in flight) → Notes W1 → W3 → W4 → NV1 → NV2 → **Confluence C0 to C3** → Whiteboard B2, B3 → Notes W2 → NV3 → Confluence C4 → Sync S1 to S5.
- **2026-11-12** — **Programme opened.** Harry: \"something to plan on - tabs for confluence spaces (ideally fuse + merak at a minimum)\". Checked before planning: \"Fuse\" is the **Bifrost** space (the `create-pr` skill writes the Fuse changelog pages under spaceId 4587524; the space named \"Fuse (Bifrost)\", key `Fuse`, is archived), Merak is `MP` (alias `MPK`); orient has no Confluence client; the credential orient already uses for Jira reaches Confluence (probe: 200 on v2 spaces and pages and on CQL search), so G1 is cleared and no new token is needed. Read-only first; writing is G2. Proposed order across programmes, one builder at a time: Whiteboard B1 (in flight) → Notes W1 → W3 → W4 → NV1 → NV2 → **Confluence C0 to C3** → Whiteboard B2, B3 → Notes W2 → NV3 → Confluence C4 → Sync S1 to S5, waiting for Harry's yes. Why after NV2: C3 reuses its sidebar and tree, so building it first would be done twice.

## Scar tissue
- **No real Confluence content in the repo, its tests, logs, committed fixtures or a disk snapshot** (R2).
- **Read-only**: the client only GETs, to one host.
- **Everything Confluence returns is untrusted** (R1).
- **No git worktrees** (`CLAUDE.md:22`); one builder at a time across programmes.
