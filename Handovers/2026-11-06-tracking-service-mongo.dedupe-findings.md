---
tags: [handover, tracking-service]
date: 2026-11-06
source: workflow wf_f7a34f8a-8de (5 lenses + skeptics + critic, read-only)
---
# tracking-service dedupe verification — findings

Every claim below was challenged by an independent skeptic; the verdict follows each one. Code refs are at c52f644 (main before #19–#23).


## shipment-identity
- [holds/high] docid-pure-function: A shipment's doc id is a pure function of the normalised businessId and key, and every write addresses the doc by that id. No ingest, backfill or return-link path can create a second doc for a key that already has one, and nothing
    -> confirmed: I found no counterexample. keyed() (internal/core/events.go:208-222) is the only place a shipment DocID is set; the other DocumentID callers are returns_items.go:189 (returns), query.go:425/565 (reads
- [holds/medium] create-trio-same-record: create_record_request, create_record and create_acknowledge for one order carry the same record identifiers, so all three resolve to the same doc id.
    -> (not challenged)
- [broken/medium] fallback-key-no-merge: One order can end up in two docs: a message with no customer ref is keyed ~SO:{salesOrder}, a later message with the ref is keyed by the ref, and no code ever re-keys or merges the first doc.
    -> confirmed: The mechanism reproduces. The ref wins, else ~SO: (snapid.go:78-81). The key is fixed at creation (reduce.go:61-63). Nothing re-keys or merges a doc: the only consumer of KeySource is MissingCustomerR
- [risk/medium] shopify-raw-failure-name: A Shopify ingest failure is keyed by the raw order's `name` verbatim, but the order's successful create is keyed by whatever the connector's per-business mapping puts in order.customerRef. When a mapping derives the ref from anyth
    -> confirmed: The code path is as described. extract.go:110-116 keys a raw order with no order/identifiers section by `name`. In shopify-connector origin/main: failure-publisher.ts:48-71 and 83-91 embed the raw ord
- [risk/low] normalisation-gaps: Normalise only trims and uppercases. It folds case and edge whitespace (including NBSP and Snap's padded fixed-width fields) but leaves a leading '#', internal whitespace, NFC/NFD forms, full-width digits, zero-width characters an
    -> confirmed: Re-ran in Go. Normalise (snapid.go:25) leaves '﻿ABC', '​ABC', 'ABC  123', '#1001' and full-width '１００１' unchanged. It trims NBSP. NFC and NFD 'é' both become 'É' but stay different bytes. Node's trim(
- [holds/low] case-coarser-than-dedupe: Tracking folds case, while dedupe-service matches businessId + customerRef exactly. Refs that differ only by case or edge whitespace both pass dedupe but land in one tracking doc, so case never splits a shipment; Snap's determinis
    -> (not challenged)
- [holds/medium] confirmations-same-key: Pick, pack and goods-out confirmation_ready carry the CustomerRef and SalesOrder that snap-adapter wrote to Snap from the canonical order, and the ref cannot be truncated on the way. They resolve to the create's key.
    -> (not challenged)
- [holds/medium] confirmation-business-id: Confirmations take businessId from the tenant the poller serves. The poller drops any row whose Snap BizId (stamped from the create's identifiers.businessId) differs from that tenant, ignoring case. So a businessId alias or mismat
    -> (not challenged)
- [risk/low] sftp-business-from-file: sftp-connector takes identifiers.businessId from the mapping, which can read a file column, and never reconciles it with metadata.customer. If the file value differs from the tenant, the create is keyed under the file's business a
    -> confirmed: The mechanism holds. The skeleton has businessId '' (sales-order.factory.ts:17), and the fixture maps the business_id column to identifiers.businessId (translator-config.fixture.ts:15). Nothing in the
- [holds/medium] failures-same-key: Delivery and create failures from fapi, sftp-connector, the poller and snap-adapter embed the canonical record, and shopify's confirmation_made republishes the parsed confirmation. Each embedded record is keyed exactly as its read
    -> (not challenged)
- [risk/low] snap-fallback-only-snap-native: A ~SNAP:{shipmentId} key can only come from a confirmation with neither a customer ref nor a sales order. The create side cannot derive a Snap id without a ref, so a ~SNAP doc never shadows a Fuse-created order. One exception: on 
    -> confirmed: The create side cannot produce a ~SNAP key. orderItem passes only the derived Snap id, and SnapShipmentID errors when both ref and SO are empty (snapid.go:35-37; events.go:185-187, 198). ShipmentKey t
- [risk/low] key-collisions-overmerge: The opposite failure, two orders sharing one doc, is possible at the edges: DocumentID maps '/' to '_', so businesses 'A/B' and 'A_B' share ids, and a real customer ref typed as '~so:123' normalises to the same key as sales order 
    -> confirmed: Both collisions are real in the code. DocumentID replaces '/' with '_' after Normalise (snapid.go:102), so 'A/B' and 'A_B' share ids. A customerRef '~so:123' normalises to '~SO:123' (snapid.go:78-79),
- [holds/medium] mongo-id-preserves-identity: Keeping _id = today's doc id carries identity over unchanged. MongoDB's unique _id index enforces at most one doc per key, just as Firestore's addressing does, and an idempotent import upsert on _id cannot mint new ids. This holds
    -> (not challenged)
- [risk/high] mongo-seen-keyed-by-messageid: A seen collection with a unique key on the bare Pub/Sub messageId will lose records. One message carries up to 100 confirmations for different shipments, and each record is applied in its own transaction under eventID messageId-i,
    -> confirmed: The facts check out. The poller publishes pages of up to ANNOUNCE_PAGE_SIZE=100 records as one message (confirmations.service.ts:325-356; confirmations/constants.ts:35). A JSON array record is decoded
- [risk/medium] mongo-first-insert-race: Two messages for a new order can race to insert the same _id. The duplicate-key or WriteConflict error must be retried or nacked, never classified as unprocessable, because the push handler acks unprocessable messages and the losi
    -> confirmed: The ack/nack mechanics are as stated. push.go:56-59 acks anything that errors.Is ErrUnprocessable, including through the errors.Join at ingest.go:125. push.go:60-64 nacks everything else. Firestore re
- [risk/low] mongo-import-legacy-scheme: The first build keyed docs {BIZ}__{SnapShipmentId}; the switch to base64 customer refs landed the same day. Any doc written under the old scheme that survived in Firestore would be imported as a second doc for the same order.
    -> refuted: The code history is right: acce5c4 (2026-10-05 14:52) used DocumentID(biz, snapShipmentId) (git show acce5c4:apps/api/internal/core/snapid.go:53-56), and 32dee64 changed the scheme 66 minutes later. T

## return-identity
- [holds/low] rga-key-one-doc: A return create or confirmation that carries businessRgaNumber is keyed by DocumentID(Normalise(businessId), Normalise(RGA)), so every event for one business + RGA folds into one return document, inside one transaction that checks
    -> (not challenged)
- [risk/high] seen-key-bulk-elements: The poller's booked-in confirmation_ready is a bulk array. Each element becomes its own item with event id messageId-i (a failure with several embedded records adds -j) and its own transaction, so a 'seen' collection keyed on the 
    -> confirmed: I could not refute it. A JSON array record decodes as Bulk (internal/core/decode.go:101-106). Each element gets event id messageId-i (internal/core/returns_items.go:100-104), and a failure with severa
- [risk/medium] empty-rga-split: Tracking treats an empty or whitespace businessRgaNumber as missing and keys the create by identifiers.id. snap-adapter's `??` chain only skips null/undefined, so Snap gets SupplierRef "". The poller then sends ReceiptId (or "") a
    -> confirmed: The code path reproduces. str trims to "" (internal/core/extract.go:46-49), so the create falls back to identifiers.id (internal/core/returns_items.go:148-150). The canonical schema permits "" (busine
- [risk/low] fallback-key-shares-rga-keyspace: When the RGA number is missing, the create's key is identifiers.id, else customer.reference. It is stored unprefixed, in the same keyspace as real RGA numbers (ReturnKeySourceOf calls it rga_number), so it can merge with a differe
    -> confirmed: The fallback value becomes RGANumber (internal/core/returns_items.go:148-150) and is keyed rga_number (:180-181). Only the ~RCPT: prefix is distinguished (:44-50), and the fallback is flagged rgaMissi
- [risk/low] no-key-create-skipped: A create with no RGA number, no identifiers.id and no customer.reference cannot be keyed. It is skipped as unprocessable and acked, so no return document is ever made for it. A confirmation can still create a `~RCPT:` orphan, but 
    -> confirmed: With no customerRef and no RGA, SnapShipmentID returns ErrNoReference (internal/core/snapid.go:34-37), so the receipt is "". firstStr over identifiers.id and customer.reference also returns "" (return
- [risk/low] snap-receipt-identity-wider: Snap's receipt id is derived from businessId + connectorId + customer.reference + RGA, which is wider than tracking's businessId + RGA. Two Snap receipts for one RGA fold into one return, and that return keeps only the newest conf
    -> confirmed: snap-adapter derives the receipt id as createDeterministicId(biz, connectorId, customer.reference, businessRgaNumber) (return-goods-authorization.service.ts:49-54), and tracking ports the same inputs 
- [risk/medium] return-and-shipment-ids-share-formula: Returns and shipments build _id with the same formula, {BIZ}__base64url(key). Today they cannot collide only because they live in separate Firestore collections. In Mongo, returns must stay in their own collection.
    -> confirmed: Both use DocumentID(business, key) = NORMALISED_BIZ__base64url(Normalise(key)) (internal/core/snapid.go:101-104): returns at returns_items.go:189 and shipments at events.go:221. A shipment's customer-
- [holds/low] link-cannot-create-shipment: Linking cannot create a shipment today. LinkReturn only patches shipments it has just read in the return's transaction, the Firestore patch is tx.Update (which fails on a missing doc), and the memory store skips unknown ids.
    -> (not challenged)
- [holds/low] link-no-double-count: Linking cannot duplicate a return on a shipment. The ref is upserted by return id, and the return is counted once through Ledger.CountedOn. When the match changes, the return is removed and decremented on the old shipment and adde
    -> (not challenged)
- [risk/low] link-wrong-shipment-gaps: The link can attach to the wrong shipment in three edge cases. The staging guard (originalPurchaseOrder == RGA) cannot fire for a confirmation-only `~RCPT:` return. A customer-ref match wins over a sales-order match. Sales-order a
    -> confirmed: All three gaps hold in code. (1) For a ~RCPT-keyed confirmation, applyReturnConfirmation sets no RGA fact (returns_reduce.go:234-236, 242-246), so RGANumberNorm is "" and Key is '~RCPT:X'. The guard o
- [risk/medium] return-txn-spans-shipments: The design's 'one transaction over a single record's docs' does not hold for returns. A return write also reads the linked shipment (a point read plus a searchKeys query) and writes up to two other shipment docs, the business doc,
    -> confirmed: The return apply gets a ShipmentReader on the same transaction (firestore_returns.go:233), reads shipments (returns_link.go:24,38,57,61), and writes shipment patches, the business doc and counters in 
- [risk/medium] new-return-race-dupkey: The service subscribes before and after the deduper, so a new return's create_record_request and create_record can race. Firestore retries the loser, which then sees the doc and does not count it as new. In Mongo, the loser's writ
    -> confirmed: Both pre-dedupe and post-dedupe topics are routed to returns (returns_items.go:21-22). cur is nil when the record is not found (firestore_returns.go:220-231). That produces NewReturn (returns_reduce.g
- [risk/low] cutover-copy-idempotency: After the hard cut, held messages redeliver. Messages already applied in Firestore are caught only by the per-record checks that the import carries over: the event doc, and for a republished copy (which writes no event doc) Timeli
    -> confirmed: The core point holds: a 'seen' collection that starts empty catches neither kind of resend. A copy writes no event doc and goes on CountedIDs, capped at 64 (dedupe.go:22, 261-267). A normal event is c
- [risk/low] backfill-skips-link-refresh: The post-import `backfill-upgrade -all` and `recompute-stats` re-derive a return without its ShipmentReader. The status/bookingState copy in the linked shipment's returns list can therefore go stale until the return's next event. 
    -> confirmed: RefreshReturnStale ignores the reader (`_ store.ShipmentReader`) and returns a ReturnWrite without Shipments (internal/core/ingest.go:253-262). recompute-stats does the same at cmd/recompute-stats/mai
- [holds/low] business-scope: Return and shipment business ids are normalised the same way, and the link only looks within the return's own business, so a return cannot attach to another business's shipment.
    -> (not challenged)

## message-dedupe
- [holds/high] a-two-layers: (a) Two layers apply per record. Layer 1 is item identity: the per-item eventID (messageId, messageId-i for a bulk element, messageId-j or messageId-i-j for a failure that embeds more than one record) is checked inside the record'
    -> confirmed: The code matches the claim. eventID is messageId, messageId-i or messageId-[i-]j (events.go:88-92, 236-239). The event-doc Get runs inside RunTransaction and returns nil, so applied=false (firestore.g
- [holds/medium] a-what-double-counts: Re-applying the same content cannot double count stats, insights, reasons or stage stats, because all of them are mark-and-move from state: a stage counts on its first reach, an arrival moves between buckets, failures count once p
    -> (not challenged)
- [holds/high] b-pre-and-post-deduper: (b) The same order arriving on create_record_request (KindReceived, group 'received') and on create_record (KindDeduplicated, group 'deduplicated') carries different messageIds and folds into one record without double counting. Bo
    -> confirmed: Routes put create_record_request on KindReceived and create_record on KindDeduplicated (events.go:24-25). Their groups differ (dedupe.go:36-46). Both go through orderItem to keyed(of.BusinessID, of.Cu
- [risk/low] b-key-fallback-split: The code follows Harry's businessId + customerRef rule only when customerRef is present. An event with no customerRef keys to ~SO:salesOrder or ~SNAP:snapId instead, so one order can split into two records, and both copies of that
    -> confirmed: The code path is real. ShipmentKey falls back to ~SO: and then ~SNAP: (snapid.go:76-86). A confirmation's customerRef comes only from identifiers.customerRef or order.customerRef (extract.go:172). Not
- [risk/medium] c-countedids-cap: A Pub/Sub redelivery of a counted copy is caught only while its id is still among the record's last 64 CountedIDs. The README assumes a redelivery comes within 'a day at most', but retention is now 7 days and a hold backlog drains
    -> confirmed: A counted copy writes no event doc. Its only redelivery guard is slices.Contains(CountedIDs) (dedupe.go:247-249), and the list is trimmed to the last 64 (dedupe.go:22, 263-266). CountedIDs is shared a
- [holds/medium] c-bulk-partial: A bulk message that half-commits (item 0 committed, item 1 hit a store error, so the whole push returns 500) is safe on redelivery. Each item is its own transaction and is recognised by its own messageId-i, through the event doc o
    -> (not challenged)
- [holds/medium] c-concurrent-dup: Two concurrent deliveries of the same messageId serialize today: the event-doc read, the record read and the record write share one Firestore transaction, and tx.Create fails if the event doc exists. In Mongo, the equivalent is a 
    -> (not challenged)
- [holds/medium] c-seen-ttl-8d: An 8-day TTL is enough for a same-messageId redelivery from a push subscription (7-day retention), but only if expireAt is anchored on the wall-clock apply time. It must not use the event's OrderTime/ReceivedAt, which cmd/redrive 
    -> (not challenged)
- [broken/medium] c-redrive-new-id: cmd/redrive replays under the dead-letter message's new messageId, because Pub/Sub does not carry the original id. A message that was partly or fully applied before it was dead-lettered is therefore re-applied as a 'republished co
    -> confirmed: Redrive rebuilds the push with MessageID: m.MessageID from the DLT pull (redrive.go:158-163) and reads only the source-subscription and publish-time attributes (redrive.go:17-21, 155). README.md:588-5
- [holds/medium] c-hold-drain: Holding and then draining a backlog does not double apply: hold mode answers 503 before reading the body, and Terraform refuses DLT while held. After the import the seen collection starts empty, so pre-cutover messages are guarded
    -> (not challenged)
- [risk/medium] c-inflight-at-hold: The hard cut assumes 'Firestore stops changing' once the hold deploys. The pre-hold Cloud Run revision can still finish in-flight pushes and commit and ack (204) them after traffic shifts, and the hold does not block note writes. 
    -> confirmed: The hold is checked per request in the new revision only (push.go:33-37). Only POST /events/v1 goes through it (router.go:49). Note POST and PATCH (router.go:56-57, 59, 76-77, 81) write Firestore in a
- [risk/medium] c-import-rerun: An 'idempotent upsert on _id' import is safe only before the hold is released. Re-running it after the drain has begun replaces Mongo records with the stale Firestore snapshot, losing every event and count folded since release, in
    -> confirmed: The shipment is a single whole-document tx.Set (firestore.go:406), with ledgerJson and timelineJson as opaque blobs (firestore.go:88-91). An upsert that replaces on _id therefore reverts everything fo
- [risk/high] d-seen-key-granularity: (d) If the seen key is the bare Pub/Sub messageId, it causes lost updates. Bulk elements (messageId-i) and multi-record failure wrappers (messageId-j) are applied in separate transactions, often to different records, so the first 
    -> confirmed: Each item gets its own pending.apply and its own transaction (ingest.go:94-104, 142-152, 154-164), with its own DocID (events.go:221). The event id is scoped under shipments/{docID} (firestore.go:357)
- [risk/high] d-seen-in-txn: The seen insert cannot lose an update only if it is written in the same Mongo session and transaction as the record, event and marks writes, so an abort or retry discards it. A claim-first insert outside the transaction loses the 
    -> confirmed: Today the existence check and every write share one RunTransaction. An existing event returns nil, so applied=false with a nil error (firestore.go:361-370, 433-436). Ingest maps that to redelivered an
- [risk/medium] d-refresh-empty-eventid: Refresh, RefreshStale and RefreshReturnStale call Apply with eventID "", which today means 'no event to dedupe on'. The Mongo Apply must skip both the seen check and the seen insert when eventID is empty, or every refresh/backfill
    -> confirmed: Refresh, RefreshStale and RefreshReturnStale call Apply/ApplyReturn with eventID "". The cited lines are ingest.go:207/231/253 at c52f644, and 210/234/256 on origin/main. cmd/recompute-stats/main.go:7
- [risk/medium] d-event-id-composite: A Firestore event doc id is unique only under its parent record. In Mongo, if events go into one collection with _id = eventID ('today's doc id'), two records holding the same eventID collide. The import upsert would overwrite one
    -> confirmed: In principle the claim is right. Event ids are unique only under a parent (firestore.go:357; firestore_returns.go:208), shipments and returns share the 'events' name (firestore.go:33, 39-40), and flat
- [risk/medium] d-redrive-store-hardcoded: On main, cmd/redrive (like backfill-*, recompute-stats and api) builds store.NewFirestore unconditionally. A redrive run after STORE flips to Mongo would apply and ack DLT messages into Firestore, so they would be lost from Mongo.
    -> confirmed: origin/main (97e9353) still constructs Firestore unconditionally in cmd/redrive/main.go:54 and 65, api/main.go:57, backfill-upgrade/main.go:49, backfill-attention/main.go:46 and recompute-stats/main.g
- [risk/low] d-returns-span-shipment: The design treats each transaction as touching 'a single record's docs', but a return's apply also updates its linked shipments' returnsJson and returnCount in the same transaction. A shipment apply sets the whole shipment doc. In
    -> confirmed: ApplyReturn tx.Update's each linked shipment's returnsJson and returnCount in the return's transaction (firestore_returns.go:261-271), after reading the shipment through txShipments (firestore_returns

## live-data
NUMBERS: Paged runQuery with a field mask, cross-checked against runAggregationQuery count (2026-11-06T14:53Z). DEV: shipments 34,294 (keySource customer_ref 34,294 / sales_order 0 / snap_shipment_id 0); returns 218 (rga_number 218 / snap_receipt_id 0). PROD: shipments 89,156 (customer_ref 89,156 / sales_order 0 / snap_shipment_id 0); returns 0, and there is no returns collection at all (listCollectionIds = businesses, insights, shipments, stats). (2) Groups sharing businessId + customerRefNorm: dev 0, prod 0. Groups sharing businessId + rgaNumberNorm: dev 0, prod n/a. (3) Fallback-keyed (~SO:/~SNAP:) docs: dev 0, prod 0, so 0 split identities. (4) Groups of businessIds that differ only by case or whitespace: dev 0 of 22 distinct, prod 0 of 17 distinct. Integrity checks, all 0 in both envs: id field != doc name; doc name != DocumentID(businessId,key); businessId not trimmed-uppercase; keySource inconsistent with key prefix; customer_ref doc whose key != customerRefNorm; rga_number doc whose key != rgaNumberNorm or whose rgaNumberNorm is empty. Extra check: references equal once internal whitespace is removed (Normalise does not fold these): dev 479 pairs (CHAMPO 477, all synthetic "INF n"/"INFn" created 2026-10-21/22; SAMMCK 2, test refs: SAMMCK__VEVTVCAx~SAMMCK__VEVTVDE, SAMMCK__VEVTVCAy~SAMMCK__VEVTVDI); prod 0. Scripts: /tmp/claude-1000/-home-hjf/c36659b6-edee-4035-ab29-ffd89416a0e8/
- [holds/low] keysource-counts: Every stored record in both environments is keyed by its primary reference. All shipments are customer_ref and all returns are rga_number, with no ~SO:/~SNAP:/~RCPT: fallback keys anywhere.
    -> (not challenged)
- [holds/high] no-dup-bizid-customerref: No two shipment documents share businessId + customerRefNorm in dev or prod, so the identity rule holds in the stored data.
    -> confirmed: I re-ran the check read-only through Firestore REST runQuery, selecting only these fields. Dev has 34,294 docs and prod has 89,183 (prod has grown by 27 since the claim's 89,156). Both have 0 business
- [holds/medium] no-dup-bizid-rga: No two return documents share businessId + rgaNumberNorm.
    -> (not challenged)
- [holds/medium] mongo-id-carries-identity: If the Mongo _id stays as today's doc id, the businessId + customerRef (and businessId + RGA) uniqueness transfers to Mongo for 100% of current documents with no merge or dedupe pass needed at import. A partial unique index on {bu
    -> (not challenged)
- [holds/low] no-split-identity: There are zero split identities today, because neither environment holds any fallback-keyed (~SO:/~SNAP:) shipment.
    -> (not challenged)
- [risk/low] split-identity-structurally-possible: The code can still create a second record for one order: any event that lacks a customer reference but has a sales order or Snap id gets a separate ~SO:/~SNAP: document, and nothing ever merges it into the customer_ref document. N
    -> confirmed: The mechanism reproduces as described. confirmationItem calls keyed() with cf.CustomerRef, cf.SalesOrder and cf.SnapShipmentID (internal/core/events.go:201-205). With no customer ref, ShipmentKey retu
- [holds/low] bizid-case-variants: No businessId differs from another only by case or whitespace, and every stored businessId is already trimmed and uppercase.
    -> (not challenged)
- [risk/low] prod-returns-absent: Prod has no returns collection, so returns identity cannot be checked in prod, and the cutover import and parity check for returns will be empty. The first prod returns would be created directly in Mongo.
    -> confirmed: listCollectionIds on bifrost-prod-global1/databases/tracking-service returns only businesses, insights, shipments and stats. Dev also has returns, returnStats and returnInsights. A count aggregation g
- [holds/low] internal-whitespace-not-folded: Normalise only trims the ends and uppercases a reference, so two refs that differ by internal whitespace count as distinct identities. Dev has 479 such pairs, all test data. Prod has 0.
    -> (not challenged)
- [risk/low] returns-rga-fallback-unmeasured: A return keyed rga_number may actually be keyed by identifiers.id or customer.reference (the RGAFallback path), so rgaNumberNorm can hold a customer reference rather than an RGA number. The size of that subset was not measured bec
    -> confirmed: The code risk is real. When a create has no businessRgaNumber, the fallback is identifiers.id, then customer.reference (internal/core/returns_items.go:148-150). keyReturn keys it as plain rga, with no

## mongo-design
- [holds/high] id-is-the-identity: Keeping today's doc id as _id makes a second customer_ref-keyed document for the same businessId + customer ref impossible at the database level: Mongo's built-in unique _id index rejects it. This holds only if the store always fi
    -> confirmed: I found no counterexample. Every ingest path computes the id with no lookup: keyed() sets BusinessID=Normalise(biz), Key=ShipmentKey(...) and DocID=DocumentID (events.go:208-222). DocumentID is determ
- [holds/high] uniq-customer-ref-partial: Harry's rule should be stated in the schema as shipments.createIndex({businessId:1, customerRefNorm:1}, {unique:true, name:'uniq_business_customer_ref', partialFilterExpression:{keySource:'customer_ref', customerRefNorm:{$gt:''}}}
    -> confirmed: The conclusion holds: on customer_ref docs customerRefNorm==key (reduce.go:481-482). Every customerRef fact comes from an event whose Normalise(customerRef) is that key (applyOrder reduce.go:357; appl
- [holds/medium] uniq-business-key: Add shipments.createIndex({businessId:1, key:1}, {unique:true, partialFilterExpression:{key:{$gt:''}}}), and the same on returns, so the identity holds independently of the base64/'/'→'_' id encoding. No document written since 32d
    -> (not challenged)
- [holds/medium] validator-keysource-consistency: Add a collection validator so the DB itself requires a customer-ref-keyed shipment's customerRefNorm to equal its key, and an rga-keyed return's rgaNumberNorm to equal its key. With that, the partial unique index on customerRefNor
    -> (not challenged)
- [holds/high] returns-uniq-rga: The returns equivalent is returns.createIndex({businessId:1, rgaNumberNorm:1}, {unique:true, partialFilterExpression:{keySource:'rga_number', rgaNumberNorm:{$gt:''}}}). It covers both real and fallback RGA numbers and excludes ~RC
    -> confirmed: The field names are right (firestore_returns.go:18,21). On rga_number returns, rgaNumberNorm==key: the create keys on Normalise(f.RGANumber) including the fallback (returns_items.go:148-151,174-181), 
- [holds/low] search-index-separate: The partial unique index cannot serve SearchPrefix, so a separate non-unique {businessId:1, customerRefNorm:1, _id:1} index (and {businessId:1, rgaNumberNorm:1, _id:1} for returns) is still needed. The search index must never be m
    -> (not challenged)
- [risk/high] split-fallback-not-enforceable: No unique index can stop one order from being split across a customer-ref doc and a ~SO:/~SNAP: fallback doc, or across two normalisation variants of the ref. A unique index on salesOrderNorm would turn the split into a dead-lette
    -> confirmed: The scenario reproduces in code. confirmationFacts takes customerRef only from identifiers.customerRef or order.customerRef (extract.go:172), and keyed() falls back to ~SO: with no lookup (events.go:2
- [risk/high] seen-key-is-event-id: The seen key must be the per-item event id (messageId, messageId-i, messageId-i-j), not the raw Pub/Sub messageId. Keying by raw messageId silently drops items 1..n of every bulk message, and drops the retry of a partially applied
    -> confirmed: Event ids are per item: bulk items are M-i (events.go:88-92; returns_items.go:100-104), and failures with several embedded records are id-j (events.go:235-239). Each item is applied in its own transac
- [holds/medium] seen-record-scoped: Today no event id applies to more than one record, so {recordId, eventId} and a global {eventId} are equivalent. Recommend _id = '<shipments|returns>/<docId>/<eventId>' with one seen row per item, written for the item's own record
    -> (not challenged)
- [risk/medium] seen-skip-empty-event-id: The Mongo store must skip both the seen check and the seen insert when eventID is empty, as Firestore does. Otherwise backfills and Refresh silently stop rewriting after the first pass, or fail on E11000.
    -> confirmed: Rewrites pass eventID '': Refresh, RefreshStale and RefreshReturnStale (ingest.go:207,231,253 in the worktree; 210,234,256 on origin/main), and recompute-stats calls st.Apply(ctx,id,"",...) directly (
- [risk/medium] seen-ttl-not-sole-guard: An 8-day seen TTL cannot be the only idempotency guard. The Mongo Apply must still check the record-scoped event doc (kept forever), or treat E11000 on the events _id as 'already applied'. Copies fall back to Timeline.CountedIDs.
    -> confirmed: The conclusion holds, but the day-9 scenario is the weakest route to it. Subscriptions keep messages 7 days (pubsub.tf:45) and set no retain_acked_messages, so seek cannot replay acked messages; an 8-
- [holds/low] concurrent-first-create: Two concurrent first events for a new businessId + ref can never produce two documents: the losing transaction gets WriteConflict or DuplicateKey on the shared _id. The store should retry the whole transaction on either error, so 
    -> (not challenged)
- [holds/medium] violation-failure-mode: If any unique index or the validator is violated during ingest, the event is parked rather than lost, and the failure is loud: E11000/121 → ItemStoreError → 500 → Pub/Sub retries → DLQ after 5 attempts, with the store-error metric
    -> (not challenged)
- [holds/medium] import-replace-upsert: cmd/import-mongo should create every index and validator first, then copy with bulkWrite replaceOne({_id}, doc, {upsert:true}, ordered:false). That makes a re-run with Firestore frozen a no-op, and makes any duplicate show up as a
    -> (not challenged)
- [risk/medium] import-validate-identity: The importer must check every shipment and return for _id == stored id == DocumentID(businessId, key), a non-empty key, and keySource == KeySourceOf(key), and report any that fail rather than import them. A document with a pre-32d
    -> confirmed: Pre-32dee64 ids were clean(biz)__clean(snapID) (git show 32dee64 snapid.go), and identity reads only compute DocumentID (query.go:424-425,561-566), so such a doc cannot be reached by identity lookup. 
- [risk/medium] hardcut-notes-not-held: INGEST_HOLD only 503s the push endpoint, so note POST/PATCH keeps writing Firestore during the hold. That breaks the design's 'Firestore stops changing' assumption: notes added between the import and the flip are lost.
    -> confirmed: The hold is set only on the pushHandler (router.go:40-43), and only handle() returns 503 (push.go:33-38). Note POST and PATCH for shipments and returns are routed without it (router.go:56-57,59,76-77,
- [risk/medium] hardcut-reimport-after-flip: Because the import is a replace-upsert, re-running it after STORE flips and the hold is released would overwrite records Mongo has advanced since, losing events and notes. The importer must refuse once the cut is live.
    -> confirmed: Nothing marks a store as live. On main, config has no backend selector at all (internal/config/config.go has only FIRESTORE_DATABASE). STORE=firestore|mongodb and storeopen exist only on the unmerged 
- [holds/low] hardcut-dlq-off: Terraform already blocks holding ingest while dead-lettering is on. Prod currently has dead_letter_enabled=true, so the cut must turn it off before the hold, or held 503s would be dead-lettered after 5 attempts and redriven under 
    -> (not challenged)
- [risk/low] return-link-no-upsert: In Mongo the return transaction's patch to the linked shipment must be updateOne with upsert:false and an asserted matchedCount==1. Firestore's tx.Update fails on a missing doc, but an upsert would create a stub shipment with no b
    -> confirmed: The facts are right. The patch is a tx.Update with returnsJson and returnCount only (firestore_returns.go:261-272), and Update fails if the doc is missing; an upsert of those $set fields would create 
- [risk/low] business-slash-collision: DocumentID maps '/' to '_' in the business id, so businesses 'A/B' and 'A_B' with the same ref share one _id and are merged into one record across tenants. This is a merge, not a duplicate, and keeping today's ids carries it into 
    -> confirmed: DocumentID replaces '/' with '_' (snapid.go:102), while the stored businessId keeps '/' (events.go:209,219; reduce.go:63). Distinct 'A/B' and 'A_B' would therefore share one id and merge. Nuance: in F

## critic
 Note: the findings I was given cut off partway through the message-dedupe lens (at `c-seen-ttl-8d`), and the fourth and fifth lenses were missing. Some gaps below may repeat what those lenses found. Paths are under `/home/hjf/code/fuse/tracking-service/.claude/worktrees/exempt-unqueried-firestore-fields/apps/api` (c52f644) unless another repo is named.

**Gaps not checked by any lens I saw**

1. **The record transaction also writes counter docs shared across records. Checked; the design's wording is wrong.**
   - Apply's transaction writes `businesses/{biz}` with `shipmentCount` +1 (`internal/store/firestore.go:419-424`).
   - It increments one stats and insights doc per business per day, plus a global `_all_` per day (`internal/store/firestore.go:440-455`, `613-631`; `internal/store/store.go:18`).
   - It reads the reason-code docs inside the transaction (`firestore.go:458`; `store.go:289`). Returns do the same (`internal/store/firestore_returns.go:273-284`).
   - So "one transaction over a single record's docs" does not describe the current code.
   - If a port moves the `$inc` calls outside the transaction, a retry or a crash after commit double-counts or loses counts.
   - If they stay inside, every apply that adds a stat conflicts on `_all__<day>`. During the drain after the hold, that is a WriteConflict storm. `withTransaction` can retry for up to 120s, while the ack deadline is 30s (`iac/projects/tracking-service/pubsub.tf:41`), so Pub/Sub redelivers the same message to another instance while the first is still running.
   - The first event of each business-day (and each new business) also races to insert its stats or business doc. That is the same E11000-vs-retry misclassification risk as `mongo-first-insert-race`, and it happens daily around UTC midnight.

2. **A producer no lens read: the `replay` service. Checked.**
   - `replay/code/src/http/controllers/failures.controller.ts:185-208` (PATCH) lets a person edit a failure's `record` and `metadata`.
   - `:211-260` republishes it to `create_record_request` as `sales_order`, or to `confirmation_ready` (pick/pack, as a one-element bulk), with `{recordType}` set (`core/failure/failure.service.ts:236-265`). The republish gets a new messageId and `timestamp=now` (`adapters/pubsub/pubsub.service.ts` `replayMetadata`).
   - Fixing customerRef, `identifiers.businessId` or `metadata.customer` is the reason to edit. The fixed replay keys to a new doc, and the original `create_data_failure` doc stays failed forever. This is `fallback-key-no-merge` driven by a person, and likely common.
   - An unedited double replay is a content copy, so it only adds Copies++.
   - Data check worth running: failed docs whose businessId + salesOrder also has a non-failed doc under a different key.
   - The local clone is at 5082263 (2026-07-21), so check origin.
   - order-management-system publishes without attributes (`order-management-system/backend/code/src/adapters/pubsub.publisher.ts:61`), so the recordType f
