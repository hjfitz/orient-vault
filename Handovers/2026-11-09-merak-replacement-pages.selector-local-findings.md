---
tags: [handover, research-copy, ecm, selector, firebird]
date: 2026-11-11
tldr: "Research copy: the Selector site side (Client4, CSS, the site database), read from source at the clone shas, with claims tagged and corrections to earlier vault notes (2026-11-11)."
status: research-copy
---
This is a research copy of the findings file `selector-local-findings.md`, kept in the vault so it can be found and cited. The synthesis is [[Systems/selector/overview]]. Where the two differ, the synthesis note is the later reading. The source says no credentials, host names or customer names are reproduced. Nothing was edited in Confluence, a repo or Firebird.

# Selector local (site) side: findings

Read-only research, 11 Nov 2026. No database, network, Slack, Jira, Confluence or token use. Source files hold default passwords, connection strings and customer names. None are reproduced here. Where a secret exists it is named as "exists" only. The Selector team member's direct message is paraphrased.

Status tags: **CONFIRMED** (read in source), **STATED** (a doc, note or the brief says it, source not read), **INFERRED** (my reading of source, not proved), **UNKNOWN**.
Evidence format: `repo@sha path:line`. Line numbers for `cust_script_text_411.txt` point at the last (body) definition of the named object.

## 0. Sources and how much was read

| Repo | sha (date) | Used for |
| --- | --- | --- |
| V4 (Client4) | 73cfd69 (2026-08-27) | the site app, upload client, update apply, status timers |
| V4-Server-Database | 82dde6b (2023-10-11) | `ClientScripts/` (site DDL, procedures, triggers, update packages) |
| V4-Server-UploadServer | 5773b8e (2026-04-15) | what the site talks to, read only to say what the client gets back |
| CSS | 414569b (2026-10-20) | the live SOAP service on hosted VMs |
| CSS-Enterprise | 3650bfb (2025-08-29) | refactor line of CSS |
| V4%20Installation | 2bf851e (2023-06-28) | Inno Setup installers for the client side |
| V4-Server-HDNLUpdater, V4-Server-ClipperUpdGenerator | 6a4eae8, 7318ac0 (2023-10-11) | producers of carrier route updates (skimmed) |
| V4-Server-Manager | a9bfab7 (2026-04-27) | not re-read; existing vault note relied on |

What I read in full: `V4/Client/Client.Alpha/uSoapUpload.pas` (1,990 lines), `dmClient.pas` lines 1955-2130, 3132-3640, 3845-4100 and 5430-5475, `uUpd.pas` (updater) first 200 lines, `cust_script_text_411.txt` triggers (all 44) and about 25 of its 114 procedures (the upload, update, lock, licence, numbering and routing families), `cust_script_text_0.txt` and `_1.txt`, UploadServer `InternalUploadShips`, `VerifyUpdates`, `VerifyVersions`, `GetVerUpdate2/3`, `GetSiteStatus`, `CommitCustSiteReg`.
What I only sampled: `fmMain.pas` (9.6k lines: timers, startup, unlock-station, export), `uFunc.pas` (33.8k lines: status writes, print, a Clipper label string), `sqlStatements.pas` (upload and update SQL), the CSS service (its commit and upload methods, `CheckUpdates`). Everything else in those files is unread.
The 238 `cust_script_text_N.txt` update scripts were categorised by title and tag counts, and about ten were read. They are not individually reviewed.
Not in any repo and not verified: IB Manager (EMS), Ghostscript as a site install, the Zebra driver, the live `CUST_SCRIPTS` rows, `UploadServer.ini`, production `Web.config`.

## 1. Short answer

A site is a Firebird database (`GFS.FDB`) with one or more Windows programs working on it. **Client4** is the desktop program: it books, validates, prints, commits, imports files, and on exactly one PC per site (the upload station) it is also the only thing that talks to GFS. **CSS** is a SOAP service on hosted VMs that books against the same database but never contacts GFS: its upload methods only post a Firebird event for Client4 to catch.
The site database is both a data store and an application: 189 tables, 114 stored procedures and 44 triggers in the newest full-create script. About 120 of the tables are reference data copied down from GFS (carriers, postcode routing, label templates, manifest definitions). The procedures own the commit/upload status machine, the update state machine, consignment number allocation, routing lookups and the licence lock. The same database also stores the binaries (`Client4.exe`, `updUtil.exe`, `BackupApp`) that the other station PCs unpack.

## 2. Local to central, two lines

Client4 on the upload station wakes on the Firebird event `SHIP_COMMITED`, marks committed shipments (status 3/4) as 8/9 with a batch flag, and sends six tables as a base64 ZIP of binary datasets inside a Delphi RPC SOAP call over HTTP(S) to the first working host in `CUST_UPL_SERVERS`.
The server inserts row by row by stored procedure (idempotent per consignment and carrier), commits even a partial batch, and returns an integer. A negative result puts the batch back to 3/4 and it is re-sent on the next trigger, login or manual upload.

## 3. Central to local, two lines

