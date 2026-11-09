---
ticket: none
title: Mongo store
service: tracking-service
status: active
created: '2026-11-06'
updated: '2026-11-06'
repo: /home/harry/code/fuse/tracking-service
worktree: /home/harry/code/fuse/tracking-service/.claude/worktrees/tracking-service-mongo-store
branch: hjf/tracking-service-mongo-store
base: origin/main
base_sha: a97baca06
pr: null
tags:
- waypoint
- plan
programme: Tracking Service
unit: D5
impl_model: opus
impl_effort: high
---
# none — Mongo store

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
<!-- What we are changing and why. Link the ticket. -->
Out-of-ticket. Programme unit **D5** of [[Bifrost/Tracking Service/Migration State|Tracking Service]] group D (Firestore → MongoDB Atlas). Build `*store.Mongo`, a MongoDB implementation of `storeopen.Backend` (`store.Store` + `store.ReturnStore` + `storeopen.Maintenance`, 41 methods), selected by `STORE=mongodb`. It honours the D5 row's must-haves: per-record transactions, a `seen` collection, record-scoped event docs, no shared documents, and stats aggregated from marks exactly as the memory store does.

D5 flips no environment. `STORE` stays `firestore` everywhere; the cutover is D7–D11. Proof: `make test-mongo` runs the whole store conformance suite green on Mongo. Mongo's served stats are byte-equal to the memory store's on the same corpus, in order and shuffled. Every binary runs with `STORE=mongodb` against a local replica set.

Design inputs: the D5 row (decided requirements), [[Handovers/2026-11-06-tracking-service-mongo.draft-design]] (where it differs, the Migration State wins), and [[Handovers/2026-11-06-tracking-service-mongo.dedupe-findings]]. This plan was drafted by a planning agent on 2026-11-06 and reviewed adversarially along three dimensions: history, factual grounding and increment structure. The reviews are folded in below.

## Acceptance criteria
<!-- Observable, checkable outcomes — not tasks. Numbered by order: increments cite them as
     (AC 2,4), and sign-off prints which criteria no increment claims. -->
- [ ] 1. **Aggregation is fast enough, or D5 stops.** Over ~600k synthetic marks (22 businesses, 30 days, a long reason-code tail), the marks aggregation for the 30-day all-business insights read set and the 7-day stats meets the agreed latency bar, measured locally and on the dev Atlas M10. If it misses, D5 stops and is replanned around `$merge` (Gate A).
- [ ] 2. **The conformance suite passes on Mongo.** Every `eachBackend` case in `internal/store` passes on Mongo with `liveCounters: true`, and the temporary pending list is gone:
  - `store_test.go`: Journey, Search, List, ConfirmationUnderAnotherSnapID, ByKey, Republishes, Channels, Attention, Lookup, LinesAndPreexisting, Insights, ReasonCap, Notes;
  - `store_returns_test.go`: ReturnJourney, ReturnLinkBySalesOrder, ReturnQueries, ReturnNotes;
  - Scopes, SortsAndWindows, AttentionLanes.
- [ ] 3. **Served stats equal the memory store's.** A differential test ingests the same corpus into memory and into Mongo, both in order and shuffled. `ReadCounters(false|true)`, Stats/Insights for every scope and day, StatsOnDay, InsightsOnDays and Businesses must be `reflect.DeepEqual`. The corpus is journey, seedCatalogue, channels, preexisting, the 55-code reason cap and rgaJourney.
- [ ] 4. **Each D5 must-have has a test that fails if it's broken.**
  1. `seen` is keyed by the per-item event id: `M-i` from a bulk message and `M-j`/`M-i-j` from a failure that embeds several records, on shipments and returns.
  2. `seen` is written in the record's transaction. After an abort (ErrNoMarks, a `uniq_*` violation, an injected failure) no `seen` or event row is left.
  3. An empty eventID writes no `seen` row and rewrites every time.
  4. Event docs are kept forever, and only `seen` has a TTL index.
  5. A first-insert race retries, and the store never returns `ErrUnprocessable`.
  6. A return patch naming an unknown shipment fails the transaction and creates no stub shipment.
  7. No shared document is written in a transaction. This one is covered by review, and no test can pin it; that is stated in the PR.
- [ ] 5. **Writes are exactly-once and concurrency-safe.**
  - 8 concurrent deliveries of one messageId give 1 event, 1 `seen` row and 0 duplicates.
  - A copy redelivered after more than 64 later copies is a no-op through `seen`.
  - Concurrent return and shipment applies, and a note added during an apply, both commit and keep their counts.
  - `runTxn` is bounded by its budget and the context.
