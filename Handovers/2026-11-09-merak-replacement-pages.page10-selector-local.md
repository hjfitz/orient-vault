A Selector site is one Firebird database (the database engine) with Windows programs working on it. **Client4** is the desktop program that books, validates, prints and commits parcels. On one PC per site, the upload station, Client4 is also the only program that talks to GFS. **CSS** is a SOAP service on hosted virtual machines (VMs). It books against the same database but never talks to GFS: its upload methods only raise a database event for Client4 to catch. About 120 of the site's 189 tables are reference data copied down from GFS. The site reports upwards by uploading six tables, and it receives reference data and updates by polling GFS. Everything here is read from a repo snapshot, not a live site. Claims carry a status: CONFIRMED (read in source), STATED (a note or Selector team member says it), INFERRED (my reading, not proved) or UNKNOWN. The central database and the interaction between the two have their own pages.

See also [Legacy Selector](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/351764483), [Legacy Selector overview](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/351764493), [Getting a Label](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/352157738), [Customer Data Flow](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/352157700), [Carrier and Proxy Interface](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/351797252), [Feature Sheet](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/351764518), [Carrier Proxies: Estate and Use Cases](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/352059403) and [Selector and ECM Coupling](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354418743).

## What runs at a site

A site is a despatch point. Two models exist (STATED, snapshot 6 Aug 2026). A hosted site runs CSS and Client4 on one VM with one database. A standalone site runs Client4 on the customer's own PC. There were 278 hosted VMs backing 259 sites, and about 1,000 sites were registered. No code branches on the model. The only record of it is a free-text field in the site table (CONFIRMED for the code, STATED for the model).

| Program | Where | What it does | Reads and writes | Status |
| --- | --- | --- | --- | --- |
| Client4 (`Client4.exe`) | Every site PC, and hosted VMs | Screens, import-folder watcher, booking, label printing, commit, manifest. On the upload station only: all contact with GFS | Reads and writes the site database directly. Listens for database events | CONFIRMED |
| updUtil | Beside Client4 | Waits for Client4 to exit, unpacks new program files from the database, restarts Client4 | Reads the database | CONFIRMED |
| BackupApp | Site, run by a scheduled task | Backs up and restores the database to `.fbk` files, locally only | Reads the database. No upload code seen (partly read) | CONFIRMED |
| CSS (ClientShipService, a SOAP web service under IIS) | Hosted VMs only | Validates, numbers, labels and commits for warehouse and API callers | Opens the database per request. No GFS client, no timer | CONFIRMED for the code, STATED for hosted-only |
| CSS helpers (printing, PDF and image conversion) | Hosted VMs | Printing and conversion for CSS | None | CONFIRMED |
| Firebird server | The site, or one PC of a multi-station site | Holds the database | n/a | CONFIRMED |
| IB Manager, Ghostscript, Zebra printer driver | Site | Admin tool, PDF conversion, thermal printer driver | n/a | STATED (one Selector team statement); not in any repo |

Client4 and CSS never call each other. They share one database, and the only link is a Firebird event (CONFIRMED). The notifier and other central programs are not site software.

Each site keeps its database path and station number in the Windows registry, not in the database (CONFIRMED). The installers create the database from a template backup, `gfs.fbk`, which is not in any repo.

## A parcel at a site, step by step

1. **Book.** Staff key a parcel, or an import file arrives in the station's import folder and Client4 maps it. A warehouse system can call CSS instead. Both write the same tables and use the same numbering procedures. For the label call itself, see [Getting a Label](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/352157738).
2. **Validate.** Client4 checks the parcel. A failure sets status -1 and writes the reason into the shipment's scan text field.
3. **Print.** Thermal labels go to the printer as raw data through the Windows spooler. PDF labels open in an external viewer. Template-based labels use only local data, so they print offline (STATED). Carriers reached through a proxy or direct API need their endpoints (STATED).
4. **Commit.** Committing is the manifest step. It adds 2 to the status, stamps the manifest date and raises the `SHIP_COMMITED` event. It runs by hand, through CSS, or daily at the site's set time (17:00 if none is set). A parcel with a future despatch date waits until that date.
5. **Day end.** No day-end procedure exists. Manifest printing and commit are the day end (CONFIRMED).
6. **Upload.** The upload station wakes on the commit event and sends the batch to GFS. Section "Going up and coming down" covers this.

