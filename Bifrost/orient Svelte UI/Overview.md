---
title: "orient Svelte UI — Overview"
status: active
verdict: undecided
owner: "hjf"
services: ["orient"]
created: "2026-11-10"
updated: "2026-11-10"
tags: [bifrost]
---
# orient Svelte UI — Overview

## Deliverables
- [[orient Svelte UI/Migration State|Migration State]] — the live source of truth for progress
- [[orient Svelte UI/Design|Design]] — the architecture, reviewed; its corrections header overrides the draft below it
- A core service (`src/core/`, Hono, one process on 127.0.0.1) over orient's existing framework-free logic
- A Svelte 5 UI (`ui/`, SvelteKit, SSR off) with orient's current look, page for page
- Next.js, React and `src/components/` removed

## Verdict
Undecided until **G1**: the measured `/today` spike (U5) passes its budget table and Harry, having used it for a full digest day, calls it terminal-fast. Go means "continue to the shared foundations (U6–U12)", not "committed to every wave"; **G5** is the second checkpoint before the cutover.

## Why this needs a programme
orient is ~90k lines with 56 pages; the UI half (~41k lines) is rewritten, the logic half is kept. The Next UI is frozen meanwhile (orient `CLAUDE.md`), so the migration has to keep moving. It touches the security boundary (Host/Origin checks that today come partly from Next for free), outside contracts (desk, scribe, `/api/write`, ~335 vault links to `localhost:3000/...`), and the deploy and systemd layout.

## Strategy
Measure Next first (U0), then a spike: the core serves `/today`'s data from a stale-while-revalidate cache and markdown as cached HTML; a Svelte `/today` renders it (U1–U5). If G1 passes, build the shared foundations: full renderer parity, logic decoupled from React, the keyboard layer, palette, quick view and terminal, the outside contracts and a proxy, all on side ports (U6–U12). Cutover (U13): the core takes `:3000` and proxies unmigrated pages to Next on `:3001`, so every URL keeps working. Then pages move in waves (W-*), each ending with its routes in `migrated-routes` and its Next files deleted. Retire Next last.

**Measured on 2026-11-10, VM, Next `/today`:** ~0.7 s server time every visit (`force-dynamic`), 1.48 MB per load (≈740 KB HTML + the same again as RSC payload), ~7,400 elements, the markdown pipeline re-run for every todo, the nav built twice. U0 re-measures this formally.

## Scar tissue
- Page URLs are a durable contract: every route keeps its path (vault links, desk, scribe).
- Nothing binds anything but 127.0.0.1; every route refuses a non-loopback Host. The browser never sees the write token or the scribe hub token.
- `index.sqlite`'s schema is guarded by the MCP server: no new tables there; caches get their own database.
- Same look: orient's design language (`design/`, Engineering/orient/design.md) carries over; improvements welcome as pages move.

## Next
U0 (bench harness + Next baseline) and U1 (core kernel) can start in parallel. Drive with `waypoint-programme` ("orient Svelte UI").
