---
title: G6 audit and D1 readiness, per business
date: 2026-10-02
gate: G6
verdict: 8 confirmation-live businesses pass; CHAMPO and LISAUK fail (verified), LISAPL fails (inferred); MANUCURIST, PHLUR, DRSAMS, DRSAMSPL unknown
---
# G6 audit and D1 readiness (2026-10-02)

**Verdict.**
- **Pass (8):** BYOMA, EPARFUM, STUBBLE, WILDSMITH, SPORTLUX, DOCKBAY, SAIRA. PURDYFIGG passes too, though less cleanly. In each, nothing but Fuse processes the outbound queue (OBQ).
- **Fail:** CHAMPO and LISAUK, verified at row level: another consumer processes their rows within seconds to minutes. LISAPL fails by inference.
- **Unknown:**
  - MANUCURIST is confirmations-enabled and busy in SNAP, but the poller has never seen a row for it.
  - PHLUR is not live yet.
  - DRSAMS and DRSAMSPL can't be read.

**Proposal:** dev soak on **HJF** (fuse-mocker simulator), first prod business **BYOMA**, then EPARFUM. Leave SAIRA and PURDYFIGG until C1 handles their stuck stock adjustments.

## Verdict table

Clears are Fuse's in the 7 days to 2026-10-02 ~12:40Z: snap-adapter `Confirmation processed` plus poller `Record dropped`. "Open" means OBQ rows open at 12:38Z, with the count older than 1 h in brackets.

| Business | G6 | Confirmations-enabled channel(s) | 7d Fuse clears | Open (>1h) | D1 notes |
|---|---|---|---|---|---|
| **BYOMA** | ✅ pass | SFTP | 224 | 0 (0) | 0 unexplained gaps, 0 clear-down failures. **Proposed first prod.** |
| **EPARFUM** | ✅ pass | SFTP | 382 | 1 (0) | 0 gaps, 0 clear-down failures. Proposed second. |
| **STUBBLE** | ✅ pass | SFTP | 1,464 | 1 (0) | 0 gaps. 9 clear-down timeouts, all rescued by re-announce. Good for exercising the failure path in a later wave. |
| **WILDSMITH** | ✅ pass | SFTP | 132 | 0 (0) | The one gap (`FORB002268`) is a poller zero-qty receipt drop. 13 manual-origin publishes. |
| **SPORTLUX** | ✅ pass | SFTP | 284 | 0 (0) | The one gap is a poller zero-qty drop. Ops re-push rows in SNAP, which re-delivers ([[g3-sportlux-represent]]). Brief CS. |
| **DOCKBAY** | ✅ pass | REST (webhook) | 1,034 (live since ~09-28) | 1 (0) | 0 gaps. A young integration, so a later wave. |
| **SAIRA** | ✅ pass | Shopify | 132 | 1 (1) | The one gap, `SIOB000866`, is a **stuck STOCK_MOVE**: open since 10-01 12:20 local and re-retrieved every cycle (128/day). It hits R3/R6 on enablement. |
| **PURDYFIGG** | ✅ pass (less clean) | REST + Shopify | 14,185 | 59 (52) | **Largest R3 backlog** (see below). Sampled gaps are stuck or slow rows; none was processed fast by another consumer. Do it last. |
| **CHAMPO** | ❌ **fail** | none (all off; polled until 10-02) | 329 (manual-origin) | 1 (1) | Another consumer processes rows 20–94 s after creation. The two consumers overlapped all week. |
| **LISAUK** | ❌ **fail** | none (skip list since 09-24) | 0 | 1 (0) | A 5-minute batch consumer processes every row, though Fuse hasn't polled it for 8 days. |
| **LISAPL** | ❌ fail (inferred) | none (skip list since 09-24) | 0 | 0 (0) | 8 days unpolled, shipping today, and nothing open. No row-level read. |
| **MANUCURIST** | ❓ unknown | SFTP | 0 (0 retrieved in 15 d) | 0 (0) | Active SNAP shipments today, but the poller has never retrieved one of its rows. |
| **PHLUR** | ❓ unknown | REST | 0 | 0 (0) | Not live in SNAP. 46 goods-in were published 09-18→10-02 with no clear-down logged, and none are left open. |
| **KAPPAHL** | n/a (not live) | SFTP | 0 | 0 (0) | The only shipment is SNAP's `DUMMY` placeholder. Re-audit at go-live. |
| **BABYMORI** | n/a (not live) | SFTP | 0 | 0 (0) | The same. |
| **SAMMCK** | n/a (not live) | SFTP | 0 | 0 (0) | The same. |
| **DRSAMS** | ❓ unknown | none (skip list) | 0 (2,003 on 09-18→09-23) | can't read | The stored SNAP password is blank. |
| **DRSAMSPL** | ❓ unknown | none (skip list) | 0 (142 on 09-18→09-23) | can't read | The stored credentials return 401. |

