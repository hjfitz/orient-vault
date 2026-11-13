---
tags: [waypoint, shopify-connector]
verified: '2026-08-24'
verified_paths: []
title: shopify-connector — known context
---

# shopify-connector — known context

`known-context.md` is exempt from staleness checks — this is interview/investigation
truth, not a claim about current source. Re-verify against code before trusting a
specific implementation detail below.

**The deepest, most current source for this service's fragility is not this file —
it's the internal refactor programme's `Migration State.md`** (Obsidian vault,
`Bifrost/Shopify Connector Untangle/Migration State.md`, owned by Harry Fitzgerald,
created 2026-11-13; it replaced the retired `Bifrost/Shopify Connector Rearchitecture/`). It is a live risk register, bug
list, and architecture review re-derived directly against `origin/main` — treat it as
more current than this doc for anything it covers, and read it before touching
ingest, confirmation, or the token-lock code. What follows summarizes its
durable, non-programme-specific findings; it does not replace it.

## Stale local checkout — a standing hazard, not a one-off {#stale-checkout}

Verified 2026-08-24: `~/code/fuse/shopify-connector` was parked on
`hjf/shopify-rearchitect-s0-baseline`, merged with `main` as of 2026-08-03 — missing
**134+ files and the entire bulk-ingest subsystem** present on `origin/main`. The
rearchitecture programme's own decision log records the same lesson repeatedly (its
2026-08-21 entry: "the tree had moved a long way... Matt shipped ~20 PRs of bulk-ingest
work" since the plan was last read). **Always `git fetch` and read `origin/main`
directly (`git show origin/main:<path>`, `git log origin/main`) before trusting
anything in this repo's working tree** — don't assume a quiet local checkout means a
quiet repo.

**Waypoint tooling implication**: this folder's docs were anchored by hand to
`origin/main`'s sha (`490c8bf`, the S1 merge), not the local checkout's HEAD — running
a bare `wp verify shopify-connector <doc>` here would stamp whatever the *local*
checkout's stale HEAD happens to be instead. Bring the checkout current (`git fetch`
+ fast-forward or a fresh worktree) before trusting `wp verify`/`wp stale` output for
this specific service.

## R1 — permanent, invisible order loss past the retrieval window {#r1-permanent-order-loss}

