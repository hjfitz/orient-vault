---
ticket: none
title: Clear routed OBQ rows after publish
service: snap-queue-polling-service
status: complete
created: '2026-10-02'
updated: '2026-10-05'
repo: /home/hjf/code/fuse/snap-adapter
worktree: /home/hjf/code/fuse/snap-adapter/.claude/worktrees/c2-clear-after-publish
branch: hjf/c2-clear-after-publish
base: origin/master
base_sha: 7c436f96e
pr: '279'
tags:
- waypoint
- plan
programme: poller-clear-down
unit: C2
impl_model: opus
impl_effort: high
---
# none — Clear routed OBQ rows after publish

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
Part of [[Poller Clear-Down/Migration State|Poller Clear-Down]] unit **C2** (no ticket), rescoped 2026-10-02. Once
the poller's publish to `confirmation_ready` resolves, it clears that group's rows off SNAP's outbound queue
(`PATCH /v2/snapoutbound/{id}/processed`). This only applies when the group is routed to one connector whose
channel subscribes to its type, and only for allow-listed businesses. Publish is the handoff: A1–A3 and E1/E5 make
every consumer end a routed confirmation in `confirmation_made` or a stored, redrivable failure. Everything else
stays on the queue for snap-adapter's clear-down, as today. That covers broadcast, unrouted, no-subscription
channel, rows with no queueId, and `stock_adjustment`. It ships dark in prod, live in dev for HJF, and D1 widens it
per business.

## Acceptance criteria
- [x] 1. For an allow-listed business, every published row of a group routed to a connector whose channel subscribes to its type is PATCHed processed after the publish resolves, and metered `snap.outbound.cleared{type,businessid}`.
- [x] 2. Broadcast, unrouted, no-subscription, `stock_adjustment` and no-queueId rows stay on the queue, metered `snap.outbound.clear_skipped{reason}`.
- [x] 3. A business off the allow-list behaves exactly as today: no PATCH and no `snap.outbound.clear*` metrics.
- [x] 4. A clear that SNAP doesn't confirm leaves the row on the queue, meters `snap.outbound.clear_failed{reason}`, logs `OutboundClearEvent.Failed`, and never fails the poll. "Not confirmed" covers: 2xx `Status:"Error"`, empty `Results`, a body that isn't an envelope, a request failure, or an open breaker. An open breaker also stops the rest of the group's PATCHes.
- [x] 5. A publish that rejects clears nothing. A later group's failure doesn't undo an earlier group's clear.
- [x] 6. The allow-list and clear concurrency are set in Terraform: dev `["HJF"]`, prod `[]`, concurrency 3. A malformed entry fails startup, so nothing is silently enabled.
- [x] 7. Dev e2e on HJF: each routed REST type (pick, pack, goods-out) is cleared within one poll, and every cleared row ends in `confirmation_made` or a replay failure for its connector.
- [x] 8. `ConfirmationDisposer` drop paths stop logging a false `RecordDropped` when SNAP answers 2xx `Status:"Error"`.

