# Container diagram: Legacy Selector, from customer set-up to central

This C4 level 2 diagram shows how a customer's set-up reaches their Selector site and how a shipment moves from request to central. It does not show how tracking reaches ECM, how billing works inside, or registration states.

It replaces the ASCII block in "The flow" on the page "Legacy Selector - Customer Data Flow" (352157700, space MPK, version 5). Researched 9 Nov 2026 from that page, `Systems/selector/architecture.md` and `known-context.md`, and the Selector repos in `~/code/selector`.

Split decision: one diagram, not two. It has 16 boxes against a limit of 20. The set-up and shipping paths share four boxes: Client4, the site database, the upload server and the central database. Splitting would draw those twice. The Gaps section says where to cut if it proves crowded.

Status values: `Verified in page` means the page states it. `Verified in source, not on page` means the vault notes or repos show it but the page does not. `Not confirmed` means no source settles it, so draw it dashed.

## Groups

| Group | Boundary type | Contents |
| --- | --- | --- |
| Hosted site (one per customer) | GCP Compute Engine Windows VM, project `gfs-cloud-selector-prod-uk1`. Standalone sites are the same without CSS, on the customer's own PC | E5, E6, E7 |
| Central Selector | Logical system boundary. Hosting Not confirmed, so no GCP icon | E2, E3, E4 |

Outside all groups: E1, E8, E9, E10, E11, E12, E13, E14, E15, E16.

## Elements

| ID | Name | C4 type | Technology or GCP product | Description | Group | Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E1 | GFS staff | person | | Create customers, sites and contracts, press "Site update", release routing files and paste contract SQL by hand. | none | Page: How the data reaches the site, steps 1, 4, 5, 6 | Verified in page |
| E2 | System 4 Manager | container | | Staff set up customers here. It builds the site packages that Client4 later pulls. | Central Selector | Page: steps 1, 2, 4 | Verified in page |
| E3 | Central database (SRV_GFS.fdb) | datastore | | Holds set-up, site packages and uploaded shipments. Its triggers queue changes for ECM and Royal Mail. | Central Selector | Page: In short, steps 1, 2, 4, 7 | Verified in page |
| E4 | Central upload server | container | | Returns stored site packages to Client4. Receives its uploads and writes shipments to the central database. | Central Selector | Page: steps 3, 7 of One shipment; Sources | Verified in page |
| E5 | Client4 | container | | Desktop app at the pack bench. The upload station pulls set-up and sends committed shipments to GFS. | Hosted site | Page: The two front doors | Verified in page |
| E6 | Site database (GFS.FDB) | datastore | | The site's own copy of contracts, ranges, routes, postcode data and label templates. | Hosted site | Page: In short, What one customer needs | Verified in page |
| E7 | CSS | container | | SOAP service on IIS. Books shipments for calling systems against the site database. Never uploads. | Hosted site | Page: The two front doors | Verified in page |
| E8 | tools-ui contract insert tool | container | | Generates contract SQL that staff paste into the site database. Central never sees it. | none | Page: How the data reaches the site, step 6 | Verified in page |
| E9 | Calling systems | system | | Customer WMS, DispatchCloud, Parcel Portal and selector-rest-proxy. They call CSS over SOAP. | none | Page: The flow; The two front doors | Verified in page |
| E10 | Pack bench operator | person | | Imports a CSV or keys in a shipment in Client4, then prints the label. | none | Page: The two front doors, Who uses it | Verified in page |
| E11 | GFS carrier proxy | container | | Turns a label request into the carrier's own call, using the customer's ApiKy key. | none | Page: The flow; One shipment, step 5 | Verified in page |
| E12 | ApiKy | system | | Checks the customer's key and returns the profile that leads to the carrier credentials. | none | Page: What one customer needs; The flow | Verified in page |
| E13 | Carriers | system | | Carrier APIs and FTP servers that answer label requests and receive pre-advice files. | none | Page: One shipment, steps 5, 8 | Verified in page |
| E14 | V4-Server-IE | container | | Sends pre-advice files over FTP to carriers that Selector did not call live. | none | Page: One shipment, step 8 | Verified in page |
| E15 | ECM | system | | Receives queued changes from the central database and tracks shipments. Its internals are not drawn. | none | Page: The flow; How the data reaches the site, step 1 | Verified in page |
| E16 | Billing app | system | | Finance's separate Delphi app. Bills from what reached the central database, on each customer's schedule. | none | Page: One shipment, step 8. `Systems/selector/known-context.md`: People and ownership | Verified in source, not on page |

## Relationships

Arrows point from the caller. A reply on the same call is not drawn.

