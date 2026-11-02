---
tags: [waypoint, replay-service]
verified: '2026-08-24'
verified_paths: []
title: replay-service — known context
---

# replay-service — known context

`known-context.md` is exempt from staleness checks — this is interview/investigation
truth, not a claim about current source. Re-verify against code before trusting a
specific implementation detail below.

## Ownership

Wider Fuse team — same shared-ownership pattern as every other service onboarded
this session (confirmed 2026-08-24, no exception here).

## The DLTs have no consumer — but they ARE monitored {#dlt-monitored-not-consumed}

Verified directly against both `iac/projects/replay/pubsub.tf` and live Datadog
monitors (2026-08-24): all three dead-letter topics
(`create_data_failure`/`confirmation_data_failure`/`confirmation_made` `.v1.dlt`)
have **no subscription reading them** — a message that exhausts its 5 delivery
attempts just sits there. This is the same underlying gap found on snap-adapter
earlier this session, but **materially better mitigated here**: a real Datadog
monitor (`[Replay] Failure dead-lettered on create_data_failure`) fires the
moment one lands, with its own alert message stating outright *"Nothing
subscribes to that DLT, so it sits unconsumed"* — the design choice is "alert a
human," not "silently trust the DLT," and that choice is explicit rather than
accidental. A second monitor (`[Replay] Failures dropped forever (unparseable
create_data_failure)`) covers the other permanent-loss path — an unparseable
payload that never even reaches storage. Both are real `@team-fuse-developers`
pages, not dashboards nobody watches. If asked to "fix" the DLT gap here, the
existing design (monitor + manual redrive) is a considered choice, not an
oversight — confirm the ask isn't already satisfied before building anything.

## The Fuse MCP catalog is stale here too {#mcp-stale-release-topics}

> SUPERSEDED 2026-10-19: the `release_*` subscription was not dead scaffolding. It was a live ingest path until FUSE-733 (d99d272, 2026-07-02). Every prod row with no `stage` comes from it: a snap-adapter WMS rejection. See [[#where-it-failed]].

`services.json` lists replay-service as subscribing to `release_*` topics.
Verified directly: it does **not** — there is no `release_*` subscription
anywhere in `pubsub.tf`. This is dead scaffolding inherited from the
collector/dedupe fork this service was built from (see the repo's own
`CLAUDE.md` "Inherited scaffolding" section, which documents the same dead
`RELEASE_*` metrics). One Datadog monitor's query pattern
(`subscription_id:replay.*`) is written broadly enough to still match a
release-style subscription name if one is ever re-added, which is likely why
that phrasing persists in the monitor's alert text even though no such
subscription currently exists. This is at least the **sixth** MCP-catalog
staleness finding across the six services onboarded this session — treat the
catalog as a starting point, never ground truth.

## A verified, small doc gap in an otherwise excellent CLAUDE.md

`POST /api/v1/failures/replay` (bulk replay by id array, max 100, concurrency 5,
per-id outcome) exists in code (PR #73) but is **not** in CLAUDE.md's own
endpoint table, even though CLAUDE.md was itself updated in the very next PR
(#74). Worth fixing in that file directly next time someone's in there — noted
here rather than fixed unilaterally, since editing another repo's CLAUDE.md is
out of scope for a Waypoint onboarding pass.

## RGA's create-side exclusion is deliberate, re-confirm before "completing" it

Only RGA's **confirmation**-side failures are captured; its create-side failures
(which do reach `create_data_failure`, per the deduper's own failure-cleanup
design) are never stored or replayable here. Stated directly in CLAUDE.md as
deliberate, not a gap. If a future ticket asks to "finish" RGA coverage, that's a
real scope decision (a new schema-map entry, business-id/record-id cases, and a
widened subscription filter) — not a bug fix.

## Not deduplicated — a redelivery is a second row {#not-deduplicated}

`saveCreateFailure` always mints a fresh UUID; there's no idempotency key on the
failure inbox itself. An at-least-once redelivery of the same underlying failure
event produces two `failures` documents. Don't assume failure-count metrics or
`/stats` totals map 1:1 onto real distinct incidents.

## CLAUDE.md here is a model example — verified current, not just present

Unlike some services this session, this repo's `CLAUDE.md` was directly
confirmed to have been updated in lockstep with the latest code change (both
landed in the same PR, #74) — treat it as trustworthy day-to-day, with the one
verified exception above (the bulk-replay endpoint gap, itself only one commit
older).

## The redrive target map is a per-recordType publish table — an easy-to-miss extra publisher

`replay-service` republishes a redriven confirmation via a per-recordType target map (not a
single hardcoded topic), so when a topic-decommission or migration changes which topic a
recordType should land on, this map is a real, separate publisher that a fleet sweep can miss
if it only checks the obvious create/confirmation-egress services. Caught during FUSE-1059
(2026-09-16): the redrive target map still pointed PO/SO confirmations at the legacy per-entity
ready topics after every other publisher had already cut over to the cross-entity topic — fixed
in replay-service#85. Any future topic decommission or recordType remap must grep this
service's redrive/target-map code specifically, not just its subscription list.

## Unknowns

- Whether the bulk-replay endpoint gap in CLAUDE.md has since been fixed —
  re-check before citing this doc as the reason it's still missing.
- Whether there's a plan to eventually delete the dead `core/use-case/*`
  scaffolding (registry + its three unused Mongo collections) — CLAUDE.md notes
  it's a deliberate standalone deletion, not yet done, but gives no timeline.

## Where it failed, and who a failure belongs to {#where-it-failed}

Learned shipping SHIP-1019 (replay #119/#121–#123, 2026-10-19):

- **Rows with no `stage` are snap-adapter WMS rejections.** About 170k rows in prod and 78k in dev were stored without a stage. replay read them off `release_*` until 2026-07-02, and between 06-04 and 07-02 each such failure was stored twice. The failure point labels them `create.wms_legacy`.
- **sftp-connector has never published a bulk failure envelope.** Its `publishToTopic` sends one message per element. The bulk branch on `/event/confirmation-failure` is unused.
- **`/groups` used to drop six list filters,** and `count`/`groupByExpression` always excluded soft-deleted rows. So `resolved=true` groups were empty until #119.
- **A record with no business used to be invisible in the queue.** This covered shopify-connector ingest failures, whose record is the raw Shopify order (FUSE-1320), and whole-file SFTP failures, which carry no record. They were stored under `businessId: ""`, which no queue shows. Since #122 they fall back to `metadata.customer`. The 540 such rows in prod were re-attributed by script on 2026-10-19; the plan file is `plans/artifacts/ship-1019-prod-reattribution-plan.json`.
- **Attribution is record first, by design.** A routed sales order carries a business that differs from the connector's, and tracking-service attributes failures the same way, so fuse-ui's tracker links stay consistent. Don't switch to preferring the envelope's customer.
- **`create.snap_adapter_internal` is a catch-all.** It mixes Snap outages (circuit open, slot timeout) with failures that never reached Snap (13 prod `invalid_deterministic_id`). Only snap-adapter can split them (FUSE-1319).

