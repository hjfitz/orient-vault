---
tags:
- system
- ecm
verified: '2026-11-11'
title: ecm — known context
---
# ecm: known context

What the MPK research left standing on 2026-11-09: the canonical figures, Harry's decisions, and every claim still unconfirmed. Sources are the handover [[Handovers/2026-11-09-merak-replacement-pages]] [1], the number reconciliation run that day [2] and, from 2026-11-10, the tracking research in [[Systems/ecm/tracking]] [3] and, from 2026-11-11, the Firebird trigger research in [[Systems/ecm/firebird-change-feed]] [5]. No interview. Figures marked `(snapshot …)` age out.

## Standing decisions (Harry, 2026-11-09)
- **Merak replacing ECM and Selector is an unconfirmed hunch.** It cannot be confirmed with Jack and Stef yet. The MPK pages say "a replacement" and leave the choice to the Merak team. Keep new wording hypothetical.
- **Merak is unannounced.** Keep the content in MPK, with no Slack. Do not anchor Merak pages on the Parcel Portal or its MKP gates.
- **No further pages are wanted.** Four were proposed and stay unwritten. Any future page stays research level, comprehensive and simple.
- **No security ticket.** Harry: "not my domain". Do not draft or offer one. Class-level notes from the research agents stay in the handover record, not re-checked.
- **DHL Parcel UK hand-off (CID-317, blocked) is dropped.** Harry: "not an us issue for now". Nothing was sent and nothing is owed.
- **Lucid diagrams are linked, not embedded.** Harry draws the Confluence whiteboards by hand.
- **Verification of the five draft pages was declined.** Do not run it unless he asks.
- **Page 2 keeps its link to "Idea: Developer promise" (349110455).** That is a recommendation. The decisions on that page stay with Stef.

## Canonical figures
The window is the 15 days from 2026-10-23 00:00 to 2026-11-07 00:00 UTC, which is "15 days to the end of 6 Nov". The reconciliation chose it because it is complete days that anyone can reproduce. Every disputed figure had been true for a different window, and the metrics move by up to 1% with the hour the window ends. The hub's first figures (6.25M and 215,319) match a run that ended about 2026-11-05 20:00 UTC. Source is Datadog application metrics. The identity service counts are `sum:<metric>{*}.as_count()` as one scalar over the whole window.

| Figure | Value |
| --- | --- |
| `raw_tracking.v1` total | about 6.29M (6,294,707) |
| Polling, Royal Mail webhook, files | about 6.01M, 218k, 62k |
| Royal Mail webhook: received, published, held for retry | about 343k, 218k, 146k |
| Evri webhook, in shadow: received, held for retry | about 563k, 59k. About 260k a week, none published |
| Unmapped codes published to BigQuery | about 11.6k, mostly Interlink (4,651), DPD (3,124) and UPS (2,412) |
| Customer webhooks sent | about 406k, which is 6.5% of events |
| New shipments (new IDs) | about 675k (674,672, `gfs.shipment_identity_service.ids_created`) |
| Shipment messages handled by the identity service | about 1.59M (1,589,233, `gfs.shipment_identity_service.messages`). Re-announcements are 914,561, which is 57.5%. An earlier page draft said 1,644,519 messages and 713,297 IDs (56.6%): that was the 15 days to about 21:00 UTC on 9 Nov, not this window |
| Nine mocked carriers | about 587k events, 9.3% |
| Evri, DHL Parcel UK, DPD Local, DPD | about 5.59M events, 88.8% |
| Hosted Selector VMs | 278, backing 259 sites (snapshot 2026-08-06). About 1,000 sites are registered |
| Bill-on-scan contracts | 1,309 (Billing space) |

**Not re-run on this window, so the wording stands:**
- 5.44M new events and 142M carrier calls.
- The file processor's 54k, 12.4k errors and 7.0k retried.
- 24.6k Evri and 21.0k Royal Mail unmatched, and the Royal Mail 21k never matched.
- The per-carrier POD traffic figures.

About 24 calls per event still holds: 142M over 6.01M is 23.6.

