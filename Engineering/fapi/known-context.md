---
tags: [waypoint, fapi]
verified: '2026-08-24'
verified_paths: []
title: fapi — known context
---

# fapi — known context

## This repo's CLAUDE.md is unusually good — read it first

`CLAUDE.md` (not the README) carries a live standing instruction: any change
that contradicts it — endpoint, auth/tenancy model, topic wiring, env vars,
deploy setup, a "gotcha" — must update the doc in the *same* PR, before push.
It's treated as source of truth precisely because the README is explicitly
called out inside CLAUDE.md as stale (it omits the whole egress/confirmation
half and the config-revision consumer, and its env/topic lists are out of
date). When in doubt, trust CLAUDE.md and the code over README.md.

> SUPERSEDED 2026-10-05 — the "merged is not deployed" paragraph below: prod has run the flag-free gate (`isActive` + `webhookUrl`) since the August backlog cleared. The removal itself still stands.

## `confirmationsEnabled` — removed from `master`, but prod is still running the old gate

**Correction (2026-08-24):** an earlier version of this note, written the same day, claimed
`confirmationsEnabled` was live two-gate eligibility. That was verified against the main
checkout's local `HEAD` (`a10d855`, branch `hjf/fuse-868-work-order-confirmation-webhooks`) —
which turned out to be **12 commits behind `origin/master`** and predates the fix below.
Lesson: verify a claim about "current" fapi behaviour against `origin/master`, not whatever
happens to be checked out locally.

What's actually true: `fapi#113` / FUSE-1078 ("Stop gating REST confirmation delivery on
deprecated `confirmationsEnabled`", merged 2026-08-20) removed the flag as a routing gate
entirely — `confirmation.service.ts` on `origin/master` now filters only on
`config?.isActive === IngressStatus.ACTIVE` plus a configured `config?.webhookUrl`, with a
comment at the old gate site: *"confirmationsEnabled is deprecated as a routing gate — don't
reintroduce it."* The field itself was deleted from `ConnectorWithRetries` and
`ConnectorRegistryService`.

**But merged is not deployed.** fapi's prod `Deploy` workflow has had its `docker-push-prod`
job parked at the manual `terraform-prod` environment approval gate since 2026-08-19 (6 queued
runs as of 2026-08-24; last successful prod deploy was `3fdbb3ea` on 2026-08-13). So **prod is
still running the old two-gate `isActive` + `confirmationsEnabled` behaviour** while `master`
is not. When diagnosing a live REST-confirmation routing issue, check which of the two
behaviours is actually deployed before concluding — don't assume `master`'s behaviour is
prod's. See the parked-deploys note under Ownership below.

## `EntityType` vs `UseCase` vs `recordType` — three names, on purpose

