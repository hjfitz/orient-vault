---
tags:
- system
- ecm
verified: '2026-11-09'
title: ecm — overview
thesis: "ECM is the event-driven platform behind GFS tracking. It learns of a shipment only after Selector uploads it into central Firebird, rebuilds its status from raw carrier scans, tells customers, and fetches proofs of delivery live. The MPK research pages and Lucid diagrams that describe it are indexed here."
confidence: moderate
---
# ecm: overview

```orient-bluf
{ "v": 1, "bluf": "ECM is the event-driven platform behind GFS tracking. It learns of a shipment only after Selector uploads it into central Firebird, rebuilds its status from raw carrier scans, tells customers, and fetches proofs of delivery live. The MPK research pages and Lucid diagrams that describe it are indexed here.", "confidence": "moderate", "action": "Treat five of the MPK pages as unverified drafts. Check a figure against known-context before you quote it." }
```

**What it is.** ECM is the team name for the platform, and the name the MPK pages use. It runs in the `gfs-ecm` GCP projects. This vault holds no statement of what the letters stand for (UNKNOWN).

**What it does.** Central Firebird's `SHIPMENTS` change feed becomes `shipments.v2.identified`. Tracking connectors, a webhook and SFTP files publish raw carrier events to `raw_tracking.v1`. Consumers derive a status, and customers read it through portals, Connect and webhooks. `gfs-pod-service` fetches the proof of delivery when someone asks.

**What it is not.** It does not make labels. Selector does, and the carrier proxies serve Selector. ECM first hears of a shipment after upload. The path of one shipment is in [[2026-11-06-life-of-a-shipment-through-ecm]]. The diagnosis of its event design is in [[2026-11-06-ecm-event-world-where-its-a-mess]].

**Standing context.** Replacing ECM and Selector with Merak is an unconfirmed hunch (Harry, 2026-11-09). The MPK pages say "a replacement" and leave the choice to the Merak team. Keep any new wording hypothetical.

## Where the research lives

All pages are in the MPK space, at `https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/<id>`. The root, 351502339, indexes them [2].

| Page | Id | State on 2026-11-09 |
| --- | --- | --- |
| Shipment Journey Through ECM | 354975746 | Live. Corrected after a 31-agent review of 36 claims: 19 confirmed, 17 partly right, none refuted |
| Selector and ECM Coupling | 354418743 | Published draft, unverified. Corrected once after a three-agent challenge |
| Tracking Events and Webhooks: What v1 Needs | 355074077 | Published draft, unverified |
| How Carriers Feed ECM | 355074111 | Published draft, unverified |
| From Label to Invoice | 354353232 | Published draft, unverified. Holds the former Day End and Billing Handoff page |
| How Each Carrier's POD Is Retrieved | 354877489 | Published draft, unverified. Code read at `GFS POD` `d1f0ada` |
| Proof of Delivery Service | 353861642 | Live |
| Carrier Tracking and Proof of Delivery | 353206337 | Live. Per-carrier counts moved to the canonical window |
| Carrier Proxies and Labelling | 353697822 | Live |
| Polling Connectors | 353697880 | Live |
| Tracking Webhook Services | 353533985 | Live |
| Carrier Integration Uses, Carrier Integration Methods | 353206310, 353697842 | Live |
| Legacy Selector (index), Customer Data Flow | 351764483, 352157700 | Live. See [[selector]] |

Harry declined a verification run for the five drafts. Do not run one unless he asks. One Sonnet reader built page 4 from the Billing space and the Selector docs. It did not read CCDIS or the `REG_WILKO_*` procedures [1].

The tools cannot delete pages, so Harry deletes three by hand [3]:
- Carrier Services (353468499).
- Day End and Billing Handoff (353566845, now a pointer).
- A scratch draft (355565572).

## Diagrams

Nine C4 diagrams were drawn in Lucidchart, folder "Merak research diagrams" (id 454289417). Each has a text twin in the vault. Harry chose to link them from the pages and draw Confluence whiteboards himself.

