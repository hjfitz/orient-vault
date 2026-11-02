---
tags: [waypoint, ledger]
---
# carrier-proxies — work ledger

Agent-facing. Newest first. What meaningful work happened here, and the
context a future agent needs. Not a diary, not release notes, not a diff.

## 2026-10-08 — CID-334

Migrate the UPS proxy onto api-host-framework

Moved all ten UPS routes from the Azure DevOps proxy into apps/ups-proxy on api-host-framework, as a three-PR stack: scaffold and infra with the five stepping-stone XML pass-throughs, then access points, then shipping. XML bodies reach the handlers raw through the framework's middlewares hook, which openapi-backend doesn't validate. Success shapes are pinned by golden fixtures from the original's integration tests. Retries are 0, because createLabel and ShipConfirm aren't idempotent (api-host-framework#14). Known original bugs are kept as-is and listed in the README: AdressLine, and ShipmentServiceOptions outside Shipment. CarrierException drops UPS's error messages, so go-live needs a decision on that.

PR: gfs-hybrid-services/carrier-proxies#4
PR: gfs-hybrid-services/carrier-proxies#5
PR: gfs-hybrid-services/carrier-proxies#6
