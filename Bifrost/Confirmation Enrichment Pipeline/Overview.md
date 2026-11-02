---
title: "Confirmation Enrichment Pipeline — Overview"
status: planning
verdict: go
owner: "Harry"
services: ["snap-queue-polling-service"]
created: "2026-09-18"
updated: "2026-09-18"
tags: [bifrost, snap-queue-polling-service, rearchitecture]
---
# Confirmation Enrichment Pipeline — Overview

<!-- The narrative and the verdict. PROGRESS lives in the Migration State doc, not here — link it,
     never duplicate its ledger. This doc changes rarely; the state doc changes every session. -->

## Deliverables
- [[Confirmation Enrichment Pipeline/Migration State|Migration State]] — the live source of truth for progress
- [[Confirmation Enrichment Pipeline/Target Design|Target Design]] — the end state every unit builds towards:
  stage order, track/type literals, drop vocabulary, announce, the awkward cases, the contract pin, the
  reviewer checklist. Read before planning any unit.
- Architecture review (2026-09-18) — https://claude.ai/artifact/UMpV4iouA7bTv3hVv9PyR8 — what runs today,
  the evidence it accreted ticket by ticket, the target shape and the first cut of the route
- Waypoint service folder — `~/Documents/obsidian/Engineering/snap-queue-polling-service/` (architecture
  explainer, known-context, the two FUSE-1063 plans that precede this)
- No Jira ticket/epic — Harry's explicit choice (2026-09-18). PRs reference this programme by name.

## Verdict
**Go**, with two conditions that are gates in the State doc: the two in-flight FUSE-1063 PRs
(snap-adapter #240, #241) are merged first, and a characterisation baseline (golden-master canonical
outputs per type + a 24h dev publish baseline) is captured before any mapper moves.

The verdict rides on one framing decision Harry made explicitly: **the set of confirmation types is not
growing any more.** So the goal is *not* extensibility. It is that the whole confirmation behaviour of
this service can be read from a small number of declarative definitions and operated on with confidence
— one place per concern, three tracks written as data, mappers as pure functions, one vocabulary for
every drop. Anything that looks like a framework or an engine (abstract stage classes, plugin registries,
a DSL) is out of scope and a review block.

## Why this needs a programme
The confirmation code under `apps/snap-queue-polling-service/src/core/snap/` grew from 4,777 to 11,674
lines in ten weeks by adding one feature per ticket to a handler-per-type model; the drain/lanes were
retrofitted in week six after four types had shipped on a base that fetched its own queue. Routing
provenance is implemented in five places, eligibility in three, error isolation in four layers (none at
publish), and 22 drop points sit in four layers with five of them silent. It is a live path: every
customer's pick/pack/despatch/receipt/RGA/work-order confirmation flows through it, INC-30 (duplicate
confirmations) lives here, and the black-box harness encodes today's fetch order as expected call counts.
That combination — large, live, and with hidden coupling — is exactly what a unit ledger with gates and
golden-master checks is for, and why it cannot be one PR.

## Strategy
**Strangle in place, one track at a time, zero external-contract change.** Topics, `recordType` /
`source` / `broadcast` attributes, envelope shapes, the claim key, the Firestore store schema and the
SNAP call pattern per type stay identical throughout — the black-box call-count expectations become a
regression asset, re-derived per unit rather than patched.

Sequence (see the ledger): foundations that make the compiler carry the shape (typed records, provenance
read once per track) → the three tracks rewritten as data literals with enrichers and pure mappers,
DESPATCH first because it has the most repetition → the cross-cutting seams (one drop vocabulary; announce
owns claim/publish/dispose with per-group isolation) → the type table replacing the six
`ConfirmationType` switch sites → close-out (debug endpoints call the pipeline, docs, harness).

There is **no cutover flip**: every unit lands behaviour-preserving on `master` and deploys through the
normal dev → prod path. Reversion of any unit is a revert of its PR.

## Target shape (the declarative end state)
Full detail, sketches and the awkward cases: [[Confirmation Enrichment Pipeline/Target Design|Target Design]].
- `tracks/` — three data literals: `DESPATCH_TRACK`, `RECEIPT_TRACK`, `STOCK_TRACK`. Each names its
  lane, key parser, batched entity resolver, `ownerOf`, its named enrichers (each with a declared
  failure policy), and its ordered **type table**: per type the ownership predicate, the enrichers it
  `needs`, `provenanceKey`, a pure `map`, schema, publish tag/recordType, failure use case,
  routing-awareness. Reading a track literal tells you everything a type does and fetches.
- `pipeline.ts` — one `pollTrack(track, target)` with nine fixed stages: select → read → pre-filter →
  resolve → discriminate → enrich → provenance → map/validate → gate → announce. Plain functions; no
  `Stage` type, no registry; isolation at exactly three boundaries (business, entry, group).
- `drop.ts` — one outcome vocabulary (`skip` / `withhold` / `clear`, closed reason lists) and one helper
  that logs and meters; every drop site uses it; fail-open declared on the gate, not at drop sites.
- `announce.ts` — the only side effects on Pub/Sub, Redis and SNAP's queue: claim → publish → clear,
  isolated per group, one Pub/Sub transport, alias publish as data.

## Scar tissue
- The queue is read **once per transaction type**, never once unfiltered (`$top` is per request; INC-30).
- **Publish before ack, claim before publish**, key `confirmation-claim:{businessId}:{queueId}` — the
  INC-30 / FUSE-1176 idempotency contract. The pipeline must not reorder it.
- A routing-store **read failure never degrades to broadcast**; only a genuine miss falls back to the
  attachment, then to manual-origin broadcast.
- The goods-out / goods-in alias asymmetry on `confirmation_ready` is deliberate (shopify-connector
  filters on `goods_out_confirmation`); the alias becomes a *field on the type definition*, not a retired
  branch.
- Absent `confirmationsEnabled` reads as **not enabled** (fail closed) — the FUSE-1063 backfill made that
  safe; do not loosen it.

## Next
Gate **G1** (review and merge snap-adapter #240 and #241, on-push deploy to prod), then unit **U0 —
characterisation baseline** (golden-master specs + 24h dev Datadog baseline in one go), driven with
`waypoint-programme`. Harry decided 2026-09-18 not to start U0 before G1.
