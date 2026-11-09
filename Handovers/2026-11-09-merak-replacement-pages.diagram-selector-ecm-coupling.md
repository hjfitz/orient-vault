Container diagram: Selector, central Firebird and ECM

This C4 level 2 diagram shows how Selector, central Firebird and ECM are coupled through the six seams, with billing beside them. It does not show carrier connectors, webhooks, proof of delivery, claims or the services that call CSS.

Page: "Selector and ECM Coupling" (MPK, page id 354418743). Sources, closest to primary evidence first: Selector architecture and known-context notes, the ECM shipment-journey explainer, then the page draft. Where the page draft and another source disagree, the Gaps section says so.

## Groups

| Group | Boundary type | Contains |
| --- | --- | --- |
| Selector | System | Client4, CSS and System 4 Manager |
| Central Firebird | System, with an on-prem part | The central database, the central upload server and the three services that read or write it |
| ECM | System | The services, topics and stores that announce, track and show a shipment |
| Billing (Finance) | System | The Delphi billing app and the invoice translator |

Outside all groups: Slipway, and the portals, Seeker and CCP tools.

## Elements

| ID | Name | C4 type | Technology or GCP product | Description | Group | Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E1 | Client4 upload station | container | Delphi | Uploads committed shipments to central Firebird. The only uploader. Pulls site packages and updates. | Selector | Selector architecture: Guardrails G1, Data flow steps 3, 4, 7 | Verified in page |
| E2 | CSS | container | C# SOAP | Books shipments for callers over SOAP. Fires SHIP_COMMITED and never uploads. | Selector | Selector architecture: Guardrails G1, The two front doors | Verified in page |
| E3 | System 4 Manager | container | Delphi | Staff set up customers, sites, contracts and ranges here. It builds the site packages. | Selector | Selector architecture: Data flow steps 1, 2 | Verified in page |
| E4 | Central upload server | container | Delphi | Receives Client4 uploads and inserts them into SHIPMENTS. Serves site packages back to Client4. | Central Firebird | Selector architecture: Data flow steps 3, 7; Explainer: Stage 2 | Verified in page |
| E5 | Central Firebird (SRV_GFS.fdb) | datastore | Firebird | Holds SHIPMENTS, set-up tables and status. Its procedures roll scans into parcel and shipment status. | Central Firebird | Page draft: Six seams; Duties nobody wrote down | Verified in page |
| E6 | Firebird Transfer Service | container | On-prem | Copies new shipments and a filtered set of updates out of Firebird as fb.shipments.v1. | Central Firebird | Explainer: Stage 3, Assessment | Verified in page |
| E7 | Scan Injector | container | On-prem | Writes legacy-shaped scans into Firebird. Calls SET_PARCEL_HIST and SET_SHIPMENT_HIST. Runs 06:00 to 23:01 UK time. | Central Firebird | Explainer: Stage 10 | Verified in page |
| E8 | Legacy shipment update service | container | | Sets STATUS 100 or 1003 for one consignment and carrier. | Central Firebird | Page draft: Three cut points, item 3; Explainer: What can change it later | Verified in page |
| E9 | gfs-modernizer | container | | Translates fb.shipments.v1 into shipments.v2. Holds each shipment for a sliding 180 s window. | ECM | Explainer: Stage 4 | Verified in page |
| E10 | shipment-identity-service | container | | Gives each shipment its ID from consignment number plus carrier. Identity lasts 30 days from first insert. | ECM | Page draft: Six seams, row 6; Explainer: Stage 5 | Verified in page |
| E11 | shipments.v2.identified | container | Pub/Sub topic | Announces each identified shipment. 17 in-project subscriptions and 2 webhook push subscriptions receive it. | ECM | Page draft: Six seams, row 1; Explainer: Stage 6 | Verified in page |
| E12 | tracking-core | container | | Opens one record per parcel. Takes carrier events from connectors and webhooks and publishes them as raw tracking events. | ECM | Explainer: Stages 6, 7 | Verified in page |
| E13 | raw_tracking.v1 | container | Pub/Sub topic | Carries raw carrier scans with the carrier's own status code. 6.29M events in 15 days. | ECM | Explainer: Stage 7, diagram | Verified in page |
| E14 | patina-service-2 | container | | Turns raw_tracking.v1 events into legacy-shaped scans for Firebird. No team owns it. | ECM | Page draft: Three cut points, item 2; Explainer: Stage 10 | Verified in page |
| E15 | ECM consignment stores (CCIS, ICIS, CCDIS) | container | | Hold consignment records, events and status for portals. CCDIS matches invoice lines on consignment number plus carrier. | ECM | Explainer: Stages 9, 13; Selector architecture: Day end and billing handoff | Verified in page |
| E16 | Reference-data feeds | container | | Customer, contract, carrier and product change feeds, plus carrier credentials. Publisher and consumers not named. | ECM | Page draft: Six seams, row 4 | Not confirmed |
| E17 | Billing app | container | Delphi | Bills straight from central SHIPMENTS on each customer's schedule. Trigger set per contract by BILL_ON_SCAN. | Billing (Finance) | Selector architecture: Day end and billing handoff | Verified in page |
| E18 | legacy-invoice-translator | container | | Writes invoice files to Cloud Storage and publishes invoices_published.v1 once Finance publishes. | Billing (Finance) | Selector architecture: Day end and billing handoff | Verified in page |
| E19 | Slipway | system | | A second shipment source. Publishes Amazon Logistics UK shipments straight to fb.shipments.v1. About 66 records since August 2026. | None (external) | Page draft: Three cut points, item 1; Explainer: Assessment | Verified in page |
| E20 | Portals, Seeker and CCP tools | system | | Staff and customer tools. They mark shipments deleted or delivered, change status, raise tickets and comments, and read scan history. | None (external) | Page draft: Six seams, rows 2, 3; Explainer: What can change it later | Verified in page |

