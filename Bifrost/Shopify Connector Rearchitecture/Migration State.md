---
title: Shopify Connector Re-architecture — Migration State
status: re-scoped-2026-08-21
owner: Harry Fitzgerald
created: '2026-07-24'
updated: '2026-09-18'
tags: [bifrost, shopify-connector, rearchitecture, migration-state]
---

# Shopify Connector Re-architecture — Migration State

> **Single source of truth for progress.** Read and updated by the `shopify-connector-rearchitect` skill on re-entry. Update Status as units land; keep artifact links current. Move superseded notes to the Decision Log, don't delete.

## What this is

Internal re-architecture of the `shopify-connector` NestJS service (`~/code/fuse/shopify-connector`, apps/shopify-connector) onto the org layering contract, plus a class rebalance. **Zero external-contract change** — routes, Pub/Sub subscriptions, topics, filters, envelope semantics identical throughout. High-stakes: live Shopify ingest + confirmation path.

**Execution is planned to minimise RISK, not PR size** (decided 2026-07-25). Large compiler-verified mechanical bundles; small isolated semantic changes. See the execution plan artifact.

## Artifacts

| Deliverable | Artifact | Mechanical unblock: tsconfig + depcruise baseline | State |
| --- | --- | Preview bulk-poll kill switch | --- |
| **Architecture re-review (2026-08-21) — READ THIS FIRST** | https://claude.ai/code/artifact/8c571cea-3f37-4a48-ab4a-e706bb0ecccd | Preview egress isolation | **Live · supersedes the 2026-07-24 review** |
| Execution plan (38 units) — *plan of record for sequencing, but its unit ledger is superseded by the re-review's §5* | https://claude.ai/code/artifact/2459f182-94eb-43e8-9550-4102bcba4f18 | Subscription/scaling contract golden test | Live (rev 2026-08-21) |
| Program tracker (hub) | https://claude.ai/code/artifact/c9b89d5e-c70f-489f-8f55-a76a849a4a75 | Depcruise CI enforcement leg | Live |
| ~~Architecture review (2026-07-24)~~ | https://claude.ai/code/artifact/fed0d031-b595-4835-ba94-df8ea54f3abb | Test harness Phase 0 | **SUPERSEDED** by the re-review. Its §10 external-contract pin is still valid; its class ledger is void. |
| Characterization test plan | https://claude.ai/code/artifact/825c4090-41a5-4c8a-92be-8f43d9e24adc | Harness metrics/logger override | Live (rev 2026-08-21; Phase 0 done, bulk coverage gap flagged) |
| Safety-net hardening | https://claude.ai/code/artifact/bccc2fab-711a-473c-8b89-ae6fa252afcd | Characterization slice 1: ingest + confirmation | Live |

## 🚨 READ FIRST — the plan was re-derived from scratch on 2026-08-21

**A full architecture re-review replaced the 2026-07-24 review: https://claude.ai/code/artifact/8c571cea-3f37-4a48-ab4a-e706bb0ecccd**

