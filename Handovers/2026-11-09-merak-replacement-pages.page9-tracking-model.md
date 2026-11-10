A tracking update is not just a status string. A carrier scan is turned into a GFS meaning, called a group (for example in transit, delivered or attempted). GFS then derives one shipment status across all the parcels of a shipment. So there are three shapes of information: the scan, the mapped scan and the shipment status. The word "status" means something different in each. Delivered is a group value, not a type of message or a topic of its own. Lost is not modelled. The research read code and deployed manifests on 10 Nov 2026, and nothing was run against production.

Each claim carries a status. CONFIRMED means it was read in code or a deployed manifest. STATED means a document or comment says it and it was not read in code. INFERRED means it follows from what was read and was not run. UNKNOWN means no source settles it. A fact the research could not find is marked `[??]` and listed in "Not confirmed yet".

## What a delivery goes through

A carrier reports a parcel as it moves. GFS gives each scan a group. The group tells customers and staff where the parcel is in its delivery. The list of groups is not fixed in code. A spreadsheet held in Google Cloud Storage sets it, and the research did not read that spreadsheet. **The list below is therefore not complete.** It holds every group the sources name.

| Group | Meaning | How it arises | Status |
| --- | --- | --- | --- |
| `DATA_ONLY` | Parcel data received, no usable scan yet. The default text is "PARCEL DATA RECEIVED" with code 200. It has the lowest precedence | The shipment status defaults to it when no usable scan exists. A scan can also map to it | CONFIRMED |
| `IN_TRANSIT` | Moving through the network. It is also the group given to any scan whose code has no mapping | Mapped from carrier codes, or by default for an unmapped code | CONFIRMED |
| `OUT_FOR_DELIVERY` | `[??]` | Mapped from carrier codes by the spreadsheet | Name CONFIRMED, mapping STATED |
| `ATTEMPTED` | Failed delivery attempt, as the sources describe it. No reason field exists | Mapped from carrier codes by the spreadsheet | Name CONFIRMED, mapping STATED |
| `HELD_AT_BRANCH` | `[??]` | Mapped from carrier codes by the spreadsheet | Name CONFIRMED, mapping STATED |
| `AWAITING_CUSTOMER_COLLECTION` | `[??]` | Mapped from carrier codes by the spreadsheet | Name CONFIRMED, mapping STATED |
| `RETURNED` | `[??]` | Mapped from carrier codes by the spreadsheet | Name CONFIRMED, mapping STATED |
| `PARTIALLY_DELIVERED` | Some parcels of a shipment are delivered and others are not | Created by GFS when it derives the shipment status. No carrier sends it | CONFIRMED |
| `DELIVERED` | Delivered. It has the highest precedence and carries the signatory | Mapped from carrier codes | CONFIRMED |
| `OTHER` | A bucket for searching only. It is never stored on a scan or status | Accepted as a search filter value | CONFIRMED that the filter accepts it, STATED that it is never stored |

Five of these names (`OUT_FOR_DELIVERY`, `ATTEMPTED`, `HELD_AT_BRANCH`, `AWAITING_CUSTOMER_COLLECTION` and `RETURNED`) are CONFIRMED only as accepted search filter values. The customer consignment search lists nine real groups and `OTHER`. That the spreadsheet emits each of the five mapped groups is STATED in the ECM development docs and not read.

### Outcomes and whether they end tracking

| Outcome | How it is represented | Does it end tracking? | Status |
| --- | --- | --- | --- |
| Delivered | Group `DELIVERED`, with the signatory. Separately, a delivered flag on the mapped scan | Not by itself. A delivered parcel is still polled where that carrier's delivered polling is switched on, and otherwise it expires after a time limit. The prod settings are unread `[??]` | CONFIRMED |
| Attempted or failed delivery | Group `ATTEMPTED`. No reason field. Any reason sits in the carrier's text, or in the free-form extras if a connector put it there `[??]` | No | Group name CONFIRMED, mapping STATED |
| Held at branch | Group `HELD_AT_BRANCH` | The findings do not say `[??]` | Name CONFIRMED |
| Partially delivered | Group `PARTIALLY_DELIVERED`, created across parcels | No | CONFIRMED |
| Returned | Group `RETURNED` | No handling that ends tracking was found | Name CONFIRMED, mapping STATED |
| Lost | Not modelled. There is no group, state or message for it. The vault notes that legacy UPS loss reporting reads Firebird status 1003 as lost, which is the same number the manual mark-as-delivered write uses | Not applicable | UNKNOWN in ECM. The 1003 note is STATED and unreconciled |
| Deleted | A parcel state, `DELETED`, set once at creation from a flag on the shipment. No scan or event announces a deletion | The parcel is polled only where that carrier's deleted polling is switched on, then it expires | CONFIRMED |

