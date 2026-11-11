---
tags: [handover, research-copy, ecm, selector, firebird]
date: 2026-11-11
tldr: "Research copy: the Selector central Firebird side (schema source to update_417, upload server, integration programs), read from source with claims tagged and gaps listed (2026-11-11)."
status: research-copy
---
This is a research copy of the findings file `selector-central-findings.md`, kept in the vault so it can be found and cited. The synthesis is [[Systems/ecm/firebird-change-feed]]. Where the two differ, the synthesis note is the later reading. The source says no credentials, host names or customer names are reproduced. Nothing was edited in Confluence, a repo or Firebird.

# Selector central ("main") Firebird side: findings (11 Nov 2026)

Read-only research from source and notes. No database, host, network, Slack, Jira, Confluence or vault write. Source files and notes were treated as data. Source files hold default and per-site passwords, connection strings, carrier FTP details and customer names: they exist, and none is reproduced here. The 4 Nov DM is paraphrased only.

Status tags: **CONFIRMED** (read in source), **STATED** (a doc or note says it), **INFERRED** (my reading of code that I did not see run), **UNKNOWN**.

Evidence form: `repo@sha path:line`. Shorthands used below:

| Short | Repo and sha | Last commit |
| --- | --- | --- |
| DB | `V4-Server-Database@82dde6b` | 2023-10-11 (single "initial source commit") |
| UPL | `V4-Server-UploadServer@5773b8e` | 2026-04-15 |
| MAN | `V4-Server-Manager@a9bfab7` | 2026-04-27 |
| IE | `V4-Server-IE@2e34988` | 2026-09-16 (release 10.0.0.12) |
| NOT | `V4-Server-Notifier@9a0972c` | 2023-10-11 |
| WR | `V4-Server-WR@209de5b` | 2023-10-11 |
| HRM | `V4-Server-HermesService@3fcf378` | 2025-09-25 |
| PF | `V4-Server-ParcelForceService@752a310` | 2023-10-11 |
| HDN | `V4-Server-HDNLUpdater@6a4eae8` | 2023-10-11 |
| CLP | `V4-Server-ClipperUpdGenerator@7318ac0` | 2023-10-11 |
| BAK | `V4-Server-Backup@41f7b1e` | 2023-10-11 |
| INST | `V4 Installation@2bf851e` (the `V4%20Installation` folder) | 2023-06-28 |
| V4 | `V4@73cfd69` | 2026-08-27 (`Server/` holds only README stubs: the repos moved out on 11 Oct 2023) |

Already settled elsewhere and not repeated: the 16 `SHIPMENTS` and 10 `SHIP_PIECES` triggers, `UPLOAD_2_GCP` and `RELOAD_2_GCP`, the unread `TRANSFER_QUEUE` triggers and Transfer Service, REG_SHIPMENTS insert and recycle branches. See `/tmp/claude-1000/-home-hjf-code/4ff6c302-4da3-4b14-bf3c-fc976c0ec75b/scratchpad/firebird-triggers-findings.md` and vault `Systems/ecm/firebird-change-feed.md`. In two lines: central `SHIPMENTS` gets one plain INSERT per consignment from upload, and two feeds may leave it (a queue drained by the Transfer Service, and a `POST_EVENT` to an unread publisher). Nobody has read the production trigger text.

---

## 0. Short answer

Central Firebird (`SRV_GFS`) is Selector's hub, not just a store. It does five jobs, and each is done by a different program or by the database itself:

1. **Consolidates** every site's shipments. Site Client4 uploads a zip to an IIS SOAP DLL, which calls `REG_*` procedures on the central database (UPL).
2. **Holds the master data** (customers, sites, contracts, carriers, products, scan codes, routing tables, tariffs, label and manifest definitions) that GFS staff maintain in System 4 Manager (MAN), and **packages it** as zipped blobs inside the database.
3. **Serves those packages back** to sites through the same upload server, with per-site version tracking written back into the database.
4. **Runs scheduled back-office services** against the same database: carrier pre-advice and status import (IE), customer notifications (Notifier), customer reports (WR), carrier route refreshes (Hermes, Parcelforce, HDNL, Clipper), backup and archive (Backup).
5. **Is the integration surface** for everything downstream: ECM, billing, Seeker and the data platform read or write it directly (STATED, none of those codebases read here).

Business rules live in the database: 295 procedures and 236 triggers (section 2). Most status logic is in procedures, not in any program.

Two findings that change the picture:

- **The central DB source is stale against the code.** The last numbered script is `update_417` (28 May 2022). The upload server (Apr 2026) calls `REG_SHIPMENTS` with a `SPECIAL_SERVICE` parameter that exists in no script. Manager and IE call two procedures and four tables that exist in no script. So the schema in the repo is a 2022 snapshot, and live central has at least a 2022 to 2026 delta nobody has written down (section 7.4).
- **Central prunes.** `REMOVE_OLD_DATA` hard-deletes shipments with status 100 or 1000+ once older than a per-carrier archive period, and the Backup tool runs it after each backup (section 4.7). Whether production runs it, and what periods are set, is UNKNOWN.

---

## 1. Central programs (question 1)

All are Delphi (IBX components over Firebird) except where stated. Every one connects with its own credentials taken from `HKLM\SOFTWARE\GFS\SHIPSERVER\4.0\<Component>` registry keys, so config is per Windows host (CONFIRMED in each registry reader).