## Relationships

| From ID | To ID | Label | Technology or message | Seam | Status |
| --- | --- | --- | --- | --- | --- |
| E2 | E1 | Signals a commit so the upload station sends the shipment | Firebird event SHIP_COMMITED in the site database | 1 | Verified in page |
| E1 | E4 | Upload committed shipments | SOAP, IUploadServer | 1 | Verified in page |
| E4 | E1 | Return site packages and updates when Client4 asks | SOAP, GetCustSiteRegData, GetVerUpdate3 | | Verified in page |
| E4 | E5 | Insert shipments, and divert a known consignment to RECYCLE_SHIPS | REG_SHIPMENTS | 1 | Verified in page |
| E3 | E5 | Write customers, sites, contracts and ranges | Firebird | 4 (upstream) | Verified in page |
| E5 | E6 | Replicate new shipments and a filtered set of updates | Firebird triggers (production text not read) | 1 | Verified in page |
| E6 | E9 | Publish each new shipment, with isDeleted and wasManuallyUpdated from STATUS | fb.shipments.v1 (cut point 1) | 1, 3 | Verified in page |
| E19 | E9 | Publish Amazon Logistics UK shipments | fb.shipments.v1 (cut point 1) | 1 | Verified in page |
| E9 | E10 | Publish the translated shipment after the 180 s window | shipments.v2 (cut point 1) | 1 | Verified in page |
| E10 | E11 | Add shipmentId and publish the identified shipment | shipments.v2.identified | 1, 6 | Verified in page |
| E11 | E12 | Say what to track | shipments.v2.identified | 1 | Verified in page |
| E11 | E15 | Announce the shipment for records and invoice matching | shipments.v2.identified | 1, 6 | Verified in page |
| E12 | E13 | Publish each carrier scan | raw_tracking.v1 | 2 | Verified in page |
| E13 | E14 | Deliver raw scans for write-back to Firebird | raw_tracking.v1 | 2 | Verified in page |
| E13 | E15 | Deliver raw scans as consignment events | raw_tracking.v1 | 2 | Verified in page |
| E14 | E7 | Send legacy-shaped scans through a staging topic | scanners.consignments.V1 (cut point 2) | 2 | Verified in page |
| E7 | E5 | Set parcel and shipment status | SET_PARCEL_HIST, SET_SHIPMENT_HIST | 2 | Verified in page |
| E5 | E17 | Read SHIPMENTS rows. Bill-on-scan contracts wait for status above 200 and not 310 | Firebird | 2, 5 | Verified in page |
| E17 | E18 | Hand over published invoices | Interface not stated | 5 | Verified in page |
| E18 | E15 | Publish invoices to ECM | invoices_published.v1 | 5, 6 | Verified in page |
| E18 | E15 | Publish one message per invoice line | invoiced_shipments_published.v1 | 5, 6 | Not confirmed |
| E20 | E8 | Mark as deleted or delivered | Portal, SUS, legacy update service (cut point 3) | 3 | Verified in page |
| E8 | E5 | Set STATUS 100 or 1003 for one consignment and carrier | Legacy update service call | 3 | Verified in page |
| E20 | E5 | Change status (2000 to 2999), raise tickets, add comments and collections | MQP, Oz, SeekerAPI | 3 | Verified in page |
| E5 | E20 | Read scan history and status | Firebird | 2 | Verified in page |
| E5 | E15 | Carry tickets and comments into ECM | shipment-queries, gfs-tickets, shipment-comments.v1 | 3 | Not confirmed |
| E5 | E16 | Publish customer, contract, carrier and product changes | fb.* change feeds | 4 | Not confirmed |
| E16 | E9 | Supply the customer company name and carrier alias | Feed not named | 4 | Not confirmed |
| E16 | E12 | Supply carrier credentials to tracking connectors | carrier-credentials.v1 | 4 | Not confirmed |

