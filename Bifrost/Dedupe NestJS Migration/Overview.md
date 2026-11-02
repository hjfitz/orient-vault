---
title: Dedupe Service — Express → NestJS Migration (Overview)
status: planning-complete
verdict: go-with-conditions
owner: Harry Fitzgerald
created: '2026-07-25'
updated: '2026-08-23'
tags: [bifrost, dedupe-service, nestjs, migration]
---

# Dedupe Service — Express → NestJS Migration (Overview)

Incremental migration of `dedupe-service` (`~/code/fuse/dedupe-service`) from **Express 4** to **NestJS 11**, delivered over 22 independently shippable pull requests with **zero external-contract change**. As of 2026-07-25 the **planning is complete**; implementation has not started. There is **no Jira ticket** — deliberately.

**Resume with the `dedupe-nest-migration` Claude Code skill** — it rehydrates all of the below and reads current progress from [[Bifrost/Dedupe NestJS Migration/Migration State|Migration State]].

## Deliverables

- **[[Bifrost/Dedupe NestJS Migration/Migration State|Migration State]]** — the live unit status table (**source of truth for progress**).
- **Plan of record** (artifact) — https://claude.ai/code/artifact/40b30f92-f5cb-4cfa-9de1-1047b156f122

## Verdict — go with conditions

Fund it as **three separable deliverables**, not one programme:

|       | Scope                                                                                           | Units                        | Value                                                                                                                 |
| ----- | ----------------------------------------------------------------------------------------------- | ---------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **A** | Phases 0–2 — CI gates, characterization net, one availability bug fix, tsconfig/toolchain split | N0, N1, B1, N2–N6, T1        | **Worth doing whether or not NestJS ever arrives.** Nothing here can be orphaned.                                     |
| **B** | Phases 3–4 — Nest owns the server; health + admin API convert                                   | S0, S1, P1, F1, R1, R2       | Delivers "dedupe is a Nest service" for onboarding at near-zero business risk. Ends at a mandatory reassessment gate. |
| **C** | Phases 5–6 — the four `/events` route groups + teardown                                         | E1, E2, E3, C2, C3a, C3b, D1 | Carries essentially **all** the risk and delivers only uniformity.                                                    |

**The non-negotiable condition:** if Deliverable A isn't funded in full, the answer is **no-go** — 112 of 289 existing assertions are written against Express's `res` mock and get rewritten by the very PRs they should guard, and on the create route a status assertion passes identically whether the record was published or silently dropped.

**Stopping after R2 is an explicitly supported end state** — but only via unit **X1**, which makes the hybrid *finished* rather than abandoned.

> [!info] Status, 2026-08-23 — **this is where the programme now stands**
> Deliverables **A and B are both complete** (R2 merged 2026-08-17). The reassessment gate is live and undecided; no Deliverable C unit may start until it is. The technical case for continuing is **stronger** than when this page was written (see the superseded bullet below); the organisational case is unchanged — open questions 1, 3 and 7 are still unanswered.

## Why this is risky enough to need a plan

> [!warning] Two of the three bullets below were overtaken by events — reconciled 2026-08-23
> Between R2 merging and this reconciliation, Harry's FUSE-1104/FUSE-1078 silent-loss hardening stack landed and **fixed the exact hazards this section was written to describe**. Kept in place, struck through, because they are why the plan is shaped the way it is. Current detail lives in [[Bifrost/Dedupe NestJS Migration/Migration State#🔄 Reconciliation 2026-08-23 — what the FUSE-1104 / FUSE-1078 stack changed under us|Migration State § Reconciliation]].

- dedupe is the **ingress → WMS gate**. All 12 Pub/Sub subscriptions have **no `dead_letter_policy`**; `ack_deadline_seconds = 20`. ~~and no `retry_policy`~~ — **#118 (2026-08-13) added exponential backoff to the push subscriptions**; the missing dead-letter policy stands.
- ~~`postRequest` sends **204 before doing any work**. Create is **at-most-once by design**. A build that answers 204 while failing internally loses records permanently and silently, with `dedupe_service.errors.generic` as the only signal.~~ **SUPERSEDED by #122 (2026-08-17):** create is now **ack-last / at-least-once** — it awaits the work, then answers 204 on success, **503 on a transient failure** (nack) and 204 on a permanent drop, with `event.nacked` / `event.dropped_permanent` as real signals. This is the single most consequential change to the plan's risk profile: **it retires two of the ten measured traps and drops E3 from `critical` to `high`**, because E3's hardest constraint — holding at-most-once through a non-passthrough `@Res()` — no longer exists to hold.
- Only ~700 of 3,838 non-test LOC is structurally Express — so this is a wrapper change applied to the most dangerous 700 lines in the estate, in a service whose HTTP layer has **0% coverage** (`src/__test__/app.spec.ts` is literally `expect(true).toBe(true)`).

