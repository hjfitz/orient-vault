---
title: "orient Svelte UI — Design"
owner: "hjf"
services: ["orient"]
created: "2026-11-10"
tags: [bifrost]
---
# orient Svelte UI — Design

> Drafted 2026-11-10 by a planning agent from source, then reviewed on three axes (history, factual grounding, increment structure). **The corrections below override the text that follows them**; the unit list and gates in [[orient Svelte UI/Migration State|Migration State]] replace §3–§4's increments and waves.
>
> **Corrections from review**
> - **Dropped 2026-11-10 (Harry): the in-browser terminal and preset prompting.** Ignore everything below about the terminal panel, xterm, the pty ticket, `/api/tmux/*`, `data-send-terminal`/`data-copy` hooks, `CopyPrompt`, `PromptBuilder`, `/tools`, and MDX via a hast runtime: none of it is built. `.mdx` renders as source.
> - **Index rebuild renames the file.** The core must read `index.sqlite` through `getDb` (`src/index/db.ts`, inode check), not its own connection, and treat a rebuild as a full invalidation. `PRAGMA data_version` alone misses it.
> - **Analytics:** `PageTracker` uses `sendBeacon`, which can't set `X-Orient`. Exempt `/api/analytics` from that header (Origin + Content-Type still checked).
> - **Write token:** `orientWriteToken()` mints non-exclusively; mint with `flag: 'wx'` and re-read, so Next and the core can't race (the laptop desk 401 hazard).
> - **Folds stay native `<details>`** (fragment links into a closed fold must open it); their bodies are cached HTML, so rendering them is cheap. "Show more" goes in the URL (`?todos=all`). URL state uses search params, not SvelteKit shallow-routing `page.state` (lost on reload).
> - **Client persistence is an allowlist:** persist `/today` only, never `/history`, recordings or sensitive globs; prefetch only allowlisted pages; own IndexedDB name. A failed refresh still shows "unavailable — detail" with `asOf`, never silent stale data.
> - **Spike port 3030**, not 3020 (the phone probe's). Dogfood through an ad-hoc `ssh -L 3030`, not by editing `orient-tunnel` (restarting it drops terminals and scribe uploads). Add every new port (3001, 3005, 3025, 3030) to CLAUDE.md's loopback-only invariant.
> - **Bench isolation is partial:** `wp` ignores `ORIENT_VAULT` and reads the real vault (read-only; say so). Make Jira unreachable via `external.jiraBase` in the scratch `.knowledge/config.yaml` (`secretVar` falls back to `~/.secrets`, so env overrides don't). Set `ORIENT_SCRIBE_URL`, `ORIENT_WRITE_TOKEN`, `ORIENT_PTY_SECRET` for scratch instances. Measure through the tunnel as well as on the VM. The bench runs **on the VM** (the laptop is a tunnel peer). No Next control arm: it would add code under `app/today/`, which the freeze forbids.
> - **Pass table is like-for-like:** end-to-end time-to-painted for both; the Next baseline is measured by U0 before anything is built, not quoted. Optimistic tick needs a rollback-on-5xx test.
> - **`renderHtml` inputs** include `title`, `ticket`, `serviceHref`, `trustedMdx`, `mdxComponents` — all in the cache key. Parity covers WikiLink's Notes branch (`noteHref`) and diagram icons (`diagram-presets`). The MDX hast runtime must itself invoke function components from the `components` map.
> - **Keymap:** ~12 components have local key handlers (FocusSuggest arrows, Slack composer, audio scrubber, popovers, games) that a capture-phase global listener would pre-empt — test those too. Space is a `/focus` binding that ignores BUTTON/A targets.
> - **`src/lib` is not 57/58 pure:** `pty-ticket.ts` (node:crypto), `review-prompt.ts` and `suggestion-window.ts` (value imports from `@/domain/unified-diff`), `terminal-store.ts` (`'use client'`). Keep the UI import allowlist explicit; move `unified-diff` into `src/lib`; the guard ignores `import type`.
> - **Counts:** 135 `server-only` files; 20 `'use server'` files (18 action files + `reader-actions` + `tool-actions`), 85 exported actions; 56 pages incl. `/` (add it to the cutover unit); 22 API `route.ts` — not "~150 routes". `deferTodo` lives in `src/edit/reader-actions.ts`.
> - **New dependencies:** `hono`, `@hono/node-server`, `hast-util-to-html`, `hastscript`, `esbuild` (direct, for the import-graph test), `playwright-core`, SvelteKit/Svelte 5/Vite.
> - **CLAUDE.md rules change as units land,** not at retirement: "one render boundary" at U6, the restart/`/sprint` rule when run ops move (W-B).
> - **Hard navigation across frameworks** (until the cutover's proxy and each wave) ends music/ambient sound and unsent drafts (design.md, "Sound outlives the page"). Svelte must reuse the exact localStorage keys (`orient.focus.notify`, `.ambient`, `.follow`) on the shared `:3000` origin.
> - The vault holds ~335 absolute `localhost:3000/...` links in 24 files: **page URLs are a durable contract**; every route keeps its path.

# Draft: move orient's UI to a Svelte 5 SPA backed by a standalone core service

## 0. What the repo actually looks like

These findings change parts of the brief.

1. **There is no middleware or proxy file, so nothing refuses a non-loopback Host globally.** `proxy.ts` and `middleware.ts` don't exist. Today's protection is:
   - binding to 127.0.0.1 (in `systemd/orient-web.service` and the `package.json` scripts);
   - Next's built-in server-action check, which compares Origin with Host;
   - per-route checks in a handful of places:
     - `app/api/write/route.ts` and `app/api/tmux/ticket/route.ts`, against `ptyAllowedHosts`;
     - `app/api/desk/act/route.ts`, against `hostAllowed(['127.0.0.1','localhost'])` plus the bearer write token;
     - `app/api/pr-ci/log/route.ts`;
     - `src/actions/notes.ts` and `app/history/access.ts`, through `src/lib/allowed-host.ts`.

   So every other page and GET route answers any Host, which leaves them open to DNS rebinding. Also, `ptyAllowedHosts` (`src/config.ts`) still defaults to include the LAN IP `192.168.1.210`. The core must add a guard that applies to everything, which is stricter than today.
2. **Seven files in the logic dirs depend on React or Next at runtime, plus seven type-only imports:**

   | File | Coupling | How it decouples |
   |---|---|---|
   | `src/domain/ticket-prs.ts` | `cache` from react | A small `memo(fn, {ttlMs: 2000})` in `src/lib/memo.ts`. It works in both Next and the core and dedupes within one render or request burst. |
   | `src/domain/system-health.ts` | `cache` from react | Same. |
   | `src/edit/reader-actions.ts` | `'use server'` and `revalidatePath` | Split into `src/edit/reader-ops.ts` (plain functions that return `TickOutcome`) and a thin Next wrapper in `src/actions/reader.ts`. |
   | `src/render/renderDocument.tsx` | `react/jsx-runtime`, `toJsxRuntime` | Stays for Next until Next retires. The core gets a new `src/render/html/renderHtml.ts` (hast to HTML string). |
   | `src/render/md/components.tsx` | The React component map | Becomes hast transforms in `src/render/html/blocks.ts` (built with hastscript). |
   | `src/render/mdx/compile.ts` | `react/jsx-runtime` passed to `run()` | `run()` takes a small JSX runtime that builds hast (`src/render/mdx/hast-runtime.ts`). |
   | `src/domain/tool-actions.ts` | A `'use server'` directive only | Harmless in the core. Its Next caller stays as it is. |

   The type-only imports run from logic files into `@/components`: `ChipTone` in `lib/recordings.ts`, `domain/pr-ci.ts` and `lib/jira-status-tone.ts`; `ContextQuery` in `domain/meeting.ts` and `domain/plan-doc.ts`; `LinkTarget` in `domain/links.ts`; `Palette*` in `app/api/palette/route.ts`. Move these types into a new `src/api/types/` so the logic layer has no edge into `components/`.

   The other 18 action files (`src/actions/*`, `app/today/actions.ts`, `app/doc/[id]/actions.ts`) and `src/actions/notes.ts` (which uses `next/headers`) follow the same split: an *op* that holds the logic, and a Next wrapper that adds `'use server'` and `revalidatePath`. That is 85 exported actions in total.
3. **`server-only` is imported by 130 logic files and throws unless the `react-server` export condition is set.** Every tsx script already runs with `NODE_OPTIONS=--conditions=react-server`, and vitest aliases it to `empty.js`. The core does the same. Once the React imports above are gone, running under `react-server` is harmless.
4. **Most of the "MDX lag" is the markdown pipeline, not MDX.**
   - The vault has 1,339 `.md` files and only 8 `.mdx` files, all under `Prompts/`. Those are the only ones executed (`src/render/mdx/trust.ts`), and they use one component, `<PromptBuilder>`. Its props are JS literals, and it is interactive: a form, a live template, copy, and re-running queries through `runToolQueries`.
   - On `/today`, `CarriedTodos` and `NeedsChecklist` call `InlineMarkdown` for **every todo and child**. Each call runs `renderDocument`, which means the whole unified pipeline plus `linkableTerms()` plus `repoPullBaseMap()`, hundreds of times per request, with no cache.
   - The vault's "custom tags" are fenced blocks (`orient-action`, `orient-data`, `orient-bluf`, `orient-evidence`, `orient-flow`, `orient-sequence`, `mermaid`) and the remark plugins in `src/render/md/plugins/*`. Each recent digest has about 9–11 orient blocks.
   - Interactive pieces:
     - **mention links:** hover card and open-beside (`MentionLink`, which uses `next/link`);
     - **mermaid:** rendered client-side;
     - **`orient-action` buttons:** `CopyPrompt`, and `SendToTerminal` (which goes through `lib/terminal-store`);
     - **`PromptBuilder`.**

     Everything else is static. That includes the flow and sequence SVGs, which `flow-layout.ts` computes on the server.
5. **Headless Claude runs are detached and keep their state in files** (`src/adapters/headless.ts`), so any process can start or read them. They still die when the cgroup of the service that spawned them stops.
6. **Outside callers of the HTTP API on :3000** must keep working:
   - `desk/` calls `GET /api/desk` and `POST /api/desk/act` with the write token, via `desk/cmd/orient-desk/main.go`, which defaults to `http://127.0.0.1:3000`.
   - `scribe/` calls `/api/recordings/upcoming` (`internal/remind`) and `/api/recordings/glossary` (`internal/enhance`).
   - Skills and CLI tools use `/api/write`.
   - Vault links are written with `orientUrl = localhost:3000`.
   - The MCP server (`mcp/`, Go) reads `index.sqlite` read-only and doesn't touch Next. Its schema guard reads `src/index/schema.sql`, so **don't add tables to index.sqlite**.
7. **The browser never sees the scribe hub token today.** Nothing in `src/` or `app/` reads it; it's scribe-to-scribe only. Keep it that way: the core never reads `~/.config/orient/scribe-hub-token`.
8. **There is no SSE or streaming today.** Freshness comes from 39 `setInterval`/`router.refresh()` sites and from `revalidatePath` after writes. The adapters already hold in-process TTL caches (`src/adapters/exec.ts` `ttlMs`, the Jira `TTL_MS` maps), but requests still await them.

## 1. Target architecture

### Core service (`src/core/`, one Node process)

The core lives under `src/` so the `@/` alias, the `server-only` handling and vitest work unchanged.

- **Kernel (`src/core/kernel/`):**
  - `server.ts`: Hono on `@hono/node-server`, binding only to `127.0.0.1`. It refuses to start if given `0.0.0.0` or `::`.
  - **Host guard:** every request, proxied ones included, must have Host in `{127.0.0.1, localhost, [::1]}` plus the core's port, or it gets a 421.
  - **Write guard:** every non-GET request from a browser must:
    - carry an `Origin` whose hostname is loopback and whose port is the core's;
    - be `Content-Type: application/json` (cross-origin calls then need a preflight, which gets no CORS headers);
    - send `X-Orient: 1`.

    This replaces the Origin check Next's server actions gave for free.
  - **Token guard:** `/api/desk/act` and `/api/write` keep the bearer `orientWriteToken()`, which is the same file both processes read. The token is never served to a browser.
  - **`cache.ts`:** a keyed stale-while-revalidate store with tags.
    - A request always gets the cached value immediately, and a refresh runs in the background.
    - `data_version.ts` checks `PRAGMA data_version` on its read-only connection every ~250 ms. When the watcher commits, it diffs `documents.indexed_at`, so a vault change becomes `doc:<id>` and `type:<t>` invalidations.
  - **`events.ts`:** one SSE stream, `GET /api/v1/events`, that pushes `{tags}` to the browser.
  - **`registry.ts`:** each module is `{ name, mount(app, kernel), start?(kernel), health?() }`, mounted at `/api/v1/<name>`. Each module's `start` owns its background refresh (for example, Jira every 5 min, `wp fleet` every 5 min).
  - **`proxy.ts`:** sends every path not in `migrated-routes` to Next upstream. It keeps the Host header so Next's own action check still passes, streams the body and doesn't re-encode it.
  - `static.ts`: serves the SPA build. Hashed assets are `immutable`. Paths in `migrated-routes` get `index.html`.
- **Modules (`src/core/modules/`):** vault/docs plus render, today, search/palette, jira, github/pr, datadog/health, wp (fleet/doctor/stale), slack, scribe/recordings, terminal (tmux and pty ticket), focus, puzzles, usage/sessions, desk, runs (ticket-run, epic-run, ci-agent), notes/edit, people/customers/entities, tools/prompt.
- **Contract (`src/api/types/*.ts`):** plain DTO types imported by both sides, plus a route-to-type map so a ~60-line typed `fetch` client (`ui/src/lib/api.ts`) gets end-to-end types. I recommend this over Hono RPC (`hc<AppType>`) because inferring types across ~150 routes slows `svelte-check`/`tsc` badly, and it would pull the server's import graph into UI type-checking.

### UI (`ui/`, SvelteKit in SPA mode)

- `adapter-static` with `fallback: 'index.html'`. The root `+layout.ts` sets `ssr = false` and `prerender = false`. The build goes to `ui/build/` and the core serves it.
- **Guard rails:**
  - A test fails if any `+*.server.ts` or `hooks.server.ts` exists.
  - A Vite `resolveId` plugin throws on imports of `server-only`, `node:*`, `better-sqlite3`, `@/config`, `@/adapters/*`, `@/domain/*`, `@/index/*` or `@/edit/*`. The UI may import only `src/api/types` and an allowlist of pure `src/lib/*` modules (57 of the 58 are pure, for example `entity-href.ts`, `quick-view.ts`, `palette.ts`, `dates.ts`, `cn.ts`).
- **Client cache (`ui/src/lib/data.svelte.ts`, about 200 lines, runes):** `query(key, {tags})`, stale-while-revalidate, dedupe, `optimistic(key, patch)` with rollback, tag invalidation from SSE, and an idle prefetch of every nav page's data after first paint. The last snapshot is persisted to IndexedDB so a reload paints instantly.
- **Keyboard layer (`ui/src/lib/keymap.ts`):** one capture-phase `keydown` listener on `window` and a stack of scopes: global, page, overlay (palette, quick view, terminal), then modal.
  - Each binding is declared as `{keys: 'g t' | 'ctrl+k' | 'space', scope, when?, run}`.
  - One place decides "is the user typing", and one place runs the 1 s chord timeout.
  - A generated `?` help overlay lists every binding.
  - When the terminal has focus, everything passes through except `ctrl+\``, which the xterm `attachCustomKeyEventHandler` forwards to the keymap.
- **Desktop only:** the nav renders once, with no `<details>` mobile copy.
- **Markdown arrives as HTML strings** in JSON and is inserted with `{@html}` inside a `use:prose` action. That action is one delegated handler set:
  - `a[data-opens-beside]`: hover card and quick view;
  - `[data-copy]`: copy;
  - `[data-send-terminal]`: send to the terminal;
  - `pre[data-mermaid]`: lazily imports mermaid when visible.

  Islands that need real components (todo checkboxes, `PromptBuilder`) are separate Svelte components mounted over `div[data-island]` placeholders.

### Rendering and its cache

- `renderHtml({path, source, docId})` takes `markdownToHast` (reused unchanged from `src/render/md/pipeline.ts`), applies the hast block transforms and serialises with `hast-util-to-html`.
- **Cache key:** `sha256(RENDERER_VERSION | path | docId | linkGen | text)`.
  - `linkGen` is a hash of the live `(id, path, title)`, aliases, entities and `repoPullBaseMap`. It is recomputed only when `data_version` changes, because wikilink and mention resolution depend on *other* documents.
- **Storage:** an in-memory LRU, backed by a disposable `~/.local/state/orient/render-cache.sqlite`. It is a separate database, so the index schema and the MCP schema guard are untouched.
- **Warming:** when the latest digest changes, the core re-renders it in the background, so the first visit after `/morning-digest` is already warm.
- **I chose lazy rendering plus warming in the core over rendering at index time.** At index time, the watcher would have to re-render every time a title changed elsewhere in the vault.
- **MDX:** compiled once per content hash with the hast runtime. `PromptBuilder` becomes `div[data-island="prompt-builder"][data-props=<json>]`. Execution stays limited to the trusted `Prompts/` folder, as now.

## 2. How the two apps coexist

| Phase | Ports | What the browser uses | Tunnel (`systemd/orient-tunnel.service`) |
|---|---|---|---|
| Spike (I0) | Next :3000 (unchanged), core :3020 | `:3020/today` for the trial; links to other pages are absolute to `http://${location.hostname}:3000/...` | Add `-L 127.0.0.1:3020:127.0.0.1:3020` (check 3020 is free on the laptop: one taken port fails the whole tunnel because of `ExitOnForwardFailure`) |
| Front door (I3 onwards) | **core :3000**, Next :3001 (internal) | Everything on :3000. The core serves migrated routes and proxies the rest, `/_next/*` and server actions to :3001. Links are same-origin and relative. | Back to 3000/3011/3014; drop 3020 |
| Retired | core :3000 only | — | Unchanged |

- **One source of truth for routing:** `src/api/migrated-routes.ts`. The core uses it to decide "serve the SPA or proxy". The SPA's `href()` helper and a `beforeNavigate` hook use it to decide client-side navigation versus `location.assign` (a full load). That makes cross-framework links deterministic instead of depending on SvelteKit's unknown-route fallback.
- **Quick view:** iframes `?embed=1` for pages still on Next. Because everything is same-origin behind the proxy, the `postMessage` origin check in `QuickView`/`lib/quick-view.ts` keeps working. Migrated targets render natively, with no iframe.
- **Terminal:**
  - The pty server on :3011 is unchanged. Its origin check matches only the hostname, so any orient port passes.
  - The ticket comes from `/api/v1/terminal/ticket`, behind the Host guard. The Next route stays until retirement.
  - Expect the terminal to reattach (the tmux session survives) on every hard navigation between frameworks.
- **Server actions stay in Next pages until those pages move.** Each Next action and each core endpoint calls the same op, so they can't diverge. The SPA never calls Next action IDs, which are build-specific.
- **Deploy:**
  - `pnpm deploy:web` keeps building Next into `.next-prod`. After I3 it restarts `orient-web` on :3001. While that runs, the core serves migrated pages and a 503 "Next is rebuilding" for the rest.
  - New `pnpm deploy:ui` runs `vite build` into `ui/.build-tmp` and then atomically renames it to `ui/build`. No restart, no downtime.
  - New `pnpm deploy:core` runs `systemctl --user restart orient-core`, which takes about 1–2 s.
- **Units:**
  - New `systemd/orient-core.service`: `pnpm core`, i.e. `NODE_OPTIONS=--conditions=react-server tsx src/core/main.ts`, with `ORIENT_CORE_PORT` and `ORIENT_NEXT_UPSTREAM` set.
  - `orient-web.service` moves to `-p 3001` in I3.
  - `scripts/install-units.sh`:
    - adds orient-core to the non-peer `UNITS`;
    - in peer mode, adds orient-core to the stop-and-disable loop;
    - at retirement, disables orient-web and removes its unit file, mirroring what the existing peer block does.
  - **Decision for the owner:** `KillMode=process` on orient-core, so detached headless runs survive a core restart. This would remove the rule "check /sprint before restarting".
- **Mac:** it runs its own orient without systemd (CLAUDE.md). How it is launched isn't in this repo; confirm before I3.

## 3. Increments for this plan

### I0. Measured spike: core `/today` data plus a Svelte `/today` (decides go/no-go)

**Build:**
- **Kernel subset:** Host guard, write guard, cache, `data_version` watcher, SSE, static serving.
- **today module:** `GET /api/v1/today` returns the same fields `app/today/page.tsx` assembles, built from the same `src/domain/today.ts` loaders.
  - Jira, `healthTrend`, `wp` (fleet/doctor/stale) and `serviceHealth` are served from the stale-while-revalidate cache with an `asOf` timestamp, so the request never awaits them.
  - Todo and need text is pre-rendered to inline HTML through `renderHtml`.
  - Fold bodies (deploy skew, nightly, GitHub, reply queue, prod health) come from `GET /api/v1/today/fold/:name`, loaded on first open and prefetched when idle.
- `POST /api/v1/docs/:id/tick`: an op over `tickTask` that returns the new `hash`, so the client can tick again immediately.
- `POST /api/v1/todos/defer` and `POST /api/v1/today/seen`.
- **Renderer subset:**
  - wikilinks, mention and plain links, callout, table/td tone, read-only checkboxes;
  - `orient-action` and `orient-data` as static HTML with `data-copy`/`data-send-terminal`;
  - mermaid as a placeholder;
  - anything else falls back to `<pre>`.
- **UI:** SvelteKit SPA with a minimal shell (nav rendered once, `g` chords) and `/today`.
  - Shows 10 todos; the rest render only when "show more" is clicked, not merely hidden.
  - Optimistic tick and defer.
  - Folds render nothing until opened.
- **Bench harness (`bench/`):**
  - Add `playwright-core` as a dev dependency and install Chromium only (`playwright install chromium`, about 150 MB).
  - It runs against a **scratch vault**: `cp -a` of the vault into the scratchpad, and its own `ORIENT_VAULT`, `ORIENT_STATE_DIR`, `ORIENT_RECORDS_DIR` and `ORIENT_VAULT_SYNC=off`, with `pnpm index:build`.
  - Two instances: the existing `.next-prod` build via `next start -p 3005` with that environment (no rebuild needed), and the core on :3025.
  - Nothing touches the real vault.

**Measuring, repeatably:**
- **Server time:**
  - `curl -w '%{time_starttransfer}'`, 30 warm requests, p50 and p95, for Next `/today` versus core `/api/v1/today`.
  - The same after `touch`ing the digest, to measure the first request after a change.
  - The same with Jira made unreachable through an environment override, to prove responses don't block on it.
  - The core emits `Server-Timing` per section.
- **Payload:** Playwright collects CDP `Network.loadingFinished.encodedDataLength`, summed per resource type, on a cold load and on a repeat visit, both compressed and raw.
- **DOM size:** `document.getElementsByTagName('*').length` once the page has settled.
- **Interaction latency:**
  - Inject a `PerformanceObserver({type:'event', durationThreshold:16, buffered:true})` and group entries by `interactionId`. Also observe `long-animation-frame`.
  - Script about 30 interactions: ctrl+k then type `plan` and Esc; `g t` from a blank stub route (`/spike/blank` in the SPA, `/tasks` on Next, the cheapest page there); tick a todo; "show more"; open and close three folds; space for the focus timer.
  - Report p75 and max duration per interaction type.
  - Run 5 repetitions at 1× and at 4× CDP CPU throttling.
  - Save `context.tracing` zips for inspection.
- **Navigation:** time from the `t` keydown to the Today `h1` plus the first section painted, using a `performance.mark` in the SPA and a MutationObserver for Next.
- **Optional control arm:** Next `/today` reading the same cached loaders behind `ORIENT_TODAY_CACHE=1`. It shows how much of the gain is the cache and how much is the framework. This is for information only and doesn't decide anything.

**Pass criteria (all must hold to continue):**

| Metric | Next baseline | Pass |
|---|---|---|
| `/api/v1/today` warm p95 (VM) | ~700 ms | ≤ 50 ms |
| First request after a digest change | ~700 ms | ≤ 150 ms |
| With Jira down | blocks or errors | ≤ 50 ms, section marked stale or unavailable |
| Cold-load transfer (gzip, JS+CSS+JSON) | 1.48 MB raw HTML+RSC | ≤ 250 KB; today JSON ≤ 200 KB raw |
| Repeat-visit transfer | full page | JSON only (assets 304 or immutable) |
| DOM elements | ~7,400 | ≤ 2,000 |
| Interaction p75 / max (1×) | measured | ≤ 50 ms / ≤ 100 ms, no LoAF > 50 ms during an interaction |
| Interaction p75 (4×) | measured | ≤ 100 ms |
| `g t` to painted, data cached | measured | ≤ 100 ms |
| Todo tick to painted | measured | ≤ 32 ms, independent of the server |
| Data parity | — | Counts of needs, todos, sprint tickets, owed and decisions equal the domain loaders' output on the scratch vault (vitest) |

- **Go:** all of the above hold, *and* the owner uses `:3020/today` for two working days and calls it terminal-fast.
- **No-go:** the interaction or navigation criteria fail while the server and payload criteria pass. Then stop and report. The cache layer is still worth keeping for Next.

### I1. HTML renderer at full parity and the render cache

- Port the remaining render components to hast transforms:
  - `ExplainerBlocks` (BLUF, evidence with drift);
  - `ExplainerDiagrams` (flow and sequence SVG, 634 lines; layout already lives in `flow-layout.ts`);
  - `OrientActions` (all 417 lines);
  - `WikiLink` and `Callout`;
  - the `td` tone map.
- Port MDX with the hast runtime and the `PromptBuilder` island placeholder.
- Add the persistent render-cache database and `linkGen`.
- **Verification:** a parity harness renders **every indexed document** with both `renderDocument` (React, via `renderToStaticMarkup` in vitest, where the component tests already run) and `renderHtml`. It compares normalised text, the set of `href`s, and the count of each `data-*` hook. Zero diffs, or diffs listed and accepted. Also a benchmark: a cached render of the largest doc in ≤ 1 ms, an uncached one recorded.

### I2. Decouple the logic layer and split ops from actions

- Make the seven file changes in the table in section 0.
- Move the type-only imports into `src/api/types/`.
- For all 19 action files, split each into `src/ops/<area>.ts` (logic) and the existing `'use server'` wrapper (which only adds `revalidatePath`). Move the logic that lives inside routes (`parseWriteRequest`, desk act, palette candidates) into ops as well.
- **Verification:**
  - A test builds the esbuild metafile for `src/core/main.ts` and fails if `react`, `react-dom`, `next/*`, `@/components/*` or `app/*` appears in the import graph.
  - `pnpm typecheck && pnpm test` pass.
  - Next behaviour is unchanged: a smoke `curl` of every route returns 200.

### I3. Core as the front door on :3000, with Next behind it on :3001

- **Proxy and routing:** the proxy plus `migrated-routes`.
- **Modules for the outside contracts:** desk (`/api/desk`, `/api/desk/act`), recordings (`/glossary`, `/upcoming`, `/[id]/audio` with Range passed through) and `/api/write`. These move to native core modules at the same paths, so desk and scribe need no change.
- **Ops:** unit changes, `install-units.sh`, deploy scripts and the tunnel, as in section 2.
- **Docs:** update `CLAUDE.md` (redeploy rules, render boundary, the two-process period) and `docs/INSTALL.md`.
- **Verification:**
  - A curl matrix sends `Host: evil.test` to every path, Next pages included, and expects 421.
  - A cross-origin POST without `X-Orient` gets 403.
  - Desk buttons work, `orient-scribe enhance -orient` fetches the glossary, and a Next page's server action (for example, ticking a todo on `/doc/[id]`) works through the proxy.
  - The bundle-leak test greps `ui/build` for `GITHUB_TOKEN`, `write-token`, `pty-secret`, `hub-token`, `.secrets` and the literal value of the token file.

### I4. Shell parity in Svelte

- The full keymap. Register every binding from today's 7 listeners: CommandPalette (ctrl+k, Esc, Tab), Chords, TerminalPanel (ctrl+\`), FocusTimer (space), QuickView (Esc), and the bindings of ReviewProvider and SuggestionReview, kept for the PR wave.
- Command palette on `/api/v1/palette` (port `app/api/palette` and `palette/ticket`).
- Quick view, native or iframe.
- Terminal panel: xterm, the ticket, and the tmux select/ensure/window/paste endpoints.
- SSE-driven invalidation in place of the polling.
- The layout-level globals that exist only as JSX: `FocusEffects`, `SoundHost`, `PageTracker` (analytics beacon to `/api/analytics`), `IndexBanner`, the not-found and loading states, a per-route `document.title` via `viewTitle`, and `?embed=1`.
- **Verification:** a Playwright keymap suite (every binding fires once and only in its scope; typing in an input never triggers chords; the terminal swallows keys except ctrl+\`), and the bench budgets re-run on `/today` with the full shell.

## 4. The remaining ~55 pages: run them as a Waypoint programme

This plan covers I0–I4. Run the page migration as a **multi-unit programme**, one unit per wave, each with its own plan. Every wave has the same definition of done:

- **Before porting:** generate a per-page *feature inventory* from the JSX: each interactive element, action call, `searchParams` key, keybinding, empty or error state, and `generateMetadata`. This stops features that exist only as JSX from being lost.
- **During:** pull non-trivial logic out of components into `src/lib` with tests first; transliterate the markup (Tailwind classes copy across verbatim); port the component tests to `@testing-library/svelte`.
- **After:** the bench budgets pass on the wave's heaviest page; the paths are added to `migrated-routes`; the Next files for those pages are deleted.

| Wave | Pages | Main risk |
|---|---|---|
| A: Reading | `[view]` (covers about 20 nav slugs), `doc/[id]`, `doc/[id]/edit` (CodeMirror), `search`, `notes`, `notes/edit`, `doc/resolve` | The editor and the conflict dialog |
| B: Delivery | `sprint`, `sprint/run/[id]`, `backlog`, `epics`, `prs`, `tickets`, `tickets/[ticket]`, `jira/[key]`, `ledger`, `runs`, `tasks` | Run-spawning ops now live in the core's cgroup |
| C: PR review | `pr/.../[number]`, `ci/[run]` (`components/pr`, 2.9k lines) | ReviewProvider and SuggestionReview keyboard, PR approval through the token |
| D: Plans and knowledge | `work`, `plans`, `plan/[slug]`, `programmes`, `programme/[slug]`, `systems`, `service/[name]`, `people`, `person/[slug]`, `customer/[id]`, `team`, `diagrams`, `skills`, `skills/[name]`, `tools`, `tools/[id]` | `/plans` is 0.77 s and 1.25 MB; the PromptBuilder island |
| E: Prod | `health`, `incidents`, `support`, `maintenance`, `soaks`, `monitors`, `availability` | — |
| F: Meetings and comms | `meetings`, `meeting/[slug]`, `recordings`, `recordings/[id]`, `slack`, `haude` | Recordings has 14 actions, an audio player and the relay |
| G: Personal | `history`, `history/[id]` (redaction and host gate), `usage`, `analytics`, `focus`, `puzzles` (chessground) | The history access gate |
| Retire | — | Remove `next`, `react`, `react-dom`, `cmdk`, `lucide-react`, `@testing-library/react`, `renderDocument.tsx`, `md/components.tsx` and `src/components`; remove `orient-web` from `install-units`; rewrite the `CLAUDE.md` invariants |

## 5. Trade-offs

- **SvelteKit SPA versus plain Svelte + Vite.** I recommend SvelteKit in SPA mode.
  - **For it:**
    - File routes map one-to-one from `app/`, which makes porting mechanical.
    - It splits code per route and preloads on hover or intent (`data-sveltekit-preload-code`).
    - `pushState`/`replaceState` with shallow routing suits the URL-held state that CLAUDE.md requires ("every view state lives in the URL").
    - `beforeNavigate` makes the cross-framework routing switch easy.
  - **Against it:** a server-side story that invites misuse. The guard test and having no SvelteKit server at all (adapter-static, served by the core) remove that.
  - **Plain Vite** would need a hand-written router of about 150 lines, plus preloading and scroll restoration. It's viable, but there are 56 routes with dynamic segments.
- **Hono versus node:http versus Fastify.**
  - **Hono:** small, composable middleware for the guards, `app.route()` gives the module mounting, has a proxy helper, and needs no plugin ceremony. I recommend it.
  - **Fastify:** its encapsulated plugins are a real microkernel, but its schema-first style duplicates zod, and the framework is heavier.
  - **node:http:** no dependencies, but you would hand-roll routing, bodies, SSE and the proxy, which is about 500 lines of infrastructure to own.
- **HTML strings versus Svelte components for markdown.** I recommend HTML strings.
  - They can be cached once per content change, cost no per-node component overhead, and take an O(1) delegated listener set.
  - Only the genuine islands (checkboxes, `PromptBuilder`) are components.
  - **Cost:** the render components get ported once (I1), and `{@html}` needs care. The input is trusted vault content that is already the source of truth, and the trusted-folder MDX rule stays.
  - **Short-cut rejected:** `renderToStaticMarkup` of the existing React components. `WikiLink` and `MentionLink` import `next/link`, and it would keep React in the core.
- **Reuse versus rewrite of `src/components`.** Reuse the logic by extracting it to `src/lib` (all 57 pure modules there are already importable) and transliterate the markup. Don't attempt automated JSX-to-Svelte conversion.
- **Keeping Next server actions during the transition.** Yes, as thin wrappers over shared ops. That's the cheapest way to have one behaviour and two front ends.
- **Client cache: custom versus TanStack Query (Svelte).** Start custom: the spike needs only stale-while-revalidate, tags and optimistic updates with rollback. Revisit TanStack if the cache grows past about 300 lines.

## 6. Risks

1. **Auth and CSRF.** The core loses Next's Origin check on writes, so the write guard is mandatory from I0. Without it, a malicious tab could POST to 127.0.0.1 with a valid Host. The Host guard must also cover proxied Next pages, and `192.168.1.210` in `ptyAllowedHosts` should be dropped or justified. The write token stays server-to-server.
2. **Terminal.** It reconnects on every cross-framework hard navigation, xterm and the central keymap conflict, and the ticket endpoint now sits behind a different guard. Test ctrl+\`, paste and resize explicitly in I4.
3. **Command palette.** It mixes navigation targets across both apps (through `migrated-routes`). Its reindex-then-`router.refresh` becomes an SSE invalidation.
4. **Server-only secrets in the client bundle.** `config.ts` holds `GITHUB_TOKEN` (read from `~/.secrets`), the write token and the pty secret. The Vite resolve guard and the bundle grep test cover it, and they must run in `scripts/check.sh` (add `svelte-check`, the UI tests and the bundle check there).
5. **Features that exist only as JSX.** Layout globals, `loading.tsx`, `not-found.tsx`, `generateMetadata`, `?embed=1`, `revalidatePath`'s implicit "fresh after write", and the hover cards. The per-page inventory is the defence.
6. **Headless runs and cgroups.** Once the run ops move into the core (wave B), restarting orient-core kills runs unless `KillMode=process`.
7. **Two caches during the transition.** Next and the core each poll Jira, GitHub and `wp`, which doubles the external calls and adds memory (Next ~300–500 MB plus the core). It's acceptable but should be watched.
8. **Proxy correctness.** It must not buffer RSC streams, must pass `content-encoding` through, must keep Host for actions, and must handle Range for audio.
9. **Freshness of the render cache.** A missed `linkGen` input gives stale link resolution. The parity harness and the `RENDERER_VERSION` bump discipline cover it.
10. **The benchmark touching the real vault.** The scratch-vault environment is mandatory, and the harness asserts `ORIENT_VAULT` isn't `~/Documents/obsidian`.
11. **The Mac.** Its orient isn't run by systemd, so the I3 unit changes don't cover it. Confirm how it is launched.

### Critical Files for Implementation
- /home/hjf/projects/orient/app/today/page.tsx (with /home/hjf/projects/orient/src/domain/today.ts)
- /home/hjf/projects/orient/src/render/renderDocument.tsx (with /home/hjf/projects/orient/src/render/md/components.tsx, /home/hjf/projects/orient/src/render/md/pipeline.ts and /home/hjf/projects/orient/src/render/mdx/compile.ts)
- /home/hjf/projects/orient/src/config.ts (ports, `ptyAllowedHosts`, `orientWriteToken`, secrets) and /home/hjf/projects/orient/src/lib/allowed-host.ts
- /home/hjf/projects/orient/src/edit/reader-actions.ts (the pattern for splitting ops from actions, and `tickTask` in /home/hjf/projects/orient/src/edit/save.ts)
- /home/hjf/projects/orient/systemd/orient-web.service, /home/hjf/projects/orient/systemd/orient-tunnel.service, /home/hjf/projects/orient/scripts/install-units.sh, /home/hjf/projects/orient/scripts/deploy-web.sh