## Affected boundaries
Paths below are under `apps/snap-queue-polling-service/src` unless they start with `iac/`.
- `adapters/snap/api.client.ts:186-190`: `clearFromOutboundQueue` goes through `request()` (widened to PATCH, `:74-92`). The shared callers are `ConfirmationDisposer` (`core/snap/confirmations/confirmation.disposer.ts:12-19`, which swallows errors). It is reached from goods-in zero-qty (`goods-in.confirmation-handler.ts:106`), goods-out cancelled (`:101`) and partial order (`:226-246`).
- `exceptions/api-client.exception.ts`: `NotCleared`, plus a discriminator so a request failure can be told apart from an open circuit. Both are currently the same class, distinguished only by `cause`.
- `shared/promise.ts`: new `mapWithConcurrency`. `chunkPromises` is untouched; it is still used at `queue-lane.ts:49,115` and `goods-in.confirmation-handler.ts:116`.
- New `core/snap/confirmations/outbound-queue.clearer.ts` and `confirmation-subscriptions.ts`. `ROUTING_AWARE_TYPES` is exported from `confirmation-failure.ts:36-44`.
- `core/snap/confirmations/confirmations.service.ts`: constructor (`:50-57`), and `announceConfirmations(groups, snapClients)` (`:271`), with the clear inside the `Correlation.childScope` after `emit` (`:311-334`). Also `types.ts:115-127`, the callers `core/polling/polling.service.ts:88` and `http/controllers/debug.controller.ts:62`, and the wiring in `bootstrap/factory/controller.factory.ts:94-110`.
- `observability/catalog/snap-polling.type.ts:56-59` gets `OUTBOUND_CLEARED`, `OUTBOUND_CLEAR_FAILED` and `OUTBOUND_CLEAR_SKIPPED`. New `observability/events/outbound-clear.type.ts`.
- Config: `config/config.schemas.ts:80-87`, `config/parse.ts`, new `config/business-id-list.ts`, `.env.sample`.
- Terraform: `iac/projects/snap-queue-polling-service/variables.tf:1-3` locals, and `cloud-run.tf` env after `CUSTOMER_CHUNK_SIZE` (`:184-187`).
- fuse-mocker (direct to main): `apps/snap-api/internal/http/snapwire/reads.go:155-172`. `markProcessed` will fire armed faults.
- Contracts: no topic, envelope, canonical type or endpoint changes, so no Fuse MCP data file and no types bump. The consumer subscription filters this relies on are read-only references: fapi `api-gateway/pubsub.tf:155,195,262,305,348,388,432`, shopify `pubsub.tf:323`, sftp `channel_filter` (`pubsub.tf:16`, RGA `:227`), all on `each origin trunk`.

## Assumptions & uncertainty
- **Channel is enforced at Pub/Sub, not in consumer code.** Every `confirmation_ready` subscription filters `recordType AND (source=CHANNEL OR broadcast="true")`. fapi and sftp take all 7 routing-aware types; shopify takes goods-out only. So a routed row on a channel that doesn't subscribe to its type reaches nobody, and must be skipped (R6). Established by reading `each origin trunk` for fapi, shopify and sftp (fapi#134/#137/#159, FUSE-1057, sftp#296). The draft's contrary claim came from stale local main checkouts.
- **A second PATCH on a processed row returns `Success` with the row in `Results`.** So the rollout-period double clear (poller first, then snap-adapter on `confirmation_made`) meters as `cleared` and logs nothing. Established by G2 on real SNAP: `Findings/snap-outbound-processed-patch.md`.
- **Stage-2 runs in a 300 s window.** Cloud Run `timeoutSeconds=300` on dev and prod; the 600 s ack deadline doesn't bind. Established by live `gcloud run services describe`, 2026-10-02. A timed-out invocation leaves rows published but uncleared, which only risks a duplicate (snap-adapter still clears them on made), never a loss.
- **SNAP is comfortable at about 10–20 concurrent requests fleet-wide and collapses past 50–60.** snap-adapter caps itself at Semaphore(5) and 10 rps per host, and ilg005 is already saturated. Established from snap-adapter `known-context.md`, MS L117 and the PURDYFIGG notes. Hence clear concurrency is 3, not 10. 1000 rows take about 100 s at 3, and realistic routed groups are tens of rows. It is a Terraform knob so it can be choked during an incident with one apply (the FUSE-1078 lesson).
- **Publish is the handoff.** SNAP no longer backs up a failed routed delivery; consumer retry (E5) plus replay does. This is a settled decision (MS 2026-09-29 and the 2026-10-02 rescope), not reopened here. D1's soak reconciliation (published = made + replay failures) is the detector.
- **Residual: E3.** A bulk push with one invalid record is acked and dropped whole by fapi and shopify. Under C2 that becomes a real loss rather than a re-announce. It stays deferred and is named in PR C's risks. The D1 reconciliation and `errors.pubsub_decode` would catch it. Established from MS L90.
- **Hardening the clear changes only logs on the disposer paths, not row behaviour,** because the disposer swallows every error. `Results` is parsed as a non-empty `z.unknown()` array, not a strict row schema, because the snap 0.3.0 history shows strict row schemas break on real nulls. Established by source read.
- **`unavailable` (Redis fail-open) rows are cleared, because they were published.** At worst that is a duplicate, the INC-30 class and the same as today, never a loss. `duplicate` claim rows weren't published this cycle, so they aren't cleared. Established by source read of `claimConfirmations` (`confirmations.service.ts:364-426`).
- **`/debug/trigger` clears too.** It is behind `authMiddleware` and runs the same announce path, and the allow-list gates it in the clearer. Established by source read.
- **Decided 2026-10-02 (Harry): yes.** Merge the dev allow-list as `["HJF"]`. HJF is a simulator business, so prod stays dark. Dev keeps C2 live after merge (no soak is planned; HJF is our simulator), and the e2e goes through Terraform rather than an out-of-band `gcloud run services update`, which the classifier blocked for FUSE-1147 and the next apply wipes.
- **Decided 2026-10-02 (Harry): yes.** Accept E3 as a named residual for D1 rather than building for it in C2.

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