## Layout hint

Order left to right: Selector, then Central Firebird, then ECM. Keep Billing (Finance) below Central Firebird, with the invoice arrows running right into ECM.

Run the shipment flow along the top row (Client4 to the upload server, the Transfer Service, then gfs-modernizer and on). Run the scan write-back along the bottom row, from ECM back to the Scan Injector. That keeps the two directions of the loop apart.

Put Slipway above the Transfer Service to modernizer arrow. Put the portals, Seeker and CCP tools bottom-left, beside Central Firebird. Put Reference-data feeds between the Firebird and ECM groups.

## Key needed

- Dashed box or arrow: `Not confirmed`.
- Seam numbers in square brackets on each arrow label, for example `[1]`. An arrow with no number is a Selector-internal flow.
- Pub/Sub icon on E11 and E13 only. The Firebird datastore has no GCP icon, because it is not a GCP product.
- Optional: tag the three cut-point arrows `CP1` (E6 to E9 and E19 to E9), `CP2` (E14 to E7) and `CP3` (E20 to E8). Drop the tags if the diagram is crowded.

## Gaps

- **Production Firebird triggers.** Nobody has read them, so the E5 to E6 arrow rests on the repo script and message volumes. The repo script has a syntax error.
- **Reference-data feeds (E16).** The page names the `fb.*` feeds and `carrier-credentials.v1` but no publisher, transport or consumer. The box is a grouping device, so it is dashed.
- **Carrier credentials conflict.** The page draft says `carrier-credentials.v1` reaches tracking connectors. The page 3 draft and the carrier-integrations notes say connectors keep their own credentials or call `carrier-credentials-manager`. Neither source names a topic consumer.
- **Manual changes into ECM.** How tickets and comments reach ECM is not stated. The effect of a CCP status change (2000 to 2999) on ECM is unconfirmed. Mark-as-deleted reaches ECM only through the normal update path.
- **Slipway has two routes.** The explainer has Slipway publishing straight to `fb.shipments.v1`. The Selector billing diagram also has Slipway exports passing through upload-service v2 and DataBridge into SHIPMENTS. Only the first is drawn.
- **Billing interfaces.** The note does not say how the billing app hands invoices to the translator, who owns the translator, or who publishes `invoiced_shipments_published.v1`. The consumers of `invoices_published.v1` are not named, so E15 is a best fit. How `BILL_ON_SCAN = 2` works is unknown.
- **Procedures.** The `SET_SHIPMENT_HIST` behaviour comes from a December 2025 dump and Scan Injector error logs. The live database may differ.
- **Hosting.** The note does not give the Firebird host or the hosting of the ECM services. No GCP product is shown for them.
- **Left out to stay at 20 boxes.** Carriers, connectors, webhooks, SUS, MQP, SeekerAPI, DataBridge, upload-service v2, the status deriver, gfs-pod-service, claims and the carrier almanac. Also the callers of CSS: selector-adapter, parcel-portal and selector-rest-proxy.
- **Owners.** No team owns `patina-service-2` or the Scan Injector. The lists of bill-on-scan carriers and of carriers written back are not available.


## As drawn in Lucid (2026-11-09)

The drawing follows the corrected findings, so it differs from the tables above:

- Selector's IE service is added in the Selector group, with an arrow into Firebird for the status procedures.
- `gfs-modernizer` and `shipment-identity-service` are one box, to stay at 20 boxes. The arrow between them is dropped.
- Slipway has a dashed arrow to Firebird for the masked billing copy, labelled Not confirmed.
- Firebird is drawn as the seam. Patina-service-2 forwards raw carrier scans, and the Scan Injector calls the status procedures.
- 20 boxes and 30 arrows.
