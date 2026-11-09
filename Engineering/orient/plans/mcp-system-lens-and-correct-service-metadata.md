---
ticket: none
title: MCP system lens and correct service metadata
service: orient
status: active
created: '2026-11-06'
updated: '2026-11-06'
repo: /home/hjf/projects/orient
worktree: /home/hjf/projects/orient
branch: master
base: ad04890ed
base_sha: ad04890ed
pr: null
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: medium
---
# none — MCP system lens and correct service metadata

<!-- Guidance in this file is written as HTML comments: Obsidian hides them, agents read them,
     and `wp signoff` ignores them. Only <angle spans> are treated as unfilled placeholders, so
     they mark the places a human or agent must actually type something. Leave the comments in
     place — deleting them costs the next reader the guidance and gains nothing at the gate.

     SUPERSEDING A STATEMENT. This file is edited by several sessions over days. When something
     here stops being true, do NOT strike it through, delete it, or bury a correction inside it.
     Put one blockquote immediately ABOVE the stale text and leave the text alone:

         > SUPERSEDED 2026-09-04 — the monitor now lives in `gfs-bifrost/observability`.
         > Everything below is kept as the record of how it was first built here.

     One marker, always above, never inside. `wp decide` writes the dated entry in
     `## Decisions & deviations` that explains why. -->

## Intent
<!-- What we are changing and why. Link the ticket. -->
Out-of-ticket, asked for by Harry 2026-11-06. The orient MCP's `orient-entity` cannot look up a
Waypoint **system**, and its **service** header is wrong for every service onboarded through a
`wp onboard` skeleton (it shows `owner=bifrost`, no language/framework/deploy/system). The goal is
`orient-entity kind=system` for purpose, owner, members by type, docs and open unknowns. The service
header should show the real `waypoint.yaml` facts, and each service doc should carry the `wp doctor`
stale flag.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. After a re-index, `entities.sidecar` equals the `sidecars` table row for every service. In particular, `orient-entity service css` shows `owner=jez-poppleton language=csharp … system=selector`, and client4 and parcel-portal show their real yaml values.
- [x] 2. When a `waypoint.yaml` is rewritten after its entity row exists, re-indexing replaces the entity's sidecar. A writer test covers this.
- [x] 3. `orient-entity system selector` returns the purpose and owner from `system.yaml`, the members grouped by type with owners (css backend, client4 frontend, matching `wp system status selector`), the docs with verified dates, and the open `## Unknowns`.
- [x] 4. Service doc lines carry a stale marker when `wp doctor` flagged them (`documents.meta.attention`).
- [x] 5. The tool description, jsonschema, server instructions and `docs/mcp-spec.md` say person, service, system or customer, and the rebuilt binary is the one Claude Code launches.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `src/index/writer.ts` `writeDocument` entity merge (indexer, run by `orient-index.service` via tsx). It also feeds the web `/service` header (`src/domain/overviews.ts`).
- `mcp/internal/store/entity.go` (new `SystemMembers`, `Doc.Attention`), `mcp/internal/vault/` (new `system.go`: system.yaml + Unknowns), `mcp/internal/tools/entity.go`, `mcp/internal/bootstrap/server.go` (Instructions).
- `docs/mcp-spec.md` `orient-entity`. `src/domain/headless.ts` lists tool names only, so it gets a comment wording update only.
- Read-only throughout. No schema change: `sidecars` and `documents.meta` already hold what's needed.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- Root cause is `sidecar: found.sidecar ?? sidecar` (writer.ts). The first sidecar seen wins forever. The `sidecars` table holds the real yaml and 7 services diverge from it. Established by reading the source and diffing the live index.
- Membership lives only in each service's `waypoint.yaml` (`system:`), which the `sidecars` table already indexes. That is the same source as `wp system status`. Established from wp.py l.448 and the live query (2 members, matching wp).
- `system.yaml` is not indexed (only `.md`/`.mdx` and waypoint/customer yaml are), so the MCP reads it via its `vault` layer. That layer already exists for "things the index does not hold". A minimal top-level-scalar reader is enough: all 5 system.yaml files use plain scalars plus `purpose: >`. There is no Go yaml dependency.
- The stale flag uses the `wp doctor` verdict the watcher already stamps into `meta.attention`, so no git is needed in the MCP. It covers `Engineering/` docs only. System docs carry no `verified_sha` and are never stamped, so systems get no stale flag.

## Increments
<!-- Each independently implementable AND verifiable. Cite the criteria it discharges as
     (AC n,n). Tick with `wp tick`, which stamps `— done: <sha>` from HEAD; never hand-write it.
     Prefer 3-7 — more usually means the ticket is too big, so say that rather than splitting
     hairs.

     A PRECONDITION THAT IS NOT CODE goes on its own indented `gate:` line, with a confirmation
     box under it. Sign-off blocks on a ticked increment sitting above an unconfirmed gate, and
     `wp brief` shows unmet gates in its NEXT block — so "do not action this yet" stops being
     bold prose a fresh session can miss:

         - [ ] 6. Widen the subscription filter (AC 6) — verify: filter matches in dev
               gate: FUSE-1052 AND FUSE-1053 confirmed in prod
                     [ ] confirmed
-->

