---
title: "Shopify Connector Untangle — Overview"
status: planning
verdict: go-safeties-first
owner: "Harry Fitzgerald"
services: ["shopify-connector", "observability"]
created: "2026-11-13"
updated: "2026-11-13"
tags: [bifrost, shopify-connector]
---
# Shopify Connector Untangle — Overview

**North star.** An engineer paged at 3am goes from one alert to the code that handled the order or
confirmation, what it decided and why, in minutes and without reading three classes.

## Deliverables
- [[Shopify Connector Untangle/Migration State|Migration State]] — the live source of truth for progress
- Supersedes [[Shopify Connector Rearchitecture/Overview|Shopify Connector Rearchitecture]] (retired 2026-11-13). Its scar tissue and live bugs are carried into the State doc. Its ledger is not.

## Verdict
**Go, safeties first.** No flow is restructured until four things are true for it:
1. Prod logs it at `info`.
2. It is monitored.
3. A wire-level test through the real `AppModule` pins it.
4. It can be switched back without a deploy.

Two decisions are Harry's before gated units start: **G1** (the outcome convention) and **G2** (the target-shape ADR). Units with no gate can start now.

## What the review found (2026-11-13)
Four independent reviewers looked at `origin/main` `84714fc`, one lens each: flows and coupling, 3am debuggability, the safety net, and the target shape. The load-bearing claims below were then re-checked by hand against the code and live config.

The service isn't a mess because its layers have the wrong names. These five things make it one.

**1. Flows share stateful hubs and branch inside them.**
- 17 routes in 9 controllers go through four hubs: `ConnectorConfigProvider`, `ShopifyStoreApi`, `PubsubService` and `ConfigApiAdaptor`.
- `ShopifySalesOrderService` (786 lines) holds preview, poll, routed confirmation and fan-out.
- `EventsController` holds five flows and two copies of the collect-then-publish loop.
- Goods-out has two routing implementations in one class. In the routed one, `routed` is always true after the early return (`shopify-sales-order.service.ts:198-203`), so its `!routed` branches never run.

**2. A query's behaviour depends on cache state.**
- `ShopifyStoreApi` carries one connector's retrieval rules and merges them into every query's `query` variable (`store.api.ts:129-132`). Instances are cached for 30s.
- ESCENTRIC and ESCENTRICPL are two prod connectors on **one shop** (`escentric.myshopify.com`), split by a UK/EU tag.
- Their rules are kept apart only by the runtime flag `shopify-connector.api-cache-per-connector`, which has been on since 2026-10-27 and expires 2027-01-31.
- The flag reader returns `false` whenever it has no snapshot, and `false` is the unsafe value.

**3. The app boots by accident of import order.**
- There are two runtime import cycles: one through the `core/shopify/index.ts` barrel, one through mongo/health.
- Loaded in another order, `@Inject(SalesOrderCollector)`, the confirmation handlers and `MONGO_COLLECTIONS` resolve to `undefined`.
- Biome's import sorting regenerates the hazardous order, so tidying imports can't fix it.

**4. Prod can't tell you what happened to one order.** Prod logs at `info` and dev at `debug`, and much of the story is at `debug`.
- A routed confirmation that isn't delivered leaves no prod log and no metric (`OrderNotFulfillable`, `RoutingComplete` and `RoutingSignals` are all `debug`).
- Poll start is `debug`, and the poll route's access log is excluded.
- A shop that fails to poll shows up only as an anonymous `N failed` warning.
- `records.collected` counts shops, not orders.
- A stock adjustment Shopify rejects is logged and acked with 202. No failure is recorded and nothing is redelivered.
- One connector whose hydration fails aborts every shop's poll (`connector-config.provider.ts:83`, `Promise.all`).
- No single id follows an order end to end. The practical join is `(businessId, customerRef)`, and the field names vary (`shop`/`shopName`/`shopifyUri`/`storeName`).

**5. Almost nothing would catch a refactor mistake.**
- There are 902 tests at 93% line coverage. The only end-to-end test through the real `AppModule` covers liveness, the guard's 401 and token revalidation.
- 36% of assertions are on mock calls, so any restructure rewrites them.
- depcruise runs in no workflow.
- Preview environments subscribe to dev's shared topics and use dev's real ShopTokens.
- The only rollback is a redeploy.
- Zero-ingest monitors cover only PURDYFIGG's bulk path. Nothing fires if SAIRA, ESCENTRIC or ESCENTRICPL stop ingesting.