- [ ] 6. **Every query shape uses an index.** Each query shape the store can issue explains to a plan with no COLLSCAN and no blocking SORT. That covers list, search, prefix, attention, counts, the marks `$match` and the Businesses `$group`.
- [ ] 7. **The import primitive can't overwrite live data.** `ImportShipment`/`ImportReturn` are idempotent while the store isn't live. After any live write (Apply, ApplyReturn, AddNote, UpdateNote) to a record, a re-import skips that record and leaves its notes alone. The store also exposes a liveness signal that D8 can refuse a whole run on (G9).
- [ ] 8. **Every binary runs on Mongo.** `api`, `redrive`, `recompute-stats`, `backfill-upgrade` and `backfill-attention` open Mongo via `storeopen` and run against a local replica set. recompute-stats and backfill-upgrade have Mongo twins of their emulator tests.
- [ ] 9. **Docs describe the Mongo path** from the increment that makes them true. That covers the README, the repo and `apps/api` CLAUDE.md, and the index rule.

## Affected boundaries
<!-- Components, paths and contracts this touches. Wikilink existing explainers; do not restate
     their contents. If this names a topic, endpoint, canonical type, collection, inter-service
     dependency or shared package, sign-off will prompt for the Fuse MCP data file too. -->
- **New in `apps/api/internal/store`:**
  - `mongo.go`, `mongo_marks.go`, `mongo_query.go`, `mongo_indexes.go`, `mongo_returns.go`, `mongo_notes.go`, `mongo_import.go`;
  - their `_test.go` files;
  - a `mongo` entry in `backend_test.go`.
- **Existing store files that change:**
  - `bson` tags beside the `firestore` tags on the fs* structs (`firestore.go:54-147,990-1006`, `firestore_returns.go:14-67`);
  - the pure helpers moved out of `memory_marks.go` (no behaviour change).
- **Other code paths:**
  - `internal/storeopen/storeopen.go:41-42`: the `ErrNotImplemented` stub goes;
  - `cmd/api` wires an `OnRetry` metric hook;
  - `Makefile` `mongo-test` scope;
  - `apps/api/CLAUDE.md`, repo `CLAUDE.md:5` (the index rule) and `README.md:84,90`.
- **Contracts to honour:**
  - the ApplyFunc re-run contract (`store.go:50-52`);
  - marks on every non-noop write (`store.go:29-30`, `ErrNoMarks` at `marks.go:16`);
  - an empty eventID means a rewrite (`firestore.go:354-358`);
  - `validID` (`firestore.go:347`);
  - ack/nack classification (`push.go:56-64`; never wrap `ErrUnprocessable`);
  - Firestore's ordering of events (`Limit(1000)`, doc-id order) and notes (`OrderBy createdAt asc`, `Limit(1000)`; `firestore.go:674,1069`).
- **Reference semantics, copied exactly:** `Tally.Add`/`merge`/`CapReasons` (`marks.go:32-129`), and `tallyMarks`/`served`, the row rules, `ReadCounters`/`ReplaceCounters`/`prune` (`memory_marks.go:22-184`).
- **Atlas user:** `readWrite` only (`iac/projects/tracking-service/mongo.tf:84-87`). That covers createIndex and createCollection, but not collMod.
- **11 new Mongo collections.** fuse-mcp `database-collections.json` needs them when they go live; that's D11, not here. See Assumptions.

## Assumptions & uncertainty
<!-- One line each, with how it was established. A genuine product or domain question goes here
     as UNRESOLVED: and is raised with the user, never invented. -->
