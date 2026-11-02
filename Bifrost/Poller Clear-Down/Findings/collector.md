# collector — feasibility study: "consume SNAP confirmations on find"

Date 2026-09-29. Read-only. Refs read:
- collector@f19ce57 (origin/master) — code + iac/projects/collector/pubsub.tf
- snap-adapter@3c1578b (worktree early-consume-feasibility) — poller `apps/snap-queue-polling-service/src`, `apps/snap-adapter/src/adapters/pubsub`
- fapi@f4bd648, sftp-connector@f6a15e3, shopify-connector@835c061, replay-service@d75997f, pkg-node@4d62ab9 (types/pubsub) — only to confirm failure-envelope shapes/sources
- Vault: Engineering/collector/{architecture,known-context,overview}.md (verified_sha 0599b6b, 2026-09-23 — behind master by 5 Renovate commits, no functional drift found), Bifrost/Fuse Collector.md (stale 3-line stub)
- Datadog prod (7d to 2026-09-29): collector logs/metrics, poller metric `fuse.confirmation.manual_origin_broadcast`, `gcp.pubsub.topic.send_message_operation_count`

## 1. What the collector is
A pure **observer / read-model** (NestJS + Mongo Atlas, Cloud Run `collector-<env>`). It never publishes. It stores the canonical body of every record type and confirmation type it taps, plus a collector-owned `lifecycle {createdAt, status}` used by fuse-ui Customer Transaction History (FUSE-967/971) via `GET /api/v1/records/:recordType/:businessId` (x-api-key). It is **not** the delivery ledger of record for confirmations today: it has no notion of OBQ queueId, no error detail, no attempt history.

## 2. Subscriptions consumed (confirmation side), with filters — pubsub.tf@f19ce57
| Topic | Sub filter | Route | Effect |
|---|---|---|---|
| confirmation_ready | recordType = purchase_order OR goods_in_confirmation | confirmation/ready/purchase_order | bulk upsert into purchase_order_confirmations, status stays null (event.controller.ts:696-818) |
| confirmation_ready | recordType = goods_out_confirmation | .../sales_order | upsert sales_order_confirmations, status null |
| confirmation_ready | pick_confirmation / pack_confirmation | .../pick_confirmation, .../pack_confirmation | upsert, status null forever (services have no status arg, no markFailed) |
| confirmation_ready | work_order_confirmation / finished_good_receipt | ... | upsert, status null; **no retry_policy** |
| confirmation_made (for_each x4) | PO: purchase_order OR goods_in_confirmation; SO: sales_order OR goods_out_confirmation; WOC; FGR | confirmation/made/:recordType | upsert + advance to `processed`; single or bulk; **no retry_policy** |
| confirmation_data_failure (for_each x5) | `<type> AND NOT attributes.source = "snap-adapter"` for goods_in, goods_out, WOC, FGR, stock_adjustment | confirmation/failure/:recordType | markFailed -> `failed`; **no retry_policy**; no upsert |
| stock_adjustment_ready / _made topics | none (dedicated topics) | confirmation/ready|made/stock_adjustment | pending / processed(+confirmedAt) |
NOT collected at all: RGA confirmations (recordType return_goods_authorization on confirmation_ready; return_goods_confirmation on failure), pick/pack `confirmation_made` and `confirmation_data_failure`, WO create-side ack/failure. No sub anywhere has a dead_letter_policy or explicit message_retention (default 7d).

