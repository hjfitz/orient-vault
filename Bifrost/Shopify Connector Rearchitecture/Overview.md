---
title: Shopify Connector Re-architecture — Overview
status: re-scoped-2026-08-21
owner: Harry Fitzgerald
created: '2026-07-24'
updated: '2026-08-24'
tags: [bifrost, shopify-connector, rearchitecture]
---

# Shopify Connector Re-architecture — Overview

Internal re-architecture of the `shopify-connector` NestJS service onto the org layering contract, plus a class-level rebalance. **Zero external-contract change** — routes, Pub/Sub subscriptions, topics, filters and envelope semantics identical throughout. That is *this programme's* constraint on itself, not a claim about the service: other people's work has changed the contract twice since the programme began (a subscription renamed + re-topiced + re-filtered, and Cloud Run scaling set fleet-wide), and the characterization net is structurally blind to both — hence the `CONTRACT-GOLDEN` unit.

**Resume with the `shopify-connector-rearchitect` Claude Code skill** — it rehydrates all of the below and reads current progress from [[Bifrost/Shopify Connector Rearchitecture/Migration State|Migration State]].

> [!warning] The plan was re-derived from scratch on 2026-08-21
> The tree moved a long way under the original plan: **+17% production code, 32 new files, a second permanent ingest path, and a live production tenant.** The **[architecture re-review](https://claude.ai/code/artifact/8c571cea-3f37-4a48-ab4a-e706bb0ecccd)** replaces the 2026-07-24 architecture review and is the document to plan from. The 38-unit execution plan remains the sequencing and risk framework, but **its unit ledger, line counts and `file:line` references are measured against a tree that no longer exists.**

## Where it stands

| | |
| --- | --- |
| **Merged** | `S0`, `S1` (characterization harness Phase 0 — [PR #231](https://github.com/gfs-bifrost/shopify-connector/pull/231), merged 2026-08-24) |
| **Done by others, no gate applied** | `D`, `F2`, `BUGFIX`(a), `PREVIEW-ISO`(a) — **four now** |
| **Retired as written** | `I`, `I2` (~5,000 lines — the plan's largest work) |
| **Re-scoped or collapsed** | `H1-COLLAPSE`, `H2-CONFIG`, `E`, `C-INGEST`, `C-CONFIRM`, `G2a`, `REHOME`, `J` |
| **Premise re-verified intact** | `K1`, `G2b`, `S5`, `S8`, `BUGFIX`(b), `L-PIN`, `L-SPLIT` |

## Deliverables

- **[[Bifrost/Shopify Connector Rearchitecture/Migration State|Migration State]]** — live status, corrections, gate, risk register, decision log (**source of truth for progress**).
- **Architecture re-review (2026-08-21) — read this first** — https://claude.ai/code/artifact/8c571cea-3f37-4a48-ab4a-e706bb0ecccd
- **Execution plan (38 units)** — sequencing + risk framework; unit ledger superseded by the re-review's §5 — https://claude.ai/code/artifact/2459f182-94eb-43e8-9550-4102bcba4f18
- **Characterization test plan** (the regression net; Phase 0 done, bulk coverage gap flagged) — https://claude.ai/code/artifact/825c4090-41a5-4c8a-92be-8f43d9e24adc
- **Safety-net hardening** (prove-the-net + telemetry surface) — https://claude.ai/code/artifact/bccc2fab-711a-473c-8b89-ae6fa252afcd
- **Program tracker** (web hub) — https://claude.ai/code/artifact/c9b89d5e-c70f-489f-8f55-a76a849a4a75
- ~~Architecture review (2026-07-24)~~ — **superseded**; its §10 external-contract pin is still valid, its class ledger is void — https://claude.ai/code/artifact/fed0d031-b595-4835-ba94-df8ea54f3abb

## The shape of it, after the re-review

The original diagnosis still holds — the service has the contract's layer *names* but not its layers. What changed is the **size and shape of the fix**. Measured against today's tree, there are **48 production-only layering violations in exactly two shapes**:

- **20 are a declaration in the wrong file**, and they split in two. **17** documents under `core/shopify/graph/**` import exactly one thing — the `ShopifyQuery`/`ShopifyMutation` type — and moving it is a pure file-location fix. The other **3** are `types.ts` files importing **port interfaces** (`IConfigApiAdapter`, `IShopifyStoreApi`), which is an ADR question — *where do ports live* — not a move. Do not bundle them.
- **28 fall on the same 12 classes**, every one the identical shape: an `@Injectable()` in `core/` that constructor-injects adapters. There is no core class that is framework-coupled but adapter-clean, or the reverse. **Eight are relocations, two need a real split, two need purifying — and "relocation" is not the same as safe.** Four of the eight sit on live runtime import cycles that close on an `@Inject()` decorator argument, which `tsc` cannot check; a ninth (`bulk-order-reaper`) has no `@Injectable()` at all and needs a deliberate factory rewrite.

So the class-level ledger is far smaller than "delete ~7, merge ~4, split ~9". Execution is still optimised to minimise **risk, not PR size**, and the **two bars** still apply — mechanical units need only `S0`, semantic units need the full gate.

## What changed underneath, and why it matters

- **R6 fired.** Prod now has one active Shopify connector (SAIRA). The programme began as internal-quality work with zero customer exposure; it no longer is. **R1 stops being hypothetical** — past the retrieval window, a missed poll is permanent, unrecoverable order loss on a real merchant's orders. **But the window is 30 minutes, not the 10 this programme quoted everywhere:** SAIRA sets its own `created_at >= 1800000` and remote conditions fully replace the defaults, so against a 5-minute poll that is a ~6-poll cushion rather than a 2-poll cliff. Still permanent, still undetectable without a monitor — and there is no ingest monitor in `iac/` at all. Re-rating every remaining semantic unit against this is an open gate item and Harry's call.
- **Two permanent ingest paths.** [FUSE-1098](https://globalfreight.atlassian.net/browse/FUSE-1098) ("retire the metered poll") is **Won't do**, so bulk is per-customer opt-in indefinitely. `SalesOrderCanonicaliser` sits on both, so a change to it lands twice — and only the metered path serves production.
- **Three units got done for us.** `D`, `F2` and `BUGFIX`(a) were completed by ordinary feature work. That is the most useful signal in the programme: the cheap, high-value findings get picked up organically by whoever is next in the file. What does *not* get picked up organically is the safety net, the recovery runbook and the monitors — the things nobody's feature ticket ever requires. **That is where this programme's real value sits.**

## What planning found before a line was written

Six defects. Three are still live and still owned by units (`S5`'s persist-error handler that never unlocks **and the spec that documents the opposite** on the 2026-07-02 incident path; `BUGFIX`(b)'s discarded `AuthFailure` state; `S8`'s metric that counts stores not orders). Two were fixed by others. One was deleted in `S0`. Two more were found on 2026-08-21 — a **dead depcruise rule** reporting 0 violations against 29 real ones, and **three configurations of the test fetch-seam that pass while making real network calls**. Both fixed in `S1`.

## How it was built

Four multi-agent workflows: an adversarial review of the architecture review (6 lenses, 32 findings folded back in); the characterization test-plan design; the safety-net hardening design; and the risk-optimal re-decomposition. A size-optimised plan was abandoned mid-run once the objective was corrected to risk. The safety-net workflow's final stages were cut off by a session limit and hand-synthesised.

**The 2026-08-21 re-review was a single author's pass — and it was then audited, and did not survive intact.** A 16-agent adversarial pass (5 lenses told to refute, every finding independently re-verified) returned **10 surviving findings: 1 claim stood with an amendment, 2 weakened, 2 refuted.** Its *measurements* all reproduced; its *judgements* were where it failed. Most consequential: "the nine moves are behaviour-neutral and compiler-verified" was **wrong** — four of them sit on live runtime import cycles closing on `@Inject()` decorator arguments, which `tsc` cannot check and which `biome`'s import sorting keeps regenerating. See the state doc's corrections 14–19.

## Next

Three tranches (detail in the state doc):

0. ~~**Stop the live bleeding**~~ — ✅ **done by Matt in [#232](https://github.com/gfs-bifrost/shopify-connector/pull/232)**, merged while the audit that flagged it was still running. My duplicate #233 was closed.
1. **Detection and recovery** — `S9` ingest monitors, then `RECOVERY`, then `S11`. These come **first** now: the poll window is stateless (no persisted watermark anywhere in `src`), so a missed window is invisible to any test suite by construction. A net cannot see it; only a monitor plus a backfill runbook survives it.
2. **Finish the net** — `S2` (re-sized down) → `S3`/`S4` → `S5` → `S6` → `S8` → `BUGFIX`(b) → `S7`, plus `CONTRACT-GOLDEN`, because the HTTP-in/SDK-out net is structurally blind to subscription and scaling changes.
3. **Structural wins, smallest first** — `SHAPE-A` (17 documents), then `MOVE-8` (⛔ **ADR first**, and sequenced as separate boot-verified steps, never one commit), then `PURIFY`, then `K1` and `SPLIT-CONFIRM`.

Drive it through the skill.
