---
tags: [support-triage]
date: 2026-09-18
business_id: SPORTLUX
customer: "SportLux (Dickies)"
connector: sftp
reporter: "James Godsell"
channel: "DM (private, not bifrost-general)"
thread_url: "https://gfsdeliver-eng.slack.com/archives/D0BKW2XEM2L/p1789741458211179"
opened_at: "2026-09-18T14:24:18Z"
outcome: escalated
session_id: 3d1affaf-d64c-40b3-a43d-732addd7ecd7
status: open
---
# SportLux/Dickies: 331 "unfulfilled" orders (11–18 Sept) — 58 never reached SNAP, 273 shipped but confirmations uncollected since 09-11

> **Verified 2026-09-18 evening.** Every claim below was re-checked against an independent source (SNAP by two keys, dedupe, collector, the GCS bucket, sftp-connector source, VM session logs). Three earlier claims in this record were **wrong and are retracted** — see *Retractions* at the end. Don't quote the earlier version.

## Reported
James Godsell DM'd Harry Fitzgerald (not in #bifrost-general) asking him to join a 16:30 call with SportLux/Dickies and their account manager: the customer reports 192 orders that haven't imported, and dispatch confirmations "in the wrong format". James's hypothesis was a `columnOrder`/line-number edit he'd made to the connector mapping. Call pushed to Monday.

**Continuation of the unresolved 2026-09-15 thread** ([[2026-09-15-sportlux-dickies-orders-missing-since-sept1]]), director-escalated on the customer's side. Harry was separately sent the customer's list: an email from Davide (SL IT, via ILG, cc Indre Mikulskyte) with `unfulfilled order ILG _ 11th sep to 18th sep.csv` — **331 unique order references** (`S-SO-0XXXXX` Business Central doc numbers), 11–18 September. The customer wants ILG to confirm how many are genuinely missing before they re-upload in one batch.

## What the 331 actually are (exhaustive, not sampled)

| Bucket | Count | Evidence |
|---|---|---|
| In SNAP — received via Fuse (dedupe hold present) | 259 | dedupe-list cross-ref; 11/11 spot-checked in SNAP are Stage 90 shipped with tracking |
| In SNAP — no Fuse record at all (single 2026-09-16 09:26Z cluster, sequential refs) | 14 | SNAP by `CustomerRef`; looks like a manual/bulk import outside Fuse — hypothesis |
| **Not in SNAP — in a file Fuse received but silently skipped** | **29** | `ILG_SO_Export 1_1109.csv`, `3_1109.csv`, `2_1609.csv` — see mechanism below |
| **Not in SNAP — never in any file Fuse holds** | **29** | grep of all 161 archived + 9 errored inbound files + live inbound dir; `2_1109.csv` doesn't exist (1 and 3 do); ranges 024517–024575 and 024703–024717 absent everywhere |

"Not in SNAP" was checked both by `CustomerRef eq 'S-SO-…'` (all 72 candidates) and, for a sample, by Shopify number `SalesOrder eq '#59xxxx'` — same answer. Bucket versioning on the SFTP bucket is **off**, so nothing deleted is recoverable.

**So the customer's "unfulfilled" list is mostly shipped orders they don't know about.** 273 of 331 are in SNAP (sampled: all shipped). The reason they look unfulfilled to the customer is the confirmation finding below.

