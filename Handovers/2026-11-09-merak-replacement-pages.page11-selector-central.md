The central Firebird database is a hub, not just a store. It is where every despatched parcel becomes GFS's record, gets its status, is billed and is passed on. About 295 stored procedures (297 when names seen only through `ALTER` are counted) and 236 triggers hold most of the status logic. The upload server receives each site's uploads and runs `REG_*` procedures. A stream of change feeds hands shipments to ECM and other readers. The repository's schema scripts stop at `update_417` and the live schema has moved on, so every catalogue on this page is a lower bound.

This page is about the central side only. The site side has its own page. A third page, "Between a Site and the Centre: Uploads, Downloads and What Crosses", covers what travels between them. It is part of the Merak research and is not a plan. Whether Merak replaces Selector or ECM is a hunch.

Evidence tags: **CONFIRMED** (read in source), **STATED** (a document or note says it), **INFERRED** (a reading of code that nobody saw run), **UNKNOWN**. A `[??]` marks a fact we do not have. Section 10 lists them.

## What sits around the central database

The central database does not work alone. Ten server programs read or write it, and the installers name three more whose source is not cloned. All are Delphi programs unless stated. Each takes its connection settings from the Windows registry of its own host.

| Program | What it does | Database access | How it starts | Evidence |
| --- | --- | --- | --- | --- |
| UploadServer | Web service for sites. Takes shipment uploads, registers sites, hands out updates and version information. 18 methods. | Reads and writes. Calls `REG_*`, `GET_*` and `CHECK_*` procedures. | Every site call, inside IIS. | CONFIRMED |
| Manager | Desktop admin tool for GFS staff. Edits master data, builds site packages, imports carrier routing files, fixes shipments. | Reads and writes through about 150 datasets. | A person. | CONFIRMED in part. Most of two large source files unread. |
| IE (Import/Export) | Windows service. Scheduled carrier jobs: send pre-advice files, import shipments, import carrier status updates. | Reads and writes. Calls 35 distinct procedures. | A schedule built from database rows, plus Firebird events. | CONFIRMED for the shell and dispatch. The carrier code (about 19,000 lines) is unread. |
| Notifier | Sends consignee email and SMS on status changes. | Reads the notification queue, writes sent state. | Firebird events, plus an SMS timer. | CONFIRMED in part |
| WR (Web Report) | Sends scheduled customer reports. Runs the SQL text stored in `WR_TEMPLATES`. | Reads templates, writes history, disables a failing report. | A schedule plus events. | CONFIRMED. One source file is dead code. |
| HermesService | Fetches Hermes (Evri) routing files, loads them, builds the site update package. | Reads and writes. | A timer. | CONFIRMED |
| ParcelForceService | Same job for Parcelforce routes. | Reads and writes. | A timer. | CONFIRMED |
| HDNLUpdater | Same job for HDNL (Collect+) routes. Raises the carrier's route version. | Reads and writes. | Command line only. The external schedule is `[??]`. | CONFIRMED |
| ClipperUpdGenerator | Rebuilds the Clipper package when the route version date moves. | Reads route data, writes the package row. | A timer, and an event no readable code posts. | CONFIRMED |
| Backup | Backs up the database, then optionally runs `REMOVE_OLD_DATA`. Can also restore. | Firebird backup service, plus one procedure. | A scheduler outside the repository. The owner is `[??]`. | CONFIRMED |
| Web scanner (`GFSWebScanner`, `WebScanCom.dll`) | Appears to poll carrier tracking and write status. | The procedures it needs exist in the database. | `[??]` | INFERRED. Source not cloned. |
| Second scan server (`SoapHistScanServer.dll`) | Named by an installer, with proxy settings. | `[??]` | `[??]` | UNKNOWN |
| Collection service (`GFSCollService`) | Appears to run pickup booking over the collections tables. | A trigger posts its event. | `[??]` | INFERRED. Source not cloned. |

Hermes has a gap. Its 2024 file format loads data but builds no site package and never raises the route version. Whether something else does so is `[??]`.

Other readers and writers are known only from notes. They are the Firebird Transfer Service, `GFSPublisher`, the Royal Mail sync service, the Scan Injector, the billing application and Seeker (all STATED, none read).

