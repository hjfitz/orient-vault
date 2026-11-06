---
tags: [waypoint, royal-mail-proxy]
verified: 2026-11-06
---
# royal-mail-proxy — known context

From the 2026-11-05/06 proxy surveys (code, Datadog). No interview.

- **Log messages are mislabelled.** "Incoming request received" comes from `createRoyalMailLabel`; "Incoming create label request received" comes from `manifestShipments`. Before 5 Nov this hid about 29.6k labels behind a "349 labels" count.
- **The busiest proxy:** 19 Royal Mail accounts, calls between 08:00 and 16:00 UTC with a 10:00 peak (snapshot 2026-11-06).
- **Changed on CID tickets** by Carrier Integrations; last change 3 Nov 2026 (CID-365, removed logging of API key values).
- **Mock copy:** `ilg-merak/carrier-playground` `apps/royal-mail-proxy`, deployed as `royalmail.mocks.merak.freightops.dev`.

## Unknowns
- Which GFS customer is behind each of the 19 Royal Mail accounts. Needs the ApiKy profiles or Royal Mail account records.
