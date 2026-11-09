---
tags: [adhoc-task]
date: 2026-11-06
tldr: "Resumed the carrier-integrations handover on rc-hjf. Added the POD carrier table, gave gfs-pod-service its own MPK page under Carrier Ingress Services, and swapped the ingress/egress naming to GFS's side across MPK and the vault; then mapped ECM's Pub/Sub event world end to end (label to POD) into two explainers"
session_id: 9ef32451-f6a6-429e-88df-add8e5d83ddf
status: done
---
# Add the POD service carrier table

## Outcome
- Added the per-carrier POD table to `Engineering/gfs-pod-service/known-context.md` and pointed the architecture's Interfaces out at it. Lint is clean, no re-anchor, `wp index` rebuilt.
- Added the same table to MPK 353206310 Carrier Integration Uses as v4.
- Swapped ingress/egress to GFS's side: 353697822 is now Carrier Egress Services and 353206337 Carrier Ingress Services. Link text updated on 5 more pages, and the vault system docs updated.
- New MPK page *Proof of Delivery Service* (353861642) under Ingress. The POD detail on the Uses page moved there.
- Stored Harry's POD-at-ingress design as a kept Waypoint idea with a draft stub, `gfs-pod-service/plans/capture-pods-at-ingress-and-serve-them-from-a-st`. It's an idea only: carriers own the service.
- Researched ECM's event world (Terraform, Flux, code, Datadog): [[2026-11-06-life-of-a-shipment-through-ecm]] and [[2026-11-06-ecm-event-world-where-its-a-mess]]. One finding needs action: the DHL Parcel UK connector is polling with invalid credentials.
- 2026-11-09: closed the gaps (cross-project Terraform, shipment mutators), published MPK *Shipment Journey Through ECM* (354975746) under Carrier Services, and corrected the POD "GPS" claim on the POD, Ingress and Uses pages and in the vault.
- Handover record: [[Handovers/2026-11-06-carrier-integrations]].