When auto-upload is on, Client4 also sends printed but uncommitted shipments on a timer, as early notice to GFS. These rows are not marked as uploaded.

### Local status values

| Status | Meaning | Set by | Status of claim |
| --- | --- | --- | --- |
| -1 | Failed validation | Validation in Client4 | CONFIRMED |
| 0 | Validated, not printed | Import and validation | CONFIRMED |
| 1 | Label printed | Print | CONFIRMED |
| 2 | Set after a print-export step with no warnings. Can be committed at once. User meaning `[??]` | Client4 | CONFIRMED that it is set, meaning UNKNOWN |
| 3, 4 | Committed. 3 comes from 1, 4 comes from 2 | Commit adds 2 | CONFIRMED |
| 8, 9 | Marked for upload (commit status plus 5), with send date, station and batch flag set | Procedure `SHIP_UPLOADING2` | CONFIRMED |
| 10, 11 | Uploaded over SOAP (plus 2) | Procedure `SHIP_UPLOADED2` | CONFIRMED |
| 12, 13 | Written to a `.gup` file for manual transfer | `SHIP_UPLOADED2`, file mode | CONFIRMED |
| 100 | Deleted, excluded from manifests. Local writer `[??]` | Not traced in Client4 | STATED for central, local writer UNKNOWN |
| Above 100 | Carrier events copied to parcels by a trigger | Trigger only. Nothing local sets it that was found | CONFIRMED for the trigger |

A failed or interrupted upload undoes the plus 5: statuses 8 and 9 return to 3 and 4. A crash is cleared the same way at the next login.

## What the site database holds

The newest full-create script (`cust_script_text_411.txt` in the client scripts folder) defines 189 tables, 114 stored procedures and 44 triggers. These counts come from the definitions in that script, not from a live site database. The previous full-create script defines 193 tables. About 120 tables are reference data copied from GFS. The data list for the script names 119 (CONFIRMED). The rest are local.

| Area | Examples | Notes |
| --- | --- | --- |
| Shipments and parcels | `SHIPMENTS` (136 columns), `SHIP_PIECES` (86), parcel items, customs, shipper, units | Key is consignment number plus carrier |
| Labels and documents | `SHIP_LABELS`, `SHIP_DOCUMENTS`, label templates (including PDF label templates, commands, barcodes, images), label printers | Label images stay on the site (CONFIRMED) |
| Manifests | `MANIFESTS` (template, query and parameters per carrier) | Definitions come down. No table of generated output was seen |
| Customers, contracts, services | `CUST_SITES` (151 columns), contracts, services, departments, third-party accounts | Arrive in the registration and site-update packages |
| Number ranges | `SHIP_RANGES`, `ITEM_RANGES`, Royal Mail and Hermes number tables | Carved out centrally, used locally |
| Carriers | `CARRIERS`, aliases, surcharges, country tables | Carrier credentials are stored in some columns |
| Routing lookups, the "gaz" data | Postcode, zone and depot tables for DPD, ANC, HDN, Clipper, Hermes, Parcelforce, UK Mail, Tuffnells and others, plus address file tables | The local data a routing check reads |
| Station set-up | `CUST_SITE_STATIONS` (about 90 columns per PC: folders, printers, defaults), import maps | One row per PC |
| Update state | Site versions, site updates, update schedule, carrier version columns | Section "Going up and coming down" |
| History and logs | None in the database | Client4 writes log files instead |

**Six upload tables.** The upload sends shipments, parcels, customs, shipper, units and site version data. The shipment query sends 96 of the 136 columns (CONFIRMED). Label images and documents are in none of the six.

**Programs stored in the database.** The database holds the program files that other station PCs unpack (CONFIRMED).

**Licence lock.** A site status (`SITE_REG`: 0, 1, 3 or 4) and a check procedure lock the site after two days of failed status checks. See the next section.

**Consignment numbers.** The procedure `NEXT_CONS_NO` takes the next number from the contract's range row. It returns nothing when the range is exhausted, unless the carrier allows recycling. If a consignment number is not set at insert, the database creates a temporary number starting `TMP`. Ranges arrive at registration and in site updates. No code read sends range use back to GFS.

