---
ticket: FUSE-1056
title: Resolve confirmation webhook target by connectorId
service: fapi
status: complete
created: '2026-08-25'
updated: '2026-10-05'
repo: /home/hjf/code/fuse/fapi
worktree: /home/hjf/code/fuse/fapi/.claude/worktrees/fuse-1056-api-connector-routing
branch: hjf/fuse-1056-api-connector-routing
base: origin/master
base_sha: 9af4721c8
pr: '123'
tags:
- waypoint
- plan
---
# FUSE-1056 — Resolve confirmation webhook target by connectorId

## Intent
fapi's confirmation-webhook egress currently broadcasts every confirmation to every
active, webhook-configured REST connector on the business (`ConfirmationService.routeConfirmations`, no connectorId awareness at all). FUSE-1056 wants it to resolve
the one originating connector by `connectorId` and fire only there, falling back to
broadcast only when explicitly told to (`broadcast="true"`) or when no connectorId is
known. Full ticket scope (Terraform `source`/`broadcast` subscription filtering, PO/SO
onto the cross-entity vein) is sequenced behind sibling FUSE-927 tickets still in
progress (FUSE-1052/1053/1054) — this plan builds everything that isn't blocked by them
and marks the rest explicitly deferred.

## Acceptance criteria
- A confirmation carrying `metadata.connectorId` is forwarded only to that connector — for
  every confirmation type currently routed through `ConfirmationService` (RGA, pick, pack,
  work_order_confirmation, finished_good_receipt, **and PO/SO**: decided 2026-08-25, see
  Decisions — PO/SO's existing legacy topics already carry `metadata.connectorId` per
  FUSE-834, so they get this routing as a side effect of increment 2, ahead of their own
  cross-entity migration).
- An unresolvable `connectorId` (not found / inactive / no webhook configured) publishes
  a `confirmation_data_failure` distinguishable as such, plus a metric — never broadcasts.
- A confirmation with no `connectorId` keeps today's broadcast-to-all — no regression.
- Single-connector customers see no behaviour change.
- Terraform `source`/`broadcast` filter widening — **deferred**, tracked as increment 3,
  gated on FUSE-1052/1053 shipping to prod (see Assumptions).
- New PO/SO cross-entity subscriptions — **explicitly out of scope**, per the ticket's own
  text ("Legacy PO/SO subscriptions stay in place until the decommission ticket").

## Affected boundaries
- `code/src/services/pubsub-schemas.ts` — `BifrostBulkMessageSchema` now re-exported from
  `@gfs-bifrost/types` instead of hand-rolled locally (fixes the strip; see Decisions —
  **not** via `@gfs-bifrost/pubsub`, that path was tried and reverted)
- `code/src/services/pubsub-ingest.service.ts` — new public `parseEnvelope()`, factored out
  of `ingestEvent()`'s existing envelope-parse step (no behaviour change for existing callers,
  including `config-event.controller.ts`)