**PR A, off `origin/master`: harden the clear (~200 lines).**

- [x] 1. Route `clearFromOutboundQueue` through `request("PATCH")` (AC 8, 4). — done: 97a7880
      - Make `Status:"Error"` throw `RequestFailure`, an empty or non-array `Results` (parsed as `z.unknown()`) throw a new `ApiClientException.NotCleared`, and a non-envelope body throw `ValidationException` with its own reason.
      - Add a discriminator (e.g. `ApiClientException.isRequestFailure`) so open-circuit and request-failure aren't told apart only by `cause`.
      - Unit tests in `adapters/snap/__test__/api.client.spec.ts`, one each: sends PATCH to the processed route; resolves on Success with the row; rejects on 2xx Status Error; rejects on empty Results; rejects a non-envelope body; short-circuits when the host breaker is open.
      - Verify: `pnpm test`, `lint:fix`, `build:check`, `build:check:tests`. Then a dev branch deploy: cancel an HJF shipment (`POST /api/v1/businesses/HJF/shipments/{id}/cancel`); the disposer's cleared row logs `RecordDropped` against the simulator's real body, and the row shows `processed`.
      gate: dev branch deploy announced in #bifrost-general, and dev back on master afterwards
            [x] confirmed

**PR B, stacked on A: pool, subscription table, clearer and observability, not wired (~650–700 lines, unit only).**

- [x] 2. `mapWithConcurrency(items, limit, fn)` in `shared/promise.ts`, a real worker pool. `chunkPromises` is untouched. Tests in new `shared/__test__/promise.spec.ts`: never runs more than the limit at once; returns results in input order; settles every item when one rejects (AC 4) — verify: `pnpm test`. — done: c173b6e
- [x] 3. `confirmation-subscriptions.ts`, `outbound-queue.clearer.ts` (`IOutboundQueueClearer.clearPublished(group, published, snapClient)`, which never rejects), the three metrics and `OutboundClearEvent.Failed` (AC 1, 2, 3, 4). — done: fd9d02b
      - Skip order:
        1. off allow-list (silent)
        2. `stock_adjustment`
        3. broadcast
        4. unrouted (no `routing.connectorId`)
        5. `no_subscription` (looked up with `Object.hasOwn`)
        6. `no_queue_id` (per row)
      - queueIds are de-duplicated before any PATCH. An open breaker stops the group, meters the remaining rows `circuit_open` and logs once with a count. A missing client meters `no_client`.
      - Subscription tests, one each: rest and sftp take every routing-aware type; shopify takes goods-out only; an unknown source takes nothing; no channel takes `stock_adjustment`.
      - Clearer tests:
        - Off allow-list: no clear; no metrics.
        - Clears every published row of a routed rest group.
        - Skips:
          - broadcast as `broadcast`
          - no connectorId as `unrouted`
          - routed shopify pick as `no_subscription`
          - unknown source as `no_subscription`
          - `stock_adjustment` as `stock_adjustment`
          - a row without queueId as `no_queue_id`
        - Clears that row's queued siblings.
        - Meters:
          - cleared, with type and businessId
          - Status Error as `snap_error`
          - empty Results as `not_cleared`
        - One failure event per failed row.
        - Keeps clearing after one row fails.
        - Stops at an open breaker.
        - Never rejects when every clear fails.
        - Clears a repeated queueId once.
      - Verify: `pnpm test`, `lint:fix`, `build:check`, `build:check:tests`.