- **The Mongo store satisfies 41 methods:** Store 19 (`store.go:252-285`), ReturnStore 18 (`:222-242`), Maintenance 4 (`storeopen.go:19-24`). recompute-stats' `counterStore` is the same set, and backfill-upgrade's `idScanner` (`cmd/backfill-upgrade/main.go:128-131`) is a subset. Established by planner and factual-review source reads.
- **The fs* structs can carry `bson` tags as they are:** plain `firestore:"x"` tags, no sentinels, and map keys without dots. None has an `_id`, though, so each Mongo doc is written through a wrapper struct, `{ID string \`bson:"_id"\`; fs* \`bson:",inline"\`}`. Without it, `InsertOne` would mint an ObjectID. `toFSReturn` already forces `SearchKeys` to `[]string{}` (`firestore_returns.go:88-89`). Factual review.
- **Times are int64 Unix µs,** through a v2 codec registry set on the client **and** the database: `db.RunCommand` explain uses the database registry. The decoder returns UTC. `seen.expireAt` is the one BSON date, because TTL needs one. This is exactly Firestore's precision, so the µs comparisons in `core/deliveries.go:158-163,195-200` stay correct. It also closes R10 by design: R10 already named int64 µs as the fallback, so D9's "ms timestamps" diff class goes away. Factual review confirmed `bson.NewRegistry`, `RegisterTypeEncoder` and `SetRegistry` in v2.
- **Concurrent in-transaction writes to one document give WriteConflict 112** with the `TransientTransactionError` label. That covers two first inserts, and a shipment replace against a return's patch. DuplicateKey is not generic: it is retried **only** on the record collection's `_id` during Apply/ApplyReturn's first insert. On a note insert, the import's guarded upsert or a `uniq_*` index it is deterministic and returned without retry. `keyPattern` is read from `WriteError.Raw`, because `IsDuplicateKeyError` can't tell indexes apart. Factual review.
- **Snapshot isolation doesn't validate reads.** A return that reads a shipment through `ShipmentReader` but doesn't patch it won't conflict with a concurrent shipment write, where Firestore's transaction would. The link reads identity fields, which never change after creation, so a stale read can't mislink. The leftover case: a return and its shipment's first event arriving at the same moment can miss the link until the return's next event. Inc 5 tests this with a concurrent-first-create case and records what it sees. Factual review; the impact is reasoned, not measured.
- **Shipment query pushdown is not "every field".** With a channel, only `Channel` is pushed down (`query.go:220-223`, `store.go:142`). With a custom sort or window, only business is pushed, plus status when business is set (`query.go:227-230`). Returns push only business and status (`returns_query.go:92-94`). The Mongo filter builders and the explain-test shapes follow this exactly, so pages match Firestore page for page for D9. Factual review.
- **There are 16 updatedAt list indexes:** the 15 non-empty subsets of {businessId, status, failed, orphan} (`firestore.go:935-944`) plus the unfiltered `{updatedAt:-1,_id:-1}`. A reverse scan serves ascending order. Factual review.
- **Business `lastSeenAt` becomes `$max(createdAt)` per business across shipments and returns.** Firestore and memory overwrite one field with the `UpdatedAt` of the latest *new* record (`firestore.go:421`, `memory.go:87`), which depends on arrival order. G5 already accepted that this value is approximated, and `$max(createdAt)` keeps its meaning of "last new record". `$group` emits `shipmentCount` and `returnCount` separately (`openapi.yaml:1753`). It becomes a D9 diff class. History and factual reviews.
- **recompute-stats on Mongo copies memory's `ReplaceCounters`** (`kept = c − have`, `memory_marks.go:139-153`). Marks written by concurrent ingest between the rebuild and the replace would become negative kept entries. That is safe only because prod recompute already runs with ingest held (Scar tissue; G5 policy), and the Mongo docs say so. History review.
- **The frozen `duplicates` history (G4)** lives in `keptCounters`/`returnKeptCounters`, written by D8 through `ImportKept`. `serve()` merges it on read, as memory merges `kept`, and recompute-stats keeps `duplicates` (`cmd/recompute-stats/main.go:128,157-161`).
- **Events `_id` is the string `docID + "/" + eventID`,** with separate `r` (recordId) and `e` (eventId) fields. That is the D5 row's composite `{recordId, eventId}` in substance; a sub-document `_id` would make the per-record range read awkward. It's unambiguous because `validID` refuses `/` in record ids.
- **Copies must stay cheap:** 78% of ingest is identical copies (known-context), and the ~40/s cap is why group D exists. So each copy writes the record and `seen`, and skips the marks write when a stored `marksHash` is unchanged. That skip is in scope, not optional. History review.
- **No push-wide deadline in `push.go` in D5.** One bulk push can apply up to 100 items, each bounded by `TxnBudget` (10 s), so a slow push can outlive the 30 s ack deadline and be redelivered while it is still running. That is safe, because `seen` and the event docs serialise it, and putting a deadline in `push.go` would change the live Firestore path. D10's burst rehearsal measures push duration; add a deadline then if it's needed.
- **No schema validators in D5.** Changing one later needs `collMod` (dbAdmin), the `_id` identity plus the partial unique indexes are the guarantee, and D8's importer validates identity (G9). The factual review thinks a validator could be set at `createCollection` time (low confidence). Not pursued.
- **D5 is not the place for the note freeze during the hard-cut hold (G9: `INGEST_HOLD` 503s only the push endpoint), and no unit owns it today.** Flagged to the programme as a Waiting-on-Harry item.
- **Whether the dev Atlas M10 is reachable from a workstation** for the benchmark is unchecked. G6 notes that no Fuse Atlas stack declares an access list. If it isn't reachable, the Gate A decision rests on local numbers and is marked provisional until D10.
- UNRESOLVED: **the latency bar for Gate A** (raised with Harry). What p95 counts as "fast enough" for marks aggregation serving fuse-ui's 30-day insights and 7-day stats? Recommendation: p95 ≤ 1 s for the 30-day all-business insights read set and ≤ 500 ms for the 7-day stats, on the dev Atlas M10 at ~600k marks. If `$merge` turns out to be needed, how stale past days may be is a separate product call, made then.

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
> SUPERSEDED 2026-11-09 — regrouped for speed (Harry: "finish it today"). Gate A is gone. Build order and parallelism:
> - **W1 foundation + shipment write path** = increments 2 + 3 (minus the Stats wiring), plus `ShipmentIDs`/`ReturnIDs`. Branch `hjf/mongo-store-foundation`.
> - **W2 marks aggregation** = increment 1 without the benchmark or gate: the `memory_marks.go` refactor, the Mongo pipeline as functions over a collection, and the differential test against memory's tally. Built **in parallel with W1** off `main`. Branch `hjf/mongo-store-marks`.
> - **W3 queries + returns** = increments 4 + 5, plus Stats/Insights wiring through W2's functions, after W1 and W2 merge. A 2-PR stack is fine.
> - **W4 notes, kept counters, import, opener, binaries, docs** = increments 6 + 7, after W1 and W2 merge, **in parallel with W3**.
> - Each W is merged as soon as its checks are green and `review-panel` finds nothing blocking. The text below is kept as the detailed spec each W implements.

