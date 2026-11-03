---
title: "Confirmation Enrichment Pipeline — Target Design"
status: design
owner: "Harry"
services: ["snap-queue-polling-service"]
created: "2026-09-18"
updated: "2026-11-03"
tags: [bifrost, snap-queue-polling-service, design]
---
# Confirmation Enrichment Pipeline — Target Design

<!-- The end state every unit in the Migration State ledger builds towards. Read before planning any
     unit. Code here is a SKETCH of shape, not an API to copy verbatim — the unit that lands a piece
     owns its final form, and records any deviation in the State doc's Decision log. -->

## The one-paragraph version
Three **tracks** — shipments, receipts, stock movements — each an object literal that says how to read
its queue rows, resolve them to a SNAP entity, tell who owns the entity, and which confirmation
**types** live on it. Each type is a literal too: an ownership predicate, the enrichments it needs, a
pure `map` from an enriched entity to a canonical (or an outcome), its schema, and the facts the
publish step needs (tag, failure use case, routing-awareness). One `pollTrack()` runs the same nine
stages for every track. Every drop goes through one function with one vocabulary. Every side effect on
Pub/Sub, Redis or SNAP's queue happens in one place, after mapping. That's the whole design; anything
that needs more machinery than this is a smell.

## Design rules (what "declarative, not extensible" means here)
1. **Tracks and types are data literals**, not classes. Behaviour lives in plain functions those
   literals point at. There is no `Stage`, `Handler`, `Enricher` or `Pipeline` base class, no registry,
   no decorator, no DSL.
2. **One place per concern.** Reading, dropping, provenance, enrichment, mapping, gating, publishing each
   happen in exactly one function. If you can't say which stage a line belongs to, it doesn't belong.
3. **Mappers are pure.** Input: an enriched entity. Output: a canonical or an outcome. No I/O, no
   metrics, no logging, no clock.
4. **The compiler carries the shape.** Typed records between stages; a mapper can only read the
   enrichments its type declared; every `ConfirmationType` appears on exactly one track (checked at
   compile time).
5. **One vocabulary for dropping.** Three outcomes (`skip`, `withhold`, `clear`), a closed set of
   reasons, one helper that logs and meters. No silent drops.
6. **Zero external-contract change.** Topics, attributes, envelopes, claim key, store schema, SNAP
   call set per type — identical. The black-box call counts are a regression asset.
7. **Boring beats clever.** Where a generic type gets hard to read, use the simpler type and a runtime
   assertion. Three near-identical lines beat an abstraction.

## The nine stages, in order
> SUPERSEDED 2026-11-03 — the **pre-filter** stage ("drop rows decidable from the raw row, claim live") is gone: the Redis claim was deleted by #308 (FUSE-1324), so there is nothing to pre-filter on, and `announce` is no longer "claim → publish → clear" (see Announce below). Two things the sketch lacked now exist in the code and the track runner must carry them: a **collection budget** (420 s, checked between lanes and at page boundaries, first page always processed, with `recordLaneDeferral` for the rest) threaded through read / resolve / enrich, and an **announce budget** (540 s, checked between pages of 100, never between a page's publish and its clear). Polls themselves are serialised per business upstream of this pipeline by a Pub/Sub ordering key, so the pipeline needs no idempotency step of its own. The list below is kept as the original design.
```
select    which businesses to poll (config gate)                       once per schedule tick
read      one queue read per track per business                         $top per request
pre-filter drop rows decidable from the raw row (claim live)            no I/O beyond Redis
resolve   batched fetch of the keyed entity; cross-tenant drop           the track's resolver
discriminate  exactly one type owns the entity, or none                  ordered predicates
enrich    run the owning type's declared enrichers                       track enrichers
provenance store read once per page per track; attachment fallback       key per type
map + validate  pure map → canonical | outcome; schema check             per-entry isolation
gate      connector eligibility + source; one broadcast escape           per group
announce  claim → publish → clear, isolated per group                    the only side effects
```
Why discriminate *before* enrich and provenance: the owning type decides which enrichers run and which
provenance key applies (FGR keys by `receipt.Prime`, everything else by its own id). Today provenance
runs first because it lives in a base class shared by handlers; under the pipeline there is no reason
for that order, and putting discrimination first makes "what does this type fetch" read straight off
the type literal.

## Shapes (sketch)