**PR C, stacked on B: config, Terraform, wiring, e2e.**

- [x] 4. `CLEAR_AFTER_PUBLISH_BUSINESS_IDS` and `CLEAR_AFTER_PUBLISH_CONCURRENCY` (AC 3, 6). — done: d74e174
      - Config:
        - Schema plus a `config/business-id-list.ts` parser: trim, drop empties, de-duplicate, each entry `/^[A-Za-z0-9_-]+$/`, default `[]`.
        - Concurrency is an int ≥ 1, default 3.
        - `parse.ts` exposes `confirmations.clearAfterPublish`; `.env.sample` documents both.
      - Terraform:
        - locals `clear_after_publish_business_ids = var.env == "dev" ? ["HJF"] : []` and `clear_after_publish_concurrency = 3`.
        - Two `env` blocks in `cloud-run.tf` after `CUSTOMER_CHUNK_SIZE`.
      - Tests in `config/__test__/business-id-list.spec.ts`, one each: unset → empty; empty string → empty; splits and trims; drops stray-comma empties; de-duplicates; rejects a bad character. Plus: concurrency defaults to 3; rejects concurrency below 1.
      - Verify: unit tests. The CI Terraform plan (dev) shows only the two new env vars, `HJF` and `3`.
- [x] 5. Inject the clearer as `ConfirmationsService`'s 5th argument. `announceConfirmations(groups, snapClients: ISnapAPI[])` builds a businessId → client map and calls `clearPublished` inside the group's `childScope` straight after `emit` resolves (AC 1, 5). — done: 4a89c09
      - Update `types.ts`, `polling.service.ts:88`, `debug.controller.ts:62`, `controller.factory.ts:94-110` and the fixtures (`__fixtures__/confirmation.service.fixture.ts:43-48`, `polling.service.spec.ts:26-34`).
      - Tests in `confirmations.service.spec.ts`, one each:
        - Clears after the publish resolves (emit before clear).
        - Nothing cleared when the publish rejects.
        - Duplicate-claim rows aren't cleared.
        - Unavailable-claim rows are cleared.
        - An earlier group stays cleared when a later group throws.
        - A withheld group is never cleared.
        - Uses the group business's client.
        - Leaves rows when that business has no client.
      - Polling spec: hands the chunk's clients to the announce.
      - Verify: `pnpm test`, `lint:fix`, `build:check`, `build:check:tests`.
- [x] 6. fuse-mocker, direct to main: `markProcessed` fires faults armed on the outbound entity, the same way the other snapwire routes call `fireFault` (AC 4, 7). — done: 0b4f75d (fuse-mocker)
      - Verify: arm a fault, PATCH a row through `/api/v2/snapoutbound/{id}/processed`; the fault's status comes back. Disarm; the next PATCH succeeds.
      - It exists so the D1 `clear_failed` monitor isn't written against a metric that has never fired.