The poll's retrieval filter is a **stateless sliding window** recomputed fresh every
poll (`new Date(Date.now() - rule.value)`) — there is **no persisted watermark
anywhere in source**. An ingest regression that survives past a connector's own
retrieval window is **permanent, unrecoverable order loss**, and — because there is
no watermark — **invisible to any test suite by construction**; only a live monitor
or a backfill runbook can catch it. As of 2026-08-24 (snapshot 2026-08-24) there is **no Datadog monitor
for this anywhere in `iac/`**, and no rehearsed recovery runbook exists yet
(tracked as the programme's `S9`/`RECOVERY` units — not started).

> SUPERSEDED 2026-10-05 — prod has two Shopify connectors (SAIRA and PURDYFIGG), not one.

**This stopped being hypothetical.** SAIRA is a live, active production Shopify
connector (the fleet's only one) with non-zero real order flow. Its actual window is
**30 minutes** (its own `retrievalConditions.salesOrder` sets `created_at >=
1800000`, which — per full-replace semantics — replaces the commonly-quoted 10-minute
default entirely). Against the 5-minute poll that's roughly a 6-poll cushion, not a
2-poll cliff, but the loss past that window is still permanent and still undetectable
without a monitor. **Don't quote "10 minutes" for this service — read the specific
connector's own conditions.**

The redeploy-free stop switch this used to assume
(`FEATURE_FLAG_ENABLE_ENTITY_EVENTS`) was deleted by unrelated cleanup work
(2026-07-24) before anyone realized it was load-bearing for this. The current
mitigation is `disable_shopify_poll` (near-instant pause, does not extend the
window) plus a Cloud Run traffic rollback to the prior revision (the actual
recovery step) — not yet rehearsed/timed as one combined runbook.

## Two ingest paths sharing one canonicaliser

`core/bulk/{tick,reap,reassemble}` is a second, permanent (not transitional) ingest
path — FUSE-1098 ("retire the metered poll") is Won't-do. `SalesOrderCanonicaliser`
serves both, so a bug or a fix there lands on both simultaneously, but only the
metered path is live in production today (SAIRA is not bulk-enabled). Treat any
change to shared canonicalisation code as touching two ingest paths, not one, even
though only one currently has customer stakes.

## Three known, still-live bugs (snapshot 2026-08-21, against `main`)

- **`handleTokenPersistError` never unlocks the token lock** — logs, increments a
  counter, rethrows, never releases. Its own test still stubs the unlock call under a
  comment claiming it *is* called — **the spec documents the opposite of the truth**
  on the exact incident path (2026-07-02) that motivated the lock protocol in the
  first place. Described in the programme as "the most dangerous artefact in the
  tree."
- **A discarded `AuthFailure` state** — the state is written when a token auth fails,
  a `hasAuthFailure` getter and a permitting code path both exist, but nothing
  actually *triggers* a rebuild off it — so the signal is captured and then dropped.
- **`records.collected` counts stores polled, not orders collected** — a real
  metric-semantics bug, more consequential now that prod has actual order volume to
  undercount.

## Do NOT change these on your own judgement {#do-not-change}

Documented directly by the team maintaining this service — these look like
inconsistencies but are deliberate:

- The `ShopToken` lock-absence filters differ by Mongo driver **on purpose** (Prisma
  needs `false`/`null`/`{isSet:false}`; the native driver's `{$ne:true}` already
  covers a missing field) — don't "sync" them.
- The release shape (`$unset` vs `null`) and reclaim predicates likewise differ by
  driver on purpose.
- Failure-publish-don't-throw on ingest, the pagination bounds, and the batched
  detail fan-out are deliberate, not incomplete.
- `GRAPHQL_REQUEST_RETRIES = 0` and the config LRU's 30s TTL are deliberate — a prior
  plan to "fix" the LRU TTL was explicitly rejected.

## The secops nightly is chronically red, and clearing it is the PR author's job {#secops-nightly}

Verified 2026-09-02: `secops.yaml` has failed on **every** nightly run against `main` since at
least 2026-08-30, so any PR opened here inherits red checks that its own diff did not cause. Two
gates, both fleet-wide rather than service-specific:

- **`image_scan`** — `CVE-2026-14456`, OpenSSL `libcrypto3` in the `node:24-alpine` base image.
  There is no fixed base-image tag published, so there is nothing to bump; fapi's `image_scan`
  fails on the identical CVE. Time-boxed in `apps/shopify-connector/.trivyignore`.
- **`dependency_audit_app`** — HIGH advisories on build-toolchain transitives of **shopify-app**.
  The underlying cause is that `@react-router/dev`, `vitest` and `vite-tsconfig-paths` sit in
  `dependencies` rather than `devDependencies`, so a `--prod` audit walks the entire build and test
  toolchain and reports its transitives as production vulnerabilities. Moving them removes the
  whole class, but it changes a **prod-deploying** app's dependency graph and its dockerfile
  install flags, so it needs its own change and verification — not a drive-by. Tracked, not done.

**"Dependency audit FAILED — 0 finding(s) gate the build" means an allowlist entry has expired.**
The `audit-ci-summary` step still labels an expired entry "allowlisted", so the advisories it lists
are a red herring. Read `audit-ci.jsonc`'s `expiry` dates first. Hit 2026-10-14: deepmerge-ts
(GHSA-ggr8-5vv4-36mx) expired the same day, and was re-dated in #334 after re-checking that
`@prisma/config` still pins 7.1.5.

The convention (org `CLAUDE.md`, *Pull Request Rules*): clear it anyway, in **its own PR off
`main`**, never bundled into or stacked on the feature PR. "Pre-existing, not mine" is the start of
the job, not the end — these went stale precisely because each author decided they were someone
else's.

## Ownership

Wider Fuse team does ordinary feature work here (confirmed 2026-08-24) — the same
pattern as the SNAP integration pair, e.g. Matt's bulk-ingest workstream landed
independently of the rearchitecture programme. The rearchitecture programme itself
is a separate, Harry-owned initiative layered on top — don't conflate "who owns
day-to-day changes" with "who owns the migration."

## `mise x -- pnpm` can silently resolve to a stray corepack-cached pnpm version, not the `mise.toml` pin

This repo pins `pnpm = "10.24"` in `mise.toml`, but `mise x -- pnpm run test` ran a
corepack-cached `pnpm@11.0.8` instead — hard-failing on the repo's ignored-builds gate
(`ERR_PNPM_IGNORED_BUILDS`) before tests ever ran. fapi and sftp-connector's `mise x -- pnpm`
calls resolved correctly in the same session, so this is repo-specific (a stray corepack
cache on this machine, not a universal `mise` bug) — but worth checking again if it recurs.
Fix: invoke the mise-installed binary directly rather than going through `mise x`:
`~/.local/share/mise/installs/pnpm/10.24.0/pnpm <cmd>`. Found 2026-09-16 during FUSE-1059
verification.

## Confirmation egress gotchas found in E1 (2026-10-02)

- **The redelivery exception filter records nothing itself** (#294). It turns only
  `ConfirmationRedeliveryRequiredException` into a 500 so Pub/Sub redelivers. Any failure record has to be
  published by the service before the throw.
- **`ShopifyIdSchema` is an unanchored `/g` regex** (`schema.ts:3`), and `mapId` only prefixes ids that lack the
  FulfillmentOrder prefix. A non-Shopify ref like an SFTP order number becomes
  `gid://shopify/FulfillmentOrder/SO-123`, which Shopify rejects with `GraphqlQueryError "Invalid id"`. E1
  added a guard so that case records properly, but the regex itself is unchanged.

## Found during FUSE-1057 confirmation routing (checked 2026-10-05) {#fuse-1057}

- **PURDYFIGG is the multi-channel canary.** It has SFTP, API and Shopify connectors on one
  storefront in prod, and it is the bulk-ingest tenant. Reason about any change that treats
  confirmations differently by channel against PURDYFIGG. SAIRA has one Shopify connector, so it
  exercises none of the interesting branches.
- **`iac/.../bifrost-shopify-connector/pubsub.tf` uses CRLF line endings; its siblings
  (`remote.tf`, `cloud-run.tf`) use LF.** A scripted edit that reads and writes it in text mode
  rewrites every line (a 6-line change once showed as `962 +++---`). Keep the line endings
  (`newline=""` in Python) and check `git diff --stat` before committing.
- **A new required env var in `config.schema.ts` must also go into `.env.test` and
  `.env.sample`.** Those are the env files that carry the topic vars, and every test that boots the
  real config fails without it.
- **A config-service `PATCH` to a connector's `config` resets any boolean you leave out to its
  default.** Flipping `isActive` alone once reset `stockAdjustmentsEnabled` from `true` to `false`.
  Send every boolean you want kept, then compare a fresh GET against the GET from before the change
  (never the PATCH response against a GET; their shapes differ).
- **When removing a Terraform resource and its provider, the provider has to outlive the resource
  by one apply.** Removing both in one commit fails the plan with `Invalid provider configuration
  ... requires explicit configuration`, because Terraform needs the provider to plan the destroy.
  This cost a fix-up commit when the source-mismatch monitor moved to `gfs-bifrost/observability`.

## Found during FUSE-1317 tracking links (checked 2026-10-19) {#fuse-1317}

- **SNAP carries two different carrier fields.** `shipping.carrierId` (SNAP `Shipment.CarrierId`) is
  the booking platform code, and `despatches[].carrier.id` (`ShipmentDespatch.Carrier`) is the real
  courier. They match for Purdy & Figg (`GFS_EVRI`). For NetCourier customers they differ: Saira sends
  header `NETCOURIER` with despatch couriers Royal Mail, UPS and DPD Local. Harry classes Saira's
  `NETCOURIER` header carrier as a SNAP config issue, not a Fuse one.
- **Shopify fills the tracking link itself for a carrier it knows.** Purdy & Figg sends no URL, yet
  prod read-backs show Shopify stored `https://www.evri.com/track/parcel/<n>/details` for `EVRI`. Only a
  carrier Shopify doesn't know needs a mapped URL rule.
- **A `lookup()` miss inside `concat()` returns the other arguments, not `''`.** "Miss means the field
  is dropped" holds only for a bare `lookup()`. A URL rule built with `concat` surfaces a miss as
  `invalid_url` (the bare tracking number), not `unresolved`.
- **The routed Shopify confirmation path needs a hand-rolled publish to test in dev.** fuse-mocker
  can't stamp `source=shopify`, and its broadcast fires every active REST connector's webhook on the
  business (GADG dev → `fulfil.io`, PURDYFIGG dev → Purdy & Figg's `onrender` sync). Publish with
  `gcloud pubsub topics publish bifrost.dev.confirmation_ready.v1
  --attribute=recordType=goods_out_confirmation,source=shopify` and `metadata.connectorId` set.
  GADG's "ILG Test Store" (`conn_c7e4fd39…`, store `quickstart-501d0f59`) is the ILG-owned target.
- **A config-service mapping `PUT` keeps a stored `dictionaries` array when the body omits the key.**
  Only an explicit `dictionaries: []` clears it, so restoring a pre-dictionary snapshot needs that.
- **(snapshot 2026-10-19) The order-tag error log hides Shopify's message.**
  `OrderUpdateMutationResponseSchema` (`core/shopify/graph/mutations/schemas.ts`) types
  `userErrors[].field` as `string`, but Shopify sends `[String!]`. Every real tag userError therefore
  logs `Shopify order tag mutation returned errors` with a ZodError in place of the reason. Seen on
  GADG dev for `ILG_FULFILLED`, where the same tag write succeeded on another of the business's shops.
- **(snapshot 2026-10-19) Saira's and Purdy & Figg's dev goods-out mappings match prod**, and dev
  `saira-dev2` is a faithful copy of the NETCOURIER case.

## Unknowns

- Whether the programme's `S9` (ingest monitors) / `RECOVERY` (backfill + fast-stop
  runbook) units have landed by the time this doc is read — check `Migration State.md`
  directly rather than trusting the "not started" status recorded here, which is a
  snapshot from the onboarding date.
- Whether GADG's dev connector's current unbounded (all-time, tag-only) retrieval
  condition — an accepted, deliberate blast radius from the 2026-07-29 full-replace
  change — has caused any real volume problem since; not re-checked during this pass.
