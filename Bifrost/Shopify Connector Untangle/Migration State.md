---
title: "Shopify Connector Untangle — Migration State"
programme: "shopify-connector-untangle"
status: planning
owner: "Harry Fitzgerald"
services: ["shopify-connector", "observability"]
created: "2026-11-13"
updated: "2026-11-13"
tags: [bifrost, migration-state]
---
# Shopify Connector Untangle — Migration State

Narrative and verdict: [[Shopify Connector Untangle/Overview|Overview]]. Repo: `gfs-bifrost/shopify-connector`, app
`apps/shopify-connector`. Monitors live in `gfs-bifrost/observability`
(`iac/projects/bifrost-observability/monitors.shopify-connector.tf`). `file:line` references are against
`origin/main` `84714fc` (2026-11-13). Re-check them before acting.

## Safeties — every unit, every PR
These are the programme's contract. A unit that can't meet one stops and says why in its Notes.

1. **Check first.**
   - Run `gh pr list` in the repo; other people's work lands in these files all the time. #368, Matt's change to quieten the shopify-api logs, touches the A units.
   - Re-read the prod Shopify connectors with `config-read production /api/v1/connectors?type=shopify` plus each connector's detail.
   - Paste the tenant count and each retrieval window into the PR body.
2. **Say the class in the title:**
   - `[see]`: logs or metrics only.
   - `[net]`: tests or CI.
   - `[fix]`: a behaviour change, stated plainly.
   - `[move]`: no behaviour change.

   Never mix `[fix]` and `[move]` in one PR.
3. **A `[move]` passes every wire scenario, canonical golden and the contract golden unmodified.**
   - A golden diff on a move is a regression, with no judgement call. dedupe holds a re-poll only when the canonical is deep-equal, so any canonical diff forwards orders twice.
   - Unit specs for moved classes may be rewritten; 36% of assertions are on mock calls. Wire scenarios are never weakened.
4. **Boot smoke and `no-circular` are green**, from C1 onwards.
5. **Dev deploy plus end-to-end evidence:**
   - For ingest: an ILG Test Store order (`shopify-test-order-create`).
   - For confirmations and stock adjustments: `mock-send`.
   - Use real outcome log lines and metric values from dev, not test output alone.
6. **Live-traffic flows move behind `shopify-connector.slice.<flow>`.** These are stock adjustment, goods-out and both ingests.
   - The flag's `false` is the old path.
   - The prod flip is a separate step, taken after G4.
   - Deleting the old path (the F units) waits for a soak with no regression in the outcome metric.
7. **A log line meant for 3am is `info` or above.** Prod runs `log_level = "info"`, dev runs `debug` (`iac/shopify-connector/env/*.tfvars`), so a line you saw in dev may not exist in prod.
8. **IaC changes (A6, B2, B4, C5 where it touches `iac/`): share the plan first**, per the plan-then-proceed rule.

## Unit status
Legend: ⬜ not started · 🟨 in progress · ✅ merged · ⛔ blocked · ⏸ deferred · ❌ dropped · 🔄 rescoped