```ts
// tracks/types.ts — the vocabulary every track speaks
type QueueRow = SnapOutboundMessage;                    // XDoc, Key, Transaction — nothing else

type Resolved<E> = { row: QueueRow; key: ParsedKey; entity: E; businessId: string };

type Outcome =
  | { kind: "skip";     reason: SkipReason }             // leave on SNAP, retry next cycle
  | { kind: "withhold"; reason: WithholdReason }         // leave on SNAP on purpose (config)
  | { kind: "clear";    reason: ClearReason };           // PATCH …/processed; nothing published

type Enricher<E, V> = {
  fetch: (r: Resolved<E>, snap: ISnapAPI) => Promise<V>;
  onFailure: "skip" | "degrade";                          // skip the entry, or map with undefined
};

type Enriched<E, N extends keyof Enrichments<E>> = Resolved<E> & {
  provenance: RoutingMetadata | undefined;               // store, else attachment fallback, else none
  storeDoc: RoutingStoreDoc | undefined;                 // lineExtensions ride here for goods-out
  enrichments: Pick<Enrichments<E>, N>;                  // only what the type declared
};

type TypeDefinition<E, N extends keyof Enrichments<E>> = {
  type: ConfirmationType;
  owns: (r: Resolved<E>) => boolean;                     // ordered within the track; first match wins
  needs: readonly N[];
  provenanceKey: (r: Resolved<E>) => string | undefined; // FGR: receipt.Prime; default: entity id
  map: (input: Enriched<E, N>) => Canonical | Outcome;   // pure
  schema: ZodType<Canonical>;
  publish: { tag?: TaggedConfirmationType; recordType: string };
  failureUseCase: FailureUseCase;
  routingAware: boolean;                                 // manual-origin failure fan-out, and the
};                                                       // hit/fallback/miss metering

type Track<E> = {
  lane: ConfirmationActions;
  parseKey: (row: QueueRow) => ParsedKey;
  resolve: (keys: ParsedKey[], snap: ISnapAPI) => Promise<Map<string, E>>;   // batched
  ownerOf: (e: E) => string | undefined;                 // cross-tenant + the group's businessId
  enrichers: Enrichments<E>;                             // named fetchers, declared once per track
  types: readonly TypeDefinition<E, any>[];              // ordered; exactly one owns any entity
};
```

```ts
// tracks/despatch.track.ts — what the shipments track reads like
export const DESPATCH_TRACK: Track<SnapShipment> = {
  lane: ConfirmationActions.DESPATCH,
  parseKey: parseShipmentKey,
  resolve: fetchShipmentsBatch,
  ownerOf: (s) => s.BizId,
  enrichers: {
    headerAttachments: { fetch: (r, snap) => snap.fetchShipmentAttachments(r.key.Shipment, ["SHH"]),        onFailure: "skip" },
    lineAttachments:   { fetch: (r, snap) => snap.fetchShipmentAttachments(r.key.Shipment, ["SHL"]),        onFailure: "skip" },
    stockDetail:       { fetch: (r, snap) => snap.fetchStockDetail(r.entity.ConsignmentId ?? r.key.Shipment), onFailure: "skip" },
    stu:               { fetch: (r, snap) => snap.fetchStu(r.entity.ConsignmentId, "OC"),                  onFailure: "skip" },
    despatchStock:     { fetch: (r, snap) => snap.fetchDespatchStock(r.key.Shipment),                       onFailure: "skip" },
    stockConsignment:  { fetch: (r, snap) => snap.fetchStockConsignment(r.entity.ConsignmentId, "DESPATCH"), onFailure: "skip" },
    pairedReceipt:     { fetch: probePairedReceipt,                                                          onFailure: "degrade" },
  },
  types: [
    { type: "pick_confirmation", owns: atStage("29", notWorkOrder), needs: ["headerAttachments", "stockDetail"],
      map: mapPick, schema: CanonicalPickConfirmationSchema, publish: { recordType: "pick_confirmation" },
      failureUseCase: "pick_confirmation", routingAware: true, provenanceKey: byShipment },
    { type: "pack_confirmation", owns: atStage("39", notWorkOrder), needs: ["headerAttachments", "stockDetail", "stu"], … },
    { type: "good_out",          owns: atStage("90", notWorkOrder), needs: ["headerAttachments", "lineAttachments", "stockConsignment", "stu", "despatchStock"],
      map: mapGoodsOut /* returns { kind: "clear", reason: "cancelled" } for cancelled shipments */, publish: { tag: "goods_out_confirmation", … }, … },
    { type: "work_order_confirmation", owns: atStage("90", isWorkOrder), needs: ["headerAttachments", "pairedReceipt"], … },
  ],
};
```
Reading that literal answers, for any type: what SNAP calls it makes (its `needs`), when it applies
(`owns`), how it publishes, and whether a missing origin is an error. That is the operability win.

