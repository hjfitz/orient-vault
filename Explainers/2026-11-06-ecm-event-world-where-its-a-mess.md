---
tags: [explain]
date: '2026-11-06'
title: ECM's event world is a mess because the bus carries raw facts and every consumer rebuilds meaning on its own
thesis: "ECM publishes raw carrier scans with no GFS meaning attached, so six consumers each re-map them, keep their own copy of the shipment and decide 'delivered' their own way; nothing is ordered, deduplicated across publishers or replayable."
confidence: high
---
# ECM's event world is a mess because the bus carries raw facts and every consumer rebuilds meaning on its own

```orient-bluf
{ "v": 1, "bluf": "ECM publishes raw carrier scans with no GFS meaning attached, so six consumers each re-map them, keep their own copy of the shipment and decide 'delivered' their own way; nothing is ordered, deduplicated across publishers or replayable.", "confidence": "high", "action": "Before adding a carrier, webhook or POD event, decide which consumer's meaning it must match. There is no canonical one." }
```

Companion to [[2026-11-06-life-of-a-shipment-through-ecm]], which tells the journey. Figures cover the 15 days to 2026-11-06.

## Situation
- **CONFIRMED** Prod runs 70 topics and 144 subscriptions in `gfs-ecm-prod-uk1`. ECM's own catalogue lists about 50 and misses the webhook paths. [1][2]
- **CONFIRMED** One shipment triggers about 194 message deliveries: 130.7M deliveries for 672k new shipment IDs. [3]

## Assessment

**No canonical meaning on the bus.**
- **CONFIRMED** `tracking-core` maps each scan, stores the result in Mongo, then publishes the raw event without it. [4]
- **CONFIRMED** Six consumers re-map every scan through their own `tracking-mapper` sidecar and their own config copy: about 18.8M lookups a week for 3.0M events. [5]
- **CONFIRMED** Config reaches each copy independently. A failed sync acks and stays stale, and mappings freeze at ingest. Two services can show one scan differently, permanently. [5]

**Many copies, many truths.**
- **CONFIRMED** `shipments.v2.identified` feeds 15 in-project subscribers and 2 cross-project webhooks. About eight build their own shipment copy, each with different merge rules. [1][5]
- **CONFIRMED** "Delivered" has at least six definitions, including STSD's group precedence, the mapper's `isDelivered`, and Connect's `text === 'DELIVERED'` POD gate. [5]
- **CONFIRMED** Tracking history lives in four diverging stores: CCIS (customer-visible only), ICIS (all), STSD (all) and tracking-core (TTL'd). [5]

**Churn and cost.**
- **CONFIRMED** 57.5% of `shipments.v2.identified` traffic re-announces a shipment that already has an ID. That is 1.58M messages for 672k IDs. [3][6]
- **CONFIRMED** Polling makes 115M carrier requests to publish 6.0M events, about 19 per event. [3]
- **CONFIRMED** The DHL Parcel UK connector polled 888 parcels with invalid credentials: 377k errors. Only DPD contracts auto-pause on credential errors. [3][4]

**At-least-once, unordered, no replay.**
- **CONFIRMED** No `raw_tracking.v1` publisher sets an ordering key. Every publisher publishes before it persists. [4]
- **CONFIRMED** Consumers dedupe on the event `id` only. The same scan from two publishers, such as Evri by connector and webhook, lands twice. [4][5]
- **CONFIRMED** No topic or subscription retains acked messages. `gfs-deadletter-register` stores dead letters but cannot replay them. [5]

**Dead weight.**
- **CONFIRMED** `tracking-patina-service` consumes the whole firehose and drops every event: prod sets `CARRIERS=NONE`. [6]
- **CONFIRMED** Four dead or orphaned subscriptions sit on `raw_tracking.v1`, each holding up to 7 days of backlog. [1]
- **CONFIRMED** `shipment-update-service` maps 3.0M events a week into a field nothing reads. Its synthetic `GFS_DELIVERED_EVENT` is dropped by every status consumer. [5]

**Split ownership.**
- **CONFIRMED** The carriers team owns the connectors, `tracking-core`, the status deriver, `gfs-pod` and the file processor. The cx team owns CCIS, ICIS, identity and claims. `gfs-modernizer` and patina are cross-team. [7]
- **CONFIRMED** The webhooks live in `gfs-hybrid-services`. Their grants on ECM topics sit in their own Terraform, outside ECM's. [2][4]

## Open items
| Item | Owner | By |
|---|---|---|
| Fix or pause the DHL Parcel UK connector's invalid credentials | carriers team | UNKNOWN |
| Decide where GFS meaning lives: publish a mapped event once, or keep per-consumer mapping | ECM and carriers | UNKNOWN |
| Confirm the cross-project grants exist in GCP (no Pub/Sub access from this account) | ECM platform | UNKNOWN |

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "doc", "ref": "ADO GFS Cloud Infrastructure/gfs-ecm-prod-uk1@7eb175c modules/subscription, modules/topic; ADO prod-uk1-primary-cluster@39fa64c deploy/k8s" },
  { "id": 2, "kind": "code", "ref": "tracking-webhook-royal-mail-sapient/iac/projects/gfs-hsci-tracking-webhook-royal-mail-sapient/pubsub.tf@3c880bf" },
  { "id": 3, "kind": "log", "ref": "Datadog, 2026-10-22T21:30Z to 2026-11-06T21:30Z: sum of *.pubsub.*.handled_messages; shipment_identity_service.ids_created; fenghuang.tracking.connector_response_service.responses.count; service:connector_dhlparcel status:error" },
  { "id": 4, "kind": "code", "ref": "tracking-core/ResponsePublisher/ConnectorResponseHandler.cs@c081108" },
  { "id": 5, "kind": "doc", "ref": "Research track 'consumers', 2026-11-06: STSD@a3dc446, CCIS@b2af452, ICIS@3d125f5, SUS@ccec388, claims@584d827, connect@6c6d527, tracking-mapper@44cfbf2; Datadog *.tracking_mapping.requests" },
  { "id": 6, "kind": "doc", "ref": "ADO fenghuang/tracking-patina-service@8edfb3e src/subscriber/tracking-handler.js; prod-uk1-primary-cluster deploy/k8s/fenghuang/tracking/tracking-patina-service.yaml" },
  { "id": 7, "kind": "doc", "ref": "gfs-ecm/ecm-development@b2b67df repos.json (team field)" }
] }
```