- [x] 7. Dev e2e on HJF: branch deploy of PR C, with HJF enabled through Terraform (AC 1–5, 7). Also D1's pre-prod pass. — done: 4a89c09
      - Before each case, check the log `version` sha is the branch head.
      - Before starting, clear HJF's stale rows `HJFE001C40661D3` and `HJF1D587E7F7993` row by row (`/queue/{xdoc}/clear`, never `/queue/clear`).
      - Case 0, passive: during the window, `snap.outbound.{cleared,clear_failed,clear_skipped}` carry only `businessid:hjf` (AC 3).
      - Case 1: one REST order through fapi ingress on connector `conn_1a5c…`, advanced 29 → 39 → 90.
        - At each stage the XDoc is `processed` within one poll (cron every 2 minutes), with `snap.outbound.cleared{type}` for pick, pack and goods-out.
        - Invariant: each cleared row ends in `confirmation_made` or a fapi failure in replay for `conn_1a5c…` (example.com webhook).
      - Case 2: record the order's routing doc (`fuse-wms-routing` `routing-metadata/HJF__{ShipmentId}`), merge `routing.source="shopify"` with `updateMask`, advance a second order to 29. Expect `clear_skipped{reason:no_subscription}` and the row still `pending`. Restore the doc.
      - Case 3: the same with `routing.source="mock"`. Expect `no_subscription`; restore.
      - Case 4: create a shipment over the SNAP wire (`/api/v2/shipments`, no routing doc) and advance it. Expect the broadcast publish, a skip with reason `broadcast`, and the row left. (`unrouted` is the defensive reason for a non-broadcast group with no connectorId; it is unit-tested.)
      - Case 5, after inc 6: arm a fault on the outbound entity, advance a routed REST order. Expect `clear_failed{reason}`, `OutboundClearEvent.Failed`, the row still `pending`. Disarm; after the 10-minute claim TTL the row re-announces and clears.
      - Case 6, withheld: set HJF's REST connector `confirmationsEnabled: false` and advance a routed order. Nothing is published or cleared, and the row stays `pending`. Restore the flag.
      - Case 7, repeat PATCH: after case 1's poller clear, snap-adapter's made clear-down PATCHes the same row again. It logs no `Confirmation clear-down failed`. That is G2 on the simulator; BYOMA's first prod cycles are the real-SNAP check.
      - Cases 4 and 6 are D1's pre-prod pass (G6 retired 2026-10-02). They prove C2 never clears a row Fuse didn't publish routed.
      gate: dev branch deploy and HJF enablement announced in #bifrost-general
            [x] confirmed
      gate: dev cleanup done. Test rows cleared row by row, routing docs and the REST connector's `confirmationsEnabled` restored, dev back on master until merge, faults disarmed, test replay failures listed in Evidence
            [x] confirmed
- [x] 8. Merge the A → B → C stack, then the prod release dark (AC 6). — done: bf29b0b
      - Verify: `snap-polling-service-prod` revision env shows `CLEAR_AFTER_PUBLISH_BUSINESS_IDS=""` and concurrency `3`, and the revision started cleanly. No `snap.outbound.clear*` in prod. Dev keeps HJF live.
      gate: prod Terraform plan shared and agreed, and `git log prod..RUN_SHA` reviewed, before the `terraform-prod` approval
            [x] confirmed

### Delivery
- Three PRs, linked as a native GitHub stack (`gh stack link` from the worktree, no `--open`, no diagram in the bodies).
- Each PR gets an out-of-ticket `wp ledger snap-queue-polling-service` entry when it opens, with the body ending `PR: gfs-bifrost/snap-adapter#N`. The second and third need `--force`.
- PR C's risk section names: the E3 residual; the rollout-period double PATCH on shared SNAP hosts (watch `snap.circuit_breaker.state` per host, since co-tenants share it); and that disposer-path logs change in PR A.
- The fuse-mocker change in inc 6 is a direct-to-main commit, so it gets no ledger entry (no PR). It is recorded in Evidence.