```ts
// pipeline.ts — one function, nine stages, no branching on ConfirmationType anywhere
export async function pollTrack<E>(track: Track<E>, target: PollTarget, snap: ISnapAPI, deps: Deps): Promise<Announced[]> {
  const rows       = await readQueue(track.lane, snap);                       // read
  const fresh      = await dropClaimed(rows, target, deps.claims);            // pre-filter
  const resolved   = await resolveEntities(track, fresh, snap, target);       // resolve (+ cross-tenant)
  const owned      = discriminate(track, resolved);                           // → Array<[TypeDefinition, Resolved]>
  const enriched   = await enrich(track, owned, snap);                        // per-entry isolation starts here
  const withOrigin = await resolveProvenance(track, enriched, deps.routing);  // one store read per page
  const mapped     = mapAndValidate(withOrigin);                              // pure; per-entry isolation
  const eligible   = await gate(mapped, target, deps.connectors);             // connector eligibility, once
  return announce(group(eligible), target, deps);                             // the only side effects
}
```
Isolation lives at three boundaries and no others: **per business** (a business's track failing loses
only that business's cycle), **per entry** (from `enrich` through `mapAndValidate`), **per group** (in
`announce`). Today's fourth boundary (per consumer) disappears because there are no consumers.

## The awkward cases, and where they land
| Case | Today | Target |
| --- | --- | --- |
| FGR keys provenance off the work order (`receipt.Prime`) | override in the handler | `provenanceKey` on the FGR type; the provenance stage reads per type, so one page read still |
| WOC probes up to 3 receipt searches for the paired R10, swallowing failures | inline try/catch in the handler | `pairedReceipt` enricher with `onFailure: "degrade"` — the mapper receives `undefined` and emits components-only, exactly as today |
| RGA's REH attachments serve both routing fallback and carrier tracking | fetched once in the handler, used twice | one `headerAttachments` enricher; provenance stage reads it for fallback, the mapper reads it for `RET_TRACK` |
| Goods-in fetches one consignment per receipt+line id | `chunkPromises` inside the handler | `stockConsignments` enricher does the same fan-out; the mapper does the matching (`goods-in.matching.ts`, unchanged, pure) |
| Goods-in zero-qty / goods-out cancelled clear the SNAP row mid-map | `disposer` called from inside `mapConfirmation` | mapper returns `{ kind: "clear", reason }`; `announce` executes it. Same timing within the cycle, no side effect in mapping |
| Stock adjustments have no routing and are broadcast | the one type missing from `expectsRoutingProvenance`; special-cased in prose | `routingAware: false` on the type, `provenanceKey: () => undefined`; nothing else special |
| Stock adjustment with unresolvable direction | returns `null`, re-polled forever, silent | `{ kind: "skip", reason: "unresolvable_direction" }` — metered every cycle, so it becomes visible and a product decision can be made |
| Customer id read from `bizId` / `businessId` / the movement's own field | three conventions across handlers | `track.ownerOf(entity)` decides once, after the cross-tenant check; the group key uses it. STOCK's `ownerOf` uses the field the canonical uses today until **G3** verifies it |
| Goods-out / goods-in publish under an alias tag | `if/else` inside the publish loop | `publish.tag` on the type; `announce` is branch-free |
| `isClearable` duck-type before claiming | `lodash.get("identifiers.queueId")` | every mapper stamps `queueId` today (verified across all 8), so the pipeline record carries `row.XDoc` as a typed field and every canonical is claimed — same behaviour, no duck-typing |
| Debug `/trigger` and `/check` | re-implement the poll | call `pollBusinesses(ids, { types, announce })`; `/check` is `announce: false` |

## Dropping: one vocabulary
```ts
type SkipReason     = "circuit_open" | "fetch_failed" | "not_returned" | "cross_tenant" | "claimed"
                    | "unowned" | "enrichment_failed" | "map_failed" | "invalid" | "unresolvable_direction";
type WithholdReason = "connector_unresolved" | "connector_ineligible" | "duplicate_claim";
type ClearReason    = "zero_quantity" | "cancelled";

function drop(ctx: DropContext, outcome: Outcome): void   // logs one event, meters one metric
// snap.confirmation.dropped{lane, outcome, reason, businessId}
```
The reasons are a closed list on purpose: a new reason is a review conversation, not a string.
Existing metric names that a dashboard or monitor reads stay emitted alongside until **G4** says
which can go. Fail-open is a property of a *gate*, declared where the gate is (the connector gate's
single `broadcastConfirmations` escape), never re-decided at a drop site.