## Settled facts: tracking (2026-11-10)
Read in code at `tracking-core` `c0811087`, in prod manifests at `a317dc0` and in Terraform at `e3c6dd9`. Detail and evidence are in [[Systems/ecm/tracking]].
- **CONFIRMED** `tracking-core` is a parcel store and a work-lease server. It has no scheduler, and connectors pull batches over gRPC.
- **CONFIRMED** The polling interval does not shrink with parcel age. Code holds one `TargetPollingMinutes` per carrier and state. The hypothesis is falsified in code. Prod values are still unread.
- **CONFIRMED** The Mongo `FindOneAndUpdate` that leases a parcel is in batch-creator, not in the connector.
- **CONFIRMED** Expiry is set in `ConsignmentHandler.cs` and refreshed in `TrackingStatusManager.cs` on each new event, by carrier and status bucket. A TTL index deletes the parcel. `ActiveParcelDomain.cs` holds no expiry logic.
- **CONFIRMED** `tracking-core` publishes to `raw_tracking.v1` before it writes Mongo. A failure between them republishes events with fresh IDs.
- **CONFIRMED** Failures other than credential errors are ignored, and the parcel waits another interval.
- **CONFIRMED** A parcel's bucket is `DELIVERED` when the deriver's `groupId` equals `DELIVERED`, and `IN_TRANSIT` otherwise. `tracking-core` calls the deriver over HTTP to get it.
- **CONFIRMED** The chain after `raw_tracking.v1` is choreography through Pub/Sub topics. Terraform is the only central artefact.
- **CONFIRMED** The bus carries no status enum. `groupId` is a string set by a spreadsheet. The mapped event is stored but never published, so each consumer maps again.
- **CONFIRMED** The `fenghuang-tracking-core-config` ConfigMap is defined in Terraform (`modules/fenghuang-scanning-core/main.tf`), not missing.
- **CONFIRMED** The inbound `shipments.v2.identified` subscription has a dead-letter topic after 10 attempts, and the Evri interim topic has one after 5. The earlier "no dead letters" is true of polling only.
- **CONFIRMED** `tracking-core/agents.md` is wrong. It says Node.js, and it names subscriptions the code does not use. Do not cite it.

## Settled facts: topics (2026-11-10)
Read in the prod Terraform (`gfs-ecm-prod-uk1`, master `35b545ce`) and the prod cluster manifests (`a317dc0`), with Datadog counters for 41 topics. Detail is in the published page MPK 356155424 (source [[Handovers/2026-11-09-merak-replacement-pages.page7-ecm-topics]]) and the map [[Handovers/2026-11-09-merak-replacement-pages.topic-usage-map]] [4].
- **CONFIRMED** Prod Terraform creates 70 topics and 145 subscriptions. The earlier catalogue listed 41 topics. The vault's count of 144 subscriptions was not recounted.
- **CONFIRMED** Verdicts, from code and manifests: LIVE 42, CONSUME-ONLY 9, PUBLISH-ONLY 8, UNKNOWN 5, ORPHAN 3, UNDEPLOYED 3. Datadog traffic is shown beside a verdict and does not change it.
- **CONFIRMED** `tracking.v1` is dead. Terraform, the manifest and the docs wire it, no code publishes it, and no code reads the subscription's env key.
- **CONFIRMED** `legacy_tracking.v1` is off in prod. The manifest sets the publish flag false by default, with no per-carrier override, and no subscription exists.
- **CONFIRMED** `raw_tracking.v1` has 15 subscriptions in the prod project and 8 running consumers. The Kubernetes tracking-patina-service runs with `CARRIERS=NONE` and drops every event, so its counter of 6,294,707 counts drops. The earlier "10 of 15" in the tracking note was wrong.
- **CONFIRMED** Datadog has no Pub/Sub metrics for the ECM prod project. Backlog, oldest unacknowledged age, acknowledgements and dead-letter counts are not measured. Traffic figures are the services' own handled or published counters.

