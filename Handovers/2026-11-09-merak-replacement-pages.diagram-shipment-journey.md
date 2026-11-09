# Container diagram (C4 level 2, dynamic flow): one shipment through ECM

This diagram follows one shipment from a Selector label, or from Slipway for Amazon, through Firebird and ECM to a delivered parcel and its proof of delivery (POD). It does not show invoicing, claims, reporting, the carrier almanac, ticket and comment flows, or manual status changes.

Page: "Shipment Journey Through ECM" (MPK, page id 354975746, version 3). It replaces the ASCII block in "The journey". Stage numbers are the page's own, from "Stage by stage". Researched 9 Nov 2026.

Sources, closest to primary evidence first: the code-review findings of 9 Nov (`page1-challenge-findings`), the journey page, the two 6 Nov explainers, then the other text twins. Where they disagree, Gaps says so.

Status values: `Verified in page` means the journey page states it. `Verified in source, not on page` means another vault source states it. `Not confirmed` means no source settles it, so draw it dashed.

## Groups

| Name | Boundary type | Contents |
| --- | --- | --- |
| Selector | System | E1 |
| Central Firebird | System, with an on-prem part | E2, E3, E5, E18 |
| ECM | System | E7, E8, E9, E10, E11, E13, E14, E15, E16, E17, E19 |
| GKE cluster `prod-uk1-primary-cluster` | GKE cluster, drawn inside ECM | E10, E14, E15, E16, E19 |

Outside all groups: E4 Upload Service v2 and DataBridge, E6 Slipway, E12 Carriers and E20 Portal, Connect and customer webhook receivers. E4 is outside because no source says which system owns it. E6 is outside because it runs in its own Cloud Run project, not in ECM.

## Elements

| ID | Name | C4 type | Technology or GCP product | Description | Group | Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E1 | Client4 upload station | container | | Prints the label (step 1) into the site's GFS.FDB, then uploads committed shipments to central Firebird. CSS is folded in. | Selector | Page: stages 1, 2, "Getting into central Firebird"; diagram-selector-ecm-coupling E1, E2 | Verified in page |
| E2 | Central upload server | container | | Receives Client4's SOAP upload and inserts shipments and pieces into central Firebird. A known consignment goes to RECYCLE_SHIPS. | Central Firebird | Page: stage 2, "Getting into central Firebird" | Verified in page |
| E3 | Central Firebird | datastore | | Holds SHIPMENTS, SHIP_PIECES and status. Its procedures turn scans into parcel and shipment status. | Central Firebird | Page: stages 2, 10; challenge findings: "The contract at Firebird" | Verified in page |
| E4 | Upload Service v2 and DataBridge | container | MongoDB (hosting Not confirmed) | Takes customer files over SFTP into MongoDB. DataBridge loads them into central Firebird every 10 minutes. | none | Page: ASCII block, "Getting into central Firebird", "Two side paths" | Verified in page |
| E5 | Firebird Transfer Service | container | | Turns Firebird trigger rows into messages. Median lag 7.5 s for shipments. | Central Firebird | Page: stage 3 | Verified in page |
| E6 | Slipway | container | Cloud Run | Publishes Amazon Logistics UK shipments straight to ECM in Firebird's row shape. About 66 records since August 2026. | none | Page: "Two side paths"; challenge findings: "Couplings that go around Firebird" | Verified in page |
| E7 | gfs-modernizer | container | | Collects messages for a sliding 180 s, resolves carrier and customer company, and publishes shipments.v2. Hosting Not confirmed. | ECM | Page: stage 4 | Verified in page |
| E8 | shipment-identity-service | container | | Adds shipmentId and shipmentIdV2 to each shipment. Hosting Not confirmed. | ECM | Page: stage 5 | Verified in page |
| E9 | shipments.v2.identified | container | Pub/Sub topic | Announces each identified shipment. 17 in-project subscriptions and 2 webhook subscriptions receive it. | ECM | Page: stages 5, 6 | Verified in page |
| E10 | tracking-core and connectors | container | GKE workload | Opens one record per parcel, then polls carrier APIs through the connectors. Publishes 6.0M raw events in 15 days. | ECM, GKE cluster | Page: stages 6, 7; diagram-tracking-carrier-to-customer E4 to E8 | Verified in page |
| E11 | Royal Mail webhook and tracking-file-processor | container | Cloud Run (webhook) and GKE workload (file processor) | Receive pushed Royal Mail events and parsed carrier SFTP files, and match them to shipments. | ECM | Page: stage 7; diagram-tracking-carrier-to-customer E10, E13 | Verified in page |
| E12 | Carriers | system | | Carrier tracking and POD APIs, the Royal Mail webhook sender, and carrier SFTP servers. | none | Page: stages 7, 12 | Verified in page |
| E13 | raw_tracking.v1 | container | Pub/Sub topic | Carries each carrier scan with the carrier's own status code. 6.29M events in 15 days. | ECM | Page: stage 7, "In short" | Verified in page |
| E14 | Status deriver | container | GKE workload | Waits a sliding 60 s, then derives status, ETA and a RED, AMBER or GREEN exception. | ECM, GKE cluster | Page: stage 8; diagram-tracking-carrier-to-customer E15 | Verified in page |
| E15 | CCIS and ICIS | container | GKE workload | Customer and staff consignment stores. They hold events and tracking status for the portal and Connect. | ECM, GKE cluster | Page: stage 9; diagram-tracking-carrier-to-customer E16 | Verified in page |
| E16 | connect-hooks | container | GKE workload | Turns tracking events into customer webhooks. 6.5% of scans become webhooks. | ECM, GKE cluster | Page: ASCII block, stage 9; diagram-tracking-carrier-to-customer E17 | Verified in page |
| E17 | patina-service-2 | container | Dataflow job | Sends raw carrier scans back toward Firebird. No team owns it. | ECM | Page: stage 10, "Where it is fragile"; challenge findings | Verified in page |
| E18 | Scan Injector | container | | Calls SET_PARCEL_HIST and SET_SHIPMENT_HIST in Firebird. Runs 06:00 to 23:01 UK time. | Central Firebird | Page: stage 10; challenge findings: "Checked by hand" | Verified in page |
| E19 | gfs-pod-service | container | GKE workload | Keeps its own shipment copy. Fetches the POD from the carrier when asked and caches it for 1 hour. | ECM, GKE cluster | Page: stage 12; diagram-pod-service E6, E8 | Verified in page |
| E20 | Portal, Connect and customer webhook receivers | system | | Customer and staff tools that show status and ask for a POD, plus customer systems that receive webhooks. | none | Page: stages 9, 12; diagram-tracking-carrier-to-customer E18, E19 | Verified in page |

