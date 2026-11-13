---
tags:
- system
- parcel-portal
verified: '2026-11-13'
title: parcel-portal — overview
thesis: "Native Dispatch, formerly the Parcel Portal (the repo, service and system ids stay parcel-portal), is GFS's own dispatch portal for a shipper whose WMS drops order CSVs: it imports them with row-level validation, books and labels them through Selector, prints at the pack bench and exports the day back to the WMS. Prod is held and nothing is deployed there, so no customer uses it yet: TCA at Yusen US, the first customer, has seen a demo and is being set up on dev. It is built to become multi-customer."
confidence: moderate
---
# parcel-portal — overview

```orient-bluf
{ "v": 1, "bluf": "Native Dispatch, formerly the Parcel Portal (the repo, service and system ids stay parcel-portal), is GFS's own dispatch portal for a shipper whose WMS drops order CSVs: it imports them with row-level validation, books and labels them through Selector, prints at the pack bench and exports the day back to the WMS. Prod is held and nothing is deployed there, so no customer uses it yet: TCA at Yusen US, the first customer, has seen a demo and is being set up on dev. It is built to become multi-customer.", "confidence": "moderate", "action": "Decide who the tenant is (shipper or warehouse operator) before adding a second customer." }
```

**What it is.** A web portal, an SFTP drop and a customer API. A customer's WMS (Manhattan SCALE for TCA) drops order files or sends them through the API. Pack-station staff fix any bad rows, pack, dispatch, print and manifest. A day-end CSV goes back to the WMS.

**Who it serves.** Pack-station staff at a 3PL warehouse, working for one shipper, and GFS staff who set each customer up. Staff are under time pressure at a bench, so the screens favour plain reasons and one-click dispatch over density.

**Why it exists.** Despatch Cloud (DC) was due to go live for TCA on 9 Nov 2026. Its CSV import fails a whole file on one bad line. The portal is the parallel route: strict partial import, a fix-it loop, and an export the WMS can read. Whether TCA switches is a business call outside engineering. UNRESOLVED: whether DC went live on 9 Nov is not recorded in the vault.

## Where it stands (13 Nov 2026)
- **Dev only.** No portal build has reached prod. Each prod run since the first push either gets cancelled by a newer run or waits at the `terraform-prod` approval. The prod launch waits at unit D1 [1][2].
- **TCA** saw a demo on 12 Nov. The 13 Nov catch-up set the next step: one proof against TCA's own Selector endpoint, then an account for TCA. TCA will start by dispatching one order at a time by hand [3].
- **The customer API** runs on dev behind a public gateway. Its key screen has been hidden since 12 Nov, because the business isn't ready for it. TCA wants an API test from 30 Nov, so bringing the screen back is an open call [3][4].
- **Programmes.**
  - `Bifrost/Parcel Portal/`: foundations, customer screens and the prod launch. 44 units, 30 merged. 5 are in progress: customer API, two acting-as units, label preview and prod launch D1. 8 UI defects are not started [2].
  - `Bifrost/Native Dispatch/`: the customer feedback, in planning since 13 Nov. 17 requirements, 33 units. 4 shipped on 12 Nov, 1 is in progress, 5 wait on an answer and Harry dropped 1 [3][4].

## Components

| Component | Where | Onboarded |
| --- | --- | --- |
| svc (Go API), sftp host, canary, customer-API gateway, dev debug MCP | `ilg-merak/parcel-portal` `apps/svc` | yes — [[parcel-portal]] service |
| ui (Next.js) | `apps/ui` in the same repo | part of [[parcel-portal]] |
| `@ilg-merak/label-print` (WebUSB) and `@ilg-merak/ssh-keygen` (browser key generation) | `packages/` in the same repo | part of [[parcel-portal]] |
| Selector (GFS's carrier layer) | external | no — it is a dependency |

## Relationship to the work
- **To [[fuse]]:** it copies Fuse's pieces (the rules-engine DSL, the mapping shape, sftp-connector's SFTP host, selector-adapter's client). It doesn't depend on Fuse at runtime. Oli Denton holds that CSV ingestion belongs in Fuse; that's gate G7 and an open direction question. The customer API is the clearest overlap with Fuse's fapi.
- **To [[ilg-platform]]:** it runs on the platform's golden images, terraform-modules and reusable workflows, in the `ilg-merak` GCP projects.
- **Programme:** `Bifrost/Parcel Portal/` holds the ledger, gates and decisions for the foundations and prod. `Bifrost/Native Dispatch/` holds the 13 Nov feedback and trial units. The multi-customer thinking is in `Bifrost/Parcel Portal/Multi-customer.md`.

See [[architecture]], [[known-context]] and [[design]] in this folder.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "code", "ref": ".github/workflows/svc-on-push.yaml@621357e" },
  { "id": 2, "kind": "doc", "ref": "Bifrost/Parcel Portal/Migration State.md" },
  { "id": 3, "kind": "doc", "ref": "Bifrost/Native Dispatch/Overview.md" },
  { "id": 4, "kind": "doc", "ref": "Bifrost/Native Dispatch/Migration State.md" }
] }
```