## Settled facts: Firebird triggers and the change feed (2026-11-11)
Read in Selector's `V4-Server-Database` at `82dde6b` (an October 2023 snapshot, so production may differ) and `V4-Server-UploadServer` at `5773b8e`, with Datadog for 2026-10-23 to 2026-11-07 UTC. Detail and evidence are in [[Systems/ecm/firebird-change-feed]] [5].
- **CONFIRMED** Selector's source holds 16 triggers on `SHIPMENTS` and 10 on `SHIP_PIECES`. They cascade status, queue notifications, write history and feed the web-scanner queue. No later script drops any of them.
- **CONFIRMED** `SHIPMENTS_AI2` posts the Firebird event `UPLOAD_2_GCP` after every shipment insert, and `RELOAD_PUBLISH_SHIPMENTS_AI` posts `RELOAD_2_GCP`. `TRANSFER_QUEUE` appears nowhere in the source.
- **CONFIRMED** Scripts switch triggers on and off in production (`ALTER TRIGGER ... INACTIVE`), so the snapshot is a lead and not a record.
- **CONFIRMED** Uploads call `REG_SHIPMENTS` and `REG_SHIP_ITEMS`. A new consignment gets a plain `INSERT`, so every after-insert trigger fires. A repeat upload does not update `SHIPMENTS` in the branch read.
- **CONFIRMED** The Firebird Transfer Service is live in production: 3,022,807 rows in 15 days, 1,715,298 of them `shipments`, with one monitor set and no insert, update or delete split.
- **STATED** The push to Pub/Sub starts from the main Firebird, not from Client4, CSS or a site database (a Selector team member, 2026-11-04, paraphrased).

## Unconfirmed
Each item has a source that says one thing and a source that says another, or no source at all.

**Figures that disagree**
- **306 against 278 VMs.** 278 is the 2026-08-06 Tech Services snapshot. About 306 is in the 4 Nov Deep Dives artifact. 306 less the 79 stopped VMs is 227, which matches neither. Needs `compute.instances.list` on `gfs-cloud-selector-prod-uk1`, which is denied.
- **142M carrier calls against about 114M polls.** The Polling Connectors table sums to about 114M, and the Journey page says 115M parcel polls. Nobody has reconciled them. They may be different measures.
- **DPD Europe proxy: dormant, or live.** Logs show 21 failures in 15 days. The proxy's own metric shows about 710 requests (about 330 a week) with 5% errors. Whether they are real labels is not confirmed. Logs older than 15 days are gone.
- **Royal Mail "about a third never matches".** The metrics give 21k of 343k unmatched and 146k held for retry. The claim is not reconciled with them.

**Claims with no evidence yet**
- **Which parcel callers ask for on the v2 POD route.** The service does not pick the delivered parcel for DPD Local. Who does is open.
- **The live billing timetable.** Each customer has its own schedule. Which run program is live, and whether split runs are on, is open.
- **Whether the `shipment-identity-service` repo matches the deployed service.** Largely settled: the GitHub repo at `7454a4e` has one publish run and no source change since, and Datadog shows the service live. Still open: the live Mongo expiry value (init skips an existing index), whether duplicate IDs exist, and the live manifest (the publish workflow header still says "not deployed").
- **Why the invoice-matching service carries a 13,398-entry fix map,** and when it was added. Stated by the identity research, not on any earlier page.
- **Whether two customers can hold the same consignment number on one carrier.** The identity key leaves out the customer.
- **Whether a live parcel changes ID at day 31.** Inferred: the expiry is 30 days and tracking runs about 90.
- **Source of CCIS, ICIS, claims-service, the Scan Injector, the Transfer Service and `gfs-modernizer`,** so how they use the ID is stated, not read. `tracking-core` itself was read on 2026-11-10 (see Tracking, below).
- **The "12 mocked carriers" row on How Carriers Feed ECM.** Its table has 12 rows. Amazon SFP is not resolved, and Veho and Exelot sent nothing.
- **The DHL Express POD module claim.** Page 5 says the module is not loaded and does not work. The cleanup pass did not re-check it.
- **Nightline.** The Selector Interface page says Nightline. Four pages name only Nightfreight. They are two carriers, so those pages cover only one.
- **Evri "keeps held events up to 90 days".** It is a read cutoff, and the TTL indexes are not confirmed. Recommended wording: "reads them for up to 90 days". Harry has not decided.