| From ID | To ID | Label | Technology or message | Status |
| --- | --- | --- | --- | --- |
| E1 | E2 | Set up customers, sites, contracts and ranges, and build site packages | Manager screens "Get ready for registering" and "Site update" | Verified in page |
| E2 | E3 | Write the customer, site, contract and range tables | Firebird | Verified in page |
| E2 | E3 | Store a site package: VER_DATA at registration, CUST_SITE_UPDATES for a site update | Firebird, zipped package | Verified in page |
| E5 | E4 | Pull the registration package or a waiting update, with global data, routing files and new Client4 versions | SOAP, GetCustSiteRegData | Verified in page |
| E4 | E3 | Read the stored package | Firebird | Verified in page |
| E5 | E6 | Load the package: wipe and reload at registration, add and change on a site update. The repo's site-update script also deletes rows missing from the package for six types (live script not checked) | Firebird | Verified in page |
| E1 | E8 | Generate contract insert SQL | tools-ui | Verified in page |
| E1 | E6 | Paste the generated SQL into the site database | SQL, by hand | Verified in page |
| E3 | E15 | Queue changes from the set-up tables for ECM | Firebird triggers, TRANSFER_QUEUE | Verified in page |
| E10 | E5 | Import a CSV or key in a shipment, then print | Client4 screens | Verified in page |
| E9 | E7 | Request a label | SOAP, ProcessShipment | Verified in page |
| E5 | E6 | Validate, route by postcode, allocate numbers and make the label from local data | Firebird | Verified in page |
| E7 | E6 | Validate, route by postcode, allocate numbers and make the label from local data | Firebird | Verified in page |
| E7 | E5 | Signal a commit so the upload station sends the shipment | Firebird event SHIP_COMMITED | Verified in page |
| E7 | E11 | Request a label for a proxy carrier | HTTPS to the URL in CUST_SITES, CARR_KEY as the ApiKy key | Verified in page |
| E5 | E11 | Request a label for a proxy carrier | HTTPS to the URL in CUST_SITES, CARR_KEY as the ApiKy key | Verified in page |
| E11 | E12 | Check the key and fetch the customer profile | HTTPS | Verified in page |
| E11 | E13 | Call the carrier with the customer's credentials or GFS's shared account | Carrier API | Verified in page |
| E7 | E13 | Call the carrier's own API directly for the fixed list that skips the proxy | Carrier API | Verified in page |
| E5 | E13 | Call the carrier's own API directly for the fixed list that skips the proxy | Carrier API | Verified in page |
| E5 | E4 | At end of day, upload committed shipments and any manifest | SOAP, IUploadServer | Verified in page |
| E4 | E3 | Write the uploaded shipments to the central database | reg_shipments | Verified in page |
| E14 | E13 | Send pre-advice files to carriers not called live | FTP | Verified in page |
| E14 | E3 | Read the shipments due for pre-advice | Firebird | Not confirmed |
| E16 | E3 | Read shipments that reached central, on each customer's invoice run | Firebird | Verified in page |

## Layout hint

Put the Central Selector group across the top, left to right: staff, Manager, the central database, with the upload server below the database. Put ECM and the Billing app to its right.

Put the Hosted site group in the middle band, with the pack bench operator and calling systems on its left. Put the proxy, ApiKy, carriers and V4-Server-IE on the right, below the central group. Put tools-ui bottom-left, beside the site database.

Run the set-up arrows downwards from Central to the site. Run the shipping arrows left to right through CSS and Client4. Draw the end-of-day upload as one long arrow back up to the upload server.

## Key needed

- Dashed box or arrow with the label `Not confirmed`: E14 to E3 only.
- Compute Engine icon on the label of the Hosted site group only. No other box carries a GCP icon, because none is a GCP product. Hosting of Central Selector and the carrier proxy is not on the page.
- Cylinder for E3 and E6. Person icon for E1 and E10.
- Arrow rule: from the caller. Replies on the same call are not drawn.
- Two arrows share a label where CSS and Client4 do the same thing (validate and label, proxy call, direct call).

## Gaps

- **The page says a Sunday invoice run. The vault does not.** `Systems/selector/architecture.md` says each customer has its own schedule: daily, weekly defaulting to Monday, or monthly. `known-context.md` lists the live timetable as unknown. The arrow to the billing app names no day.
- **V4-Server-IE reading central is not confirmed.** The page says it sends pre-advice by FTP. The repo's `Source/uSQL.pas` reads central carrier, FTP and contract tables. It does not show a read of the shipment table, so that arrow is dashed.
- **One Client4 box stands for two roles.** The pack bench instance and the upload-station instance may be different instances on the same database. The page does not say. Treat one box as a simplification.
- **Standalone sites are not drawn.** About 172 sites run Client4 on a PC with a local database and no CSS. The model is recorded in free text, so the count is approximate.
- **Hosting of central and the proxy is not on the page.** Central Selector has no GCP icon. The carrier proxy shows none because the page does not name a host. Another twin records GKE for most proxies and Cloud Run for FedEx and InPost.
- **The proxy and direct lists differ between CSS and Client4.** `FEDEX` and `INPOST` go to a proxy in CSS but direct in Client4 (`Systems/selector/architecture.md`, Getting a label). Both arrows are drawn for both apps. Template carriers make no call and are not drawn.
- **Shipments reaching ECM are not on this page.** The page text says triggers on Manager's tables queue changes for ECM and Royal Mail. That arrow is drawn. Whether the same triggers carry uploaded shipments is covered by the Selector and ECM coupling diagram, which notes the production triggers were never read.
- **Royal Mail's replica (`rm_replica`) is not drawn.** The ASCII mentions it. It is a second consumer of the same triggers.
- **Who pastes the contract SQL is "someone" on the page.** The diagram says GFS staff. The page and vault do not name a role.
- **Calling systems omit Fuse's selector-adapter.** `Systems/selector/known-context.md` says selector-adapter, parcel-portal and selector-rest-proxy all book through CSS. The page lists the other three.
- **Left out on purpose:** the registration states, CSS API users and the Manager Versions screen. Also the carrier credential stores and the processing inside ECM and billing.
- **If Harry finds one diagram crowded, cut at the site database.** Set-up would be E1, E2, E3, E4, E5, E6, E8 and E15. Shipping would be E3, E4, E5, E6, E7, E9 to E14 and E16.