Seven increments of about 500–700 lines each, about 3,500–4,000 lines in all, one PR each. That is the top of the 3–7 range, because D5 is large. The Firestore store alone is about 1,650 lines before tests.

**Shared mechanism for increments 2–6:**
- `backend_test.go` gets a `mongo` entry: `openMongo` skips unless `TEST_MONGODB_URI` is set, opens a fresh database `it<nanos>` per test, runs `EnsureIndexes`, and drops the database on cleanup.
- A temporary `pending` map, keyed `Test` or `Test/subtest` with the missing method as its reason (e.g. "needs SearchKeys"), skips what isn't built yet. Unbuilt methods return an unexported `errNotYet`.
- Each PR states its pending delta. Increment 7 deletes the map.

**Gates on every PR:**
- `make fmt-check vet lint test-race test-emulator` (Firestore must stay green under the new tags);
- `make test-mongo`;
- a green `api-mongo` run linked in the PR evidence, because that check isn't required (see Waiting on Harry);
- `terraform fmt -check -recursive iac` where `iac` is touched.

Every merge rolls prod, so never merge while a Deploy run is in flight (Scar tissue).

- [x] 1. **Marks shape, aggregation pipeline and benchmark** (AC 1). These are pure functions over a marks collection; nothing touches `Store` yet. — done: a97baca
  - **Refactor, no behaviour change.** Move the pure helpers out of `memory_marks.go`: `serve(marks, kept)`, which does merge then `CapReasons`, and the row projections `statsOf`, `insightsOf`, `statsOnDayOf` and `insightsOnDaysOf`.
  - **Marks doc shape:** `{_id: docID, businessId, marksHash, m:[{d, t:"s"|"i"|"r", k, b, ch, ex, n}]}`.
  - **Pipeline:** `$match` on `m.d` and business, `$unwind` with `includeArrayIndex`, `$match`, then `$group` by `{biz,d,t,k,b,ch}` with `$sum n` and `$min {id,i,ex}`.
  - **Tally assembly:** rows sorted by `(first.id, first.i)`, which reproduces `Tally.Add`'s first-example-in-id-order rule.
  - **Tests and benchmark:**
    - A differential test: random synthetic `Marks` are fed to the memory `tallyMarks` and inserted into Mongo, and the aggregation must be `DeepEqual`.
    - `BenchmarkMongoMarks*`, gated by `MONGO_BENCH=1`: it bulk-loads ~90k records and ~600k entries, then times the 30-day insights read set and the 7-day stats and saves explain `executionStats`. It runs locally and, if reachable, on the dev Atlas M10.
  - verify: `make test-race`, where memory's marks tests stay green through the refactor; `make test-mongo` (differential); `MONGO_BENCH=1 TEST_MONGODB_URI=… go test -run '^$' -bench MongoMarks -benchtime 20x ./internal/store/`, with the numbers and explain output recorded in Evidence.
      gate: Gate A — the latency bar is agreed with Harry and met on these numbers (dev Atlas, or local marked provisional). If it's missed: stop, and replan around a `$merge` rollup with Harry's staleness call.
            [ ] confirmed