**Retention.** Shipments stay after upload (statuses 10 to 13). No purge was found (INFERRED).

### What the triggers and procedures do

The four `SHIPMENTS` triggers (CONFIRMED):

| Trigger | When | What it does |
| --- | --- | --- |
| `SHIPMENTS_BI0` | Before insert | Takes a temporary consignment number if none is set, and stamps the insert date |
| `SHIPMENTS_BU0` | Before update | Status 2 clears the receive date, so the row is sent again as early shipment info |
| `SHIPMENTS_AU0` | After update | Copies a status change into 3 to 101 to every parcel of the shipment |
| `SHIPMENTS_AD0` | After delete | Deletes the shipment's label rows and a linked Spring shipment |

The other 40 triggers do four jobs. They fill keys on insert (21 tables), cascade deletes, propagate renames, and write the department-change queue. Four queue triggers are inactive in the script. No site trigger posts a change feed. Events come from procedures: `SHIP_COMMITED`, `SHIP_UPLOADED`, `LOCK_STATUS`, `SITE_UPDATED`, `UPDATE_FAILED`, `META_UPDATE` and `UPD_FOUND`.

The 114 procedures fall into five families:

- **Commit and upload state:** mark, undo and finish uploads, check uncommitted shipments, set auto-commit and auto-upload.
- **Update, download and lock:** read versions, save downloads, start and undo updates, lock the site, check licence status.
- **Registration and upsert:** initialise the site, insert or update contracts, services, departments, ranges and carrier rows.
- **Numbering:** consignment, parcel, Royal Mail and Hermes numbers, range top-up, recycle limit.
- **Routing and service lookups:** depot, service and address lookups (for example `GET_DPD_DEPOT`, `GET_SERVICE_BY_ROUTE`, `FIND_PAF_ADDRESS`), carrier alias resolution.

## Going up and coming down

### Up: site to GFS

The upload station wakes on `SHIP_COMMITED`. It marks every committed shipment of the site (3 and 4) as 8 and 9 with a batch flag. It then builds a ZIP of binary datasets from the six tables, encodes it in base64 and sends it in one SOAP call. The target is the first working host in the local table `CUST_UPL_SERVERS`, ordered by `UPL_ORDER` (CONFIRMED). The site logs in to GFS as a Firebird user whose details travel in the ZIP. Whether those details differ per site is UNKNOWN.

The call returns an integer. Zero or more is success. A negative marks failure, and the batch returns to 3 and 4. Any SOAP error counts as failure, so a timeout after GFS committed leads to a re-send. There is no timed retry. The next attempt comes at the next commit event, the next login on the upload station, or a manual upload. Events are handled only while a user is logged in to Client4 (CONFIRMED). A Client4 sitting at its login screen does not upload.

If the site is offline for more than two days, the licence check locks it (status 3). A GFS answer of 3 locks it too, and 11 unlocks it. A manual export writes the same six tables to a `.gup` file and marks the batch 12 and 13. How that file reaches GFS is UNKNOWN. Wire detail and central handling belong on the interaction page, "Between a Site and the Centre: Uploads, Downloads and What Crosses".

### Down: GFS to site

The site polls. It asks for versions after an upload that reports pending versions, on a schedule, at login and by hand. A newer package sets `upd_found` to 1. The site then downloads each package into a blob column. The `upd_found` values (CONFIRMED) are:

| Value | Meaning |
| --- | --- |
| 0 | Current |
| 1 | Newer version found |
| 2 | Downloading (owned by a station) |
| 3 | Downloaded, blob stored |
| 4 | Applying (owned by a station) |

The upload station applies all downloaded packages in one transaction, under a site lock that blocks users. If a statement fails, the transaction rolls back, state 4 returns to 3, and the same packages are tried again on the next cycle. On success, `SAVE_UPDATES` sets the state to 0 and Client4 unpacks any new programs.

Partial application is possible. A script can contain a `<Reconnect>` tag (50 scripts), which commits mid-script. Scripts with `<ExecMetaSQL>` (60) run database definition changes. Anything before a reconnect stays committed if a later statement fails, and the retry runs the earlier part again. Whether they are safe to re-run is not checked. A code comment records an earlier fault where route data was lost on reconnect, yet the update reported success.