## Relationships

| From ID | To ID | Step | Label | Technology or message | Status |
| --- | --- | --- | --- | --- | --- |
| E1 | E2 | 2 | Upload committed shipments after a commit | SOAP, IUploadServer | Verified in page |
| E2 | E3 | 2 | Insert shipments and pieces, diverting a known consignment to RECYCLE_SHIPS | REG_SHIPMENTS | Verified in page |
| E4 | E3 | 2 | Load customers' files into SHIPMENTS every 10 minutes | DataBridge, batch load | Verified in page |
| E6 | E4 | 2 | Export a masked copy of each Amazon shipment for billing | MongoDB collection | Verified in page |
| E4 | E3 | 2 | Load Slipway's masked copy into SHIPMENTS | DataBridge, REG_WILKO procedures | Not confirmed |
| E3 | E5 | 3 | Fire insert and filtered status triggers into the transfer queue | Firebird triggers (production text not read) | Verified in page |
| E5 | E7 | 3 | Publish each shipment and piece as a message | `fb.shipments.v1`, `fb.ship_pieces.v1` | Verified in page |
| E6 | E7 | 3 | Publish Amazon shipments directly, bypassing Firebird | `fb.shipments.v1`, `fb.ship_pieces.v1` | Verified in page |
| E7 | E8 | 4 | Publish the translated shipment | `shipments.v2` | Verified in page |
| E8 | E9 | 5 | Add shipmentId and publish the identified shipment | `shipments.v2.identified` | Verified in page |
| E9 | E10 | 6 | Say which parcels to track | Pub/Sub subscription | Verified in page |
| E9 | E11 | 6 | Deliver shipments so pushed events and file rows can be matched | Pub/Sub subscriptions | Verified in page |
| E9 | E14 | 6 | Deliver shipments for status derivation | Pub/Sub subscription | Verified in page |
| E9 | E15 | 6 | Deliver shipments so a consignment record opens | Pub/Sub subscription | Verified in page |
| E9 | E19 | 6 | Deliver shipments for the POD service's own copy | Pub/Sub subscription | Verified in page |
| E10 | E12 | 7 | Poll the carrier's API for each due parcel | HTTPS, SOAP or XML by carrier | Verified in page |
| E12 | E11 | 7 | Push Royal Mail events and supply SFTP tracking files | HTTPS webhook, SFTP | Verified in page |
| E10 | E13 | 7 | Publish each new tracking event | `raw_tracking.v1` | Verified in page |
| E11 | E13 | 7 | Publish each matched event | `raw_tracking.v1` | Verified in page |
| E13 | E14 | 8 | Deliver every raw event for derivation | Pub/Sub subscription | Verified in page |
| E14 | E15 | 8 | Publish status, ETA and exception | `shipment_tracking_status.v2`, `shipment_exception_status` | Verified in page |
| E13 | E15 | 9 | Deliver raw events as consignment events | Pub/Sub subscription | Verified in source, not on page |
| E13 | E16 | 9 | Deliver every raw event for customer webhook rules | Pub/Sub subscription | Verified in page |
| E15 | E20 | 9 | Serve status and events to customers and staff | Mechanism not stated | Verified in page |
| E16 | E20 | 9 | Send customer webhooks | HTTPS webhook | Verified in page |
| E13 | E17 | 10 | Deliver raw scans for write-back | Pub/Sub subscription | Verified in page |
| E17 | E18 | 10 | Send the carrier's raw code and scan text | `scanners.consignments.V1` (topic in the staging project) | Verified in page |
| E18 | E3 | 10 | Add scan history, then set parcel and shipment status | SET_PARCEL_HIST, SET_SHIPMENT_HIST | Verified in page |
| E20 | E19 | 12 | Ask for the POD by shipment ID | HTTP | Verified in page |
| E19 | E12 | 12 | Fetch the POD from the carrier on read | Carrier POD API | Verified in page |