## What makes it tractable

**Express's async-await behaviour lives in the Router, not the app.** Legacy express-4 routers mounted on Nest's own express-5 instance keep their exact current semantics (measured: sync throw → `errorHandler` 200; async throw → unhandled rejection, no response; `errorHandler` hits 1, not 2). So **the behaviour flip happens per route, at conversion time** — not all at once. That is what makes real incrementalism available rather than notional.

The convergence target is `replay` — which **was itself forked from collector/dedupe**, so its Nest layout already contains dedupe's own metric names and a per-record-type registry. This is a convergence onto a sibling, not a greenfield design. But note the deliberate divergences below.

## Strategy in one line

Net-first → thin-shell coexistence via the config-service seam → **provider bridge (P1) before any route converts** → per-route conversion, health first and create-request last and alone → retire the hand-rolled DI. **The middleware chain is never converted.**

## Deliberate, permanent divergences from replay

- `requestIdMiddleware` / `loggerMiddleware` stay raw `app.use()` **forever**. A `forRoutes("*")` `NestMiddleware` sees `req.path === "/"` and skips legacy routes — converting them silently rewrites `request.path` on every Datadog log line.
- `src/observability/` stays **byte-identical**. Never copy replay's `format.ts` (it nests correlation under `requestor.*`; dedupe's is top-level).
- Error responses stay `{message}` or bare status — **never** `application/problem+json`.
- No `APP_GUARD` / `APP_PIPE` / `APP_INTERCEPTOR` for the lifetime of the programme.
- **No `unplugin-swc` / `@swc/core`** — dedupe is vite 8 + rolldown; replay is vite 7 + esbuild, so replay's transformer experience doesn't transfer. config-service's "no decorators declared in specs" rule is the answer instead.

## Blocking gates before anything starts

- [ ] Merge **PR #82** (open, CLEAN, MERGEABLE) — it rewrites `config.ts`, `event.controller.ts`, `metrics.ts`
- [ ] **Explicit human sign-off** that introducing NestJS is sanctioned (org contract *Agent Stop Conditions* — new architectural concept + new directories)
- [x] ~~Decide the fate of `origin/hjf/refactor-to-new-structure`~~ — **binned 2026-07-25**, nothing salvageable (bundle archived for recovery). The lesson stands: **this exact restructure was already attempted and abandoned once**, which is the strongest argument for stopping at the Phase-4 gate.
- [ ] Capture the master secops baseline (both `dependency_audit` and `image_scan` are red on master)

## Recommended first PR

**`N0` — widen the CI `pull_request: branches:` filters to include `hjf/**`.** ~15 lines, three files, zero runtime surface, unblocks the other 21 units. Every PR gate currently filters on the PR's *base* ref, so **stacked PRs run no CI at all** — and it fails silently, as a PR with no checks rather than a red build.

If the first PR should deliver value even if the migration is cancelled, start with **`B1`** instead — `buildCacheService()` never settles when Redis is unreachable, so the revision never becomes ready. A genuine availability bug that stands on its own merits.

## How it was built

A 14-agent workflow: five parallel surveys → four independent sequencing strategies → synthesis → three adversarial verification passes → a completeness critic. 3.2M tokens, 691 tool calls. The critic **overturned three of the synthesis's own load-bearing measurements** (the route-sorting claim was false; a cited error message was fabricated; the sequencing made five units unimplementable) and found the abandoned January branch that nobody had looked for. Claims marked `[verified]` in the artifact were re-run independently against the repo, the Terraform, the installed packages and the GitHub API.

## Next

Question 2 (*what happened to the January branch?*) is **closed** — binned. **Question 1 (*is this worth its risk budget at all?*) now gates everything.** Answer it, then merge #82 and land `N0`. Drive it through the skill.
