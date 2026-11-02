# snap-obq-semantics — SNAP outbound queue (OBQ) API semantics

Date: 2026-09-29. Investigator label: snap-obq-semantics. Strictly read-only.

## Refs read

- snap-adapter@3c1578b3c6f813b61fec4dfe5e5bc4f250d9bd99 (origin/master, worktree early-consume-feasibility)
- pkg-node@4d62ab933dfe7bc7e28c86fd928798b840000000 (origin/main) — pkg/snap entity-registry, outbound types/schema, constants
- /home/hjf/code/fuse/snap-api.openapi.yaml (vendor-derived OpenAPI; snapOutbound at lines 5066-5100 and 11463-11605)
- Vault: Engineering/snap-queue-polling-service/{known-context,architecture,operations}.md; Engineering/snap-adapter/{overview,architecture}.md; Support/2026-09-23-lisauk-goods-out-confirmations-drained.md; Bifrost/Confirmation Enrichment Pipeline/Target Design.md
- Slack thread (read-only) #bifrost-general p1790148725881649 (Dr Sam's / Lisa Eldridge / Shackleton "Jitterbit-shared queue" thread)
- LIVE probe: DEV SNAP tenant, business GADG (Fuse MCP get-snap-connection environment "staging" = the dev/test SNAP host ilg001testapi.snapwarehouse.net; note: the MCP's env enum is staging/production, "staging" is what we call dev). Only read tools used: snap-get-outbound-queue, snap-search (snapOutbound), snap-get (snapOutbound by id). No snap-write, no `next`, no `/processed`.

## 1. HEADLINE ANSWER

"After a row is marked processed, can we still read it back and could we re-queue it?"

- READ BACK: **YES (empirically proven), by id only.** `GET /v2/snapoutbound/{XDoc}` returns processed rows with `DateProcessed` stamped and row `Stage` flipped `"00"` -> `"90"`. Oldest processed row I could fetch: GAOB000119/GAOB000120 created 2025-12-15 (>9 months old), so there is no short retention purge visible in dev. Rows are retained, not deleted or archived out of reach.
- BUT the **LIST route does not show processed rows at all** (implicitly scoped to open rows). `GET /v2/snapoutbound?$filter=XDoc eq 'GAOB001430'` returns `[]` although `GET /v2/snapoutbound/GAOB001430` returns the row. `DateProcessed ne null`, `Stage eq '90'`, `Transaction eq 'STOCK_MOVE'` (all STOCK_MOVE rows in dev are processed) all return `[]`. So there is **no list/filter API to enumerate processed rows**; an audit/reconcile of "what did SNAP emit that we consumed" is only possible by id enumeration (XDoc is a per-tenant sequential `GAOB%06d`, so enumeration is feasible but unindexed) or via Fuse-side records.
- RE-QUEUE: **UNKNOWN (untested).** No documented un-process/re-queue route. The only write surface is `PATCH /v2/snapoutbound/{id}` (body = SnapOutbound) and `PATCH /v2/snapoutbound/{id}/processed`. Whether PATCH /{id} with `{Stage:"00",DateProcessed:null}` re-opens a row is not documented and I was forbidden to test it. Needs a controlled write test on a throwaway dev row (human-approved).
- Also: SNAP's own re-emit is not something we can trigger; new rows are minted by SNAP on stage transitions only.

## 2. Row shape and identity

Fields observed live: `Host` (e.g. HOST_GADG), `XDoc` (row id, e.g. GAOB001430), `Transaction` (DESPATCH | RECEIPT | STOCK_MOVE), `Key` (free-form quoted kv string), `Message` (null in all samples), `Error` (null in all samples), `Batch` (null in all samples), `DateCreated`, `DateProcessed`, `Stage` (row's own state: "00" open, "90" closed).

- OpenAPI (snap-api.openapi.yaml:5066) documents only Host, XDoc, Transaction, Key, Batch, DateCreated, DateProcessed, Stage. **`Message` and `Error` are absent from the OpenAPI but present on the wire and in pkg-node's schema** (pkg-node@4d62ab9:pkg/snap/src/types/schemas/entities/outbound.schema.ts) — meaning is undocumented; SNAP may write to them on failure. Never observed non-null.
- OpenAPI describes `XDoc` as "Task ID" and `Key` as "movement data ... including Task ID". In practice **XDoc is the row's unique queue id**; Fuse calls it `queueId` (snap-queue-polling-service: `identifiers.queueId = item.XDoc`; claim key = XDoc).
- `Key` shapes: DESPATCH `Shipment="GADG9CBD01EA422" Stage="29"`; RECEIPT `Receipt="GADG1DC5625471D" Stage="90"`; STOCK_MOVE `Site="0006" Type="SREC" Move="6SRC000457" Line="SEDCDP72EW" SKU="TTRS2"`. The `Stage` inside Key is the order stage (29 pick, 39 pack, 90 despatch/receipt-complete), **not** the row's `Stage` field.
- **One event -> one row per stage transition**: a shipment yields separate rows per stage (e.g. GADG9CBD01EA422: GAOB001424 @29, GAOB001425 @39). Multiple rows per order is by design. I found no duplicate (same Key + Stage) rows in the ~35 rows I could view; I could not enumerate processed history so duplicates in general = unknown.
- Default list order is ascending XDoc (oldest first) empirically; `$orderby=DateCreated desc` works.

## 3. Semantics of list / next / processed

| Route | What it does | Evidence |
|---|---|---|
| `GET /v2/snapoutbound` | Returns ONLY open rows (Stage "00", DateProcessed null) regardless of filter; supports $top/$skip/$filter/$orderby per OpenAPI; poller sends `$top=1000` + `Transaction eq '<type>'` only, no $skip, no orderby | api.client.ts:194-217; live probe |
| `GET /v2/snapoutbound/{id}` | Returns any row by XDoc incl. processed; 404 "No matching entity" for non-existent ids | live probe (GAOB000119 processed 2025-12-15 OK; GAOB000101 -> No matching entity) |
| `GET /v2/snapoutbound/next` | OpenAPI: "next open (unprocessed) record"; side effects (lease/lock/visibility timeout) UNDOCUMENTED. Fuse never calls it. NOT probed (may mutate) | openapi:11550; entity-registry.ts:826-832 |
| `PATCH /v2/snapoutbound/{id}/processed` | Marks processed. Fuse calls it with NO body. Effect (empirical, from resulting rows): `DateProcessed` set to server time (ms precision), row `Stage` 00->90 | api.client.ts:153-157; snap-adapter confirmations.service.ts:18-27; rows above |
| `PATCH /v2/snapoutbound/{id}` | Vendor's worked example for "mark processed" hits this path (openapi:11515-11523 says unclear whether same op). Body schema = SnapOutbound. Could conceivably set arbitrary fields. Untested | openapi |

- **No lease/visibility timeout evidence.** Fuse reads the same open rows every poll (2 min cadence per vault) and they reappear until PATCHed. GET list has no side effect (I called it dozens of times; open set unchanged).
- **Idempotency of PATCH processed: UNKNOWN.** No test allowed. Fuse code has no special handling of a 404/400 on an already-processed row: any error from the clear becomes a `confirmation_data_failure` (snap-adapter event.controller.ts:196-220; to-confirmation-failure.ts, code `snap-adapter.<recordType>.obq_clear_down_failed`). In the early-consume design a double-clear (e.g. a Pub/Sub redelivery of the clear, or an operator PATCH) has unknown behaviour.
- SNAP does NOT re-emit or escalate open rows: open rows in dev are up to 15 days old with no duplicates or change (GAOB001424 created 2026-09-14T12:28:03, still open 2026-09-29). Nothing in SNAP alerts on stale unprocessed rows that I could find (nothing documented).

## 4. Live dev probe results (GADG, 2026-09-29)

Open (unprocessed) rows: **19 total**: DESPATCH 17 (order-stage 29: 7, 39: 7, 90: 3), RECEIPT 2 (both order-stage 90), STOCK_MOVE 0. Single Host value (HOST_GADG). Oldest open: GAOB001424 (DESPATCH, created 2026-09-14T12:28:03, 15 days old); newest open: GAOB001551 (RECEIPT, 2026-09-24T15:47:45). Open XDocs: 1424-1429, 1445-1450, 1458-1462, 1549, 1551.

Processed-row lifecycle samples:
- Typical: DateProcessed = DateCreated + ~1-2 min (e.g. GAOB001430 created 15:53:45, processed 15:54:08; GAOB001432/1433 STOCK_MOVE created 09:14:56, processed 09:16:07.657 / 09:16:08.52 — consistent with poll (2 min) -> deliver -> confirmation_made -> PATCH).
- Late clears: GAOB001421/1422/1423 created 2026-09-14, processed 2026-09-24T14:56:08-09 (three rows within 1s: a bulk/manual or gating-change clear, 10 days late); GAOB001463/1464 created 09-17, processed 09-21T12:04:10 (4 days late).
- GAOB001549 (RECEIPT) OPEN while adjacent GAOB001550 processed at 15:38:06 and 1551 open: per-row, not per-batch.
- **Anomaly: rows with row Stage "90" but DateProcessed null**: GAOB000180 (created 2026-04-14) and GAOB000200 (2026-04-15), both STOCK_MOVE, both absent from the list route. So a row can leave the open list WITHOUT a DateProcessed stamp (mechanism unknown: SNAP-internal close, manual edit, or a PATCH /{id} with a body). Implication: "not on the list" != "processed by us".
- Retention: rows fetched back to GAOB000119/120 (2025-12-15). Gaps in the id sequence (GAOB000100/101/105/110/115 -> No matching entity) may be purged rows OR ids belonging to other sequences/hosts; cannot tell. Treat retention as "at least 9.5 months in dev, upper bound unknown".
- `$filter` with a bare datetime literal (`DateCreated lt 2026-09-01T00:00:00`) returns HTTP 400; OData datetime syntax not established (irrelevant for processed rows since list excludes them).

## 5. Is the OBQ shared with another consumer? YES in prod for split customers — critical

- Slack thread (#bifrost-general, 2026-09-23/24, p1790148725881649): James Godsell: "the Fuse Snap API host was looking at the Jitterbit queue, instead of having a fuse dedicated queue ... both were looking at the Jitterbit queue." Denis Tomolea: Fuse "draining the queue before JB even attempting to pick up." Affected DRSAMS, DRSAMSPL, LISAUK, LISAPL (~920 + ~710 goods-out), Shackleton (ecom confirmations imported via Jitterbit posted to wholesale SFTP), Academically Gifted / AYM Studio ("Confirmations are switched off in the backend config and connector level but they are still draining the queue"; support bot: fixed 16:16; "Anything that's gone into Snap's queue since the fix is still there for Jitterbit to pick up"). Harry: "Fuse can pick up either everything, or nothing. ... split hosts have worked in the past."
- The OBQ is therefore a **single-consumer, first-to-process-wins queue**; Jitterbit and Fuse both read the open set for a Host and whoever PATCHes first removes it for the other. Per-Host queues (row `Host`, e.g. HOST_LISAUK; user FUSEAPI10 owns several hosts) are the isolation mechanism, mis-set for these customers. Rows carry no consumer attribution.
- Under early consume, the blast radius of this misconfiguration changes: today a row is only cleared after downstream *delivery/clear*; with Jitterbit also reading, a Fuse early-consume would remove rows JB expects within one poll (2 min) with no chance for JB. (Today the same drain happened, via the confirmation_made clear, ~1-2 min later — see GAOB timings — so JB race is essentially already lost in prod; the difference is what happens to rows Fuse cannot deliver: today they are cleared only on success or explicit drop.) Vault Support note 2026-09-23 confirms "Likely the same shared-Jitterbit-queue setup ... (hypothesis, not verified in SNAP)". I could not verify shared-queue topology in SNAP itself; dev shows only HOST_GADG.
- Outcome for the ~2k drained confirmations: needed **manual replay** from support ("we may have to manually replay all 2k+ confirmations") — evidence that today, once cleared/drained, SNAP cannot re-present them; recovery depended on replay-service failure records, not on SNAP. Whether SNAP can re-queue was never used.

## 6. How the poller and snap-adapter use the OBQ (relevant code facts)

- Read: `fetchFromOutboundQueue` GET /v2/snapoutbound `$top=1000`, `$filter=Transaction eq '<DESPATCH|RECEIPT|STOCK_MOVE>'`; requires `"Results" in resp.data` else throws (api.client.ts:194-217). **No $skip/orderby, so a backlog > 1000 rows for one Transaction type only exposes the first 1000 (ascending XDoc) each poll**; `fetchOutboundQueue` swallows any error to `[]` (fetch-outbound-queue.ts:31-45) — a failed read = silent empty poll.
- Claim: Redis `SET NX` on `identifiers.queueId` (XDoc), 10-min TTL, fail-open (vault known-context INC-30). Claimed rows are skipped on re-poll for the TTL (queue-lane.ts:dropClaimed).
- Clear by poller: only for its own drops (zero-qty goods-in, cancelled goods-out); `ConfirmationDisposer` **swallows** a failed PATCH (logs `Confirmation drop failed`, returns) (confirmation.disposer.ts:7-22). Row then stays open and re-appears next poll.
- Clear by snap-adapter: `POST /confirmation/made/:recordType` -> `res.sendStatus(202)` FIRST, then decode/clear (event.controller.ts:handleConfirmationMade). Failures of decode are logged only (`MessageDecodeFailed`) with no failure record, no row clear. Non-clearable record (missing queueId/businessId) or clear PATCH failure -> `confirmation_data_failure` (stage `confirmation_made`). Whether the clear PATCH is retried by the poller/adapter HTTP layer was not verified (pkg-node's snap AxiosBuilder excludes PATCH from retry per its changelog, but the poller has its own retry.interceptor.ts that I did not fully read). **Neither clear path inspects the response body**: poller `clearFromOutboundQueue` (api.client.ts:153-157) and snap-adapter `ConfirmationsService.clearFromOutboundQueue` (confirmations.service.ts:18-27) just await the axios call. SNAP is documented (pkg-node `snap` 0.1.0 changelog) to return HTTP 2xx with `{Status:"Error"}` for some write validation failures, and other snap-adapter writes guard against it (`assertSnapWriteOk` in work-order.service.ts:239; `Status === "Error"` checks in master-data/purchase-order/RGA services) but the OBQ clear does not — so a clear that SNAP rejected with 2xx+Status Error would be treated as success (row stays open, confirmation later re-announced as a duplicate). Whether PATCH /processed can actually do this is untested.
- Rows the service leaves on the queue indefinitely by design/accepted defect: work-order shipments at stage 29/39 (FUSE-1062, vault known-context); confirmations with unresolvable connector ("withheld", left on queue, retried each cycle) unless business `broadcastConfirmations`; cross-tenant entries skipped; entries whose SNAP shipment lookup returns nothing ("dropped, not failed — the queue item stays put", despatch.entries.ts). Under early consume each of these would need an explicit terminal outcome, since they currently rely on "row stays".
- pkg-node registry: `snapOutbound` write = patch only; specialRoutes next + markProcessed with the vendor caveat that the doc example hits /{id} instead (entity-registry.ts:810-843).
- The poller's list read has NO explicit open-row filter; it depends on SNAP's implicit list scoping (proven empirically here, undocumented in OpenAPI). If SNAP ever returned processed rows in the list, the poller would re-announce them (claim TTL only 10 min).

## 7. Exit paths table (OBQ-level)

| Path | Trigger | Outcome today | Recorded where | Terminal | Silent | Safety-net dependence |
|---|---|---|---|---|---|---|
| Row cleared after delivery | confirmation_made -> PATCH processed 2xx | Row Stage 90 + DateProcessed; retained, readable by id | SNAP row + snap-adapter `ConfirmationEvent.Processed` log/metric | yes | no | no |
| Clear PATCH fails | SNAP 5xx/401/404 on PATCH | confirmation_data_failure (stage confirmation_made); row stays open; poller re-announces after claim TTL (dup confirmation) | replay-service/collector | no (re-announces) | no | yes (row stays open -> re-announce) |
| snap-adapter crash after 202 | crash/undecodable between 202 and PATCH | Row stays open; re-announced later | decode failure log only | no | yes (no failure record) | yes |
| Poller drop-clear fails | PATCH fails in ConfirmationDisposer | swallowed; log only; row re-polled | log only | no | yes | yes |
| Poll read fails | SNAP error/circuit open | `[]`, skipped cycle | log/metric | n/a | partly | yes (rows just wait) |
| Backlog > 1000 per Transaction | large queue | first 1000 only per poll | none | n/a | yes | yes |
| Withheld / unresolved connector / WO stage 29-39 / missing shipment / cross-tenant | routing/enrich conditions | row left open indefinitely, re-evaluated every poll | log/metric only | no | yes for WO/missing shipment | yes |
| Fuse+Jitterbit share host queue | misconfigured Host | Fuse clears rows Jitterbit expects (or vice versa) | none in SNAP (no consumer attribution) | n/a | yes | n/a |
| Row leaves list without DateProcessed (Stage 90) | unknown SNAP-side | disappears from poller view unseen | none | n/a | yes | n/a |

## 8. Open questions

1. Re-queue: does `PATCH /v2/snapoutbound/{id}` accept `{Stage:"00", DateProcessed:null}` and re-open a processed row? (needs a write test on a throwaway dev row; not allowed here)
2. Is `PATCH /{id}/processed` idempotent (2xx / 400 / 404 on an already-processed row)? Vendor doc silent. Drives whether an at-least-once retry of the clear is safe.
3. What do `next`'s lease semantics look like (side effects, ordering, single record)? Not probed.
4. Mechanism behind rows with Stage 90 and DateProcessed null (GAOB000180, GAOB000200).
5. Is the retention of processed rows bounded (SNAP housekeeping job) in prod? Dev shows >=9.5 months; id gaps (000100-000115) unexplained.
6. Max `$top` and `$skip` behaviour above 1000 on this list route; whether SNAP truncates silently. (MCP tool caps at 100, so >100 not probed.)
7. Meaning/population of `Message` and `Error` columns (never non-null in dev sample).
8. Shared-queue topology in prod: which Hosts/users have both Fuse and Jitterbit reading the same Host; SNAP has no consumer attribution to prove it.
9. Why dev GADG has 19 rows open for up to 15 days (routing/gating? withheld?) — not investigated (out of area).
