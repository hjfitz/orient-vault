GFS chases a parcel from the moment it knows the shipment. It adds the parcel to a tracked list. Then it either asks the carrier about it (polling) or waits for the carrier to send news (webhook or file). Chasing stops when the parcel is delivered and that carrier's delivered-state setting is off, or when the parcel expires. It can also stop in the other ways listed below. The wait between polls of one parcel is one number of minutes per carrier and parcel state. It does not shrink as the parcel ages. Nothing central runs the rest of the flow: once a scan is published, each service reacts to it on its own.

Polling does almost all the work. In the 15 days from 23 Oct to 7 Nov 2026 (UTC), polling brought about 6.01M events from about 142M carrier calls. That is about 24 calls per event. The 142M figure was not re-run on this window. The Polling Connectors page sums to about 114M polls, and nobody has reconciled the two. They may be different measures.

This page sets out the delivery behaviour: what GFS chases, when, what stops it, and what happens when a carrier does not answer. [ECM](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354975746) is named only as the way it is done today, in "How ECM does it today". ECM is the platform GFS runs tracking on now. The hypothetical replacement is only a hunch. Status tags: **CONFIRMED** (read in code, a manifest, Terraform or Datadog), **STATED** (a document says it), **INFERRED** (follows from code, not measured) and **UNKNOWN** (nothing settles it).

## Three ways news about a parcel arrives

A carrier's news reaches GFS by one of three routes. All three end up on the same raw scan feed (the `raw_tracking.v1` topic). They differ in who starts the exchange and who decides what is sent.

| | Polling | Webhook | Files |
| --- | --- | --- | --- |
| Who tells whom | GFS asks the carrier about each due parcel | The carrier sends each event to GFS as it happens | The carrier drops a file on its secure file server and GFS collects it |
| Who decides what is tracked | GFS. It picks the parcels | The carrier decides what it sends. GFS holds or drops what it cannot match to a shipment | The file decides |
| How fresh | Set by the polling interval for that carrier and state. Values are `[??]` | Delivery delay is `[??]` | GFS checks for new files every 20 minutes (STATED). The delay after that is `[??]` |
| Volume, 15 days to 7 Nov 2026 | About 6.01M events | About 218k published, all from Royal Mail. Evri sent about 563k and none were published, because its webhook runs in shadow | About 62k on the feed. The file processor counts 54k, plus about 7.4k on a separate error count |

- **CONFIRMED** Polling is the only route where GFS chooses the parcels. **STATED** A polled parcel comes from the tracked list, so it is already matched to its shipment.
- **STATED** A carrier that is polled and also sends webhooks feeds the raw scan feed twice, because nothing deduplicates across routes. Section "Where early or duplicate news goes wrong" covers why.
- **STATED** Evri is polled today. Its webhook records events but publishes none, so turning it on later does not backfill.

For the per-carrier detail, see [Polling Connectors](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353697880), [Carrier Tracking and Proof of Delivery](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353206337) and [Tracking Webhook Services](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353533985). For the topics behind each route, see [ECM Pub/Sub Topics](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/356155424).

## What gets chased

### How a parcel starts being tracked

The identity step announces each shipment once it knows it. The tracking service (tracking-core) reads that announcement and creates one tracked parcel for each parcel in the shipment. For the identity step, see [Shipment Identity](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/355631312).

- **CONFIRMED** A tracked parcel is keyed on parcel number and shipment ID. It starts in the state IN_TRANSIT, or DELETED if the shipment is marked deleted.
- **CONFIRMED** Three cases are skipped. The shipment has no parcels. The contract is on the `untracked` list. The announcement is an update for a parcel that is already tracked.
- **CONFIRMED** The tracked parcel is given an expiry date when it is created. The value comes from carrier and state settings, with a default.

### The three states

| State | How a parcel gets there | Polled? |
| --- | --- | --- |
| IN_TRANSIT | Where every new parcel starts | Yes, if the carrier's in-transit setting is on |
| DELIVERED | The latest derived status group is DELIVERED. The change is one-way | Only if the carrier's delivered-state setting is on |
| DELETED | The shipment was marked deleted when announced | Only if the carrier's deleted-state setting is on |

- **CONFIRMED** A status helper works out the state after each poll that brings news. The state is DELIVERED when the status group is DELIVERED, and IN_TRANSIT otherwise.
- **CONFIRMED** Each carrier and state has its own switch, so a delivered parcel is polled only while that switch is on. Amazon polled 2.6M delivered parcels in the window (STATED by Polling Connectors).

### Every way tracking ends