### A — See: every flow says what happened (logs and metrics only)
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **A0** | ⬜ | Outcome convention + `recordOutcome` helper | | low | sonnet/medium | | Gated on G1. Each item emits one `info` event, `<flow>.outcome`, and one metric, `fuse.shopify.<flow>.outcome{outcome,reason,businessid,connectorid}`. Identity fields are fixed: `businessId`, `connectorId`, `shop`, `orderName`, `orderGid`, `customerRef` or `sku`, `correlationId`. It sits beside existing events and is additive. Copy the `core/bulk/reap` `REAP_METRIC.ORDERS{outcome}` shape. Verify with specs on the helper only. |
| **A1** | ⬜ | Metered ingest outcomes | A0 | low | sonnet/medium | | **Per order:** `published` / `failed` / `dropped_no_mapping` / `canonical_invalid`. Today a no-mapping drop is silent (`sales-order.collector.ts:~556`).<br>**Per shop:** `collected{n}` / `failed{reason}`, naming the shop and connector. Today it is an anonymous warning (`collector.ts:99`), and the token fetch sits outside the try block (`store.api.ts:114,483`).<br>**Per poll:** a summary with the real order count. Leave `records.collected` unchanged: PURDYFIGG's T3/T4 monitors read it with `source:bulk`. Coordinate with #368. |
| **A2** | ⬜ | Goods-out outcomes | A0 | low | sonnet/medium | | One per confirmation × connector, at `info`: `delivered` / `already_fulfilled` / `not_deliverable{reason}` / `failed{reason}` / `skipped_not_in_shop` / `redelivery_exhausted`. Every line carries `route=routed\|fanout`. This replaces debug-only `OrderNotFulfillable` / `RoutingComplete` / `RoutingSignals` (catalog `fulfillment-event.type.ts:10`, `confirmation-routing-event.type.ts:6,26`). Tag `FORWARD_FAILURE` (`:338`, `:588`). Partial multi-group success gets its own outcome; the behaviour stays as it is until D6. |
| **A3** | ⬜ | Stock-adjustment outcomes | A0 | low | sonnet/low | | Per shop: `adjusted` / `failed` / `variant_not_found` / `no_change` / `no_active_connector`. Today a failure is logged and acked (`shopify-stock-adjustment.service.ts:112`), and no-ops are silent (`:126`, debug events). Behaviour is unchanged; G3/D3 decide it. |
| **A4** | ⬜ | Token-health + bulk outcomes | A0 | low | sonnet/low | | **Revalidation:** a run summary plus a per-connector `ok` / `stale` / `invalid` / `probe_failed` outcome. Tag it `businessid`, not `customerId`. Revalidation start is debug today, and OK is silent.<br>**Bulk:** a per-connector tick outcome at `info` (`TickPolledOp` / `TickCompleted` are debug), and `OrderReapFailed` gains the order name. |
| **A5** | ⬜ | Correlation hygiene | A0 | med | opus/high | | **Scoping:** use `childScope` per record and per fan-out leg instead of `Correlation.set` in loops (`confirmation-events.controller.ts:90,169`). Log `Incoming record received` after the scope is set (`:131` vs `:149`). Give the background tag (`shopify-order-tagging.service.ts:46`) its own child scope.<br>**Publishing:** pass identity explicitly. `pubsub.service.ts:234-250` reads it from ALS and defaults `correlationId` to `""`.<br>**Scar tissue:** the CLS `runWith` nesting must survive. |
| **A6** | ⬜ | Monitors on the outcomes | A1,A2,A3,A4 | med | sonnet/medium | | Repo: `gfs-bifrost/observability`. Share the plan first.<br>**New monitors:**<br>- zero ingest per metered tenant (SAIRA, ESCENTRIC, ESCENTRICPL), with a window well under each tenant's retrieval window (4–5h) and tolerant of night-time volume<br>- poll run failed<br>- goods-out `not_deliverable` / `failed` rate<br>- stock-adjustment `failed`<br>- reap dead-letter queue depth<br>**Dead monitors to fix:**<br>- "Inventory update rejected" greps strings that aren't in the code<br>- the `lines_skipped` threshold of 1,000,000 never fires<br>- the GraphQL failures monitor greps lines the recorder suppresses<br>**Done means:** each new monitor tripped once on dev and seen to page (G4). |
| **A7** | ⬜ | 3am runbook per flow | A6 | low | sonnet/low | | Waypoint `operations.md`: for each flow, page → saved Datadog query → orchestrator file → levers (flag, scheduler pause, rollback, backfill). |