## What the database holds

The repository's 2014 base schema plus 416 numbered update scripts give 475 tables, 295 procedures, 236 triggers and no views. The method: a script strips comments, then replays every `CREATE`, `CREATE OR ALTER`, `RECREATE` and `DROP` in order. Counts from plain `grep` agree for the base schema. Production differs, as the next section explains.

Tables fall into areas. Grouping is by name prefix and the counts overlap, so treat them as approximate.

| Area | About | What it holds |
| --- | --- | --- |
| Shipments, pieces, history | 27 | `SHIPMENTS` (125 columns in 2014), `SHIP_PIECES`, `SHIP_PIECES_HIST` (scan history), comments, customs, labels, documents, the web-scanner queue |
| Recycle | 3 | `RECYCLE_SHIPS`, a full copy of a shipment, plus its parcel and unit tables. Duplicate uploads are parked here. |
| Customers, sites, contracts, services | 45 | `CUSTOMERS`, `CUST_SITES`, `CUST_CONTRACTS`, `PRODUCTS`, `SERVICE_LEVELS`, number ranges |
| Carriers, aliases, scan codes, routing | about 130 | `CARRIERS`, `CARRIER_ALIASES`, `CARRIER_SCAN_CODES`, `SCAN_CODE_MAPPING`, and route tables per carrier |
| Billing, invoices, tariffs, commission | about 130 | `INVOICE*`, `CHARGE*`, `TARIFF*`, `CO_*`, carrier invoice landing tables |
| Queues, replication, service control, logs | about 50 | `NOTIFY_ITEMS`, `RM_REPLICA`, `RELOAD_PUBLISH_SHIPMENTS`, schedules, service logs |
| Site packages and versions | 8 | `CUST_SCRIPTS`, `CUST_SITE_UPDATES`, `CARRIER_UPDATES`, version ledgers |
| Users and web access | 7 | `WEB_USERS`, web scanner registration tables |
| Claims, comments, collections | 26 | `CLAIMS` and `CLAIM_*`, `COLLECTIONS*` |
| Labels, manifests | 15 | Label and manifest definitions, including blob columns |
| Reference | about 45 | Countries, currencies, public holidays, the Royal Mail address file |

The 2022 schema has no table named for tickets. The change feed does carry tables named `v_tickets`, `v_ships_comments` and `v_collections` (Datadog). The repository has no views, so those names are either later additions or views made after 2022 (INFERRED).

### Procedures

Counts by name prefix, taken from the last definition of each procedure. The prefixes are `GET_` 120, `REG_` 38, `UPDATE_` 16, `ADD_` 12, `CHECK_` 10, `SET_` 10, `UPD_` 10, `UPS_` 9, eight customer-specific report procedures, `NEXT_` 5, and about 55 others.

Only about 72 of the roughly 297 procedures are called from readable server code. That count comes from a pattern search of `execute procedure` and `from X(` calls, so it is approximate. The other 225 or so are called by triggers, by other procedures, by unread programs, or by nobody. Removing any of them is unsafe until someone finds its callers.

The ones that matter most for delivery:

- **`REG_SHIPMENTS`.** The upload entry point for a shipment (next section).
- **`REG_SHIP_ITEMS`.** Registers parcels. An unknown carrier returns silently, so the site sees success and the parcel is gone.
- **`GET_SCAN_CODE`.** Turns a carrier's scan code into a GFS status. Unknown codes become 207 and are learned.
- **`SET_PARCEL_HIST`.** Inserts a scan into parcel history, once per parcel, carrier, consignment, scan date and text.
- **`SET_SHIPMENT_HIST`.** Copies the best scan onto each parcel, then rolls the parcels up into the shipment status.
- **`UPDATE_STATUS` and the per-carrier `UPDATE_*_STATUS`.** Carrier status import, through `GET_SCAN_CODE`.
- **`CHECK_SHIP_STATUS`.** Sets 1005 ("assumed delivered") for stale shipments. It takes one scanner's identifier but acts on every site.
- **`COMMIT_WEB_SHIPMENTS`.** Moves web-created shipments to their next status in bulk. Site 0 commits every site's shipments.
- **`REPLACE_SHIP_BY_RECYCLE`.** Manager's "replace" (section 8).
- **`GET_UPD_VER` and `GET_CARRIER_UPD_VER`.** Version checks that also record what each site has installed.
- **`CHECK_CARRIER`.** Turns a carrier alias into the canonical carrier name. Every program calls it.
- **`NEXT_CONS_NO`.** Allocates consignment numbers from per-site ranges.
- **`MARK_FOR_SCANNING_VER2`.** Lets the web scanner claim work.
- **`REMOVE_OLD_DATA`.** The archive procedure (section 8).