## Finding 1 — Dispatch confirmations are being written, but the customer has collected none since 2026-09-11 15:44Z
- The `from_ilg/sales_order_confirmations/*-confirmation.csv` files **are** the goods-out (dispatch) confirmations — the confirmation recordType is `sales_order`; the use case is `goods_out_confirmation`. Header = the configured goods-out mapping (`AccountID … Packages_SSCC … Stage, StockPool, Service, Carrier, TrackingNumber`), Stage 90, tracking populated. Fuse writes them every couple of minutes as shipments despatch (294 writes in 30 days).
- **186 of those files are sitting uncollected in the customer's outbound folder**, from `2026-09-11-1544` onward (3 on 09-11, then 53/51/21/27/30 per weekday 09-14→09-18). Everything before 09-11 15:44Z is gone — the customer's client fetch-and-deletes (established in [[2026-07-28-sportlux-oc-confirmation-missing]]). Only other survivor is a 0-byte file from 2026-05-06.
- **The customer's SFTP client is still logging in** — ~22–24 sessions per weekday, every 15 minutes ~09:00–15:00Z, including today. It connects; it does not take the files.
- Fuse side looks healthy in every direction I can observe: gcsfuse is mounted `--stat-cache-ttl 0 --type-cache-ttl 0` (Cloud Run's direct-to-GCS writes are immediately visible to SFTP listings); no mount errors or VM restarts in 10 days of VM logs; uploads through the same mount worked all week. **Cannot fully rule out** a listing-visibility problem without shell access to the VM.
- Header/column order is **identical** on 09-11 15:44Z, 09-18 06:32Z (before James's PUT) and 09-18 16:46Z (after it). Our output format did not change in the window. `GORespLines_LineNumber` = SNAP `SOLineId` (20000/30000…) = the line number the customer sent inbound. Whatever "wrong format" means, it isn't visible from our side — **need an actual rejected file from the customer**.

## Finding 2 — 29 orders were uploaded into `archive/` and silently skipped (real platform behaviour, no signal)
Mechanism, confirmed three independent ways:
1. **Logs.** A normal file produces `Incoming file event: …/create_sales_order/<file>` → `Attempting to download …` → (processing, dedupe record) → a second `Incoming file event: …/create_sales_order/archive/<file>` from Fuse's own move. The 3 broken files produce **only** the archive-path event, once, ever.
2. **Code.** `sftp-connector/code/src/gcs/storage.service.ts:288` — `if (parts.length > 4) return false;` with the comment *"If parts is longer than 4, we can assume the client has created their own directory, like archive... we don't care for these"*. A path with an extra segment (`…/archive/x.csv` = 5 parts) is dropped **before any log line, metric or failure record**.
3. **Object metadata.** Fuse's own archive move stamps `custom_fields.fuseCorrelationId` on the archived object (`file-routing.service.ts`, `CORRELATION_METADATA_KEY`). `1_1609.csv` / `1_1809.csv` (processed normally) carry it. `1_1109`, `3_1109`, `2_1609` — and every file in the 09-17 10:20 burst — **have no custom metadata**. Fuse never touched them.

**Who put them there:** at every one of the four archive-path write moments, a session on **the customer's SFTP login (`FUSE_DD2AF79592`)** had opened seconds earlier — 08:08:20Z for a write at 08:08:50Z, 14:43:20Z→14:43:39Z, 11:12:39Z→11:12:59Z on 09-16, and 10:16:41Z for the 10:20–10:21Z burst on 09-17. Each of those sessions is **off the regular 15-minute poll cadence** — a second client or a human, not the automated poller. So: uploaded via the customer's credentials, directly into `archive/`. **Whose hands were on those credentials is not determinable from our logs** — sshd `Accepted publickey` (source IP) lines and sftp-server transfer logs are **not shipped to Cloud Logging**, and **GCS data-access audit logging is off** for the bucket. Note James Godsell had direct access to this customer's prod SFTP mid-week (per the 09-15 thread, where Harry asked him to stop); the 09-11 events predate that thread.

The 09-17 10:20Z burst (91 files, June → 2 Sept, undated names like `ILG_SO_Export 27.csv`) went the same route and was equally ignored — but spot-checks of 5 refs across it show all were **already in SNAP, shipped on their original dates**. Harmless duplicate re-upload; nothing stuck from it.

## Finding 3 — Everything abnormal starts on Thursday 2026-09-11
- Customer SFTP sessions: **50** on 09-11 vs 22–24 on every other weekday (extra off-cadence sessions clustered 08:xx and 10:xx).
- First archive-path uploads: 08:08:50Z and 14:43:39Z.
- Connector config **PATCHed via fuse-ui at 13:46:12Z** (`PATCH …/connectors/conn_bad08a939d7a4d38a98dad51935bef44`, correlationId `ef3c0caf-…`; revision fanned out to sftp/snap/rest connectors). config-service exposes no revision-history endpoint, so **what it changed is unknown from here** — ask James.
- Confirmation collection stops after 15:44Z.
- Also on this connector: `PUT …/mappings/goods_out_confirmation` 09-10 08:46Z, and again **today 14:51:56Z** (fuse-ui — ten minutes after James's DM saying he believed column order was the problem).
- 12–13 Sept had no inbound files and no SFTP sessions — that's Saturday/Sunday, not a gap.

## Retractions (from the first pass of this record)
- ~~"Dispatch confirmations do not appear to be reaching SPORTLUX's SFTP at all"~~ — wrong. I misread `confirmation type sales_order` as an order acknowledgement. They are the dispatch confirmations and are being written normally. The real problem is collection (Finding 1).
- ~~"`snap-polling-service` StU-not-found warnings are the likely mechanism"~~ — wrong. Non-blocking: `consignmentsToCanonical` falls back to `{}` and still emits the consignment with its SSCC; the warn is even commented out in current master (`goods-out.confirmation-handler.ts:~498`). Noise, not a cause.
- ~~"dedupe-service 4,110 held records is a release bug"~~ — wrong. Holds are only deleted via `release()` on the failure path; there is no TTL index (`sales-order.service.ts:195–205`). Held count ≈ processed count by design (collector holds 4,111). Not a defect.
- ~~"Zero inbound files for 12–13 Sept is a real gap"~~ — weekend.
- Earlier ~50–55 estimate → exact **58**; earlier "185 ≈ 192 replay backlog" → unrelated older backlog (still in Follow-ups).

## Fix / Resolution
No resolution reached; call Monday. Read-only throughout; nothing posted to Slack. For Monday:
- **Give the customer the exact split**: 273 of 331 are in SNAP (shipped), **58 never reached SNAP** — 29 they'll need to re-send (never received in any form: the whole `2_1109` export plus two mid-week ranges), 29 were uploaded into the `archive/` sub-folder and must be re-uploaded to `to_ilg/create_sales_order/` itself.
- **Ask the customer (a) for one of the "wrong format" files they rejected, and (b) what changed in their SFTP client/process on Thu 11 Sept** — that day's session count doubled, uploads started landing in `archive/`, and confirmation collection stopped. The 186 uncollected confirmations are still there for them to pull.
- **Ask James what the 09-11 13:46Z connector PATCH and today's 14:51Z mapping PUT changed**, and confirm he wasn't logged into the customer's SFTP at 08:08Z/14:43Z on 09-11, 11:12Z on 09-16, or 10:16Z on 09-17 — if he was, the "who" is answered.
- File a defect for the silent archive-path drop: `storage.service.ts:288` should at minimum log at warn with the path (ideally metric + move to `error/`). Customer-uploaded files vanishing with zero signal is the actual platform gap here, and it can hit any SFTP customer.
- Observability follow-ups (own tickets): ship sshd auth + sftp-server transfer logs from the SFTP VM to Cloud Logging/Datadog; enable GCS data-access audit logs on `sftp-connector-prod-storage`. Either would have answered "who uploaded this" in one query.

## Follow-ups (separate from this complaint)
- **185-record replay-service backlog, 2026-06-03 → 2026-09-07, never redriven** (`attempts: 0`). Includes the still-unfixed "Description — Too big (≤30 chars)" defect from [[2026-07-29-sportlux-sku-description-too-long]] (still producing `master_data` failures on 2026-09-14), and 6 orders (S-SO-022262/022282/022257/022265/022261/022283) that hit a `snap-adapter` crash `Cannot read properties of undefined (reading 'requestStart')` at 2026-09-02T06:47:24Z, marked `replayable: true` — redrive once someone confirms scope.

## Evidence gaps
- Who held the customer's SFTP key during the off-cadence sessions (no IP/transfer logs shipped; no GCS audit logs).
- Contents of the 09-11 13:46Z connector PATCH.
- Why the customer's poller lists-but-doesn't-collect since 09-11 — needs their side, or VM shell access to watch a session.

## Links
- Slack DM (not posted to): https://gfsdeliver-eng.slack.com/archives/D0BKW2XEM2L/p1789741458211179
- Prior threads: [[2026-09-15-sportlux-dickies-orders-missing-since-sept1]], [[2026-07-29-sportlux-sku-description-too-long]], [[2026-07-28-sportlux-oc-confirmation-missing]], [[2026-08-24-sportlux-po-truck7-purchaseorderid]]
- Related gotcha: [[reference_columnorder_must_match_legacy_transformer]]