fapi predates the org-wide `use_case` → `recordType` cutover (see the root
CLAUDE.md's "Record Kinds" section) and still uses the legacy identifiers
internally:

- `EntityType` — the five kinds that emit (`master-data`, `sales-order`,
  `purchase-order`, `return-goods`, `work-order`).
- `UseCase` — a deliberately-kept alias of `EntityType`, naming the API
  surface's use cases (what auth/tenancy key off) rather than the emission
  pipeline, even though today the two coincide.
- On the wire, the new convention is honoured: `create_record_request`
  carries `attributes.recordType`, and the confirmation route is
  `:recordType`-keyed.

Per the org rule: don't introduce new `useCase` identifiers here, and don't
mass-rename the existing ones outside a PR explicitly scoped to the cutover.

## Direct API submissions skip the mapping-default layer

SFTP/Shopify customers get missing fields filled in by their
`CONNECTOR_MAPPING` before a record is even built. A direct fapi submission
bypasses that entirely, and nothing in the create pipeline (fapi, dedupe,
snap-adapter) consumes config-service's `DEFAULT_MAPPING` fragment to fill
the gap — this is a known, unaddressed hole, not an oversight anyone has
missed. Validation stays permissive on purpose (most location/routing/
shipping fields are optional at the schema level) since the same schemas
serve connectors that *do* get defaults applied upstream. A thin API request
still returns `202 Accepted`; the gap surfaces later as a blank SNAP field or
an outright creation failure on `create_data_failure` — never in the API
response itself. See `README.md`'s field-requirements table for the specific
fields this bites (per-entity mandatory-in-SNAP fields, verified live against
a real business's dev config 2026-07-13).

> SUPERSEDED 2026-10-05 — the second bullet below: PO/SO no longer have their own `*_made` topics. Every type except `stock_adjustment` publishes to the shared `CONFIRMATION_MADE_TOPIC` with a `recordType` attribute (PO/SO as `goods_in_confirmation` / `goods_out_confirmation`). See [[architecture]] *Egress / confirmation pipeline*.

## Deliberate asymmetries in the confirmation flow

- `stock_adjustment` publishes one single-record `BifrostMessage` per
  adjustment (matching how other connectors handle it); order types publish
  one bulk envelope per confirmation event.
- Cross-entity confirmation types (RGA, pick, pack, WOC) share
  `CONFIRMATION_MADE_TOPIC` with a `recordType` attribute for subscriber
  filtering; per-entity types (PO, SO) have their own dedicated `*_made`
  topic with no attribute needed. Adding a new cross-entity confirmation type
  means wiring both `confirmationTopicMap` and `confirmationAttributesMap`,
  or subscribers silently can't filter on it.
- Only RGA used to publish confirmation-delivery failures (to the wrong,
  ingress-side `create_data_failure` topic) — fixed alongside FUSE-901's
  introduction of the dedicated `confirmation_data_failure` topic, which all
  seven confirmation types now use uniformly.

## `API_KEY` is vestigial

Parsed by the env schema, required for the app to boot, but read by no auth
guard. Don't build new auth on it or "wire it up" without an explicit
decision to do so — HTTP Basic against RemoteConfig is the only real
customer-endpoint auth path.

## `packageManager` mismatch is live, not yet fixed

`mise.toml` pins `pnpm = latest` (10.x); `package.json` still declares
`packageManager: pnpm@9.0.0`. This is the same pnpm-9-vs-10 class of issue
the org root CLAUDE.md warns about generally — hasn't caused a concrete
incident here yet, but flag it if you're touching lockfile/CI tooling in
this repo.

> SUPERSEDED 2026-10-05 — prod is current: fapi releases go out through `terraform-prod` approvals as they merge (E1 `35b2e89` and E8 `66c7a4d` on 2026-10-02/05). Kept as the record of the August backlog.

## Prod deploys have been parked since 2026-08-19 (snapshot 2026-08-24) — check before trusting "it's fixed"

Verified live (2026-08-24): fapi's `Deploy` workflow gates prod behind a manual
`terraform-prod` GitHub Environment approval on the `docker-push-prod` job. Six pushes to
`master` since 2026-08-19 have each queued their own run and all six are sitting `waiting` at
that gate, unapproved — last successful prod deploy was `3fdbb3ea` (2026-08-13). Every
`master`-only fix noted elsewhere in this doc (the `confirmationsEnabled` removal above, the
FailureUseCase naming fix, the dev portal) is merged but **not live in prod**. Approving only
the newest queued run (not an older one) avoids the parked-deploy rollback hazard — an older
queued run would deploy code older than what a newer one already built.

## Ownership

Owned by the Bifrost/Fuse team (not a solo-owned service). No specific
near-term roadmap item was flagged at onboarding time beyond what's already
tracked as an open gap above (`DEFAULT_MAPPING` consumption). Production
history reported as solid at onboarding time — see the parked-deploys note
above for a live operational gap found afterward.

## fapi ACKs a canonical-validation failure with 204, not 400

A confirmation whose `record` fails the Zod canonical-schema boundary is logged
(`Record validation failed`) and the Pub/Sub push is **acked** anyway — deliberately, to
avoid an endless redelivery loop on a message that can never become valid. So "the endpoint
returned 204" is **not** sufficient evidence a confirmation was actually processed and
delivered; only the `Received <type> confirmation payload` log line (or downstream evidence
of delivery) proves that. Any future verification of this path must check for the *absence*
of `Record validation failed` in the window, not just the HTTP status code.

Found 2026-09-16 while verifying FUSE-1059's PO/SO cross-entity cutover.

> SUPERSEDED 2026-10-05 — every fapi `confirmation_ready` subscription now filters `recordType AND (source="rest" OR broadcast="true")` (fapi#134/#137, RGA via A4 fapi#159), so SFTP/Shopify-routed confirmations no longer reach fapi. See *Confirmation delivery, as of 2026-10-05* below.

## Cross-entity `confirmation_ready` broadcasts to every business regardless of connector type

fapi's `confirmation_ready` subscription is unfiltered by connector type, so **every**
business's confirmations reach fapi's routing logic — including businesses whose channel is
SFTP or Shopify, not REST. FUSE-1056's single-connector-by-id resolution requires a
`webhookUrl`, which SFTP/Shopify connectors never have by design (they deliver via
sftp-connector's/shopify-connector's own independent subscriptions on the same topic). Every
such business trips fapi's `fuse.confirmation.unroutable`/`forward.failure` metrics and the
two monitors built on them — **with zero customer impact**, since the business's real delivery
channel (SFTP/Shopify) still works fine. This gotcha has existed since FUSE-1056
(2026-09-08); PO/SO's near-universal confirmation volume just exposed it at alerting scale
for the first time on 2026-09-16 (filed as FUSE-1226). Nothing currently distinguishes
"this business's channel isn't REST" from "genuine misconfiguration" in the metric/monitor —
a real fix (filtering the unroutable metric to REST-channel businesses only, or similar)
is still open.

## Confirmation delivery, as of 2026-10-05 {#confirmation-delivery-2026-10}

- **What fapi receives.** Only confirmations routed to a REST connector (`source="rest"`), plus broadcasts. That's every `confirmation_ready` subscription, RGA included.
- **"Takes the type" for REST means having a `webhookUrl`.** REST connectors carry no use-case keys, so config-service's `useCases` is `[]` for them. Anything that judges which connectors take a type from `useCases` gets REST wrong.
- **A fan-out (broadcast, or no `connectorId`) ends in `made` or one stored failure per REST connector that wasn't delivered** (E1, fapi#161/#162). A failed leg is a misconfigured, inactive or webhook-failing connector, or (since E8, fapi#166 on remote-config 2.3.0) one remote-config couldn't load. Each failure carries that `connectorId` on the body and envelope, so a replay redrive reaches that connector alone. `made` is published once when any connector delivered.
- **A routed confirmation whose connector remote-config couldn't load** records a retryable `config_service` dependency failure (`fapi.connector_unresolved`). Before E8 it was the non-retryable `connector_unresolvable`.
- **A push that keeps failing is bounded** by the `confirmation_ready` retry budget (E5, fapi#160: `deliveryAttempt` cap, then a recorded retryable failure and an ack).

## Gotchas carried over from FUSE-1056 (checked against `origin/master` 2026-10-05)

- **Which exceptions get acked is decided in two places.** `AllExceptionsFilter.catch()` picks
  the status, and `isAckedException()` (`http/filters/all-exceptions/is-acked-exception.ts`) tells
  `LoggingInterceptor` whether the request-outcome metric counts the call as failed. They are two
  separate lists over the same exception classes. A new "ack, don't retry" exception must go in
  both. If you miss the filter, a poison message redelivers forever. If you miss the predicate, the
  metric reports a failure that was acked.
- **Never route by `resolveByConnectorId` alone.** remote-config's
  `ConnectorBacklinkHandler.resolveByConnectorId(id)` looks the id up across every business and
  every connector type. A stale or wrong `connectorId` on an envelope can then name another
  customer's active REST connector. fapi used to resolve that way, and was fixed by comparing
  `businessId`. Today it is safe by construction: `ConfigApiAdapter` loads only the business's
  REST connectors (`resolveWithUnresolved(businessId, ConnectorType.REST)`), and
  `ConfirmationService.selectTargets` picks the named id from that list.
- **A pkg-node package's `workspace:*` dependency on another pkg-node package is published as an
  exact version.** fapi consumes `@gfs-bifrost/pubsub` and `@gfs-bifrost/remote-config`, which
  both build on `@gfs-bifrost/types`. A fix published in `types` only reaches fapi through
  `pubsub` once `pubsub` is itself bumped and republished (that is why `pubsub` 0.4.1 exists).
  Check the published manifest (`npm view <pkg>@<ver> dependencies`) before assuming a fix has
  arrived. remote-config avoids this with a `>=` peer range.

## Unknowns

- Whether `DEFAULT_MAPPING` consumption for direct-API submissions is
  actually planned/ticketed anywhere, or just a documented-and-accepted gap.
- Whether the two stubbed v1 routes (`return-goods`, `work-orders`, stock
  lookup) have a retirement or completion date, or stay stubbed indefinitely
  for sandbox/docs parity.
- Real-world usage volume/criticality of `api-gateway-sandbox` — confirmed
  as customer/partner-facing by intent, but not how heavily it's actually
  used.
- **The `portal/` developer-portal app (added 2026-08-24 to [[overview]]/[[architecture]])
  needs a real onboarding pass** — its own auth model, whether it's actually customer-live
  yet or still being stood up, and its relationship to `api-gateway-sandbox` (both consume
  the same OpenAPI export; unclear if they serve overlapping or distinct audiences). Missed
  entirely at first onboarding because the main checkout was on a stale branch — see the
  `confirmationsEnabled` correction above for the same root cause.