### The repository is not the live schema

The last numbered script is `update_417`. Its newest dated change is 28 May 2022, though the repository snapshot was committed in Oct 2023 (an earlier note said `update_411`, which is wrong). Evidence that the live schema has moved on:

- The upload server (Apr 2026) calls `REG_SHIPMENTS` with a `:special_service` parameter. No script defines it (CONFIRMED).
- Manager and IE call two procedures and four tables that no script defines (CONFIRMED).
- The Transfer Service queue tables are not in the scripts, and no script mentions `TRANSFER_QUEUE` (CONFIRMED).
- The Test replica reports about 25 triggers on `SHIPMENTS`. The scripts hold 16 (STATED).

Anyone building from these scripts would get the wrong contract.

## What happens to an upload

This is the central half. The upload server receives a zip, connects to central with the site's own database account, then runs five loops in one transaction. Each loop runs one procedure per row, in this order: `REG_SHIPMENTS`, `REG_SHIP_ITEMS`, `REG_SHIP_CUSTOMS`, then `REG_SHIP_UNITS` and `REG_SHIPPER` if present. The wire format and the site's view are on "Between a Site and the Centre: Uploads, Downloads and What Crosses".

1. **New consignment.** `REG_SHIPMENTS` does a plain `INSERT` into `SHIPMENTS`. Every insert trigger then fires, including the one that posts `UPLOAD_2_GCP` (CONFIRMED).
2. **Existing consignment.** The procedure copies the old row to `RECYCLE_SHIPS` only when key fields differ. The fields are despatch date, site, contract, service, pack count, address line 1, town, postcode and country. It does not update `SHIPMENTS`. Otherwise the new data is dropped (CONFIRMED for the first branch read; four of five carrier branches unread).
3. **Temporary numbers.** A consignment or parcel number that starts with `TMP` is forced to status 106. Central logs an alert row and still keeps the record. The business meaning of 106 is INFERRED, because no status table row was found in the scripts.
4. **Parcels.** A duplicate parcel, or a parcel that arrives before its shipment, goes to the recycle tables. Five carriers also get a second, paired parcel row.
5. **Failure.** Errors return a negative code to the site, but **the transaction commits even when a row failed**. Rows processed before the failure stay in central. A retry then takes the duplicate path for those rows (CONFIRMED).

The three customer-specific `REG_` procedures named for one retailer copy the same duplicate check. They match on consignment and carrier, send mismatches to `RECYCLE_SHIPS`, and use hard-coded defaults, including status 310. No readable program calls them.

## How a shipment gets its status

Status is written in many places. About 30 procedures contain a direct `UPDATE` of a status column (27 counted in the 2022 source), and 19 procedures insert shipments. Several triggers also rewrite status. The set is larger, because many carrier procedures call these indirectly. The main routes:

- **Carrier files through IE.** IE calls the per-carrier `UPDATE_*` procedures, which call `GET_SCAN_CODE`, then insert into parcel history. IE then calls `SET_SHIPMENT_HIST` (CONFIRMED for the dispatch; carrier bodies unread).
- **Scan codes.** `GET_SCAN_CODE` looks the code up in `CARRIER_SCAN_CODES`, then `SCAN_CODE_MAPPING`. An unknown code becomes 207 and the procedure inserts a mapping row, so later sightings count as known. It is a read procedure that writes. DPD and Interlink code 17 default to 202. Status 999 becomes 1000 for single-parcel shipments.
- **Roll-up.** `SET_SHIPMENT_HIST` sets 999 when every parcel is accounted for but not all are delivered.
- **Assumed delivery.** `CHECK_SHIP_STATUS` sets 1005 between 200 and 999 after a per-scanner age or pause limit. Its caller is not in readable code. The web scanner is the likely one (INFERRED).
- **Triggers.** Carrier-specific rules sit in trigger code, for example Royal Mail 1005 and 3000, Collect+ 100 to 101, and Packeta new shipments at 202.
- **The Scan Injector.** It must call `GET_SCAN_CODE`, `SET_PARCEL_HIST` and `SET_SHIPMENT_HIST`. Inserting into parcel history alone updates neither parcels nor shipments (CONFIRMED constraint; the Injector itself is STATED).