1. **Expiry.** **CONFIRMED** A database index deletes the parcel at its expiry date. Each poll that brings at least one new event, after filtering, resets the date to now plus a count of days. The count is set per carrier and state.
2. **Delivered, with the delivered-state setting off.** **CONFIRMED** The parcel moves to DELIVERED and is no longer leased for polling.
3. **DELETED, with the deleted-state setting off.** **CONFIRMED** Same effect, for a deleted shipment.
4. **The `untracked` list.** **CONFIRMED** A contract on the list is skipped when the parcel is created and again when a poll is handed out.
5. **Credential pause.** **CONFIRMED** Repeated credential errors pause polling for a contract. This is enabled for two carrier IDs in prod, 10 and 19, which Polling Connectors states are DPD and DPD Local. Section "When a carrier does not answer" has the detail.
6. **No new events.** **INFERRED** A parcel that brings no new event never has its expiry reset, so it ends at the date set when it was created.

Two points about expiry:

- **CONFIRMED** The expiry is reset by each new event, so the days run from the last new event, not from creation. Earlier research notes said a parcel stops only at DELIVERED with the setting off, or 90 days after creation. The code shows more exits than that.
- **STATED** The prod manifest sets 90 days through an environment variable. **UNKNOWN** The code at the version read does not appear to use that variable. The effective number of days per carrier and state is `[??]`.

One risk to note, not a confirmed bug. **CONFIRMED** (code path) A shipment may be deleted after tracking has started, with the news arriving as an update. The tracking service then returns before it marks the parcel DELETED. The parcel could then keep being polled. **UNKNOWN** Which kind of announcement a deletion arrives as is `[??]`.

## How often

The rule, in plain words:

- **CONFIRMED** Each carrier and state has one number, the target polling minutes. The connector for that carrier supplies it with each request for work.
- **CONFIRMED** A parcel is due when the time since it was last handed out for polling is longer than that number. Due parcels are served oldest first.
- **CONFIRMED** The time is stamped when the parcel is handed out, not when the carrier answers. A failed or slow poll still counts as a poll, so the parcel is not due again for one full interval.
- **CONFIRMED** There is no age term. The interval does not depend on creation date, despatch date, event count, last event time or poll count. It does not shrink as a parcel ages.
- **CONFIRMED** A parcel's interval changes only when its state changes, for example from IN_TRANSIT to DELIVERED. That uses a different setting. It is not a function of age.

It is natural to expect the interval to fall as a parcel ages. The code shows that it does not. The prod values sit in the configuration store and nobody has read them. A person could still have set the DELIVERED value shorter or longer than the IN_TRANSIT value. Polled data could then look age-shaped without any code deriving it from age.

How the loop runs:

- **CONFIRMED** A connector runs one loop for each carrier and state that is switched on. The loop asks the tracking service for a batch of due parcels, then calls the carrier for every parcel in the batch in parallel.
- **CONFIRMED** If the batch was full, the loop asks again at once. Otherwise it waits 30 seconds. After an error it waits 60 seconds. These are code defaults, and prod overrides are `[??]`.
- **CONFIRMED** The code default batch size is 100, although a comment in the code says 1000. The prod value is `[??]`.
- **CONFIRMED** The configuration service allows target polling minutes up to 9999, so the limit is effectively unbounded.

Two effects follow from the code, and neither has been measured:

- **INFERRED** A new parcel has no last-polled time. MongoDB sorts a missing value first, so a new parcel should be polled soon after it is created. This is the opposite of a back-off. The sort order was not tested.
- **INFERRED** The real gap between polls can be longer than the target. When more parcels are due than one batch can drain, the oldest go first. The gap then becomes the time the queue takes to cycle.

What would settle the unknowns: read the prod configuration entries for target polling minutes, batch size, interval seconds and expiry days. Or sample the last-polled times of a few tracked parcels over time, and split the gaps by state and by parcel age.

## When a carrier does not answer

| Case | What GFS does | Status |
| --- | --- | --- |
| The carrier returns an error | Records a failed poll with a reason. There is no retry and no backoff | CONFIRMED |
| The failure is not a credentials error | Nothing is written. The parcel waits one more interval | CONFIRMED |
| A rate limit, such as a 429 | Treated as an ordinary carrier error. The whole batch is sent in parallel, and no throttle was found in the tracking service or its connector framework | CONFIRMED. A single carrier client could add its own throttle, and that was not checked per connector |
| The carrier returns no new events | Nothing is published and nothing is updated. The parcel waits one more interval. The interval does not change | CONFIRMED |
| A credentials error | A row is stored for four hours (the default). A contract with more than three rows is skipped when polls are handed out. Prod enables this for DPD and DPD Local only | CONFIRMED mechanism. The carrier names are STATED |
| The whole batch fails | The loop logs the error and waits 60 seconds (the default) before it asks again | CONFIRMED default |
| One carrier and state loop crashes | The loop logs an error and stops. Nothing restarts it until its settings change or the pod restarts | CONFIRMED by reading the code, not exercised |