| Diagram | Lucid document id | Text twin |
| --- | --- | --- |
| Selector, Firebird and ECM | `ea0a71eb-4fb1-4124-9fe5-e70720cb5e20` | [[Handovers/2026-11-09-merak-replacement-pages.diagram-selector-ecm-coupling]] |
| Shipment journey | `2a2e0c77-b50f-4a8f-8389-63ad1cbf6a62` | [[Handovers/2026-11-09-merak-replacement-pages.diagram-shipment-journey]] |
| Tracking, carrier to customer | `bb2d2e80-97e3-4dd6-8987-fb476539082b` | [[Handovers/2026-11-09-merak-replacement-pages.diagram-tracking-carrier-to-customer]] |
| Polling connector | `4081aae8-66c2-4184-b740-ca467d81ba87` | [[Handovers/2026-11-09-merak-replacement-pages.diagram-polling-connector]] |
| Tracking webhook service | `a9a3115b-bce5-4257-b6e4-2f63ae886457` | [[Handovers/2026-11-09-merak-replacement-pages.diagram-tracking-webhook]] |
| gfs-pod-service | `22adc685-20d6-4e99-bed6-54a03bc4bc16` | [[Handovers/2026-11-09-merak-replacement-pages.diagram-pod-service]] |
| Carrier proxy | `e1cffe19-99b0-45f9-bcc5-fb0f828c9b46` | [[Handovers/2026-11-09-merak-replacement-pages.diagram-carrier-proxy]] |
| Customer data flow (Selector) | `0ebebd78-e550-4199-a8b6-37b48b6f4312` | [[Handovers/2026-11-09-merak-replacement-pages.diagram-customer-data-flow]] |
| Pre-advice by file | `5c1c552d-27ef-430b-addd-6cc3cf894aea` | [[Handovers/2026-11-09-merak-replacement-pages.diagram-carrier-integration-methods]] |

The Lucid macro did not render on the Confluence site on 2026-11-09, because the app is not installed. Smart links do render. The links on the pages are view-only and restricted to the account.

## Source copies of the draft pages

The vault copies are the source for edits. Change the live page first, then the copy.
- [[Handovers/2026-11-09-merak-replacement-pages.page1-selector-ecm-coupling]] and its [[Handovers/2026-11-09-merak-replacement-pages.page1-challenge-findings]]
- [[Handovers/2026-11-09-merak-replacement-pages.page2-tracking-events-webhooks]]
- [[Handovers/2026-11-09-merak-replacement-pages.page3-how-carriers-feed-ecm]]
- [[Handovers/2026-11-09-merak-replacement-pages.page4-label-to-invoice]]
- [[Handovers/2026-11-09-merak-replacement-pages.page5-pod-by-carrier]]

## Neighbours
- [[selector]] owns the label, the upload and central Firebird's set-up. ECM and Selector meet at Firebird (see [[Systems/ecm/architecture]]).
- [[carrier-integrations]] owns the proxies, the polling connectors, the webhooks, the file path and `gfs-pod-service`. Those services feed ECM's `raw_tracking.v1`.
- These ECM services have no vault folder yet:
  - `gfs-modernizer`, `shipment-identity-service` and `patina-service-2`
  - the Scan Injector and the Firebird Transfer Service
  - the status deriver, CCIS, ICIS and `connect-hooks`
- `gfs-pod-service`, `tracking-core`, the webhooks and the file path do have Waypoint folders.

## What deliberately isn't here
- **The long form.** The MPK pages carry it. This system is the index, the contracts and the open questions.
- **Security findings.** Harry declined a security ticket ("not my domain"). Do not draft or offer one.
- **Parcel Portal.** It is not part of the Merak replacement framing.

## Evidence
```orient-evidence
{ "v": 1, "items": [
  { "id": 1, "kind": "doc", "ref": "Handovers/2026-11-09-merak-replacement-pages.md" },
  { "id": 2, "kind": "doc", "ref": "Confluence MPK 351502339 1. Research into Existing Services" },
  { "id": 3, "kind": "doc", "ref": "Tasks/2026-11-09-merak-pages-published.md" }
] }
```