**Worth copying:**
- `core/bulk/reap`: factory-built, no decorators, leaf imports, and a typed per-order outcome metric.
- The `packages/shopify-token-management` boundary: framework-free, with the consumer supplying the collection, logger and metrics.
- From the egress service, its module-per-flow layout and decisions-as-data. Not its 1,146-line orchestrator.

## Live context that sizes the risk
Read from prod config-service on 2026-11-13.

| Tenant | Path | Retrieval window | Notes |
| --- | --- | --- | --- |
| SAIRA | metered | 5h (`created_at >= 18000000`) | Tag `ILG_RELEASED`. Stock adjustments and outbound tags on. |
| ESCENTRIC | metered | 4h | Same shop as ESCENTRICPL, tag `UK`. |
| ESCENTRICPL | metered | 4h | Same shop, tag `EU`. |
| PURDYFIGG | bulk | n/a | The only tenant with ingest monitors (T1–T6). |

The old programme's 10-minute and 30-minute windows are stale. A missed window is still permanent, silent loss, because nothing persists a watermark. But the budget to detect and recover is hours, not minutes.

## Why this needs a programme
- Four live merchants ingest through a poll window with no watermark. An ingest regression that outlasts the window loses orders for good, and nothing says so.
- dedupe-service holds a re-polled order only when its canonical record is deep-equal to the stored one (`dedupe-service` `sales-order.service.ts`, `isEqual`). Even a cosmetic canonical change forwards every in-window order a second time.
- Other people ship features into the same files all the time. The old programme saw four of its units done by others and the external contract change twice.

That combination needs sequencing and hard gates, not a big-bang rewrite.

## Strategy
**See → stop → pin → fix → move → retire.**
1. **See (A).** Every flow emits one `info` outcome event and one outcome metric per item, with the same identity fields. Then monitors on those metrics, including zero-ingest per metered tenant. Log and metric changes only.
2. **Stop and recover (B).** A timed fast-stop drill (pause the scheduler out of band, pin Cloud Run traffic to the prior revision), deploy rails, a backfill route and preview isolation.
3. **Pin (C).** CI rails, breaking the import cycles, wire-level scenarios through the real `AppModule` per flow, and a contract golden over the IaC. The scenarios record the Shopify wire and Pub/Sub publishes and golden the canonical output.
4. **Fix (D).** The behaviour bugs, one per PR, each only after its flow is pinned.
5. **Move (E).** One flow at a time into its own slice under `core/`: one controller, one orchestrator you read top to bottom, a typed outcome, and plain classes wired by factory in `bootstrap/`.
   - Live-traffic flows switch behind a runtime flag whose `false` is the old path. The flag reader's fail-closed default is then the safe one, and reverting is a flag flip with no deploy.
6. **Retire (F).** Delete each old path after a soak. Finally, flip the layering rules to `error`.

**Cutover mechanism.** `@gfs-bifrost/remote-config` feature flags are already wired (`modules/shopify/shopify.module.ts:108-115`) and push-refreshed. Flags are global in v1 (`targets` is `null`), so a prod flip moves all tenants at once unless the G2 ADR chooses per-business keys.

## What carries over from the retired programme
- **Scar tissue:** all of it, in the State doc.
- **Live bugs:**
  - The token persist-error unlock is now D4. It is lower severity than the old programme said, because the lock expires after 30s.
  - The dead `AuthFailure` state is now D5.
  - The `records.collected` units problem is folded into A1.
- **Ideas that survive under new ids:** preview isolation (B4), contract golden (C5), depcruise in CI (C1), the recovery runbook (B1, B3) and ingest monitors (A6).
- **What doesn't survive:** the layer-compliance framing, the 48-unit ledger, and the ports/MOVE-8 plan.

## Next
G1 and G2 are Harry's calls. Four units have no gate and can start now: **B1** (fast-stop drill), **C1** (CI rails), **C5** (contract golden) and **B4** (preview isolation). Drive the programme with `waypoint-programme`.