### B — Stop and recover
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **B1** | ⬜ | Fast-stop + rollback drill, timed | | med | sonnet/medium | | No `traffic` block exists in `cloud-run.tf`, and tfvar levers need a merge plus the prod gate, which is too slow.<br>**Drill on dev:**<br>1. Pause the schedulers out of band (`gcloud scheduler jobs pause`).<br>2. `gcloud run services update-traffic --to-revisions=<prior>=100`.<br>3. Resume.<br>Time it. Record what the next Terraform apply does to the pinned traffic. Write the runbook into `operations.md`; there's no PR. Done when the measured time sits well under the shortest live window (4h). |
| **B2** | ⬜ | Deploy rails | | med | sonnet/medium | | Record the prior revision in the job summary before each prod apply. Make the prod jobs `need` the dev apply. Add a post-deploy smoke: liveness, plus the guard's 401 on an authenticated route. Platform hat: if this belongs in the reusable workflows, do it there. |
| **B3** | ⬜ | Backfill route | C3 | high | opus/high | | Re-ingest one connector over an explicit `created_at` window, keeping its non-time conditions. Remember that conditions are full-replace.<br>**Verify on dev:**<br>- re-sent unchanged orders are held by dedupe<br>- missing ones flow through<br>**Open, answer before prod use:** what happens downstream when a re-sent order's canonical changed (an edited Shopify order)? dedupe forwards it, then snap-adapter tries to create it again. |
| **B4** | ⬜ | Preview isolation | | med | sonnet/medium | | Previews create subscriptions on six dev shared topics, and act on them with dev's ShopTokens, Mongo and Redis (`remote.tf:55-56`, `pubsub.tf`). Gate those subscriptions off in previews, and drive previews by direct push instead. Standing rule: never preview a branch that touches token or lock code. Share the plan first. |

### C — Pin behaviour (the net)
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **C1** | ⬜ | CI rails | | low | sonnet/low | | Add a `pretest` that builds `packages/shopify-token-management`; a fresh checkout fails 31/64 suites without it. Run the token package's own suite in the connector workflow.<br>Add depcruise to the code-quality matrix: runtime `no-circular` as `error`, with today's two cycles allowlisted by name, and the layering rules left at `warn` (baseline 182). |
| **C2** | ⬜ | Break the two runtime cycles | C1 | med | sonnet/medium | | **Cycle A:** `core/shopify/index.ts:7` re-exports `use-cases`, which imports the collections/confirmations barrels, which import back.<br>**Cycle B:** `adapters/db/mongo.connection.ts:11` → `providers/health` → `modules/mongo` → `adapters/db`.<br>Import by path and clear the allowlist. Boot smoke gates it. It is `[move]` and behaviour-neutral. |
| **C3** | ⬜ | Wire scenarios: ingest | C1 | high | opus/medium | | Through the real `AppModule` with the existing `shopify-wire` and `harness.pubsub` recorder; the recorder is built but unused today.<br>**Metered poll scenarios:**<br>- a SAIRA-shaped connector<br>- **two connectors on one shop**, ESCENTRIC UK/PL-shaped. With the cache flag off this should go RED today, which feeds D1.<br>**Bulk:** tick plus reap, PURDYFIGG-shaped.<br>**Golden:** each published canonical, its attributes and its metadata. |
| **C4** | ⬜ | Wire scenarios: confirmations | C1 | high | opus/medium | | **Goods-out:**<br>- routed<br>- fan-out across two connectors on one shop<br>- partial multi-group<br>- not-in-shop<br>- already fulfilled<br>Assert on the `fulfillmentCreate` wire and on `confirmation_made` / `confirmation_data_failure`.<br>**Stock adjustment:** pin the `@idempotent` key bytes (`stock-adjustment.handler.ts:191`).<br>**Tags:** ack and failure. |
| **C5** | ⬜ | Contract golden | | med | sonnet/medium | | From IaC, pin:<br>- subscriptions, filters, ack deadlines, retry and dead-letter settings<br>- topics<br>- Cloud Run scaling and env<br>A change fails unless the golden is updated in the same PR with a reason. Baseline the 2026-10-01 `confirmation_ready` retry/DLT shape as current, not drift. |