For the six seams where this meets ECM, see [Selector and ECM Coupling](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354418743). For the journey after the hand-off, see [Shipment Journey Through ECM](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354975746) and [From Label to Invoice](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354353232).

## Who reads or writes central

| Consumer | What it reads or writes | Mechanism | Evidence |
| --- | --- | --- | --- |
| Firebird Transfer Service | Reads a transfer queue, publishes shipment, parcel and reference-table messages | Polls the queue and reacts to Firebird events | Live in production. Datadog shows 3,022,807 rows transferred in the 15 days to 7 Nov 2026, and heartbeats and logs up to 11 Nov. Trigger text and code unread. |
| `UPLOAD_2_GCP` and `GFSPublisher` | A trigger posts the event after every shipment insert. The listener publishes shipments and marks them published. | Firebird event | Trigger CONFIRMED. The listener is STATED. Datadog has no metric or indexed log under any searched name, so no sign it runs. That is absence from Datadog, not proof it is stopped. |
| Royal Mail sync | Drains `RM_REPLICA`, which master-data triggers fill | Event plus table | Queue CONFIRMED. Consumer STATED, unread. |
| Billing | Billing tables live in central. The application reads them. | Direct SQL | Tables CONFIRMED. Reader STATED. |
| Seeker | Reads shipment data | Direct SQL | STATED |
| Data platform | Extracts about 70 tables by query, not by trigger | Direct SQL | STATED (Data Solutions page, Dec 2025) |
| Manager | Writes master data, builds packages, fixes shipments | Direct datasets and procedures | CONFIRMED |
| IE | Creates shipments from carrier files, writes status, exports pre-advice | Timer plus events | CONFIRMED in part |
| Portals | Create shipments, commit them, read tracking and claims, set manual status 100 or 1003 | `REG_WEB_*`, `COMMIT_WEB_SHIPMENTS`, `GET_CLAIM*` | Procedures CONFIRMED. Callers STATED. |
| Scan Injector | Writes carrier scans into central | Procedures above | STATED |
| Tickets and comments | A trigger writes `SHIPS_COMMENTS` when `gfs_comments` changes. Claims and collections have their own notes tables. | Trigger | Trigger CONFIRMED. Ticket tables `[??]`. |

The Transfer Service feed is live. The other feed has no data in Datadog. We do not know whether both exist in production, which one produces `fb.shipments.v1`, or whether the Transfer Service replaced the publisher. The counts line up with the Transfer Service only indirectly. Five small reference tables match the modernizer's input counts exactly, but the shipment counts differ by 11.2 per cent, and no topic-level metric exists.

The topics the feeds publish to are on [ECM Pub/Sub Topics](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/356155424). Trigger and feed detail is in the Firebird change feed note, and this page does not repeat it. In short: central `SHIPMENTS` gets one plain insert per consignment from an upload, and two feeds may leave it. Nobody has read the production trigger text.

## What central sends back to sites

Everything central sends to a site is a zip held as a blob in the database. Manager or a route program builds it from `SELECT` lists stored in `CUST_SCRIPTS`, and stores it in `CUST_SITES.VER_DATA`, `CUST_SITE_UPDATES` or `CARRIER_UPDATES`. Sites pull on demand and the server never contacts them. The pattern is on "Between a Site and the Centre: Uploads, Downloads and What Crosses".

## Housekeeping and things that teach themselves