A manual mark-as-delivered creates a synthetic scan, one per parcel. Downstream it is treated as an ordinary scan, if it survives (CONFIRMED). The mismatch section below covers why it may not.

## Who sees what

Audiences get different shapes of information. None of them gets all three.

| Audience | What they get | Customer-visible? | Known distortions | Status |
| --- | --- | --- | --- | --- |
| Customer webhook | The raw scan, mapped again by the webhook itself. Body fields: `gfsId`, `carrierName`, `parcelNumber`, `consignmentNumber`, `carrierEventTime`, `status`, `text`, `isDelivered` | Yes, sent to the customer | It never carries the derived shipment status. `status` is a display string with six values: AWAITING COLLECTION, IN TRANSIT, OUT FOR DELIVERY, DELIVERED, RETURNED, DATA ONLY. It folds `ATTEMPTED`, `HELD_AT_BRANCH` and `PARTIALLY_DELIVERED` into IN TRANSIT. `carrierEventTime` holds the received time, not the carrier's time. The body has no event id, GFS code, delivery window, location or signatory. A failed post is logged and dropped. Whether it honours the visibility flag `[??]` | CONFIRMED |
| Customer portal data (customer consignment information service) | The shipment status, customer-visible variant only, plus the raw scan and the exception status | Yes, STATED by the vault as the store customers read | Which portal screens read it, and whether Connect reads it directly `[??]`. It also holds the only record of unmapped codes (see below) | Subscriptions CONFIRMED, customer use STATED |
| Internal portal data (internal consignment information service) and the customer care portal | The internal store gets the raw scan, the older shipment status without the visibility flag, and the exception status. The care portal API gets the raw scan and new-shipment announcements | No | Which portal reads which store, and what the care portal does with the scans `[??]`. Its source was not found | Subscriptions CONFIRMED by manifest and counters, use UNKNOWN |
| Claims | The raw scan. Its pod carries a mapper sidecar, so it probably maps the scan itself | No | What claims stores from a scan `[??]`. Its source was not read | Subscription CONFIRMED, mapper use STATED and INFERRED |
| Reporting | The shipment status, customer-visible variant only, and the exception status | No | For the status, it sees only what customers could see. It is not among the live readers of the raw scan | CONFIRMED |
| Legacy Firebird side | A legacy-shaped scan with the carrier's raw code in `carrCode` and the carrier's text in `scanText`. `isDelivered` and the deleted flag are fixed to false | No | The group never reaches Firebird. Firebird derives its own integer status from the raw code, and unknown codes become 207. Who writes these scans in production is unknown `[??]` | CONFIRMED for the shape and the procedures (a December 2025 dump, not live), UNKNOWN for the writer |

Firebird is the legacy shipment database. [Shipment Journey Through ECM](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354975746) explains it. The webhook is covered in [Tracking Webhook Services](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353533985).

## What one event contains

### A carrier scan

The scan is published as one message per scan (`raw_tracking.v1`). The message is JSON in camelCase and omits null fields.

| Field | What it holds |
| --- | --- |
| `id` | The event id. The publisher mints it, so it is not the carrier's id |
| `statusCode`, `statusDescription` | The carrier's own code and text. Nothing enumerates them |
| `reportedDate`, `isReportedDateLocalizable` | The time the carrier reported, with its offset, and a flag for whether it can be localised. A null flag is published as true |
| `receivedDate` | The time GFS received the scan |
| `location` | `countryCode`, `lat` and `long` |
| `depot` | `name` |
| `signatory` | `name` |
| `delivery` | The delivery window: `scheduledDate`, `from` and `to` |
| `additionalData` | A free-form dictionary a connector may fill |
| `rawData` | The carrier's whole response for the poll. Every scan from that poll carries it |
| `parcel` | The parcel identity: `shipmentId`, `shipmentIdV2`, `carrier`, `carrierV2`, `consignmentNumber`, `parcelNumber`, `serviceCode`, `contractNo` and `company` |

Status: CONFIRMED. The `id` field is missing on a manual mark-as-delivered scan.

### What the mapped scan adds

A mapping lookup (carrier, code and a text pattern, held in the spreadsheet) attaches GFS meaning to the scan. GFS stores the result and does not publish it with the scan.

| Field | What it holds |
| --- | --- |
| `code`, `text` | The GFS code and text. They replace the carrier's code and text. The text is the carrier's if the mapping row says so |
| `groupId` | The group, a free string |
| `isDelivered` | A delivered flag from the spreadsheet |
| `isVisibleToCustomer` | Whether customers may see the event |
| `exceptionStatus` | A red, amber or green status: `id` (RED 200, AMBER 100, GREEN 0) and `priority` |
| `isUnmapped` | True when no mapping row matched |
| `date` | The reported time, with the offset dropped |

Status: CONFIRMED. The raw carrier code stays on the stored raw scan only.

### The shipment status