- [x] 1. Writer prefers the freshly parsed sidecar over the stored one (AC 2). Verify with a writer test (re-index with a changed sidecar replaces it), plus `pnpm typecheck`, `pnpm lint` and `pnpm test`. — writer tests + typecheck/lint/4736 tests green — done: b6e3fa7
- [x] 2. Re-index the live index (restart `orient-index` and sweep) (AC 1). Verify that no service's `entities.sidecar` differs from `sidecars.json`. — stopped watcher, one-off sweep (1115 docs) + attention stamp; 0 services where entities.sidecar != sidecars.json — done: 38061ee
- [x] 3. MCP `system` kind: store `SystemMembers`, vault `ReadSystem` (yaml + Unknowns), and `renderSystem` in the `renderFolder` style. Also update the description, jsonschema, Instructions and mcp-spec (AC 3,5). Verify with go tests in the existing style, `make vet test fmt-check lint`, and the live binary over stdio. — go vet/test/lint/fmt green; live binary over stdio shows selector members/docs/unknowns — done: 38061ee
- [x] 4. Per-doc stale marker from `meta.attention` on service doc lines (AC 4). Verify with a render test, and live with `orient` (design.md is STALE). — render tests; live: orient design.md STALE — done: 38061ee
- [x] 5. Rebuild `mcp/bin/orient-mcp` and `pnpm deploy:web` after the `/sprint` check (AC 1,5). Verify `orient-entity` live output for system selector and service css, and curl `/service/css`. — make build; deploy:web; /service/{css,client4,parcel-portal} 200, css shows jez-poppleton; live MCP output verified — done: 38061ee

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-11-06 [inc 5] `pnpm deploy:web`. `/service/css`, `/service/client4` and `/service/parcel-portal` return 200, and `/service/css` now renders `jez-poppleton`. The rebuilt `mcp/bin/orient-mcp` (the path `~/.claude.json` launches) answers over stdio with `service css`: `type=backend system=selector owner=jez-poppleton language=csharp framework=[asp.net asmx (.net framework 4.8.1), firebirdsql.data.firebirdclient] deploy=vm`. client4 shows `owner=jez-poppleton language=delphi system=selector`, and parcel-portal shows `owner=hjf language=[go, typescript] deploy=cloud-run`.
- 2026-11-06 [inc 3] Live `orient-entity system selector` over stdio returns owner=jez-poppleton, PURPOSE, `MEMBERS 2` (`backend: css (jez-poppleton)`, `frontend: client4 (jez-poppleton)`), matching `wp system status selector`. It also lists the 4 docs with `verified 2026-11-05`, and `UNKNOWNS 9`: the first 8, with the Billing group folded in, then "+1 more". Before this change the same call returned `kind "system" is not person, service or customer`.
- 2026-11-06 [inc 4] Live `orient-entity service orient` shows `design.md verified 2026-11-03@11aaab0 STALE`, matching `wp context orient` (STALE:1).
- 2026-11-06 [inc 2] Stopped `orient-index`, then ran one sweep (1115 docs) plus the attention stamp (79 flagged) against the live index, and restarted the watcher. Before, 7 services had `entities.sidecar` diverging from `sidecars.json` (tracking-service, css, client4, selector-rest-proxy, selector-adapter, parcel-portal, fuse-devtools); css had `owner bifrost`, null language/framework/deploy and no system. After, 0 diverge.
- 2026-11-06 [inc 1,3,4] review-panel (backend + tests, sonnet). Folded in: a missing `Systems/` dir now maps to not-found instead of a raw path error, a quoted ` #` and `null`/`~` are read correctly, non-not-exist read errors surface, membership drops a service whose folder no longer holds a live doc (the `sidecars` table is never pruned), a group bullet in Unknowns carries its children, and multi-assert tests were split. `go vet/test`, golangci-lint (0 issues), `pnpm typecheck`, biome, and vitest (247 files, 4736 tests) are green.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- The in-session `mcp__orient__orient-entity` tool. Running Claude Code sessions keep the old orient-mcp process until restarted, so verification went through the same binary over stdio instead.
- A yaml-only rewrite flowing through the running watcher end to end. This is covered by the writer test plus the watcher's existing force-reparse on sidecar change. It would be proved by the next `wp onboard` that fills in a skeleton.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-11-06** — Left active, not complete: the sole sign-off blocker is 2 uncommitted desk/gnome-extension paths owned by another session in this shared checkout (signoff has no path scope). Everything else passes (all 5 ACs and increments, diff vs ad04890ed reconciled, evidence filled, learning promoted, ledger written). Complete it with: wp plan set-status orient --plan mcp-system-lens-and-correct-service-metadata --status complete, once those desk edits are committed.

- **2026-11-06** — Re-index ran as a one-off scratch sweep (watcher stopped, then restarted), not a schema rebuild: startup only catches up changed files and the backstop sweep is 6h. No migration or data loss: sidecar is a JSON column rewritten in place. Systems get no stale flag: wp doctor covers Engineering/ only and system docs carry no verified_sha.
- 2026-11-06 — Planned without the Step 2 draft agent and Step 3 review trio. Harry asked for a proportionate plan for a small change. Factual grounding was done by reading the source directly, and history by grepping orient's design.md/ledger (no prior entry touches the sidecar merge or orient-entity).

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
(promoted to design.md ## Traps on 2026-11-06)
