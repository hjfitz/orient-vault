---
tags: [explain]
date: '2026-11-06'
title: ECM's event world is a mess because the bus carries raw facts and every consumer rebuilds meaning on its own
thesis: "ECM publishes raw carrier scans with no GFS meaning attached, so tracking-core and six consumers each re-map them, at least eight keep their own copy of the shipment, and each decides 'delivered' its own way; nothing is ordered across publishers, deduplicated across sources or replayable."
confidence: high
---
# ECM's event world is a mess because the bus carries raw facts and every consumer rebuilds meaning on its own

```orient-bluf
{ "v": 1, "bluf": "ECM publishes raw carrier scans with no GFS meaning attached, so tracking-core and six consumers each re-map them, at least eight keep their own copy of the shipment, and each decides 'delivered' its own way; nothing is ordered across publishers, deduplicated across sources or replayable.", "confidence": "high", "action": "Before adding a carrier, webhook or POD event, decide which consumer's meaning it must match. There is no canonical one." }
```

> Companion to [[2026-11-06-life-of-a-shipment-through-ecm]], which tells the journey. Figures cover the 15 days to 2026-11-06 unless stated. Re-checked against code, Terraform and Datadog on 2026-11-09.

## Situation
- **CONFIRMED** Terraform declares 70 topics and 144 subscriptions in `gfs-ecm-prod-uk1`. Nobody here can list the live set. ECM's own catalogue lists about 50 and misses the webhook paths. [1][2]
- **CONFIRMED** Subscriber handlers processed about 120M messages, about 179 per new shipment ID. Each message counts once per subscriber that handled it. [3]

## Assessment

### No canonical meaning on the bus
- **CONFIRMED** `tracking-core` maps each scan, stores the result in Mongo, then publishes the raw event without it. [4]
- **CONFIRMED** Six consumers and tracking-core each map every scan through their own sidecar. That is about 18.8M lookups a week for 3.0M events. [5]
- **CONFIRMED** Each service holds its own config copy and caches mappings for 20 minutes. A failed sync acks and stays stale, and mappings freeze at ingest. [5]

### Many copies, many truths
- **CONFIRMED** `shipments.v2.identified` feeds 17 declared subscriptions in the ECM project and 2 webhook push subscriptions elsewhere. At least eight consumers keep their own copy. [1][5]
- **CONFIRMED** "Delivered" has at least six definitions, including the deriver's group precedence and Connect's `text === 'DELIVERED'` POD gate. [5]
- **CONFIRMED** Firebird status codes never reach ECM. Only `isDeleted` (100) and `wasManuallyUpdated` (1005+) pass through, and Firebird sets 1005 automatically. [6]

### Churn and cost
- **CONFIRMED** 57.5% of `shipments.v2.identified` messages re-announce a known shipment. About 610k `SHIPMENTS` updates arrive a week, and 449k of them escape the 180 s window. [3][6]
- **ASSESSED** Daytime Scan Injector writes drive about half of those updates. This rests on minute-level correlation; overnight backlog writes almost never fire. [3]
- **CONFIRMED** tracking-core streams 115M parcel polls to connectors to publish 6.0M events, about 19 per event. [3]
- **CONFIRMED** DHL Parcel UK rejects about 15 contracts with error 3002. tracking-core cannot pause them, so about 850 parcels are re-polled about 70 times a day. CID-317 tracks it. [3][4]

### At-least-once, unordered, no replay
- **CONFIRMED** Only the deriver sets an ordering key, on `shipment_tracking_status.v2`. Publishers publish before they persist. [4][5]
- **CONFIRMED** Consumers dedupe on the event `id` only. The same scan from two publishers lands twice, which the Evri cutover will hit. [4][5]
- **CONFIRMED** No topic or subscription keeps acked messages. `gfs-deadletter-register` stores dead letters but cannot replay them. [5]

### Dead weight
- **CONFIRMED** The Kubernetes `tracking-patina-service` consumes the whole firehose and drops every event. Its Dataflow sibling, `patina-service-2`, does the real write-back. [6]
- **CONFIRMED** Three subscriptions on `raw_tracking.v1` have no running consumer: the stopped mapper, parcel-eta and data-warehouse. The `.longmen` one is the data team's live feed. [1][7]
- **CONFIRMED** `shipment-update-service` maps 3.0M events a week into a field nothing reads. [5]