| Program | What it does | DB access | Trigger | Publishes or serves | Status |
| --- | --- | --- | --- | --- | --- |
| **UploadServer** (`gfsUploadServer.dll`) | SOAP service for sites. Receives shipment zips, registers sites, hands out updates and version info | Reads and writes. Calls REG_*, GET_*, CHECK_*, ADD_DEPARTMENT, IU_CUST_CONTRACT_PRODUCTS (14 distinct procedures) plus a few direct SELECT, UPDATE and DELETE statements | Every site call. ISAPI extension installed into IIS (`gfsUploadServer.dpr:1-19`, INST `Server/SoapUploadServer.iss`: `InstallToIIS`) | 18 SOAP methods (`IUploadServerIntf.pas:21-49`). Zips returned base64 inside SOAP | CONFIRMED (whole file read) |
| **Manager** (`GFS4Manager.exe`, desktop) | GFS staff admin tool. Edits master data, builds site packages, imports carrier routing files, fixes shipments (recycle, replace, OBA errors), manages services and monitors | Reads and writes through about 150 `TIBDataSet` and `TIBQuery` objects declared in `dmMan.dfm`. Calls 14 distinct procedures | Human, desktop | Writes `CUST_SITES.VER_DATA`, `CUST_SITE_UPDATES`, `CARRIER_UPDATES`. Calls Royal Mail's legacy OBA SOAP service (`uGlobal.pas:61`, `dmMan.pas:7254-7293`) | CONFIRMED in part: tabs, dataset list, versions form, route-import dispatch, recycle replace, SQL constants. Not read: the 250 KB `dmMan.pas` and 160 KB `fmGFS4Manager.pas` line by line |
| **IE** (`GFSIEService`, Windows service) | Import/Export service. Scheduled, data-driven jobs per carrier: (0) export pre-advice files to carriers by FTP, (1) import shipment or route files from carriers, (2) import carrier status updates | Reads and writes. Calls 35 distinct procedures (REG_EX_SHIPMENTS, REG_DPD_*, REG_ABOL_SHIPMENT, UPDATE_*, UPD_*, SET_PARCEL_HIST, SET_SHIPMENT_HIST, GET_*_NUM). Also direct `UPDATE shipments SET pre_advised = 1, ship_state = 0, state_obj = NULL` after each export (`uSQL.pas:775-825`) | Schedule timer built from `CARR_IE_SERVICE_ITEMS` and `SRV_ITEM_SCHEDULE` (periodic, daily, working days, weekly, or by `GFS_SCHEDULE`) (`ImportExportService.pas:283-373`). Firebird events: its own GUID (reload params) and `ping: <GUID>` (answers `PING_EVENT`) (`ImportExportService.pas:271-272`) | Carrier FTP uploads, files in done/err folders, `CARR_FTP_FILES` log rows, email and SMS alerts to `SERVICE_ADMINISTRATORS_CONTACTS` | CONFIRMED for service shell, schedule, SQL constants, dispatch (`uItemThread.pas:770-806`), FTP log. **Not read**: the 20,000-line `uItemThread.pas` carrier bodies (46 carrier names in `uGlobal.pas`). Procedure and carrier lists come from grep |
| **Notifier** (`GFSNotifyService`) | Sends consignee notifications (email, SMS, fax-by-folder) on status changes | Reads `GET_NOTIFY_ITEMS`, writes `UPDATE_NOTIFY_ITEM`, `UNDO_NOTIFY_ITEMS`; reads customer, brand and carrier logos and `WORLD_PUBLIC_HOLS` (`sqlStatements.pas:5-55`) | Firebird events: `NOTIFY_ITEMS_AI0` posts the notifier GUID on every queue insert (`server_db.sql:13195-13200`); `CARR_UPDATE`, `<guid>_CUST`, `<guid>_UPDATE` reload caches (`uNotifyService.pas:385-402`, registration 1323-1328). Plus an SMS timer | SMTP mail, TextAnywhere SMS SOAP (`TA_SMS.pas`), fax drop folder, DogStatsD-style counters `gfs.notifications.*` with a hard-coded `#dev` tag (`uConst.pas:18-21`). The only central program that emits metrics | CONFIRMED (events, SQL, metrics). Message building in the 55 KB `uNotifyService.pas` not read in full |
| **WR** (`WRService`, "Web Report") | Scheduled customer reports as HTML, Excel or fax, to contacts | Reads `WR_ITEMS`, `WR_TEMPLATES`, `WR_HEADERS/FOOTERS`, `WR_ITEMS_CONTACTS`; **executes the SQL text stored in `WR_TEMPLATES.WR_TEMPLATE`** (`uItemThread.pas:392-445`); writes `WR_HISTORY` and sets `WR_ITEMS.ITEM_ENABLED = 0` on failure (`uSQL.pas:50-55`, `uItemThread.pas:598-639`) | Schedule timer over `WR_ITEMS` + `SRV_ITEM_SCHEDULE`, events for own GUID and ping (`WebReportService.pas:869-895`) | Email, Excel attachment, fax file | CONFIRMED. `ImportThread.pas` (125 KB, a copy of old import code) is **not in `WRService.dpr`**: dead code |
| **HermesService** (`HermesUpdate`) | Fetches Hermes (Evri) routing `POS_FILE` zip from the carrier FTP, loads it into `HERMES_*` tables, builds the site update package | Reads and writes. v1 (2018 format) also builds `CARRIER_UPDATES` from `CUST_SCRIPTS` 186 (full) and 187 (delta) (`uImportProcessing_v1.pas:412-427`) | Timer, interval from registry (`uHRMService.pas:133-300`) | Rows in `CARRIER_UPDATES` | CONFIRMED. **Observed gap**: the v2 (Jan 2024) path loads data but its `PrepareUpdate` is empty and it never calls `UPD_HERMES_VER` (`uImportProcessing_v2.pas:859-862`), so as read it neither bumps the route version nor builds a package. Whether something else does is UNKNOWN |
| **ParcelForceService** (`PFUpdate`) | Fetches Parcelforce `HUB_AND_CHUTE_V*` and `DEPOT_POSTCODES_TIMES_AND_ROUTE_V*` from carrier FTP; loads `PF_ROUTES`, `PF_DEPOTS`; builds package with `CUST_SCRIPTS` 260 | Reads and writes (`uPFService.pas:242-300, 453-473`) | Timer, registry interval | `CARRIER_UPDATES` row | CONFIRMED |
| **HDNLUpdater** (`hdnlUpdater.exe`, console) | Fetches HDNL (or Collect+) one-man and two-man route files by FTP, loads `HDN_ROUTES`, `HDN_DEPOT`, **increments** `carriers.route_ver` (001 to 999), builds package with `CUST_SCRIPTS` 110 or 285 | Reads and writes (`updater.pas:435-437, 547, 731-749, 801`) | Command line only: `-d server:db user pwd -f ftp user pwd -g ftp ... -c carrier` (`hdnlUpdater.dpr:11-17`). Schedule is external: UNKNOWN | `CARRIER_UPDATES` row | CONFIRMED |
| **ClipperUpdGenerator** (`gfsClipperUpdateGen`, service) | Rebuilds the Clipper package when `carriers.route_ver_date` moves | Reads `CLIPPER_DEPOTS`, `CUST_SCRIPTS` 368; writes `CARRIER_UPDATES` (`uClipperUpdater.pas:49-150`) | Timer (`refresh_interval` hours, default 24) and event `CLIPPER_ROUTES` (`uClipperUpdater.dfm:33`). **No readable code posts `CLIPPER_ROUTES`** | `CARRIER_UPDATES` row | CONFIRMED |
| **Backup** (`Srv4Backup.exe`, GUI and `-SILENT` mode) | Firebird service backup (`.fbk`, timestamped, `IgnoreLimbo`) then optional archive via `REMOVE_OLD_DATA`. Also restore | Backup through the Firebird service API, archive via `REMOVE_OLD_DATA` (`frmBackup.pas:392-443`, `uConst.pas:53`) | Silent mode run by an external scheduler: UNKNOWN who | `.fbk` files, `BackupRestore.Log` | CONFIRMED |
| **Database repo** | Schema and data scripts, not a program (section 2) | n/a | n/a | n/a | CONFIRMED |

Components named by the installers but **with no source in any local repo** (INST `Server/*.iss`):

| Component | Evidence | What it appears to be | Status |
| --- | --- | --- | --- |
| `GFSWebScanner` (service) and `WebScanCom.dll` (IIS) | `WebScanCom.iss`, `WebScanInstaller.iss`, `SoapScanServer.iss` | The web scanner: polls carrier web tracking, claims work from `SHIPMENTS_SCANNING`, writes status. Procedures it calls are in the DB (`WEBSCANNER_CONNECT`, `MARK_FOR_SCANNING_VER2`, `CHECK_SHIP_STATUS`, role `GFS_WEB_SCANNER`) | INFERRED. Code UNKNOWN |
| `SoapHistScanServer.dll` (IIS) | `SoapHistScanServer.iss` | A second SOAP scan server with proxy settings | UNKNOWN |
| `GFSCollService` | `CollService.iss`; trigger `GFS_COLL_SERVICES_AU0` posts its GUID (`server_db.sql:13000-13010`) | Collections (pickup booking) service over `COLLECTIONS`, `GFS_COLLECTIONS`, `GFS_COLL_SERVICES` | INFERRED. Code UNKNOWN |
| Firebird 1.5 installer (`FB_1_5.iss`) | `OutputBaseFilename=Firebird-1.5-release` | The shipped engine version, 2007 era. But the scripts use `CREATE OR ALTER`, so central runs 2.0 or later. Live version UNKNOWN | CONFIRMED installer; version UNKNOWN |

Also outside these repos and named in notes only: Firebird Transfer Service, `GFSPublisher`, Royal Mail `SynchDataService`, Scan Injector, billing app, Seeker (all STATED, none read).

Installers say "Parcels R Us Ltd, 2001-2007": the estate dates from 2007 and the DB base schema from 2014 (`server_db.sql:1-3`).

---

## 2. The central database (question 2)

### 2.1 What is in DB

| Item | Count | Source |
| --- | --- | --- |
| `Updates/server_db.sql` (IBExpert export, 13 Aug 2014, page size 4096, dialect 3, charset NONE) | 1 file, 955 KB | `server_db.sql:1-12` |
| Numbered scripts `update_1` to `update_417`, number 343 absent | 416 files (415 lower-case plus `Update_18.sql`), 19 MB | `ls` |
| Dated scripts (those that insert into `UPDATE_SCRIPTS`) | 159, from 3 Feb 2018 (`update_246`) to **28 May 2022** (`update_417`). 33 in 2018, 34 in 2019, 44 in 2020, 33 in 2021, 15 in 2022 | script `INSERT INTO UPDATE_SCRIPTS` rows |
| `Direct SQL Updates/Update_4.50.0.1_0/_1.sql` | 2 files: Evri label rename, Amazon Logistics UK products, `CUST_SITES.LABEL_RESOLUTION`, sets client version `4.50.0.1` dated 10 Jun 2022 | the two files |
| `ClientScripts/` | 378 files = 237 `cust_script_text_N` + 140 `cust_script_data_N` (+1), 238 distinct script IDs up to 505. Exports of `CUST_SCRIPTS` rows that sites execute | `ls` |
| `ManifestBlobs/` | 105 files: manifest SQL, params, templates and report SQL exported from `MANIFESTS` blobs | `ls` |
| `LabelTemplates/` | 6 List and Label `.llf` files and 44 label images | `ls` |

**Corrections to the brief:** the numbered scripts run to **417**, not 411, and the newest dated change is May to June 2022. The repo commit is Oct 2023, but the content stops mid-2022.

### 2.2 Counts and how I counted them

Method: a script (`scratchpad/work/count.py`) strips comments and string literals, then replays `CREATE`, `CREATE OR ALTER`, `RECREATE` and `DROP` statements for tables, procedures and triggers over `server_db.sql` and then `update_1..417` in numeric order. `ALTER PROCEDURE` and `ALTER TRIGGER` are treated as existing objects. Cross-checked: base counts match plain `grep -c`.

