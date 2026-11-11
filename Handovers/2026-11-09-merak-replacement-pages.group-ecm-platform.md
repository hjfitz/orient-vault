This group answers how a shipment's information moves once Selector has created it. The most useful fact is where Selector and ECM meet. ECM learns of a shipment only after Selector uploads it into central Firebird and the Firebird Transfer Service publishes a create message. ECM does not make labels. From there it gives each shipment its own ID, rebuilds a status from raw carrier scans, tells customers and fetches proofs of delivery on request. Services react to Pub/Sub topics, and no central orchestrator runs at run time. Some pages name options for a possible replacement. No replacement is decided.

Tags appear where the source research gives one.

## What is in this group

| Page | The question it answers | State |
| --- | --- | --- |
| [Shipment Journey Through ECM](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354975746) | How does one shipment travel from label to proof of delivery, and what can change it on the way? | Live |
| [Selector and ECM Coupling](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354418743) | Where do Selector and ECM meet, what breaks if either goes first, and what duties does nobody document? | Published draft, unverified |
| [Shipment Identity: Why ECM Gives Each Shipment Its Own ID](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/355631312) | Why does a consignment number not identify a shipment, how is the ID made, and how long does it last? | Published draft, unverified |
| [ECM Pub/Sub Topics: Shapes, Producers and Consumers](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/356155424) | What does each of the 70 topics carry, who writes it, who reads it, and is it live? | Published draft, unverified |

## What we know

- The Journey page was corrected after a 31-agent review of 36 claims: 19 confirmed, 17 partly right, none refuted.
- Six seams carry the traffic: shipments, scans and status, manual changes, reference data, billing and identity. Firebird is the seam, and the pages describe it as a weak one.
- About 30 procedures write `STATUS`, and nothing in the Firebird feeds or procedures is versioned. Nobody has read the production triggers.
- The ID is a counter minted on first sight, keyed on consignment number plus carrier. The code sets it to last 30 days, and the live value is not read. A shipment seen later gets a new ID. Customers see it as `gfsId`.
- In the 15 days to 7 Nov 2026 the identity service handled about 1.59M shipment messages and minted about 675k IDs. 914,561 messages (57.5%) were re-announcements.
- **CONFIRMED** The prod Terraform creates 70 topics and 145 subscriptions. Verdicts: LIVE 42, CONSUME-ONLY 9, PUBLISH-ONLY 8, UNKNOWN 5, ORPHAN 3, UNDEPLOYED 3.
- **CONFIRMED** Datadog has no Pub/Sub metrics for the ECM prod project. Backlog, oldest unacknowledged age, acknowledgements and dead-letter counts are not measured.
- No direct Selector to ECM call exists. A search of the Selector repo found no Pub/Sub, `raw_tracking` or `tracking-core` reference.

## Where to start

1. Shipment Journey Through ECM, for the whole path.
2. Selector and ECM Coupling, for the seam with Selector.
3. Shipment Identity, for the ID that every later service joins on.
4. ECM Pub/Sub Topics, for the topic-by-topic detail.

Selector's own side is covered by [Legacy Selector](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/351764483).

## Not confirmed yet

- **Production Firebird triggers** on `SHIPMENTS` and `SHIP_PIECES`. One read-only query by a DBA settles it.
- **Whether the identity repo matches the deployed service.** Largely settled. Still open are the live Mongo expiry, whether duplicate IDs exist and the live manifest.
- **Whether two customers can hold the same consignment number on one carrier.** The identity key leaves out the customer.
- **Day 31.** Whether a live parcel changes ID then is INFERRED. The expiry is 30 days and tracking runs about 90.
- **Unread source.** CCIS, ICIS, claims-service, the Scan Injector, the Transfer Service and `gfs-modernizer` are unread, so their use of the ID is stated, not read.
- **The Transfer Service's deployed config.** Every `fb.*` publisher rests on it. Repo config and prod Terraform disagree on topic and project names.
- **Subscription count.** 145 in the prod Terraform against 144 in the vault. Which one is missing is unknown.
- **Who writes legacy scans in prod.** The Kubernetes patina service runs but drops every event. The writer is UNKNOWN.
- **Owed correction, Selector and ECM Coupling and Shipment Identity.** Both say tracking runs about 90 days after the last new event. The expiry resets on each new event, by carrier and status bucket, and the 90 is not confirmed.
- **Owed wording, Selector and ECM Coupling.** "Evri keeps them up to 90 days" could read as deletion. It is a read cutoff. The recommended wording is not yet decided.

## Related groups

- [Tracking: How GFS Follows a Parcel](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/357597186) covers how GFS chases a parcel and what an update means.
- [Proof of Delivery](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/357236740) covers the proofs of delivery that ECM fetches live.
- [Carriers and How We Integrate With Them](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/357629953) covers the carriers and the routes by which tracking arrives.
- [1. Research into Existing Services](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/351502339) is the research root.
