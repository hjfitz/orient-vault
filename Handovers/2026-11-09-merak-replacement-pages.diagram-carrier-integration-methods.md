---
tags: [handover, diagram-twin]
page: Carrier Integration Methods (MPK 353697842), section "Pre-advice by file"
level: C4 container
status: drawn in Lucid, link below
---
# Container diagram: pre-advice by file

This diagram shows how a shipment uploaded from Client4 ends up as a pre-advice file on a carrier's FTP server. It does not show which carriers and jobs are live, the routing-data and invoice file flows, or the SOAP and REST methods.

It replaces the ASCII block in "Pre-advice by file" on the page "Carrier Integration Methods" (353697842, space MPK, version 3). Researched 9 Nov 2026 from that page, the Selector twin for the coupling diagram, and the Tech Services knowledge vault.

Status values: `Verified in page` means the page states it. `Verified in vault` means a Tech Services vault note states it, not the page. `Not confirmed` means no source settles it.

Lucid document: see the link on the page. Nothing is drawn dashed, because every item below is stated by a source.

## Groups

| Group | Boundary type | Contents |
| --- | --- | --- |
| Central Firebird | System. Same group name as the Selector coupling diagram | E2, E3, E4, E5 |

E1, E6 and E7 sit outside the group. The page says V4-Server-IE is central, but not where it runs or which database host it uses, so it stays outside.

## Elements

| ID | Name | C4 type | Technology or GCP product | Description | Group | Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E1 | Client4 upload station | container | Delphi | Uploads shipments from a customer site to central. The only uploader. | none | Page: block, first line. Selector coupling twin, E1 | Verified in page |
| E2 | Central upload server | container | SOAP, Delphi | Receives Client4 uploads and writes them into SHIPMENTS. | Central Firebird | Page: "the upload server (SOAP, Client4 to central)". Selector coupling twin, E4 | Verified in page |
| E3 | SHIPMENTS | datastore | Firebird table | Central shipment rows. A new upload arrives at status 101. `pre_advised` is set to 1 once the file is sent. | Central Firebird | Page: block | Verified in page |
| E4 | CARR_IE_SERVICE_ITEMS | datastore | Firebird table | One job row per carrier export, with its schedule (`ACT_TIME`, `ACT_PERIOD`) or a database event. | Central Firebird | Page: Jobs bullet and Not confirmed bullet | Verified in page |
| E5 | CARR_FTP_FILES | datastore | Firebird table | Log of each pre-advice file sent. Holds the file content as well. | Central Firebird | Page: block. Vault: `guides/customs-ids-add-refs-and-dpd-preadvice.md` | Verified in vault |
| E6 | V4-Server-IE | container | Delphi | Runs one export job for one carrier and product group (`products.FTP_FILE_PREF`). Marks the shipments, builds the carrier's file and sends it. Release 10.0.0.12 shipped in Sep 2026. | none | Page: block, Jobs, Grouping and Upkeep bullets. Sources list `uItemThread.pas` | Verified in page |
| E7 | Carrier FTP server | system | FTP | The carrier's server that receives the pre-advice file. Plain FTP only. Hosts live in `CARRIER_FTP_ACCESS` rows. | none | Page: block, Transport bullet | Verified in page |

Counts: 7 elements. Three are containers (E1, E2, E6), one is a system (E7) and three are datastores (E3, E4, E5).

## Relationships

| From ID | To ID | Label | Technology or message | Status |
| --- | --- | --- | --- | --- |
| E1 | E2 | Upload shipments | SOAP | Verified in page |
| E2 | E3 | Insert the shipments at status 101 | Firebird | Verified in page |
| E6 | E4 | Read the export job for one carrier and product group | Firebird query | Verified in page |
| E6 | E3 | Mark the shipments the job will send | Firebird update | Verified in page |
| E6 | E7 | Send the carrier's file: CSV, fixed-width, XML or EDIFACT | FTP put | Verified in page |
| E6 | E5 | Log the file sent | Firebird insert | Verified in page |
| E6 | E3 | Set pre_advised = 1 on the shipments sent | Firebird update | Verified in page |

Counts: 7 relationships. The page names the steps in order but not the database call behind each, so the technology column for the Firebird rows is the obvious one, not a quoted one.

## Layout hint

Run Client4, the central upload server and SHIPMENTS left to right along the top, with the Central Firebird group holding the upload server and the three tables. Put V4-Server-IE at the right of the group and the carrier FTP server at far right.

## Key needed

- Cylinder: a table. Plain rectangle: a container or an external system.
- Arrows run in the direction of the call or the write.
- No GCP icons. No box here is a GCP product.
- Note on the picture: "Not confirmed: which jobs are live, and their hosts and schedules. Those live in central-database rows."

## Gaps

- **Which database holds the tables.** The page says "central SHIPMENTS" and "central-database rows". The Selector coupling twin puts SHIPMENTS in central Firebird. Vault notes tie `CARR_FTP_FILES` to Firebird. `CARR_IE_SERVICE_ITEMS` is also drawn there on the page's "central-database rows" wording.
- **What "marks the shipments" changes.** The page does not say which column. Sources name `PRE_ADVISED` and `SHIP_STATE` in `uSQL.pas`, so the mark may be a state change. Not confirmed, so the label says only "Mark".
- **The upload server's insert.** The page says "Client4 upload (SOAP) → central SHIPMENTS". The Selector coupling twin says the central upload server does the insert. The page names the upload server only in the line below the methods table.
- **Which jobs are live, for which carriers, and to which hosts.** The page marks this Not confirmed.
- **How DPD (Parceline) is pre-advised.** Not in the IE export list. The page marks it Not confirmed.
- **Who sends New Look's pre-advice over SFTP.** IE has no SFTP. Not on this diagram.