**Not assessed:** the rest of the skip list (GADG, ESCENTRICPL, BFA, ACADEMIC, SISTACO, AYMSTUDIO, EADEM, NUZEST, ESCENTRIC, JOLOVESPL, DISCOVERED, SHACKLETON). All their connectors are off and they aren't polled, so there was nothing to sample. Each needs this audit before its confirmations are switched on.

## Method
1. **Roster:** the 30 prod businesses with a SNAP backend, read from config-service (connector type, active, `confirmationsEnabled`), and the poller's skip list from `snap.poll.skipped_ineligible_business`.
2. **Fuse clears:**
   - Datadog, `@environment:prod`, flex tier (it reaches back about 15 days).
   - snap-adapter `Confirmation processed` by `@record.identifiers.queueId`.
   - snap-adapter `Confirmation clear-down failed`.
   - poller `Record dropped` by `@confirmationId` (the `ConfirmationDisposer`: zero-qty receipts, cancelled shipments).
3. **XDoc gap analysis.** XDocs are sequential per SNAP Host. A number in a business's range with no Fuse clear or drop is one of three things: a skipped number, a row still open, or a row someone else processed. Sampled gaps were read by id in SNAP (GET only, a few dozen in total). A row processed shortly after creation with no Fuse clear means another consumer.
4. **Open-row census:** one `GET /v2/snapoutbound?$top=1000` per business, with that business's own credentials. That is the call the poller already makes every cycle. Rows older than 1 h are the R3 backlog.
5. **Activity check for quiet businesses:** the three newest shipments (`$orderby=DateCreated desc`), to tell "not live" from "live but invisible to Fuse".

**What the OBQ is scoped by.** SNAP scopes the OBQ to the API user's Host, not to the instance:
- DOCKBAY's `TPOB001039` is invisible to the MANUCURIST user on the same instance (ilg001).
- EPARFUM, WILDSMITH and LISAUK all use the `FORB` prefix on ilg005, with independent counters.

So sharing an instance leaks nothing between tenants. A foreign consumer has to be reading the same Host, presumably a second API user configured for it.

**Clocks:**
- UK businesses: `DateCreated` and `DateProcessed` are both in BST.
- CHAMPO (Polish site): `DateCreated` reads as CEST and `DateProcessed` as BST.
- This was checked against a Fuse clear: CHAMPO `GIOB005753` was cleared at 04:48:05Z, and its `DateProcessed` is 05:48:05.

**Tool caveat: the snap MCP returns the wrong tenant's data.**
- `snap-mcp` caches one HTTP client per host URL and ignores the credentials on later calls (`src/snap/snap-api.service.ts`, `clientFor`). Every call to an instance therefore runs as whichever tenant called it first. In this session that was ilg001 → DOCKBAY, ilg003 → CHAMPO, ilg004 → SPORTLUX, ilg005 → PURDYFIGG.
- Two early "gap XDoc doesn't exist" reads were artefacts of this: SAIRA `SIOB000866` and WILDSMITH `FORB002268`.
- Everything after that was read by direct HTTPS GET with each business's own credentials.
- **Any snap-MCP read of a second tenant on the same instance is suspect until this is fixed.**

## Evidence: fails and unknowns

### CHAMPO (fail, verified)
Sampled gaps with no Fuse clear and no poller drop:

| XDoc | Transaction | Processed after creation (local clocks reconciled) |
|---|---|---|
| `GIOB005752` | DESPATCH | ~28 s |
| `GIOB005585` | STOCK_MOVE | ~67 s |
| `GIOB005000` | — | ~94 s |
| `GIOB005742` | — | ~20 h |

- **Fuse can't process that fast.** The poller runs every 10 minutes, so it can't produce sub-minute processing with no log.
- **The gaps are frequent.** Of 1,190 numbers in the 7-day window, 861 have no Fuse clear. A large block, `GIOB004624–5364`, is partly an artefact of where the window starts, but there are frequent single gaps outside it.
- **The overlap ran until today.**
  - Fuse polled CHAMPO until 2026-10-02 ~03:39Z, when its skip first appears.
  - All week it published CHAMPO goods-out as manual-origin broadcasts, delivered over SFTP.
  - So both consumers took CHAMPO rows, first-to-process wins, for the whole week.