### D — Fix (behaviour changes, one per PR, each after its flow is pinned)
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **D1** | ⬜ | Per-connector API cache key, always | C3 | med | sonnet/medium | | Make the per-connector keying in `api.factory.ts` (`cacheKeyFor`) unconditional, then retire the flag `shopify-connector.api-cache-per-connector`. It has been on in prod since 2026-10-27 and expires 2027-01-31, and it reads `false` (shop keying) whenever the reader has no snapshot. ESCENTRIC and ESCENTRICPL share `escentric.myshopify.com`. Prove it with C3's two-connectors-one-shop scenario, RED with the flag off and then GREEN. **Do this early.** |
| **D2** | ⬜ | One bad connector stops aborting everyone | C3,A1 | med | opus/medium | | `ConnectorConfigProvider.getAll()` runs `Promise.all` over hydration (`connector-config.provider.ts:83`). One parse failure or mapping-fetch failure kills the poll, tick and revalidation for every shop. Make it per-connector, with a failure outcome. Fetch the goods-out mapping only for flows that read it (`:174-190`). |
| **D3** | ⛔ | Stock adjustment failure semantics | C4,A3 | med | sonnet/medium | | Blocked on G3(a). Today a rejection is acked 202 with nothing recorded, but the backlog monitor's text says it redelivers. |
| **D4** | ⬜ | Token persist-error releases the lock | | low | sonnet/medium | | `token-provider-base.ts:346-366` logs, counts and throws without unlocking, and `shop-token-provider.spec.ts:984-987` documents the opposite. The lock expires after 30s, so the real cost is a spent refresh token. Package change: it redeploys all three apps. Scar tissue: native driver only. |
| **D5** | ⬜ | Remove the dead AuthFailure state | C3 | low | sonnet/low | | Set at `store.api.ts:159-162`. `hasAuthFailure` (`:592`) has no callers, and the next `getSession` resets it. Delete it rather than wire it; recovery already lives in the token path. |
| **D6** | ⛔ | Goods-out partial multi-group success | C4,A2 | high | opus/high | | Blocked on G3(b). When a later group fails, the handler throws after earlier groups were already created in Shopify (`sales-order-confirmation.handler.ts:246-293`). |

### E — Move: one flow per slice (no behaviour change)
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **E1** | ⬜ | Slice: token-health | C2,A4 | low | sonnet/medium | | First slice; it sets the pattern under G2. Covers the revalidate route and its mutex, which swallows errors (`events.controller.ts:169-188`). The route and IaC don't change. |
| **E2** | ⬜ | Slice: config-refresh | C2 | low | sonnet/medium | | The config and feature-flag revision routes (`events.controller.ts:275-339`). |
| **E3** | ⬜ | Slice: preview + test-orders | C2 | low | sonnet/low | | Manual traffic only. `TestOrdersModule` shares AppModule's `ShopifyModule` instance (`test-orders.module.ts:9-15`). |
| **E4** | ⬜ | Slice: order-tagging | C2,C4 | low | sonnet/medium | | Ack, failure, and the background tag that goods-out calls. Tagging stays detached; always 202. |
| **E5** | ⬜ | Slice: stock-adjustment (flagged) | C2,C4,A3,A6 | med | sonnet/medium | | Moves the made-publish out of the controller (`confirmation-events.controller.ts:100-119`). The idempotency key stays byte-identical. Prod flip after G4. |
| **E6a** | ⬜ | Goods-out: split routed / fan-out, drop dead branches | C2,C4,A2 | med | opus/medium | | Lifts routed (`shopify-sales-order.service.ts:194-395, 717-772`) and fan-out (`:397-647`) into separate files. Deletes the unreachable `!routed` branches (`:213, :317-323, :349, :725`). |
| **E6b** | ⬜ | Slice: goods-out (flagged) | E6a,E4,A6,B1 | high | opus/high | | One orchestrator per route kind, returning outcomes. Scar tissue: status short-circuit before the owner-map fetch; routed failures always recorded; failure envelope semantics; the redelivery budget. Never merge the two loops. |
| **E7** | ⬜ | Split `ShopifyStoreApi`; rules stop riding on the instance | D1,C3,C4 | high | opus/high | | Split into transport / bulk / inventory / token. Retrieval rules become an explicit argument of the ingest query only. **First, list which query documents declare `$query`**: a non-ingest query that does is silently filtered by retrieval rules today. Fix that as its own `[fix]` if found. `GRAPHQL_REQUEST_RETRIES = 0` and the 30s TTL stay. |
| **E8** | ⬜ | Slice: ingest-bulk | C2,C3,A4,A6,B1 | med | opus/medium | | Tick and reap are already slice-shaped. Keep `tickMutex`, the reap dead-letter queue and the concurrency bound in `cloud-run.tf`. Only bulk-enabled businesses are affected. |
| **E9** | ⬜ | Slice: ingest-metered (flagged, dual path) | E7,D2,C3,A1,A6,B1,B3 | high | opus/high | | Poll, manual poll, the collector, and the publish loop moved out of the controller (`events.controller.ts:96-160, 212-267`). The C3 goldens must match byte for byte across the flag.<br>**Scar tissue:**<br>- CLS nesting<br>- failures published, not thrown<br>- page caps (`collector:42-45`)<br>- batch of 10 (`:54`)<br>- full-replace conditions<br>Prod flip after G4, with B1 rehearsed that week. |