- [x] 2. **Scaffolding** (AC 2,9). The groundwork the later increments build on: — done: a97baca
  - `bson` tags on every fs* struct, `fsReturn` included;
  - `_id` wrapper structs;
  - the µs codec on the client and database registries, with UTC decode;
  - the `Mongo` type with `NewMongo(db, MongoOptions{Now, TxnBudget, OnRetry})`, `EnsureIndexes` (empty for now) and `errNotYet` stubs, so `*Mongo` satisfies `storeopen.Backend`;
  - `openMongo` and the pending map;
  - `make mongo-test` scope set to `./internal/store/... ./internal/storeopen/...`;
  - the stale `liveCounters` comment fixed (`backend_test.go:21,28`).
  - verify: `make test-emulator` green, proving the tags are inert to Firestore; a codec round-trip test (sub-µs input → `Truncate(µs)`, UTC, nil and zero time, `map[string]time.Time`, `*time.Time`); `make test-mongo` runs the suite with every case pending and none failing.
- [x] 3. **Shipment write path, `seen`, reads, stats wiring** (AC 2,3,4,5,9). The Apply transaction, on `runTxn`: — done: a97baca
  - **Transaction steps:**
    1. Point-read `seen`, then the event `_id`, when eventID ≠ "".
    2. Read the record, then run `fn`. A Noop writes nothing.
    3. Nil marks → `ErrNoMarks`.
    4. Insert the record, or replace it asserting matched == 1.
    5. Insert the event if there is one.
    6. Upsert the marks unless `marksHash` is unchanged.
    7. Insert `seen` with `expireAt` = injected clock + 8 d.
  - **`runTxn`** is the store's own loop, not the driver's `WithTransaction`, whose 120 s retry outlives the 30 s ack deadline. It uses snapshot reads, majority writes and the primary. Its budget is min(ctx deadline, `TxnBudget` = 10 s) with jittered backoff. It retries the transient label and WriteConflict, retries only the commit on `UnknownTransactionCommitResult`, and calls `OnRetry`.
  - **Methods:** Get, GetMany and Events (an `_id` range then `SortEvents`, limit 1000). Stats, Insights, StatsOnDay and InsightsOnDays are wired over increment 1's functions.
  - **Indexes:** `seen` `{expireAt:1}` with TTL 0; marks `{"m.d":1, businessId:1}`; `uniq_business_customer_ref` (partial on `keySource:"customer_ref"`, `customerRefNorm:{$gt:""}`).
  - **Mongo-only tests, one behaviour each:**
    - 8 goroutines with the same messageId;
    - 8 with distinct ids and the same content: 1 event, `Duplicates.received` = 7;
    - a bulk `confirmation_ready` of 3 records (`M-0..M-2`) and its redelivery;
    - a failure wrapper embedding 2 records (`M-0`/`M-1`, `M-i-j`);
    - 70 copies, then the first copy redelivered;
    - Refresh with "" run twice;
    - the `expireAt` anchor;
    - ErrNoMarks leaves nothing;
    - a pre-seeded `uniq_*` violation fails fast, isn't `ErrUnprocessable`, and leaves no `seen` or event row;
    - an injected post-`seen` failure leaves no `seen` row;
    - a context deadline bounds `runTxn`;
    - only `seen` carries a TTL index;
    - an identical copy skips the marks write.
  - **Plus:** the shipment-side differential (journey, seedCatalogue, channels, preexisting, the 55-code cap; in order and shuffled), compared on the marks aggregation directly, because `Querier.Stats` also needs the counts from increment 4. `BenchmarkMongoCopies`, gated, runs a copy-heavy write load at 6× (~46/s) and records its numbers.
  - **Docs:** `apps/api/CLAUDE.md` ("no TTL", "dedupe is the event doc") and README:90 updated for Mongo in this PR.
  - **Pending lifted:** ConfirmationUnderAnotherSnapID, LinesAndPreexisting, Journey, Republishes and Lookup (counter subtests still skip). ByKey's exact-mode subtest stays pending on SearchKeys.
  - verify: `make test-mongo`, `make test-emulator`, gates.
