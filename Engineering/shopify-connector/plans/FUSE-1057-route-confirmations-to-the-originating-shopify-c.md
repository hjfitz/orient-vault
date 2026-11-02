---
ticket: FUSE-1057
title: Route confirmations to the originating Shopify connector by connectorId
service: shopify-connector
status: complete
created: '2026-09-02'
updated: '2026-10-05'
repo: /home/hjf/code/fuse/shopify-connector
worktree: /home/hjf/code/fuse/shopify-connector/.claude/worktrees/fuse-1057-connector-routing
branch: hjf/fuse-1057-connector-routing
base: origin/main
base_sha: 27c0993
pr: '254'
tags:
- waypoint
- plan
---
# FUSE-1057 — Route confirmations to the originating Shopify connector by connectorId

## Intent
[FUSE-1057](https://globalfreight.atlassian.net/browse/FUSE-1057). `ShopifySalesOrderService
.processConfirmations` has no connector-awareness today — every sales-order confirmation for a
business is attempted against **every** active, mapping-configured Shopify connector
(`Promise.allSettled` over all of them). This resolves the *one* originating connector by
`metadata.connectorId` and delivers only there, falling back to today's broadcast-to-all only
when `attributes.broadcast="true"` or no `connectorId` is present. A connectorId that should have
resolved but can't publishes a `confirmation_data_failure` (`rule=connector_unresolvable`) instead
of silently broadcasting — as does a connectorId belonging to another channel, which additionally
raises a monitor (Harry, 2026-09-02). Mirrors the sibling FUSE-1055 (sftp-connector #262) /
FUSE-1056 (fapi #121) pattern, both still in draft.

## Acceptance criteria
- [x] A `goods_out_confirmation` (sales_order) carrying `metadata.connectorId` is delivered only
  to that connector, not broadcast to every active Shopify connector on the business.
- [x] `attributes.broadcast === "true"`, or an absent `connectorId`, preserves today's
  broadcast-to-all — no regression; single-connector customers (SAIRA, the only live prod
  Shopify tenant today) see no behaviour change.
- [x] A `connectorId` naming a Shopify connector on this business that isn't usable (inactive, or
  no confirmation mapping) publishes a `confirmation_data_failure`
  (`errors: [{type: "business_rule", rule: "connector_unresolvable"}]`) + a metric, and does
  **not** fall back to broadcast.
- [x] A `connectorId` naming no Shopify connector on this business (another channel's confirmation,
  which this subscription still receives) is **also** a failure — same `connector_unresolvable`
  publish, tagged with its own reason — and a Datadog monitor fires on it. Decided by Harry
  2026-09-02: a mismatched source is a real defect upstream, not something to swallow quietly.
- [x] A monitor exists on the mismatched-source metric, with a named alert channel (mirrors
  FUSE-1053's monitor AC).
- [x] Terraform `source`/`broadcast` subscription-filter widening on `goods_out_confirmation` —
  **deferred**, tracked as increment 6, gated on FUSE-1052/1053 shipping to prod.
- purchase_order — **out of scope entirely**: shopify-connector has no PO ingestion or
  confirmation path at all (confirmed by source — see Assumptions). The ticket's shared
  "PO/SO" template language, copied across FUSE-1055/1056/1057, doesn't apply here; this plan
  covers sales_order confirmations only.

## Affected boundaries
- `apps/shopify-connector/src/adapters/pubsub/pubsub.service.ts` /
  `adapters/pubsub/types.ts` — `ingestEvent()` validates the envelope via `PubSubEventSchema`
  but discards `message.attributes`; needs a way to expose `attributes.broadcast` to the
  controller (mirrors fapi/sftp's `parseEnvelope()` factor-out).
- `apps/shopify-connector/src/http/controllers/confirmation-events.controller.ts` —
  `salesOrderConfirmationHandler` reads the broadcast attribute, threads
  `metadata.connectorId`/`broadcast` into `processConfirmations`.
- `apps/shopify-connector/src/core/shopify/use-cases/shopify-sales-order.service.ts` —
  `processConfirmations` — the core routing change. **Narrow within the already-fetched,
  Shopify-scoped `getByBusinessId(bizId)` list — do *not* route through
  `ConnectorConfigProvider.getByConnectorId`.** That resolver looks a connector up globally by id
  with no type or tenancy filter and then hydrates it via
  `ZodUtilities.parse(ShopifyIngressSchema, connector.config)`, which **throws** for a non-Shopify
  connector — so a foreign-channel connectorId is indistinguishable from a genuine not-found, and
  a wrong id could in principle reach another customer's connector. sftp-connector's sibling PR
  filters within the business's own connectors for exactly this reason (its code comment: "so a
  wrong id can't reach another customer's connector"); fapi's code-review correction onto the
  global resolver was about not reinventing an existing resolver, not about tenancy, and doesn't
  transfer here.
- New: an egress failure publisher for `confirmation_data_failure`. shopify-connector has **zero**
  existing wiring to this topic (verified — no reference anywhere in `apps/shopify-connector` or
  its `iac/`). `EntityType.SALES_ORDER_FAILURE` → `createSalesOrderFailure` is the **ingest-side**
  `create_data_failure` topic, a different topic entirely, not reusable here. Mirror
  `core/collections/sales-order.failure-publisher.ts`'s shape (build-then-publish-swallow-log,
  never throw — matches [[known-context]]'s documented "failure-publish-don't-throw" convention).
- `apps/shopify-connector/src/providers/observability/metrics.service.ts` —
  `CONFIRMATION_UNROUTABLE_REASON` gains `CONNECTOR_UNRESOLVABLE: "connector_unresolvable"` and
  `SOURCE_MISMATCH: "source_mismatch"`.
- **A monitor on the `source_mismatch` reason — now in `gfs-bifrost/observability`, not this repo**
  (`monitors.shopify-connector.tf`). It was built here first (the fleet's first monitor-as-code,
  `providers.tf` + `monitors.tf`) and moved out on 2026-09-02; this repo's IaC carries no Datadog
  resource, provider or app key. See increment 4 and the deviation below.
- `apps/shopify-connector/src/providers/app-config/{types,config.schema,app.config.service}.ts`,
  `src/app.module.ts` (topics map), `src/core/types.ts` (new `EntityType` member) — new topic
  plumbing for `confirmation_data_failure`.
- `iac/shopify-connector/projects/bifrost-shopify-connector/{remote.tf,pubsub.tf,cloud-run.tf}` —
  pull `confirmation_data_failure_topic_id`/`_topic_name` from `core_pubsub` remote state
  (outputs already exist — verified in `bifrost-pubsub/iac/projects/bifrost-pubsub/errors.outputs.tf`,
  same source sftp-connector already reads), add an IAM publisher binding
  (mirrors `cloudrun_create_data_failure_push`) + env var. The `goods_out_confirmation`
  subscription's `source`/`broadcast` filter — deferred to increment 6.
- Not touched: `stock_adjustment` confirmations (no connectorId concept applies — out of ticket
  scope). The internal shopify-connector re-architecture programme's `C-CONFIRM`/`G2a` units
  (confirmation-handler split, same controller file) — per `Migration State.md` that unit is
  "re-scope, not started," so low collision risk today, but re-check before implementing in case
  it's moved.

## Assumptions & uncertainty
- **Confirmed by source (`core/types.ts`, `http/controllers/`):** shopify-connector has no
  `EntityType.PURCHASE_ORDER` and no PO confirmation route or service at all — the ticket's
  generic "PO/SO" AC language narrows to sales_order only. Not asked; settled by reading the code.
- **Confirmed by source:** unlike fapi's pre-1056 state, shopify-connector's `ingestEvent` already
  imports `BifrostBulkMessageSchema`/`PubSubEventSchema` directly from `@gfs-bifrost/types` (not a
  local hand-rolled schema), and `PubsubService.prepareMessage` already stamps
  `connectorId`/`source`/`recordType` on outbound envelopes — so the FUSE-794 metadata-strip class
  fapi had to fix in its increment 1 does not apply here. `metadata.connectorId` already round-trips
  through `ingestEvent` today.
- **Live-traffic finding, flagged not chased:** shopify-connector's lockfile resolves
  `@gfs-bifrost/types@9.3.0` (verified in `pnpm-lock.yaml`) — pre-9.3.1, i.e. it should still carry
  the `PubSubEventSchema` bug pkg-node's 9.3.1 changelog describes (schema requires **both**
  camelCase and snake_case `messageId`/`publishTime` on the same envelope object, said to make it
  unable to validate any real Pub/Sub push message). But live Datadog logs (2026-09-02, `service:
  shopify-connector`) show `salesOrderConfirmationHandler` actively decoding and processing real
  confirmations successfully right now ("Handling confirmation" → "Confirmation Processed" →
  "Confirmation successful", `202 Accepted`). Either real GCP Pub/Sub push traffic sends both
  casings (contradicting the pkg-node fix's stated premise that "real messages only ever send
  camelCase"), or something else differs. Not resolved or chased here — out of this ticket's scope
  — but flagged because increment 1 builds on this exact `PubSubEventSchema`/`ingestEvent` path.
- **Confirmed by source:** `ConnectorConfigProvider.getByConnectorId` → `ConfigApiAdaptor
  .getConnectorByConnectorId` → remote-config's `ConnectorBacklinkHandler.resolveByConnectorId`,
  which **throws** on no match (distinct from `resolve()`'s empty-array-on-no-match, per the
  `@gfs-bifrost/remote-config` changelog) — *and* `hydrateConfiguration` throws again for any
  connector that resolves but isn't Shopify-shaped. Two different causes, one indistinguishable
  outcome — see Affected boundaries for why this plan routes via the business-scoped list instead.
- **The ordering hazard this plan exists to avoid — verified against live prod config (2026-09-02).**
  `PURDYFIGG` has three connectors on one storefront: `Main SFTP`, `API`, and
  `Purdy and Figg Live Shopify` — a live, multi-channel business, and the one just enabled for bulk
  Shopify ingest in prod (`89b4fa8`). shopify-connector's `goods_out_confirmation` subscription is
  filtered on `recordType` **only**, so it already receives PURDYFIGG's SFTP- and API-origin
  confirmations. Today those harmlessly no-op (the handler returns `undefined` — "order not on this
  store"). A naive connectorId narrowing would instead classify every one of them
  `connector_unresolvable` and publish a failure — a false-failure flood into
  `confirmation_data_failure` and the exceptions surface, for a live customer, in the window
  between increment 3 and the deferred increment 6. Increment 3's decision table below is written
  to close this; do not simplify it away.
- SAIRA — the only single-Shopify-connector live tenant — is unaffected either way, so the
  "single-connector customers see no behaviour change" AC is trivially met for it. PURDYFIGG is the
  case that actually exercises this ticket.
- **Confirmed by source:** no existing `confirmation_data_failure` plumbing anywhere in
  shopify-connector (app or iac) — genuinely new infrastructure, not an extension of an existing
  publisher. Confirms FUSE-1011's own "not yet investigated" note for this service.
- **Verified via GitHub (sftp-connector #262, fapi #121 + its Waypoint plan):** the concrete
  pattern this plan mirrors — `type: "business_rule"` / `rule: "connector_unresolvable"` failure
  shape (no `reason` field exists on `BifrostFailure`/`FailureAttributes` despite the ticket text
  implying one — decided 2026-08-25 on the fapi plan), connectorId resolution narrowed-not-filtered,
  Terraform filter widening deferred as its own increment gated on FUSE-1052/1053.
- **Verified via Jira (2026-09-02):** the full upstream chain is not yet merged — FUSE-1052/1053
  (Snap: publish `source`/`broadcast` attributes + no-origin broadcast) is snap-adapter PR #194,
  open; FUSE-1054 (PO/SO dual-publish onto the cross-entity vein — not actually load-bearing for
  shopify-connector, since sales_order has been on the cross-entity vein since commit `05813b6`,
  pre-dating this ticket) is PR #188, open; FUSE-1011 (widens replay-service's
  `confirmation_data_failure` subscription filter to include `sales_order`, not just pick/pack) is
  still "Ready for Refinement," not started. **Increments 1-3 below don't require any of these
  merged first** — they build against `metadata.connectorId` (already flowing, FUSE-834 done) and
  a raw `attributes.broadcast` read that degrades safely (`undefined` → broadcast preserved) when
  the attribute doesn't exist yet. Only increment 6 (the Terraform filter) and full confidence that
  a `connector_unresolvable` failure is actually replayable both gate on the upstream tickets —
  matches fapi's own plan precedent exactly.
- **Confirmed by source (snap-adapter `origin/master`,
  `apps/snap-queue-polling-service/src/core/snap/confirmations/confirmations.service.ts:166`):**
  the poller already stamps `metadata.connectorId` from the SNAP attachment's
  `routing?.connectorId` on the confirmation publish, optional-chained — so it's present when SNAP
  carries routing and absent otherwise, which is exactly the two branches this plan needs. fapi's
  sibling plan left this unverified; it's verified now. Still worth sampling a real prod message in
  waypoint-test to confirm non-null in practice for a Shopify tenant.
- **Decided 2026-09-02 (Harry) — a mismatched source fails loudly, it is not skipped.** The
  question was whether a connectorId naming no Shopify connector on this business should be a
  silent skip (today's effective behaviour) or a failure. Call: *"if we've got a connector with a
  mismatched source, let's fire a monitor and fail things."* So both unusable-connector and
  foreign-channel land on `connector_unresolvable`, separated only by a metric `reason` tag, and a
  monitor watches the foreign-channel one. Rationale: a confirmation reaching the wrong channel's
  connector means something upstream is wrong, and the FUSE-927 family exists to stop channel
  bleed — swallowing it quietly is how it stays invisible.
- **Could not measure the mismatched-source volume from logs — so increment 3 measures it in
  flight rather than guessing.** Every confirmation consumer receives every business's
  confirmations (subscriptions filter on `recordType` only), so a business appearing in
  sftp-connector's logs does not mean its orders originate there — the deciding signal is the
  envelope's `connectorId`, which isn't on any log line I can query. What *is* established: the 28
  Shopify-less businesses never reach the connectorId branch at all (they short-circuit on the
  existing zero-candidates gate — ~2,548 `No routable connector` warns/7d, unchanged by this
  ticket), so the exposed population is PURDYFIGG alone. Whether PURDYFIGG's orders actually arrive
  through its SFTP/API connectors as well as Shopify is unknown; its SFTP connector currently has
  the goods-out confirmation use case **inactive** (`Confirmation use case not active for connector
  — skipping`, ~557 confirmations/7d), which is suggestive but not proof of origin. Hence the 3→4→5
  sequencing below: emit the metric, build the monitor, read the real number off prod, then
  turn the failure publish on.

## Increments
Each independently implementable and verifiable. Tick only what is done and verified.

- [x] 1. Expose the Pub/Sub envelope's `attributes` alongside `ingestEvent()`'s existing decode
  (factor a `parseEnvelope`-style read out of `ingestEvent`'s existing envelope-parse step — no
  behaviour change for the existing call). `salesOrderConfirmationHandler` reads
  `attributes.broadcast === "true"` and logs it (not yet wired into routing). — verify: unit test
  asserting `attributes.broadcast` is read/logged; a second test asserting `metadata.connectorId`
  already survives decode unmodified (documents there's no strip bug here, see Assumptions); full
  suite green; `build:check` clean.
  — done 2026-09-02: `parseEnvelope()` factored out of `ingestEvent()` (which now calls it, so the
  existing path is unchanged), added to `IPubsubService` + the mock fixture; controller reads
  `attributes.broadcast`, stamps `connectorId` into the correlation scope (so it rides every
  confirmation log line, which it didn't before) and debug-logs both. 3 new tests
  (broadcast true / absent-attributes false / connectorId survives decode); 727/727 suite,
  `build:check` clean, `lint` exit 0.
- [x] 2. Stand up the `confirmation_data_failure` egress-failure publisher and its plumbing: new
  `EntityType` member, `PubsubTopics.confirmationDataFailure` + env var + config schema entry,
  `app.module.ts` topics-map entry, Terraform (`remote.tf` pulls the two existing `core_pubsub`
  outputs, `pubsub.tf` IAM publisher binding, `cloud-run.tf` env var), and a
  `ConfirmationFailurePublisher` mirroring `SalesOrderFailurePublisher`'s shape (`stage:
  "confirmation"`, swallow-and-log on publish failure, never throw). `CONFIRMATION_UNROUTABLE_REASON
  .CONNECTOR_UNRESOLVABLE` added. No caller yet. — verify: unit tests for the new publisher in
  isolation; `terragrunt plan` (dev) shows only the new topic-id lookup + IAM binding + env var;
  `build:check` clean.
  — done 2026-09-02: `EntityType.SALES_ORDER_CONFIRMATION_FAILURE` → `confirmationDataFailure`
  topic; env var through `config.schema.ts`/`app.config.service.ts`/`cloud-run.tf` **and both
  tracked env files** (`.env.test`, `.env.sample` — a required `z.string()` var breaks every
  config-booting test otherwise); `remote.tf` locals + `pubsub.tf` IAM publisher binding;
  `ConfirmationFailurePublisher` registered in `shopify.module.ts`. Stamps
  `useCase`/`recordType: "goods_out_confirmation"` and `stage: "confirmation_ready"` (matching
  sftp-connector's egress precedent, not fapi's `confirmation_made`). 8 new tests; 735/735 suite,
  `build:check` clean, `lint` exit 0. Repo `CLAUDE.md` updated in the same change per its own
  rule. `terragrunt plan` still outstanding — runs at deploy time in Step 3.
- [x] 3. Wire routing into `ShopifySalesOrderService.processConfirmations`: accept
  `connectorId`/`broadcast` params (threaded from the controller) and apply this decision table
  against the business's own Shopify-scoped connector list (`getByBusinessId`, already fetched —
  no new config call, no global-by-id resolve):

  | `broadcast` / `connectorId` | connectorId matches a Shopify connector on this business? | Outcome |
  | --- | --- | --- |
  | `broadcast=true`, or no `connectorId` | — | broadcast to all (today's behaviour, unchanged) |
  | set | yes, active + mapping-configured | deliver to that one connector only |
  | set | yes, but inactive or unmapped | `connector_unresolvable` failure + metric (`reason: connector_unresolvable`), no delivery, no broadcast |
  | set | no | `connector_unresolvable` failure + metric (`reason: source_mismatch`) + monitor, no delivery, no broadcast |

  Both failing rows publish the same failure; the `reason` tag is what separates a broken connector
  from a wrong-channel delivery, and what the monitor (increment 4) watches. **This increment stops
  short of publishing on the last row** — it emits the `source_mismatch` metric and logs, but still
  skips, so the real volume can be read off prod before failures start landing for a live customer
  (increment 5 turns the publish on). — verify: unit tests, one behaviour each — resolve-to-one;
  `broadcast=true` overrides a set connectorId; absent connectorId broadcasts; inactive/unmapped
  match → failure publish + metric + zero delivery attempts + no broadcast fallback; foreign
  connectorId → zero delivery attempts + `source_mismatch` metric + no failure publish (yet);
  single-connector customer unaffected. All pre-existing `processConfirmations` tests updated for
  the new params and passing unmodified in behaviour.
  — done 2026-09-02: routing lives in a private `selectTargets` that returns the target configs or
  `undefined` (already reported). Deliberately placed **after** the existing zero-candidates gate,
  so the 28 Shopify-less businesses keep hitting `no_connectors` exactly as today and never reach
  the connectorId branch. `ConfirmationRouting { connectorId?, broadcast }` threaded from the
  controller; defaults to `{ broadcast: false }` so the existing call shape stays valid.
  9 new tests covering every row of the table plus the two negative cases; 746/746 suite,
  `build:check` clean, `lint` exit 0.
- [x] 4. **Datadog monitor for `source_mismatch`, in Terraform.** **Superseded — the monitor now
  lives in `gfs-bifrost/observability`, not here; everything below describes how it was first
  built in this repo and is kept only as the record of that. See Decisions and Verification.**
  It was the **fleet's first
  monitor-as-code** — verified 2026-09-02: zero `datadog_monitor` resources in any Fuse repo, and
  the `datadog-integration` repo wires only the GCP→Datadog metric/log *pipeline* (google providers
  only, no Datadog provider). So the increment is provider adoption as much as it is one monitor:
  add the `DataDog/datadog` provider to
  `iac/shopify-connector/projects/bifrost-shopify-connector/providers.tf` (pinned), source
  `api_key` from the **existing** `datadog_api_key` var (already passed into the terragrunt apply
  by `shopify-connector-manual-deploy.yaml:41-42`) and `app_key` from a new var. Credentials are
  confirmed working (see Decisions); the only open item is whether CI gets a service-account app
  key rather than the personal one in `~/.secrets`.
  Monitor: a metric monitor on **`shopify_connector.confirmations.unroutable`** — underscore
  prefix, this service is **not** on the shared `fuse.*` catalogue (see Decisions) — filtered to
  `reason:source_mismatch` + `environment:prod`, threshold above zero on an `.as_count()` sum,
  with a named alert channel (mirrors FUSE-1053's monitor AC).
  **Three traps to design against, all now verified rather than assumed:** (a) scope on
  **`environment`**, never `env` — the sidecar hard-codes `DD_ENV=serverless`, so every line and
  series reads `env:serverless` and an `env:prod` monitor silently never fires (the 2026-08-27
  class of bug); (b) the metric prefix is `shopify_connector` (underscore) while the Datadog **log**
  service is `shopify-connector` (hyphen) — the two disagree for this service, so a name copied
  from one side 404s on the other; (c) sum an `.as_count()`, not the bare series — a bare sum
  averages a rate and reads near-zero on a real signal.
  Placement was per-service iac by default (Harry, 2026-09-02 — wanted the Terraform in this
  ticket); **superseded the same day** — Fuse's Datadog resources are managed in one repo,
  `gfs-bifrost/observability`, and this monitor moved there. See the deviation below.
  — done 2026-09-02 (commit `32a08cd`): provider pinned `4.19.0`; `datadog_app_key` var defaulted
  `""`; monitor `count = var.is_preview_env ? 0 : 1`, **one per env**, name-suffixed with `var.env`,
  and the `@team-fuse` handle only interpolated when `var.env == "prod"` so a dev signal can't page.
  Shape copied from the fleet's closest existing monitor (`[SFTP] File Upload Failure`) rather than
  invented: `query alert`, `sum(last_5m):avg:…as_count() >= 1`, tags `team:fuse`/`domain:fuse`.
  `notify_no_data = false` — this counter reading zero *is* the healthy state.
  **No shared-workflow change was needed** — the reusable `terragrunt.yaml` already exposes
  `tf_var_extra_1..5`, and slot 3 was free, so the key rides `tf_var_extra_3_*` in `manual-deploy`,
  `on-push` (all three jobs) and `tf-plan`. — verify: `terragrunt plan`
  (dev) shows only the provider + one monitor resource; the monitor exists in Datadog post-apply
  and is **verified firing** against a synthetic foreign-connectorId confirmation in dev; a
  no-mismatch window leaves it green.
- [x] 5. Turn the foreign-channel row's failure publish on, once increment 4's monitor has read the
  real `source_mismatch` volume off prod. If it's ~zero this is trivial; if it's material, that
  number is the argument for pulling increment 6 forward instead of eating the failures. — verify:
  the foreign-connectorId unit test flips to asserting a published failure; prod
  `confirmation_data_failure` volume after deploy matches what the metric predicted, with no
  surprise third source of mismatches.
  — done 2026-09-06 (commit `b684722`, PR #254, branch `hjf/fuse-1057-filter-and-mismatch-failure`): the
  "read prod volume first" gate was dropped — it existed only because of the exposure increment 6
  removes, and increment 6 turned out to be unblocked (see Decisions). The mismatch branch now logs
  at `warn` (`audience: support`) and calls `publishUnroutable`; the test pinning "does not publish a
  failure yet" flipped to assert the publish. Dev-verified: a `source=shopify` envelope naming the
  SFTP connector produced `Confirmation named a connector on another channel — nothing sent` and
  `Published failure event (21487207580630029)`, no delivery, 202.
- [x] 6. **Deferred — do not action until the pre-condition is confirmed.** Widen the
  `goods_out_confirmation` Terraform subscription filter from
  `attributes.recordType = "goods_out_confirmation"` to `... AND (attributes.source = "shopify" OR
  attributes.broadcast = "true")`. Pre-condition: confirm in Datadog/live traffic that
  `snap-queue-polling-service` is actually publishing `source`/`broadcast` in prod (FUSE-1052
  **and** FUSE-1053 shipped) — applying this filter first silently zeroes shopify-connector's
  confirmation delivery entirely. — verify: `terragrunt plan` shows only the filter change; a live
  confirmation with `broadcast=true` or `source=shopify` still reaches the endpoint post-deploy; a
  `source=sftp`-only, non-broadcast confirmation does not.
  — done 2026-09-06 (commit `b684722`, PR #254). Pre-condition confirmed from source, not Jira:
  snap-adapter #194 (FUSE-1052+1053) merged 2026-09-02 10:31 and is an ancestor of `80dcce0`, the
  last completed snap prod deploy (2026-09-02 16:24); `pubsub.router.ts` stamps `source` and
  `broadcast="true"` conditionally. Filter is now `attributes.recordType = "goods_out_confirmation"
  AND (attributes.source = "shopify" OR attributes.broadcast = "true")` — a 1-line CRLF-preserving
  edit. Dev-verified with five envelopes: `source=shopify` arrives; `source=sftp` non-broadcast →
  zero log lines (dropped at the subscription); `broadcast=true` arrives; legacy shape with neither
  attribute → zero log lines. Prod filter unchanged until #254 merges and passes QA.

## Verification

**Local (2026-09-02, commit `a73bc53`):** `pnpm test` 746/746 across 50 suites (20 new);
`pnpm run build:check` clean; `pnpm run lint` exit 0. (No `build:check:tests` script in this repo —
`build:check` already covers specs; CI runs test/lint/build:check only.)

**Dev deploy:** `shopify-connector-manual-deploy.yaml` run `33621080953` — both jobs green
(`docker-push-dev`, `terraform-apply-dev`), revision `shopify-connector-dev-cr-00461-lvh` Ready.

**Terraform, verified live rather than from the plan output:**
- `gcloud run services describe` → `PUBSUB_TOPIC_ID_CONFIRMATION_DATA_FAILURE =
  bifrost.dev.confirmation_data_failure.v1` on the dev service.
- `gcloud pubsub topics get-iam-policy bifrost.dev.confirmation_data_failure.v1` →
  `roles/pubsub.publisher` for `shopify-connector-dev-cr@bifrost-dev-global1`.
- The service reaching Ready is itself evidence the new **required** env var is set — a missing one
  fails the zod config schema at boot.

**Increment 1 — verified end-to-end on the deployed build.** Published two real
`goods_out_confirmation` envelopes to `bifrost.dev.confirmation_ready.v1` (records generated with
`@gfs-bifrost/types`' own `buildGoodsOutConfirmation` and schema-checked before publishing).
Read back via `gcloud logging read` (Datadog's pipeline hadn't ingested them yet — the same lag
fapi's FUSE-1056 hit):
- `broadcast=true` attribute, `connectorId: conn_c7e4fd39…` → `Confirmation routing signals`
  logged `broadcast: True` with the connectorId; `202 Accepted`.
- no `broadcast` attribute, `connectorId: conn_179b2416…` → same line logged `broadcast: False`.
- `connectorId` now rides **every** subsequent confirmation log line for the request (it appears on
  `Resolved all connectors from cache`, `Processing confirmations for business`, the unroutable
  warn and the access log) — the correlation-scope stamping this increment added.

**Increments 2 + 3 — verified end-to-end on the deployed build (2026-09-02).** Dev initially had
**no active Shopify connector at all**, so every confirmation short-circuited on the pre-existing
`no_active_connectors` gate before `selectTargets` was reached. Harry authorised activating GADG's
`conn_c7e4fd39…` ("ILG Test Store", store `quickstart-501d0f59.myshopify.com`) in dev config, which
opened the path. That left an ideal matrix on GADG: `conn_c7e4fd39…` active + `goods_out_confirmation`
mapping; `conn_3759d3fa…` ("Nylah's Bees") **shopify but inactive and unmapped**; `conn_179b2416…`
("Primary SFTP") a different channel entirely. Five real envelopes published to
`bifrost.dev.confirmation_ready.v1`, read back via `gcloud logging read`:

| case | `connectorId` / attr | observed |
| --- | --- | --- |
| resolved | active + mapped Shopify | `Processing confirmation` against **`quickstart-501d0f59…` only**; `Confirmation processing complete` lists that one store; 202 |
| source mismatch | the SFTP connector | `Confirmation is not for a Shopify connector`; **no** `Processing confirmation`, **no** `Published failure event`; 202 |
| unresolvable | Shopify, inactive + unmapped | `Confirmation named a Shopify connector that cannot receive it — nothing sent` **and `Published failure event (21456849073174800)`**; no delivery; 202 |
| no connectorId | absent | broadcast to every eligible connector, unchanged; 202 |
| broadcast | `broadcast=true` + a set connectorId | routing signals `broadcast: True`, broadcast path taken; 202 |

The `Published failure event` line is also the **first real proof of increment 2's plumbing** — the
IAM binding and env var carried an actual message onto `bifrost.dev.confirmation_data_failure.v1`,
not just a passing unit test. (The resolved/broadcast cases end in `Invalid Fulfillment Order ID`,
expected: the synthetic record's fulfilment id doesn't exist in that store. What's being proven is
*which* connector was targeted, not that Shopify accepted it.)

**Metrics confirmed in Datadog** (`shopify_connector.confirmations.unroutable{environment:dev}
by{reason}.as_count()`): `source_mismatch: 1`, `connector_unresolvable: 1`,
`no_active_connectors: 3` — exactly the shape and counts the five sends should produce, and the
query increment 4's monitor will use, now validated against real emitted data.

**Increment 4 — monitor verified live, including that it actually fires.** Deploy run
`33624082677`, both jobs green. Monitor `318650428` exists in Datadog as
`[Shopify] Confirmation Source Mismatch — dev`, query
`sum(last_5m):avg:shopify_connector.confirmations.unroutable{reason:source_mismatch,environment:dev}
.as_count() >= 1`, tags `domain:fuse`/`service:shopify-connector`/`team:fuse`,
`notify_no_data: false`, and **no `@` handle in the dev copy** (confirmed by reading the rendered
message back off the API) so a dev signal cannot page. It read `OK` on creation, then published
three foreign-connectorId confirmations and it transitioned **OK → Alert in 80s**, then recovered
to **OK 280s** after they stopped (consistent with the `last_5m` window clearing) — so the metric
name, the `reason` tag, the `environment` scope, the threshold *and* the recovery all line up
against real emitted data, not just a plan diff.

**Residual gap, stated rather than papered over:** GADG has only *one* eligible Shopify connector in
dev, so "delivered to one of several" and "broadcast reaches several" are indistinguishable in the
live evidence — both correctly target the single store. The multi-connector narrowing is covered by
unit tests only. Reproducing it live needs a second active, confirmation-mapped Shopify connector in
dev, which doesn't exist.

**Increment 4 — monitor handed over to `gfs-bifrost/observability` (2026-09-02).** Dev deploy run
`33635623553`, both jobs green, `Apply complete! Resources: 0 added, 1 changed, 1 destroyed` — the
destroyed resource being `datadog_monitor.confirmation_source_mismatch[0]` (`318650428`), which now
**404s** on the Datadog monitor API, with no source-mismatch monitor left anywhere in the org. The
`DataDog/datadog` provider and app key came out in a following commit, once dev state no longer
held the resource; the branch's dev plan is back to `0 to add, 1 to change, 0 to destroy` (its own
image tag) and the touched IaC and workflow files match `main` byte-for-byte. The monitor is
recreated in `observability` as two resources, `confirmation_source_mismatch_dev` /
`_prod`, with the same query — so it gets a **new id**; checked first that no Fuse dashboard binds
a widget to a monitor id.

### Evidence
- 2026-10-05 [sign-off] Both PRs read with `gh pr view --repo gfs-bifrost/shopify-connector`: #239
  MERGED 2026-09-06 11:01 (`cd552df`), #254 MERGED 2026-09-07 09:54 (`f9ffaaf`), no failing checks
  on either. Both are ancestors of `origin/main` (`5c28e8d`). The gate can't read the `pr:` field
  because `wp` passes `'239, 254'` to `gh` as one PR number, and with no readable PR it can't see
  the work is merged and blocks on "no diff". `wp` supports one PR per plan, so `pr:` now holds
  `254`, the PR that finished the plan (increments 5–6). #239 (increments 1–4) is recorded here and
  in the increments; the old value was `'239, 254'`.
- 2026-10-05 [sign-off] Prod `shopify-connector-prod-cr` runs revision `00053-9qx`, image
  `prod-5c28e8d…` (`DD_VERSION` the same, Ready 2026-10-05 09:20), with
  `PUBSUB_TOPIC_ID_CONFIRMATION_DATA_FAILURE=bifrost.prod.confirmation_data_failure.v1`. Both merges
  are live in prod (AC 1–4).
- 2026-10-05 [sign-off] Prod subscription `shopify-connector_prod_goods_out_confirmation_v1_sub`
  filter read live: `attributes.recordType = "goods_out_confirmation" AND (attributes.source =
  "shopify" OR attributes.broadcast = "true")`. AC 6 is applied in prod.
- 2026-10-05 [sign-off] `selectTargets` on `origin/main` read: broadcast or no `connectorId` returns
  every eligible connector (AC 2); a match returns `[target]` only (AC 1); a Shopify connector on the
  business that isn't eligible goes to `publishUnroutable` (`connector_unresolvable`) with no
  fallback (AC 3); no match publishes a failure and returns nothing (AC 4). At #254's merge the
  mismatch branch used the same `connector_unresolvable` publish, as AC 4 says. FUSE-1238 (#294,
  2026-10-01) later changed that branch's rule to `source_mismatch` and limited it to routed
  confirmations. `architecture.md` already describes the current shape.
- 2026-10-05 [sign-off] Datadog: monitors `318683760` (`[FUSE][Shopify Connector] Confirmation
  Source Mismatch — prod`) and `318683764` (dev) exist, `managed-by:terraform`, notifying
  `@team-bifrost @slack-bifrost-notifications` (AC 5). Query is
  `fuse.confirmation.unroutable{reason:source_mismatch,environment:prod}` (dev copy: `environment:dev`). That is the right metric:
  the service now emits on the shared `fuse.*` catalogue (`service:shopify-connector` shows
  `no_connectors` 266 and `use_case_inactive` 18,613 over 7 days), and
  `shopify_connector.confirmations.unroutable` has no data in 7 days. Zero `source_mismatch` in prod
  over 7 days, as the filter predicts. Both monitors read `No Data`, the healthy state for this
  counter.

## Decisions & deviations

- **2026-09-06 — increments 5 and 6 shipped together in one PR (#254), and the increment-6 gate had
  been open since the day this plan was written.** This plan recorded FUSE-1052/1053 as "snap-adapter
  PR #194, open" on 2026-09-02; #194 merged at 10:31 that morning and reached prod at 16:24. Nobody
  re-checked, and Jira still showing both tickets *In Progress* kept the stale belief alive for four
  days. Lesson: re-verify an upstream gate against GitHub/merge-base, not Jira, before repeating it.
  With 6 unblocked the 5→6 ordering inverts — 6 is what stops foreign-channel confirmations arriving,
  so shipping 5 alone was the riskier order; together they are safe. Harry, 2026-09-06.
- **2026-09-06 — no prod deploys until the ticket passes QA.** Proposed approving #239's held
  `terraform-prod` gate to read live `source`/`broadcast` volume before building 5+6; Harry rejected
  it outright — prod is downstream of QA, never an instrument for finishing development. Everything
  needed was verifiable in dev (both #239 and snap #194 were already there). The gate stays held.
  Recorded as a standing rule in agent memory (`feedback_no_prod_deploy_before_qa`).

- **2026-09-02 — monitors live in one repo, not per service (reverses this increment's placement
  decision).** `gfs-bifrost/observability` was created the same day to hold Fuse's Datadog
  dashboards and monitors as Terraform, and Harry's call was to move this monitor there rather
  than leave the fleet's first monitor-as-code as a per-service precedent. The mechanical trap
  worth remembering: **removing the resource and its provider in one commit fails the plan
  outright** — `Invalid provider configuration ... requires explicit configuration` — because
  Terraform needs a configured provider to plan the destroy of a resource still in state. The
  provider has to outlive the resource by exactly one apply.
- **2026-09-02 — review round on #239 (Harry, 3 comments), first two addressed in `ec42084`.**
  (1) *"does this duplicate existing globals? these should be in their own files"* — yes it did:
  `source: "shopify"` was declared or inlined in **four** places (`adapters/pubsub/pubsub.service.ts`,
  both failure publishers). Hoisted to a single `src/constants.ts` as `BIFROST_SOURCE`.
  It sits at the src root rather than `adapters/pubsub/constants.ts` deliberately — core publishers
  read it, and `no-core-to-adapters` is a **tracked depcruise warn baseline**, so putting it under
  adapters would have added a violation. The confirmation use case/stage moved to
  `core/confirmations/constants.ts`, matching the per-module `constants.ts` convention already used
  in six places. (2) *"let's ensure that we drive these via existing tfvars"* — monitor tags now
  `concat(var.datadog_monitor_tags, ["service:${var.project_name}"])` with the shared tags in
  `global.tfvars`; the alert handle is a per-env tfvar (`prod` = `@team-fuse`, `dev` = `""`), which
  also removed the `var.env == "prod"` conditional from the resource; and the metric prefix is
  derived as `replace(var.project_name, "-", "_")`, which is how dd-trace builds it.
- **2026-09-02 — (3) `@gfs-bifrost/pubsub`: recommended as its own PR, and only the ingest half.**
  Harry asked whether now is the time. Findings: the **ingest** half (`PubSubIngestor`) is a clean
  swap but drags a lockstep change to the exception filter + `exceptions/pubsub/` (the package
  throws its own `PubSubValidationError`/`PubSubDecodeError`, and those types drive the ack-vs-retry
  decision on the very route this PR re-routes), plus a `types` pin bump — this app resolves
  `9.3.0` while `pubsub@0.4.1` depends on `9.4.1`, and with no workspace override that means a
  second nested copy of `types` (the exact trap fapi documented). The **publish** half should
  **not** move: `PubSubRouter.getTopic` calls `pubSubClient.topic(name)` with **no batching
  options**, where this service deliberately passes `{ batching: PUBLISH_BATCHING }` (1000 msgs /
  10ms) and comments that batching only engages on a reused Topic — swapping would silently drop
  client-side publish batching on a per-order publish path. The router also takes caller-supplied
  metadata where this service derives it from the CLS correlation context. So: ingest yes (separate
  PR), publish not until the package can batch — worth raising with the platform side.
- **2026-09-02 — increment 4's monitor metric in this plan was wrong; corrected against live
  Datadog.** The plan said `fuse.confirmation.unroutable`. That metric exists but is emitted
  **only by fapi (`rest_connector`/`api-gateway`) and sftp-connector** — shopify-connector has not
  migrated to the shared `@gfs-bifrost/observability` catalogue and still emits via its local
  `METRIC` map over dogstatsd. The real metric is **`shopify_connector.confirmations.unroutable`**,
  tagged `reason` and `environment`. Verified: a query on the plan's name returns series scoped to
  the other two services only; the real name returns `environment:prod,reason:no_connectors` with
  an `.as_count()` total of **2,594 over 7d**, which agrees with the ~2,548 `No routable connector`
  log warns in the same window — so the metric is reliable enough to monitor on. (First attempt
  read `total=1` because the query omitted `.as_count()` and was summing a rate, not a count — not
  metric loss.)
- **2026-09-02 — the Datadog credentials for increment 4 exist; only the CI wiring is an open
  question.** `DATADOG_APP_KEY` is present in `~/.secrets` and validates against the management API
  (`GET /api/v1/monitor` → 200, 175 monitors, US1 `datadoghq.com`, paired with the GFS
  `DATADOG_API_KEY` — so a monitor created with it lands in the org where the fleet's existing
  monitors live, not the ILG one the sidecar also dual-ships to). The provider's `api_key` half
  needs no new plumbing: `shopify-connector-manual-deploy.yaml:41-42` already passes
  `secrets.DATADOG_API_KEY` into the terragrunt apply as `datadog_api_key`. **Open:** a Datadog
  application key is user-scoped, so wiring the one in `~/.secrets` into shared CI bakes a personal
  credential into the deploy path and it dies with that account — a service-account key is the
  right thing for CI. Raised with Harry rather than decided here.

## Learnings
<!-- Promoted 2026-10-05 at sign-off: resolver tenancy and purchase_order scope → architecture.md
"Confirmation routing"; connectorId's two meanings → operations.md correlation fields; PURDYFIGG
canary, pubsub.tf CRLF, required env vars, config PATCH booleans, provider-outlives-resource →
known-context.md. Already covered, so cleared: red checks (known-context #secops-nightly + org
CLAUDE.md), monitors in gfs-bifrost/observability (operations.md). The rest are in Handback. -->

## Handback
Learnings that were true when written but are no longer true, or never got settled. Checked
2026-10-05 against `origin/main` `5c28e8d` and live prod.

- **"Every confirmation consumer receives every channel's confirmations (subscriptions filter on
  `recordType` only)" — no longer true for shopify-connector.** Increment 6 widened its prod
  subscription to `source = "shopify" OR broadcast = "true"`, so other channels' confirmations stop
  at the broker. It may still hold for other consumers; not checked here. Note that the code
  comment above `selectTargets` (`shopify-sales-order.service.ts:710`) and the prod monitor's
  message text both still say the subscription filters on `recordType` alone. Both are stale. Not
  fixed here (code and the observability repo are out of scope for sign-off).
- **"Metrics are `shopify_connector.*`, not on the shared `fuse.*` catalogue" — false now.** The
  service moved onto `@gfs-bifrost/observability`'s catalogue; the unroutable counter is
  `fuse.confirmation.unroutable` with `service:shopify-connector`, and the old name has had no data
  for 7 days. `operations.md` already says this. The log-service-vs-metric-prefix mismatch no longer
  applies to this counter.
- **"shopify-connector has zero `confirmation_data_failure` wiring" — false now.** This plan added
  it (`ConfirmationFailurePublisher`, topic env var, IAM binding), and FUSE-1238 extended it.
  `architecture.md` documents it.
- **The `@gfs-bifrost/types@9.3.0` `PubSubEventSchema` contradiction was never resolved, and is now
  moot here.** The app pins `@gfs-bifrost/types` `10.9.0`, past the 9.3.1 fix. Whether real push
  envelopes ever carried both casings was not established.
- **The mechanism named in the correlation learning is stale.** `CorrelationIdMiddleware` /
  cls-hooked / `setCorrelationDetails` were replaced by the observability SDK's `Correlation.set`.
  The point of the learning still holds and was promoted to `operations.md`.
