This group answers how GFS follows a parcel after it ships. Which parcels does GFS chase, and when? How does news arrive? What does an update mean, and how does a delivery show up in the data? The most useful fact is that polling does almost all the work. It brought about 6.01M of about 6.29M events from about 142M carrier calls. The wait between polls of one parcel does not shrink as the parcel ages. Nothing central runs the steps after a scan is published. Each service reacts on its own.

Tags appear where the source research gives one. Volumes cover 23 Oct to 7 Nov 2026 (UTC, 15 days). The 142M figure was not re-run on that window.

## What is in this group

| Page | The question it answers | State |
| --- | --- | --- |
| [Chasing a Parcel: How GFS Decides What to Track and When](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/356614148) | Which parcels does GFS chase, when does it ask, what stops it, and what happens when a carrier does not answer? | Published draft, unverified |
| [What a Tracking Update Means: Events, Statuses and Delivery Outcomes](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/356614184) | What shapes does an update take, what statuses exist, and how is a delivery represented? | Published draft, unverified |
| [Carrier Tracking and Proof of Delivery](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353206337) | How do tracking and proofs of delivery get from carriers to customers, and which carriers have tracking? | Live |
| [Polling Connectors](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353697880) | How do the connectors poll carriers, which ones run, and what does polling cost? | Live |
| [Tracking Webhook Services](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353533985) | How do events that carriers push arrive, which carriers use it, and where does each cutover stand? | Live |
| [Tracking Events and Webhooks: What v1 Needs](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/355074077) | What would a v1 tracking API and webhook need, judged by where ECM falls short? | Published draft, unverified |

## What we know

- **CONFIRMED** `tracking-core` is a parcel store and a work-lease server. It has no scheduler, and connectors pull batches over gRPC.
- **CONFIRMED** The polling interval is one `TargetPollingMinutes` per carrier and state, with no age term. **UNKNOWN** Prod values sit in etcd and are unread.
- **CONFIRMED** Mongo deletes a parcel through a time-to-live index. Each new event resets its expiry, by carrier and status bucket.
- **CONFIRMED** A carrier error gets no retry and no backoff. Only a credentials error is acted on.
- **CONFIRMED** `tracking-core` publishes to `raw_tracking.v1` before it writes Mongo. A failure between the two republishes events with fresh IDs.
- **CONFIRMED** The bus carries no status enum. `groupId` is a free string set by a spreadsheet, and delivered is a `groupId` value, not a topic or message type.
- **CONFIRMED** The customer webhook folds `ATTEMPTED`, `HELD_AT_BRANCH` and `PARTIALLY_DELIVERED` into `IN TRANSIT`. A failed POST is logged and acknowledged, with no retry.
- Customer webhooks sent about 406k messages, which is 6.5% of events. The Royal Mail webhook published about 218k, and files added about 62k.

## Where to start

1. Chasing a Parcel, for what GFS tracks and when.
2. What a Tracking Update Means, for what comes back.
3. Carrier Tracking and Proof of Delivery, for coverage by carrier.
4. Polling Connectors, then Tracking Webhook Services, for the two main routes.
5. Tracking Events and Webhooks: What v1 Needs, for where ECM falls short.

## Not confirmed yet

- **Prod etcd values.** The interval, batch limit and expiry per carrier and state, and whether `DELIVERED` differs from `IN_TRANSIT`.
- **The effective expiry.** Prod sets 90 days as an environment variable. The code at the cloned commit does not appear to read it.
- **The mapping spreadsheet.** Nobody has read its codes, groups or delivered flags. It sets which groups exist.
- **Status 1003.** The Firebird procedures read it as delivered. Legacy UPS loss reporting reads it as lost. The two are unreconciled.
- **Royal Mail "about a third never matches".** The metrics show 21k of 343k unmatched and 146k held for retry. The claim is not reconciled with them.
- **Evri "keeps held events up to 90 days".** It is a read cutoff, and the TTL indexes are not confirmed. The recommended wording is "reads them for up to 90 days". It is not yet decided.
- **Owed correction, Polling Connectors.** It attributes the lease query to the connector. It is in `tracking-core`'s batch-creator. It also says the `fenghuang-tracking-core-config` ConfigMap is not in the cluster repo. Terraform defines it.
- **Owed correction, Tracking Events and Webhooks: What v1 Needs.** It says every event carries the raw code and the derived status. The raw topic carries the raw code only, and the mapped result stays in each store. Its "at least six definitions" of delivered is partly counted: four in code plus CCIS's own re-derivation, with ICIS unread.
- **Owed correction, retry wording.** "No retry or dead-letter handling" holds for polling only.
- **Owed correction, Connect webhook docs.** They list `carrier`, and the code sends `carrierName`. The docs omit `carrierEventTime`, which holds the received time.
- **Owed check.** No located page says polling slows with age or that tracking is orchestrated centrally. Whether any wording implies it is still to be checked.

## Related groups

- [Carriers and How We Integrate With Them](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/357629953) covers which carriers GFS uses and how data moves to and from them.
- [Proof of Delivery](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/357236740) covers the signatures and photos fetched from carriers on request.
- [ECM Platform: How a Shipment Moves Through It](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/357662721) covers the topics and identity behind the tracking flow.
- [1. Research into Existing Services](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/351502339) is the research root.