**Answers owed by others**
- **The production Firebird triggers on `SHIPMENTS` and `SHIP_PIECES`, narrowed on 2026-11-11.** Selector's source triggers are read, at `82dde6b`. Still missing: the text of every `TRANSFER_QUEUE` trigger, the roughly nine extra production triggers on `SHIPMENTS` (about 25 on Test against 16 in source) and any extra on `SHIP_PIECES`, and whether `SHIPMENTS_AI2` and the queue triggers are active. The read-only queries in [[Systems/ecm/firebird-change-feed]] settle it.
- **Which carriers `patina-service-2` writes back,** and which carriers hold the 1,309 bill-on-scan contracts. The list is ADO variable group `gfs-patina-service.prod` (Library id 141), which the ADO MCP cannot read.
- **Who runs `CHECK_SHIP_STATUS`,** and which host runs the Scan Injector. Datadog shows `MEDC-APP-01-P`. SRE-126 confirmed `MEDC-APP-12-P`.
- **What the deployed mark-as-delivered code writes.** The default of 1003 is read from code, and legacy UPS loss reporting reads 1003 as lost. Nobody owns the write-back.
- **Whether DataBridge writes Slipway's masked billing export into Firebird in production.**
- **Evri code-mapping coverage before the CID-315 cutover.**
- **Whether any n8n workflow calls a carrier API.**
- **Live GCP state:** cross-project grants, the warehouse subscription and `tracking-dump@`.
- **Whether Client4's SOAP upload carries a file or shipment records.**

**Firebird triggers and change feed (2026-11-11)**
- **The text of every `TRANSFER_QUEUE` trigger.** STATED by the Tech Services vault (a metadata read of the Test replica) and Confluence 206274620, and in no readable source. The likeliest home is the Firebird Transfer Service repo's `sql/` folder (ADO project GFS Legacy Migration, commit `8569227`), which the ADO tools could not reach.
- **The Transfer Service's delete capture, ordering, batching and resume,** and its live config: tables, topic names, project, poll interval, batch size.
- **`GFSPublisher`.** STATED by the vault as the listener for `UPLOAD_2_GCP` (ADO repo `V6`). Its code is unread, and Datadog shows no `gfs.legacy-publisher.*` metric and no indexed log, which does not prove it is stopped. Whether it runs beside the Transfer Service is open.
- **Which feed produces `fb.shipments.v1`.** ASSESSED as the Transfer Service: five small tables match the modernizer's counts exactly (carriers 36, customers 36, contracts 420, contract services 458, products 43). No Pub/Sub topic metric exists for `fb.*`, so the topic's own volume was not measured.
- **The 11% gap.** The modernizer received 1,906,654 shipment messages against the Transfer Service's 1,715,298. INFERRED, not shown: Slipway's direct publish to `fb.shipments.v1` explains part of it.
- **The 1.8 updates per new shipment.** STATED by an earlier session from `sql/4_fts_doppelganger_updates_3.sql`, not re-read. Upload alone does not update `SHIPMENTS`, so the updates are ASSESSED as later status writes that pass an unread filter.
- **Delete handling.** Whether a delete, replace or rename reaches `fb.shipments.v1` as a DELETE. `delete from shipments` appears only in the swap-consignment branch of `REG_SHIP_ITEMS`.