## Announce: the only side effects
> SUPERSEDED 2026-10-05 — the sketch below predates Poller Clear-Down C2. Announce now has a second clear: once a
> group's publish resolves, `OutboundQueueClearer.clearPublished` PATCHes that group's published rows (allow-listed
> businesses, routed to a channel that subscribes to the type; broadcast/unrouted/no-subscription/`stock_adjustment`
> left for snap-adapter). U7 keeps both clears in dispose:
>
> ```ts
> const claimed = await claim(g, deps.claims);                 // claim BEFORE publish (INC-30)
> await publish(claimed, g.type.publish, attributes(g));
> await clear(g.outcomes.filter(isClear), deps.snap);          // mapper drops: zero-qty / cancelled
> await deps.clearer.clearPublished(g, claimed, deps.snap);    // C2: routed + allow-listed, never rejects
> ```
>
> The sketch is kept below as the original design.

```ts
async function announce(groups: Group[], target: PollTarget, deps: Deps) {
  return allSettled(groups.map(async (g) => {                 // per-group isolation
    const claimed   = await claim(g, deps.claims);            // claim BEFORE publish (INC-30)
    await publish(claimed, g.type.publish, attributes(g));    // one transport: the package PubSubRouter
    await clear(g.outcomes.filter(isClear), deps.snap);       // zero-qty / cancelled
    if (g.type.routingAware && !g.provenance) await reportManualOrigin(g, deps.failures);
  }));
}
```
Ordering pinned by scar tissue: claim → publish, and the whole cycle completes before the stage-2 ack.
A publish failure on one group is logged and metered and no longer aborts the rest of the cycle.

## What stays byte-identical (the contract pin)
Topics and `recordType` / `source` / `broadcast` attributes; `BifrostMessage` envelopes and
`metadata.recordType`; the claim key `confirmation-claim:{businessId}:{queueId}` and TTL; the Firestore
store doc shape and ids; the SNAP call set per type (plus, since C2, one `PATCH …/processed` per published routed row for an allow-listed business; the black-box mock business isn't allow-listed, so its counts are unchanged) (asserted by the black-box counts 56 / 21 / 40 / 11
and by a contract test per type comparing `needs` to the U0 inventory); `$top=1000` per read; the
600 s ack deadline; `confirmationsEnabled` fail-closed semantics.

## Testing model
- **Golden masters (U0):** for every type, fixtures + live payloads → exact canonical output on
  `master`, deep-equal. Any diff during U3/U4/U5 is a stop.
- **Mapper unit tests:** pure functions, no SNAP mock — the bulk of today's handler specs migrate here
  and get shorter.
- **Track tests:** a fake `ISnapAPI` recording calls; assert the call set per type equals its `needs`.
- **Pipeline tests:** one fake track exercising every stage's outcome paths (each drop reason once).
- **Black-box:** unchanged expectations through U1–U8; the arithmetic beside each count is the doc.

## Reviewer checklist (block on any)
- A class with behaviour where a literal + function would do.
- A generic type that needs a comment to read; prefer the simpler type and a runtime assertion.
- A `switch`/map over `ConfirmationType` outside `tracks/`.
- I/O, metrics or logging inside a `map` function.
- A drop that doesn't go through `drop()`.
- A `broadcastConfirmations` check outside the connector gate.
- A changed black-box count without its arithmetic written beside it.

## Open design questions (decide in the unit that meets them)
1. **`Enriched<E, N>` narrowing** — worth the generic, or use optional fields + a runtime assertion in
   the mapper? Decide in U3 with real code in front of us; rule 7 applies.
2. **Provenance before or after enrich?** This design says after (so fallback can read attachments the
   type already needs). If a type ever needs attachments *only* for fallback, it pays one fetch per
   entity on a store miss — acceptable; the store hit rate is the drain gauge for removing that path.
3. **Stock track ownership (G3)** — which movement field is the owner, and does cross-tenant apply.
4. **Debug `/check` output** — today returns raw confirmations; keep that or return the pipeline's
   typed records.
