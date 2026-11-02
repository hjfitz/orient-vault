---
tags:
- system
- parcel-portal
verified: '2026-10-29'
title: parcel-portal — overview
thesis: "Parcel Portal is GFS's own shipping portal for a shipper whose WMS drops order CSVs: it imports them with row-level validation, books and labels them through Selector, prints at the pack bench and exports the day back to the WMS. It serves one customer today (TCA at Yusen US) and is built to become multi-customer."
confidence: moderate
---
# parcel-portal — overview

```orient-bluf
{ "v": 1, "bluf": "Parcel Portal is GFS's own shipping portal for a shipper whose WMS drops order CSVs: it imports them with row-level validation, books and labels them through Selector, prints at the pack bench and exports the day back to the WMS. It serves one customer today (TCA at Yusen US) and is built to become multi-customer.", "confidence": "moderate", "action": "Decide who the tenant is (shipper or warehouse operator) before adding a second customer." }
```

**What it is.** A web portal plus an SFTP drop. A customer's WMS (Manhattan SCALE for TCA) drops order files; pack-station staff fix any bad rows, pack, dispatch, print and manifest; a day-end CSV goes back to the WMS.

**Who it serves.** Pack-station staff at a 3PL warehouse, working for one shipper, and GFS staff who set each customer up. Staff are under time pressure at a bench, so the screens favour plain reasons and one-click dispatch over density.

**Why it exists.** Despatch Cloud (DC) is going live for TCA on 9 Nov 2026, and its CSV import fails a whole file on one bad line. The portal is the parallel route: strict partial import, a fix-it loop, and an export the WMS can read. Whether TCA switches is a business call outside engineering.

## Components

| Component | Where | Onboarded |
| --- | --- | --- |
| svc (Go API), sftp host, canary | `ilg-merak/parcel-portal` `apps/svc` | yes — [[parcel-portal]] service |
| ui (Next.js) | `apps/ui` in the same repo | part of [[parcel-portal]] |
| `@ilg-merak/label-print` (WebUSB) | `packages/label-print` in the same repo | part of [[parcel-portal]] |
| Selector (GFS's carrier layer) | external | no — it is a dependency |

## Relationship to the work
- **To [[fuse]]:** it copies Fuse's pieces (the rules-engine DSL, the mapping shape, sftp-connector's SFTP host, selector-adapter's client) but doesn't depend on Fuse at runtime. Oli Denton holds that CSV ingestion belongs in Fuse; that's gate G7 and an open direction question.
- **To [[ilg-platform]]:** it runs on the platform's golden images, terraform-modules and reusable workflows, in the `ilg-merak` GCP projects.
- **Programme:** `Bifrost/Parcel Portal/` holds the ledger, gates and decisions. The multi-customer thinking is in `Bifrost/Parcel Portal/Multi-customer.md`.

See [[architecture]], [[known-context]] and [[design]] in this folder.