- `code/src/http/controllers/confirmation.controller.ts` — reads `attributes.broadcast` via
  `parseEnvelope()`, logged (not yet wired into routing — that's increment 2)
- `code/src/services/confirmation.service.ts` — `routeConfirmations` (core change, increment 2)
- `code/src/services/pubsub-emitter.ts` — reuses existing `emitConfirmationFailure` unchanged, no
  signature change (see Decisions — the planned `@gfs-bifrost/observability` bump turned out
  unnecessary)
- `iac/projects/api-gateway/pubsub.tf` — deferred increment, not touched until the gate clears
- Explicitly **not touched**: `code/src/http/controllers/config-event.controller.ts` — shares
  `PubSubIngestService`/`PubSubDecodeException` with the confirmation flow; the `parseEnvelope()`
  extraction is behaviour-preserving for it, no further change needed there

## Assumptions & uncertainty
- **Confirmed by reading source (the actual blocker, not mentioned in the ticket):** fapi's
  own `BifrostBulkMessageSchema` (in `pubsub-schemas.ts`) hand-rolls `{customer, correlationId,
  timestamp}` instead of reusing a shared schema, so `connectorId`/`source`/`recordType`/
  `recordId` are silently zod-stripped on every confirmation decode today — the FUSE-794 strip
  class, alive in this exact path. No connectorId routing is possible until this is fixed.
- **Tried, and reverted — see Decisions 2026-08-25:** `@gfs-bifrost/pubsub` (0.4.0) looked like
  a clean fix (its `BifrostBulkMessageSchema` composes `@gfs-bifrost/types`'s full
  `BifrostMessageMetadataSchema`, and its `parseEnvelope()` already exposes `message.attributes`)
  but its envelope schema is broken for real traffic — see Decisions. Landed instead: pull only
  the clean `BifrostBulkMessageSchema` factory from `@gfs-bifrost/types` (a different file,
  unaffected by the bug) into fapi's own local, correct envelope handling, and add
  `parseEnvelope()` to fapi's own `PubSubIngestService` for the attributes need. Same outcome
  (strip fixed, attributes readable), no new dependency, no exception-filter changes needed.
- **Scoped deliberately narrow:** `config-event.controller.ts` (the config-revision consumer)
  shares `PubSubIngestService`/`PubSubDecodeException`/`pubsub-schemas.ts` with the confirmation
  flow. The `parseEnvelope()` extraction is a pure refactor of `ingestEvent()`'s existing logic
  (verified: its own tests plus the full suite stayed green), so it needed no change at all.
- **Confirmed by reading source:** `ConfigApiAdapter.getConnectorsByBusinessId` already
  resolves `ConnectorType.REST` only — no extra type-filtering needed to scope resolution to
  "the customer's API/webhook connectors."
- **Decided 2026-08-25 (Harry):** no `reason` field exists on `BifrostFailure`/
  `FailureAttributes` in `@gfs-bifrost/types` (8.4.0) today, despite FUSE-1053/1056's ticket
  text speaking of `reason="connector_unresolvable"` / `reason="no_originating_connector"` as
  if it were a formal field. Confirmed: express it without a `@gfs-bifrost/types` change — see
  the next bullet for exactly where it landed once `business_rule` was settled.
- **Decided 2026-08-25 (Harry):** failure classification is `type: "business_rule"`, not
  `"dependency"`. Reasoning discussed and confirmed: `connector_unresolvable` fires from a
  lookup against fapi's own already-fetched connector list coming up empty or inactive — no
  network call happens (unlike the existing `connector_webhook` delivery-failure precedent,
  which really did POST and fail). That's a business/config-state check, matching
  `BusinessRuleFailureError`'s shape (`{ type: "business_rule", rule: string }`, no `retryable`
  field) — a bare Pub/Sub redelivery can't fix a bad connectorId, only a config change or a
  manual replay can, which fits the no-automatic-retry shape of a business-rule failure better
  than a dependency failure's `retryable: boolean`. Consequence for the earlier `errors[].code`
  plan: `BusinessRuleFailureError` has no `code` field at all (only `DependencyFailureError`/
  `InfrastructureFailureError` do) — landed as `errors[].rule = "connector_unresolvable"`
  instead, the field the type actually offers for this purpose.
