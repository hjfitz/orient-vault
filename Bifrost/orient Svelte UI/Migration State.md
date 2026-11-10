---
title: orient Svelte UI — Migration State
programme: orient-svelte-ui
status: active
owner: hjf
services:
- orient
created: '2026-11-10'
updated: '2026-11-10'
tags:
- bifrost
- migration-state
---
# orient Svelte UI — Migration State

<!-- The single source of truth for PROGRESS. The Overview carries the narrative and the verdict;
     this doc is the live ledger a session reads to know what is done and what is next.
     `wp programme status/next/tick` read and write the `## Unit status` tables below, so keep the
     table shape intact. Architecture and the review corrections: [[orient Svelte UI/Design|Design]]. -->

orient has no PRs or CI: a unit ships as commits on `master`, pushed, then deployed. The `PR` column holds the commit range.

## Unit status
Legend: ⬜ not started · 🟨 in progress · ✅ merged · ⛔ blocked · ⏸ deferred · ❌ dropped · 🔄 rescoped

### Spike — measure, then prove `/today`
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **U0** | 🟨 | Bench harness + Next baseline |  | low | sonnet/medium | | `bench/` on the VM: scratch vault copy (own `ORIENT_VAULT`/state/records dirs, sync off, Jira unreachable via scratch `config.yaml`), existing `.next-prod` on :3005, `playwright-core` + Chromium. Measures server time (warm/cold/after a digest change/Jira down, on the VM and through the tunnel), transfer, DOM size, interaction latency (Event Timing + LoAF, 1× and 4× CPU) and navigation. Writes `bench/baseline.json`. Verified by two runs agreeing within 10%. |
| **U1** | ✅ | Core kernel subset |  | med | opus/high | 8918859..96bca5a | `src/core/`: Hono on 127.0.0.1 (refuses 0.0.0.0/::), Host guard (421), write guard (loopback Origin + JSON + `X-Orient`, analytics exempt from the header), SWR cache with tags, invalidation via `getDb` (inode-aware) + `data_version`, SSE `/api/v1/events`, static serving, `wx` write-token minting. Verified by a guard test matrix (bad Host, cross-origin POST, missing header) and an invalidation test that survives `index:build`'s rename. |
| **U2** | 🟨 | Today module + ops | U1 | med | sonnet/high | | `GET /api/v1/today` from `src/domain/today.ts` loaders, slow sources (Jira, health, `wp`, services) served from cache with `asOf`; fold bodies; tick/defer/seen ops (defer from `reader-actions`). Verified by a data-parity vitest on the scratch vault (needs, todos, sprint, owed, decisions counts equal the loaders'). |
| **U3** | ✅ | `renderHtml` subset (hast → HTML) | U1 | med | sonnet/high | 4419122..2bf4578 | Built to be extended by U6, not thrown away. Wikilinks, mentions, links, callouts, td tone, read-only checkboxes, `orient-action`/`orient-data` as HTML with `data-*` hooks, mermaid placeholder, `<pre>` fallback. Content-hash cache with the full key. Verified by snapshot tests + a grep proving today's digest and todos use no unsupported fence kind. |
| **U4** | ⬜ | Svelte shell + `/today` + guard rails | U0, U2, U3 | med | sonnet/medium | | `ui/` SvelteKit SPA on :3030: nav once, `g` chords, `/today` with the same look, native `<details>` folds, `?todos=all`, optimistic tick/defer with rollback, allowlisted persistence (today only). Guard rails from the first build: no `+*.server.ts`, Vite import guard, bundle secret grep, `svelte-check` in `scripts/check.sh`. Verified by those checks + a rollback-on-5xx test. |
| **U5** | ⬜ | Spike measurement + report | U4 | low | sonnet/medium | | Run the bench against core+Svelte with the same harness and data as U0; fill the pass table below; write the report into the Decision log. Feeds G1. |

### Foundations — on side ports, after G1
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **U6** | ⬜ | Renderer parity, MDX, render cache | U3 | high | opus/high | | Explainer blocks and diagrams (with `diagram-presets` icons), all of `OrientActions`, WikiLink incl. the Notes branch, MDX via a hast runtime that calls `components`, `PromptBuilder` as an island; `render-cache.sqlite` (own DB) + `linkGen`. Verified by a parity harness over every indexed doc against `renderDocument` (text, hrefs, hook counts). Updates CLAUDE.md's render-boundary rule. |
| **U7** | ⬜ | Decouple logic from React/Next |  | med | sonnet/medium | | The 7 runtime couplings (`cache` → `src/lib/memo.ts`, reader-ops split, hast runtime), type-only edges into `src/api/types/`, `unified-diff` into `src/lib`, every action file split into an op + thin `'use server'` wrapper. Verified by an esbuild import-graph test (no react/next/components/app from `src/core/main.ts`) + full typecheck/tests + a 200 sweep of Next routes. |
| **U8** | ⬜ | Keyboard layer + help overlay | U4 | med | sonnet/high | | One capture-phase listener, scoped stack, typing detection, chord timeout, generated `?` overlay; carries all 7 global listeners' bindings and coexists with the ~12 local key handlers. Verified by a Playwright keymap suite incl. the local handlers. |
| **U9** | ⬜ | Palette, quick view, layout globals, SSE | U6, U8 | med | sonnet/medium | | `/api/v1/palette`, quick view (native, or iframe `?embed=1` for Next pages), FocusEffects/SoundHost (same localStorage keys), PageTracker, IndexBanner, not-found/loading, titles; SSE invalidation replaces the 39 polling sites as pages move. |
| **U10** | ⬜ | Terminal panel | U8 | high | opus/high | | xterm, ticket via the core, tmux endpoints; ctrl+` passes through the keymap. Verified by Playwright: open, type, paste, resize, reattach. |
| **U11** | ⬜ | Outside contracts on a side port | U7 | med | sonnet/medium | | desk (`/api/desk`, `/api/desk/act` + bearer), recordings (`glossary`, `upcoming`, audio with Range), `/api/write` — same paths. Verified by desk and `orient-scribe enhance -orient` against the side port. |
| **U12** | ⬜ | Proxy + `migrated-routes` on a side port | U7, U11 | high | opus/high | | Streams RSC unbuffered, passes encoding and Range, keeps Host for server actions; one route list shared by the core and the SPA's links. Verified by a curl matrix (Host `evil.test` → 421 everywhere, Next pages included) and a server action through the proxy. |

### Cutover
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **U13** | ⬜ | Core takes :3000, Next to :3001 | U9, U10, U12 | high | opus/high | | `orient-core.service`, `orient-web` on :3001, `deploy:core`/`deploy:ui`, `install-units.sh` (peer branch stops orient-core too), `/` and `/today` served by Svelte, tunnel unchanged (3000/3011/3014). Updates CLAUDE.md (ports, redeploy rules) and docs/INSTALL.md. Verified by desk, scribe, terminal and a Next server action working through :3000, and the guard matrix. |

### Waves — one plan each on promotion; each starts with a generated feature inventory and ends with its routes in `migrated-routes` and its Next files deleted
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **W-A1** | ⬜ | `[view]` slugs, search, notes | U13 | med | sonnet/medium | | First wide consumer of the U6 renderer. |
| **W-A2** | ⬜ | `doc/[id]` + editor | W-A1 | high | opus/high | | CodeMirror and the conflict dialog. |
| **W-B** | ⬜ | Delivery: sprint, runs, backlog, epics, PRs, tickets, ledger, tasks | U13 | med | sonnet/medium | | Run-spawning ops move into the core's cgroup; updates the `/sprint` restart rule. |
| **W-C** | ⬜ | PR review + CI logs | W-B | high | opus/high | | `components/pr` (2.9k lines), ReviewProvider/SuggestionReview keys, approval path. |
| **W-D1** | ⬜ | Work, plans, programmes | W-A1 | med | sonnet/medium | | `/plans` is 0.77 s / 1.25 MB today. |
| **W-D2** | ⬜ | Systems, services, people, customers, team, skills, tools, diagrams | W-A1 | low | sonnet/medium | | `PromptBuilder` island on tools. |
| **W-E** | ⬜ | Prod: health, incidents, support, maintenance, soaks, monitors, availability | W-A1 | low | sonnet/low | | |
| **W-F** | ⬜ | Meetings, recordings, Slack, haude | W-A1 | med | sonnet/medium | | Recordings: 14 actions, audio player, relay. |
| **W-G** | ⬜ | History, usage, analytics, focus, puzzles | W-A1 | med | sonnet/medium | | History access gate and redaction; chessground. |
| **Retire** | ⬜ | Remove Next, React, `src/components` | W-A2, W-B, W-C, W-D1, W-D2, W-E, W-F, W-G | med | sonnet/medium | | Drop deps, `renderDocument.tsx`, `orient-web` from install-units; rewrite CLAUDE.md invariants. |

## Spike budgets
U5 fills this; all must hold for G1. U0 fills the baseline column.

| Metric | Next baseline | Pass |
| --- | --- | --- |
| `/today` data warm p95, VM / via tunnel | U0 | ≤ 50 ms / ≤ 100 ms |
| First request after a digest change | U0 | ≤ 150 ms |
| Jira unreachable | U0 | ≤ 50 ms, section marked unavailable with `asOf` |
| Cold-load transfer (gzip) | U0 | ≤ 250 KB |
| Repeat visit | U0 | data only; assets immutable |
| DOM elements | U0 | ≤ 2,000 |
| Interaction p75 / max, 1× | U0 | ≤ 50 ms / ≤ 100 ms, no LoAF > 50 ms in an interaction |
| Interaction p75, 4× CPU | U0 | ≤ 100 ms |
| Keypress to `/today` painted, data cached | U0 | ≤ 100 ms |

## Gates
- [ ] **G1 — Spike go/no-go** — blocks U6, U7, U8. U5's pass table holds and Harry, after a full digest day on `:3030/today`, calls it terminal-fast. No-go if interaction or navigation budgets fail while server and payload pass: stop and report; keep the core's cache for Next.
- [x] **G2 — Mac decided** — blocks U13. Does a Mac still run orient, and how is it launched? CLAUDE.md and desk/README.md still say it does; the 2026-11-09 ledger retired the laptop's own orient. Cleared 2026-11-10: no Mac runs orient; a future Mac would use the VM's through the tunnel. Docs corrected.
- [x] **G3 — LAN IP in `ptyAllowedHosts`** — blocks U13. `192.168.1.210` is a default in `src/config.ts`; it also gates `/history` and the terminal origin. Drop it, or say what still needs it. Cleared 2026-11-10: drop it (Harry). Removed in U13 with the Host guard work.
- [x] **G4 — Headless runs survive a core restart** — blocks W-B. `KillMode=process` on `orient-core` keeps detached runs alive and retires the "check /sprint before restarting" rule. Cleared 2026-11-10: no headless runs during the migration (Harry), so restarts are safe; no `KillMode` change. The `/sprint` rule stays for after.
- [ ] **G5 — Foundations used for a day on the side port** — blocks U13. Shell, palette, quick view and terminal in daily use before `:3000` flips.
- [x] **G6 — Cross-framework hops accepted** — blocks U13. Between the cutover and each page's wave, moving between a Svelte page and a Next page is a full page load: music and ambient sound stop, unsent drafts are lost, the terminal reattaches. Accept it, or move Focus/Sound earlier. Cleared 2026-11-10: accepted (Harry uses YouTube Music and another pomodoro timer meanwhile).
- [x] **G7 — Phone viewing** — blocks U4. design.md judges layouts at phone width too, and the phone reaches orient through Termius. Desktop-only (drops the duplicate mobile nav) or keep a phone layout? Cleared 2026-11-10: desktop only (Harry seldom works from the phone; a phone recorder page may come back on its own later).
- [ ] **G8 — A week on the full Svelte UI** — blocks Retire.

## Risks
- **R1 ★ CSRF and Host** — Next's server-action Origin check goes away; the core's Host and write guards cover every route from U1, proxied Next pages included (U12). Today most Next routes don't check Host at all — the core is stricter. — open.
- **R2 ★ Secrets in the client bundle** — `config.ts` holds `GITHUB_TOKEN`, the write token, the pty secret. Vite import guard + bundle grep run in `scripts/check.sh` from U4. — open.
- **R3 ★ Features that exist only as JSX** — layout globals, loading/not-found, metadata, `?embed=1`, implicit freshness after writes, hover cards. Each wave starts from a generated feature inventory. — open.
- **R4 Index rebuild renames the file** — any long-lived reader must go through `getDb`'s inode check. — open.
- **R5 Two caches during the transition** — Next and the core both poll Jira/GitHub/`wp`; double external calls and ~2× memory until Retire. — standing.
- **R6 Proxy correctness** — unbuffered RSC streaming, encodings, Host for actions, Range for audio. — open.
- **R7 Render-cache staleness** — a missed `linkGen` input serves stale link resolution; the parity harness and a `RENDERER_VERSION` bump discipline cover it. — open.

## Decision log
- **2026-11-10** — U1 review: a local process can forge the browser write headers (Origin, X-Orient). Accepted: each machine has one login user (harry on the VM, hjf on the laptop), and any process running as them can read the 0600 write token anyway — the guards exist for browsers (CSRF, DNS rebinding, framing), not for the local user. Revisit if a second user is ever added.
- **2026-11-10** — Gates G2, G3, G4, G6, G7 answered by Harry (see Gates). Desktop-only UI; cross-framework full-page hops accepted; no Mac; LAN IP dropped; no headless runs during the migration. Programme active.
- **2026-11-10** — Swap the UI framework for a Svelte 5 SPA over a standalone core service, keeping the look. Why: input lag Harry feels in every Next/React UI; measured `/today` at ~0.7 s server time per visit, 1.48 MB, ~7,400 elements, markdown re-run per todo. One core process (modules registered with a small kernel), not microservices.
- **2026-11-10** — Next.js UI frozen: fixes only until a page moves (orient `CLAUDE.md`, ccafb1c).
- **2026-11-10** — Phone recorder plan abandoned (not in use); the spike port is 3030, not the probe's 3020.
- **2026-11-10** — Units ship to `master` like the rest of orient (no PRs); the `PR` column holds commit ranges.

## Scar tissue
- Page URLs are a durable contract (~335 vault links to `localhost:3000/...` in 24 files; desk and scribe call fixed paths) — every route keeps its path.
- `index.sqlite`'s schema is guarded by `mcp/` (`src/index/schema.sql`) — caches get their own database, never a new table there.
- Loopback only: nothing binds 0.0.0.0; new ports (3001, 3005, 3025, 3030) join CLAUDE.md's loopback list when introduced.
- The browser never sees the write token or the scribe hub token.
- Folds are native `<details>` and view state lives in the URL (search params) — design-language rules, not implementation choices.
- `wp` ignores `ORIENT_VAULT`: anything that shells out to it reads the real vault.