- **CONFIRMED** Only credential errors are acted on. Every other failure is ignored and the parcel just waits another interval.
- **CONFIRMED** No rate-limit handling was found.
- **INFERRED** A credential pause ends when its rows expire after four hours, if the carrier's credentials are fixed. A carrier still failing would refill the rows.
- **CONFIRMED** This describes polling. News about a new shipment, read by the tracking service, is retried by the topic. After 10 failed attempts the message goes to a dead-letter topic. Terraform shows that setting.

## Where early or duplicate news goes wrong

- **Publish before store (CONFIRMED).** The tracking service publishes new events first and saves them second. If a failure falls between the two, the next poll finds the same events new and republishes them under fresh event IDs.
- **Each publisher mints its own ID (CONFIRMED).** The same scan from a connector and from a webhook gets two IDs. Consumers deduplicate on that ID alone, so both land.
- **No ordering key (CONFIRMED).** The raw scan topic carries no ordering key, and the events from one poll are published in parallel. **UNKNOWN** Whether the shared publishing library adds one.
- **Early scans wait for the shipment (CONFIRMED).** The Royal Mail webhook parks a scan until the shipment is known. That was about 146k of the 343k received in the window. The status service drops a scan for a shipment it has not stored, with no error.

## How ECM does it today

This is the only section that leads with service names. Everything above is behaviour. This section maps it to ECM.

- **One image, three roles.** **CONFIRMED** The `tracking-core` image runs as three deployments, chosen by a mode setting. Prod runs 3 replicas of each. `consignment-manager` creates tracked parcels from the shipment announcement. `batch-creator` hands out due parcels. `response-publisher` takes carrier results, deduplicates, publishes events and updates parcel state.
- **gRPC between connectors and tracking-core.** **CONFIRMED** Each connector runs the loops from "How often". It asks `batch-creator` for a batch over gRPC, a remote procedure call protocol. It streams results to `response-publisher`. No scheduler, timer or work queue exists in `tracking-core`.
- **etcd holds the settings.** **CONFIRMED** etcd is a key-value store. It holds the entries for each connector and state: switched on, carrier IDs, batch limit, interval seconds, error interval seconds and target polling minutes. The entry names are STATED by a configuration-service document, and their shape is CONFIRMED from test seeds. Prod values are `[??]`.
- **Two sidecars.** **CONFIRMED** The `response-publisher` pod runs `tracking-mapper` and `shipment-tracking-status-deriver` beside the main process. It calls them inside the pod. The deriver answer sets the DELIVERED or IN_TRANSIT state.
- **MongoDB store.** **CONFIRMED** The database is `tracking-core`, collection `active-parcels`. One index covers carrier, state and last-polled time, and serves the lease. A time-to-live (TTL) index on the expiry date deletes parcels. A second expiry field has its TTL index commented out, so it deletes nothing. The `untracked` list and the credential-error rows are also Mongo collections.
- **The lease.** **CONFIRMED** A MongoDB find-one-and-update in `batch-creator` picks the oldest due parcel and sets the last-polled time in one step. It is not in the connector. **INFERRED** Because the pick and the stamp are one atomic update, two workers should not be handed the same parcel.
- **Topics.** **CONFIRMED** `consignment-manager` reads `shipments.v2.identified`. `response-publisher` publishes `raw_tracking.v1`. A legacy topic is switched off in prod. The rest is on [ECM Pub/Sub Topics](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/356155424).

## What a replacement would need to keep

Hypothetical. Merak replacing ECM is only a hunch. These are behaviours the code shows, not a recommendation.

- Keep chasing delivered parcels for a period, to catch late scans and proof of delivery. Today a delivered parcel is polled while the carrier's delivered-state setting is on.
- Keep separate intervals for each carrier and each state, with the option to switch a state off.
- Keep the credential-failure pause, so a contract with bad credentials does not produce endless failed calls.
- Keep a lease that cannot hand one parcel to two workers.
- Keep expiry that is reset by new news, so a parcel with recent events stays tracked.
- Keep publishing idempotent. Pick an event ID that is the same on a republish, or accept duplicates.

## Not confirmed yet

