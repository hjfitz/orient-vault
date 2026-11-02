---
tags: [explain]
date: '2026-08-25'
title: 'GADG bulk-ingest soak test: what the order seeder found'
thesis: "The synthetic order seeder proved the GADG bulk-ingest path works end to end. Shopify's dev-store order cap and snap-adapter's SNAP write throughput are the real limits."
confidence: high
---
# GADG bulk-ingest soak test: what the order seeder found

```orient-bluf
{ "v": 1, "bluf": "The synthetic order seeder proved the GADG bulk-ingest path works end to end. Shopify's dev-store order cap and snap-adapter's SNAP write throughput are the real limits.", "confidence": "high", "action": "Decide whether to restore collector-dev's 28 stubbed subscriptions, and ticket the SNAP NullReferenceException on kit SKU TTRS." }
```

## Situation

- **CONFIRMED** Nothing in Fuse could create Shopify orders on demand, so the bulk-ingest tick (FUSE-1092/93/94) had no volume test. [1][2]
- **CONFIRMED** The fix was a dev-only seeder in `shopify-connector`, aimed at GADG's "ILG Test Store". It started at 6,000 orders and grew to 10,000 mid-run. [1]
- **CONFIRMED** The seeder chains itself through its own Pub/Sub tick, never an in-process loop, because Cloud Run throttles CPU between requests. It serves one allowlisted business, and a Mongo run doc tracks each run. [1]
- **CONFIRMED** GADG joined `bulk_ingest_enabled_businesses` in dev, beside `PURDYFIGG`. [1]
- **CONFIRMED** Both ingest lanes build the Shopify filter from the same `retrievalConditions.salesOrder` config through one `ShopifyRuleBuilder` singleton. GADG's sentinel-tag filter therefore ingests nothing in either lane, by design. [1]
- **CONFIRMED** GADG's config changed repeatedly all day on purpose. Harry set `isActive: active`, a 30-day retrieval window and a multi-day volume ramp. [3]
- **CONFIRMED** The bulk tick's reap count climbed from 24,196 to 25,124 in 25 minutes. That is the ramp working, not a stuck loop. [3]

## Assessment

- **CONFIRMED** Shopify caps trial and dev stores at five `orderCreate` calls per minute. Measured acceptance: 12 of 12 at 30s spacing, 11 of 12 at 10s, 8 of 16 at 5s. Shopify staff confirmed the cap. [4]
- **CONFIRMED** Orders are not in `bulkOperationRunMutation`'s supported list, so no bulk route exists. The 5/min cap is the floor for any dev-store order soak. A paid store would not hit it. [4]
- **CONFIRMED** The first 1,000 orders cleared the ingest path. A manual poll pulled 165 through canonicalisation, dedupe, collector and snap-adapter into SNAP with zero connector errors. [1]
- **CONFIRMED** SNAP's field errors `SKUId - MANDATORY` and `UnitOfMeasure - Invalid Unit` (on `"EA"`) share one cause. `Email - MANDATORY` is independent. [5]
- **CONFIRMED** A controlled retest resubmitted one captured canonical record through fapi, changing only `skuId` from `""` to a real GADG SKU. Both errors cleared together. [5]
- **ASSESSED** SNAP checks the unit against the product resolved from the SKU. An empty SKU resolves no product, so the unit reads as invalid. The retest supports this but does not show SNAP's internals. [5]
- **CONFIRMED** The deploy check failed twice. The 12s pacing fix (`8a9bae88`) sat unpushed, so the overnight deploy still ran 10s pacing. [1]
- **CONFIRMED** Refusals came back at 25%, not the predicted ~10%, and 96s tick spacing was impossible under a 12s constant. [1]
- **CONFIRMED** The earlier "10% refusal" read was one post-deploy batch. The store had sat idle and Shopify's rate bucket had refilled. [1]
- **ASSESSED** The root cause was treating `git commit` as `git push` and a green pipeline as proof of the deployed image. Checking the running image sha against the intended commit would have caught both. [1]
- **CONFIRMED** `ShopifyApiException: Shopify Api failed to build` fired 12 times between 15:11:42 and 15:13:30 UTC on 2026-08-25, then stopped. Seeding continued and the empty-batch abort guard never tripped. [6]
- **UNKNOWN** The exception's root cause. `buildShopApi()` throws `BuildFailure` for an active connector with no recorded auth failure that needs a session rebuild. The trigger stays unestablished. [6]

### Downstream load, 15:51 UTC