### F — Retire
| Unit | St | Summary | Deps | Risk | Tier | PR | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **F1** | ⬜ | Delete old stock-adjustment path + flag | E5 | low | sonnet/low | | After a soak with no `failed` regression. |
| **F2** | ⬜ | Delete old goods-out path + flag | E6b | low | sonnet/low | | After a soak. |
| **F3** | ⬜ | Delete old metered-ingest path + flag | E9 | med | sonnet/low | | After a soak that covers at least one full trading week for every metered tenant. |
| **F4** | ⬜ | Retire `providers/` `modules/` `utils/`; layering rules to `error` | E1,E2,E3,E4,E8,F1,F2,F3 | low | sonnet/medium | | Update the repo `CLAUDE.md` and Waypoint `architecture.md`. Drop the stale `ReapConcurrencyGate` / `REAP_MAX_CONCURRENCY_PER_INSTANCE` mention, which doesn't exist in `src`. |

## Gates
- [ ] **G1 — Outcome convention agreed** — blocks A0, A1, A2, A3, A4, A5. Harry approves the shape in A0's Notes: one event and one metric per item, fixed identity fields, old events kept until A6 moves the monitors.
- [ ] **G2 — Target-shape ADR signed** — blocks E1, E2, E3, E4, E5, E6a, E6b, E7, E8, E9. This trips an Agent Stop Condition.
  - New directories: `core/<flow>/`, `core/kernel/`, `bootstrap/containers/`.
  - Retiring `providers/`, `modules/` and `utils/`.
  - Slice classes are plain (no `@Injectable`), wired by `useFactory` in `bootstrap/`.
  - No barrels in `core/`.
  - Slices import kernel interfaces, not adapters.
  - Flag keys are global or per-business.

  Harry signs it; record it with `wp decide --record`.
- [ ] **G3 — Two product decisions** — blocks D3, D6. (a) When Shopify rejects a stock adjustment, nack for redelivery (the `@idempotent` key makes retries safe) or publish a failure record? (b) When goods-out partially succeeds across fulfilment groups, what is the outcome, and what goes to `confirmation_made` / `confirmation_data_failure`?
- [ ] **G4 — Detection proven** — blocks E5, E6b, E8, E9. A6's monitors are applied in prod, and each has been tripped once on dev and seen to page, before any live-traffic flow moves.

## Risks
- **R1 ★ Silent, permanent order loss on the metered path.** The poll window keeps no state (no watermark), and no zero-ingest monitor covers SAIRA, ESCENTRIC or ESCENTRICPL. Windows are 4–5h. Mitigations: A1, A6, B1 and B3 before E9. — open.
- **R2 ★ Canonical drift doubles orders through dedupe.** dedupe holds a re-poll only when the record is deep-equal (`isEqual`). Each order is polled about 48–60 times inside its window. Mitigation: C3 goldens are a hard gate on every `[move]`. — open.
- **R3 ★ Shared-shop config leak held by a fail-unsafe flag.** ESCENTRIC UK and PL share one shop, and the cache flag defaults to shop keying when the reader has no snapshot. Mitigation: D1. — open.
- **R4 ★ The app boots by import order.** There are two runtime cycles, `@Inject()` arguments are `undefined` under other load orders, and Biome reorders imports. Mitigations: C1/C2, then factory wiring in E. — open.
- **R5 Stock adjustments lost silently.** They are acked on failure, and the monitor text claims they are redelivered. Mitigations: A3 now (visible), D3 after G3. — open.
- **R6 Preview envs double-process dev messages with dev's real tokens.** Mitigation: B4. — open.
- **R7 Other people's work moves the files mid-unit.** The old programme had four units done by others and saw the contract change twice. Mitigations: C5, small units, and the PR check in Safeties 1. — standing.
- **R8 Refactor-hostile specs.** 384 of 1,062 assertions are on mock calls. Wire scenarios are the contract, and unit specs are allowed to churn. — standing.
- **R9 Dev logs at `debug`, prod at `info`.** A signal verified on dev may not exist in prod. Mitigation: Safeties 7. — standing.
- **R10 Retrieval rules ride on every query.** `store.api.ts:129-132` merges them into every query's `query` variable. A non-ingest query whose document declares `$query` may be filtered silently. E7 checks this first. — open.