- **One row is stuck for both consumers:** `GIOB005324` (DESPATCH `POL2649882`) has been open since 09-24 18:52 local. Neither consumer took it.
- **Who the other consumer is is not established.** Jitterbit is the likely candidate, but nothing here identifies it.

### LISAUK (fail, verified)
Fuse hasn't polled LISAUK since 09-24, yet its queue holds only rows created in the last few minutes. Consecutive rows, by id (local time):

| XDoc | Created | Processed | Lag |
|---|---|---|---|
| `FORB156842` | 13:11:12 | 13:15:29 | 257 s |
| `FORB156843` | 13:12:57 | 13:15:31 | 154 s |
| `FORB156844` | 13:14:35 | 13:15:34 | 59 s |
| `FORB156845` | 13:16:01 | 13:20:26 | 265 s |
| `FORB156846` | 13:17:43 | 13:20:28 | 165 s |
| `FORB156847` | 13:19:26 | 13:20:30 | 64 s |
| `FORB156848` | 13:22:28 | 13:25:23 | 175 s |
| `FORB156849` | 13:24:06 | 13:25:26 | 80 s |
| `FORB156850` | 13:27:45 | 13:30:30 | 165 s |
| `FORB156851` | 13:30:25 | 13:30:32 | 7 s |
| `FORB156852` | 13:34:38 | 13:35:25 | 47 s |

- **The cadence is a polling consumer's.** Rows are processed in batches on a 5-minute cadence (:15, :20, :25, :30, :35), about 2 s apart within a batch. `FORB155000` (09-27) and `FORB156500` (10-01) look the same.
- **The earlier hypothesis is now verified:** "same shared-Jitterbit-queue setup as DRSAMS" ([[2026-09-23-lisauk-goods-out-confirmations-drained]]). Another consumer reads this Host.
- **It follows that the 09-18 → 09-24 window was a live race.** The poller retrieved 2,752 LISAUK goods-out rows in that window.

### LISAPL (fail, inferred, no row-level read)
- The poller retrieved 1,420 LISAPL goods-out rows up to 09-24, and none since (skip list).
- SNAP shows new shipments today (`POL2678107`, `POL2678111`, `POL2678129`).
- Its OBQ has **0 open rows** after 8 days with nobody from Fuse clearing it, so something else is processing them.
- No XDoc ids were available to read by id (poller logs for LISAPL carry no queue id), so this rests on inference, not a row read.

### MANUCURIST (unknown, worth a look)
- **The facts:**
  - Its SFTP connector is confirmations-enabled.
  - SNAP has shipments created today (`SAL2776153`–`SAL2776157`).
  - Its OBQ has 0 open rows.
  - The poller has retrieved **0 rows in 15 days** (`fuse.confirmation.retrieved`).
  - Fuse cleared nothing.
- **In the last 16 days Fuse has only created purchase orders for MANUCURIST.** Its sales orders reach SNAP some other way.
- **Two explanations fit, and this audit can't separate them:**
  - SNAP doesn't queue MANUCURIST despatches to the Host Fuse reads.
  - Another consumer always processes them within the poller's 10-minute window.
- **Why it matters:** in the second case, switching D1 on would start a race. Ask whoever owns MANUCURIST's SNAP interface before enabling it. One row read by id would settle it, but its XDoc prefix is unknown.

### PHLUR (unknown)
- Only SNAP's `DUMMY` placeholder shipment exists, so it is not live in SNAP.
- Fuse published 46 PHLUR goods-in confirmations between 09-18 and 10-02.
- No snap-adapter clear-down and no poller drop was logged for any of them, and none is open now. How those rows were closed is unexplained.
- Re-audit when PHLUR goes live.

### DRSAMS / DRSAMSPL (unknown, can't read SNAP)
- **No working read credentials:** DRSAMS's stored password is blank, and DRSAMSPL's credentials return 401.
- **Fuse cleared most, but not all, of their sequence between 09-18 and 09-23:**
  - DRSAMS: 2,003 distinct rows over `DROB267032–269430`, 2,399 numbers (~84%).
  - DRSAMSPL: 142 over `TPOB000355–514`, 160 numbers (~89%).
- **The missing numbers could be either** non-despatch types or another consumer.
- **The shared-Jitterbit-queue hypothesis stays unverified for both.** They are on the skip list with every connector off.