- **Found while implementing increment 2, avoided a cross-repo dependency:** the plan's
  increment 3 assumed `reason`/tag values passed to `metricsService.increment(...)` had to be
  members of `@gfs-bifrost/observability`'s `CONFIRMATION_UNROUTABLE_REASON` enum, requiring a
  package bump. Checked the SDK's actual `increment(name: string, value?: number, tags?:
  MetricTags): void` signature — tag values are plain strings, not constrained to that enum at
  the call site; `classifyUnroutable`'s return type is merely how the *existing* branches happen
  to type their own return value. Used the literal `"connector_unresolvable"` directly (comment
  ties it to the convention) — same Datadog outcome, no pkg-node PR/publish/pin-bump cycle
  needed. Formalising it into the shared enum is optional future cleanup, not required.
- **Decided 2026-08-25 (Harry):** connectorId-resolution is entity-agnostic in
  `routeConfirmations` — once increment 1 fixes the metadata strip, PO/SO's *existing legacy*
  topics (which already carry `metadata.connectorId` per FUSE-834's completed AC, which names
  "PO, SO, RGA, Pick/Pack" explicitly) get real single-connector routing immediately, ahead of
  their own cross-entity migration. Confirmed: let it apply — strictly safer than today's
  unconditional broadcast, and extends the ticket's benefit to PO/SO as a deliberate side
  effect rather than an oversight.
- Assumption: absence of `connectorId` (today's universal case, pre-FUSE-834-cutover orders,
  and the pre-FUSE-1053 no-origin case) keeps unconditional broadcast — fail-open, matching
  the org's anti-silent-drop stance and trivially satisfying "single-connector customers see
  no change." Not explicit in the AC; this is the deliberate interpretation.
- Not yet re-verified against a live message: that `snap-queue-polling-service` actually
  stamps `metadata.connectorId`/`metadata.source` on confirmation_ready today (FUSE-834 is
  Done; FUSE-1052's own ticket text asserts it's already true). Re-check in waypoint-test/work
  via a real Datadog/Pub/Sub sample before relying on it.
- Verified: sibling in-flight branches exist — `hjh/fuse-1054-po-so-cross-entity-confirmations`
  (fapi, sftp-connector, snap-adapter) and `ndk/fuse-1052-1053-broadcasting-confirmations`
  (snap-adapter). Diffed fapi's FUSE-1054 branch against `origin/master`: it touches only
  `pubsub-emitter.ts` (confirmation_made dual-publish for PO/SO) plus portal/CI files — no
  overlap with the files this plan touches. Low collision risk, but re-diff before merging if
  either branch lands first.
- Not verified: the snap-adapter FUSE-1052/1053 branch's actual `attributes` shape (only
  commit subjects were read, not the diff). If this plan is actioned before that branch
  merges, re-check the real `source`/`broadcast` attribute names/values against what's
  assumed here before building increment 3.

## Increments
- [x] 1. Fix the metadata strip and expose `broadcast`. `pubsub-schemas.ts`'s
  `BifrostBulkMessageSchema` now re-exports `@gfs-bifrost/types`'s factory (composed from
  `BifrostMessageMetadataSchema`) instead of a hand-rolled narrow object — zero call-site
  changes needed in `confirmation.controller.ts` (same import name, same signature).
  `PubSubIngestService` gained a public `parseEnvelope()`, factored out of `ingestEvent()`'s
  existing envelope-parse step (no behaviour change). The controller calls it to read
  `attributes.broadcast` and logs it (not yet wired into routing — increment 2). No new
  dependency, no exception-filter changes — see Decisions for why the original plan (adopt
  `@gfs-bifrost/pubsub`) was reverted. — verified: new test asserts `metadata.connectorId`/
  `source` survive decode and reach `routeConfirmations`; new test asserts `attributes.broadcast`
  is read and logged; full suite (295 tests, 24 files) green; `build:check` clean; `lint`
  clean on every touched file.
- [x] 2. In `ConfirmationService.routeConfirmations`: `broadcast` added as a 6th parameter
  (threaded from the controller). When `broadcast` is true or `metadata.connectorId` is absent,
  target every `candidateConnector` (unchanged prior behaviour). Otherwise target only the
  candidate whose `connectorId` matches. When that resolves to zero targets, emit the
  `fuse.confirmation.unroutable` metric with `reason: "connector_unresolvable"` and publish a
  `confirmation_data_failure` (`toFailureUseCase(type)`, `errors: [{ type: "business_rule", rule:
  "connector_unresolvable", problem }]`, `connectorId` set to the unresolved id, `transaction`),
  then return `false` without forwarding. `tryEmitConfirmationFailure` and the new
  `tryEmitConnectorUnresolvableFailure` now share one `publishConfirmationFailure` helper (same
  publish/metric/log, different `errors` shape) rather than duplicating it. — verified: 3 new
  unit tests (resolve-to-one, broadcast overrides a set connectorId, unresolvable → business_rule
  failure + metric + no forward); all 40 pre-existing `routeConfirmations` tests updated for the
  new parameter and still pass unmodified in behaviour (`broadcast: false` matches today's
  default); full suite 298/298; `build:check` and `lint` clean on every touched file.
- [x] 1b. **Adopt `@gfs-bifrost/pubsub`'s `PubSubIngestor`** (2026-09-01), completing what
  increment 1 deferred on 2026-08-25. Prerequisite cleared: `@gfs-bifrost/pubsub` republished as
  0.4.1 today, now correctly resolving `@gfs-bifrost/types@9.4.1` (was hard-pinned at an exact
  `7.1.0` — see the pkg-node Decisions entry below for why publishing `types` 9.3.1 alone hadn't
  been enough). Swapped `PubSubIngestService`/`pubsub-schemas.ts`/`PubSubDecodeException`
  (deleted entirely) for the package's `PubSubIngestor`/`PubSubValidationError`/
  `PubSubDecodeError` in both push consumers (`confirmation.controller`, `config-event.controller`
  — the latter untouched by increments 1/2, now updated too since it shares the same ingest
  service). `PubSubIngestor` is stateless — registered via a factory provider in `app.module.ts`.
  `AllExceptionsFilter`/`isAckedException` updated in lockstep to recognise the package's two
  exception types (ack/204, never retry — same semantics as the retired local exception).
  — verified: `build:check` clean, 304/304 tests passing, lint clean (14 pre-existing
  `noNonNullAssertion` warnings, unrelated, untouched). **Live dev evidence (2026-09-01,**
  `manual-deploy.yaml` **run** `33519641909`**):** published a valid RGA confirmation to
  `bifrost.dev.confirmation_ready.v1` for business GADG — decoded correctly via the new
  `PubSubIngestor`, resolved the connector, attempted forward, fell through to the existing
  delivery-failure path exactly as before, 204 ack. Published a deliberately invalid record
  (`{foo:"bar"}`) on the same route — threw `PubSubValidationError` (`Record validation failed`,
  correct Zod issues for missing `identifiers`/`lines`, payload captured), logged via the new
  filter branch, acked 204 in 11.7ms (no retry storm). Also published a minimal valid
  `config_revision` event (`{resources:[]}`) to `bifrost.dev.config_revision.v1` — 202 Accepted,
  confirming `config-event.controller`'s swap works too. fapi's own `CLAUDE.md` updated in the
  same change (named the retired local files).
> SUPERSEDED 2026-09-14 — blocker (b) below is settled and the scope is now SEVEN subscriptions,
> not five. FUSE-1059 Inc 1 performs an ATOMIC swap of fapi's PO/SO ready subs (add cross-entity
> `recordType = "purchase_order"` / `recordType = "goods_out_confirmation"` + remove the two legacy
> subs in one apply), deliberately recordType-only so nothing narrows inside the apply that deletes
> the fallback. There is therefore no double-delivery window, and by the time this increment runs
> the file carries seven recordType-only cross-entity ready subs — widen all seven. Order on the
> shared `api-gateway/pubsub.tf`: FUSE-1059 Inc 1 first, this increment second.

- [x] 3. **UNBLOCKED 2026-09-02 15:30 — the producer is now in prod.** Widen the 5 existing
  cross-entity confirmation subscriptions' Terraform filters (rga, pick, pack,
  work_order_confirmation, fgr_confirmation) from `recordType = "X"` to `recordType = "X" AND
  (source = "api" OR broadcast = "true")`. Applying this before the producer stamps those
  attributes silently zeroes fapi's delivery for all five record types — a Pub/Sub filter on an
  attribute that never exists matches nothing. That was the block, and it is now cleared:
  * FUSE-1052/1053 (`a002534`) was parked at snap-adapter's `terraform-prod` gate as run
    `33619912433` — one of ~12 waiting poller runs, with prod sat on `dedac84` from 2026-08-24.
  * Gate approved; apply completed **`1 added, 1 changed, 0 destroyed`**, matching the reviewed
    plan exactly (pubsub publisher IAM on `confirmation_data_failure` created; Cloud Run image,
    `CONFIRMATION_DATA_FAILURE_TOPIC_NAME` env and the container-dependencies annotation changed
    in place). Prod moved forward 6 commits, also carrying FUSE-866, FUSE-871, FUSE-1009 and
    FUSE-1050.
  * Live `snap-polling-service-prod` now serves
    `snap-queue-polling-service:prod-a0025343b4de08e716c87513efa53070da316fa9`; the revision booted
    15:28:30 and was polling normally by 15:30:05 across all three business groups, with **zero
    errors** in the window.
  **Pre-condition CLEARED 2026-09-04** — the plan's last unverified step (that real prod
  confirmation traffic actually carries `source`/`broadcast`, not just that the producer booted)
  is now closed. `fuse.confirmation.manual_origin_broadcast` — the metric FUSE-1053 introduced,
  which only fires on the new code path and only when the publisher stamps `broadcast="true"` —
  has emitted continuously under `environment:prod, service:snap-polling-service` from
  2026-09-02 16:00Z onward, across PURDYFIGG, STUBBLE, BYOMA, WILDSMITH, LEMONADE and GADG.
  Prod has since moved past `a002534` to `95bdc57`. **Tagging gotcha:** these series carry
  `environment:prod`, **not** `env:prod` — the `env` tag reads `serverless`, so an `env:prod`
  scope returns nothing and a monitor written that way would silently never fire.
  **Two things still gate the filter work, both decisions rather than unknowns:** (a) `filter` is
  `ForceNew` — delete-then-create with no `create_before_destroy`, so each subscription's backlog
  is discarded and anything published in the gap never arrives; wants a planned quiet-window
  apply. (b) The PO/SO **add-vs-swap** call (shared with FUSE-1055) — with FUSE-1054 dual-publish
  merged (`d0c7b6a`, snap-adapter#220, 2026-09-04), *adding* filtered PO/SO subscriptions while
  the legacy pair stays means both push the same endpoint and each confirmation is delivered
  twice. Settle that before touching the filters.
  — verify: `terragrunt plan` shows only the filter change; a live confirmation with
  `broadcast=true` or `source=api` still reaches the endpoint post-deploy; a `source=sftp`-only,
  non-broadcast confirmation does **not**.
  **Evidence:**
  - 2026-10-05 [sign-off] Shipped in three PRs, all merged: fapi#134 (`bc93eea`, PO/SO,
    2026-09-16), fapi#137 (`e3d1b9a`, pick/pack/WOC/FGR, 2026-09-16) and fapi#159 (`50578d2`, RGA,
    2026-10-01 — reversing #137's call to leave RGA `recordType`-only). The landed value is
    `source = "rest"`, not the `source = "api"` this increment was written with.
  - 2026-10-05 [sign-off] `gcloud pubsub subscriptions list --project bifrost-prod-global1`: all
    seven `api-gateway.prod.confirmation_ready.{po,so,rga,pick,pack,woc,fgr}.v1.sub` filters read
    `(attributes.recordType = …) AND (attributes.source = "rest" OR attributes.broadcast = "true")`,
    matching `iac/projects/api-gateway/pubsub.tf` on `origin/master` (`907bcb2`). So the
    `sftp`-only, non-broadcast case is excluded at the subscription by construction.
  - 2026-10-05 [sign-off] Datadog, prod, last 3 days: `service:rest_connector` still receives and
    acks confirmations on `/events/v1/confirmation/ready/*` (811 `204`s, last at 09:24Z today).
    `fuse.confirmation.unroutable{service:api-gateway,environment:prod}` over 7 days shows only
    `no_connectors` (708) and `use_case_inactive` (1009), which are broadcasts reaching businesses
    with no REST connector, and **zero** `connector_unresolvable`. That was the PURDYFIGG
    Shopify-named case the filter was meant to stop.
  - 2026-10-05 [sign-off] Not re-read: the `terragrunt plan` output on #134/#137/#159. Both PR
    bodies left their dev-evidence checkboxes unticked. The live prod filters above are the proof
    relied on instead.
- [x] 4. **Datadog monitor on `connector_unresolvable`** — done as
  [observability#3](https://github.com/gfs-bifrost/observability/pull/3) (draft), **not** in fapi's
  IaC. Two resources, prod notifying and dev not, in `monitors.fapi.tf`.

  > **Correction to an earlier note in this plan.** It recorded that shopify-connector #239's
  > monitor had been "reverted at source" and inferred the team had abandoned monitors-as-code.
  > That inference was wrong. Commit `1180207` ("drop the datadog provider now nothing here manages
  > a monitor") removed the provider from #239 because the monitor **moved** to the new
  > `gfs-bifrost/observability` repo, where `confirmation_source_mismatch_{prod,dev}` now live,
  > committed on `main`. The conclusion "don't put it in fapi's IaC" survives, but for the opposite
  > reason: that repo's first rule is *"Fuse's Datadog dashboards and monitors live here, not in
  > service repos — if you find one in a service repo, that is the thing to fix, not to copy"*,
  > because two Terraform states managing one Datadog resource silently fight. This also retires
  > the `datadog_app_key` / `tf_var_extra_3` prerequisite: fapi needs none of it.

  These four facts were verified live in Datadog on 2026-09-02, and each is a way the naive mirror
  of shopify's monitor would have failed silently:
  * **The metric name differs in prefix *and* pluralisation.** fapi emits
    `fuse.confirmation.unroutable`; shopify emits `shopify_connector.confirmations.unroutable`.
    Copying #239's derived name (`${replace(project_name,"-","_")}.confirmations.unroutable`) would
    yield `api_gateway.confirmations.unroutable`, which does not exist — a silent no-op monitor.
  * **The metric is shared between services and must be scoped.** Its `service` tag carries
    `api-gateway,rest_connector` on fapi's series and `sftp-connector,sftp_connector` on
    sftp-connector's. Unscoped, this monitor would alert fapi's team on sftp-connector's unroutable
    confirmations. Filter `service:api-gateway`.
  * **The metric as a whole is *not* zero in prod, so the `reason` filter is what makes this a
    should-read-zero signal.** Live 30-day prod counts on fapi's series: `no_connectors` ~66,
    `no_active_connectors` ~20, `no_confirmation_enabled_connectors` ~13. Only
    `reason:connector_unresolvable` is the anomaly case — a named `connectorId` that resolved to
    nothing, to something inactive, or (since `f2342d1`) to **another business's** connector, which
    makes it closer to a cross-tenant security signal than shopify's volume probe. It currently
    reads ~4.6 in dev and **zero in prod**, as expected: the routing that emits it is still an
    unmerged draft.
  Resulting query (one monitor per environment):
  `sum(last_5m):sum:fuse.confirmation.unroutable{reason:connector_unresolvable,service:api-gateway,environment:<env>}.as_count() >= 1`
  * **Copy these deliberate choices from #239**: `notify_no_data = false` — load-bearing here,
    since prod legitimately has no data for this reason today; `critical = 1`; scope on
    `environment:`, never `env:` (confirmed — the sidecar pins `env:serverless`); only the prod
    copy carries an alert handle. Deviate on the space aggregator: `sum:` not `avg:`, since the
    question is how many occurred across revisions, not their average.
  — verified: `terragrunt plan` (terraform 1.9.0 / terragrunt 0.50.8, matching CI) reads
  **2 to add, 0 to change, 0 to destroy** — only the two monitors, nothing else in the estate
  moves; `terraform fmt -check -recursive` clean; CI `terraform-plan` passes on the PR. The dev
  query returns a **real series** (23 hits / 30d, buckets 2,8,3,1,9), which is what rules out the
  match-nothing failure above.
  **Still unproven, and cannot be pre-merge:** the `OK → Alert → OK` transition that
  `observability/CLAUDE.md` requires of a new monitor — a monitor cannot be driven until it
  exists, and applies there happen only through CI on merge. Drive the dev signal once it applies.
  The **prod** copy stays unproven until #121 ships, since the code emitting its reason is not in
  prod; that is expected, and is why `notify_no_data = false` is load-bearing rather than
  cosmetic.

## Verification
- Increment 1 (2026-08-25): `pnpm run build:check` clean; `pnpm test` — 295/295 passing across
  24 files (full suite, not just the touched files); `pnpm run lint` — no warnings in any file
  this increment touched (the 15 pre-existing `noNonNullAssertion` warnings elsewhere are
  untouched, not introduced). New coverage: `confirmation.controller.spec.ts` — a test asserting
  `metadata.connectorId`/`source` survive decode and reach `routeConfirmations`'s call args, and
  a test asserting `attributes.broadcast` is read off the envelope and logged.
- Increment 2 (2026-08-25): `pnpm run build:check` clean; `pnpm test` — 298/298 passing across
  24 files; `pnpm run lint` clean on every touched file. New coverage in
  `confirmation.service.spec.ts` (`describe("connectorId-based resolution (FUSE-1056)")`): named
  connectorId forwards to exactly one connector out of two candidates; `broadcast=true` forwards
  to both candidates even with a connectorId set; an unresolvable connectorId forwards to none,
  publishes a `business_rule`/`connector_unresolvable` failure with the right `connectorId`, and
  emits the `connector_unresolvable`-reason metric. All 23 pre-existing `routeConfirmations` call
  sites (spanning both spec files) updated to pass `broadcast: false` and pass unmodified,
  confirming today's broadcast-to-all behaviour is unchanged when no connectorId/broadcast signal
  is present.
- **Live dev evidence (2026-08-26).** Deployed to dev (`manual-deploy.yaml` run `32958291853`,
  `docker-push-dev`/`terraform-apply-dev` both succeeded, headSha `084053d`). `fuse-mocker`'s
  MCP tools (`mock-send`/`mock-generate`) 404 in this environment — its Next.js UI app has no
  `/api/v1/messages`/`/api/v1/generate` routes, consistent with the fuse-mocker-go migration
  having moved the API to a separate Go app the MCP tool's configured URL wasn't updated for;
  a fuse-mocker tooling issue, not a fapi one. Worked around it: published two real
  `return_goods_authorization` confirmations directly onto `bifrost.dev.confirmation_ready.v1`
  (`gcloud pubsub topics publish`, `attributes.recordType=return_goods_authorization`) for
  business `GADG`, which has exactly one active, webhook-configured REST connector
  (`conn_faef29654e044305ba642ef0201f00a7`, "Primary API", `webhookUrl: https://example.com`).
  Confirmed via `gcloud logging read` against the live `api-gateway-dev` Cloud Run service
  (bypassing Datadog, whose log pipeline wasn't returning either correlationId in this window —
  a separate, unchased gap):
  - **`metadata.connectorId` set to the real connector** (`correlationId: fuse-1056-resolve-test`):
    "Forwarding confirmation to connector" fires exactly once, for that connector; three retry
    attempts against `https://example.com` all fail (expected — it's not a real webhook
    receiver), which correctly falls through to the *existing* dependency-failure path
    (`Published confirmation_data_failure event`) — proving the strip fix, the resolve-to-one
    logic, and the pre-existing delivery-failure path (now sharing `publishConfirmationFailure`)
    all work together on real traffic, not just in unit tests.
  - **`metadata.connectorId` set to an id that resolves to nothing**
    (`correlationId: fuse-1056-unresolvable-test`, connector cache now warm from the first send):
    zero "Forwarding confirmation to connector" lines — no forward attempted — and the exact new
    log line fires verbatim: *"Confirmation could not be routed: connectorId did not resolve to
    an active, webhook-configured connector"*, structured fields `connectorId:
    conn_does_not_exist_1056`, `businessId: GADG`, `type: return_goods_authorization`, followed
    by "Published confirmation_data_failure event" / "Emitted confirmation_data_failure event".
  - Both cases ack cleanly (`POST .../return_goods_authorization - 204`) — no retry storm either
    way, matching the ack-not-retry design.

## Decisions & deviations
- **2026-09-08 — PR relinked from closed #121 to merged #123; increments 1/2/1b are now live on
  master.** #121 was closed without merging (cause not captured in this plan at the time); the same
  content was reopened as `fapi#123` and merged today via `pr-clear` (squash, `4b44377`) — auto-deployed
  prod for api-gateway. `wp doctor` flagged this as PR-DRIFT (plan pointing at a closed PR) rather than
  UNCLOSED, because the frontmatter `pr` field hadn't been updated to the PR that actually shipped.
  Jira `FUSE-1056` transitioned to **Ready for QA** in the same run. Status stays `active`, not
  `signed-off` — increment 3 (Terraform filter widening) is still open, gated on the add-vs-swap PO/SO
  decision recorded above; this plan isn't done, only its shipped increments changed which PR carries
  them.
- **2026-09-02 — closed a cross-tenant delivery hole in increment 2's own resolution path
  (commit `f2342d1`).** Found while planning the shopify-connector sibling (FUSE-1057) and
  reviewing what that plan should reuse from here. `resolveTargetConnector` resolved the named
  connector by id alone and guarded only on `isActive` + `webhookUrl`. Because
  remote-config's `resolveByConnectorId` is keyed on id with **no tenancy or type scoping** (see
  Learnings), a wrong or stale `connectorId` on the envelope that happened to name **another
  customer's active REST connector** would have forwarded this customer's confirmation to that
  customer's webhook — the `webhookUrl` guard only closes the foreign-*channel* case (an
  SFTP/Shopify connector has no `webhookUrl` to find), not the foreign-*tenant* one. Now compares
  the resolved connector's `businessId` against the confirmation's and treats a mismatch as
  unroutable alongside not-found/inactive. Harry's call (2026-09-02) to fix #121 directly rather
  than leave a review comment. Side finding: the spec's `makeRestConnector` factory never set
  `businessId` at all — every connector it built carried `undefined`, so the guard broke all 6
  connectorId-resolution tests until the factory was given a real default. — verified: 305/305
  tests (one new: a connectorId resolving to another business forwards to nobody), `build:check`
  clean, `lint` exit 0.
- **2026-09-01 — `pubsub` republished (0.4.1) then the `PubSubIngestor` swap completed; CI on
  #121 shows two unrelated pre-existing failures, not caused by this change.** `image_scan` and
  `image_scan_portal` both fail on `CVE-2026-14456` (`libcrypto3`/`libssl3`, HIGH) — an OS-level
  package in the shared Alpine base image, not an npm dependency. Confirmed pre-existing and
  unrelated by checking `master`'s own CI: `DevSecOps Scans` has been red on `master` itself
  since at least 2026-08-31 (two consecutive nightly runs), well before this branch existed —
  not something introduced by adopting `@gfs-bifrost/pubsub`. Left untouched — allowlisting a
  fresh CVE via `.trivyignore` is a separate triage decision, out of scope for this ticket.
  `mergeStateStatus` on #121 shows `UNSTABLE` because of this, not because of anything in this
  diff — build/lint/test/type-check are all clean.
- **2026-09-01 — attempted the `@gfs-bifrost/pubsub` swap Harry asked for now that pkg-node#211
  merged and `@gfs-bifrost/types` 9.3.1 published; stopped before touching code.** Verified
  against the real GitHub Packages registry (`npm view @gfs-bifrost/pubsub@0.4.0 dependencies`,
  authenticated): the **latest published** `@gfs-bifrost/pubsub` is still `0.4.0` — unchanged by
  #211 — and its manifest pins `"@gfs-bifrost/types": "7.1.0"` **exactly**, not a caret range
  (pnpm's `workspace:*`→registry conversion froze it at whatever `types` version was current when
  `pubsub` 0.4.0 was itself last published, months before 9.3.1). fapi's own direct
  `@gfs-bifrost/types` dependency is a proper `^9.3.0` range and resolves fine — but adopting
  `@gfs-bifrost/pubsub` would pull its own separately-resolved, nested `types@7.1.0` for its
  compiled `dist`'s internal use, since fapi's `code/` has no `pnpm-workspace.yaml` override to
  force a single resolved version. `pubsub`'s bundled `PubSubEventSchema` would still be the
  broken pre-9.3.1 one — publishing `@gfs-bifrost/types` 9.3.1 does **not** transitively reach
  `pubsub`'s consumers until `pubsub` itself is bumped and republished against it. Adopting today
  would buy nothing and add a duplicate stale `types` copy to the tree. **Did not implement the
  swap** — reported to Harry rather than proceeding on a premise that turned out false.
- **2026-08-26 — code review round on PR #121 (Harry, 5 blocking comments), all addressed in
  commit `3c041cf`:**
  1. "Received {type} confirmation event" log dropped from `info` to `debug`.
  2. Removed an explanatory comment on the `broadcast` attribute read in `confirmation.controller.ts`
     judged unnecessary given the code.
  3. Removed the added `broadcast`-override explanation from the `routeConfirmations` doc comment,
     kept the original `transaction` line.
  4. **`ConfirmationService.resolveTargetConnector` now resolves the named connectorId via
     `@gfs-bifrost/remote-config`'s `ConnectorBacklinkHandler.resolveByConnectorId`** (through new
     `ConfigApiAdapter.getConnectorByConnectorId` / `ConnectorRegistryService.getByConnectorId`)
     instead of filtering the already-fetched business-wide `candidateConnectors` list — see the
     matching Learnings entry for why this is the more correct primitive. The zero-total-candidates
     path (fetching the full business list, `CONNECTORS_FOUND` metric, `classifyUnroutable`) is
     unchanged; only the connectorId-narrowing branch was swapped. Added a new test for a
     resolved-but-inactive connector (a case the old client-side filter couldn't distinguish from
     "not found," both now correctly land on `connector_unresolvable`).
  5. **Re-opened and fixed the `@gfs-bifrost/pubsub` question rather than leaving it as a static
     Learning.** Filed and merged-locally-verified the upstream fix:
     [pkg-node#211](https://github.com/gfs-bifrost/pkg-node/pull/211). Did **not** re-adopt the
     package in this PR — #211 isn't merged/published yet, and swapping onto an unpublished fix
     would leave fapi on a broken dependency until it lands. Asked Harry on the PR thread whether to
     hold #121 for #211, or ship on the local implementation and swap as a fast-follow; no answer
     yet as of this entry.
- **2026-08-25 — reverted the `@gfs-bifrost/pubsub` adoption planned for increment 1; found and
  worked around a real bug in the shared package instead of shipping onto it.** While building
  it, every fixture decode failed with "Invalid PubSub event envelope." Root cause, confirmed by
  reading source: `@gfs-bifrost/types`'s `PubSubEventSchema`
  (`pkg-node/pkg/types/src/pubsub/schemas/pubsub-event.schema.ts`) requires **both**
  `messageId`/`publishTime` (camelCase) **and** `message_id`/`publish_time` (snake_case) present
  simultaneously on the same object. Real Google Cloud Pub/Sub push envelopes only ever send
  camelCase — there is no snake_case variant on the wire — so this schema can never validate a
  real message. `@gfs-bifrost/pubsub`'s `PubSubIngestor` re-exports this exact schema, so it
  inherits the defect. Had this shipped, every real confirmation push would have thrown, and
  with the exception-filter changes that increment also made (ack 204 on the package's
  `PubSubValidationError`), it would have been silently swallowed rather than retried — a total,
  silent outage of every confirmation webhook (RGA/pick/pack/WOC/FGR), exactly the FUSE-1011
  silent-drop class this epic exists to close, introduced at the center of the flow it's meant
  to fix. Caught by the new unit tests failing immediately, before any deploy.
  **Fix applied here:** reverted the package dependency and the exception-filter/`is-acked-exception`
  changes entirely (nothing throws the package's exception types anymore, so nothing needed to
  recognise them). Kept fapi's own local `PubSubEventSchema` (camelCase-only, correct) for
  envelope parsing, and pulled in only `@gfs-bifrost/types`'s `BifrostBulkMessageSchema` factory
  — a different file (`bifrost-message.schema.ts`), unaffected by the bug, and confirmed clean by
  reading it directly — for the metadata-strip fix.
  **Not fixed here, flagged for a separate pkg-node defect:** the `PubSubEventSchema` bug itself.
  It blocks any real consumer of `@gfs-bifrost/pubsub`'s `PubSubIngestor`/`ingestEvent`/
  `ingestBulkEvent`/`parseEnvelope` against real Pub/Sub traffic — worth its own ticket in
  pkg-node; out of scope to fix from fapi.

## Learnings
<!-- Promoted 2026-10-05 at sign-off. Exception acking in two places, never routing by
resolveByConnectorId alone, and workspace:* pins went to known-context.md ("Gotchas carried over
from FUSE-1056"). The PubSubIngestor decode path went to architecture.md (Egress step 1). PO/SO
getting connectorId routing for free was already covered by architecture.md step 4. -->

## Handback
- 2026-10-05 [sign-off] The Learning "fapi now follows the same pattern
  (`ConfigApiAdapter.getConnectorByConnectorId` → `ConnectorRegistryService.getByConnectorId`)" is
  no longer true. On `origin/master` (`907bcb2`), fapi has no `resolveByConnectorId` call at all.
  It loads the business's REST connectors through remote-config's
  `resolveWithUnresolved(businessId, ConnectorType.REST)` (remote-config 2.3.0, E8 fapi#166) and
  picks the named id from that list in `ConfirmationService.selectTargets`. Not promoted. The
  still-true part (the package's resolver is global, so don't route by it alone) is in
  known-context.md.
- 2026-10-05 [sign-off] The Learning that adopting `PubSubIngestor` was "a clean follow-up once
  #211 merges, not done in this PR" was overtaken by increment 1b (2026-09-01). fapi is now on
  `@gfs-bifrost/pubsub` `^0.5.0`. Only the current decode path was promoted.