**Tracking (2026-11-10)**
- **Prod etcd values.** `targetPollingMinutes`, `batchLimit`, `intervalSeconds` and `expiryDays` per carrier and state, and whether `DELIVERED` differs from `IN_TRANSIT`. `etcdctl get --prefix connectors:` settles it.
- **Whether prod runs master.** The prod image `tracking-core:prod-44693` and the deriver sidecar `prod-53270` map to no git sha. Three prod env vars have no binding at `c081108`: `GetNewTrackingV2Enabled`, `UseGetNewTrackingV2` and `TrackingStatusV2Enabled`.
- **The `ExpiryDays` binding.** Prod sets `ActiveParcel__ParcelOptions__default__ExpiryDays=90`, and the code binds only the `Connectors` section. The effective expiry per carrier and bucket is open. The spread of `expiryDate - createdDate` in Mongo settles it.
- **`Gfs.Core.PubSub` publisher.** Whether it adds an ordering key or attributes to `raw_tracking.v1`. The NuGet package was not read. The topic map found no ordering on any `raw_tracking.v1` subscription (Terraform, CONFIRMED).
- **The prod mapping spreadsheet.** Its codes, groups and `isDelivered` values, whether `VALID_GROUP_IDS` is set, and whether any prod subscription filters on the `groupId` attribute.
- **Who writes legacy scans in prod.** The Kubernetes patina service runs but drops every event (`CARRIERS=NONE`, CONFIRMED on 2026-11-10). The Dataflow job's source and `patina-service-2` were not found. The research files disagree on the label: one marks the `patina-service-2` flow CONFIRMED from its README and a Terraform comment, the other marks the prod writer UNKNOWN. This note keeps the flow as stated and the writer as unknown.
- **What the Scan Injector does** with `scanners.consignments.V1`, and whether the Dataflow write-back sends one state per message or one aggregate per session window.
- **The staging project.** `scanners.consignments.V1` sits in `gfs-ecm-staging`. Its own Terraform, subscription and dead-letter setup were not seen.
- **CCIS, ICIS, claims-service and `gfs-pod`** beyond the two CCIS files read. The Go filter enum in `consignment-query-service` was unreachable.
- **Whether deployed images match the cloned shas.** That covers `tracking-core`, the deriver, `connect-hooks`, and the Royal Mail webhook (the standalone repo at `3c880bf`, with a move into the monorepo in a PR).
- **Deletion after creation.** A deleted consignment re-announced as an `UPDATE` does not flip an existing parcel to `DELETED`, because the handler returns first. This is a risk, not a confirmed bug. The event type a deletion arrives as is unknown.
- **Live GCP topic state.** The reports used Terraform and manifests only, with no GCP access. The first read used a Terraform clone 15 months old. The topic map of 2026-11-10 used master `35b545ce`, and also had no GCP access.
- **Which of `parcel.carrier` and `parcel.carrierV2` holds the numeric ID.** The ECM catalogue and the simulator header disagree, and every type is a string.
- **Smaller gaps.** The `untracked` list contents. Which carriers fill `additionalData`, a failure reason or a delivery window. The `getMapping` function body. How many prod env vars are dead.

**Topics (2026-11-10)**
- **The on-prem Firebird Transfer Service's deployed config.** Every `fb.*` publisher rests on it. The repo config names `fb.<x>.v1.prod` in project `gfs-ecm`, while prod Terraform creates `fb.<x>.v1` in `gfs-ecm-prod-uk1`. Nine topics have a running consumer and no readable publisher, and Datadog shows traffic on three of them, so a publisher exists that no repo shows.
- **Source for ccp-api, the oz gateway, longmen, the CS bot, the report-scheduler and the Cloud Run route-validation-import service.** Also the invoice translator's host, and what the CS bot is.
- **Whether the cluster repo matches the cluster.** The local manifests clone is at `a317dc0` and remote master is at `b7e16c7`. Image tags may differ, and the cluster was not read.
- **The subscription count.** 145 in the prod Terraform against the vault's 144. Which one is missing is unknown.
- **Datadog gaps.** Topics outside the 41 queried were not measured, apart from nine seen in passing. The push subscriptions in `gfs-selector-rest-prod-uk1`, `patina-service-2` in prod, data-warehouse, longmen, tracking-mapper and parcel-eta-service are not measured. Several counts name a topic by inference from a metric or subscription name.
- **Whether gfs-modernizer publishes to `tracking-events.v2` and `customers.v2`.** The env vars are set and no subscription exists.
- **Message shapes not read:** `windowed-shipments-parcels`, `shipment-number-updates`, `tracking-events.v2`, `customers.v2`, `ticket-actions`, `report-run`, `route_validation_import.v1`, `connect.usage_notifications.v1` and the claims topics other than `claims.v1`. Also the call sites of most claims publish functions and of the CCDIS publish to `invoiced_shipments_published.v1`.
- **Ack and nack behaviour** of the shared subscriber library in each image. Whether `shipment_tracking_status.v2` ordering is honoured on publish, because the deriver's client is built without publisher options.
- **Whether Flux applies the `carrier-cs.yml` manifest,** given its `.yml` extension.
- **Whether the BigQuery write on `cs.bot.logs.*` has the rights it needs.** Terraform shows two subscriptions on each of the ticket and exception topics but describes one.
- **The parcel-eta-service history.** The repo says retired 2026-07-27. An earlier finding said 0 replicas since 2022.
- **Topics outside the prod Terraform,** in staging, dev, playground and finance-dev, and the staging module internals.