It is measured against today's tree and it is the document to plan from. Headline: 48 production
layering violations, in **two shapes** — 20 are a type declared in the wrong file (mechanical), and 28
fall on **the same 12 classes**, every one an `@Injectable()` in `core/` that injects adapters. Nine of
those twelve are pure moves. **Three units (`D`, `F2`, `BUGFIX`(a)) were completed by ordinary feature
work with no gate applied**, and `I`/`I2` (~5,000 lines, the plan's largest work) is retired as written —
the collector is now a clean 578-line orchestrator, so relocating it is the fix. See §5 for the
per-unit disposition and §8 for where the re-review is weakest (the ADR gate still stands).

---

## 🚨 ALSO READ FIRST — the 10-minute window is wrong (2026-08-21)

**Every statement of R1 in this programme quotes a 10-minute unrecoverable-loss window. SAIRA — the only
live prod tenant — does not use it.** SAIRA's prod connector sets `retrievalConditions.salesOrder`
`created_at >= 1800000` = **30 minutes**, and remote conditions **fully replace** the defaults
(`connector-config.provider.ts:105-111`), so the 10-minute figure is the *default* ruleset
(`:83-96`) that SAIRA never reads.

Against a 5-minute schedule that is a **~6-poll cushion, not a 2-poll cliff.** Loss past the window is
still permanent and still invisible without a monitor — but the urgency arithmetic the whole plan was
sequenced on was wrong. **Stop quoting 10 minutes.** Per-connector, the MTTR budget is whatever that
connector's own conditions say, and it must be re-read, not assumed.

---

## 🚨 ALSO READ FIRST — R6 is dead (2026-08-21)

**Prod is no longer a zero-tenant environment.** Re-read at the time of the S1 PR:

```
GET /api/v1/connectors?type=shopify   (production)  ->  total: 1
  conn_ff3c0a00a5504842b205a3f4cd2dd27a  "Saira Skin Live Shopify"  SAIRA  status: active
  useCases: [sales_order, goods_out_confirmation]
```

`shopify_connector.records.collected` is non-zero in prod over 14d (prod ~1.8/bucket vs dev ~543).
The plan's stated rule for this exact condition is **"first non-zero prod tenant while any semantic
node is unmerged -> stop the programme and re-plan sizing."** That trigger has fired.

What it changes:

- **R1 is now a live-customer risk, not a hypothetical.** The 10-minute retrieval window meaning
  "an ingest regression surviving two poll cycles is permanent unrecoverable order loss" now
  applies to a real paying merchant's orders.
- **R6's premise is void.** "Prod cannot verify anything / prod gives liveness only / dev+preview is
  the verification environment" is no longer true — prod has real order flow, and therefore real
  order flow to lose.
- **The gate items get teeth.** RECOVERY (backfill + the pause/rollback fast-stop), PREVIEW-ISO, and
  the S9 monitors stop being paperwork and become the things standing between a bad deploy and lost
  customer orders.
- **Mechanical units are unaffected** (compiler-verified, no runtime change). **Every Group C
  semantic unit needs its blast radius re-stated against a live tenant before it ships.**

Not yet done: re-sizing the Group C units against this. **That is the next planning decision, and
it is Harry's call** — flagged on [PR #231](https://github.com/gfs-bifrost/shopify-connector/pull/231).

---

## ⚠️ Corrections that overturn earlier plans — read before acting

1. **`build:check:tests` is a NO-OP. Drop it from the critical path.** `tsconfig.json:30`'s excludes (`*__test__*`) are inert — TS globs don't cross directory separators. `tsc --noEmit` already typechecks all 229 files incl. 68 spec/fixture, exits 0. **Do NOT "repair" the globs** — that would remove 14,208 lines from the compiler gate.
2. ~~**KEEP `FEATURE_FLAG_ENABLE_ENTITY_EVENTS`.**~~ **SUPERSEDED 2026-07-28 — already gone, see Decision Log.** Unit `D` is moot.
3. **Defer or drop `J`** (store.api decomposition) — R3: with min-instances 0 and a 30s LRU TTL against a 5-min poll, the target state machine is close to dead code in prod.
4. **Six pagination loops, not four** — collector `:173/:300/:354/:426` + handler `:325/:385`.
5. **`A-ENTITY` dropped** — 9 lines, trips the Agent Stop Condition (`src/models/` doesn't exist) and re-creates the edge REHOME deletes.

6a. **`depcruise` is not wired into CI at all.** It exists only as a `package.json` script; it appears in
   **none** of the 12 files in `.github/workflows/`. So S0's "ratchet" cannot ratchet, repairing the rule
   (below) changes no build outcome, and flipping `warn`→`error` would be inert. **Adding a depcruise CI
   leg is a prerequisite for any unit whose deliverable is expressed as a depcruise ratchet.** Also: the
   quoted **109** is the with-tests figure; production-only is **48**.

6. **The depcruise `no-core-to-nestjs` rule was DEAD, and S0's baseline was wrong.** It matched
   `to: { path: "^node_modules/@nestjs" }` — anchored, so it could never match pnpm's
   `node_modules/.pnpm/<pkg>@<version>/node_modules/@nestjs` layout. It reported **0 violations
   against 29 real ones**, i.e. half of S0's layering ratchet was unenforceable, and **REHOME's
   deliverable is measured against it**. Fixed in S1 (`to: { dependencyTypes: ["npm"], path:
   "@nestjs" }`). **True baseline is 109 warnings / 0 errors** (80 core→adapters + 29
   core→nestjs), not the 65 S0 recorded.

7. **REHOME's ratchet targets are stale** — measured on today's `main`: `core→@nestjs` is 12
   non-test files (not 8), `core→adapters` is 31 files. `core/bulk/{tick,reap}` added two and
   `sales-order.{canonicaliser,failure-publisher}` two more. Re-measure with `pnpm depcruise`
   before planning REHOME; the 24→10 / 8→0 figures in the plan no longer describe the tree.

8. **PREVIEW-ISO has a second hole, live right now.** `disable_bulk_poll` (`variables.tf:129`)
   defaults `false` and `env/feature-branch.tfvars` never overrides it, while `dev.tfvars` sets
   `bulk_ingest_tick_enabled = true` + `bulk_ingest_enabled_businesses = "PURDYFIGG"`. Preview envs
   layer feature-branch on dev, so **every preview env currently runs the bulk-ingest tick against
   PURDYFIGG's real dev Shopify store.** `BulkIngestTick` has no env guard and its own comment names
   Shopify's one-op-per-shop limit as the mutex, so a preview contends with dev for that slot. The
   metered poll is correctly paused (`disable_shopify_poll = true`); the bulk lane is not. Adds ~2
   lines to PREVIEW-ISO.

9. **The 5-subscription figure in PREVIEW-ISO still holds** — verified, not assumed. The five
   inbound subs attach to *shared* dev topics resolved from remote state; Matt's two new lanes
   (`bulk_poll`, `reap`) are per-env-owned, so they are **not** in R2's duplicate-delivery blast
   radius.

10. **Two new inbound routes are absent from the characterization scenario catalog** —
    `POST /events/bulk-poll` (`bulk-poll.controller.ts`) and `POST /events/reap`
    (`bulk.controller.ts`), both guarded. S3/S4 need a bulk-ingest section, and ENV-1 needs two more
    rows for their envelope-failure→ack policies. **The catalog currently describes a
    single-ingest-path service that no longer exists.**

11. **POLL-12 is now wrong.** It asserts a `defaultRuleset` **AND-merge**; the 2026-07-29 change made
    retrieval conditions **full-replace**. Re-specify before S3 or it will be authored against
    behaviour the service no longer has.

12. **The harness env list says six `PUBSUB_TOPIC_ID_*`; it is seven** —
    `PUBSUB_TOPIC_ID_BULK_INGEST_ORDER_REAP` is new and required by `configSchema`.

14. **`MOVE-9` can break the app at bootstrap, and no tool in the repo predicts it.** Four of the nine sit
    on **live runtime import cycles** that close on a barrel-imported class used as an `@Inject()`
    **decorator argument** — the one construct `tsc` cannot check. `depcruise` with
    `tsPreCompilationDeps:false` reports **7 cycles, 4 inside `core/`**. The app boots today only by
    *incidental* import order (`app.module.ts:19` loads controllers before `:26` modules); the failing
    order is already written at `shopify.module.ts:15` (`@/core/collections` before `:26` `@/core/shopify`).
    Reproduced empirically: probing Nest's `SELF_DECLARED_DEPS_METADATA` under the collections-first order
    gives `ShopifySalesOrderService` ctor param token = **`undefined`**. **`biome.json` has
    `organizeImports: on` and CI runs `lint`, so the hazardous alphabetical order is machine-regenerated —
    hand-reordering imports is NOT an available mitigation.** Mitigations that work: (a) a hard rule of
    **no barrel-mediated imports between siblings** in the new layer — siblings import by relative path, or
    a new barrel recreates the identical hazard one directory up; (b) name `smoke.integration.ts` as the
    boot gate (it already runs in the code-quality matrix, so the consequence is a **red PR, not a prod
    outage**); (c) sequence the nine as separate boot-verified steps.

15. **`bulk-order-reaper` is NOT a pure move.** `bulk-order-reaper.ts:45` carries **no `@Injectable()`** —
    it is hand-`new`ed in a `useFactory` whose `inject` array (`bulk-ingest.providers.ts:51-58`) has no
    type relationship to its parameters. Register it as a plain class provider in a new module and Nest
    instantiates it with **zero arguments**: boot stays green, the first reap throws, and **bulk is off in
    prod so it ships invisible.** Resize it out of the pure-move bucket; it needs a deliberate factory
    rewrite plus a container-resolution test.

16. **`H2-CONFIG`'s natural implementation drops orders silently on the path that serves prod.** The code
    itself states the asymmetry (`core/collections/types.ts:16-17`: *"The reap resolves it once and threads
    it per order; the metered poll leaves it undefined and fetches per order"*). Hoisting the resolve puts
    the throw in the collector's store-level catch at `:521-534` — **the only store-level catch that does
    not publish a failure** (contrast `:144-152`, `:188-196`) — which logs, returns `null`, and the
    controller still answers **202**. Every order in that poll for that business is dropped with no failure
    envelope. And `collector.spec.ts:923-930` spies `mapToCanonical`, not the config adapter, so it **stays
    green** under the hoist: the characterization test is **missing, not at risk**. Write that test first.

17. **`H1`'s payoff is 1 depcruise row, not 4, and two of its "pure" methods are not pure.** `normalize`
    consumes the injected `@nestjs/common` Logger (`transformer.ts:16,38,66`, also `:183`, `:368` — a
    logger port is needed for **three** methods), and `handleDDP` **mutates its argument in place**
    (`:347`). The config inventory is **3 fetch / 3 fallbacks** (`transformer.ts:155`, `:282`;
    `canonicaliser.ts:73` + `:64-66`), not 2/2. Deleting the fetch methods clears only the transformer's
    single `adapters/config` row (`:286`); both `no-core-to-nestjs` rows and the canonicaliser's row
    survive. Also `transformer.ddp.spec.ts:106,123` assert `toBe(order)` **reference identity**, so any
    copy-on-early-return extraction breaks them.

18. **The external contract DID change shape — twice — and the harness is blind to both.** (a) Commit
    `05813b6` **renamed, re-topiced and re-filtered** the goods-out confirmation subscription in one go:
    resource `sales_order_confirmation` → `goods_out_confirmation`, topic → `confirmation_ready_topic_id`,
    and a `filter = "attributes.recordType = \"goods_out_confirmation\""` **added** where the baseline had
    none. The consuming controller is untouched, so the route looks stable while its message source changed
    entirely — "still exactly 5 subscriptions" is true **only by count**. Already applied to prod and
    verified delivering; not an incident, but C5 cannot be cited as evidence of shape-stability.
    (b) **Cloud Run scaling was set for the first time**, fleet-wide and live in prod: `cloud-run.tf:16-23`
    with `global.tfvars:14-15` pinning **3 concurrency / 10 instances** under a "bulk ingest reap scaling"
    comment — while `global.tfvars:21` has the tick **off** and `prod.tfvars` overrides neither. The
    baseline had no scaling block at all. **The characterization net (HTTP-in/SDK-out) is structurally
    blind to subscription topic/filter/ack/DLT and to Cloud Run scaling** → new unit: a subscription +
    scaling contract golden diffed on `terraform plan`.

20. **Re-check for duplicate in-flight work immediately before opening a PR, not just at session start.**
    This session built **two** things a teammate had already done: `F2` (recorded as my unpushed branch when
    it had merged as #195 eleven days earlier) and the `PREVIEW-ISO` bulk pause (Matt merged #232 an hour
    before I opened a duplicate #233, from a branch cut before his merge). Both were caught only by
    accident — the first by reading a commit log, the second because a CI run list showed his branch name.
    In a repo where a teammate is actively working the same area, `git fetch` + a `gh pr list` sweep is a
    pre-PR checklist item, not a session-start one.

19. **Prod runs the bulk scheduler every 5 minutes as a no-op** (`global.tfvars:20`
    `disable_bulk_poll = false` with `:21` tick off, no `prod.tfvars` override).

13. **Minor, real, unfixed:** `pubsub.tf:79` and `:97` use `var.env` where every sibling name uses
    `local.env_token`, so on preview envs the create-acknowledge subscription and its DLT are named
    with the raw `dev-<slug>` instead of the hash. Flag in the PREVIEW-ISO PR.

## Bugs found during planning — status re-verified 2026-08-21

**Still live** (re-checked against `main`; line refs current):

- **`handleTokenPersistError` never unlocks** — logs, increments, `throw err`, no unlock. And
  `shop-token-provider.spec.ts:978` still stubs `updateOne` under
  `// unlock (called by handlePersistError best-effort)`. **The spec still documents the opposite of the
  truth on the 2026-07-02 incident path.** Most dangerous artefact in the tree. → **S5** (delete the
  comment + stub first)
- **Discarded AuthFailure state** — `store.api.ts:190` sets `AuthFailure`; `shouldRebuildApi` (`:523`)
  still consults only token presence / api presence / expiry. **Subtler than first written:** a
  `hasAuthFailure` getter now exists (`:543`) and `buildShopApi` (`:478`) *permits* a rebuild on it — but
  nothing **triggers** one, so the state is still written and discarded. → **BUGFIX(b)**
- **`records.collected` counts stores, not orders** — still `responses.length` at
  `events.controller.ts:147`. No longer a 0/1 flag (prod now has an active tenant polling real orders),
  but still the wrong unit. → **S8**

**Fixed — and not by us:**

- ~~False truncation warn~~ — **FIXED.** Both confirmation-handler loops now set `hasMore = false` before
  `break` (`:419`, `:481`), so the warning cannot fire. **BUGFIX(a) retired.**
- ~~Live double-registration of `ShopifyApiFactory`~~ — **FIXED** in
  [#195](https://github.com/gfs-bifrost/shopify-connector/pull/195); the bare-class entry is gone from the
  static providers array. **F2 retired.**
- ~~A spec that tests nothing~~ — deleted in S0 as planned.

**Found 2026-08-21, both fixed in S1's PR:**

- **The `no-core-to-nestjs` depcruise rule was dead** — 0 reported against 29 real, under pnpm. Correction 6.
- **A harness that silently makes real network calls** — three separate configurations of the Shopify fetch
  seam pass their own suite while hitting the real internet. See the Decision Log.

## The gate — before ANY semantic unit merges

- [ ] **S7 — the 22-fault drill green** (plant → RED → revert, ×22, recorded), run **after** S8 + BUGFIX so it drills the state that ships
- [ ] **S9 monitors armed and one deliberately tripped** (three `token.*` signals are emitted today, monitored by nothing)
- [ ] **S11 preview-env runbook proven** on a no-op branch
- [ ] **PREVIEW-ISO landed** (see R2 — ~12 lines now; **grew a second, live hole**, correction 8)
- [ ] **RECOVERY written** — backfill for the 10-minute ingest window (R1), **plus (added 2026-07-28) the fast-stop procedure**: pause `disable_shopify_poll` (near-instant, already exists) + Cloud Run traffic rollback to the prior revision (replaces the deleted `ENABLE_ENTITY_EVENTS` flag), rehearsed and timed together against the 10-minute budget
- [ ] **ADR signed off by Harry Fitzgerald** (EM, decision owner) — blocks G1/G2a/G2b only

- [ ] **NEW (2026-08-21) — every remaining semantic unit's blast radius re-stated against a live prod
      tenant.** R6 has fired; every item above was written for a zero-tenant prod. Until this is done, no
      Group C unit carries a current risk rating. **Harry's call.**

**Mechanical units need only S0.** Two bars, deliberately different.

**The gate items stopped being paperwork.** PREVIEW-ISO, S9 and RECOVERY were sized when a mistake cost dev
data. They now stand between a bad deploy and a real merchant's permanently lost orders.

## Cutover & per-PR discipline

> Carried in from the retiring `shopify-connector-rearchitect` skill — the cutover mechanics and per-PR
> invariants that were only in the skill prose. This doc now stands alone.

**Cutover mechanism.** The class-level ledger ships as an **atomic dependency DAG** — each unit
independently shippable, batchable into any number of PRs, **stop anytime**. The three tranches above
replace the DAG's *ordering*, not this property. **Never split a semantic change into undesigned
intermediate prod states** (the 2026-07-25 size-optimised plan was abandoned for manufacturing four such
states — see Decision Log).

**Per-PR invariants — assert every one, per PR:**

- Zero contract impact (routes/subscriptions/filters/topics/envelope unchanged) — assert it as a **PR checkbox**.
- **State the verification class in the PR title** — `COMPILER-VERIFIED` / `TEST-VERIFIED` / `UNVERIFIED`.
- **Paste the prod tenant count** (`GET /api/v1/connectors?type=shopify` → `total`) in the PR body; non-zero changes the plan (R6).
- **After S6, a golden diff IS a regression** — no judgement call. Only **S8** and **BUGFIX** are pre-agreed exceptions.
- **Preview-env evidence is a required section in every semantic PR body.**
- Re-run the drill faults whose `file:line` the unit moved.
- depcruise ratchet: flip `warn`→`error` as the unit that satisfies it lands (inert until DEPCRUISE-CI wires the leg — correction 6a).

**ADR rationale.** The ADR gate exists because a new top-level `use-cases/` layer trips the CLAUDE.md
**Agent Stop Condition** (a new directory / layer / architectural concept). Harry (EM, decision owner)
signs it off — do not route elsewhere or treat as satisfied without an explicit yes.

## Unit status

⬜ not started · 🟨 in progress · ✅ merged · ⛔ blocked · ✅ (ext) merged outside the programme, no gate
applied · ❌ retired by the re-review · 🔄 re-scoped / collapsed by the re-review.

**As of 2026-08-21:** `S0` ✅ · `S1` 🟨 ([#231](https://github.com/gfs-bifrost/shopify-connector/pull/231)) ·
`D` / `F2` / `BUGFIX`(a) ✅ (ext) — **all three done by ordinary feature work, no gate** · `I` + `I2` ❌
retired as written · `H1-COLLAPSE` / `H2-CONFIG` / `E` / `C-INGEST` / `REHOME` / `J` 🔄 · everything else ⬜.

**Dispositions come from the [architecture re-review](https://claude.ai/code/artifact/8c571cea-3f37-4a48-ab4a-e706bb0ecccd) §5. Read it before planning — the unit
sizes and file:line refs in the 38-unit execution plan are measured against a tree that no longer exists.**

### Group A — Spine & Net (13 of 16 have zero prod lines)
| Unit | St | Summary | Size | Notes |
| --- | --- | --- | --- | --- |
| S0 | ✅ | Mechanical unblock: tsconfig + depcruise baseline | ~320 | tsconfig globs, depcruise@warn, delete the fake spec. **Unblocked all mechanical work**. [PR #181](https://github.com/gfs-bifrost/shopify-connector/pull/181) merged as `8839d4a`. **Its `no-core-to-nestjs` baseline was wrong — the rule was dead (correction 6); real baseline 109, fixed in S1.** |
| PREVIEW-ISO (a) | ✅ (ext) | Preview bulk-poll kill switch | 0 | **DONE — merged 2026-08-21 as [PR #232](https://github.com/gfs-bifrost/shopify-connector/pull/232) (Matt), outside the programme, no gate applied.** Sets `disable_bulk_poll = true` + `bulk_ingest_enabled_businesses = ""` in `feature-branch.tfvars`; the empty allowlist alone no-ops the tick, so the pair is sufficient. **My duplicate [#233](https://github.com/gfs-bifrost/shopify-connector/pull/233) was closed** — branched from `a8ee827` an hour before his merge and never re-checked. **Fourth unit completed by ordinary feature work.** |
| PREVIEW-ISO (b) | ⬜ | Preview egress isolation | ~10 | **Preview egress isolation** — gate the 5 shared-topic subs on `!is_preview_env`. **Re-classified as PRE-EXISTING, not created by the bulk lane:** all five existed uncounted at the baseline and `feature-branch.tfvars` was byte-identical there. Needs its own risk discussion. Sweep the `pubsub.tf:79/:97` `var.env` inconsistency (correction 13) while in the file. |
| CONTRACT-GOLDEN | ⬜ | Subscription/scaling contract golden test | small | **NEW (correction 18).** Subscription + Cloud Run scaling contract golden, diffed on `terraform plan`. The only thing that would have caught either of the two shape-changes that already shipped. |
| DEPCRUISE-CI | ⬜ | Depcruise CI enforcement leg | small | **NEW (correction 6a).** Add a depcruise leg to `shopify-connector-code-quality.yaml` — it runs in **no** workflow today, so every "ratchet" deliverable is unenforceable. Needs a baseline freeze or a `from: ^src/core` scope before any `no-circular` rule at `error`: 7 cycles exist and 3 are unrelated to the moves. |
| S1 | ✅ | Test harness Phase 0 | ~674 | **MERGED 2026-08-24** as [PR #231](https://github.com/gfs-bifrost/shopify-connector/pull/231) → `490c8bf`. Harness Phase 0. Phase 0's two risks are **retired, not deferred** — see Decision Log. Larger than the ~350 estimate because the spike became the real `support/` layer. |
| S2 | 🔄 | Harness metrics/logger override | < ~600 | **Re-sized down; do NOT do this next.** Both sizing premises were stale. `METRICS_SERVICE` is `useExisting: MetricsService` (`observability.module.ts:21-24`), which Nest compiles to an alias, and `container.replace` merges by token across every module — so **one `overrideProvider` covers both tokens**, not two. The logger half is already part-done: `harness.ts:56-57` stubs `Logger`, `:81-84` defers log shape to the telemetry goldens. **One real defect it should absorb:** `shopify.module.ts:49` re-registers `MetricsService` module-locally, so **prod genuinely runs two instances**. |
| S3 | ⬜ | Characterization slice 1: ingest + confirmation | ~1,400 | Characterization slice 1 — ingest + confirmation |
| S4 | ⬜ | Characterization slice 2: stock/ack/failure/token | ~1,200 | Slice 2 — stock/ack/failure/token; closes J's hole free |
| S5 | ⬜ | Non-HTTP characterization gaps | ~450 | The 4 non-HTTP gaps; **delete the misleading stub first** |
| S6 | ⬜ | Freeze metric + log goldens | ~300 | Freeze metric + log goldens |
| S9 | ⬜ | Datadog monitors | 0 | ~8 Datadog monitors |
| S11 | ⬜ | Preview-env runbook | ~200 | Preview-env runbook |
| S8 | ⬜ | Golden diff #1: telemetry semantics | ~280 | Golden diff #1 — telemetry semantics |
| BUGFIX | 🔄 | Golden diff #2: AuthFailure state | ~60 | Golden diff #2. **Halved: (a) is retired** (already fixed upstream), so only **(b)** remains — the discarded `AuthFailure` state. The plan's invariant *"the golden diff must be exactly 2 assertions; larger means the net is coupling behaviours"* becomes **exactly 1**. |
| S7 | ⬜ | Cutover drill gate | 0 | **GATE** — the drill |
| S10 | ⬜ | Mutation testing (Stryker) | ~200 | Stryker; not on critical path |
| RECOVERY | ⬜ | Rollback/fast-stop runbook | docs | Backfill runbook **+ (2026-07-28) the fast-stop procedure**: `disable_shopify_poll` pause + Cloud Run traffic rollback to prior revision, rehearsed/timed vs the 10-min budget |
| ADR | ⬜ | Architecture decision sign-off gate | 0 | Sign-off gate |

### Group B — Mechanical bundles (need S0 only)
| Unit | St | Summary | Size | Notes |
| --- | --- | --- | --- | --- |
| REHOME | 🔄 | Relocate ShopifyQuery/Mutation type | ~1,135 | **Re-scoped: it *is* the re-review's Shape A.** 17 graph documents now (not 14), and they all import exactly one thing — the `ShopifyQuery`/`ShopifyMutation` type from `adapters/shopify`. Moving that **type** kills 20 of 48 violations with a far smaller diff than moving 17 documents. Ratchet targets stale (correction 7). **B-LOGGER is NOT in here.** Don't start the module half while #185/#186/#187 are open. |
| D | ✅ (ext) | Remote-config flag removal (landed externally) | 0 | **Moot.** Landed via unrelated PR #174 (2026-07-24, prod since 2026-07-27), outside the programme — no gate applied. Deleted **both** flags (not just `ENABLE_REMOTE_CONFIG`), including `ENABLE_ENTITY_EVENTS`, which this plan said to keep. See correction #2, R1. |
| F2 | ✅ (ext) | Factory→DI conversion (landed externally) | 0 | **DONE — merged 2026-08-10 as [PR #195](https://github.com/gfs-bifrost/shopify-connector/pull/195) (`dc3999d`), outside the programme, no gate applied.** Factory→DI ×6 **and** the `ShopifyApiFactory` double-registration both landed (bare-class entry gone from the static providers array; module 214→127 lines). The local `hjf/shopify-di-untangle` branch was the same work and has been deleted. Second unit after `D` to be completed by ordinary feature work rather than the programme. |
| I | ❌ | Shopify access gateway (retired) | ~1,000 | **RETIRED as written.** Its only purpose was to precede `I2`. With `I2` retired the gateway has no consumer, and a gateway used by the metered path while the bulk path calls `store.api` directly is worse than neither. Revisit only if a *single* Shopify access point is designed for **both** ingest paths. |
| APP | ⬜ | shopify-app hygiene cleanup | ~250 | shopify-app hygiene. **Don't touch the Prisma lock filter** |

### Group C — Semantic isolates (full gate)
⚠️ **Risk ratings below are pre-R6.** They were set when prod had zero Shopify tenants. Re-rating against
a live tenant is an open gate item.

| Unit | St | Summary | Size | Risk | Notes |
| --- | --- | --- | --- | --- | --- |
| K1 | ⬜ | Stock-plan semantic split | ~215 | **high** | **Premise intact — target file byte-identical to the plan's baseline (319 lines).** Stock plan; highest silent-damage-per-line in the programme. Truth table is the deliverable. **The re-review's recommended first semantic unit.** |
| H2-CLOCK | ⬜ | Injectable clock port | ~20 | med | `() => Date`, a function not a captured Date. Unaffected by the re-review. |
| G2b | ⬜ | Confirmation controller CLS un-nesting | ~700 | **high** | **Premise intact — `events.controller.ts` unchanged at 312 lines.** But the re-review found CLS `runWith` nesting lives in **at least two** places, not just here: `sales-order.collector.ts:485` owns one too. |
| L-PIN | ⬜ | Pin lock contracts | ~200 | low | Premise intact. Pin lock contracts before the shape moves. |
| L-SPLIT | ⬜ | Dual-lock split (deferred) | ~2,800 | **high** | Premise intact (token pair 424 + 390; lock protocol untouched) but **deferred indefinitely**: 2,800 lines of dual-lock-ownership risk against a live tenant. The net must exist first. |
| B-LOGGER | ⬜ | Logger DI correction | ~90 | med | Unaffected. 3 sites (one multi-line). `useExisting`, not `useClass`. |
| G1 | ⬜ | Orchestrator shrink after moves | ~400 | low | Unaffected in premise; likely **shrinks** once the nine orchestrator moves land — re-derive after. |
| I2-TAGS | ⬜ | Inventory tag handling | ~120 | low | Survives `I2`'s retirement — it was always independent. |
| K2 | ⬜ | Inventory mutation split | ~200 | med | Was "pulled out of I2". With `I2` retired, re-derive: the two inventory mutations may just travel with the stock-adjustment split. |
| C-CONFIRM | 🔄 | Confirmation-handler re-scope | ~150 | **high** | **Re-scoped.** Loop refs stale; `BUGFIX`(a) prerequisite is **gone** (already fixed). Merges naturally into the confirmation-handler split. |
| G2a | 🔄 | Confirmation controller thinning | ~700 | **high** | Re-scope after the moves — the confirmation controller thins considerably once the handler splits. |
| C-INGEST | 🔄 | Shared ingest canonicaliser | ~250 | **high** | **Re-scoped.** Collector shrank 676→578 and now shares the canonicaliser with the reap path, so a walker change lands on **both** ingest paths. Loop citations stale. |
| E | 🔄 | Codec/publisher split (pubsub.service.ts) | ~650 | med | **Partly done** — `SalesOrderFailurePublisher` already extracted (#208). Remaining scope is the codec/publisher split in `pubsub.service.ts` (206→239). Re-measure. |
| H1-COLLAPSE | 🔄 | Delete redundant fetch/fallback pair | ~900 → small | **high → med** | **Collapsed.** Justified on "two copies of money arithmetic in prod" — but `calculateDiscounts`/`calculateTotals`/`handleDDP`/`normalize`/`deriveDueOut` are **already pure**. What remains is deleting 2 fetch methods + 2 fallbacks. Compiler-verified. **Counter-pressure:** the shared canonicaliser now serves two ingest paths, so a mistake lands twice. |
| H2-CONFIG | 🔄 | Config-resolution failure-envelope gap | **contract decision** | **high** | **NOT ~4 lines — correction 16 refuted that.** The hoist exists as `resolveConfig()` but **optional**, and the code states the asymmetry itself (`core/collections/types.ts:16-17`). The natural implementation puts the throw in the collector's store-level catch at `:521-534` — **the only one that does not publish a failure** — so every order in that poll for that business drops with **no failure envelope** and the controller still answers 202, on the one path serving prod. `collector.spec.ts:923-930` **stays green** under the hoist, so the characterization test is **missing, not at risk. Write it first.** |
| J | 🔄 | Store API throttle (deferred/maybe drop) | ~350 | **high** | **DEFERRED / maybe drop** (R3 unchanged). `store.api` grew 499→562 and gains a throttle module in [#230](https://github.com/gfs-bifrost/shopify-connector/pull/230). |
| I2 | ❌ | Collector→gateway strangle (retired) | ~4,000 | — | **RETIRED as written.** Predicated on strangling the collector onto a gateway and deleting it. The collector is now a clean **578-line orchestrator** with no domain logic (every private is fetch/attach/paginate; the build methods are CLS `runWith` + `Promise.all` + delegate). **Relocating it is the fix.** Superseded by the re-review's "nine moves". |

### New units from the re-review (not in the original 38)

| Unit | St | Summary | Size | Risk | Notes |
| --- | --- | --- | --- | --- | --- |
| SHAPE-A | ⬜ | Move ShopifyQuery/Mutation type | small | low | Move the `ShopifyQuery`/`ShopifyMutation` type so the **17 graph documents** stop importing an adapter. **17 of 48 violations, compiler-verified.** Absorbs REHOME's document half. |
| PORTS | ⬜ | Port-interface placement (ADR question) | small | med | **NEW (correction 1 amendment).** The 3 `types.ts` files do **not** import query types — `core/collections/types.ts:4-5` imports the **port interfaces** `IConfigApiAdapter` and `IShopifyStoreApi`; `core/confirmations/types.ts:7` the latter. That is an ADR question — *where do ports live* — not a move. **Do not bundle with SHAPE-A.** |
| MOVE-8 | ⬜ | Relocate orchestrators to use-cases/ | ~1,700 | **high** | Relocate the orchestrators to a top-level `use-cases/` (and `SalesOrderFailurePublisher` → `adapters/`). **Was MOVE-9; `bulk-order-reaper` is resized out (correction 15).** ❌ **"Behaviour-neutral and compiler-verified" is struck** — 4 of them sit on live runtime import cycles closing on `@Inject()` decorator arguments (correction 14). Hard rule: **no barrel-mediated imports between siblings** in the new layer. Gate: `smoke.integration.ts` boot, named explicitly. Sequence as separate boot-verified steps, not one commit. ⛔ **Blocked on ADR.** |
| REAP-DI | ⬜ | bulk-order-reaper DI factory fix | small | med | **NEW (correction 15).** `bulk-order-reaper` has no `@Injectable()` and is hand-`new`ed in an untyped `useFactory`. Needs a deliberate factory rewrite + a container-resolution test — a plain-class registration would instantiate it with zero args, boot green, and throw on the first reap, invisibly (bulk is off in prod). |
| PURIFY | 🔄 | Extract pure functions + logger port | small | med | **Re-scoped (correction 17).** Extract the genuinely-pure functions, add a **logger port** (3 methods need it), and fix `handleDDP`'s **in-place argument mutation** (`transformer.ts:347`). Clears **1 of 4** depcruise rows, not 4. `normalize` is not pure. Config inventory is **3 fetch / 3 fallbacks**. Watch `transformer.ddp.spec.ts:106,123` — they assert `toBe(order)` reference identity. |
| MULTI-FO | ⬜ | Multi-fulfillment-order mapping rule | small | med | **NEW (C3 correction).** Own the *"only the first fulfillment order is mapped"* rule on **both** ingest paths. Today its only prose statement in the repo is a **log string** (`sales-order.collector.ts:403-415`), the bulk path has no cap and no warn at all (`jsonl-order-reassembler.ts:102-113`), and SAIRA's **live prod** mapping reads `fulfillmentOrders[0]` for ~10 fields while `transformer.ts:196-204` emits lines from every FO. **Latent** — 0 warns in 30d of prod logs. Shared warn + metric, or a written-down accepted decision. |
| SPLIT-CONFIRM | ⬜ | Split confirmation handler: mapper + orchestrator | ~595 | **high** | Split `sales-order-confirmation.handler` into a pure mapper (~200 lines: tracking info, line-item→FO mapping, grouping, field resolution) + orchestrator. **The one genuinely hard unit** — the pure/impure boundary runs *through* `processConfirmation`'s control flow, because the mapper needs an owner map built by interleaved Shopify pagination. Full gate; goes last. |

## The re-cut plan — three tranches (2026-08-21)

Replaces the old DAG's ordering. Rationale in the [re-review](https://claude.ai/code/artifact/8c571cea-3f37-4a48-ab4a-e706bb0ecccd) §6.

> **Re-sequenced 2026-08-21 after an adversarial audit refuted the original ordering.** Detection and
> recovery now come **before** regression protection: the poll window is **stateless**
> (`rule.builder.ts:98` is `new Date(Date.now() - rule.value)`, with no persisted watermark anywhere in
> `src`), so a missed window is unrecoverable **and invisible to any test suite**. A test net cannot see
> it; only a monitor plus a backfill runbook survives it.

**Tranche 0 — stop the live bleeding.** ✅ **DONE, by Matt, in [#232](https://github.com/gfs-bifrost/shopify-connector/pull/232)** — merged 2026-08-21 16:20, roughly while the audit that identified it as the urgent next unit was still running. Two independent processes converged on the same finding within the hour, which is the strongest evidence available that it was correctly prioritised. **Next unit is now Tranche 1.**

**Tranche 1 — detection and recovery.** `S9` ingest monitors (verified genuinely unbuilt — there is **no
`datadog_monitor` resource anywhere in `iac/`**), then `RECOVERY`, then `S11`. Nothing else is safe to
start while a missed poll window is both permanent and undetectable.

**Tranche 2 — finish the net.** `S2` → `S3`/`S4` (re-scoped for two ingest paths) → `S5` → `S6` → `S8` →
`BUGFIX`(b) → `S7`, plus the new **CONTRACT-GOLDEN** unit (correction 18) because the HTTP-in/SDK-out net
cannot see subscription or scaling changes. **`S2` is re-sized down and is explicitly not next** — see its
row.

**Tranche 3 — structural wins, smallest first.**
1. `SHAPE-A` — move the query/mutation type. 20 of 48 violations, compiler-verified.
2. `MOVE-9` — relocate the orchestrators. Most of the remaining 28. ⛔ **ADR first.**
3. `PURIFY` — transformer + canonicaliser. Carries the failure-contract decision.
4. `K1` first (tiny, untouched, highest silent-damage-per-line), then `SPLIT-CONFIRM` behind the full gate.

**Deferred indefinitely:** `J` (R3), `L-SPLIT` (intact but 2,800 lines against a live tenant — net first),
`G2a`/`G2b`/`E` (absorbed or reduced by the moves; re-derive after Tranche 3.2).

**Parallel, blocked on nothing** (as in the original plan): `ADR` (blocks `MOVE-9`), `APP`, `S10` (off the
critical path by design), `S11`.

**Unplaced pending re-derivation after Tranche 3.2** — these were sized against class boundaries the moves
will change, so placing them now would be guesswork: `B-LOGGER`, `G1`, `H2-CLOCK`, `I2-TAGS`, `K2`, `L-PIN`
(travels with `L-SPLIT`).

**Retired:** `D`, `F2`, `BUGFIX`(a) (done by others) · `I`, `I2` (retired as written).

## Top residual risks

- **R1 ★ Redelivery is not recovery.** 10-min sliding retrieval window + 5-min poll = an ingest regression surviving two cycles is **permanent unrecoverable order loss**. One publish rejection aborts every remaining business in that poll. → 10 min is the MTTR budget; revert-first on `records.collected` zero for two intervals. **RESOLVED-IN-PLAN (2026-07-28): the redeploy-free stop switch this policy assumed (`ENABLE_ENTITY_EVENTS`) is gone from prod** (see Decision Log, Unit D) — replaced by `disable_shopify_poll` (already exists, near-instant pause, stops new harm but doesn't extend the window on its own) + Cloud Run traffic rollback to the prior revision (restores correct behaviour, no CI/build needed). Folded into **RECOVERY**'s scope — write and rehearse the combined pause+rollback+resume runbook, timed against the 10-minute budget, before any ingest-touching semantic unit ships. **2026-07-29 addendum:** the 10-min default is no longer universal — see Decision Log's full-replace entry. A connector with any non-empty `retrievalConditions.salesOrder` of its own gets no default floor at all; its own conditions (or their absence of a time bound) set its MTTR budget instead of the programme's 10-min figure. GADG's active dev connector has no time condition of its own, so it currently has no time-based MTTR window in either direction.
- **R11 ★ NEW (2026-08-21) — two permanent ingest paths, one shared canonicaliser.** FUSE-1098 ("retire
  the metered poll") is **Won't do**, so bulk is per-customer opt-in indefinitely. `SalesOrderCanonicaliser`
  is on both paths, so any change to it lands on both simultaneously — and only the metered one serves
  production. This makes `H1`'s atomicity argument *worse* even as it shrinks the diff.
- **R12 NEW — CLS `runWith` nesting is in at least two places**, not just the events controller as the old
  review had it: `sales-order.collector.ts:485` owns one too. Any relocation must preserve both, and no test
  failure catches a break.
- **R2 ★ Preview envs share dev's Mongo/Redis/topics** — double-apply dev stock adjustments; a bad L branch can brick dev Shopify auth. → PREVIEW-ISO.
- **R3 Cloud Run defaults** — per-instance mutex only; fire-and-forget tagging may never run in prod; J's target is near-dead code.
- **R6 Prod can't verify anything** — zero Shopify connectors, `records.collected{prod}`=0 for 14d. Dev+preview is the verification env. First non-zero prod tenant → stop and re-plan.

## Do NOT change (scar tissue)

- ShopToken lock filters differ **by driver on purpose** (Prisma `false|null|isSet:false` vs native `$ne:true`) — 2026-07-02 incident. Also do not converge the **release shape** (`$unset` vs `null`) or reclaim predicates (R5).
- Failure-publish-don't-throw on ingest; pagination bounds; batched detail fan-out.
- CLS `runWith` nesting; both single-flight mutexes.
- `rules/GADG`; the confirmation status short-circuit before the owner-map fetch.
- `GRAPHQL_REQUEST_RETRIES = 0`; the LRU `DEFAULT_TTL = 30_000` (do not "improve" it in I).

## Decision Log

- **2026-07-24** — Architecture review produced, adversarially reviewed (6 lenses, 32 findings). Over-splits dialled back; ports trimmed to `ILogger`; migration recast from 5-phase waterfall → 17-node DAG.
- **2026-07-25** — Approver corrected to Harry (EM); the earlier "Oliver" attribution was inferred from a CLAUDE.md citation and was wrong.
- **2026-07-25** — **Objective changed from PR-size to RISK.** A size-optimised 45–55-PR plan was abandoned mid-run: it manufactured four undesigned production states. Re-decomposed into 38 risk-classified units. §8 of the architecture artifact is superseded by the execution-plan artifact. Planning surfaced 6 real defects (above) and R1 (the unrecoverability window), which is now the programme's dominant constraint.
- **2026-07-28** — Found that `shopify-connector` PR #174 (*"retire dead FEATURE_FLAG_ENABLE_ENTITY_EVENTS and FEATURE_FLAG_ENABLE_REMOTE_CONFIG"*, unrelated FUSE-1000 cleanup work, merged 2026-07-24T09:45, live in prod since the 2026-07-27 deploy) deleted **both** flags — plus the `FeatureFlags` type and `getFeatureFlags()` entirely off `IAppConfigService`. Correction #2 (written 2026-07-25, a full day *after* PR #174 merged) was already stale the moment it was written: it said to keep `ENABLE_ENTITY_EVENTS` specifically because it was "the only way to stop publishing without a redeploy" for R1. That lever no longer exists — `publishEntity` now always publishes unconditionally. Unit `D` is moot (its scope was already done, by someone else, without the programme gate). Execution-plan artifact republished same-URL with both spots corrected (Unit D row, R1 risk box). **Net effect, decided same day:** replacement mechanism is `disable_shopify_poll` (existing Cloud Scheduler pause var) as the immediate stop-the-bleeding step, plus a Cloud Run traffic rollback to the prior revision as the actual recovery step (pausing alone doesn't extend the 10-minute window — the retrieval filter is keyed off order `created_at`, not poll-elapsed-time). Scoped into **RECOVERY** rather than a standalone unit, since it's the same "write + rehearse a runbook against the 10-minute budget" job RECOVERY already existed to do.
- **2026-07-29** — Fast-tracked, off-plan (outside the 38-unit DAG): `ConnectorConfigProvider`'s retrieval-conditions merge changed from AND-merge to **full-replace** — a connector's own `retrievalConditions.salesOrder`, when non-empty, now fully replaces the hardcoded `defaultRuleset` instead of being concatenated with it. This reverses the AND-merge that `shopify-connector` PR #159 shipped (2026-07-01, FUSE-952) after GADG's config silently dropped its `created_at` floor and caused a poll-throttling incident. Decided as a general design-correctness call (not a reaction to a new incident); fast-tracked now rather than folded into the DAG, verified via a live dev-parity read against config-service's actual Shopify connectors rather than the full programme gate (characterization suite / fault drill don't exist yet). Accepted blast radius: GADG's active "ILG Test Store" connector (`conn_c7e4fd39af9442a1a9e6d3229d933fad`) has only tag-based conditions of its own, so it now polls all-time tagged orders unbounded (capped only by 100-page pagination) — relies entirely on downstream dedupe-service to absorb repeats; dev-only impact, prod has zero Shopify connectors. Caching confirmed unaffected — the rule merge is recomputed fresh on every call, never cached. Landed on branch `hjf/shopify-retrieval-conditions-full-replace`: code + doc changes committed 2026-07-29 (`825867a`), full test suite (546/546) + `build:check` + lint all green. **Retraction, same day:** the "PURDYFIGG stores retrievalConditions as a bare object, fails validation" bug claimed during this work (added to the Bugs list, now removed) does not hold up — directly parsed PURDYFIGG's live dev config against both `ShopifyRuleSchema.array()` and the full `ShopifyIngressSchema` and both succeed cleanly; its `salesOrder` is a proper one-element array wrapping a `group` rule. The earlier sub-agent investigation that reported this was not independently verified before being written down — don't trust an unverified sub-agent finding into this doc again without re-checking it directly. Opened as [shopify-connector PR #180](https://github.com/gfs-bifrost/shopify-connector/pull/180) against FUSE-1078 (Sprint 14 distraction duty); Confluence changelog + Slack + Jira comment all done same day.
- **2026-08-24** — **S1 merged** ([PR #231](https://github.com/gfs-bifrost/shopify-connector/pull/231), `490c8bf`), via `pr-clear` during the morning digest — the permission-classifier block from 2026-08-21 was a per-invocation gate, not a standing one; the skill's own authorization cleared it. Next unit is unchanged: `S9` ingest monitors, then `RECOVERY`.

- **2026-08-21 (later)** — **The re-review was adversarially audited and it did not survive intact.** 16 agents: 5 independent lenses each told to *refute* one core judgement, every finding then re-checked by a separate skeptic before it counted. **10 findings survived. Of the 5 claims: 1 stands with an amendment, 2 weakened, 2 refuted. None held clean.** The audit's value was almost entirely in things a single reader cannot see:
  - **The `MOVE-9` cycle hazard (correction 14) is the headline.** Four of the nine relocations sit on live *runtime* import cycles that close on a barrel-imported class used as an `@Inject()` decorator argument — the one construct `tsc` cannot check. The auditor did not argue this from reading; it **probed Nest's `SELF_DECLARED_DEPS_METADATA` under the failing import order and got `undefined`**. The app boots today by accident of import order, and **biome's `organizeImports` regenerates the hazardous order**, so import hygiene is not an available mitigation. My "behaviour-neutral and compiler-verified" claim was wrong in the most dangerous possible way — the failure mode is a Nest resolution error at bootstrap.
  - **The mitigation is cheaper than the hazard, though**: my own S1 harness is the gate. `smoke.integration.ts` boots the real `AppModule` and already runs in the code-quality matrix, so the consequence is a **red PR, not a prod outage**. That is worth stating precisely because it changes MOVE-8 from "dangerous" to "gated".
  - **I quoted a dead code path as evidence.** My C3 argument cited `core/shopify/rules/GADG/sales-order.rules.ts`; `shopifyRules` has **no consumer in `src`**. The auditor replaced it with SAIRA's live prod mapping, which is far stronger — and reframed the finding as the **MULTI-FO** unit.
  - **My causal story for the collector shrinking was wrong.** It was `cfe14ca` extracting the canonicalisation pipeline, not the failure-publisher extraction. `I`/`I2` still retire, but for a different reason than I gave.
  - **The external contract DID change shape, twice** (correction 18) — a subscription renamed + re-topiced + re-filtered in one commit, and Cloud Run scaling set for the first time fleet-wide. My "nothing was renamed, re-typed or re-filtered" was simply false, and worse, **the harness is bound to the wrong layer to ever notice** → new `CONTRACT-GOLDEN` unit.
  - **The 10-minute loss window is wrong for the only tenant that matters.** SAIRA sets 30 minutes. The entire programme's urgency arithmetic was built on a figure SAIRA never reads.
  - **`depcruise` runs in no workflow at all** — so S0's "ratchet", and the repair I shipped in S1, change no build outcome. Sobering: I fixed a measurement instrument that was not plugged in.
  - **Sequencing refuted.** S2 was wrong as next on both of its sizing premises (`METRICS_SERVICE` is a `useExisting` alias, so one override covers both tokens; and the harness already stubs `Logger`). Detection and recovery must precede regression protection, because the poll window is **stateless** — no persisted watermark anywhere in `src` — so a missed window is invisible to any test suite by construction.
  - **Actioned:** `PREVIEW-ISO` urgent slice, 3 lines, [PR #233](https://github.com/gfs-bifrost/shopify-connector/pull/233) — provably inert for dev/prod. New units created: `PORTS`, `REAP-DI`, `MULTI-FO`, `CONTRACT-GOLDEN`, `DEPCRUISE-CI`. `MOVE-9` → `MOVE-8`.
  - **Standing lesson:** the re-review's own §8 predicted exactly this ("treat the numbers as solid and the recommendations as a proposal"). The numbers did hold — every measurement reproduced. It was the **judgements** that failed. Single-author architectural judgement on a live service is not good enough, and the cost of finding that out was one workflow.

- **2026-08-21** — **S0 merged; S1 built and opened; R6 invalidated.** Rehydrated after ~3 weeks and found the tree had moved a long way: **S0 landed** (#181, `8839d4a`), and Matt shipped ~20 PRs of the FUSE-1092/1093/1094 bulk-ingest workstream — `core/bulk/{tick,reap,reassemble}`, a dedicated reap coordination lane (topic + DLT + subscription), two new guarded routes (`POST /events/bulk-poll`, `POST /events/reap`), and #223/#227 routing bulk-enabled businesses **off** the metered poll with PURDYFIGG live on dev. **The service now has two ingest paths; the plan and the scenario catalog both describe one.** Corrections 6–13 above capture the consequences.
  - **Node chosen: S1, not a mechanical bundle.** S0 unblocked REHOME/F2/I/APP, but Matt has three open drafts (#185/#186 FUSE-999 observability, #187) that rewire logging, metrics and module providers across the tree — REHOME is a mass `git mv` of all eight modules and would have handed him a brutal conflict. S1 is all-new files, zero conflict, and it is the head of the critical path every Group C unit is gated behind.
  - **Phase 0's two risks are retired, not deferred, and both were real.** (1) `@shopify/shopify-api`'s node adapter runs `setAbstractFetchFunc(globalThis.fetch)` at import time, capturing fetch **by value** — so a `globalThis.fetch` stub installed later cannot work, and `bootHarness` imports `AppModule` **dynamically** to guarantee the wire is installed first. Import order is deliberately not relied on: biome sorts imports and duly reordered `harness.ts` on the first `lint:fix`. (2) Under jest, `globalThis.fetch` is Node's built-in bound to Node's **internal** undici, which reads its global dispatcher from the **outer realm**, not the sandbox one userland `setGlobalDispatcher` writes to — measured directly (`globalThis.fetch` → real DNS; `undici.fetch` → intercepted). **A dispatcher-only mock works in plain node and intercepts nothing under jest**, which is exactly why the plain-node spike passing was not sufficient evidence.
  - **`undici` pinned to 7.x.** Measured on both node majors: 6.x and 7.x intercept Node's built-in fetch, **8.x intercepts nothing** on either — while still registering a global-dispatcher symbol that looks correct. A plain `pnpm add -D undici` grabs 8.10.0 and would have produced a harness that silently made real network calls. Interception is therefore proven by a **canary call**, never a version or symbol check.
  - **Both negative tests recorded** (the actual acceptance criterion — a net that passes when interception is off is worse than none). Unmatched interceptor → 3 wire tests RED with 0 operations recorded; wire install removed → all 7 fail at the canary and boot refuses to proceed. Note the route still returns **202** in the first case because `validateConnector` catches, which is real behaviour (TOK-2) and precisely why the recorder rather than the status code is the assertion.
  - **Found a dead measurement instrument and fixed it.** `no-core-to-nestjs` reported **0 violations against 29 real ones** — see correction 6. Worth dwelling on: S0's stated deliverable was a depcruise baseline, S0's PR recorded "65 warnings, 0 errors", and half of what that number was supposed to be measuring was unmeasurable. **REHOME's deliverable is expressed as a ratchet against this rule.** Fixed in the S1 PR as a deliberate in-scope addition rather than a separate unit, since S1 exists to make verification trustworthy.
  - **R6 fired.** Prod Shopify connector count is **1** (SAIRA, active) with non-zero prod `records.collected` — see the READ FIRST block at the top. S1 itself is unaffected (test-only, zero production lines) so it still ships, but **re-sizing Group C against a live tenant is now the next planning decision and is Harry's call**, flagged on PR #231.
  - Verified: 47 suites / 701 tests (baseline 46/696 — exactly the +5 added), `build:check` exit 0, `lint:fix` exit 0, depcruise 109/0. mongod pinned to 7.0.24 and CI-cached (unpinned it resolves `latest` and pulls ~220MB per cold run). Confluence changelog + `#bifrost-forge` done; no Jira comment (no ticket, same as S0).

- **2026-07-30** — **S0 shipped**: recovered the stashed WIP from `hjf/shopify-rearchitect-s0-baseline`, re-verified fresh (536/536 tests, `build:check`, `build`, lint all clean; `depcruise` baseline confirmed at 65 warnings/0 errors), committed (`5393ab9`), and opened [shopify-connector PR #181](https://github.com/gfs-bifrost/shopify-connector/pull/181) — **no ticket**, tracked here instead (same convention as the dedupe-service NestJS migration). Prod Shopify connector count re-verified at time of PR: still `0` (R6). Confluence changelog + Slack done; no Jira comment (no ticket to comment on). Status set to 🟨 (PR open) rather than ✅ — flip to ✅ once it actually merges, not before.
- **2026-10-01** — **Subscription shape changed outside this programme (Poller Clear-Down E5, [PR #300](https://github.com/gfs-bifrost/shopify-connector/pull/300)).** `goods_out_confirmation` gains `retry_policy` 10s/600s and a `dead_letter_policy` (max 10) on `bifrost.<env>.confirmation_ready.v1.dlt`, and the controller now records a confirmation as a retryable failure on its 10th delivery attempt. **CONTRACT-GOLDEN** should baseline that shape, so it isn't read as drift.