- **Pruning.** `REMOVE_OLD_DATA` hard-deletes shipments with status 100 or 1000 and above once they pass a per-carrier archive period. It also deletes old FTP logs, carrier updates, service logs, report history, site updates and notification items. The Backup tool runs it after each backup. Whether production runs it, and the periods, is `[??]`. A reader that assumes history is permanent is wrong if it runs.
- **Learning scan codes.** `GET_SCAN_CODE` writes unknown codes into `SCAN_CODE_MAPPING` as 207. The status set is partly data that people curate after the fact.
- **Replace.** Manager's "replace" renames the old shipment's key to `<consignment>#N`, with parcels renamed to match. It then inserts the recycle copy as a new shipment. A consumer keyed on consignment and carrier sees a new shipment and an orphan. The existing notes say this can bill twice (STATED). The rename and insert are CONFIRMED.
- **Claim columns.** IE and the web scanner use `ship_state`, `state_obj` and `state_date` on `SHIPMENTS` as claim leases. Each claim is a row update. Whether this adds to the feed's message count is a hypothesis, not evidence.

## What a replacement would need to keep

This is hypothetical. In delivery terms, a replacement would need:

- One place where every despatched shipment becomes a record, including partial and repeated uploads.
- The status rules that sit in procedures and triggers today, written down first.
- A defined answer to a repeated upload: when it is dropped, when it is parked, and who resolves it.
- A feed that downstream services can rely on, with a known source of truth for what it carries.
- The housekeeping: number ranges, scan-code learning, version ledgers and pruning.
- A versioned schema. Today it is a contract that nobody versions, and the repository copy is years behind.

## Not confirmed yet

- Production triggers: the `TRANSFER_QUEUE` triggers and the roughly 9 extra triggers on `SHIPMENTS`. `[??]`
- Live `CUST_SCRIPTS` rows and the schedule rows that drive IE and WR. `[??]`
- The Firebird engine version on central. The installer says 1.5, but the scripts use `CREATE OR ALTER`, so it is later. `[??]`
- The Backup schedule, the HDNL schedule, and whether archive is on. `[??]`
- Unread source: the Transfer Service, `GFSPublisher`, Royal Mail sync, billing, Seeker, the Scan Injector, the web scanner. `[??]`
- Listeners for the alert events (`RECYCLE_*`, `*_ALERT`, `P2P_ADD`) and for `CLIPPER_ROUTES`. `[??]`
- Callers of the other 225 or so procedures. `[??]`
- Unread parts of IE, Manager, and four of the five `REG_SHIPMENTS` carrier branches. `[??]`
- Grants. The export holds four roles and no `GRANT` statements. `[??]`
- Where the feed's `v_tickets` and the other `v_` names are defined. `[??]`
- The business meaning of status 106. `[??]`

## Sources

Repository snapshots read (ADO legacy repositories, local clones):

| Repository | Commit | Date |
| --- | --- | --- |
| V4-Server-Database | 82dde6b | 2023-10-11 |
| V4-Server-UploadServer | 5773b8e | 2026-04-15 |
| V4-Server-Manager | a9bfab7 | 2026-04-27 |
| V4-Server-IE | 2e34988 | 2026-09-16 |
| V4-Server-Notifier | 9a0972c | 2023-10-11 |
| V4-Server-WR | 209de5b | 2023-10-11 |
| V4-Server-HermesService | 3fcf378 | 2025-09-25 |
| V4-Server-ParcelForceService | 752a310 | 2023-10-11 |
| V4-Server-HDNLUpdater | 6a4eae8 | 2023-10-11 |
| V4-Server-ClipperUpdGenerator | 7318ac0 | 2023-10-11 |
| V4-Server-Backup | 41f7b1e | 2023-10-11 |
| V4 Installation | 2bf851e | 2023-06-28 |

Other evidence: a read-only Datadog check on 11 Nov 2026, covering 23 Oct to 7 Nov 2026. Two Confluence pages, on the Transfer Service and on Data Solutions extraction. The ECM notes on the change feed.

Related pages: [Legacy Selector](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/351764483), [Customer Data Flow](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/352157700), [Selector and ECM Coupling](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354418743), [From Label to Invoice](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354353232), [Shipment Journey Through ECM](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354975746), [ECM Pub/Sub Topics](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/356155424).