## Owed
- Harry deletes three Confluence pages by hand: Carrier Services (353468499), Day End and Billing Handoff (353566845) and a scratch draft (355565572).
- Harry's feedback on the five draft pages. Apply it to the live page first, then the vault copy.
- The `orient-writers` skills `plainly` and `c4-diagrams` are uncommitted.
- Retest the Lucid macro on Confluence once the admin installs the app.
- Someone with GCP access lists subscriptions and backlogs for `gfs-ecm-prod-uk1` (`gcloud pubsub subscriptions list`; Cloud Monitoring).
- Someone with Firebird admin access runs the read-only trigger queries in [[Systems/ecm/firebird-change-feed]]. Harry decides who is asked. Nothing has been sent.
- Access to the ADO repos GFS Legacy Migration (Firebird Transfer Service, `sql/`) and `V6` (`GFSPublisher`). The ADO tools could not reach either on 2026-11-11.
- **Owed corrections to MPK pages, for Harry (Confluence not edited).** These findings contradict or soften:
  - *Polling Connectors* (353697880) attributes the `FindOneAndUpdate` to the connector. It runs in batch-creator.
  - *How Carriers Feed ECM* (355074111) says polling has "no retry and no dead-letter queue". That holds for polling. The inbound `shipments.v2.identified` subscription has a dead-letter topic after 10 attempts. It also says "a parcel expires after 90 days", and the expiry resets on each new event, by carrier and bucket. The 90 is not confirmed.
  - *Selector and ECM Coupling* (354418743) and *Shipment Identity* (355631312) say tracking stops or runs about 90 days after the last new event. Same softening.
  - *Tracking Events and Webhooks* (355074077) says every event carries the raw code beside the derived status. `raw_tracking.v1` carries the raw code only, and the mapped result stays in each store. Its "at least six definitions" of delivered is partly counted: four in code plus CCIS's own re-derivation, with ICIS unread.
  - The MPK sentence "no retry or dead-letter handling" holds for polling only (the research read 353697880 and 353206337 and does not say which carries it). The MPK claim that the `fenghuang-tracking-core-config` ConfigMap is missing from the cluster repo is wrong: Terraform defines it.
  - The Connect webhook docs list `carrier`, and the code sends `carrierName`. The docs omit `carrierEventTime`, which holds the received time.
  - *Tracking pages 356614148 and 356614184* (10 Nov 2026) state three items as open that the lists above carry too. The delivery group list lives in a spreadsheet in Google Cloud Storage that nobody read. Firebird status 1003 is read as delivered by the procedures and as lost by legacy UPS loss reporting, and the two are unreconciled. Prod etcd polling values are unread.
  - No page located says polling slows with age or that tracking is orchestrated centrally. Harry to check whether any wording implies it.
- **Waypoint contradictions (not edited, owed to the Waypoint owner).** In `Engineering/tracking-core/`: `architecture.md` G2 and `overview.md` say a parcel expires after 90 days. The expiry resets on each new event, and other exits exist (`DELETED` key off, the `untracked` list, credential pause). `architecture.md`'s action says "no retries or dead letters", true of polling only. `overview.md` says "up to 100 parcels", which is the C# default, and the prod value is in etcd. `known-context.md` says the ConfigMap is not in the cluster repo. `waypoint.yaml` and `overview.md` point readers at `agents.md`, which is wrong.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "doc", "ref": "Handovers/2026-11-09-merak-replacement-pages.md" },
  { "id": 2, "kind": "doc", "ref": "Session scratchpad numbers-canonical.md, 2026-11-09 (Datadog metrics via execute_code; not in the vault)" },
  { "id": 3, "kind": "doc", "ref": "Systems/ecm/tracking.md and Handovers/2026-11-09-merak-replacement-pages.tracking-core-findings.md, ...tracking-topic-catalogue.md, ...tracking-model-findings.md (2026-11-10)" },
  { "id": 4, "kind": "doc", "ref": "Handovers/2026-11-09-merak-replacement-pages.topic-usage-map.md and ...topic-datadog-usage.md (research copies, 2026-11-10); Confluence MPK 356155424 ECM Pub/Sub Topics (draft, unverified)" },
  { "id": 5, "kind": "doc", "ref": "Systems/ecm/firebird-change-feed.md; Handovers/2026-11-09-merak-replacement-pages.firebird-triggers-findings.md and ...firebird-feeds-datadog.md (research copies, 2026-11-11)" }
] }
```