### One-way and narrow
- **CONFIRMED** Firebird replicates new shipments and a filtered set of updates. Parcel edits and invoice numbers never replicate. Nobody has read the production trigger text. [6]
- **CONFIRMED** No portal, API or staff tool edits a shipment's address or route. Those exist only as tickets that staff action by hand. [8]

### Split ownership
- **CONFIRMED** The carriers team owns the connectors, `tracking-core`, the status deriver, `gfs-pod` and the file processor. The cx team owns CCIS, ICIS, identity and claims. [9]
- **CONFIRMED** The webhooks' grants on ECM topics sit in their own Terraform, outside ECM's. [2]
- **CONFIRMED** No team owns the write-back. Engineers redeploy `patina-service-2` as needed, Tech Services monitors the Scan Injector, and SRE runs its host. Someone cancelled CXD-364, the ownership ticket, unresolved. [7]
- **CONFIRMED** Two identities hold project-wide Pub/Sub editor rights: the data warehouse project's agent, and `tracking-dump@`, which nobody claims. [10]

## Open items
| Item | Owner | By |
|---|---|---|
| Fix or stop polling the DHL Parcel UK contracts that DHL rejects (CID-317, Blocked) | Carrier Integrations Development | UNKNOWN |
| Decide where GFS meaning lives: publish a mapped event once, or keep per-consumer mapping | ECM and carriers | UNKNOWN |
| Read the production replication trigger on central Firebird | DBA or legacy-org access | UNKNOWN |
| Confirm live GCP state: cross-project grants, warehouse subscription, `tracking-dump@` | SRE | UNKNOWN |

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "doc", "ref": "ADO GFS Cloud Infrastructure/gfs-ecm-prod-uk1@7eb175c main.tf, modules/subscription, modules/topic, modules/longmen-connection; prod-uk1-primary-cluster@39fa64c deploy/k8s" },
  { "id": 2, "kind": "code", "ref": "tracking-webhook-royal-mail-sapient/iac/projects/gfs-hsci-tracking-webhook-royal-mail-sapient/pubsub.tf@3c880bf" },
  { "id": 3, "kind": "log", "ref": "Datadog, 2026-10-22T21:30Z to 2026-11-06T21:30Z and week to 2026-11-09: *.pubsub.*.handled_messages (120,437,957); shipment_identity_service.ids_created; gfs_modernizer.messages; tracking_batch_service.batches_sent; connector_dhlparcel errors" },
  { "id": 4, "kind": "code", "ref": "tracking-core/ResponsePublisher/ConnectorResponseHandler.cs@c081108" },
  { "id": 5, "kind": "doc", "ref": "STSD@a3dc446, CCIS@b2af452, ICIS@3d125f5, SUS@ccec388, claims@584d827, connect@6c6d527, tracking-mapper@44cfbf2 (mapping-cache.js); Datadog *.tracking_mapping.requests" },
  { "id": 6, "kind": "doc", "ref": "node-modernizer@2350a1d shipment-translator.js; Firebird Transfer Service@8569227 sql/4_fts_doppelganger_updates_3.sql; gfs-pipelines@b70e8ca FIREBIRD_DDL/procedures.sql; ADO fenghuang/tracking-patina-service@8edfb3e" },
  { "id": 7, "kind": "doc", "ref": "gfs-data-services/gfs-pipelines@b70e8ca PROD gfs-ecm-extractor config.py; ADO patina-service-2-prod builds 54715, 57009, 57328; Jira CXD-364; Datadog monitors 258252839, 258316179" },
  { "id": 8, "kind": "doc", "ref": "service-core@dc00bd4 customer-gateway typedefs; gfs-customer-care tickets-handler@5334293, oz-admin-ui@9f911e7" },
  { "id": 9, "kind": "doc", "ref": "gfs-ecm/ecm-development@b2b67df repos.json (team field)" },
  { "id": 10, "kind": "code", "ref": "ecm-prod-uk1-iac/terraform/envs/prod.tfvars@68d97d7" }
] }
```