The site polls: after every upload that reports pending versions, on a schedule, at login and manually, it asks for versions, flags what is newer (`upd_found = 1`), downloads each package into a blob column (2, then 3), and the upload station applies all downloaded packages in one transaction under a site lock (4, then 0 or back to 3).
Package kinds are `ver_type` 1 (meta scripts), 2 and 3 (carrier routes, standard and HD), 4 to 100 (binaries), below 0 (site updates) and above 100 (the site's own id: registration and site-update script). Hermes and Clipper routes use separate daily pulls.

## 4. Q1: the local stack

| Program | Where | What it does | Starts | Uses local Firebird | Talks to central |
| --- | --- | --- | --- | --- | --- |
| **Client4** (`GFSClient4`, `Client4.exe`) | every site PC; hosted VMs too | screens, import-folder watcher, label booking and printing, commit, manifest, day end, and (upload station only) all GFS traffic | user launches it; timers start inside it once a user is logged in | direct `gfsDB` connection (Firebird client library), events via IBX `TIBEvents` | yes, via `uSoapUpload` (section 7) |
| **updUtil.exe** | next to Client4 | waits on Client4's mutex to exit, unpacks new exes from `cust_site_ver.upd_file`, restarts Client4 | launched by Client4 after an update ("NeedClose") | direct, reads registry for path and station | no |
| **BackupApp** (C#) | site, installed with a scheduled task (`at` or `schtasks`) | Firebird backup and restore to `.fbk` (`FbBackup`/`FbRestore`) | scheduler or manual | yes | no upload code seen (partly read) |
| **CSS** (`vzClientSoapServer`, ASMX under IIS) | hosted VMs only | validates, numbers, labels, commits for WMS and API callers | IIS, request-driven | opens the DB per request (`GFSConn`) | **none** (section 6) |
| Firebird server | site (or one PC of a multi-station site) | the database | Windows service from the installer | n/a | no |
| CSS helpers: `PrintingModule.exe`, `PrintPDFLib`, `ThermalLabelPrintHelper`, `FileConverter` (Ghostscript PDF to PNG), `ClientServerProxy` (client library that calls CSS, URL from registry) | hosted VMs | printing and image conversion for CSS | called by CSS | no | no |
| IB Manager (EMS), Ghostscript, Zebra driver | site | admin tool, PDF conversion, thermal printer driver | n/a | n/a | n/a |

- **CONFIRMED** (CSS has no GFS client): grep for upload-server client symbols (`GFS_HOST`, `IUploadServer`, `GetVerUpdate`, `VerifyUpdates`) finds none in CSS source. `CSS/vzClientSoapServer/ClientShipService.asmx.cs:5825` `CheckUpdates` only reads `check_ver_status(2)` and, if asked, fires event `UPD_FOUND`. There is no timer or worker thread in CSS except the log queue (`Logging/AsyncLogProcessor.cs`) and no `Global.asax`.
- **CONFIRMED** (Client4 does not call CSS): no `ClientShipService`, `vzCSS` or `CSSURL` reference in `V4/Client/Client.Alpha/*.pas`. The two apps are independent callers of one database.
- **CONFIRMED** (print path): thermal labels go as raw printer data through the Windows spooler (`V4@73cfd69 Client.Alpha/uFunc.pas:27019-27058`, `OpenPrinter`/`StartDocPrinter`/`WritePrinter`). PDF labels open in an external viewer whose path is `CUST_SITES.FOXIT_PATH` (`uFunc.pas:27327`). CSS can print through `PrintPDFLib` when the request names a printer (STATED, `Systems/selector/architecture.md`).
- **CONFIRMED** (installers): `V4%20Installation@2bf851e Client/Install_30/ClientCompliteInstallerFB30.iss` installs Firebird 3.0 (compact), restores a `gfs.fbk` through `gbak` to create the site database and an admin database, installs `Client4.exe`, `updUtil.exe`, SSL libraries, `thrfare.dat`, BackupApp, and registers a backup task. It can download newer component zips by reading a `version.ini` from a URL named in `setup.ini` (key `website/url`). A separate set (`Install/`) still has Firebird 1.5 compact. CSS has its own installer (`CSS/Info_installer/readme.txt`) that installs Firebird 1.5.6, restores `GFS.fbk` and installs CSS into IIS. `gfs.fbk` is not in any repo.
- **CONFIRMED** (site configuration lives in registry plus database): Client4 and `updUtil` read the database path, an encrypted SYSDBA password and the station number from `HKLM\Software\GFS\ShipClient\4.0\Client` (`uUpd.pas:19-20, 144-165`; `uSoapUpload.pas:1138-1165`). The encryption key is a fixed string in source. Not reproduced.
- **Hosted versus standalone:** CONFIRMED that no code branches on it. The model is recorded only in free-text `CUST_SITES.CUST_URL` (vault: STATED). Hosted VM: CSS plus Client4 on one VM and one `GFS.FDB`. Standalone: Client4 only (CSS installer exists, so a standalone CSS is possible). Both are STATED by the brief and the vault, not seen in code.
- **Not site software:** Manager, UploadServer, IE, Notifier, WR, HermesService, ParcelForceService, HDNLUpdater, ClipperUpdGenerator and the central Backup are central tools (STATED by the `V4%20Installation/Server` installer names; the one I read, UploadServer, is central).

## 5. Q2: the local database

### 5.1 What it holds (189 tables in `cust_script_text_411.txt:2453-5139`)

| Area | Tables (examples) | Notes |
| --- | --- | --- |
| Shipments and parcels | `SHIPMENTS` (136 columns), `SHIP_PIECES` (86), `SHIP_PARCEL_ITEMS`, `SHIP_CUSTOMS`, `SHIP_SHIPPER`, `SHIP_INTER`, `SHIP_LICENSES`, `SHIP_DANGEROUS`, `SHIP_PACKAGES`, `SHIP_COMM_TYPE`, `SHIP_STATUS` | key is (`CONS_NO`, `CARRIER`) |
| Labels and documents | `SHIP_LABELS` (label blob per parcel), `SHIP_DOCUMENTS`, `LABEL_TEMPLATES`, `PDF_LABEL_TEMPLATES/COMMANDS/BARCODES/IMAGES`, `PDF_REPORTS`, `LABEL_PRINTERS`, `LABEL_TYPES`, `LABEL_STOCK_TYPES` | templates arrive from central |
| Manifests | `MANIFESTS` (template, SQL and params per carrier), `MANIFEST_TYPES` | definitions come down; generated output is not stored as a table I saw |
| Customer, contracts, services | `CUSTOMERS` (4 columns), `CUST_SITES` (151), `CUST_CONTRACTS`, `CUST_SITE_CONTRACTS`, `CUST_CONTRACT_SERVICES/PRODUCTS`, `CONTRACT_SERVICE_RANGES`, `THIRD_PARTY_ACCOUNTS`, `CUST_DEPARTMENTS`, `CUST_SENDERS`, `CUST_ROUTES` | package or off-package SQL |
| Number ranges | `SHIP_RANGES`, `ITEM_RANGES`, plus Royal Mail and Hermes number tables | carved out centrally, consumed locally |
| Carriers and credentials | `CARRIERS` (route versions, update flags, route script blobs), `CUST_CONTRACTS.CARR_KEY/CARR_PSW`, `CUST_UPL_SERVERS.GFS_USER/GFS_PSW`, `GFS_USERS` (CSS API users), carrier surcharges, aliases, country and DHL/DPD feature tables | secrets exist in these columns. Not copied |
| Postcode and depot routing ("gazetteer") | `DPD_POSTLIST`, `DPD_ZONES`, `ANC_DEPOT`, `HDN_ROUTES`/`HDN_DEPOT`, `CC_ROUTING`/`CC_DEPOTS`, `UK_MAIL_*`, `HERMES_ROUTES/DEPOTS`, `TUFFNELLS_ROUTES`, `PF_ROUTES`, `PANTHER_POSTCODE`, `NF_POSTCODE`, `NORDIC_ROUTES`, `CITY_SPRINT_ROUTES`, `CLIPPER_DEPOTS`, `RM_SORT_CODES`, plus `PAF_*` address tables | the "local gaz" data |
| Station and UI set-up | `CUST_SITE_STATIONS` (about 90 columns: folders, printers, defaults, auto-print), `SITE_STATION_*`, `IMPORT_MAP`, `IMP_MAP_FIELDS`, `STATION_BIN_VER`, `STATION_DEF_SERVICES` | one row per PC |
| Address book and goods | `ADDRESS_BOOK`, `AB_GROUP(S)`, `GOODS`, `HOLD_ADDRESS` | local only |
| Update state | `CUST_SITE_VER`, `CUST_SITE_UPDATES`, `CARRIER_UPLOAD_SCHEDULE`, `CARRIERS.UPD_*` | section 8.3 |
| Queues | `CUST_DEP_CHANGES` (department changes waiting for registration), `CARR_DISPATCH` (collection bookings), `CA_SCHEDULE/CA_SETTINGS` (ChannelAdvisor) | |
| History and logs | none in the database. Client4 writes files (carrier log per carrier per day, `C:\temp\hermes_update.log`) | `uCarrierLogger.pas:1-15`, `uSoapUpload.pas:94-108` |

Site-only tables not in any central create script I scanned: 32 (for example `CUST_SITE_STATIONS`, `GFS_USERS`, `CUST_ROUTES`, `CUST_DEP_CHANGES`, `STATION_*`, `LABEL_PRINTERS`, `ADDRESS_BOOK` group tables, `SHIP_INTER`, `SHIP_LICENSES`). 157 of 189 share a name with a central table (CONFIRMED by script scan: central 421 tables in `server_db.sql`, 465 including later `CREATE TABLE` in updates).
The full-create scripts are `cust_script_text_382.txt` (340 KB), `410` (351 KB, 193 tables) and `411` (345 KB, 189 tables; drops `CARRIER_POSTCODE_EXCEPT`, `CUST_SITE_DOMESTIC_COUNTRY`, `LANG_NAMES`, `TMP_RM_COUNTRY`). They are templates with `{0}` to `{5}` placeholders for connection, so they build a new site database (the "new-DB generator"). `cust_script_text_409.txt` is an in-place migration to the 150-character address domains.

### 5.2 How the site and central schemas differ for the same name (base scripts only)

Counts are `CREATE TABLE` in site 411 versus `V4-Server-Database/Updates/server_db.sql` (2014 base, later `ALTER`s not applied, so central figures are floors).

| Table | Site columns | Central base columns | Reading |
| --- | --- | --- | --- |
| `SHIPMENTS` | 136 | 125 | site-only: `STATION_ID`, `UPL_STATION`, `UPLOAD_FLAG`, `LABEL_TYPE/ORIENT_TYPE/STOCK_TYPE`, `RESIDENTIAL`, `URBAN_CODE`, `TIN_*`, `HOLD_AT_LOCATION`, `CA_*`, `LINK_SERVICE/LABEL/METER_NO/CONTRACT`, `CHANNEL_IDENT`, `PRINT_USER`, `LABEL_PRINTER`. Central-only: `SHIP_STATE/STATE_DATE/STATE_OBJ`, `CUSTOMER_ID`, `SCAN_DEPOT_NAME`, `SCH_DEL_DATE`, `INVOICE_NUMBER`, `DAYS_LATE`, `SLA_CS`, `SIGN_URL`, `SHIP_LABELS`, the four charge columns, `SHIP_DIR` |
| `SHIP_PIECES` | 86 | 30 | the site row carries far more per-parcel label and carrier detail |
| `CUST_SITES` | 151 | 97 | site holds all per-site carrier URLs, timers and options |
| `CUSTOMERS` | 4 | 30 | site keeps id, guid, company, registered flag only |
| `CUST_CONTRACTS` | 14 | 27 | |

- The upload query sends **96 of the 136** site `SHIPMENTS` columns (`sqlShipUpload0`, `V4@73cfd69 sqlStatements.pas:1247`; I diffed the lists). Not sent: all label-format, station, residential, TIN, hold-at-location, ChannelAdvisor and link-service columns, `ACCOUNT_NO`, `INVOICE_NO`, `MANIFEST_DATE`, `RECEIVE_DATE`, `INSERT_DATE`, `UPL_STATION`, `UPLOAD_FLAG`.
- **CONFIRMED:** the site `SHIPMENTS` has `SCAN_*`, `SIGN_BY`, `SIGNATURE`, `GFS_COMMENTS` columns, and no Client4 source reads them (grep, no hits). Nothing flows back from central into these. `SCAN_TEXT` is reused as the local validation message.
- **CONFIRMED:** label blobs (`SHIP_LABELS`) and `SHIP_DOCUMENTS` are not in any of the six upload queries. Labels never leave the site.

### 5.3 Local status values and what sets them

Source: `uFunc.pas:3831-3886, 9716, 10262-10276`, `fmMain.pas:4312, 8977`, `sqlStatements.pas:1196-1232, 1264-1305`, procedures in `cust_script_text_411.txt:10918-10946, 11161, 11054`.

| Status | Meaning | Set by |
| --- | --- | --- |
| -1 | imported or entered, failed validation (`SCAN_TEXT` holds the reason) | validation in `uFunc.pas` |
| 0 | validated, not yet printed (import tab) | import and validation |
| 1 | label printed (`PRINTED_DATE`, `PRINT_USER` set); commit-eligible once `despatch_date <= NOW` | print |
| 2 | set in `fmMain.pas:8977` after a print-export step, no warnings. Commit-eligible at once | Client4 UI. Exact user meaning UNKNOWN |
| 3, 4 | committed (manifested, `MANIFEST_DATE` set). 3 = from 1, 4 = from 2 | `status = status + 2` in commit (`sqlCommitAll`, CSS commit methods) |
| 8, 9 | marked for upload: `SEND_DATE`, `UPL_STATION`, `UPLOAD_FLAG` set (+5) | `SHIP_UPLOADING2` |
| 10, 11 | uploaded by SOAP (+2) | `SHIP_UPLOADED2(station, 0, flag)`, which also posts `SHIP_UPLOADED` |
| 12, 13 | uploaded to a `.gup` file for manual transfer (+2 +2) | `SHIP_UPLOADED2(station, 2, flag)` |
| 100 | deleted (excluded from manifests) | not traced to a writer in Client4; STATED by the sibling research for central. Local writer UNKNOWN |
| above 100 | carrier events (parcel status copied from `SHIPMENTS_AU0` for 3 to 101) | trigger only; nothing local sets it that I found |

Failure or crash undoes the +5: `UNDO_UPLOADING2` (status 8/9 back to 3/4, clear `UPL_STATION`, `UPLOAD_FLAG`, `SEND_DATE`) on a negative result, and `UNDO_SESSION` at every login (`fmLogin.pas:393, 406`) for batches stuck by a crash. The upload server sets central status 106 for consignment numbers beginning `TMP` (`UploadServer IUploadServerImpl.pas:1243-1244`; `NEXT_GFS_CONS_NO` generates `'TMP' || n`, `cust_script_text_411.txt:10265`).
Registration states in `CUST_SITES.SITE_REG` (0, 1, 3, 4) and the licence lock are in section 8.4.

### 5.4 Triggers: all 44 in the site full-create script (`cust_script_text_411.txt:5436-5987`)

The four `SHIPMENTS` triggers (CONFIRMED, lines 5849-5892):

| Trigger | Event | Does |
| --- | --- | --- |
| `SHIPMENTS_BI0` | before insert | if `CONS_NO` is null, takes `NEXT_GFS_CONS_NO` (a `TMP<n>` number); sets `INSERT_DATE` |
| `SHIPMENTS_BU0` | before update | status 2 clears `RECEIVE_DATE` (so it is re-sent as ship info) |
| `SHIPMENTS_AU0` | after update | when status changes into 3 to 101, copies it to all the shipment's `SHIP_PIECES`. A linked Spring shipment follows status 2 |
| `SHIPMENTS_AD0` | after delete | deletes `SHIP_LABELS`. Deletes the linked Spring shipment |

The other 40, by purpose:

| Purpose | Triggers |
| --- | --- |
| Key generation on insert (`BI0`) | `SHIP_PIECES` (next parcel number), `SHIP_CUSTOMS`, `SHIP_DOCUMENTS`, `SHIP_LABELS`, `SHIP_LICENSES`, `SHIP_LICENSE_DETAILS`, `SHIP_PARCEL_ITEMS`, `ADDRESS_BOOK`, `GOODS`, `FEDEX_BROKERS`, `HERMES_ROUTES`, `MAP_FORMATS`, `QR_MAP`, `QR_RULES`, `QR_ZIP`, `QR_ZIP_ARRAY`, `CA_SCHEDULE`, `CARR_DISPATCH`, `CARRIER_UPLOAD_SCHEDULE`, `CUST_SITE_CONTACTS`, `CUST_UPL_SERVERS` |
| Cascade on parent delete or key change | `SHIP_PIECES_AD0/AU0` (items), `CUST_CONTRACTS_AD0` (routes, site contracts, station defaults), `CUST_CONTRACT_SERVICES_AD0` (products, routes), `CUST_SITE_CONTRACTS_AD0`, `CUST_CONTRACT_PRODUCTS_AD0`, `CUST_DEPARTMENTS_AD0`, `CUST_SITE_CONTACTS_AD0`, `AB_GROUPS_BD0`, `ADDRESS_BOOK_BD0`, `FEDEX_BROKERS_AD0`, `CUST_SENDERS_AD0` |
| Propagate renames | `CUST_SENDERS_AU0`, `CUST_SITES_AU0` (company name to stations; reprint switch), `CUST_CONTRACT_PRODUCTS_AI0` (new product gets a default row for every station) |
| Department-change queue for registration | `CUST_DEPARTMENTS_AI0/AU0`, `CUST_CONTRACT_PRODUCTS_AD1`, `CUST_SITES_BU0` write `CUST_DEP_CHANGES` rows. **Four are INACTIVE**: `CUST_DEPARTMENTS_AI0`, `CUST_DEPARTMENTS_AU0`, `CUST_CONTRACT_PRODUCTS_AD1`, `CUST_SITES_BU0` (in the 411 script) |

Contrast with central: the central `SHIPMENTS` has 16 triggers (status cascade, notifications, `POST_EVENT 'UPLOAD_2_GCP'`) in the sibling research. The site `SHIPMENTS` has four, and none posts a change feed. The only site "outbound" signals are events posted by procedures: `SHIP_COMMITED`, `SHIP_UPLOADED`, `LOCK_STATUS`, `SITE_UPDATED`, `UPDATE_FAILED`, `META_UPDATE`, `UPD_FOUND`.

### 5.5 Procedures: 114 in 411, by purpose (names from `cust_script_text_411.txt:545-2449`)

| Family | Procedures |
| --- | --- |
| Commit and upload state | `SHIP_STATUS_CHANGED` (just `POST_EVENT`), `SHIP_COMMITED` (sets `LOCK_DATE`), `SHIP_UPLOADING/2`, `SHIP_UPLOADED/2`, `UNDO_UPLOADING/2`, `UNDO_SESSION`, `CHECK_UNCOMMITED_SHIPS`, `CHECK_MANIFESTED`, `GET_RM_OBA_SHIPS/2`, `SET_AUTO_COMMIT`, `SET_AUTO_UPLOAD` |
| Update, download, lock | `GET_SITE_VER`, `GET_UPD_VER`, `GET_UPD_SCRIPT`, `SAVE_DOWNLOAD`, `CHECK_DOWNLOADS`, `SITE_UPDATING`, `SAVE_UPDATES`, `UNDO_UPDATE/UNDO_UPDATES/UNDO_DOWNLOAD`, `PURGE_DOWNLOADS`, `CHECK_VER_START`, `CHECK_VER_STATUS`, `TRIG_LOCK_COUNT`, `DEC_LOCK_STATUS`, `UNLOCK_SITE`, `CHECK_LIC_STATUS`, `CHECK_HERMES_UPDATE`, `GET_HERMES_VER_DATE` |
| Registration and upsert | `INIT_SITE`, `ASSIGN_DEF_ON_REG`, `IU_*` (contracts, services, products, departments, ranges, third-party accounts, site contracts, consolidation, default services), `*_IU` for carrier and Hermes/NORDIC reference rows, `UPD_UPL_SERVER`, `CHECK_DEP_CHANGES`, `GET_CUST_DEP_CHANGES` |
| Numbering | `NEXT_GFS_CONS_NO`, `NEXT_GFS_PARCEL_NO`, `NEXT_CONS_NO`, `NEXT_PARCEL_NO`, `NEXT_RM_NO`, `NEXT_HERMES_GM_NUM`, `NEXT_GEN_VALUE`, `ADD_TO_RANGES/IRANGES`, `CHECK_RECYCLE_LIMIT` |
| Routing and service lookups ("Firebird as application") | `GET_DPD_DEPOT`, `GET_ANC_DEPOT`, `GET_NF_DEPOT`, `GET_DHL_DEPOT`, `GET_TUFFNELLS_DAY_NUM`, `GET_SERVICE_BY_ROUTE`, `GET_SHIP_SERVICE`, `FIND_PAF_ADDRESS`, `CHECK_BY_PAF`, `CHECK_DPD_COUNTRY`, `DPD_SERVICE_AVAILABLE`, `FIND_URC_CODE`, `GET_QR_RULE/ZIP`, `QR_MIN/MAX`, `CHECK_CARRIER` (alias resolution), `FIND_CONSOLIDATE_CONS`, `GET_CONSOLIDATE_CARRIERS` |
| Reports | `RM_SALES_SUMMARY`, `RM2_SALES_LIST/SUMMARY` |

`NEXT_CONS_NO` (`:10015`) takes the next number from the contract's `SHIP_RANGES` row, and returns nothing when the range is exhausted unless the carrier allows recycling (`CHECK_RECYCLE_LIMIT`, per-carrier `RECYCLE_PERIOD`). Ranges are shipped down at registration and site update. **No code path I read sends consumption back**: the only upward channel for range state is the shipments themselves. How GFS notices a near-exhausted range is UNKNOWN.

### 5.6 The update scripts (`ClientScripts/`)

- 378 files are 238 `cust_script_text_N.txt` plus 140 `cust_script_data_N.txt` (ids up to 505). `text` is the script run on the site. `data` lists, as `<name.bin>select ...</name.bin>` (or just a table name per line for the carrier/reference scripts), what central selects and zips beside it (`V4-Server-Database@82dde6b ClientScripts/cust_script_data_0.txt`, `_411.txt` lists 119 reference tables). 
- Tag use in the scripts: `<ExecSQL>` 710, `<md>` 354, `<ExecByParam>` 341, `<ExecMetaSQL>` 215 (60 scripts), `<Reconnect>` 71 (50 scripts), `<UpdByParam>` 9, `<UpdHrmByParam>` 5, `<Multi>` 7, `<ExecBySelect>` 3.
- By title: about 39 label-template changes, 14 route or postcode updates, 134 numbered only by ticket, three full-create scripts, 48 other. About 60 contain `ALTER TABLE` or procedure changes, 139 contain inserts.
- Script 0 is "GFS tuned registration" (`cust_script_text_0.txt`: wipes shipments, routes, ranges, contracts, departments, stations' default services, upload servers and the update flags, resets the generators, then loads the package) and script 1 is "Update site". Scripts can rewrite the update machinery itself: script 414 (`update locking algorithm`) re-creates `SAVE_UPDATES` and `UNDO_UPDATES`.

## 6. Q3: what a site does day to day

| Step | Path | Evidence |
| --- | --- | --- |
| Book a label (Client4) | staff or an import file. A thread watches the station's import folder (`FindFirst` on the station folder) and maps files through `IMPORT_MAP`. Validation sets status -1 or 0. Label is drawn from local template tables, or comes from a carrier call: Client4's own carrier units (`Carriers/`: BJS, COLL8, DPD, Exelot, OCS, RoyalMail, via GFS proxies), direct calls (`uFedex.pas`, `uInPostClient.pas`, Spring, Aramex, Chronopost and others). Client4 never calls CSS. Paths per carrier are in the vault ([[Systems/selector/architecture]] "Getting a label") and MPK 352157738, not repeated | `uimThread.pas:243`, `Client.Alpha/*.pas`, vault |
| Book a label (CSS) | WMS or integrator calls `ProcessShipment`. Same tables, same numbering procedures | `CSS@414569b ClientShipService.asmx.cs` |
| Local lookups during booking | depot and route lookups are local queries or procedures (`GET_ANC_DEPOT`, `GET_DPD_DEPOT`, `hdn_routes`, `CC_Routing`, `GET_NF_DEPOT`) in both apps | `sqlStatements.pas:72, 128, 2163`; `CSS ClientShipService.asmx.cs:3608-3750`; `ValidateProcedures.cs:3135-3276` |
| Print | raw spooler writes for thermal printers, external viewer for PDF | section 4 |
| Commit (manifest) | `status + 2`, `MANIFEST_DATE = NOW`, then `SHIP_STATUS_CHANGED('SHIP_COMMITED')`. Manual in Client4, `CommitShipments` in CSS, or auto-commit daily at `AC_TIME` (else `CLOSE_TIME`, else 17:00) on the site's `AC_STATION`. Auto-commit mode 9 commits all, mode 15 excludes Royal Mail. It can first write a print-export CSV | `sqlStatements.pas:1229`; `uSoapUpload.pas:216-340`; `fmMain.pas:780-784`; `dmClient.pas:5454-5464`; `uFunc.pas:33756` |
| Day end | there is no day-end procedure. Manifest print and commit are the day end. A shipment with `despatch_date` in the future is held until the date (`status = 1 and despatch_date <= NOW`) | `sqlCountCommitAll` |
| Pre-advice of uncommitted shipments | mode 8 (`UploadShipInfo`) every `AU_INTERVAL` minutes when `AUTO_UPLOAD = 1`, on `AU_STATION`, not on dial-up. Sends status 1 and 2 rows (14-ish columns) and marks them with `RECEIVE_DATE`. Central procedure `REG_SHIP_INFO` | `fmMain.pas:776-778`; `uSoapUpload.pas:1658`; `sqlStatements.pas:1294-1299`; `UploadServer uplConst.pas:268` |
| Upload | event-driven on `SHIP_COMMITED`, immediately, upload station only (section 7) | `dmClient.pas:2094-2113` |
| ChannelAdvisor | on `SHIP_UPLOADED` with `USE_CA = 1`, Client4 posts shipped status back to CA from the upload station. CA orders are also imported by Client4 | `dmClient.pas:2115-2121` |
| Licence/site status | every `CHECK_LIC_PERIOD` hours (24 by default on the upload station) mode 11 asks central for the site's status. See 8.4 | `fmMain.pas:807-810`; `dmClient.pas:5440` |
| Backup | scheduled `BackupApp` to `.fbk`, local only | installer |

### Behaviour when the upload fails or the site is offline

- **Failure of mode 0 returns a negative; the batch reverts to 3/4** (`uSoapUpload.pas:1868-1896`, `UNDO_UPLOADING2`). Client4 shows "failed to upload, repeat upload" and shows the manual Upload button (`fmMain.pas:5917-5922`). **There is no timed retry of mode 0.** The next attempt is the next `SHIP_COMMITED` event, the next login of the upload station (`CheckStatus(0)` returns 5 when shipments sit at 3/4, then `fmMain.pas:8807` starts mode 0), or the user.
- **Event processing only happens when a user is logged in to Client4:** `MainEventsEventAlert` wraps everything in `if FLogged` (`dmClient.pas:1969`). An open Client4 sitting at the login screen does not upload.
- **Labels still print offline** for template carriers (local data only). Proxy and direct-API carriers need their endpoints (STATED by vault).
- **Offline for more than two days locks the site.** `CHECK_LIC_STATUS` (`cust_script_text_411.txt:7088`): if the status check fails, `check_lic_date` is stamped, and when it is older than two days while `SITE_REG = 1` the site sets itself to 3 (locked) and posts `LOCK_STATUS`. Requires a failed mode 11 run, which only runs on the upload station. A reachable central answering 3 locks it too; answering 11 unlocks.
- **Dial-up (RAS) and an HTTP proxy are supported** from `CUST_SITES.DIAL_UP/DIALUP_CONN/PROXY_*` (`uSoapUpload.pas:1186-1215`).
- **Manual path:** "unlock station" or export writes the six tables to a `.gup` ZIP in the station's export folder and marks the batch 12/13 (`fmMain.pas:6310-6330`, `uSoapUpload.pas:1815-1822`). How a `.gup` reaches central is UNKNOWN: nothing in the repos reads `.gup`.

## 7. Q4: local to central

| Aspect | Finding | Status | Evidence |
| --- | --- | --- | --- |
| Transport | SOAP RPC over HTTP(S) to a Delphi ISAPI library (`library gfsUploadServer`), one operation per call. Indy `TidHTTPRIO`. Interface `IIUploadServer` has 19 operations | CONFIRMED | `V4@73cfd69 gfsUploadServer.pas:1-76`; `UploadServer gfsUploadServer.dpr:1` |
| Setting for the URL | `CUST_UPL_SERVERS.GFS_HOST` (rows ordered by `UPL_ORDER`). Same table holds `GFS_USER`, `GFS_PSW`, proxy fields. Delivered per site in the registration and site-update packages (`upl_servers.bin`, `where CUST_ID = :SITE_ID`). A hard-coded URL inside `Client4.exe` was not found in the files read | CONFIRMED for the table; the DM says the URL is inside `Client4.exe`: **conflicts**, the code reads it from the table (a build default may exist elsewhere: UNKNOWN) | `uSoapUpload.pas:1219-1271`; `sqlStatements.pas:305`; `cust_script_data_0.txt:241-250` |
| Failover | tries each host with `CheckConnection` in order, first result >= 0 wins. `CheckConnection` on the server only proves its own registry setup read, it does not test the database or the caller | CONFIRMED | `uSoapUpload.pas:1260-1280`; `IUploadServerImpl.pas:206-212` |
| TLS and timeout | SSLv23 method, no peer verification set (`VerifyMode := []`); read timeout from `CUST_SITES.GFS_TIMEOUT` | CONFIRMED | `uSoapUpload.pas:1244-1248, 1132-1136` |
| How a site identifies itself | (1) registration: the site GUID (`CUST_SITES.CUST_SITE`) as `SITE_GUID` into `GetCustSiteRegData` and `CommitCustSiteReg`. (2) every later call: a `cnt.txt` entry in the ZIP holding `GFS_USER`/`GFS_PSW`, which the server uses as the **Firebird login with role `SOAP_UPLOAD`** to central (`InternalCheckConnection`). The row-level site id is `CUST_ID` inside the data. `GetVerUpdate*` take user and password as SOAP parameters | CONFIRMED | `IUploadServerImpl.pas:851-927, 1266-1320`; `uplConst.pas:11` |
| Whether credentials are per site | UNKNOWN. The table is per site (`CUST_ID`), but whether values differ is in live data. The server never checks that the shipments' `CUST_ID` matches the login | CONFIRMED (no check); values UNKNOWN | `IUploadServerImpl.pas:952-970` only checks the site is not locked |
| Payload | ZIP of DevExpress `TdxMemData` binary datasets, base64 (Indy MIME) in `TRemotableZip.EncodedZip`. Entries: `cnt.txt` (login), `ships.bin`, `pieces.bin` (parcels), `customs.bin`, `ver_info.bin` (site versions), `dep.bin` (shipper), `items.bin` (parcel items). Queries: `sqlShipUpload`, `sqlItemUpload`, `sqlCustomUpload`, `sqlShipperUpload`, `sqlUnitUpload`, all `where STATUS in (8,9) and UPL_STATION = n and UPLOAD_FLAG = flag`. `dep.bin` and `items.bin` are the shipper and unit tables despite the names | CONFIRMED | `uSoapUpload.pas:1798-1860`; `gfsConst.pas:200`; `sqlStatements.pas:1247-1291`; `UploadServer uplConst.pas:9` |
| Whole batch size | every status 3/4 shipment at the moment of marking, across all stations of the site (`SHIP_UPLOADING2` marks all `STATUS IN (3,4)` with `UPL_STATION = this station`) | CONFIRMED | `cust_script_text_411.txt:10946-10962` |
| Idempotency and order | server calls `reg_shipments`, `reg_ship_items`, `reg_ship_customs`, `reg_ship_units`, `reg_shipper` row by row in table order (ships first, then items, customs, units, shipper). `reg_shipments` inserts when the (consignment, carrier) is absent. If present and key fields differ, the old row is archived in `RECYCLE_SHIPS`, with no `UPDATE shipments` in that block (sibling finding, re-checked at `update_284.sql:195-205`). A repeat is therefore absorbed silently | CONFIRMED | `IUploadServerImpl.pas:1118-1262`; `update_284.sql:195` |
| Partial batches | on a per-row error `RunShipQuery` exits with a negative code, but `InternalUploadShips` still calls `ShipTrans.Commit` if the transaction is open: **rows written before the failure are kept**. Client sees the negative, reverts the whole batch, and re-sends it | CONFIRMED | `IUploadServerImpl.pas:1250-1255, 1467-1474` |
| What it returns | integer. `>= 0` ok (and, with updates enabled and pending, the result of `VerifyVersions`, so a positive number means "newer versions exist"). Negatives: -4 init, -5 database connection, -6 login or role refused, -7 site not found, -8 site locked (SITE_REG 3) or bad ZIP, -9 unreadable ZIP, -15 commit error, -100 unknown, and `-10 - n - 100` (-111 to -115) or `-10 - n - 200` (-211 to -215) for a failing table n | CONFIRMED | `gfsConst.pas:103-123`; `IUploadServerImpl.pas:1135-1140, 1179-1189, 1253`; client adds 1 on success (`uSoapUpload.pas:1884`) |
| Client side on any SOAP exception | result -70, same as a failure: batch reverts. A timeout after the server committed therefore causes a re-send | CONFIRMED | `uSoapUpload.pas:1868-1876` |
| What a repeat does (client view) | a re-sent batch returns success, no signal that it was a duplicate. Manual "Reupload" (mode 5, `fmReupload`) selects status 10 to 13 by despatch date range and calls `ReUploadShips`, which runs the same server code without the backup copy | CONFIRMED | `uSoapUpload.pas:1400-1475`; `IUploadServerImpl.pas:1861-1865` |
| Events the client raises | after a successful upload `SHIP_UPLOADED2` posts `SHIP_UPLOADED` (also the trigger for ChannelAdvisor shipped posts). `SHIP_COMMITED` (CSS or Client4) triggers the upload. `LOCK_STATUS` while uploading (a lock counter blocks commits during an upload) | CONFIRMED | `cust_script_text_411.txt:10918-10925`; `dmClient.pas:3597-3629` |
| Server-side copy | if the upload server has `BackupDatabase` set, every upload ZIP is also stored in `ship_backup` before processing. Active in production: UNKNOWN | CONFIRMED (code), UNKNOWN (live) | `IUploadServerImpl.pas:1370-1399` |
| Retention on site | shipments stay in the site database after upload (statuses 10 to 13). Nothing I read purges them | INFERRED | no delete path found in the files read |

Other outbound dependencies configured per site (names only): `ROUTE_URL` (carrier-routes service), `CR_SERVICE_URL` (credit manager, used by CSS), `POSTCODER_URL(2)`, `FEDEX_URL`, `DHL_URL`, `UPS_URL`, `ARAMEX_URL`, `UKM_*_URL`, `IPARCEL_URL`, `ACP_URL`, `HERMES_PS_URL`, `DPDSHOPS_URL`, `NORDIC_FTP`, `HRM_FTP`. Nordic routes are fetched by FTP straight from the supplier, not through the upload server (`uNordicClient.pas`, `fmMain.pas:787-790`).

## 8. Q5: central to local

### 8.1 What comes down

| Kind | `ver_type` | Stored on site in | Content | How it is made centrally |
| --- | --- | --- | --- | --- |
| Registration package | script id 0 | `CUST_SITES.UPD_VER_SCRIPT` (via `SAVE_DOWNLOAD(NULL...)`) | the whole starting data set for the site | Manager "get ready"; stored in `CUST_SITES.VER_DATA` (vault, `fmSiteReg.pas`) |
| Site update | above 100 (site id) | `CUST_SITES.UPD_VER_SCRIPT` | script 1 plus per-site data, deletes and inserts rows for the six keyed config types | Manager "Site update" (vault) |
| Meta (global) update | 1 | `CUST_SITE_VER.UPD_FILE` | scripts such as new label templates, reference data, DDL changes | uploaded as `CUST_SCRIPTS` rows (the numbered scripts) |
| Site update (named) | below 0 | `CUST_SITE_UPDATES.UPD_FILE` | one-off per-site packages | Manager Versions screen (vault) |
| Carrier route update | 2 (full) and 3 (HD, with delta) | `CARRIERS.ROUTE_VER_SCRIPT`, `HD_ROUTE_VER_SCRIPT` | postcode and depot routing for one carrier | central tools write `CARRIER_UPDATES`: `HDNLUpdater` reads the carrier's FTP files, builds from `CUST_SCRIPTS` 110/285 (`updater.pas:435-437, 547-553`); `ClipperUpdGenerator` uses 368 (`uClipperUpdater.pas:119, 133`). Both skimmed |
| Binaries | 4 to 100 | `CUST_SITE_VER.UPD_FILE` | `Client4.exe` (type 4), `updUtil.exe`, `BackupApp.exe` | Manager Versions screen (vault) |
| Hermes and Clipper routes | separate calls (modes 10, 13) | `HERMES_*`, `CC_*` tables directly | `GetLastCarrUpdate(carrier, user, pwd, old version date)` | central |
| Royal Mail services | mode 14 | `CUST_RM_PRODUCTS` | service availability per contract | central |
| Site status or licence | mode 11 | `CUST_SITES.SITE_REG`, `CHECK_LIC_DATE` | integer status | central |
| Ship info | none | | nothing comes back | |

Label templates are in the repo under `V4-Server-Database/LabelTemplates` (48 files) and manifests under `ManifestBlobs` (105 files): these are the sources the numbered scripts load (`manifest_sql_N.sql`, `manifest_param_N.txt`). Which are live: UNKNOWN.

### 8.2 Mechanisms and cadence (all CONFIRMED unless marked)

| Trigger | Mode | What |
| --- | --- | --- |
| After a successful upload that returned more than 1 (pending versions) | 1, `GetVersions` | send `ver_info`, server's `VerifyUpdates` answers with newer versions, site records `upd_found = 1` (`uSoapUpload.pas:989-1130`, `dmClient.pas:3615-3620`) |
| Scheduled at `CARRIER_UPLOAD_SCHEDULE.SCH_TIME` when schedule is on | 1 | `fmMain.pas:768-772` |
| At login, if `CHECK_VER_STATUS` returns 0 or 6 | 1 | `fmMain.pas:8803-8814` |
| Manual menu | 1, 2 | `fmMain.pas:6008, 6024` |
| Event `UPD_FOUND` | 2, `GetUpdate` | one `GetVerUpdate3` per found item, saves each with `SAVE_DOWNLOAD` (`uSoapUpload.pas:837-987`) |
| Event `UPD_DOWNLOAD` on the upload station | local | `StartUpdates` applies (section 8.3) (`dmClient.pas:2102-2110`) |
| Daily at `HRM_TIME` (default 08:00), Clipper daily | 10, 13 | `fmMain.pas:792-806`, `dmClient.pas:5465-5468` |
| Daily Nordic FTP thread, RM service check | | `fmMain.pas:787-790, 812-816` |

Whether updates happen at all depends on all of: central `AUTO_UPDATE = 1` for the site (`GetCommonVer` checks it for each type), site not locked, `block_updates` off on the upload server (`UploadServer ...Impl.pas:2078-2084, 2315-2330`), the site's upload station running with a logged-in user, and a successful `CheckConnection`.

### 8.3 Version tracking, apply and failure (state machine)

`upd_found` on `CUST_SITE_UPDATES`, `CUST_SITE_VER`, `CUST_SITES`, `CARRIERS` (and `upd_hd_ver_found` on `CARRIERS`):

| Value | Meaning | Set by |
| --- | --- | --- |
| 0 | current | `SAVE_UPDATES`, `PURGE_DOWNLOADS` |
| 1 | newer version found, size and date noted | client after `VerifyUpdates` (`sqlSiteVerFound`, `sqlCarrierVerFound`, ...) |
| 2 | downloading, owned by station n | `GET_UPD_VER` |
| 3 | downloaded, blob stored | `SAVE_DOWNLOAD` |
| 4 | applying, owned by station n | `SITE_UPDATING` |

- **Apply:** `StartUpdates` (`dmClient.pas:3849-3990`) reads the pending list, then runs every script in **one transaction**. A script statement failure stops the loop, rolls back and calls `UNDO_UPDATES` (4 back to 3, post `UPDATE_FAILED`), so the same packages are tried again on the next update cycle. On success it commits, reconnects, calls `SAVE_UPDATES` (4 to 0, `SITE_VER = UPD_VER`, post `SITE_UPDATED`), then `CheckBinUpdates`, which unpacks new exes and may close Client4 so `updUtil` swaps them.
- **Partial application is possible.** `<Reconnect>` (50 scripts) commits and reconnects mid-script and disables cancel (`ExecSingleStm`, `dmClient.pas:3156-3204`). `<ExecMetaSQL>` (60 scripts) runs DDL. Anything before a `<Reconnect>` is committed even if a later statement fails. The retry then re-runs the earlier part. Whether each such script is safe to re-run is **INFERRED not checked**. A comment at `dmClient.pas:927-931` records an earlier fault where gazetteer apply wrote on the wrong transaction, was lost on reconnect, yet `SAVE_UPDATES` still reported success.
- **A pending row with no script** is treated as a failure, not skipped (`dmClient.pas:3898-3912`).
- **Download failure:** a failed `GetVerUpdate3` leaves state 2 and the loop `Break`s on connection errors (-5, -6, -32); `UNDO_UPDATE` (`iUpdateNotFound`) resets that item to 0; `CHECK_DOWNLOADS` resets stuck 2s to 1 for the next try (`cust_script_text_411.txt:6956`). A crash mid-download or mid-apply is cleared at login by `UNDO_SESSION` (minus 1 on in-flight states).
- **Locking:** the site is locked for users while updates apply (`lock_station`, events `SITE_UPDATE` and `SITE_UPDATED`). `CHECK_DOWNLOADS` takes the lock only when nothing is half-way.
- **Versions seen by central:** each version check sends `ver_info.bin`, and `GET_CARRIER_UPD_VER` writes the site's installed carrier versions into central `CUST_CARRIER_VER_INFO` (`server_db.sql:16221-16275`, table `:7065`). The vault says `CUST_VER_INFO` is "the only central record"; this second table also exists. Whether both are live is UNKNOWN.
- **Dates cross the wire as locale-formatted strings** (`GetStrVerDate` uses `DateTimeToStr`, the server uses `StrToDateTime`) (`uSoapUpload.pas:851-860`; `IUploadServerImpl.pas:756-780`). A regional-settings mismatch between a site and the server is a plausible cause of "not found" results. INFERRED.
- **What a site that missed versions gets:** non-HD carrier routes return only the latest (`GET_CARRIER_UPD_VER` returns the current `ROUTE_VER`); HD routes return a delta only if the gap is under `hd_delta_max_days`, otherwise the full set. So a missed version is recoverable for routes. The Hermes and meta scripts are different: whether a meta script depends on an earlier one is UNKNOWN.

### 8.4 Registration and the lock

Mode 3 downloads the registration package for a key (`GetCustSiteRegData`), stores it with `SAVE_DOWNLOAD(NULL...)`, `RegGFSClient` runs script 0 in one transaction, and mode 4 `CommitCustSiteReg` sets central `SITE_REG = 1` (`dmClient.pas:4046-4100`; `IUploadServerImpl.pas:214-265`). `CommitCustSiteReg` returns 0 if central is already 1 and refuses with -8 unless central `SITE_REG` is 4 (`IUploadServerImpl.pas:236-244`). `GetCustSiteRegData` was not read. `SITE_REG` values (0, 1, 3, 4) are in the vault ([[Systems/selector/architecture]]). `CHECK_VER_STATUS` returns 11 for locked, -1 for unregistered.

## 9. Q6: variation and risks

### 9.1 Client4, CSS, CSS-Enterprise

| | Client4 (`V4`) | CSS (`CSS`) | CSS-Enterprise |
| --- | --- | --- | --- |
| Role | desktop, upload station | SOAP service, live on hosted VMs | refactor of CSS |
| Language | Delphi 7, DevExpress, IBX | .NET Framework, Firebird .NET provider | same |
| History | 73cfd69, 2026-08-27 | 698 commits, last 414569b 2026-10-20 (a release merge was reverted in the history, `0454e04`) | 9 commits: single-project import 2023-02-10, then five refactor commits 2025-08-22 to 08-29 |
| GFS contact | all of it | none | none (still only posts `SHIP_COMMITED`: `ClientShipService.asmx.cs:1692, 1977`) |
| Carriers | `Carriers/*.pas` plus ~40 `u*Client.pas` units | `Carriers/` 14 files (BJS, Coll8, DPD, Exelot, FedEx, InPost, OCS, RoyalMail, template, `ICarrier`) plus per-carrier `*Procedures.cs` | 26 carrier classes with `CarrierFactory`/`CarrierRegistry`/`Injector`, `Processing/` chain-of-responsibility, `Validations/` factory |
| Web methods | n/a | 35 | 35 |

CSS-Enterprise's own README calls it an internal playground that "may or may not become the official repo". It is not what runs on the VMs. The vault already notes this. I did not diff behaviour between CSS and CSS-Enterprise beyond the structure above.

### 9.2 Local processes that treat Firebird as an application

1. **Routing in procedures and tables** (section 5.5): booking asks the site database for depots, zones, services and PAF addresses. The "gaz" check the DM described fits `CC_ROUTING`, `HDN_ROUTES`, `GET_ANC_DEPOT` and friends. The version of the Clipper routing set (`ROUTE_VER`, `GFS_DEPOT`) is written into the label string sent to the carrier (`LC:V<…>_GAZ:V<…>`, `uFunc.pas:22553`), so a stale site is visible to the carrier. STATED by the DM, CONFIRMED in source.
2. **Number allocation** from `SHIP_RANGES`, with temporary `TMP` numbers.
3. **Commit and upload state machine** (status +2, +5, +2).
4. **Event bus:** `POST_EVENT` is the only IPC between CSS and Client4, and between procedures and the UI. A Client4 that is not running or not logged in misses events and is not replayed (no queue; startup re-checks status).
5. **Update distribution and apply**, including storing the `.exe` files each PC unpacks (`cust_site_ver.upd_file`, `uUpd.pas:34-40`).
6. **Licence lock** (`CHECK_LIC_STATUS`).
7. **Self-modifying update machinery** (scripts rewrite `SAVE_UPDATES`).

### 9.3 Version drift

- Sites hold their own version of everything: `SITE_VER`, per-carrier `ROUTE_VER`, per-station Client4 exe (`STATION_BIN_VER`), schema (by meta scripts, no single schema version number I found), Firebird server (installers for both 1.5 and 3.0 exist; `ALTER SEQUENCE ... RESTART WITH` in `uSoapUpload.pas` Hermes update is Firebird 3 syntax and `CREATE OR ALTER` needs 2.0+, so a 1.5 site cannot take the newest scripts. INFERRED).
- Drift causes in source: `AUTO_UPDATE = 0`; site locked; upload station off or not logged in; `block_updates`; failed download or apply left in state 1 or 3; a package that fails halfway (section 8.3); Hermes and Clipper routes on separate daily pulls; script-order dependence (UNKNOWN). The vault's note that central only records versions in `CUST_VER_INFO` should be re-checked against `CUST_CARRIER_VER_INFO`.
- The repo scripts are the October 2023 snapshot (sha 82dde6b) while Client4 is August 2026. Live `CUST_SCRIPTS` rows are not visible: **which site scripts are live is UNKNOWN**.

### 9.4 What a replacement would need to preserve on the site (delivery terms)

Everything below is derived from the findings above, not from a requirements source.

1. **Book without GFS being reachable** for template-label carriers: contracts, services, number ranges, routing tables, templates and manifest definitions held locally and refreshed by pull.
2. **Consignment numbers** allocated locally (carrier ranges plus temporary numbers that central marks 106), with range recycling per carrier.
3. **A durable "committed, not yet delivered to GFS" state** with an at-least-once uploader on one designated machine, batch marking, revert on failure, and an idempotent receiver keyed on consignment plus carrier that tolerates partial commits and replays.
4. **A trigger between a CSS-style API and the uploader** (today a Firebird event, lost if the uploader is not logged in). The CSS contract used by Fuse's selector-adapter, Parcel Portal and selector-rest-proxy.
5. **Pull-based updates with versions**, per-site config package, carrier route sets, script packages and binaries, with a site lock during apply and rollback to "downloaded" on failure.
6. **Licence or status check** with a self-lock after two days of failed checks.
7. **Registration** by a site key, with a one-shot start package.
8. **Raw thermal printing** (ZPL, EPL, DPL) through Windows queues, PDF printing through an external viewer, and the import-folder watcher with per-station maps.
9. **ChannelAdvisor round trip** and the other per-site outbound integrations (Postcoder, Nordic FTP, FedEx and InPost direct).
10. **Station UI configuration** (defaults, auto-commit time, auto-upload interval) in `CUST_SITES` and `CUST_SITE_STATIONS`.
11. **Dial-up and proxy support** exist in code; whether any site relies on them is UNKNOWN.

### 9.5 Corrections to existing notes

| Existing claim | Source says | Status |
| --- | --- | --- |
| "Site updates only add and change data. A contract or service removed in Manager stays on the site" ([[Systems/selector/architecture]] G5; [[Systems/selector/known-context]] "Manager edits"; [[Engineering/client4/architecture]] Updates) | Script 1 uses `<UpdByParam>` for six keyed config types (contracts, third-party accounts, site contracts, contract services, departments, contract products). `ExecStm` deletes local rows that are not in the package for those types (`V4@73cfd69 dmClient.pas:3290-3355`; `ClientScripts/cust_script_text_1.txt:136-154`), and the delete triggers cascade into routes and station defaults (`cust_script_text_411.txt:5508-5612`). So deletes propagate for those six types **if the live site-update script matches repo script 1**. It also means off-package contract SQL (tools-ui) is deleted by the next site update, not only by re-registration | CONFIRMED in source; live script UNKNOWN |
| "The upload URL is set inside Client4.exe" (DM, paraphrased) | the URL is read from `CUST_UPL_SERVERS.GFS_HOST` in the site database at each session | CONFIRMED; build default not seen |
| `CUST_VER_INFO` is the only central record of site versions | `CUST_CARRIER_VER_INFO` is also written by `GET_CARRIER_UPD_VER` | CONFIRMED |
| "378 files" as scripts | 238 text scripts plus 140 data files | CONFIRMED |
| CSS "UploadShipments only fires an event" | true for `ReuploadShipments` too: it calls the same method and the date range is not used (`ProcessShipProcedures.cs:4498-4551`) | CONFIRMED |
| Vault "upload station is the only link" | also true that an unauthenticated-looking `CheckConnection` returns OK from the server regardless of site | CONFIRMED |

## 10. Unknowns (not verifiable from source)

- Live `CUST_SCRIPTS` rows: which registration (type 0) and site-update (types 1 and 5) scripts are current, and whether a non-tuned registration exists.
- The live `UploadServer.ini` (`ServerIndex`), registry `block_updates`, `BackupDatabase`; production `Web.config` values per VM.
- Whether `GFS_USER`/`GFS_PSW` differ per site, and what the `SOAP_UPLOAD` role is granted.
- How a `.gup` export file is ingested centrally (no reader in any repo).
- Which sites are on Firebird 1.5, 2.x or 3.0, and how many run more than one station.
- IB Manager (EMS), Ghostscript and the Zebra driver as standard site installs: stated by the brief only. Ghostscript appears in CSS (`FileConverter`) but not in the Client4 installers.
- The writer of local status 100 and the user-facing meaning of status 2.
- How GFS learns that a site is running low on number range.
- Whether re-running the first half of a `<Reconnect>` script after a partial failure is safe.
- What `GetLastCarrUpdate` returns exactly (not read past its call site) and the Hermes update's full-versus-delta rule.
- The central tools (Manager, UploadServer beyond the paths read, HDNLUpdater, ClipperUpdGenerator) were not read in full. The other agent covers central.

## 11. Pages worth linking rather than repeating

MPK 351764483 (Legacy Selector) and children, in particular Getting a Label 352157738 and Customer Data Flow 352157700. Vault: `Systems/selector/architecture.md`, `known-context.md`, `Engineering/client4/*`, `Engineering/css/*`, `Handovers/2026-11-09-merak-replacement-pages.firebird-triggers-findings.md`. This file adds the site statuses, the update state machine, the licence lock, the upload code path and the site trigger and procedure catalogue, none of which are in those notes.
