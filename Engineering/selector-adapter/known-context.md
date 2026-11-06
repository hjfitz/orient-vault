---
tags:
- waypoint
- selector-adapter
verified: '2026-10-27'
---
# selector-adapter — known context

Decisions from Harry (2026-10-27) and facts that source can't give you. Claims marked
`(snapshot …)` describe mutable state and age out.

## Intent and ownership

- **Selector is delivery, not fulfilment.** The customer has packed the goods; Fuse books the carrier
  shipment and gets the label. Only `sales_order` goes to Selector. Manifesting (`CommitShipments`)
  stays in Selector.
- **Owner:** Harry, as out-of-team work with no ticket. The **Delivery Backends** programme
  (`Bifrost/Delivery Backends/`) carries it from spike to real traffic.
- **Selector config** becomes a `SELECTOR` backend in config-service `BACKEND_CONFIG` (programme A1–A3),
  managed from a Merak portal (C2). It never appears in fuse-ui.
- **Routing:** the deduper stamps one boolean attribute per backend type (`snap`, `selector`), and each
  adapter's subscription filters on its own tag (B1, B3).

## Decisions behind the rules (Gate C, 2026-10-27)

- A timeout after send leaves the claim ambiguous; the next delivery reconciles with `DailyShipQuery`
  by despatch date and upper-cased `ShipRef`. Found → booked; absent → book.
- Bad credentials (`FAILURE 0010`) nack: a config fault, not an order fault.
- Domestic = country code GB, including Northern Ireland. Jersey, Guernsey, the Isle of Man and unknown
  countries are rejected. (snap-adapter's `deriveCountryCode` defaults unknown to GB; this adapter must not.)
- A past or missing `dates.shipment` becomes today in Europe/London, because Selector rejects both.
- `quantities.weight` is kg; a missing weight uses the connection default.
- Recipient = first `shipAddresses` + first `shipContacts`; contact name → `PersonName`,
  `customer.name` → `Company` (without a company Selector warns `0002` but still books).
- Carrier, service and contract come from connection defaults only; `shipping.carrier`/`method` are
  ignored, because upstream values are not Selector codes.
- An already-booked order that is amended or redriven stays booked.
- The spike closed **without a live dev end-to-end test**. Delivery Backends B2 owns the first real-route proof.

## Surprises

- Selector **does not deduplicate**. Three `ProcessShipment` calls with one reference gave three
  consignments, and `ShipmentID` stays 0. The claim is the only guard.
- The **sandbox `TEST` account is shared** with other teams' traffic; `DailyShipQuery` shows their bookings.
- The Go Firestore client **retries an unreachable host until the context ends**. Without the 5 s
  per-call timeout a push request hung for 25 s.
- The proxy (`selector-rest-proxy`) only ever used the batch `ProcessShipments`; the single call was
  first proven here.

## Fragility

- **Claim keys change in B2** to (order, `backendId`), once config-service mints backend IDs. Claims
  written before then use `{businessId}:{shipmentId}`. (snapshot 2026-10-27: no real claims exist)
- **The canonical has no packages.** One package per order is a placeholder until a package model exists.
- **No dead-letter policy.** An order that can never succeed retries until the 7-day retention lapses;
  prod needs tracking-service's DLT plus a `.dlt.sub` hold subscription.
- **Fuse shipments reach billing only if the Selector site commits and uploads them.** The adapter
  calls `ProcessShipment` only (`booker.go:24`), and leaves manifesting to Selector. Billing bills from
  central Selector `SHIPMENTS` rows, which exist only after a commit and a Client4 upload from the
  site's upload station. So each target site needs auto-commit (`AUTO_COMMIT`/`AC_TIME`) and
  auto-upload on, and a running upload station. Nothing alerts when a booked shipment never reaches
  billing. Check this per business before Delivery Backends takes real traffic. Parcel Portal commits
  explicitly (`CommitShipments`), for comparison. Source: MPK *Legacy Selector - Day End and Billing
  Handoff* (353566845), 2026-11-06.

## Unknowns

- Will customers need tracking numbers or labels returned to them, and through which topic?
- What do multi-package and international (customs) orders look like in the canonical?
- When does a business have both Snap and Selector backends, and which records go to each?
