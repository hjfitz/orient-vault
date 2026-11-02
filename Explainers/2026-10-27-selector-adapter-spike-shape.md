---
tags: [explain]
date: 2026-10-27
thesis: "Build selector-adapter first, as a dev-only Go spike that turns one canonical sales order into one Selector ProcessShipment call; the shared platform work waits until PM/EM settle delivery versus fulfilment."
confidence: moderate
---
# Selector adapter: spike first, one order per ProcessShipment call

```orient-bluf
{ "v": 1, "bluf": "Build selector-adapter first, as a dev-only Go spike that turns one canonical sales order into one Selector ProcessShipment call; the shared platform work waits until PM/EM settle delivery versus fulfilment.", "confidence": "moderate", "action": "Agree ProcessShipment and the field mapping, then draft the single selector-adapter Waypoint plan." }
```

## Situation

- **CONFIRMED** Fuse will gain a Go selector-adapter in a new gfs-bifrost repo. It books a carrier shipment in Selector for orders the customer has already packed. It replaces selector-rest-proxy, which serves two tenants today [1].
- **CONFIRMED** Only `sales_order` goes to Selector. Fuse doesn't commit or manifest, and v1 publishes nothing back.
- **ASSESSED** The product boundary between delivery and fulfilment is open. Anything that encodes it, such as the "fulfilment connection" rename, connections per business, or broadcast routing, would commit the platform early.

## Assessment

- **CONFIRMED** Shared rollout has hard blockers. snap-adapter throws when a business has no Snap backend [2]. The SNAP-only schema rejects any other backend type, and the poller parses whole pages with it [3]. config-service holds one backend per business. None of these apply to a dev spike that saves no config and reads no live traffic.
- **CONFIRMED** The spike stays isolated. A static connection provider stands in for config-service, and the Selector sandbox (`TEST`) is the target. Its dev subscription filters on `attributes:fulfilmentSelector`, which only fuse-mocker sets.
- **ASSESSED** That filter is the future production design: the deduper tags each record with its connection types. Replay redrives already pass through the deduper, since they publish to `create_record_request` [4].
- **CONFIRMED** Selector's WSDL offers `ProcessShipment` (single) and `ProcessShipments` (batch) [5]. The proxy uses the batch call [6].
- **ASSESSED** The single call fits better. Fuse handles one order per message, and a batch brings partial success and redelivery that rebooks every shipment in it. Both calls take the same `RequestedShipment`, so changing later is cheap.
- **CONFIRMED** A canonical sales order has the address, contact and references. It has no packages, only an order-level weight [7]. The spike sends one default package. A `packages[]` field waits for product clarity.
- **CONFIRMED** The WSDL requires value fields the proxy spec omits, among them `ShipperId`, `ShipmentID`, `Packs`, `TotalWeight` and `ConsolidateShipment` [5]. Connection config supplies `ShipperId` and the carrier defaults. `ConsolidateShipment` is `false`.
- **UNKNOWN** Does Selector reject a repeated `ShipmentReference`? The answer decides the duplicate-shipment guard.
- **UNKNOWN** Does `ShipmentID = 0` make Selector assign one, and does `RouteMapCode` alone select a carrier? The first sandbox runs settle both.

## Open items

| Item | Owner | By |
|---|---|---|
| Confirm `ProcessShipment` and the field mapping | Harry | 2026-10-28 |
| Draft the selector-adapter Waypoint plan (dev-only, no ticket) | Claude | after confirmation |
| Settle delivery versus fulfilment, which gates the shared programme | PM/EM | open |
| Check whether fuse-mocker `mock-send` can set a custom attribute | Claude | in the plan |

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "doc", "ref": "Engineering/selector-rest-proxy/known-context.md" },
  { "id": 2, "kind": "url", "ref": "https://github.com/gfs-bifrost/snap-adapter/blob/a09a346/apps/snap-adapter/src/adapters/customer-router/customer.http-router.ts", "note": "forCustomer throws SnapMissingCredentialsException" },
  { "id": 3, "kind": "url", "ref": "https://github.com/gfs-bifrost/pkg-node/blob/bae9d99/pkg/types/src/config/schemas/backend-fragment.schema.ts", "note": "type: z.literal(\"SNAP\"); the poller parses /backend pages with it" },
  { "id": 4, "kind": "url", "ref": "https://github.com/gfs-bifrost/replay-service/blob/9254a1f/code/src/core/failure/failure.service.ts", "note": "inboundTarget publishes to CREATE_RECORD_REQUEST_TOPIC" },
  { "id": 5, "kind": "url", "ref": "https://sandbox.gfsdeliver.com/ClientServer_450/ClientShipService.asmx?wsdl", "note": "read 2026-10-27; ShipRequest/ShipReply, RequestedShipmentDetails" },
  { "id": 6, "kind": "url", "ref": "https://github.com/gfs-hybrid-services/selector-rest-proxy/blob/05c2bea/src/handlers/selector/process-shipments.handler.ts" },
  { "id": 7, "kind": "url", "ref": "https://github.com/gfs-bifrost/pkg-node/blob/bae9d99/pkg/types/src/canonical/types/sales-order.types.ts" }
] }
```

## Update @ 15:10

- **CONFIRMED** Selector is delivery, not fulfilment (Harry, 2026-10-27). fuse-ui shows no Selector config or anything related.
- **CONFIRMED** config-service may still hold Selector config. How Fuse tells a delivery customer from a fulfilment customer stays open until the team has built the adapter.
- **ASSESSED** Storing it in `BACKEND_CONFIG` would bring back the backend-reader blocker, because the poller parses whole pages as SNAP-only [3].
