---
title: Waypoint Programmes Formalisation — Migration State
programme: waypoint-programmes-formalisation
status: complete
owner: Harry Fitzgerald
services:
- waypoint-tooling
- orient
created: '2026-09-10'
updated: '2026-09-18'
tags:
- bifrost
- migration-state
---
# Waypoint Programmes Formalisation — Migration State

Making programmes first-class in Waypoint (template + `wp programme` + a generic `waypoint-programme`
skill + an orient detail view), the way plans already are. The first programme tracked in the new shape
— so it doubles as the worked example. Overview: [[Waypoint Programmes Formalisation/Overview|Overview]].

## Unit status
Legend: ⬜ not started · 🟨 in progress · ✅ merged · ⛔ blocked · ⏸ deferred · ❌ dropped · 🔄 rescoped

### Deliverable A — data model + `wp programme` tooling
| Unit | St | Summary | Deps | Risk | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| **P0** | ✅ | Ledger schema + templates | | low | | `templates/programme.md` + `programme-overview.md`; canonical ledger schema (Unit+St required, Deps powers `next`). |
| **P1** | ✅ | `wp programme new` scaffold | P0 | low | | `wp programme new <Name>` scaffolds `Bifrost/<Name>/` from template. |
| **P2** | ✅ | `status`/`next` ledger parse | P1 | med | | `wp programme status/next` — tolerant ledger parse; proven against real dedupe (23u) + shopify (48u). |
| **P3** | ✅ | `wp programme tick` | P1 | med | | `wp programme tick --unit --status [--pr]` — by-position cell edit, pipe-safe. |
| **P4** | ✅ | Unit-to-plan promotion | P0 | low | | `programme:`/`unit:` on `wp plan new` → a unit can be promoted to a plan (`wp fleet` renders `· prog/unit`). |

### Deliverable B — orient surfacing
| Unit | St | Summary | Deps | Risk | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| **O1** | ✅ | Gate/risk entry extractors | | med | | `programme-gate` + `programme-risk` entry extractors (`src/content/entries.ts` + kinds in `types.ts`). |
| **O2** | ✅ | Programme doc view + rollup | O1 | high | | `src/domain/programme-doc.ts` (`programmeDocView`) — progress rollup from `programme-unit` glyph counts, gates, risks, decisions, groups. |
| **O3** | ✅ | Programme doc reader | O2 | med | | `ProgrammeReader.tsx` wired into `app/doc/[id]/page.tsx` (4-type switch → 5). |
| **O4** | ✅ | Programmes list page | O2 | low | | `app/programmes/page.tsx` — per-row progress bar, counts and next-unblocked; verified against all six programmes. |

### Deliverable C — generic skill + migration (retire the five)
| Unit | St | Summary | Deps | Risk | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| **S1** | ✅ | `waypoint-programme` skill | P2 | high | | Write `waypoint-programme` — the 80% skeleton; per-programme 20% read from each State.md. |
| **S2** | ✅ | Prove on fuse-mocker-go | S1 | med | | Prove on **fuse-mocker-go** (complete, low risk); move specifics into its State.md; retire that bespoke skill. |
| **S3** | ✅ | Migrate secops-api-go | S2 | med | | Migrate secops-api-go, retire it. |
| **S4** | ✅ | Migrate fuse-mcp-go | S2 | med | | Migrate fuse-mcp-go, retire it. |
| **S5** | ✅ | Migrate shopify rearchitect | S2 | high | | Migrate shopify-connector-rearchitect (active), retire it. |
| **S6** | ✅ | Migrate dedupe migration | S2 | high | | Migrate dedupe-nest-migration (active), retire it. |

## Gates
- [x] **A0 — schema signed off** — the Migration State shape agreed before tooling built on it (Harry, 2026-09-10).
- [x] **Gate A — tolerant parser proven** — `status`/`next` parse the real dedupe + shopify ledgers; `tick` round-tripped on a scratch programme. Nothing migrates until this holds.
- [x] **Gate B — orient renders the programmes** — ProgrammeReader matches `wp` exactly (dedupe 18/23, shopify 5/48, mocker 26/27, mcp 17/19, secops 20/21); the Programmes list shows per-row progress.
- [x] **Gate C — surface progress in orient before retiring** — Harry set this as the sole condition for retiring the bespoke skills (2026-09-10). Met by O2–O4, so all five were retired; each one's specifics (cutover mechanism, invariants, scar tissue, PR discipline) were moved into its own State doc first, so nothing was lost.

## Risks
- **R1 ★** Tolerant parser misreads a hand-authored ledger — *mitigation:* proven read-side against the real dedupe + shopify docs (different columns/glyphs); `tick` edits cells by position so a Notes cell with a literal `|` is safe. *Status:* resolved for read + tick.
- **R2 ★** Migrating an active programme's skill loses hard-won scar tissue — *mitigation:* move each programme's specifics into its own State.md first, prove parity, retire the active ones (shopify, dedupe) last. *Status:* open.
- **R3** A programme with no `Deps` column gets an imprecise `next` (all todos) — *mitigation:* the template ships a Deps column; existing docs can add one when migrated. *Status:* accepted.

## Decision log
- **2026-09-10** — **Complete.** Harry set "surface programme progress in orient" as the sole condition for retiring the bespoke skills; met by the ProgrammeReader + the Programmes-list progress, so O4 was pulled in and all five skills (dedupe, shopify, fuse-mcp-go, fuse-mocker-go, secops-api-go) retired. Each one's load-bearing specifics were migrated into its own State doc first (one agent per programme) — most notably the dedupe **never-self-merge / draft-then-stop** PR discipline, which had lived only in the skill. `waypoint-programme` now drives all six via `wp programme`.
- **2026-09-10** — Shipped A + B(O1–O3) + C(S1) in one pass, verified end-to-end: `wp programme` parses all six real ledgers (dedupe 23, shopify 48, mocker 27, mcp 19, secops 21, this 15); orient's ProgrammeReader matches `wp` exactly.
- **2026-09-10** — Agreed (Harry): full build, sequenced, proven on one programme first · a unit stays a **ledger row** with optional promotion to a plan · migrate + retire the five bespoke skills incrementally.
- **2026-09-10** — Ledger schema is **tolerant, minimal-required**: only `Unit` + `St` (glyph); `Deps` powers `wp programme next`; everything else optional. So the two large hand-authored ledgers parse without a rewrite.

## Scar tissue
- **The Overview must NOT carry a `programme:` key or a `-state` tag** — only the Migration State doc is the ledger. Otherwise `iter_programmes()` yields both docs and the folder is seen twice (`find_programme` also collapses by folder defensively).
- **A frontmatter value that is a `{{token}}` must be the WHOLE value** — `title: {{name}} — Overview` JSON-quotes to `"…" — Overview`, invalid YAML. Use a per-doc `{{title}}` token.
- **`wp programme tick` edits table cells by pipe position, never split/rejoin the whole row** — a Notes cell can legally contain `|`, which would corrupt a naive rejoin.