- [x] 4. **Shipment queries, counts, indexes, explain test; counters on** (AC 2,6). `mongo_query.go` holds List, SearchKeys, SearchPrefix, ListAttention, CountAttention, CountActionNeeded, CountOrphans, ShipmentIDs and Businesses. — done: a97baca
  - **Filters and paging:**
    - Filter builders follow Firestore's pushdown exactly (Assumptions) and take a collection spec, so increment 5 reuses them for returns rather than refactoring them.
    - Keyset paging is `(f < v) OR (f == v AND _id < id)`.
    - ns bounds round to µs: ceil for `>=` and `<`, floor for `<=`.
  - **`mongo_indexes.go`** is a declarative list: the 16 updatedAt indexes, with the `failed`/`orphan` subsets partial, plus createdAt ×3, channel ×2, searchKeys ×2, prefix ×2 (separate from the partial unique index), attention ×2, actionNeeded (partial) and `{businessId, createdAt, _id}` for Businesses.
  - **`mongo_explain_test.go`** enumerates every shape the builders can emit, including the marks `$match` and the Businesses `$group`. It explains each on ~200 seeded docs and asserts that the winning plan has no COLLSCAN and no blocking `SORT`. It handles SBE output (`winningPlan.queryPlan`) and explains `count` for the counts. Index coverage is checked against the candidate plans, not the winner, to avoid planner-race flakes.
  - **Flip the Mongo backend to `liveCounters: true`.**
  - **Pending lifted:** Search, List, Channels, Attention, ByKey, Insights, ReasonCap, Scopes, AttentionLanes, plus the counter subtests from increment 3. SortsAndWindows stays pending on its returns subtest.
  - **Docs:** the repo `CLAUDE.md:5` index rule gains its Mongo half: declare in `mongo_indexes.go`, and the explain test fails otherwise.
  - verify: `make test-mongo`, gates.
- [ ] 5. **Returns** (AC 2,3,4,5). This is ApplyReturn with a transaction-scoped `ShipmentReader` (findOne, plus a sorted, limited find on the session).
  - **Linked-shipment patches:** `updateOne({_id}, {$set:{returnsJson, returnCount}, $unset:{importedAt}}, upsert:false)`, which errors unless `MatchedCount == 1`. Memory skips unknown ids (`memory_returns.go:62`); Mongo follows Firestore's `tx.Update`, so this test stays Mongo-only.
  - **Methods and indexes:** the return queries and counts through increment 4's builders; ReturnIDs; return marks and ReturnStats/ReturnInsights/OnDay(s); the return indexes (`uniq_business_rga` partial on `keySource:"rga_number"`), with their explain shapes.
  - **Tests:**
    - a patch to an unknown shipment fails the transaction (no stub, no return written);
    - a return apply concurrent with an apply on its linked shipment: both commit, and `returnCount` survives;
    - a returns bulk booked-in (`M-i`) and its redelivery;
    - a return and its shipment's first event arriving concurrently, with the result recorded (write-skew note);
    - the rgaJourney differential, which completes AC 3.
  - **Pending lifted:** ReturnJourney, ReturnLinkBySalesOrder, ReturnQueries, SortsAndWindows.
  - verify: `make test-mongo`, `make test-emulator`, gates.