- **CONFIRMED** dedupe-service holds 26,853 unique GADG sales orders and has blocked 82,283 duplicate resends. Its inbound subscription peaks near 3,726 undelivered messages and drains in about 76s. [7]
- **CONFIRMED** No timeout-driven nacks appear anywhere. Dev showed zero 5xx or 429 over 6h and zero `@requestor.deliveryAttempt:>1` on snap-adapter's create path. shopify-connector polls via GraphQL, so ingest has no webhook-timeout exposure. [7]
- **CONFIRMED** snap-adapter fails about 92% of its SNAP writes: 184 failed against 17 succeeded in a 4h sample. replay-service holds 129,668 GADG failure records from that day. [7]
- **CONFIRMED** Seeded orders with an empty `skuId` and no `shipContacts` email fail SNAP validation. Harry knows this harness noise. [7]
- **CONFIRMED** A well-formed order on kit SKU `TTRS` (a component of the `XTTRS` kit) throws a raw SNAP `NullReferenceException` on create. No ticket exists. [7][8]
- **CONFIRMED** snap-adapter's consume subscription holds about 9,707 undelivered messages, oldest unacked about 3h45m. Its SNAP write rate cannot match the soak rate. [7]
- **ASSESSED** A sales order landing then would wait hours before its first attempt. Everything upstream absorbs the volume. [7]

### Collector, 20:12 BST

- **CONFIRMED** `collector-dev` scaled to 33 instances because it had no `max_instance_count`, so Cloud Run defaulted to 100. [9]
- **CONFIRMED** Harry directed two actions. First, all 28 collector push subscriptions went to pull with an empty endpoint. Instances then fell from 33 to 7, and Harry's session backed up the 28 original endpoints for restoration. [9]
- **CONFIRMED** Second, a `max_instance_count = 15` cap went onto collector's Cloud Run Terraform. It deployed to dev, and the live revision showed `autoscaling.knative.dev/maxScale=15`. [9]
- **ASSESSED** The cap derives from the dedicated Atlas M10 connection floor: 1,500 connections divided by Cloud Run concurrency 80 gives about 18. It rounds down to 15 for margin. [9]
- **CONFIRMED** The Terraform edit first landed in collector's main checkout. It was caught before commit, reverted with only two files touched, and redone in a worktree. [9]
- **CONFIRMED** Seeding resumed toward 10,000 once collector sat outside the pipeline. Seeding and ingestion are independent. [9]

## Open items

| Item | Owner | By |
|---|---|---|
| Decide whether to restore collector-dev's 28 stubbed subscriptions. Restoring exposes it to its backlog plus the live ramp. Status after 20:12 BST on 2026-08-25 is UNKNOWN. | Harry | UNKNOWN |
| Ticket the SNAP `NullReferenceException` on kit SKU `TTRS` (`XTTRS` kit). | Harry | UNKNOWN |
| Root-cause the `ShopifyApiException` blip, if it recurs. | Harry | UNKNOWN |
| Spot-check 2026-10-12: collector `master` carries no `max_instance_count` and no PR for the cap branch appears. The cap may never have merged. [10] | Harry | UNKNOWN |

## Evidence

```orient-evidence
{
  "v": 1,
  "items": [
    { "id": 1, "kind": "doc", "ref": "gfs-bifrost/shopify-connector branch hjf/bulk-test-order-seeder: e0460448 seeder, 67450b58 surface Shopify user errors, 8a9bae88 12s pacing fix (live on revision shopify-connector-dev-cr-00456-sjk), 1855314b GADG onto bulk-ingest allowlist" },
    { "id": 2, "kind": "ticket", "ref": "FUSE-1092", "note": "bulk-ingest tick, with FUSE-1093 and FUSE-1094" },
    { "id": 3, "kind": "log", "ref": "GADG connector config revisions and bulk tick reap count 24,196 to 25,124 over 25 minutes, 2026-08-25" },
    { "id": 4, "kind": "doc", "ref": "Shopify community threads 'OrderCreate mutation error after 5 imports' and 'Bulk operations for order create'; seeder pacing measurements at 30s, 10s and 5s" },
    { "id": 5, "kind": "log", "ref": "fapi resubmission of a canonical record from a real SNAP rejection, twice, varying only skuId" },
    { "id": 6, "kind": "log", "ref": "jsonPayload.error=~\"ShopifyApiException\" 12 hits 2026-08-25T15:11:42Z to 15:13:30Z, none since" },
    { "id": 7, "kind": "log", "ref": "dedupe-service, snap-adapter and shopify-connector dev logs and Pub/Sub backlog metrics, 6h to 15:51 UTC 2026-08-25" },
    { "id": 8, "kind": "doc", "ref": "Bifrost/Kit Confirmations & Short-Ship (FUSE-785)" },
    { "id": 9, "kind": "doc", "ref": "gfs-bifrost/collector branch hjf/fuse-1000-collector-scaling-cap, commit 1d1b05f, iac/projects/collector/cloud-run.tf and variables.tf" },
    { "id": 10, "kind": "code", "ref": "iac/projects/collector/cloud-run.tf@9c4d56d", "note": "origin/master on 2026-10-12: scaling block sets min_instance_count only" }
  ]
}
```
