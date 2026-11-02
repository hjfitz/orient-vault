---
tags: [waypoint, bifrost-pubsub]
verified: '2026-08-24'
verified_paths: []
title: bifrost-pubsub — known context
---

# bifrost-pubsub — known context

`known-context.md` is exempt from staleness checks — this is interview/investigation
truth, not a claim about current source. Re-verify against code before trusting a
specific implementation detail below.

## Ownership

Wider Fuse team — same shared-ownership pattern as every other service
onboarded this session (confirmed 2026-08-24), despite a topic
deletion/rename here breaking every consumer at once with no compile-time
signal that anything broke.

## The README is substantially stale — the biggest finding of this pass {#readme-stale}

Confirmed directly against the actual `.pubsub.tf` files, not assumed: the
README's Topics section describes a version of the pipeline that predates
two real, already-merged changes.

- **It lists deleted topics as current.** `create_master_data_request`,
  `create_purchase_order_request`, `create_sales_order_request` and their
  non-`_request` counterparts are presented as the live per-entity creation
  path, with the cross-entity `create_record_request`/`create_record` topics
  described as something that "will supersede" them. In reality, the
  per-entity topics are **already gone** — deleted in commit `#12` ("Delete
  legacy post-dedup topics") and this repo's current HEAD ("Remove legacy
  pre-dedup request topics"). The supersession isn't upcoming, it already
  happened.
- **It omits topics that are both live and central.** `create_data_failure`,
  `confirmation_data_failure`, and the cross-entity `confirmation_ready`/
  `confirmation_made` topics don't appear anywhere in the README's tables,
  despite existing in the Terraform and being exactly the topics
  snap-adapter, replay-service, and snap-queue-polling-service all subscribe
  to or publish on (documented in their own Waypoint doc sets this session).
- **One dead link**: the README's own second sentence points to
  `../AGENTS.md` for "the full set of event rules" — no file exists at that
  path from this repo's location.

**Practical implication**: don't use this README as a source of truth for
"what topics exist" — read `iac/projects/bifrost-pubsub/*.pubsub.tf`
directly (a `grep -n 'topic_name\s*='` across them gives the real list in
seconds). The README's envelope-*shape* documentation (the `BifrostMessage`/
`BifrostBulkMessage`/`BifrostEntityError` type definitions) looked accurate
during this pass — it's specifically the topic-list section that's behind,
not the whole document.

## Two DLT-ownership conventions coexist, and it's not obvious which applies where

This repo's shared module auto-creates a DLT alongside every topic it
defines. Some consumer subscriptions read that DLT id back via
`terraform_remote_state` (verified for snap-adapter's `create_record`
subscriptions); others define a wholly separate, locally-owned DLT topic in
their own IaC keyed to the *subscription* rather than the topic (verified
for replay-service's three DLTs). Neither is wrong, but conflating them —
assuming every DLT a consumer touches was provisioned here — would produce a
wrong mental model of who owns cleanup/monitoring for a given dead-letter
topic. Check the consumer's own `pubsub.tf` for whether it declares
`google_pubsub_topic` locally or reads an output from this repo's remote
state before assuming either way.

## No secops workflow — confirmed, not investigated further

Only `deploy.yaml` and `tf-plan-pr.yaml` exist; there's no gitleaks/
dependency-audit/semgrep workflow, unlike every application repo onboarded
this session. Plausibly a non-issue for a repo with no real third-party
dependencies to scan (pure Terraform, no `package.json`), but this wasn't
independently confirmed to be an intentional decision versus an oversight
during this pass.

## Confirmation recordType is asymmetric between ready and made for sales_order

The ready-side and made-side `recordType` values for a sales-order confirmation are
**different strings**: ready-side SO = `goods_out_confirmation` (what snap-queue-polling-service
stamps when publishing to `confirmation_ready`), made-side SO = `sales_order` (what
fapi/sftp-connector/shopify-connector stamp when publishing to `confirmation_made`).
Purchase-order confirmations are symmetric (`purchase_order` on both sides). A subscription
filter written symmetrically (assuming ready and made share one recordType per entity) will
silently match nothing for sales-order. Found during FUSE-1059 (PO/SO legacy-topic
decommission, 2026-09-16) — not documented anywhere else in the fleet.

## This repo is the single owner of every confirmation topic and its DLT

Every consumer repo (fapi, snap-adapter, sftp-connector, shopify-connector, replay-service,
collector) only ever creates subscriptions/IAM grants against topic ids pulled from **this
repo's Terraform remote-state outputs** — never a hardcoded topic name. Each topic module
also stands up its own DLT, so a topic pair (ready/made, or a single cross-entity topic) is
4 outputs (name/id/dlt_name/dlt_id) per topic in `confirmations.outputs.tf`. Deleting a topic
here breaks any consumer whose Terraform still dereferences its removed outputs — a clean
teardown requires the consumer-side references gone *first*, verified via a fleet-wide grep
for the specific output names (stronger proof than trusting `terraform plan` locally, since a
missing remote-state output surfaces as an "Unsupported attribute" error, not a clean diff).

## Unknowns

- Whether the README staleness has a fix already in flight, or is genuinely
  unaddressed — not confirmed either way during this onboarding pass.
- Whether the no-secops-workflow gap was a deliberate call (nothing to scan)
  or simply never set up when other repos got their secops workflow added.
