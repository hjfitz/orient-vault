---
tags: [adhoc-task]
date: 2026-10-27
tldr: "Onboarded selector-rest-proxy into Waypoint and shaped the Fuse selector-adapter: dev-only Go spike on ProcessShipment, shared platform work deferred; explainer written"
session_id: df864a71-c756-4a55-ad95-619475305331
status: done
---
# Onboard selector-rest-proxy into Waypoint

## Outcome
Cloned gfs-hybrid-services/selector-rest-proxy to ~/code/fuse/selector-rest-proxy and wrote
Engineering/selector-rest-proxy/ (waypoint.yaml, overview, architecture, known-context), anchored at 05c2bea.
Open unknowns: why CID-308 EU validation was disabled, Fuse adapter ticket, ApiKy profile ownership.

Shaped the selector-adapter (Go, gfs-bifrost): adapter-first dev spike on Selector `ProcessShipment`, shared programme (types, config-service multi-connection, deduper tagging, reader tolerance, fuse-ui) deferred pending PM/EM delivery-vs-fulfilment call. Explainer: Explainers/2026-10-27-selector-adapter-spike-shape.md. Plan drafted + 3-way reviewed: Engineering/selector-adapter/plans/selector-adapter-dev-spike.md (complete 2026-10-27; deployed to dev; live e2e moved to Delivery Backends B2).