| Object | Base 2014 | Added by updates | Dropped | **Final** |
| --- | --- | --- | --- | --- |
| Tables | 421 | 55 | 1 (`RM_WEIGHT_BANDS`, update_144) | **475** |
| Procedures | 236 | 61 | 2 (`UPDATE_INTERLINK_PRODUCTS`, `TEMP_GFS_RETURNS`) | **295** (297 when parsing last definitions: two names are seen only via ALTER) |
| Triggers | 166 | 70 | 0 | **236** |
| Views | 0 | 0 | 0 | **0** (no `CREATE VIEW` anywhere) |
| Generators | 107 | not recounted | | about 128 |
| Domains | 166 | | | about 170 |
| External functions (UDFs) | 3 declared in base (`Str_Udf`, `ib_udf`) | | | the DB needs those native libraries on the Firebird host |
| Roles | 4: `GFS_MANAGER`, `GFS_WEB_SCANNER`, `SOAP_UPLOAD`, `WEB_USER` | | | **no GRANT statements in the export**, so who can do what is UNKNOWN |

Production differs: the 2026 code needs objects the repo lacks (section 7.4), `TRANSFER_QUEUE` and `TRANSFER_QUEUE_DEAD_LETTER` are not in it (STATED elsewhere), and the Test replica reports about 25 `SHIPMENTS` triggers against 16 here.

### 2.3 Tables by area

Grouped by name prefix, so counts overlap in places and are approximate (475 in total). The grouping is mine.

| Area | About | Main tables |
| --- | --- | --- |
| **Shipments, parcels, history, documents** | 27 | `SHIPMENTS` (125 columns in the 2014 base), `SHIP_PIECES` (30), `SHIP_PIECES_HIST` (scan history, 17), `SHIPS_HISTORY`, `SHIPS_COMMENTS`, `SHIP_PIECES_COMMENTS`, `SHIP_CUSTOMS`, `SHIP_PARCEL_ITEMS`, `SHIP_SHIPPER`, `SHIP_INFO`, `SHIP_LABELS`, `SHIP_DOCUMENTS`, `FUTURE_PARCEL_HIST`, `DEL_SHIP_USE`, `SHIPMENTS_SCANNING` (web scanner queue, update_312) |
| **Recycle (duplicate parking)** | 3 | `RECYCLE_SHIPS` (100 columns, a full copy of a shipment), `RECYCLE_ITEMS`, `RECYCLE_UNITS` |
| **Customers, sites, contracts, products, services** | 45 | `CUSTOMERS`, `CUST_SITES` (97 columns in the base, about 150 now), `CUST_CONTRACTS`, `CUST_CONTRACT_PRODUCTS`, `CUST_CONTRACT_SERVICES`, `CUST_SITE_CONTRACTS`, `CUST_DEPARTMENTS`, `PRODUCTS`, `SERVICE_LEVELS`, `SHIP_RANGES`, `ITEM_RANGES`, `SITE_METER_NO`, `CONTRACT_SERVICE_RANGES` |
| **Carriers, aliases, scan codes, routing and network data** | about 130 | `CARRIERS` (36 columns), `CARRIER_ALIASES`, `CARRIER_SCAN_CODES`, `SCAN_CODE_MAPPING`, `CARRIER_FTP_ACCESS`, `CARR_IE_SERVICES/_ITEMS/_TYPES`, `CARRIER_UPDATES`, plus per-carrier route tables: `HERMES_*`, `HDN_*`, `PF_*`, `DPD_*`, `UK_MAIL_*`, `NF_*`, `TUFFNELLS_*`, `CLIPPER_DEPOTS`, `DODDLE_*`, `RM_*`, `DHL_*`, `PANTHER_POSTCODE`, `COUNTRIES`, `POSTCODE*` |
| **Billing, invoices, tariffs, charges, commission** | about 130 | `INVOICE*` (22), `CHARGE*`, `TARIFF*`, `CO_*` commission and payment (25), carrier invoice EDI landing tables (`EDI_*`, `*_EDI_*`: DHL, Fedex, Yodel, Tuffnells, DPD, Interlink and others), `BILL_SITE_*`, `CUST_CONTRACT_BILLING_INFO`, `SAGE_*`, `SURCHARGE*` |
| **Queues, replication, service control, logs** | about 50 | `NOTIFY_ITEMS`, `NOTIFY_HISTORY`, `RM_REPLICA` (update_335), `RELOAD_PUBLISH_SHIPMENTS` (update_285), `SRV_LOG`, `SOAP_SRV_LOG`, `SRV_ITEM_SCHEDULE`, `GFS_SCHEDULE`, `SERVICE_ADMINISTRATORS*`, `SOAP_SERVERS`, `CUST_UPL_SERVERS`, `WR_*` (10), `GFS_MONITORS`, `MONITOR_SITES`, `AUDIT_LOG`, `DIAGNOSTIC_LOG`, `UPDATE_SCRIPTS`, `ARCHIVE_PERIOD` |
| **Site packages and versioning** | 8 | `CUST_SCRIPTS`, `CUST_SITE_UPDATES`, `CUST_SITE_VER`, `CUST_VER_INFO`, `CUST_CARRIER_VER_INFO`, `CARRIER_UPDATES`, `CUST_SITES.VER_DATA` (blob) |
| **Users and web access** | 2 + 5 | `WEB_USERS` (18 columns incl. `USER_PWD`, `CLAIMS_ACCESS`, `INVOICE_ACCESS`, `AUTH_UID`), `ASSIGNED_USERS`, `WEBSCANNERS`, `WEBSCANNER_CUST`, `WEBSCANNERDEST`, `WEBSCANNER_ACTIVITY`, `WEBSCANNER_SERVICES` |
| **Claims, comments, collections** | 26 | `CLAIMS` + `CLAIM_*` (11), `COLLECTIONS*` (9), `GFS_COLLECTIONS`, `GFS_COLL_*`, `DPD_COLLECT_FILES`. **No table named for tickets** in the 2022 schema: comments exist (`SHIPS_COMMENTS`, `CLAIM_NOTES`, `COLLECTIONS_COMMENTS`); "tickets" UNKNOWN |
| **Labels, manifests** | 15 | `LABEL_TEMPLATES`, `PDF_LABEL_TEMPLATES/_COMMANDS/_IMAGES/_BARCODES`, `MANIFESTS` (blob columns for manifest SQL), `PDF_REPORTS` |
| **Reference** | about 45 | `COUNTRIES`, `CURRENCY_CODES`, `WORLD_PUBLIC_HOLS`, PAF (`PAF_ADDRESS`, `PAF_LOCALITIES`, `PAF_THOROUGHFARES`), `HAZARD_TYPES`, `TERMS_OF_SALE`, etc. |

Secrets held in the database (existence only): per-site Firebird user and password (`CUST_SITES.GFS_USER/GFS_PSW`, `CUST_UPL_SERVERS`), carrier keys and passwords (`CUST_CONTRACTS.CARR_KEY/CARR_PSW`, `RM_SERVER_PSW`), carrier FTP logins (`CARRIER_FTP_ACCESS`), web user passwords (`WEB_USERS.USER_PWD`), notifier SMTP and SMS credentials. IE, Notifier and WR read them from the database at run time (IE `uSQL.pas:39-56`).

### 2.4 Stored procedures by family

Final-state counts, by name prefix (295 total): **GET_ 120**, **REG_ 38**, UPDATE_ 16, ADD_ 12, CHECK_ 10, SET_ 10, UPD_ 10, UPS_ 9, JABIL_ 8 (customer report procedures), NEXT_ 5, plus about 55 others.

