ECM gives every shipment its own ID because a consignment number alone does not identify one shipment. Carriers do not guarantee uniqueness, and Selector sites reuse numbers, so the same number and carrier can come back for a different shipment. One service (`shipment-identity-service`) mints a number once, and every later ECM service joins on it. The ID is reliable for 30 days from first sight, not "forever" as the repo's design doc says.

This page explains why the ID exists, how it is made, where it stops working and what a replacement would have to keep. It is research for the Merak team, which has not chosen a design. Volumes cover the 15 days to 6 Nov 2026. The ID's place in the full path is on [Shipment Journey Through ECM](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354975746/Shipment+Journey+Through+ECM).

## In short

- **The natural key is consignment number plus carrier.** Carrier is already in it, so two carriers using the same number is not the problem.
- **The problem is reuse over time.** Per the service's design doc, customers wrap back to the start of their number range. A Selector site restore can also re-issue numbers on the same day. The doc says the rule to skip numbers after a restore is not enforced. These reasons are stated, not measured.
- **Without the ID, each service would repeat the date logic.** The credit and debit information service (CCDIS) already tries four matches in turn, then a hard-coded fix map of 13,398 entries.
- **The ID is a counter, minted on first sight.** It is stored beside the consignment number and carrier, and added to `shipments.v2` to make `shipments.v2.identified`.
- **It forgets after 30 days.** A shipment seen again after that gets a new ID. Tracking runs for about 90 days, so a live parcel can change ID part-way through.
- **Customers see it.** Webhook bodies carry it as `gfsId`, and Connect returns it. A replacement has to keep that.

## Why a consignment number is not enough

Customers hold a range of consignment numbers per carrier. When they use the range up, they start again. When a Selector site is restored from backup after a fault, numbers already used that day can be issued again. The documented process is to skip ahead after a restore, but the doc says it is rarely followed.

So the same consignment number and carrier can mean two different shipments, some days or months apart. Services downstream cannot tell them apart from the key alone. Before the identity service existed, each one had to carry its own date-based matching, and a change meant editing many services.

The clearest sign is invoice matching. CCDIS tries these in order: consignment number and carrier, then postcode, then despatch date, then a fix map. The map has 13,398 entries. Nothing on any page says why those entries were needed or when they were added.

The key leaves out the customer. Whether two customers can hold the same number for the same carrier is not known.

## How the ID is made

The service reads `shipments.v2`, adds the ID and publishes `shipments.v2.identified`. Every later ECM service is meant to read that topic, not the one before it.

| Step | What happens |
| --- | --- |
| 1. Look up | The service upserts a record keyed on consignment number and carrier, and adds the message ID to a list on it. A unique index on that pair backs the key. |
| 2. Mint | If the record is new, a second write sets its first-seen date and a new `shipmentId`. The ID is the next value of a counter in MongoDB. |
| 3. Drop repeats | If the message ID is already on the record, the service drops the message without publishing. |
| 4. Publish | The ID is sent with the shipment. A second ID, `shipmentIdV2`, is a hash of the carrier, consignment number and despatch date. It needs no storage. |

Two gaps follow from the code:

- **The mint is two writes, not one.** Two messages for the same new shipment, close together, can each see a record with no ID, and each mint one. The `tracking-webhook-core` README says two IDs can appear within milliseconds for one shipment. No test covers this against a real database.
- **A publish failure can lose the message.** If the service saves the record but fails to publish, the redelivered message is recognised as a repeat and dropped. This is read from the code and has not been run.

## How long an ID lasts

The record has a first-seen date that is set once. A MongoDB expiry on that date deletes the record after a set number of days. Later activity does not extend it.

- **The setting is 30 days** on the manifest we could read. That manifest predates the move to the new platform. The expiry on the live collection has not been checked, because the service skips creating an index that already exists.
- **A shipment seen after expiry gets a new ID.** Nothing else deletes or reuses IDs.
- **Tracking runs for about 90 days,** so a parcel still live on day 31 can get a new ID the next time it is announced again. This is inferred.
- **The design doc describes a different rule.** It describes a date window of 90 days before and 7 days after delivery. The code does not implement it. The expiry appears to stand in for it.

Over the 15 days from 23 Oct to the end of 6 Nov 2026 (UTC), the service handled 1,589,233 shipment messages and minted 674,672 IDs. About 57.5% of messages (914,561) were re-announcements of a shipment it already knew. These figures come from the Datadog metrics `messages` and `ids_created`.

## Who uses the ID

Confirmed in code:

- **The shipment update service** stores shipments keyed on it.
- **The status deriver** stops with an error if a parcel has no ID.
- **The POD service** stores and serves proofs of delivery by it.
- **Tracking webhook services** look up the ID by consignment number and carrier, then stamp it on events. They pick one when more than one exists.
- **Customer webhooks and Connect** send it to customers as `gfsId`.
- **CCDIS** also uses it.

Stated on pages or in Terraform but not read in code: ICIS, claims, MQP and reporting.

Two earlier statements on these pages are too strong. Not every ECM store keys on the ID: the POD cache keys on carrier, consignment number and parcel. And ECM's own data-journey doc says the ID is never shown to end users, which the webhook and Connect code contradicts. There is no evidence that carriers or Firebird receive it.

## What a replacement has to do

These are options for the Merak team, not a recommendation.

- **A. Mint at label creation.** Make a UUID or similar when the label is made, and keep a lasting index from carrier and tracking number to ID. That removes the guessing, the expiry and the race. Carrier events that arrive with only a tracking number still need a lookup.
- **B. Keep inferring, for shipments Merak did not create.** Files and Slipway shipments arrive without a Merak label. This needs one atomic mint, a reliable way to publish after saving, and a window longer than the tracking period.
- **C. Hash the identifying fields.** Include customer and despatch date. It needs no storage, but breaks when the despatch date is missing or changes.

Whichever is chosen, it has to keep the `gfsId` that customers already receive.

This reading would be wrong if Merak creates every shipment, if number ranges are provably unique per customer, if the live expiry differs from 30 days, or if reused numbers no longer occur.

## Not confirmed yet

- **The live MongoDB:** the expiry value, and whether duplicate IDs exist.
- **The live manifest.** The repo's publish workflow still says "not deployed". One deployment record and live Datadog metrics show it running, and the code since the last publish has no source changes.
- **Why the 13,398 fix-map entries exist,** and when they were added.
- **Source of tracking-core, CCIS, ICIS and claims,** so their use of the ID is stated, not read.
- **Whether two customers can share a number on one carrier.**
- **No "multiple shipment ID" webhook logs in 14 days.** Either the case is rare, or those services do not log it.

## Sources

- **Service code and design doc:** `gfs-ecm/shipment-identity-service` at `7454a4e`: `src/data-access/shipment-repository.js`, `src/data-access/id-generator.js`, `src/init/index.js` and `Documentation/shipment-identity-service-index.md`.
- **Consumers:** the shipment update service, status deriver, POD service, `tracking-webhook-core`, `connect-hooks` and CCDIS.
- **Volumes:** Datadog application metrics for `shipment_identity_service`.