- [ ] 6. **Notes, kept counters, import primitive** (AC 2,4,7).
  - **Notes** go in `mongo_notes.go`. Note docs have `_id` = `docID/noteID` plus `r` and `createdAt`; the index is `{r:1, createdAt:1}`; reads are `createdAt` asc, limit 1000, matching Firestore. The methods are AddNote/UpdateNote and their return twins, each in one transaction:
    - AddNote reads the parent (ErrNotFound if it's missing), inserts the note (DuplicateKey is deterministic, not retried), `$inc`s noteCount/openNoteCount, `$set`s lastNote when `RefOf(note).Newer`, and `$unset`s `importedAt`.
    - UpdateNote with `openDelta == 0` writes nothing (`firestore.go:1112-1117`). Otherwise it updates `resolved`, `$inc`s openNoteCount and `$unset`s `importedAt`.
  - **Kept counters:** `keptCounters`/`returnKeptCounters` hold arrays, not maps, because reason codes contain dots and spaces. This increment adds ReadCounters, ReplaceCounters (memory's semantics) and `ImportKept`, and makes the kept/replace cases from `memory_marks_test.go:145-184,212-234` backend-generic.
  - **Import primitive:** `ImportShipment`/`ImportReturn` run one transaction that first checks the record (absent, or present with `importedAt`). It then replace-upserts the record stamped with `importedAt`, plus its marks; inserts events with insert-if-absent; and writes notes only when the record passed the guard. Event writes beyond the transaction's size go in byte-bounded batches, still only after the guard passes.
  - **Liveness signal:** `Live(ctx)` is true once any `seen` row exists. The import never writes `seen`, and the first live apply does, so D8 can refuse a run on it (G9).
  - **Tests:** re-import is idempotent; after an Apply, an ApplyReturn, an AddNote and an UpdateNote (one test each), a re-import skips the record and leaves its notes unchanged; `Live` reads false after an import and true after one apply.
  - **Pending lifted:** Notes, ReturnNotes.
  - verify: `make test-mongo`, gates.
- [ ] 7. **Opener, binaries, docs** (AC 2,8,9).
  - **`storeopen.Open` for mongodb:** connect, ping the primary, `NewMongo`, `EnsureIndexes`, and `Disconnect` on close. `ErrNotImplemented` goes, and `storeopen_test.go:32-38` becomes an open and ping test.
  - **Metrics:** `cmd/api` wires `OnRetry` to a transaction-retry/WriteConflict metric through the existing observability package, so metrics stay in-service.
  - **Twins of the emulator tests, both required:**
    - recompute-stats, including "duplicates are kept" (seeded through `ImportKept`) and `TestRecomputeRewritesStaleCodesWhoseTotalsAgree` (the `0585898` scar);
    - `backfill-upgrade -all`.
  - **Build:** `mongo-test` adds `./cmd/...`. Delete the pending map.
  - **Docs:** README:84 (the binaries no longer refuse) and the "Stats are Firestore increments" / conformance-suite lines. recompute-stats on Mongo still needs ingest held.
  - verify: `make test-mongo`. Then a manual run against `make mongo-up` with `STORE=mongodb`:
    - `go run ./cmd/api` plus `scripts/replay-fixture.sh`, then curl the shipments, stats, insights, businesses, returns and notes endpoints;
    - `recompute-stats -dry-run`, then a real run;
    - `backfill-upgrade -all -dry-run`;
    - `backfill-attention -dry-run`;
    - `redrive` against the Pub/Sub emulator.

## Verification
<!-- The single authority for evidence. Increment lines carry `— done: <sha>` and nothing else.
     Check-selection order lives in verification-menu.md — do not restate it here. -->

### Evidence
<!-- Newest first, dated. One bullet per check actually run, opening with what it discharges.
     "Suite green" alone is not evidence. Sign-off requires at least one dated bullet here. -->
- 2026-11-09 [W1/W2] **Drafts open, not merged (merges are Harry's; the agent is denied).**
  - **#24, the CVE fix:** `x/net` 0.62.0. The base-image `datadog-init` copy is allowlisted to 2026-11-16. 14/14 checks green.
  - **#25, W2 marks aggregation:**
    - matches memory's `serve(tallyMarks)` by `reflect.DeepEqual` on a seeded 600-record corpus (70 codes, so the cap bites);
    - 6 mutation checks fail as they should;
    - the explain check shows IXSCAN.
  - **#26 + #27, W1 scaffold and shipment write path (stack #28):**
    - 6 conformance cases run on Mongo, and 22 Mongo-only tests;
    - review-panel (backend, data, tests): looks good after the fixes in `d5b9f4c`.
    - **`d5b9f4c` fixes:** a test that redelivers after the seen row is gone and asserts no copy is counted (it fails with the event-doc fallback removed); a start barrier on the concurrent tests; `Events` checks existence with a projection.
    - **Gates on `d5b9f4c`:** `make fmt-check vet lint test-race` 0 issues; `make test-emulator` all ok; `make mongo-test` ok.
  - **Integration branch** `hjf/mongo-store-integration` = main + #24 + #25 + #27. W3 and W4 build on it.
  - **`make test-mongo` needs `docker compose`,** which the workstation lacks. Locally the tests run `mongo:8.0.13 --replSet` via `docker run` plus `make mongo-test MONGO_PORT=…`; CI uses compose.
- 2026-11-06 [baseline] **Today's Firestore-served latencies, for Gate A context:** prod `/api/v1/stats` 0.15–0.26 s and `/api/v1/stats/businesses` **8.5–9.0 s** (single curls at 15:41Z and 17:59Z); dev `/stats/businesses` 3.7 s. The Mongo Businesses `$group` should beat this, not match it.
- 2026-11-06 [plan] **Drafted and reviewed, not implemented.** A planning agent drafted 5 increments over worktree `a97baca`. Three independent reviewers (history, factual grounding, increment structure) checked it. Their findings are folded in, and the plan is now 7 increments with the benchmark first. The factual reviewer ran `go test ./internal/store/` (memory backend): it passes with 0 skips. No code has been written.

### Not verified
<!-- Stated, not papered over. "(none)" is a deliberate claim, and a fine one. -->
- **Everything in the ACs.** This is a draft plan, and no increment has started.
- **Whether the dev Atlas M10 is reachable from a workstation** for the Gate A benchmark.
- **The write-skew impact on return linking.** It is reasoned, not measured; increment 5 measures it.

## Decisions & deviations
<!-- Date-stamped, newest first — written by `wp decide`, and by hand when that is easier.
     Where implementation departed from this plan, and why. Source wins over the plan: correct
     the plan in the same increment and record the correction here. Legitimately empty at plan
     time. A decision worth defending in a review six months out belongs in a durable record
     instead — `wp decide --record`. -->
- **2026-11-09 — Gate A dropped, plan simplified (Harry):** "latency isn't a concern … we're overcomplicating this and being overly cautious — let's get it finished today." No benchmark gate and no `$merge`: stats are live aggregation over marks. Increments regroup into 4 PRs (see Increments), built in parallel where they don't depend on each other, and merged as each goes green.
- **2026-11-06 — Deviations from the D5 row, made knowingly:**
  - **An own `runTxn` loop, not the driver's `WithTransaction`:** its 120 s retry outlives the 30 s ack deadline, and it doesn't separate DuplicateKey by site.
  - **The row's (a)–(e) are reordered and split into 7 increments:**
    - (c), the marks benchmark, runs first as Gate A, because its outcome can change the marks doc shape that the write path writes;
    - (a) splits into scaffolding (2) and the write path (3);
    - (b) is 4, (d) is 5, and (e) splits across 6 and 7.
  - **Events `_id` is a string `docID/eventID` with `r`/`e` fields,** not a sub-document.
  - All from the 2026-11-06 reviews.
- **2026-11-06 — Draft open questions already decided elsewhere, dropped:**
  - recompute-equivalent served stats: G5;
  - fewer phantom duplicates through `seen`: the hard-cut and `seen` decision, R7 closed by design. Add it to D9's expected diff classes;
  - refusing a whole import run once live: G9;
  - int64 µs: R10's named fallback;
  - `lastSeenAt` approximation: G5. Only the mechanical formula was left, `$max(createdAt)`.

## Learnings
<!-- Durable facts about the service surfaced while planning, working or testing that are not
     already written anywhere in the vault — a gotcha, a constraint, a fragile edge, a confirmed
     or refuted hypothesis. Not restated doc content. Sign-off promotes each confirmed one into
     the matching durable doc, then clears it from here; a refuted one moves to ## Handback
     rather than being deleted. Legitimately empty. -->
- **The fs* doc structs have no `_id`/id-bearing field.** The id lives only in the Firestore doc path, so any non-Firestore persistence needs a wrapper that carries it.
- **Firestore reads notes in `createdAt` order (`firestore.go:1069`) but events in doc-id order (`:674`).** A port that range-reads both by id changes which notes come back past 1,000.
- **Shipment list pushdown narrows with a channel or a custom sort/window** (`core/query.go:220-230`). Pages differ by store unless every backend pushes down the same subset.
- **`backend_test.go:21,28`'s comment that memory turns `liveCounters` off once it aggregates marks is stale.** Memory aggregates marks and still passes every live-counter case.
- **`api-mongo` is not a required check and is off the nightly** (`api-code-quality.yaml:82-87`), so CI green says nothing about Mongo until it is made required.