## 3. Data model
Collections (constants.ts:14-27): purchase_order_confirmations, sales_order_confirmations, pick_confirmations, pack_confirmations, work_order_confirmations, finished_good_receipts, stock_adjustments (+ record collections). Doc = canonical body top-level keys `$set` + `metadata` (envelope, last writer wins, so correlationId is the latest ingest's) + `lifecycle{createdAt,status}` + optional `deletedAt`.
Upsert keys (NOT queueId): PO conf `receiptId+bizId`; SO conf `shipmentId+bizId`; pick/pack `shipmentId+businessId`; WOC/FGR `id+businessId`; stock_adjustment `businessId+id+lineId`. `identifiers.queueId` is stored inside the body (required on goods-in/out + stock adjustment, optional on the rest — pkg-node types) but is unindexed, not a key, not searchable via reference search.
Indexes are non-unique (registry: e.g. `{identifiers.shipmentId:1, identifiers.bizId:1}`), so concurrent upserts on the same key can insert duplicates; `advanceStatus` uses updateOne and would update only one of them.
Status = `pending -> processing -> processed -> failed`, monotonic by rank (lifecycle.ts:36-41); `failed` is highest and therefore terminal; only `status` moves — no `updatedAt`, no failure reason/source/stage/connectorId, no history (collection.ts:168-215). Confirmations: `ready` leaves `status: null`; `made` -> processed; failure -> failed.
Retention: no TTL index, no expireAfterSeconds anywhere in src/iac; only soft-delete via release_* (PO/SO/MD records, never confirmations). Atlas M10 10GB autoscale, backups+PIT on (mongo.tf). Growth unbounded.

## 4. Event handling per confirmation event type
- **ready** (`handleConfirmation`): `ingestBulkEvent` validates every record with the canonical Zod schema; ONE bad record throws PubSubValidationError -> filter maps to **HTTP 204 (ACK, dropped)** for the WHOLE batch (all-or-nothing) (pkg-node ingest.ts:47-80; all-exceptions.filter.ts:46-74). Counted by `fuse.collector.record_dropped{reason:zod}` — prod 7d: 0.
- **made** (`handleConfirmationMade`): upserts (creates the doc if ready never landed) and advances to processed; same all-or-nothing validation. Success is therefore self-contained; can arrive before ready.
- **failure** (`markConfirmationsFailed`, :942-1000): accepts single BifrostFailure, bulk (sftp: one BifrostFailure per confirmation), or `record.confirmations[]` (fapi). **Never upserts** — `advanceStatus(filter, FAILED)` on the existing doc keyed by business key + `metadata.customer`. matched==0 -> log "Failure for a record not held" and nothing else; no `record` -> "Failure carried no record"; keyless record -> markFailed returns 0. Prod 7d: 214 "not held" (all sales_order) vs 365 marked failed (sales_order) + 9 (purchase_order).
- **Source distinction**: filter excludes only `attributes.source = "snap-adapter"` (snap-adapter clear-down failures, stage confirmation_made, `to-confirmation-failure.ts:10-11`). fapi (source "rest"), sftp-connector (config.meta.source) failures pass and mark `failed`.

## 5. Would the collector accept a POLLER-authored failure?
Yes, mechanically, and it already receives them. `buildManualOriginFailure` (poller confirmation-failure.ts:53-83) publishes to confirmation_data_failure with attributes {recordType: goods_in_confirmation|goods_out_confirmation|WOC|FGR|pick|pack|return_goods_confirmation, stage: confirmation_ready, source: "snap-queue-polling-service"}, error type `business_rule`/`no_originating_connector`, `record` = the single canonical, published immediately after the ready message (confirmations.service.ts:336-358). Source != snap-adapter so the collector filter passes it; for goods_in/out/WOC/FGR it routes to markFailed -> `failed` (terminal, cannot be superseded by a later `made`), even though the message text says "nothing failed ... broadcast to all connectors". Pick/pack/RGA have no collector failure route (dropped by filter). Effect of stage: collector ignores `stage`, so a new poller stage would work without change but would need a pkg-node FailureStage enum bump for validation (FailureStageSchema is a closed enum).
Volume: prod `fuse.confirmation.manual_origin_broadcast` = 7,855 good_out + 11 good_in over 7d; `confirmation_data_failure` topic carried ~300-450 msgs/hour until ~2026-09-23 08:00 then tens/day (gcp.pubsub send_message_operation_count). Collector "marked failed" now runs ~35-114/day. I could not prove from logs that the current post-09-23 failed transitions are poller-manual-origin (the poller failure publisher logs nothing) — treat attribution as likely, not proven.

## 6. What an operator can find today
- `GET /api/v1/records/:recordType/:businessId?reference=` (per business, newest-first by createdAt, exact-match reference search incl. correlationId/_id). Returns lifecycle{createdAt,status}. **No status filter, no cross-business view, no age filter, no queueId search, no index on lifecycle.status, no "stuck since" (no status timestamp).** `status: null` means both "announced, still in flight" and "announced, connector silently did nothing". The Fuse MCP `get-fuse-records` uses the legacy route which does not return lifecycle at all.
- Failure reasons are not stored in collector; operators go to replay-service (failure inbox) or Datadog.
- Metric `fuse.lifecycle.transition{to,type}` counts transitions only (prod 7d: sales_order_confirmations ->processed 16,389, ->failed 365; PO conf 27 / 9); there is no gauge of "announced but not terminal".
=> An operator cannot currently answer "which confirmations were announced but never delivered" without a Mongo query on Atlas (`lifecycle.status: null`, createdAt older than N). Collector gives a partial, lossy ledger: announced (null) -> made (processed) | failed, keyed by business entity not OBQ row.

## 7. Confirmation lifecycle ledger — how good is it?
Not durable/complete enough to be the system of record for "consumed from SNAP":
1. Key mismatch: one doc per (shipmentId|receiptId + biz) — a second OBQ row / re-announce for the same shipment overwrites the body, and does NOT reset status (a fresh announcement shows `processed` from the earlier delivery; a prior `failed` masks a later success). Not per queueId, not per attempt.
2. Failed is terminal and irrevocable: replay success (republishes to confirmation_ready, replay-service failure.service.ts:725-757) or a second connector's `made` cannot move it; lifecycle.ts:26-35 defers this to FUSE-1024. Broadcast with one failing connector = permanent `failed` even if others delivered.
3. Failures are lossy at collector: failure-before-ready race, failures for records never announced (poller mapping/validation failure never emits a failure event — `queue-lane.ts:88-101` returns [] on mapping error, goods-out handler filter logs+metric only at goods-out.confirmation-handler.ts:467-485), sftp `invalid.record` w/o identifiers, no pick/pack/RGA routes.
4. Silent non-outcomes downstream leave status null forever: fapi NotRouted (no candidate connectors, log+metric only), sftp `logNoEligibleConnectors`/`logUnresolvableConnector` (return without made or failure), shopify `if (!fulfillments?.length) continue;` (no made, no failure). Today those rely on the OBQ row being re-announced.
5. Ingest fragility: 204-drop of whole invalid batch (ready and made and failure), 11 subs without backoff (2 ready + 4 made + 5 failure; the vault says 8 — #105 added 3 failure subs), no DLQ, 7d retention, non-unique upsert keys.
6. No record of *consume* itself: collector never learns that the poller marked the row processed; no such event exists.

## 8. What would be needed for collector to be the system of record
(Facts about gaps, not design opinion.)
- A durable per-row identity: key/ index on (businessId, queueId, recordType) (or a separate append-only `confirmation_events` collection) instead of shipmentId/receiptId.
- Persist transition events with timestamps and failure payload (errors[], source, stage, connectorId, transaction, upstream) — today only status.
- A `consumed`/`announced` state written from a durable event the poller publishes BEFORE marking the SNAP row processed; collector can only see what reached Pub/Sub (publishMessage ack is the durability point). Mark-processed before publish-ack = loss the collector can never see.
- Failure ingestion must upsert (create the ledger row from the failure's embedded canonical) so failure-before-ready and never-announced records are recorded; must cover pick/pack/RGA/stock_adjustment (RGA has no collection at all), and status must allow a later success/replay to supersede or at least append.
- No silent 204 drops for ledger events: per-record validation instead of all-or-nothing, DLQ or an explicit "unparseable" quarantine, retry_policy on every sub, alert on record_dropped>0 and on non-terminal age.
- Query surface: status filter + age + cross-business + queueId lookup, index on lifecycle.status/createdAt; a stuck-confirmation gauge/monitor.
- Retention/TTL policy for the ledger (none today).

## 9. Exit paths / terminal outcomes (collector view, if OBQ row already consumed)
See structured output. Key: collector records only 3 outcomes (announced=null, processed, failed); everything else is invisible to it.

## 10. Datadog evidence summary (prod, 7d to 2026-09-29)
- collector "Confirmation marked processed" 17,249 sales_order / 33 PO; "Confirmation stored" 8,056 / 33 (events not records; made outnumbers ready 2.1:1 suggests multiple made per confirmation or repeat announcements — unverified).
- record_dropped: no series (0).
- "Failure for a record not held": 214, 210 of them on 2026-09-22 (before goods-out failure route deployed 09-23).
- confirmation_data_failure topic publishes/hour: ~270-460 (09-22) -> near zero after 09-23 morning.

## Open questions
- Which producer authors the current ~35-114 failed transitions/day? (poller manual-origin vs fapi vs sftp). Needs the failure message `source` attribute (e.g. a Pub/Sub snapshot/replay-service failure list filtered by source).
- Can one OBQ row (XDoc/queueId) ever map to >1 canonical of the same type / same shipmentId (multi-despatch, kit, short-ship)? Determines whether the shipmentId key collapses distinct confirmations.
- Why did made events (17,249) outnumber ready events (8,056)? Broadcast fan-out or re-announce loop (the 561-per-4h flat pattern in manual_origin metric 09-19..09-27 looks like a re-publish loop).
- Do the Cloud Run 5xx paths (DatabaseError) produce hot redelivery loops on the 11 backoff-less subs in practice? No prod evidence gathered.
- Does fuse-ui Transaction History surface `status: null` distinctly or as "pending"? (not read)