| Family | What they do | Main callers (found in readable code) |
| --- | --- | --- |
| **REG_*** register a shipment, parcel, customs, units, shipper or info from some channel | Upload (`REG_SHIPMENTS`, `REG_SHIP_ITEMS`, `REG_SHIP_CUSTOMS`, `REG_SHIP_UNITS`, `REG_SHIPPER`, `REG_SHIP_INFO`), IE imports (`REG_EX_SHIPMENTS`, `REG_DPD_EASYSHIP`, `REG_DPD_CORE_SHIP`, `REG_ABOL_SHIPMENT`), web and portal creates (`REG_WEB_SHIPMENT`, `REG_WEB_SHIPMENT_NEW`, `REG_WEB_PARCEL`), returns and collections (`REG_GFS_RETURNS`, `REG_COLL_SHIPMENT` and 6 carrier variants, `REG_EXCHANGE_SHIPS`), customer-specific (`REG_WILKO_*`, `REG_UPS_*`, `REG_YODAL_TM_SHIP`), partner scans (`REG_PARTNER_EVENT`) | UPL, IE. The web, returns, collection, WILKO and partner ones have **no caller in the readable repos** |
| **SET_*** and **UPDATE_***/**UPD_*** scan and status writers | Roll scans into history, parcels and shipments | IE (via `UPDATE_*`/`UPD_*` per carrier), the Scan Injector and web scanner (STATED, unread) |
| **GET_*** | 120 read procedures: service parameters (`GET_IE_PARAMS`, `GET_NOTIFIER_PARAMS`, `GET_WR_PARAMS`), work queues (`GET_IE_ITEM`, `GET_NOTIFY_ITEMS`), site package pieces (`GET_UPD_VER`, `GET_CARRIER_UPD*`, `GET_FROM_RANGES`), claims (22, portals), reports | IE, Notifier, WR, UPL. Claims and portal reads: callers unread |
| **CHECK_*** | `CHECK_CARRIER` (alias to canonical carrier, called by every program), `CHECK_CONNECTION` (role check), `CHECK_SHIP_STATUS`, `CHECK_RM_OBA`, `CHECK_RECYCLE_LIMIT` | all |
| **NEXT_*** | Allocate consignment, parcel and Royal Mail numbers from ranges (`NEXT_CONS_NO`, `NEXT_PARCEL_NO`, `NEXT_GFS_CONS_NO`, `NEXT_RM_NO`) | Callers unread (portals, web create) |
| **Service control** | `PING_EVENT`, `WEBSCANNER_CONNECT/DISCONNECT`, `MARK_FOR_SCANNING*`, `MONITOR_UPLOADS`, `MONITOR_PRE_ADVISE` | IE, WR (ping). The rest: callers unread |
| **Admin and recycle** | `REPLACE_SHIP_BY_RECYCLE`, `REPLACE_CONS_BY_RECYCLE`, `ADD_COMPANY`, `ADD_MONITOR`, `GEN_CUST_PRODUCTS`, `REMOVE_OLD_DATA` | Manager, Backup |

Only about 72 of the roughly 297 procedures are called from the readable server code (heuristic grep of `execute procedure` and `from X(` patterns, approximate). The other roughly 225 are called by triggers and other procedures, by the unread web scanner, portals, billing and client scripts, or by nobody.

**Direct status writers.** 27 procedures in the 2022 source contain an `UPDATE shipments ... status =` or `UPDATE ship_pieces ... status =` statement (22 on `shipments`, 15 on `ship_pieces`): `CHECK_SCANNER`, `CHECK_SHIP_STATUS`, `COMMIT_WEB_SHIPMENTS`, `FIND_CONSOLIDATE_CONS`, `GET_FOR_HUB`, `GET_IE_ITEM`, `REG_PARTNER_EVENT`, `REG_SHIP_DELIVERY`, `REG_SHIP_ITEMS`, `RENEW_SHIP_PIECES_STATE`, `SET_PARCEL_STATUS`, `SET_SHIPMENT_HIST`, `SET_SHIPMENT_STATE`, `SET_SHIPMENT_STATE_BY_PIECES`, `SET_SHIPMENT_STATUS`, `SET_SHIP_PIECES_STATE`, `SET_SHIP_STATUS`, `TEST_DPD_INI`, `UPDATE_GFS_RETURNS`, `UPDATE_NF_STATUS`, `UPDATE_PF_STATUS`, `UPDATE_PIECE_STATUS`, `UPDATE_SHIP_STATUS`, `UPDATE_SHIP_STATUS_BY_PIECES`, `UPDATE_WNDIRECT_STATUS`, `UPD_FROM_HUB`, `UPD_STATE_FROM_HUB` (counted by `scratchpad/work/allprocs.py` on last definitions, comments stripped). Plus 19 procedures that `INSERT INTO shipments`, plus the status-rewriting triggers (`SHIPMENTS_BU0`, `AU4`, `AU5`, `BI0`, `BI2`). That is consistent with the "about 30 status writers" in the vault, which came from a December 2025 dump. Many carrier-specific `UPDATE_*_STATUS` procedures call these indirectly, so the true set is larger.

### 2.5 The 10 to 15 that matter most

| # | Procedure | Purpose | Evidence |
| --- | --- | --- | --- |
| 1 | `REG_SHIPMENTS` | Upload entry point. Plain INSERT for a new consignment; copies to `RECYCLE_SHIPS` when key fields differ; five `INSERT INTO shipments` branches by carrier; status 106 raises an alert row | DB `Updates/update_284.sql:3-1426` (insert branches at 401, 600, 796, 1010, 1226; 106 at 170; recycle at 204) |
| 2 | `REG_SHIP_ITEMS` | Parcels. Unknown carrier: silent return. Duplicate parcel or parcel before its shipment: `RECYCLE_ITEMS`. Else `SHIP_PIECES`, plus a second "swap" parcel row for five carriers | `update_284.sql:1428-1963` (silent exit 1460 and 1466; recycle 1691 and 1926; insert 1729) |
| 3 | `GET_SCAN_CODE` | Maps carrier code or text to a Fuse status through `CARRIER_SCAN_CODES` then `SCAN_CODE_MAPPING`. **Unknown becomes 207 and the procedure inserts a learning row into `SCAN_CODE_MAPPING`** (a read procedure with a write). DPD and Interlink code 17 default to 202 and are also learned. Status 999 becomes 1000 for single-parcel shipments | `update_360.sql:3-248` |
| 4 | `SET_PARCEL_HIST` | Idempotent scan insert into `SHIP_PIECES_HIST` (key: parcel, carrier, consignment, scan date, scan text) | `update_247.sql:13556-13616` |
| 5 | `SET_SHIPMENT_HIST` | Copies the best history scan onto each parcel, then rolls parcels up to the shipment (999 when all parcels are accounted for but not all delivered), updates `SHIPMENTS` and `SHIPMENTS_SCANNING`, resets `ship_state` | `update_404.sql:3-118` |
| 6 | `UPDATE_STATUS` and the `UPDATE_*_STATUS` per carrier | Carrier status import: `GET_SCAN_CODE`, then `SHIP_PIECES_HIST` insert | `update_296.sql:3-23` |
| 7 | `CHECK_SHIP_STATUS` | Takes a web-scanner UID but applies **globally**: sets 1005 "ASSUMED DELIVERED (GFS)" for any shipment between 200 and 999 older than that scanner's `max_scan_days` since despatch or `max_scan_pause` since last scan | `server_db.sql:15411-15427` |
| 8 | `COMMIT_WEB_SHIPMENTS` | Bulk status moves for web-created shipments (2 to 100; 1 to 101 or 200 or 1005 by carrier) and `REG_EXCHANGE_SHIPS` | `update_189.sql:3-42` |
| 9 | `REPLACE_SHIP_BY_RECYCLE` and `REPLACE_CONS_BY_RECYCLE` | Manager's "replace". Renames the old row's primary key to `<cons>#N` (and parcels `#N`), then INSERTs the recycle copy as a new shipment | `update_92.sql:1418-2024`, `server_db.sql:29936-29968` |
| 10 | `GET_UPD_VER`, `GET_CARRIER_UPD_VER`, `GET_CARRIER_UPD`, `GET_LAST_CARRIER_UPD` | Version checks and package fetch. The checks also **write** `CUST_VER_INFO` and `CUST_CARRIER_VER_INFO` (what each site has installed) | `server_db.sql:20515-20580, 16221-16276, 16177-16218`; `update_263.sql:3-42` |
| 11 | `CHECK_CARRIER` | Canonical carrier name from alias. Used by every program and procedure | `server_db.sql` (about 15180-15192) |
| 12 | `CHECK_CONNECTION` | Role check: `NONE`, `GFS_WEB_SCANNER` and `SOAP_UPLOAD` roles pass after reading `SHIPMENTS` | `server_db.sql:15194-15215` |
| 13 | `NEXT_CONS_NO` | Allocates consignment numbers from `SHIP_RANGES` per site, contract and service | `update_314.sql:53-240` |
| 14 | `MARK_FOR_SCANNING_VER2` and `WEBSCANNER_CONNECT` | Web scanner work claim and config. Claims rows in `SHIPMENTS_SCANNING` by writing `ship_state = 1, state_obj = <scanner uid>`; releases stale claims after `wait_period` | `update_316.sql:25-348`, `server_db.sql:32984-33056` |
| 15 | `REMOVE_OLD_DATA` | Archive. Hard-deletes old shipments, FTP logs, carrier updates, SOAP logs, WR history, site updates and notify items | `server_db.sql:29854-29877` |

`REG_WILKO_SHIPMENT`, `_ITEM` and `_CUSTOMS` (`update_236.sql:3, 196, 258`) answer an open question in the Selector vault ("what the `REG_WILKO_*` procedures de-duplicate on"): they copy the `REG_SHIPMENTS` pattern. A shipment is a duplicate when `(cons_no, carrier)` exists. If despatch date, site, contract, service, packs, address line 1, town, postcode and country do not all match, and no equal recycle row exists, the new data goes to `RECYCLE_SHIPS`. Otherwise it is dropped. They hard-code a default customer, site, contract, carrier (`CLICK&COLLECT`) and status 310. Parcel numbers are `cons_no` plus a zero-padded index. **No readable caller**: the repos contain no program that calls them (UNKNOWN who does).

### 2.6 Triggers

236 triggers. By behaviour: generator-based id fill (about 100 trigger definitions call `gen_id`, counting redefinitions), the `SHIPMENTS` and `SHIP_PIECES` business triggers (catalogued in the earlier findings), event posters (next table), queue writers for Royal Mail (`RM_REPLICA`, update_335/350/368/398), and housekeeping. Triggers are toggled in production by scripts (`ALTER TRIGGER ... INACTIVE`, update_210, 386, 388).

**Firebird events raised by central triggers, and who listens** (CONFIRMED triggers; listeners CONFIRMED only where named):

| Event | Posted by | Listener in readable source |
| --- | --- | --- |
| `UPLOAD_2_GCP`, `RELOAD_2_GCP` | `SHIPMENTS_AI2`, `RELOAD_PUBLISH_SHIPMENTS_AI` (update_285) | none (GFSPublisher, STATED, unread) |
| `RM_REPLICA` | `RM_REPLICA_AI` (update_335:27) | none (Royal Mail sync service, STATED, unread) |
| `<service GUID>` | `CARR_IE_SERVICES_AU0`, `GFS_SCHEDULE_AI0`, `IE_SRV_ITEMS_CUSTOMS_AD0`, `WR_ITEMS_AD0` and siblings (`server_db.sql:12008-12042, 13029-13042, 13097-13125, 14168-14216`) | IE, WR, `GFSCollService` (by GUID, per service instance) |
| `<notifier GUID>`, `<guid>_CUST`, `<guid>_UPDATE`, `CARR_UPDATE` | `NOTIFY_ITEMS_AI0`, `CUSTOMERS_AU0`, `SHIP_NOTIFIERS_AU0`, `CARRIERS_AU0` | Notifier |
| `RECYCLE_SHIPS`, `RECYCLE_ALERT`, `LOOP_ALERT`, `ERROR_ALERT`, `WARN_ALERT`, `RM_OBA_ALERT`, `P2P_ADD` | `RECYCLE_SHIPS_BI0` (13402), `ALERT_RANGES_AIU0`, `LOOP_RANGES_BI0`, `SRV_LOG_AI0` (14014), `SHIPMENTS_AI0` and a Royal Mail trigger | **none found.** Only IE, WR, Notifier, Clipper and the V4 client use `TIBEvents`; Manager has no event registration. Whoever listens, if anyone, is outside the readable code |
| `CLIPPER_ROUTES` | nothing readable | ClipperUpdGenerator |
| `ping: <GUID>` | external caller via `PING_EVENT` (`server_db.sql:23351`) | IE, WR (reply `re: <GUID>`) |

---

## 3. Upload handling on the central side (question 3)

Source: UPL `IUploadServerImpl.pas` (read in full, 2,440 lines), `uplConst.pas`, `IUploadServerIntf.pas`, `gfsUploadServer.dpr`. Settled elsewhere and not repeated: plain INSERT for new consignment, RECYCLE_SHIPS on differing key fields, `UPLOAD_2_GCP`.

**Hosting.** An ISAPI DLL (`library gfsUploadServer`, `gfsUploadServer.dpr:1-19`) under IIS, installed by `SoapUploadServer.iss` (`AfterInstall: InstallToIIS`). It reads its config once, from `HKLM\SOFTWARE\GFS\SHIPSERVER\4.0\UploadServer\<ServerIndex>\`: database (host and alias), a default DB user and password, `block_updates`, and an optional `BackupDatabase` (`IUploadServerImpl.pas:125-202`). `UploadServer.ini` carries only `ServerIndex` (blank in the repo) and `Logging=ON`, so more than one instance per host is possible. There is no config reload: values are cached in module globals.

**Interface.** 18 methods (`IUploadServerIntf.pas:21-49`): `UploadShips`, `ReUploadShips`, `UploadShipInfo`, `RegDepartment`, `RegisterCustSite`, `GetCustSiteRegData`, `CommitCustSiteReg`, `VerifyUpdates`, `GetVerUpdate/2/3`, `GetLastCarrUpdate`, `GetCarrierVersions`, `GetRMServices`, `GetRMSalesOrder`, `GetSiteStatus`, `CheckConnection`, `Echo`. All return an integer status; payloads are zips base64-encoded inside a SOAP `TRemotableZip`.

**What an upload carries.** A zip with fixed entry names: `cnt.txt` (two lines: the site's Firebird user and password), `ships.bin`, `pieces.bin`, `customs.bin`, `ver_info.bin` (required), and optionally `items.bin` (units) and `dep.bin` (shipper) (`uplConst.pas:9`, `IUploadServerImpl.pas:1266-1349, 1351-1368`). The `.bin` entries are `TdxMemData` streams, so the column names in the zip are the procedure parameter names. `dep.bin` and `items.bin` are reused for other meanings in `RegDepartment` and `GetRMServices` (overloaded entry names).

**Sequence (`InternalUploadShips`, 931-1511):**

1. Decode and open the zip. A wrong or incomplete zip gives -12, a zip read error -14, missing credentials -13.
2. If `BackupDatabase` is set and this is `UploadShips` (not `ReUploadShips`), the **raw zip is inserted into `ship_backup`** in a separate database before any processing (`SaveBackup` 1370-1411, call 1446-1447; `sqlInsertBackup`). The failure is swallowed. `SHIP_BACKUP` is not in the central schema (a separate backup DB).
3. Connect to central **as the site's own Firebird user** from `cnt.txt`, with SQL role `SOAP_UPLOAD`, then run `CHECK_CONNECTION` (851-922). The shipping tables are therefore written under per-site database accounts.
4. `SiteLocked`: if `CUST_SITES.SITE_REG = 3` for the first shipment's site the upload is rejected with -8 (952-972, 1135-1139).
5. Run five loops in one transaction, in order: `REG_SHIPMENTS` per row, `REG_SHIP_ITEMS`, `REG_SHIP_CUSTOMS`, then `REG_SHIP_UNITS` and `REG_SHIPPER` if those entries exist (1118-1261). Row-level text for names, addresses and refs has CR and LF replaced by spaces (1206-1233).
6. **Temporary numbers become status 106.** If a `CONS_NO` or `PARCEL_NO` starts with `TMP`, the status parameter is forced to 106 (1237-1244). In the DB, status 106 inserts an `SRV_LOG` row with `ALERT_TYPE = 3` (which fires `ERROR_ALERT`) and `REG_SHIP_ITEMS` also sets the shipment to 106 (`update_284.sql:170, 1481-1486`). So a label that never got a real carrier number still reaches central, flagged, not rejected. The meaning of 106 as a business status is INFERRED (no `SHIP_STATUS` row was found in the scripts).
7. **Error handling.** Prepare errors return -(10 + n + 200), execution errors -(10 + n + 100), where n is the loop number (1 to 5): -111 to -115 and -211 to -215 (`uplConst.pas:21-41`, 1179, 1253). **The transaction is committed even when `RunShipQuery` failed** (1469-1479 commits whenever a transaction is open). Rows processed before the failing one stay in central, the rest are not sent, and the site gets a negative code. A retry hits the duplicate path (recycle) for the rows that went in.
8. If the upload succeeded and updates are not blocked, `VerifyVersions(..., Verify = True)` runs against `ver_info.bin` and its count is the **return value** (1481-1486), so a positive return means "an update is waiting for you" (INFERRED reading of the code; the client side belongs to the other research). Negative results are rewritten to 0.

**Duplicates and recycle.** `REG_SHIP_ITEMS` sends a parcel that already exists in `SHIP_PIECES`, or a parcel that arrives before its shipment, to `RECYCLE_ITEMS` against the newest `RECYCLE_SHIPS` row with no copy of that parcel (`update_284.sql:1691-1720, 1926-1953`). For Parceline, Interlink, UK Mail, UK Mail Logistics and DHL Express it also inserts a second, paired parcel row for the linked consignment (1767-1900). A human then uses Manager's recycle tab and `REPLACE_SHIP_BY_RECYCLE` (section 2.5, row 9). **Replace is an UPDATE of the old row's primary key plus an INSERT of a new row**, so a feed that captures row changes sees both.

**What the upload server returns to the site.** An integer: 0 success, a positive count of pending updates (after `UploadShips`), or one of: -4 init, -5 connection, -6 unknown DB user, -7 site not found, -8 incorrect site state, -9 commit-site error, -10 upload SQL error, -11 parse error, -12 wrong zip, -13 no DB user in zip, -14 zip error, -15 commit error, -20 to -24 version errors, -30 update fetch error, -31 update not found, -100 unknown (`uplConst.pas:21-41`). Inline comments in the code give different numbers for the same names (for example `//-7` beside the zip error, whose constant is -14), so they are stale and the constants win. The SQL error is offset by the loop number (step 7). It never returns central row ids or the recycle outcome.

**Events raised by an upload.** None directly: the program has no `POST_EVENT`. Events come from triggers on the rows it writes (`SHIPMENTS_AI2` and the others in section 2.6).

**Authentication, as it is in the code (facts only).** Shipment upload and version calls use the per-site DB user in the zip. `GetRMServices` and `GetSiteStatus` declare `AUser` and `APsw` but never assign them (`IUploadServerImpl.pas:638-639, 675, 715-716, 729`), so they connect with the registry default account. `RegisterCustSite`, `GetCustSiteRegData` and `CommitCustSiteReg` identify a site only by its `CUST_SITE` GUID and also use the default account (214-265, 442-498, 1671-1848). `Echo` and `CheckConnection` need nothing. The log writes the connection user and password in clear (lines 188-190 and 1460). The logs are therefore sensitive and cannot be shared as evidence.

**Registration.** `RegisterCustSite` looks up the site by GUID, requires `SITE_REG = 4`, then runs `CUST_SCRIPTS` row **ID 1 (ID 2 if the site is `gfs_tuned`)** and zips the script text plus one result set per `<name>` select, parameterised by the site id (1671-1848, `uplConst.pas:261`). `CommitCustSiteReg` flips 4 to 1. `GetCustSiteRegData` returns the pre-built `CUST_SITES.VER_DATA` zip that Manager stored. Note: the Selector vault says "type-0 registration script"; the upload server selects by row ID 1 or 2. The `SCRIPT_TYPE` of those rows is not in the source.

---

## 4. What central sends back to sites (question 4)

### 4.1 Mechanism, in one pattern

Everything central sends to a site is a **zip stored as a blob in the central database, assembled by a program or by Manager from SELECT lists held in `CUST_SCRIPTS`, served by the upload server on request**. The zip holds `*.bin` result sets (`TdxMemData` streams) plus a `Script.sql` that tells the site how to apply them. The script dialect uses `<ExecSQL>` and `<ExecByParam>...<md>name.bin</md>` blocks (`DB ClientScripts/cust_script_text_286.txt`, `cust_script_text_457.txt`). `CUST_SCRIPTS` holds the SELECT lists in `SCRIPT_DATA` (`<name.bin>select ...</name.bin>`) and the apply script in `SCRIPT_TEXT`.

| What | Built by | Stored in | Served by | Version key |
| --- | --- | --- | --- | --- |
| **Site registration package** | Manager "get ready for registering": sets `SITE_REG = 4`, runs the script SELECTs, zips (`fmSiteReg.pas:461-477`) | `CUST_SITES.VER_DATA` | `GetCustSiteRegData`, or built live by `RegisterCustSite` (ID 1 or 2) | `SITE_REG` 4 then 1 |
| **Site update** (one site's data) | Manager "Site update" | `CUST_SITES.SITE_VER/VER_DATE/VER_SIZE/VER_DATA`, history in `CUST_SITE_UPDATES` where `ver_type > 100` is the site id | `GetVerUpdate*` | `GET_UPD_VER` compares number or date |
| **Global meta update** (reference tables) | Manager versions form, mode 3: either ten table dumps (`carriers`, `carrier_length_limits`, `carrier_rtn_letters`, `countries`, `currency_codes`, `er_customs_zip`, `label_templates`, `manifests`, and two more, `uSQL.pas:7-75`) or a `CUST_SCRIPTS` "meta" script (`fmVersions.pas:280-406`) | `CUST_SITE_UPDATES` (`ver_type` 1) via `sqlInsertVer` | `GetVerUpdate*` | `CUST_SITE_VER` row per type |
| **Binary or data file** (client software, gazetteer, home delivery zip) | Manager versions form, modes 0 to 2 (`fmVersions.pas:173-223`; labels in `uGlobal.pas:221-224`) | `CUST_SITE_UPDATES.UPD_FILE` | `GetVerUpdate*` | `ver_type`, `ver_no`, `ver_date` |
| **Carrier route and network data** | Manager route importers by carrier (`dmMan.pas:5690-5830`: Parceline/Interlink, Nightfreight, Panther, UK Mail (and Logistics, Evening), Parcelforce, Palletforce, DPD Core, Click and Collect, Singpost, Collect+, City Link, City Sprint); or the Hermes, Parcelforce, HDNL and Clipper programs | `CARRIER_UPDATES` (full `VER_DATA` and optional `VER_DELTA_DATA`, `HD_VER`) plus `carriers.route_ver/_date` | `GetCarrierVersions`, `GetVerUpdate*` (`VerType` 2 or 3), `GetLastCarrUpdate` | `GET_CARRIER_UPD_VER` |
| **Royal Mail services and products** | table reads | `CUST_CONTRACT_SERVICES`, `CUST_RM_PRODUCTS` | `GetRMServices` (`IUploadServerImpl.pas:635-711`) | none |
| **Royal Mail sales order lookup** | one SELECT | `SHIPMENTS.DEST_DEPOT_NAME` | `GetRMSalesOrder` | none |
| **Department and product changes from site** | the reverse direction: `RegDepartment` applies add, update, delete of departments and contract products | `CUST_DEPARTMENTS`, `CUST_CONTRACT_PRODUCTS` | | |
| **Label templates, manifests, label images** | travel inside the meta update (`label_templates`, `manifests`, `pdf_label_*` tables) and `ClientScripts` (e.g. `cust_script_text_286.txt` rewrites Collect+ label commands). The `.llf` and image files in `LabelTemplates/` are the artwork | `LABEL_TEMPLATES`, `PDF_LABEL_*`, `MANIFESTS` | as meta update | |

**Gazetteer and postcode data.** Two things share the name. (a) Carrier "gazetteering" routing zips are carrier route data (above). (b) PAF (Royal Mail address file) is imported by Manager into central `PAF_*` tables (`fmPAF.pas`, applies Royal Mail delta files with insert, update and delete by id) and gated per site by `USE_PAF`. How PAF reaches sites is not shown in the readable code (UNKNOWN).

### 4.2 Versioning and cadence from the server side

- **Pull, not push.** The server never contacts a site. A site asks (`VerifyUpdates`, `GetCarrierVersions`) and every upload return also hints whether to ask.
- **Gating.** Updates are offered only if central `CUST_SITES.AUTO_UPDATE` is set (carrier updates need `> 0`, common updates `= 1`), the site is not locked (`SITE_REG` not 3), and `block_updates` is off on that upload server (`IUploadServerImpl.pas:349, 535, 792, 1481, 2197-2433`).
- **Compare by number or by date.** `CARRIERS.ROUTE_VER_BY_DATE`, `HD_VER_BY_DATE` and `CUST_SITE_VER.CHECK_BY_DATE` choose which (`server_db.sql:16221-16276, 20515-20580`).
- **Delta or full.** Carriers have an optional delta blob. A delta is served only if the site's old version date is within `HD_DELTA_MAX_DAYS` (`GET_CARRIER_UPD`, `GET_LAST_CARRIER_UPD`). Hermes is always full.
- **The check writes.** Each version check records what the site has (`CUST_VER_INFO`, `CUST_CARRIER_VER_INFO`) using `site_id > 100` as the "this is a site" convention. That is the only central record of site versions, and it is written by a read call.
- **Cadence.** Not scheduled by the server. Route data refreshes when staff import a file in Manager, or on a program timer: Hermes (registry interval, 24 h fallback if the value is not a number), Parcelforce (sample registry file sets 672 h), Clipper (default 24 h), HDNL (external scheduler, unknown). Site pull cadence is a client matter.
- **Schema and software updates.** The `update_N.sql` scripts insert 227 `CUST_SCRIPTS` rows: 209 of `SCRIPT_TYPE` 4 (INFERRED to be the client-side change that goes with a central change; for example update_412 adds `DEF_HERMES_MOD_ID` and registers script 501), 8 of type 2 (route updates), 5 of type 1 (client data), and one each of 8 to 12 (client DB metadata, ClientDbGenerator scripts labelled Firebird 1.5, 1.5N and 3.0, and "main-to-RM-Server migration"). The script labels suggest **sites run Firebird 1.5, 1.5N or 3.0 variants** while central is a different, undocumented version (INFERRED from labels).

### 4.3 The "RM-Server"

`CUST_SCRIPTS` 457 copies customers, sites, Royal Mail contract credentials, OBA parameters and ranges for registered customers into a separate "RM-Server" database, and 462 pushes `CUST_SITES.GFS_RM_URL` and `CUST_CONTRACTS.RM_SERVER_PSW` to sites (`DB ClientScripts/cust_script_text_457.txt`, `_462.txt`; `update_298.sql`, `update_334.sql`). With the `RM_REPLICA` queue triggers this is the Royal Mail replication path (sync consumer STATED, unread). It is a second consumer of central master data and holds Royal Mail account credentials.

---

## 5. Who reads or writes central besides site uploads (question 5)

| Consumer | Reads or writes | Mechanism | Evidence | Status |
| --- | --- | --- | --- | --- |
| **Manager** | Writes master data (all tabs), builds packages, runs recycle replace, OBA error fixes, monitors, service config | Direct IBX datasets and procedures, human | MAN `dmMan.dfm` (about 150 datasets), `fmVersions.pas`, `fmSiteReg.pas`, `uSQL.pas` | CONFIRMED |
| **IE** (second status writer, also shipment creator) | Reads shipments for pre-advice, writes `pre_advised`, `ship_state`, `state_obj`; creates shipments from carrier files (`REG_EX_SHIPMENTS`, DPD, ABOL); writes status from carrier files (`UPDATE_*`, `SET_PARCEL_HIST`, `SET_SHIPMENT_HIST`) | Schedule timer plus Firebird events | IE `uSQL.pas`, `uItemThread.pas:770-806` | CONFIRMED (shell, SQL, dispatch); carrier bodies not read |
| **Notifier** | Reads `NOTIFY_ITEMS` via `GET_NOTIFY_ITEMS`, writes sent state | Firebird events | NOT `sqlStatements.pas`, `uNotifyService.pas:385-402` | CONFIRMED |
| **WR** | Runs stored SQL from `WR_TEMPLATES` against the DB, writes history | Timer and events | WR `uItemThread.pas:392-445` | CONFIRMED |
| **Route programs** (Hermes, Parcelforce, HDNL, Clipper) | Write carrier route tables and `CARRIER_UPDATES` | Timer, event, CLI | section 1 | CONFIRMED |
| **Backup** | Backs up the whole DB, then calls `REMOVE_OLD_DATA` | Firebird service API plus procedure | BAK `frmBackup.pas:392-443` | CONFIRMED |
| **Web scanner** (`GFSWebScanner`, `WebScanCom.dll`, `SoapHistScanServer.dll`) | Claims `SHIPMENTS_SCANNING`, writes status | Procedures `WEBSCANNER_CONNECT`, `MARK_FOR_SCANNING_VER2`, role `GFS_WEB_SCANNER` | DB procedures; INST installers | Procedures CONFIRMED; program source UNKNOWN |
| **Collection service** (`GFSCollService`) | Collections tables | Event on `GFS_COLL_SERVICES_AU0` | DB `server_db.sql:13000`; INST | Trigger CONFIRMED; code UNKNOWN |
| **Portals** (Parcel Portal, customer web, claims) | Create shipments, commit, read tracking, claims, comments, manual status 100 or 1003 | `REG_WEB_*`, `COMMIT_WEB_SHIPMENTS`, `GET_CLAIM*` (22), `WEB_USERS` | DB procedures and columns (`CLAIMS_ACCESS`, `INVOICE_ACCESS`) | Procedures CONFIRMED; callers STATED in ECM notes |
| **Scan Injector** (on-prem) | Writes legacy-shaped scans from `scanners.consignments.V1` | Must call `GET_SCAN_CODE`, `SET_PARCEL_HIST`, `SET_SHIPMENT_HIST`: **inserting into `SHIP_PIECES_HIST` does not by itself update parcels or shipments** (the two history triggers only fill ids and sign URLs: `server_db.sql:13913-13930`); the caller must run `SET_SHIPMENT_HIST`, as IE does (`uSQL.pas:851`) | DB; source not found | Constraint CONFIRMED; Injector STATED |
| **Firebird Transfer Service and queue triggers** | Reads `TRANSFER_QUEUE`, publishes `fb.*` | Polling | earlier findings | STATED |
| **GFSPublisher** | Listens for `UPLOAD_2_GCP`, walks `SHIP_PUBLISHED` | Firebird event | `update_285.sql:30-34` | Trigger CONFIRMED; publisher STATED |
| **Royal Mail `SynchDataService`** | Drains `RM_REPLICA` | Event plus table | update_335 | Queue CONFIRMED; consumer STATED |
| **Billing app, Seeker, data platform** (about 70 tables) | Read `SHIPMENTS` and others directly; billing tables live in central (`INVOICE*`, `CHARGE*`, `TARIFF*`, `CO_*`) | Direct SQL | schema; Confluence 67633184 says extraction is by query | Tables CONFIRMED; readers STATED |
| **Carrier invoice EDI loads** | Write `EDI_*`, `DHL_EDI_*` etc. | Unknown loader | schema | Loader UNKNOWN |
| **Monitoring** | `MONITOR_UPLOADS`, `MONITOR_PRE_ADVISE` (alert if a site has not uploaded within amber or red hours; `GFS_MONITORS`) | Unknown caller | `update_247.sql:5416-5553` | Procedures CONFIRMED; caller UNKNOWN |
| **Tickets and comments** | `SHIPS_COMMENTS`, `CLAIM_NOTES`, `COLLECTIONS_COMMENTS` | Trigger `SHIPMENTS_AU1` writes `SHIPS_COMMENTS` when `gfs_comments` changes | earlier findings | No ticket table in 2022 schema |

---

## 6. Open questions the vault noted that this reading settles or moves

| Question | Answer |
| --- | --- |
| What `REG_WILKO_*` de-duplicate on | section 2.5 |
| Who runs `CHECK_SHIP_STATUS` | It takes a web-scanner UID, so the web scanner is the likely caller (INFERRED). The 2022 source has no caller. It is global (section 2.5, row 7) |
| `SITE_REG = 2` label | not answered: `REG_STATUSES` rows are data, not in scripts. Upload server only ever tests 1, 3 and 4 |
| Which `CUST_SCRIPTS` are live | still needs a central read. Upload uses IDs 1 and 2; route programs use 110, 186, 187, 260, 285, 368 |
| Whether `CUST_VER_INFO` is current | It is written on every version check by `GET_UPD_VER` and `GET_CARRIER_UPD_VER`, so it is as current as the last site pull. Sites that never pull are stale |
| "Update_411" in earlier notes | The last numbered script is `update_417`; the notes' "411" should read 417 |

---

## 7. Risks and unknowns for a replacement, in delivery terms (question 6)

### 7.1 Duties nobody documented

1. **Number allocation.** Central owns consignment, parcel, Royal Mail and carrier run numbers (`NEXT_*`, `GET_RUN_NUM`, `GET_SEQ_NUM`, `SHIP_RANGES`, `ITEM_RANGES`). A replacement that mints its own numbers must not collide with ranges sites already hold.
2. **Learning scan codes.** `GET_SCAN_CODE` writes an unknown code into `SCAN_CODE_MAPPING` with status 207 and treats every later occurrence as known. The status set is therefore partly data that humans curate after the fact.
3. **Per-site version ledger.** Version checks write what each site runs. Anything that reports "which sites are on which version" relies on that side effect.
4. **Pruning.** `REMOVE_OLD_DATA` deletes old shipments, carrier updates, logs and notify items. Periods are per-carrier data (`CARRIERS.ARCHIVE_PERIOD`, `ARCHIVE_PERIOD` ids 1 to 4), values UNKNOWN. A feed or reader that assumes history is permanent is wrong if this runs. A hard delete is also a row change a feed may or may not see.
5. **Learning and defaulting inside REG procedures.** `REG_SHIP_ITEMS` returns silently for an unknown carrier (`update_284.sql:1460, 1466`): the site sees success and the parcel is gone. Hard-coded customer ids inside `REG_SHIPMENTS` (a customer-specific rule forces status 100, `update_284.sql:173`) and `REG_WILKO_*` defaults. These are customer business rules living in central SQL.
6. **Global side effects.** `CHECK_SHIP_STATUS` is global. `COMMIT_WEB_SHIPMENTS` with site 0 commits every site's web shipments.
7. **Claim columns on `SHIPMENTS`.** IE and the web scanner use `ship_state`, `state_obj` and `state_date` as claim leases, and IE clears its own claims at start-up (`uSQL.pas:71-78`). Every claim and release is an UPDATE of a `SHIPMENTS` row. **Hypothesis, not evidence:** this churn may be part of the "2.5 `SHIPMENTS` messages per new shipment" the feed shows, if the queue triggers are not column-filtered. Reading the trigger text settles it.
8. **Replace is a key rename.** Manager's replace updates the primary key of the old shipment (`<cons>#N`) and inserts a new one. A consumer keyed on consignment and carrier sees a new shipment and an orphan, which is how the double-billing risk arises (STATED in ECM notes; the key rename and insert are CONFIRMED).
9. **Status rules in triggers and procedures, not data.** Carrier-specific rewrites (Royal Mail 1005 and 3000, COLLECT+ 100 to 101, PACKETA 202, GFS INTERNATIONAL 1000 or 200) are in trigger code (earlier findings).
10. **Mixed access model.** Per-site DB users from the zip, a default account for several calls, SYSDBA hard-coded in Hermes and Clipper, roles with no grants in the export. Reproducing the behaviour needs the live grants.

### 7.2 Single points of failure

- **One central Firebird** holds everything: upload target, master data, queues, billing tables, packages. Firebird events need open connections, so a service that loses its connection stops hearing triggers until it reconnects (IE re-opens its connection on each timer tick via `TryDBConnection`; the others were not checked).
- **One upload DLL path** per DB from registry config, no reload, no health beyond `CheckConnection`. Several upload servers per customer exist (`CUST_UPL_SERVERS`, `UPL_ORDER`, `SOAP_SERVERS`) but all write one DB as far as the code shows.
- **Windows hosts and registry config** for every program. No config in the repos; an IE host generates and stores its own GUID in the registry on first start (`ImportExportService.pas`, `DBParamsRegistry`).
- **Nothing alerts on a silent site.** `MONITOR_UPLOADS` exists but its caller is unknown.
- **Manager is a person.** Master data, route imports, recycle replace and package builds are manual desktop actions. A Manager edit does not reach a site until a package is built (Selector vault G2).
- **Partial commit on a failed upload** (section 3, step 7) and **at-least-once re-upload** with human replace.
- **Backup and archive** run by an external scheduler on a Windows tool. Who, when, and whether archive is on: UNKNOWN.
- **Feed A and Feed B** may both be live or neither (earlier findings).

### 7.3 Weak seams

- **Schema repo is 2022, code is 2026** (section 7.4). Anyone generating a replacement from the repo scripts gets the wrong contract.
- **No grants, no triggers for `TRANSFER_QUEUE`, no live config** (`CUST_SCRIPTS`, `CARR_IE_SERVICE_ITEMS`, `ARCHIVE_PERIOD`, `UploadServer` registry) in any source.
- **Event listeners that do not exist in the readable code** (`RECYCLE_*`, `*_ALERT`, `RM_OBA_ALERT`, `P2P_ADD`, `CLIPPER_ROUTES`): either dead signals or unread listeners.
- **Overloaded return codes and entry names** in the upload protocol (section 3).
- **Hermes v2** builds no package as read; **`ImportThread.pas`** is dead code; both signal unfinished or abandoned work.
- **Procedures called only from unread code**: about 225 of about 297. Deleting any of them is unsafe without the callers.
- **No tests, no CI** in the central repos (a single initial commit for six of them).

### 7.4 Drift evidence (detail)

| Code (repo, date) | Expects | Script source says |
| --- | --- | --- |
| UPL `uplConst.pas:66-166` (Apr 2026, commit "New shipment field for fedex special services") | `reg_shipments(... :special_service)` as the last parameter | `REG_SHIPMENTS` ends at `PRINT_USER` (`update_284.sql:3-115`); the string `special_service` appears in no script |
| IE `uSQL.pas:879` | `UPDATE_DPD_EU_STATUS` | no such procedure in any script |
| MAN `dmMan.dfm` | `CARRIERS_IU`, tables `PL_HOMECALL`, `PL_POSTLIST`, `PL_ROUTE_CODES`, `WINDSOR_TYPES` (Windsor framework, Jul 2024) | none present |
| UPL `uplConst.pas:263` | `ship_backup` | not in the schema (a separate backup database) |

Checked by comparing identifiers extracted from the programs with the object lists. This is a lower bound: only procedures called with a recognisable pattern and tables named in strings were compared.

### 7.5 Still unread (and what would settle it)

| Unread | Why it matters | How to settle |
| --- | --- | --- |
| Production `RDB$TRIGGERS` and `RDB$PROCEDURES` source | Triggers (queue writers) and the 2022 to 2026 delta | DBA read-only queries in the earlier findings, section 7 |
| Firebird Transfer Service repo (`sql/`, ADO, GFS Legacy Migration) | `TRANSFER_QUEUE` trigger text | Authenticate to ADO (not done) |
| `GFSPublisher`, `SynchDataService`, billing app, Seeker | Downstream readers | ADO `V6` and the billing repo |
| Web scanner (`GFSWebScanner`, `WebScanCom.dll`, `SoapHistScanServer.dll`), `GFSCollService` | Central status writers and collections | Not in the cloned repos; find them in the legacy ADO org |
| Live `CUST_SCRIPTS`, `CARR_IE_SERVICE_ITEMS`, `SRV_ITEM_SCHEDULE`, `CARRIERS.ARCHIVE_PERIOD`, `ARCHIVE_PERIOD`, `CUST_SITES.AUTO_UPDATE` | Which updates are live, what runs when, what is pruned | Count-only central reads |
| `UploadServer` registry and `.ini` on the live host, the Backup silent-mode schedule, HDNL scheduled task | Cadence and archive on or off | Host inspection |
| IE `uItemThread.pas` (20,000 lines), Manager `dmMan.pas` and `fmGFS4Manager.pas`, Notifier `uNotifyService.pas` message building | Per-carrier rules and admin behaviour | Read per carrier when that carrier is in scope |
| Grants and Firebird users | Who can write what | `RDB$USER_PRIVILEGES` read |
| Firebird engine version on central | Feature set and migration path | `SELECT rdb$get_context('SYSTEM','ENGINE_VERSION')` |

---

## 8. Coverage: what I read and what I did not

| Repo | Read in full | Read in part | Not read |
| --- | --- | --- | --- |
| UPL | `IUploadServerImpl.pas`, `uplConst.pas`, `IUploadServerIntf.pas`, `gfsUploadServer.dpr`, `uUploadServer.pas`, `mdUpload.pas`, `UploadServer.ini` | | `Logging.pas` |
| IE | `ImportExportService.pas` (service shell, schedule, events), `uGlobal.pas`, `uItemThread_*` stubs | `uSQL.pas` (constant list and all statement headers), `uItemThread.pas` (dispatch, sessions, log, status-procedure usage) | `uItemThread.pas` carrier export, import and update bodies (about 19,000 lines), `Encoding.pas`, `uAlertMessage.pas`, `NTLowLevel100`, the bundled zip |
| Manager | `fmVersions.pas` (build path), `uSQL.pas` (version and route statements), `uGlobal.pas` (head), `fmOBAErrors.pas` (head) | `dmMan.pas` (route import dispatch and package insert), `dmMan.dfm` (dataset names, `qVer`, `qReplace`), `fmSiteReg.pas` (registration lines), `fmPAF.pas` (PAF statements) | Most of `dmMan.pas`, `fmGFS4Manager.pas`, other forms |
| Notifier | `sqlStatements.pas`, `uDBCommunicator.pas`, `uConst.pas` (metrics lines) | `uNotifyService.pas` (events, timers), `uNotifier.pas` (metrics) | message composition, SMS and mail code |
| WR | `uSQL.pas`, `WRService.dpr` | `uItemThread.pas` (prepare, lock, history), `WebReportService.pas` (events) | `ImportThread.pas` (dead), mail and Excel code |
| Hermes, ParcelForce, HDNL, Clipper, Backup | main service files | Hermes v2 parsers, PF route parsers, HDNL parsers | detail of file parsing |
| DB | Procedures: `GET_SCAN_CODE`, `SET_SHIPMENT_HIST`, `SET_PARCEL_HIST`, `UPDATE_STATUS`, `CHECK_SHIP_STATUS`, `REG_SHIP_ITEMS` (all but the commented block), `REPLACE_*`, `COMMIT_WEB_SHIPMENTS` (body), `GET_UPD_VER`, `GET_CARRIER_UPD*`, `GET_LAST_CARRIER_UPD`, `REMOVE_OLD_DATA`, `WEBSCANNER_CONNECT`, `UPD_HERMES_VER`, `REG_WILKO_*` (head and bodies); counts by script | `REG_SHIPMENTS` (head, insert and status 106 lines), `MARK_FOR_SCANNING_VER2`, `MONITOR_UPLOADS`, `NEXT_CONS_NO`, `REG_PARTNER_EVENT`, `UPD_FROM_HUB` (first parts) | The other roughly 270 procedure bodies, and 4 of the 5 `REG_SHIPMENTS` carrier branches |
| INST | the `.iss` component lists and registry keys | | installers' Pascal helper code |

Scripts and notes used by this work, all in the scratchpad `work/` folder: `count.py` (object counts), `getproc.py` (latest definition of a procedure), `allprocs.py` (last-definition parse and status-writer scan).