### Handed to D1 (not C2's to do)
- **G6 is retired (2026-10-02, see Migration State).** C2 clears only routed rows it has published, so a business with no confirmations-enabled connector has nothing cleared. The named skip tests (`broadcast`, `unrouted`, "a withheld group is never cleared") and e2e cases 4 and 6 carry that protection. Keep them if the plan changes.
- **D1 order:** BYOMA, WILDSMITH, EPARFUM, SPORTLUX, DOCKBAY, STUBBLE, then SAIRA and PURDYFIGG after C1. There is no HJF soak; inc 7 is the pre-prod pass.
- **The `snap.outbound.clear_failed` monitor: done 2026-10-02.** observability#60, applied `d4953f6` behind `terraform-prod` after Harry agreed the plan (2 to add). Prod monitor `327518496` warns at 3 and alerts at 10 per business in 30 minutes; dev copy `327518495` notifies nobody. Still owed: the firing proof (OK → Alert → OK on the dev copy) once #279 is in dev.
- **STUBBLE.** 157 prod routing docs carry `source="snap-adapter"` (snap-adapter #253 era) and will skip as `no_subscription`. That is safe, they keep looping as today, but it is noisy. Check whether the data repair ran before STUBBLE's turn.
- **Rollback** is a local edit, a PR and the `terraform-prod` gate. Break-glass: `gcloud run services update … --update-env-vars CLEAR_AFTER_PUBLISH_BUSINESS_IDS=` on prod, with Terraform updated after.
- **Per business, watch:**
  - cleared vs `fuse.confirmation.published`
  - `clear_failed` ≈ 0
  - stage-2 under 300 s with no 504s
  - claim duplicates and downstream duplicates flat
  - breaker state per host

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-10-05 [inc 8] **Prod, dark.** Harry approved after the plan and range were shared: run 37296611988 through `terraform-prod`. `snap-polling-service-prod` is on `bf29b0b`, Ready, with `CLEAR_AFTER_PUBLISH_BUSINESS_IDS` empty and `CLEAR_AFTER_PUBLISH_CONCURRENCY=3`. In the 15 minutes after: no prod error logs, 57 `fuse.confirmation.published`, and zero `snap.outbound.cleared` / `clear_failed` (nothing allow-listed). AC 6.
- 2026-10-05 [inc 8 + monitor] **Merged and firing-proven in dev.**
  - **Merge:** Schuster approved #277, #278 and #279. The native stack #280 was merged atomically (squash) at `bf29b0b`.
  - **Dev:** the Deploy run 37296611988 dev apply put `snap-polling-service-dev` on `dev-bf29b0b` with `CLEAR_AFTER_PUBLISH_BUSINESS_IDS=HJF` and `CLEAR_AFTER_PUBLISH_CONCURRENCY=3`.
  - **Firing proof** for monitor `327518495` (dev copy):
    - Two routed REST orders for HJF via fapi (`HJF193810AECC1D`, `HJF71DCAD414354`) were advanced to picked and packed, giving 4 rows.
    - A persistent `status_error` fault on `snapoutbound` (`HJF479D669A9308`) failed every clear with `reason: snap_error` (`Outbound queue clear failed` at 10:32:07Z).
    - Failures came in rounds of 4 every 12 minutes, the 10-minute claim TTL plus the 2-minute poll: 10:32, 10:44 and 10:56Z.
    - The monitor went OK → Warn at 10:34:26Z (more than 3) and Warn → Alert at 10:57:47Z (12 in 30 minutes, over 10).
    - Fault removed at 10:58:02Z. The next re-announce cleared all 4 rows at 11:08:07Z, so nothing was lost.
    - The monitor stepped down to Warn at 11:03:48Z as the first round aged out, and returned to OK at 11:27:38Z once the last round aged out. Full OK → Warn → Alert → Warn → OK cycle proven.
  - **Prod:** the release is parked at `terraform-prod` (run 37296611988). The plan is 1 in-place change: adds `CLEAR_AFTER_PUBLISH_BUSINESS_IDS=""` and `CLEAR_AFTER_PUBLISH_CONCURRENCY=3`, plus the image. Beyond C2 it ships only #274 (types `^10.9.0`) and a CLAUDE.md edit from #275.
- 2026-10-02 [inc 7] **Dev e2e on HJF**, branch `4a89c09` (manual deploy run 37017974118, announced in #bifrost-general; revision env `CLEAR_AFTER_PUBLISH_BUSINESS_IDS=HJF`, `CLEAR_AFTER_PUBLISH_CONCURRENCY=3` from Terraform; dev back on master `7c436f9` via run 37022505726, env gone). Orders went in through fapi REST as HJF (`submit-to-fuse`), so snap-adapter wrote real `rest` routing docs on `conn_1a5c…`.
  - **Case 1 (AC 1, 7).** `HJFD6980F1C47C9` was advanced picked → packed → despatched. Each row was `processed` within one poll:
    - pick `HJFA09CC500C6E6`, 14:18:08Z
    - pack `HJF3C20776C82E5`, 14:20:07Z
    - goods-out `HJF7E826A4C4837`, 14:22:07Z
    - `snap.outbound.cleared{businessid:hjf}` = 1 each for pick, pack and goods-out.
    - fapi failed 3× against example.com and acked, so there was no `confirmation_made` and the poller did the clear.
    - Invariant: replay holds one redrivable failure per cleared row on `conn_1a5c…`: `8bf86704` (pick), `d897e9ce` (pack), `0c84efa5` (goods-out).
  - **Case 2 (AC 2).** On `HJF37621F0AB673`, `routing.source=shopify`, then picked. `HJF8D6FA95E7F56` stayed `pending`, with `clear_skipped{type:pick_confirmation, reason:no_subscription}` = 1.
  - **Case 3 (AC 2).** `routing.source=mock`, then packed. `HJF0BE3CA9306F8` stayed `pending` (`no_subscription`, pack).
  - **Case 4 (AC 2).** Routing doc deleted, then despatched. `HJF898A68FF319A` was published broadcast (`fuse.confirmation.manual_origin_broadcast` good_out = 1), skipped `broadcast`, and left `pending`. Side effect: case 2's pick re-announced at 14:38 after its claim expired. With the doc gone it went out broadcast, was skipped `broadcast` and left pending (pick broadcast = 1).
  - **Case 5 (AC 4, 5).** One fault armed on `snapoutbound` (503, count 3, enough for the interceptor's 2 retries). `HJF32A9359FC7BA` was published, then `Outbound queue clear failed` (`reason: request_failed`, 503) at 14:36:08Z, `clear_failed{request_failed}` = 1, row `pending`. Once the 10-minute claim expired it re-announced and was `processed` at 14:48:06Z. No loss.
  - **Case 6 (withheld).** `conn_1a5c…` `confirmationsEnabled: false` (PATCH; GET before and after showed only that field change). HJF then had no confirmations-enabled connector, so the poller stopped polling HJF (last HJF fetch 14:30:03Z). `HJF32A9359FC7BA` stayed `pending`, with nothing published or cleared. That is the business-level withhold. The per-connector withhold is unit-tested ("never clears a group withheld for an ineligible connector"). Flag restored to `true`; the business index matches its pre-test state.
  - **Case 7 (repeat PATCH).** HJF's only delivering connector posts to example.com, so no `confirmation_made` occurs and snap-adapter's clear-down can't be triggered. Instead the same wire call was made: `PATCH /v2/snapoutbound/HJF7E826A4C4837/processed` on the already-cleared row returned `Success` with the row, `DateProcessed` restamped 14:22:07 → 14:23:28. snap-adapter's own clear-down log check is left for BYOMA's first prod cycles.
  - **Case 0 (AC 3).** Every `snap.outbound.*` series in the window carries `businessid:hjf` only.
  - **Cleanup:**
    - test rows cleared one by one (`/queue/{xdoc}/clear`), plus the two stale rows before starting
    - `HJF__HJF37621F0AB673` routing doc restored to `rest`/`conn_1a5c…`
    - faults: none
    - connector flag restored
    - dev on master
    - test replay failures (HJF, 2026-10-02): `8bf86704`, `d897e9ce`, `0c84efa5`, `329c02cf`, `600d7010`, `429a2c90`
- 2026-10-02 [inc 6] fuse-mocker `0b4f75d` (direct to main, Deploy run 37017588719 green): `markProcessed` fires faults armed on `snapoutbound`, and the UI fault dialog lists it. 3 new Go tests: armed 503; item stays queued; clears once the count is spent. `go test ./...` and `go vet` clean. Exercised live in e2e case 5.
- 2026-10-02 [inc 4, 5] Unit, `d74e174` and `4a89c09`.
  - Config:
    - 6 `parseBusinessIdList` tests.
    - Throwaway schema check: `HJF, BYOMA` → `[HJF, BYOMA]`; `HJF,BAD ID` fails; unset → `[]`; concurrency default 3, `0` fails.
  - Announce wiring: 8 `confirmations.service.spec` tests.
    - emit before clear
    - rejected publish clears nothing
    - duplicate-claim rows not cleared
    - unavailable-claim rows cleared
    - an earlier group stays cleared when a later group throws
    - the right business's client
    - no client → `undefined`
    - withheld group never cleared
  - Polling spec: hands the chunk's clients to the announce.
  - Full suite 707/707; lint exit 0; `build:check` and `build` clean.
- 2026-10-02 [inc 2, 3] Unit, PR #278 (`c173b6e`, `fd9d02b`). Pool: peak in-flight 3 for 7 items at limit 3; input order kept; every item settled when one rejects. Channel table: 7 tests (rest/sftp every routing-aware type, shopify goods-out only, unknown and inherited keys false, no `stock_adjustment`). Clearer: 26 tests covering the allow-list, every skip and fail reason, dedupe, breaker stop plus a single log, and never rejecting. Full suite 692/692, lint exit 0, `build:check` clean.
- 2026-10-02 [inc 1] Dev e2e, branch `97a7880` (manual deploy run 37014966542, announced in #bifrost-general, revision `snap-polling-service-dev-00438-cx2`): cancelled HJF shipment `HJFD86486746A56` through the simulator. The poller logged `Shipment cancelled - dropping from confirmation flow`, then `Record dropped` for `HJF3784C6A7DDEF` at 13:48:05Z on `version:97a7880…`. The row shows `processed` at 13:48:05Z. That proves the hardened clear parses the simulator's real success body. Error paths are unit-only until inc 6.
- 2026-10-02 [inc 1] `api.client.spec.ts` gains 6 clear tests (PATCH route, success, 2xx Status Error → `isSnapError`, empty Results → `isNotCleared`, non-envelope → `ValidationException`, breaker open sends nothing). Full suite 656/656, `lint` exit 0, `build:check` clean. The black-box mock's processed route now answers with a real SNAP envelope.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- snap-adapter's own clear-down running after a poller clear, end to end. No HJF connector produces `confirmation_made` (the webhook is example.com), so only the equivalent wire PATCH was run (case 7). BYOMA's first prod D1 cycles prove it: no `Confirmation clear-down failed` for cleared rows.
- The per-connector withhold inside a business that still has another enabled connector: unit-tested only. HJF has no second enabled connector.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->

- **2026-10-02 (Harry)** — E3 (whole-bulk Zod drop in fapi/shopify) accepted as a named D1 residual, stated in PR C's risks; not built for in C2.

- **2026-10-02 (Harry)** — Dev allow-list merges as ["HJF"], prod []; the e2e goes through Terraform, not an out-of-band gcloud update.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