Step 11 (delivered) has no arrow of its own. It reuses steps 7 to 10, so label those four steps with a small "also stage 11" note.

## Layout hint

Read left to right: Selector, Central Firebird, then ECM. Run the create path along the top (E1, E2, E3, E5, E7, E8, E9). Put Slipway above E5 and E4 below E2, with the masked-copy arrows dashed.

Run tracking down the ECM group: E10 and E11 under E9, then E13, then E14, E15, E16 on the right. Put E12 Carriers at the bottom left of ECM. Draw the write-back (E13, E17, E18, E3) as a return lane along the bottom, back to Firebird.

Put E19 and E20 at the far right, with the POD arrows running down to E12.

## Key needed

- Dashed arrow with the label `Not confirmed`: E4 to E3 for Slipway's masked copy.
- Step numbers in circles on each arrow, matching the page's stage numbers.
- Pub/Sub icon on E9 and E13 only. GKE icon on the cluster group label and on E10, E14, E15, E16 and E19. Cloud Run icon on E6. Dataflow icon on E17.
- E11 mixes Cloud Run and GKE, so draw it as a plain box and say so in the key.
- Plain boxes with no icon for Firebird, Selector, E4, E7, E8, the Transfer Service and the Scan Injector. They are not confirmed GCP products.
- Cylinder for E3. Messages that are not drawn as boxes (`fb.shipments.v1`, `shipments.v2`, `scanners.consignments.V1`) appear only in arrow labels.

## Gaps

- **Possible page error: "set shipment status" wording.** The page's "In short" says a Dataflow job and the Scan Injector "write scan history and set shipment status". The code review found the Dataflow job sets no status. The Scan Injector calls the Firebird procedures and Firebird derives the status. The diagram follows the review.
- **Possible page error: stage 11.** It says "the write-back sets a Firebird delivered status". Firebird maps the raw carrier code to the status (`GET_SCAN_CODE`, unknown becomes 207). The page never says the scans sent back are raw. Stage 10 shows `carrCode` only.
- **Possible page omission: Slipway's masked copy.** The ASCII block shows only Slipway's direct publish. "Two side paths" mentions the copy. Whether DataBridge writes it into Firebird in production is not confirmed, so that arrow is dashed.
- **Identity rule differs between sources.** The page says `shipmentId` comes from a counter. The coupling twin says consignment number plus carrier. Only a legacy copy of the live service was read.
- **Step 6 count.** The ASCII block says 19 subscriptions. The stage table says 17 plus 2. They agree. Only the topic box shows the total.
- **Raw events reach CCIS and ICIS directly.** The page's ASCII block shows them fed only by the status deriver. The manifests show their own `raw_tracking.v1` subscription. That arrow is `Verified in source, not on page`.
- **E7 and E8 hosting is unknown.** No source places gfs-modernizer or shipment-identity-service in the GKE cluster, so they have no hosting icon.
- **Production Firebird triggers have not been read.** The E3 to E5 arrow rests on a repo script with a syntax error and on message volumes.
- **Scan Injector source is unread.** It sits in the unreachable legacy organisation. Its arrow rests on error logs and Selector's own calls.
- **Folded to stay at 20 boxes:** CSS and the site's GFS.FDB (into E1); the tracking connectors and tracking-core (E10); the Royal Mail webhook and file processor (E11); `file-ingestion-ftp-proxy`; customer webhook receivers (into E20).
- **Left out:** claims, reporting, the Hub import service, the carrier almanac, the reference-data feeds, invoicing (stage 13) and `legacy-invoice-translator`. Also manual status, ticket and comment flows.
- **Ownership.** No team owns `patina-service-2` or the Scan Injector.
- **Carrier coverage of write-back is partial.** The page lists some carriers as unresolved, so the E17 to E18 arrow does not apply to every shipment.
