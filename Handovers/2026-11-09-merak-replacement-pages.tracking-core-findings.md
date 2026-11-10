---
tags: [handover, research-copy, ecm, tracking]
date: 2026-11-10
tldr: "Research copy: how tracking-core orchestrates polling, and why the polling interval does not shrink with parcel age (code read at c081108, 2026-11-10)."
status: research-copy
---
This is a research copy of the findings file `tracking-core-findings.md`, kept in the vault so it can be found and cited. The synthesis is [[Systems/ecm/tracking]]. Where the two differ, the synthesis note is the later reading. Nothing was edited in Confluence, a repo or Firebird.

# tracking-core: how ECM tracking is orchestrated, and whether polling interval changes with parcel age

Read-only research, 10 Nov 2026. Nothing was edited in Confluence, the vault or any repo.

## Verdicts

| Hypothesis | Verdict | One line |
| --- | --- | --- |
| H1. tracking-core orchestrates polling | PARTLY CONFIRMED | It owns the parcel store and the "who is due" decision, and serves work over gRPC. It has no scheduler. Each connector's loop decides when to ask, so cadence is set jointly: the due test lives in tracking-core, the threshold and loop timing come from each connector's etcd config. |
| H2. Interval decreases as a parcel gets older | FALSIFIED in code (prod values UNKNOWN) | There is no age term anywhere. The interval is one scalar, `TargetPollingMinutes`, per carrier and per tracking state (IN_TRANSIT, DELIVERED, DELETED). The only way a parcel's interval changes is a state change, mainly IN_TRANSIT to DELIVERED, and that is a different config key, not a function of age. Whether prod's DELIVERED value is shorter or longer than IN_TRANSIT is unknown. |

## What was read (source ranked by closeness to code)

| Source | Ref | Weight |
| --- | --- | --- |
| tracking-core source, Azure DevOps `globalfreightsolutions/fenghuang/tracking-core`, master | `c0811087b8ed4dce4968bb8e9b985f6853f51a69` (2026-06-08, "Merged PR 13681: docs: add agents.md"). ADO `master` objectId was checked live on 10 Nov and equals this sha. The local clone `/home/hjf/code/apiky-survey/ado/tracking-core` is a shallow 1-commit clone of it, so file content is identical to ADO master. | CONFIRMED when I cite code |
| Prod cluster manifests, `prod-uk1-primary-cluster` | `a317dc0b90a3ef4df30fcdc82293a4abd924f74b` (2026-11-06), `deploy/k8s/fenghuang/tracking/tracking-core.yaml`, `connectors-config-api.yaml` | Deploy config. Image tag is `tracking-core:prod-44693`; I could not map that tag to a git sha |
| Terraform, `/home/hjf/code/k8s/gfs-ecm-prod-uk1` | `e3c6dd9` (2025-07-30), `modules/fenghuang-scanning-core/main.tf`, `modules/subscription/main.tf`, root `main.tf` | Infra as code, 15 months old, may lag what is deployed |
| `connectors-configuration-api` (ADO), `docs/etcd-data-structure.md` | commit `f3f089aa3078f0b973d8b911a99133f1e6cee8ab` (master listing) | Doc, not code. Directory listing shows a plain REST CRUD API over etcd with no background worker |
| Connector repos (ADO, local clones), e2e `init.js` etcd seeds | each a single-commit shallow clone | Test seeds only (values like 0.1 minutes are test values, not prod) |
| Waypoint `~/Documents/obsidian/Engineering/tracking-core/` (`overview.md`, `architecture.md`, `known-context.md`) | `verified_sha: c081108` (matches ADO master), verified 2026-11-06 | Second-hand, checked against code below |
| MPK 353697880 (Polling Connectors, v11) and 353206337 (Carrier Tracking and PoD, v13), read via Atlassian MCP, markdown | | STATED |

The Waypoint vault note `verified_sha c081108` is current against ADO master, so it is not stale on source. The vault's claim that source was "stated, not read" is out of date for the code paths below, which I have now read.

## Q1. What is tracking-core, and is it the orchestrator?