GFS derives one status per shipment. Within each parcel, the scan with the highest group precedence wins, then the latest date. The winners are then collapsed across parcels. The status is published as `{ shipmentId, trackingStatusV2 }`.

| Field | What it holds |
| --- | --- |
| `date` | The reported time of the winning scan |
| `text`, `code` | The GFS text and code |
| `groupId` | The group |
| `isVisibleToCustomer` | Whether customers may see the status |
| `eta` or `signatory` | `eta` (`from`, `to`, `scheduledDate`) on every group except the two delivered ones. `signatory` only on `DELIVERED` and `PARTIALLY_DELIVERED` |

Status: CONFIRMED. A new status is calculated one window after a shipment's last scan. The default window is 60 seconds and the prod value was not checked `[??]`. The status is published in two variants: all events, and customer-visible events only. A separate message carries the red, amber or green exception status for the shipment.

## Where the records disagree

| # | Disagreement | In delivery terms | Status |
| --- | --- | --- | --- |
| 1 | Delivered has two sources | The mapper's delivered flag (`isDelivered`) and the group `DELIVERED` both come from the same spreadsheet row. The flag feeds the webhook and some clean-up. The group feeds the parcel state and the shipment status. Nothing asserts they agree | CONFIRMED that two sources exist. That they differ in production: UNKNOWN |
| 2 | The manual delivered scan is incomplete | A manual mark-as-delivered creates a scan with no `id` and no `parcel.company`. The webhook drops it for the missing company. The customer and internal stores skipping it is STATED by the vault and was not read. Whether the spreadsheet has a row for its code `GFS_DELIVERED_EVENT` is unknown `[??]` | CONFIRMED for the missing fields |
| 3 | The group list is a free string | A spreadsheet sets the groups and nothing in production enforces the list. The check exists in code and runs only when a setting is present. No production manifest searched sets it | CONFIRMED that no searched manifest sets it, STATED that production leaves it unset |
| 4 | Unmapped codes look mapped | An unmapped code becomes `IN_TRANSIT`, visible to customers, with the carrier's own text. The `isUnmapped` flag is ignored by the webhook. Only one consumer reports unmapped codes | CONFIRMED |
| 5 | The scan carries the raw code only | The mapped result is not published with the scan, so every consumer maps again, and each freezes the mapping in force when it saw the scan | CONFIRMED for the polling service, the shipment status calculation, the webhook and the manual-delivery service. STATED for the others |
| 6 | The webhook docs disagree with the code | The docs list `carrier`, but the code sends `carrierName`. The docs omit `carrierEventTime`. The docs call `gfsId` a string, while GFS stores the shipment id as an integer | CONFIRMED |
| 7 | A later deletion may never be recorded | A shipment deleted after creation and re-announced as an update does not flip an existing parcel to deleted in the code read. What event type a deletion arrives as is unknown `[??]`. This is a risk to check, not a confirmed bug | CONFIRMED that the path returns early, INFERRED that deletions are missed |
| 8 | Reported time is carried inconsistently | The scan keeps the offset. The mapped scan drops it. The shipment status carries it as a string. The legacy scan converts it to London time | CONFIRMED |

## What MPK 355074077 got right and wrong

The page is [Tracking Events and Webhooks: What v1 Needs](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/355074077). The table checks its claims against code.

| Claim | Verdict |
| --- | --- |
| The polling service publishes the raw scan and throws its own mapping away | Right. The mapping is stored, not published |
| Each publisher mints its own event id | Right, for the polling service, the Royal Mail webhook and the file import |
| No ordering key on raw scans, only on the shipment status | Right |
| Unmapped becomes IN TRANSIT, and only one consumer reports unmapped codes | Right |
| The manual delivered scan has no id and no company | Right. That the customer store, internal store and claims drop or store it was not read |
| The webhook body lacks event id, status code, delivery window, location and signatory | Right |
| "ECM keeps the raw code beside the derived status. Every event carries both." | Partly wrong as stated. The raw scan carries the raw code only. The mapped result stays in the parcel store and in each consumer's store, and is never published with the scan |
| Delivered has "at least six definitions" | Partly counted. The code shows four, plus the customer store's own re-derivation. The internal store was not read |
| GFS rates each shipment RED, AMBER or GREEN | Right |

## How ECM represents it today

This is the only section that leads with message and service names. [ECM Pub/Sub Topics](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/356155424) holds the topic detail and the verdicts, so this section does not repeat them.