### PURDYFIGG (pass, less clean)
No sampled gap was processed fast by someone else. The gaps are of two kinds:
- **Rows still open:** `SPLU033277`, `042022`, `043453`, `043894`.
- **Clear-down timeouts processed hours later with no Fuse log** (09-29/30 evenings): `SPLU039115`, `039214`, `041581`, `041585`, `041590`, plus `SPLU036464` (processed 09-30 08:29Z). Who processed them is unidentified: an operator, or a low-rate other actor. It is not the fast pattern seen at CHAMPO and LISAUK.

The 49 clear-down timeouts in 7 days are PURDYFIGG's, and the other 9 fleet-wide are STUBBLE's. Both are on ilg005.

## D1 readiness: backlog (R3) and channel gaps (R6)
**Rows older than 1 h at 12:38Z:**
- **PURDYFIGG: 52.**
  - 36 DESPATCH, the oldest `SPLU023707` from 09-21 17:40 local.
  - 23 STOCK_MOVE, the oldest from 09-24.
  - It re-retrieves about 2,875 stock adjustments a day, and `claimed_entry_skipped` was 29,002 in 24 h.
- **SAIRA: 1** STOCK_MOVE (`SIOB000866`), re-retrieved about 128 times a day.
- **CHAMPO: 1** DESPATCH since 09-24, but it fails G6 anyway.
- **Everyone else: 0.**

**Stock adjustments on the Shopify businesses.** SAIRA (Shopify only) and PURDYFIGG (REST + Shopify) have stock adjustments that are retrieved every cycle and never cleared.
- **Why they stay open was not traced here.** It could be a channel that doesn't take the type (R6), or something else.
- **Under C1/C2 they land in replay as unroutable failures on the first poll after enablement** (R3). Brief support first.
- **PURDYFIGG also has the stuck DESPATCH rows,** alongside the ongoing Shopify "Confirmation dispatch failed" rate.

**Connectors that take each type.** Every passing business has at least one confirmations-enabled connector.
- **SFTP businesses:** with a zero backlog, every row they emit already reaches a terminal outcome.
- **Not established for SAIRA and PURDYFIGG stock adjustments:** that a connector takes the type (see above).

## Proposed first dev soak and first prod business
- **Dev soak: HJF on fuse-mocker's snap-api simulator.**
  - Its `BACKEND_CONFIG` points at the simulator, so the **real poller and snap-adapter** run end to end.
  - DESPATCH, RECEIPT and STOCK_MOVE rows, and clear-down faults, can be driven through the `/api/v1` control plane. That covers a full day of the soak checks (published = made + replay failures; no row re-announced after a clear).
  - **Limit:** the simulator's `processed` PATCH only partly models real SNAP (G2 was simulator-only). Treat the dev soak as a check of the poller logic, not of SNAP's semantics.
- **First prod: BYOMA.**
  - G6 pass.
  - A single SFTP channel.
  - About 32 confirmations a day: enough signal, small blast radius.
  - 0 unexplained gaps, 0 open rows, 0 clear-down failures in 7 days, so nothing lands in replay on enablement.
  - On ilg003, away from the ilg005 clear-down timeouts.
- **Second: EPARFUM** (G6 pass, single SFTP channel, about 55 a day, 0 backlog).
- **Then:**
  - STUBBLE, which exercises the timeout-and-rescue path.
  - WILDSMITH.
  - SPORTLUX, after briefing CS on re-push.
  - DOCKBAY.
- **SAIRA and PURDYFIGG last,** after C1 handles their stuck stock adjustments and support is briefed on the R3 backlog.
- **Not D1 candidates:** CHAMPO, LISAUK and LISAPL fail G6. Their connectors are all off today, so nothing is owed. Switching their confirmations on is a Jitterbit cutover conversation, not a D1 step.

## Unknowns, stated plainly
- **The identity of the other consumer** on CHAMPO, LISAUK and (inferred) LISAPL. Jitterbit is assumed, not shown.
- **MANUCURIST:** is there no OBQ row for Fuse's Host, or does another consumer win every time?
- **PHLUR:** how 46 published goods-in rows were closed with no Fuse clear-down.
- **DRSAMS / DRSAMSPL:** G6 can't be assessed without working SNAP read credentials.
- **PURDYFIGG:** who processed the clear-down-timeout rows hours later.
- **SAIRA / PURDYFIGG stock adjustments:** the exact reason they stay open.
- **Not live yet** (KAPPAHL, BABYMORI, SAMMCK, PHLUR) and the 12 not-assessed skip-list businesses: G6 must be re-run at go-live or before enablement.
