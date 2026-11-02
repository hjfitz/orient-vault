---
ticket: FUSE-1317
title: Dictionary lookups and tracking URLs on Shopify goods-out confirmations
service: shopify-connector
status: active
created: '2026-10-19'
updated: '2026-10-19'
repo: /home/hjf/code/fuse/shopify-connector
worktree: /home/hjf/code/fuse/shopify-connector/.claude/worktrees/fuse-1317-shopify-confirmation-dictionaries
branch: hjf/fuse-1317-shopify-confirmation-dictionaries
base: origin/main
base_sha: 505584bec
pr: '342'
tags:
- waypoint
- plan
impl_model: sonnet
impl_effort: high
---
# FUSE-1317 — Dictionary lookups and tracking URLs on Shopify goods-out confirmations

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
[FUSE-1317](https://globalfreight.atlassian.net/browse/FUSE-1317), asked for by Jack to manage carrier tracking links for non-Selector customers (see [FUSE-1285](https://globalfreight.atlassian.net/browse/FUSE-1285)). A Shopify goods-out confirmation's carrier rule gets the mapping's dictionaries, so `lookup()` resolves there. A new optional header rule targeting `shipping.carrierTrackingNumberUrl` sends one tracking URL per tracking number as Shopify's `trackingInfo.urls`. Proof: on a dev Shopify store, the fulfilment Shopify stores (read back from the `fulfillmentCreate` response) carries the looked-up company and URL. Purdy & Figg and Saira, whose mappings have no lookups and no URL rule, see byte-identical requests.

Paths below are relative to `apps/shopify-connector/src`. fuse-ui needs no code: its goods-out catalogue already offers `shipping.carrierTrackingNumberUrl` as "Tracking URL", and its `shopifyOut` editor already authors `lookup()` (verified in increment 3).

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [x] 1. A Shopify goods-out confirmation mapping whose carrier rule uses `lookup()` sends the looked-up value to Shopify as the tracking company.
- [x] 2. On a lookup miss with a default, the default is sent.
- [x] 3. On a lookup miss with no default, the field behaves as on the other dictionary flows: the carrier falls back to the despatch's carrier, and the URLs are not sent.
- [x] 4. A mapping with no lookups and no URL rule sends exactly today's `fulfillmentCreate` request, including Saira's shape (header carrier `NETCOURIER`, despatch carrier `Royal Mail`) and Purdy & Figg's.
- [x] 5. A header rule targeting `shipping.carrierTrackingNumberUrl` makes Shopify store one tracking URL per tracking number. No such rule means no URL, as today.
- [x] 6. A person can author the dictionary, the carrier lookup and the URL rule on a Shopify goods-out mapping in the fuse-ui editor, and it round-trips through config-service to the connector.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- `core/confirmations/sales-order-confirmation.handler.ts`: `resolveMappedCarrier` (:331-349) is the only DSL call on the confirmation path; `buildTrackingInfo` (:295-325); the fulfilment-order and line rules read `rule.from` as a plain path (`resolveLineField`), so `lookup()` there never runs and stays out of scope.
- `core/shopify/constants.ts` `ConfirmationMappingFields` (`shipping.carrierId` today); `core/confirmations/types.ts` `TrackingInfo`; `core/confirmations/…/create-fulfillment.mutation.ts` selection; the success log in `shopify-sales-order.service.ts` (`ConfirmationSucceeded`).
- Mapping delivery: routed `getConnectorMapping` (`providers/connector/connector-config.provider.ts:188`) and fan-out `findConnectorMapping` (:167-171), both through remote-config 2.4.0's `ConnectorMappingHandler`, whose schemas (types 10.15.0) keep `dictionaries`. No package bump.
- Shopify Admin API `April26` (`adapters/shopify/api/store.api.ts:78`): `FulfillmentTrackingInput.urls` pairs with `numbers` by position; an unparseable `URL` is a top-level GraphQL error that fails the whole fulfilment.
- `.github/workflows/shopify-connector-manual-deploy.yaml` (notifications backfill), `CLAUDE.md:112`.
- fuse-ui, read only: `goods-out-confirmation-keys.json` (:60 Carrier ID, :63 Tracking URL), `labels.const.ts` `shopifyOut` (expression side `from`), the Dictionaries tab behind `fuse-ui.mapping-dictionaries` (on in dev and prod).

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- Dictionaries already reach the handler on both the routed and the fan-out path; nothing strips them. — grounding review traced both paths and every Zod parse.
- `lookup()`: hit → value; miss with default → default; miss without → `''`, and the rule's field is dropped; unknown dictionary → throws `Unknown dictionary '<name>' in lookup`. `{ dictionaries: undefined }` behaves exactly like today. — rules-engine 2.1.1, installed and pinned.
- `concat(lookup(...), track)` on a miss returns the bare tracking number, not `''`. A URL rule built that way is caught by the URL check, logged as `invalid_url`, and omitted. — grounding review, `interpreter.js` concat.
- One URL per tracking number, evaluated per despatch against `{ ...confirmation, despatches: [despatch] }`, so `despatches[0].carrier.id` and `despatches[0].carrier.track` mean "this parcel". This is the sftp-connector parcel convention (`goods-out-parcels.ts:106`). URLs are sent all-or-nothing, as Shopify documents for an unknown company. Real shipments have one despatch and one number (200 of 200 prod samples), so the multi-parcel branch is a guard, not the common case. — draft, grounding and history reviews, collector sample.
- SNAP fills `shipping.carrierId` from `Shipment.CarrierId`, the booking code (`NETCOURIER` for Saira, `GFS_EVRI` for Purdy & Figg), and `despatches[].carrier.id` from `ShipmentDespatch.Carrier`, the real courier for NetCourier customers (Royal Mail, UPS, DPD Local for Saira). — snap-adapter `goods-out.confirmation-handler.ts:493-571`, 100 prod confirmations each.
- A URL rule that errors (unknown dictionary or similar) omits the URLs and logs `TrackingUrlsOmitted` with `reason: rule_failed`. A URL is additive and must never block a fulfilment. — decided as the default, FUSE-1118 precedent (skip the non-essential part, warn support).
- A carrier rule that errors keeps today's behaviour: a recorded, retryable failure, as ingest does for an unknown dictionary (FUSE-1222). Reclassifying DSL errors is out of scope. — decided as the minimal default; open to Harry below.
- Lookups stay out of the fulfilment-order-id and line rules: the DSL returns strings and the quantity read needs a number. — draft recommendation, taken.
- The routed path is reachable in dev only with a `source=shopify` publish, which the mocker can't stamp. The mocker's broadcast would also reach REST webhooks on partner systems (Purdy & Figg's `onrender` sync, GADG's `fulfil.io`). The e2e therefore publishes with `gcloud pubsub topics publish … --attribute=recordType=goods_out_confirmation,source=shopify` and `metadata.connectorId` set, to one connector, as the E1 plan did on 2026-10-02. That knowingly departs from agents.md's "use the mocker" for this one reason. — history and grounding reviews.
- DECIDED 2026-10-19 (Harry): Saira sending `NETCOURIER` as the carrier is a SNAP config issue, not a Fuse one. Out of scope; Saira's request stays exactly as today (AC 4).
- DECIDED 2026-10-19 (Harry): I create the dev test order myself, through the dev store's own token.
- DECIDED 2026-10-19 (Harry): we take dev. Schuster's branch `sne/fuse-1293-line-item-properties` (f09bef45) is on it now; redeploy it afterwards so dev is as we found it.

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

- [x] 1. Dictionaries in the carrier rule, with a read-back of what Shopify stored (AC 1,2,3,4). First commit the AC4 characterisation specs, green on unmodified main: they pin the exact `FulfillmentInput` for Purdy & Figg's shape (`GFS_EVRI` both sides, `substring` rule) and Saira's (header `NETCOURIER`, despatch `Royal Mail`, identity rule), across several despatches, a repeated tracking number, a tracked despatch with no carrier id, and a despatch with no tracking number. Then pass `{ dictionaries: mappings.dictionaries }` in `resolveMappedCarrier` through a small `evaluateHeaderRule` helper that increment 2 reuses. Add `trackingInfo { company number url }` to the `fulfillmentCreate` selection, carry it on the result, and log `company` and whether URLs were sent on the success event. Backfill `notify_on_success`, `notify_on_failure` and `slack_webhook` on the manual-deploy workflow. — verify: the new spec block (lookup hit → company; miss with default; miss without → despatch carrier; case-insensitive dictionary; unknown dictionary → failure as today); `connector-config.service.spec` "carries the goods-out mapping's dictionaries" for both the routed and fan-out methods; the characterisation file unchanged by the feature commit; `pnpm test`, `pnpm lint:fix`, `pnpm build:check` in `apps/shopify-connector`. — characterisation specs green on main (825590c5) and unchanged; carrier lookup specs; provider passthrough specs; 807 tests, build:check, lint — done: dce4f48b
- [x] 2. Mapping-driven tracking URLs (AC 1,2,3,5, AC 4 kept). Add `ConfirmationMappingFields.TRACKING_URL = "shipping.carrierTrackingNumberUrl"` and `TrackingInfo.urls?`. Write the URL logic as a pure function beside `buildTrackingInfo`, because the programme's SPLIT-CONFIRM unit plans to lift tracking into a pure mapper. No URL rule → no `urls` key at all. Otherwise evaluate the rule once per distinct tracking number, against that number's first despatch, with dictionaries. Accept only `http:`/`https:` values that `URL.canParse` accepts, and send `new URL(v).href`. Send `urls` only when every number has one; otherwise omit `urls`, still send numbers and company, and log `TrackingUrlsOmitted` (warn, audience support, `reason: unresolved | invalid_url | rule_failed`, counts). Update `CLAUDE.md:112`. — verify: the characterisation file has a zero-line diff; specs: no rule → `not.toHaveProperty('urls')`; single despatch hit; per-number URLs for two carriers; repeated number → one URL; untracked despatch doesn't shift alignment; default on miss; bare-lookup miss → omitted `unresolved`; concat miss → omitted `invalid_url`; one unresolved → all omitted; non-http rejected; unknown dictionary → fulfils without URLs, `rule_failed`; same `urls` on every fulfilment-order group. Same commands as 1. — 13 tracking-URL specs; characterisation file zero-line diff since 825590c5; 820 tests, build:check, lint — done: 4cf25f88
- [x] 3. Verification in dev and the prod soak (AC 1,2,3,4,5,6). Preflight: whose branch is on dev (Schuster's today), dev store token liveness (`Shop token upserted` by `@shop`), the flag state. Target the ILG-owned GADG "ILG Test Store" (`conn_c7e4fd39…`, `quickstart-501d0f59`). Snapshot its goods-out mapping with `config-read` and keep the copy. In the editor, add a `carrier_urls` dictionary, a carrier `lookup()` rule and a `shipping.carrierTrackingNumberUrl` rule; Test Mapping dry-runs it unsaved (first screenshot); save, and confirm the `config_revision` was processed in Datadog. Publish routed goods-out confirmations with `source=shopify` against one paid, unfulfilled, `ILG_RELEASED` dev order with 4-5 lines, one line per send: baseline (untouched mapping, run first), carrier and URL hit, miss with default, miss without default. Use a carrier Shopify doesn't know and a made-up host (`https://fuse-1317.example/track/…`), so the read-back proves the URL came from us. Restore the mapping from the snapshot in one write, and compare a fresh GET with it. Redeploy dev to whatever was there before. After each prod deploy, soak Purdy & Figg and Saira: `ConfirmationSucceeded` rate unchanged, zero `TrackingUrlsOmitted`, zero `Unknown dictionary`. — verify: screenshots, the logged read-back of `trackingInfo` per send, `mock-activity` or Datadog `confirmation_made`, and the soak queries. — dev e2e base/hit/def/miss read back from Shopify; AC6 authored in fuse-ui; prod 0fefcb40 PURDYFIGG 225 successes, 0 warn/error/omitted/unknown-dictionary; Saira soak moved to inc 4 — done: 4cf25f88
      gate: a dev Shopify order exists for the e2e (Harry approved me creating it, and taking dev)
            [x] confirmed
- [ ] 4. Saira's prod soak (AC 4). Saira had no confirmations in increment 3's window. When it next confirms on `0fefcb40` or later, check: `Confirmation dispatched successfully` with `trackingInfo.company: NETCOURIER` and no `url` we sent, and zero `Tracking URLs omitted` and `Unknown dictionary`. — verify: Datadog `service:shopify-connector @environment:prod @businessId:SAIRA @flow:confirmation` from 2026-10-19T14:01:44Z.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-19 [inc 3] **Prod soak, Purdy & Figg (AC 4).** Prod moved to `0fefcb40` (revision 00058) at 14:01:44 UTC, after I read the plan (image bump plus standing drift) and approved the gate. Over the next ~45 min PURDYFIGG logged 186 `Confirmation dispatched successfully` on the new version, against a baseline of 100–150 an hour. The flow logged zero warn or error lines, zero `Tracking URLs omitted` and zero `Unknown dictionary`. The read-back shows `company: EVRI` as before; the stored URL is Shopify's own Evri link. **Saira had no confirmations in the window**, so its prod soak is still owed (it is pinned in specs and was checked on dev).
- 2026-10-19 [inc 3] **Dev restored.** The ILG Test Store goods-out mapping was PUT back from `ilg-test-store-goods-out-snapshot.json`. A fresh GET matches the snapshot except that `dictionaries` reads `[]` where the snapshot had no key, which behaves identically (an empty lookup). Dev `shopify-connector` was redeployed from Schuster's `sne/fuse-1293-line-item-properties` (head unchanged at f09bef45), run 39262833347. The merge's own Deploy run then applied `main` to dev (revision 00564), so his branch was redeployed again: run 39265351233, revision 00565, `dev-f09bef45`.
- 2026-10-19 [inc 3] **AC 3 and 5 (miss with no default).** The rules were rewritten without their defaults and sent with despatch carrier `MYSTERY` (`fuse-1317-miss`, 13:42 UTC). The connector logged `Tracking URLs omitted…` with `reason: invalid_url`, `resolved: 0`, `total: 1` and `audience: support`, because the bare-`concat` miss yields the tracking number alone. Shopify stored `{company: MYSTERY, number: FUSE1317-MISS, url: null}` (Fulfillment/7294737449245), so the carrier fell back to the despatch's raw carrier and the fulfilment still succeeded.
- 2026-10-19 [inc 3] **AC 2 (miss with default).** With despatch carrier `MYSTERY` (`fuse-1317-def`, 13:40 UTC), Shopify stored `{company: "Fuse Other Courier", number: FUSE1317-DEF, url: "https://fuse-1317.example/track/other?ref=FUSE1317-DEF"}` (Fulfillment/7294733517085). Both defaults reached Shopify.
- 2026-10-19 [inc 3] **AC 1 and 5 (hit).** With despatch carrier `NETCOURIER` (`fuse-1317-hit`, 13:40 UTC), Shopify stored `{company: "Fuse Test Courier", number: FUSE1317-HIT, url: "https://fuse-1317.example/track/nc?ref=FUSE1317-HIT"}` (Fulfillment/7294733353245). The made-up host proves the URL came from our dictionary, not from Shopify's carrier list.
- 2026-10-19 [inc 3] **AC 4 dev baseline.** The untouched snapshot mapping was sent first (`fuse-1317-base`, 13:32 UTC), with header carrier `NETCOURIER`. Shopify stored `{company: NETCOURIER, number: FUSE1317-BASE, url: null}` (Fulfillment/7294713692445), as before the change.
- 2026-10-19 [inc 3] **How the e2e ran.** Each scenario was one routed publish to `bifrost.dev.confirmation_ready.v1` with attributes `recordType=goods_out_confirmation,source=shopify` and `metadata.connectorId=conn_c7e4fd39af9442a1a9e6d3229d933fad`, one line of dev order #11452 (`gid://shopify/Order/18957531578653`, fulfilment order 22173554442525) per send. All sends ran on dev version `4cf25f88`, and each logged `Confirmation dispatched successfully` with the Shopify read-back `trackingInfo`, `Record published to topic` (`confirmation_made`) and `202 Accepted`. The stored values were also read back directly over Shopify GraphQL (`q-fulfillments.graphql`), and they match the logs.
- 2026-10-19 [inc 3] **AC 6.** A local fuse-ui (origin/main 6f0d67f) against dev config-service authored both dictionaries (`carrier_names` NETCOURIER→Fuse Test Courier; `carrier_urls` NETCOURIER→`https://fuse-1317.example/track/nc?ref=`), the carrier rule `lookup('carrier_names', despatches[0].carrier.id, 'Fuse Other Courier')`, and the URL rule `concat(lookup('carrier_urls', despatches[0].carrier.id, 'https://fuse-1317.example/track/other?ref='), despatches[0].carrier.track)` → Tracking URL, built in the structured expression builder. Saved; `config-read` returned the rules and dictionaries; the connector logged `Config revision received` at 13:39:50 UTC. Screenshots `shots/1317-rules-authored.png`, `1317-rule-url.png`, `1317-rule-carrier.png`.
- 2026-10-19 [inc 1-2] The characterisation spec (825590c5) was green on unmodified main and has a zero-line diff through 4cf25f88. 820 tests in 56 suites pass, plus `build:check` and `lint` in `apps/shopify-connector`.

### Not verified
- **The prod soak (AC 4 in prod).** Pending until the merge. It is the `ConfirmationSucceeded` rate for Purdy & Figg and Saira against the pre-deploy rate, zero `TrackingUrlsOmitted` and zero `Unknown dictionary`.
- **The fan-out path end to end.** Only the routed path ran in dev, because a broadcast would fire partner REST webhooks. The fan-out mapping passthrough is covered by the `getGoodsOutConfirmationStates` provider spec only.
- **Multi-parcel URLs against real Shopify.** Every dev send had one tracking number. Positional pairing across several numbers is proven in specs only (200 of 200 prod samples have one number).
- **The `rule_failed` path against real Shopify** (an unknown dictionary on the URL rule). Specs only.
- **Test Mapping dry-run of the authored rules.** Not captured; the real sends prove the same evaluation.

## Rollout & rollback
<!-- Added on demand. Written at plan time; amend in place as it changes.
     `Shared state touched:` is the single home for the five classes git does not own — a dev
     deploy, a prod config write, a Datadog monitor, a CI var or secret, cross-repo IaC. Reverting
     the branch undoes none of them, so if they are not written here they are not written down. -->

- **Order:** 1 → 2 → 3. Increment 1 can go to prod alone and is inert for both live customers. Increment 2 is inert without a URL rule.
- **Flags/config:** none added. The fuse-ui `fuse-ui.mapping-dictionaries` flag is already on in prod, so a `lookup()` can be authored on a prod carrier rule today and throws. **Guard:** no `lookup()` on a prod Shopify carrier rule until increment 1 is in prod; a prod URL rule does nothing until increment 2 is.
- **One-way doors:** none in code. A real customer URL rule puts links on the shopper's order status page, which is customer-facing. That is support/TSE config after release and out of scope here; it needs the carrier URL templates (FUSE-1285) first.
- **Rollback:** per increment `git revert`.
- **Shared state touched:** the dev `shopify-connector` deploy (Schuster's branch is on it; put it back afterwards); the GADG ILG Test Store goods-out mapping in dev config-service (snapshot, restore in one write); a test order in the `quickstart-501d0f59` dev store and its ingested sales order in GADG's dev SNAP, which stay; routed publishes to `bifrost.dev.confirmation_ready.v1`. No prod config writes.
- **Proof in prod:** the AC4 soak per deploy, against the pre-deploy `ConfirmationSucceeded` rate for both connectors, and zero `TrackingUrlsOmitted` and `Unknown dictionary`. The feature itself is only proven in dev until a customer configures it.

## Handback
<!-- Append-only, newest first. Written by `wp handback`, never by hand.
     Sign-off never clears this section — a refuted approach is exactly what a
     later session needs and what ## Learnings would have deleted. -->

### 2026-10-19 15:52
- **stopped:** Merged (#341, #342) and live in prod on 0fefcb40 since 2026-10-19 14:01:44 UTC; PURDYFIGG soak clean (225 successes, 0 warn/error). Waiting on SAIRA's first prod confirmation on 0fefcb40 or later (increment 4; Saira is bursty, the last batch was 13:00 UTC). Then: tick 4, wp signoff, set-status complete, wp index, git worktree remove this worktree and delete the local branch. Jira is already Ready for QA; the evidence branch is deleted.
- **turn:** world

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-19** — Learnings promoted at sign-off: known-context.md #fuse-1317 (SNAP carrier fields, Shopify auto-links known carriers, concat-miss, routed dev publish, config-service PUT keeps dictionaries, order-tag schema bug snapshot), architecture.md **Tracking.**, operations.md success-line trackingInfo. Increment 4 (Saira prod soak) added because Saira had no confirmations in the soak window.

- **2026-10-19** — Shipped as a two-PR native stack (#343) to stay near the size target: #341 = characterisation spec + carrier dictionaries (hjf/fuse-1317-carrier-dictionaries at dce4f48b, 512 lines), #342 = tracking URLs (this plan's branch, 364 lines). pr: records #342 because it is the plan's branch; #341 merges first.

- **2026-10-19** — Restoring the dev mapping needed an explicit dictionaries: [] — a PUT that omitted the key left the dictionaries in place. Final state has dictionaries: [] where the snapshot had none; equivalent at runtime.

- **2026-10-19** — The success log now carries the trackingInfo Shopify stored (company, number, url), read back from the fulfillmentCreate response. Tracking numbers are shopper-facing but not PII on their own, and support had no way to see what was sent.

- **2026-10-19** — Took dev from Schuster's sne/fuse-1293-line-item-properties (f09bef45) with Harry's say-so, and redeployed it afterwards (run 39262833347).

- **2026-10-19** — Created dev order #11452 in the quickstart-501d0f59 store through its own ShopToken (read from dev Mongo, never printed), with Harry's approval for this test only. The order and its ingested GADG dev SNAP sales order stay.

- **2026-10-19** — The dev e2e used routed gcloud publishes (source=shopify, one connectorId) instead of fuse-mocker: the mocker can't stamp source=shopify, and its broadcast would fire GADG's fulfil.io REST webhook. Departs from agents.md's mocker rule for that reason only.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
(none)