| Shape | ECM representation | Status |
| --- | --- | --- |
| Connector result | A gRPC `ConnectorResponse` with repeated `TrackingEvent`, a `Status` and an `ErrorReason`. The status and error reason describe the call, not the parcel | CONFIRMED |
| Carrier scan | `raw_tracking.v1`, one message per scan. Four publishers: tracking-core, the Royal Mail webhook, the file processor and the shipment update service (manual delivered). No ordering key | CONFIRMED |
| Stored scan and mapped scan | The `ActiveParcel` document in the Mongo `active-parcels` collection, with `tracking.events` and `tracking.mappedEvents`, plus `trackingState` (IN_TRANSIT, DELIVERED, DELETED) and a bucket that is DELIVERED when `groupId` equals `DELIVERED`, otherwise IN_TRANSIT. The document expires on a time-to-live index | CONFIRMED |
| Shipment status | `shipment_tracking_status.v2`, ordered by shipment, with attributes `visibilityGroup` (`ALL` or `CUSTOMER_VISIBLE`) and `groupId`. An older `shipment_tracking_status` topic is obsolete | CONFIRMED |
| Exception status | `shipment_exception_status`, published on every window expiry, not only on change | CONFIRMED |
| Unmapped codes | `unmapped-tracking.v1`, from the customer store's mapper sidecar only | CONFIRMED |
| Customer webhook | An HTTP POST from connect-hooks. No topic. It reads `raw_tracking.v1` and maps the scan again | CONFIRMED |
| Legacy scan | `scanners.consignments.V1`, in the staging project | CONFIRMED for the topic and shape, UNKNOWN for the live writer |

tracking-core's own bucket and the shipment status come from the same deriver logic with different inputs. tracking-core sends only one parcel's mapped events and keeps only DELIVERED or IN_TRANSIT. The asynchronous deriver sees the whole shipment and adds `PARTIALLY_DELIVERED`, delivery windows and the two visibility variants (CONFIRMED).

## What a replacement would need to keep

Merak replacing ECM is only a hunch. These points describe what the sources show a replacement would have to carry or deliberately change.

- **A stable vocabulary of delivery stages**, with a named place where the list lives. Today a spreadsheet sets it and nothing enforces it.
- **One source for delivered.** Today the flag and the group can disagree in principle.
- **A shipment status derived across all parcels**, with partial delivery, a delivery window and the signatory.
- **Customer-visible and internal kept apart.** Today this is a flag on each scan and two variants of the shipment status.
- **The raw carrier code kept beside the GFS meaning**, on the event itself.
- **An id on every event, and what customers already receive.** Customers receive the webhook fields above and the `gfsId` shipment id. Any change to the display strings, such as showing attempted delivery, changes what they see.

## Not confirmed yet

- The production mapping spreadsheet: the full list of codes, groups and delivered flags `[??]`. The meanings of `OUT_FOR_DELIVERY`, `HELD_AT_BRANCH`, `AWAITING_CUSTOMER_COLLECTION` and `RETURNED` `[??]`.
- Who writes legacy scans in production, and what the on-premises Scan Injector does with them `[??]`. The Kubernetes patina service is configured to drop every real carrier. A Dataflow job's source was not found.
- The customer and internal consignment stores beyond two files, the claims service, and the proof-of-delivery service (gfs-pod). That includes which portals read which store.
- The Go filter enum in the consignment query service. The repository was unreachable.
- Whether the deployed images match the cloned shas. One deriver image tag could not be mapped to a sha.
- Whether any production subscription filters on the `groupId` attribute.
- The event type a deletion arrives as, and whether the webhook honours the visibility flag.
- The prod delivered polling settings and the prod window length `[??]`.
- The meaning of Firebird status 1003 (delivered or lost) and of the other legacy integers.

## Sources

Read on 10 Nov 2026. Short shas are the heads read that day.

| Source | Sha |
| --- | --- |
| tracking-core (ADO `fenghuang/tracking-core`) | `c081108` |
| tracking-mapper (GitHub `gfs-ecm`) | `44cfbf2` |
| shipment-tracking-status-deriver (GitHub `gfs-ecm`) | `a3dc446` |
| tracking-configuration-distribution-service | `bbd5e74` |
| connect, holding connect-hooks | `6c6d527` |
| shipment-update-service | `ccec388` |
| customer consignment information service (GitHub `gfs-ecm`) | `b2af452` |
| tracking-webhook-core (GitHub `gfs-hybrid-services`) | `254827c` |
| tracking-file-processor (ADO) | `e6da4bf` |
| tracking-patina-service (ADO) | `8edfb3e` |
| Production cluster manifests (ADO `prod-uk1-primary-cluster`) | `a317dc0` |
| ECM development docs (GitHub `gfs-ecm`), STATED only | `b2b67df` |
| Firebird procedures | December 2025 dump of central procedures, not live |

Related pages:

- [Tracking Events and Webhooks: What v1 Needs](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/355074077)
- [Tracking Webhook Services](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353533985)
- [Carrier Tracking and Proof of Delivery](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353206337)
- [Shipment Journey Through ECM](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354975746)
- [Shipment Identity](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/355631312)
- [ECM Pub/Sub Topics](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/356155424)