## Decision log
- **2026-11-13** — **Programme created; [[Shopify Connector Rearchitecture/Overview|Shopify Connector Rearchitecture]] retired, not deleted.**
  - **Why:** its layer-compliance framing measured the wrong thing. The tree and the tenant base moved under it. Prod now has four active Shopify connectors, and the retrieval windows are 4–5h rather than its 10 and 30 minutes.
  - **The new north star is 3am debuggability.** The order is see → stop → pin → fix → move → retire.
  - **Carried over:** the scar tissue and the live bugs (D4, D5, A1).
- **2026-11-13** — **Review method.** Four independent reviewers on `84714fc` (flows/coupling, debuggability, safety net, target shape), then a hand re-check against code and live config. The re-check followed the old programme's lesson that single-author judgement didn't survive audit. Claims re-checked:
  - stock adjustments acked on failure (`shopify-stock-adjustment.service.ts:112`, controller returns 202)
  - routing events at debug only, with prod `info` and dev `debug`
  - `Promise.all` hydration
  - `routed` always true
  - rules merged into every query
  - the cache flag's prod state and the shared Escentric shop
  - the dedupe deep-equality hold
- **2026-11-13** — **Cutover uses the runtime feature flags already wired.** A slice flag's `false` is always the old, proven path, so the reader's fail-closed default is the safe direction. D1 removes the one flag where `false` is the unsafe direction.

## Scar tissue
- **ShopToken lock:** on the native `mongodb` driver only, never Prisma. The filters differ by driver on purpose: `isRefreshing: { $ne: true }` and `lockTimeout: null` match a missing field. Don't converge the release shape (`$unset` vs `null`) or the reclaim predicates. Incident 2026-07-02.
- **Ingest:** failures are published, not thrown. Keep the pagination caps (`sales-order.collector.ts:42-45`) and the detail batch of 10 (`:54`).
- **CLS:** the `runWith` nesting in `events.controller.ts` (~111-141) and `sales-order.collector.ts` (~87, 481) survives every move. Nothing catches a break until C3.
- **Mutexes:** three single-flight mutexes, one each for poll, revalidate and bulk tick (`bulk-poll.controller.ts:25`). Each is per instance and best-effort, and stays that way.
- **GraphQL:** `GRAPHQL_REQUEST_RETRIES = 0` and the 30s LRU TTL on `ShopifyStoreApi` are deliberate.
- **Goods-out:**
  - The status short-circuit (`sales-order-confirmation.handler.ts:130`) runs before the owner-map fetch (`:205`).
  - Routed failures are always recorded.
  - The failure `recordType`/`useCase` is `goods_out_confirmation`, and `connectorId` is the connector that failed.
  - `MAX_TRANSIENT_DELIVERY_ATTEMPTS` equals the subscription's `max_delivery_attempts` (10).
- **`confirmation_ready` filter:** relies on the poller stamping `source`/`broadcast`.
- **Retrieval conditions:** full-replace, not AND-merge. A connector's own conditions replace the 10-minute default entirely.
- **Stock adjustment:** the `@idempotent` key (`uuidv5(...)`, `stock-adjustment.handler.ts:191`) stays byte-identical.
- **Canonical output:** deep-equality is load-bearing for dedupe (R2).
- **Characterization harness:**
  - `@shopify/shopify-api` captures `fetch` by value at import, so `AppModule` is imported dynamically.
  - `undici` is pinned to 7.x; 8.x intercepts nothing and gives no sign of it.
  - Interception is proven by a canary call, not by a version check.
- **Imports:** Biome `organizeImports` reorders imports, so import order is never a mitigation for a cycle.
