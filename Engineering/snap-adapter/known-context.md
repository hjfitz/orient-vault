---
tags: [waypoint, snap-adapter]
verified: '2026-08-24'
verified_paths: []
title: snap-adapter — known context
---

# snap-adapter — known context

`known-context.md` is exempt from staleness checks — this is interview/investigation
truth, not a claim about current source. Re-verify against code before trusting a
specific implementation detail below.

## No consumer on the create_record dead-letter topic — a real order-loss gap {#no-consumer-on-the-dead-letter-topic}

**Confirmed directly by the team (2026-08-24), not inferred**: if this service goes
down badly enough, **orders are actually lost**, because no DLT (dead-letter topic)
consumer is configured yet. This is sharper than "delayed" — the polling side
recovers with no data at risk; this side can genuinely drop work.

What the code and Terraform show, consistent with that statement: each of the 5
`create_record` subscriptions (`iac/projects/snap-adapter/pubsub.tf`) declares a
`dead_letter_policy` pointing at `create_record_topic_dlt_id` — a topic *owned by a
separate `core_pubsub` remote state*, not by this app. Nothing in this repo (or
apparently anywhere else) subscribes to that DLT topic to hold, alert on, or redrive
what lands there. A message that reaches Pub/Sub's own dead-letter threshold — as
opposed to the app's own self-managed retry-exhaustion path (see
[[architecture#release-vs-create_data_failure]], which *does* correctly route to
`entity_error`/`create_data_failure` and gets held by the deduper for replay) — is
effectively gone. The two paths look similar (both are "this create didn't make it")
but only one has anywhere to land.

**Practical implication**: an outage/bug that causes the app to crash, hang, or
otherwise fail to return a clean `503`/`204` (rather than cleanly exhausting its own
`MAX_TRANSIENT_DELIVERY_ATTEMPTS` budget and self-reporting) risks silent data loss,
not just delay. If asked to harden this service, standing up a DLT subscription +
alert (or redirecting the DLT policy at something replay-service already watches) is
the highest-leverage fix — higher priority than anything else found during this
onboarding pass.

## RGA and work_order are still the least battle-tested paths

Confirmed by the team (2026-08-24): despite being real, non-stub implementations,
`return_goods_authorization` and `work_order` are meaningfully newer and less trusted
than `sales_order`/`purchase_order`/`master_data`. Treat a surprise in one of those
two paths with more suspicion of a real gap, and less surprise that a real gap
exists, than the same symptom on the three legacy types.

## SNAP itself degrades hard under concurrency, and this has actually happened

May 2026: production overload incidents traced to per-instance axios default
concurrency (80, not the Cloud Run instance count) — SNAP's own comfortable ceiling
is ~10-20 concurrent requests fleet-wide; past ~50-60 concurrent, latency and failure
rate both explode (12-18s avg / 131s max latency, ~70% hourly failure rate observed).
The current `Semaphore`(5)/`TokenBucket`(10rps/burst 20)/circuit-breaker stack (FUSE-
1078) is the fix; if SNAP starts failing broadly again, check whether these limits
were loosened before assuming a SNAP-side regression.

## SNAP write-response parsing has burned real incidents twice

`FUSE-599` (`Successes: 0/1` swallowing the real per-field error) happened because a
schema was written against one shape of SNAP's error envelope and silently returned
nothing for the others (object vs array body, nested vs flat `Errors`, raw
`AxiosError` vs `EntityCreationException` wrapper). `collectSnapFieldErrors`'s
structural walk (`ColumnId` + `Error`, wherever it sits) is the fix — don't reintroduce
a fixed-shape parser here even if it looks like it covers "the" shape; there isn't one.

## Ownership

No dedicated owner — wider Fuse team, shared with `snap-queue-polling-service`.

## Doc-of-record for SNAP nuance

The app's own `CLAUDE.md` (`apps/snap-adapter/CLAUDE.md`) carries hard-won, very
specific SnapFulfil write-path nuance (RGA creation, deterministic ids, segmented
write parsing) that this Waypoint doc summarizes but does not replace — read it
directly before touching create-path code for any entity type.

## Fuse metadata is out of SNAP attachments, and why it had to go (promoted 2026-10-05)

- **A keyed re-PUT replaces a SNAP record's child rows, attachments included.** If the retry that would rewrite them then fails, the live entity is left without them, and no metric fires. Routing provenance and the Shopify `fulfillmentId` used to live in those attachments. Since 2026-10-01 both live only in Firestore, written before the create (#275, #276). So this edge case no longer loses Fuse data. It still applies to the SNAP-visible attachments (duty, notes, delivery instructions, customisations).
- **`already_in_wms` skips all post-create work, not just the shipment write.** When SNAP auto-allocates before a redelivery (the 2026-09-29 PURDYFIGG timeouts), the order is acknowledged without its post-create attachments. That is why line data moved to the pre-create write, keyed by the `SOLineId` the adapter sets before the PUT.
- **The routing upsert used to be a whole-doc `set()`.** It wiped the post-create `lineExtensions` on every redelivery, and this happened in prod: the 2026-09-21 PURDYFIGG redrive rewrote 118 routing docs, and the attachment fallback hid it. Fixed by the field-masked merge (#264). Firestore `mergeFields` throws on a listed field that is absent from the data, so the mask must be built from the fields actually present.
- **Prod never ran `ROUTING_STORE_REQUIRED=true`.** The flag was deleted outright when the write became unconditional (#275), so there was no separate prod flip.

## Unknowns

- Whether the DLT-consumer gap above has a ticket/plan already, or is genuinely
  unaddressed as of this onboarding pass — the team confirmed the gap exists but not
  its remediation status.
- Whether `@gfs-bifrost/types` `^8.4.0` (older than the `^9.2.1`/`^9.3.0` pins seen
  elsewhere in the fleet as of 2026-08-24) is a deliberate pin or simply not yet
  bumped — a new connector use case breaking consumers on older `types` pins has
  bitten other services on stale `types` pins before; not confirmed whether
  snap-adapter is exposed the same way.

## SnapFulfil replaces a CarrierId it doesn't recognise

A shipment create whose `CarrierId` isn't in the tenant's CARRIER lookup still succeeds, but Snap stores its own value. GADG dev (lookup: `NETCOURIER` only) turned a work order sent with `OWN` into S10 `GADGDFD78D24007` with `CarrierId: NETCOURIER`, with no error back (verified 2026-10-19). The snap-api simulator doesn't model this; it stores whatever it's sent. To make a carrier land, add it to the tenant's CARRIER lookup in SnapFulfil. Code can't do it. A 2024 GADG shipment holding the non-lookup `DHL` shows older or other paths behaved differently, so don't generalise from that one.
