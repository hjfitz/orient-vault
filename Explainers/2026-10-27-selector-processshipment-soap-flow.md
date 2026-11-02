---
tags: [explain]
date: 2026-10-27
thesis: "selector-adapter books one order with one SOAP 1.1 POST: a document/literal RequestedShipment carrying ShipRequest, credentials in the body, SOAPAction ProcessShipment; it reads ShipReply.ResponseStatus to decide ack, nack or reject."
confidence: moderate
---
# Selector adapter: the ProcessShipment SOAP call, end to end

```orient-bluf
{ "v": 1, "bluf": "selector-adapter books one order with one SOAP 1.1 POST: a document/literal RequestedShipment carrying ShipRequest, credentials in the body, SOAPAction ProcessShipment; it reads ShipReply.ResponseStatus to decide ack, nack or reject.", "confidence": "moderate", "action": "Decide what the claim does when the call times out after sending; it is the one step that can book a shipment twice." }
```

## Situation

- **CONFIRMED** selector-adapter makes one Selector call per order: `ProcessShipment`, the single-shipment operation [1]. The sequence below is the whole path for one `create_record` sales order.

```orient-sequence
{ "v": 1,
  "actors": [
    { "id": "ps", "label": "Pub/Sub create_record" },
    { "id": "ad", "label": "selector-adapter", "service": "selector-adapter" },
    { "id": "rd", "label": "Redis claim" },
    { "id": "sel", "label": "Selector ClientShipService.asmx" }
  ],
  "steps": [
    { "from": "ps", "to": "ad", "label": "push sales_order (filter fulfilmentSelector)", "kind": "async" },
    { "from": "ad", "to": "ad", "label": "validate canonical, resolve connection, map RequestedShipment", "kind": "call" },
    { "from": "ad", "to": "rd", "label": "SET NX claim:{businessId}:{shipmentId}", "kind": "call" },
    { "from": "rd", "to": "ad", "label": "won, or lost (ack and stop)", "kind": "return" },
    { "from": "ad", "to": "sel", "label": "POST SOAPAction ProcessShipment", "kind": "call", "ev": [1] },
    { "from": "sel", "to": "ad", "label": "ShipReply: ResponseStatus + ProcessedShipment", "kind": "return", "ev": [1] },
    { "from": "ad", "to": "ps", "label": "2xx ack, or 5xx nack", "kind": "return" }
  ] }
```

## Assessment

### The request

- **CONFIRMED** The service has SOAP 1.1 and 1.2 bindings at the same `.asmx` address, both `document/literal` [1]. The adapter uses 1.1: `Content-Type: text/xml; charset=utf-8` and `SOAPAction: "ProcessShipment"`.
- **CONFIRMED** The WSDL declares no SOAP header [1]. Credentials travel in the body as `AuthenticationDetails`: `VersionId` 5.0.0, `UserID`, `UserPassword`. The proxy sends the same [2].
- **CONFIRMED** The body element is the message part, so the names nest twice [1]:

```xml
<RequestedShipment xmlns="http://justshoutgfs.com/Client/Ship/v5/">
  <ShipRequest>
    <AlternativeServices>false</AlternativeServices>
    <PrintSpecification>…ZPLII, 203 dpi, 4x6…</PrintSpecification>
    <Shipment>                    <!-- type RequestedShipment -->
      <Recipient>…</Recipient>
      <Shipment>…</Shipment>      <!-- type RequestedShipmentDetails -->
    </Shipment>
    <AuthenticationDetails>…</AuthenticationDetails>
  </ShipRequest>
</RequestedShipment>
```

- **CONFIRMED** The namespace still reads `justshoutgfs.com` after the domain moved to `gfsdeliver.com` [1]. It is an identifier, so the adapter must send it verbatim.
- **ASSESSED** The adapter derives the endpoint from the connection's WSDL URL by dropping `?wsdl`. It never fetches the WSDL at runtime, unlike the proxy, which fetches it on every request [2].

### The reply

- **CONFIRMED** Selector wraps the reply in `ProcessedShipment` → `ProcessShipmentResult` (type `ShipReply`). That holds `ResponseStatus` and a `Shipment` with `ConsignmentNo`, `ShipmentID`, `ShipmentStatus` and base64 labels [1].
- **CONFIRMED** `ResponseStatus` is one of `SUCCESS`, `NOTE`, `WARNING`, `ERROR`, `FAILURE` [1]. The proxy treats only `ERROR` and `FAILURE` as failures [3]. The adapter does the same.
- **ASSESSED** The outcomes map to Pub/Sub as below.

| Outcome | Adapter does |
|---|---|
| `SUCCESS`, `NOTE`, `WARNING` | log `ConsignmentNo`, ack |
| `ERROR`, `FAILURE` | permanent: release the claim, ack |
| connection error, HTTP 5xx, timeout | transient: nack |
- **UNKNOWN** Bad credentials may come back as a SOAP Fault or as `FAILURE`. One sandbox call with a wrong password settles it.

### The step that can double-book

- **ASSESSED** A timeout after the POST leaves the booking state unknown. Releasing the claim lets the redelivery book again. Keeping it drops the order.
- **UNKNOWN** If Selector rejects a repeated `Recipient.ShipmentReference`, the adapter keeps no claim and lets Selector deduplicate. The sandbox decides which.

### After Fuse

- **CONFIRMED** The booking stays open until the client runs `CommitShipments` (end of day, manifest) in Selector. Until then `DeleteShipments` can cancel it [1]. Fuse calls neither in v1.

## Evidence

```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "url", "ref": "https://sandbox.gfsdeliver.com/ClientServer_450/ClientShipService.asmx?wsdl", "note": "read 2026-10-27: ShipServiceSoap binding, ProcessShipment operation, ShipRequest, ShipReply, ResponseStatusType" },
  { "id": 2, "kind": "url", "ref": "https://github.com/gfs-hybrid-services/selector-rest-proxy/blob/05c2bea/src/selector.ts" },
  { "id": 3, "kind": "url", "ref": "https://github.com/gfs-hybrid-services/selector-rest-proxy/blob/05c2bea/src/handlers/selector/util.ts" }
] }
```
