---
tags:
- waypoint
- ups-proxy
verified: '2026-11-06'
---
# ups-proxy — known context

From the 2026-11-05/06 proxy surveys and the carrier-playground port. No interview.

- **CSS's LabelRecovery can't work:** CSS sends it as `text/xml`, which this proxy doesn't parse, so UPS receives `{}`.
- **The dev rewrite** (`carrier-proxies/apps/ups-proxy`, CID-334) moves all ten routes onto api-host-framework. Its camelCase routes would break Selector's PascalCase calls (G1).
- **UPS accounts:** GFS holds a pool and assigns one per customer; the customer's ApiKy profile is only `{"company": ...}`.
- **Mock copy:** `ilg-merak/carrier-playground` `apps/ups-proxy`.

## Unknowns
- Whether UPS's JSON APIs return a single object instead of an array for one item, which would break V2's mapping.