- **Prod polling settings.** Target polling minutes, batch size, interval seconds and which states are switched on, per carrier and state. They are in the prod etcd. A read of the prefix settles them. Whether DELIVERED differs from IN_TRANSIT depends on them.
- **Prod expiry.** The effective days per carrier and state. The `ExpiryDays` variable is set to 90 in the manifest, and the code at the version read does not appear to bind it. The spread of expiry date minus creation date in Mongo would settle it.
- **Whether prod runs the code read.** The prod image `prod-44693` is not mapped to a commit. Three prod flags have no matching setting in that code.
- **Whether deployed images match the commits** read for the tracking service, the status deriver, the webhook services and the connect hooks.
- **Shared publishing library.** Whether it adds an ordering key or attributes to the raw scan topic. The package was not read.
- **Go filter enum.** The filter list in the consignment query service was unreachable.
- **Deleted shipment arriving as an update.** The code path is read. Which announcement a deletion arrives as is `[??]`. This is a risk, not a confirmed bug.
- **Batch size.** 100 in the code default, 1000 in a code comment. The prod value is in etcd.
- **Webhook delivery delay** `[??]` and **file delay after the 20-minute check** `[??]`.
- **142M calls against about 114M polls.** Open. They may measure different things.
- **Live Pub/Sub and cluster state.** The research read Terraform and manifests only. The Terraform read for the tracking service is from July 2025, and a later read of the prod project found the same subscription defaults.

## Sources

Research ran on 10 Nov 2026, read-only. Window for counts: 23 Oct 00:00 to 7 Nov 00:00 UTC, from Datadog application counters.

| Source | Version |
| --- | --- |
| `tracking-core`, Azure DevOps master | c0811087b8ed4dce4968bb8e9b985f6853f51a69 (8 Jun 2026) |
| Prod cluster manifests, `prod-uk1-primary-cluster` | a317dc0 (6 Nov 2026) |
| Prod Terraform, `gfs-ecm-prod-uk1` | e3c6dd9 (30 Jul 2025, tracking module) and master 35b545ce (topic map) |
| `connectors-configuration-api`, `docs/etcd-data-structure.md` | f3f089a (a document, not code) |
| Connector end-to-end seeds | Test values only, not prod |

| Claim | Evidence in `tracking-core` at c081108 |
| --- | --- |
| The lease and the due rule | `ActiveParcelRepository.cs:104-128`; `ActiveParcelDomain.cs:149` |
| Untracked and paused contracts skipped | `ActiveParcelDomain.cs:156-165` |
| Parcel creation, skip rules, first expiry | `ConsignmentHandler.cs:51-130` |
| State and expiry reset on new events | `TrackingStatusManager.cs:33-69` |
| Bucket is DELIVERED when the group is DELIVERED | `RemoteTrackingStatusV2Getter.cs:63` |
| TTL index on expiry date; second expiry index commented out | `ActiveParcelRepository.cs:237-245` |
| Expiry days read from the `Connectors` section | `Settings/ActiveParcelConfiguration.cs` |
| Prod expiry variable set to 90 | `deploy/k8s/fenghuang/tracking/tracking-core.yaml:169,391` |
| Loop sleeps (30 s, 60 s) and full-batch repeat | `BatchRequestManager.cs:46,50-52`; `Options.cs:54,60` |
| Batch size default 100; comment says 1000 | `Options.cs:47` |
| Carrier calls in parallel | `BatchRequestHandler.cs:47` |
| Carrier error: failed response, no retry | `TrackingRequestHandler.cs:58,74,90,106` |
| Only credential errors acted on | `ConnectorResponseHandler.cs:72-76`; `ErrorResponseHandler.cs:26-30` |
| Credential pause: four hours, more than three rows | `CredentialErrorsHandler.cs:39-46,56,69,120`; `tracking-core.yaml:354-363,745-750` |
| No new events: nothing written | `ConnectorResponseHandler.cs:87` |
| Publish, then store | `ConnectorResponseHandler.cs:112-131` |
| A faulted loop is not restarted | `CarrierConnectorWorker.cs` (`StartProcessing`) |
| Allowed states and polling minutes limit | `connectors-config-api.yaml:93-94,105-110` (prod manifests) |
| UPDATE for an existing parcel returns early | `ConsignmentHandler.cs:111-124` |

Related MPK pages:

- [Polling Connectors](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353697880)
- [Carrier Tracking and Proof of Delivery](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353206337)
- [Tracking Webhook Services](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353533985)
- [Shipment Journey Through ECM](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354975746)
- [Shipment Identity](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/355631312)
- [ECM Pub/Sub Topics](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/356155424)
