Status tags: **CONFIRMED** (read in source), **STATED** (a document or note says it, source not read), **INFERRED** (a reading of source, not proved), **UNKNOWN**. `[??]` marks a missing fact, listed in "Not confirmed yet". Merak replacing Selector is a hunch, not a decision. This page is part of the Merak research.

Up: Client4, the desktop program on a site's one upload station, posts a base64 ZIP of binary datasets in a single SOAP (Simple Object Access Protocol) call. It goes to the first working host in a list held in the site database. The upload server logs in to central Firebird as the site's own database user and runs the `REG_*` (register) procedures in one transaction. That transaction commits even if a row failed. Down: sites poll central, download update packages into binary columns, and apply them in one transaction under a site lock. An upload has no timed retry: a failed batch waits for the next commit, login or manual upload. A download is retried only by the next version check. All of this is CONFIRMED in source, except where a tag says otherwise.

Terms. A *site* is a despatch location with its own Firebird database file. *Central* is the main Firebird database. A *batch* is the set of committed shipments sent in one upload. A *package* is one zipped update that central builds and a site downloads.

Two sibling pages cover each side on its own. They are "Selector at a Site: What Runs Locally and What the Site Database Holds" and "Central Firebird: What the Hub Does and Who Reads It". Booking a label is on [Legacy Selector](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/351764483) and [Customer Data Flow](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/352157700).

## A shipment's trip up

A parcel is despatched at a site. It becomes GFS's record when central holds the shipment. The steps below give the local status at each point. Central keeps whichever status arrives, except for temporary numbers (step 7).