One .NET Core 3.1 repo, one Docker image, one `Startup.cs`; the role is chosen at runtime by `System__Mode`.

| Mode | Prod deployment (replicas) | What it does | Evidence | Status |
| --- | --- | --- | --- | --- |
| `CONSIGNMENT_MANAGER` | `fenghuang-tracking-core-consignment-manager` (3) | Pub/Sub subscriber. Creates `active-parcels` documents | `Startup.cs:154-162`, `ConsignmentManagerService.cs:21-29`, manifest `tracking-core.yaml:42-47,125` | CONFIRMED |
| `BATCH_CREATOR` | `fenghuang-tracking-core-batch-creator` (3) | gRPC server, `TrackingBatchServiceV1.GetBatch` (server stream). Leases due parcels | `Startup.cs` `MapGrpcService<TrackingBatchService>`, `TrackingBatchService.cs:44`, `tracking_batch_v1.proto` | CONFIRMED |
| `RESPONSE_PUBLISHER` | `fenghuang-tracking-core-response-publisher` (3) | gRPC server, `ConnectorResponseServiceV1.SendResponse` (client stream). Dedupes, maps, publishes, updates state | `Startup.cs` `MapGrpcService<ConnectorService>`, `ConnectorService.cs:55`, `connector_response_v1.proto` | CONFIRMED |

Plus, outside the tracking-core code: the connector framework (`src/Gfs.Fenghuang.Tracking.Core.Frameworks.Connector`, package version 0.6.2 in the csproj, line 4), which each `connectors-*` service embeds as a NuGet package. The response-publisher pod also runs the `tracking-mapper` and `shipment-tracking-status-deriver` sidecars, called over localhost HTTP (`tracking-core.yaml` env `TrackingMapper__Options__MappingEndpoint`, `RemoteTrackingStatusV2Getter__Options__TrackingStatusV2Endpoint`).

Store: Mongo database `tracking-core`, collection `active-parcels` (manifest `ActiveParcelRepositoryOptions__*`). Config: etcd, prefix key `connectors` (`Program.cs:33`, manifest `Etcd__PrefixKeys__0`).

How it "orchestrates": there is no cron, no timer, no Cloud Run job, no push to connectors and no Pub/Sub work queue in tracking-core. It is a pull model:

1. A connector's `CarrierConnectorWorker` starts one loop per enabled etcd batch key, i.e. per carrier and state (`CarrierConnectorWorker.cs:54-56`; options can change live, `:82`).
2. Each loop (`BatchRequestManager.Run`) calls `GetBatch(carrier, limit, targetPollingMinutes, status)` on batch-creator (`BatchRequestHandler.cs:~30-45`, per-carrier values come from the connector's own etcd options).
3. batch-creator repeatedly does a Mongo `FindOneAndUpdate` to pick the oldest-due parcel and stamps `LastRequestedAt = now` (`ActiveParcelRepository.cs:104-128`), skipping untracked or paused contracts (`ActiveParcelDomain.cs:156-165`), up to `limit` parcels, streaming each back.
4. The connector calls the carrier for every streamed parcel in parallel (`BatchRequestHandler.cs:47`, `AsyncEnumerableParallelProcessor`; no rate limit or backoff was found in this code) and streams results to response-publisher.
5. If the batch was full (`BatchLimit == processed`) the loop asks again immediately; otherwise it sleeps `IntervalSeconds` (default 30; `BatchRequestManager.cs:50-52`, `Options.cs:54`). After an exception it sleeps `IntervalErrorSeconds` (default 60; `BatchRequestManager.cs:46`, `Options.cs:60`). Defaults only: prod overrides are in etcd and unknown.

So tracking-core is the state store and work-lease server, not an orchestrator in the sense of a scheduler. The cadence emerges from connectors pulling. Status: CONFIRMED.

## Correction to the "Already known" list: who does the FindOneAndUpdate

A connector does not touch Mongo for scheduling. The `FindOneAndUpdate` is in tracking-core's batch-creator (`ActiveParcelRepository.cs:104-128`, called via `ActiveParcelDomain.cs:149`). The connector only calls gRPC `GetBatch`. (Some connectors, DPD and DHL Parcel, have their own small Mongo collections with a `LastRequestedAt`; these are write-only bookkeeping, I found no read that gates polling: `connectors-dpd/.../ParcelRepository.cs:35-47`, `DPDClient.cs:105,141`.) Status of the corrected statement: CONFIRMED.

## Q2. Lifecycle of an active parcel

Created: consignment-manager consumes subscription `shipments.v2.identified.fenghuang.tracking-core` (topic from `shipment-identity-service`; subscription name derived in `modules/subscription/main.tf:3`, topic name root `main.tf:331`). For each parcel in the consignment it upserts a document keyed on (`parcel.parcelNumber`, `parcel.shipmentId`) (`ConsignmentHandler.cs:129`, `ActiveParcelRepository.cs:36-51`), then sets `trackingState` to IN_TRANSIT, or DELETED if the consignment `isDeleted` (`ConsignmentHandler.cs:130`, `ActiveParcelRepository.cs:203-221`). Skipped when: consignment has no parcels (`:51-56`), contract is on the Mongo `untracked` list (`:59-63`), or the message is an `UPDATE` for a parcel that already exists (`:111-124`). Status: CONFIRMED.

Fields (`Shared/Models/ActiveParcel.cs`): `parcel` block (shipmentId, shipmentIdV2, parcelNumber, consignmentNumber, customerId, company, contractNo, carrier, carrierV2, carrierCode, serviceCode, despatchDate, address country/postcode), `tracking.lastRequestedAt`, `tracking.lastReceivedAt`, `tracking.events[]`, `tracking.mappedEvents[]`, `createdDate`, `expiryDate`, `expiryDateV2`, `shouldPublishToLegacy`, `currentStatus` {id, bucket, description}, `trackingState`, `wasManuallyUpdated`.

There is no `nextPollAt`, no poll count, and no stored "last new event" timestamp. `lastReceivedAt` is set in memory (`ActiveParcelDomain.cs:59`) but no repository method writes it, so I found no persisted value (CONFIRMED by grep: it appears only at that line and the model). "Due" is computed at query time from `lastRequestedAt`.

How it leaves:

| Exit | Mechanism | Evidence | Status |
| --- | --- | --- | --- |
| Mongo TTL delete | TTL index `expiryDate_v1`, `ExpireAfter = 0` on `expiryDate` | `ActiveParcelRepository.cs:237-239` | CONFIRMED |
| Expiry initial value | `now + ExpiryDays(default, default)` set on insert only (`SetOnInsert`) | `ConsignmentHandler.cs:78,83`, `ActiveParcelRepository.cs:45` | CONFIRMED |
| Expiry refresh | Only when a poll yields at least one new, unfiltered event: `expiryDate = now + ExpiryDays(carrier, status bucket)` | `ConnectorResponseHandler.cs:87,100,127-131`, `TrackingStatusManager.cs:33-46,48-69` | CONFIRMED |
| V2 expiry | `expiryDateV2 = max(event.receivedDate) + ExpiryDays`; its TTL index is commented out ("dark launching") so it deletes nothing | `TrackingStatusManager.cs:60`, `ActiveParcelRepository.cs:241-244` | CONFIRMED |
| Delivered | Status bucket "Delivered" sets state DELIVERED, one-way (the update filter excludes docs already DELIVERED). The parcel is still leased if that carrier's DELIVERED batch key is enabled | `TrackingStatusManager.cs:44`, `ActiveParcelRepository.cs:210,218` | CONFIRMED |
| Untracked contract | Skipped at lease time and at ingest | `ActiveParcelDomain.cs:156-158` | CONFIRMED |
| Credential pause | See Q5 | | CONFIRMED |

So "tracks a parcel for 90 days after its last new event" is the right shape but is not in `ActiveParcelDomain.cs`. That file has no expiry logic. The logic is in `ConsignmentHandler.cs`, `TrackingStatusManager.cs` and the TTL index in `ActiveParcelRepository.cs`. Also the refresh is "last new event that survives filtering", and the days value is per carrier and per status bucket, not a constant. Status of the shape: CONFIRMED. Status of the number 90: STATED only, see below.

### The 90 is not read from where the code reads expiry

- Code reads `ExpiryDays` from the `Connectors` config section: `Connectors:carriers:{carrier}:activeParcel:parcelOptions:{status}:expiryDays`, falling back to `default`, and throws if neither exists (`Settings/ActiveParcelConfiguration.cs:12-13,~30-58`; bound at `Startup.cs:158,168`).
- Prod manifests set the env var `ActiveParcel__ParcelOptions__default__ExpiryDays=90` on consignment-manager (`tracking-core.yaml:169`) and response-publisher (`:391`). A search of the whole of `src` finds no code that binds an `ActiveParcel` section; only `Connectors`.
- `connectors-configuration-api/docs/etcd-data-structure.md` documents etcd keys `connectors:{name}:activeParcel:parcelOptions:{status}:expiryDays` (no `carriers` segment), which does not obviously match the `Connectors:carriers:...` shape the code binds.
- The tracking-core e2e compose sets both forms to different values (`e2e/consignment-manager/docker-compose.yml:67-68`: 90 on the env var, 60 on the `Connectors__carriers__default` form).

Net: the effective prod expiry (per carrier and status) is UNKNOWN. 90 is STATED by an env var that the code at this sha does not appear to read. What would settle it: read the prod etcd keys under `connectors:` for `expiryDays`, or check Mongo for the spread of `expiryDate - createdDate`.

## Q3. The polling schedule

Exact rule (CONFIRMED, `ActiveParcelRepository.cs:104-128`):

```
filter = (parcel.carrier == carrier OR parcel.carrierV2 == carrierV2)
         AND trackingState == state                       // IN_TRANSIT | DELIVERED | DELETED
         AND NOT (tracking.lastRequestedAt > now - TargetPollingMinutes)
update = set tracking.lastRequestedAt = now
sort   = tracking.lastRequestedAt ascending
```

Consequences, all from that code:

- The interval is the same scalar for every parcel of a given carrier and state. There is no function of `createdDate`, `despatchDate`, event count, last event time or poll count anywhere in the lease path (`ActiveParcelDomain.cs:121-170`, `TrackingBatchService.cs:56-63`, `connector_response`/`tracking_batch` protos carry no age field).
- `TargetPollingMinutes` is per request, supplied by the connector from its etcd options (`BatchRequestHandler.cs:~30-45`, `Options.cs:41`). Etcd keys are per connector and per status: `connectors:{name}:framework:batchOptions:{STATE}:targetPollingMinutes` (also `enabled`, `carrierId`, `carrierIdV2`, `status`, `batchLimit`, `intervalSeconds`, `intervalErrorSeconds`). Sources: `connectors-configuration-api/docs/etcd-data-structure.md` (STATED, doc) and the `e2e/init.js` seeds in `connectors-dpd` etc. (key shape CONFIRMED, values are test values). The config API's own limit is `ConnectorValidation__MaxTargetPollingMinutes=9999` (`connectors-config-api.yaml:93-94`), i.e. effectively unbounded.
- The API's allowed statuses are exactly IN_TRANSIT, DELIVERED, DELETED (`connectors-config-api.yaml:105-110`). There is no "age band" dimension in config.
- Dispatch order is oldest `lastRequestedAt` first. A new parcel has no `lastRequestedAt`; it matches the filter (a `Not(Gt(null, ...))` is true) and, by MongoDB's null-first ascending sort, should be leased before any previously polled parcel. That means a new parcel is polled soon after creation, which is the opposite of an age-based back-off, and not the same as the interval shrinking. The null sort order is MongoDB semantics, not tested here: marked inferred.
- Effective cadence can be longer than the target: when more parcels are due than `BatchLimit` can drain, the queue works through the oldest first, so the real gap is the queue cycle time. No code prioritises older parcels. (inference from the code, not measured.)
- `lastRequestedAt` is stamped at lease time, not when the carrier answers. A failed or slow poll still counts as a poll; the parcel is not due again for `TargetPollingMinutes`.
- Mongo index `lastRequestedAt_v1` is on (`parcel.carrier`, `trackingState`, `lastRequestedAt`) (`ActiveParcelRepository.cs:228-230`).

Prod values of `targetPollingMinutes`, `batchLimit`, `intervalSeconds` and `enabled` per carrier and state: UNKNOWN. They live in prod etcd. No repo, manifest or Terraform contains them. (Same gap that the MPK page and the vault note already record.) A human could still have set a shorter DELIVERED than IN_TRANSIT interval, or vice versa, so the data could look "age-shaped" in Datadog even though no code derives it from age. Do not guess a schedule from the key name.

What would settle H2 empirically: read the etcd keys (`etcdctl get --prefix connectors: | grep targetPollingMinutes`) or, without etcd, sample a few `active-parcels` documents' successive `lastRequestedAt` gaps, split by `trackingState` and by parcel age.

## Q4. Pub/Sub topics and subscriptions

| Direction | Topic | Subscription or publisher | Evidence | Status |
| --- | --- | --- | --- | --- |
| Consumes | `shipments.v2.identified` | `shipments.v2.identified.fenghuang.tracking-core`, consumed only by consignment-manager | `main.tf:331,341`, `modules/fenghuang-scanning-core/main.tf:8-15`, `ConsignmentSubscriberService.cs:40`, manifest `ConsignmentManager__Subscriber__Subscription` from ConfigMap `shipment_subscription` | CONFIRMED (infra from 2025-07 Terraform) |
| Publishes | `raw_tracking.v1` | response-publisher, config `PubSubSettings__RawTrackingTopic` | `EventPublisher.cs:54`, `modules/fenghuang-scanning-core/main.tf:26-34`, root `main.tf:~345` | CONFIRMED |
| Publishes (legacy) | `legacy_tracking.v1` | Prod has `LegacyPublisher__Options__default__ShouldPublishToLegacy=false` | manifest `tracking-core.yaml:389`, `EventPublisherLegacy.cs:48` | CONFIRMED config, I did not read the publish branch end to end |
| Subscription created, no consumer in code | `tracking.v1` (`tracking_subscription`), tracking-mapping config topic (`tracking_mapping_config_subscription`) | Terraform creates both and puts them in the ConfigMap, and the manifest wires `TrackingEventManager__Subscriber__Subscription` | `modules/fenghuang-scanning-core/main.tf:17-24,46-53`, `tracking-core.yaml:144-147` | No code consumes either: `Startup.cs` registers only `ConsignmentManager:Subscriber`, and a grep for `TrackingEventManager` in `src` returns nothing. `agents.md` says tracking-core subscribes to `tracking_configuration_notifications.v1` and `tracking.v1`; I could not find that in code. Treat as a stale claim |

`raw_tracking.v1` message shape (`EventPublisher.cs:66-76`, `Publishers/Models.cs`): JSON, camelCase, nulls omitted; payload is a `TrackingEvent` with `id`, `parcel{...}`, `receivedDate`, `reportedDate`, `isReportedDateLocalizable`, `statusCode`, `statusDescription`, optional signatory, location, depot, delivery, `additionalData`, `rawData[]`. The `PubsubMessage` carries only `Data`. tracking-core sets no ordering key and no attributes (CONFIRMED in this repo). The shared `Gfs.Core.PubSub` NuGet's `IPublisher.PublishAsync` was not read, so whether it adds anything on top is UNKNOWN.

Event id: `ObjectId.GenerateNewId()` minted in response-publisher per new event (`ActiveParcelDomain.cs:72`). So it is not derived from (parcel, date, code); a republish of the same carrier event mints a new id. Confirms the "Already known" point that dedupe downstream on id alone cannot catch republishes from here.

Dedupe inside tracking-core: against the parcel's stored events by (`reportedDate`, `statusCode`) (`TrackingEventDeduplicator.cs`, `IsDuplicate`), plus a "full duplicate vs previous received event" check; implemented in `ActiveParcelDomain.GetNewTrackingEvents` (`:172-231`). CONFIRMED.

Write order hazard (CONFIRMED, `ConnectorResponseHandler.cs:112-131`): all events are published to `raw_tracking.v1` in parallel (`Task.WhenAll`, line 125), and only after that succeeds are state, events and expiry written to Mongo (lines 127-131). If a publish throws, nothing is persisted; the next poll finds the same events "new" again and republishes them under fresh ids. If the Mongo write fails after a good publish, the same happens. Events from one poll are published concurrently, so arrival order on the topic is not guaranteed. Messages are not batched into one list (a list-publishing experiment was reverted: ADO commits `d30866b`, `1df9a2b`, 2023).

Retries and dead-lettering (Terraform, `modules/subscription/main.tf`, applies to the consignment subscription): `ack_deadline_seconds = 10`, `max_delivery_attempts = 10` to a dead-letter topic, `retry_policy` 10 s to 600 s backoff, message ordering off by default. In code, the handler nacks on bad JSON, validation failure or any exception, and acks on success (`PubSubMessageHandler.cs:51,60,67,73`). So the inbound side does have a DLQ. This contradicts a literal reading of the MPK sentence "no retry or dead-letter handling" if it is read as about all of tracking-core; it is true of the polling loop (Q5), not of the inbound subscription. The Terraform read is 15 months old.

## Q5. Carrier error, rate limit, no new events

| Case | What happens | Evidence | Status |
| --- | --- | --- | --- |
| Carrier returns an error | The connector catches it, increments a metric, and returns a `Successful=false` response with a reason. There is no retry and no backoff in the connector framework | `TrackingRequestHandler.cs:58,74,90,106` | CONFIRMED |
| Response-publisher receives a failure | `ErrorResponseHandler` acts only on `CredentialsError`. All other reasons (generic, carrier API, parcel not found) return without any write | `ConnectorResponseHandler.cs:72-76`, `ErrorResponseHandler.cs:26-30` | CONFIRMED |
| What the parcel's next poll looks like | `lastRequestedAt` was already stamped at lease time, so a failed parcel waits another `TargetPollingMinutes` | `ActiveParcelRepository.cs:113` | CONFIRMED |
| Rate limit (for example 429) | Not special-cased. It is a carrier API error: no backoff, the whole batch was issued in parallel | `TrackingRequestHandler.cs:74`, `BatchRequestHandler.cs:47` | CONFIRMED (no throttle found in tracking-core or framework code; a carrier client could add its own, not checked per connector) |
| Credentials error | A row is inserted into Mongo `credential-errors` (TTL 4 hours by default). A contract (carrierV2, customer, contract) with more than `PauseThreshold` (3) rows is skipped by the batch-creator. Enabled only for carrierV2 `10` and `19` in prod | `ErrorResponseHandler.cs:~40-50`, `CredentialErrorsHandler.cs:39-46,56,69,120`, manifest `tracking-core.yaml:354-363,745-750` | CONFIRMED mechanism. That `10` and `19` are DPD and DPD Local is from the MPK page (STATED) |
| Whole batch fails | `BatchRequestManager` logs, counts `batch.error`, sleeps `IntervalErrorSeconds` (default 60) | `BatchRequestManager.cs:46` | CONFIRMED default |
| No new events | Response-publisher returns early, nothing is published, state and expiry are not updated (`ConnectorResponseHandler.cs:87`). `lastRequestedAt` is already stamped, so the parcel simply waits one more interval. No interval change | | CONFIRMED |
| Short or empty batch | Connector sleeps `IntervalSeconds` (default 30) | `BatchRequestManager.cs:50-52` | CONFIRMED default |
| Loop fault | A faulted per-key task logs an error and terminates; nothing restarts it until the options change or the pod restarts | `CarrierConnectorWorker.cs` `StartProcessing` continuation | CONFIRMED by reading, not exercised |

## Q6. Contradictions and corrections to the "Already known" list and to the vault

1. "A connector does a Mongo FindOneAndUpdate": it is tracking-core's batch-creator that does (see above). The connector makes a gRPC call.
2. "ActiveParcelDomain.cs is cited for 90 days": it contains no expiry logic. Expiry is in `ConsignmentHandler.cs:83`, `TrackingStatusManager.cs:48-69` and the TTL index at `ActiveParcelRepository.cs:239`. The days value is per carrier and status bucket from config, and the prod value is unconfirmed (the only 90 in prod is an env var the code does not appear to read).
3. Vault `architecture.md` guardrail G2 ("a parcel stops being polled only when it reaches DELIVERED with that state's etcd key off, or when it expires after 90 days") is incomplete. Other exits: DELETED key off, `untracked` list, credential pause for enabled carriers, and the expiry is refreshed by each new event so it is not 90 days from creation.
4. Vault says "up to 100 parcels"; the C# default is 100 (`Options.cs:47`) though its own doc comment says 1000. The prod value is in etcd. UNKNOWN.
5. Vault says "There are no retries or dead letters". True of polling. The inbound `shipments.v2.identified` subscription has a dead-letter topic with 10 attempts per Terraform.
6. Vault and MPK say the `fenghuang-tracking-core-config` ConfigMap "isn't in the cluster repo". It is defined in Terraform: `/home/hjf/code/k8s/gfs-ecm-prod-uk1/modules/fenghuang-scanning-core/main.tf:55-68` (keys `shipment_subscription`, `tracking_subscription`, `raw_tracking_topic`, `legacy_tracking_topic`, `tracking_mapping_config_subscription`). Topic names: `shipments.v2.identified` in, `raw_tracking.v1` out, `legacy_tracking.v1` configured but off.
7. `tracking-core/agents.md` says "Runtime: Node.js, npm" and that it subscribes to `tracking.v1` and `tracking_configuration_notifications.v1`. The repo is C# (.NET Core 3.1) and I found no code for those subscriptions. `agents.md` is wrong on both points, so do not cite it.
8. Calls-per-event: the MPK pages already flag 24, 26 and 19 as unreconciled. I did not re-derive them.
9. Several prod flags have no binding in the code at this sha: `ConnectorResponseHandler__Options__GetNewTrackingV2Enabled`, `...UseGetNewTrackingV2`, and `TrackingStatusSettings__TrackingStatusV2Enabled` (grep over `src` finds none of these names). Either they are dead env vars, or prod runs an image built from different source than master (`prod-44693` is not mapped to a sha). This affects how far "the code I read is what runs" can be pushed.

## Not verified, and what would settle it

| Unknown | Settled by |
| --- | --- |
| Prod `targetPollingMinutes`, `batchLimit`, `intervalSeconds`, `enabled` per carrier and state | `etcdctl get --prefix connectors:` on prod etcd, or the `connectors-configuration-api` GET endpoints (needs access) |
| Effective prod `expiryDays` per carrier and status, and whether the `Connectors:carriers:...` binding picks up the etcd keys at all | Same etcd read, plus Mongo `expiryDate - createdDate` distribution |
| Whether any human or job changes etcd values by parcel age | Not in code: `connectors-configuration-api` has no background worker in its file listing. Etcd audit or change history would confirm |
| Real interval distribution per parcel | Mongo: sample `lastRequestedAt` over time, or Datadog on `tracking_batch_service.batches_sent` per carrier and state |
| Whether prod runs master `c081108` | Map image tag `tracking-core:prod-44693` to a build in the ADO pipeline |
| Whether `Gfs.Core.PubSub`'s publisher adds an ordering key or attributes | Read that NuGet package (not in the local clones) |
| Other `raw_tracking.v1` subscriptions' ordering setting | Only `tracking-mapper`'s subscription was seen (ordering default false). The rest are in other modules |
| `untracked` list contents | Mongo `tracking-core.untracked` |
| Terraform state vs deployed Pub/Sub config | `gcloud pubsub subscriptions describe` (read-only) |