## Where sites differ and drift

- **CSS, CSS-Enterprise and Client4.** CSS runs on hosted VMs (698 commits, last 20 Oct 2026). CSS-Enterprise is a refactor line with 9 commits. Its README calls it an internal playground that "may or may not become the official repo". It is not what runs on the VMs. Both have 35 web methods, and neither contacts GFS.
- **Hosted versus standalone.** The split is recorded only in free text. A CSS installer exists, so a standalone site could also run CSS.
- **Firebird versions.** The installers include both Firebird 1.5 and 3.0. Newer scripts need Firebird 2.0 or later, and one Hermes update needs Firebird 3 syntax, so a 1.5 site cannot take them (INFERRED). Which sites run which version is UNKNOWN.
- **Firebird as an application.** Booking asks the site database for depots, zones, services and address matches. The database also runs number allocation, commit state, update apply and the licence lock. The routing set version goes into the label string sent to a carrier. A stale site is therefore visible to the carrier (STATED, CONFIRMED in source).
- **Drift.** Each site holds its own versions: site, carrier routes, Client4 per station, and schema. Updates lag when auto-update is off at GFS, the site is locked, or the upload station is off or logged out. A failed download or partial apply also causes lag. No single schema version number was found.
- **What the snapshot cannot say.** The client database scripts are an Oct 2023 snapshot (sha 82dde6b). Client4 is from Aug 2026. Which scripts are live is UNKNOWN.

## What a replacement would need to keep

This is hypothetical: Merak replacing Selector is only a hunch. The list comes from the findings above, not from requirements.

- Book and print without a connection to GFS, using contracts, services, routing tables, templates and manifest definitions held locally.
- Commit locally before upload, with a durable "committed, not yet delivered" state.
- Re-send a batch safely, with the receiver absorbing duplicates and partial commits.
- Keep reference data cached locally with a version, refreshed by pull.
- Apply updates safely: lock during apply, and fall back to "downloaded" on failure.
- Allocate consignment numbers locally without collisions, including temporary numbers and per-carrier range recycling.

## Not confirmed yet

- The live `CUST_SCRIPTS` rows: which registration and site-update scripts are current `[??]`.
- Whether site upload credentials differ per site `[??]`.
- How a `.gup` export file reaches GFS `[??]`.
- The standard install contents (IB Manager, Ghostscript, Zebra driver) beyond one Selector team statement `[??]`.
- The user-facing meaning of local status 2, and the writer of status 100 `[??]`.
- Which Firebird versions are deployed `[??]`.
- Whether Reconnect scripts are safe to re-run `[??]`.
- How GFS learns that a site is low on number range `[??]`.
- Whether a build default for the upload host exists, and whether any site uses dial-up `[??]`.
- Coverage: the carrier clients, the main form and the CSS commit and upload methods were sampled. Of 238 update scripts, about ten were read.

**Correction.** An earlier vault note said site updates only add and change data, so a contract or service removed in Manager stays on the site. The repo says otherwise. The site-update script (script 1) deletes local rows missing from the package for six types: contracts, third-party accounts, site contracts, services, departments and products. Delete triggers then cascade into routes and station defaults. So if the live script matches the repo, deletions do propagate. The live script was not checked.

A Selector team member said the upload address is set inside `Client4.exe`. The code reads it from `CUST_UPL_SERVERS` instead. I took the code. A build default may exist elsewhere.

## Sources

| Repo | sha | Date | Used for |
| --- | --- | --- | --- |
| V4 (Client4) | 73cfd69 | 27 Aug 2026 | Site app, upload client, update apply |
| V4-Server-Database, `ClientScripts/` | 82dde6b | 11 Oct 2023 | Site tables, procedures, triggers, update packages |
| V4-Server-UploadServer | 5773b8e | 15 Apr 2026 | Return values the site sees |
| CSS | 414569b | 20 Oct 2026 | Hosted SOAP service |
| CSS-Enterprise | 3650bfb | 29 Aug 2025 | Refactor line |
| V4 Installation | 2bf851e | 28 Jun 2023 | Site installers |

Also used: vault notes on Selector for estate counts (snapshot 6 Aug 2026), and a Selector team member's message of 4 Nov 2026 (paraphrased). Research date: 11 Nov 2026.