1. **Print.** Local status 1 means the label is printed. Status 2 is set after a print-export step. What staff mean by 2 is `[??]`.
2. **Commit.** Staff commit in Client4, a web-service call commits, or an automatic commit runs daily at the site's set time. Without a set time it runs at close time, else 17:00. Status goes up by 2: 3 from 1, 4 from 2. The procedure posts the event `SHIP_COMMITED`. The web service (CSS) books shipments for warehouse systems on hosted virtual machines. It never contacts central and only posts this event.
3. **Wake.** Client4 on the upload station catches the event, but only while a user is logged in. Two other triggers exist: the upload station's login, when shipments sit at 3 or 4, and the manual Upload button.
4. **Mark.** The procedure `SHIP_UPLOADING2` adds 5 to every shipment at 3 or 4 for this station. Status becomes 8 or 9. It also stamps a send date, the station and a batch flag. A lock counter blocks commits while an upload runs.
5. **Pack.** Client4 selects the 8 and 9 rows. It sends 96 of the 136 site shipment columns. Label images and documents never leave the site. The ZIP holds `cnt.txt` (the site's database login), `ships.bin`, `pieces.bin`, `customs.bin` and `ver_info.bin`. Optional `dep.bin` (shipper) and `items.bin` (units) may follow.
6. **Send.** Client4 reads the hosts from `CUST_UPL_SERVERS`, ordered by `UPL_ORDER`. It tries each in turn, and the first result of 0 or more wins. The address lives in the site database. A default may also sit in the executable (UNKNOWN).
7. **Register at central.** The server runs `REG_SHIPMENTS`, `REG_SHIP_ITEMS`, `REG_SHIP_CUSTOMS`, `REG_SHIP_UNITS` and `REG_SHIPPER`, row by row, in one transaction. A consignment number that starts with `TMP` is a temporary number. Central stores such a shipment at status 106. Other central statuses on arrival are `[??]`.
8. **Reply.** The server returns an integer. Zero or more is success. A positive number means newer update packages exist (INFERRED on the server side, acted on by the client).
9. **Close at the site.** On success, status goes up by 2 to 10 or 11, and the site posts `SHIP_UPLOADED`. On a negative result, `UNDO_UPLOADING2` returns the batch to 3 or 4. Any SOAP error counts as a negative result, so a timeout after central committed causes a re-send.

A separate pre-advice call sends uncommitted shipments (status 1 and 2) every set number of minutes when auto-upload is on. Central handles it with `REG_SHIP_INFO`. A manual export writes the same datasets to a `.gup` file and marks the batch 12 or 13. How that file reaches central is `[??]`.

**Idempotency.** Central identifies a shipment by consignment number plus carrier. If the pair is absent, `REG_SHIPMENTS` inserts a row. If it exists and key fields differ, the procedure copies the old row to `RECYCLE_SHIPS`. The key fields are despatch date, site, contract, service, packs, address line 1, town, postcode and country. The branch read has no `UPDATE shipments`. If the key fields match, the repeat is absorbed. The site is told "success" in every case. Only the insert branch and the start of the recycle branch were read. Four carrier-specific branches were not.

**Return codes.** Negative codes name the stage that failed. They include -5 database connection, -6 login or role refused, -7 site not found, -8 site locked or in the wrong state and -15 commit error. Codes -111 to -115 and -211 to -215 name the failing table by position. The client adds -70 for any SOAP exception.

**What raises events.** The upload server posts none. At the site, `SHIP_COMMITED` starts an upload and `SHIP_UPLOADED` follows one. At central, the trigger `SHIPMENTS_AI2` posts `UPLOAD_2_GCP` after every shipment insert. Whether it is active in production is UNKNOWN. A status 106 insert also writes a log row that fires `ERROR_ALERT`. No listener was found.

## What comes down

Central never pushes. A site asks, and central answers. Everything that comes down is a ZIP stored in a binary column in central, built from the `SELECT` lists held in `CUST_SCRIPTS`.

| Package | What it carries | Built by | Held in |
| --- | --- | --- | --- |
| Registration | The site's starting data set, loaded once | Manager, the desktop admin tool | `CUST_SITES.VER_DATA` |
| Site update | One site's contracts, services and departments | Manager | `CUST_SITES.VER_DATA`, history in `CUST_SITE_UPDATES` |
| Meta update | Reference data, label templates, manifest definitions, schema scripts | Manager, from `CUST_SCRIPTS` rows | `CUST_SITE_UPDATES` |
| Carrier routes | Postcode and depot routing for one carrier | Manager importers, or the Hermes, Parcelforce, HDNL and Clipper programs | `CARRIER_UPDATES` |
| Binaries | `Client4.exe`, `updUtil.exe`, `BackupApp.exe` | Manager | `CUST_SITE_UPDATES` |

Hermes and Clipper routes use separate daily pulls. Which `CUST_SCRIPTS` rows are live is `[??]`.

**How a site notices.** The upload station asks for versions after an upload that returned a positive number, at login and by hand. It also asks at a scheduled time where a schedule is on. Central answers only if the site's `AUTO_UPDATE` is set, the site is not locked, and updates are not blocked on that upload server. Each check also writes what the site runs back to central, into `CUST_VER_INFO` and `CUST_CARRIER_VER_INFO`. Whether both tables are live is UNKNOWN.

**The update state machine.** The value `upd_found` records how far each package has got on the site.

| Value | Meaning | Set by |
| --- | --- | --- |
| 0 | Current | `SAVE_UPDATES`, `PURGE_DOWNLOADS` |
| 1 | Newer version found | Client4 after the version reply |
| 2 | Downloading, owned by one station | `GET_UPD_VER` |
| 3 | Downloaded, stored in a binary column | `SAVE_DOWNLOAD` |
| 4 | Applying, owned by one station | `SITE_UPDATING` |

**Apply.** The upload station runs every downloaded script in one transaction while the site is locked to users. If a statement fails, the transaction rolls back, state 4 returns to 3 and the site posts `UPDATE_FAILED`. The same packages are tried at the next update cycle. On success, state returns to 0, the site version is recorded, and `updUtil.exe` swaps any new executables.

**Partial apply.** Scripts can commit part way. The `<Reconnect>` tag (50 scripts) commits and reconnects mid-script, so earlier statements stay even if later ones fail. The `<ExecMetaSQL>` tag (60 scripts) runs schema changes. Whether such a script is safe to re-run is INFERRED, not checked. A code comment records an earlier fault where a gazetteer apply was lost on reconnect, yet the site still reported success.

**Deletions.** Earlier notes say a contract removed in Manager stays on the site. The repo's site-update script says otherwise. For six keyed types (contracts, third-party accounts, site contracts, contract services, departments, contract products), it deletes local rows missing from the package. Delete triggers cascade to routes and station defaults. So the earlier note is wrong if the live script matches the repo. The live script was not checked.

## When things fail

| Case | Site does | Central does | Tag |
| --- | --- | --- | --- |
| Site offline | Shipments stay at 3 or 4. Template-label carriers still print. After two days of failed status checks the site locks itself. | Nothing. | CONFIRMED (lock rule) |
| Upload fails halfway | Client4 reverts the whole batch to 3 or 4 and shows "repeat upload". It re-sends on the next commit event, login or manual upload. | Keeps the rows written before the failure and returns a negative code. | CONFIRMED |
| Central partial commit | Sees only the negative code. | Commits whenever a transaction is open, even after a failed row. A failed upload therefore leaves partial data in central, and the batch is re-sent later. | CONFIRMED |
| Duplicate upload | Sees success. | Inserts only absent pairs. A pair with different key fields goes to `RECYCLE_SHIPS`. A duplicate parcel goes to `RECYCLE_ITEMS`. A person then uses Manager's recycle screen. | CONFIRMED |
| Parcel with an unknown carrier | Sees success. | Returns silently and drops the parcel. | CONFIRMED |
| Upload host unreachable | Tries the next host in `UPL_ORDER`. | The connection check proves only the server's own set-up, not the database. | CONFIRMED |
| Site crashes mid-upload | `UNDO_SESSION` at the next login returns stuck 8 and 9 rows to 3 and 4. | Nothing. | CONFIRMED |
| Download fails | State stays 2. The loop stops on connection errors. `CHECK_DOWNLOADS` resets stuck 2s to 1 for the next try. | Nothing. | CONFIRMED |
| Apply partly fails | Rolls back to state 3. Anything before a `<Reconnect>` stays committed. | Nothing. | CONFIRMED, re-run safety INFERRED |
| Locked site | Updates and uploads stop. | Rejects uploads from a locked site with -8. | CONFIRMED |
| Version drift | A site behind on versions keeps working on old data. | Records installed versions only when the site asks. | CONFIRMED |

A missed route version is recoverable: central sends the latest full set, or a delta when the gap is short. Whether a meta script depends on an earlier one is UNKNOWN.

## What happens next at central

After the upload, central's own change feeds hand the shipment to ECM. See [Selector and ECM Coupling](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354418743), [Shipment Journey Through ECM](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354975746) and [ECM Pub/Sub Topics](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/356155424). [From Label to Invoice](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354353232) covers the later path.

The Firebird change feed note finds that the Firebird Transfer Service is live. Datadog shows 3,022,807 rows in the window to 7 Nov 2026, but the trigger text that fills its queue is unread. The other feed, the `UPLOAD_2_GCP` event, has a confirmed trigger, and Datadog shows no data for GFSPublisher. That does not prove it is stopped. The central page, "Central Firebird: What the Hub Does and Who Reads It", has the detail.

## Where the two sides drift apart

- **Two schemas under one set of names.** 157 of 189 site tables share a name with a central table, but the columns differ. Site `SHIPMENTS` has 136 columns, against 125 in the central 2014 base. 32 site tables have no central counterpart in the scripts scanned.
- **A stale central script set.** The last numbered central script is `update_417`, dated 28 May 2022. The April 2026 upload server calls `REG_SHIPMENTS` with `:special_service`, which no repo script defines. Live central has moved on outside the repo.
- **Stale client scripts.** The repo's site scripts are an October 2023 snapshot, while Client4 is August 2026. Which scripts are live is `[??]`.
- **Version drift between sites.** Each site holds its own site, route, executable and schema versions. Causes in source include `AUTO_UPDATE` off, a locked site, an upload station that is off or logged out, and a failed apply. Installers exist for Firebird 1.5 and 3.0. The newest scripts need newer syntax, so a 1.5 site cannot take them (INFERRED).
- **Reference data changes quietly.** Central can change contracts, routes and templates. A site sees the change only at its next successful pull and apply. Dates cross the wire as locale-formatted text, so a regional-settings mismatch is a plausible cause of "not found" (INFERRED).
- **Nothing flows back into the shipment.** Site `SHIPMENTS` has scan and signature columns, and no Client4 source reads them. No code read sends carrier events from central back to the site.
- **The local Firebird is an application.** Site procedures own commit and upload status, update state, consignment numbering, routing lookups and the licence lock. Scripts can rewrite the update procedures themselves.

## What a replacement would need to keep

Hypothetical. These points come from the sources, not from a requirements document.

- An upload keyed on consignment number plus carrier, safe to repeat, with central able to absorb a partial batch.
- A local commit before anything is reported to central, with a durable "committed, not yet delivered" state.
- Safe partial-failure behaviour: a failed batch is re-sent whole, and the site is told the true outcome.
- Versioned reference data pushed down, with a site lock during apply and a rollback to "downloaded".
- A site that can keep booking and printing while offline, with a rule for how long.
- A clear event when a shipment becomes known to GFS.

## Not confirmed yet

- Live `CUST_SCRIPTS` rows: which registration and site-update scripts are current, and whether the live site-update script matches repo script 1.
- Upload server configuration files and whether updates are blocked or the server-side backup copy is on in production.
- Whether site upload credentials differ per site. Central does not check that a shipment's site matches the login.
- How a `.gup` export file reaches central. No repo reads one.
- Which upload host order is used in production, and whether Client4 ships a built-in default address.
- The meaning of local status 2, and what writes local status 100.
- Whether re-running the first half of a `<Reconnect>` script after a failure is safe.
- Whether both version tables are live, and whether `SHIPMENTS_AI2` is active in production.
- Central status on arrival, other than 106 for temporary numbers: `[??]`.
- How central learns that a site's number range is nearly used.
- Every `[??]` in the text above.

## Sources

| Repo | Commit | Date |
| --- | --- | --- |
| V4 (Client4) | 73cfd69 | 2026-08-27 |
| V4-Server-Database | 82dde6b | 2023-10-11 |
| V4-Server-UploadServer | 5773b8e | 2026-04-15 |
| V4-Server-Manager | a9bfab7 | 2026-04-27 |
| CSS | 414569b | 2026-10-20 |
| V4-Server-HDNLUpdater, V4-Server-ClipperUpdGenerator | 6a4eae8, 7318ac0 | 2023-10-11 |

Datadog read for the window 23 Oct to 7 Nov 2026, plus the research findings and the Firebird change feed note of 11 Nov 2026. Related pages: [Legacy Selector](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/351764483), [Customer Data Flow](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/352157700), [Selector and ECM Coupling](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354418743), [Shipment Journey Through ECM](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354975746), [From Label to Invoice](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354353232), [ECM Pub/Sub Topics](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/356155424).
